# FICHIER: analyzer-engine/cli.py (MODIFIÉ)
import asyncio
import logging
import argparse
import os

# NOUVEAUX IMPORTS STRATÉGIQUES
from plugins.loader import load_plugins
from ingestion.orchestration.pipeline_director import PipelineDirector

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_ingestion(file_path: str):
    """
    Fonction principale pour lancer le pipeline d'ingestion sur un fichier spécifique.
    """
    director = PipelineDirector()
    
    if not os.path.exists(file_path):
        logger.error(f"Fichier cible introuvable : {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    logger.info(f"Démarrage de l'ingestion pour le fichier : {file_path}")
    
    # Détecter le langage à partir de l'extension du fichier (simpliste mais efficace)
    language = "python" if file_path.endswith(".py") else "unknown"
    if language == "unknown":
        logger.warning(f"Langage inconnu pour le fichier {file_path}, tentative avec 'python'")

    await director.process(
        file_path=file_path,
        source_code=source_code,
        language=language
    )
    
    logger.info(f"Ingestion terminée pour le fichier {file_path}.")


async def main():
    """Point d'entrée principal du CLI."""
    
    # Charger les plugins AVANT toute autre opération.
    # Les registres seront ainsi peuplés avec les composants externes
    # avant que le PipelineDirector ne soit instancié et utilisé.
    logger.info("="*50)
    logger.info("Phase de démarrage : Chargement des plugins externes...")
    load_plugins()
    logger.info("Chargement des plugins terminé. L'application est prête.")
    logger.info("="*50)
    # =====================================================================

    parser = argparse.ArgumentParser(description="CLI pour l'écosystème JabbarRoot Analyzer.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Création de la sous-commande 'ingest'
    ingest_parser = subparsers.add_parser("ingest", help="Lancer le pipeline d'ingestion sur un fichier.")
    ingest_parser.add_argument("file", type=str, help="Le chemin vers le fichier à analyser.")

    args = parser.parse_args()

    if args.command == "ingest":
        await run_ingestion(args.file)

if __name__ == "__main__":
    asyncio.run(main())