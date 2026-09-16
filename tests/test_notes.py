"""End-to-end tests for /api/v1/notes.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/notes")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/notes", json={"title": "Meeting notes"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["title"] == "Meeting notes"
    assert body["is_deleted"] is False
    assert body["is_private"] is False
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_title(client) -> None:
    assert client.post("/api/v1/notes", json={}).status_code == 422
    assert client.post("/api/v1/notes", json={"body": "orphan"}).status_code == 422


# -----------------------------------------------------------------------------

def test_parent_reference_round_trips(client) -> None:
    r = client.post(
        "/api/v1/notes",
        json={"title": "On the deal", "parent_type": "opportunity", "parent_id": 7},
    )
    assert r.status_code == 201
    body = r.json()
    assert (body["parent_type"], body["parent_id"]) == ("opportunity", 7)


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post("/api/v1/notes", json={"title": "T", "body": "B"}).json()
    r = client.get(f"/api/v1/notes/{created['id']}")
    assert r.status_code == 200
    assert r.json()["body"] == "B"


# -----------------------------------------------------------------------------

def test_get_missing_note_404(client) -> None:
    r = client.get("/api/v1/notes/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Note 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for t in ("a", "b", "c"):
        client.post("/api/v1/notes", json={"title": t})
    first = client.get("/api/v1/notes", params={"limit": 2}).json()
    second = client.get("/api/v1/notes", params={"limit": 2, "offset": 2}).json()
    assert [n["title"] for n in first] == ["a", "b"]
    assert [n["title"] for n in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post("/api/v1/notes", json={"title": "T", "body": "B"}).json()
    r = client.put(f"/api/v1/notes/{created['id']}", json={"is_private": True})
    assert r.status_code == 200
    body = r.json()
    assert body["is_private"] is True
    assert body["title"] == "T"   # untouched
    assert body["body"] == "B"    # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/notes", json={"title": "T"}).json()
    assert client.put(f"/api/v1/notes/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_note_404(client) -> None:
    assert client.put("/api/v1/notes/999", json={"title": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/notes", json={"title": "T"}).json()
    assert client.delete(f"/api/v1/notes/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/notes/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_note_404(client) -> None:
    assert client.delete("/api/v1/notes/999").status_code == 404


# -----------------------------------------------------------------------------
