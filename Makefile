
API_PORT    := $(shell grep API_PORT= .env | sed 's/.*=//')
HOST        := $(shell grep HOST= .env | sed 's/.*=//')


# ------------------------------------------------------------------------

chk-env:
	@echo "API_PORT |${API_PORT}|"
	@echo "HOST     |${HOST}|"


# uv sync reads pyproject.toml / uv.lock and creates .venv if it is missing.
install:
	uv sync

git-chk:
	git status --short && \
	echo '---' && \
	git log --oneline -8 && \
	echo '---' && \
	git show --stat HEAD | head -30


# ------------------------------------------------------------------------
# Test suite — dedicated Postgres (docker/test/), see doc/TESTING.md.
# `make test` starts the container if needed and runs pytest; the schema is
# migrated by the test suite itself (alembic upgrade head).
# ------------------------------------------------------------------------

TEST_COMPOSE := docker compose -f docker/test/docker-compose.yml


test-db-up:
	$(TEST_COMPOSE) up -d
	@n=0; \
	while ! $(TEST_COMPOSE) exec -T db pg_isready -q -U api >/dev/null 2>&1; do \
	    n=$$((n+1)); \
	    if [ $$n -ge 60 ]; then echo "test database did not become ready in time"; exit 1; fi; \
	    sleep 0.5; \
	done
	@echo "test database is ready (127.0.0.1:5433)"


test-db-down:
	$(TEST_COMPOSE) down


test-db-reset:
	$(TEST_COMPOSE) down
	$(MAKE) test-db-up


test:
	$(MAKE) test-db-up
	.venv/bin/pytest


# ------------------------------------------------------------------------

run:
	.venv/bin/uvicorn app.main:app --host $(HOST) --port $(API_PORT)


dev:
	.venv/bin/uvicorn app.main:app --host $(HOST) --port $(API_PORT) --reload


# ------------------------------------------------------------------------

migrate:
	.venv/bin/alembic -c db/alembic.ini upgrade head


autogenerate:
	.venv/bin/alembic -c db/alembic.ini revision --autogenerate -m "$(or $(msg),update schema)"
