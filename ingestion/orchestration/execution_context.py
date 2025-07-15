# FICHIER: analyzer-engine/ingestion/orchestration/execution_context.py (CORRIGÉ)
from pydantic import BaseModel, ConfigDict # <-- AJOUTER ConfigDict
from typing import Optional, List, Dict, Any
from core.models.ast_models import NormalizedAST

class ExecutionContext(BaseModel):
    """L'objet qui circule entre les étapes du pipeline, transportant l'état."""
    
    # ======================= MODIFICATION ELITE =======================
    # Remplacement de l'ancienne sous-classe `Config` par la syntaxe moderne `ConfigDict`
    # pour éliminer l'avertissement de dépréciation de Pydantic V2.
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # ==================================================================

    # Données initiales
    file_path: str
    source_code: str
    language: str
    
    # Données enrichies par les étapes successives
    normalized_ast: Optional[NormalizedAST] = None
    entities: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    chunks: List[Dict[str, Any]] = []
    
    # L'ancienne classe Config est supprimée.
    # class Config:
    #     arbitrary_types_allowed = True