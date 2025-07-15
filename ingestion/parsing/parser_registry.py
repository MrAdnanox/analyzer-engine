# analyzer-engine/ingestion/parsing/parser_registry.py
from typing import List, Type
from core.contracts.parser_contract import IParser
from .parsers.python_parser import PythonParser # <-- MODIFICATION: Import

class ParserRegistry:
    """Registre pour trouver le parseur adéquat."""
    def __init__(self):
        self._parsers: List[IParser] = []

    def register(self, parser: IParser):
        self._parsers.append(parser)

    def get_parser(self, language: str) -> IParser:
        for parser in self._parsers:
            if parser.supports_language(language):
                return parser
        raise ValueError(f"No parser found for language: {language}")


# Registre "singleton"
parser_registry = ParserRegistry()
# <-- MODIFICATION: Enregistrement du parseur Python au démarrage
parser_registry.register(PythonParser())