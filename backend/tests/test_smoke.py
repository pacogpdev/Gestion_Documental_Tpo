import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Verify that the root endpoint is reachable and returns a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Welcome" in response.json()["message"]

def test_health_endpoint():
    """Verify that the health endpoint returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
