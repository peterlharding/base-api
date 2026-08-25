
CREATE OR REPLACE FUNCTION public.set_when_modified()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.when_modified := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER application_user_set_when_modified
    BEFORE UPDATE ON public.application_user
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_when_modified();


