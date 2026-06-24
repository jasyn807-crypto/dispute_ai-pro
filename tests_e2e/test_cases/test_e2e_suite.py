import pytest
import httpx
import io
import time

# =====================================================================
# TIER 1: FEATURE COVERAGE (>=5 cases per feature, total >=20)
# =====================================================================

# --- Feature 1: Authentication ---

def test_t1_auth_register_agency_success(public_client):
    """Case 1: Verify agency registration succeeds with valid data."""
    timestamp = int(time.time() * 1000)
    email = f"t1_agency_{timestamp}@test.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": f"T1 Agency {timestamp}",
        "phone": "123-456-7890"
    }
    resp = public_client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email
    assert data["role"] == "agency"
    assert data["is_active"] is True
    assert "id" in data

def test_t1_auth_register_client_success(public_client):
    """Case 2: Verify client registration succeeds when linked to an existing agency."""
    timestamp = int(time.time() * 1000)
    # Register agency first
    agency_email = f"t1_agency_c_{timestamp}@test.com"
    agency_resp = public_client.post("/api/auth/register", json={
        "email": agency_email,
        "password": "Password123!",
        "role": "agency",
        "company_name": f"T1 Client Agency {timestamp}"
    })
    assert agency_resp.status_code == 201
    
    # Log in as agency to get agency_id from /me
    login_resp = public_client.post("/api/auth/token", data={
        "username": agency_email,
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    me_resp = public_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    agency_id = me_resp.json()["agency"]["id"]
    
    # Register client
    client_email = f"t1_client_{timestamp}@test.com"
    client_payload = {
        "email": client_email,
        "password": "Password123!",
        "role": "client",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "555-555-5555",
        "agency_id": agency_id
    }
    resp = public_client.post("/api/auth/register", json=client_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == client_email
    assert data["role"] == "client"

def test_t1_auth_login_success(public_client):
    """Case 3: Verify OAuth2 login flow returns valid token and role."""
    timestamp = int(time.time() * 1000)
    email = f"login_t1_{timestamp}@test.com"
    public_client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": "Login Test Company"
    })
    
    resp = public_client.post("/api/auth/token", data={
        "username": email,
        "password": "Password123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "agency"

def test_t1_auth_me_endpoint_agency(public_client):
    """Case 4: Verify /me endpoint returns user data and agency profile."""
    timestamp = int(time.time() * 1000)
    email = f"me_agency_{timestamp}@test.com"
    public_client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": "Me Agency Company",
        "phone": "555-0199"
    })
    
    token_resp = public_client.post("/api/auth/token", data={
        "username": email,
        "password": "Password123!"
    })
    token = token_resp.json()["access_token"]
    
    resp = public_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email
    assert data["role"] == "agency"
    assert data["agency"] is not None
    assert data["agency"]["company_name"] == "Me Agency Company"
    assert data["agency"]["phone"] == "555-0199"

def test_t1_auth_rbac_agency_restricted(client_client):
    """Case 5: Verify client-role client cannot access agency-restricted endpoints."""
    # Try calling agency-only endpoints using client_client fixture
    resp1 = client_client.get("/api/agency/clients")
    assert resp1.status_code == 403
    
    resp2 = client_client.get("/api/agency/metrics")
    assert resp2.status_code == 403


# --- Feature 2: Credit Report Parsing ---

def test_t1_parser_upload_text_report(client_client):
    """Case 6: Verify client can upload a credit report file successfully."""
    report_content = b"EXPERIAN REPORT: NEGATIVE ITEM ACME Collections $500"
    files = {"report": ("experian.txt", io.BytesIO(report_content), "text/plain")}
    resp = client_client.post("/api/parser/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    assert "negative_items" in data
    assert len(data["negative_items"]) > 0

def test_t1_parser_negative_items_structure(client_client):
    """Case 7: Verify parsed negative items follow the expected interface schema."""
    files = {"report": ("report.txt", io.BytesIO(b"Credit report content"), "text/plain")}
    resp = client_client.post("/api/parser/upload", files=files)
    assert resp.status_code == 200
    items = resp.json()["negative_items"]
    for item in items:
        assert "id" in item
        assert "creditor" in item
        assert "amount" in item
        assert "bureau" in item
        assert "status" in item

def test_t1_parser_multiple_bureau_extraction(client_client):
    """Case 8: Verify report extraction pulls negative items from different bureaus."""
    files = {"report": ("report.txt", io.BytesIO(b"Sample report"), "text/plain")}
    resp = client_client.post("/api/parser/upload", files=files)
    items = resp.json()["negative_items"]
    bureaus = {item["bureau"] for item in items}
    assert "Equifax" in bureaus
    assert "Experian" in bureaus

def test_t1_parser_list_reports(client_client):
    """Case 9: Verify client can retrieve all previously uploaded reports."""
    # Upload first
    files = {"report": ("my_report.txt", io.BytesIO(b"Test list report"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    
    # List reports
    list_resp = client_client.get("/api/parser/reports")
    assert list_resp.status_code == 200
    report_ids = [r["report_id"] for r in list_resp.json()]
    assert report_id in report_ids

def test_t1_parser_unauth_upload_blocked(public_client):
    """Case 10: Verify unauthenticated users are blocked from uploading reports."""
    files = {"report": ("unauth.txt", io.BytesIO(b"Secret report"), "text/plain")}
    resp = public_client.post("/api/parser/upload", files=files)
    assert resp.status_code == 401


# --- Feature 3: LLM Dispute Letter Generation ---

def test_t1_dispute_generate_letter(client_client):
    """Case 11: Verify dispute letter generation succeeds with valid request."""
    # 1. Parse report to get report_id and items
    files = {"report": ("rep.txt", io.BytesIO(b"abc"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    item_id = upload_resp.json()["negative_items"][0]["id"]
    
    # 2. Generate letter
    payload = {
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "This account belongs to another person with a similar name."
    }
    resp = client_client.post("/api/dispute/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "letter_id" in data
    assert "content" in data
    assert "similar name" in data["content"]

def test_t1_dispute_multiple_items(client_client):
    """Case 12: Verify generating a single dispute letter for multiple selected items."""
    files = {"report": ("rep.txt", io.BytesIO(b"abc"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    item_ids = [item["id"] for item in upload_resp.json()["negative_items"][:2]]
    
    payload = {
        "report_id": report_id,
        "item_ids": item_ids,
        "reason": "Not mine."
    }
    resp = client_client.post("/api/dispute/generate", json=payload)
    assert resp.status_code == 200
    content = resp.json()["content"]
    for iid in item_ids:
        assert iid in content

def test_t1_dispute_compliance_valid(client_client):
    """Case 13: Verify compliance check approves legal, standard letters."""
    letter_content = "Dear Bureau, please verify the following debt with creditor ACME Collections. It was paid in full."
    resp = client_client.post("/api/dispute/compliance", json={"letter_content": letter_content})
    assert resp.status_code == 200
    data = resp.json()
    assert data["compliant"] is True
    assert len(data["prohibited_claims_found"]) == 0

def test_t1_dispute_compliance_invalid(client_client):
    """Case 14: Verify compliance check rejects letters with prohibited claims."""
    letter_content = "I guarantee deletion of all bad items in 24 hours using a 100% legal trick!"
    resp = client_client.post("/api/dispute/compliance", json={"letter_content": letter_content})
    assert resp.status_code == 200
    data = resp.json()
    assert data["compliant"] is False
    assert "guarantee deletion" in data["prohibited_claims_found"]
    assert "100% legal trick" in data["prohibited_claims_found"]

def test_t1_dispute_compliance_suggestions(client_client):
    """Case 15: Verify compliance helper returns correction suggestions."""
    letter_content = "Clean credit in 24 hours!"
    resp = client_client.post("/api/dispute/compliance", json={"letter_content": letter_content})
    data = resp.json()
    assert data["compliant"] is False
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0


# --- Feature 4: CRM & Lob Mailing Simulation ---

def test_t1_mailing_dispatch_success(client_client):
    """Case 16: Verify sending a letter via USPS Lob simulator succeeds."""
    # 1. Upload report & generate letter
    files = {"report": ("rep.txt", io.BytesIO(b"xyz"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    item_id = upload_resp.json()["negative_items"][0]["id"]
    
    gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "Paid in full"
    })
    letter_id = gen_resp.json()["letter_id"]
    
    # 2. Mail
    mail_resp = client_client.post("/api/dispute/mail", json={
        "letter_id": letter_id,
        "recipient_bureau": "Equifax"
    })
    assert mail_resp.status_code == 200
    data = mail_resp.json()
    assert "mail_id" in data
    assert data["status"] == "queued"
    assert "tracking_number" in data

def test_t1_mailing_tracking_format(client_client):
    """Case 17: Verify tracking number follows Simulated USPS prefix standard."""
    files = {"report": ("rep.txt", io.BytesIO(b"xyz"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    item_id = upload_resp.json()["negative_items"][0]["id"]
    gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "Paid"
    })
    letter_id = gen_resp.json()["letter_id"]
    
    mail_resp = client_client.post("/api/dispute/mail", json={
        "letter_id": letter_id,
        "recipient_bureau": "Experian"
    })
    assert mail_resp.json()["tracking_number"].startswith("USPS-LOB-")

def test_t1_mailing_status_tracking(client_client):
    """Case 18: Verify client status reports the correct count of disputes sent."""
    # Check initial status
    status_resp_init = client_client.get("/api/client/status")
    initial_total = status_resp_init.json()["disputes_summary"]["total"]
    
    # Mail one dispute
    files = {"report": ("rep.txt", io.BytesIO(b"xyz"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    item_id = upload_resp.json()["negative_items"][0]["id"]
    gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "Paid"
    })
    letter_id = gen_resp.json()["letter_id"]
    
    client_client.post("/api/dispute/mail", json={
        "letter_id": letter_id,
        "recipient_bureau": "TransUnion"
    })
    
    status_resp = client_client.get("/api/client/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["disputes_summary"]["total"] == initial_total + 1

def test_t1_mailing_agency_metrics(backend_url, agency_client):
    """Case 19: Verify agency metrics show the total disputes dispatched."""
    # Find agency profile
    me_resp = agency_client.get("/api/auth/me")
    agency_id = me_resp.json()["agency"]["id"]
    
    # Check initial metrics
    metrics_resp_init = agency_client.get("/api/agency/metrics")
    init_total_disputed = metrics_resp_init.json()["dispute_metrics"]["total_disputed"]
    
    # Register client under this agency
    timestamp = int(time.time() * 1000)
    client_email = f"metric_client_{timestamp}@test.com"
    with httpx.Client(base_url=backend_url) as client:
        client.post("/api/auth/register", json={
            "email": client_email,
            "password": "Password123!",
            "role": "client",
            "first_name": "Metric",
            "last_name": "Test",
            "agency_id": agency_id
        })
        
        # Log in client
        tok_resp = client.post("/api/auth/token", data={"username": client_email, "password": "Password123!"})
        client_token = tok_resp.json()["access_token"]
        
        # Client uploads & mails
        headers = {"Authorization": f"Bearer {client_token}"}
        up_resp = client.post("/api/parser/upload", files={"report": ("rep.txt", io.BytesIO(b"abc"), "text/plain")}, headers=headers)
        report_id = up_resp.json()["report_id"]
        item_id = up_resp.json()["negative_items"][0]["id"]
        
        gen_resp = client.post("/api/dispute/generate", json={
            "report_id": report_id,
            "item_ids": [item_id],
            "reason": "Not mine"
        }, headers=headers)
        letter_id = gen_resp.json()["letter_id"]
        
        client.post("/api/dispute/mail", json={
            "letter_id": letter_id,
            "recipient_bureau": "Equifax"
        }, headers=headers)
        
    # Check agency metrics updated
    metrics_resp = agency_client.get("/api/agency/metrics")
    assert metrics_resp.status_code == 200
    assert metrics_resp.json()["dispute_metrics"]["total_disputed"] == init_total_disputed + 1

def test_t1_mailing_unauth_mail_blocked(public_client):
    """Case 20: Verify unauthenticated users cannot request mailing services."""
    resp = public_client.post("/api/dispute/mail", json={
        "letter_id": "some_id",
        "recipient_bureau": "Equifax"
    })
    assert resp.status_code == 401


# =====================================================================
# TIER 2: BOUNDARY & EDGE CASES (>=5 cases per feature, total >=20)
# =====================================================================

# --- Feature A: Authentication Edge Cases ---

def test_t2_auth_register_duplicate_email(public_client):
    """Case 21: Registering with an already existing email returns 400 Bad Request."""
    timestamp = int(time.time() * 1000)
    email = f"duplicate_{timestamp}@test.com"
    
    # First registration
    public_client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": "First Corp"
    })
    
    # Second registration with same email
    resp = public_client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": "Second Corp"
    })
    assert resp.status_code == 400
    assert "email already registered" in resp.text.lower()

def test_t2_auth_register_invalid_role(public_client):
    """Case 22: Registering with an invalid role returns 400 Bad Request."""
    resp = public_client.post("/api/auth/register", json={
        "email": "invalid_role@test.com",
        "password": "Password123!",
        "role": "administrator",
        "company_name": "Admin Corp"
    })
    assert resp.status_code == 400

def test_t2_auth_register_client_missing_agency(public_client):
    """Case 23: Registering a client without an agency_id returns 400 Bad Request."""
    resp = public_client.post("/api/auth/register", json={
        "email": "client_no_agency@test.com",
        "password": "Password123!",
        "role": "client",
        "first_name": "Jane",
        "last_name": "Doe"
    })
    assert resp.status_code == 400

def test_t2_auth_register_client_nonexistent_agency(public_client):
    """Case 24: Registering a client with non-existent agency ID returns 400 Bad Request."""
    resp = public_client.post("/api/auth/register", json={
        "email": "client_bad_agency@test.com",
        "password": "Password123!",
        "role": "client",
        "first_name": "Jane",
        "last_name": "Doe",
        "agency_id": 99999
    })
    assert resp.status_code == 400

def test_t2_auth_login_invalid_password(public_client):
    """Case 25: Logging in with incorrect password returns 400/401."""
    timestamp = int(time.time() * 1000)
    email = f"wrong_pass_{timestamp}@test.com"
    public_client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": "Wrong Pass Corp"
    })
    
    resp = public_client.post("/api/auth/token", data={
        "username": email,
        "password": "WrongPassword"
    })
    assert resp.status_code in [400, 401]

def test_t2_auth_register_agency_missing_company(public_client):
    """Case 26: Registering an agency without company_name returns 400 Bad Request."""
    resp = public_client.post("/api/auth/register", json={
        "email": "agency_no_company@test.com",
        "password": "Password123!",
        "role": "agency",
        "phone": "111-222-3333"
    })
    assert resp.status_code == 400


# --- Feature B: Parser Edge Cases ---

def test_t2_parser_upload_empty_file(client_client):
    """Case 27: Uploading an empty file returns 400 Bad Request."""
    files = {"report": ("empty.txt", io.BytesIO(b""), "text/plain")}
    resp = client_client.post("/api/parser/upload", files=files)
    assert resp.status_code == 400

def test_t2_client_upload_empty_document(client_client):
    """Case 28: Uploading an empty verification document returns 400 Bad Request."""
    files = {"file": ("empty_id.jpg", io.BytesIO(b""), "image/jpeg")}
    resp = client_client.post("/api/client/upload", data={"document_type": "id_proof"}, files=files)
    assert resp.status_code == 400

def test_t2_client_upload_invalid_type(client_client):
    """Case 29: Uploading a verification document with an invalid document type returns 400."""
    files = {"file": ("id.jpg", io.BytesIO(b"valid bytes"), "image/jpeg")}
    resp = client_client.post("/api/client/upload", data={"document_type": "unsupported_type"}, files=files)
    assert resp.status_code == 400

def test_t2_client_upload_no_files(client_client):
    """Case 30: Calling document upload endpoint without files returns 422/400."""
    # Upload with missing "file" key
    resp = client_client.post("/api/client/upload", data={"document_type": "id_proof"})
    assert resp.status_code in [400, 422]

def test_t2_parser_upload_missing_param(client_client):
    """Case 31: Calling parser upload without multipart report parameter returns 422/400."""
    resp = client_client.post("/api/parser/upload", files={})
    assert resp.status_code in [400, 422]


# --- Feature C: Dispute Letter Edge Cases ---

def test_t2_dispute_generate_empty_item_ids(client_client):
    """Case 32: Dispute generation fails when item_ids list is empty."""
    # 1. Parse report
    files = {"report": ("rep.txt", io.BytesIO(b"abc"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    
    # 2. Try generating with empty items list
    resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [],
        "reason": "Invalid"
    })
    assert resp.status_code == 400

def test_t2_dispute_generate_nonexistent_report_id(client_client):
    """Case 33: Dispute generation fails when report_id does not exist."""
    resp = client_client.post("/api/dispute/generate", json={
        "report_id": "nonexistent-uuid-12345",
        "item_ids": ["item_1"],
        "reason": "Invalid"
    })
    assert resp.status_code in [400, 404]

def test_t2_dispute_generate_nonexistent_item_id(client_client):
    """Case 34: Dispute generation fails when item_ids do not belong to report."""
    files = {"report": ("rep.txt", io.BytesIO(b"abc"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    
    resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": ["nonexistent_item"],
        "reason": "Not mine"
    })
    assert resp.status_code == 400

def test_t2_dispute_compliance_case_insensitive(client_client):
    """Case 35: Compliance helper detects prohibited statements regardless of case."""
    bad_content = "i GuArAnTeE dElEtIoN of all negative records!"
    resp = client_client.post("/api/dispute/compliance", json={"letter_content": bad_content})
    assert resp.status_code == 200
    assert resp.json()["compliant"] is False
    assert "guarantee deletion" in resp.json()["prohibited_claims_found"]

def test_t2_dispute_compliance_empty_text(client_client):
    """Case 36: Compliance helper handles empty text inputs gracefully."""
    resp = client_client.post("/api/dispute/compliance", json={"letter_content": ""})
    assert resp.status_code == 200
    assert resp.json()["compliant"] is True


# --- Feature D: Mailing Edge Cases ---

def test_t2_mailing_nonexistent_letter(client_client):
    """Case 37: Mailing a nonexistent letter returns 404 Not Found."""
    resp = client_client.post("/api/dispute/mail", json={
        "letter_id": "nonexistent-letter-id-999",
        "recipient_bureau": "Equifax"
    })
    assert resp.status_code == 404

def test_t2_mailing_invalid_bureau(client_client):
    """Case 38: Mailing a letter with an unsupported bureau returns 400 Bad Request."""
    files = {"report": ("rep.txt", io.BytesIO(b"xyz"), "text/plain")}
    upload_resp = client_client.post("/api/parser/upload", files=files)
    report_id = upload_resp.json()["report_id"]
    item_id = upload_resp.json()["negative_items"][0]["id"]
    gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "Paid"
    })
    letter_id = gen_resp.json()["letter_id"]
    
    resp = client_client.post("/api/dispute/mail", json={
        "letter_id": letter_id,
        "recipient_bureau": "Super Bureau"
    })
    assert resp.status_code == 400

def test_t2_agency_metrics_no_clients(public_client):
    """Case 39: Agency metrics for a brand-new agency return 0.0 metrics correctly."""
    timestamp = int(time.time() * 1000)
    email = f"empty_agency_{timestamp}@test.com"
    public_client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": "agency",
        "company_name": "Empty Agency Corp"
    })
    tok_resp = public_client.post("/api/auth/token", data={"username": email, "password": "Password123!"})
    token = tok_resp.json()["access_token"]
    
    resp = public_client.get("/api/agency/metrics", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["billing_summary"]["active_clients_count"] == 0
    assert data["billing_summary"]["monthly_recurring_revenue"] == 0.0
    assert data["dispute_metrics"]["total_disputed"] == 0

def test_t2_client_status_no_disputes(client_client):
    """Case 40: Status for client with zero disputes lists 0 counts."""
    resp = client_client.get("/api/client/status")
    assert resp.status_code == 200
    summary = resp.json()["disputes_summary"]
    assert summary["total"] == 0
    assert summary["pending"] == 0


# =====================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (pairwise coverage, total >=4)
# =====================================================================

def test_t3_cross_report_and_dispute_flow(client_client):
    """Case 41: End-to-end mapping from report upload -> item extraction -> letter generation."""
    # 1. Upload report
    files = {"report": ("experian_report.txt", io.BytesIO(b"Credit data..."), "text/plain")}
    up_resp = client_client.post("/api/parser/upload", files=files)
    report_id = up_resp.json()["report_id"]
    negative_items = up_resp.json()["negative_items"]
    
    # 2. Select creditor & bureau
    selected_item = negative_items[0]
    
    # 3. Generate letter
    gen_payload = {
        "report_id": report_id,
        "item_ids": [selected_item["id"]],
        "reason": "Not my transaction"
    }
    gen_resp = client_client.post("/api/dispute/generate", json=gen_payload)
    assert gen_resp.status_code == 200
    letter_content = gen_resp.json()["content"]
    
    # Assert that details of the parsed item are in the dispute letter
    assert selected_item["creditor"] in letter_content
    assert str(selected_item["amount"]) in letter_content
    assert selected_item["bureau"] in letter_content

def test_t3_cross_compliance_check_and_mail(client_client):
    """Case 42: Intercept compliance check before mailing, fix, and send."""
    # 1. Upload report and generate letter
    files = {"report": ("report.txt", io.BytesIO(b"Report info"), "text/plain")}
    up_resp = client_client.post("/api/parser/upload", files=files)
    report_id = up_resp.json()["report_id"]
    item_id = up_resp.json()["negative_items"][0]["id"]
    
    # A non-compliant draft
    non_compliant_reason = "I guarantee deletion of this bad item!"
    gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": non_compliant_reason
    })
    letter_id = gen_resp.json()["letter_id"]
    letter_content = gen_resp.json()["content"]
    
    # Check compliance
    comp_resp = client_client.post("/api/dispute/compliance", json={"letter_content": letter_content})
    assert comp_resp.json()["compliant"] is False
    
    # Fix the issue by generating compliant letter
    compliant_reason = "This account is paid in full as of 2025."
    gen_resp_fixed = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": compliant_reason
    })
    fixed_letter_id = gen_resp_fixed.json()["letter_id"]
    fixed_letter_content = gen_resp_fixed.json()["content"]
    
    # Verify compliance passes
    comp_resp_fixed = client_client.post("/api/dispute/compliance", json={"letter_content": fixed_letter_content})
    assert comp_resp_fixed.json()["compliant"] is True
    
    # Mail the compliant letter
    mail_resp = client_client.post("/api/dispute/mail", json={
        "letter_id": fixed_letter_id,
        "recipient_bureau": "Equifax"
    })
    assert mail_resp.status_code == 200
    assert mail_resp.json()["status"] == "queued"

def test_t3_cross_agency_monitoring_client_onboarding(backend_url, agency_client):
    """Case 43: Agency registers client -> client uploads docs -> agency tracks onboarding updates."""
    # Find agency profile
    me_resp = agency_client.get("/api/auth/me")
    agency_id = me_resp.json()["agency"]["id"]
    
    # 1. Register Client under this agency
    timestamp = int(time.time() * 1000)
    client_username = f"tracked_client_{timestamp}"
    client_email = f"{client_username}@test.com"
    client_password = "Password123!"
    
    with httpx.Client(base_url=backend_url) as client:
        reg_resp = client.post("/api/auth/register", json={
            "email": client_email,
            "username": client_username,
            "password": client_password,
            "role": "client",
            "first_name": "Jane",
            "last_name": f"Tracked_{timestamp}",
            "agency_id": agency_id
        })
        assert reg_resp.status_code == 201
        
        # Log in as client
        tok_resp = client.post("/api/auth/token", data={"username": client_email, "password": client_password})
        client_token = tok_resp.json()["access_token"]
        
        # Client uploads address proof
        headers = {"Authorization": f"Bearer {client_token}"}
        up_resp = client.post(
            "/api/client/upload", 
            data={"document_type": "address_proof"}, 
            files={"file": ("utility.pdf", io.BytesIO(b"utility content"), "application/pdf")}, 
            headers=headers
        )
        assert up_resp.status_code == 201
        
    # 2. Agency lists clients and checks status/onboarding step
    clients_resp = agency_client.get("/api/agency/clients")
    assert clients_resp.status_code == 200
    
    # Locate client in agency list
    my_client = None
    for c in clients_resp.json():
        if c["last_name"] == f"Tracked_{timestamp}":
            my_client = c
            break
            
    assert my_client is not None
    assert my_client["onboarding_step"] == "document_uploaded"

def test_t3_cross_dispute_delivery_updates_metrics(backend_url, agency_client):
    """Case 44: Client mails letter -> USPS delivers -> agency metrics reflect update."""
    # Find agency profile
    me_resp = agency_client.get("/api/auth/me")
    agency_id = me_resp.json()["agency"]["id"]
    
    # Register client
    timestamp = int(time.time() * 1000)
    client_email = f"metrics_delivery_{timestamp}@test.com"
    
    with httpx.Client(base_url=backend_url) as client:
        client.post("/api/auth/register", json={
            "email": client_email,
            "password": "Password123!",
            "role": "client",
            "first_name": "Delivery",
            "last_name": "Track",
            "agency_id": agency_id
        })
        
        # Log in client
        tok_resp = client.post("/api/auth/token", data={"username": client_email, "password": "Password123!"})
        client_token = tok_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {client_token}"}
        
        # Upload & Mail
        up_resp = client.post("/api/parser/upload", files={"report": ("rep.txt", io.BytesIO(b"abc"), "text/plain")}, headers=headers)
        report_id = up_resp.json()["report_id"]
        item_id = up_resp.json()["negative_items"][0]["id"]
        
        gen_resp = client.post("/api/dispute/generate", json={
            "report_id": report_id,
            "item_ids": [item_id],
            "reason": "Not mine"
        }, headers=headers)
        letter_id = gen_resp.json()["letter_id"]
        
        mail_resp = client.post("/api/dispute/mail", json={
            "letter_id": letter_id,
            "recipient_bureau": "Equifax"
        }, headers=headers)
        mail_id = mail_resp.json()["mail_id"]
        
        # Check initial agency metrics
        metrics_resp_init = agency_client.get("/api/agency/metrics")
        assert metrics_resp_init.json()["dispute_metrics"]["deleted"] == 0
        
        # Simulate USPS Delivery
        client.post(f"/api/test/simulate-delivery?mail_id={mail_id}")
        
    # Check agency metrics updated with deleted (dispute success)
    metrics_resp = agency_client.get("/api/agency/metrics")
    assert metrics_resp.status_code == 200
    assert metrics_resp.json()["dispute_metrics"]["deleted"] == 1
    assert metrics_resp.json()["dispute_metrics"]["success_rate"] == 1.0


# =====================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (>=5 scenarios)
# =====================================================================

def test_t4_scenario_1_client_onboarding(backend_url, agency_client):
    """Scenario 1: Complete new client onboarding sequence and validation.
    
    1. Agency registers a client in onboarding state.
    2. Client uploads ID verification. Status should remain onboarding.
    3. Client uploads address verification. Status changes to active, step completed.
    4. Agency lists clients and verifies active status.
    """
    me_resp = agency_client.get("/api/auth/me")
    agency_id = me_resp.json()["agency"]["id"]
    
    timestamp = int(time.time() * 1000)
    email = f"scenario1_client_{timestamp}@test.com"
    
    with httpx.Client(base_url=backend_url) as client:
        # Step 1: Register
        client.post("/api/auth/register", json={
            "email": email,
            "password": "Password123!",
            "role": "client",
            "first_name": "Scen1",
            "last_name": f"Onboard_{timestamp}",
            "agency_id": agency_id
        })
        
        tok_resp = client.post("/api/auth/token", data={"username": email, "password": "Password123!"})
        client_token = tok_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {client_token}"}
        
        # Get initial client status
        status_resp = client.get("/api/client/status", headers=headers)
        assert status_resp.json()["status"] == "onboarding"
        assert status_resp.json()["onboarding_step"] == "document_upload"
        
        # Step 2: Upload ID Proof
        files_id = {"file": ("license.jpg", io.BytesIO(b"some license image data"), "image/jpeg")}
        client.post("/api/client/upload", data={"document_type": "id_proof"}, files=files_id, headers=headers)
        
        status_resp = client.get("/api/client/status", headers=headers)
        assert status_resp.json()["status"] == "onboarding"
        assert status_resp.json()["onboarding_step"] == "document_uploaded"
        
        # Step 3: Upload Address Proof
        files_addr = {"file": ("bill.jpg", io.BytesIO(b"some bill image data"), "image/jpeg")}
        client.post("/api/client/upload", data={"document_type": "address_proof"}, files=files_addr, headers=headers)
        
        status_resp = client.get("/api/client/status", headers=headers)
        # Both documents uploaded, client should now be active
        assert status_resp.json()["status"] == "active"
        assert status_resp.json()["onboarding_step"] == "completed"
        
    # Step 4: Agency checks list
    clients_resp = agency_client.get("/api/agency/clients")
    my_client = next(c for c in clients_resp.json() if c["last_name"] == f"Onboard_{timestamp}")
    assert my_client["status"] == "active"
    assert my_client["onboarding_step"] == "completed"

def test_t4_scenario_2_multi_bureau_dispute(client_client):
    """Scenario 2: Generate and mail separate dispute letters for multiple bureaus.
    
    1. Client uploads report with multiple negative items (Equifax & Experian).
    2. Client groups selected items by bureau.
    3. Client generates a custom dispute letter for Equifax.
    4. Client generates a custom dispute letter for Experian.
    5. Client dispatches both letters and tracks USPS tracking codes.
    """
    # Step 1: Upload
    files = {"report": ("bureau_report.txt", io.BytesIO(b"Report data..."), "text/plain")}
    up_resp = client_client.post("/api/parser/upload", files=files)
    report_id = up_resp.json()["report_id"]
    items = up_resp.json()["negative_items"]
    
    # Step 2: Group by bureau
    equifax_items = [item["id"] for item in items if item["bureau"] == "Equifax"]
    experian_items = [item["id"] for item in items if item["bureau"] == "Experian"]
    
    assert len(equifax_items) > 0
    assert len(experian_items) > 0
    
    # Step 3: Generate Equifax Letter
    eq_gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": equifax_items,
        "reason": "Not my Equifax account"
    })
    eq_letter_id = eq_gen_resp.json()["letter_id"]
    
    # Step 4: Generate Experian Letter
    ex_gen_resp = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": experian_items,
        "reason": "Not my Experian account"
    })
    ex_letter_id = ex_gen_resp.json()["letter_id"]
    
    # Step 5: Mail Equifax Letter
    eq_mail_resp = client_client.post("/api/dispute/mail", json={
        "letter_id": eq_letter_id,
        "recipient_bureau": "Equifax"
    })
    assert eq_mail_resp.json()["status"] == "queued"
    assert eq_mail_resp.json()["tracking_number"].startswith("USPS-LOB-")
    
    # Mail Experian Letter
    ex_mail_resp = client_client.post("/api/dispute/mail", json={
        "letter_id": ex_letter_id,
        "recipient_bureau": "Experian"
    })
    assert ex_mail_resp.json()["status"] == "queued"
    assert ex_mail_resp.json()["tracking_number"].startswith("USPS-LOB-")

def test_t4_scenario_3_compliance_remediation_loop(client_client):
    """Scenario 3: Non-compliant draft remediation loop.
    
    1. Client drafts letter with non-compliant claims.
    2. Runs compliance check -> validation fails.
    3. Client reads suggestions, drafts compliant letter.
    4. Runs compliance check -> validation passes.
    5. Dispatches compliant letter via Lob simulator.
    """
    # 1. Upload report
    files = {"report": ("report.txt", io.BytesIO(b"Credit info"), "text/plain")}
    up_resp = client_client.post("/api/parser/upload", files=files)
    report_id = up_resp.json()["report_id"]
    item_id = up_resp.json()["negative_items"][0]["id"]
    
    # 2. Draft non-compliant letter (reason with prohibited keyword)
    bad_gen = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "Clean credit in 24 hours!"
    })
    bad_letter_id = bad_gen.json()["letter_id"]
    bad_content = bad_gen.json()["content"]
    
    # Compliance check fails
    comp1 = client_client.post("/api/dispute/compliance", json={"letter_content": bad_content})
    assert comp1.json()["compliant"] is False
    assert "clean credit in 24 hours" in comp1.json()["prohibited_claims_found"]
    suggestions = comp1.json()["suggestions"]
    assert len(suggestions) > 0
    
    # 3 & 4. Draft compliant letter using suggestion guidance
    good_gen = client_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [item_id],
        "reason": "This listing is inaccurate; verification is requested."
    })
    good_letter_id = good_gen.json()["letter_id"]
    good_content = good_gen.json()["content"]
    
    comp2 = client_client.post("/api/dispute/compliance", json={"letter_content": good_content})
    assert comp2.json()["compliant"] is True
    
    # 5. Mail
    mail_resp = client_client.post("/api/dispute/mail", json={
        "letter_id": good_letter_id,
        "recipient_bureau": "Equifax"
    })
    assert mail_resp.status_code == 200
    assert mail_resp.json()["status"] == "queued"

