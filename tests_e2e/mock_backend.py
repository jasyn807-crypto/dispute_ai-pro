import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import uuid
import datetime

app = FastAPI(title="Credit Repair SaaS Mock E2E Backend")

# Solid In-Memory Database
USERS: Dict[int, Dict[str, Any]] = {}
AGENCIES: Dict[int, Dict[str, Any]] = {}
CLIENTS: Dict[int, Dict[str, Any]] = {}
REPORTS: Dict[str, Dict[str, Any]] = {}
LETTERS: Dict[str, Dict[str, Any]] = {}
MAILS: Dict[str, Dict[str, Any]] = {}
DOCUMENTS: Dict[int, Dict[str, Any]] = {}

# Sequence Counters
user_seq = 1
agency_seq = 1
client_seq = 1
doc_seq = 1

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Pydantic Schemas matching PROJECT.md interface and handoff definitions
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str  # "agency" or "client"
    username: Optional[str] = None
    company_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    agency_id: Optional[int] = None

class AgencyProfileSchema(BaseModel):
    id: int
    company_name: str
    phone: Optional[str] = None
    created_at: str

class ClientProfileSchema(BaseModel):
    id: int
    user_id: int
    agency_id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: str
    onboarding_step: str
    created_at: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: str

class UserMeResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: str
    agency: Optional[AgencyProfileSchema] = None
    client: Optional[ClientProfileSchema] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class ClientStatusResponse(BaseModel):
    client_id: int
    status: str
    onboarding_step: str
    disputes_summary: Dict[str, int]
    documents_uploaded: List[Dict[str, Any]]

class NegativeItem(BaseModel):
    id: str
    creditor: str
    amount: float
    bureau: str
    status: str

class ParserUploadResponse(BaseModel):
    report_id: str
    negative_items: List[NegativeItem]

class ReportResponse(BaseModel):
    report_id: str
    filename: str
    uploaded_at: str

class DisputeGenerateRequest(BaseModel):
    report_id: str
    item_ids: List[str]
    reason: str

class DisputeGenerateResponse(BaseModel):
    letter_id: str
    content: str

class DisputeComplianceRequest(BaseModel):
    letter_content: str

class DisputeComplianceResponse(BaseModel):
    compliant: bool
    prohibited_claims_found: List[str]
    suggestions: str

class DisputeMailRequest(BaseModel):
    letter_id: str
    recipient_bureau: str

class DisputeMailResponse(BaseModel):
    mail_id: str
    status: str
    tracking_number: str

# Helper Functions
def get_user_by_email_or_username(login_name: str) -> Optional[Dict[str, Any]]:
    for u in USERS.values():
        if u["email"].lower() == login_name.lower():
            return u
        if u.get("username") and u["username"].lower() == login_name.lower():
            return u
    return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    if not token.startswith("mock-token-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = token.replace("mock-token-", "").split("-")
    if len(parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
        )
    try:
        user_id = int(parts[0])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token user ID",
        )
    
    if user_id not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return USERS[user_id]

def require_role(allowed_roles: List[str]):
    def dependency(current_user = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user
    return dependency

# Endpoints
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister):
    global user_seq, agency_seq, client_seq
    
    # 1. Email check
    if get_user_by_email_or_username(user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # 2. Username check (if provided)
    if user_in.username and get_user_by_email_or_username(user_in.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    # 3. Role validation
    if user_in.role not in ["agency", "client"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be 'agency' or 'client'")
        
    # 4. Role specific validations & database entry creation
    uid = user_seq
    user_seq += 1
    
    created_at_str = datetime.datetime.utcnow().isoformat()
    
    user_record = {
        "id": uid,
        "email": user_in.email,
        "username": user_in.username or user_in.email.split("@")[0],
        "password": user_in.password,
        "role": user_in.role,
        "is_active": True,
        "created_at": created_at_str
    }
    
    if user_in.role == "agency":
        if not user_in.company_name or not user_in.company_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is required for agency registration"
            )
        aid = agency_seq
        agency_seq += 1
        
        AGENCIES[aid] = {
            "id": aid,
            "user_id": uid,
            "company_name": user_in.company_name,
            "phone": user_in.phone,
            "created_at": created_at_str
        }
        USERS[uid] = user_record
        
    elif user_in.role == "client":
        if not user_in.first_name or not user_in.first_name.strip() or not user_in.last_name or not user_in.last_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="First name and last name are required for client registration"
            )
        if not user_in.agency_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agency ID is required for client registration"
            )
        if user_in.agency_id not in AGENCIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agency with ID {user_in.agency_id} does not exist"
            )
            
        cid = client_seq
        client_seq += 1
        
        CLIENTS[cid] = {
            "id": cid,
            "user_id": uid,
            "agency_id": user_in.agency_id,
            "first_name": user_in.first_name,
            "last_name": user_in.last_name,
            "phone": user_in.phone,
            "status": "onboarding",
            "onboarding_step": "document_upload",
            "created_at": created_at_str
        }
        USERS[uid] = user_record
        
    return UserResponse(
        id=uid,
        email=user_record["email"],
        role=user_record["role"],
        is_active=user_record["is_active"],
        created_at=user_record["created_at"]
    )

