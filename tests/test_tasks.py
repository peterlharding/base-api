"""End-to-end tests for /api/v1/tasks.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/tasks")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/tasks", json={"subject": "Call back"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["subject"] == "Call back"
    # Server defaults come through untouched:
    assert body["is_closed"] is False
    assert body["is_deleted"] is False
    assert body["is_archived"] is False
    assert body["is_reminder_set"] is False
    assert body["call_duration_in_seconds"] == 0
    assert body["activity_date"] is not None
    assert body["reminder_datetime"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_subject(client) -> None:
    assert client.post("/api/v1/tasks", json={}).status_code == 422
    assert client.post("/api/v1/tasks", json={"status": "Open"}).status_code == 422


# -----------------------------------------------------------------------------

def test_polymorphic_reference_round_trips(client) -> None:
    """who_*/what_* are a free discriminator plus id; nothing validates them."""
    r = client.post("/api/v1/tasks", json={
        "subject": "Follow up",
        "who_type": "contact", "who_id": 1,
        "what_type": "account", "what_id": 2,
    })
    assert r.status_code == 201
    body = r.json()
    assert (body["who_type"], body["who_id"]) == ("contact", 1)
    assert (body["what_type"], body["what_id"]) == ("account", 2)


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post("/api/v1/tasks", json={"subject": "Call", "priority": "High"}).json()
    r = client.get(f"/api/v1/tasks/{created['id']}")
    assert r.status_code == 200
    assert r.json()["priority"] == "High"


# -----------------------------------------------------------------------------

def test_get_missing_task_404(client) -> None:
    r = client.get("/api/v1/tasks/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Task 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for s in ("a", "b", "c"):
        client.post("/api/v1/tasks", json={"subject": s})
    first = client.get("/api/v1/tasks", params={"limit": 2}).json()
    second = client.get("/api/v1/tasks", params={"limit": 2, "offset": 2}).json()
    assert [t["subject"] for t in first] == ["a", "b"]
    assert [t["subject"] for t in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/tasks", json={"subject": "Call", "status": "Open", "priority": "Low"}
    ).json()
    r = client.put(f"/api/v1/tasks/{created['id']}", json={"status": "Closed"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "Closed"
    assert body["subject"] == "Call"    # untouched
    assert body["priority"] == "Low"    # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/tasks", json={"subject": "Call"}).json()
    assert client.put(f"/api/v1/tasks/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_task_404(client) -> None:
    assert client.put("/api/v1/tasks/999", json={"subject": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/tasks", json={"subject": "Call"}).json()
    assert client.delete(f"/api/v1/tasks/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/tasks/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_task_404(client) -> None:
    assert client.delete("/api/v1/tasks/999").status_code == 404


# -----------------------------------------------------------------------------
