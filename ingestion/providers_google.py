# FICHIER: analyzer-engine/ingestion/providers_google.py (CONTENU RESTAURÉ)
import os
import logging
from typing import List
import google.generativeai as genai
from core.contracts.provider_contracts import EmbeddingProvider, LLMProvider

logger = logging.getLogger(__name__)


class GoogleEmbeddingProvider(EmbeddingProvider):
    """Implémentation pour les embeddings de Google (Gemini)."""

    def __init__(self):
        self.api_key = os.getenv("EMBEDDING_API_KEY")
        if not self.api_key:
            raise ValueError("EMBEDDING_API_KEY is not set.")
        genai.configure(api_key=self.api_key)
        self.model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        self.dimension = 768  # Dimension pour text-embedding-004

    async def generate_embedding(self, text: str) -> List[float]:
        return genai.embed_content(model=self.model_name, content=text)["embedding"]

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        result = genai.embed_content(model=self.model_name, content=texts)
        return result["embedding"]

    def get_embedding_dimension(self) -> int:
        return self.dimension


class GoogleLLMProvider(LLMProvider):
    """Implémentation pour les LLMs de Google (Gemini)."""

    def __init__(self, model_choice: str = None):
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("LLM_API_KEY is not set.")
        genai.configure(api_key=self.api_key)
        self.model_name = model_choice or os.getenv("LLM_CHOICE", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(self.model_name)

    async def generate_text(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048
    ) -> str:
        config = {"temperature": temperature, "max_output_tokens": max_tokens}
        response = await self.model.generate_content_async(
            prompt, generation_config=genai.types.GenerationConfig(**config)
        )
        return response.text
