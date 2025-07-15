from abc import ABC, abstractmethod
from ..models.ast_models import NormalizedAST


class IParser(ABC):
    """Contrat pour transformer le code source en un AST normalisé."""

    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """Vérifie si ce parseur supporte le langage donné."""
        pass

    @abstractmethod
    async def parse(self, code: str) -> NormalizedAST:
        """Parse le code et retourne un AST normalisé."""
        pass
