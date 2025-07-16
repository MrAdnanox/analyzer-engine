# analyzer-engine/services/websocket_manager.py
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Gère les connexions WebSocket actives pour notifier les clients."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job_id: {job_id}")

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket disconnected for job_id: {job_id}")

    async def broadcast_to_job(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                await connection.send_json(message)
