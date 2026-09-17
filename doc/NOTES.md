
# v0.7.1

Done. Migration 0005 indexes all 25 foreign key columns.

## The measurement

I set out to verify this actually helps rather than assert it, and the first two attempts were wrong in instructive ways.

Attempt 1 pointed all 50,000 contacts at one account. The planner chose a seq scan correctly - when a predicate matches every row, scanning is cheaper than an index. Bad test, not a bad index.

Attempt 2 spread 50,000 contacts across 200 accounts. The index was used (Bitmap Index Scan on contact_account_id_idx), but the timings were identical with and without it - roughly 5ms either way. At that size the scan is cheap enough that the SET NULL update dominates.

Attempt 3, at 1M rows across 2,000 accounts, is where it shows:

```
with index:     9.1 ms   14.1 ms   11.7 ms
without index: 49.2 ms   47.5 ms   46.4 ms
```

About 4x, and widening - the scan is O(n) while the lookup isn't. So the honest summary is that this does nothing at your current volumes and matters once these tables get large, which is the reason to add it now rather than later.

## Verified

```
fresh build             0001..0005, 35 non-pkey indexes
unindexed FK columns    0
downgrade round trip    35 -> 10 -> 35
dev upgraded in place   0004 -> 0005, seed rows intact
dev vs test schema      identical (indexes and constraints)
autogenerate drift      only instance_metadata_singleton
make test               164 passed
```

The indexes are declared in each model's __table_args__ too, so autogenerate stays clean - without that it would have proposed dropping all 25, the same trap the CRM models hit earlier.

## Two choices worth knowing

Built inside the transaction, not CONCURRENTLY. A transactional build is atomic and leaves nothing behind on failure, and at these sizes the write lock is momentary. CREATE
INDEX CONCURRENTLY can't run in a transaction and can leave an invalid inde right call only once the lock duration actually matters. That reasoningis in the migration docstring.

Naming follows <table>_<column>_idx, matching login_session_user_id_idx and token_blacklist_user_id_idx rather than SQLAlchemy's ix_ default.                                
CLAUDE.md/AGENTS.md had this listed as an open gap; that's now replaced with the measurement and a note that any new foreign key should get its index in the same migration. Changelog has a fresh [Unreleased] section.

---

No measurable difference at 50k rows - the times are equivalent. Let me find where it actually matters rather than assert a benefit I haven't measured:

Clear at scale:

┌───────────────┬──────────┬──────────┐
│               │ 50k rows │ 1M rows  │
├───────────────┼──────────┼──────────┤
│ with index    │ ~5 ms    │ ~11.7 ms │
├───────────────┼──────────┼──────────┤
│ without index │ ~5 ms    │ ~47.5 ms │
└───────────────┴──────────┴──────────┘

Roughly 4x at a million rows, and widening - the seq scan is O(n) while the index lookup isn't. Clearing the synthetic data and running the full verification:


# v0.2.0

Routes — new layer, verified live against Postgres:

```bash
app/api/v1/
├── router.py           api_router (prefix /api/v1)
├── schemas.py          UserCreate / UserUpdate / User
└── endpoints/
    └── users.py        CRUD for application_user
```

* GET  /api/v1/users?limit=&offset= — paged list (default 50, max 200)
* POST /api/v1/users — create; only username mandatory
* GET/PUT/DELETE /api/v1/users/{id} — by surrogate key; PUT is patch-style (only fields sent are changed), empty body → 400

Design choices worth knowing: password and the *_by_id audit stamps are deliberately excluded from the schemas (never exposed, never written); the path param is id to avoid clashing with the legacy string user_id column; DB server defaults (timezone Australia/Melbourne, user_type 'Standard', etc.) come through untouched on create.

Verified end-to-end: list → create (201, defaults populated) → get (200) → patch (200) → empty PUT (400) → delete (204) → get-after-delete (404) → missing username (422). One curiosity: the sequence had advanced past a previously-deleted row, so new ids start at 2 — harmless, but row 1 no longer exists in application_user.


---

All done — and yes on the version call. Summary:

v0.2.0 release, pushed to origin:

|   Step    |                                                       Result                                                        |
| --------- | ------------------------------------------------------------------------------------------------------------------- |
| Changelog | CHANGELOG.md created (none existed) — 0.2.0 covers the route layer + alembic move with the endpoint table and       |
|           | design notes; 0.1.0 documents the scaffold                                                                          |
| Version   | pyproject.toml bumped 0.1.0 → 0.2.0                                                                                 |
| Commit 1  | eb4dfdd — the route code                                                                                            |
| Commit 2  | be14e20 — changelog + version bump (the tag anchor)                                                                 |
| Tags      | v0.2.0 → be14e20, and v0.1.0 back-tagged onto 3af39b4 — there were no tags at all before, so the scaffold release   |
|           | got its marker too                                                                                                  |
| Push      | main (3af39b4..be14e20) + both tags, verified on the remote                                                         |


Why 0.2.0 fits: 0.1.0 was the scaffold — it booted and probed the DB but had no API surface. This release adds the first versioned endpoints, which is a feature, hence a minor bump under 0.x.

On your workflow question: I didn't have one saved — this was the first release. I've now written the procedure down and stored it in my project memory so every future release follows it automatically:

1. Changelog entry (Keep a Changelog format)
2. Bump pyproject.toml
3. Two commits on main: feature code, then release docs
4. Annotated vX.Y.Z tag on the release commit (back-tagging any untagged versions)
5. git push origin main --tags

Next up on your roadmap: more resources, auth, tests, README, Dockerfile, CI — just say which one.


---

Alright — the working tree is clean, git-chk is in the Makefile, and
doc/ and scripts/git-chk.sh are committed. Before I put together the
test infrastructure design, I'll quickly check the environment (docker
availability, and which Postgres image the dev stack is using so that
the test stack matches it):


Environment check complete: Docker 29 + Compose v5.4, and the dev stack
is running on a floating postgres image. Now I've got the whole picture:

* Sync SQLAlchemy + psycopg 3, with the engine created at import time
from get_settings().database_url — meaning if I override the environment
variables before importing the app, the whole stack (including alembic's
env.py, which uses the same settings) will point at the test DB without
any code changes.
* The endpoint calls db.commit() — so the common "wrap each test in a
transaction and roll it back" pattern won't work. Instead, per-test
TRUNCATE … RESTART IDENTITY is the correct isolation strategy (and as
a bonus, you get deterministic IDs).
* pydantic-settings gives environment variables priority over .env, so
DB_PORT/DB_NAME can be overridden for testing.

This is a multi-file build (compose file, conftest, test suite, Makefile
targets, dev dependencies). So let me put together a plan to get your
approval.

---



