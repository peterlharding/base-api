
-- lead

DROP   TABLE IF EXISTS public.lead;

CREATE TABLE public.lead (
    id                        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                      uuid,

    description               text,

    salutation                varchar(24),
    first_name                varchar(32),
    last_name                 varchar(64),

    title                     varchar(128),
    company                   varchar(96),

    street                    text,
    city                      varchar(64),
    state                     varchar(32),
    postal_code               varchar(18),
    country                   varchar(32),

    phone                     varchar(18),
    mobile_phone              varchar(18),
    fax                       varchar(18),
    email                     varchar(64),
    website                   varchar(64),

    lead_source               varchar(96),
    status                    varchar(32),
    industry                  varchar(32),
    rating                    varchar(32),
    annual_revenue            varchar(32),
    number_of_employees       varchar(32),

    owner_id                  bigint,

    do_not_call               boolean DEFAULT false,
    has_opted_out_of_fax      boolean DEFAULT false,
    has_opted_out_of_email    boolean DEFAULT false,
    is_unread_by_owner        boolean DEFAULT false,
    is_deleted                boolean DEFAULT false,

    is_converted              boolean DEFAULT false,
    converted_date            timestamptz NOT NULL DEFAULT now(),
    converted_account_id      bigint,
    converted_contact_id      bigint,
    converted_opportunity_id  bigint,

    activity_date             timestamptz NOT NULL DEFAULT now(),
    transfer_date             timestamptz NOT NULL DEFAULT now(),

    operating_systems         text DEFAULT NULL,
    master_record_ref         varchar(18),

    updated_at                timestamptz NOT NULL DEFAULT now(),
    updated_by_id             bigint,
    created_at                timestamptz NOT NULL DEFAULT now(),
    created_by_id             bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER lead_set_updated_at
    BEFORE UPDATE ON public.lead
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
