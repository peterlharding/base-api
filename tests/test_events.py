"""End-to-end tests for /api/v1/events.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/events")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/events", json={"subject": "Kickoff"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["subject"] == "Kickoff"
    # Server defaults come through untouched:
    assert body["is_all_day_event"] is False
    assert body["is_group_event"] is False
    assert body["is_private"] is False
    assert body["is_child"] is False
    assert body["is_archived"] is False
    assert body["is_deleted"] is False
    assert body["is_recurrence"] is False
    assert body["is_reminder_set"] is False
    assert body["duration_in_minutes"] == 0
    assert body["activity_datetime"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_subject(client) -> None:
    assert client.post("/api/v1/events", json={}).status_code == 422
    assert client.post("/api/v1/events", json={"location": "Room 1"}).status_code == 422


# -----------------------------------------------------------------------------

def test_owner_and_account_are_strings_on_this_table(client) -> None:
    """event.account_id / owner_id are varchar(18) here, not bigint.

    Pinning this because it differs from every other CRM table, where the
    same column names are bigint.
    """
    r = client.post(
        "/api/v1/events",
        json={"subject": "Review", "account_id": "001A000001BcdEfG", "owner_id": "005A000000XyzAbC"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["account_id"] == "001A000001BcdEfG"
    assert body["owner_id"] == "005A000000XyzAbC"


# -----------------------------------------------------------------------------

def test_recurrence_fields_round_trip(client) -> None:
    r = client.post("/api/v1/events", json={
        "subject": "Standup",
        "is_recurrence": True,
        "recurrence_type": "Weekly",
        "recurrence_day_of_week_mask": "62",
        "recurrence_end_date_only": "2026-12-31",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["is_recurrence"] is True
    assert body["recurrence_type"] == "Weekly"
    assert body["recurrence_end_date_only"] == "2026-12-31"


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/events", json={"subject": "Kickoff", "location": "Room 1"}
    ).json()
    r = client.get(f"/api/v1/events/{created['id']}")
    assert r.status_code == 200
    assert r.json()["location"] == "Room 1"


# -----------------------------------------------------------------------------

def test_get_missing_event_404(client) -> None:
    r = client.get("/api/v1/events/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Event 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for s in ("a", "b", "c"):
        client.post("/api/v1/events", json={"subject": s})
    first = client.get("/api/v1/events", params={"limit": 2}).json()
    second = client.get("/api/v1/events", params={"limit": 2, "offset": 2}).json()
    assert [e["subject"] for e in first] == ["a", "b"]
    assert [e["subject"] for e in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/events", json={"subject": "Kickoff", "location": "Room 1"}
    ).json()
    r = client.put(f"/api/v1/events/{created['id']}", json={"location": "Room 2"})
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "Room 2"
    assert body["subject"] == "Kickoff"   # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/events", json={"subject": "Kickoff"}).json()
    assert client.put(f"/api/v1/events/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_event_404(client) -> None:
    assert client.put("/api/v1/events/999", json={"subject": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/events", json={"subject": "Kickoff"}).json()
    assert client.delete(f"/api/v1/events/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/events/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_event_404(client) -> None:
    assert client.delete("/api/v1/events/999").status_code == 404


# -----------------------------------------------------------------------------
