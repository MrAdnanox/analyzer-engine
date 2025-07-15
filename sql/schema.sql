-- FICHIER: sql/schema.sql (version finale)
-- ===================================================================
-- ==    ORCHESTRATEUR DE SCHÉMA MODULAIRE - JABBARROOT V5.0        ==
-- ==    Ce fichier ne contient aucune logique. Il assemble les     ==
-- ==    modules dans l'ordre correct des dépendances.              ==
-- ===================================================================

-- Supprime l'ancien schéma pour une reconstruction propre.
\i _drop_all.sql

-- 1. Fondations : extensions, fonctions et triggers.
\echo '==> Creating core components (extensions, functions, triggers)...'
\i core/00_extensions.sql
\i core/01_functions.sql
\i core/02_triggers.sql

-- 2. Modules : tables et leurs index.
\echo '==> Creating table modules...'
\i modules/00_documents_chunks.sql
\i modules/01_sessions_messages.sql

-- 3. Vues : abstractions pour la lecture des données.
\echo '==> Creating logical views...'
\i views/00_document_summaries.sql

\echo '==> Schema modularization complete.'