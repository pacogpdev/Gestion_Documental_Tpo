import logging
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.authorization import AuthorizationPolicy
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.services.audit_service import AuditService
from backend.app.services.identity_sync_service import IdentityDisabledError, IdentitySyncService

authorization_policy = AuthorizationPolicy()
logger = logging.getLogger(__name__)


def _emit_authorization_outcome(db, user_id, outcome, reason, correlation_id) -> None:
    audit = AuditService.log_action(db, user_id, "AUTHORIZATION_OUTCOME", "User", user_id)
    logger.info(
        "authorization.outcome",
        extra={"outcome": outcome, "reason": reason, "correlation_id": correlation_id,
               "local_audit_id": str(audit.id)},
    )


def get_authorized_user(
    claims: dict = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    if settings.is_local_development:
        return claims
    correlation_id = uuid.uuid4().hex
    try:
        user = IdentitySyncService.sync(db, claims)
    except IdentityDisabledError as error:
        _emit_authorization_outcome(
            db, error.user_id, "denied", "identity_disabled", correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        ) from error
    return {
        "email": user.email,
        "name": user.full_name,
        "roles": sorted(role.name for role in user.roles),
        "_authorization_user_id": user.id,
        "_correlation_id": correlation_id,
    }


def require_operation(operation: str):
    def check(
        current_user: dict = Depends(get_authorized_user), db: Session = Depends(get_db)
    ) -> dict:
        try:
            authorization_policy.authorize(operation, current_user.get("roles", []))
        except HTTPException:
            if "_authorization_user_id" in current_user:
                _emit_authorization_outcome(
                    db=db,
                    user_id=current_user["_authorization_user_id"],
                    outcome="denied", reason="operation_denied",
                    correlation_id=current_user["_correlation_id"],
                )
            raise
        if "_authorization_user_id" in current_user:
            _emit_authorization_outcome(
                db=db, user_id=current_user["_authorization_user_id"],
                outcome="authorized", reason="operation_allowed",
                correlation_id=current_user["_correlation_id"],
            )
        return current_user

    return check
