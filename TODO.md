# TODO

Outstanding work on base-api, roughly in the order it is worth doing.
Current release: v0.7.1.

## 1. Endpoints for the React front end

Three tables exist, are modelled and migrated, and have no endpoints.
The front end needs all three:

- **`login_session`** - so the app can record a sign-in and list active
  sessions.  `app/utils.py` has a `log_session` helper that nothing calls,
  and whose signature does not match the commented-out call in
  `app/api/v1/endpoints/auth.py`.
- **`audit_log`** - so the app can record activity.  Wants `application`,
  `reference_type`, `reference_id`, `event`, `description` and `user_id` on
  each mutation.  `user_id` is now available: the bearer dependency resolves
  a token to an ApplicationUser.
- **`instance_metadata`** - so the app can report backend and schema
  versions.  The table carries release and version check constraints and a
  singleton index, but holds no row, so something has to stamp it.

Unlike the CRM resources these are not plain CRUD: `audit_log` and
`login_session` are append-mostly and should probably not accept arbitrary
updates or deletes, and `instance_metadata` is a singleton.

## 2. Nothing writes `audit_log` or `login_session`

Separate from having endpoints: the API itself should record sign-ins and
mutations, rather than relying on the front end to report its own activity.

## 3. `created_by_id` / `updated_by_id` are never set

Every table carries them and every row has them NULL.
Now unblocked - the bearer dependency yields the acting user, so the CRUD
layer could stamp them.

## 4. Migrations have no tests

Nothing exercises a migration against data.
Every test runs against a database already at head, so a migration that
corrupts existing rows passes the suite - which is exactly what happened with
the self-reference bug in `0004`, caught by eye rather than by CI.
A fixture that builds to revision N, plants data, upgrades and asserts would
have caught it.

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
- **`/health` is unauthenticated.**
  It is a liveness probe; requiring a token would defeat it.
- **`/api/v1/auth/authenticate` is unauthenticated by design.**
  It carries its own HTTP Basic layer instead, and a test asserts it stays
  reachable without a bearer token - otherwise no client could ever obtain
  one.
- **Write schemas reject unknown fields, response schemas do not.**
  The response models are validated from ORM objects rather than
  caller-supplied dicts, so forbidding extras there buys nothing.
