-- FinanceGPT Database Initialization
-- This runs automatically when PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- Create read-only user for analytics
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'financegpt_readonly') THEN
    CREATE ROLE financegpt_readonly WITH LOGIN PASSWORD 'readonly_change_me';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE financegpt TO financegpt_readonly;
GRANT USAGE ON SCHEMA public TO financegpt_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO financegpt_readonly;
