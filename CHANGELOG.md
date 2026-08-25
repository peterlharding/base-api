# Changelog

All notable changes to base-api are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(minor bumps for new features while at 0.x).

## [0.5.0] - 2026-08-25

### Added

- SQLAlchemy models for the new tables (migrations 0003–0006), so the
  credentials/session/instance schema is usable from application code:
  - `ApiCredential` (`api_credentials`) — identity `id`, `gen_random_uuid()`
    `user_guid`, unique `email`.
  - `TokenBlacklist` (`token_blacklist`) — uuid `jti` primary key,
    `application_user` FK with `ON DELETE CASCADE`, `expiry`/`user_id`
    indexes and the table comment.
  - `LoginSession` (`login_session`) — bigint identity `id`, bytea token
    hash, inet, jsonb `data`, 12-hour default expiry, the named unique
    and check constraints, and the `user_id`/`expires_at` indexes.
  - `instance_metadata` — a Core `Table` on `Base.metadata` rather than
    an ORM class: the singleton table has no primary key, which the ORM
    cannot map; the unique index on `(true)` and the trigger stay in the
    migration.
- `ApplicationUser.when_modified` — the `timestamptz` column added by
  migration `0002` but missing from the model (trigger-maintained, never
  written by the app).  Models are now an exact mirror of the migrated
  schema: `alembic revision --autogenerate` reports no diff beyond the
  un-expressible `instance_metadata_singleton` functional index.

### Changed

- `app/db/models.py` is now an `app/db/models/` package with one module
  per table; `app/db/models/__init__.py` re-exports everything, so
  existing imports (`from app.db.models import ApplicationUser`,
  `from app.db import models`) are unchanged.

## [0.4.0] - 2026-08-25

### Added

- Alembic migrations for the new credentials/session/instance schema — a
  fresh database now builds fully with `alembic upgrade head`
  (chain `0001` → `0006`):
  - `0002` — `set_when_modified()` trigger function and the
    `application_user_set_when_modified` trigger; adds the
    `when_modified timestamptz` column to `application_user` that the
    trigger maintains.
  - `0003` — `api_credentials` (identity `id`, uuid `user_guid`, unique
    `email`) seeded with the four bootstrap credential rows.
  - `0004` — `token_blacklist` (uuid `jti` primary key, `application_user`
    FK with `ON DELETE CASCADE`, `expiry`/`user_id` indexes, table comment).
  - `0005` — `instance_metadata` singleton (unique index on `(true)`),
    release/version check constraints, `set_when_modified` trigger.
  - `0006` — `login_session` (bytea token hash, inet, jsonb `data`,
    12-hour default expiry, check constraints, indexes) and the
    `login_session_active` view.
- Matching SQL scripts: `api_credentials.sql`, `token_blacklist.sql`,
  `instance_metadata.sql` and `login_session.sql` under
  `db/schema/create/`, plus `db/schema/ddl/set_when_modified.sql`.
- Dev tooling: `scripts/docker-chk.sh` docker check script; `git-chk`
  extended with `log -8` and `show --stat`; test-design notes in
  `doc/NOTES.md`.

### Changed

- Moved the DB-creation SQL scripts from `docker/db/` into `db/schema/`
  (`create/` and `ddl/`); setup and docs updated to match.
- `uv.lock` is no longer tracked (added to `.gitignore`); regenerate it
  locally with `uv lock` / `uv sync`.

### Fixed

- `api_credentials.sql` seed INSERT now uses `OVERRIDING SYSTEM VALUE`:
  `id` is `GENERATED ALWAYS AS IDENTITY`, so the explicit-id insert was
  rejected by Postgres. The `0003` migration applies the same fix.

## [0.3.0] - 2026-08-24

### Added

- Test suite: pytest running the real app end-to-end against a dedicated,
  disposable Postgres (`docker/test/docker-compose.yml` — 127.0.0.1:5433,
  database `base_api_test`, no volume). It never touches the dev stack
  (5432 / `base_api`); both run side by side.
- `tests/conftest.py` pins `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_PASSWORD`
  before the app is imported, so the real engine, `SessionLocal` and alembic
  all target the test database — no app changes, no dependency overrides.
  A session fixture runs the real migrations (`alembic upgrade head`); an
  autouse fixture truncates every table `RESTART IDENTITY` after each test,
  keeping primary keys predictable.
- `tests/test_users.py` — 10 end-to-end tests for `/api/v1/users` (health,
  paged list, create with server defaults, validation 422s, 404/400 paths,
  patch semantics, delete).
- Makefile targets: `test`, `test-db-up` (idempotent, waits on `pg_isready`),
  `test-db-down`, `test-db-reset` (fresh database, migrations re-run).
- Dev dependencies (`pytest`, `httpx2`) in the uv `dev` dependency group.
- `doc/TESTING.md` — how the test database works and how to add tests.

### Fixed

- Alembic migration `0001` called `op.create_sequence()`, which is not a real
  alembic op — it had never actually run, because the dev database was built
  from the psql scripts. Replaced with raw `op.execute` DDL, so a fresh
  database can now really be built with `alembic upgrade head`.

## [0.2.0] - 2026-08-23

### Added

- Versioned API layer at `/api/v1` (`app/api/v1/`, mounted in `create_app()`).
- Users CRUD endpoints for `application_user`, served under `/api/v1/users`:
  - `GET /api/v1/users` — paged list in id order (`limit` default 50, max 200; `offset`).
  - `POST /api/v1/users` — create a user; only `username` is mandatory (201 on success).
  - `GET /api/v1/users/{id}` — fetch one user by surrogate key (404 if missing).
  - `PUT /api/v1/users/{id}` — patch-style update: only the fields present in the
    payload are changed; an empty payload is rejected with 400.
  - `DELETE /api/v1/users/{id}` — delete (204 on success).
- Pydantic schemas `UserCreate` / `UserUpdate` / `User` in `app/api/v1/schemas.py`.
  `password` and the `*_by_id` audit stamps are never exposed or written through the API;
  `created_date` / `last_modified_date` / `last_login_date` are read back only.
- Path parameter is named `id` (the table's surrogate key) so it cannot be confused
  with the legacy string `user_id` column, which remains an ordinary field.
- Database server defaults (e.g. `timezone_key = 'Australia/Melbourne'`,
  `user_type = 'Standard'`) pass through unchanged on create.

### Changed

- Moved the Alembic configuration into `db/` (`db/alembic.ini`, `db/alembic/`);
  `migrate` and `autogenerate` now run `alembic -c db/alembic.ini`, and `env.py`
  resolves the repo root from one level deeper.

## [0.1.0] - 2026-08-23

### Added

- FastAPI application scaffold: `create_app()` in `app/main.py` with a `/health`
  liveness probe that also reports database reachability (503 when down).
- Postgres setup for the `base_api` database (see `docker/db/SETUP.md`) and
  `app/core/config.py` settings loaded from the environment / `.env`.
- SQLAlchemy models mirroring `application_user` (`app/db/models.py`), engine and
  per-request session dependency (`app/db/session.py`), and Alembic migration `0001`
  building the table from scratch.
- uv tooling (`pyproject.toml`, `uv.lock`) and Makefile targets:
  `install`, `run`, `dev`, `migrate`, `autogenerate`.
