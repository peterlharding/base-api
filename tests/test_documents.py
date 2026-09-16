"""End-to-end tests for /api/v1/documents.

Same shape as tests/test_users.py; see doc/TESTING.md.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/documents", json={"name": "Proposal.pdf"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY after each test
    assert body["name"] == "Proposal.pdf"
    # Server defaults come through untouched:
    assert body["is_deleted"] is False
    assert body["is_public"] is False
    assert body["is_internal_use_only"] is False
    assert body["body_length"] == 0
    assert body["body_length_compressed"] == 0
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_name(client) -> None:
    assert client.post("/api/v1/documents", json={}).status_code == 422
    assert client.post(
        "/api/v1/documents", json={"content_type": "application/pdf"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_create_accepts_uuid_fields(client) -> None:
    guid = "5b82b0f0-0db7-45a9-8e14-e24ec063dd73"
    folder = "af5e9adf-4f90-4b9f-9a50-68f94742fe70"
    r = client.post(
        "/api/v1/documents",
        json={"name": "Proposal.pdf", "guid": guid, "folder_ref": folder},
    )
    assert r.status_code == 201
    assert r.json()["guid"] == guid
    assert r.json()["folder_ref"] == folder


# -----------------------------------------------------------------------------

def test_create_rejects_malformed_uuid(client) -> None:
    r = client.post("/api/v1/documents", json={"name": "x", "folder_ref": "not-a-uuid"})
    assert r.status_code == 422


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/documents", json={"name": "Proposal.pdf", "url": "https://example.com/p.pdf"}
    ).json()
    r = client.get(f"/api/v1/documents/{created['id']}")
    assert r.status_code == 200
    assert r.json()["url"] == "https://example.com/p.pdf"


# -----------------------------------------------------------------------------

def test_get_missing_document_404(client) -> None:
    r = client.get("/api/v1/documents/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Document 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for n in ("a", "b", "c"):
        client.post("/api/v1/documents", json={"name": n})
    first = client.get("/api/v1/documents", params={"limit": 2}).json()
    second = client.get("/api/v1/documents", params={"limit": 2, "offset": 2}).json()
    assert [d["name"] for d in first] == ["a", "b"]
    assert [d["name"] for d in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/documents", json={"name": "Proposal.pdf", "keywords": "sales"}
    ).json()
    r = client.put(f"/api/v1/documents/{created['id']}", json={"is_public": True})
    assert r.status_code == 200
    body = r.json()
    assert body["is_public"] is True
    assert body["name"] == "Proposal.pdf"   # untouched
    assert body["keywords"] == "sales"      # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/documents", json={"name": "x"}).json()
    assert client.put(f"/api/v1/documents/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_document_404(client) -> None:
    assert client.put("/api/v1/documents/999", json={"name": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/documents", json={"name": "x"}).json()
    assert client.delete(f"/api/v1/documents/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/documents/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_document_404(client) -> None:
    assert client.delete("/api/v1/documents/999").status_code == 404


# -----------------------------------------------------------------------------
