import io
import os
from app.services.parser import CreditReportParser

def test_parser_service_json():
    # Test JSON parser with derogatory_items
    json_data = b"""{
        "derogatory_items": [
            {
                "bureau": "Equifax",
                "creditor": "ACME Collections",
                "account_number": "123456XXXX",
                "amount": 500.0,
                "negative_type": "collection",
                "status": "pending"
            }
        ]
    }"""
    items = CreditReportParser.parse_report("report.json", json_data)
    assert len(items) == 1
    assert items[0]["creditor"] == "ACME Collections"
    assert items[0]["amount"] == 500.0
    assert items[0]["bureau"] == "Equifax"
    assert items[0]["status"] == "collection"

def test_parser_service_text():
    # Test plain text parser
    text_data = b"""EQUIFAX CREDIT REPORT
    - Creditor: ACME Collections, Account #: 123456XXXX, Balance: $500.00, Status: Collection
    EXPERIAN CREDIT REPORT
    - Creditor: Apex Visa, Account #: 987654XXXX, Balance: $1200.00, Status: Charge-off
    """
    items = CreditReportParser.parse_report("report.txt", text_data)
    assert len(items) == 2
    assert items[0]["creditor"] == "ACME Collections"
    assert items[0]["amount"] == 500.0
    assert items[0]["bureau"] == "Equifax"
    assert items[0]["status"] == "collection"

    assert items[1]["creditor"] == "Apex Visa"
    assert items[1]["amount"] == 1200.0
    assert items[1]["bureau"] == "Experian"
    assert items[1]["status"] == "charge_off"

def test_parser_service_fallback():
    # Test fallback generator when parsing fails or input is empty
    items_empty = CreditReportParser.parse_report("report.txt", b"")
    assert len(items_empty) == 3
    # Check that fallback contains standard items
    bureaus = {item["bureau"] for item in items_empty}
    assert "Equifax" in bureaus
    assert "Experian" in bureaus
    assert "TransUnion" in bureaus

    # Test that unstructured non-empty contents yield 0 items
    items_unstructured = CreditReportParser.parse_report("report.txt", b"Sample report")
    assert len(items_unstructured) == 0

def test_parser_upload_endpoints(client):
    # Setup roles
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

    # Login client
    login_client = client.post("/api/auth/token", data={
        "username": "client@test.com",
        "password": "testpassword123"
    })
    client_token = login_client.json()["access_token"]
    headers_client = {"Authorization": f"Bearer {client_token}"}

    # 1. Test empty file rejection
    files_empty = {"report": ("empty.txt", b"", "text/plain")}
    resp_empty = client.post("/api/parser/upload", headers=headers_client, files=files_empty)
    assert resp_empty.status_code == 400
    assert "empty" in resp_empty.json()["detail"].lower()

    # 2. Test large file rejection (>5MB)
    large_content = b"a" * (5 * 1024 * 1024 + 1)
    files_large = {"report": ("large.txt", large_content, "text/plain")}
    resp_large = client.post("/api/parser/upload", headers=headers_client, files=files_large)
    assert resp_large.status_code == 400
    assert "limit" in resp_large.json()["detail"].lower()

    # 3. Test successful upload
    report_content = b"EXPERIAN REPORT: NEGATIVE ITEM ACME Collections $500"
    files = {"report": ("experian.txt", report_content, "text/plain")}
    resp = client.post("/api/parser/upload", headers=headers_client, files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    assert "negative_items" in data
    assert len(data["negative_items"]) > 0
    
    for item in data["negative_items"]:
        assert "id" in item
        assert "creditor" in item
        assert "amount" in item
        assert "bureau" in item
        assert "status" in item

    # 4. Check client status progression
    status_resp = client.get("/api/client/status", headers=headers_client)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["onboarding_step"] == "report_parsed"
    assert status_data["onboarding_steps"]["report_parsed"] is True

    # 5. List uploaded reports
    list_resp = client.get("/api/parser/reports", headers=headers_client)
    assert list_resp.status_code == 200
    reports = list_resp.json()
    assert len(reports) == 1
    assert reports[0]["report_id"] == data["report_id"]
    assert reports[0]["filename"] == "experian.txt"