@app.post("/api/auth/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email_or_username(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email/username or password"
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Mock token format: mock-token-{id}-{role}
    token = f"mock-token-{user['id']}-{user['role']}"
    return TokenResponse(access_token=token, role=user["role"])

@app.get("/api/auth/me", response_model=UserMeResponse)
def get_me(current_user = Depends(get_current_user)):
    agency_profile = None
    client_profile = None
    
    if current_user["role"] == "agency":
        for a in AGENCIES.values():
            if a["user_id"] == current_user["id"]:
                agency_profile = AgencyProfileSchema(**a)
                break
    elif current_user["role"] == "client":
        for c in CLIENTS.values():
            if c["user_id"] == current_user["id"]:
                client_profile = ClientProfileSchema(**c)
                break
                
    return UserMeResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        agency=agency_profile,
        client=client_profile
    )

@app.get("/api/agency/clients", response_model=List[ClientProfileSchema])
def list_clients(current_user = Depends(require_role(["agency"]))):
    # Find agency profile
    agency = None
    for a in AGENCIES.values():
        if a["user_id"] == current_user["id"]:
            agency = a
            break
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency profile not found")
        
    # Return all clients linked to this agency
    res = []
    for c in CLIENTS.values():
        if c["agency_id"] == agency["id"]:
            res.append(ClientProfileSchema(**c))
    return res

@app.get("/api/agency/metrics")
def get_agency_metrics(current_user = Depends(require_role(["agency"]))):
    # Find agency profile
    agency = None
    for a in AGENCIES.values():
        if a["user_id"] == current_user["id"]:
            agency = a
            break
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency profile not found")
        
    # Gather metrics based on agency's clients
    agency_clients = [c for c in CLIENTS.values() if c["agency_id"] == agency["id"]]
    active_clients_count = sum(1 for c in agency_clients if c["status"] == "active")
    
    # Calculate totals
    total_disputes = 0
    resolved_disputes = 0
    deleted_disputes = 0
    
    # Filter mails based on letters belonging to reports of this agency's clients
    client_ids = [c["id"] for c in agency_clients]
    
    for mail in MAILS.values():
        letter_id = mail["letter_id"]
        letter = LETTERS.get(letter_id)
        if letter:
            report_id = letter["report_id"]
            report = REPORTS.get(report_id)
            if report and report["client_id"] in client_ids:
                total_disputes += 1
                if mail["status"] == "delivered":
                    resolved_disputes += 1
                    deleted_disputes += 1  # Simulate success in mock
                    
    success_rate = round(deleted_disputes / resolved_disputes, 2) if resolved_disputes > 0 else 0.0
    
    # Billing
    mrr = active_clients_count * 99.0
    pending_invoice = len(agency_clients) * 99.0 - mrr
    
    return {
        "dispute_metrics": {
            "total_disputed": total_disputes,
            "pending": total_disputes - resolved_disputes,
            "deleted": deleted_disputes,
            "verified": 0,
            "success_rate": success_rate
        },
        "billing_summary": {
            "active_clients_count": active_clients_count,
            "monthly_recurring_revenue": mrr,
            "pending_invoice_amount": pending_invoice,
            "payment_history": []
        }
    }

