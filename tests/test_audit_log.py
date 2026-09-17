"""/api/v1/audit-log - append-only: GET and POST, never PUT or DELETE."""

from sqlalchemy import insert, select

from app.db.session import SessionLocal
from app.models import ApplicationUser


GUID = "abababab-cdcd-efef-0101-232323232323"


def _entry(**over):
    body = {
        "application": "crm-web",
        "reference_type": 1,
        "reference_id": 42,
        "event": "update",
        "description": "changed the billing city",
    }
    body.update(over)
    return body


# -----------------------------------------------------------------------------

def test_create_and_read_back(client) -> None:
    r = client.post("/api/v1/audit-log", json=_entry())
    assert r.status_code == 201
    body = r.json()
    assert body["application"] == "crm-web"
    assert body["event"] == "update"
    assert body["created_at"] is not None

    assert client.get(f"/api/v1/audit-log/{body['id']}").status_code == 200


# -----------------------------------------------------------------------------

def test_required_fields(client) -> None:
    for missing in ("application", "reference_type", "reference_id",
                    "event", "description"):
        body = _entry()
        del body[missing]
        r = client.post("/api/v1/audit-log", json=body)
        assert r.status_code == 422, f"{missing} is not required"


# -----------------------------------------------------------------------------

def test_unknown_field_is_rejected(client) -> None:
    r = client.post("/api/v1/audit-log", json=_entry(nonsense="x"))
    assert r.status_code == 422


# -----------------------------------------------------------------------------

def test_a_client_cannot_choose_the_user(client) -> None:
    """user_id comes from the token, never the payload.

    Otherwise the log records whoever the caller claims to be, which makes it
    worthless as an audit trail.
    """
    r = client.post("/api/v1/audit-log", json=_entry(user_id="somebody-else"))
    assert r.status_code == 422
    assert any("user_id" in str(d["loc"]) for d in r.json()["detail"])


# -----------------------------------------------------------------------------

def test_entries_are_attributed_to_the_token_holder(protected_client) -> None:
    """With the real dependency in force, user_id is the token's subject."""
    from app.auth.handler import sign_token

    with SessionLocal() as s:
        s.execute(insert(ApplicationUser).values(
            username="auditor", guid=GUID, is_active=True))
        s.commit()

    r = protected_client.post(
        "/api/v1/audit-log", json=_entry(),
        headers={"Authorization": f"Bearer {sign_token(GUID)}"})

    assert r.status_code == 201
    assert r.json()["user_id"] == GUID


# -----------------------------------------------------------------------------

def test_is_append_only(client) -> None:
    created = client.post("/api/v1/audit-log", json=_entry()).json()

    for method in ("put", "patch", "delete"):
        r = getattr(client, method)(f"/api/v1/audit-log/{created['id']}")
        assert r.status_code == 405, f"{method.upper()} is accepted on an audit log"


# -----------------------------------------------------------------------------

def test_newest_first(client) -> None:
    ids = [client.post("/api/v1/audit-log", json=_entry(description=f"e{i}")).json()["id"]
           for i in range(3)]
    listed = [e["id"] for e in client.get("/api/v1/audit-log").json()]
    assert listed == sorted(ids, reverse=True)


# -----------------------------------------------------------------------------

def test_filters(client) -> None:
    client.post("/api/v1/audit-log", json=_entry(application="crm-web", event="create"))
    client.post("/api/v1/audit-log", json=_entry(application="batch", event="update"))

    assert len(client.get("/api/v1/audit-log",
                          params={"application": "crm-web"}).json()) == 1
    assert len(client.get("/api/v1/audit-log", params={"event": "update"}).json()) == 1
    assert client.get("/api/v1/audit-log",
                      params={"application": "nope"}).json() == []


# -----------------------------------------------------------------------------

def test_pagination(client) -> None:
    for i in range(3):
        client.post("/api/v1/audit-log", json=_entry(description=f"e{i}"))
    first = client.get("/api/v1/audit-log", params={"limit": 2}).json()
    second = client.get("/api/v1/audit-log", params={"limit": 2, "offset": 2}).json()
    assert len(first) == 2 and len(second) == 1


# -----------------------------------------------------------------------------

def test_missing_entry_404(client) -> None:
    r = client.get("/api/v1/audit-log/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Audit entry 999999 not found"
