#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Add foreign keys to the CRM tables

  The CRM tables were created without them, so any bigint was accepted in a
  reference column and nothing noticed when it pointed at nothing.

  ON DELETE SET NULL throughout: deleting a user orphans the records they
  owned rather than destroying them, and deleting an account leaves its
  contacts intact but unlinked.  Every column below is already nullable, so
  nothing has to change to accommodate that.

  DEFERRABLE INITIALLY IMMEDIATE, because application_user and user_role
  reference each other: application_user.user_role_id points at user_role,
  and user_role.forecast_user_id points back.  Neither can be populated
  first while constraints are checked per statement.  Leaving them IMMEDIATE
  by default keeps the error on the offending statement during normal work;
  a bulk load that cannot honour the ordering issues SET CONSTRAINTS ALL
  DEFERRED inside its transaction, which is what scripts/seed.py does.

  Values that do not resolve are set to NULL before each constraint is
  created, so an existing database can be upgraded in place.  That discards
  data, but only data that was already meaningless - a reference to a row
  that is not there.  The sample data used 0 as a "none" sentinel, and 0 is
  never a valid identity value.  Without this step the migration succeeds on
  an empty database and fails on a populated one.

  Not every reference column can take a constraint, and the ones left alone
  are left alone deliberately:

    * polymorphic - the target table is chosen by a sibling discriminator:
      access.reference_id (reference_type), note.parent_id (parent_type),
      task.who_id (who_type), task.what_id (what_type), attachment.parent_id
    * wrong type - event.account_id and event.owner_id are varchar(18) on
      that table, and audit_log.user_id is varchar, so they cannot reference
      a bigint key
    * no target table exists - application_user.profile_id, and the opaque
      *_ref columns (account.record_type_ref, document.folder_ref,
      opportunity.campaign_ref, opportunity.pricebook_ref, and the
      Salesforce-style refs on event, lead and user_role)

  The definitions live here rather than in db/schema/create/*.sql because
  Postgres has no ADD CONSTRAINT IF NOT EXISTS: putting them in the create
  scripts as well would make a fresh build add each constraint twice, once
  in 0003 and again here.
"""
# -----------------------------------------------------------------------------

from typing import Sequence, Union

from alembic import op


# -----------------------------------------------------------------------------

revision:      str = '0004'
down_revision: str = '0003'

branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------

def upgrade() -> None:
    # Reconcile before constraining; see the note in the module docstring.
    op.execute(
        "UPDATE access SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = access.owner_id)"
    )
    op.execute(
        "UPDATE access SET user_id = NULL"
        " WHERE user_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = access.user_id)"
    )
    op.execute(
        "UPDATE account SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = account.owner_id)"
    )
    op.execute(
        "UPDATE attachment SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = attachment.owner_id)"
    )
    op.execute(
        "UPDATE contact SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = contact.owner_id)"
    )
    op.execute(
        "UPDATE document SET author_id = NULL"
        " WHERE author_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = document.author_id)"
    )
    op.execute(
        "UPDATE lead SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = lead.owner_id)"
    )
    op.execute(
        "UPDATE note SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = note.owner_id)"
    )
    op.execute(
        "UPDATE opportunity SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = opportunity.owner_id)"
    )
    op.execute(
        "UPDATE task SET owner_id = NULL"
        " WHERE owner_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = task.owner_id)"
    )
    op.execute(
        "UPDATE quote SET quoter_id = NULL"
        " WHERE quoter_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = quote.quoter_id)"
    )
    op.execute(
        "UPDATE user_role SET forecast_user_id = NULL"
        " WHERE forecast_user_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = user_role.forecast_user_id)"
    )
    op.execute(
        "UPDATE application_user SET delegated_approver_id = NULL"
        " WHERE delegated_approver_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM application_user WHERE application_user.id = application_user.delegated_approver_id)"
    )
    op.execute(
        "UPDATE account SET parent_id = NULL"
        " WHERE parent_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM account WHERE account.id = account.parent_id)"
    )
    op.execute(
        "UPDATE contact SET account_id = NULL"
        " WHERE account_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM account WHERE account.id = contact.account_id)"
    )
    op.execute(
        "UPDATE opportunity SET account_id = NULL"
        " WHERE account_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM account WHERE account.id = opportunity.account_id)"
    )
    op.execute(
        "UPDATE quote SET account_id = NULL"
        " WHERE account_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM account WHERE account.id = quote.account_id)"
    )
    op.execute(
        "UPDATE task SET account_id = NULL"
        " WHERE account_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM account WHERE account.id = task.account_id)"
    )
    op.execute(
        "UPDATE lead SET converted_account_id = NULL"
        " WHERE converted_account_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM account WHERE account.id = lead.converted_account_id)"
    )
    op.execute(
        "UPDATE contact SET reports_to_id = NULL"
        " WHERE reports_to_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM contact WHERE contact.id = contact.reports_to_id)"
    )
    op.execute(
        "UPDATE quote SET contact_id = NULL"
        " WHERE contact_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM contact WHERE contact.id = quote.contact_id)"
    )
    op.execute(
        "UPDATE lead SET converted_contact_id = NULL"
        " WHERE converted_contact_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM contact WHERE contact.id = lead.converted_contact_id)"
    )
    op.execute(
        "UPDATE lead SET converted_opportunity_id = NULL"
        " WHERE converted_opportunity_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM opportunity WHERE opportunity.id = lead.converted_opportunity_id)"
    )
    op.execute(
        "UPDATE user_role SET parent_role_id = NULL"
        " WHERE parent_role_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM user_role WHERE user_role.id = user_role.parent_role_id)"
    )
    op.execute(
        "UPDATE application_user SET user_role_id = NULL"
        " WHERE user_role_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM user_role WHERE user_role.id = application_user.user_role_id)"
    )

    op.create_foreign_key(
        "access_owner_id_fkey", "access", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "access_user_id_fkey", "access", "application_user",
        ["user_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "account_owner_id_fkey", "account", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "attachment_owner_id_fkey", "attachment", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "contact_owner_id_fkey", "contact", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "document_author_id_fkey", "document", "application_user",
        ["author_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "lead_owner_id_fkey", "lead", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "note_owner_id_fkey", "note", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "opportunity_owner_id_fkey", "opportunity", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "task_owner_id_fkey", "task", "application_user",
        ["owner_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "quote_quoter_id_fkey", "quote", "application_user",
        ["quoter_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "user_role_forecast_user_id_fkey", "user_role", "application_user",
        ["forecast_user_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "application_user_delegated_approver_id_fkey", "application_user", "application_user",
        ["delegated_approver_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "account_parent_id_fkey", "account", "account",
        ["parent_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "contact_account_id_fkey", "contact", "account",
        ["account_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "opportunity_account_id_fkey", "opportunity", "account",
        ["account_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "quote_account_id_fkey", "quote", "account",
        ["account_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "task_account_id_fkey", "task", "account",
        ["account_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "lead_converted_account_id_fkey", "lead", "account",
        ["converted_account_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "contact_reports_to_id_fkey", "contact", "contact",
        ["reports_to_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "quote_contact_id_fkey", "quote", "contact",
        ["contact_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "lead_converted_contact_id_fkey", "lead", "contact",
        ["converted_contact_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "lead_converted_opportunity_id_fkey", "lead", "opportunity",
        ["converted_opportunity_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "user_role_parent_role_id_fkey", "user_role", "user_role",
        ["parent_role_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )
    op.create_foreign_key(
        "application_user_user_role_id_fkey", "application_user", "user_role",
        ["user_role_id"], ["id"], ondelete="SET NULL",
        deferrable=True, initially="IMMEDIATE",
    )


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.drop_constraint("application_user_user_role_id_fkey", "application_user", type_="foreignkey")
    op.drop_constraint("user_role_parent_role_id_fkey", "user_role", type_="foreignkey")
    op.drop_constraint("lead_converted_opportunity_id_fkey", "lead", type_="foreignkey")
    op.drop_constraint("lead_converted_contact_id_fkey", "lead", type_="foreignkey")
    op.drop_constraint("quote_contact_id_fkey", "quote", type_="foreignkey")
    op.drop_constraint("contact_reports_to_id_fkey", "contact", type_="foreignkey")
    op.drop_constraint("lead_converted_account_id_fkey", "lead", type_="foreignkey")
    op.drop_constraint("task_account_id_fkey", "task", type_="foreignkey")
    op.drop_constraint("quote_account_id_fkey", "quote", type_="foreignkey")
    op.drop_constraint("opportunity_account_id_fkey", "opportunity", type_="foreignkey")
    op.drop_constraint("contact_account_id_fkey", "contact", type_="foreignkey")
    op.drop_constraint("account_parent_id_fkey", "account", type_="foreignkey")
    op.drop_constraint("application_user_delegated_approver_id_fkey", "application_user", type_="foreignkey")
    op.drop_constraint("user_role_forecast_user_id_fkey", "user_role", type_="foreignkey")
    op.drop_constraint("quote_quoter_id_fkey", "quote", type_="foreignkey")
    op.drop_constraint("task_owner_id_fkey", "task", type_="foreignkey")
    op.drop_constraint("opportunity_owner_id_fkey", "opportunity", type_="foreignkey")
    op.drop_constraint("note_owner_id_fkey", "note", type_="foreignkey")
    op.drop_constraint("lead_owner_id_fkey", "lead", type_="foreignkey")
    op.drop_constraint("document_author_id_fkey", "document", type_="foreignkey")
    op.drop_constraint("contact_owner_id_fkey", "contact", type_="foreignkey")
    op.drop_constraint("attachment_owner_id_fkey", "attachment", type_="foreignkey")
    op.drop_constraint("account_owner_id_fkey", "account", type_="foreignkey")
    op.drop_constraint("access_user_id_fkey", "access", type_="foreignkey")
    op.drop_constraint("access_owner_id_fkey", "access", type_="foreignkey")


# -----------------------------------------------------------------------------
