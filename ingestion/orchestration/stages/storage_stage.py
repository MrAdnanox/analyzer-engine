# FICHIER MODIFIÉ: analyzer-engine/ingestion/orchestration/stages/storage_stage.py
import logging
from datetime import datetime
from typing import Optional, Callable, Awaitable

from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext

# ======================= CORRECTION ELITE =======================
# L'étape ne crée plus ses propres dépendances. Elle les recevra.
# from ...storage.repositories.sqlite_graph_repository import SQLiteGraphRepository
# from ...storage.repositories.postgres_repository import PostgresRepository
from core.contracts.repository_contract import ICodeRepository
from core.contracts.vector_repository_contract import IVectorRepository

logger = logging.getLogger(__name__)


class StorageStage(IPipelineStage):
    """Étape responsable de la persistance des données via les repositories."""

    def __init__(
        self,
        code_repo: ICodeRepository,
        vector_repo: IVectorRepository,
        status_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ):
        super().__init__(status_callback)
        # Les dépendances sont maintenant injectées.
        self.code_repo = code_repo
        self.vector_repo = vector_repo

    async def execute(self, context: ExecutionContext, job_id: str) -> ExecutionContext:
        # ... le reste de la méthode execute reste identique ...
        # Elle utilise self.code_repo et self.vector_repo qui ont été injectés.
        logger.info(f"StorageStage: Storing data for {context.file_path}")

        if self.status_callback:
            await self.status_callback(
                {
                    "job_id": job_id,
                    "type": "log",
                    "level": "info",
                    "message": f"Storing knowledge graph for {context.file_path}...",
                }
            )

        document_metadata = {
            "language": context.language,
            "entity_count": len(context.entities),
            "relationship_count": len(context.relationships),
            "chunk_count": len(context.chunks),
            "ingested_at": datetime.utcnow().isoformat(),
        }

        file_data = {
            "file_path": context.file_path,
            "entities": context.entities,
            "relationships": context.relationships,
        }
        await self.code_repo.add_code_structure(file_data)

        if self.status_callback:
            await self.status_callback(
                {
                    "job_id": job_id,
                    "type": "log",
                    "level": "info",
                    "message": f"Storing vector chunks for {context.file_path}...",
                }
            )

        document_content = f"Code container for {context.file_path}"
        await self.vector_repo.save_document_with_chunks(
            context.file_path, document_content, context.chunks, document_metadata
        )

        return context
