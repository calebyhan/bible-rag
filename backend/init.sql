-- Initialize pgvector extension for Bible RAG
-- This script should be run on a fresh Supabase/PostgreSQL database

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Step 2: Create schema using SQLAlchemy models
-- Note: The actual tables are created by running `python database.py` or by SQLAlchemy migrations
-- This init.sql is primarily for enabling the pgvector extension in Supabase

-- Step 3: After importing data, create the vector index
-- Run this AFTER all embeddings are inserted (run from Python using database.create_vector_index()):
--
-- CREATE INDEX IF NOT EXISTS idx_embeddings_vector
-- ON embeddings
-- USING ivfflat (vector vector_cosine_ops)
-- WITH (lists = 100);
--
-- Note: The 'lists' parameter should be approximately sqrt(total_rows)
-- For ~31,000 verses, lists=100 is a good starting point
-- Adjust based on your actual data size

-- Step 4: Grant necessary permissions (if needed for Supabase)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Verification queries (run after setup):
-- SELECT COUNT(*) FROM translations;
-- SELECT COUNT(*) FROM books;
-- SELECT COUNT(*) FROM verses;
-- SELECT COUNT(*) FROM embeddings;
-- SELECT pg_size_pretty(pg_total_relation_size('embeddings')) AS embeddings_size;
