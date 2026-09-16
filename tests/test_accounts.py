"""End-to-end tests for /api/v1/accounts.

Same shape as tests/test_users.py: the real app over HTTP against the
dedicated test Postgres; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/accounts")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/accounts", json={"name": "Acme"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["name"] == "Acme"
    # Server defaults come through untouched:
    assert body["is_deleted"] is False
    assert body["operating_systems"] == ""
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_name(client) -> None:
    assert client.post("/api/v1/accounts", json={}).status_code == 422
    assert client.post(
        "/api/v1/accounts", json={"industry": "Software"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_create_accepts_uuid_guid(client) -> None:
    """account.guid is a real uuid, unlike contact.guid."""
    guid = "5b82b0f0-0db7-45a9-8e14-e24ec063dd73"
    r = client.post("/api/v1/accounts", json={"name": "Acme", "guid": guid})
    assert r.status_code == 201
    assert r.json()["guid"] == guid


# -----------------------------------------------------------------------------

def test_create_rejects_malformed_guid(client) -> None:
    r = client.post("/api/v1/accounts", json={"name": "Acme", "guid": "not-a-uuid"})
    assert r.status_code == 422


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/accounts", json={"name": "Acme", "billing_city": "Melbourne"}
    ).json()
    r = client.get(f"/api/v1/accounts/{created['id']}")
    assert r.status_code == 200
    assert r.json()["billing_city"] == "Melbourne"


# -----------------------------------------------------------------------------

def test_get_missing_account_404(client) -> None:
    r = client.get("/api/v1/accounts/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Account 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for name in ("a", "b", "c"):
        client.post("/api/v1/accounts", json={"name": name})
    first = client.get("/api/v1/accounts", params={"limit": 2}).json()
    second = client.get("/api/v1/accounts", params={"limit": 2, "offset": 2}).json()
    assert [a["name"] for a in first] == ["a", "b"]
    assert [a["name"] for a in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/accounts",
        json={"name": "Acme", "industry": "Software", "billing_city": "Melbourne"},
    ).json()
    r = client.put(f"/api/v1/accounts/{created['id']}", json={"industry": "Hardware"})
    assert r.status_code == 200
    body = r.json()
    assert body["industry"] == "Hardware"
    assert body["name"] == "Acme"                # untouched
    assert body["billing_city"] == "Melbourne"   # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/accounts", json={"name": "Acme"}).json()
    assert client.put(f"/api/v1/accounts/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_account_404(client) -> None:
    r = client.put("/api/v1/accounts/999", json={"name": "Nobody"})
    assert r.status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/accounts", json={"name": "Acme"}).json()
    assert client.delete(f"/api/v1/accounts/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/accounts/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_account_404(client) -> None:
    assert client.delete("/api/v1/accounts/999").status_code == 404


# -----------------------------------------------------------------------------
