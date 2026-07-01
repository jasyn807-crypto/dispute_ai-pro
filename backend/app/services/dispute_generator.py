"""
LLM-simulated dispute letter generator.

Generates realistic dispute letters using rotating templates with randomized
phrasing. No actual API calls are made – all generation is local.
"""

import random
from datetime import datetime, timezone
from typing import Optional


# ── Template Components ────────────────────────────────────────────────────

OPENING_SALUTATIONS = [
    "To Whom It May Concern:",
    "Dear Dispute Resolution Department:",
    "Dear Credit Bureau Representative:",
    "To the Attention of the Consumer Dispute Department:",
]

IDENTITY_PARAGRAPHS = [
    (
        "I am writing to formally dispute the accuracy of certain information "
        "in my credit file maintained by your bureau. Pursuant to the Fair Credit "
        "Reporting Act (FCRA), 15 U.S.C. § 1681i, I am requesting that you "
        "investigate and completely remove the inaccurate information identified below."
    ),
    (
        "Under the provisions of the Fair Credit Reporting Act, Section 611 "
        "(15 U.S.C. § 1681i), I am exercising my right to dispute the following "
        "item(s) that appear on my credit report. I believe the information is "
        "inaccurate and request a thorough investigation and removal of this negative item."
    ),
    (
        "This letter serves as a formal dispute regarding information currently "
        "reported on my credit file. In accordance with the Fair Credit Reporting "
        "Act (FCRA), specifically Section 611, I am requesting verification of "
        "the disputed item(s) listed below, and that you delete it from my record."
    ),
]

DISPUTE_REASON_TEMPLATES = {
    "collection": [
        (
            "The collection account listed under {account_name} (account ending "
            "in {account_last4}) with a reported balance of ${balance:.2f} is being "
            "disputed. I do not recognize this debt, and I request that you verify "
            "this account with the furnisher pursuant to FCRA Section 611(a)."
        ),
        (
            "I am disputing the collection entry from {account_name} "
            "(account ****{account_last4}), reporting a balance of ${balance:.2f}. "
            "This account has not been properly validated under the Fair Debt "
            "Collection Practices Act (FDCPA), 15 U.S.C. § 1692g. I request "
            "immediate verification or removal."
        ),
        (
            "The collection account from {account_name} (****{account_last4}) "
            "showing ${balance:.2f} is inaccurate. I have no record of this "
            "obligation and request verification of this tradeline in accordance "
            "with my rights under the FCRA."
        ),
    ],
    "late_payment": [
        (
            "The late payment notation on the account with {account_name} "
            "(account ending in {account_last4}) is inaccurate. I have always "
            "made payments on this account in a timely manner, and I request "
            "that this derogatory mark be investigated and completely removed per FCRA "
            "Section 611."
        ),
        (
            "I dispute the reported late payment(s) on my {account_name} account "
            "(****{account_last4}). My records indicate that all payments were "
            "made by their respective due dates. Please conduct a reinvestigation "
            "as required under 15 U.S.C. § 1681i and remove this inaccurate record."
        ),
    ],
    "charge_off": [
        (
            "The charge-off reported by {account_name} (account ending in "
            "{account_last4}) with a balance of ${balance:.2f} is disputed. "
            "I believe this account has been inaccurately reported and request "
            "verification from the original creditor pursuant to FCRA Section 611."
        ),
        (
            "I am formally disputing the charge-off entry from {account_name} "
            "(****{account_last4}), listed with a balance of ${balance:.2f}. "
            "The status of this account is inaccurate. Under 15 U.S.C. § 1681i, "
            "I request that you verify this information or remove it from my file."
        ),
    ],
    "bankruptcy": [
        (
            "The bankruptcy record appearing on my credit report is inaccurate. "
            "I request that you verify this public record with the appropriate "
            "court and remove this record in accordance with FCRA Section 611."
        ),
    ],
    "inquiry": [
        (
            "The hard inquiry from {account_name} dated {date_reported} was not "
            "authorized by me. I did not apply for credit with this entity and "
            "request that this unauthorized inquiry be removed from my credit "
            "file immediately per FCRA Section 604."
        ),
        (
            "I am disputing the inquiry from {account_name} listed on my credit "
            "report. I have no knowledge of authorizing this credit pull. Please "
            "provide proof of my written authorization or remove this inquiry "
            "from my file."
        ),
    ],
    "repossession": [
        (
            "The repossession entry from {account_name} (account ending in "
            "{account_last4}) with a reported balance of ${balance:.2f} is "
            "inaccurate. I request full verification of this account including "
            "the deficiency balance calculation and sale documentation per "
            "FCRA Section 611."
        ),
    ],
}

