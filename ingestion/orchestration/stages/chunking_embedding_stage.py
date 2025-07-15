# Fichier : analyzer-engine/ingestion/orchestration/stages/chunking_embedding_stage.py

import logging

# ========================= AJOUTER CET IMPORT =========================
from dataclasses import asdict

# ======================================================================
from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext
from ...chunker import SimpleChunker
from ...embedder import create_embedder
from core.models.db import IngestionConfig

logger = logging.getLogger(__name__)


class ChunkingEmbeddingStage(IPipelineStage):
    """Étape responsable du chunking et de la génération des embeddings."""

    def __init__(self):
        self.config = IngestionConfig()
        self.chunker = SimpleChunker(self.config)
        self.embedder = create_embedder()

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        logger.info(
            f"ChunkingEmbeddingStage: Processing {len(context.entities)} entities from {context.file_path}"
        )

        doc_chunks = self.chunker.chunk_from_entities(
            entities=context.entities, file_path=context.file_path
        )

        embedded_chunks = await self.embedder.embed_chunks(doc_chunks)

        context.chunks = [asdict(chunk) for chunk in embedded_chunks]
        # ==============================================================================

        logger.info(f"Generated {len(context.chunks)} embedded chunks.")
        return context