def test_t4_scenario_4_agency_billing_accumulation(backend_url, agency_client):
    """Scenario 4: Verify agency billing metrics accumulate correctly as active clients are onboarded.
    
    1. Fetch current agency metrics.
    2. Register 3 new clients.
    3. Complete onboarding for all 3 clients (uploading both ID and address verification).
    4. Fetch agency metrics again. Verify active clients count = +3, and MRR increased by 3 * $99.
    """
    # 1. Fetch current metrics
    me_resp = agency_client.get("/api/auth/me")
    agency_id = me_resp.json()["agency"]["id"]
    
    init_metrics = agency_client.get("/api/agency/metrics").json()
    init_active = init_metrics["billing_summary"]["active_clients_count"]
    init_mrr = init_metrics["billing_summary"]["monthly_recurring_revenue"]
    
    # 2. Register 3 new clients and onboard them
    with httpx.Client(base_url=backend_url) as client:
        for i in range(3):
            timestamp = int(time.time() * 1000) + i
            email = f"billing_client_{i}_{timestamp}@test.com"
            
            # Register
            client.post("/api/auth/register", json={
                "email": email,
                "password": "Password123!",
                "role": "client",
                "first_name": "BClient",
                "last_name": f"Billing_{i}_{timestamp}",
                "agency_id": agency_id
            })
            
            # Login
            tok_resp = client.post("/api/auth/token", data={"username": email, "password": "Password123!"})
            token = tok_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Upload ID proof
            files_id = {"file": ("id.jpg", io.BytesIO(b"license bytes"), "image/jpeg")}
            client.post("/api/client/upload", data={"document_type": "id_proof"}, files=files_id, headers=headers)
            
            # Upload address proof
            files_addr = {"file": ("address.jpg", io.BytesIO(b"bill bytes"), "image/jpeg")}
            client.post("/api/client/upload", data={"document_type": "address_proof"}, files=files_addr, headers=headers)
            
    # 3. Verify metrics updated
    new_metrics = agency_client.get("/api/agency/metrics").json()
    assert new_metrics["billing_summary"]["active_clients_count"] == init_active + 3
    assert new_metrics["billing_summary"]["monthly_recurring_revenue"] == init_mrr + (3 * 99.0)

