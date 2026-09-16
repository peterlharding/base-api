
--  ---------------------------------------------------------------------------
-- audit_log
--  ---------------------------------------------------------------------------

CREATE TABLE public.audit_log (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application     varchar(32) NOT NULL,
    reference_type  integer NOT NULL,
    reference_id    integer NOT NULL,
    reference       varchar(50),
    event           varchar(50) NOT NULL,
    description     varchar(256) NOT NULL,
    user_id         varchar(50) NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

--  ---------------------------------------------------------------------------

