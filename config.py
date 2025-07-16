# FICHIER MODIFIÉ: analyzer-engine/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration centralisée et validée pour l'application.
    Pydantic lit automatiquement les variables depuis le fichier .env.
    """

    # 1. Base de Données (PostgreSQL)
    DATABASE_URL: str

    # 2. Knowledge Graph (Neo4j)
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # 3. Fournisseur LLM (Google Gemini)
    LLM_PROVIDER: str = "google"
    LLM_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    LLM_API_KEY: str
    LLM_CHOICE: str = "gemini-1.5-flash"

    # 4. Fournisseur d'Embedding (Google Gemini)
    EMBEDDING_PROVIDER: str = "google"
    EMBEDDING_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    EMBEDDING_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-004"

    # 5. Configuration de l'Ingestion
    INGESTION_LLM_CHOICE: str = "gemini-1.5-flash"

    # 6. Configuration de l'Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_PORT: int = 8058
    DEBUG_MODE: bool = False

    # 7. Configuration Vector Search
    VECTOR_DIMENSION: int = 768
    MAX_SEARCH_RESULTS: int = 10

    # 8. Autres configurations
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    SESSION_TIMEOUT_MINUTES: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instanciation unique qui sera utilisée dans toute l'application
settings = Settings()
