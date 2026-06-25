import pytest
import subprocess
import time
import sys
import os
import socket
import httpx

def pytest_addoption(parser):
    parser.addoption(
        "--backend-url",
        action="store",
        default=None,
        help="Base URL of the running backend. If not provided, the mock backend will be automatically launched."
    )

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

@pytest.fixture(scope="session")
def backend_url(pytestconfig):
    url = pytestconfig.getoption("--backend-url")
    if url:
        yield url.rstrip('/')
        return

    # Auto-launch the mock backend
    host = "127.0.0.1"
    port = 8000
    base_url = f"http://{host}:{port}"
    
    if is_port_in_use(host, port):
        # A backend (mock or real) is already running on port 8000
        print(f"\n[E2E] Port {port} is already in use. Assuming backend is running at {base_url}.")
        yield base_url
        return

    # Start mock_backend.py as a subprocess using the current Python executable
    mock_backend_path = os.path.join(os.path.dirname(__file__), "mock_backend.py")
    if not os.path.exists(mock_backend_path):
        mock_backend_path = os.path.join(os.getcwd(), "credit_repair_saas", "tests_e2e", "mock_backend.py")
        
    print(f"\n[E2E] Starting mock backend from {mock_backend_path}...")
    
    mock_backend_log_path = os.path.join(os.path.dirname(__file__), "mock_backend.log")
    log_file = open(mock_backend_log_path, "w", encoding="utf-8")
    
    # Run the mock backend
    process = subprocess.Popen(
        [sys.executable, mock_backend_path],
        stdout=log_file,
        stderr=log_file,
        text=True
    )
    
    # Wait for the backend to become healthy
    health_url = f"{base_url}/health"
    timeout = 10
    start_time = time.time()
    healthy = False
    
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            log_file.close()
            with open(mock_backend_log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            raise RuntimeError(f"Mock backend process terminated early with code {process.returncode}. Log: {log_content}")
            
        try:
            response = httpx.get(health_url, timeout=1.0)
            if response.status_code == 200 and response.json().get("status") == "ok":
                healthy = True
                break
        except httpx.RequestError:
            pass
        time.sleep(0.5)
        
    if not healthy:
        process.terminate()
        process.wait()
        log_file.close()
        raise TimeoutError(f"Mock backend failed to start and pass healthcheck within {timeout} seconds.")
        
    print(f"[E2E] Mock backend is running and healthy at {base_url}!")
    
    yield base_url
    
    # Teardown: terminate mock backend process
    print("\n[E2E] Stopping mock backend...")
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    log_file.close()
    print("[E2E] Mock backend stopped.")

@pytest.fixture(scope="session")
def public_client(backend_url):
    """Client for unauthenticated public requests."""
    with httpx.Client(base_url=backend_url, timeout=5.0) as client:
        yield client

@pytest.fixture
def agency_client(backend_url):
    """Client authenticated as an Agency user."""
    timestamp = int(time.time() * 1000)
    username = f"agency_{timestamp}"
    password = f"AgencyPassword{timestamp}!"
    email = f"{username}@agency.com"
    
    # Register the agency user
    with httpx.Client(base_url=backend_url) as client:
        reg_resp = client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "role": "agency",
            "company_name": f"Test Agency {timestamp}"
        })
        assert reg_resp.status_code == 201, f"Agency registration failed: {reg_resp.text}"
        
        # Log in to retrieve token
        token_resp = client.post("/api/auth/token", data={
            "username": email,
            "password": password
        })
        assert token_resp.status_code == 200, f"Token request failed: {token_resp.text}"
        token = token_resp.json()["access_token"]
        
        # Create client authenticated with bearer token
        auth_client = httpx.Client(
            base_url=backend_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0
        )
        yield auth_client
        auth_client.close()

@pytest.fixture
def client_client(backend_url):
    """Client authenticated as an end-Client user linked to a fresh agency."""
    timestamp = int(time.time() * 1000)
    
    # 1. Register a fresh agency for this client
    agency_username = f"agency_for_client_{timestamp}"
    agency_password = f"AgencyPassword{timestamp}!"
    agency_email = f"{agency_username}@agency.com"
    
    with httpx.Client(base_url=backend_url) as client:
        reg_agency_resp = client.post("/api/auth/register", json={
            "email": agency_email,
            "username": agency_username,
            "password": agency_password,
            "role": "agency",
            "company_name": f"Agency For Client {timestamp}"
        })
        assert reg_agency_resp.status_code == 201, f"Agency registration failed: {reg_agency_resp.text}"
        
        # Log in to retrieve agency token to get agency ID
        token_resp = client.post("/api/auth/token", data={
            "username": agency_email,
            "password": agency_password
        })
        assert token_resp.status_code == 200, f"Agency Token request failed: {token_resp.text}"
        agency_token = token_resp.json()["access_token"]
        
        # Get agency ID via /me endpoint
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {agency_token}"})
        assert me_resp.status_code == 200, f"Agency me request failed: {me_resp.text}"
        agency_id = me_resp.json()["agency"]["id"]
        
        # 2. Register the client user with the valid agency_id
        client_username = f"client_{timestamp}"
        client_password = f"ClientPassword{timestamp}!"
        client_email = f"{client_username}@client.com"
        
        reg_client_resp = client.post("/api/auth/register", json={
            "email": client_email,
            "username": client_username,
            "password": client_password,
            "role": "client",
            "first_name": "Test",
            "last_name": f"Client_{timestamp}",
            "agency_id": agency_id
        })
        assert reg_client_resp.status_code == 201, f"Client registration failed: {reg_client_resp.text}"
        
        # 3. Log in as client to retrieve client token
        token_resp_client = client.post("/api/auth/token", data={
            "username": client_email,
            "password": client_password
        })
        assert token_resp_client.status_code == 200, f"Client Token request failed: {token_resp_client.text}"
        token = token_resp_client.json()["access_token"]
        
        # Create client authenticated with bearer token
        auth_client = httpx.Client(
            base_url=backend_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0
        )
        yield auth_client
        auth_client.close()
