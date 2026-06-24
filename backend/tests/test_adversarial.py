import os
import shutil
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db, Base
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.agency import Agency
from app.main import app

# Helper to setup and log in a client for isolated tests
def register_and_login_client(client, email="client_test@test.com"):
    # Register agency
    client.post("/api/auth/register", json={
        "email": f"agency_{email}",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Test Agency"
    })
    # Register client
    client.post("/api/auth/register", json={
        "email": email,
        "password": "testpassword123",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe",
        "agency_id": 1
    })
    # Login
    login = client.post("/api/auth/token", data={
        "username": email,
        "password": "testpassword123"
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# 1. JWT SECURITY BOUNDARY TESTS
# ==========================================

def test_invalid_jwt_format(client):
    """Verify that a malformed JWT string results in a 401 response."""
    headers = {"Authorization": "Bearer not-a-valid-token-string"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_expired_jwt(client):
    """Verify that an expired JWT results in a 401 response."""
    # Create token that expired 10 minutes ago
    expired_token = create_access_token(
        data={"sub": "1", "role": "agency"},
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_none_algorithm_jwt(client):
    """Verify that a JWT with 'none' algorithm is rejected (401)."""
    payload = {"sub": "1", "role": "agency", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    # Construct an unsigned token using the standard none algorithm
    token_none = jwt.encode(payload, key="", algorithm="none")
    headers = {"Authorization": f"Bearer {token_none}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_wrong_signature_jwt(client):
    """Verify that a JWT signed with a different key is rejected (401)."""
    payload = {"sub": "1", "role": "agency", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    wrong_token = jwt.encode(payload, "WRONG_SECRET_KEY", algorithm="HS256")
    headers = {"Authorization": f"Bearer {wrong_token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_jwt_nonexistent_user(client):
    """Verify that a valid token representing a non-existent user ID is rejected (401)."""
    # 99999 does not exist in memory DB
    token = create_access_token(data={"sub": "99999", "role": "agency"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


# ==========================================
# 2. FILE UPLOAD SECURITY & EDGE CASES
# ==========================================

def test_upload_empty_file(client):
    """Verify that uploading an empty (0-byte) file is rejected with 400 Bad Request."""
    headers = register_and_login_client(client, "empty_file_client@test.com")

    # Upload empty file
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    data = {"document_type": "address_proof"}
    
    response = client.post(
        "/api/client/upload",
        headers=headers,
        data=data,
        files=files
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_upload_large_file(client):
    """Verify that uploading a file <= 5MB succeeds, but > 5MB fails."""
    headers = register_and_login_client(client, "large_file_client@test.com")

    # 1. 1 MB of dummy text (should succeed)
    large_content = b"A" * 1024 * 1024
    files = {"file": ("large.txt", large_content, "text/plain")}
    data = {"document_type": "identity"}

    response = client.post(
        "/api/client/upload",
        headers=headers,
        data=data,
        files=files
    )
    assert response.status_code == 201
    res_data = response.json()
    file_path = res_data["file_path"]
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) == 1024 * 1024

    # Clean up file safely
    if os.path.exists(file_path):
        os.remove(file_path)

    # 2. 6 MB of dummy text (should fail)
    too_large_content = b"B" * 6 * 1024 * 1024
    files_too_large = {"file": ("too_large.txt", too_large_content, "text/plain")}
    response_too_large = client.post(
        "/api/client/upload",
        headers=headers,
        data=data,
        files=files_too_large
    )
    assert response_too_large.status_code == 400
    assert "exceeds" in response_too_large.json()["detail"]

    # Clean up directory safely
    client_dir = os.path.dirname(file_path)
    shutil.rmtree(client_dir, ignore_errors=True)

def test_upload_path_traversal_filename(client):
    """Verify that filename containing directory traversal sequences is sanitized."""
    headers = register_and_login_client(client, "traversal_file_client@test.com")

    # Traversing filename
    files = {"file": ("../../etc/passwd", b"malicious content", "text/plain")}
    data = {"document_type": "other"}

    response = client.post(
        "/api/client/upload",
        headers=headers,
        data=data,
        files=files
    )
    assert response.status_code == 201
    res_data = response.json()
    # The path traversal characters '/' and '\' must be sanitized out
    # Filename input: "../../etc/passwd" -> sanitized should become "....etcpasswd" or similar without slashes
    saved_path = res_data["file_path"]
    filename_part = os.path.basename(saved_path)
    assert "/" not in filename_part
    assert "\\" not in filename_part
    assert "passwd" in filename_part

    # Clean up file and directory safely
    if os.path.exists(saved_path):
        os.remove(saved_path)
    client_dir = os.path.dirname(saved_path)
    shutil.rmtree(client_dir, ignore_errors=True)

def test_upload_path_traversal_document_type(client):
    """Verify that path traversal in document_type is rejected."""
    headers = register_and_login_client(client, "traversal_type_client@test.com")

    files = {"file": ("test.txt", b"content", "text/plain")}
    data = {"document_type": "../../../id_proof"}

    response = client.post(
        "/api/client/upload",
        headers=headers,
        data=data,
        files=files
    )
    assert response.status_code == 400
    assert "Invalid document type" in response.json()["detail"]


# ==========================================
# 3. INPUT VALIDATION & INJECTION TESTS
# ==========================================

def test_register_sql_injection(client):
    """Verify that email/password containing SQL injection payloads are handled safely."""
    # Attempting SQL injection in email field
    sql_injection_email = "victim@test.com' OR '1'='1"
    response = client.post("/api/auth/register", json={
        "email": sql_injection_email,
        "password": "testpassword123",
        "role": "agency",
        "company_name": "SQL Injection Corp"
    })
    # FastAPI/Pydantic email validator should catch this first and return 422
    assert response.status_code == 422

    # Attempting SQL injection in company name (valid email)
    sql_injection_company = "Agency'; DROP TABLE users;--"
    response2 = client.post("/api/auth/register", json={
        "email": "safe_email@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": sql_injection_company
    })
    assert response2.status_code == 201
    
    # Confirm user exists with the exact company name (it wasn't executed as SQL)
    login = client.post("/api/auth/token", data={
        "username": "safe_email@test.com",
        "password": "testpassword123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["agency"]["company_name"] == sql_injection_company

def test_register_malformed_json(client):
    """Verify that a malformed JSON payload returns a 400 or 422 error."""
    # Invalid JSON syntax
    headers = {"Content-Type": "application/json"}
    response = client.post("/api/auth/register", data="{ malformed: json, ", headers=headers)
    assert response.status_code in [400, 422]

def test_register_extreme_inputs(client):
    """Verify that very long inputs are handled safely."""
    long_company_name = "A" * 10000
    response = client.post("/api/auth/register", json={
        "email": "long_inputs@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": long_company_name
    })
    # SQLite does not strictly enforce VARCHAR length limits, so it should succeed
    assert response.status_code == 201

def test_register_long_password(client):
    """Verify that passwords longer than 72 bytes are correctly handled and verified by bcrypt."""
    long_password = "p" * 100  # 100 bytes long
    
    try:
        # Register agency
        response = client.post("/api/auth/register", json={
            "email": "long_pwd@test.com",
            "password": long_password,
            "role": "agency",
            "company_name": "Long Password Agency"
        })
        assert response.status_code in [201, 400, 422], f"Expected 201, 400, or 422, got {response.status_code}"
        
        # Login with the full 100 character password
        login_full = client.post("/api/auth/token", data={
            "username": "long_pwd@test.com",
            "password": long_password
        })
        assert login_full.status_code == 200
        assert "access_token" in login_full.json()
    except ValueError as e:
        # If it raised ValueError, this is a confirmed bug (500 internal server error in production)
        pytest.fail(f"Bug confirmed: ValueError raised in get_password_hash for long password (>72 bytes): {e}")


# ==========================================
# 4. CONCURRENCY & DATABASE LOCK TESTS
# ==========================================

def test_sqlite_lock_contention(tmp_path):
    """Verify that concurrent DB write sessions wait on SQLite lock instead of crashing, utilizing connection timeout."""
    db_file = tmp_path / "test_concurrency.db"
    db_url = f"sqlite:///{db_file}"
    
    # Create engine with 20 second timeout
    engine = create_engine(db_url, connect_args={"timeout": 20})
    
    # Enforce foreign keys in SQLite for test engine
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    def create_user_task(user_id):
        session = SessionLocal()
        try:
            user = User(
                email=f"user_concur_{user_id}@test.com",
                hashed_password=get_password_hash("password123"),
                role="client",
                is_active=True
            )
            session.add(user)
            # Try to commit - under concurrency, SQLite might lock, but connect_args timeout=20 will make threads wait
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return e
        finally:
            session.close()
            
    num_threads = 15
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(create_user_task, range(num_threads)))
        
    for r in results:
        assert r is True, f"Concurrency test failed with exception: {r}"

def test_concurrent_api_requests_real_db(tmp_path):
    """Verify that concurrent API requests on different database sessions succeed under load."""
    original_db_url = settings.DATABASE_URL
    
    temp_db_file = tmp_path / "temp_api_concur.db"
    settings.DATABASE_URL = f"sqlite:///{temp_db_file}"
    
    # Re-initialize engine
    test_engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 20}
    )
    
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    test_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    def override_get_db():
        db = test_SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    api_client = TestClient(app)
    
    # 1. Register the agency first (synchronously)
    agency_resp = api_client.post("/api/auth/register", json={
        "email": "agency_api_concur@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "API Concur Agency"
    })
    assert agency_resp.status_code == 201
    
    # 2. Register multiple clients concurrently
    def register_client_task(i):
        response = api_client.post("/api/auth/register", json={
            "email": f"api_concur_client_{i}@test.com",
            "password": "testpassword123",
            "role": "client",
            "first_name": f"First_{i}",
            "last_name": f"Last_{i}",
            "agency_id": 1
        })
        return response.status_code
        
    num_requests = 10
    with ThreadPoolExecutor(max_workers=5) as executor:
        status_codes = list(executor.map(register_client_task, range(num_requests)))
        
    # Clean up overrides and restore database url settings
    app.dependency_overrides.clear()
    settings.DATABASE_URL = original_db_url
    
    for code in status_codes:
        assert code == 201
