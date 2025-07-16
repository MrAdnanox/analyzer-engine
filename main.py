# FICHIER CORRIGÉ : analyzer-engine/main.py

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ELITE FIX: Importer la CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import endpoints as api_v1
from plugins.loader import load_plugins
from api.dependencies import get_db_pool, close_db_pool, sqlite_repo_singleton

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JabbarRoot Analyzer Engine",
    description="Service d'analyse et d'ingestion de code.",
    version="1.0.0",
)

# ELITE FIX: Définition et ajout de la middleware CORS
# Ceci est l'emplacement idéal : après l'initialisation de l'app et avant l'inclusion des routeurs.
origins = [
    "http://localhost:5173",  # Origine du serveur de développement SvelteKit/Vite
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Actions à exécuter au démarrage de l'application."""
    logger.info("=" * 50)
    logger.info("Phase de démarrage : Initialisation des ressources...")
    await get_db_pool()  # Initialise le pool de connexion Postgres
    await sqlite_repo_singleton.initialize()  # Initialise la connexion SQLite
    load_plugins()
    logger.info("Chargement des plugins terminé. L'application est prête.")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def on_shutdown():
    """Actions à exécuter à l'arrêt de l'application."""
    logger.info("Phase d'arrêt : Libération des ressources...")
    await close_db_pool()
    await sqlite_repo_singleton.close()
    logger.info("Ressources libérées. Arrêt propre.")


# ======================= GESTIONNAIRE D'ERREURS GLOBAL =======================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# ============================================================================

# Le routeur est inclus APRÈS que la middleware CORS a été ajoutée.
app.include_router(api_v1.router, prefix="/api/v1", tags=["v1"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the JabbarRoot Analyzer Engine API"}
