"""End-to-end tests for /api/v1/leads.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/leads")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/leads", json={"last_name": "Nguyen"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["last_name"] == "Nguyen"
    # Server defaults come through untouched:
    assert body["do_not_call"] is False
    assert body["has_opted_out_of_fax"] is False
    assert body["has_opted_out_of_email"] is False
    assert body["is_unread_by_owner"] is False
    assert body["is_deleted"] is False
    assert body["is_converted"] is False
    assert body["activity_date"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_last_name(client) -> None:
    assert client.post("/api/v1/leads", json={}).status_code == 422
    assert client.post("/api/v1/leads", json={"company": "Acme"}).status_code == 422


# -----------------------------------------------------------------------------

def test_conversion_fields_are_not_cross_validated(client) -> None:
    """is_converted and the converted_* ids are independent.

    Nothing enforces that they are set together, so a lead can claim to be
    converted while pointing at nothing - pinned so the behaviour is explicit.
    """
    r = client.post(
        "/api/v1/leads", json={"last_name": "Nguyen", "is_converted": True}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["is_converted"] is True
    assert body["converted_account_id"] is None
    assert body["converted_contact_id"] is None
    assert body["converted_opportunity_id"] is None


# -----------------------------------------------------------------------------

def test_conversion_ids_round_trip(client) -> None:
    """The converted_* columns carry foreign keys, so the targets must exist."""
    account = client.post("/api/v1/accounts", json={"name": "Acme"}).json()
    contact = client.post("/api/v1/contacts", json={"last_name": "Nguyen"}).json()
    opp = client.post("/api/v1/opportunities", json={"name": "Acme renewal"}).json()

    r = client.post("/api/v1/leads", json={
        "last_name": "Nguyen",
        "is_converted": True,
        "converted_account_id": account["id"],
        "converted_contact_id": contact["id"],
        "converted_opportunity_id": opp["id"],
    })
    assert r.status_code == 201
    body = r.json()
    assert body["converted_account_id"] == account["id"]
    assert body["converted_contact_id"] == contact["id"]
    assert body["converted_opportunity_id"] == opp["id"]


# -----------------------------------------------------------------------------

def test_conversion_ids_must_exist(client) -> None:
    """A dangling reference is now rejected rather than silently stored."""
    r = client.post(
        "/api/v1/leads", json={"last_name": "Nguyen", "converted_account_id": 999}
    )
    assert r.status_code == 400
    assert "constraint" in r.json()["detail"]


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/leads", json={"last_name": "Nguyen", "company": "Southbank"}
    ).json()
    r = client.get(f"/api/v1/leads/{created['id']}")
    assert r.status_code == 200
    assert r.json()["company"] == "Southbank"


# -----------------------------------------------------------------------------

def test_get_missing_lead_404(client) -> None:
    r = client.get("/api/v1/leads/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Lead 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for n in ("a", "b", "c"):
        client.post("/api/v1/leads", json={"last_name": n})
    first = client.get("/api/v1/leads", params={"limit": 2}).json()
    second = client.get("/api/v1/leads", params={"limit": 2, "offset": 2}).json()
    assert [x["last_name"] for x in first] == ["a", "b"]
    assert [x["last_name"] for x in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/leads",
        json={"last_name": "Nguyen", "status": "New", "company": "Southbank"},
    ).json()
    r = client.put(f"/api/v1/leads/{created['id']}", json={"status": "Working"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "Working"
    assert body["last_name"] == "Nguyen"        # untouched
    assert body["company"] == "Southbank"       # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/leads", json={"last_name": "Nguyen"}).json()
    assert client.put(f"/api/v1/leads/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_lead_404(client) -> None:
    assert client.put("/api/v1/leads/999", json={"last_name": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/leads", json={"last_name": "Nguyen"}).json()
    assert client.delete(f"/api/v1/leads/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/leads/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_lead_404(client) -> None:
    assert client.delete("/api/v1/leads/999").status_code == 404


# -----------------------------------------------------------------------------
