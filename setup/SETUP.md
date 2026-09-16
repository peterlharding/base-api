# Database setup

Sets up the Postgres instance used by base-api:

| Object             | Type     | Notes                                          |
| ------------------ | -------- | ---------------------------------------------- |
| `plh`              | role     | LOGIN                                          |
| `root`             | role     | LOGIN                                          |
| `api`              | role     | LOGIN; owner of the application database       |
| `$DB_NAME`         | database | owned by `api`, created empty (default `base_api`) |

All three roles share the same password. It is **not** stored in this
repository - the SQL scripts receive it as the `db_password` psql variable.

Tables are **not** created here.  Alembic owns the schema: `make setup`
creates the roles and an empty database, and `make migrate` from the repo
root builds every table.
That is the same path the test suite takes, so dev and test are built
identically and cannot drift.
The standalone table scripts in `db/schema/create/` are reference material
for that reason, not part of the setup run.

## 1. Configure the password and the port

Both are read from the `.env` file at the repository root (`.env` is
gitignored; `setup/env.template` is the template).
It is the single source of truth: `docker-compose.yml` interpolates
`DB_PASSWORD` and `DB_PORT` from it, and so does the application, so the
container and the app can never disagree about where the database is.

```sh
DB_PASSWORD=your-password
DB_NAME=base_api        # the database to create; the app reads the same key
DB_PORT=5432            # any free port; the app reads the same key
```

`DB_NAME` and `DB_PORT` may both be omitted, falling back to `base_api` and 5432.
Change it if another Postgres already has that port; the test stack has its
own key, `TEST_DB_PORT` (see [doc/TESTING.md](../doc/TESTING.md)).

## 2. Start Postgres

From `docker/db/`:

```sh
make up
```

This starts container `base-db` with superuser `postgres`, listening on
`127.0.0.1:$DB_PORT`.
The recipe passes the repo-root `.env` to compose; to invoke it by hand, do
the same, because `--env-file` is a top-level flag and must precede the
subcommand:

```sh
docker compose --env-file ../../.env up -d   # from docker/db/
```

## 3. Create the roles and the database

From `docker/db/`:

```sh
make setup
```

The recipe reads `DB_PASSWORD` from the repo-root `.env` itself; an exported
`DB_PASSWORD` still wins if you prefer `set -a; . ../../.env; set +a`.

Or run the scripts manually, from `docker/db/`, with the `.env` values
exported (`set -a; . ../../.env; set +a`):

```sh
docker exec -i base-db psql -v ON_ERROR_STOP=1 -U postgres -v db_password="$DB_PASSWORD" < ../../db/schema/sql/01-create-users.sql
docker exec -i base-db psql -v ON_ERROR_STOP=1 -U postgres -v db_name="$DB_NAME"         < ../../db/schema/sql/02-create-database.sql
```

Pass `db_name`: omitted, the script falls back to `base_api`, which is not
what the application connects to unless `DB_NAME` happens to say so.

`ON_ERROR_STOP=1` matters: reading a script from stdin, psql reports a SQL
error and still exits 0, so without it a failure is silently stepped over.

The scripts are idempotent - safe to re-run at any time. Re-running
`01-create-users.sql` also updates the roles' passwords to the value of
`DB_PASSWORD`.

## 4. Build the schema

From the repo root:

```sh
make migrate
```

This runs `alembic upgrade head` and creates every table.
On a brand-new instance (fresh volume), do steps 2, 3 and 4 in order.

## 5. Verify

```sh
docker exec -e PGPASSWORD="$DB_PASSWORD" base-db \
    psql -h 127.0.0.1 -U api -d "$DB_NAME" -c 'select current_user, current_database();'
```

should print:

```
 current_user | current_database
--------------+------------------
 api          | base_api      (or whatever DB_NAME is set to)
```

## Connection string

```
postgresql://api:$DB_PASSWORD@127.0.0.1:$DB_PORT/$DB_NAME
```

`make chk-env` in this directory prints the values actually in effect.

