"""End-to-end tests for /api/v1/quotes.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/quotes")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/quotes", json={"quoter": "PLH"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["quoter"] == "PLH"
    # Server defaults come through untouched:
    assert body["status"] == "Active"
    assert body["comment"] == ""
    assert body["description"] == ""
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_quoter(client) -> None:
    """quoter is NOT NULL in the database, not just an API-level choice."""
    assert client.post("/api/v1/quotes", json={}).status_code == 422
    assert client.post("/api/v1/quotes", json={"company": "Acme"}).status_code == 422


# -----------------------------------------------------------------------------

def test_money_keeps_exact_precision(client) -> None:
    """numeric(12,2) round-trips as a string, so no float rounding creeps in."""
    r = client.post("/api/v1/quotes", json={
        "quoter": "PLH",
        "quote_amount": "1234.50",
        "order_amount": "0.01",
        "invoice_amount": "9999999999.99",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["quote_amount"] == "1234.50"
    assert body["order_amount"] == "0.01"
    assert body["invoice_amount"] == "9999999999.99"


# -----------------------------------------------------------------------------

def test_money_rejects_non_numeric(client) -> None:
    r = client.post("/api/v1/quotes", json={"quoter": "PLH", "quote_amount": "lots"})
    assert r.status_code == 422


# -----------------------------------------------------------------------------

def test_dates_round_trip(client) -> None:
    r = client.post("/api/v1/quotes", json={
        "quoter": "PLH", "quote_date": "2026-01-15", "order_date": "2026-02-01",
    })
    assert r.status_code == 201
    assert r.json()["quote_date"] == "2026-01-15"
    assert r.json()["order_date"] == "2026-02-01"


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post("/api/v1/quotes", json={"quoter": "PLH", "order_no": "SO-1"}).json()
    r = client.get(f"/api/v1/quotes/{created['id']}")
    assert r.status_code == 200
    assert r.json()["order_no"] == "SO-1"


# -----------------------------------------------------------------------------

def test_get_missing_quote_404(client) -> None:
    r = client.get("/api/v1/quotes/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Quote 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for q in ("a", "b", "c"):
        client.post("/api/v1/quotes", json={"quoter": q})
    first = client.get("/api/v1/quotes", params={"limit": 2}).json()
    second = client.get("/api/v1/quotes", params={"limit": 2, "offset": 2}).json()
    assert [q["quoter"] for q in first] == ["a", "b"]
    assert [q["quoter"] for q in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/quotes", json={"quoter": "PLH", "quote_amount": "100.00"}
    ).json()
    r = client.put(f"/api/v1/quotes/{created['id']}", json={"status": "Closed"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "Closed"
    assert body["quoter"] == "PLH"                # untouched
    assert body["quote_amount"] == "100.00"       # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/quotes", json={"quoter": "PLH"}).json()
    assert client.put(f"/api/v1/quotes/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_quote_404(client) -> None:
    assert client.put("/api/v1/quotes/999", json={"quoter": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/quotes", json={"quoter": "PLH"}).json()
    assert client.delete(f"/api/v1/quotes/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/quotes/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_quote_404(client) -> None:
    assert client.delete("/api/v1/quotes/999").status_code == 404


# -----------------------------------------------------------------------------
