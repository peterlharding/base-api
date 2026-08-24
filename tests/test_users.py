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
    assert body["timezone_key"] == "Australia/Melbourne"
    assert body["user_type"] == "Standard"
    assert body["locale_key"] == "en_AU"
    assert body["email_encoding_key"] == "ISO-8859-1"
    assert body["start_day"] == 6
    assert body["end_day"] == 23
    assert body["created_date"] is not None
    assert body["last_modified_date"] is not None
    # Never exposed:
    assert "password" not in body


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
