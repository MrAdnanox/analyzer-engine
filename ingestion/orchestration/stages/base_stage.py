# analyzer-engine/ingestion/orchestration/stages/base_stage.py
from abc import ABC, abstractmethod
from ..execution_context import ExecutionContext

class IPipelineStage(ABC):
    """Contrat pour une étape de la chaîne de montage."""
    
    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """Exécute la logique de l'étape et retourne le contexte mis à jour."""
        pass