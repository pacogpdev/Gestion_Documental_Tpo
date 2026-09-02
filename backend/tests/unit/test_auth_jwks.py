from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt
from jose.utils import base64url_encode

from backend.app.core import security


AUDIENCE = "api://facturas"
ISSUER = "https://login.microsoftonline.com/tenant-id/v2.0"
SCOPE = "api://facturas/access_as_user"


class Response:
    def __init__(self, keys):
        self.keys = keys

    def raise_for_status(self):
        return None

    def json(self):
        return {"keys": self.keys}


def as_base64url(value):
    return base64url_encode(value.to_bytes((value.bit_length() + 7) // 8, "big")).decode()


def public_jwk(private_key, kid="key-1"):
    numbers = private_key.public_key().public_numbers()
    return {"kty": "RSA", "kid": kid, "n": as_base64url(numbers.n), "e": as_base64url(numbers.e)}


def access_token(private_key, **claims):
    now = datetime.now(timezone.utc)
    payload = {
        "aud": AUDIENCE,
        "iss": ISSUER,
        "tid": "tenant-id",
        "scp": "access_as_user",
        "exp": now + timedelta(minutes=5),
        "nbf": now - timedelta(minutes=1),
        **claims,
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "key-1"})


@pytest.fixture
def verifier(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    for name, value in {
        "ENTRA_ID_TENANT_ID": "tenant-id",
        "ENTRA_ID_CLIENT_ID": AUDIENCE,
        "ENTRA_ID_API_AUDIENCE": AUDIENCE,
        "ENTRA_ID_ISSUER": ISSUER,
        "ENTRA_ID_JWKS_URL": "https://issuer.example/keys",
        "ENTRA_ID_API_SCOPE": SCOPE,
    }.items():
        monkeypatch.setattr(security.settings, name, value)
    monkeypatch.setattr(security.requests, "get", lambda *_args, **_kwargs: Response([public_jwk(private_key)]))
    return security.SecurityService(), private_key


def assert_unauthorized(verifier, token):
    with pytest.raises(HTTPException) as error:
        verifier.validate_token(token)
    assert error.value.status_code == 401
    assert error.value.detail == "Invalid access token"


def test_valid_access_token_is_accepted(verifier):
    service, private_key = verifier

    assert service.validate_token(access_token(private_key))["tid"] == "tenant-id"


@pytest.mark.parametrize(
    "claims",
    [
        {"aud": "api://other"},
        {"iss": "https://issuer.example/v2.0"},
        {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        {"nbf": datetime.now(timezone.utc) + timedelta(minutes=1)},
    ],
    ids=["wrong-audience", "wrong-issuer", "expired", "not-before"],
)
def test_invalid_claims_are_rejected_without_error_details(verifier, claims):
    service, private_key = verifier

    assert_unauthorized(service, access_token(private_key, **claims))


def test_bad_signature_is_rejected_without_error_details(verifier):
    service, _ = verifier
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    assert_unauthorized(service, access_token(other_key))


def test_jwks_timeout_returns_safe_service_unavailable(verifier, monkeypatch):
    service, private_key = verifier
    monkeypatch.setattr(security.requests, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(security.requests.Timeout()))

    with pytest.raises(HTTPException) as error:
        service.validate_token(access_token(private_key))

    assert error.value.status_code == 503
    assert error.value.detail == "Identity provider unavailable"


def test_jwks_cache_refreshes_after_its_ttl(verifier, monkeypatch):
    service, private_key = verifier
    calls = []
    timestamps = iter((0, 10, 300, 300))
    monkeypatch.setattr(security, "monotonic", lambda: next(timestamps))
    monkeypatch.setattr(
        security.requests,
        "get",
        lambda *_args, **_kwargs: calls.append(1) or Response([public_jwk(private_key)]),
    )

    service._get_jwks()
    service._get_jwks()
    service._get_jwks()

    assert len(calls) == 2


def test_unknown_kid_refreshes_jwks_once_before_accepting_new_key(verifier, monkeypatch):
    service, private_key = verifier
    responses = [Response([]), Response([public_jwk(private_key)])]
    monkeypatch.setattr(security.requests, "get", lambda *_args, **_kwargs: responses.pop(0))

    assert service.validate_token(access_token(private_key))["tid"] == "tenant-id"
    assert responses == []
