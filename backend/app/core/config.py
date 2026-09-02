from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import List, Optional

ENTRA_REQUIRED_FIELDS = (
    "ENTRA_ID_TENANT_ID",
    "ENTRA_ID_API_AUDIENCE",
    "ENTRA_ID_ISSUER",
    "ENTRA_ID_JWKS_URL",
    "ENTRA_ID_API_SCOPE",
)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Facturas Control"
    API_V1_STR: str = "/api/v1"

    # Database (SQLite dev, Azure SQL prod — set via .env)
    DATABASE_URL: str = "sqlite:///backend/test.db"

    # CORS origins — comma-separated list of allowed origins.
    # Empty string = fall back to localhost dev defaults in main.py.
    BACKEND_CORS_ORIGINS: str = ""
    """Comma-separated list of allowed CORS origins (e.g. 'https://facturas.pedroortiz.com').
    When empty, main.py falls back to localhost dev origins."""

    # Azure Entra ID
    APP_ENV: str = "local"
    AUTH_MODE: str = "local-dev"
    ENTRA_ID_TENANT_ID: str = ""
    ENTRA_ID_CLIENT_ID: str = ""
    ENTRA_ID_API_AUDIENCE: str = ""
    ENTRA_ID_ISSUER: str = ""
    ENTRA_ID_JWKS_URL: str = "" # Usually https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
    ENTRA_ID_API_SCOPE: str = ""
    
    # Azure AI Content Understanding (replaces Document Intelligence)
    AZURE_CONTENT_ENDPOINT: Optional[str] = None
    """Content Understanding endpoint (e.g. https://{resource}.services.ai.azure.com/).
    Falls back to AZURE_AI_ENDPOINT if not set."""
    AZURE_CONTENT_KEY: Optional[str] = None
    """Content Understanding API key. Falls back to AZURE_AI_KEY if not set."""
    AZURE_AI_ENDPOINT: str = ""
    """Legacy Document Intelligence endpoint — used as fallback for Content Understanding."""
    AZURE_AI_KEY: str = ""
    
    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "facturas-proveedores"

    @field_validator('API_V1_STR')
    @classmethod
    def api_v1_str_must_start_with_slash(cls, v: str) -> str:
        if not v.startswith('/'):
            raise ValueError('API_V1_STR must start with a forward slash (/)')
        return v

    @model_validator(mode="after")
    def validate_auth_configuration(self):
        if self.APP_ENV not in {"local", "staging", "production"}:
            raise ValueError("APP_ENV must be local, staging, or production")
        if self.AUTH_MODE not in {"local-dev", "entra"}:
            raise ValueError("AUTH_MODE must be local-dev or entra")
        if self.AUTH_MODE == "local-dev" and self.APP_ENV != "local":
            raise ValueError("local-dev authentication is allowed only in local APP_ENV")
        if self.AUTH_MODE == "entra":
            if not all(getattr(self, field) for field in ENTRA_REQUIRED_FIELDS):
                raise ValueError("Entra authentication requires complete identity configuration")
        return self

    @property
    def is_local_development(self) -> bool:
        return self.APP_ENV == "local" and self.AUTH_MODE == "local-dev"

    model_config = SettingsConfigDict(env_file="backend/.env")

settings = Settings()
