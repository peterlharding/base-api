
-- contact
CREATE TABLE public.contact (
    id                       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                     varchar(18),

    salutation               varchar(24),
    first_name               varchar(32),
    last_name                varchar(64),

    title                    varchar(96),
    department               varchar(96),
    account_id               bigint,

    description              text,
    notes                    text,

    other_street             varchar(96),
    other_city               varchar(32),
    other_state              varchar(20),
    other_postal_code        varchar(18),
    other_country            varchar(18),

    mailing_street           varchar(96),
    mailing_city             varchar(32),
    mailing_state            varchar(20),
    mailing_postal_code      varchar(10),
    mailing_country          varchar(32),

    phone                    varchar(18),
    fax                      varchar(18),
    mobile_phone             varchar(18),
    home_phone               varchar(18),
    other_phone              varchar(18),
    email                    varchar(64),

    assistant_name           varchar(96),
    assistant_phone          varchar(18),

    reports_to_id            bigint,

    owner_id                 bigint,

    lead_source              text,

    birthdate                date,

    do_not_call              boolean  DEFAULT false,
    has_opted_out_of_email   boolean  DEFAULT false,
    has_opted_out_of_fax     boolean  DEFAULT false,

    last_activity_date       timestamptz NOT NULL DEFAULT now(),

    is_deleted               boolean DEFAULT false,

    created_at               timestamptz NOT NULL DEFAULT now(),
    created_by_id            bigint,
    updated_at               timestamptz NOT NULL DEFAULT now(),
    updated_by_id            bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER contact_set_updated_at
    BEFORE UPDATE ON public.contact
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
