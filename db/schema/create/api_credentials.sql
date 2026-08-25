
DROP TABLE IF EXISTS api_credentials;

CREATE TABLE api_credentials (
    id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_guid       uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    email           character varying(128) NOT NULL UNIQUE,
    hashed_password character varying(128) NOT NULL
);

-- Data for Name: api_credentials;
--
-- OVERRIDING SYSTEM VALUE: id is GENERATED ALWAYS AS IDENTITY, so a plain
-- INSERT of explicit ids is rejected by Postgres.

INSERT INTO public.api_credentials (id, user_guid, email, hashed_password)
    OVERRIDING SYSTEM VALUE
VALUES
  (1, 'ff40bf6f-e202-4348-8a05-d84a9098d2d2', 'api@performiq.com',       'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98'),
  (2, 'bcc26c7e-3124-4023-a743-2ffa11a6731e', 'plh@performiq.com',       'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98'),
  (3, '148e1d8f-97f5-45b4-bfbc-d9da86f1c0ed', 'peterlharding@gmail.com', 'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98'),
  (4, '8bd2c76a-2018-41e1-bd97-87ae639a3aba', 'bgg@gobject-craft.com.au','c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98');


