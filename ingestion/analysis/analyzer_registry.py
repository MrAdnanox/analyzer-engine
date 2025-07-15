# FICHIER: ingestion/analysis/analyzer_registry.py
from typing import List
from core.contracts.analyzer_contract import IAnalyzer
from .processors.ast_entity_extractor import ASTEntityExtractor


class AnalyzerRegistry:
    def __init__(self):
        self._analyzers: List[IAnalyzer] = []

    def register(self, analyzer: IAnalyzer):
        self._analyzers.append(analyzer)

    def get_analyzers(self) -> List[IAnalyzer]:
        return self._analyzers


# Registre "singleton" pour l'application
analyzer_registry = AnalyzerRegistry()

# Enregistrement des analyseurs au démarrage de l'application
analyzer_registry.register(ASTEntityExtractor())
