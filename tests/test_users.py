"""End-to-end tests for /api/v1/users.

Each test drives the real app (routing, SQLAlchemy, Postgres via
docker/test) over HTTP through the TestClient; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_health_reports_database(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/users")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/users", json={"username": "alice"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["username"] == "alice"
    # Server defaults come through untouched:
    assert body["is_active"] is True
    assert body["timezone_sid_key"] == "Australia/Melbourne"
    assert body["user_type"] == "Standard"
    assert body["locale_sid_key"] == "en_AU"
    assert body["email_encoding_key"] == "ISO-8859-1"
    assert body["receives_info_emails"] is False
    assert body["receives_admin_info_emails"] is False
    assert body["start_day"] == 6
    assert body["end_day"] == 23
    assert body["created_at"] is not None
    assert body["updated_at"] is not None
    # Never exposed:
    assert "hashed_password" not in body


# -----------------------------------------------------------------------------

def test_create_requires_username(client) -> None:
    r = client.post("/api/v1/users", json={})
    assert r.status_code == 422


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post("/api/v1/users", json={"username": "bob"}).json()
    r = client.get(f"/api/v1/users/{created['id']}")
    assert r.status_code == 200
    assert r.json()["username"] == "bob"


# -----------------------------------------------------------------------------

def test_get_missing_user_404(client) -> None:
    assert client.get("/api/v1/users/999").status_code == 404


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for name in ("a", "b", "c"):
        client.post("/api/v1/users", json={"username": name})
    first = client.get("/api/v1/users", params={"limit": 2}).json()
    second = client.get("/api/v1/users", params={"limit": 2, "offset": 2}).json()
    assert [u["username"] for u in first] == ["a", "b"]
    assert [u["username"] for u in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/users", json={"username": "carol", "first_name": "Caroline"}
    ).json()
    r = client.put(f"/api/v1/users/{created['id']}", json={"first_name": "Carol"})
    assert r.status_code == 200
    body = r.json()
    assert body["first_name"] == "Carol"
    assert body["username"] == "carol"  # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/users", json={"username": "dave"}).json()
    r = client.put(f"/api/v1/users/{created['id']}", json={})
    assert r.status_code == 400


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/users", json={"username": "erin"}).json()
    assert client.delete(f"/api/v1/users/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/users/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_create_duplicate_email_409(client) -> None:
    """application_user.email is UNIQUE; a clash is a conflict, not a 500."""
    first = client.post(
        "/api/v1/users", json={"username": "one", "email": "dup@example.com"}
    )
    assert first.status_code == 201

    clash = client.post(
        "/api/v1/users", json={"username": "two", "email": "dup@example.com"}
    )
    assert clash.status_code == 409
    assert "email" in clash.json()["detail"]


# -----------------------------------------------------------------------------

def test_update_to_duplicate_email_409(client) -> None:
    client.post("/api/v1/users", json={"username": "one", "email": "a@example.com"})
    second = client.post(
        "/api/v1/users", json={"username": "two", "email": "b@example.com"}
    ).json()

    r = client.put(
        f"/api/v1/users/{second['id']}", json={"email": "a@example.com"}
    )
    assert r.status_code == 409


# -----------------------------------------------------------------------------

def test_session_still_usable_after_conflict(client) -> None:
    """The rollback in _commit leaves the connection healthy for the next call."""
    client.post("/api/v1/users", json={"username": "one", "email": "dup@example.com"})
    assert client.post(
        "/api/v1/users", json={"username": "two", "email": "dup@example.com"}
    ).status_code == 409

    ok = client.post(
        "/api/v1/users", json={"username": "three", "email": "fresh@example.com"}
    )
    assert ok.status_code == 201
    assert len(client.get("/api/v1/users").json()) == 2


# -----------------------------------------------------------------------------

def test_duplicate_email_leaves_no_row(client) -> None:
    client.post("/api/v1/users", json={"username": "one", "email": "dup@example.com"})
    client.post("/api/v1/users", json={"username": "two", "email": "dup@example.com"})
    assert [u["username"] for u in client.get("/api/v1/users").json()] == ["one"]


# -----------------------------------------------------------------------------

def test_null_emails_do_not_clash(client) -> None:
    """UNIQUE allows many NULLs, so users without an email are unaffected."""
    assert client.post("/api/v1/users", json={"username": "one"}).status_code == 201
    assert client.post("/api/v1/users", json={"username": "two"}).status_code == 201


# -----------------------------------------------------------------------------
