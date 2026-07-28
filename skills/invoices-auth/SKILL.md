---
name: invoices-auth
description: >
  Authentication and authorization patterns for the invoices app.
  Azure Entra ID JWT validation, dev-mode bypass, RoleChecker,
  frontend useAuth hook, Axios JWT interceptor, role matrix.
  Trigger: When editing backend/app/core/security.py, frontend/src/hooks/useAuth.ts,
  frontend/src/api/client.ts, adding auth or role checks, modifying JWT validation,
  or changing the role/permission system.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Editing `backend/app/core/security.py` — JWT validation, RoleChecker, dev user
- Editing `frontend/src/hooks/useAuth.ts` — auth state management
- Editing `frontend/src/api/client.ts` — Axios JWT interceptor
- Editing `backend/app/api/endpoints/users.py` — `/users/me` endpoint
- Adding role-based access to a new endpoint or page
- Modifying the JWT validation flow or dev mode bypass

## Critical Patterns

### Two modes: Development vs. Production

The auth system has **two modes** determined by whether `ENTRA_ID_JWKS_URL` is configured in `.env`:

| Mode | Trigger | Auth behavior |
|---|---|---|
| **Development** | `ENTRA_ID_JWKS_URL` is empty | No login required. Returns a hardcoded `DEV_USER` with Admin role. |
| **Production** | `ENTRA_ID_JWKS_URL` is set | Validates JWT from Azure Entra ID, extracts roles from `roles` claim. |

### Backend: OptionalHTTPBearer

Allows requests without an `Authorization` header when in dev mode:

```python
class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        if not settings.ENTRA_ID_JWKS_URL:
            return None  # ← dev mode: no credential needed
        return await super().__call__(request)

security = OptionalHTTPBearer()
```

### Backend: DEV_USER (development fallback)

```python
DEV_USER = {
    "sub": "dev-user-001",
    "email": "dev@facturascontrol.local",
    "name": "Dev User",
    "roles": ["Admin"],
    "preferred_username": "dev@facturascontrol.local"
}
```

### Backend: get_current_user

Returns either the dev user (no Azure configured) or the validated JWT payload:

```python
async def get_current_user(cred: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not settings.ENTRA_ID_JWKS_URL:
        return DEV_USER        # ← dev mode shortcut

    if cred is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = cred.credentials
    return security_service.validate_token(token)
```

### Backend: SecurityService.validate_token

Full JWT validation against Azure Entra ID JWKS:

```python
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
                raise HTTPException(status_code=401, detail="Invalid token: Key ID not found in JWKS")

            pub_key = jwk.construct(key_data)
            payload = jwt.decode(
                token,
                pub_key.to_pem(),
                algorithms=["RS256"],
                audience=settings.ENTRA_ID_CLIENT_ID,
                issuer=f"https://sts.windows.net/{settings.ENTRA_ID_TENANT_ID}/"
            )
            return payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
```

- JWKS is cached in memory (`_jwks_cache`) for the lifetime of the process
- Validates: signature (RS256), audience (client ID), issuer (tenant)

### Backend: RoleChecker

Dependency that enforces role-based access:

```python
class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: dict = Depends(get_current_user)):
        # Dev mode: skip role check entirely
        if not settings.ENTRA_ID_JWKS_URL:
            return user

        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
```

**Usage in endpoints**: always as the last dependency with `_` name (side-effect only):

```python
@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Clerk", "Admin"]))
):
```

### Role matrix

| Role | Upload | Approve/Reject | Delete | List | View Suppliers | Create Supplier |
|---|---|---|---|---|---|---|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Approver** | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| **Clerk** | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Viewer** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |

**Backend enforcement:**

| Endpoint | Allowed roles |
|---|---|
| `POST /invoices/upload` | Clerk, Admin |
| `DELETE /invoices/{id}` | Clerk, Admin |
| `PATCH /invoices/{id}/approve` | Approver, Admin |
| `GET /invoices` | All authenticated users |
| `GET /suppliers` | All authenticated users |
| `POST /suppliers` | Admin (no explicit RoleChecker — uses `get_current_user` only) |
| `GET /users/me` | All authenticated users |

