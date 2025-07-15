# FICHIER: tests/core/models/test_db_models.py (NOUVEAU)
# Premier test unitaire, validant la logique pure d'un modèle Pydantic.
# C'est une victoire rapide qui valide la configuration de base de pytest.
import pytest
from pydantic import ValidationError
from core.models.db import IngestionConfig


@pytest.mark.unit
def test_ingestion_config_defaults():
    """Vérifie que la configuration par défaut est valide."""
    config = IngestionConfig()
    assert config.chunk_size == 1000
    assert config.chunk_overlap < config.chunk_size


@pytest.mark.unit
def test_ingestion_config_overlap_validation():
    """Valide que la logique de validation de Pydantic lève une erreur
    lorsque la superposition est supérieure ou égale à la taille du chunk."""
    with pytest.raises(ValidationError) as exc_info:
        IngestionConfig(chunk_size=500, chunk_overlap=500)

    # Vérifie que l'erreur contient le message attendu.
    assert "must be less than chunk size" in str(exc_info.value)