@app.get("/api/client/status", response_model=ClientStatusResponse)
def get_client_status(current_user = Depends(require_role(["client"]))):
    client = None
    for c in CLIENTS.values():
        if c["user_id"] == current_user["id"]:
            client = c
            break
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found")
        
    # Get client's documents
    client_docs = [doc for doc in DOCUMENTS.values() if doc["client_id"] == client["id"]]
    
    # Get client's reports and count disputes
    client_reports = [r for r in REPORTS.values() if r["client_id"] == client["id"]]
    report_ids = [r["report_id"] for r in client_reports]
    
    total_disputes = 0
    resolved_disputes = 0
    
    for mail in MAILS.values():
        letter_id = mail["letter_id"]
        letter = LETTERS.get(letter_id)
        if letter and letter["report_id"] in report_ids:
            total_disputes += 1
            if mail["status"] == "delivered":
                resolved_disputes += 1
                
    return ClientStatusResponse(
        client_id=client["id"],
        status=client["status"],
        onboarding_step=client["onboarding_step"],
        disputes_summary={
            "total": total_disputes,
            "pending": total_disputes - resolved_disputes,
            "deleted": resolved_disputes,
            "verified": 0
        },
        documents_uploaded=client_docs
    )

@app.post("/api/client/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user = Depends(require_role(["client"]))
):
    global doc_seq
    
    # Validate document_type
    allowed_types = ["id_proof", "address_proof"]
    if document_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Allowed types: {allowed_types}"
        )
        
    # Validate client exists
    client = None
    for c in CLIENTS.values():
        if c["user_id"] == current_user["id"]:
            client = c
            break
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found")
        
    # Boundary: empty file validation
    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
        
    did = doc_seq
    doc_seq += 1
    
    doc_record = {
        "id": did,
        "client_id": client["id"],
        "document_type": document_type,
        "filename": file.filename,
        "file_path": f"./uploads/documents/client_{client['id']}/{document_type}_{file.filename}",
        "uploaded_at": datetime.datetime.utcnow().isoformat()
    }
    DOCUMENTS[did] = doc_record
    
    # State update: update onboarding_step and status
    client["onboarding_step"] = "document_uploaded"
    
    # If both id_proof and address_proof are uploaded, update status to active and step to completed
    uploaded_types = {d["document_type"] for d in DOCUMENTS.values() if d["client_id"] == client["id"]}
    if "id_proof" in uploaded_types and "address_proof" in uploaded_types:
        client["status"] = "active"
        client["onboarding_step"] = "completed"
        
    return {
        "document_id": did,
        "document_type": document_type,
        "filename": file.filename,
        "message": "Document uploaded successfully",
        "uploaded_at": doc_record["uploaded_at"]
    }

