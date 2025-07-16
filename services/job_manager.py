# FICHIER MODIFIÉ: services/job_manager.py
import uuid
from typing import Dict, List
from core.models.service_models import IngestionJob


class JobManager:
    """Gère l'état des jobs d'ingestion en mémoire."""

    def __init__(self):
        self.jobs: Dict[str, IngestionJob] = {}

    def create_job(self, files: List[str]) -> IngestionJob:
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            job_id=job_id,
            status="PENDING",
            details="Job has been created and is waiting to start.",
            files=files,
        )
        self.jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> IngestionJob | None:
        return self.jobs.get(job_id)

    def update_job_status(self, job_id: str, status: str, details: str):
        if job := self.get_job(job_id):
            job.status = status
            job.details = details
