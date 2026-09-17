# TODO

Outstanding work on base-api, roughly in the order it is worth doing.
Current release: v0.7.1.

## 1. The API does not write audit_log itself

`login_session` is now recorded server-side on every sign-in, and the
front end can `POST` its own activity to `/api/v1/audit-log`.
What is missing is the API recording its own mutations - a create, update or
delete through any CRUD route leaves no trace.

---

## Deliberate non-goals

Recorded so they are not mistaken for oversights.

- **Twenty reference columns carry no foreign key.**
  Polymorphic ones paired with a discriminator (`task.who_id`,
  `note.parent_id`, `access.reference_id`, `attachment.parent_id`), ones of
  the wrong type (`event.account_id` and `event.owner_id` are varchar on that
  table), and ones with no target table (`application_user.profile_id`, the
  `*_ref` columns).
  `tests/test_foreign_keys.py` pins this so it reads as a decision.
- **Sample data is not loaded by a migration.**
  See the docstring in `scripts/seed.py`.
- **Constraints live only in the migration that introduces them**, never in
  `db/schema/create/*.sql`, because Postgres has no
  `ADD CONSTRAINT IF NOT EXISTS`.
- **Migration tests use their own database.**
  `tests/test_migrations.py` creates and drops a scratch database per
  session, because it moves the schema version around.
  The rest of the suite shares one database already at head.
- **`/health` is unauthenticated.**
  It is a liveness probe; requiring a token would defeat it.
- **`/api/v1/auth/authenticate` is unauthenticated by design.**
  It carries its own HTTP Basic layer instead, and a test asserts it stays
  reachable without a bearer token - otherwise no client could ever obtain
  one.
- **Write schemas reject unknown fields, response schemas do not.**
  The response models are validated from ORM objects rather than
  caller-supplied dicts, so forbidding extras there buys nothing.
