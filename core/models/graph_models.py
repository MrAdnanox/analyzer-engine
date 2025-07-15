# FICHIER: analyzer-engine/core/models/graph_models.py
from pydantic import BaseModel, Field
from typing import Literal


class CodeEntity(BaseModel):
    """Représente un nœud dans notre graphe de connaissance : une fonction, une classe, un fichier."""

    name: str = Field(description="Le nom de l'entité, ex: 'execute_agent'.")
    type: Literal["FUNCTION", "CLASS", "FILE"] = Field(
        description="Le type de l'entité."
    )
    file_path: str = Field(description="Le chemin du fichier où l'entité est définie.")
    source_code: str = Field(description="Le code source complet de l'entité.")


class CodeRelationship(BaseModel):
    """Représente une arête dans notre graphe : un appel, une utilisation, etc."""

    source_name: str
    target_name: str
    type: Literal["CALLS", "USES_TYPE", "DEFINES_IN_FILE"]


class GraphSearchResult(BaseModel):
    """Structure de données standard pour les résultats de recherche dans le graphe."""

    source: str
    relationship: str
    target: str
