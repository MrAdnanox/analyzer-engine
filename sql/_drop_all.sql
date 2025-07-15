-- FICHIER: sql/_drop_all.sql

DROP VIEW IF EXISTS document_summaries;
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS get_document_chunks(uuid);
-- La dimension du vecteur est spécifiée pour une suppression précise.
DROP FUNCTION IF EXISTS hybrid_search(vector(768), text, integer, double precision);
DROP FUNCTION IF EXISTS match_chunks(vector(768), integer);
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;