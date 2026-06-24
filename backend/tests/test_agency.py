def test_agency_endpoints(client):
    # 1. Register agency and login
    resp_agency = client.post("/api/auth/register", json={
        "email": "agency@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Apex Agency"
    })
    assert resp_agency.status_code == 201
    agency_id = 1  # First agency registered

    login_agency = client.post("/api/auth/token", data={
        "username": "agency@test.com",
        "password": "testpassword123"
    })
    assert login_agency.status_code == 200
    agency_token = login_agency.json()["access_token"]

    # 2. Register client and login
    resp_client = client.post("/api/auth/register", json={
        "email": "client@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "12345678",
        "agency_id": agency_id
    })
    assert resp_client.status_code == 201

    login_client = client.post("/api/auth/token", data={
        "username": "client@test.com",
        "password": "testpassword123"
    })
    assert login_client.status_code == 200
    client_token = login_client.json()["access_token"]

    # 3. Agency clients endpoint access control
    headers_agency = {"Authorization": f"Bearer {agency_token}"}
    headers_client = {"Authorization": f"Bearer {client_token}"}

    # Agency should succeed
    clients_resp = client.get("/api/agency/clients", headers=headers_agency)
    assert clients_resp.status_code == 200
    clients_data = clients_resp.json()
    assert len(clients_data) == 1
    assert clients_data[0]["email"] == "client@test.com"
    assert clients_data[0]["first_name"] == "John"
    assert clients_data[0]["last_name"] == "Doe"

    # Client should be forbidden (RBAC check)
    clients_resp_forbidden = client.get("/api/agency/clients", headers=headers_client)
    assert clients_resp_forbidden.status_code == 403

    # 4. Agency metrics endpoint access control
    # Agency should succeed
    metrics_resp = client.get("/api/agency/metrics", headers=headers_agency)
    assert metrics_resp.status_code == 200
    metrics_data = metrics_resp.json()
    assert metrics_data["total_clients"] == 1
    assert metrics_data["dispute_success_rate"] == 0.75
    assert metrics_data["simulated_billing"] == 99.0
    assert metrics_data["agency_id"] == agency_id
    assert metrics_data["metrics"]["total_clients"] == 1
    assert metrics_data["dispute_metrics"]["success_rate"] == 0.75
    assert metrics_data["billing_summary"]["active_clients_count"] == 0

    # Client should be forbidden (RBAC check)
    metrics_resp_forbidden = client.get("/api/agency/metrics", headers=headers_client)
    assert metrics_resp_forbidden.status_code == 403
