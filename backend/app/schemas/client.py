from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class AgencyProfileSchema(BaseModel):
    id: int
    company_name: str
    name: Optional[str] = None  # Alias for company_name
    phone: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClientProfileSchema(BaseModel):
    id: int
    user_id: int
    agency_id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: str
    onboarding_step: str
    signed_agreement: bool
    signed_at: Optional[datetime] = None
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)

class UserMeResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    agency_profile: Optional[AgencyProfileSchema] = None
    agency: Optional[AgencyProfileSchema] = None
    client_profile: Optional[ClientProfileSchema] = None
    client: Optional[ClientProfileSchema] = None

    model_config = ConfigDict(from_attributes=True)

class ClientListItem(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    status: str
    onboarding_step: Optional[str] = None
    signed_agreement: Optional[bool] = False
    signed_at: Optional[datetime] = None
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)

class AgencyMetrics(BaseModel):
    total_clients: int
    dispute_success_rate: float
    simulated_billing: float
    dispute_metrics: dict
    billing_summary: dict
    agency_id: int
    metrics: dict

class ClientStatus(BaseModel):
    client_id: int
    status: str
    updated_at: datetime
    onboarding_step: Optional[str] = None
    onboarding_steps: Optional[dict] = None
    signed_agreement: Optional[bool] = False
    signed_at: Optional[datetime] = None

    disputes_summary: Optional[dict] = None
    dispute_summary: Optional[dict] = None
    documents_uploaded: Optional[list] = None

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    document_type: str
    filename: str
    file_path: Optional[str] = None
    status: Optional[str] = None
    client_id: Optional[int] = None
    uploaded_at: datetime
