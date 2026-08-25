

DROP TABLE IF EXISTS public.token_blacklist;

CREATE TABLE public.token_blacklist (
    jti            uuid        PRIMARY KEY,
    user_id        integer     REFERENCES public.application_user(id) ON DELETE CASCADE,
    reason         text        NOT NULL DEFAULT '',
    expiry         timestamptz NOT NULL,
    blacklisted_on timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX token_blacklist_expiry_idx  ON public.token_blacklist (expiry);
CREATE INDEX token_blacklist_user_id_idx ON public.token_blacklist (user_id);

COMMENT ON TABLE public.token_blacklist IS
    'Revoked token IDs. Rows are deletable once expiry passes — the token fails validation anyway.';

