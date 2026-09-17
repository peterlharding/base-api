
-- instance_metadata sample data
--
-- An UPDATE, not an INSERT.  The row itself is stamped by migration 0006,
-- because it has to exist on every database including production, and
-- make seed is a development convenience that production never runs.  A
-- second INSERT here would violate the unique index on (true) that makes
-- the table a singleton.
--
-- Only the environment-describing columns are set.  app_version and
-- db_version are left to the migration: the endpoint reports the running
-- app version from pyproject.toml and the live alembic revision anyway, so
-- the stored versions describe when the database was stamped rather than
-- what is serving requests.

UPDATE public.instance_metadata
   SET release = 'dev',
       notes   = 'development database, seeded by make seed';
