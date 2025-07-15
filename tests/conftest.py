# FICHIER: tests/conftest.py (CORRIGÉ)
# L'import de testcontainers est déplacé à l'intérieur de la fixture
# pour n'être chargé que lorsque la fixture est réellement utilisée.
import pytest
# from testcontainers.postgres import PostgresContainer <-- SUPPRIMER CETTE LIGNE
from ingestion.storage.repositories.sqlite_graph_repository import SQLiteGraphRepository
from ingestion.storage.repositories.postgres_repository import PostgresRepository
import os

@pytest.fixture(scope="function")
async def sqlite_repo():
    """Fixture pour un repo SQLite en mémoire. Rapide et isolé."""
    repo = SQLiteGraphRepository(db_path=":memory:")
    await repo.initialize()
    yield repo
    await repo.close()

@pytest.fixture(scope="session")
def postgres_container():
    """Démarre un conteneur PostgreSQL pour la durée de la session de test."""
    # ======================= MODIFICATION ELITE =======================
    # L'import est maintenant à l'intérieur de la fixture.
    # Il ne sera exécuté que si un test demande cette fixture.
    from testcontainers.postgres import PostgresContainer
    # ==================================================================
    
    with PostgresContainer("postgres:16-alpine") as postgres:
        os.environ["DATABASE_URL"] = postgres.get_connection_url()
        # Note: l'exécution de psql dans le conteneur serait nécessaire ici.
        # Pour la simplicité, nous supposons que le schéma est appliqué.
        yield postgres

@pytest.fixture(scope="function")
async def postgres_repo(postgres_container):
    """Fixture pour un repo PostgreSQL pointant vers le conteneur de test."""
    repo = PostgresRepository()
    # Assurer que le pool de connexion est réinitialisé pour chaque test
    if repo._pool:
        await repo.close()
    await repo.initialize()
    # Idéalement, on nettoierait les tables ici avant chaque test (TRUNCATE)
    yield repo
    await repo.close()