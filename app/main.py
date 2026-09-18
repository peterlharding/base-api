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


# -----------------------------------------------------------------------------

from app.core.config import get_settings
from app.core.cors import configure_cors
from app.db.session import SessionLocal

from app.api.v1.router import api_v1_router


# -----------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(title=settings.app_title)

    # Before the routes: CORSMiddleware answers the preflight OPTIONS itself,
    # so a protected route never sees it.  A preflight that had to carry a
    # token would be unanswerable - the browser sends it without one.
    configure_cors(app, settings)

    app.include_router(api_v1_router)

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

