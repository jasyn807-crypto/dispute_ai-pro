from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.user import User, UserRole
from app.models.agency import Agency
from app.models.client import Client
from app.models.dispute import DisputeItem, DisputeLetter
from app.models.billing import BillingTransaction
from app.schemas.client import ClientListItem, AgencyMetrics

router = APIRouter()

@router.get("/clients", response_model=List[ClientListItem])
def list_clients(
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db)
):
    agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency profile not found"
        )
    
    clients = db.query(Client).filter(Client.agency_id == agency.id).all()
    
    result = []
    for client in clients:
        result.append(ClientListItem(
            id=client.id,
            email=client.user.email if client.user else "",
            first_name=client.first_name,
            last_name=client.last_name,
            phone=client.phone,
            status=client.status,
            onboarding_step=client.onboarding_step,
            created_at=client.created_at
        ))
    return result

@router.get("/metrics", response_model=AgencyMetrics)
def get_metrics(
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db)
):
    agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency profile not found"
        )

    # 1. Total clients count
    clients = db.query(Client).filter(Client.agency_id == agency.id).all()
    total_clients = len(clients)
    client_ids = [c.id for c in clients]

    # 2. Dispute items aggregation
    total_disputed = 0
    pending = 0
    deleted = 0
    verified = 0
    success_rate = 0.75  # Default mock success rate for M1

    if client_ids:
        total_disputed = db.query(DisputeItem).filter(DisputeItem.client_id.in_(client_ids)).count()
        pending = db.query(DisputeItem).filter(DisputeItem.client_id.in_(client_ids), DisputeItem.status == "pending").count()
        deleted = db.query(DisputeItem).filter(DisputeItem.client_id.in_(client_ids), DisputeItem.status == "deleted").count()
        verified = db.query(DisputeItem).filter(DisputeItem.client_id.in_(client_ids), DisputeItem.status == "verified").count()
        
        resolved = deleted + verified
        if resolved > 0:
            success_rate = round(float(deleted) / resolved, 2)

    # 3. Dispute letters count for simulated billing
    total_disputes_sent = 0
    disputes_by_status = {"draft": 0, "mailed": 0, "accepted": 0, "rejected": 0}
    if client_ids:
        total_disputes_sent = db.query(DisputeLetter).filter(
            DisputeLetter.client_id.in_(client_ids),
            DisputeLetter.status == "mailed"
        ).count()
        
        statuses = ["draft", "mailed", "accepted", "rejected"]
        for s in statuses:
            disputes_by_status[s] = db.query(DisputeLetter).filter(
                DisputeLetter.client_id.in_(client_ids),
                DisputeLetter.status == s
            ).count()

    # 4. Billing summary
    active_clients_count = sum(1 for c in clients if c.status == "active")
    monthly_recurring_revenue = active_clients_count * 99.0
    pending_invoice_amount = (total_clients - active_clients_count) * 99.0

    # Fetch billing transactions
    tx_records = db.query(BillingTransaction).filter(BillingTransaction.agency_id == agency.id).all()
    transactions = [
        {
            "id": tx.id,
            "amount": tx.amount,
            "description": tx.description,
            "status": tx.status,
            "created_at": tx.created_at
        }
        for tx in tx_records
    ]

    # Simulated billing top-level vs inside metrics
    simulated_billing_top = total_clients * 99.0
    simulated_billing_dict = {
        "total_cost": total_disputes_sent * 15.00,
        "currency": "USD",
        "rate_per_dispatch": 15.00
    }

    # Consolidated structures
    dispute_metrics = {
        "total_disputed": total_disputed,
        "pending": pending,
        "deleted": deleted,
        "verified": verified,
        "success_rate": success_rate
    }

    billing_summary = {
        "active_clients_count": active_clients_count,
        "monthly_recurring_revenue": monthly_recurring_revenue,
        "pending_invoice_amount": pending_invoice_amount,
        "payment_history": transactions
    }

    metrics_dict = {
        "total_clients": total_clients,
        "total_disputes_sent": total_disputes_sent,
        "disputes_by_status": disputes_by_status,
        "dispute_success_rate": success_rate,
        "simulated_billing": simulated_billing_dict
    }

    return AgencyMetrics(
        total_clients=total_clients,
        dispute_success_rate=success_rate,
        simulated_billing=simulated_billing_top,
        dispute_metrics=dispute_metrics,
        billing_summary=billing_summary,
        agency_id=agency.id,
        metrics=metrics_dict
    )
