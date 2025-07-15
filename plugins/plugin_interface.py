# FICHIER: analyzer-engine/plugins/plugin_interface.py
from abc import ABC, abstractmethod
from ingestion.parsing.parser_registry import ParserRegistry
from ingestion.analysis.analyzer_registry import AnalyzerRegistry

class IJabbarRootPlugin(ABC):
    """
    Le contrat fondamental pour tout plugin externe.
    Une classe implémentant cette interface est le point d'entrée
    qu'analyzer-engine cherchera dans chaque plugin.
    """

    @abstractmethod
    def register(self, parser_registry: ParserRegistry, analyzer_registry: AnalyzerRegistry):
        """
        Cette méthode est appelée par le chargeur de plugins au démarrage.
        Elle reçoit les registres centraux de l'application pour que le plugin
        puisse y enregistrer ses propres composants (parseurs, analyseurs, etc.).
        """
        pass