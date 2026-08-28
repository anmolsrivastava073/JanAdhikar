"""
F.A.C.T.S. Legal Triage Engine
================================
Implements four of JanAdhikar's core legal-quality features:

1. F.A.C.T.S. Triage        -> facts_triage()
2. RTI Section 8 Bypasser   -> scan_section_8_risks(), SEVERABILITY_CLAUSE
3. Pecuniary Jurisdiction   -> resolve_pecuniary_jurisdiction()
4. Litigation-Readiness     -> calculate_readiness_score()
"""

import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# 2. RTI SECTION 8(1) PREEMPTIVE BYPASSER
# ---------------------------------------------------------------------------

SEVERABILITY_CLAUSE = (
    "SEVERABILITY NOTICE (Section 10, RTI Act, 2005): If any part of the "
    "information sought herein is claimed exempt under Section 8 or Section 9 "
    "of the Act, the PIO is statutorily required to sever and provide the "
    "remaining non-exempt portions rather than rejecting the application in "
    "its entirety."
)

# Trigger phrases mapped to the most likely Section 8(1) exemption a PIO
# will cite, with a ready rewrite instruction.
SECTION_8_TRIGGERS: List[Dict[str, Any]] = [
    {
        "pattern": r"\bwhy\b",
        "clause": "8(1)/2(f)",
        "risk": "Interrogative / Opinion-Seeking",
        "explanation": "Questions starting with 'Why' ask for an opinion or "
                        "justification, not a material record, and fall outside "
                        "the definition of 'information' under Section 2(f).",
        "rewrite_hint": "Convert to a request for a record: 'Provide a certified "
                         "copy of the file noting / inspection report / order "
                         "explaining the decision on...'"
    },
    {
        "pattern": r"\bhow (did|does|will|can)\b",
        "clause": "8(1)/2(f)",
        "risk": "Interrogative / Opinion-Seeking",
        "explanation": "'How' questions typically ask the PIO to explain a process "
                        "rather than furnish an existing document.",
        "rewrite_hint": "Ask for the SOP, manual, or process document instead: "
                         "'Provide a certified copy of the standard operating "
                         "procedure / process manual governing...'"
    },
    {
        "pattern": r"\b(salary|income tax|medical record|personal (details|information)|bank (account|statement))\b",
        "clause": "8(1)(j)",
        "risk": "Third-Party Personal Information",
        "explanation": "Requests for another individual's personal data can be "
                        "denied unless a larger public interest is demonstrated.",
        "rewrite_hint": "Add a public-interest justification, e.g. 'sought in "
                         "larger public interest to verify misuse of public funds "
                         "/ corruption', and limit the ask to official-duty records."
    },
    {
        "pattern": r"\b(ongoing investigation|under investigation|fir (details|copy)|chargesheet)\b",
        "clause": "8(1)(h)",
        "risk": "Obstruction of Investigation",
        "explanation": "Information that could impede an ongoing investigation or "
                        "prosecution may be withheld until the case concludes.",
        "rewrite_hint": "Request only administrative/procedural records (e.g. date "
                         "of FIR registration, current status) rather than "
                         "investigation case-file contents."
    },
    {
        "pattern": r"\b(trade secret|proprietary|vendor (bid|quote)|commercial terms)\b",
        "clause": "8(1)(d)",
        "risk": "Commercial Confidence",
        "explanation": "Competitive bid pricing or proprietary vendor information "
                        "before tender finalization is often exempted.",
        "rewrite_hint": "Ask for the finalized/awarded contract value and terms "
                         "after tender finalization, not competing bids."
    },
    {
        "pattern": r"\ball (documents|records|files)\b",
        "clause": "7(9)",
        "risk": "Vague / Overbroad Request",
        "explanation": "Overbroad, multi-year 'all documents' requests "
                        "disproportionately divert the authority's resources and "
                        "are commonly rejected.",
        "rewrite_hint": "Narrow the request to a specific document type and a "
                         "defined time period (e.g. 'last 6 months')."
    },
]


def scan_section_8_risks(query_text: str) -> List[Dict[str, str]]:
    """Pre-emptively scans a citizen's raw query for Section 8/9/2(f) rejection
    triggers before a draft is even generated."""
    if not query_text:
        return []

    text_lower = query_text.lower()
    hits: List[Dict[str, str]] = []
    seen_clauses = set()

    for trigger in SECTION_8_TRIGGERS:
        if re.search(trigger["pattern"], text_lower):
            if trigger["clause"] in seen_clauses:
                continue
            seen_clauses.add(trigger["clause"])
            hits.append({
                "clause": trigger["clause"],
                "risk": trigger["risk"],
                "explanation": trigger["explanation"],
                "rewrite_hint": trigger["rewrite_hint"],
            })

    return hits