DEFAULT_DISPUTE_REASON = [
    (
        "The account listed under {account_name} (account ending in "
        "{account_last4}) with a balance of ${balance:.2f} is being disputed. "
        "I believe this information is inaccurate and request verification "
        "pursuant to FCRA Section 611(a)."
    ),
]

VERIFICATION_REQUESTS = [
    (
        "Please provide me with the following documentation to support the "
        "accuracy of this reported information:\n"
        "  1. The original signed contract or agreement bearing my signature\n"
        "  2. Complete payment history for the account\n"
        "  3. Documentation from the original creditor verifying the debt\n"
        "  4. Proof that this account belongs to me and not another individual"
    ),
    (
        "In accordance with my rights under the FCRA, I am requesting the "
        "following verification:\n"
        "  • A copy of the original creditor's records establishing the debt\n"
        "  • Complete account statements and payment history\n"
        "  • Documentation showing the account belongs to me\n"
        "  • The method of verification used in your investigation"
    ),
]

CLOSING_PARAGRAPHS = [
    (
        "Under FCRA Section 611(a)(1), you are required to conduct a reasonable "
        "investigation within 30 days of receiving this dispute. If the information "
        "cannot be verified, it must be promptly deleted. Please send "
        "me an updated copy of my credit report reflecting the deletion made as a "
        "result of this investigation."
    ),
    (
        "Please be advised that under the FCRA, you must complete your investigation "
        "within 30 days and notify me of the results. If the disputed information "
        "is found to be inaccurate or unverifiable, I expect it to be "
        "removed immediately. I request a free copy of my updated credit report "
        "upon completion of the investigation."
    ),
    (
        "I expect your investigation to be completed within the 30-day period "
        "mandated by federal law. Should you fail to investigate this matter or "
        "fail to respond within the required timeframe, I reserve the right to "
        "take legal action, including filing a complaint with the Consumer "
        "Financial Protection Bureau (CFPB)."
    ),
]

CROA_DISCLOSURE = (
    "\n\n--- CREDIT REPAIR ORGANIZATIONS ACT (CROA) DISCLOSURE ---\n"
    "You have the right to dispute inaccurate information in your credit report "
    "by contacting the credit bureau directly. You are not required to use a "
    "credit repair organization to do so. No one can legally remove accurate and "
    "timely negative information from a credit report. Under federal law, a credit "
    "repair organization cannot require you to waive your rights under the Credit "
    "Repair Organizations Act."
)

SIGN_OFFS = [
    "Sincerely,",
    "Respectfully,",
    "Thank you for your prompt attention to this matter,",
    "Regards,",
]

BUREAU_ADDRESSES = {
    "equifax": (
        "Equifax Information Services LLC\n"
        "P.O. Box 740256\n"
        "Atlanta, GA 30374-0256"
    ),
    "experian": (
        "Experian\n"
        "P.O. Box 4500\n"
        "Allen, TX 75013"
    ),
    "transunion": (
        "TransUnion LLC\n"
        "Consumer Dispute Center\n"
        "P.O. Box 2000\n"
        "Chester, PA 19016"
    ),
}


# ── Generator ──────────────────────────────────────────────────────────────