def test_t4_scenario_5_end_to_end_registration_to_mailing(backend_url, public_client):
    """Scenario 5: Complete E2E business flow starting from raw registration down to USPS dispatch.
    
    1. Register agency and log in.
    2. Register client linked to registered agency and log in.
    3. Client uploads credit report and extracts negative items.
    4. Client generates a dispute letter for selected Equifax collection item.
    5. Client runs compliance check, which passes successfully.
    6. Client dispatches the dispute letter via Lob mailing simulator.
    7. Client calls /client/status to verify 1 dispute is sent.
    8. Agency calls /agency/metrics to verify the metrics show 1 dispute has been dispatched.
    """
    timestamp = int(time.time() * 1000)
    
    # 1. Register and log in Agency
    agency_email = f"scen5_agency_{timestamp}@test.com"
    agency_pass = "Password123!"
    reg_agency = public_client.post("/api/auth/register", json={
        "email": agency_email,
        "password": agency_pass,
        "role": "agency",
        "company_name": f"Scenario 5 Agency {timestamp}"
    })
    assert reg_agency.status_code == 201
    
    tok_agency = public_client.post("/api/auth/token", data={"username": agency_email, "password": agency_pass})
    agency_token = tok_agency.json()["access_token"]
    
    me_agency = public_client.get("/api/auth/me", headers={"Authorization": f"Bearer {agency_token}"})
    agency_id = me_agency.json()["agency"]["id"]
    
    # 2. Register and log in Client
    client_email = f"scen5_client_{timestamp}@test.com"
    client_pass = "Password123!"
    reg_client = public_client.post("/api/auth/register", json={
        "email": client_email,
        "password": client_pass,
        "role": "client",
        "first_name": "S5",
        "last_name": f"Client_{timestamp}",
        "agency_id": agency_id
    })
    assert reg_client.status_code == 201
    
    tok_client = public_client.post("/api/auth/token", data={"username": client_email, "password": client_pass})
    client_token = tok_client.json()["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}
    
    # 3. Client uploads credit report & extracts negative items
    files = {"report": ("report_scen5.txt", io.BytesIO(b"Credit Report for Scenario 5"), "text/plain")}
    up_resp = public_client.post("/api/parser/upload", files=files, headers=client_headers)
    assert up_resp.status_code == 200
    report_id = up_resp.json()["report_id"]
    items = up_resp.json()["negative_items"]
    
    # Find Equifax item
    eq_item = next(item for item in items if item["bureau"] == "Equifax")
    
    # 4. Generate dispute letter
    gen_resp = public_client.post("/api/dispute/generate", json={
        "report_id": report_id,
        "item_ids": [eq_item["id"]],
        "reason": "This collections item belongs to someone else."
    }, headers=client_headers)
    assert gen_resp.status_code == 200
    letter_id = gen_resp.json()["letter_id"]
    letter_content = gen_resp.json()["content"]
    
    # 5. Check compliance
    comp_resp = public_client.post("/api/dispute/compliance", json={"letter_content": letter_content}, headers=client_headers)
    assert comp_resp.status_code == 200
    assert comp_resp.json()["compliant"] is True
    
    # 6. Mail dispute letter
    mail_resp = public_client.post("/api/dispute/mail", json={
        "letter_id": letter_id,
        "recipient_bureau": "Equifax"
    }, headers=client_headers)
    assert mail_resp.status_code == 200
    assert mail_resp.json()["status"] == "queued"
    
    # 7. Check client status
    status_resp = public_client.get("/api/client/status", headers=client_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["disputes_summary"]["total"] == 1
    
    # 8. Check agency metrics
    agency_headers = {"Authorization": f"Bearer {agency_token}"}
    metrics_resp = public_client.get("/api/agency/metrics", headers=agency_headers)
    assert metrics_resp.status_code == 200
    assert metrics_resp.json()["dispute_metrics"]["total_disputed"] == 1
