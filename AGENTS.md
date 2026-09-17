# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Commands

All commands run from the repo root.
The venv is `.venv/` and is driven by `uv`; the Makefile calls `.venv/bin/...` directly rather than relying on activation.

```sh
make install        # uv sync (creates .venv from pyproject.toml / uv.lock)
make dev            # uvicorn with --reload, on $HOST:$API_PORT from .env
make run            # uvicorn without reload
make test           # starts the test Postgres, waits for it, runs pytest
make test-db-up     # start / wait on the test container only
make test-db-down   # stop it (its data is discarded)
make test-db-reset  # down + up: clean database, migrations re-run
make migrate        # alembic -c db/alembic.ini upgrade head
make seed           # load db/schema/data sample rows (refuses if tables are non-empty)
make seed-reset     # truncate the seeded tables first, then load
make prune-blacklist          # delete expired token_blacklist rows
make prune-blacklist-dry-run  # report what would be deleted
make autogenerate msg="..."   # alembic revision --autogenerate
make git-chk        # status + last 8 commits + stat of HEAD
```

Single test, once the container is up (plain `pytest` works too):

```sh
.venv/bin/pytest tests/test_users.py::test_create_minimal_populates_defaults
```

There is no linter or formatter configured in this repo.

## Configuration

`.env` at the repo root is the single source of truth for host ports and credentials.
Four consumers read it, three of them not through pydantic-settings, so keep them in mind when adding a key.

* `app/core/config.py` (`Settings`, pydantic-settings) reads it for the app: `APP_NAME`, `APP_TITLE`, `HOST`, `API_PORT`, and the `DB_*` connection fields.
  Real environment variables take priority over `.env`, which is the mechanism the test suite relies on.
* `tests/conftest.py` reads the `TEST_*` keys through its own `_TestDb` settings class (see Testing below).
* Both compose stacks interpolate it; the Makefiles pass it with `docker compose --env-file ... -f ...`.
  `--env-file` is a top-level flag and must precede the subcommand.
* The Makefiles grep it textually.
  Those greps are anchored (`'^DB_PORT='`) on purpose: unanchored, `DB_PORT=` also matches the `TEST_DB_PORT=` line and feeds two values into `sed`.

Ports and the database name are never hardcoded outside `.env`.
`db/schema/sql/02-create-database.sql` takes `DB_NAME` as the psql variable `db_name`, so the database `make setup` creates is always the one `Settings.db_name` connects to.
`DB_PORT` drives the dev stack and the app; `TEST_DB_PORT` drives the test stack and the suite.
The names are deliberately distinct so that pointing `DB_PORT` at dev cannot redirect the tests.
Both compose files carry `${...:-5432}` / `${...:-5433}` fallbacks, so a checkout with no `.env` still comes up.

`.env` is gitignored; `setup/env.template` is the committed template and the only record of the required keys.

`get_settings()` is `@lru_cache`d, so environment changes after first call have no effect within a process.
This is why `tests/conftest.py` defines its own settings class rather than calling `get_settings()`: doing so would cache the dev settings before `app/db/session.py` builds its engine.

## Architecture

FastAPI + SQLAlchemy 2.0 (sync, `Mapped[...]` / `mapped_column`) + psycopg 3 against Postgres.
Python >= 3.14.

```
app/main.py            create_app(): mounts api_router, defines /health
app/core/config.py     Settings + get_settings() (lru_cache); .database_url
app/db/session.py      engine + SessionLocal, built AT IMPORT TIME; get_db() dependency
app/models/base.py     DeclarativeBase `Base` - the metadata everything keys off
app/models/            one module per table; __init__ imports all 18 of them
app/api/v1/router.py   api_router, prefix /api/v1
app/api/v1/schemas.py  pydantic request/response models
app/api/v1/crud.py     shared commit/get_or_404/apply_update helpers
app/api/v1/endpoints/  one module per resource, plus auth and three that are
                       not plain CRUD: audit_log, login_sessions,
                       instance_metadata
app/auth/              password hashing, JWT sign/decode, bearer dependency
app/core/version.py    app version, read from pyproject.toml
db/alembic/            migrations (env.py reuses get_settings())
db/schema/create/      table DDL - executed by the migrations, not standalone
db/schema/ddl/         the set_updated_at trigger function
db/schema/sql/         role + database bootstrap, run by `make setup`
db/schema/data/        sample rows, loaded by `make seed`
setup/                 .env template and SETUP.md
docker/db/             dev Postgres stack
docker/test/           throwaway Postgres for the test suite
```

Three consequences of this layout are worth knowing before changing anything:

**The engine is created at import time.**
`app/db/session.py` calls `create_engine(get_settings().database_url)` at module scope.
Anything that needs to point the app at a different database must set the `DB_*` environment variables before `app.db.session` is first imported.
This is why `tests/conftest.py` sets them at the very top of the file, above its own imports, and why no dependency override is needed.

