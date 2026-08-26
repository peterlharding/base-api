-- Create the application_user table in the base_api database.
--
-- Must run against base_api (not the postgres maintenance database), after
-- 02-create-database.sql:
--
--   psql -U postgres -d base_api -f 03-create-application_user.sql
--
-- Idempotent: does nothing if the table already exists.

CREATE SEQUENCE IF NOT EXISTS application_user_id_seq;

CREATE TABLE IF NOT EXISTS public.application_user (
    id                    integer                     NOT NULL DEFAULT nextval('application_user_id_seq'::regclass),
    user_guid             uuid,
    username              character varying(32),
    password              character varying(128),
    first_name            character varying(32),
    last_name             character varying(32),
    company_name          character varying(32),
    division              character varying(32),
    department            character varying(40),
    title                 character varying(40),
    street                character varying(40),
    city                  character varying(32),
    state                 character varying(32),
    postal_code           character varying(18),
    country               character varying(32),
    email                 character varying(64),
    phone                 character varying(24),
    fax                   character varying(24),
    mobile_phone          character varying(24),
    alias                 character varying(24),
    is_active             boolean                     DEFAULT true,
    timezone_key          character varying(32)       DEFAULT 'Australia/Melbourne',
    user_role_id          integer,
    locale_key            character varying(12)       DEFAULT 'en_AU',
    email_encoding_key    character varying(18)       DEFAULT 'ISO-8859-1',
    profile_id            integer,
    employee_number       character varying(20),
    user_type             character varying(20)       DEFAULT 'Standard',
    start_day             integer                     DEFAULT 6,
    end_day               integer                     DEFAULT 23,
    language_locale_key   character varying(12)       DEFAULT 'en_US',
    delegated_approver_id integer,
    last_login_date       timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_date          timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id         integer,
    last_modified_date    timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_modified_by_id   integer,
    PRIMARY KEY (id)
);

-- Same ownership as a SERIAL column, so dropping the table drops the sequence.
ALTER SEQUENCE application_user_id_seq OWNED BY public.application_user.id;
