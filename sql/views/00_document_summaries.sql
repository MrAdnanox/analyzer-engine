-- FICHIER: sql/views/00_document_summaries.sql
-- Responsabilité Unique : Créer des vues d'agrégation pour les rapports.

CREATE OR REPLACE VIEW document_summaries AS
SELECT
    d.id,
    d.title,
    d.source,
    d.created_at,
    d.updated_at,
    d.metadata,
    COUNT(c.id) AS chunk_count,
    AVG(c.token_count) AS avg_tokens_per_chunk,
    SUM(c.token_count) AS total_tokens
FROM documents d
LEFT JOIN chunks c ON d.id = c.document_id
GROUP BY d.id;