**`Base.metadata` is the single source of truth for "all tables".**
Alembic autogenerate and the test suite's per-test TRUNCATE both iterate it.
A new model must be imported in `app/models/__init__.py` or it is invisible to both.

**Models mirror the migrated schema exactly, including server defaults.**
Columns carry `server_default=text(...)` so `alembic revision --autogenerate` reports no diff, and so creates return the database's own defaults (timezone `Australia/Melbourne`, `user_type` `Standard`, and so on) rather than Python-side values.
The one deliberate exception autogenerate still reports is the `instance_metadata_singleton` functional index, which cannot be expressed in metadata.
`instance_metadata` is a Core `Table` rather than an ORM class because the singleton table has no primary key.

### Alembic owns the schema

`db/alembic/versions/` is the sole authority for every table.
Dev and test are built by the identical path, so they cannot drift:

* `make setup` (in `docker/db/`) runs `db/schema/sql/01-create-users.sql` and `db/schema/sql/02-create-database.sql`, creating the roles and an **empty** database.
* `make migrate` (repo root) runs `alembic upgrade head` and creates the tables, exactly as the test suite's session fixture does.

The migrations do not write DDL inline; each one executes SQL from `db/schema/`, resolved from `__file__` rather than the cwd:

```python
_SCHEMA = Path(__file__).resolve().parents[2] / "schema"
op.execute(_sql("create", "contact.sql"))
```

So `db/schema/create/*.sql` is migration payload, not reference material.
`db/schema/sql/` is the exception, and the reason it is a sibling of `create/` rather than part of it: `db/schema/sql/01-create-users.sql` and `db/schema/sql/02-create-database.sql` create the roles and the database itself, are run by `make setup`, and are never touched by a migration.
Two consequences: those scripts must not contain `DROP TABLE` (a re-run would destroy data), and a schema edit means editing the `.sql` file plus adding a migration that applies the change to existing databases.

That second rule does **not** hold for constraints.
Postgres has no `ADD CONSTRAINT IF NOT EXISTS`, so a constraint written into a create script *and* added by a later migration is applied twice on a fresh build, and the migration fails.
Constraints therefore live only in the migration that introduces them, which is why `0004` adds 25 foreign keys that `db/schema/create/*.sql` does not mention.

The chain is three migrations, each executing a group of scripts:

| revision | installs |
|---|---|
| `0001` | `set_updated_at()` and `application_user` |
| `0002` | `api_credentials`, `token_blacklist`, `instance_metadata`, `audit_log`, `login_session` |
| `0003` | the 12 CRM tables |

Ordering is load-bearing.
`application_user` is created in `0001` alongside the trigger function, because `token_blacklist` and `login_session` in `0002` both carry a foreign key to `application_user(id)`.
The 12 CRM tables declare no foreign keys at all, so their load order within `0003` is unconstrained.

`updated_at` is maintained by the `set_updated_at()` trigger function, defined once in `db/schema/ddl/set_updated_at.sql` and installed by a `CREATE TRIGGER` at the foot of each create script that has an `updated_at` column (13 of them).
The function is never called by application code and `updated_at` must never be written by it.

`db/schema/sql/01-create-users.sql` takes the shared role password as the psql variable `db_password` so it never lands in the repo.
Note that psql does **not** substitute `:variables` inside a dollar-quoted `$$ ... $$` block; the server receives a literal `:db_password` and fails with `syntax error at or near ":"`.
Role DDL is therefore generated outside any dollar quote and run with `\gexec`.

`db/alembic.ini` sets `script_location = %(here)s/alembic`, so the `alembic` CLI works from any directory, as does `pytest`.

Always pass `-v ON_ERROR_STOP=1` when feeding psql a script on stdin.
Without it psql reports a SQL error and still exits 0, so `make` steps over the failure and the real cause gets buried under its fallout.

### Sample data is not in the migration chain

`db/schema/data/*.sql` is sample data (2 rows per table), loaded by `scripts/seed.py` via `make seed`, never by a migration.
Three reasons, all of which bite in practice:

* Migrations replay on every environment, production included.
* `conftest.py` truncates every table in `Base.metadata` after **each** test while migrations run **once** per session, so migration-seeded rows survive only until the first test finishes.
  The `api_credentials` row seeded by `0002` already demonstrates this: 1 row after `make migrate`, 0 after `make test`.
* The files assume their rows land on ids 1 and 2 and cross-reference them (`owner_id`, `created_by_id`, `parent_role_id`), but identity values are consumed by failed inserts and reset by `TRUNCATE`.

