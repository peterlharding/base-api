
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
	git status --short && echo '---' && git log --oneline -5


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
