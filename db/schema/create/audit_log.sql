
--  ---------------------------------------------------------------------------
-- audit_log
--
-- Written by the API itself, in app/api/v1/crud.py, which every mutation
-- already passes through.  Nothing else writes here: an entry a client can
-- compose is an entry a client can fabricate or omit.
--
-- Mutations only.  Reads are not recorded - on a CRM the list endpoints would
-- produce far more rows than everything else combined.  action is free text
-- rather than a constrained set so 'login', 'export' or 'convert-lead' can be
-- added later without a migration.
--  ---------------------------------------------------------------------------

CREATE TABLE public.audit_log (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application     varchar(32) NOT NULL,           -- which app is reporting
    action          varchar(32) NOT NULL,           -- create | update | delete
    reference_type  varchar(64) NOT NULL,           -- the table affected
    reference_id    bigint,                         -- the row, where there is one

    description     text NOT NULL DEFAULT '',       -- what changed

    -- The acting user's guid rather than a foreign key to application_user:
    -- an audit entry has to outlive the user it names.
    user_id         varchar(50) NOT NULL,

    created_at      timestamptz NOT NULL DEFAULT now()
);

--  ---------------------------------------------------------------------------
-- Read patterns: what happened to this row, and what has this user been doing.

CREATE INDEX audit_log_reference_idx  ON public.audit_log (reference_type, reference_id);
CREATE INDEX audit_log_user_id_idx    ON public.audit_log (user_id);
CREATE INDEX audit_log_created_at_idx ON public.audit_log (created_at DESC);

--  ---------------------------------------------------------------------------
