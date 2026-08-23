

# v0.2.0

Routes — new layer, verified live against Postgres:

```
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

```
┌───────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│   Step    │                                                       Result                                                        │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Changelog │ CHANGELOG.md created (none existed) — 0.2.0 covers the route layer + alembic move with the endpoint table and       │
│           │ design notes; 0.1.0 documents the scaffold                                                                          │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Version   │ pyproject.toml bumped 0.1.0 → 0.2.0                                                                                 │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Commit 1  │ eb4dfdd — the route code                                                                                            │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Commit 2  │ be14e20 — changelog + version bump (the tag anchor)                                                                 │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Tags      │ v0.2.0 → be14e20, and v0.1.0 back-tagged onto 3af39b4 — there were no tags at all before, so the scaffold release   │
│           │ got its marker too                                                                                                  │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Push      │ main (3af39b4..be14e20) + both tags, verified on the remote                                                         │
└───────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Why 0.2.0 fits: 0.1.0 was the scaffold — it booted and probed the DB but had no API surface. This release adds the first versioned endpoints, which is a feature, hence a minor bump under 0.x.

On your workflow question: I didn't have one saved — this was the first release. I've now written the procedure down and stored it in my project memory so every future release follows it automatically:

1. Changelog entry (Keep a Changelog format)
2. Bump pyproject.toml
3. Two commits on main: feature code, then release docs
4. Annotated vX.Y.Z tag on the release commit (back-tagging any untagged versions)
5. git push origin main --tags

Next up on your roadmap: more resources, auth, tests, README, Dockerfile, CI — just say which one.


