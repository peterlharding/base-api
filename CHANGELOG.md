# Changelog

All notable changes to base-api are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(minor bumps for new features while at 0.x).

## [0.2.0] - 2026-08-23

### Added

- Versioned API layer at `/api/v1` (`app/api/v1/`, mounted in `create_app()`).
- Users CRUD endpoints for `application_user`, served under `/api/v1/users`:
  - `GET /api/v1/users` — paged list in id order (`limit` default 50, max 200; `offset`).
  - `POST /api/v1/users` — create a user; only `username` is mandatory (201 on success).
  - `GET /api/v1/users/{id}` — fetch one user by surrogate key (404 if missing).
  - `PUT /api/v1/users/{id}` — patch-style update: only the fields present in the
    payload are changed; an empty payload is rejected with 400.
  - `DELETE /api/v1/users/{id}` — delete (204 on success).
- Pydantic schemas `UserCreate` / `UserUpdate` / `User` in `app/api/v1/schemas.py`.
  `password` and the `*_by_id` audit stamps are never exposed or written through the API;
  `created_date` / `last_modified_date` / `last_login_date` are read back only.
- Path parameter is named `id` (the table's surrogate key) so it cannot be confused
  with the legacy string `user_id` column, which remains an ordinary field.
- Database server defaults (e.g. `timezone_key = 'Australia/Melbourne'`,
  `user_type = 'Standard'`) pass through unchanged on create.

### Changed

- Moved the Alembic configuration into `db/` (`db/alembic.ini`, `db/alembic/`);
  `migrate` and `autogenerate` now run `alembic -c db/alembic.ini`, and `env.py`
  resolves the repo root from one level deeper.

## [0.1.0] - 2026-08-23

### Added

- FastAPI application scaffold: `create_app()` in `app/main.py` with a `/health`
  liveness probe that also reports database reachability (503 when down).
- Postgres setup for the `base_api` database (see `docker/db/SETUP.md`) and
  `app/core/config.py` settings loaded from the environment / `.env`.
- SQLAlchemy models mirroring `application_user` (`app/db/models.py`), engine and
  per-request session dependency (`app/db/session.py`), and Alembic migration `0001`
  building the table from scratch.
- uv tooling (`pyproject.toml`, `uv.lock`) and Makefile targets:
  `install`, `run`, `dev`, `migrate`, `autogenerate`.
