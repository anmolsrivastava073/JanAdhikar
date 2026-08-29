import json
import base64
import re
import logging
from typing import Dict, Any, List
from .classifier import classifier
from .facts_engine import resolve_pecuniary_jurisdiction, check_statute_of_limitations
from .data.jurisdiction_knowledge import resolve_knowledge_graph_node

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> dict:
    """Safely extracts JSON from a string even if it's wrapped in markdown or conversational text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try: return json.loads(json_match.group(1))
            except json.JSONDecodeError: pass
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            try: return json.loads(json_match.group(1))
            except json.JSONDecodeError: pass
        return {
            "violated_rights": ["Right to Fair Service"],
            "legal_explanation": "Based on the provided facts.",
            "target_portal_name": "CPGRAMS",
            "target_portal_url": "https://pgportal.gov.in",
            "evidence_analysis": "Reviewing attached documents.",
            "demand_notice_draft": text
        }


GRIEVANCE_SYSTEM_PROMPT = """You are an Expert Indian Legal Analyst, Consumer Rights Advocate, and Senior Civic Ombudsman.
Analyze the citizen's grievance and return a structured legal analysis with a professionally drafted Demand Notice.

DEMAND NOTICE FORMAT RULES:
1. Address to: The concerned authority (resolved from problem context).
2. Subject: Formal Legal Notice under [Applicable Act] read with [Sections].
3. Body Structure:
   - Paragraph 1 (Facts): Precise factual summary of the grievance.
   - Paragraph 2 (Legal Violations): Specific statutory provisions violated (Consumer Protection Act 2019, CPGRAMS Citizen Charter, etc.).
   - Paragraph 3 (Relief Demanded): Exact remedy, refund with 18% p.a. interest, compensation, and punitive damages.
   - Paragraph 4 (Escalation Warning): If not resolved within 15 days, this matter will be escalated to the Consumer Commission / High Court / CIC.
4. Closing: Formal valediction and date/place fields.

PORTAL ROUTING RULES:
- If financial deficiency or consumer complaint → "e-Daakhil (https://edaakhil.nic.in)"
- If government service failure → "CPGRAMS (https://pgportal.gov.in)"
- If labor/EPF issue → "EPFO Grievance Portal (https://epfigms.gov.in)"
- If electricity → "State DISCOM Grievance Portal"
- If railways → "Rail Madad (https://railmadad.indianrailways.gov.in)"

