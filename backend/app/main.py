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

# Auto-create tables on startup (convenient for SQLite)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="B2B Credit Repair SaaS Backend", version="0.2.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(agency_router, prefix="/api/agency", tags=["Agency"])
app.include_router(client_router, prefix="/api/client", tags=["Client"])
app.include_router(parser_router, prefix="/api/parser", tags=["Parser"])
app.include_router(disputes_router, prefix="/api/disputes", tags=["Disputes"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(mailing_router, prefix="/api/mailing", tags=["Mailing"])

@app.get("/")
def read_root():
    return {"message": "B2B Credit Repair SaaS API is active"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
