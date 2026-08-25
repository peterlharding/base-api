# Database setup

Sets up the Postgres instance used by base-api:

| Object             | Type     | Notes                                          |
| ------------------ | -------- | ---------------------------------------------- |
| `plh`              | role     | LOGIN                                          |
| `root`             | role     | LOGIN                                          |
| `api`              | role     | LOGIN; owner of the `base_api` database        |
| `base_api`         | database | owned by `api`                                 |
| `application_user` | table    | in `base_api`, primary key `id`                |

All three roles share the same password. It is **not** stored in this
repository — the SQL scripts receive it as the `db_password` psql variable.

## 1. Configure the password

The password is read from the environment variable `DB_PASSWORD`. Add it to a
`.env` file at the repository root (`.env` is gitignored; `.env.example` is a
template), or export it in your shell:

```sh
echo 'DB_PASSWORD=your-password' >> .env
```

## 2. Start Postgres

From this directory:

```sh
make up
```

(or `docker compose up -d` directly). This starts container `base-db` with
superuser `postgres` — password set in `docker-compose.yml` — listening on
`127.0.0.1:5432`.

## 3. Run the setup scripts

```sh
set -a; . ../../.env; set +a   # load DB_PASSWORD into the environment (bash)
make setup
```

or run the scripts manually:

```sh
docker exec -i base-db psql -U postgres -v db_password="$DB_PASSWORD" < db/schema/create/01-create-users.sql
docker exec -i base-db psql -U postgres                               < db/schema/create/02-create-database.sql
docker exec -i base-db psql -U postgres -d base_api                   < db/schema/create/03-create-application_user.sql
```

The scripts are idempotent — safe to re-run at any time. Re-running
`01-create-users.sql` also updates the roles' passwords to the value of
`DB_PASSWORD`.

On a brand-new instance (fresh volume), start Postgres in step 2 and then run
step 3.

## 4. Verify

```sh
docker exec -e PGPASSWORD="$DB_PASSWORD" base-db \
    psql -h 127.0.0.1 -U api -d base_api -c 'select current_user, current_database();'
```

should print:

```
 current_user | current_database
--------------+------------------
 api          | base_api
```

## Connection string

```
postgresql://api:$DB_PASSWORD@127.0.0.1:5432/base_api
```


# NOTES

1)  I have moved the SQL scripts to db/schema/create off the project root


