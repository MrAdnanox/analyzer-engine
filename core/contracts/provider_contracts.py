# FICHIER: analyzer-engine/core/contracts/provider_contracts.py
from typing import List, Protocol


class EmbeddingProvider(Protocol):
    """Définit une interface commune pour tous les fournisseurs d'embedding."""

    async def generate_embedding(self, text: str) -> List[float]: ...

    async def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[List[float]]: ...

    def get_embedding_dimension(self) -> int: ...


class LLMProvider(Protocol):
    """Définit une interface commune pour tous les fournisseurs de LLM."""

    async def generate_text(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024
    ) -> str: ...
