# FICHIER MODIFIÉ: analyzer-engine/ingestion/orchestration/stages/analysis_stage.py
import logging
from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext
from ingestion.analysis.analyzer_registry import analyzer_registry

logger = logging.getLogger(__name__)


class AnalysisStage(IPipelineStage):
    """
    Étape d'orchestration qui exécute tous les analyseurs enregistrés
    sur le contexte d'exécution.
    """

    async def execute(self, context: ExecutionContext, job_id: str) -> ExecutionContext:
        logger.info(
            f"AnalysisStage: Running all registered analyzers on {context.file_path}"
        )
        # ... (le reste de la méthode est déjà correct)
        context.entities = []
        context.relationships = []

        registered_analyzers = analyzer_registry.get_analyzers()
        logger.info(f"Found {len(registered_analyzers)} analyzers to execute.")

        for analyzer in registered_analyzers:
            context = await analyzer.analyze(context)

        logger.info(
            f"Analysis complete. Total entities: {len(context.entities)}, Total relationships: {len(context.relationships)}."
        )
        return context
