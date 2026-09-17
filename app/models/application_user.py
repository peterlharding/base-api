#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy model for the application_user table.

Mirrors db/schema/create/application_user.sql, installed by migration 0001.
Server defaults are declared so `alembic revision --autogenerate` reports no
diff, and so a create returns the database's own values untouched.
"""
# -----------------------------------------------------------------------------

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.hybrid import (
    hybrid_property,
    hybrid_method
)


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class ApplicationUser(Base):
    """Mirrors the application_user table (see db/schema/create/application_user.sql)."""

    __tablename__ = "application_user"
    __table_args__ = (
        # one per foreign key: Postgres indexes the parent side only,
        # so without these a parent delete scans this table
        Index("application_user_delegated_approver_id_idx", "delegated_approver_id"),
        Index("application_user_user_role_id_idx", "user_role_id"),
    )

    id:                           Mapped[int]         = mapped_column(
        BigInteger, primary_key=True
    )

    guid:                         Mapped[UUID | None] = mapped_column(Uuid)

    username:                     Mapped[str | None]  = mapped_column(String(32))
    hashed_password:              Mapped[str | None]  = mapped_column(String(255))
    alias:                        Mapped[str | None]  = mapped_column(String(32))

    first_name:                   Mapped[str | None]  = mapped_column(String(32))
    last_name:                    Mapped[str | None]  = mapped_column(String(32))

    company_name:                 Mapped[str | None]  = mapped_column(String(100))
    division:                     Mapped[str | None]  = mapped_column(String(32))
    department:                   Mapped[str | None]  = mapped_column(String(100))
    title:                        Mapped[str | None]  = mapped_column(String(100))

    street:                       Mapped[str | None]  = mapped_column(String(100))
    city:                         Mapped[str | None]  = mapped_column(String(50))
    state:                        Mapped[str | None]  = mapped_column(String(32))
    postal_code:                  Mapped[str | None]  = mapped_column(String(20))
    country:                      Mapped[str | None]  = mapped_column(String(100))

    email:                        Mapped[str | None]  = mapped_column(String(255), unique=True)
    phone:                        Mapped[str | None]  = mapped_column(String(20))
    phone_extension:              Mapped[str | None]  = mapped_column(String(10))
    fax:                          Mapped[str | None]  = mapped_column(String(20))
    mobile_phone:                 Mapped[str | None]  = mapped_column(String(20))

    is_active:                    Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("true")
    )

    user_role_id:                 Mapped[int | None]  = mapped_column(BigInteger, ForeignKey("user_role.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    user_type:                    Mapped[str | None]  = mapped_column(
        String(20), server_default=text("'Standard'")
    )

    profile_id:                   Mapped[int | None]  = mapped_column(BigInteger)

    timezone_sid_key:             Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'Australia/Melbourne'")
    )

    locale_sid_key:               Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'en_AU'")
    )

    language_locale_key:          Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'en_US'")
    )

    receives_info_emails:         Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("false")
    )

    receives_admin_info_emails:   Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("false")
    )

    email_encoding_key:           Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'ISO-8859-1'")
    )

    employee_number:              Mapped[str | None]  = mapped_column(String(50))
    delegated_approver_id:        Mapped[int | None]  = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    start_day:                    Mapped[int | None]  = mapped_column(
        Integer, server_default=text("6")
    )

    end_day:                      Mapped[int | None]  = mapped_column(
        Integer, server_default=text("23")
    )

    last_login_date:              Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Set by POST /api/v1/auth/revoke-all; NULL until it is used.
    tokens_revoked_before:        Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # created_at / updated_at are server-maintained: updated_at is advanced by
    # the application_user_set_updated_at trigger, never written by the app.
    created_at:                   Mapped[datetime]    = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    created_by_id:                Mapped[int | None]  = mapped_column(BigInteger)

    updated_at:                   Mapped[datetime]    = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    updated_by_id:                Mapped[int | None]  = mapped_column(BigInteger)

    hash                                = '0052'

    # -------------------------------------------------------------------------

    def is_correct_password(self, password: str) -> bool:
        """Check a plaintext password against the stored bcrypt digest."""
        from app.auth.password import verify_password

        return verify_password(password, self.hashed_password)


    # -------------------------------------------------------------------------
    # Wholesale revocation.
    #
    # A blacklist cannot do this job.  It is keyed on jti, and the only place
    # a jti is recorded is the blacklist itself, so there is no list of a
    # user's outstanding tokens to walk - login_session stores a hash of the
    # token, not its id, and a token obtained from refresh creates no session
    # row at all.  A cutoff compares against a claim the token carries, so it
    # covers every token ever issued to this user without having to have seen
    # any of them.

    def revoke_tokens(self, *, now=None):
        """Revoke every token issued to this user.  Returns the cutoff.

        Including the one the caller is holding: revoke-all means all, and a
        carve-out for the current device would be a second rule to get wrong.
        """
        from datetime import datetime, timezone

        self.tokens_revoked_before = now or datetime.now(timezone.utc)

        return self.tokens_revoked_before


    # -------------------------------------------------------------------------

    def rejects_token_issued_at(self, issued_at: float | int | None) -> bool:
        """True if a token with this ``iat`` falls before the revocation cutoff.

        ``iat`` is seconds since the epoch, fractional since v0.15.0.  An
        integer one predates that release and truncates towards the past, so
        it can only make a token look older than it was - which errs towards
        revoking, never away from it.

        A token carrying no ``iat`` is rejected once a cutoff exists, because
        there is then no way to place it relative to one.  Nothing this API
        issues is in that position.
        """
        from datetime import datetime, timezone

        if self.tokens_revoked_before is None:
            return False

        if issued_at is None:
            return True

        return datetime.fromtimestamp(issued_at, tz=timezone.utc) < self.tokens_revoked_before


    # -------------------------------------------------------------------------
    # Computed display names. NULL-safe Python implementations; no
    # `.expression` overrides yet because we only use these in
    # templates, not in WHERE clauses. Add a SQL expression if/when
    # we need to filter or order by them at the DB.

    @hybrid_property
    def first_last_name(self) -> str:
        """First Last - the natural human display."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @hybrid_property
    def last_first_name(self) -> str:
        """Last, First - the sortable display (related lists, headers)."""
        if self.first_name and self.last_name:
            return f"{self.last_name}, {self.first_name}"
        return self.last_name or self.first_name or ''

    # -------------------------------------------------------------------------

    def __str__(self):
        return '<User: %r <%s>>' % (self.id, self.guid)

    # -------------------------------------------------------------------------

    def __repr__(self):
        return f"""<User:
           id: {self.id}
         guid: {self.guid}
     username: {self.username}
   first_name: {self.first_name}
    last_name: {self.last_name}
 company_name: {self.company_name}
"""

    # -------------------------------------------------------------------------

    def jsonify(self):

         if self.last_login:
              last_login = self.last_login_date.strftime('%Y-%m-%d %H:%M:%S')
         else:
              last_login = "Never"

         if self.when_modified:
              updated_at = self.update_at.strftime('%Y-%m-%d %H:%M:%S')
         else:
              updated_at = "Never"

         return {
                    'id'             : self.id,
                    'guid'           : self.guid,
                    'username'       : self.username,
                    'hashedPassword' : self.hashed_password,
                    'email'          : self.email,
                    'firstName'      : self.first_name,
                    'lastName'       : self.last_name,
                    'companyName'    : self.company_name,
                    'isAdmin'        : self.is_admin,
                    'isActive'       : self.is_active,
                    'role'           : self.role,
                    'notes'          : self.notes,
                    'lastLogin'      : last_login,
                    'createdAt'      : self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updatedAt'      : updated_at,
                }


    # -------------------------------------------------------------------------


# =============================================================================
