# analyzer-engine/ingestion/orchestration/stages/storage_stage.py
import logging
from datetime import datetime
from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext
from ...storage.repositories.sqlite_graph_repository import SQLiteGraphRepository
from ...storage.repositories.postgres_repository import PostgresRepository

logger = logging.getLogger(__name__)


class StorageStage(IPipelineStage):
    """Étape responsable de la persistance des données via les repositories."""

    def __init__(self):
        self.code_repo = SQLiteGraphRepository()
        self.vector_repo = PostgresRepository()

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        logger.info(f"StorageStage: Storing data for {context.file_path}")

        # 1. Assembler un dictionnaire de métadonnées riche pour le document.
        document_metadata = {
            "language": context.language,
            "entity_count": len(context.entities),
            "relationship_count": len(context.relationships),
            "chunk_count": len(context.chunks),
            "ingested_at": datetime.utcnow().isoformat(),
        }

        # Stockage du graphe
        file_data = {
            "file_path": context.file_path,
            "entities": context.entities,
            "relationships": context.relationships,
        }
        graph_result = await self.code_repo.add_code_structure(file_data)
        logger.info(f"Graph storage result: {graph_result}")

        # Stockage vectoriel
        document_content = f"Code container for {context.file_path}"
        chunks_saved = await self.vector_repo.save_document_with_chunks(
            context.file_path, document_content, context.chunks, document_metadata
        )
        logger.info(f"Vector storage: {chunks_saved} chunks saved.")

        return context
