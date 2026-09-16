# Testing

The suite runs the real app (routing, SQLAlchemy, migrations) against a
**real Postgres**, on a dedicated container that is separate from the dev
database.  SQLite is deliberately out: the app relies on Postgres behaviour
(server-side defaults, sequences, `TRUNCATE`, transactional DDL) that a file
database would not exercise.

## The test database

`docker/test/docker-compose.yml` runs a throwaway Postgres:

|           | dev (`docker/db/`)      | test (`docker/test/`)        |
|-----------|-------------------------|------------------------------|
| port key  | `DB_PORT` (default 5432)| `TEST_DB_PORT` (default 5433)|
| database  | `base_api`              | `base_api_test`              |
| container | `base-db`               | `base-db-test`               |
| data      | persistent              | discarded on `down`          |

Both stacks can run at the same time, and tests can never touch dev data.

Both ports are chosen in the repo-root `.env`, which is the single source of
truth: the compose files interpolate them, and the app and the test suite
read the same file.  Change either key if something else on the host already
holds that port.  The keys are deliberately distinct - the suite reads only
the `TEST_*` keys, so pointing `DB_PORT` at the dev database cannot redirect
the tests.

## How the tests reach it

`tests/conftest.py` reads the `TEST_*` keys from the repo-root `.env` and
sets `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_PASSWORD` from them **before the
app is imported**.  The engine in `app/db/session.py` is built
at import time from `Settings`, and pydantic-settings prefers real
environment variables over `.env`, so the whole stack — app, `SessionLocal`
and alembic (same `get_settings()`) — runs against the test database with no
app changes and no dependency overrides.

* **Schema** — a session fixture runs the real alembic migrations
  (`upgrade head`) once per run: the full chain on a freshly-reset
  container, a no-op otherwise.
* **Isolation** — an autouse fixture truncates every table in
  `Base.metadata` **before** each test, with `RESTART IDENTITY`, so primary
  keys are predictable (1, 2, 3, …).  New tables are picked up automatically.
  (The endpoints call `db.commit()`, so the transaction-rollback isolation
  pattern is not usable.)

  Before rather than after on purpose: truncating on the way out leaves the
  first test of a run exposed to whatever the container already held, and a
  single stray row from a manual session is enough to fail it — pointing at
  the wrong test.  The last test's rows survive the run, which helps a
  post-mortem.

## Running

```sh
make test          # starts the container if needed, waits, runs pytest
make test-db-up    # just start / wait on the container
make test-db-down  # stop it (its data goes away)
make test-db-reset # stop + start: fresh database, migrations re-run
```

Plain `pytest` works too, once the container is up: it resolves the port from
the same `.env`, so it cannot disagree with `make test`.

`make chk-env` prints the `TEST_DB_PORT` actually in effect.

## Adding tests

Drop a `test_*.py` in `tests/`; the `client` fixture (a `TestClient` on the
real app) is available to every test.
