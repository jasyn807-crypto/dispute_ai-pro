import os

def test_client_endpoints(client):
    # 1. Register agency and client, then login client
    client.post("/api/auth/register", json={
        "email": "agency@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Apex Agency"
    })
    
    client.post("/api/auth/register", json={
        "email": "client@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe",
        "agency_id": 1
    })

    login_client = client.post("/api/auth/token", data={
        "username": "client@test.com",
        "password": "testpassword123"
    })
    client_token = login_client.json()["access_token"]
    headers_client = {"Authorization": f"Bearer {client_token}"}

    # Login agency
    login_agency = client.post("/api/auth/token", data={
        "username": "agency@test.com",
        "password": "testpassword123"
    })
    agency_token = login_agency.json()["access_token"]
    headers_agency = {"Authorization": f"Bearer {agency_token}"}

    # 2. Get initial status
    status_resp = client.get("/api/client/status", headers=headers_client)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["client_id"] == 1
    assert status_data["status"] == "onboarding"
    assert status_data["onboarding_step"] == "document_upload"
    assert status_data["onboarding_steps"]["identity_uploaded"] is False

    # Agency accessing client status should be forbidden
    status_resp_forbidden = client.get("/api/client/status", headers=headers_agency)
    assert status_resp_forbidden.status_code == 403

    # 3. Upload document (valid)
    files = {"file": ("test_id.jpg", b"mock jpg bytes content", "image/jpeg")}
    data = {"document_type": "id_proof"}
    
    upload_resp = client.post(
        "/api/client/upload", 
        headers=headers_client, 
        data=data, 
        files=files
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["message"] == "Document uploaded successfully"
    assert upload_data["document_type"] == "id_proof"
    assert upload_data["filename"] == "test_id.jpg"
    assert "uploads/documents/client_1" in upload_data["file_path"].replace("\\", "/")

    # Verify physical file exists
    assert os.path.exists(upload_data["file_path"])

    # 4. Check status progression
    status_resp_2 = client.get("/api/client/status", headers=headers_client)
    assert status_resp_2.status_code == 200
    status_data_2 = status_resp_2.json()
    assert status_data_2["status"] == "documents_uploaded"
    assert status_data_2["onboarding_step"] == "document_uploaded"
    assert status_data_2["onboarding_steps"]["identity_uploaded"] is True
    assert len(status_data_2["documents_uploaded"]) == 1

    # 5. Upload invalid document type
    files_invalid = {"file": ("address.pdf", b"mock pdf bytes", "application/pdf")}
    data_invalid = {"document_type": "invalid_type"}
    upload_resp_invalid = client.post(
        "/api/client/upload",
        headers=headers_client,
        data=data_invalid,
        files=files_invalid
    )
    assert upload_resp_invalid.status_code == 400

    # 6. Agency upload document should be forbidden
    upload_resp_forbidden = client.post(
        "/api/client/upload",
        headers=headers_agency,
        data={"document_type": "id_proof"},
        files={"file": ("test_id.jpg", b"mock bytes", "image/jpeg")}
    )
    assert upload_resp_forbidden.status_code == 403

    # Clean up created upload file
    if os.path.exists(upload_data["file_path"]):
        os.remove(upload_data["file_path"])
    client_dir = os.path.dirname(upload_data["file_path"])
    if os.path.exists(client_dir) and not os.listdir(client_dir):
        os.rmdir(client_dir)
