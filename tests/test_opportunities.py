"""End-to-end tests for /api/v1/opportunities.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/opportunities")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/opportunities", json={"name": "Acme renewal"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["name"] == "Acme renewal"
    # Server defaults come through untouched:
    assert body["is_private"] is False
    assert body["is_closed"] is False
    assert body["is_won"] is False
    assert body["is_deleted"] is False
    assert body["has_opportunity_line_item"] is False
    assert body["close_date"] is not None
    assert body["last_activity_date"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_name(client) -> None:
    assert client.post("/api/v1/opportunities", json={}).status_code == 422
    assert client.post(
        "/api/v1/opportunities", json={"stage_name": "Prospecting"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_money_columns_are_strings_on_this_table(client) -> None:
    """amount / expected_revenue / probability are varchar here, not numeric.

    Pinned because quote uses numeric(12,2) for the equivalent columns.
    """
    r = client.post("/api/v1/opportunities", json={
        "name": "Acme renewal", "amount": "50000", "probability": "75",
        "expected_revenue": "37500",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == "50000"
    assert body["probability"] == "75"
    assert body["expected_revenue"] == "37500"


# -----------------------------------------------------------------------------

def test_uuid_reference_fields(client) -> None:
    campaign = "5b82b0f0-0db7-45a9-8e14-e24ec063dd73"
    r = client.post(
        "/api/v1/opportunities", json={"name": "Acme", "campaign_ref": campaign}
    )
    assert r.status_code == 201
    assert r.json()["campaign_ref"] == campaign
    assert client.post(
        "/api/v1/opportunities", json={"name": "Acme", "pricebook_ref": "not-a-uuid"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/opportunities", json={"name": "Acme", "stage_name": "Negotiation"}
    ).json()
    r = client.get(f"/api/v1/opportunities/{created['id']}")
    assert r.status_code == 200
    assert r.json()["stage_name"] == "Negotiation"


# -----------------------------------------------------------------------------

def test_get_missing_opportunity_404(client) -> None:
    r = client.get("/api/v1/opportunities/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Opportunity 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for n in ("a", "b", "c"):
        client.post("/api/v1/opportunities", json={"name": n})
    first = client.get("/api/v1/opportunities", params={"limit": 2}).json()
    second = client.get("/api/v1/opportunities", params={"limit": 2, "offset": 2}).json()
    assert [o["name"] for o in first] == ["a", "b"]
    assert [o["name"] for o in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/opportunities",
        json={"name": "Acme", "stage_name": "Prospecting", "amount": "1000"},
    ).json()
    r = client.put(
        f"/api/v1/opportunities/{created['id']}",
        json={"stage_name": "Closed Won", "is_won": True, "is_closed": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["stage_name"] == "Closed Won"
    assert body["is_won"] is True
    assert body["name"] == "Acme"        # untouched
    assert body["amount"] == "1000"      # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/opportunities", json={"name": "Acme"}).json()
    assert client.put(f"/api/v1/opportunities/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_opportunity_404(client) -> None:
    assert client.put("/api/v1/opportunities/999", json={"name": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/opportunities", json={"name": "Acme"}).json()
    assert client.delete(f"/api/v1/opportunities/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/opportunities/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_opportunity_404(client) -> None:
    assert client.delete("/api/v1/opportunities/999").status_code == 404


# -----------------------------------------------------------------------------
