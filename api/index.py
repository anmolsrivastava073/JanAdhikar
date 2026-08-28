import io
import json
import email
import logging
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from .case_manager import case_manager
from .classifier import classifier, analyze_pio_response
from .outcome_predictor import outcome_engine
from .department_resolver import department_resolver
from .rti_pdf_generator import generate_rti_pdf, generate_generic_pdf
from .appeal_pdf_generator import generate_first_appeal_pdf
from .grievance_resolver import grievance_resolver
from .intake_chat import router as intake_router
from .facts_engine import calculate_readiness_score, facts_triage

logger = logging.getLogger(__name__)

app = FastAPI(title="JanAdhikar AI API", version="2.6")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake_router)

class GeneratePDFRequest(BaseModel):
    title: Optional[str] = "Document"
    content: Optional[str] = ""

class CaseInitResponse(BaseModel):
    case_id: str
    message: str

class ClassifyRequest(BaseModel):
    case_id: Optional[str] = None
    problem_text: Optional[str] = ""
    language: Optional[str] = "English"

class FormSubmitRequest(BaseModel):
    case_id: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None

class RTIPredictRequest(BaseModel):
    case_id: Optional[str] = None
    draft_text: Optional[str] = None

class RTIImproveRequest(BaseModel):
    case_id: Optional[str] = None

class DepartmentResolveRequest(BaseModel):
    case_id: Optional[str] = None
    location: Optional[str] = None

class GrievanceGenerateRequest(BaseModel):
    case_id: Optional[str] = None
    form_data: Optional[Any] = None
    user_problem: Optional[str] = ""
    language: Optional[str] = "English"
    files: Optional[List[Dict[str, Any]]] = None

class PIOAnalysisRequest(BaseModel):
    case_id: str
    pio_text: Optional[str] = ""

class FirstAppealRequest(BaseModel):
    appellant_name: str
    appellant_address: str
    first_appellate_authority: str
    pio_address: str
    rti_registration_no: str
    rti_filing_date: str
    pio_reply_date: Optional[str] = None
    grounds_of_appeal: str
    legal_precedent: str

class ReadinessRequest(BaseModel):
    case_id: Optional[str] = None
    route: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None

class TranslateRequest(BaseModel):
    text: str
    target_language: str

@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "system": "JanAdhikar Backend Active",
        "database_connected": getattr(case_manager, "is_connected", True)
    }

@app.post("/api/case/init", response_model=CaseInitResponse)
def init_case():
    new_case_id = case_manager.create_case()
    return CaseInitResponse(case_id=new_case_id, message="Save this ID safely.")

@app.post("/api/translate")
def translate_text(payload: TranslateRequest):
    translated = outcome_engine.translate_document(payload.text, payload.target_language)
    return {"translated_text": translated}

@app.post("/api/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...), 
    language: str = Form("English")
):
    try:
        file_bytes = await audio_file.read()
        filename = audio_file.filename or "recording.webm"
        
        if not file_bytes:
            return {"text": "", "transcription": ""}
            
        client = classifier.client
        if not client:
            return {"text": "Voice input received. Please review your text.", "transcription": "Voice input received."}
            
        if language == "English":
            text = client.audio.transcriptions.create(
                file=(filename, file_bytes),
                model="whisper-large-v3",
                response_format="json",
                language="en"
            ).text
        else:
            raw_text = client.audio.transcriptions.create(
                file=(filename, file_bytes),
                model="whisper-large-v3",
                prompt="The user is speaking Hinglish or an Indian language. Transcribe accurately.",
                response_format="json"
            ).text
            
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are a translator. Translate the following text into 'Hinglish' (conversational Hindi written using ONLY the English alphabet). Under NO circumstances should you use Devanagari script. Do not add commentary."},
                    {"role": "user", "content": raw_text}
                ],
                temperature=0.0
            )
            text = resp.choices[0].message.content.strip()

        return {"text": text, "transcription": text}
    except Exception as e:
        print(f"Transcription error: {e}")
        return {"text": "failed", "transcription": "failed"}

@app.post("/api/case/classify")
def classify_problem(payload: ClassifyRequest):
    case_id = payload.case_id or case_manager.create_case()
    case = case_manager.get_case(case_id) or {}

    problem_text = payload.problem_text or case.get("user_problem", "")
    language = payload.language or case.get("language", "English")

    result = classifier.classify(problem_text, language)
    
    case_manager.update_case(case_id, {
        "status": "classified",
        "route": result["route"],
        "sub_category": result["sub_category"],
        "user_problem": problem_text,
        "form_schema": result["form_schema"],
        "extracted_facts": result.get("extracted_data", {}),
        "facts_analysis": result.get("facts_analysis"),
        "language": language
    })

    return {**result, "case_id": case_id}

