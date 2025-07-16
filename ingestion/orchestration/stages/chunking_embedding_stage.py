# FICHIER MODIFIÉ: analyzer-engine/ingestion/orchestration/stages/chunking_embedding_stage.py

import logging
from dataclasses import asdict
from typing import Optional, Callable, Awaitable  # <-- AJOUTER LES IMPORTS

from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext
from ...chunker import SimpleChunker
from ...embedder import create_embedder
from core.models.db import IngestionConfig

logger = logging.getLogger(__name__)


class ChunkingEmbeddingStage(IPipelineStage):
    """Étape responsable du chunking et de la génération des embeddings."""

    # ======================= CORRECTION ELITE =======================
    # Le constructeur est maintenant aligné sur celui de la classe parente IPipelineStage.
    # Il accepte le status_callback, même s'il ne l'utilise pas directement dans cette étape.
    # Cela garantit la cohérence de l'instanciation dans le PipelineDirector.
    # ================================================================
    def __init__(
        self, status_callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ):
        super().__init__(status_callback)
        self.config = IngestionConfig()
        self.chunker = SimpleChunker(self.config)
        self.embedder = create_embedder()

    async def execute(self, context: ExecutionContext, job_id: str) -> ExecutionContext:
        logger.info(
            f"ChunkingEmbeddingStage: Processing {len(context.entities)} entities from {context.file_path}"
        )

        doc_chunks = self.chunker.chunk_from_entities(
            entities=context.entities, file_path=context.file_path
        )

        # Ici, on pourrait utiliser self.status_callback pour notifier de la progression de l'embedding
        # par exemple en passant un callback à embed_chunks. Pour l'instant, on le garde simple.
        embedded_chunks = await self.embedder.embed_chunks(doc_chunks)

        context.chunks = [asdict(chunk) for chunk in embedded_chunks]

        logger.info(f"Generated {len(context.chunks)} embedded chunks.")

        # Exemple d'utilisation du callback
        if self.status_callback:
            await self.status_callback(
                {
                    "job_id": job_id,
                    "type": "log",
                    "level": "info",
                    "message": f"Generated {len(context.chunks)} embedded chunks for {context.file_path}.",
                }
            )

        return context
