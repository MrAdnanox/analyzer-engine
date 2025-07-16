# NOUVEAU FICHIER: analyzer-engine/api/dependencies.py
from typing import AsyncGenerator
import asyncpg
from asyncpg.pool import Pool

from config import settings
from services.job_manager import JobManager
from services.websocket_manager import WebSocketManager
from ingestion.storage.repositories.postgres_repository import PostgresRepository
from ingestion.storage.repositories.sqlite_graph_repository import SQLiteGraphRepository

# ======================= GESTION DU CYCLE DE VIE =======================
# Ces objets seront créés une seule fois pour toute la durée de vie de l'application.
pool: Pool | None = None


async def get_db_pool() -> Pool:
    """Retourne le pool de connexion, le crée s'il n'existe pas."""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=5, max_size=10)
    return pool


async def close_db_pool():
    """Ferme le pool de connexion à la base de données."""
    if pool:
        await pool.close()


# ======================= SINGLETONS =======================
# Ces managers sont des singletons pour partager leur état à travers l'application.
job_manager_singleton = JobManager()
websocket_manager_singleton = WebSocketManager()
sqlite_repo_singleton = SQLiteGraphRepository()

# ======================= PROVIDERS DE DÉPENDANCES =======================
# FastAPI appellera ces fonctions pour chaque requête qui en a besoin.


async def get_postgres_repo() -> AsyncGenerator[PostgresRepository, None]:
    """Provider pour le repository PostgreSQL."""
    db_pool = await get_db_pool()
    yield PostgresRepository(db_pool)


def get_sqlite_repo() -> SQLiteGraphRepository:
    """Provider pour le repository SQLite."""
    return sqlite_repo_singleton


def get_job_manager() -> JobManager:
    """Provider pour le JobManager."""
    return job_manager_singleton


def get_websocket_manager() -> WebSocketManager:
    """Provider pour le WebSocketManager."""
    return websocket_manager_singleton
