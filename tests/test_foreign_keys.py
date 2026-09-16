"""Foreign key behaviour across the CRM tables (migration 0004).

The constraints are ON DELETE SET NULL, so deleting a parent orphans its
children rather than destroying them.  They are DEFERRABLE INITIALLY
IMMEDIATE, so an ordinary request still fails on the offending statement.
"""


# -----------------------------------------------------------------------------

def _user(client, username="owner"):
    return client.post("/api/v1/users", json={"username": username}).json()


def _account(client, name="Acme"):
    return client.post("/api/v1/accounts", json={"name": name}).json()


# -----------------------------------------------------------------------------

def test_dangling_reference_is_rejected(client) -> None:
    r = client.post("/api/v1/contacts", json={"last_name": "X", "account_id": 999})
    assert r.status_code == 400
    assert "constraint" in r.json()["detail"]


# -----------------------------------------------------------------------------

def test_valid_reference_is_accepted(client) -> None:
    account = _account(client)
    r = client.post(
        "/api/v1/contacts", json={"last_name": "X", "account_id": account["id"]}
    )
    assert r.status_code == 201
    assert r.json()["account_id"] == account["id"]


# -----------------------------------------------------------------------------

def test_update_to_a_dangling_reference_is_rejected(client) -> None:
    contact = client.post("/api/v1/contacts", json={"last_name": "X"}).json()
    r = client.put(f"/api/v1/contacts/{contact['id']}", json={"account_id": 999})
    assert r.status_code == 400


# -----------------------------------------------------------------------------

def test_deleting_an_account_orphans_its_contacts(client) -> None:
    """ON DELETE SET NULL: the contact survives, unlinked."""
    account = _account(client)
    contact = client.post(
        "/api/v1/contacts", json={"last_name": "X", "account_id": account["id"]}
    ).json()

    assert client.delete(f"/api/v1/accounts/{account['id']}").status_code == 204

    after = client.get(f"/api/v1/contacts/{contact['id']}")
    assert after.status_code == 200, "the contact must not be deleted with its account"
    assert after.json()["account_id"] is None


# -----------------------------------------------------------------------------

def test_deleting_a_user_orphans_what_they_owned(client) -> None:
    user = _user(client)
    account = client.post(
        "/api/v1/accounts", json={"name": "Acme", "owner_id": user["id"]}
    ).json()

    assert client.delete(f"/api/v1/users/{user['id']}").status_code == 204

    after = client.get(f"/api/v1/accounts/{account['id']}")
    assert after.status_code == 200
    assert after.json()["owner_id"] is None


# -----------------------------------------------------------------------------

def test_self_reference_flattens_on_delete(client) -> None:
    """account.parent_id points at account; deleting a parent does not cascade."""
    parent = _account(client, "Parent")
    child = client.post(
        "/api/v1/accounts", json={"name": "Child", "parent_id": parent["id"]}
    ).json()

    assert client.delete(f"/api/v1/accounts/{parent['id']}").status_code == 204

    after = client.get(f"/api/v1/accounts/{child['id']}")
    assert after.status_code == 200
    assert after.json()["parent_id"] is None


# -----------------------------------------------------------------------------

def test_polymorphic_references_stay_unconstrained(client) -> None:
    """These carry a discriminator, so they cannot take a foreign key.

    Pinned so the asymmetry is deliberate rather than an oversight.
    """
    assert client.post(
        "/api/v1/notes", json={"title": "N", "parent_type": "account", "parent_id": 999}
    ).status_code == 201
    assert client.post(
        "/api/v1/attachments", json={"name": "a.pdf", "parent_id": 999}
    ).status_code == 201
    assert client.post(
        "/api/v1/tasks", json={"subject": "T", "who_type": "contact", "who_id": 999}
    ).status_code == 201


# -----------------------------------------------------------------------------
