
DROP TABLE IF EXISTS public.login_session;

CREATE TABLE public.login_session (
    id                 bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_token_hash bytea       NOT NULL,
    user_id            integer     NOT NULL
                                   REFERENCES public.application_user(id) ON DELETE CASCADE,
    workstation        text,
    ip_address         inet,
    user_agent         text,
    data               jsonb       NOT NULL DEFAULT '{}'::jsonb,
    started            timestamptz NOT NULL DEFAULT now(),
    last_seen          timestamptz NOT NULL DEFAULT now(),
    expires_at         timestamptz NOT NULL DEFAULT now() + interval '12 hours',
    revoked_at         timestamptz,

    CONSTRAINT login_session_token_key    UNIQUE (session_token_hash),
    CONSTRAINT login_session_expiry_check CHECK (expires_at > started),
    CONSTRAINT login_session_data_object  CHECK (jsonb_typeof(data) = 'object')
);

CREATE INDEX login_session_user_id_idx    ON public.login_session (user_id);
CREATE INDEX login_session_expires_at_idx ON public.login_session (expires_at);

CREATE VIEW public.login_session_active AS
    SELECT * FROM public.login_session
    WHERE revoked_at IS NULL
      AND expires_at > now();


