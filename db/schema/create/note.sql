
-- note
CREATE TABLE public.note (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                    uuid,

    title                   text,
    body                    text,

    parent_type             varchar(64),
    parent_id               bigint,

    is_deleted              boolean DEFAULT false,
    is_private              boolean DEFAULT false,

    owner_id                bigint,

    updated_at              timestamptz NOT NULL DEFAULT now(),
    updated_by_id           bigint,
    created_at              timestamptz NOT NULL DEFAULT now(),
    created_by_id           bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER note_set_updated_at
    BEFORE UPDATE ON public.note
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
