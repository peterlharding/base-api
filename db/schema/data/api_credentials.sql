
-- api_credentials sample data
--
-- Moved out of db/schema/create/api_credentials.sql, which migration 0002
-- executes.  A migration runs once, so a credential seeded there could never
-- be changed again without a further migration - which is exactly what
-- happened when the hashes moved from SHA-256 to bcrypt.
--
-- Passwords are bcrypt-hashed (app/auth/password.py).  The plaintext is
-- 'sample-password'.  Regenerate with:
--     python -m app.auth.password '<password>'

INSERT INTO public.api_credentials (guid, email, hashed_password)
VALUES
(
    'ff40bf6f-e202-4348-8a05-d84a9098d2d2',
    'api@performiq.com',
    '$2b$12$simuD1Jkz4Vt7j4eXO0eZu8rDdPFZBh7KpPCiwAoOqLhwtI.PSwD.'
);
