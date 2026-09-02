import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.schemas import Role, User
from backend.app.services.audit_service import AuditService


RECOGNIZED_ROLES = frozenset(("Admin", "Approver", "Clerk", "Viewer"))


class IdentityDisabledError(PermissionError):
    pass


class IdentitySyncService:
    @classmethod
    def sync(cls, db: Session, claims: dict) -> User:
        tenant_id, entra_oid = claims["tid"], claims["oid"]
        user = db.query(User).filter_by(tenant_id=tenant_id, entra_oid=entra_oid).one_or_none()
        if user is None:
            user = User(id=uuid.uuid4(), tenant_id=tenant_id, entra_oid=entra_oid,
                        email=claims.get("preferred_username"))
            db.add(user)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                user = db.query(User).filter_by(tenant_id=tenant_id, entra_oid=entra_oid).one_or_none()
                if user is None:
                    raise
        return cls._project(db, user, claims)

    @staticmethod
    def _project(db: Session, user: User, claims: dict) -> User:
        if user.is_disabled:
            raise IdentityDisabledError("Identity is disabled")

        role_names = set(claims.get("roles", ())) & RECOGNIZED_ROLES
        user.email = claims.get("preferred_username")
        user.full_name = claims.get("name")
        user.roles = db.query(Role).filter(Role.name.in_(role_names)).order_by(Role.name).all()
        user.last_synced_at = datetime.now(timezone.utc)
        AuditService.log_action(
            db, user.id, "IDENTITY_SYNCED", "User", user.id, commit=False
        )
        db.commit()
        db.refresh(user)
        return user
