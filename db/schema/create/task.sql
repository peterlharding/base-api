
-- task
CREATE TABLE public.task (
    id                          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                        uuid,

    subject                     text,
    description                 text,

    type                        varchar(64),
    status                      varchar(32),
    priority                    varchar(32),

    who_type                    varchar(32),
    who_id                      bigint,
    who_ref                     text,

    what_type                   varchar(32),
    what_id                     bigint,
    what_ref                    text,

    is_closed                   boolean DEFAULT false,
    is_deleted                  boolean DEFAULT false,
    is_archived                 boolean DEFAULT false,

    owner_id                    bigint,
    account_id                  bigint,

    activity_date               timestamptz NOT NULL DEFAULT now(),

    call_duration_in_seconds    integer DEFAULT 0,
    call_type                   varchar(64),
    call_disposition            text,
    call_object                 text,

    is_reminder_set             boolean DEFAULT false,
    reminder_datetime           timestamptz NOT NULL DEFAULT now(),

    updated_at                  timestamptz NOT NULL DEFAULT now(),
    updated_by_id               bigint,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    created_by_id               bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER task_set_updated_at
    BEFORE UPDATE ON public.task
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
