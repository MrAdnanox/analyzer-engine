# FICHIER: analyzer-engine/core/exceptions/base_exceptions.py
class RepositoryError(Exception):
    """Exception de base pour les erreurs liées à la couche de persistance."""

    pass


class EntityNotFoundError(RepositoryError):
    """Levée lorsqu'une entité n'est pas trouvée dans le repository."""

    def __init__(self, entity_name: str):
        super().__init__(f"Entity '{entity_name}' not found.")
        self.entity_name = entity_name
