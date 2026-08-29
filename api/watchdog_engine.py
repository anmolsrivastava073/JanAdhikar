import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Statutory RTI constants under RTI Act, 2005
RTI_NORMAL_DEADLINE_DAYS = 30  # Section 7(1)
RTI_LIFE_LIBERTY_DEADLINE_HOURS = 48  # Section 7(1) Proviso
RTI_FIRST_APPEAL_WINDOW_DAYS = 30  # Section 19(1) (Within 30 days of expiry of PIO window)
SECTION_20_DAILY_PENALTY_INR = 250  # Section 20(1)
SECTION_20_MAX_PENALTY_INR = 25000  # Section 20(1) cap

def parse_iso_datetime(dt_str: Optional[str], default: Optional[datetime] = None) -> datetime:
    """Parses an ISO format datetime string safely into UTC aware datetime."""
    if not dt_str:
        return default or datetime.now(timezone.utc)
    try:
        clean_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{dt_str}': {e}. Using default.")
        return default or datetime.now(timezone.utc)

def calculate_deadlines(filing_date_str: Optional[str] = None, life_liberty: bool = False) -> Dict[str, str]:
    """
    Deterministically computes statutory deadlines from a filing date.
    Returns ISO strings for filing_date, response_due_date, and first_appeal_due_date.
    """
    filing_dt = parse_iso_datetime(filing_date_str)
    
    if life_liberty:
        response_due_dt = filing_dt + timedelta(hours=RTI_LIFE_LIBERTY_DEADLINE_HOURS)
    else:
        response_due_dt = filing_dt + timedelta(days=RTI_NORMAL_DEADLINE_DAYS)
        
    first_appeal_due_dt = response_due_dt + timedelta(days=RTI_FIRST_APPEAL_WINDOW_DAYS)
    
    return {
        "filing_date": filing_dt.isoformat(),
        "response_due_date": response_due_dt.isoformat(),
        "first_appeal_due_date": first_appeal_due_dt.isoformat(),
    }

