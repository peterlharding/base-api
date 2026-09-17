CREATE TABLE api_credentials (
    id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid            uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    email           character varying(128) NOT NULL UNIQUE,
    hashed_password character varying(128) NOT NULL
);
