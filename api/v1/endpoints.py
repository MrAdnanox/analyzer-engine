# analyzer-engine/api/v1/endpoints.py
import os
import logging
import tempfile
from typing import List
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Depends,
    status,
)

from api.v1.models import HealthStatus, IngestionResponse
from services.job_manager import JobManager
from services.websocket_manager import WebSocketManager
from services.ingestion_service import IngestionService
from ingestion.storage.repositories.postgres_repository import PostgresRepository
from ingestion.storage.repositories.sqlite_graph_repository import SQLiteGraphRepository
from api.dependencies import (
    get_postgres_repo,
    get_sqlite_repo,
    get_job_manager,
    get_websocket_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Ensemble des origines autorisées pour les WebSockets.
# Essentiel pour la sécurité.
ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}


# Cette fonction, supprimée par le linter, est le cœur de l'exécution asynchrone.
async def run_ingestion_background(
    job_id: str,
    file_paths: List[str],
    job_manager: JobManager,
    websocket_manager: WebSocketManager,
):
    """Wrapper pour lancer le service d'ingestion en arrière-plan."""

    async def status_callback(message: dict):
        """Callback pour mettre à jour et diffuser le statut du job via WebSocket."""
        job = job_manager.get_job(job_id)
        if job:
            # Met à jour l'état en mémoire du job.
            job_manager.update_job_status(
                job_id, message.get("status", job.status), message["message"]
            )
        # Diffuse le message à tous les clients connectés pour ce job.
        await websocket_manager.broadcast_to_job(job_id, message)

    ingestion_service = IngestionService(status_callback)
    await ingestion_service.run_ingestion_for_job(job_id, file_paths)


# Cet endpoint complet, supprimé par le linter, est le point d'entrée de toute l'opération.
@router.post(
    "/ingest", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED
)
async def ingest_files(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    job_manager: JobManager = Depends(get_job_manager),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """Endpoint pour démarrer un job d'ingestion avec un ou plusieurs fichiers."""
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    file_names = []
    for file in files:
        # Utilisation de os.path.basename pour la sécurité, évite les path traversal.
        filename = os.path.basename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        file_paths.append(file_path)
        file_names.append(filename)

    job = job_manager.create_job(files=file_names)

    # La tâche est ajoutée à l'arrière-plan, permettant une réponse immédiate.
    background_tasks.add_task(
        run_ingestion_background, job.job_id, file_paths, job_manager, websocket_manager
    )

    # Génère l'URL WebSocket correcte que le client doit utiliser.
    websocket_url = str(
        request.url_for("websocket_endpoint", job_id=job.job_id)
    ).replace("http", "ws")

    return IngestionResponse(
        job_id=job.job_id,
        message="Ingestion job started in the background.",
        websocket_url=websocket_url,
    )


@router.get("/health", response_model=HealthStatus)
async def get_health_status(
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
    sqlite_repo: SQLiteGraphRepository = Depends(get_sqlite_repo),
):
    """Endpoint pour vérifier la santé des services dépendants ET l'état des données."""
    pg_status = "Error"
    graph_status = "Error"
    doc_count = 0
    chk_count = 0

    try:
        async with postgres_repo._get_connection() as conn:
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            chk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
        pg_status = "OK"
    except Exception as e:
        logger.error(f"Health check failed for PostgreSQL: {e}")
        pg_status = "Error"

    try:
        await sqlite_repo.find_entity_relationships("health_check_test")
        graph_status = "OK"
    except Exception as e:
        logger.error(f"Health check failed for SQLite Graph DB: {e}")
        graph_status = "Error"

    return HealthStatus(
        postgres_status=pg_status,
        graph_db_status=graph_status,
        document_count=doc_count,
        chunk_count=chk_count,
    )


@router.websocket("/ws/jobs/{job_id}/status", name="websocket_endpoint")
async def websocket_endpoint(
    websocket: WebSocket,
    job_id: str,
    websocket_manager: WebSocketManager = Depends(get_websocket_manager),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Endpoint WebSocket pour le suivi en temps réel d'un job."""

    origin = websocket.headers.get("origin")
    logger.info(
        f"[WEBSOCKET-AUTH] Connection attempt for job {job_id} from origin: {origin}. Headers: {websocket.headers.raw}"
    )

    if origin not in ALLOWED_ORIGINS:
        logger.warning(f"WebSocket connection from untrusted origin rejected: {origin}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket_manager.connect(job_id, websocket)

    try:
        job = job_manager.get_job(job_id)
        if job:
            await websocket.send_json(
                {
                    "job_id": job.job_id,
                    "type": "status",
                    "status": job.status,
                    "message": job.details,
                }
            )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(job_id, websocket)
        logger.info(f"WebSocket for job {job_id} disconnected.")
