# FICHIER MODIFIÉ: analyzer-engine/ingestion/orchestration/pipeline_director.py
import logging
from typing import List, Optional, Callable, Awaitable

from .stages.base_stage import IPipelineStage
from .execution_context import ExecutionContext
from .stages.parsing_stage import ParsingStage
from .stages.analysis_stage import AnalysisStage
from .stages.chunking_embedding_stage import ChunkingEmbeddingStage
from .stages.storage_stage import StorageStage

# ======================= CORRECTION ELITE =======================
# Le directeur a maintenant besoin des repositories pour les injecter dans la StorageStage.
from ingestion.storage.repositories.postgres_repository import PostgresRepository
from ingestion.storage.repositories.sqlite_graph_repository import SQLiteGraphRepository
from api.dependencies import get_db_pool  # Pour créer le repo postgres

logger = logging.getLogger(__name__)


class PipelineDirector:
    """Le chef d'orchestre : construit et exécute le pipeline."""

    def __init__(
        self, status_callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ):
        self.status_callback = status_callback
        # L'initialisation des étapes est déplacée dans une méthode async
        # car elle a maintenant besoin d'attendre la création du pool de BDD.
        self.pipeline: List[IPipelineStage] = []

    async def initialize_pipeline(self):
        """Initialise le pipeline de manière asynchrone."""
        if self.pipeline:
            return

        # Crée les dépendances nécessaires pour les étapes
        db_pool = await get_db_pool()
        vector_repo = PostgresRepository(db_pool)
        code_repo = SQLiteGraphRepository()
        await code_repo.initialize()  # SQLite a besoin d'une initialisation manuelle

        self.pipeline = [
            ParsingStage(self.status_callback),
            AnalysisStage(self.status_callback),
            ChunkingEmbeddingStage(self.status_callback),
            # Injecte les dépendances dans la StorageStage
            StorageStage(code_repo, vector_repo, self.status_callback),
        ]
        logger.info(f"PipelineDirector initialized with {len(self.pipeline)} stages.")

    async def process(
        self, file_path: str, source_code: str, language: str, job_id: str
    ):
        """Démarre et exécute le pipeline complet pour un fichier donné."""
        # S'assure que le pipeline est initialisé
        await self.initialize_pipeline()

        context = ExecutionContext(
            file_path=file_path, source_code=source_code, language=language
        )

        logger.info(f"PipelineDirector: Starting process for {context.file_path}...")
        for i, stage in enumerate(self.pipeline):
            stage_name = stage.__class__.__name__
            logger.info(
                f"--- [{job_id}] Executing Stage {i+1}/{len(self.pipeline)}: {stage_name} ---"
            )
            context = await stage.execute(context, job_id)

        logger.info(f"PipelineDirector: Process finished for {context.file_path}.")
        return context