The loader refuses to run against non-empty tables, because the `INSERT`s carry no conflict handling and simply append.
Use `make seed-reset` to truncate first.
`ORDER` in `scripts/seed.py` loads `application_user` first; the tables declare no foreign keys, so nothing enforces that, but the cross-references are meaningless without it.

### Adding a model

`app/models/__init__.py` must import it, or it is invisible to both alembic autogenerate and the test suite's per-test TRUNCATE: autogenerate will propose **dropping** its table, and the suite will not clean it between tests.
All 18 tables are currently registered, and `make autogenerate` reports no diff beyond the `instance_metadata_singleton` functional index, which cannot be expressed in metadata.
Any other diff means a model and its `db/schema/create/*.sql` have drifted; the SQL is the authority.

`Base` lives in `app/models/base.py`, beside the models.
There must be exactly one `DeclarativeBase`: a second would create a second metadata and split the models across the two silently, which no error would report.

Audit columns are named `updated_at` / `updated_by_id` throughout, matching the SQL and the `set_updated_at()` trigger.

### Three resources are not plain CRUD

Most endpoints are the same five operations over a table.  These are not, and
the asymmetry is deliberate:

`POST /api/v1/auth/logout` revokes the token the request was made with: its `jti` goes into `token_blacklist`, and the matching `login_session` is stamped `revoked_at`.
Only that token - signing out on one device does not sign the user out everywhere.
The blacklist is consulted in **two** places, and both are load-bearing: `bearer.resolve()` for ordinary requests, and `refresh` separately, because refresh reads the Authorization header itself rather than going through the dependency.
Without the second check a revoked token could be exchanged for a fresh one and logout would achieve nothing.

`token_blacklist` only grows on logout, so logout is also where it is pruned: a row only has to outlive the token it revokes, and once the expiry passes the token fails validation on its own.
`make prune-blacklist` (and `--dry-run`) does the same for a deployment where nobody signs out for a long stretch.

* **`login-sessions`** is read-only.
  The API writes a row itself when it issues a token (`record_login_session`
  in `app/utils.py`), because a front end that reports its own sessions can
  decline to, or report someone else's.
  Only a SHA-256 of the token is stored, and the endpoint never returns even
  that.
* **`audit-log`** is append-only: `GET` and `POST`, no `PUT` or `DELETE`.
  An audit trail the recorded parties can edit is not one.
  `user_id` comes from the bearer token, never the payload.
* **`instance-metadata`** is a singleton: one object, no path parameter, no
  writes.
  `release`, `db_version` and `notes` come from the row; `app_version` and
  `alembic_revision` are read at request time, because a version stamped into
  a row goes stale the moment the application is upgraded without a
  migration.

`instance_metadata` is excluded from the test suite's per-test TRUNCATE
(`_KEEP` in `conftest.py`): it describes the database rather than holding
test data, and migration `0006` stamps the single row that every test is
entitled to find.

### API conventions

Every resource follows the same shape, and `users.py` is the reference: page with `limit`/`offset`, create, fetch-or-404, patch-style update, delete.
Adding one means a model, a `Base`/`Create`/`Update`/response quartet in `schemas.py`, an endpoint module, and a line in `router.py`.

The path parameter is always the surrogate integer `id`, never the client-side `guid`.
Routes are the pluralised table name, kebab-cased when it is more than one word: `user_role` is served at `/api/v1/user-roles`.
`PUT` is patch-style: `model_dump(exclude_unset=True)`, and an empty body is a 400.
Server-managed columns are deliberately absent from the write schemas - `hashed_password`, and the `created_by_id` / `updated_by_id` stamps - while `created_at` / `updated_at` are read back but never written.

`app/api/v1/crud.py` holds the parts that differ only by model, so they are not repeated per resource:

* `commit(db, Model, label)` translates constraint violations into 4xx rather than letting them escape as a 500 - unique to **409**, and FK / not-null / check to **400**.
  It rolls back first, because an aborted transaction poisons every later use of the session.
* `get_or_404(db, Model, pk, label)` and `apply_update(row, fields)`.
* `commit()` also stamps `created_by_id` and `updated_by_id` from the acting user, on the twelve tables that carry those columns.
  `actor_id` is a **required** parameter rather than a defaulted one, so a new endpoint that forgets it fails at import rather than silently writing rows with no provenance.

Write routes therefore take `actor: ApplicationUser = Depends(jwt_bearer)` as a value; read routes use `dependencies=[Depends(jwt_bearer)]`.
The parameter is named `actor`, not `user`: in `users.py` the entity being written is itself a user, and the two shadowed each other - the stamp silently recorded the new row's own id instead of the caller's.

The stamps are readable on the response schemas and absent from the write schemas, so a client cannot claim the work was done by someone else.
Note that a contextvar set inside a FastAPI dependency does **not** reach the endpoint body, in either sync or async routes, so the actor cannot be passed implicitly.

