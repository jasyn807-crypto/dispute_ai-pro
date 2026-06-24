def test_register_agency(client):
    # Test valid agency registration
    response = client.post("/api/auth/register", json={
        "email": "agency@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Test Agency Inc."
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "agency@test.com"
    assert data["role"] == "agency"
    
    # Test duplicate register
    response_dup = client.post("/api/auth/register", json={
        "email": "agency@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Test Agency Inc."
    })
    assert response_dup.status_code == 400
    assert response_dup.json()["detail"] == "Email already registered"

    # Test missing company name
    response_missing = client.post("/api/auth/register", json={
        "email": "agency2@test.com",
        "password": "testpassword123",
        "role": "agency"
    })
    assert response_missing.status_code == 422 or response_missing.status_code == 400

def test_register_client_validation(client):
    # Test registering client with missing agency
    response = client.post("/api/auth/register", json={
        "email": "client@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe"
    })
    assert response.status_code == 400 or response.status_code == 422

    # Register agency first
    resp_agency = client.post("/api/auth/register", json={
        "email": "agency@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Test Agency"
    })
    assert resp_agency.status_code == 201

    # Fetch agency ID from /me or database (we can fetch it by registering client to agency_id=1 as it starts autoincrement from 1)
    # Let's test registering client with invalid agency ID
    response_invalid_agency = client.post("/api/auth/register", json={
        "email": "client@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe",
        "agency_id": 999
    })
    assert response_invalid_agency.status_code == 400

    # Test valid client registration
    response_valid_client = client.post("/api/auth/register", json={
        "email": "client@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe",
        "agency_id": 1
    })
    assert response_valid_client.status_code == 201

def test_login_and_me_endpoints(client):
    # Register agency
    client.post("/api/auth/register", json={
        "email": "agency@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Test Agency Inc."
    })
    
    # Login
    response = client.post("/api/auth/token", data={
        "username": "agency@test.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    assert token_data["role"] == "agency"
    
    # Fetch Me
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "agency@test.com"
    assert me_data["role"] == "agency"
    assert me_data["agency_profile"]["company_name"] == "Test Agency Inc."
    assert me_data["agency"]["company_name"] == "Test Agency Inc."

    # Login with wrong credentials
    resp_wrong = client.post("/api/auth/token", data={
        "username": "agency@test.com",
        "password": "wrongpassword"
    })
    assert resp_wrong.status_code == 401
