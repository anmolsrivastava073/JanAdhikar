"""
JanAdhikar Social Media Complaint Generator
GraphRAG-powered social accountability layer.

Converts a vague citizen issue into structured, domain-aware, legally-grounded
social media threads targeting the correct ministry/authority handles.
"""
import json
import logging
from typing import Dict, Any, List, Optional
try:
    from .classifier import classifier
    from .data.jurisdiction_knowledge import resolve_knowledge_graph_node
except ImportError:
    try:
        from classifier import classifier
        from data.jurisdiction_knowledge import resolve_knowledge_graph_node
    except ImportError:
        from classifier import classifier
        from jurisdiction_knowledge import resolve_knowledge_graph_node

logger = logging.getLogger(__name__)

SOCIAL_SYSTEM_PROMPT = """You are JanAdhikar's Social Accountability Campaign Specialist.
Convert a citizen's civic grievance into a structured, high-impact, legally-grounded
social media complaint campaign.

SOCIAL MEDIA CAMPAIGN RULES:
1. Twitter/X Thread: Generate exactly 5 numbered tweets/posts.
   - Tweet 1: Strong opening hook that captures attention, names the authority and issue.
   - Tweet 2: Precise legal framing — cite the specific Act, Section, and violation.
   - Tweet 3: Factual specifics (what documents were sought or denied, how many days elapsed).
   - Tweet 4: Social accountability pressure — tag the Ministry, Minister, and oversight body.
   - Tweet 5: Specific demand with legal deadline and escalation path.
   - Each tweet MUST be under 280 characters.
   - Include relevant hashtags: #RTIAct #JanAdhikar #CIC #TransparencyIndia + domain-specific ones.

2. LinkedIn Post: 150-200 words, professional tone, explain civic issue + legal rights + call to action.
3. WhatsApp Broadcast Message: Under 600 characters, simple language (citizen-friendly, no jargon).

CRITICAL RULES:
- All outputs in the citizen's selected language.
- DO NOT fabricate case numbers, dates, or personal details not provided.
- The Twitter thread must always end with the phrase: "Filed under #RTIAct Sec 6(1). Watch this space."
- Legal terminology must be precise: PIO, CPIO, Section 6(1), Section 7(1), Section 20(1), CIC, First Appeal.
- Social handles MUST come from the provided authority entity — do NOT invent handles.

Return ONLY valid JSON:
{
  "twitter_thread": ["tweet1", "tweet2", "tweet3", "tweet4", "tweet5"],
  "linkedin_post": "<professional 150-200 word post>",
  "whatsapp_message": "<under 600 char message>",
  "campaign_hashtags": ["#hashtag1", "#hashtag2"],
  "authority_handles": ["@handle1", "@handle2"]
}
"""

# Per-domain Twitter handle roster (verified as of 2025)
SOCIAL_HANDLES_MAP = {
    "roads_highways_infrastructure":   ["@NHAI_Official", "@MORTHIndia", "@nitin_gadkari", "@MoHUA_India", "#RTIAct", "#RoadSafety", "#AccountabilityNow"],
    "healthcare_hospitals_ayushman":   ["@MoHFW_INDIA", "@AyushmanNHA", "#HealthForAll", "#RTIAct", "#CitizenRights"],
    "labor_pension_epfo_esi":         ["@socialepfo", "@LabourMinistry", "@esichq", "#EPFOseva", "#PensionRights", "#RTIAct"],
    "police_fir_investigation_law":   ["@HMOIndia", "@PMOIndia", "#CriminalJustice", "#RTIAct", "#JusticeForCitizens"],
    "municipal_sanitation_water_utilities": ["@MoHUA_India", "@SwachhBharatGov", "#SwachhBharat", "#RTIAct", "#CleanIndia"],
    "land_revenue_property_records":  ["@DoLR_GoI", "@PMOIndia", "#LandRights", "#RevenueReform", "#RTIAct"],
    "ration_pds_food_supplies":       ["@fooddeptgoi", "@PMOIndia", "#FoodSecurity", "#PDS", "#RTIAct"],
    "electricity_discom_power":       ["@MinOfPower", "@CEA_India", "#PowerForAll", "#RTIAct", "#ElectricityRights"],
    "education_exams_universities":   ["@EduMinOfIndia", "@ugc_india", "@cbseindia29", "#EducationForAll", "#RTIAct", "#ExamJustice"],
    "banking_financial_frauds":       ["@RBI", "@FinMinIndia", "#BankingFraud", "#RTIAct", "#FinancialJustice"],
    "railways_irctc_transport":       ["@RailMinIndia", "@AshwiniVaishnaw", "@RailwaySeva", "#IndianRailways", "#RTIAct"],
    "passport_immigration_consular":  ["@MEAIndia", "@passportsevamea", "#PassportSeva", "#RTIAct", "#MEAIndia"],
}

# Fallback generic handles when domain match is weak
DEFAULT_HANDLES = ["@PMOIndia", "@CPGRAMS_GoI", "@CIC_India", "#RTIAct", "#JanAdhikar", "#TransparencyIndia"]


def _build_domain_key(domain: str) -> str:
    """Map GraphRAG domain string back to knowledge graph key for handle lookup."""
    domain_lower = domain.lower()
    for key in SOCIAL_HANDLES_MAP:
        if any(word in domain_lower for word in key.split("_") if len(word) > 3):
            return key
    return ""


