"""End-to-end tests for /api/v1/contacts.

Same shape as tests/test_users.py: the real app over HTTP against the
dedicated test Postgres; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/contacts")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/contacts", json={"last_name": "Harding"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["last_name"] == "Harding"
    # Server defaults come through untouched:
    assert body["do_not_call"] is False
    assert body["has_opted_out_of_email"] is False
    assert body["has_opted_out_of_fax"] is False
    assert body["is_deleted"] is False
    assert body["last_activity_date"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_last_name(client) -> None:
    assert client.post("/api/v1/contacts", json={}).status_code == 422
    assert client.post(
        "/api/v1/contacts", json={"first_name": "Peter"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/contacts", json={"last_name": "Harding", "email": "plh@example.com"}
    ).json()
    r = client.get(f"/api/v1/contacts/{created['id']}")
    assert r.status_code == 200
    assert r.json()["email"] == "plh@example.com"


# -----------------------------------------------------------------------------

def test_get_missing_contact_404(client) -> None:
    r = client.get("/api/v1/contacts/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Contact 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for name in ("a", "b", "c"):
        client.post("/api/v1/contacts", json={"last_name": name})
    first = client.get("/api/v1/contacts", params={"limit": 2}).json()
    second = client.get("/api/v1/contacts", params={"limit": 2, "offset": 2}).json()
    assert [c["last_name"] for c in first] == ["a", "b"]
    assert [c["last_name"] for c in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/contacts",
        json={"last_name": "Harding", "first_name": "Pete", "mailing_city": "Melbourne"},
    ).json()
    r = client.put(f"/api/v1/contacts/{created['id']}", json={"first_name": "Peter"})
    assert r.status_code == 200
    body = r.json()
    assert body["first_name"] == "Peter"
    assert body["last_name"] == "Harding"        # untouched
    assert body["mailing_city"] == "Melbourne"   # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/contacts", json={"last_name": "Harding"}).json()
    assert client.put(f"/api/v1/contacts/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_contact_404(client) -> None:
    r = client.put("/api/v1/contacts/999", json={"first_name": "Nobody"})
    assert r.status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/contacts", json={"last_name": "Harding"}).json()
    assert client.delete(f"/api/v1/contacts/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/contacts/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_contact_404(client) -> None:
    assert client.delete("/api/v1/contacts/999").status_code == 404


# -----------------------------------------------------------------------------

def test_duplicate_email_allowed(client) -> None:
    """contact.email carries no UNIQUE constraint, unlike application_user."""
    assert client.post(
        "/api/v1/contacts", json={"last_name": "One", "email": "dup@example.com"}
    ).status_code == 201
    assert client.post(
        "/api/v1/contacts", json={"last_name": "Two", "email": "dup@example.com"}
    ).status_code == 201


# -----------------------------------------------------------------------------
