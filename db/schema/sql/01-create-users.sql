-- Create the application database roles: plh, root and api.
--
-- All three are plain LOGIN roles sharing one password.  The password is
-- passed in as the psql variable `db_password` so it never has to live in
-- this file (or the repository):
--
--   psql -v ON_ERROR_STOP=1 -U postgres -v db_password="$DB_PASSWORD" -f 01-create-users.sql
--
-- Idempotent: re-running the script updates the password on existing roles.
--
-- Note: psql does NOT substitute :variables inside a dollar-quoted block, so
-- none of this can live in a DO $$ ... $$ body - the server would receive a
-- literal ':db_password' and fail with `syntax error at or near ":"`.  The
-- statements below are therefore generated outside any dollar quote and run
-- with \gexec.

-- An unset variable is a syntax error rather than an empty string, so fold
-- "not set" into "empty" and let the single check below report both.
\if :{?db_password}
\else
\set db_password ''
\endif

-- Refuse to run without a password.  Generated rather than written literally
-- for the reason in the header comment.  Needs -v ON_ERROR_STOP=1 to stop the
-- script: reading from a file or stdin, psql otherwise reports the error and
-- still exits 0.
SELECT format('DO $guard$ BEGIN RAISE EXCEPTION %L; END $guard$',
              'db_password is empty; pass it with -v db_password="..." (see SETUP.md)')
 WHERE :'db_password' = ''
\gexec

-- CREATE the role if it is missing, otherwise ALTER it to the current
-- password.  %I quotes the identifier, %L the password literal.
SELECT format(
           CASE
               WHEN EXISTS (SELECT FROM pg_roles WHERE rolname = role_name)
               THEN 'ALTER ROLE %I WITH LOGIN PASSWORD %L'
               ELSE 'CREATE ROLE %I LOGIN PASSWORD %L'
           END,
           role_name, :'db_password')
  FROM (VALUES ('plh'), ('root'), ('api')) AS t(role_name)
\gexec

\echo 'roles plh, root and api ready'
