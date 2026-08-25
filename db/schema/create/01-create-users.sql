-- Create the application database roles: plh, root and api.
--
-- All three are plain LOGIN roles sharing one password.  The password is
-- passed in as the psql variable `db_password` so it never has to live in
-- this file (or the repository):
--
--   psql -U postgres -v db_password="$DB_PASSWORD" -f 01-create-users.sql
--
-- Idempotent: re-running the script updates the password on existing roles.

DO
$$
BEGIN
    IF :db_password = '' THEN
        RAISE EXCEPTION 'db_password is empty; pass it with -v db_password="..." (see SETUP.md)';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'plh') THEN
        CREATE ROLE plh LOGIN PASSWORD :db_password;
    ELSE
        ALTER ROLE plh WITH LOGIN PASSWORD :db_password;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'root') THEN
        CREATE ROLE root LOGIN PASSWORD :db_password;
    ELSE
        ALTER ROLE root WITH LOGIN PASSWORD :db_password;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api') THEN
        CREATE ROLE api LOGIN PASSWORD :db_password;
    ELSE
        ALTER ROLE api WITH LOGIN PASSWORD :db_password;
    END IF;
END
$$;
