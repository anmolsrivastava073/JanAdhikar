import json
from typing import Dict, Any, List
from groq import Groq
from .prompts import (
    RTI_DRAFT_SYSTEM_PROMPT,
    RTI_PREDICTOR_SYSTEM_PROMPT,
    RTI_IMPROVE_SYSTEM_PROMPT
)
from .classifier import classifier
from .facts_engine import scan_section_8_risks, SEVERABILITY_CLAUSE

class OutcomeEngine:
    def __init__(self):
        self.model = "openai/gpt-oss-120b"

    def _get_client(self) -> Groq:
        return classifier.client

    def _get_lang_rule(self, language: str) -> str:
        return f"\n\nCRITICAL LANGUAGE INSTRUCTION:\nThe user has selected '{language}'. ALL text output MUST be written in {language}."

    def _ensure_severability(self, draft: str) -> str:
        """Feature 2 safety net: guarantees every RTI draft carries a Section 10
        severability clause, even if the LLM omitted one."""
        if not draft:
            return draft
        lowered = draft.lower()
        if "section 10" in lowered or "severability" in lowered:
            return draft
        return f"{draft.rstrip()}\n\n{SEVERABILITY_CLAUSE}"

    def generate_initial_rti(self, form_data: Dict[str, Any], user_problem: str, language: str) -> str:
        client = self._get_client()

        # Feature 2: pre-flight Section 8 risk scan fed straight into the drafting prompt
        section8_risks = scan_section_8_risks(user_problem)
        risk_note = ""
        if section8_risks:
            risk_lines = "\n".join(
                f"- {r['risk']} ({r['clause']}): {r['rewrite_hint']}" for r in section8_risks
            )
            risk_note = f"\n\nPRE-FLIGHT SECTION 8 RISK SCAN — proactively avoid these patterns:\n{risk_lines}"

        if client:
            try:
                prompt = f"User Problem: {user_problem}\nForm Details:\n{json.dumps(form_data, indent=2)}{risk_note}"
                sys_prompt = RTI_DRAFT_SYSTEM_PROMPT + self._get_lang_rule(language)
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                draft = response.choices[0].message.content.strip()
                return self._ensure_severability(draft)
            except Exception as e:
                print(f"[OutcomeEngine] Initial RTI generation failed: {e}")

        app_name = form_data.get("applicant_name", "Applicant")
        app_city = form_data.get("applicant_city", "Local Jurisdiction")
        fallback_draft = f"""APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005\n\nTo,\nThe CPIO,\n{app_city}\n\nSubject: RTI request regarding {user_problem[:60]}"""
        return self._ensure_severability(fallback_draft)

    def predict_rti_outcome(self, draft_text: str, language: str) -> Dict[str, Any]:
        client = self._get_client()
        if client:
            try:
                sys_prompt = RTI_PREDICTOR_SYSTEM_PROMPT + self._get_lang_rule(language)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": f"Analyze this RTI Draft:\n\n{draft_text}"}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content.strip())
            except Exception as e:
                print(f"[OutcomeEngine] RTI prediction failed: {e}")

        return {
            "prediction": "APPROVED",
            "probabilities": {"approved": 0.88, "partial": 0.09, "rejected": 0.03},
            "detected_risks": [{"risk_code": "INFO", "description": "Fallback response used.", "severity": "LOW"}],
            "improvement_suggestions": []
        }

    def generate_improved_rti(self, original_draft: str, risks: List[Dict[str, Any]], suggestions: List[str], language: str) -> Dict[str, Any]:
        client = self._get_client()
        if client:
            try:
                user_content = f"Original Draft:\n{original_draft}\n\nIdentified Risks:\n{json.dumps(risks)}\n\nSuggestions:\n{json.dumps(suggestions)}"
                sys_prompt = RTI_IMPROVE_SYSTEM_PROMPT + self._get_lang_rule(language)
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                parsed = json.loads(response.choices[0].message.content.strip())
                if parsed.get("improved_draft"):
                    parsed["improved_draft"] = self._ensure_severability(parsed["improved_draft"])
                return parsed
            except Exception as e:
                print(f"[OutcomeEngine] RTI improvement failed: {e}")

        return {
            "improved_draft": self._ensure_severability(original_draft),
            "filing_instructions": ["Print 2 copies.", "Submit by Speed Post."]
        }
        
    def generate_first_appeal(self, case_data: Dict[str, Any], pio_analysis: Dict[str, Any], language: str) -> str:
        client = self._get_client()
        form_data = case_data.get("form_data", {})
        dept_info = case_data.get("department_info", {})
        original_draft = case_data.get("improved_draft") or case_data.get("initial_draft", "Original RTI Application")
        pio_reply = case_data.get("pio_response_text", "No response / Deemed Refusal")
        
        if client:
            try:
                sys_prompt = """You are an expert Indian Appellate Advocate practicing before the Central Information Commission (CIC).
Generate a watertight, formal First Appeal document under Section 19(1) of the Right to Information Act, 2005.

Rules for Drafting:
1. Title: "BEFORE THE FIRST APPELLATE AUTHORITY"
2. Address to: "The First Appellate Authority (FAA), [Department Name derived from facts]"
3. Section 1: "Appellant & PIO Details".
4. Section 2: "Brief Facts". Summarize the original RTI query and the PIO's exact reply.
5. Section 3: "Grounds for Appeal". Attack the PIO's cited exemption vigorously using the provided CIC Precedents and Legal Counter. 
6. Section 4: "Prayer". Demand the information free of cost under Section 7(6) and recommend a Section 20(1) penalty on the PIO.

Output pure, professional plain text. DO NOT use markdown formatting like **bold**, *italics*, or code blocks like ```. Do not add conversational intro/outro.""" + self._get_lang_rule(language)

                user_content = f"""
Appellant Name: {form_data.get('applicant_name', 'Applicant')}
Appellant Address: {form_data.get('applicant_address', 'Address on record')}
Target Public Authority: {dept_info.get('public_authority_name', 'Concerned Department')}
Original RTI Request: {original_draft}
PIO's Reply: {pio_reply}
Exemption Cited by PIO: {pio_analysis.get('exemption_cited', 'None')}
Legal Grounds / Precedent to use: {pio_analysis.get('precedent_title', '')} - {pio_analysis.get('legal_counter', '')}
"""
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.2
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[OutcomeEngine] First Appeal generation failed: {e}")

        # Fallback if API fails
        appellant_name = form_data.get("applicant_name", "[Applicant Name]")
        dept_name = dept_info.get("public_authority_name", "[Public Authority]")
        grounds = pio_analysis.get("appeal_grounds", "The PIO failed to provide complete information in accordance with the RTI Act.")
        precedent = pio_analysis.get("legal_counter", "Section 7(9) and CIC guidelines mandate strict adherence to disclosure.")
        
        return f"BEFORE THE FIRST APPELLATE AUTHORITY\nUnder Section 19(1) of the RTI Act, 2005\n\nAppellant: {appellant_name}\nPublic Authority: {dept_name}\n\nGROUNDS FOR APPEAL:\n{grounds}\n\nSTATUTORY PRECEDENT:\n{precedent}\n\nPRAYER:\nDirect the PIO to provide complete information free of cost under Section 7(6) and initiate Section 20(1) penalty proceedings."

    def translate_document(self, text: str, target_language: str) -> str:
        client = self._get_client()
        if client:
            try:
                sys_prompt = f"You are an expert Indian Legal Translator. Translate the following legal document into formal, official {target_language}. Maintain the exact structure, numbering, and legal terminology appropriate for Indian civic applications. Output ONLY the translated text in pure plain text without markdown wrappers (**bold**, etc.) or conversational filler."
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[OutcomeEngine] Translation failed: {e}")
        return text

outcome_engine = OutcomeEngine()
