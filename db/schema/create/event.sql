-- event
CREATE TABLE public.event (
    id                           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                         varchar(18),

    who_ref                      varchar(18),
    what_ref                     varchar(18),

    subject                      varchar(128),
    description                  text,
    location                     varchar(32),

    type                         varchar(64),
    show_as                      varchar(32),

    activity_date                date,
    activity_datetime            timestamptz NOT NULL DEFAULT now(),

    is_all_day_event             boolean DEFAULT false,

    duration_in_minutes          integer DEFAULT 0,

    account_id                   varchar(18),
    owner_id                     varchar(18),

    is_group_event               boolean DEFAULT false,
    is_private                   boolean DEFAULT false,
    is_child                     boolean DEFAULT false,
    is_archived                  boolean DEFAULT false,
    is_deleted                   boolean DEFAULT false,

    is_recurrence                boolean DEFAULT false,
    recurrence_activity_id       varchar(18),
    recurrence_start_datetime    timestamptz NOT NULL DEFAULT now(),
    recurrence_end_date_only     date,
    recurrence_timezone_sid_key  varchar(32),
    recurrence_type              varchar(32),
    recurrence_interval          varchar(32),
    recurrence_day_of_week_mask  varchar(32),
    recurrence_day_of_month      varchar(32),
    recurrence_instance          varchar(32),
    recurrence_month_of_year     varchar(32),

    is_reminder_set              boolean DEFAULT false,
    reminder_datetime            timestamptz NOT NULL DEFAULT now(),

    updated_at                   timestamptz NOT NULL DEFAULT now(),
    updated_by_id                bigint,
    created_at                   timestamptz NOT NULL DEFAULT now(),
    created_by_id                bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER event_set_updated_at
    BEFORE UPDATE ON public.event
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