### Frontend: useAuth hook

```typescript
import { useState } from 'react';

export type UserRole = 'Admin' | 'Approver' | 'Viewer';

interface User {
  email: string;
  fullName: string;
  roles: UserRole[];
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(
    () => {
      try {
        const stored = localStorage.getItem('user_profile');
        return stored ? JSON.parse(stored) : null;
      } catch { return null; }
    }
  );
  const [loading] = useState(false);

  const login = (userData: User, token: string) => {
    localStorage.setItem('user_profile', JSON.stringify(userData));
    localStorage.setItem('auth_token', token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('user_profile');
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  const hasRole = (role: UserRole) => user?.roles.includes(role) || false;

  return { user, loading, login, logout, hasRole };
};
```

- State is **hydrated from localStorage** on mount (persists across refreshes)
- `login()` saves both user profile and JWT token to localStorage
- `logout()` clears both
- `hasRole(role)` is a safe check — returns `false` when no user is logged in

### Frontend: API client JWT interceptor

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

- No default `Content-Type` — Axios auto-detects: JSON for objects, `multipart/form-data` for FormData
- Interceptor reads `auth_token` from localStorage on every request
- In dev mode the backend ignores the Authorization header anyway

### Frontend: Navbar auto-fetch

The `Navbar` calls `GET /users/me` on mount to auto-login in dev mode:

```typescript
useEffect(() => {
  if (!localStorage.getItem('user_profile')) {
    apiClient.get('/users/me')
      .then(res => login(res.data, 'dev-token'))
      .catch(err => console.warn('Could not fetch user profile', err));
  }
}, []);
```

- Only fetches if no user is already in localStorage (avoids redundant calls)
- Uses `'dev-token'` as a placeholder token — never validated in dev mode
- In production, the token would come from the Azure Entra ID login flow

### Frontend: Role-based rendering

```tsx
const { hasRole } = useAuth();

{hasRole('Admin') && <button>Add Supplier</button>}
{(hasRole('Approver') || hasRole('Admin')) && <Link to="/upload">Upload Invoice</Link>}
```

**Pages and their role access:**

| Page/Route | Access |
|---|---|
| `/dashboard` | All authenticated users |
| `/upload` | Admin, Approver |
| `/suppliers` | Admin |

### Frontend: Users/me endpoint

```python
class UserResponse(BaseModel):
    email: str
    fullName: str
    roles: List[str]

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        email=current_user.get("email", "dev@facturascontrol.local"),
        fullName=current_user.get("name", "Dev User"),
        roles=current_user.get("roles", ["Admin"]),
    )
```

Maps the JWT/dev-user dict to a camelCase `UserResponse`.

### Testing auth in frontend tests

Inject auth state via the `<AuthProvider>` in `test-utils.tsx`:

```tsx
// Admin
render(<Component />, {
  user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
  token: 'fake-jwt-token',
});

// Viewer (restricted)
render(<Component />, {
  user: { email: 'viewer@test.com', fullName: 'Viewer User', roles: ['Viewer'] },
  token: 'fake-jwt-token',
});

// Unauthenticated
render(<Component />);
```

## Structural Context (CodeGraph)

> Derived from the CodeGraph index (653 nodes, 1,321 edges). Use for impact analysis before edits.

### Hub symbols in this area
| Symbol | Location | Callers | Tests | Note |
|--------|----------|---------|-------|------|
| `get_current_user` | security.py:72 | 6 (invoices, suppliers, users) | test_supplier_stats.py, conftest.py ✅ | #1 backend auth hub — every protected endpoint |
| `RoleChecker` | security.py:87 | 2 (invoices, suppliers) | ⚠️ no direct test | #2 backend auth hub — RBAC guard |
| `SecurityService.validate_token` | security.py:29 | 1 (get_current_user) | indirect | JWT validation with JWKS key rotation |
| `OptionalHTTPBearer` | security.py:10 | 1 (security dep) | indirect | Dev-mode bypass when ENTRA_ID_JWKS_URL empty |
| `useAuth` | useAuth.ts:20 | 9 (Navbar, SupplierDashboard, Suppliers, UploadInvoice) | useAuth.test.ts ✅ | #1 frontend auth hub |
| `User` (frontend) | useAuth.ts:5 | 1 (useAuth) | ⚠️ no direct test | Interface only |

