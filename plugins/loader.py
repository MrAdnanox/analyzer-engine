# FICHIER: analyzer-engine/plugins/loader.py
import os
import importlib.util
import logging
from .plugin_interface import IJabbarRootPlugin
from ingestion.parsing.parser_registry import parser_registry
from ingestion.analysis.analyzer_registry import analyzer_registry

logger = logging.getLogger(__name__)

PLUGINS_DIR = "plugins_enabled"


def load_plugins():
    """
    Découvre, importe et enregistre tous les plugins valides trouvés
    dans le répertoire PLUGINS_DIR.
    """
    if not os.path.exists(PLUGINS_DIR) or not os.path.isdir(PLUGINS_DIR):
        logger.warning(
            f"Répertoire des plugins '{PLUGINS_DIR}' introuvable ou invalide. Aucun plugin externe ne sera chargé."
        )
        return

    for package_name in os.listdir(PLUGINS_DIR):
        package_path = os.path.join(PLUGINS_DIR, package_name)
        entry_point_path = os.path.join(package_path, "main.py")

        if os.path.isdir(package_path) and os.path.exists(entry_point_path):
            try:
                # Importer dynamiquement le module du plugin
                spec = importlib.util.spec_from_file_location(
                    f"plugins_enabled.{package_name}.main", entry_point_path
                )
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)

                # Chercher et instancier la classe du plugin
                for obj_name in dir(plugin_module):
                    obj = getattr(plugin_module, obj_name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, IJabbarRootPlugin)
                        and obj is not IJabbarRootPlugin
                    ):
                        plugin_instance = obj()
                        logger.info(
                            f"Chargement du plugin '{plugin_instance.__class__.__name__}' depuis '{package_name}'."
                        )

                        # Enregistrer le plugin ! C'est ici que la magie opère.
                        plugin_instance.register(parser_registry, analyzer_registry)
                        logger.info(
                            f"Plugin '{plugin_instance.__class__.__name__}' enregistré avec succès."
                        )
                        # On suppose un seul point d'entrée par plugin pour la clarté
                        break

            except Exception as e:
                logger.error(
                    f"Échec du chargement du plugin depuis '{package_name}': {e}",
                    exc_info=True,
                )
