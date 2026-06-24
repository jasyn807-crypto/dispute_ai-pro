"""
Audit logging service.

Records user actions for compliance and security audit trails.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session


# ── Inline AuditLog model reference ────────────────────────────────────────
# We import here to avoid circular imports at module level.

def log_action(
    db: Session,
    *,
    user_id: Optional[int] = None,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """
    Create an audit log entry.

    Args:
        db: SQLAlchemy session
        user_id: ID of the user performing the action
        action: Short verb phrase, e.g. "create_dispute", "upload_report"
        resource_type: The type of resource acted upon, e.g. "dispute", "client"
        resource_id: The primary key of the affected resource
        ip_address: Requesting client IP address
        details: Optional JSON-serializable dict with extra context
    """
    from app.models.audit_log import AuditLog  # deferred import

    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
        details=details,
    )
    db.add(entry)
    # We don't commit here – the caller is responsible for the transaction.
