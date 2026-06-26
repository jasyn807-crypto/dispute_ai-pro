"""
Simulated mailing dispatch API router.

Endpoints:
- POST /api/mailing/dispatch  – Simulate mailing a dispute letter
- GET  /api/mailing/logs      – Get mailing history
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.client import Client
from app.models.dispute import DisputeLetter
from app.models.audit_log import MailingLog
from app.models.billing import BillingTransaction
from app.services.audit_logger import log_action
from app.schemas.dispute import (
    MailDispatchRequest,
    MailDispatchResponse,
    MailingLogResponse,
)

router = APIRouter()

BUREAU_ADDRESSES = {
    "equifax": "Equifax Information Services LLC, P.O. Box 740256, Atlanta, GA 30374-0256",
    "experian": "Experian, P.O. Box 4500, Allen, TX 75013",
    "transunion": "TransUnion LLC, P.O. Box 2000, Chester, PA 19016",
}


def _get_agency_client_ids(user: User, db: Session) -> list[int]:
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


# ── POST /api/mailing/dispatch ─────────────────────────────────────────────

@router.post("/dispatch", response_model=MailDispatchResponse, status_code=status.HTTP_201_CREATED)
def dispatch_mail(
    body: MailDispatchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simulate mailing a dispute letter to a credit bureau."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == body.dispute_letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")

    allowed_ids = _get_agency_client_ids(current_user, db)
    if letter.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not letter.letter_content or not letter.letter_content.strip():
        raise HTTPException(status_code=400, detail="Letter has no content. Generate a letter first.")

def perform_mail_dispatch(
    letter: DisputeLetter,
    db: Session,
    recipient_name: Optional[str] = None,
    recipient_address: Optional[str] = None,
    ip_address: Optional[str] = None,
    triggered_by_user_id: Optional[int] = None
) -> MailingLog:
    """
    Executes the actual USPS print/mail action (either via Lob API or simulated fallback logs)
    and saves the dispatch records.
    """
    bureau_lower = letter.bureau.lower() if letter.bureau else "unknown"
    rec_name = recipient_name or f"{bureau_lower.title()} Dispute Department"
    rec_addr = recipient_address or BUREAU_ADDRESSES.get(
        bureau_lower, f"{bureau_lower.title()} - Address on file"
    )

    # Simulate tracking number and delivery estimate
    tracking_number = f"USPS-CR-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    delivery_estimate = now + timedelta(days=5)

    mailing_log = MailingLog(
        dispute_letter_id=letter.id,
        recipient_name=rec_name,
        recipient_address=rec_addr,
        bureau=bureau_lower,
        tracking_number=tracking_number,
        status="queued",
        dispatched_at=now,
        delivery_estimate=delivery_estimate,
    )
    db.add(mailing_log)

    # Update letter status
    letter.status = "mailed"
    letter.mail_tracking_id = tracking_number
    letter.sent_at = now

    client = db.query(Client).filter(Client.id == letter.client_id).first()

    # Real-world Lob/USPS API request and structured logging
    import os
    import logging
    logger = logging.getLogger("app.mailing")
    lob_api_key = os.environ.get("LOB_API_KEY")
    if lob_api_key:
        logger.info(f"Dispatching letter #{letter.id} via Lob API...")
        try:
            import httpx
            resp = httpx.post(
                "https://api.lob.com/v1/letters",
                auth=(lob_api_key, ""),
                json={
                    "description": f"Dispute letter #{letter.id}",
                    "to": {
                        "name": rec_name,
                        "address_line1": rec_addr,
                        "address_city": "Atlanta",
                        "address_state": "GA",
                        "address_zip": "30374",
                        "address_country": "US"
                    },
                    "from": {
                        "name": f"{client.first_name if client else 'Client'} {client.last_name if client else 'User'}",
                        "address_line1": "123 Main St",
                        "address_city": "Atlanta",
                        "address_state": "GA",
                        "address_zip": "30303",
                        "address_country": "US"
                    },
                    "file": f"<html><body>{letter.letter_content}</body></html>",
                    "color": False
                },
                timeout=10.0
            )
            logger.info(f"Lob API response status: {resp.status_code}")
            if resp.status_code in (200, 201):
                lob_data = resp.json()
                tracking_number = lob_data.get("tracking_number") or tracking_number
                mailing_log.tracking_number = tracking_number
                letter.mail_tracking_id = tracking_number
                logger.info(f"Lob dispatch successful. Tracking number: {tracking_number}")
            else:
                logger.error(f"Lob API error: {resp.text}")
        except Exception as e:
            logger.error(f"Failed to call Lob API: {str(e)}")

    if triggered_by_user_id:
        log_action(
            db,
            user_id=triggered_by_user_id,
            action="dispatch_mail",
            resource_type="mailing_log",
            resource_id=None,
            ip_address=ip_address,
            details={
                "dispute_letter_id": letter.id,
                "tracking_number": tracking_number,
                "bureau": bureau_lower,
            },
        )

    db.commit()
    db.refresh(mailing_log)
    return mailing_log


@router.post("/dispatch", response_model=MailDispatchResponse, status_code=status.HTTP_201_CREATED)
def dispatch_mail(
    body: MailDispatchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simulate mailing a dispute letter to a credit bureau."""
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == body.dispute_letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")

    allowed_ids = _get_agency_client_ids(current_user, db)
    if letter.client_id not in allowed_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not letter.letter_content or not letter.letter_content.strip():
        raise HTTPException(status_code=400, detail="Letter has no content. Generate a letter first.")

    # Enforcement: If current user is a Client, they MUST have paid the dispatch transaction first
    if current_user.role == "client":
        paid_tx = db.query(BillingTransaction).filter(
            BillingTransaction.client_id == letter.client_id,
            BillingTransaction.description.like(f"%Letter #{letter.id}%"),
            BillingTransaction.status == "paid"
        ).first()
        if not paid_tx:
            raise HTTPException(
                status_code=402, 
                detail="Payment required for mailing. Please complete Stripe checkout first."
            )

    # Determine recipient
    bureau_lower = letter.bureau.lower() if letter.bureau else "unknown"
    recipient_name = body.recipient_name or f"{bureau_lower.title()} Dispute Department"
    recipient_address = body.recipient_address or BUREAU_ADDRESSES.get(
        bureau_lower, f"{bureau_lower.title()} - Address on file"
    )

    # Create dispatch
    mailing_log = perform_mail_dispatch(
        letter=letter,
        db=db,
        recipient_name=recipient_name,
        recipient_address=recipient_address,
        ip_address=request.client.host if request.client else None,
        triggered_by_user_id=current_user.id
    )


    return MailDispatchResponse(
        message=f"Letter dispatched to {recipient_name} via simulated USPS. Tracking: {tracking_number}",
        mailing_log=MailingLogResponse(
            id=mailing_log.id,
            dispute_letter_id=mailing_log.dispute_letter_id,
            recipient_name=mailing_log.recipient_name,
            recipient_address=mailing_log.recipient_address,
            bureau=mailing_log.bureau,
            tracking_number=mailing_log.tracking_number,
            status=mailing_log.status,
            dispatched_at=mailing_log.dispatched_at,
            delivery_estimate=mailing_log.delivery_estimate,
        ),
        letter_status=letter.status,
    )


# ── GET /api/mailing/logs ─────────────────────────────────────────────────

@router.get("/logs", response_model=List[MailingLogResponse])
def list_mailing_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get mailing history for all disputes belonging to the current user/agency."""
    allowed_ids = _get_agency_client_ids(current_user, db)
    if not allowed_ids:
        return []

    # Join through dispute_letters to filter by client_id
    logs = (
        db.query(MailingLog)
        .join(DisputeLetter, MailingLog.dispute_letter_id == DisputeLetter.id)
        .filter(DisputeLetter.client_id.in_(allowed_ids))
        .order_by(MailingLog.dispatched_at.desc())
        .all()
    )

    return [
        MailingLogResponse(
            id=log.id,
            dispute_letter_id=log.dispute_letter_id,
            recipient_name=log.recipient_name,
            recipient_address=log.recipient_address,
            bureau=log.bureau,
            tracking_number=log.tracking_number,
            status=log.status,
            dispatched_at=log.dispatched_at,
            delivery_estimate=log.delivery_estimate,
        )
        for log in logs
    ]
