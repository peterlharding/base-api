-- Create the base_api database, owned by the api role.
--
-- Run after 01-create-users.sql (the owner role must already exist):
--
--   psql -U postgres -f 02-create-database.sql
--
-- Idempotent: does nothing if the database already exists.
--
-- CREATE DATABASE cannot run inside a transaction (so no DO block); the
-- \gexec meta-command executes the generated statement only when the
-- database is missing.

SELECT format('CREATE DATABASE %I OWNER %I', 'base_api', 'api')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'base_api')
\gexec

\echo 'database "base_api" ready (owner: api)'
