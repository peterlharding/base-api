"""/api/v1/audit-log - read-only; the API writes these rows itself.

Entries are created in app/api/v1/crud.py, which every mutation already
passes through, so a route cannot be silently unaudited.  Mutations only:
reads are not recorded.
"""

import pytest
from sqlalchemy import insert, select

from app.auth.handler import sign_token
from app.db.session import SessionLocal
from app.models import AuditLog, ApplicationUser


GUID = "acacacac-1111-2222-3333-444444444444"


@pytest.fixture()
def actor():
    with SessionLocal() as s:
        s.execute(insert(ApplicationUser).values(
            username="auditor", guid=GUID, is_active=True))
        s.commit()
    return {"Authorization": f"Bearer {sign_token(GUID)}"}


def _entries(client, **params):
    return client.get("/api/v1/audit-log", params=params).json()


# -----------------------------------------------------------------------------

def test_a_create_is_recorded(protected_client, actor) -> None:
    r = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                              headers=actor)
    assert r.status_code == 201

    entries = protected_client.get("/api/v1/audit-log", headers=actor).json()
    assert len(entries) == 1
    e = entries[0]
    assert e["action"] == "create"
    assert e["reference_type"] == "account"
    assert e["reference_id"] == r.json()["id"]
    assert e["user_id"] == GUID


# -----------------------------------------------------------------------------

def test_an_update_records_which_columns_changed(protected_client, actor) -> None:
    created = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                                    headers=actor).json()

    protected_client.put(f"/api/v1/accounts/{created['id']}",
                         json={"industry": "Software"}, headers=actor)

    entries = protected_client.get("/api/v1/audit-log",
                                   params={"action": "update"}, headers=actor).json()
    assert len(entries) == 1
    assert entries[0]["reference_id"] == created["id"]
    assert "industry" in entries[0]["description"]


# -----------------------------------------------------------------------------

def test_a_delete_is_recorded(protected_client, actor) -> None:
    created = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                                    headers=actor).json()

    protected_client.delete(f"/api/v1/accounts/{created['id']}", headers=actor)

    entries = protected_client.get("/api/v1/audit-log",
                                   params={"action": "delete"}, headers=actor).json()
    assert len(entries) == 1
    assert entries[0]["reference_type"] == "account"
    assert entries[0]["reference_id"] == created["id"]


# -----------------------------------------------------------------------------

def test_reads_are_not_recorded(protected_client, actor) -> None:
    """Mutations only - list endpoints would otherwise drown everything else."""
    protected_client.post("/api/v1/accounts", json={"name": "Acme"}, headers=actor)
    before = len(protected_client.get("/api/v1/audit-log", headers=actor).json())

    protected_client.get("/api/v1/accounts", headers=actor)
    protected_client.get("/api/v1/contacts", headers=actor)

    after = len(protected_client.get("/api/v1/audit-log", headers=actor).json())
    assert after == before


# -----------------------------------------------------------------------------

def test_an_update_that_changes_nothing_records_nothing(protected_client, actor) -> None:
    """The log describes the data, not the request."""
    created = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                                    headers=actor).json()
    before = len(protected_client.get("/api/v1/audit-log", headers=actor).json())

    r = protected_client.put(f"/api/v1/accounts/{created['id']}",
                             json={"name": "Acme"}, headers=actor)
    assert r.status_code == 200

    after = len(protected_client.get("/api/v1/audit-log", headers=actor).json())
    assert after == before, "a no-op update produced an entry"


# -----------------------------------------------------------------------------

def test_a_failed_write_records_nothing(protected_client, actor) -> None:
    """The entry lives in the same transaction, so a rollback takes it too."""
    protected_client.post("/api/v1/users",
                          json={"username": "one", "email": "dup@example.com"},
                          headers=actor)
    before = len(protected_client.get("/api/v1/audit-log", headers=actor).json())

    clash = protected_client.post("/api/v1/users",
                                  json={"username": "two", "email": "dup@example.com"},
                                  headers=actor)
    assert clash.status_code == 409

    after = len(protected_client.get("/api/v1/audit-log", headers=actor).json())
    assert after == before, "a rejected write left an audit entry behind"


# -----------------------------------------------------------------------------

def test_every_mutating_resource_is_audited(protected_client, actor) -> None:
    """Derived from the resources themselves, so a new one is covered."""
    resources = [
        ("accounts", {"name": "Acme"}, "account"),
        ("contacts", {"last_name": "Nguyen"}, "contact"),
        ("tasks", {"subject": "Call"}, "task"),
        ("events", {"subject": "Kickoff"}, "event"),
        ("documents", {"name": "d.pdf"}, "document"),
        ("notes", {"title": "N"}, "note"),
        ("opportunities", {"name": "Deal"}, "opportunity"),
        ("leads", {"last_name": "Rossi"}, "lead"),
        ("quotes", {"quoter": "PLH"}, "quote"),
        ("attachments", {"name": "a.pdf"}, "attachment"),
        ("access", {"reference_type": "account"}, "access"),
        ("user-roles", {"name": "Sales"}, "user_role"),
        ("users", {"username": "someone"}, "application_user"),
    ]
    for path, body, _ in resources:
        assert protected_client.post(f"/api/v1/{path}", json=body,
                                     headers=actor).status_code == 201, path

    seen = {e["reference_type"] for e in
            protected_client.get("/api/v1/audit-log", params={"limit": 200},
                                 headers=actor).json()}
    missing = {table for _, _, table in resources} - seen
    assert not missing, f"unaudited: {missing}"


# -----------------------------------------------------------------------------

def test_the_audit_trail_does_not_audit_itself(protected_client, actor) -> None:
    protected_client.post("/api/v1/accounts", json={"name": "Acme"}, headers=actor)
    entries = protected_client.get("/api/v1/audit-log", headers=actor).json()
    assert all(e["reference_type"] != "audit_log" for e in entries)


# -----------------------------------------------------------------------------

def test_is_read_only(protected_client, actor) -> None:
    """No POST: an entry a client can compose is one it can fabricate."""
    assert protected_client.post("/api/v1/audit-log", json={}, headers=actor
                                 ).status_code == 405
    protected_client.post("/api/v1/accounts", json={"name": "Acme"}, headers=actor)
    eid = protected_client.get("/api/v1/audit-log", headers=actor).json()[0]["id"]
    for method in ("put", "patch", "delete"):
        r = getattr(protected_client, method)(f"/api/v1/audit-log/{eid}", headers=actor)
        assert r.status_code == 405, f"{method.upper()} accepted"


# -----------------------------------------------------------------------------

def test_newest_first_and_filters(protected_client, actor) -> None:
    protected_client.post("/api/v1/accounts", json={"name": "A"}, headers=actor)
    protected_client.post("/api/v1/contacts", json={"last_name": "B"}, headers=actor)

    listed = protected_client.get("/api/v1/audit-log", headers=actor).json()
    assert [e["id"] for e in listed] == sorted((e["id"] for e in listed), reverse=True)

    assert len(protected_client.get("/api/v1/audit-log",
                                    params={"reference_type": "account"},
                                    headers=actor).json()) == 1
    assert len(protected_client.get("/api/v1/audit-log",
                                    params={"user_id": GUID},
                                    headers=actor).json()) == 2


# -----------------------------------------------------------------------------

def test_missing_entry_404(protected_client, actor) -> None:
    r = protected_client.get("/api/v1/audit-log/999999", headers=actor)
    assert r.status_code == 404
