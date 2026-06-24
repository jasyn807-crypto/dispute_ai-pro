"""
Dispute management API router.

Endpoints:
- POST /api/disputes               – Create a dispute (link item to a new letter)
- GET  /api/disputes               – List disputes (filterable by client_id, status)
- GET  /api/disputes/{id}          – Dispute detail with letter + items
- POST /api/disputes/{id}/generate-letter   – Generate dispute letter
- POST /api/disputes/{id}/check-compliance  – Run compliance check
- PUT  /api/disputes/{id}/status   – Update dispute status
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.client import Client
from app.models.dispute import DisputeLetter, DisputeItem
from app.services.dispute_generator import generate_dispute_letter
from app.services.compliance_checker import check_compliance
from app.services.audit_logger import log_action
from app.schemas.dispute import (
    DisputeCreate,
    DisputeStatusUpdate,
    DisputeItemResponse,
    DisputeLetterResponse,
    DisputeDetailResponse,
    ComplianceCheckResponse,
)

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_agency_client_ids(user: User, db: Session) -> list[int]:
    """Return client IDs belonging to the current user's agency."""
    if user.role == "agency":
        agency = user.agency_profile
        if not agency:
            return []
        clients = db.query(Client).filter(Client.agency_id == agency.id).all()
        return [c.id for c in clients]
    elif user.role == "client":
        client = db.query(Client).filter(Client.user_id == user.id).first()
        return [client.id] if client else []
    return []


# ── POST /api/disputes ─────────────────────────────────────────────────────