Output ONLY valid JSON:
{
  "violated_rights": ["<Right 1>", "<Right 2>"],
  "legal_explanation": "<Detailed legal analysis citing specific Acts, Sections, and consumer/civic rights violated>",
  "target_portal_name": "<Portal/Forum name>",
  "target_portal_url": "<URL>",
  "evidence_analysis": "<Analysis of provided documents/facts>",
  "demand_notice_draft": "<Complete formal demand notice in pure plain text WITHOUT any markdown formatting>"
}
"""


class GrievanceResolver:
    def __init__(self):
        self.vision_model = "llama-3.2-11b-vision-preview"
        self.text_model = "openai/gpt-oss-120b"

    def _get_client(self):
        return classifier.client

    def _attach_facts_engine_outputs(self, pack: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        form_data = form_data or {}
        pack["pecuniary_jurisdiction"] = resolve_pecuniary_jurisdiction(form_data.get("financial_loss"))
        pack["statute_of_limitations"] = check_statute_of_limitations(
            form_data.get("incident_date"), "Rights/Grievance"
        )
        return pack

    def _fallback_demand_notice(self, user_problem: str, location: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Knowledge-graph-backed structured fallback (no LLM required)."""
        app_name = form_data.get("applicant_name") or "The Applicant"
        app_city = location or form_data.get("applicant_city") or "the concerned locality"
        app_addr = form_data.get("applicant_address") or app_city
        app_contact = form_data.get("applicant_contact") or "[Contact on Record]"
        incident_date = form_data.get("incident_date") or "[Date of Incident]"
        desired_relief = form_data.get("desired_relief") or "Immediate resolution and appropriate compensation"
        financial_loss = form_data.get("financial_loss") or ""

        graph_node = resolve_knowledge_graph_node(user_problem, app_city)
        pa_name = graph_node.get("public_authority_name", "The Concerned Authority")
        pio_desig = graph_node.get("pio_designation", "The Officer In-Charge")
        domain = graph_node.get("domain", "Public Administration")

        portal_map = {
            "consumer": ("e-Daakhil Consumer Forum", "https://edaakhil.nic.in"),
            "epfo": ("EPFO Grievance Portal", "https://epfigms.gov.in"),
            "rail": ("Rail Madad", "https://railmadad.indianrailways.gov.in"),
            "electricity": ("CGPDTM / State DISCOM Grievance Portal", "https://pgportal.gov.in"),
        }
        portal_name, portal_url = "CPGRAMS", "https://pgportal.gov.in"
        for kw, (pn, pu) in portal_map.items():
            if kw in user_problem.lower() or kw in domain.lower():
                portal_name, portal_url = pn, pu
                break

        legal_issue = graph_node.get("legal_issue_statement") or "Public administration deficiency and statutory non-compliance"
        fin_clause = f" amounting to Rs. {financial_loss}" if financial_loss else ""

        demand_notice = f"""FORMAL LEGAL NOTICE / GRIEVANCE PETITION

To,
{pio_desig},
{pa_name},
{app_city}

Date: ______________
Place: {app_city}

Subject: Formal Legal Notice regarding {domain} deficiency ({legal_issue}) in {app_city} — Demand for immediate statutory remedy.

Sir / Madam,

1. PARTICULARS OF THE AGGRIEVED PARTY:
   Name: {app_name}
   Address: {app_addr}
   Contact: {app_contact}

2. FACTS & BACKGROUND:
   The Complainant states that the following grievance arose on or about {incident_date} involving {legal_issue}:
   Factual background: {user_problem}

3. STATUTORY VIOLATIONS:
   The acts/omissions of the Respondent constitute clear violation of:
   (a) The citizen's right to timely and effective public service delivery as guaranteed under the Citizen Charter of {pa_name};
   (b) Article 14 and Article 21 of the Constitution of India (Right to Equality and Right to Life with Dignity);
   (c) Applicable Consumer Protection Act, 2019 provisions (if service was paid for) and/or the Administrative Circular/Service Level Agreement applicable to the authority.

4. RELIEF DEMANDED:
   In light of the above facts, the Complainant hereby formally demands:
   (a) {desired_relief}{fin_clause};
   (b) Compensation for mental agony, harassment, and financial loss caused by the delay/deficiency;
   (c) If monetary recovery is involved: payment with 18% per annum simple interest from the date of default.

5. ESCALATION WARNING:
   Take NOTICE that if the aforesaid grievance is not resolved within 15 (fifteen) calendar days from the date of receipt of this notice, the Complainant reserves the right to:
   (a) File a Consumer Complaint before the District Consumer Disputes Redressal Commission under Section 35 of the Consumer Protection Act, 2019;
   (b) File an RTI Application under Section 6(1) of the RTI Act, 2005 seeking file notings and action taken records;
   (c) Approach the appropriate High Court by way of Writ Petition under Article 226 of the Constitution.

Yours faithfully,
{app_name}
Contact: {app_contact}
"""

        pack = {
            "violated_rights": [
                "Right to Timely Service Delivery (Citizen Charter)",
                "Right to Life with Dignity (Article 21, Constitution of India)",
                "Consumer Rights under Consumer Protection Act 2019"
            ],
            "legal_explanation": f"The grievance pertains to {domain}. The authority {pa_name} has failed to discharge its statutory duties. The citizen is entitled to immediate remedy under applicable statutes and the Citizen Charter, with financial penalty and interest where applicable.",
            "target_portal_name": portal_name,
            "target_portal_url": portal_url,
            "evidence_analysis": "Documents and facts provided support the grievance claim.",
            "demand_notice_draft": demand_notice
        }
        return self._attach_facts_engine_outputs(pack, form_data)

    def analyze_proof_and_rights(self, user_problem: str, location: str, form_data: Dict[str, Any], files_data: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        client = self._get_client()
        app_city = location or form_data.get("applicant_city") or "India"
        graph_node = resolve_knowledge_graph_node(user_problem, app_city)
        pa_name = graph_node.get("public_authority_name", "Concerned Authority")
        domain = graph_node.get("domain", "Civic Administration")

        if client:
            try:
                lang_rule = f"\n\nCRITICAL: Write ALL output (violated_rights, legal_explanation, demand_notice_draft) in {language}." if language != "English" else ""
                system_prompt = GRIEVANCE_SYSTEM_PROMPT + lang_rule

                user_content_str = (
                    f"Citizen Problem: {user_problem}\n"
                    f"Location: {app_city}\n"
                    f"Domain (GraphRAG): {domain}\n"
                    f"Identified Authority: {pa_name}\n"
                    f"Applicant Details: {json.dumps(form_data)}"
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [{"type": "text", "text": user_content_str}]}
                ]

                has_images = False
                if files_data:
                    for fd in files_data:
                        mime = fd.get("mime_type", "")
                        if mime.startswith("image/"):
                            has_images = True
                            encoded_image = fd.get("base64") or (
                                base64.b64encode(fd["bytes"]).decode('utf-8') if "bytes" in fd else ""
                            )
                            if encoded_image:
                                messages[1]["content"].append({
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime};base64,{encoded_image}"}
                                })

                resp = client.chat.completions.create(
                    model=self.vision_model if has_images else self.text_model,
                    messages=messages,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )

                raw_content = resp.choices[0].message.content.strip()
                pack = extract_json_from_text(raw_content)
                return self._attach_facts_engine_outputs(pack, form_data)

            except Exception as e:
                logger.error(f"[GrievanceResolver] LLM call failed ({e}). Using knowledge-graph fallback.")

        return self._fallback_demand_notice(user_problem, location, form_data)

    def _fallback(self) -> Dict[str, Any]:
        return self._fallback_demand_notice("Citizen grievance & deficiency of service", "India", {})


grievance_resolver = GrievanceResolver()
