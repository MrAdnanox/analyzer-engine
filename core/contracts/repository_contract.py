# FICHIER: analyzer-engine/core/contracts/repository_contract.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ICodeRepository(ABC):
    """
    Contrat pour la persistance et la récupération de la connaissance du code.
    Toute interaction avec la base de données du graphe de code DOIT passer par ce contrat.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialise la connexion et les structures nécessaires."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Ferme la connexion à la base de données."""
        pass

    @abstractmethod
    async def add_code_structure(self, file_data: Dict[str, Any]) -> Dict[str, int]:
        """Ajoute les entités (nœuds) et relations (arêtes) d'un fichier au graphe."""
        pass

    @abstractmethod
    async def find_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Recherche une entité par son nom et retourne toutes ses relations directes.
        C'est le remplaçant direct de la fonction `search_code_graph`.
        """
        pass
