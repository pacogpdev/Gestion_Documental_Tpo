from pathlib import Path

from backend.app.core.config import Settings


PROJECT_ROOT = Path(__file__).parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def test_storage_container_default_is_facturas_proveedores():
    settings = Settings(_env_file=None)

    assert settings.AZURE_STORAGE_CONTAINER == "facturas-proveedores"


def test_database_url_is_the_sole_engine_selector():
    settings_fields = Settings.model_fields

    assert "DATABASE_URL" in settings_fields
    assert not {"DB_URL", "SQLALCHEMY_DATABASE_URL", "AZURE_SQL_URL"}.intersection(
        settings_fields
    )


def test_environment_files_declare_the_facturas_proveedores_container():
    env_contents = (BACKEND_ROOT / ".env").read_text(encoding="utf-8")
    example_contents = (BACKEND_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "AZURE_STORAGE_CONTAINER=facturas-proveedores" in env_contents
    assert "AZURE_STORAGE_CONTAINER=facturas-proveedores" in example_contents


def test_requirements_declare_azure_blob_and_mssql_drivers():
    requirements = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "azure-storage-blob" in requirements
    assert "pymssql" in requirements
