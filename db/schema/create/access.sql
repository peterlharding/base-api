
-- access
CREATE TABLE public.access (
    id                    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    access_type           varchar(20) DEFAULT NULL,   -- 'Create', 'Update', 'View', 
    reference_name        varchar(255) DEFAULT NULL,
    reference_type        varchar(32) DEFAULT NULL,

    reference_id          bigint,
    owner_id              bigint,
    user_id               bigint,

    last_referenced_date  timestamptz NOT NULL DEFAULT now()
);