def calculate_section_20_penalty(
    response_due_date_str: str,
    response_received_at_str: Optional[str] = None,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Deterministically calculates Section 20(1) potential statutory penalty exposure.
    - ₹250 / day for unjustified delay
    - Capped at ₹25,000 maximum
    - If response was received, penalty is computed up to the response date
    - If no response received, penalty accrues up to 'now'
    """
    current_dt = now or datetime.now(timezone.utc)
    due_dt = parse_iso_datetime(response_due_date_str, current_dt)
    
    # End point for calculating overdue duration
    if response_received_at_str:
        cutoff_dt = parse_iso_datetime(response_received_at_str, current_dt)
    else:
        cutoff_dt = current_dt

    if cutoff_dt <= due_dt:
        return {
            "is_overdue": False,
            "days_overdue": 0,
            "section_20_penalty_inr": 0,
            "penalty_rate_per_day": SECTION_20_DAILY_PENALTY_INR,
            "penalty_max_cap": SECTION_20_MAX_PENALTY_INR,
            "statutory_note": "Potential Section 20 penalty calculated under Section 20(1) of RTI Act, 2005."
        }

    diff = cutoff_dt - due_dt
    # Full 24h day count
    full_days_overdue = max(0, int(diff.total_seconds() // 86400))
    if diff.total_seconds() > 0 and full_days_overdue == 0:
        full_days_overdue = 1

    calculated_penalty = min(SECTION_20_MAX_PENALTY_INR, full_days_overdue * SECTION_20_DAILY_PENALTY_INR)

    return {
        "is_overdue": True,
        "days_overdue": full_days_overdue,
        "section_20_penalty_inr": calculated_penalty,
        "penalty_rate_per_day": SECTION_20_DAILY_PENALTY_INR,
        "penalty_max_cap": SECTION_20_MAX_PENALTY_INR,
        "statutory_note": "Potential statutory exposure under Section 20(1). Formal imposition subject to Information Commission proceedings."
    }

def notify_case_event(case_data: Dict[str, Any], event_type: str, event_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Notification abstraction for watchdog events.
    Appends the event to the in-app audit trail and prepares notification payloads.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    event_entry = {
        "type": event_type,
        "timestamp": now_iso,
        "metadata": event_metadata or {}
    }
    
    events: List[Dict[str, Any]] = case_data.get("watchdog_events", [])
    events.append(event_entry)
    case_data["watchdog_events"] = events
    case_data["last_watchdog_event"] = event_type
    case_data["last_watchdog_event_at"] = now_iso
    
    logger.info(f"[Watchdog Event] Case {case_data.get('id')}: {event_type} | Metadata: {event_metadata}")
    return event_entry

def evaluate_watchdog_state(case: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Authoritative, deterministic state evaluator for an RTI case.
    Evaluates statutory deadlines, calculates overdue penalties, performs idempotent state
    transitions, and emits events when new milestone triggers occur.
    """
    current_dt = now or datetime.now(timezone.utc)
    
    # 1. Initialize statutory dates if missing
    filing_date_str = case.get("filing_date")
    life_liberty = case.get("life_liberty_flag", False)
    
    if not filing_date_str:
        deadlines = calculate_deadlines(life_liberty=life_liberty)
        case["filing_date"] = deadlines["filing_date"]
        case["response_due_date"] = deadlines["response_due_date"]
        case["first_appeal_due_date"] = deadlines["first_appeal_due_date"]
        filing_date_str = case["filing_date"]
    elif not case.get("response_due_date"):
        deadlines = calculate_deadlines(filing_date_str, life_liberty=life_liberty)
        case["response_due_date"] = deadlines["response_due_date"]
        case["first_appeal_due_date"] = deadlines["first_appeal_due_date"]

    response_due_date_str = case["response_due_date"]
    first_appeal_due_date_str = case.get("first_appeal_due_date")
    
    filing_dt = parse_iso_datetime(filing_date_str, current_dt)
    response_due_dt = parse_iso_datetime(response_due_date_str, current_dt)
    first_appeal_due_dt = parse_iso_datetime(first_appeal_due_date_str, response_due_dt + timedelta(days=30))

    # 2. Extract Response details
    response_received_at_str = case.get("response_received_at") or case.get("pio_response_date")
    has_response = bool(response_received_at_str or case.get("pio_response_text"))

    # 3. Calculate Section 20 Penalties
    penalty_info = calculate_section_20_penalty(
        response_due_date_str=response_due_date_str,
        response_received_at_str=response_received_at_str if has_response else None,
        now=current_dt
    )

    # 4. Calculate timing metrics
    time_remaining_seconds = max(0, int((response_due_dt - current_dt).total_seconds()))
    days_remaining = max(0, int((response_due_dt.date() - current_dt.date()).days))
    is_due_today = (response_due_dt.date() == current_dt.date()) or (0 < (response_due_dt - current_dt).total_seconds() <= 86400 and days_remaining == 0)
    is_overdue = current_dt > response_due_dt

    # 5. Retrieve or initialize notification state & events
    notification_state = case.setdefault("notification_state", {
        "started_sent": False,
        "seven_day_warning_sent": False,
        "three_day_warning_sent": False,
        "due_today_sent": False,
        "overdue_sent": False,
        "deemed_refusal_sent": False,
        "appeal_ready_sent": False,
        "response_received_sent": False
    })
    
    events = case.setdefault("watchdog_events", [])
    
    # Guarantee initial started event if watchdog is enabled
    if case.get("watchdog_enabled", True) and not notification_state.get("started_sent"):
        notify_case_event(case, "WATCHDOG_STARTED", {"filing_date": filing_date_str, "due_date": response_due_date_str})
        notification_state["started_sent"] = True

    # 6. Determine Watchdog Status & Idempotent Event Triggers
    watchdog_status = "ACTIVE"
    appeal_eligible = False

    if case.get("status") == "CLOSED":
        watchdog_status = "CLOSED"
    elif has_response:
        watchdog_status = "RESPONSE_RECEIVED"
        if not notification_state.get("response_received_sent"):
            notify_case_event(case, "RESPONSE_RECEIVED", {
                "received_at": response_received_at_str,
                "was_overdue": is_overdue,
                "days_overdue": penalty_info["days_overdue"]
            })
            notification_state["response_received_sent"] = True
        
        # If response was analyzed and requires appeal or is deemed unsatisfactory
        if case.get("first_appeal_draft") or case.get("status") == "pio_analyzed":
            appeal_eligible = True
            if not notification_state.get("appeal_ready_sent"):
                notify_case_event(case, "APPEAL_DRAFT_READY", {
                    "exemption_cited": case.get("exemption_cited"),
                    "precedent": case.get("precedent_title")
                })
                notification_state["appeal_ready_sent"] = True

    elif is_overdue:
        # Expired without response -> OVERDUE & DEEMED REFUSAL under Sec 7(2)
        watchdog_status = "DEEMED_REFUSAL"
        appeal_eligible = True

        if not notification_state.get("overdue_sent"):
            notify_case_event(case, "DEADLINE_BREACHED", {
                "due_date": response_due_date_str,
                "days_overdue": penalty_info["days_overdue"]
            })
            notification_state["overdue_sent"] = True

        if not notification_state.get("deemed_refusal_sent"):
            notify_case_event(case, "DEEMED_REFUSAL", {
                "statutory_reference": "Section 7(2) RTI Act, 2005",
                "days_overdue": penalty_info["days_overdue"],
                "section_20_penalty": penalty_info["section_20_penalty_inr"]
            })
            notification_state["deemed_refusal_sent"] = True

        if not notification_state.get("appeal_ready_sent"):
            notify_case_event(case, "APPEAL_ELIGIBLE", {
                "statutory_reference": "Section 19(1) RTI Act, 2005",
                "reason": "Deemed Refusal under Section 7(2)"
            })
            notification_state["appeal_ready_sent"] = True

    elif is_due_today:
        watchdog_status = "DUE_TODAY"
        if not notification_state.get("due_today_sent"):
            notify_case_event(case, "DEADLINE_TODAY", {"due_date": response_due_date_str})
            notification_state["due_today_sent"] = True

    elif days_remaining <= 3:
        watchdog_status = "DUE_SOON"
        if not notification_state.get("three_day_warning_sent"):
            notify_case_event(case, "DEADLINE_3_DAYS", {"days_remaining": days_remaining})
            notification_state["three_day_warning_sent"] = True

    elif days_remaining <= 7:
        watchdog_status = "DUE_SOON"
        if not notification_state.get("seven_day_warning_sent"):
            notify_case_event(case, "DEADLINE_7_DAYS", {"days_remaining": days_remaining})
            notification_state["seven_day_warning_sent"] = True

    else:
        watchdog_status = "ACTIVE"

    # 7. Update case dictionary with unified authoritative state
    case["watchdog_enabled"] = case.get("watchdog_enabled", True)
    case["watchdog_status"] = watchdog_status
    case["is_overdue"] = penalty_info["is_overdue"]
    case["days_overdue"] = penalty_info["days_overdue"]
    case["days_remaining"] = days_remaining
    case["time_remaining_seconds"] = time_remaining_seconds
    case["section_20_penalty_inr"] = penalty_info["section_20_penalty_inr"]
    case["last_watchdog_check_at"] = current_dt.isoformat()
    case["appeal_eligible"] = appeal_eligible
    
    # Maintain legacy computed_status compatibility for existing views
    if has_response:
        case["computed_status"] = "RESPONSE_RECEIVED"
    elif is_overdue:
        case["computed_status"] = "DEEMED_REFUSAL"
    elif watchdog_status == "DUE_TODAY":
        case["computed_status"] = "DUE_TODAY"
    else:
        case["computed_status"] = "ACTIVE"

    return case


def run_scheduled_watchdog(case_manager_instance, now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Batch execution runner for Vercel Cron.
    Scans all active RTI cases, calculates deterministic timelines, updates state idempotently,
    and returns an execution report.
    """
    current_dt = now or datetime.now(timezone.utc)
    active_cases = case_manager_instance.list_active_cases()
    processed_count = 0
    updated_count = 0
    errors: List[str] = []

    for case in active_cases:
        case_id = case.get("id")
        if not case_id:
            continue
        processed_count += 1
        try:
            prev_status = case.get("watchdog_status")
            prev_events_len = len(case.get("watchdog_events", []))
            
            # Evaluate deterministic state
            evaluated_case = evaluate_watchdog_state(case, now=current_dt)
            
            # Persist updated state
            case_manager_instance.update_case(case_id, evaluated_case)
            updated_count += 1
                
        except Exception as e:
            err_msg = f"Error evaluating watchdog for case {case_id}: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

    return {
        "status": "success" if not errors else "partial_success",
        "timestamp": current_dt.isoformat(),
        "processed_count": processed_count,
        "updated_count": updated_count,
        "error_count": len(errors),
        "errors": errors[:5]
    }
