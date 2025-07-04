-- Initialize PostgreSQL database for Manushya.ai
-- This script sets up the pgvector extension and initial database configuration

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create custom functions for vector operations
-- Cosine similarity function
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$;

-- L2 distance function
CREATE OR REPLACE FUNCTION l2_distance(a vector, b vector)
RETURNS float
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN a <-> b;
END;
$$;

-- Inner product function
CREATE OR REPLACE FUNCTION inner_product(a vector, b vector)
RETURNS float
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN a <#> b;
END;
$$;

-- Set up connection limits and performance settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();

-- Create indexes for better performance
--- CREATE INDEX IF NOT EXISTS idx_memories_identity_id ON memories(identity_id);
--- CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON memories(memory_type);
--- CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
--- CREATE INDEX IF NOT EXISTS idx_memories_is_deleted ON memories(is_deleted);
--- CREATE INDEX IF NOT EXISTS idx_memories_ttl_days ON memories(ttl_days);

-- Create a function to clean up old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days integer DEFAULT 2555)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM audit_logs 
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Create a function to clean up expired memories
CREATE OR REPLACE FUNCTION cleanup_expired_memories()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count integer;
BEGIN
    UPDATE memories 
    SET is_deleted = true, deleted_at = NOW()
    WHERE ttl_days IS NOT NULL 
      AND created_at < NOW() - INTERVAL '1 day' * ttl_days
      AND is_deleted = false;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO manushya;
GRANT CREATE ON SCHEMA public TO manushya;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO manushya;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO manushya;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO manushya;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO manushya;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO manushya;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO manushya; 