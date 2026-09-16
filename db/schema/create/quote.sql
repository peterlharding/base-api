
-- quote
CREATE TABLE public.quote (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    quote_date       date,
    quote_amount     numeric(12,2),

    quoter           varchar(64) NOT NULL,
    quoter_id        bigint,

    account_id       bigint,
    company          varchar(80) DEFAULT NULL,

    contact_id       bigint,
    contact          varchar(32) DEFAULT NULL,

    comment          text DEFAULT '',
    description      text DEFAULT '',

    order_no         varchar(32) DEFAULT NULL,
    order_date       date,
    order_amount     numeric(12,2),

    invoice_no       varchar(32) DEFAULT NULL,
    invoice_date     date,
    invoice_amount   numeric(12,2),

    status           varchar(16) DEFAULT 'Active',
    doc_path         text,

    updated_at       timestamptz NOT NULL DEFAULT now(),
    updated_by_id    bigint,
    created_at       timestamptz NOT NULL DEFAULT now(),
    created_by_id    bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER quote_set_updated_at
    BEFORE UPDATE ON public.quote
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
