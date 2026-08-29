import os
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
from .social_complaint_generator import social_complaint_generator
from .watchdog_engine import (
    evaluate_watchdog_state,
    run_scheduled_watchdog,
    calculate_deadlines,
    calculate_section_20_penalty
)

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

class SocialGenerateRequest(BaseModel):
    case_id: Optional[str] = None
    user_problem: Optional[str] = ""
    language: Optional[str] = "English"
    form_data: Optional[Dict[str, Any]] = None

class WatchdogStartRequest(BaseModel):
    case_id: str
    life_liberty: Optional[bool] = False

class WatchdogResponseRequest(BaseModel):
    case_id: str
    pio_text: Optional[str] = ""
    response_received_at: Optional[str] = None

class WatchdogSimulateRequest(BaseModel):
    case_id: str
    scenario: str  # "today", "7_days", "3_days", "due_today", "overdue_10", "overdue_100", "response_ontime", "response_late", "custom", "reset"
    simulated_days_ago: Optional[int] = None

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
        clean_id = payload.case_id.strip().upper()
        analysis = analyze_pio_response(payload.pio_text or "")
        analysis["case_id"] = clean_id

        case = case_manager.get_case(clean_id)
        if case:
            case["pio_response_text"] = payload.pio_text
            if not case.get("response_received_at"):
                case["response_received_at"] = datetime.now(timezone.utc).isoformat()
            case["pio_response_date"] = case["response_received_at"]

            language = case.get("language", "English")
            draft = outcome_engine.generate_first_appeal(case, analysis, language)

            case["exemption_cited"] = analysis.get("exemption_cited")
            case["legal_counter"] = analysis.get("legal_counter")
            case["precedent_title"] = analysis.get("precedent_title")
            case["status"] = "pio_analyzed"
            case["first_appeal_draft"] = draft

            # Run deterministic watchdog evaluation
            evaluated = evaluate_watchdog_state(case)
            case_manager.update_case(clean_id, evaluated)

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

@app.post("/api/social/generate")
def generate_social_campaign(payload: SocialGenerateRequest):
    """
    GraphRAG-powered social media complaint generator.
    Produces Twitter thread, LinkedIn post, and WhatsApp broadcast
    tagged with verified ministry/authority handles.
    """
    case_id = payload.case_id or ""
    case = case_manager.get_case(case_id.strip().upper()) if case_id else {}

    user_problem = payload.user_problem or case.get("user_problem", "Civic grievance")
    language = payload.language or case.get("language", "English")
    form_data = payload.form_data or case.get("form_data", {})
    dept_info = case.get("department_info", {})

    result = social_complaint_generator.generate(
        user_problem=user_problem,
        form_data=form_data,
        department_info=dept_info,
        case_id=case_id,
        language=language
    )
    return {"case_id": case_id, **result}

# ----------------- WATCHDOG & SLA ENGINE ENDPOINTS -----------------

