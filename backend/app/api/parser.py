import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.credit_report import CreditReport
from app.models.dispute import DisputeItem
from app.services.parser import CreditReportParser
from app.schemas.parser import ParserUploadResponse, ReportResponse, NegativeItemSchema

router = APIRouter()

UPLOAD_DIR = "uploads/documents"

@router.post("/upload", response_model=ParserUploadResponse)
async def upload_credit_report(
    report: UploadFile = File(...),
    client_id: Optional[int] = Form(None),
    client_id_query: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        content = await report.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
        
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploads are not allowed.")
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 5MB limit.")

    # Determine client_id
    target_client_id = None
    if current_user.role == "client":
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client profile not found")
        target_client_id = client.id
    elif current_user.role == "agency":
        resolved_client_id = client_id or client_id_query
        if not resolved_client_id:
            # Fallback to first client for agency uploads
            first_client = db.query(Client).filter(Client.agency_id == current_user.agency_profile.id).first()
            if not first_client:
                raise HTTPException(status_code=400, detail="No clients associated with this agency")
            resolved_client_id = first_client.id
        
        client = db.query(Client).filter(
            Client.id == resolved_client_id,
            Client.agency_id == current_user.agency_profile.id
        ).first()
        if not client:
            raise HTTPException(status_code=403, detail="Client does not belong to your agency")
        target_client_id = client.id
    else:
        raise HTTPException(status_code=403, detail="Unauthorized role")

    # Save report file under uploads/documents/client_{client_id}/
    client_dir = os.path.join(UPLOAD_DIR, f"client_{target_client_id}")
    os.makedirs(client_dir, exist_ok=True)
    safe_filename = "".join([c for c in report.filename if c.isalnum() or c in "._-"])
    file_path = os.path.join(client_dir, f"report_{safe_filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Parse content
    parsed_items = CreditReportParser.parse_report(report.filename, content)

    # Save CreditReport record
    db_report = CreditReport(
        client_id=target_client_id,
        filename=report.filename or "unknown_report",
        file_path=file_path,
        status="parsed",
        raw_content=content.decode("utf-8", errors="ignore")
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # Save DisputeItem records
    db_items = []
    for item in parsed_items:
        db_item = DisputeItem(
            client_id=target_client_id,
            bureau=item["bureau"],
            creditor_name=item["creditor"],
            account_number=item.get("account_number"),
            balance=item["amount"],
            negative_type=item["status"],
            status="pending",
            credit_report_id=db_report.id
        )
        db.add(db_item)
        db_items.append(db_item)
    db.commit()

    for item in db_items:
        db.refresh(item)

    # Update client onboarding_step and status
    if client.onboarding_step in ["document_upload", "document_uploaded"]:
        client.onboarding_step = "report_parsed"
    if client.status in ["onboarding", "documents_uploaded"]:
        client.status = "active"
    db.commit()

    return ParserUploadResponse(
        report_id=db_report.id,
        negative_items=[
            NegativeItemSchema(
                id=str(item.id),
                creditor=item.creditor_name,
                amount=item.balance or 0.0,
                bureau=item.bureau,
                status=item.negative_type
            )
            for item in db_items
        ]
    )

@router.get("/reports", response_model=List[ReportResponse])
def list_credit_reports(
    client_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "client":
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client profile not found")
        reports = db.query(CreditReport).filter(CreditReport.client_id == client.id).all()
    elif current_user.role == "agency":
        if client_id:
            client = db.query(Client).filter(
                Client.id == client_id,
                Client.agency_id == current_user.agency_profile.id
            ).first()
            if not client:
                raise HTTPException(status_code=403, detail="Client does not belong to your agency")
            reports = db.query(CreditReport).filter(CreditReport.client_id == client_id).all()
        else:
            reports = db.query(CreditReport).join(Client).filter(
                Client.agency_id == current_user.agency_profile.id
            ).all()
    else:
        raise HTTPException(status_code=403, detail="Unauthorized role")

    return [
        ReportResponse(
            report_id=r.id,
            filename=r.filename,
            uploaded_at=r.uploaded_at
        )
        for r in reports
    ]
