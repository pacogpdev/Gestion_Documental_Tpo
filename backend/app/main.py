from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.endpoints import invoices, suppliers, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="System for automated invoice extraction and approval",
    version="1.0.0"
)

# CORS — allow Vite dev server and production origin.
# When BACKEND_CORS_ORIGINS is set (comma-separated), use those.
# Otherwise fall back to localhost dev defaults.
_cors_env = settings.BACKEND_CORS_ORIGINS.strip()
if _cors_env:
    origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",  # alternative dev port
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(invoices.router, prefix="/api")
app.include_router(suppliers.router, prefix="/api")
app.include_router(users.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.get("/health")
async def health():
    return {"status": "ok"}
