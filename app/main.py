#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""FastAPI application entry point.

Run from the repo root:  uvicorn app.main:app --host 127.0.0.1 --port 8091
(or `make run` / `make dev`).
"""
# -----------------------------------------------------------------------------

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal


# -----------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_title)
    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict:
        """Liveness probe; also reports whether the database is reachable."""
        payload: dict[str, str] = {"name": settings.app_name, "title": settings.app_title}
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
            payload["database"] = "ok"
            return payload
        except Exception:
            payload["database"] = "unavailable"
            return JSONResponse(status_code=503, content=payload)

    return app


# -----------------------------------------------------------------------------

app = create_app()


# -----------------------------------------------------------------------------

