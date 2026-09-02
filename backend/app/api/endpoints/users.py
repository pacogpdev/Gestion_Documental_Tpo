from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.api.dependencies import require_operation
from backend.app.core.authorization import AuthorizationPolicy

router = APIRouter(prefix="/users", tags=["users"])

class UserResponse(BaseModel):
    email: str | None
    fullName: str | None
    roles: list[str]
    permissions: list[str]

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: dict = Depends(require_operation("read"))
):
    """
    Returns the profile of the currently authenticated user.
    In dev mode, returns a mock Admin user.
    """
    return UserResponse(
        email=current_user.get("email"),
        fullName=current_user.get("name"),
        roles=current_user.get("roles", []),
        permissions=sorted(AuthorizationPolicy().permissions_for(current_user.get("roles", []))),
    )
