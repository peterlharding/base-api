
-- application_user
CREATE TABLE public.application_user (
    id                          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid                        uuid,

    username                    varchar(32),
    hashed_password             varchar(255),
    alias                       varchar(32),

    first_name                  varchar(32),
    last_name                   varchar(32),

    company_name                varchar(100),
    division                    varchar(32),
    department                  varchar(100),
    title                       varchar(100),

    street                      varchar(100),
    city                        varchar(50),
    state                       varchar(32),
    postal_code                 varchar(20),
    country                     varchar(100),

    email                       varchar(255) UNIQUE,
    phone                       varchar(20),
    phone_extension             varchar(10),
    fax                         varchar(20),
    mobile_phone                varchar(20),

    is_active                   boolean DEFAULT true,

    user_role_id                bigint,
    user_type                   varchar(20) DEFAULT 'Standard',
    profile_id                  bigint,

    timezone_sid_key            varchar(32) DEFAULT 'Australia/Melbourne',

    locale_sid_key              varchar(32) DEFAULT 'en_AU',
    language_locale_key         varchar(32) DEFAULT 'en_US',

    receives_info_emails        boolean DEFAULT false,
    receives_admin_info_emails  boolean DEFAULT false,
    email_encoding_key          varchar(32) DEFAULT 'ISO-8859-1',

    employee_number             varchar(50),
    delegated_approver_id       bigint,

    start_day                   integer DEFAULT 6,
    end_day                     integer DEFAULT 23,

    last_login_date             timestamptz,

    created_at                  timestamptz NOT NULL DEFAULT now(),
    created_by_id               bigint,
    updated_at                  timestamptz NOT NULL DEFAULT now(),
    updated_by_id               bigint
);

-- ---------------------------------------------------------------------------
-- Maintained by db/schema/ddl/set_updated_at.sql

CREATE TRIGGER application_user_set_updated_at
    BEFORE UPDATE ON public.application_user
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
