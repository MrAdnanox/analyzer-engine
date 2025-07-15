# FICHIER: tests/conftest.py (VERSION COMPLÈTE, VALIDÉE ET ROBUSTE)
import pytest
import os
from ingestion.storage.repositories.sqlite_graph_repository import SQLiteGraphRepository
from ingestion.storage.repositories.postgres_repository import PostgresRepository


@pytest.fixture(scope="session")
def postgres_container():
    if os.getenv("CI"):
        yield
        return
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("pgvector/pgvector:pg16") as postgres:
        os.environ["DATABASE_URL"] = postgres.get_connection_url().replace(
            "postgresql+psycopg2", "postgresql"
        )
        yield postgres


@pytest.fixture(scope="function")
async def postgres_repo(postgres_container):
    repo = PostgresRepository()
    await repo.initialize()
    yield repo
    await repo.close()


@pytest.fixture(scope="function")
async def db_schema(postgres_repo: PostgresRepository):
    sql_files_order = [
        "sql/core/00_extensions.sql",
        "sql/core/01_functions.sql",
        "sql/core/02_triggers.sql",
        "sql/modules/00_documents_chunks.sql",
        "sql/modules/01_sessions_messages.sql",
        "sql/views/00_document_summaries.sql",
    ]
    async with postgres_repo._get_connection() as conn:
        for file_path in sql_files_order:
            with open(file_path, "r") as f:
                await conn.execute(f.read())
    yield
    async with postgres_repo._get_connection() as conn:
        with open("sql/_drop_all.sql", "r") as f:
            await conn.execute(f.read())


@pytest.fixture(scope="function")
async def sqlite_repo():
    repo = SQLiteGraphRepository(db_path=":memory:")
    await repo.initialize()
    yield repo
    await repo.close()
