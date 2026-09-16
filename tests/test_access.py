"""End-to-end tests for /api/v1/access.

The noun is uncountable, so the collection and the singular share a path.
This table carries no audit columns, which several tests pin.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/access")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/access", json={"reference_type": "account"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["reference_type"] == "account"
    assert body["last_referenced_date"] is not None


# -----------------------------------------------------------------------------

def test_response_has_no_audit_timestamps(client) -> None:
    """access has no created_at / updated_at / *_by_id, unlike every other table."""
    body = client.post("/api/v1/access", json={"reference_type": "account"}).json()
    assert "created_at" not in body
    assert "updated_at" not in body
    assert "created_by_id" not in body
    assert "updated_by_id" not in body


# -----------------------------------------------------------------------------

def test_create_requires_reference_type(client) -> None:
    """API-level: every column on this table is nullable in the database."""
    assert client.post("/api/v1/access", json={}).status_code == 422
    assert client.post("/api/v1/access", json={"user_id": 1}).status_code == 422


# -----------------------------------------------------------------------------

def test_last_referenced_date_is_writable(client) -> None:
    """No set_updated_at trigger on this table, so the client owns the value."""
    stamp = "2026-01-15T09:30:00Z"
    created = client.post(
        "/api/v1/access",
        json={"reference_type": "account", "last_referenced_date": stamp},
    ).json()
    assert created["last_referenced_date"].startswith("2026-01-15T09:30:00")


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/access",
        json={"reference_type": "account", "reference_id": 7, "access_type": "View"},
    ).json()
    r = client.get(f"/api/v1/access/{created['id']}")
    assert r.status_code == 200
    assert r.json()["access_type"] == "View"
    assert r.json()["reference_id"] == 7


# -----------------------------------------------------------------------------

def test_get_missing_access_404(client) -> None:
    r = client.get("/api/v1/access/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Access 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for t in ("a", "b", "c"):
        client.post("/api/v1/access", json={"reference_type": t})
    first = client.get("/api/v1/access", params={"limit": 2}).json()
    second = client.get("/api/v1/access", params={"limit": 2, "offset": 2}).json()
    assert [a["reference_type"] for a in first] == ["a", "b"]
    assert [a["reference_type"] for a in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/access", json={"reference_type": "account", "access_type": "View"}
    ).json()
    r = client.put(f"/api/v1/access/{created['id']}", json={"access_type": "Edit"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_type"] == "Edit"
    assert body["reference_type"] == "account"   # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/access", json={"reference_type": "account"}).json()
    assert client.put(f"/api/v1/access/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_access_404(client) -> None:
    assert client.put("/api/v1/access/999", json={"access_type": "View"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/access", json={"reference_type": "account"}).json()
    assert client.delete(f"/api/v1/access/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/access/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_access_404(client) -> None:
    assert client.delete("/api/v1/access/999").status_code == 404


# -----------------------------------------------------------------------------
