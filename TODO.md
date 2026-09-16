# TODO

Outstanding work on base-api, roughly in the order it is worth doing.
Current release: v0.7.1.

## 1. Endpoints for `user_role`

The last CRM table without them, and it already has seed data and a model.
Follows the pattern in `app/api/v1/endpoints/` - a `Base`/`Create`/`Update`/
response quartet in `schemas.py`, an endpoint module, a line in `router.py`.

## 2. Authentication

`api_credentials`, `login_session` and `token_blacklist` are modelled,
migrated and seeded, and **nothing uses them**.
Every endpoint is open.

This is the largest remaining gap and the one that decides the shape of
several others: whether `audit_log` records who did something, whether
`created_by_id` and `updated_by_id` can be populated at all, and whether the
infrastructure tables should ever get plain CRUD endpoints.

## 3. Nothing writes `audit_log`

The table exists, has a model and is migrated, but no code path records to
it.
It wants `application`, `reference_type`, `reference_id`, `event`,
`description` and `user_id` on each mutation - which needs item 2 first, or
`user_id` is always unknown.

## 4. `instance_metadata` is never populated

The table carries release and version check constraints and a singleton
index, but holds no row, so nothing records which schema version a database
is at beyond `alembic_version`.
Either a migration stamps it, or drop the table.

## 5. `created_by_id` / `updated_by_id` are never set

Every table carries them and every row has them NULL, because the API has no
concept of a current user.
Blocked on item 2.

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
- **Write schemas reject unknown fields, response schemas do not.**
  The response models are validated from ORM objects rather than
  caller-supplied dicts, so forbidding extras there buys nothing.
