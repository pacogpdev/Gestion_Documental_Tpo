from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Facturas Control"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/facturas_db"
    
    # Azure Entra ID
    ENTRA_ID_TENANT_ID: str = ""
    ENTRA_ID_CLIENT_ID: str = ""
    ENTRA_ID_JWKS_URL: str = "" # Usually https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
    
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

    model_config = SettingsConfigDict(env_file="backend/.env")

settings = Settings()
