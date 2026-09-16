

# -----------------------------------------------------------------------------
# The repo-root .env is the single source of truth for DB_PORT and DB_PASSWORD,
# which docker-compose.yml interpolates.  --env-file is a top-level flag and
# must precede the subcommand.
# -----------------------------------------------------------------------------

ROOT_ENV := ../../.env
COMPOSE  := docker compose --env-file $(ROOT_ENV)

# Respects an already-exported DB_PASSWORD (set -a; . ../../.env; set +a),
# otherwise reads it from the repo-root .env.  Anchored on purpose.
DB_PASSWORD ?= $(shell grep -s '^DB_PASSWORD=' $(ROOT_ENV) | sed 's/.*=//')
DB_PORT     ?= $(shell grep -s '^DB_PORT='     $(ROOT_ENV) | sed 's/.*=//')
DB_NAME     ?= $(shell grep -s '^DB_NAME='     $(ROOT_ENV) | sed 's/.*=//')


# -----------------------------------------------------------------------------

up:
	$(COMPOSE) up -d
	docker ps

down:
	$(COMPOSE) down
	sleep 1
	docker ps

# Create the application roles and the empty base-api database (see ../../setup/SETUP.md).
#
# Tables are NOT created here.  Alembic owns the schema: run `make migrate`
# from the repo root afterwards, which is the same path the test suite takes,
# so dev and test are built identically and cannot drift.
#
# ON_ERROR_STOP is not optional: reading a script from stdin, psql reports a
# SQL error and still exits 0, so without it make marches on to the next step
# and the real failure is buried under its fallout.
PSQL := docker exec -i base-db psql -v ON_ERROR_STOP=1 -U postgres

setup:
	$(PSQL) -v db_password=$(DB_PASSWORD) < ../../db/schema/sql/01-create-users.sql
	$(PSQL) -v db_name=$(DB_NAME) < ../../db/schema/sql/02-create-database.sql
	@echo 'roles and database ready - now run `make migrate` from the repo root'

chk-env:
	@echo "     DB_NAME |$(DB_NAME)|"
	@echo "     DB_PORT |$(DB_PORT)|"
	@echo " DB_PASSWORD |$(DB_PASSWORD)|"
