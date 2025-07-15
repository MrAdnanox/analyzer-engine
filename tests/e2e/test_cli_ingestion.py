# Fichier: tests/e2e/test_cli_ingestion.py (VERSION FINALE ET VALIDÉE)
import pytest
import os
from cli import run_ingestion


@pytest.mark.integration
async def test_pipeline_ingestion_logic(
    mocker, sqlite_repo, postgres_repo, db_schema, tmp_path
):
    """
    Valide le flux d'ingestion de bout-en-bout en appelant directement la logique
    applicative et en injectant des dépendances de test (repositories).
    """
    # --- Arrange ---
    sample_code_path = tmp_path / "sample_code.py"
    sample_code_path.write_text("def my_func(a: int):\n    return a + 1\n")

    mocker.patch.dict(os.environ, {"APP_ENV": "test"})
    mocker.patch(
        "ingestion.orchestration.stages.storage_stage.SQLiteGraphRepository",
        return_value=sqlite_repo,
    )
    mocker.patch(
        "ingestion.orchestration.stages.storage_stage.PostgresRepository",
        return_value=postgres_repo,
    )

    # --- Act ---
    await run_ingestion(str(sample_code_path))

    # --- Assert ---
    relationships = await sqlite_repo.find_entity_relationships("my_func")
    assert len(relationships) > 0

    documents = await postgres_repo.list_documents(limit=10, offset=0)
    assert len(documents) == 1
    assert documents[0].title == str(sample_code_path)
    assert documents[0].chunk_count > 0
