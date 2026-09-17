"""created_by_id and updated_by_id are set from the bearer token.

Applied in crud.commit(), which every write already funnels through, so no
route can quietly skip it.  The columns are readable but never writable: a
client cannot claim the work was done by someone else.
"""

import pytest
from sqlalchemy import insert, select

from app.auth.handler import sign_token
from app.db.session import SessionLocal
from app.models import Account, ApplicationUser

from conftest import OVERRIDE_USER_GUID


ACTOR_GUID = "dddddddd-eeee-ffff-0000-111111111111"
OTHER_GUID = "eeeeeeee-ffff-0000-1111-222222222222"


@pytest.fixture()
def actors():
    """Two real users, so a stamp can be attributed to a specific one."""
    with SessionLocal() as s:
        s.execute(insert(ApplicationUser).values(
            username="actor", guid=ACTOR_GUID, is_active=True))
        s.execute(insert(ApplicationUser).values(
            username="other", guid=OTHER_GUID, is_active=True))
        s.commit()
        rows = {u.guid.__str__(): u.id
                for u in s.scalars(select(ApplicationUser))}
    return rows


# -----------------------------------------------------------------------------

def _auth(guid):
    return {"Authorization": f"Bearer {sign_token(guid)}"}


# -----------------------------------------------------------------------------

def test_create_stamps_both_columns(protected_client, actors) -> None:
    r = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                              headers=_auth(ACTOR_GUID))
    assert r.status_code == 201
    body = r.json()
    assert body["created_by_id"] == actors[ACTOR_GUID]
    assert body["updated_by_id"] == actors[ACTOR_GUID]


# -----------------------------------------------------------------------------

def test_update_changes_only_updated_by(protected_client, actors) -> None:
    """created_by_id records who made the row and must not move."""
    created = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                                    headers=_auth(ACTOR_GUID)).json()

    r = protected_client.put(f"/api/v1/accounts/{created['id']}",
                             json={"industry": "Software"},
                             headers=_auth(OTHER_GUID))
    assert r.status_code == 200
    body = r.json()
    assert body["created_by_id"] == actors[ACTOR_GUID], "creator was overwritten"
    assert body["updated_by_id"] == actors[OTHER_GUID]


# -----------------------------------------------------------------------------

def test_a_client_cannot_set_the_stamps(protected_client, actors) -> None:
    """They are absent from the write schema, so sending them is a 422."""
    r = protected_client.post(
        "/api/v1/accounts",
        json={"name": "Acme", "created_by_id": 999, "updated_by_id": 999},
        headers=_auth(ACTOR_GUID))
    assert r.status_code == 422
    locs = str(r.json()["detail"])
    assert "created_by_id" in locs and "updated_by_id" in locs


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("resource,minimal", [
    ("accounts",      {"name": "Acme"}),
    ("contacts",      {"last_name": "Nguyen"}),
    ("tasks",         {"subject": "Call"}),
    ("events",        {"subject": "Kickoff"}),
    ("documents",     {"name": "doc.pdf"}),
    ("notes",         {"title": "Note"}),
    ("opportunities", {"name": "Deal"}),
    ("leads",         {"last_name": "Rossi"}),
    ("quotes",        {"quoter": "PLH"}),
    ("attachments",   {"name": "scan.pdf"}),
    ("user-roles",    {"name": "Sales"}),
    ("users",         {"username": "someone"}),
])
def test_every_stamped_resource_records_the_actor(
    protected_client, actors, resource, minimal
) -> None:
    r = protected_client.post(f"/api/v1/{resource}", json=minimal,
                              headers=_auth(ACTOR_GUID))
    assert r.status_code == 201, r.text
    assert r.json()["created_by_id"] == actors[ACTOR_GUID], f"{resource} unstamped"


# -----------------------------------------------------------------------------

def test_access_has_no_stamps_and_still_works(protected_client, actors) -> None:
    """access carries neither column; commit() must not trip over that."""
    r = protected_client.post("/api/v1/access", json={"reference_type": "account"},
                              headers=_auth(ACTOR_GUID))
    assert r.status_code == 201
    assert "created_by_id" not in r.json()


# -----------------------------------------------------------------------------

def test_stamp_is_written_to_the_database_not_just_echoed(protected_client, actors) -> None:
    created = protected_client.post("/api/v1/accounts", json={"name": "Acme"},
                                    headers=_auth(ACTOR_GUID)).json()
    with SessionLocal() as s:
        row = s.scalar(select(Account).where(Account.id == created["id"]))
        assert row.created_by_id == actors[ACTOR_GUID]
        assert row.updated_by_id == actors[ACTOR_GUID]
