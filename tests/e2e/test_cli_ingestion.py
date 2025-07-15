# Fichier: tests/e2e/test_cli_ingestion.py (MODIFIÉ)

import pytest
import subprocess
import sys
import os
# AJOUTER CET IMPORT
from ingestion.chunker import DocumentChunk

@pytest.mark.e2e
# AJOUTER `mocker` AUX ARGUMENTS DU TEST
async def test_cli_ingest_e2e(sqlite_repo, postgres_repo, tmp_path, mocker):
    """
    Valide le flux complet : CLI -> Parsing -> Analysis -> Storage.
    """
    # Arrange: Créer un fichier de code source temporaire
    sample_code_path = tmp_path / "sample_code.py"
    sample_code_path.write_text("def my_func():\n    pass\n")

    # On mock la méthode qui fait l'appel réseau.
    # On définit une fonction qui simule le comportement de embed_chunks
    def mock_embed_chunks(chunks: list[DocumentChunk], progress_callback=None):
        # La vraie fonction modifie les chunks en place, on doit faire pareil.
        for chunk in chunks:
            # On simule un embedding de la bonne dimension
            chunk.embedding = [0.0] * 768 
        return chunks

    mocker.patch(
        'ingestion.embedder.EmbeddingGenerator.embed_chunks', 
        side_effect=mock_embed_chunks
    )

    # Act: Exécuter la commande CLI comme un processus externe
    command = [
        sys.executable,
        "cli.py",
        "ingest",
        str(sample_code_path)
    ]

    # Utiliser les mêmes BDD que les fixtures pour la validation
    os.environ["SQLITE_DB_PATH"] = sqlite_repo.db_path

    result = subprocess.run(command, capture_output=True, text=True, check=False)

    # Assert
    assert result.returncode == 0, f"CLI command failed: {result.stderr}"
    assert "Ingestion terminée" in result.stdout

    # Valider l'état final dans les BDD
    # 1. Graphe de code (SQLite)
    relationships = await sqlite_repo.find_entity_relationships("my_func")
    assert len(relationships) > 0
    assert any(r["source"] == "my_func (FUNCTION)" for r in relationships)

    # 2. Données vectorielles (Postgres)
    documents = await postgres_repo.list_documents(10, 0)
    assert len(documents) == 1
    assert documents[0].source == str(sample_code_path)
