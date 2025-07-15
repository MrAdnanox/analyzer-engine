# analyzer-engine/ingestion/parsing/parsers/python_parser.py
import ast

from core.contracts.parser_contract import IParser
from core.models.ast_models import NormalizedAST, ASTNode

class PythonParser(IParser):
    """Implémentation du contrat IParser pour le langage Python."""

    def supports_language(self, language: str) -> bool:
        return language.lower() == "python"

    async def parse(self, code: str) -> NormalizedAST:
        """Parse le code Python en utilisant le module natif `ast`."""
        try:
            native_ast = ast.parse(code)
            root_node = self._transform_node(native_ast)
            return NormalizedAST(root=root_node, language="python")
        except SyntaxError as e:
            # Idéalement, lever une exception de notre `core.exceptions`
            raise ValueError(f"Python syntax error: {e}")

    def _transform_node(self, node: ast.AST) -> ASTNode:
        """Transforme récursivement un nœud AST natif en notre ASTNode normalisé."""
        node_type = node.__class__.__name__
        name = self._extract_name(node)
        
        children = [self._transform_node(child) for child in ast.iter_child_nodes(node)]
        
        return ASTNode(
            node_type=node_type,
            name=name,
            children=children,
            metadata={
                "lineno": getattr(node, 'lineno', -1),
                "col_offset": getattr(node, 'col_offset', -1)
            }
        )

    def _extract_name(self, node: ast.AST) -> str:
        """Extrait un nom significatif du nœud AST."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return node.name
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""