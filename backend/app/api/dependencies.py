from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.authorization import AuthorizationPolicy
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.services.identity_sync_service import IdentityDisabledError, IdentitySyncService

authorization_policy = AuthorizationPolicy()


def get_authorized_user(
    claims: dict = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    if settings.is_local_development:
        return claims
    try:
        user = IdentitySyncService.sync(db, claims)
    except IdentityDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        ) from error
    return {
        "email": user.email,
        "name": user.full_name,
        "roles": sorted(role.name for role in user.roles),
    }


def require_operation(operation: str):
    def check(current_user: dict = Depends(get_authorized_user)) -> dict:
        authorization_policy.authorize(operation, current_user.get("roles", []))
        return current_user

    return check
