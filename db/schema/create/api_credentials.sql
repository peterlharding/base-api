CREATE TABLE api_credentials (
    id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guid            uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    email           character varying(128) NOT NULL UNIQUE,
    hashed_password character varying(128) NOT NULL
);

-- Data for Name: api_credentials;
--
-- OVERRIDING SYSTEM VALUE: id is GENERATED ALWAYS AS IDENTITY, so a plain
-- INSERT of explicit ids is rejected by Postgres.

INSERT INTO public.api_credentials (id, guid, email, hashed_password)
    OVERRIDING SYSTEM VALUE
VALUES
  (1, 'ff40bf6f-e202-4348-8a05-d84a9098d2d2', 'api@performiq.com',       'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98');

