# FICHIER MODIFIÉ: analyzer-engine/ingestion/orchestration/stages/parsing_stage.py
from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext
from ingestion.parsing.parser_registry import parser_registry
import logging  # <-- AJOUTER L'IMPORT

logger = logging.getLogger(__name__)  # <-- AJOUTER LE LOGGER


class ParsingStage(IPipelineStage):
    """Étape responsable du parsing du code source."""

    async def execute(self, context: ExecutionContext, job_id: str) -> ExecutionContext:
        logger.info(f"Parsing source code for {context.file_path}")
        parser = parser_registry.get_parser(context.language)
        normalized_ast = await parser.parse(context.source_code)
        context.normalized_ast = normalized_ast
        logger.info(f"AST generated for language {context.language}")
        return context
