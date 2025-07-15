import pytest
from unittest.mock import AsyncMock
from ingestion.orchestration.pipeline_director import PipelineDirector
from ingestion.orchestration.execution_context import ExecutionContext


@pytest.mark.unit
async def test_pipeline_director_stage_execution_order(mocker):
    """
    Valide que le PipelineDirector exécute chaque étape dans le bon ordre
    en utilisant des mocks pour isoler le test de l'implémentation des étapes.
    """
    # Arrange: Créer des mocks pour les étapes du pipeline
    mock_stage1 = AsyncMock()
    mock_stage2 = AsyncMock()

    # Simuler le flux de données à travers les étapes
    context_after_stage1 = ExecutionContext(
        file_path="test.py",
        source_code="",
        language="python",
        entities=[{"name": "entity1"}],
    )
    mock_stage1.execute.return_value = context_after_stage1

    context_after_stage2 = ExecutionContext(
        file_path="test.py",
        source_code="",
        language="python",
        entities=[{"name": "entity1"}],
        chunks=[{"content": "chunk1"}],
    )
    mock_stage2.execute.return_value = context_after_stage2

    # Isoler le PipelineDirector de ses dépendances réelles en patchant
    # l'attribut `pipeline` de l'instance que nous allons tester.
    director = PipelineDirector()
    mocker.patch.object(director, "pipeline", [mock_stage1, mock_stage2])

    initial_context = ExecutionContext(
        file_path="test.py", source_code="", language="python"
    )

    # Act: Exécuter le processus sur le directeur patché
    final_context = await director.process(
        initial_context.file_path, initial_context.source_code, initial_context.language
    )

    # Assert: Vérifier que les mocks ont été appelés correctement
    mock_stage1.execute.assert_called_once()
    # Vérifier que le contexte initial a bien été passé à la première étape
    assert mock_stage1.execute.call_args[0][0].file_path == "test.py"

    mock_stage2.execute.assert_called_once()
    # Vérifier que le contexte de la première étape a été passé à la seconde
    assert mock_stage2.execute.call_args[0][0] == context_after_stage1

    # Vérifier que le contexte final est bien celui retourné par la dernière étape
    assert final_context == context_after_stage2
