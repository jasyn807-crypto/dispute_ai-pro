"""
Document upload API router (agency-side).

Endpoints:
- POST /api/documents/upload              – Upload identity document for a client
- GET  /api/documents/clients/{id}/documents  – List documents for a client
"""

import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.client import Client
from app.models.document import ClientDocument
from app.schemas.client import DocumentUploadResponse

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploads/documents"


class DocumentListItem(BaseModel):
    id: int
    client_id: int
    document_type: str
    filename: str
    file_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── POST /api/documents/upload ─────────────────────────────────────────────

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document_for_client(
    client_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an identity document for a specific client.
    Agency staff provides the client_id via form data.
    """
    allowed_types = ["id_proof", "address_proof", "identity", "address", "ssn_card",
                     "utility_bill", "other"]
    if document_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Allowed types: {allowed_types}",
        )

    # Validate file
    file_size = file.size
    if file_size is None:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploads are not allowed.")
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 5MB limit.")

    # Verify client belongs to agency
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if current_user.role == "agency":
        if not current_user.agency_profile or client.agency_id != current_user.agency_profile.id:
            raise HTTPException(status_code=403, detail="Client does not belong to your agency")

    # Save file
    client_dir = os.path.join(UPLOAD_DIR, f"client_{client.id}")
    os.makedirs(client_dir, exist_ok=True)

    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._-"])
    file_path = os.path.join(client_dir, f"{document_type}_{safe_filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    doc = ClientDocument(
        client_id=client.id,
        document_type=document_type,
        filename=file.filename,
        file_path=file_path,
    )
    db.add(doc)
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
        uploaded_at=doc.uploaded_at,
    )


# ── GET /api/documents/clients/{client_id}/documents ───────────────────────

@router.get("/clients/{client_id}/documents", response_model=List[DocumentListItem])
def list_client_documents(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all documents for a given client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Authorization
    if current_user.role == "agency":
        if not current_user.agency_profile or client.agency_id != current_user.agency_profile.id:
            raise HTTPException(status_code=403, detail="Client does not belong to your agency")
    elif current_user.role == "client":
        if client.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    docs = db.query(ClientDocument).filter(ClientDocument.client_id == client_id).all()
    return [
        DocumentListItem(
            id=d.id,
            client_id=d.client_id,
            document_type=d.document_type,
            filename=d.filename,
            file_path=d.file_path,
            uploaded_at=d.uploaded_at,
        )
        for d in docs
    ]
