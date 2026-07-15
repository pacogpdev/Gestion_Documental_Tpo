import pytest
from pydantic import ValidationError

# We import Settings to test its validation rules
from backend.app.core.config import Settings


def test_settings_default_values():
    """Verify that Settings loads with expected default values."""
    settings = Settings()
    assert settings.PROJECT_NAME == "Facturas Control"
    assert settings.API_V1_STR == "/api/v1"


def test_api_v1_str_must_start_with_slash():
    """
    TDD Red Phase: Ensure API_V1_STR always starts with a forward slash.
    This test is expected to FAIL initially because the validator does not exist yet.
    """
    with pytest.raises(ValidationError):
        Settings(API_V1_STR="api/v1")  # Missing leading slash should be invalid