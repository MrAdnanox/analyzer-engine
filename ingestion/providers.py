# FICHIER: analyzer-engine/ingestion/providers.py (MODIFIÉ)
import os
import logging
from typing import Optional
from dotenv import load_dotenv

from core.contracts.provider_contracts import EmbeddingProvider, LLMProvider
from .providers_google import GoogleEmbeddingProvider, GoogleLLMProvider
from .providers_mocks import MockEmbeddingProvider, MockLLMProvider

load_dotenv()
logger = logging.getLogger(__name__)

# Cache pour les instances de fournisseurs (Singleton pattern)
_embedder_instance: Optional[EmbeddingProvider] = None
_llm_instance: Optional[LLMProvider] = None
_ingestion_llm_instance: Optional[LLMProvider] = None


def get_embedder() -> EmbeddingProvider:
    """Factory pour le fournisseur d'embedding."""
    global _embedder_instance
    if _embedder_instance is None:
        if os.getenv("APP_ENV") == "test":
            logger.warning("RUNNING IN TEST MODE: Using MockEmbeddingProvider")
            _embedder_instance = MockEmbeddingProvider()
        else:
            provider_name = os.getenv("EMBEDDING_PROVIDER", "google").lower()
            if provider_name == "google":
                _embedder_instance = GoogleEmbeddingProvider()
            else:
                raise ValueError(f"Unsupported embedding provider: {provider_name}")
    return _embedder_instance


def get_llm() -> LLMProvider:
    """Factory pour le fournisseur LLM principal."""
    global _llm_instance
    if _llm_instance is None:
        if os.getenv("APP_ENV") == "test":
            logger.warning("RUNNING IN TEST MODE: Using MockLLMProvider for main LLM")
            _llm_instance = MockLLMProvider()
        else:
            provider_name = os.getenv("LLM_PROVIDER", "google").lower()
            if provider_name == "google":
                _llm_instance = GoogleLLMProvider(model_choice=os.getenv("LLM_CHOICE"))
            else:
                raise ValueError(f"Unsupported LLM provider: {provider_name}")
    return _llm_instance


def get_ingestion_model() -> LLMProvider:
    """Factory pour le fournisseur LLM utilisé durant l'ingestion (ex: chunking sémantique)."""
    global _ingestion_llm_instance
    if _ingestion_llm_instance is None:
        if os.getenv("APP_ENV") == "test":
            logger.warning("RUNNING IN TEST MODE: Using MockLLMProvider for ingestion")
            _ingestion_llm_instance = MockLLMProvider()
        else:
            provider_name = os.getenv("LLM_PROVIDER", "google").lower()
            if provider_name == "google":
                _ingestion_llm_instance = GoogleLLMProvider(
                    model_choice=os.getenv("INGESTION_LLM_CHOICE")
                )
            else:
                raise ValueError(
                    f"Unsupported LLM provider for ingestion: {provider_name}"
                )
    return _ingestion_llm_instance
