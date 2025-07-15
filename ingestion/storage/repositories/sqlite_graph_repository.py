# FICHIER: analyzer-engine/ingestion/storage/repositories/sqlite_graph_repository.py

import os
import logging
import aiosqlite
from typing import List, Dict, Any

# IMPORTS STRATÉGIQUES :
# Dépendance à l'abstraction (le contrat) et aux exceptions définies dans core.
from core.contracts.repository_contract import ICodeRepository
from core.exceptions.base_exceptions import RepositoryError

logger = logging.getLogger(__name__)

# La configuration de la base de données est une responsabilité de l'implémentation.
DB_FILE = "code_graph.sqlite"

class SQLiteGraphRepository(ICodeRepository):
    """
    Implémentation du contrat ICodeRepository utilisant une base de données SQLite locale.
    Cette classe encapsule toute la logique de lecture et d'écriture pour le graphe de connaissance du code.
    """

    def __init__(self, db_path: str = DB_FILE):
        """
        Initialise le repository.
        
        Args:
            db_path: Chemin vers le fichier de la base de données SQLite.
        """
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None
        logger.info(f"SQLiteGraphRepository instance created for database at: {self.db_path}")

    async def initialize(self) -> None:
        """
        Initialise la connexion à la base de données et crée le schéma si nécessaire.
        Cette méthode est idempotente.
        """
        if self.conn and not self.conn.is_closed():
            logger.debug("Connection already initialized.")
            return

        try:
            # Créer le répertoire parent s'il n'existe pas
            os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
            self.conn = await aiosqlite.connect(self.db_path)
            # Utiliser aiosqlite.Row pour accéder aux colonnes par leur nom.
            self.conn.row_factory = aiosqlite.Row
            # Activer les contraintes de clé étrangère, crucial pour l'intégrité des données.
            await self.conn.execute("PRAGMA foreign_keys = ON;")
            await self._create_tables_if_not_exists()
            logger.info(f"SQLiteGraphRepository initialized. Database at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLiteGraphRepository: {e}", exc_info=True)
            raise RepositoryError(f"Failed to initialize SQLiteGraphRepository: {e}")

    async def close(self) -> None:
        """Ferme la connexion à la base de données si elle est ouverte."""
        if self.conn and not self.conn.is_closed():
            await self.conn.close()
            self.conn = None
            logger.info("SQLiteGraphRepository connection closed.")

    async def _create_tables_if_not_exists(self) -> None:
        """Crée les tables `entities` et `relationships` si elles n'existent pas."""
        if not self.conn:
            raise RepositoryError("Database connection not initialized.")

        try:
            # Utilisation de executescript pour exécuter plusieurs instructions dans une transaction.
            await self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('FUNCTION', 'CLASS', 'FILE')),
                    file_path TEXT NOT NULL,
                    source_code TEXT,
                    UNIQUE(name, file_path)
                );

                CREATE TABLE IF NOT EXISTS relationships (
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('CALLS', 'USES_TYPE', 'DEFINES_IN_FILE')),
                    PRIMARY KEY (source_id, target_id, type),
                    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
                CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id);
                CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id);
            """)
            await self.conn.commit()
            logger.debug("Tables 'entities' and 'relationships' are ready.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise RepositoryError(f"Failed to create tables: {e}")

    async def add_code_structure(self, file_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Ajoute les entités (nœuds) et relations (arêtes) d'un fichier au graphe de manière atomique.
        Cette méthode absorbe la logique de l'ancien `graph_builder.py`.
        """
        if not self.conn:
            await self.initialize()

        entities = file_data.get('entities', [])
        relationships = file_data.get('relationships', [])
        file_path = file_data.get('file_path')

        if not entities or not file_path:
            logger.warning("No entities or file_path provided in file_data. Skipping.")
            return {"entities_added": 0, "relations_added": 0}

        entities_added_count = 0
        relations_added_count = 0
        
        # Utiliser une transaction explicite pour garantir l'atomicité.
        async with self.conn.cursor() as cursor:
            try:
                # 1. Insérer toutes les entités
                for entity in entities:
                    await cursor.execute(
                        "INSERT OR IGNORE INTO entities (name, type, file_path, source_code) VALUES (?, ?, ?, ?)",
                        (entity['name'], entity['type'], file_path, entity.get('source_code', ''))
                    )
                    if cursor.rowcount > 0:
                        entities_added_count += 1

                # 2. Récupérer les IDs des entités pour créer les relations
                entity_ids = {}
                await cursor.execute("SELECT id, name FROM entities WHERE file_path = ?", (file_path,))
                rows = await cursor.fetchall()
                for row in rows:
                    entity_ids[row['name']] = row['id']
                
                # 3. Insérer toutes les relations
                for rel in relationships:
                    source_id = entity_ids.get(rel['source'])
                    target_id = entity_ids.get(rel['target'])
                    
                    if source_id and target_id:
                        await cursor.execute(
                            "INSERT OR IGNORE INTO relationships (source_id, target_id, type) VALUES (?, ?, ?)",
                            (source_id, target_id, rel['type'])
                        )
                        if cursor.rowcount > 0:
                            relations_added_count += 1
                    else:
                        logger.warning(f"Could not find IDs for relationship: {rel}. Skipping.")
                
                await self.conn.commit()
                logger.info(f"Added {entities_added_count} new entities and {relations_added_count} new relationships for {file_path}.")

            except Exception as e:
                await self.conn.rollback()
                logger.error(f"Transaction failed for {file_path}. Rolling back. Error: {e}", exc_info=True)
                raise RepositoryError(f"Failed to add code structure: {e}")

        return {"entities_added": entities_added_count, "relations_added": relations_added_count}

    async def find_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Recherche une entité par son nom et retourne toutes ses relations directes (entrantes et sortantes).
        Cette méthode remplace la fonction `search_code_graph` de l'ancien `graph_utils.py`.
        """
        if not self.conn:
            await self.initialize()

        if not os.path.exists(self.db_path):
            logger.warning(f"Graph database file '{self.db_path}' not found. Run ingestion first.")
            return []

        results = []
        try:
            async with self.conn.cursor() as cursor:
                # La recherche est insensible à la casse et partielle pour plus de flexibilité.
                search_term = f"%{entity_name}%"
                
                # Recherche des relations sortantes ET entrantes en une seule requête optimisée.
                # Utilisation de UNION pour combiner les deux cas de figure.
                query = """
                    SELECT 
                        s.name AS source_name, s.type AS source_type, 
                        r.type AS rel_type, 
                        t.name AS target_name, t.type AS target_type
                    FROM relationships r
                    JOIN entities s ON r.source_id = s.id
                    JOIN entities t ON r.target_id = t.id
                    WHERE s.name LIKE ?
                    
                    UNION
                    
                    SELECT 
                        s.name AS source_name, s.type AS source_type, 
                        r.type AS rel_type, 
                        t.name AS target_name, t.type AS target_type
                    FROM relationships r
                    JOIN entities s ON r.source_id = s.id
                    JOIN entities t ON r.target_id = t.id
                    WHERE t.name LIKE ?
                """
                
                await cursor.execute(query, (search_term, search_term))
                relationships = await cursor.fetchall()
                
                if not relationships:
                    logger.info(f"No relationships found for entity matching '{entity_name}'.")
                    return []

                for rel in relationships:
                    fact = {
                        "source": f"{rel['source_name']} ({rel['source_type']})",
                        "relationship": rel['rel_type'],
                        "target": f"{rel['target_name']} ({rel['target_type']})"
                    }
                    if fact not in results:
                        results.append(fact)
        except Exception as e:
            logger.error(f"Error querying code graph for entity '{entity_name}': {e}", exc_info=True)
            raise RepositoryError(f"Error querying code graph: {e}")

        return results
    
    async def clean_db(self) -> None:
        """Supprime toutes les données des tables du graphe."""
        if not self.conn:
            await self.initialize()
            
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("DELETE FROM relationships;")
                await cursor.execute("DELETE FROM entities;")
                # Réinitialise la séquence des IDs auto-incrémentés pour une base propre.
                await cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('entities');")
            await self.conn.commit()
            logger.warning("Graph database has been cleaned (all entities and relationships removed).")
        except Exception as e:
            await self.conn.rollback()
            logger.error(f"Failed to clean graph database: {e}", exc_info=True)
            raise RepositoryError(f"Failed to clean graph database: {e}")