-- Create the application database, owned by the api role.
--
-- The name comes from DB_NAME in the repo-root .env, the same key the
-- application reads, so the two cannot disagree:
--
--   psql -v ON_ERROR_STOP=1 -U postgres -v db_name="$DB_NAME" -f 02-create-database.sql
--
-- Run after 01-create-users.sql (the owner role must already exist).
-- Idempotent: does nothing if the database already exists.
--
-- CREATE DATABASE cannot run inside a transaction (so no DO block); the
-- \gexec meta-command executes the generated statement only when the
-- database is missing.

-- An unset variable is a syntax error rather than an empty string, so fall
-- back to the same default the application uses.
\if :{?db_name}
\else
\set db_name 'base_api'
\endif

SELECT format('CREATE DATABASE %I OWNER %I', :'db_name', 'api')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db_name')
\gexec

\echo 'database' :'db_name' 'ready (owner: api)'
