from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models import Base
from app.api.auth import router as auth_router
from app.api.agency import router as agency_router
from app.api.client import router as client_router
from app.api.parser import router as parser_router

# Auto-create tables on startup (convenient for SQLite)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="B2B Credit Repair SaaS Backend", version="0.1.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(agency_router, prefix="/api/agency", tags=["Agency"])
app.include_router(client_router, prefix="/api/client", tags=["Client"])
app.include_router(parser_router, prefix="/api/parser", tags=["Parser"])

@app.get("/")
def read_root():
    return {"message": "B2B Credit Repair SaaS API is active"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