# ---------------------------------------------------------------------------
# 3. PECUNIARY JURISDICTION AUTO-ROUTER (Consumer Protection Act, 2019)
# ---------------------------------------------------------------------------

def _parse_amount(raw: Optional[Any]) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = re.sub(r"[^\d.]", "", str(raw))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def resolve_pecuniary_jurisdiction(disputed_amount: Optional[Any]) -> Dict[str, Any]:
    """Maps a disputed claim amount to the correct Consumer Commission tier
    under the Consumer Protection Act, 2019."""
    amount = _parse_amount(disputed_amount)

    if amount is None:
        return {
            "amount_parsed": None,
            "forum_tier": "UNDETERMINED",
            "forum_name": "District Consumer Disputes Redressal Commission (default)",
            "reasoning": "No specific claim amount was provided; defaulting to the "
                         "District Commission. Provide the exact disputed amount for "
                         "an accurate jurisdictional match.",
        }

    if amount <= 5_000_000:  # up to Rs. 50 Lakh
        tier = "DISTRICT"
        forum = "District Consumer Disputes Redressal Commission"
    elif amount <= 20_000_000:  # Rs. 50L - Rs. 2 Crore
        tier = "STATE"
        forum = "State Consumer Disputes Redressal Commission"
    else:  # above Rs. 2 Crore
        tier = "NATIONAL"
        forum = "National Consumer Disputes Redressal Commission (NCDRC)"

    return {
        "amount_parsed": amount,
        "forum_tier": tier,
        "forum_name": forum,
        "reasoning": f"Disputed value of Rs. {amount:,.0f} falls within the "
                     f"pecuniary jurisdiction of the {forum} under the Consumer "
                     f"Protection Act, 2019.",
    }


# ---------------------------------------------------------------------------
# 1(T). STATUTE OF LIMITATIONS CHECK
# ---------------------------------------------------------------------------

def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %B %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(raw).strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def check_statute_of_limitations(incident_date: Optional[str], route: str) -> Dict[str, Any]:
    """Checks whether a Grievance/Consumer claim still falls within its
    statutory filing window. RTI has no such limitation."""
    if route != "Rights/Grievance":
        return {"applicable": False, "status": "NOT_APPLICABLE"}

    parsed = _parse_date(incident_date)
    if not parsed:
        return {
            "applicable": True,
            "status": "UNKNOWN",
            "message": "Incident date not provided — cannot verify the 2-year "
                       "limitation period under Section 69 of the Consumer "
                       "Protection Act, 2019. Please provide the date the issue "
                       "occurred.",
        }

    days_elapsed = (date.today() - parsed).days
    years_elapsed = days_elapsed / 365.25

    if years_elapsed > 2:
        return {
            "applicable": True,
            "status": "EXPIRED",
            "days_elapsed": days_elapsed,
            "message": f"This incident occurred approximately {years_elapsed:.1f} "
                       f"years ago. Section 69 of the Consumer Protection Act, 2019 "
                       f"generally requires filing within 2 years of the cause of "
                       f"action. You may still file with an application for "
                       f"condonation of delay explaining the reason for the delay.",
        }

    return {
        "applicable": True,
        "status": "WITHIN_LIMIT",
        "days_elapsed": days_elapsed,
        "days_remaining": max(0, 730 - days_elapsed),
        "message": f"Filed within the statutory 2-year window "
                   f"({days_elapsed} days elapsed).",
    }


# ---------------------------------------------------------------------------
# 4. LITIGATION-READINESS SCORE
# ---------------------------------------------------------------------------

RTI_REQUIRED_FIELDS = [
    ("applicant_name", "Applicant full name"),
    ("applicant_address", "Applicant postal address"),
    ("applicant_city", "City / District"),
    ("applicant_pincode", "PIN Code"),
    ("target_department", "Target public authority"),
    ("specific_records", "Specific records requested"),
]

GRIEVANCE_REQUIRED_FIELDS = [
    ("applicant_name", "Applicant full name"),
    ("applicant_address", "Applicant postal address"),
    ("applicant_city", "City / District"),
    ("target_department", "Opposing party / authority"),
    ("incident_date", "Date of incident"),
    ("desired_relief", "Relief / remedy sought"),
]


