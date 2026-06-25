"""
Database seed script for Credit Repair SaaS.

Creates demo data:
  - 1 agency (CreditFix Pro)
  - 2 agency staff users
  - 5 client profiles at various stages
  - Uploaded sample reports with parsed negative items
  - Some existing disputes and letters

Usage:
    cd backend
    python seed_data.py
"""

import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.agency import Agency
from app.models.client import Client
from app.models.document import ClientDocument
from app.models.credit_report import CreditReport
from app.models.dispute import DisputeLetter, DisputeItem
from app.models.billing import BillingTransaction
from app.models.audit_log import AuditLog, MailingLog


def utcnow():
    return datetime.now(timezone.utc)


def seed():
    # Recreate all tables
    print("[seed] Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ── 1. Agency Staff User ───────────────────────────────────────────
        print("[seed] Creating agency user and profile...")
        agency_user = User(
            email="admin@creditfixpro.com",
            hashed_password=get_password_hash("password123"),
            role="agency",
            is_active=True,
        )
        db.add(agency_user)
        db.flush()

        agency = Agency(
            user_id=agency_user.id,
            company_name="CreditFix Pro",
            phone="(555) 100-2000",
        )
        db.add(agency)
        db.flush()

        # Second agency staff user
        staff_user_2 = User(
            email="staff@creditfixpro.com",
            hashed_password=get_password_hash("password123"),
            role="agency",
            is_active=True,
        )
        db.add(staff_user_2)
        db.flush()

        staff_agency_2 = Agency(
            user_id=staff_user_2.id,
            company_name="CreditFix Pro",  # Same company, different user
            phone="(555) 100-2001",
        )
        db.add(staff_agency_2)
        db.flush()

        print(f"  [OK] Agency: CreditFix Pro (ID={agency.id})")
        print(f"  [OK] Staff: admin@creditfixpro.com, staff@creditfixpro.com")

        # ── 2. Client Users & Profiles ─────────────────────────────────────
        print("[seed] Creating 5 client profiles...")

        client_data = [
            {
                "email": "john.doe@email.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "(555) 200-1001",
                "status": "active",
                "onboarding_step": "report_parsed",
            },
            {
                "email": "jane.smith@email.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "(555) 200-1002",
                "status": "active",
                "onboarding_step": "report_parsed",
            },
            {
                "email": "robert.johnson@email.com",
                "first_name": "Robert",
                "last_name": "Johnson",
                "phone": "(555) 200-1003",
                "status": "documents_uploaded",
                "onboarding_step": "document_uploaded",
            },
            {
                "email": "sarah.williams@email.com",
                "first_name": "Sarah",
                "last_name": "Williams",
                "phone": "(555) 200-1004",
                "status": "onboarding",
                "onboarding_step": "document_upload",
            },
            {
                "email": "michael.brown@email.com",
                "first_name": "Michael",
                "last_name": "Brown",
                "phone": "(555) 200-1005",
                "status": "active",
                "onboarding_step": "report_parsed",
            },
        ]

        clients = []
        for cd in client_data:
            user = User(
                email=cd["email"],
                hashed_password=get_password_hash("password123"),
                role="client",
                is_active=True,
            )
            db.add(user)
            db.flush()

            client = Client(
                user_id=user.id,
                agency_id=agency.id,
                first_name=cd["first_name"],
                last_name=cd["last_name"],
                phone=cd["phone"],
                status=cd["status"],
                onboarding_step=cd["onboarding_step"],
            )
            db.add(client)
            db.flush()
            clients.append(client)
            print(f"  [OK] Client: {cd['first_name']} {cd['last_name']} ({cd['status']})")

        # ── 3. Sample Credit Reports ───────────────────────────────────────
        print("[seed] Loading sample credit reports...")

        sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
        report_assignments = [
            (clients[0], "sample_report_equifax.json"),    # John Doe
            (clients[1], "sample_report_experian.json"),   # Jane Smith
            (clients[4], "sample_report_transunion.json"), # Michael Brown
        ]

        credit_reports = []
        for client, filename in report_assignments:
            filepath = os.path.join(sample_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    raw_content = f.read()
            else:
                raw_content = "{}"
                print(f"  [!] File not found: {filepath}")

            report = CreditReport(
                client_id=client.id,
                filename=filename,
                file_path=f"sample_data/{filename}",
                status="parsed",
                raw_content=raw_content,
            )
            db.add(report)
            db.flush()
            credit_reports.append((client, report, raw_content))
            print(f"  [OK] Report: {filename} -> {client.first_name} {client.last_name}")

        # ── 4. Parsed Negative Items (DisputeItems) ────────────────────────
        print("[seed] Creating dispute items from sample reports...")

        all_dispute_items = []
        for client, report, raw_content in credit_reports:
            try:
                data = json.loads(raw_content)
            except json.JSONDecodeError:
                continue

            bureau = data.get("bureau", "equifax").capitalize()
            accounts = data.get("accounts", [])

            for acct in accounts:
                if acct.get("status") != "derogatory":
                    continue

                # Determine negative type
                payment_history = acct.get("payment_history", "").lower()
                if "collection" in payment_history:
                    negative_type = "collection"
                elif "charge" in payment_history:
                    negative_type = "charge_off"
                elif "late" in payment_history or "days" in payment_history:
                    negative_type = "late_payment"
                elif "repossession" in payment_history:
                    negative_type = "collection"  # Mapped to collection for DB
                else:
                    negative_type = "collection"

                item = DisputeItem(
                    client_id=client.id,
                    credit_report_id=report.id,
                    bureau=bureau,
                    creditor_name=acct["creditor"],
                    account_number=acct.get("account_number_last4"),
                    balance=acct.get("balance", 0.0),
                    negative_type=negative_type,
                    status="pending",
                )
                db.add(item)
                db.flush()
                all_dispute_items.append((client, item))
                print(f"    • {acct['creditor']} (${acct.get('balance', 0):.2f}) → {negative_type}")

            # Also add hard inquiries as dispute items
            for inq in data.get("inquiries", []):
                if inq.get("type") == "hard":
                    item = DisputeItem(
                        client_id=client.id,
                        credit_report_id=report.id,
                        bureau=bureau,
                        creditor_name=inq["creditor"],
                        account_number=None,
                        balance=0.0,
                        negative_type="collection",  # inquiries mapped to collection type
                        dispute_reason="Unauthorized hard inquiry",
                        status="pending",
                    )
                    db.add(item)
                    db.flush()
                    all_dispute_items.append((client, item))

        # ── 5. Disputes & Letters ──────────────────────────────────────────
        print("[seed] Creating sample disputes and letters...")

        # Create dispute letters for some items (first 3 items)
        from app.services.dispute_generator import generate_dispute_letter

        disputes_created = 0
        for client, item in all_dispute_items[:3]:
            letter_content = generate_dispute_letter(
                client_first_name=client.first_name,
                client_last_name=client.last_name,
                client_address=None,
                client_ssn_last4=None,
                client_dob=None,
                bureau=item.bureau,
                account_name=item.creditor_name,
                account_last4=item.account_number,
                item_type=item.negative_type or "collection",
                balance=item.balance or 0.0,
            )

            letter = DisputeLetter(
                client_id=client.id,
                bureau=item.bureau,
                letter_content=letter_content,
                status="draft",
            )
            db.add(letter)
            db.flush()

            item.dispute_letter_id = letter.id
            item.status = "pending"
            item.disputed_at = utcnow()
            disputes_created += 1

        print(f"  [OK] Created {disputes_created} dispute letters")

        # Mark one dispute as mailed
        if disputes_created > 0:
            first_letter = db.query(DisputeLetter).first()
            if first_letter:
                first_letter.status = "mailed"
                first_letter.mail_tracking_id = "USPS-CR-DEMO12345678"
                first_letter.sent_at = utcnow() - timedelta(days=3)

                mailing = MailingLog(
                    dispute_letter_id=first_letter.id,
                    recipient_name=f"{first_letter.bureau.title()} Dispute Department",
                    recipient_address="P.O. Box 740256, Atlanta, GA 30374-0256",
                    bureau=first_letter.bureau.lower(),
                    tracking_number="USPS-CR-DEMO12345678",
                    status="mailed",
                    dispatched_at=utcnow() - timedelta(days=3),
                    delivery_estimate=utcnow() + timedelta(days=2),
                )
                db.add(mailing)
                print("  [OK] Marked 1 letter as mailed with tracking")

        # ── 6. Audit Logs ──────────────────────────────────────────────────
        print("[seed] Creating sample audit logs...")
        audit_entries = [
            AuditLog(
                user_id=agency_user.id,
                action="seed_database",
                resource_type="system",
                resource_id=None,
                ip_address="127.0.0.1",
                details={"message": "Database seeded with demo data"},
            ),
            AuditLog(
                user_id=agency_user.id,
                action="create_client",
                resource_type="client",
                resource_id=clients[0].id,
                ip_address="127.0.0.1",
                details={"client_name": "John Doe"},
            ),
        ]
        db.add_all(audit_entries)
        print(f"  [OK] Created {len(audit_entries)} audit log entries")

        # ── 7. Billing Transactions ────────────────────────────────────────
        print("[seed] Creating sample billing transactions...")
        billing_txns = [
            BillingTransaction(
                agency_id=agency.id,
                client_id=clients[0].id,
                amount=99.00,
                description="Monthly subscription - John Doe",
                status="paid",
            ),
            BillingTransaction(
                agency_id=agency.id,
                client_id=clients[1].id,
                amount=99.00,
                description="Monthly subscription - Jane Smith",
                status="paid",
            ),
            BillingTransaction(
                agency_id=agency.id,
                client_id=clients[4].id,
                amount=99.00,
                description="Monthly subscription - Michael Brown",
                status="pending",
            ),
        ]
        db.add_all(billing_txns)
        print(f"  [OK] Created {len(billing_txns)} billing transactions")

        # ── Commit ─────────────────────────────────────────────────────────
        db.commit()
        print("\n" + "=" * 60)
        print("[OK] Database seeded successfully!")
        print("=" * 60)
        print("\nDemo Credentials:")
        print("  Agency Staff:  admin@creditfixpro.com / password123")
        print("  Agency Staff:  staff@creditfixpro.com / password123")
        print("  Client:        john.doe@email.com     / password123")
        print("  Client:        jane.smith@email.com   / password123")
        print("  Client:        robert.johnson@email.com / password123")
        print("  Client:        sarah.williams@email.com / password123")
        print("  Client:        michael.brown@email.com  / password123")
        print(f"\nTotal dispute items: {len(all_dispute_items)}")
        print(f"Total dispute letters: {disputes_created}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
