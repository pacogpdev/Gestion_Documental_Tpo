import inspect
from datetime import timezone
from pathlib import Path

from backend.app.api.endpoints.invoices import _cleanup_uploaded_blob
from backend.app.core.database import DatabaseManager
from backend.app.models.schemas import AuditLog, Invoice, InvoiceResponse


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_database_manager_accepts_an_optional_database_url():
    parameter = inspect.signature(DatabaseManager.__init__).parameters["db_url"]

    assert parameter.annotation == str | None
    assert parameter.default is None


def test_model_timestamp_defaults_are_utc_aware():
    created_at = Invoice.__table__.c.created_at.default.arg(None)
    timestamp = AuditLog.__table__.c.timestamp.default.arg(None)

    assert created_at.tzinfo is timezone.utc
    assert timestamp.tzinfo is timezone.utc


def test_invoice_response_uses_pydantic_v2_attribute_configuration():
    assert "Config" not in InvoiceResponse.__dict__
    assert InvoiceResponse.model_config["from_attributes"] is True


def test_blob_cleanup_accepts_unconfigured_storage():
    _cleanup_uploaded_blob("https://storage.example/container/invoice.pdf", None)


def test_mypy_configuration_enables_sqlalchemy_support():
    config = (BACKEND_ROOT / "mypy.ini").read_text()

    assert "plugins = sqlalchemy.ext.mypy.plugin" in config
    assert "ignore_missing_imports = True" in config
    assert "check_untyped_defs = True" in config


def test_pytest_configuration_filters_starlette_test_client_warning():
    config = (BACKEND_ROOT / "pytest.ini").read_text()

    assert "filterwarnings" in config
    assert "starlette.exceptions.StarletteDeprecationWarning" in config
