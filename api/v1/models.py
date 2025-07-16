# FICHIER MODIFIÉ: api/v1/models.py
from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Modèle de données pour le statut de santé du système."""

    postgres_status: str
    graph_db_status: str
    document_count: int
    chunk_count: int


class IngestionResponse(BaseModel):
    """Modèle de réponse pour la création d'un job d'ingestion."""

    job_id: str
    message: str
    websocket_url: str
