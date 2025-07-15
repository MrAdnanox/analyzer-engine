# FICHIER: analyzer-engine/ingestion/storage/repositories/postgres_repository.py (MODIFIÉ)
import os
import json
import logging
import asyncio  # <-- AJOUTER CET IMPORT
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool
from dotenv import load_dotenv

from core.contracts.vector_repository_contract import IVectorRepository
from core.models.db import ChunkResult, DocumentMetadata
from core.exceptions.base_exceptions import RepositoryError

load_dotenv()
logger = logging.getLogger(__name__)


class PostgresRepository(IVectorRepository):
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RepositoryError("DATABASE_URL environment variable not set")
        self._pool: Optional[Pool] = None
        logger.info("PostgresRepository instance created.")

    async def initialize(self) -> None:
        if self._pool is not None and not self._pool._closed:
            return

        # ======================= LA RÉSILIENCE AU BON ENDROIT =======================
        # La logique de retry est maintenant DANS le composant. Il est robuste par conception.
        max_retries = 5
        retry_delay = 2  # secondes
        for attempt in range(max_retries):
            try:
                self._pool = await asyncpg.create_pool(
                    self.database_url, min_size=2, max_size=5, command_timeout=30
                )
                logger.info(f"PostgreSQL pool initialized on attempt {attempt + 1}")
                return  # Succès, on sort de la méthode
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} to connect to PostgreSQL failed: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error("All attempts to connect to PostgreSQL failed.")
                    raise RepositoryError(
                        f"Failed to initialize PostgreSQL pool after {max_retries} retries: {e}"
                    )
                await asyncio.sleep(retry_delay * (attempt + 1))  # Backoff simple
        # ============================================================================

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed for instance.")

    @asynccontextmanager
    async def _get_connection(self):
        if not self._pool:
            await self.initialize()

        # Le reste du code utilise self._pool qui est maintenant propre à l'instance
        async with self._pool.acquire() as connection:
            yield connection

    async def vector_search(
        self, embedding: List[float], limit: int
    ) -> List[ChunkResult]:
        async with self._get_connection() as conn:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            rows = await conn.fetch(
                "SELECT * FROM match_chunks($1::vector, $2)", embedding_str, limit
            )
            return [
                ChunkResult(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    score=row["similarity"],
                    metadata=json.loads(row["metadata"]),
                    document_title=row["document_title"],
                    document_source=row["document_source"],
                )
                for row in rows
            ]

    async def hybrid_search(
        self, embedding: List[float], query_text: str, limit: int, text_weight: float
    ) -> List[ChunkResult]:
        async with self._get_connection() as conn:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            rows = await conn.fetch(
                "SELECT * FROM hybrid_search($1::vector, $2, $3, $4)",
                embedding_str,
                query_text,
                limit,
                text_weight,
            )
            return [
                ChunkResult(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    score=row["combined_score"],
                    metadata=json.loads(row["metadata"]),
                    document_title=row["document_title"],
                    document_source=row["document_source"],
                )
                for row in rows
            ]

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        async with self._get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id::text, title, source, content, metadata FROM documents WHERE id = $1::uuid",
                document_id,
            )
            return dict(row) if row else None

    async def list_documents(self, limit: int, offset: int) -> List[DocumentMetadata]:
        async with self._get_connection() as conn:
            # Cette requête est simplifiée, on pourrait la rendre plus complexe au besoin
            rows = await conn.fetch(
                "SELECT d.id::text, d.title, d.source, d.created_at, d.updated_at, COUNT(c.id) AS chunk_count FROM documents d LEFT JOIN chunks c ON d.id = c.document_id GROUP BY d.id ORDER BY d.created_at DESC LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
            return [DocumentMetadata(**dict(row)) for row in rows]

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        async with self._get_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM get_document_chunks($1::uuid)", document_id
            )
            return [dict(row) for row in rows]

    async def save_document_with_chunks(
        self,
        file_path: str,
        document_content: str,
        chunks: List[Dict[str, Any]],
        document_metadata: Dict[str, Any],
    ) -> int:
        async with self._get_connection() as conn:
            async with conn.transaction():

                document_id = await conn.fetchval(
                    "INSERT INTO documents (title, source, content, metadata) VALUES ($1, $2, $3, $4) RETURNING id",
                    file_path,
                    file_path,
                    document_content,
                    json.dumps(document_metadata),
                )

                chunks_to_insert = [
                    (
                        document_id,
                        c["content"],
                        str(c["embedding"]),
                        c["index"],
                        json.dumps(c["metadata"]),
                        c.get("token_count"),
                    )
                    for c in chunks
                    if c.get("embedding") is not None
                ]

                if not chunks_to_insert:
                    return 0

                await conn.executemany(
                    "INSERT INTO chunks (document_id, content, embedding, chunk_index, metadata, token_count) VALUES ($1, $2, $3, $4, $5, $6)",
                    chunks_to_insert,
                )
                return len(chunks_to_insert)
