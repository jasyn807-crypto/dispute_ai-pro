"""
Compliance checker for dispute letters.

Scans letters for prohibited content including:
- Guarantees of credit score improvement
- Promises of item removal
- Misleading claims about success rates
- Unauthorized practice of law language
- Missing required CROA disclosures
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class ComplianceResult:
    """Result of a compliance scan."""
    passed: bool
    flags: List[str] = field(default_factory=list)
    notes: str = ""


# ── Prohibited Patterns ───────────────────────────────────────────────────

# Each entry is (compiled regex pattern, flag description)
PROHIBITED_PATTERNS = [
    # Guarantees of credit score improvement
    (
        re.compile(r"(?i)guarantee[ds]?\s+(?:your\s+)?(?:credit\s+)?score\s+(?:will\s+)?(?:increase|improve|go\s+up|rise)"),
        "Contains guarantee of credit score improvement"
    ),
    (
        re.compile(r"(?i)(?:we|I)\s+(?:can|will)\s+(?:definitely|certainly|absolutely)\s+(?:raise|boost|increase|improve)\s+(?:your\s+)?(?:credit\s+)?score"),
        "Contains guarantee of credit score improvement"
    ),
    (
        re.compile(r"(?i)guaranteed\s+(?:credit\s+)?(?:score\s+)?(?:increase|improvement|boost)"),
        "Contains guarantee of credit score improvement"
    ),
    (
        re.compile(r"(?i)your\s+score\s+will\s+(?:definitely|certainly|absolutely|guaranteed)\s+(?:go\s+up|increase|improve)"),
        "Contains guarantee of credit score improvement"
    ),

    # Promises of item removal
    (
        re.compile(r"(?i)(?:we|I)\s+(?:will|can)\s+(?:remove|delete|erase|eliminate)\s+(?:all\s+)?(?:negative\s+)?items?"),
        "Contains promise of item removal"
    ),
    (
        re.compile(r"(?i)guaranteed?\s+(?:removal|deletion)\s+of\s+(?:negative\s+)?items?"),
        "Contains promise of guaranteed item removal"
    ),
    (
        re.compile(r"(?i)(?:every|all)\s+negative\s+(?:item|mark|entry)\s+(?:will|can)\s+be\s+(?:removed|deleted|erased)"),
        "Contains promise of removing all negative items"
    ),

    # Misleading success rate claims
    (
        re.compile(r"(?i)\b(?:100|9\d)\s*%\s*(?:success|removal|deletion)\s*rate\b"),
        "Contains misleading success rate claim"
    ),
    (
        re.compile(r"(?i)(?:we|I)\s+(?:always|never\s+fail\s+to)\s+(?:get|achieve|succeed)"),
        "Contains misleading claim about consistent success"
    ),

    # Unauthorized practice of law
    (
        re.compile(r"(?i)(?:as\s+)?(?:your|our)\s+(?:attorney|lawyer|legal\s+counsel)"),
        "Contains unauthorized practice of law language"
    ),
    (
        re.compile(r"(?i)(?:legal\s+)?(?:advice|counsel|representation)\s+(?:is|will\s+be)\s+provided"),
        "Contains unauthorized practice of law language"
    ),
    (
        re.compile(r"(?i)(?:we|I)\s+(?:am|are)\s+(?:providing|offering)\s+legal\s+(?:advice|services|representation)"),
        "Contains unauthorized practice of law language"
    ),

    # False government affiliation
    (
        re.compile(r"(?i)(?:we|I)\s+(?:am|are)\s+(?:affiliated|associated|partnered)\s+with\s+(?:the\s+)?(?:government|federal|FTC|CFPB)"),
        "Contains false government affiliation claim"
    ),

    # Upfront payment demands (CROA violation)
    (
        re.compile(r"(?i)(?:payment|fee|charge)\s+(?:is\s+)?(?:required|due|must\s+be\s+(?:paid|made))\s+(?:before|prior\s+to|in\s+advance)"),
        "Contains potential CROA violation: upfront payment demand"
    ),
]

REQUIRED_CROA_KEYWORDS = [
    "credit repair organizations act",
    "croa",
]

REQUIRED_CROA_CONCEPTS = [
    # At least one of these concepts should appear
    "right to dispute",
    "not required to use a credit repair organization",
    "cannot legally remove accurate",
    "waive your rights",
]


def check_compliance(letter_content: str) -> ComplianceResult:
    """
    Scan a dispute letter for compliance issues.

    Returns a ComplianceResult with passed=True if compliant, passed=False
    with specific flags if non-compliant.
    """
    flags: List[str] = []

    if not letter_content or not letter_content.strip():
        return ComplianceResult(
            passed=False,
            flags=["Letter content is empty"],
            notes="Cannot perform compliance check on empty content."
        )

    # Check for prohibited patterns
    for pattern, description in PROHIBITED_PATTERNS:
        if pattern.search(letter_content):
            flags.append(description)

    # Check for CROA disclosure presence
    lower_content = letter_content.lower()
    has_croa_mention = any(kw in lower_content for kw in REQUIRED_CROA_KEYWORDS)

    if not has_croa_mention:
        flags.append("Missing required CROA (Credit Repair Organizations Act) disclosure")
    else:
        # If CROA is mentioned, verify at least some required concepts are present
        concepts_found = sum(1 for c in REQUIRED_CROA_CONCEPTS if c in lower_content)
        if concepts_found < 2:
            flags.append(
                "CROA disclosure is present but may be incomplete – "
                "ensure it covers consumer rights and limitations of credit repair"
            )

    # Build result
    passed = len(flags) == 0
    notes_parts = []
    if passed:
        notes_parts.append("Letter passed all compliance checks.")
    else:
        notes_parts.append(f"Letter failed compliance check with {len(flags)} issue(s).")
        for i, flag in enumerate(flags, 1):
            notes_parts.append(f"  {i}. {flag}")

    return ComplianceResult(
        passed=passed,
        flags=flags,
        notes="\n".join(notes_parts)
    )