def generate_dispute_letter(
    client_first_name: str,
    client_last_name: str,
    client_address: Optional[str],
    client_ssn_last4: Optional[str],
    client_dob: Optional[str],
    bureau: str,
    account_name: str,
    account_last4: Optional[str],
    item_type: str,
    balance: float,
    date_reported: Optional[str] = None,
    original_creditor: Optional[str] = None,
) -> str:
    """
    Generate a unique dispute letter. Uses OpenAI GPT-4o-mini if OPENAI_API_KEY is present,
    otherwise falls back to templates with randomized phrasing.
    """
    import os
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            import httpx
            prompt = (
                f"You are an expert FCRA/FDCPA legal compliance dispute letter generator. "
                f"Generate a professional, highly customized, legally compliant dispute letter under FCRA and FDCPA guidelines.\n"
                f"Client Name: {client_first_name} {client_last_name}\n"
                f"Client Address: {client_address or '[Address on file]'}\n"
                f"Client SSN Last 4: {client_ssn_last4 or 'N/A'}\n"
                f"Client DOB: {client_dob or 'N/A'}\n"
                f"Credit Bureau: {bureau}\n"
                f"Disputed Account Name: {account_name}\n"
                f"Disputed Account Last 4 digits: {account_last4 or 'N/A'}\n"
                f"Item Type: {item_type}\n"
                f"Reported Balance: ${balance:.2f}\n"
                f"Date Reported: {date_reported or 'N/A'}\n"
                f"Original Creditor: {original_creditor or 'N/A'}\n\n"
                f"IMPORTANT: The goal of this dispute is to use reporting errors/inaccuracies to get the negative item completely removed or deleted from the client's credit file. "
                f"Do NOT ask the credit bureau to correct the details or fix the errors while leaving the negative item active. "
                f"Demand the complete removal or deletion of the entire negative tradeline due to the inaccuracies.\n\n"
                f"Output only the generated letter content. Do not include extra conversational text or markdown styling. Just output the text of the letter."
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            res = httpx.post(url, headers=headers, json=payload, timeout=30.0)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if text and text.strip():
                    return text.strip()
        except Exception:
            pass

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            prompt = (
                f"Generate a professional, highly customized, legally compliant dispute letter under FCRA and FDCPA guidelines.\n"
                f"Client Name: {client_first_name} {client_last_name}\n"
                f"Client Address: {client_address or '[Address on file]'}\n"
                f"Client SSN Last 4: {client_ssn_last4 or 'N/A'}\n"
                f"Client DOB: {client_dob or 'N/A'}\n"
                f"Credit Bureau: {bureau}\n"
                f"Disputed Account Name: {account_name}\n"
                f"Disputed Account Last 4 digits: {account_last4 or 'N/A'}\n"
                f"Item Type: {item_type}\n"
                f"Reported Balance: ${balance:.2f}\n"
                f"Date Reported: {date_reported or 'N/A'}\n"
                f"Original Creditor: {original_creditor or 'N/A'}\n\n"
                f"IMPORTANT: The goal of this dispute is to use reporting errors/inaccuracies to get the negative item completely removed or deleted from the client's credit file. "
                f"Do NOT ask the credit bureau to correct the details or fix the errors while leaving the negative item active. "
                f"Demand the complete removal or deletion of the entire negative tradeline due to the inaccuracies.\n\n"
                f"Output only the generated letter content. Do not include extra conversational text."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert FCRA/FDCPA legal compliance dispute letter generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception:
            pass


    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    bureau_lower = bureau.lower()
    bureau_address = BUREAU_ADDRESSES.get(bureau_lower, f"{bureau}\n[Address on file]")

    # Fill template variables
    fmt = {
        "account_name": account_name,
        "account_last4": account_last4 or "XXXX",
        "balance": balance or 0.0,
        "date_reported": date_reported or "N/A",
        "original_creditor": original_creditor or account_name,
    }

    # Header
    header = (
        f"{client_first_name} {client_last_name}\n"
        f"{client_address or '[Address on file]'}\n\n"
        f"Date: {today}\n\n"
        f"{bureau_address}\n\n"
    )

    # Personal identification block
    id_block = "RE: Dispute of Inaccurate Credit Information\n\n"
    if client_ssn_last4:
        id_block += f"SSN (last 4): ***-**-{client_ssn_last4}\n"
    if client_dob:
        id_block += f"Date of Birth: {client_dob}\n"
    id_block += "\n"

    # Salutation
    salutation = random.choice(OPENING_SALUTATIONS) + "\n\n"

    # Opening paragraph
    opening = random.choice(IDENTITY_PARAGRAPHS) + "\n\n"

    # Dispute reason – pick template based on item type
    reason_templates = DISPUTE_REASON_TEMPLATES.get(item_type, DEFAULT_DISPUTE_REASON)
    reason = random.choice(reason_templates).format(**fmt)
    if original_creditor and original_creditor != account_name:
        reason += f"\n\nOriginal Creditor: {original_creditor}"
    reason += "\n\n"

    # Verification request
    verification = random.choice(VERIFICATION_REQUESTS) + "\n\n"

    # Closing
    closing = random.choice(CLOSING_PARAGRAPHS) + "\n\n"

    # CROA disclosure (required for credit repair organizations)
    croa = CROA_DISCLOSURE + "\n\n"

    # Sign-off
    sign_off = (
        f"{random.choice(SIGN_OFFS)}\n\n"
        f"{client_first_name} {client_last_name}\n"
    )

    return header + id_block + salutation + opening + reason + verification + closing + croa + sign_off

