# Testing

The suite runs the real app (routing, SQLAlchemy, migrations) against a
**real Postgres**, on a dedicated container that is separate from the dev
database.  SQLite is deliberately out: the app relies on Postgres behaviour
(server-side defaults, sequences, `TRUNCATE`, transactional DDL) that a file
database would not exercise.

## Prerequisites

Docker, and a **Compose v2 plugin new enough to talk to your daemon**.
The CLI and the plugin are separate packages on Debian and Ubuntu, so the
plugin can lag years behind while `docker --version` looks current.

Docker Engine 29 refuses clients below API 1.44, and Compose v2.18 asks for
1.42, which fails as:

```
Error response from daemon: client version 1.42 is too old.
Minimum supported API version is 1.44
```

Check with:

```sh
docker version --format 'client API {{.Client.APIVersion}} | daemon min {{.Server.MinAPIVersion}}'
docker compose version
env | grep -i DOCKER_          # a pinned DOCKER_API_VERSION does the same thing
```

Nothing in this repository causes or can work around that - `make test-db-up`
is a plain `docker compose up -d`.  To test while sorting it out, start the
container with the CLI instead, which does not go through Compose:

```sh
docker run -d --name base-db-test \
  -e POSTGRES_USER=api -e POSTGRES_PASSWORD=test -e POSTGRES_DB=base_api_test \
  -p 127.0.0.1:$TEST_DB_PORT:5432 --shm-size=128m postgres

.venv/bin/pytest
```

`make test` only runs `test-db-up` before `pytest`, so `pytest` alone works
once the container exists.

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

## Migration tests

`tests/test_migrations.py` runs against a **separate scratch database**,
created and dropped per session, because it moves the schema version around
and that would wreck the database the rest of the suite shares.

The rest of the suite runs against a database already at head, so a migration
that corrupts existing rows passes every one of those tests.  Migration
`0004` did exactly that.

The fixtures are in `tests/migration_fixtures.py`:

```python
def test_something(migrate):
    migrate.to("0003")              # build to a revision
    with migrate.session() as s:    # plant data
        ...
    migrate.to("0004")              # upgrade
    with migrate.session() as s:    # assert what survived
        ...
```

## Adding tests

Drop a `test_*.py` in `tests/`; the `client` fixture (a `TestClient` on the
real app) is available to every test.
