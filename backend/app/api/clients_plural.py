from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.client import Client
from app.models.agency import Agency
from app.models.credit_report import CreditReport
from app.models.document import ClientDocument
from app.schemas.client import ClientListItem
from pydantic import BaseModel
from app.core.security import get_password_hash
from datetime import datetime, timezone

router = APIRouter()

class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    dob: Optional[str] = None
    ssn_last4: Optional[str] = None

class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None

class ClientDetailResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: str
    onboarding_step: str
    created_at: datetime

@router.get("", response_model=List[ClientListItem])
def list_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "agency":
        agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
        if not agency:
            return []
        clients = db.query(Client).filter(Client.agency_id == agency.id).all()
    elif current_user.role == "client":
        clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    else:
        return []

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

@router.get("/{client_id}", response_model=ClientDetailResponse)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    if current_user.role == "agency":
        agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
        if not agency or client.agency_id != agency.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == "client":
        if client.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    return ClientDetailResponse(
        id=client.id,
        email=client.user.email if client.user else "",
        first_name=client.first_name,
        last_name=client.last_name,
        phone=client.phone,
        status=client.status,
        onboarding_step=client.onboarding_step,
        created_at=client.created_at
    )

@router.post("", response_model=ClientDetailResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency profile not found")

    hashed_pwd = get_password_hash("Password123!")
    user = User(
        email=body.email,
        hashed_password=hashed_pwd,
        role="client",
        is_active=True
    )
    db.add(user)
    db.flush()

    client = Client(
        user_id=user.id,
        agency_id=agency.id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        status="onboarding",
        onboarding_step="document_upload"
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return ClientDetailResponse(
        id=client.id,
        email=user.email,
        first_name=client.first_name,
        last_name=client.last_name,
        phone=client.phone,
        status=client.status,
        onboarding_step=client.onboarding_step,
        created_at=client.created_at
    )

@router.put("/{client_id}", response_model=ClientDetailResponse)
def update_client(
    client_id: int,
    body: ClientUpdate,
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
    if not agency or client.agency_id != agency.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if body.first_name is not None:
        client.first_name = body.first_name
    if body.last_name is not None:
        client.last_name = body.last_name
    if body.phone is not None:
        client.phone = body.phone
    if body.status is not None:
        client.status = body.status
        
    db.commit()
    db.refresh(client)

    return ClientDetailResponse(
        id=client.id,
        email=client.user.email if client.user else "",
        first_name=client.first_name,
        last_name=client.last_name,
        phone=client.phone,
        status=client.status,
        onboarding_step=client.onboarding_step,
        created_at=client.created_at
    )

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    current_user: User = Depends(RoleChecker(["agency"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    agency = db.query(Agency).filter(Agency.user_id == current_user.id).first()
    if not agency or client.agency_id != agency.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = client.user
    db.delete(client)
    if user:
        db.delete(user)
    db.commit()
    return None

@router.get("/{client_id}/timeline")
def get_client_timeline(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    timeline = [
        {"id": 1, "title": "Client Registered", "description": "Profile created in CreditEngine", "date": client.created_at.isoformat(), "icon": "👤"}
    ]
    if client.onboarding_step in ["document_uploaded", "report_parsed", "active"]:
        timeline.append({"id": 2, "title": "Documents Uploaded", "description": "ID and address proofs verified", "date": client.updated_at.isoformat(), "icon": "📁"})
    
    reports = db.query(CreditReport).filter(CreditReport.client_id == client.id).all()
    for i, r in enumerate(reports):
        timeline.append({
            "id": 10 + i,
            "title": f"Credit Report Uploaded ({r.filename})",
            "description": "System extracted negative items successfully",
            "date": r.uploaded_at.isoformat(),
            "icon": "📋"
        })
        
    timeline.sort(key=lambda x: x["date"], reverse=True)
    return timeline

@router.get("/{client_id}/reports")
def get_client_reports(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    reports = db.query(CreditReport).filter(CreditReport.client_id == client_id).all()
    return [
        {
            "report_id": r.id,
            "filename": r.filename,
            "uploaded_at": r.uploaded_at.isoformat()
        }
        for r in reports
    ]

@router.get("/{client_id}/documents")
def get_client_documents(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    docs = db.query(ClientDocument).filter(ClientDocument.client_id == client_id).all()
    return [
        {
            "id": d.id,
            "document_type": d.document_type,
            "filename": d.filename,
            "uploaded_at": d.uploaded_at.isoformat()
        }
        for d in docs
    ]
