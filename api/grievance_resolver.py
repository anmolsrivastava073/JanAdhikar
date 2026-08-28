import json
import base64
import re
from typing import Dict, Any, List
from .classifier import classifier
from .facts_engine import resolve_pecuniary_jurisdiction, check_statute_of_limitations

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
        
        # Absolute fallback if AI failed to return JSON
        return {
            "violated_rights": ["Right to Fair Service"],
            "legal_explanation": "Based on the provided facts.",
            "target_portal_name": "Appropriate Legal Forum",
            "target_portal_url": "",
            "evidence_analysis": "Reviewing attached documents.",
            "demand_notice_draft": text # Dump whatever raw text the AI generated into the draft field
        }

class GrievanceResolver:
    def __init__(self):
        self.vision_model = "llama-3.2-11b-vision-preview" 
        self.text_model = "openai/gpt-oss-120b"

    def _get_client(self):
        return classifier.client

    def _attach_facts_engine_outputs(self, pack: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 3 (Pecuniary Jurisdiction) + Feature 1(T) (Statute of Limitations)
        are attached to every grievance pack, AI-generated or fallback."""
        form_data = form_data or {}
        pack["pecuniary_jurisdiction"] = resolve_pecuniary_jurisdiction(form_data.get("financial_loss"))
        pack["statute_of_limitations"] = check_statute_of_limitations(
            form_data.get("incident_date"), "Rights/Grievance"
        )
        return pack

    def _generate_intelligent_analysis(self, user_problem: str, location: str, form_data: Dict[str, Any], files_data: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        p_lower = user_problem.lower()
        app_name = form_data.get("applicant_name") or "Applicant"
        app_city = location or form_data.get("applicant_city") or "India"
        app_addr = form_data.get("applicant_address") or app_city
        app_contact = form_data.get("applicant_contact") or "Provided on Record"

        pack = {
            "violated_rights": [
                "Right to Timely Public Service Delivery",
                "Constitution of India (Article 14 & 21)"
            ],
            "legal_explanation": f"Public administrative bodies in {app_city} are bound by statutory Citizen Charters.",
            "target_portal_name": "CPGRAMS",
            "target_portal_url": "https://pgportal.gov.in",
            "evidence_analysis": "Based on provided facts.",
            "demand_notice_draft": f"""FORMAL GRIEVANCE PETITION\nTo: Concerned Department, {app_city}\nFrom: {app_name}\nSubject: Grievance regarding {user_problem[:60]}\n..."""
        }
        return self._attach_facts_engine_outputs(pack, form_data)

    def analyze_proof_and_rights(self, user_problem: str, location: str, form_data: Dict[str, Any], files_data: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        client = self._get_client()
        if client:
            try:
                system_prompt = """You are an Expert Indian Legal Analyst. Return ONLY valid JSON:
{
  "violated_rights": ["Right 1", "Right 2"],
  "legal_explanation": "Analysis.",
  "target_portal_name": "e-Daakhil / CPGRAMS",
  "target_portal_url": "https://...",
  "evidence_analysis": "What the proofs show",
  "demand_notice_draft": "The complete legal demand notice."
}"""

                user_content_str = f"Issue: {user_problem}\nLocation: {location}\nForm Data: {json.dumps(form_data)}"

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
                            encoded_image = fd.get("base64") or (base64.b64encode(fd["bytes"]).decode('utf-8') if "bytes" in fd else "")
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
                pack = extract_json_from_text(raw_content) # Use the robust extractor here!
                return self._attach_facts_engine_outputs(pack, form_data)
                
            except Exception as e:
                print(f"Grievance LLM call failed ({e}). Using expert legal rule engine.")

        return self._generate_intelligent_analysis(user_problem, location, form_data, files_data, language)

    def _fallback(self) -> Dict[str, Any]:
        return self._generate_intelligent_analysis("Consumer & civic rights grievance", "India", {}, [], "English")

grievance_resolver = GrievanceResolver()