@app.post("/api/case/readiness")
def compute_readiness(payload: ReadinessRequest):
    case = case_manager.get_case(payload.case_id) if payload.case_id else None
    route = payload.route or (case.get("route") if case else None) or "RTI"
    form_data = payload.form_data or (case.get("form_data") if case else {}) or {}
    return calculate_readiness_score(form_data, route)

@app.post("/api/rti/generate")
def generate_rti(payload: FormSubmitRequest):
    case_id = payload.case_id or case_manager.create_case()
    case = case_manager.get_case(case_id) or {}

    user_problem = case.get("user_problem", "Public Records & Inspection Inquiry")
    language = case.get("language", "English")
    form_data = payload.form_data or case.get("form_data", {})
    
    draft = outcome_engine.generate_initial_rti(form_data, user_problem, language)

    case_manager.update_case(case_id, {
        "status": "rti_drafted",
        "form_data": form_data,
        "initial_draft": draft
    })
    return {"case_id": case_id, "initial_draft": draft}

@app.post("/api/rti/predict")
def predict_rti(payload: RTIPredictRequest):
    case_id = payload.case_id or case_manager.create_case()
    case = case_manager.get_case(case_id) or {}

    draft_text = payload.draft_text or case.get("initial_draft") or case.get("improved_draft") or "Application under Section 6(1) of RTI Act 2005"
    language = case.get("language", "English")
    
    prediction_result = outcome_engine.predict_rti_outcome(draft_text, language)
    case_manager.update_case(case_id, {
        "status": "rti_predicted",
        "prediction_result": prediction_result
    })
    return {"case_id": case_id, **prediction_result}

@app.post("/api/rti/improve")
def improve_rti(payload: RTIImproveRequest):
    case_id = payload.case_id or case_manager.create_case()
    case = case_manager.get_case(case_id) or {}

    initial_draft = case.get("initial_draft") or case.get("improved_draft", "Application under Section 6(1) of RTI Act 2005")
    pred = case.get("prediction_result", {})
    risks = pred.get("detected_risks", [])
    suggestions = pred.get("improvement_suggestions", [])
    language = case.get("language", "English")

    improved_result = outcome_engine.generate_improved_rti(initial_draft, risks, suggestions, language)
    case_manager.update_case(case_id, {
        "status": "rti_completed",
        "improved_draft": improved_result.get("improved_draft"),
        "filing_instructions": improved_result.get("filing_instructions")
    })
    return {"case_id": case_id, **improved_result}

@app.post("/api/rti/resolve-department")
def resolve_department(payload: DepartmentResolveRequest):
    case_id = payload.case_id or case_manager.create_case()
    case = case_manager.get_case(case_id) or {}

    user_problem = case.get("user_problem", "Public Authority Records Request")
    extracted_facts = {**case.get("form_data", {}), **case.get("extracted_facts", {})}
    location = payload.location or extracted_facts.get("applicant_city") or extracted_facts.get("applicant_state", "")
    language = case.get("language", "English")

    dept_info = department_resolver.resolve("RTI", user_problem, location, extracted_facts, language)
    case_manager.update_case(case_id, {"department_info": dept_info})
    return {"case_id": case_id, **dept_info}

@app.get("/api/rti/pdf/{case_id}")
def download_rti_pdf(case_id: str):
    case = case_manager.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case ID not found.")

    draft_text = (
        case.get("improved_draft") or 
        case.get("initial_draft") or 
        case.get("grievance_pack", {}).get("demand_notice_draft") or
        case.get("user_problem", "")
    )
    dept_info = case.get("department_info") or {}
    form_data = case.get("form_data", {})
    applicant_details = {
        "name": form_data.get("applicant_name", "[Applicant Name]"),
        "address": form_data.get("applicant_address", ""),
        "contact": form_data.get("applicant_contact", ""),
        "place": form_data.get("applicant_city", ""),
        "date": "",
    }

    pdf_bytes = generate_rti_pdf(applicant_details, dept_info, draft_text)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={case_id}_Document.pdf"}
    )

@app.post("/api/analyze_pio_backend")
def analyze_pio_backend_endpoint(payload: PIOAnalysisRequest):
    try:
        analysis = analyze_pio_response(payload.pio_text or "")
        analysis["case_id"] = payload.case_id

        case = case_manager.get_case(payload.case_id)
        if case:
            case["pio_response_text"] = payload.pio_text
            language = case.get("language", "English")
            
            draft = outcome_engine.generate_first_appeal(case, analysis, language)

            case_manager.update_case(payload.case_id, {
                "pio_response_text": payload.pio_text,
                "exemption_cited": analysis.get("exemption_cited"),
                "legal_counter": analysis.get("legal_counter"),
                "precedent_title": analysis.get("precedent_title"),
                "status": "pio_analyzed",
                "first_appeal_draft": draft
            })

        return analysis
    except Exception as e:
        logger.error(f"Error in /analyze_pio_backend: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze PIO response")

