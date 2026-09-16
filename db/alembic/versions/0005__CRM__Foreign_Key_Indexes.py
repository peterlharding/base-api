#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Index the foreign key columns added in 0004

  Postgres indexes the parent side of a foreign key, because it needs a
  unique constraint there, but it creates nothing on the child side.  Every
  DELETE or key UPDATE on a parent therefore scans each referencing table to
  find the rows it has to set to NULL.  With twenty-five constraints that is
  twenty-five sequential scans per parent delete.

  One index per constrained column, named to the convention already used by
  login_session and token_blacklist: <table>_<column>_idx.

  Built inside the migration transaction rather than CONCURRENTLY.  These
  tables are small, so the exclusive lock is momentary, and a transactional
  build is atomic - a failure leaves nothing behind.  CREATE INDEX
  CONCURRENTLY cannot run inside a transaction and can leave an invalid
  index if it fails, so it is the right choice only once these tables are
  large enough that the write lock matters.  They are not yet.
"""
# -----------------------------------------------------------------------------

from typing import Sequence, Union

from alembic import op


# -----------------------------------------------------------------------------

revision:      str = '0005'
down_revision: str = '0004'

branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------

def upgrade() -> None:
    op.create_index("access_owner_id_idx", "access", ["owner_id"])
    op.create_index("access_user_id_idx", "access", ["user_id"])
    op.create_index("account_owner_id_idx", "account", ["owner_id"])
    op.create_index("account_parent_id_idx", "account", ["parent_id"])
    op.create_index("application_user_delegated_approver_id_idx", "application_user", ["delegated_approver_id"])
    op.create_index("application_user_user_role_id_idx", "application_user", ["user_role_id"])
    op.create_index("attachment_owner_id_idx", "attachment", ["owner_id"])
    op.create_index("contact_owner_id_idx", "contact", ["owner_id"])
    op.create_index("contact_account_id_idx", "contact", ["account_id"])
    op.create_index("contact_reports_to_id_idx", "contact", ["reports_to_id"])
    op.create_index("document_author_id_idx", "document", ["author_id"])
    op.create_index("lead_owner_id_idx", "lead", ["owner_id"])
    op.create_index("lead_converted_account_id_idx", "lead", ["converted_account_id"])
    op.create_index("lead_converted_contact_id_idx", "lead", ["converted_contact_id"])
    op.create_index("lead_converted_opportunity_id_idx", "lead", ["converted_opportunity_id"])
    op.create_index("note_owner_id_idx", "note", ["owner_id"])
    op.create_index("opportunity_owner_id_idx", "opportunity", ["owner_id"])
    op.create_index("opportunity_account_id_idx", "opportunity", ["account_id"])
    op.create_index("quote_quoter_id_idx", "quote", ["quoter_id"])
    op.create_index("quote_account_id_idx", "quote", ["account_id"])
    op.create_index("quote_contact_id_idx", "quote", ["contact_id"])
    op.create_index("task_owner_id_idx", "task", ["owner_id"])
    op.create_index("task_account_id_idx", "task", ["account_id"])
    op.create_index("user_role_forecast_user_id_idx", "user_role", ["forecast_user_id"])
    op.create_index("user_role_parent_role_id_idx", "user_role", ["parent_role_id"])


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.drop_index("user_role_parent_role_id_idx", table_name="user_role")
    op.drop_index("user_role_forecast_user_id_idx", table_name="user_role")
    op.drop_index("task_account_id_idx", table_name="task")
    op.drop_index("task_owner_id_idx", table_name="task")
    op.drop_index("quote_contact_id_idx", table_name="quote")
    op.drop_index("quote_account_id_idx", table_name="quote")
    op.drop_index("quote_quoter_id_idx", table_name="quote")
    op.drop_index("opportunity_account_id_idx", table_name="opportunity")
    op.drop_index("opportunity_owner_id_idx", table_name="opportunity")
    op.drop_index("note_owner_id_idx", table_name="note")
    op.drop_index("lead_converted_opportunity_id_idx", table_name="lead")
    op.drop_index("lead_converted_contact_id_idx", table_name="lead")
    op.drop_index("lead_converted_account_id_idx", table_name="lead")
    op.drop_index("lead_owner_id_idx", table_name="lead")
    op.drop_index("document_author_id_idx", table_name="document")
    op.drop_index("contact_reports_to_id_idx", table_name="contact")
    op.drop_index("contact_account_id_idx", table_name="contact")
    op.drop_index("contact_owner_id_idx", table_name="contact")
    op.drop_index("attachment_owner_id_idx", table_name="attachment")
    op.drop_index("application_user_user_role_id_idx", table_name="application_user")
    op.drop_index("application_user_delegated_approver_id_idx", table_name="application_user")
    op.drop_index("account_parent_id_idx", table_name="account")
    op.drop_index("account_owner_id_idx", table_name="account")
    op.drop_index("access_user_id_idx", table_name="access")
    op.drop_index("access_owner_id_idx", table_name="access")


# -----------------------------------------------------------------------------
