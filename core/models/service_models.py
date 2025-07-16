# NOUVEAU FICHIER: core/models/service_models.py
from pydantic import BaseModel
from typing import List


class IngestionJob(BaseModel):
    """
    Modèle de données pour un job d'ingestion.
    Réside dans `core` car il est partagé entre la couche service et la couche API.
    """

    job_id: str
    status: str
    details: str
    files: List[str]
