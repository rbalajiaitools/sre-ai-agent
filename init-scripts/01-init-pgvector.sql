-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema for shared tables
CREATE SCHEMA IF NOT EXISTS shared;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA shared TO astra_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA shared TO astra_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA shared TO astra_user;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA shared GRANT ALL ON TABLES TO astra_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA shared GRANT ALL ON SEQUENCES TO astra_user;
