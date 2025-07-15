# FICHIER: analyzer-engine/ingestion/providers_mocks.py (MODIFIÉ)
from typing import List


class MockEmbeddingProvider:
    """Un faux client d'embedding qui ne fait pas d'appel réseau."""

    def get_embedding_dimension(self) -> int:
        # La dimension doit correspondre à celle du modèle Gemini utilisé (text-embedding-004)
        return 768

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self.get_embedding_dimension() for _ in texts]

    async def generate_embedding(self, text: str) -> List[float]:
        return [0.0] * self.get_embedding_dimension()


class MockLLMProvider:
    """Un faux client LLM qui ne fait pas d'appel réseau, conforme au contrat LLMProvider."""

    async def generate_text(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024
    ) -> str:
        # Retourne une réponse prévisible et instantanée pour les tests.
        return "Mocked LLM response for semantic chunking."
