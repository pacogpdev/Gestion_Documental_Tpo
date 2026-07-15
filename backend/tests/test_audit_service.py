import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from backend.app.services.audit_service import AuditService
from backend.app.models.schemas import AuditLog

import pytest
import uuid
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from backend.app.services.audit_service import AuditService
from backend.app.models.schemas import AuditLog

def test_log_action_persists_record(db_session: Session):
    """Scenario: Record persistence. Verify that log_action saves a record to the DB."""
    user_id = str(uuid.uuid4())
    action = "APPROVE_INVOICE"
    entity_type = "Invoice"
    entity_id = str(uuid.uuid4())
    
    entry = AuditService.log_action(db_session, user_id, action, entity_type, entity_id)
    
    # Verify the returned object
    assert str(entry.user_id) == user_id
    assert entry.action == action
    assert entry.entity_type == entity_type
    assert str(entry.entity_id) == entity_id
    
    # Verify persistence in DB
    db_entry = db_session.query(AuditLog).filter(AuditLog.id == entry.id).first()
    assert db_entry is not None
    assert db_entry.action == action

def test_log_action_propagates_commit_failure(db_session: Session):
    """Scenario: Database commit failure. Verify that the exception is propagated."""
    # Mock the session's commit method to raise an exception
    # We use a mock for the session here because we want to force a failure
    mock_session = MagicMock(spec=Session)
    mock_session.commit.side_effect = Exception("DB Connection Lost")
    
    with pytest.raises(Exception) as excinfo:
        AuditService.log_action(mock_session, "u1", "act", "ent", "id")
    
    assert "DB Connection Lost" in str(excinfo.value)
