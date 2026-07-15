from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
from jose.utils import base64url_decode
import requests
from backend.app.core.config import settings

# DEV MODE: Allow empty Authorization header when Azure is not configured
class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        if not settings.ENTRA_ID_JWKS_URL:
            return None
        return await super().__call__(request)

security = OptionalHTTPBearer()

class SecurityService:
    def __init__(self):
        self._jwks_cache = None

    def _get_jwks(self):
        if self._jwks_cache is None:
            response = requests.get(settings.ENTRA_ID_JWKS_URL)
            response.raise_for_status()
            self._jwks_cache = response.json().get("keys", [])
        return self._jwks_cache

    def validate_token(self, token: str):
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            jwks = self._get_jwks()
            key_data = next((k for k in jwks if k["kid"] == kid), None)
            
            if not key_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: Key ID not found in JWKS"
                )
            
            # Construct public key
            pub_key = jwk.construct(key_data)
            
            # Validate token
            payload = jwt.decode(
                token,
                pub_key.to_pem(),
                algorithms=["RS256"],
                audience=settings.ENTRA_ID_CLIENT_ID,
                issuer=f"https://sts.windows.net/{settings.ENTRA_ID_TENANT_ID}/"
            )
            return payload
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

# Mock user for local development when Azure is not configured
DEV_USER = {
    "sub": "dev-user-001",
    "email": "dev@facturascontrol.local",
    "name": "Dev User",
    "roles": ["Admin"],
    "preferred_username": "dev@facturascontrol.local"
}

security_service = SecurityService()

async def get_current_user(cred: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    # DEVELOPMENT MODE: Bypass Azure validation when not configured
    if not settings.ENTRA_ID_JWKS_URL:
        return DEV_USER
    
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token = cred.credentials
    return security_service.validate_token(token)


class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: dict = Depends(get_current_user)):
        # DEVELOPMENT MODE: Skip role check when Azure is not configured
        if not settings.ENTRA_ID_JWKS_URL:
            return user
        
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user

