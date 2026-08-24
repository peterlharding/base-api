# Testing

The suite runs the real app (routing, SQLAlchemy, migrations) against a
**real Postgres**, on a dedicated container that is separate from the dev
database.  SQLite is deliberately out: the app relies on Postgres behaviour
(server-side defaults, sequences, `TRUNCATE`, transactional DDL) that a file
database would not exercise.

## The test database

`docker/test/docker-compose.yml` runs a throwaway Postgres:

|          | dev (`docker/db/`)  | test (`docker/test/`)  |
|----------|---------------------|------------------------|
| port     | 127.0.0.1:5432      | 127.0.0.1:5433         |
| database | `base_api`          | `base_api_test`        |
| container| `base-db`           | `base-db-test`         |
| data     | persistent          | discarded on `down`    |

Both stacks can run at the same time, and tests can never touch dev data.

## How the tests reach it

`tests/conftest.py` sets `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_PASSWORD`
**before the app is imported**.  The engine in `app/db/session.py` is built
at import time from `Settings`, and pydantic-settings prefers real
environment variables over `.env`, so the whole stack — app, `SessionLocal`
and alembic (same `get_settings()`) — runs against the test database with no
app changes and no dependency overrides.

* **Schema** — a session fixture runs the real alembic migrations
  (`upgrade head`) once per run: the full chain on a freshly-reset
  container, a no-op otherwise.
* **Isolation** — an autouse fixture truncates every table in
  `Base.metadata` after each test, with `RESTART IDENTITY`, so primary keys
  are predictable (1, 2, 3, …).  New tables are picked up automatically.
  (The endpoints call `db.commit()`, so the transaction-rollback isolation
  pattern is not usable.)

## Running

```sh
make test          # starts the container if needed, waits, runs pytest
make test-db-up    # just start / wait on the container
make test-db-down  # stop it (its data goes away)
make test-db-reset # stop + start: fresh database, migrations re-run
```

Plain `pytest` works too, once the container is up.

## Adding tests

Drop a `test_*.py` in `tests/`; the `client` fixture (a `TestClient` on the
real app) is available to every test.
