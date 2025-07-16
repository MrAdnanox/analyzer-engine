# FICHIER MODIFIÉ: analyzer-engine/ingestion/orchestration/stages/base_stage.py
from abc import ABC, abstractmethod
from ..execution_context import ExecutionContext
from typing import Optional, Callable, Awaitable


class IPipelineStage(ABC):
    def __init__(
        self, status_callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ):
        self.status_callback = status_callback

    @abstractmethod
    async def execute(self, context: ExecutionContext, job_id: str) -> ExecutionContext:
        pass
