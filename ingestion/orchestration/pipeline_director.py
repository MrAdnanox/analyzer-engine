# analyzer-engine/ingestion/orchestration/pipeline_director.py
import logging
from typing import List
from .stages.base_stage import IPipelineStage
from .execution_context import ExecutionContext
from .stages.parsing_stage import ParsingStage
from .stages.analysis_stage import AnalysisStage
from .stages.chunking_embedding_stage import ChunkingEmbeddingStage
from .stages.storage_stage import StorageStage

logger = logging.getLogger(__name__)

class PipelineDirector:
    """Le chef d'orchestre : construit et exécute le pipeline."""

    def __init__(self):
        # Le pipeline est maintenant enrichi. L'ordre est crucial.
        self.pipeline: List[IPipelineStage] = [
            ParsingStage(), # <-- MODIFICATION: Étape maintenant activée !
            AnalysisStage(),
            ChunkingEmbeddingStage(),
            StorageStage(),
        ]
        logger.info(f"PipelineDirector initialized with {len(self.pipeline)} stages.")

    async def process(self, file_path: str, source_code: str, language: str):
        """Démarre et exécute le pipeline complet pour un fichier donné."""
        context = ExecutionContext(file_path=file_path, source_code=source_code, language=language)
        
        logger.info(f"PipelineDirector: Starting process for {context.file_path}...")
        for i, stage in enumerate(self.pipeline):
            stage_name = stage.__class__.__name__
            logger.info(f"--- Executing Stage {i+1}/{len(self.pipeline)}: {stage_name} ---")
            context = await stage.execute(context)
        
        logger.info(f"PipelineDirector: Process finished for {context.file_path}.")
        return context