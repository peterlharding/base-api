
CREATE TABLE public.instance_metadata (
    release       text        NOT NULL,
    app_version   text        NOT NULL,
    db_version    text        NOT NULL,
    notes         text        NOT NULL DEFAULT '',
    when_modified timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT instance_metadata_release_check CHECK (release IN ('dev', 'test', 'staging', 'prod')),
    CONSTRAINT instance_metadata_app_version_check CHECK (app_version ~ '^v\d+\.\d+\.\d+$'),
    CONSTRAINT instance_metadata_db_version_check  CHECK (db_version  ~ '^v\d+\.\d+\.\d+$')
);

CREATE UNIQUE INDEX instance_metadata_singleton ON public.instance_metadata ((true));

CREATE TRIGGER instance_metadata_set_when_modified
    BEFORE UPDATE ON public.instance_metadata
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_when_modified();


-- On Update

-- UPDATE public.instance_metadata
-- SET app_version = 'v1.3.0',
--     db_version  = 'v0.5.0',
--     notes       = 'Schema modernisation: timestamptz, FKs, session expiry';


-- Migration

-- INSERT INTO public.instance_metadata (release, app_version, db_version, notes)
-- SELECT d.release, v.version, d.db_version, d.notes
-- FROM public.db_metadata d CROSS JOIN public.version v;
