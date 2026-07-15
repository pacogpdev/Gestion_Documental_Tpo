from sqlalchemy.orm import Session
from backend.app.models.schemas import AuditLog
import uuid
from datetime import datetime, timezone

class AuditService:
    @staticmethod
    def log_action(db: Session, user_id: str, action: str, entity_type: str, entity_id: str):
        """
        Records a critical action in the audit_logs table.
        """
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
