"""
Dashboard stats and metrics API router.

Endpoints:
- GET /api/dashboard/stats           – Overview statistics
- GET /api/dashboard/pipeline        – Client pipeline by status
- GET /api/dashboard/dispute-metrics – Dispute success/failure breakdown
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.user import User
from app.models.agency import Agency
from app.models.client import Client
from app.models.dispute import DisputeLetter, DisputeItem
from app.schemas.dashboard import OverviewStats, PipelineResponse, PipelineStage, DisputeMetrics

router = APIRouter()


def _get_agency(user: User, db: Session) -> Agency:
    agency = db.query(Agency).filter(Agency.user_id == user.id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency profile not found")
    return agency


# ── GET /api/dashboard/stats ───────────────────────────────────────────────

@router.get("/stats", response_model=OverviewStats)
def dashboard_stats(
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db),
):
    """Overview stats: total clients, active disputes, success rate, revenue."""
    agency = _get_agency(current_user, db)

    clients = db.query(Client).filter(Client.agency_id == agency.id).all()
    total_clients = len(clients)
    active_clients = sum(1 for c in clients if c.status == "active")
    client_ids = [c.id for c in clients]

    # Dispute items
    total_disputes = 0
    active_disputes = 0
    resolved_disputes = 0

    if client_ids:
        total_disputes = db.query(DisputeItem).filter(
            DisputeItem.client_id.in_(client_ids)
        ).count()
        active_disputes = db.query(DisputeItem).filter(
            DisputeItem.client_id.in_(client_ids),
            DisputeItem.status == "pending",
        ).count()
        resolved_disputes = db.query(DisputeItem).filter(
            DisputeItem.client_id.in_(client_ids),
            DisputeItem.status.in_(["deleted", "verified"]),
        ).count()

    success_rate = 0.0
    if resolved_disputes > 0:
        deleted = db.query(DisputeItem).filter(
            DisputeItem.client_id.in_(client_ids),
            DisputeItem.status == "deleted",
        ).count()
        success_rate = round(deleted / resolved_disputes, 2) if resolved_disputes else 0.0

    # Letters
    letters_generated = 0
    letters_mailed = 0
    if client_ids:
        letters_generated = db.query(DisputeLetter).filter(
            DisputeLetter.client_id.in_(client_ids),
        ).count()
        letters_mailed = db.query(DisputeLetter).filter(
            DisputeLetter.client_id.in_(client_ids),
            DisputeLetter.status == "mailed",
        ).count()

    estimated_monthly_revenue = active_clients * 99.0

    return OverviewStats(
        total_clients=total_clients,
        active_clients=active_clients,
        total_disputes=total_disputes,
        active_disputes=active_disputes,
        resolved_disputes=resolved_disputes,
        success_rate=success_rate,
        letters_generated=letters_generated,
        letters_mailed=letters_mailed,
        estimated_monthly_revenue=estimated_monthly_revenue,
    )


# ── GET /api/dashboard/pipeline ────────────────────────────────────────────

@router.get("/pipeline", response_model=PipelineResponse)
def client_pipeline(
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db),
):
    """Client pipeline: count of clients at each status stage."""
    agency = _get_agency(current_user, db)

    rows = (
        db.query(Client.status, func.count(Client.id))
        .filter(Client.agency_id == agency.id)
        .group_by(Client.status)
        .all()
    )

    pipeline = [PipelineStage(status=row[0], count=row[1]) for row in rows]
    total = sum(s.count for s in pipeline)

    return PipelineResponse(pipeline=pipeline, total=total)


# ── GET /api/dashboard/dispute-metrics ─────────────────────────────────────

@router.get("/dispute-metrics", response_model=DisputeMetrics)
def dispute_metrics(
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db),
):
    """Dispute success/failure rates broken down by status and type."""
    agency = _get_agency(current_user, db)

    clients = db.query(Client).filter(Client.agency_id == agency.id).all()
    client_ids = [c.id for c in clients]

    if not client_ids:
        return DisputeMetrics(
            total=0,
            by_status={},
            by_negative_type={},
            success_rate=0.0,
        )

    total = db.query(DisputeItem).filter(
        DisputeItem.client_id.in_(client_ids)
    ).count()

    # By status
    status_rows = (
        db.query(DisputeItem.status, func.count(DisputeItem.id))
        .filter(DisputeItem.client_id.in_(client_ids))
        .group_by(DisputeItem.status)
        .all()
    )
    by_status = {row[0]: row[1] for row in status_rows}

    # By negative type
    type_rows = (
        db.query(DisputeItem.negative_type, func.count(DisputeItem.id))
        .filter(DisputeItem.client_id.in_(client_ids))
        .group_by(DisputeItem.negative_type)
        .all()
    )
    by_negative_type = {(row[0] or "unknown"): row[1] for row in type_rows}

    # Success rate
    resolved = by_status.get("deleted", 0) + by_status.get("verified", 0)
    deleted = by_status.get("deleted", 0)
    success_rate = round(deleted / resolved, 2) if resolved > 0 else 0.0

    return DisputeMetrics(
        total=total,
        by_status=by_status,
        by_negative_type=by_negative_type,
        success_rate=success_rate,
    )
