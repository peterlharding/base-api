
-- ---------------------------------------------------------------------------
-- Trigger function: stamp updated_at on every real change.
--
-- Installed by each table's create script (see the CREATE TRIGGER at the foot
-- of db/schema/create/*.sql for the tables that carry an updated_at column).
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------------
