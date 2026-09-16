
-- document
CREATE TABLE public.document (
    id                      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                    uuid,

    name                    varchar(128),
    content_type            varchar(32),
    type                    varchar(16),

    url                     text,
    description             text,
    keywords                text,

    body_length             integer DEFAULT 0,
    body_length_compressed  integer DEFAULT 0,

    author_id               bigint,
    author_details          text,

    folder_ref              uuid,

    is_deleted              boolean DEFAULT false,
    is_public               boolean DEFAULT false,
    is_internal_use_only    boolean DEFAULT false,

    updated_at              timestamptz NOT NULL DEFAULT now(),
    updated_by_id           bigint,
    created_at              timestamptz NOT NULL DEFAULT now(),
    created_by_id           bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER document_set_updated_at
    BEFORE UPDATE ON public.document
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