@app.post("/api/watchdog/start")
def start_watchdog(payload: WatchdogStartRequest):
    clean_id = payload.case_id.strip().upper()
    case = case_manager.get_case(clean_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case ID not found.")
    
    case["watchdog_enabled"] = True
    if payload.life_liberty:
        case["life_liberty_flag"] = True
        
    evaluated_case = evaluate_watchdog_state(case)
    case_manager.update_case(clean_id, evaluated_case)
    
    return {
        "status": "success",
        "message": "JanAdhikar SLA Watchdog is now monitoring this case.",
        "case_id": clean_id,
        "watchdog_status": evaluated_case.get("watchdog_status"),
        "filing_date": evaluated_case.get("filing_date"),
        "response_due_date": evaluated_case.get("response_due_date"),
        "first_appeal_due_date": evaluated_case.get("first_appeal_due_date"),
        "days_remaining": evaluated_case.get("days_remaining"),
        "days_overdue": evaluated_case.get("days_overdue"),
        "section_20_penalty_inr": evaluated_case.get("section_20_penalty_inr")
    }

@app.get("/api/watchdog/{case_id}")
def get_watchdog_case(case_id: str):
    clean_id = case_id.strip().upper()
    case_data = case_manager.get_case(clean_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="Case ID not found.")
    
    evaluated = evaluate_watchdog_state(case_data)
    case_manager.update_case(clean_id, evaluated)
    
    return {
        "case_id": clean_id,
        "watchdog_enabled": evaluated.get("watchdog_enabled", True),
        "watchdog_status": evaluated.get("watchdog_status", "ACTIVE"),
        "computed_status": evaluated.get("computed_status", "ACTIVE"),
        "filing_date": evaluated.get("filing_date"),
        "response_due_date": evaluated.get("response_due_date"),
        "first_appeal_due_date": evaluated.get("first_appeal_due_date"),
        "response_received_at": evaluated.get("response_received_at") or evaluated.get("pio_response_date"),
        "is_overdue": evaluated.get("is_overdue", False),
        "days_remaining": evaluated.get("days_remaining", 0),
        "days_overdue": evaluated.get("days_overdue", 0),
        "time_remaining_seconds": evaluated.get("time_remaining_seconds", 0),
        "section_20_penalty_inr": evaluated.get("section_20_penalty_inr", 0),
        "appeal_eligible": evaluated.get("appeal_eligible", False),
        "last_watchdog_check_at": evaluated.get("last_watchdog_check_at"),
        "last_watchdog_event": evaluated.get("last_watchdog_event"),
        "watchdog_events": evaluated.get("watchdog_events", []),
        "notification_state": evaluated.get("notification_state", {}),
        "pio_response_text": evaluated.get("pio_response_text", ""),
        "exemption_cited": evaluated.get("exemption_cited", ""),
        "legal_counter": evaluated.get("legal_counter", ""),
        "precedent_title": evaluated.get("precedent_title", ""),
        "first_appeal_draft": evaluated.get("first_appeal_draft", ""),
        "department_info": evaluated.get("department_info", {}),
        "form_data": evaluated.get("form_data", {}),
        "user_problem": evaluated.get("user_problem", ""),
        "data": evaluated
    }

@app.post("/api/watchdog/run")
def run_watchdog_cron(request: Request):
    cron_secret = os.environ.get("CRON_SECRET")
    if cron_secret:
        auth_header = request.headers.get("Authorization", "")
        custom_header = request.headers.get("x-vercel-cron-secret", "")
        if auth_header != f"Bearer {cron_secret}" and custom_header != cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid Cron Secret")
            
    result = run_scheduled_watchdog(case_manager)
    return result

@app.post("/api/watchdog/response")
def record_watchdog_response_endpoint(payload: WatchdogResponseRequest):
    clean_id = payload.case_id.strip().upper()
    case = case_manager.get_case(clean_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case ID not found.")
        
    received_dt = payload.response_received_at or datetime.now(timezone.utc).isoformat()
    case["response_received_at"] = received_dt
    case["pio_response_date"] = received_dt
    case["pio_response_text"] = payload.pio_text or ""
    
    # Analyze PIO response
    analysis = analyze_pio_response(payload.pio_text or "")
    case["exemption_cited"] = analysis.get("exemption_cited")
    case["legal_counter"] = analysis.get("legal_counter")
    case["precedent_title"] = analysis.get("precedent_title")
    case["status"] = "pio_analyzed"
    
    # Generate first appeal draft
    language = case.get("language", "English")
    first_appeal_draft = outcome_engine.generate_first_appeal(case, analysis, language)
    case["first_appeal_draft"] = first_appeal_draft
    
    # Re-evaluate watchdog state with response recorded
    evaluated = evaluate_watchdog_state(case)
    case_manager.update_case(clean_id, evaluated)
    
    return {
        "status": "success",
        "case_id": clean_id,
        "analysis": analysis,
        "watchdog_state": evaluated,
        "first_appeal_draft": first_appeal_draft
    }

@app.post("/api/watchdog/simulate")
def simulate_watchdog_scenario(payload: WatchdogSimulateRequest):
    clean_id = payload.case_id.strip().upper()
    case = case_manager.get_case(clean_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case ID not found.")
        
    now = datetime.now(timezone.utc)
    scenario = payload.scenario.lower()
    
    if scenario == "today":
        # Filed today (30 days remaining)
        filing_dt = now
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"
    elif scenario == "7_days":
        # 23 days ago -> 7 days remaining
        filing_dt = now - timedelta(days=23)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"
    elif scenario == "3_days":
        # 27 days ago -> 3 days remaining
        filing_dt = now - timedelta(days=27)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"
    elif scenario == "due_today":
        # 30 days ago -> due today
        filing_dt = now - timedelta(days=30)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"
    elif scenario == "overdue_10":
        # 40 days ago -> 10 days overdue (₹2500 penalty)
        filing_dt = now - timedelta(days=40)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"
    elif scenario == "overdue_100":
        # 130 days ago -> 100 days overdue (₹25,000 max penalty)
        filing_dt = now - timedelta(days=130)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"
    elif scenario == "response_ontime":
        # Filed 20 days ago, response received yesterday (0 penalty)
        filing_dt = now - timedelta(days=20)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = (now - timedelta(days=1)).isoformat()
        case["pio_response_date"] = case["response_received_at"]
        case["pio_response_text"] = "Information provided under Section 7(1)."
        case["status"] = "RESPONSE_RECEIVED"
    elif scenario == "response_late":
        # Filed 45 days ago, response received 5 days ago (10 days overdue -> ₹2500 penalty)
        filing_dt = now - timedelta(days=45)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = (now - timedelta(days=5)).isoformat()
        case["pio_response_date"] = case["response_received_at"]
        case["pio_response_text"] = "Belated response received from PIO."
        case["status"] = "RESPONSE_RECEIVED"
    elif scenario == "custom" and payload.simulated_days_ago is not None:
        filing_dt = now - timedelta(days=payload.simulated_days_ago)
        case["filing_date"] = filing_dt.isoformat()
        case["response_due_date"] = (filing_dt + timedelta(days=30)).isoformat()
        case["first_appeal_due_date"] = (filing_dt + timedelta(days=60)).isoformat()
        case["response_received_at"] = None
        case["pio_response_date"] = None
        case["pio_response_text"] = None
        case["status"] = "FILED"

    # Reset notification flags so clean transition events populate for simulation
    case["notification_state"] = {}
    case["watchdog_events"] = []
    
    evaluated = evaluate_watchdog_state(case, now=now)
    case_manager.update_case(clean_id, evaluated)
    
    return {
        "status": "success",
        "scenario": scenario,
        "case_id": clean_id,
        "evaluated_state": evaluated
    }

@app.get("/api/case/{case_id}")
def get_case_state(case_id: str):
    clean_id = case_id.strip().upper()
    case_data = case_manager.get_case(clean_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="Case ID not found.")
        
    evaluated = evaluate_watchdog_state(case_data)
    case_manager.update_case(clean_id, evaluated)

    response_payload = {
        "case_id": clean_id,
        "watchdog_enabled": evaluated.get("watchdog_enabled", True),
        "watchdog_status": evaluated.get("watchdog_status", "ACTIVE"),
        "computed_status": evaluated.get("computed_status", "ACTIVE"),
        "is_overdue": evaluated.get("is_overdue", False),
        "days_overdue": evaluated.get("days_overdue", 0),
        "days_remaining": evaluated.get("days_remaining", 0),
        "section_20_penalty_inr": evaluated.get("section_20_penalty_inr", 0),
        "filing_date": evaluated.get("filing_date"),
        "response_due_date": evaluated.get("response_due_date"),
        "first_appeal_due_date": evaluated.get("first_appeal_due_date"),
        "time_remaining_seconds": evaluated.get("time_remaining_seconds", 0),
        "appeal_eligible": evaluated.get("appeal_eligible", False),
        "last_watchdog_check_at": evaluated.get("last_watchdog_check_at"),
        "last_watchdog_event": evaluated.get("last_watchdog_event"),
        "watchdog_events": evaluated.get("watchdog_events", []),
        "notification_state": evaluated.get("notification_state", {}),
        "pio_response_text": evaluated.get("pio_response_text", ""),
        "exemption_cited": evaluated.get("exemption_cited", ""),
        "legal_counter": evaluated.get("legal_counter", ""),
        "precedent_title": evaluated.get("precedent_title", ""),
        "first_appeal_draft": evaluated.get("first_appeal_draft", ""),
        "department_info": evaluated.get("department_info", {}),
        "form_data": evaluated.get("form_data", {}),
        "user_problem": evaluated.get("user_problem", ""),
        "data": evaluated 
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
