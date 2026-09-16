
HOST        := $(shell grep -s '^HOST='         .env | sed 's/.*=//')
API_NAME    := $(shell grep -s '^API_NAME='     .env | sed 's/.*=//')
API_PORT    := $(shell grep -s '^API_PORT='     .env | sed 's/.*=//')
API_LOG     := $(shell grep -s '^API_LOG='      .env | sed 's/.*=//')
DB_NAME     := $(shell grep -s '^DB_NAME='      .env | sed 's/.*=//')
DB_PORT     := $(shell grep -s '^DB_PORT='      .env | sed 's/.*=//')
DB_USER     := $(shell grep -s '^DB_USER='      .env | sed 's/.*=//')
DB_PASSWORD := $(shell grep -s '^DB_PASSWORD='  .env | sed 's/.*=//')

# Anchored on purpose: an unanchored 'DB_PORT=' also matches TEST_DB_PORT=
# and would feed two values into sed.  Only used for the readiness message;
# compose itself reads .env directly via --env-file.
TEST_DB_PORT := $(shell grep -s '^TEST_DB_PORT=' .env | sed 's/.*=//')

PSQL         := psql


# ------------------------------------------------------------------------

chk-env:
	@echo "        HOST |${HOST}|"
	@echo "    API_NAME |${API_NAME}|"
	@echo "    API_PORT |${API_PORT}|"
	@echo "     API_LOG |${API_LOG}|"
	@echo "     DB_NAME |${DB_NAME}|"
	@echo "     DB_PORT |${DB_PORT}|"
	@echo "     DB_USER |${DB_USER}|"
	@echo " DB_PASSWORD |${DB_PASSWORD}|"
	@echo "TEST_DB_PORT |${TEST_DB_PORT}|"


# uv sync reads pyproject.toml / uv.lock and creates .venv if it is missing.
git-chk:
	git status --short && \
	echo '---' && \
	git log --oneline -8 && \
	echo '---' && \
	git show --stat HEAD | head -30


# ------------------------------------------------------------------------

venv:
	uv venv .venv

install:
	uv sync

pip-install:
	uv pip install -r requirements.txt


# ------------------------------------------------------------------------

dev:
	.venv/bin/uvicorn app.main:app --host $(HOST) --port $(API_PORT) --reload

run:
	.venv/bin/uvicorn app.main:app --host $(HOST) --port $(API_PORT)


# ------------------------------------------------------------------------
# Test suite — dedicated Postgres (docker/test/), see doc/TESTING.md.
# `make test` starts the container if needed and runs pytest; the schema is
# migrated by the test suite itself (alembic upgrade head).
# ------------------------------------------------------------------------

# --env-file is a top-level flag and must precede the subcommand.  It is
# what supplies TEST_DB_PORT to docker/test/docker-compose.yml.
TEST_COMPOSE := docker compose --env-file .env -f docker/test/docker-compose.yml


test-db-up:
	$(TEST_COMPOSE) up -d
	@n=0; \
	while ! $(TEST_COMPOSE) exec -T db pg_isready -q -U api >/dev/null 2>&1; do \
	    n=$$((n+1)); \
	    if [ $$n -ge 60 ]; then echo "test database did not become ready in time"; exit 1; fi; \
	    sleep 0.5; \
	done
	@echo "test database is ready (127.0.0.1:$(TEST_DB_PORT))"


test-db-down:
	$(TEST_COMPOSE) down


test-db-reset:
	$(TEST_COMPOSE) down
	$(MAKE) test-db-up


test:
	$(MAKE) test-db-up
	.venv/bin/pytest


# ------------------------------------------------------------------------

migrate:
	.venv/bin/alembic -c db/alembic.ini upgrade head

autogenerate:
	.venv/bin/alembic -c db/alembic.ini revision --autogenerate -m "$(or $(msg),update schema)"


# ------------------------------------------------------------------------
# Sample data (db/schema/data), deliberately outside the migration chain -
# see the docstring in scripts/seed.py.  `seed-reset` truncates first, which
# the data files need in order to land on the ids they cross-reference.

seed:
	.venv/bin/python scripts/seed.py

seed-reset:
	.venv/bin/python scripts/seed.py --reset

# ------------------------------------------------------------------------

connect:
	$(PSQL) -h ${HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}


# ------------------------------------------------------------------------


