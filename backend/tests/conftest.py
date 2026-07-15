import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import the app and dependencies
import sys
import os
# Add the project root to the path so 'backend.app' imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.main import app
from backend.app.core.database import get_db, Base, db_manager, DatabaseManager
from backend.app.core.security import get_current_user
# IMPORTANT: Import models so they register with Base.metadata before create_all
from backend.app.models.schemas import Invoice, Supplier, LineItem, Role, User, AuditLog

# Use a temporary file for SQLite to avoid :memory: concurrency issues with FastAPI's threadpool
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    test_manager = DatabaseManager(db_url=SQLALCHEMY_DATABASE_URL)
    
    Base.metadata.create_all(bind=test_manager.engine)
    db = test_manager.get_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_manager.engine)
        test_manager.engine.dispose()
        # Remove the temporary database file
        if os.path.exists("test_db.sqlite"):
            os.remove("test_db.sqlite")

@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with overridden dependencies."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        # Return a mock user payload that matches what Entra ID would return
        return {
            "email": "test@example.com",
            "roles": ["Admin", "Clerk", "Approver"]
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides after test
    app.dependency_overrides.clear()