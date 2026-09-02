import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


AUTH_ENVIRONMENT_KEYS = (
    "APP_ENV",
    "AUTH_MODE",
    "ENTRA_ID_TENANT_ID",
    "ENTRA_ID_API_AUDIENCE",
    "ENTRA_ID_ISSUER",
    "ENTRA_ID_JWKS_URL",
    "ENTRA_ID_API_SCOPE",
)


def make_settings(monkeypatch, **values):
    for key in AUTH_ENVIRONMENT_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def test_local_bypass_requires_explicit_local_environment_and_mode(monkeypatch):
    settings = make_settings(monkeypatch, APP_ENV="local", AUTH_MODE="local-dev")

    assert settings.is_local_development is True


def test_local_dev_mode_is_rejected_outside_local_environment(monkeypatch):
    with pytest.raises(ValidationError):
        make_settings(monkeypatch, APP_ENV="production", AUTH_MODE="local-dev")


def test_entra_mode_fails_closed_when_required_settings_are_missing(monkeypatch):
    with pytest.raises(ValidationError):
        make_settings(monkeypatch, APP_ENV="production", AUTH_MODE="entra")


def test_entra_mode_accepts_complete_production_configuration(monkeypatch):
    settings = make_settings(
        monkeypatch,
        APP_ENV="production",
        AUTH_MODE="entra",
        ENTRA_ID_TENANT_ID="tenant-id",
        ENTRA_ID_API_AUDIENCE="api://facturas",
        ENTRA_ID_ISSUER="https://login.microsoftonline.com/tenant-id/v2.0",
        ENTRA_ID_JWKS_URL="https://login.microsoftonline.com/tenant-id/discovery/v2.0/keys",
        ENTRA_ID_API_SCOPE="api://facturas/access_as_user",
    )

    assert settings.is_local_development is False