def calculate_readiness_score(form_data: Dict[str, Any], route: str) -> Dict[str, Any]:
    """Computes the 'Litigation-Readiness' completeness score (0-100) used to
    drive the UI progress meter."""
    fields = RTI_REQUIRED_FIELDS if route == "RTI" else GRIEVANCE_REQUIRED_FIELDS
    form_data = form_data or {}

    filled: List[str] = []
    missing: List[str] = []
    for key, label in fields:
        value = form_data.get(key)
        if value and str(value).strip():
            filled.append(label)
        else:
            missing.append(label)

    score = round((len(filled) / len(fields)) * 100) if fields else 0

    if score >= 90:
        label = "Court Ready"
    elif score >= 60:
        label = "Filing Viable"
    elif score >= 30:
        label = "Needs Detail"
    else:
        label = "Weak"

    return {
        "score": score,
        "label": label,
        "filled_fields": filled,
        "missing_fields": missing,
    }


# ---------------------------------------------------------------------------
# 1. F.A.C.T.S. LEGAL TRIAGE ENGINE (orchestrator)
# ---------------------------------------------------------------------------

def facts_triage(
    route: str,
    user_problem: str,
    form_data: Dict[str, Any],
    extracted_facts: Dict[str, Any],
) -> Dict[str, Any]:
    """Runs the full F.A.C.T.S. checklist and returns a structured breakdown
    the frontend can render as a checklist card."""
    form_data = form_data or {}
    extracted_facts = extracted_facts or {}
    merged = {**extracted_facts, **form_data}

    # F - Facts & Evidence
    evidence_note = merged.get("evidence_available") or merged.get("file_or_work_no")
    facts_status = {
        "id": "facts",
        "label": "Facts & Evidence",
        "status": "OK" if evidence_note else "NEEDS_INPUT",
        "detail": (
            f"Reference / evidence on record: {evidence_note}"
            if evidence_note else
            "No reference number or documentary evidence captured yet. "
            "Attach receipts, application numbers, or correspondence if available."
        ),
    }

    # A - Authority Mapping
    authority = merged.get("target_department")
    authority_status = {
        "id": "authority",
        "label": "Authority Mapping",
        "status": "OK" if authority else "NEEDS_INPUT",
        "detail": (
            f"Routed to: {authority}" if authority else
            "Target public authority / opposing party not yet identified — "
            "the AI will attempt to auto-resolve this from your problem statement."
        ),
    }

    # C - Cause of Action
    cause_status = {
        "id": "cause_of_action",
        "label": "Cause of Action",
        "status": "OK" if user_problem else "NEEDS_INPUT",
        "detail": (
            "No problem statement captured yet."
            if not user_problem else
            "Your plain-language complaint will be mapped to the applicable "
            "statutory provision during drafting."
        ),
    }

    # T - Timeline / Statute of Limitations
    limitation = check_statute_of_limitations(merged.get("incident_date"), route)
    timeline_status = {
        "id": "timeline",
        "label": "Timeline (Statute of Limitations)",
        "status": (
            "OK" if (not limitation.get("applicable") or limitation.get("status") == "WITHIN_LIMIT")
            else ("WARNING" if limitation.get("status") == "EXPIRED" else "NEEDS_INPUT")
        ),
        "detail": limitation.get("message", "Not applicable to RTI filings — no limitation period."),
    }

    # S - Statutory Exemption Predictor (RTI) / Pecuniary Jurisdiction (Grievance)
    if route == "RTI":
        risks = scan_section_8_risks(user_problem)
        exemption_status = {
            "id": "exemption_predictor",
            "label": "Statutory Exemption Predictor",
            "status": "WARNING" if risks else "OK",
            "detail": (
                f"{len(risks)} potential Section 8/9 rejection trigger(s) detected "
                f"and will be auto-corrected in your draft."
                if risks else
                "No obvious Section 8/9 exemption triggers detected in your query."
            ),
            "risks": risks,
        }
    else:
        jurisdiction = resolve_pecuniary_jurisdiction(merged.get("financial_loss"))
        exemption_status = {
            "id": "pecuniary_jurisdiction",
            "label": "Pecuniary Jurisdiction",
            "status": "OK" if jurisdiction.get("amount_parsed") is not None else "NEEDS_INPUT",
            "detail": jurisdiction.get("reasoning"),
            "jurisdiction": jurisdiction,
        }

    return {
        "route": route,
        "checklist": [facts_status, authority_status, cause_status, timeline_status, exemption_status],
    }
