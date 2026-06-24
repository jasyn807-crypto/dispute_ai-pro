"""
Pydantic schemas for dispute-related endpoints.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ────────────────────────────────────────────────────────

class DisputeCreate(BaseModel):
    """Create a new dispute for a negative item."""
    client_id: int
    dispute_item_id: int
    dispute_reason: Optional[str] = None


class DisputeStatusUpdate(BaseModel):
    """Update dispute status."""
    status: str  # pending, in_progress, sent, responded, resolved, rejected
    resolution_notes: Optional[str] = None


class GenerateLetterRequest(BaseModel):
    """Optional parameters for letter generation."""
    bureau: Optional[str] = None  # Override if different from item's bureau


class MailDispatchRequest(BaseModel):
    """Request to simulate mailing a dispute letter."""
    dispute_letter_id: int
    recipient_name: Optional[str] = None
    recipient_address: Optional[str] = None


# ── Response Schemas ───────────────────────────────────────────────────────

class DisputeItemResponse(BaseModel):
    id: int
    client_id: int
    dispute_letter_id: Optional[int] = None
    credit_report_id: Optional[str] = None
    bureau: str
    creditor_name: str
    account_number: Optional[str] = None
    balance: Optional[float] = None
    negative_type: Optional[str] = None
    dispute_reason: Optional[str] = None
    status: str
    disputed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisputeLetterResponse(BaseModel):
    id: int
    client_id: int
    bureau: str
    letter_content: str
    status: str
    compliance_status: Optional[str] = None
    compliance_notes: Optional[str] = None
    mail_tracking_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisputeDetailResponse(BaseModel):
    """Full dispute detail including the letter and disputed items."""
    letter: DisputeLetterResponse
    items: List[DisputeItemResponse]


class ComplianceCheckResponse(BaseModel):
    dispute_letter_id: int
    passed: bool
    flags: List[str]
    notes: str
    compliance_status: str


class MailingLogResponse(BaseModel):
    id: int
    dispute_letter_id: int
    recipient_name: str
    recipient_address: str
    bureau: str
    tracking_number: Optional[str] = None
    status: str
    dispatched_at: datetime
    delivery_estimate: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MailDispatchResponse(BaseModel):
    message: str
    mailing_log: MailingLogResponse
    letter_status: str