### Call paths through this area
```
[Backend — prod mode]
HTTP request → OptionalHTTPBearer → get_current_user (security.py:72)
  → SecurityService.validate_token (security.py:29)
    → _get_jwks (cached JWKS from Microsoft)
    → jwt.decode(token, pub_key, audience, issuer)
  → returns payload (with roles)
→ RoleChecker.__call__ (security.py:91)
  → checks user.roles ∩ allowed_roles
  → 403 if no match

[Backend — dev mode]
HTTP request → OptionalHTTPBearer (returns None) → get_current_user
  → ENTRA_ID_JWKS_URL empty → returns DEV_USER (Admin role)
→ RoleChecker.__call__ → ENTRA_ID_JWKS_URL empty → returns user (skips check)

[Frontend — dev mode bootstrap]
Navbar mount → apiClient.get('/users/me')
  → users.py:get_current_user_profile
  → login(profile, 'dev-token') → localStorage.setItem
```

### Per-symbol test coverage
- `get_current_user`: `backend/tests/api/test_supplier_stats.py` + `backend/tests/conftest.py` ✅
- `RoleChecker`: ⚠️ no direct test — only exercised transitively via endpoint tests. Adding a direct test is a recommended next step.
- `useAuth` (frontend): `frontend/src/hooks/useAuth.test.ts` ✅
- `User` (frontend interface): no direct test (interface only)
- `SecurityService.validate_token`: no direct test (requires Azure mocking)
- `OptionalHTTPBearer`: no direct test

### Cross-layer dependencies
- **⚠️ Role drift (flagged by CodeGraph):** Backend `RoleChecker` allows `["Clerk", "Admin"]` on `POST /upload` and `DELETE /invoices/{id}`. Frontend `UserRole` type (useAuth.ts:3) = `'Admin' | 'Approver' | 'Viewer'` — **omits 'Clerk'**. A Clerk user authenticated via Entra ID would not see Upload/Suppliers nav links in the frontend, even though the backend authorizes them. This is a type-consistency gap, not a security hole (backend still enforces). Fix: add `'Clerk'` to the frontend `UserRole` union type.
- **`DEV_USER["roles"]`** = `["Admin"]` (security.py:66) — in dev mode, all role-gated features are visible. This is intentional but means dev mode cannot test Clerk-only or Viewer-only UI.
- **Auth state propagation:** `Navbar` auto-fetches `/users/me` on mount → populates `useAuth` → all 9 callers read `hasRole()`. If Navbar is not rendered (e.g., test renders a page in isolation), `useAuth` returns null and `hasRole()` returns false. The `test-utils.tsx` wrapper handles this by injecting a mock user.
- **JWT interceptor** (client.ts) attaches `Authorization: Bearer <token>` from localStorage. In dev mode, token is `'dev-token'` (set by Navbar). Backend `OptionalHTTPBearer` returns None, so the token is never validated — dev bypass.

## File Structure

```
backend/app/core/
└── security.py              # JWT validation, OptionalHTTPBearer, RoleChecker, DEV_USER

backend/app/api/endpoints/
└── users.py                 # GET /users/me — user profile endpoint

frontend/src/
├── hooks/
│   └── useAuth.ts           # Auth state, login, logout, hasRole
├── api/
│   └── client.ts            # Axios instance with JWT interceptor
├── components/
│   └── Navbar.tsx           # Auto-fetch /users/me on mount
└── test-utils.tsx           # AuthProvider wrapper for tests
```
