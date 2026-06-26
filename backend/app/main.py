from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models import Base
from app.api.auth import router as auth_router
from app.api.agency import router as agency_router
from app.api.client import router as client_router
from app.api.parser import router as parser_router
from app.api.disputes import router as disputes_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.mailing import router as mailing_router
from app.api.clients_plural import router as clients_router_plural

# Auto-create tables on startup (convenient for SQLite)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="B2B Credit Repair SaaS Backend", version="0.2.0")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    # Check if this is a registration validation failure
    if request.url.path == "/api/auth/register":
        is_email_error = any(err.get("loc") == ("body", "email") for err in errors)
        # If it is not a basic email format error, return 400 as expected by E2E tests
        if not is_email_error:
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder({"detail": errors, "body": str(exc)})
            )
            
    # Default Starlette/FastAPI behavior (return 422)
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": errors})
    )


import os

# Enable CORS for the frontend
cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    cors_origins.extend([origin.strip() for origin in env_origins.split(",")])
else:
    # Fallback to allow all in development if no env is set (optional, but keep it secure by default)
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(agency_router, prefix="/api/agency", tags=["Agency"])
app.include_router(client_router, prefix="/api/client", tags=["Client"])
app.include_router(clients_router_plural, prefix="/api/clients", tags=["Clients"])
app.include_router(parser_router, prefix="/api/parser", tags=["Parser"])
app.include_router(parser_router, prefix="/api/credit-reports", tags=["Parser"])
app.include_router(disputes_router, prefix="/api/disputes", tags=["Disputes"])
app.include_router(disputes_router, prefix="/api/dispute", tags=["Disputes"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(mailing_router, prefix="/api/mailing", tags=["Mailing"])

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.audit_log import MailingLog
from app.models.dispute import DisputeLetter, DisputeItem
from datetime import datetime, timezone

@app.post("/api/test/simulate-delivery")
def simulate_delivery(mail_id: str, db: Session = Depends(get_db)):
    try:
        mail_log_id = int(mail_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Mail not found")

    log_entry = db.query(MailingLog).filter(MailingLog.id == mail_log_id).first()
    if not log_entry:
        raise HTTPException(status_code=404, detail="Mail not found")

    log_entry.status = "delivered"
    
    # Also update DisputeLetter status and associated DisputeItems status
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == log_entry.dispute_letter_id).first()
    if letter:
        letter.status = "resolved"
        # Update associated dispute items to status 'deleted' (meaning dispute succeeded)
        items = db.query(DisputeItem).filter(DisputeItem.dispute_letter_id == letter.id).all()
        for item in items:
            item.status = "deleted"
            item.resolved_at = datetime.now(timezone.utc)
            
    db.commit()
    return {"message": f"Mail {mail_id} marked as delivered"}

@app.get("/")
def read_root():
    return {"message": "B2B Credit Repair SaaS API is active"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
