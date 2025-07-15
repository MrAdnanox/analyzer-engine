-- FICHIER: sql/core/00_extensions.sql
-- Responsabilité Unique : Activer les extensions PostgreSQL nécessaires.
-- Ordre 00 car tout le reste en dépend.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;