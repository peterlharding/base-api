"""End-to-end tests for /api/v1/attachments.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/attachments")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/attachments", json={"name": "scan.pdf"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["name"] == "scan.pdf"
    # Server defaults come through untouched:
    assert body["body_length"] == 0
    assert body["body_length_compressed"] == 0
    assert body["is_deleted"] is False
    assert body["is_private"] is False
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_name(client) -> None:
    assert client.post("/api/v1/attachments", json={}).status_code == 422
    assert client.post(
        "/api/v1/attachments", json={"content_type": "application/pdf"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_parent_reference_is_unconstrained(client) -> None:
    """parent_id has no discriminator and no foreign key; any bigint is accepted."""
    r = client.post(
        "/api/v1/attachments", json={"name": "scan.pdf", "parent_id": 999999}
    )
    assert r.status_code == 201
    assert r.json()["parent_id"] == 999999


# -----------------------------------------------------------------------------

def test_create_rejects_malformed_uuid(client) -> None:
    r = client.post("/api/v1/attachments", json={"name": "x", "guid": "not-a-uuid"})
    assert r.status_code == 422


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/attachments", json={"name": "scan.pdf", "content_type": "application/pdf"}
    ).json()
    r = client.get(f"/api/v1/attachments/{created['id']}")
    assert r.status_code == 200
    assert r.json()["content_type"] == "application/pdf"


# -----------------------------------------------------------------------------

def test_get_missing_attachment_404(client) -> None:
    r = client.get("/api/v1/attachments/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Attachment 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for n in ("a", "b", "c"):
        client.post("/api/v1/attachments", json={"name": n})
    first = client.get("/api/v1/attachments", params={"limit": 2}).json()
    second = client.get("/api/v1/attachments", params={"limit": 2, "offset": 2}).json()
    assert [a["name"] for a in first] == ["a", "b"]
    assert [a["name"] for a in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/attachments", json={"name": "scan.pdf", "content_type": "application/pdf"}
    ).json()
    r = client.put(f"/api/v1/attachments/{created['id']}", json={"is_private": True})
    assert r.status_code == 200
    body = r.json()
    assert body["is_private"] is True
    assert body["name"] == "scan.pdf"                     # untouched
    assert body["content_type"] == "application/pdf"      # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/attachments", json={"name": "x"}).json()
    assert client.put(f"/api/v1/attachments/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_attachment_404(client) -> None:
    assert client.put("/api/v1/attachments/999", json={"name": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/attachments", json={"name": "x"}).json()
    assert client.delete(f"/api/v1/attachments/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/attachments/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_attachment_404(client) -> None:
    assert client.delete("/api/v1/attachments/999").status_code == 404


# -----------------------------------------------------------------------------