@app.post("/api/parser/upload", response_model=ParserUploadResponse)
async def parse_credit_report(
    report: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Boundary: empty file validation
    content = await report.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
        
    # Get client_id
    client_id = None
    if current_user["role"] == "client":
        for c in CLIENTS.values():
            if c["user_id"] == current_user["id"]:
                client_id = c["id"]
                break
    else:
        # Mock default client_id for non-client (e.g. agency parser utility)
        client_id = 1
        
    report_id = str(uuid.uuid4())
    negative_items = [
        NegativeItem(
            id=f"item_{report_id}_1",
            creditor="ACME Collections",
            amount=500.0,
            bureau="Equifax",
            status="delinquent"
        ),
        NegativeItem(
            id=f"item_{report_id}_2",
            creditor="Late Pay Co",
            amount=120.0,
            bureau="Experian",
            status="delinquent"
        ),
        NegativeItem(
            id=f"item_{report_id}_3",
            creditor="TransUnion ChargeOff",
            amount=1500.0,
            bureau="TransUnion",
            status="charge_off"
        )
    ]
    
    REPORTS[report_id] = {
        "report_id": report_id,
        "client_id": client_id,
        "filename": report.filename,
        "uploaded_at": datetime.datetime.utcnow().isoformat(),
        "negative_items": [item.dict() for item in negative_items]
    }
    
    return ParserUploadResponse(
        report_id=report_id,
        negative_items=negative_items
    )

@app.get("/api/parser/reports", response_model=List[ReportResponse])
def get_reports(current_user = Depends(get_current_user)):
    client_id = None
    if current_user["role"] == "client":
        for c in CLIENTS.values():
            if c["user_id"] == current_user["id"]:
                client_id = c["id"]
                break
    
    res = []
    for r in REPORTS.values():
        if client_id is None or r["client_id"] == client_id:
            res.append(ReportResponse(
                report_id=r["report_id"],
                filename=r["filename"],
                uploaded_at=r["uploaded_at"]
            ))
    return res

@app.post("/api/dispute/generate", response_model=DisputeGenerateResponse)
def generate_dispute_letter(
    req: DisputeGenerateRequest,
    current_user = Depends(get_current_user)
):
    # Boundary validation
    if req.report_id not in REPORTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if not req.item_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item IDs cannot be empty")
        
    report = REPORTS[req.report_id]
    item_map = {item["id"]: item for item in report["negative_items"]}
    
    for iid in req.item_ids:
        if iid not in item_map:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item {iid} not found in report")
            
    letter_id = str(uuid.uuid4())
    content = f"Dear Credit Bureau,\n\nI am disputing the following entries:\n"
    for iid in req.item_ids:
        item = item_map[iid]
        content += f"- Creditor: {item['creditor']}, Amount: ${item['amount']}, Bureau: {item['bureau']} (ID: {iid}). Reason: {req.reason}\n"
    content += "\nPlease verify and delete if incorrect.\n"
    
    LETTERS[letter_id] = {
        "letter_id": letter_id,
        "report_id": req.report_id,
        "item_ids": req.item_ids,
        "content": content,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    return DisputeGenerateResponse(
        letter_id=letter_id,
        content=content
    )

@app.post("/api/dispute/compliance", response_model=DisputeComplianceResponse)
def check_compliance(
    req: DisputeComplianceRequest,
    current_user = Depends(get_current_user)
):
    content_lower = req.letter_content.lower()
    prohibited_keywords = ["guarantee deletion", "100% legal trick", "clean credit in 24 hours"]
    prohibited_found = []
    
    for kw in prohibited_keywords:
        if kw in content_lower:
            prohibited_found.append(kw)
            
    is_compliant = len(prohibited_found) == 0
    suggestions = (
        "Looks good!" if is_compliant 
        else f"Prohibited statements found. Please remove references to: {', '.join(prohibited_found)}"
    )
    
    return DisputeComplianceResponse(
        compliant=is_compliant,
        prohibited_claims_found=prohibited_found,
        suggestions=suggestions
    )

@app.post("/api/dispute/mail", response_model=DisputeMailResponse)
def mail_dispute_letter(
    req: DisputeMailRequest,
    current_user = Depends(get_current_user)
):
    if req.letter_id not in LETTERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute letter not found")
        
    allowed_bureaus = ["Equifax", "Experian", "TransUnion"]
    if req.recipient_bureau not in allowed_bureaus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid bureau. Allowed: {allowed_bureaus}"
        )
        
    mail_id = f"mail_{str(uuid.uuid4())[:8]}"
    tracking_number = f"USPS-LOB-{str(uuid.uuid4().int)[:10]}"
    
    MAILS[mail_id] = {
        "mail_id": mail_id,
        "letter_id": req.letter_id,
        "recipient_bureau": req.recipient_bureau,
        "status": "queued",
        "tracking_number": tracking_number,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    return DisputeMailResponse(
        mail_id=mail_id,
        status="queued",
        tracking_number=tracking_number
    )

# Helper route for E2E testing to simulate USPS delivery status updates
@app.post("/api/test/simulate-delivery")
def simulate_delivery(mail_id: str):
    if mail_id not in MAILS:
        raise HTTPException(status_code=404, detail="Mail not found")
    MAILS[mail_id]["status"] = "delivered"
    return {"message": f"Mail {mail_id} marked as delivered"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
