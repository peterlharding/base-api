"""Unknown fields in a request payload are rejected, not silently dropped.

The write schemas set extra="forbid".  Before that, pydantic's default
extra="ignore" meant a misspelled field was discarded: a POST returned 201
with the value gone, and a PUT carrying only misspelled fields returned 400
"No fields provided to update" without saying which field was wrong.

The response schemas are deliberately left permissive - they are validated
from ORM objects, not caller-supplied dicts.
"""

import pytest


# Every resource, with the field that is mandatory on create.
RESOURCES = [
    ("users",         {"username": "u"}),
    ("accounts",      {"name": "Acme"}),
    ("contacts",      {"last_name": "Nguyen"}),
    ("tasks",         {"subject": "Call"}),
    ("events",        {"subject": "Kickoff"}),
    ("documents",     {"name": "doc.pdf"}),
    ("notes",         {"title": "Note"}),
    ("opportunities", {"name": "Deal"}),
    ("leads",         {"last_name": "Rossi"}),
    ("quotes",        {"quoter": "PLH"}),
    ("access",        {"reference_type": "account"}),
    ("attachments",   {"name": "scan.pdf"}),
]


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("resource,minimal", RESOURCES)
def test_create_rejects_unknown_field(client, resource, minimal) -> None:
    r = client.post(f"/api/v1/{resource}", json={**minimal, "nonsense": "x"})
    assert r.status_code == 422
    assert any("nonsense" in str(d["loc"]) for d in r.json()["detail"])


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("resource,minimal", RESOURCES)
def test_update_rejects_unknown_field(client, resource, minimal) -> None:
    created = client.post(f"/api/v1/{resource}", json=minimal).json()
    r = client.put(f"/api/v1/{resource}/{created['id']}", json={"nonsense": "x"})
    assert r.status_code == 422, "was 400 'No fields provided' before extra=forbid"
    assert any("nonsense" in str(d["loc"]) for d in r.json()["detail"])


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("resource,minimal", RESOURCES)
def test_create_still_accepts_known_fields(client, resource, minimal) -> None:
    """Guard against a typo in the config breaking every write."""
    assert client.post(f"/api/v1/{resource}", json=minimal).status_code == 201


# -----------------------------------------------------------------------------

def test_the_error_names_the_field(client) -> None:
    r = client.post("/api/v1/notes", json={"title": "N", "descrption": "typo"})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["type"] == "extra_forbidden"
    assert detail["loc"][-1] == "descrption"


# -----------------------------------------------------------------------------

def test_empty_update_is_still_400_not_422(client) -> None:
    """An empty body carries no unknown field, so it is still the 400."""
    created = client.post("/api/v1/notes", json={"title": "N"}).json()
    assert client.put(f"/api/v1/notes/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_responses_are_unaffected(client) -> None:
    """Response schemas stay permissive; they validate ORM objects."""
    created = client.post("/api/v1/accounts", json={"name": "Acme"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Acme"
    assert "created_at" in body and "updated_at" in body
    assert client.get(f"/api/v1/accounts/{body['id']}").status_code == 200


# -----------------------------------------------------------------------------