@app.post("/generate_appeal_pdf")
@app.post("/api/generate_appeal_pdf")
def generate_appeal_pdf_endpoint(payload: FirstAppealRequest):
    try:
        pdf_bytes = generate_first_appeal_pdf(
            appellant_name=payload.appellant_name,
            appellant_address=payload.appellant_address,
            first_appellate_authority=payload.first_appellate_authority,
            pio_address=payload.pio_address,
            rti_registration_no=payload.rti_registration_no,
            rti_filing_date=payload.rti_filing_date,
            pio_reply_date=payload.pio_reply_date,
            grounds_of_appeal=payload.grounds_of_appeal,
            legal_precedent=payload.legal_precedent
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="First_Appeal_{payload.rti_registration_no}.pdf"'
            }
        )
    except Exception as e:
        logger.error(f"Error generating appeal PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate First Appeal PDF")

@app.post("/api/grievance/generate")
def generate_grievance(payload: GrievanceGenerateRequest):
    case_id = payload.case_id or case_manager.create_case()
    case = case_manager.get_case(case_id) or {}

    form_data = payload.form_data or case.get("form_data", {})
    if isinstance(form_data, str):
        try:
            parsed_form_data = json.loads(form_data)
        except Exception:
            parsed_form_data = {}
    else:
        parsed_form_data = form_data or {}

    user_problem = payload.user_problem or case.get("user_problem", "Citizen Grievance & Deficiency of Service")
    language = payload.language or case.get("language", "English")
    location = parsed_form_data.get("applicant_city", "")
    files_data = payload.files or []

    try:
        pack = grievance_resolver.analyze_proof_and_rights(
            user_problem=user_problem,
            location=location,
            form_data=parsed_form_data,
            files_data=files_data,
            language=language
        )
    except Exception as e:
        print(f"Grievance resolution fallback: {e}")
        pack = grievance_resolver._fallback()

    case_manager.update_case(case_id, {
        "status": "grievance_completed",
        "form_data": parsed_form_data,
        "grievance_pack": pack
    })

    return {"case_id": case_id, **pack}

@app.post("/api/generate-pdf")
def generate_generic_pdf_endpoint(payload: GeneratePDFRequest):
    pdf_bytes = generate_generic_pdf(payload.title, payload.content)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Document.pdf"}
    )

@app.get("/api/case/{case_id}")
def get_case_state(case_id: str):
    case_data = case_manager.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="Case ID not found.")
        
    filing_date_str = case_data.get("filing_date")
    if not filing_date_str:
        filing_date_obj = datetime.now(timezone.utc) - timedelta(days=35) 
        filing_date_str = filing_date_obj.isoformat()
    else:
        try:
            filing_date_obj = datetime.fromisoformat(filing_date_str.replace("Z", "+00:00"))
        except ValueError:
            filing_date_obj = datetime.now(timezone.utc) - timedelta(days=35)

    response_due_date_obj = filing_date_obj + timedelta(days=30)
    first_appeal_due_date_obj = filing_date_obj + timedelta(days=60)
    now = datetime.now(timezone.utc)
    
    is_overdue = now > response_due_date_obj
    diff_time = now - response_due_date_obj
    days_overdue = diff_time.days if is_overdue and diff_time.days > 0 else 0
    
    section_20_penalty = min(25000, days_overdue * 250)
    time_remaining_seconds = max(0, int((response_due_date_obj - now).total_seconds()))

    computed_status = case_data.get("status", "ACTIVE")
    if computed_status in ["classified", "initialized", "FILED"] and is_overdue:
        computed_status = "DEEMED_REFUSAL"

    response_payload = {
        "case_id": case_id,
        "computed_status": computed_status,
        "is_overdue": is_overdue,
        "days_overdue": days_overdue,
        "section_20_penalty_inr": section_20_penalty,
        "filing_date": filing_date_str,
        "response_due_date": response_due_date_obj.isoformat(),
        "first_appeal_due_date": first_appeal_due_date_obj.isoformat(),
        "time_remaining_seconds": time_remaining_seconds,
        "pio_response_text": case_data.get("pio_response_text", ""),
        "exemption_cited": case_data.get("exemption_cited", ""),
        "legal_counter": case_data.get("legal_counter", ""),
        "precedent_title": case_data.get("precedent_title", ""),
        "first_appeal_draft": case_data.get("first_appeal_draft", ""),
        "data": case_data 
    }

    return response_payload

@app.get("/api/debug/supabase")
def debug_supabase():
    from .case_manager import case_manager
    import os
    return {
        "use_supabase": case_manager.use_supabase,
        "has_url_env": bool(os.environ.get("SUPABASE_URL")),
        "has_key_env": bool(os.environ.get("SUPABASE_KEY")),
        "url_prefix": os.environ.get("SUPABASE_URL", "")[:20],
        "memory_case_count": len(case_manager._memory_cases),
    }
