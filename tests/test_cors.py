"""Cross-origin access - app/core/cors.py.

Off unless CORS_ORIGINS names an origin, which is how the test environment
and every server-to-server deployment run.  The tests that need it on build
their own app rather than reaching for the real settings, so switching it on
here cannot switch it on for the rest of the suite.
"""

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.cors import HEADERS, METHODS, configure_cors, origins
from app.main import create_app


ALLOWED = "http://localhost:5173"


def _app(cors_origins: str, release: str = "dev") -> TestClient:
    """A minimal app configured exactly as create_app() configures the real one."""
    app = FastAPI()
    configure_cors(app, Settings(cors_origins=cors_origins, release=release))

    @app.get("/thing")
    def thing() -> dict:
        return {"ok": True}

    @app.post("/thing")
    def make_thing() -> dict:
        return {"ok": True}

    return TestClient(app)


def _preflight(client, origin=ALLOWED, method="POST", headers="authorization"):
    return client.options("/thing", headers={
        "Origin": origin,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": headers,
    })


# -----------------------------------------------------------------------------
# Parsing

@pytest.mark.parametrize("value, expected", [
    ("", []),
    ("   ", []),
    (ALLOWED, [ALLOWED]),
    (f"{ALLOWED},https://app.example.com", [ALLOWED, "https://app.example.com"]),
    (f"  {ALLOWED} ,  https://app.example.com  ", [ALLOWED, "https://app.example.com"]),
    (f"{ALLOWED},", [ALLOWED]),
    (f"{ALLOWED},,https://app.example.com", [ALLOWED, "https://app.example.com"]),
])
def test_origins_are_parsed_from_a_comma_separated_string(value, expected) -> None:
    assert origins(Settings(cors_origins=value)) == expected


# -----------------------------------------------------------------------------

def test_a_bare_origin_does_not_have_to_be_json() -> None:
    """The reason cors_origins is a str and not a list[str].

    pydantic-settings runs a complex annotation through json.loads first, so
    typing this as list[str] makes CORS_ORIGINS=http://localhost:5173 a
    startup failure.
    """
    assert Settings(cors_origins=ALLOWED).cors_origins == ALLOWED


# -----------------------------------------------------------------------------
# Off by default

def test_nothing_is_shared_when_no_origin_is_configured() -> None:
    r = _app("").get("/thing", headers={"Origin": ALLOWED})

    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers


# -----------------------------------------------------------------------------

def test_no_middleware_is_installed_when_no_origin_is_configured() -> None:
    """Structural, because the behaviour alone cannot show this.

    CORSMiddleware with an empty allow list emits no header either, so a
    response looks identical whether the middleware is absent or present and
    matching nothing.  The difference is that the installed one intercepts
    every preflight to answer 400.
    """
    app = FastAPI()

    assert configure_cors(app, Settings(cors_origins="")) == []
    assert app.user_middleware == []


# -----------------------------------------------------------------------------

def test_the_real_app_has_cors_off_in_this_environment() -> None:
    """The suite's .env names no origin, so the default path is the tested one."""
    r = TestClient(create_app()).get("/health", headers={"Origin": ALLOWED})

    assert "access-control-allow-origin" not in r.headers


# -----------------------------------------------------------------------------
# On

def test_a_configured_origin_is_allowed() -> None:
    r = _app(ALLOWED).get("/thing", headers={"Origin": ALLOWED})

    assert r.headers["access-control-allow-origin"] == ALLOWED


# -----------------------------------------------------------------------------

def test_an_unconfigured_origin_is_not() -> None:
    r = _app(ALLOWED).get("/thing", headers={"Origin": "https://evil.example.com"})

    assert "access-control-allow-origin" not in r.headers


# -----------------------------------------------------------------------------

def test_localhost_and_127_0_0_1_are_different_origins() -> None:
    """Worth pinning because they are the same machine and not the same origin."""
    r = _app("http://localhost:5173").get(
        "/thing", headers={"Origin": "http://127.0.0.1:5173"})

    assert "access-control-allow-origin" not in r.headers


# -----------------------------------------------------------------------------
# Preflight

def test_the_preflight_is_answered() -> None:
    r = _preflight(_app(ALLOWED))

    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ALLOWED


# -----------------------------------------------------------------------------

def test_the_preflight_needs_no_token() -> None:
    """The middleware answers OPTIONS before routing, which it has to.

    A browser sends a preflight without credentials, so a preflight that had
    to be authenticated could never succeed and every cross-origin write
    would fail.
    """
    r = _preflight(_app(ALLOWED))

    assert r.status_code == 200
    assert "authorization" in r.headers["access-control-allow-headers"].lower()


# -----------------------------------------------------------------------------

def test_the_authorization_header_is_allowed() -> None:
    """Without it every cross-origin request is anonymous and the API is useless."""
    assert "Authorization" in HEADERS


# -----------------------------------------------------------------------------

def test_credentials_are_not_allowed() -> None:
    """Auth here is a bearer token in a header; cookies buy nothing."""
    r = _app(ALLOWED).get("/thing", headers={"Origin": ALLOWED})

    assert "access-control-allow-credentials" not in r.headers


# -----------------------------------------------------------------------------
# Drift

def test_every_method_the_api_serves_is_allowed() -> None:
    """Otherwise a new method works everywhere except from a browser.

    Derived from the live schema rather than a list kept by hand, so adding
    PATCH to a router fails here instead of in somebody's network tab.
    """
    served = {
        method.upper()
        for path in create_app().openapi()["paths"].values()
        for method in path
    }

    assert served <= set(METHODS), f"not allowed by CORS: {sorted(served - set(METHODS))}"


# -----------------------------------------------------------------------------
# The wildcard

def test_a_wildcard_is_allowed_off_production() -> None:
    r = _app("*", release="dev").get("/thing", headers={"Origin": ALLOWED})

    assert r.headers["access-control-allow-origin"] in ("*", ALLOWED)


# -----------------------------------------------------------------------------

def test_a_wildcard_is_refused_on_production() -> None:
    """Fail at startup rather than serve every site on the internet."""
    with pytest.raises(RuntimeError, match="prod"):
        configure_cors(FastAPI(), Settings(cors_origins="*", release="prod"))


# -----------------------------------------------------------------------------

def test_a_named_origin_is_fine_on_production() -> None:
    """The refusal is about the wildcard, not about production having CORS."""
    assert configure_cors(
        FastAPI(), Settings(cors_origins="https://app.example.com", release="prod")
    ) == ["https://app.example.com"]
