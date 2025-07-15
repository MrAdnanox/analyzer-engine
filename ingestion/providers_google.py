"""
Google AI provider implementation for embeddings.
"""

import os
import logging
from typing import List, Optional
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# As per Google's documentation, the new model is text-embedding-004
# https://ai.google.dev/docs/embeddings/migration-guide
# It produces 768 dimensions, so we will standardize on this.
# This is a key architectural decision to resolve the dimension mismatch.
EMBEDDING_DIMENSION = 768
# The model name in the SDK is different from the API identifier
SDK_MODEL_NAME = "models/text-embedding-004"


class GoogleAIEmbedder:
    """
    Wrapper for Google AI (Gemini) embedding model.
    Implements a common interface for embedding generation.
    """

    def __init__(self, model_name: str = SDK_MODEL_NAME, api_key: Optional[str] = None):
        """
        Initializes the Google AI embedder.

        Args:
            model_name (str): The model name to use, e.g., 'models/text-embedding-004'.
            api_key (Optional[str]): The API key. Defaults to EMBEDDING_API_KEY env var.
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google AI API key not found in EMBEDDING_API_KEY env var."
            )

        # Configure the genai library
        genai.configure(api_key=self.api_key)
        self.dimension = EMBEDDING_DIMENSION

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text (str): The text to embed.

        Returns:
            List[float]: The embedding vector.
        """
        try:
            # genai.embed_content is synchronous, so we run it in an executor
            # to avoid blocking the asyncio event loop.
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,  # Uses the default ThreadPoolExecutor
                lambda: genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document",  # or "retrieval_query"
                ),
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Google AI embedding for single text failed: {e}")
            # Return a zero vector on failure, matching the dimension.
            return [0.0] * self.dimension

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts (List[str]): A list of texts to embed.

        Returns:
            List[List[float]]: A list of embedding vectors.
        """
        try:
            # genai.embed_content handles batching internally.
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=self.model_name, content=texts, task_type="retrieval_document"
                ),
            )
            return [e for e in result["embedding"]]
        except Exception as e:
            logger.error(f"Google AI embedding batch failed: {e}")
            # Fallback to zero vectors for the entire failed batch.
            return [[0.0] * self.dimension for _ in texts]

    def get_embedding_dimension(self) -> int:
        """
        Returns the embedding dimension for the model.

        Returns:
            int: The vector dimension size.
        """
        return self.dimension
