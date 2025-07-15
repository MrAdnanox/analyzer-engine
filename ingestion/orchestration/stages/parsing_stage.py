# analyzer-engine/ingestion/orchestration/stages/parsing_stage.py
from .base_stage import IPipelineStage
from ..execution_context import ExecutionContext
from ingestion.parsing.parser_registry import parser_registry


class ParsingStage(IPipelineStage):
    """Étape responsable du parsing du code source."""

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        parser = parser_registry.get_parser(context.language)
        normalized_ast = await parser.parse(context.source_code)
        context.normalized_ast = normalized_ast
        print(f"ParsingStage: AST généré pour le langage {context.language}")
        return context