class SocialComplaintGenerator:
    def __init__(self):
        self.model = "openai/gpt-oss-120b"

    def _get_client(self):
        return classifier.client

    def generate(
        self,
        user_problem: str,
        form_data: Dict[str, Any],
        department_info: Dict[str, Any],
        case_id: str = "",
        language: str = "English"
    ) -> Dict[str, Any]:
        """
        Full social campaign generator:
        1. GraphRAG entity resolution for correct authority handles
        2. LLM-powered tweet thread / LinkedIn / WhatsApp copy
        3. Structured, language-aware output
        """
        city = form_data.get("applicant_city") or form_data.get("applicant_state") or ""
        app_name = form_data.get("applicant_name") or "Citizen"
        
        # GraphRAG node — supplies domain, handles, and statutory queries
        graph_node = resolve_knowledge_graph_node(user_problem, city)
        domain = graph_node.get("domain", "Civic Administration")
        pa_name = department_info.get("public_authority_name") or graph_node.get("public_authority_name", "Concerned Department")
        pio_desig = department_info.get("pio_designation") or graph_node.get("pio_designation", "PIO")
        faa_desig = department_info.get("faa_designation") or graph_node.get("faa_designation", "First Appellate Authority")
        legal_issue = graph_node.get("legal_issue_statement") or "Public administration deficiency and statutory non-compliance"
        
        # Select social handles from knowledge graph
        domain_key = _build_domain_key(domain)
        handle_pool = SOCIAL_HANDLES_MAP.get(domain_key, DEFAULT_HANDLES)
        dept_handles = department_info.get("social_handles") or graph_node.get("social_handles") or []
        
        # Merge department-resolved handles with domain pool (dedup)
        combined_handles = list(dict.fromkeys(dept_handles + [h for h in handle_pool if h.startswith("@")][:3]))
        hashtags = [h for h in handle_pool if h.startswith("#")] + ["#RTIAct", "#JanAdhikar"]
        hashtags = list(dict.fromkeys(hashtags))

        client = self._get_client()
        if client:
            try:
                user_content = f"""Citizen Background / Problem: {user_problem}
Synthesized Legal Grievance: {legal_issue}
Domain: {domain}
Location: {city}
Applicant: {app_name}
Case ID: {case_id}
Public Authority (CPIO): {pio_desig}, {pa_name}
First Appellate Authority: {faa_desig}
Available Social Handles (use these): {json.dumps(combined_handles)}
Campaign Hashtags (use these): {json.dumps(hashtags)}
Language for ALL output: {language}
"""
                sys_prompt = SOCIAL_SYSTEM_PROMPT
                if language != "English":
                    sys_prompt += f"\n\nCRITICAL: Write ALL tweet, LinkedIn, and WhatsApp content in {language}. Legal section references (Sec 6(1), Sec 7(1)) remain in English."

                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result = json.loads(resp.choices[0].message.content.strip())
                result["domain"] = domain
                result["authority_handles"] = combined_handles
                result["campaign_hashtags"] = hashtags
                return result
            except Exception as e:
                logger.error(f"[SocialComplaintGenerator] LLM error: {e}")

        # --- Deterministic fallback (no API key needed) ---
        tag_str = " ".join(combined_handles[:3]) + " " + " ".join(hashtags[:4])
        
        twitter_thread = [
            f"🚨 CIVIC ACCOUNTABILITY ALERT | {city or 'India'} — Matter: {legal_issue} | {pa_name} must act. {tag_str[:60]}",
            f"⚖️ Under Section 6(1) of the RTI Act 2005, a formal information request has been submitted to {pio_desig}. The PIO is legally mandated to respond within 30 days under Section 7(1). #RTIAct",
            f"📋 RTI Application ref: {case_id}. Filed on behalf of citizen seeking certified records & file notings. No response = Deemed Refusal under Section 7(2). #TransparencyIndia",
            f"📢 Tagging for accountability: {' '.join(combined_handles[:4])} — {city or 'India'} citizens deserve timely administration. #JanAdhikar #CIC",
            f"🔔 DEMAND: Provide complete information within 30 days or face Section 20(1) penalties (₹250/day). First Appeal to {faa_desig} is ready. Filed under #RTIAct Sec 6(1). Watch this space."
        ]
        
        # Trim tweets to 280 chars
        twitter_thread = [t[:280] for t in twitter_thread]

        linkedin_post = (
            f"Civic Accountability & Transparency Notice | {city or 'India'}\n\n"
            f"A formal Right to Information (RTI) application has been submitted to {pa_name} "
            f"under Section 6(1) of the RTI Act, 2005 concerning {legal_issue}.\n\n"
            f"Under Section 7(1), the Public Information Officer ({pio_desig}) is legally "
            f"mandated to respond within 30 calendar days. Failure to do so constitutes "
            f"Deemed Refusal under Section 7(2), triggering First Appeal rights under Section 19(1) "
            f"and Section 20(1) financial penalties of ₹250 per day.\n\n"
            f"Case Reference: {case_id}\n"
            f"#RTIAct #Transparency #CivicRights #JanAdhikar #India"
        )

        whatsapp_message = (
            f"📢 RTI Application Filed! Ref: {case_id}\n"
            f"Matter: {legal_issue}\n"
            f"Authority: {pa_name}\n"
            f"Statutory Deadline: 30 days (Sec 7(1) RTI Act)\n"
            f"Status: Monitored live by JanAdhikar SLA Watchdog.\n"
            f"#RTIAct #JanAdhikar"
        )

        return {
            "twitter_thread": twitter_thread,
            "linkedin_post": linkedin_post,
            "whatsapp_message": whatsapp_message,
            "campaign_hashtags": hashtags,
            "authority_handles": combined_handles,
            "domain": domain
        }


social_complaint_generator = SocialComplaintGenerator()
