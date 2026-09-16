
-- account
CREATE TABLE public.account (
    id                    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                  uuid,

    name                  varchar(128),
    type                  varchar(32),
    description           text,
    notes                 text,

    record_type_ref       uuid,
    parent_id             bigint,

    billing_street        text,
    billing_city          varchar(32),
    billing_state         varchar(20),
    billing_postal_code   varchar(10),
    billing_country       varchar(32),

    shipping_street       text,
    shipping_city         varchar(32),
    shipping_state        varchar(20),
    shipping_postal_code  varchar(10),
    shipping_country      varchar(32),

    phone                 varchar(18),
    fax                   varchar(18),

    account_number        varchar(32),
    website               text,
    sic                   varchar(32),
    industry              varchar(32),
    annual_revenue        varchar(32),
    number_of_employees   varchar(32),
    ownership             varchar(32),
    ticker_symbol         varchar(18),
    rating                varchar(18),
    site                  text,

    owner_id              bigint,

    is_deleted            boolean DEFAULT false,

    last_activity_date    date,
    operating_systems     text  DEFAULT '',

    created_at            timestamptz NOT NULL DEFAULT now(),
    created_by_id         bigint,
    updated_at            timestamptz NOT NULL DEFAULT now(),
    updated_by_id         bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER account_set_updated_at
    BEFORE UPDATE ON public.account
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
