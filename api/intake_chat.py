import os
import json
import re
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq

router = APIRouter()

class IntakeMessage(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    current_extracted_data: Dict[str, Any] = {}

INTAKE_SYSTEM_PROMPT = """You are JanAdhikar's Expert Legal & KYC Intake Assistant. Your job is to converse empathetically with citizens in India who are facing civic, consumer, labor, or pension issues.

Your objectives:
1. Understand the user's core problem completely.
2. Politely ask for missing essential details needed for a legal petition or RTI (e.g., Department name, location/city, timeline/dates, specific amounts, or reference numbers if applicable).
3. If the user doesn't know specific technical details or office addresses, intelligently infer or auto-fill them based on the context of their city and problem.
4. Evaluate when you have gathered enough information to proceed.

CRITICAL BOUNDARIES (STRICTLY ENFORCED):
- NEVER draft any letters, petitions, RTI applications, or legal notices in this chat. 
- NEVER provide the final legal solution, classification, or verdict.
- If the user explicitly asks you to "write a letter" or "give me the application", politely decline. Tell them that your role is ONLY to collect facts, and the system will generate the official documents in the next step.

CRITICAL FORMATTING RULE FOR QUESTIONS:
- When asking multiple questions or requesting several pieces of missing information, ALWAYS format them as a clear, concise numbered list (1., 2., 3.) or bulleted list.
- NEVER combine multiple questions into long, dense narrative paragraphs. Keep questions scannable, simple, and friendly.

You must respond ONLY in valid JSON format matching this exact schema:
{
  "assistant_reply": "Your conversational response guiding the user or asking the next question(s) formatted in lists if multiple.",
  "is_ready_to_persist": false,
  "is_ready_to_proceed": boolean (true if you have gathered enough facts to classify and draft the RTI/Grievance, false if more info is needed),
  "extracted_data": {
    "problem_summary": "Concise summary of the grievance with all collected facts",
    "route_guess": "RTI" or "Rights/Grievance" or "Other",
    "applicant_city": "Inferred or stated city (e.g., Jaipur)",
    "department_name": "Inferred target department",
    "applicant_name": "Name if provided or null",
    "applicant_contact": "Phone/Email if provided or null",
    "additional_notes": "Any other helpful context"
  }
}
"""

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
            "assistant_reply": "I am processing your details. Could you please specify:\n1. Your city / district\n2. The specific authority or company involved?",
            "is_ready_to_proceed": False,
            "extracted_data": {}
        }

@router.post("/api/intake/chat")
def intake_chat(payload: IntakeMessage):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {
            "assistant_reply": "Namaste! I have noted your issue. To ensure accurate drafting, please confirm your city/district and the concerned public authority.",
            "is_ready_to_proceed": True,
            "extracted_data": {
                "problem_summary": payload.message,
                "route_guess": "RTI",
                "applicant_city": "Local Jurisdiction",
                "department_name": "Concerned Public Authority"
            }
        }

    try:
        client = Groq(api_key=api_key)
        
        messages = [{"role": "system", "content": INTAKE_SYSTEM_PROMPT}]
        for h in payload.history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": payload.message})

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b", 
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        raw_content = response.choices[0].message.content.strip()
        result = extract_json_from_text(raw_content)
        
        if payload.current_extracted_data:
            merged_data = {**payload.current_extracted_data, **result.get("extracted_data", {})}
            result["extracted_data"] = merged_data

        return result
        
    except Exception as e:
        print(f"Intake Chat Exception: {str(e)}")
        return {
            "assistant_reply": "I apologize, our secure legal network experienced a slight delay. Please continue telling me about your problem.",
            "is_ready_to_proceed": False,
            "extracted_data": payload.current_extracted_data
        }
