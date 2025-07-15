# FICHIER: analyzer-engine/core/contracts/vector_repository_contract.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.db import ChunkResult, DocumentMetadata


class IVectorRepository(ABC):
    """
    Contrat pour la persistance et la recherche de données vectorielles et documentaires.
    Toute interaction avec la base de données principale (ex: PostgreSQL) DOIT passer par ce contrat.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialise la connexion et les ressources nécessaires."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Ferme la connexion à la base de données."""
        pass

    @abstractmethod
    async def vector_search(
        self, embedding: List[float], limit: int
    ) -> List[ChunkResult]:
        """Effectue une recherche par similarité vectorielle."""
        pass

    @abstractmethod
    async def hybrid_search(
        self, embedding: List[float], query_text: str, limit: int, text_weight: float
    ) -> List[ChunkResult]:
        """Effectue une recherche hybride (vecteur + texte)."""
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un document complet par son ID."""
        pass

    @abstractmethod
    async def list_documents(self, limit: int, offset: int) -> List[DocumentMetadata]:
        """Liste les documents disponibles avec leurs métadonnées."""
        pass

    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Récupère tous les chunks pour un document donné."""
        pass

    @abstractmethod
    async def save_document_with_chunks(
        self,
        file_path: str,
        document_content: str,
        chunks: List[Dict[str, Any]],
        document_metadata: Dict[str, Any],
    ) -> int:
        """Sauvegarde un document et tous ses chunks de manière atomique."""
        pass
