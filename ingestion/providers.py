"""
Flexible provider configuration for LLM and embedding models.
This module acts as a factory for creating provider-specific clients.
"""

import os
import logging
from typing import Optional, Any, Protocol, List
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
from .providers_google import GoogleAIEmbedder

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# --- Embedding Provider Abstraction ---

class EmbeddingProvider(Protocol):
    """
    Defines a common interface for all embedding providers.
    This ensures that the application can switch between providers seamlessly.
    """
    async def generate_embedding(self, text: str) -> List[float]:
        ...

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        ...

    def get_embedding_dimension(self) -> int:
        ...

# --- Provider Implementations ---

class OpenAIEmbedderWrapper:
    """
    Wrapper for OpenAI embedding client to conform to the EmbeddingProvider protocol.
    """
    def __init__(self, model_name: str, api_key: str, base_url: str):
        import openai  # Lazy import
        self.model_name = model_name
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        # Standardize on 1536 for OpenAI's text-embedding-3-small/large
        self.dimension = 1536

    async def generate_embedding(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(model=self.model_name, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return [0.0] * self.dimension

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            response = await self.client.embeddings.create(model=self.model_name, input=texts)
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            return [[0.0] * self.dimension for _ in texts]

    def get_embedding_dimension(self) -> int:
        return self.dimension

# --- Factory Functions ---

def get_llm_model(model_choice: Optional[str] = None) -> OpenAIModel:
    """
    Get LLM model configuration based on environment variables.
    This supports any OpenAI-compatible API.
    
    Args:
        model_choice: Optional override for model choice.
    
    Returns:
        Configured OpenAI-compatible model for use with Pydantic-AI.
    """
    llm_choice = model_choice or os.getenv('LLM_CHOICE', 'gpt-4-turbo-preview')
    base_url = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
    api_key = os.getenv('LLM_API_KEY') # No default for security
    
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is not set.")

    provider = OpenAIProvider(base_url=base_url, api_key=api_key)
    return OpenAIModel(llm_choice, provider=provider)


def get_embedder() -> EmbeddingProvider:
    """
    Factory function to get the configured embedding provider instance.
    This is the single point of entry for creating an embedder.

    Returns:
        An instance of a class that conforms to the EmbeddingProvider protocol.
    
    Raises:
        ValueError: If the provider is unsupported or API keys are missing.
    """
    provider_name = os.getenv('EMBEDDING_PROVIDER', 'openai').lower()
    api_key = os.getenv('EMBEDDING_API_KEY')
    
    if not api_key:
        raise ValueError("EMBEDDING_API_KEY environment variable is not set.")

    # CORRECTED: Accept 'gemini' as an alias for the 'google' provider.
    if provider_name in ('google', 'gemini'):
        from .providers_google import GoogleAIEmbedder
        model_name = os.getenv('EMBEDDING_MODEL', 'models/text-embedding-004')
        return GoogleAIEmbedder(model_name=model_name, api_key=api_key)
    
    elif provider_name == 'openai':
        base_url = os.getenv('EMBEDDING_BASE_URL', 'https://api.openai.com/v1')
        model_name = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        return OpenAIEmbedderWrapper(model_name=model_name, api_key=api_key, base_url=base_url)
        
    else:
        raise ValueError(f"Unsupported embedding provider: {provider_name}")


def get_ingestion_model() -> OpenAIModel:
    """
    Get ingestion-specific LLM model (can be faster/cheaper than main model).
    
    Returns:
        Configured model for ingestion tasks.
    """
    ingestion_choice = os.getenv('INGESTION_LLM_CHOICE')
    
    # If no specific ingestion model, use the main model
    if not ingestion_choice:
        return get_llm_model()
    
    return get_llm_model(model_choice=ingestion_choice)


def get_model_info() -> dict:
    """
    Get information about current model configuration.
    
    Returns:
        Dictionary with model configuration info.
    """
    provider_name = os.getenv('EMBEDDING_PROVIDER', 'openai').lower()
    embedder = get_embedder()
    
    return {
        "llm_provider": os.getenv('LLM_PROVIDER', 'openai'),
        "llm_model": os.getenv('LLM_CHOICE'),
        "llm_base_url": os.getenv('LLM_BASE_URL'),
        "embedding_provider": provider_name,
        "embedding_model": os.getenv('EMBEDDING_MODEL'),
        "embedding_base_url": os.getenv('EMBEDDING_BASE_URL', 'N/A if not Google/OpenAI'),
        "embedding_dimension": embedder.get_embedding_dimension(),
        "ingestion_model": os.getenv('INGESTION_LLM_CHOICE', 'same as main'),
    }

def validate_configuration() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    required_vars = ['LLM_API_KEY', 'LLM_CHOICE', 'EMBEDDING_API_KEY', 'EMBEDDING_MODEL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    try:
        get_embedder()
        get_llm_model()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False
        
    return True