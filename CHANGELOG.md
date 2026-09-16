# Changelog

All notable changes to base-api are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(minor bumps for new features while at 0.x).

## [0.8.0] - 2026-09-17

### Changed

- **Breaking for clients sending unknown fields.**
  The `*Create` and `*Update` schemas set `extra="forbid"`, so a field the
  schema does not define is a **422** naming it, rather than being silently
  dropped.
  Previously a `POST` carrying a misspelled field returned 201 with the value
  discarded, and a `PUT` carrying only misspelled fields returned 400
  "No fields provided to update" without saying which field was wrong.
  An empty `PUT` body carries no unknown field and is still the 400.
  The response schemas stay permissive: they are validated from ORM objects,
  not caller-supplied dicts.

### Added

- `TODO.md`, recording the outstanding work and the deliberate non-goals.
- `tests/test_payload_validation.py`, covering all twelve resources.

## [0.7.1] - 2026-09-17

### Added

- Migration `0005` indexes the 25 foreign key columns added in `0004`.
  Postgres indexes only the parent side of a foreign key, so a parent delete
  was scanning every referencing table to find the rows to set to NULL.
  Measured on `contact`: indistinguishable at 50k rows, roughly 4x faster at
  1M (47ms to 12ms), and widening, since the scan is O(n) and the lookup is
  not.
  Named `<table>_<column>_idx`, matching `login_session` and
  `token_blacklist`.
  Built inside the migration transaction rather than `CONCURRENTLY`: these
  tables are small enough that the lock is momentary, and a transactional
  build leaves nothing behind if it fails.

## [0.7.0] - 2026-09-16

### Added

- Migration `0004` adds 25 foreign keys across the CRM tables, all
  `ON DELETE SET NULL`, so deleting a parent orphans its children rather
  than destroying them.
  They are `DEFERRABLE INITIALLY IMMEDIATE`: `application_user.user_role_id`
  and `user_role.forecast_user_id` reference each other, so no insertion
  order satisfies both while constraints are checked per statement.
  `scripts/seed.py` issues `SET CONSTRAINTS ALL DEFERRED` for its load;
  ordinary requests still fail on the offending statement.
- `tests/test_foreign_keys.py` covers rejection of dangling references, the
  `SET NULL` behaviour on delete, and the columns that remain unconstrained.

### Changed

- The migration reconciles before it constrains: any reference that does not
  resolve is set to NULL first, so an existing database upgrades in place.
  Without it the migration succeeded on an empty database and failed on a
  populated one.
- `db/schema/data/application_user.sql` used `0` as a "none" sentinel for
  `delegated_approver_id`.
  Identity values start at 1, so `0` can never resolve; it is now NULL.

### Fixed

- A reference to a non-existent row is now rejected with 400 rather than
  silently stored.

## [0.6.0] - 2026-09-16

A CRM schema lands on top of the API scaffold, and the migration history is
squashed to accommodate it.

**Breaking.**
The migration chain was rewritten, `application_user` was redesigned, and the
models moved package.
An existing database cannot be migrated forward - it has to be rebuilt with
`make setup` followed by `make migrate`.

### Added

- Twelve CRM resources under `/api/v1`, each with the same CRUD shape as
  `users` (page with `limit`/`offset`, create, fetch-or-404, patch-style
  `PUT`, delete): `accounts`, `contacts`, `tasks`, `events`, `documents`,
  `notes`, `opportunities`, `leads`, `quotes`, `access` and `attachments`,
  for 24 routes in total.
- Thirteen SQLAlchemy models for the CRM and `audit_log` tables, all
  registered on `Base.metadata` so alembic autogenerate and the test suite's
  TRUNCATE see them.
- `app/api/v1/crud.py` - `commit()`, `get_or_404()` and `apply_update()`,
  shared by every endpoint module rather than repeated per resource.
- `audit_log` table, and `db/schema/create/*.sql` for the twelve CRM tables.
- `set_updated_at()` trigger function (`db/schema/ddl/`), installed on the
  thirteen tables that carry an `updated_at` column.
- Sample data: `db/schema/data/*.sql` (13 files, 2 rows each) plus
  `scripts/seed.py`, exposed as `make seed` and `make seed-reset`.
  Deliberately outside the migration chain - see the script's docstring.
- `DB_PORT`, `TEST_DB_PORT` and `DB_NAME` are read from the repo-root `.env`
  by the application, both compose stacks and the Makefiles, so the host
  ports and database name are chosen in exactly one place.
- `db/schema/sql/` holds the role and database bootstrap scripts, kept apart
  from `db/schema/create/` because migrations never execute them.
  `setup/` holds `env.template` and `SETUP.md`.
- `CLAUDE.md`, guidance for future Claude Code sessions.
- 141 tests, taking the suite from 15 to 156.

### Changed

- **`application_user` redesigned** along CRM lines: `bigint` identity primary
  key, and `user_guid`->`guid`, `password`->`hashed_password`,
  `timezone_key`->`timezone_sid_key`, `locale_key`->`locale_sid_key`,
  `created_date`->`created_at`, `last_modified_date`->`updated_at`,
  `last_modified_by_id`->`updated_by_id`, plus `phone_extension`,
  `receives_info_emails` and `receives_admin_info_emails`.
  `when_modified` is gone.
  The model, API schemas and tests follow the new names.
- **Migration chain squashed** from `0001`-`0008` to three revisions:
  `0001` (trigger function + `application_user`), `0002` (the API tables) and
  `0003` (the twelve CRM tables).
  Migrations now execute SQL from `db/schema/`, resolved from `__file__`
  rather than the working directory.
- `db/schema/create/*.sql` is migration payload rather than standalone
  bootstrap, so the `DROP TABLE IF EXISTS` headers were removed - a re-run
  would otherwise destroy data.
- `make setup` creates the roles and an **empty** database only; alembic owns
  every table.
  Dev and test are therefore built by the identical path and cannot drift.
- `app/db/models/` moved to `app/models/`, and `app/db/base.py` to
  `app/models/base.py`, so the declarative base sits with the models.
- `token_blacklist.user_id` and `login_session.user_id` widened from
  `integer` to `bigint` to match `application_user.id`.
- The test suite truncates **before** each test rather than after, so a stray
  row left in the container cannot fail the first test of a run.
- `db/alembic.ini` resolves `script_location` with `%(here)s`, so the
  `alembic` CLI and `pytest` both work from any directory.

### Removed

- `.env.example`, superseded by `setup/env.template`.
- `db/schema/create/03-create-application_user.sql`, superseded by
  `application_user.sql`.
- `db/schema/ddl/set_when_modified.sql`, superseded by `set_updated_at.sql`.

### Fixed

- `make setup` failed with `syntax error at or near ":"`.
  psql does not substitute `:variables` inside a dollar-quoted `$$ ... $$`
  block, so the server received a literal `:db_password`.
  The role DDL is now generated outside any dollar quote and run with
  `\gexec`.
- psql is invoked with `-v ON_ERROR_STOP=1` throughout.
  Reading a script from stdin it otherwise reports an error and still exits
  0, so `make` stepped over the failure and the real cause was buried.
- A duplicate email returned 500 rather than 409.
  `commit()` now translates unique violations to **409** and foreign-key,
  not-null and check violations to **400**, rolling back first so the session
  stays usable.
- `db/alembic/env.py` and `tests/conftest.py` still imported the old
  `app.db.models` path and failed at import.

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
