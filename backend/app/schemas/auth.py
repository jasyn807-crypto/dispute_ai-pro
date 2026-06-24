from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str
    company_name: Optional[str] = None
    agency_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    agency_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_role_fields(self):
        role_val = self.role.lower() if self.role else ""
        if role_val == "agency":
            name = self.company_name or self.agency_name
            if not name or not name.strip():
                raise ValueError("Company name is required for agency registration")
            if not self.company_name:
                self.company_name = name
        elif role_val == "client":
            if not self.first_name or not self.first_name.strip():
                raise ValueError("First name is required for client registration")
            if not self.last_name or not self.last_name.strip():
                raise ValueError("Last name is required for client registration")
            if self.agency_id is None:
                raise ValueError("Agency ID is required for client registration")
        else:
            raise ValueError("Role must be either 'agency' or 'client'")
        return self

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
