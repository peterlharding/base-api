# TODO

Outstanding work on base-api, roughly in the order it is worth doing.

## 1. Retention

Three tables grow without bound and nothing prunes them:

- `audit_log` - one row per mutation, by design.  How long is a
  retention decision, not a cleanup one.
- `login_session` - one row per sign-in, never deleted.
- `token_blacklist` - pruned on logout and by `make prune-blacklist`,
  but nothing runs the latter on a schedule.

## 2. No revoke-all

Signing out one device leaves the others signed in, so there is no way
to respond to a compromised account in one action.

Current release: v0.7.1.

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
- **Logout revokes one token, not every token a user holds.**
  Signing out on one device leaves other devices signed in.
  A revoke-all would be a separate endpoint.
- **`token_blacklist` is pruned on logout, not on a schedule.**
  The table only grows on logout, so that is where it is kept in check.
  `make prune-blacklist` covers a deployment where nobody signs out for a
  long stretch; nothing runs it automatically.
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
