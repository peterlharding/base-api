"""End-to-end tests for /api/v1/user-roles.

Same shape as tests/test_users.py; see doc/TESTING.md.
The route is kebab-cased because the resource name is two words.
"""


# -----------------------------------------------------------------------------

def test_list_empty(client) -> None:
    r = client.get("/api/v1/user-roles")
    assert r.status_code == 200
    assert r.json() == []


# -----------------------------------------------------------------------------

def test_create_minimal_populates_defaults(client) -> None:
    r = client.post("/api/v1/user-roles", json={"name": "Sales Manager"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1  # TRUNCATE ... RESTART IDENTITY before each test
    assert body["name"] == "Sales Manager"
    # Server defaults come through untouched:
    assert body["opportunity_access_for_account_owner"] == "Edit"
    assert body["case_access_for_account_owner"] == "Edit"
    assert body["contact_access_for_account_owner"] == "Edit"
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


# -----------------------------------------------------------------------------

def test_create_requires_name(client) -> None:
    assert client.post("/api/v1/user-roles", json={}).status_code == 422
    assert client.post(
        "/api/v1/user-roles", json={"portal_type": "None"}
    ).status_code == 422


# -----------------------------------------------------------------------------

def test_rejects_unknown_field(client) -> None:
    r = client.post("/api/v1/user-roles", json={"name": "X", "nonsense": 1})
    assert r.status_code == 422
    assert any("nonsense" in str(d["loc"]) for d in r.json()["detail"])


# -----------------------------------------------------------------------------

def test_role_hierarchy(client) -> None:
    """parent_role_id is a self-reference with a foreign key."""
    parent = client.post("/api/v1/user-roles", json={"name": "Managing Director"}).json()
    child = client.post(
        "/api/v1/user-roles",
        json={"name": "Sales Manager", "parent_role_id": parent["id"]},
    )
    assert child.status_code == 201
    assert child.json()["parent_role_id"] == parent["id"]


# -----------------------------------------------------------------------------

def test_dangling_parent_role_is_rejected(client) -> None:
    r = client.post("/api/v1/user-roles", json={"name": "X", "parent_role_id": 999})
    assert r.status_code == 400


# -----------------------------------------------------------------------------

def test_deleting_a_parent_role_flattens_children(client) -> None:
    """ON DELETE SET NULL, so the child role survives at top level."""
    parent = client.post("/api/v1/user-roles", json={"name": "MD"}).json()
    child = client.post(
        "/api/v1/user-roles", json={"name": "Sales", "parent_role_id": parent["id"]}
    ).json()

    assert client.delete(f"/api/v1/user-roles/{parent['id']}").status_code == 204

    after = client.get(f"/api/v1/user-roles/{child['id']}")
    assert after.status_code == 200
    assert after.json()["parent_role_id"] is None


# -----------------------------------------------------------------------------

def test_forecast_user_reference(client) -> None:
    user = client.post("/api/v1/users", json={"username": "forecaster"}).json()
    r = client.post(
        "/api/v1/user-roles", json={"name": "Sales", "forecast_user_id": user["id"]}
    )
    assert r.status_code == 201
    assert r.json()["forecast_user_id"] == user["id"]

    assert client.delete(f"/api/v1/users/{user['id']}").status_code == 204
    assert client.get(f"/api/v1/user-roles/{r.json()['id']}").json()["forecast_user_id"] is None


# -----------------------------------------------------------------------------

def test_get_by_id(client) -> None:
    created = client.post(
        "/api/v1/user-roles", json={"name": "Sales", "rollup_description": "Sales team"}
    ).json()
    r = client.get(f"/api/v1/user-roles/{created['id']}")
    assert r.status_code == 200
    assert r.json()["rollup_description"] == "Sales team"


# -----------------------------------------------------------------------------

def test_get_missing_user_role_404(client) -> None:
    r = client.get("/api/v1/user-roles/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "User role 999 not found"


# -----------------------------------------------------------------------------

def test_list_pagination(client) -> None:
    for n in ("a", "b", "c"):
        client.post("/api/v1/user-roles", json={"name": n})
    first = client.get("/api/v1/user-roles", params={"limit": 2}).json()
    second = client.get("/api/v1/user-roles", params={"limit": 2, "offset": 2}).json()
    assert [r["name"] for r in first] == ["a", "b"]
    assert [r["name"] for r in second] == ["c"]


# -----------------------------------------------------------------------------

def test_update_partial_only_changes_sent_fields(client) -> None:
    created = client.post(
        "/api/v1/user-roles", json={"name": "Sales", "portal_type": "None"}
    ).json()
    r = client.put(
        f"/api/v1/user-roles/{created['id']}",
        json={"contact_access_for_account_owner": "Read"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["contact_access_for_account_owner"] == "Read"
    assert body["name"] == "Sales"          # untouched
    assert body["portal_type"] == "None"    # untouched


# -----------------------------------------------------------------------------

def test_update_empty_body_400(client) -> None:
    created = client.post("/api/v1/user-roles", json={"name": "Sales"}).json()
    assert client.put(f"/api/v1/user-roles/{created['id']}", json={}).status_code == 400


# -----------------------------------------------------------------------------

def test_update_missing_user_role_404(client) -> None:
    assert client.put("/api/v1/user-roles/999", json={"name": "x"}).status_code == 404


# -----------------------------------------------------------------------------

def test_delete(client) -> None:
    created = client.post("/api/v1/user-roles", json={"name": "Sales"}).json()
    assert client.delete(f"/api/v1/user-roles/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/user-roles/{created['id']}").status_code == 404


# -----------------------------------------------------------------------------

def test_delete_missing_user_role_404(client) -> None:
    assert client.delete("/api/v1/user-roles/999").status_code == 404


# -----------------------------------------------------------------------------
