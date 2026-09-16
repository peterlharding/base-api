
-- user_role
CREATE TABLE public.user_role (
    id                                    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                                  uuid,
    name                                  varchar(64),

    parent_role_id                        bigint,
    rollup_description                    text,

    opportunity_access_for_account_owner  varchar(20) DEFAULT 'Edit',
    case_access_for_account_owner         varchar(20) DEFAULT 'Edit',
    contact_access_for_account_owner      varchar(20) DEFAULT 'Edit',

    forecast_user_id                      bigint,

    portal_account_ref                    varchar(18),
    portal_type                           varchar(20),

    updated_at                            timestamptz NOT NULL DEFAULT now(),
    updated_by_id                         bigint,
    created_at                            timestamptz NOT NULL DEFAULT now(),
    created_by_id                         bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER user_role_set_updated_at
    BEFORE UPDATE ON public.user_role
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
