# FICHIER: core/contracts/analyzer_contract.py
from abc import ABC, abstractmethod
from ingestion.orchestration.execution_context import ExecutionContext

class IAnalyzer(ABC):
    """Contrat pour un composant d'analyse qui enrichit l'ExecutionContext."""

    @abstractmethod
    async def analyze(self, context: ExecutionContext) -> ExecutionContext:
        """
        Analyse le contexte (souvent l'AST) et retourne le contexte enrichi.
        Chaque analyseur doit s'assurer de ne pas écraser les résultats
        des autres et d'ajouter ses propres découvertes.
        """
        pass