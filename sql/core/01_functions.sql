-- FICHIER: sql/core/01_functions.sql
-- Responsabilité Unique : Définir les fonctions stockées (logique métier en base).

-- Fonction de recherche par similarité vectorielle pure.
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(768),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    chunk_id UUID, document_id UUID, content TEXT, similarity FLOAT,
    metadata JSONB, document_title TEXT, document_source TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.document_id, c.content, 1 - (c.embedding <=> query_embedding),
           c.metadata, d.title, d.source
    FROM chunks c JOIN documents d ON c.document_id = d.id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Fonction de recherche hybride (vecteur + texte plein).
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(768), query_text TEXT, match_count INT DEFAULT 10, text_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    chunk_id UUID, document_id UUID, content TEXT, combined_score FLOAT,
    vector_similarity FLOAT, text_similarity FLOAT, metadata JSONB,
    document_title TEXT, document_source TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT id, 1 - (embedding <=> query_embedding) AS vector_sim
        FROM chunks WHERE embedding IS NOT NULL
        ORDER BY vector_sim DESC LIMIT match_count * 2
    ),
    text_results AS (
        SELECT id, ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', query_text)) AS text_sim
        FROM chunks WHERE to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
    )
    SELECT c.id, c.document_id, c.content,
           (COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight),
           COALESCE(v.vector_sim, 0), COALESCE(t.text_sim, 0), c.metadata, d.title, d.source
    FROM chunks c JOIN documents d ON c.document_id = d.id
    LEFT JOIN vector_results v ON c.id = v.id
    LEFT JOIN text_results t ON c.id = t.id
    WHERE v.id IS NOT NULL OR t.id IS NOT NULL
    ORDER BY combined_score DESC LIMIT match_count;
END;
$$;

-- Fonction utilitaire pour récupérer tous les chunks d'un document.
CREATE OR REPLACE FUNCTION get_document_chunks(doc_id UUID)
RETURNS TABLE (chunk_id UUID, content TEXT, chunk_index INTEGER, metadata JSONB)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT id, chunks.content, chunks.chunk_index, chunks.metadata
    FROM chunks WHERE document_id = doc_id ORDER BY chunk_index;
END;
$$;