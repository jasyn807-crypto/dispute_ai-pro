from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.agency import Agency
from app.models.client import Client
from app.schemas.auth import UserRegister, Token, UserResponse
from app.schemas.client import UserMeResponse, AgencyProfileSchema, ClientProfileSchema

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # 1. Check if email already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    role_lower = user_in.role.lower()

    # 2. Role-specific validation
    if role_lower == "agency":
        company_name = user_in.company_name or user_in.agency_name
        if not company_name or not company_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is required for agency registration"
            )
    elif role_lower == "client":
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
        # Check if agency exists
        agency = db.query(Agency).filter(Agency.id == user_in.agency_id).first()
        if not agency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agency with ID {user_in.agency_id} does not exist"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Role must be 'agency' or 'client'"
        )

    # 3. Create User
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=role_lower,
        is_active=True
    )
    db.add(user)
    db.flush()  # Populate user.id

    # 4. Create Profile
    if role_lower == "agency":
        company_name = user_in.company_name or user_in.agency_name
        profile = Agency(
            user_id=user.id,
            company_name=company_name,
            phone=user_in.phone
        )
        db.add(profile)
    else:
        profile = Client(
            user_id=user.id,
            agency_id=user_in.agency_id,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone=user_in.phone,
            status="onboarding",
            onboarding_step="document_upload"
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # We store both ID and email as sub to be compatible, let's store ID (as string)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    # Prepare response data with both styles of profiles (agency/agency_profile, client/client_profile)
    agency_profile = None
    client_profile = None

    if current_user.role == "agency" and current_user.agency_profile:
        agency_profile = AgencyProfileSchema(
            id=current_user.agency_profile.id,
            company_name=current_user.agency_profile.company_name,
            name=current_user.agency_profile.company_name,
            phone=current_user.agency_profile.phone,
            created_at=current_user.agency_profile.created_at
        )
    elif current_user.role == "client" and current_user.client_profile:
        client_profile = ClientProfileSchema(
            id=current_user.client_profile.id,
            user_id=current_user.client_profile.user_id,
            agency_id=current_user.client_profile.agency_id,
            first_name=current_user.client_profile.first_name,
            last_name=current_user.client_profile.last_name,
            phone=current_user.client_profile.phone,
            status=current_user.client_profile.status,
            onboarding_step=current_user.client_profile.onboarding_step,
            created_at=current_user.client_profile.created_at
        )

    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        agency_profile=agency_profile,
        agency=agency_profile,
        client_profile=client_profile,
        client=client_profile
    )
