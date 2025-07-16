# NOUVEAU FICHIER: analyzer-engine/services/ingestion_service.py
import logging
import os
from typing import List, Callable, Awaitable
from ingestion.orchestration.pipeline_director import PipelineDirector

logger = logging.getLogger(__name__)


class IngestionService:
    """Service encapsulant la logique d'ingestion pour la rendre réutilisable."""

    def __init__(self, status_callback: Callable[[dict], Awaitable[None]]):
        self.director = PipelineDirector(status_callback=status_callback)
        self.status_callback = status_callback

    async def run_ingestion_for_job(self, job_id: str, file_paths: List[str]):
        logger.info(f"[{job_id}] Starting ingestion for {len(file_paths)} files.")
        await self.status_callback(
            {
                "job_id": job_id,
                "type": "status",
                "status": "RUNNING",
                "message": f"Starting ingestion for {len(file_paths)} files.",
            }
        )

        for i, file_path in enumerate(file_paths):
            if not os.path.exists(file_path):
                logger.error(f"[{job_id}] File not found: {file_path}")
                await self.status_callback(
                    {
                        "job_id": job_id,
                        "type": "log",
                        "level": "error",
                        "message": f"File not found: {file_path}. Skipping.",
                    }
                )
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()

                log_message = f"({i+1}/{len(file_paths)}) Processing: {os.path.basename(file_path)}"
                logger.info(f"[{job_id}] {log_message}")
                await self.status_callback(
                    {
                        "job_id": job_id,
                        "type": "log",
                        "level": "info",
                        "message": log_message,
                    }
                )

                language = "python" if file_path.endswith(".py") else "unknown"
                await self.director.process(
                    file_path=file_path,
                    source_code=source_code,
                    language=language,
                    job_id=job_id,
                )
            except Exception as e:
                error_message = f"Failed to process {file_path}: {e}"
                logger.error(f"[{job_id}] {error_message}", exc_info=True)
                await self.status_callback(
                    {
                        "job_id": job_id,
                        "type": "log",
                        "level": "error",
                        "message": error_message,
                    }
                )

        final_message = "Ingestion job completed."
        logger.info(f"[{job_id}] {final_message}")
        await self.status_callback(
            {
                "job_id": job_id,
                "type": "status",
                "status": "SUCCESS",
                "message": final_message,
            }
        )
