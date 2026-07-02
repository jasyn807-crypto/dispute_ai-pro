import pytest
from unittest.mock import patch
from app.models.client import Client
from app.models.dispute import DisputeLetter
from app.models.billing import BillingTransaction
from app.models.audit_log import MailingLog

def test_dispatch_mail_workflow(client, db_session, monkeypatch):
    # Ensure LOB_API_KEY is not in the environment to avoid real api calls,
    # or mock the httpx post request if it gets called.
    monkeypatch.delenv("LOB_API_KEY", raising=False)

    # 1. Register Agency and Client
    client.post("/api/auth/register", json={
        "email": "agency_mailing@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Mailing Agency"
    })
    
    client.post("/api/auth/register", json={
        "email": "client_mailing@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "Mailing",
        "last_name": "Client",
        "agency_id": 1
    })

    # Log in client
    login_client = client.post("/api/auth/token", data={
        "username": "client_mailing@test.com",
        "password": "testpassword123"
    })
    client_token = login_client.json()["access_token"]
    headers_client = {"Authorization": f"Bearer {client_token}"}

    # Log in agency
    login_agency = client.post("/api/auth/token", data={
        "username": "agency_mailing@test.com",
        "password": "testpassword123"
    })
    agency_token = login_agency.json()["access_token"]
    headers_agency = {"Authorization": f"Bearer {agency_token}"}

    # 2. Insert mock DisputeLetter via db_session
    db_client = db_session.query(Client).first()
    assert db_client is not None

    letter = DisputeLetter(
        client_id=db_client.id,
        bureau="Equifax",
        letter_content="This is a test dispute letter content.",
        status="draft"
    )
    db_session.add(letter)
    db_session.commit()
    db_session.refresh(letter)

    letter_id = letter.id

    # 3. Client trying to dispatch without paying first -> 402 Payment Required
    resp_dispatch_402 = client.post(
        "/api/mailing/dispatch",
        headers=headers_client,
        json={"dispute_letter_id": letter_id}
    )
    assert resp_dispatch_402.status_code == 402
    assert "Payment required" in resp_dispatch_402.json()["detail"]

    # 4. Insert paid BillingTransaction via db_session
    tx = BillingTransaction(
        agency_id=db_client.agency_id,
        client_id=db_client.id,
        amount=15.00,
        description=f"Mailing Fee for Letter #{letter_id}",
        status="paid"
    )
    db_session.add(tx)
    db_session.commit()

    # 5. Client trying to dispatch after paying -> 201 Created
    resp_dispatch_success = client.post(
        "/api/mailing/dispatch",
        headers=headers_client,
        json={"dispute_letter_id": letter_id}
    )
    assert resp_dispatch_success.status_code == 201
    resp_data = resp_dispatch_success.json()
    assert "message" in resp_data
    assert "mailing_log" in resp_data
    assert resp_data["letter_status"] == "mailed"
    
    log_data = resp_data["mailing_log"]
    assert log_data["dispute_letter_id"] == letter_id
    assert log_data["bureau"] == "equifax"
    assert log_data["status"] == "queued"
    assert log_data["tracking_number"].startswith("USPS-CR-")

    # 6. Verify logs endpoint
    resp_logs_client = client.get("/api/mailing/logs", headers=headers_client)
    assert resp_logs_client.status_code == 200
    logs_client = resp_logs_client.json()
    assert len(logs_client) == 1
    assert logs_client[0]["id"] == log_data["id"]

    resp_logs_agency = client.get("/api/mailing/logs", headers=headers_agency)
    assert resp_logs_agency.status_code == 200
    logs_agency = resp_logs_agency.json()
    assert len(logs_agency) == 1
    assert logs_agency[0]["id"] == log_data["id"]


def test_dispatch_mail_error_cases(client, db_session):
    # Register agency and client
    client.post("/api/auth/register", json={
        "email": "agency_err@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Error Agency"
    })
    client.post("/api/auth/register", json={
        "email": "client_err@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "Error",
        "last_name": "Client",
        "agency_id": 1
    })

    # Log in agency
    login_agency = client.post("/api/auth/token", data={
        "username": "agency_err@test.com",
        "password": "testpassword123"
    })
    agency_token = login_agency.json()["access_token"]
    headers_agency = {"Authorization": f"Bearer {agency_token}"}

    # 1. Dispatch non-existent dispute letter -> 404 Not Found
    resp_404 = client.post(
        "/api/mailing/dispatch",
        headers=headers_agency,
        json={"dispute_letter_id": 9999}
    )
    assert resp_404.status_code == 404
    assert resp_404.json()["detail"] == "Dispute letter not found"

    # 2. Dispatch dispute letter with empty content -> 400 Bad Request
    db_client = db_session.query(Client).first()
    empty_letter = DisputeLetter(
        client_id=db_client.id,
        bureau="Experian",
        letter_content="",
        status="draft"
    )
    db_session.add(empty_letter)
    db_session.commit()
    db_session.refresh(empty_letter)

    resp_400 = client.post(
        "/api/mailing/dispatch",
        headers=headers_agency,
        json={"dispute_letter_id": empty_letter.id}
    )
    assert resp_400.status_code == 400
    assert "no content" in resp_400.json()["detail"]


def test_dispatch_mail_unauthorized(client, db_session):
    # Register two agencies and clients
    client.post("/api/auth/register", json={
        "email": "agency1@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Agency One"
    })
    client.post("/api/auth/register", json={
        "email": "client1@test.com",
        "password": "testpassword123",
        "role": "client",
        "first_name": "Client",
        "last_name": "One",
        "agency_id": 1
    })

    client.post("/api/auth/register", json={
        "email": "agency2@test.com",
        "password": "testpassword123",
        "role": "agency",
        "company_name": "Agency Two"
    })

    # Log in Agency 2 (ID is 2)
    login_agency2 = client.post("/api/auth/token", data={
        "username": "agency2@test.com",
        "password": "testpassword123"
    })
    agency2_token = login_agency2.json()["access_token"]
    headers_agency2 = {"Authorization": f"Bearer {agency2_token}"}

    # Create letter for client1
    db_client1 = db_session.query(Client).filter_by(first_name="Client").first()
    letter = DisputeLetter(
        client_id=db_client1.id,
        bureau="TransUnion",
        letter_content="Please investigate these accounts.",
        status="draft"
    )
    db_session.add(letter)
    db_session.commit()
    db_session.refresh(letter)

    # Agency 2 trying to dispatch client 1's letter -> 403 Forbidden
    resp_403 = client.post(
        "/api/mailing/dispatch",
        headers=headers_agency2,
        json={"dispute_letter_id": letter.id}
    )
    assert resp_403.status_code == 403
    assert resp_403.json()["detail"] == "Not authorized"