Only `application_user.email` carries a UNIQUE constraint today, so no other resource can produce a 409 yet; the handling is in place for when they gain one.

Unknown fields in a payload are rejected: the `*Create` and `*Update` schemas set `extra="forbid"`, so a misspelled field is a **422** naming it, rather than being silently dropped.
An empty `PUT` body carries no unknown field and is still the 400.
The response schemas stay permissive on purpose - they are validated from ORM objects, not caller-supplied dicts.

`event.account_id` and `event.owner_id` are **varchar(18)** on that table, not bigint as the same column names are everywhere else, and the schema types them as strings to match.

Migration `0004` adds 25 foreign keys across the CRM tables, all `ON DELETE SET NULL`: deleting a user orphans what they owned rather than destroying it.
They are `DEFERRABLE INITIALLY IMMEDIATE`, because `application_user.user_role_id` and `user_role.forecast_user_id` reference each other and no insertion order satisfies both under per-statement checking.
Ordinary requests still fail on the offending statement; `scripts/seed.py` issues `SET CONSTRAINTS ALL DEFERRED` inside its transaction.

Reference columns that are **not** constrained are unconstrained deliberately, and accept any bigint:
polymorphic ones paired with a discriminator (`access.reference_id`, `note.parent_id`, `task.who_id`, `task.what_id`, `attachment.parent_id`), ones of the wrong type (`event.account_id` and `event.owner_id` are varchar on that table), and ones with no target table (`application_user.profile_id`, and the opaque `*_ref` columns).

Migration `0005` indexes all 25 child columns, named `<table>_<column>_idx` to match the convention `login_session` and `token_blacklist` already used.
Postgres indexes only the parent side of a foreign key, so without these a parent delete scans every referencing table.
Measured on `contact`: no difference at 50k rows, roughly 4x at 1M (47ms to 12ms), and the gap widens because the scan is O(n) while the lookup is not.

Any new foreign key should get an index in the same migration.

## Testing

See `doc/TESTING.md`.
Tests drive the real app over HTTP (`TestClient`) against a real Postgres on `127.0.0.1:$TEST_DB_PORT` (`base_api_test`, container `base-db-test`), never the dev database.
SQLite is deliberately not used: the tests depend on Postgres behaviour (server-side defaults, sequences, `TRUNCATE`, transactional DDL).

* A session-scoped autouse fixture runs the real migrations (`upgrade head`) once per run.
* An autouse fixture runs `TRUNCATE ... RESTART IDENTITY CASCADE` over `Base.metadata.tables` **before** each test, so primary keys are predictable and tests assert on `id == 1`.
  Before rather than after, so a stray row left in the container by a manual session cannot fail the first test of a run.
  Rollback-based isolation is not usable because the endpoints call `db.commit()`.
* The `client` fixture is available to every test; just drop a `test_*.py` in `tests/`.

**Migrations are tested against data**, in `tests/test_migrations.py`.
Every other test runs against a database already at head, so a migration that corrupts existing rows passes all of them - which is exactly what `0004` did, clearing valid self-referencing values while 222 tests stayed green.

Those tests use a scratch database created and dropped per session (`tests/migration_fixtures.py`), so moving its revision around cannot disturb the one the rest of the suite shares.
`migrate.to(revision)` moves in either direction; `migrate.session()` gives a session on it.
`db/alembic/env.py` honours a URL the caller has already pinned, which is what points alembic at the scratch database.

A migration that changes data wants a test that plants rows at the previous revision, upgrades, and asserts what survived.
* `_TestDb` in `conftest.py` resolves the connection from the `TEST_*` keys of the root `.env`, then writes them into `os.environ` as `DB_*` above its own imports.
  Bare `pytest` and `make test` therefore always agree on the port.

## Release process

Per `doc/CONVENTIONS.md` and the existing history:

1. Update `CHANGELOG.md` (Keep a Changelog format).
2. Bump `version` in `pyproject.toml` (semver; minor bumps for features while at 0.x).
3. Two commits on `main`: the feature code first, then a `Release vX.Y.Z: changelog and version bump` commit.
4. Annotated `vX.Y.Z` tag on the release commit.
5. `git push origin main --tags`.

`doc/CONVENTIONS.md` also calls for detailed notes under `release_notes/vX.Y.Z.md`; that directory does not exist yet.

## Code style in this repo

Existing modules follow a distinctive layout that new files should match:

* A `#!/usr/bin/env python` shebang, then a module docstring, wrapped in `# ---...` rule comments.
* `# ---...` rule comments separating every top-level definition.
* Import blocks separated by rules, with local `app.*` imports in their own block.
* Column and attribute assignments vertically aligned within a class.
