from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from backend.app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

class UserResponse(BaseModel):
    email: str
    fullName: str
    roles: List[str]

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the profile of the currently authenticated user.
    In dev mode, returns a mock Admin user.
    """
    return UserResponse(
        email=current_user.get("email", "dev@facturascontrol.local"),
        fullName=current_user.get("name", "Dev User"),
        roles=current_user.get("roles", ["Admin"]),
    )
