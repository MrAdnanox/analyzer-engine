# FICHIER: tests/ingestion/orchestration/test_pipeline_director.py (CORRIGÉ)
import pytest
from unittest.mock import AsyncMock
from ingestion.orchestration.pipeline_director import PipelineDirector
from ingestion.orchestration.execution_context import ExecutionContext


@pytest.mark.unit
async def test_pipeline_director_stage_execution_order(mocker):
    """
    Valide que le PipelineDirector exécute chaque étape dans le bon ordre
    et transmet le contexte correctement.
    """
    # Arrange: Mocker les étapes du pipeline
    mock_stage1 = AsyncMock()
    mock_stage2 = AsyncMock()

    mock_stage1.execute.return_value = ExecutionContext(
        file_path="test.py",
        source_code="",
        language="python",
        entities=[{"name": "entity1", "type": "FUNCTION"}],
    )
    mock_stage2.execute.return_value = ExecutionContext(
        file_path="test.py",
        source_code="",
        language="python",
        entities=[{"name": "entity1", "type": "FUNCTION"}],
        chunks=[{"content": "chunk1", "embedding": [0.1]}],
    )

    # ======================= MODIFICATION ELITE =======================
    # 1. On instancie d'abord le directeur.
    director = PipelineDirector()

    # 2. On utilise `mocker.patch.object` pour remplacer l'attribut `pipeline`
    #    SUR CETTE INSTANCE SPÉCIFIQUE.
    mocker.patch.object(director, "pipeline", [mock_stage1, mock_stage2])
    # ==================================================================

    context = ExecutionContext(file_path="test.py", source_code="", language="python")

    # Act
    # On utilise l'instance que nous avons créée et patchée.
    final_context = await director.process(
        context.file_path, context.source_code, context.language
    )

    # Assert
    mock_stage1.execute.assert_called_once()
    mock_stage2.execute.assert_called_once()

    assert mock_stage2.execute.call_args[0][0].entities == [
        {"name": "entity1", "type": "FUNCTION"}
    ]
    assert final_context.chunks == [{"content": "chunk1", "embedding": [0.1]}]
