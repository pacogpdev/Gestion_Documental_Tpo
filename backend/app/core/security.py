from time import monotonic
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
import requests
from backend.app.core.config import settings

JWKS_CACHE_TTL_SECONDS = 300
JWKS_REQUEST_TIMEOUT_SECONDS = 5


def _has_scope(payload: dict, scope: str) -> bool:
    return scope in payload.get("scp", "").split()


def _find_key(jwks: list[dict], kid: str | None) -> dict | None:
    return next((key for key in jwks if key.get("kid") == kid), None)


class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        if settings.is_local_development:
            return None
        return await super().__call__(request)

security = OptionalHTTPBearer()

class SecurityService:
    def __init__(self):
        self._jwks_cache = None
        self._jwks_cached_at = 0.0

    def _get_jwks(self, refresh: bool = False):
        if refresh or self._jwks_cache is None or monotonic() - self._jwks_cached_at >= JWKS_CACHE_TTL_SECONDS:
            try:
                response = requests.get(settings.ENTRA_ID_JWKS_URL, timeout=JWKS_REQUEST_TIMEOUT_SECONDS)
                response.raise_for_status()
                keys = response.json().get("keys", [])
            except (requests.RequestException, ValueError, AttributeError) as error:
                raise _JwksUnavailable() from error
            if not isinstance(keys, list):
                raise _JwksUnavailable()
            self._jwks_cache = keys
            self._jwks_cached_at = monotonic()
        return self._jwks_cache

    def validate_token(self, token: str):
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            jwks = self._get_jwks()
            key_data = _find_key(jwks, kid)
            
            if not key_data:
                jwks = self._get_jwks(refresh=True)
                key_data = _find_key(jwks, kid)
            if not key_data:
                raise ValueError("Unknown signing key")
            
            pub_key = jwk.construct(key_data, algorithm="RS256")
            payload = jwt.decode(
                token,
                pub_key.to_pem(),
                algorithms=["RS256"],
                audience=settings.ENTRA_ID_API_AUDIENCE,
                issuer=settings.ENTRA_ID_ISSUER,
            )
            scope = settings.ENTRA_ID_API_SCOPE.rsplit("/", 1)[-1]
            if payload.get("tid") != settings.ENTRA_ID_TENANT_ID or not _has_scope(payload, scope):
                raise ValueError("Token is not an API access token")
            return payload
        except _JwksUnavailable as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Identity provider unavailable"
            ) from error
        except HTTPException:
            raise
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            ) from error


class _JwksUnavailable(Exception):
    pass

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
    if settings.is_local_development:
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
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user

