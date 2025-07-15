# FICHIER: ingestion/analysis/processors/ast_entity_extractor.py
import logging
from core.contracts.analyzer_contract import IAnalyzer
from ingestion.orchestration.execution_context import ExecutionContext
from core.models.ast_models import ASTNode

logger = logging.getLogger(__name__)

class ASTEntityExtractor(IAnalyzer):
    """
    Analyseur spécialisé dans l'extraction des entités (classes, fonctions)
    et de leurs relations de base à partir de l'AST.
    """
    async def analyze(self, context: ExecutionContext) -> ExecutionContext:
        logger.info("ASTEntityExtractor: Analyzing AST for entities and relationships.")
        if not context.normalized_ast:
            logger.warning("No AST found, skipping entity extraction.")
            return context

        entities = []
        relationships = []

        # 1. Créer une entité pour le fichier lui-même.
        file_entity_name = context.file_path
        entities.append({
            "type": "FILE",
            "name": file_entity_name,
            "source_code": context.source_code
        })

        # 2. Parcourir l'AST pour trouver les autres entités.
        self._traverse_ast(
            node=context.normalized_ast.root,
            entities=entities,
            relationships=relationships,
            file_entity_name=file_entity_name
        )

        # Assurez-vous d'ajouter les résultats au contexte au lieu de les remplacer.
        context.entities.extend(entities)
        context.relationships.extend(relationships)

        logger.info(f"ASTEntityExtractor: Found {len(entities)} entities and {len(relationships)} relationships.")
        return context

    def _traverse_ast(self, node: ASTNode, entities: list, relationships: list, file_entity_name: str):
        """Parcourt l'AST pour trouver des entités et des relations simples."""
        if node.node_type in ("FunctionDef", "AsyncFunctionDef", "ClassDef"):
            entity_type_map = {
                "FunctionDef": "FUNCTION",
                "AsyncFunctionDef": "FUNCTION",
                "ClassDef": "CLASS",
            }
            entity_name = node.name
            entities.append({
                "type": entity_type_map[node.node_type],
                "name": entity_name,
                "source_code": f"# Source code for {entity_name} would be extracted here"
            })

            relationships.append({
                "source": entity_name,
                "target": file_entity_name,
                "type": "DEFINES_IN_FILE"
            })

        for child in node.children:
            self._traverse_ast(child, entities, relationships, file_entity_name)