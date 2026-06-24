import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.user import User, UserRole
from app.models.client import Client
from app.models.document import ClientDocument
from app.models.dispute import DisputeItem
from app.models.credit_report import CreditReport
from app.schemas.client import ClientStatus, DocumentUploadResponse

router = APIRouter()

UPLOAD_DIR = "uploads/documents"

@router.get("/status", response_model=ClientStatus)
def get_status(
    current_user: User = Depends(RoleChecker(["client"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )

    documents = db.query(ClientDocument).filter(ClientDocument.client_id == client.id).all()

    # Determine if identity and address proofs have been uploaded
    has_id_proof = any(d.document_type in ["id_proof", "identity"] for d in documents)
    has_address_proof = any(d.document_type in ["address_proof", "address"] for d in documents)

    # Dispute item summary
    total_disputed = db.query(DisputeItem).filter(DisputeItem.client_id == client.id).count()
    pending = db.query(DisputeItem).filter(DisputeItem.client_id == client.id, DisputeItem.status == "pending").count()
    deleted = db.query(DisputeItem).filter(DisputeItem.client_id == client.id, DisputeItem.status == "deleted").count()
    verified = db.query(DisputeItem).filter(DisputeItem.client_id == client.id, DisputeItem.status == "verified").count()

    has_report = db.query(CreditReport).filter(CreditReport.client_id == client.id).count() > 0

    onboarding_steps = {
        "identity_uploaded": has_id_proof,
        "address_uploaded": has_address_proof,
        "report_parsed": has_report
    }

    disputes_summary = {
        "total": total_disputed,
        "pending": pending,
        "deleted": deleted,
        "verified": verified
    }

    dispute_summary = {
        "total_disputes": total_disputed,
        "in_progress": pending,
        "resolved": deleted + verified
    }

    docs_uploaded = [
        {
            "id": doc.id,
            "document_type": doc.document_type,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at
        }
        for doc in documents
    ]

    return ClientStatus(
        client_id=client.id,
        status=client.status,
        updated_at=client.updated_at,
        onboarding_step=client.onboarding_step,
        onboarding_steps=onboarding_steps,
        disputes_summary=disputes_summary,
        dispute_summary=dispute_summary,
        documents_uploaded=docs_uploaded
    )

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(RoleChecker(["client"])),
    db: Session = Depends(get_db)
):
    allowed_types = ["id_proof", "address_proof", "identity", "address", "other"]
    if document_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Allowed types: {allowed_types}"
        )

    # Determine file size
    file_size = file.size
    if file_size is None:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploads are not allowed."
        )

    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit."
        )

    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )

    client_dir = os.path.join(UPLOAD_DIR, f"client_{client.id}")
    os.makedirs(client_dir, exist_ok=True)

    # Clean filename to avoid directory traversal or injection
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._-"])
    file_path = os.path.join(client_dir, f"{document_type}_{safe_filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create document record
    doc = ClientDocument(
        client_id=client.id,
        document_type=document_type,
        filename=file.filename,
        file_path=file_path
    )
    db.add(doc)

    # Update client onboarding progress and status
    if client.onboarding_step == "document_upload":
        client.onboarding_step = "document_uploaded"
    if client.status == "onboarding":
        client.status = "documents_uploaded"

    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        message="Document uploaded successfully",
        document_id=doc.id,
        document_type=doc.document_type,
        filename=doc.filename,
        file_path=doc.file_path,
        status=client.status,
        client_id=client.id,
        uploaded_at=doc.uploaded_at
    )