@router.post("", response_model=DisputeLetterResponse, status_code=status.HTTP_201_CREATED)
def create_dispute(
    body: DisputeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new dispute letter and associate a dispute item with it."""
    # Verify the dispute item exists
    item = db.query(DisputeItem).filter(DisputeItem.id == body.dispute_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Dispute item not found")

    # Authorization: agency staff can only dispute items for their clients
    allowed_ids = _get_agency_client_ids(current_user, db)
    if item.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized for this client")

    # Optionally update the dispute reason on the item
    if body.dispute_reason:
        item.dispute_reason = body.dispute_reason

    # Create a DisputeLetter (draft)
    letter = DisputeLetter(
        client_id=item.client_id,
        bureau=item.bureau,
        letter_content="",  # Will be populated via /generate-letter
        status="draft",
    )
    db.add(letter)
    db.flush()

    # Link item to the new letter
    item.dispute_letter_id = letter.id
    item.status = "pending"
    item.disputed_at = datetime.now(timezone.utc)

    # Audit
    log_action(
        db,
        user_id=current_user.id,
        action="create_dispute",
        resource_type="dispute_letter",
        resource_id=letter.id,
        ip_address=request.client.host if request.client else None,
        details={"dispute_item_id": item.id, "bureau": item.bureau},
    )

    db.commit()
    db.refresh(letter)

    return DisputeLetterResponse(
        id=letter.id,
        client_id=letter.client_id,
        bureau=letter.bureau,
        letter_content=letter.letter_content,
        status=letter.status,
        mail_tracking_id=letter.mail_tracking_id,
        sent_at=letter.sent_at,
        created_at=letter.created_at,
    )


# ── GET /api/disputes ──────────────────────────────────────────────────────

@router.get("", response_model=List[DisputeLetterResponse])
def list_disputes(
    client_id: Optional[int] = None,
    dispute_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List dispute letters, optionally filtered by client_id and/or status."""
    allowed_ids = _get_agency_client_ids(current_user, db)
    if not allowed_ids:
        return []

    query = db.query(DisputeLetter).filter(DisputeLetter.client_id.in_(allowed_ids))

    if client_id is not None:
        if client_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this client")
        query = query.filter(DisputeLetter.client_id == client_id)

    if dispute_status:
        query = query.filter(DisputeLetter.status == dispute_status)

    letters = query.order_by(DisputeLetter.created_at.desc()).all()

    return [
        DisputeLetterResponse(
            id=l.id,
            client_id=l.client_id,
            bureau=l.bureau,
            letter_content=l.letter_content,
            status=l.status,
            mail_tracking_id=l.mail_tracking_id,
            sent_at=l.sent_at,
            created_at=l.created_at,
        )
        for l in letters
    ]


# ── GET /api/disputes/{id} ─────────────────────────────────────────────────

@router.get("/{dispute_id}", response_model=DisputeDetailResponse)
def get_dispute_detail(
    dispute_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full dispute detail including the letter and associated items."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == dispute_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")

    allowed_ids = _get_agency_client_ids(current_user, db)
    if letter.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    items = db.query(DisputeItem).filter(DisputeItem.dispute_letter_id == letter.id).all()

    return DisputeDetailResponse(
        letter=DisputeLetterResponse(
            id=letter.id,
            client_id=letter.client_id,
            bureau=letter.bureau,
            letter_content=letter.letter_content,
            status=letter.status,
            mail_tracking_id=letter.mail_tracking_id,
            sent_at=letter.sent_at,
            created_at=letter.created_at,
        ),
        items=[
            DisputeItemResponse(
                id=i.id,
                client_id=i.client_id,
                dispute_letter_id=i.dispute_letter_id,
                credit_report_id=i.credit_report_id,
                bureau=i.bureau,
                creditor_name=i.creditor_name,
                account_number=i.account_number,
                balance=i.balance,
                negative_type=i.negative_type,
                dispute_reason=i.dispute_reason,
                status=i.status,
                disputed_at=i.disputed_at,
                resolved_at=i.resolved_at,
                created_at=i.created_at,
            )
            for i in items
        ],
    )


# ── POST /api/disputes/{id}/generate-letter ────────────────────────────────

@router.post("/{dispute_id}/generate-letter", response_model=DisputeLetterResponse)
def generate_letter(
    dispute_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate (or regenerate) a dispute letter using simulated LLM."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == dispute_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")

    allowed_ids = _get_agency_client_ids(current_user, db)
    if letter.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Gather client info
    client = db.query(Client).filter(Client.id == letter.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get the first linked dispute item for account details
    item = db.query(DisputeItem).filter(DisputeItem.dispute_letter_id == letter.id).first()

    account_name = item.creditor_name if item else "Unknown Account"
    account_last4 = item.account_number[-4:] if item and item.account_number else None
    item_type = item.negative_type or "collection" if item else "collection"
    balance = item.balance or 0.0 if item else 0.0

    content = generate_dispute_letter(
        client_first_name=client.first_name,
        client_last_name=client.last_name,
        client_address=None,  # Client model doesn't have address
        client_ssn_last4=None,
        client_dob=None,
        bureau=letter.bureau,
        account_name=account_name,
        account_last4=account_last4,
        item_type=item_type,
        balance=balance,
    )

    letter.letter_content = content
    letter.status = "draft"

    log_action(
        db,
        user_id=current_user.id,
        action="generate_letter",
        resource_type="dispute_letter",
        resource_id=letter.id,
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(letter)

    return DisputeLetterResponse(
        id=letter.id,
        client_id=letter.client_id,
        bureau=letter.bureau,
        letter_content=letter.letter_content,
        status=letter.status,
        mail_tracking_id=letter.mail_tracking_id,
        sent_at=letter.sent_at,
        created_at=letter.created_at,
    )


# ── POST /api/disputes/{id}/check-compliance ───────────────────────────────

@router.post("/{dispute_id}/check-compliance", response_model=ComplianceCheckResponse)
def run_compliance_check(
    dispute_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run compliance check on a dispute letter."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == dispute_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")

    allowed_ids = _get_agency_client_ids(current_user, db)
    if letter.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not letter.letter_content or not letter.letter_content.strip():
        raise HTTPException(
            status_code=400,
            detail="Letter has no content. Generate a letter first."
        )

    result = check_compliance(letter.letter_content)

    # Persist compliance result on the letter (using existing status field)
    compliance_status_str = "passed" if result.passed else "failed"
    # Store compliance info in status field note (letter status stays as draft/mailed)

    log_action(
        db,
        user_id=current_user.id,
        action="check_compliance",
        resource_type="dispute_letter",
        resource_id=letter.id,
        ip_address=request.client.host if request.client else None,
        details={"passed": result.passed, "flags": result.flags},
    )

    db.commit()

    return ComplianceCheckResponse(
        dispute_letter_id=letter.id,
        passed=result.passed,
        flags=result.flags,
        notes=result.notes,
        compliance_status=compliance_status_str,
    )


# ── PUT /api/disputes/{id}/status ──────────────────────────────────────────

@router.put("/{dispute_id}/status", response_model=DisputeLetterResponse)
def update_dispute_status(
    dispute_id: int,
    body: DisputeStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the status of a dispute letter."""
    valid_statuses = {"draft", "pending", "mailed", "accepted", "rejected",
                      "in_progress", "sent", "responded", "resolved"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed: {sorted(valid_statuses)}"
        )

    letter = db.query(DisputeLetter).filter(DisputeLetter.id == dispute_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")

    allowed_ids = _get_agency_client_ids(current_user, db)
    if letter.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    old_status = letter.status
    letter.status = body.status

    # If resolved/accepted/rejected, update linked dispute items
    if body.status in ("resolved", "accepted"):
        items = db.query(DisputeItem).filter(DisputeItem.dispute_letter_id == letter.id).all()
        for item in items:
            item.status = "deleted"
            item.resolved_at = datetime.now(timezone.utc)
    elif body.status == "rejected":
        items = db.query(DisputeItem).filter(DisputeItem.dispute_letter_id == letter.id).all()
        for item in items:
            item.status = "verified"
            item.resolved_at = datetime.now(timezone.utc)

    log_action(
        db,
        user_id=current_user.id,
        action="update_dispute_status",
        resource_type="dispute_letter",
        resource_id=letter.id,
        ip_address=request.client.host if request.client else None,
        details={"old_status": old_status, "new_status": body.status},
    )

    db.commit()
    db.refresh(letter)

    return DisputeLetterResponse(
        id=letter.id,
        client_id=letter.client_id,
        bureau=letter.bureau,
        letter_content=letter.letter_content,
        status=letter.status,
        mail_tracking_id=letter.mail_tracking_id,
        sent_at=letter.sent_at,
        created_at=letter.created_at,
    )
