import os
import random
import string
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

try:
    from supabase import create_client, Client
except ImportError:
    create_client, Client = None, None

logger = logging.getLogger(__name__)

class CaseManager:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_KEY", "")

        self.use_supabase = bool(url and key and create_client)
        self._memory_cases: Dict[str, Dict[str, Any]] = {}

        if self.use_supabase:
            try:
                self.supabase: Client = create_client(url, key)
                logger.info("Database Connected: Using Supabase for persistent case storage.")
            except Exception as e:
                logger.error(f"Supabase initialization error: {e}")
                self.use_supabase = False
        else:
            logger.warning("WARNING: Supabase credentials missing. Falling back to in-memory storage.")

    def _generate_case_id(self) -> str:
        chars = string.ascii_uppercase + string.digits
        return f"CR-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}"

    def create_case(self, life_liberty: bool = False) -> str:
        case_id = self._generate_case_id()
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        
        # Statutory 30-day (or 48-hour) initial deadlines
        if life_liberty:
            due_dt = now_dt + timedelta(hours=48)
        else:
            due_dt = now_dt + timedelta(days=30)
        first_appeal_due_dt = due_dt + timedelta(days=30)

        initial_data = {
            "id": case_id,
            "status": "FILED",
            "filing_date": now_iso,
            "response_due_date": due_dt.isoformat(),
            "first_appeal_due_date": first_appeal_due_dt.isoformat(),
            "life_liberty_flag": life_liberty,
            "watchdog_enabled": True,
            "watchdog_status": "ACTIVE",
            "watchdog_started_at": now_iso,
            "watchdog_events": [
                {
                    "type": "WATCHDOG_STARTED",
                    "timestamp": now_iso,
                    "metadata": {
                        "filing_date": now_iso,
                        "response_due_date": due_dt.isoformat(),
                        "note": "JanAdhikar statutory RTI watchdog activated."
                    }
                }
            ],
            "notification_state": {
                "started_sent": True,
                "seven_day_warning_sent": False,
                "three_day_warning_sent": False,
                "due_today_sent": False,
                "overdue_sent": False,
                "deemed_refusal_sent": False,
                "appeal_ready_sent": False,
                "response_received_sent": False
            },
            "pio_response_date": None,
            "response_received_at": None,
            "first_appeal_date": None,
            "first_appeal_decision_date": None,
        }

        if self.use_supabase:
            try:
                self.supabase.table("cases").upsert({"id": case_id, "data": initial_data}).execute()
            except Exception as e:
                logger.error(f"Supabase UPSERT Error on Create for case {case_id}: {e}")
                raise RuntimeError(f"Failed to persist case to database: {e}") from e
        else:
            self._memory_cases[case_id] = initial_data

        return case_id

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        if not case_id:
            return None

        clean_id = case_id.strip().upper()

        if self.use_supabase:
            try:
                response = self.supabase.table("cases").select("data").eq("id", clean_id).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]["data"]
                return None  
            except Exception as e:
                logger.error(f"Supabase SELECT Error for case {clean_id}: {e}")
                return None 

        return self._memory_cases.get(clean_id)

    def list_active_cases(self) -> List[Dict[str, Any]]:
        """
        Retrieves active cases where watchdog is active (status not CLOSED).
        """
        active_cases: List[Dict[str, Any]] = []

        if self.use_supabase:
            try:
                # Query all cases and filter in python to support heterogeneous schema data
                response = self.supabase.table("cases").select("id, data").execute()
                if response.data:
                    for row in response.data:
                        case_data = row.get("data", {})
                        if isinstance(case_data, dict):
                            case_id = row.get("id") or case_data.get("id")
                            if case_id:
                                case_data["id"] = case_id
                            if case_data.get("status") != "CLOSED" and case_data.get("watchdog_enabled", True):
                                active_cases.append(case_data)
            except Exception as e:
                logger.error(f"Supabase list_active_cases Error: {e}")
        else:
            for case_id, case_data in self._memory_cases.items():
                if case_data.get("status") != "CLOSED" and case_data.get("watchdog_enabled", True):
                    case_data["id"] = case_id
                    active_cases.append(case_data)

        return active_cases

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not case_id:
            return {}

        clean_id = case_id.strip().upper()
        current_data = self.get_case(clean_id)
        
        if current_data is None:
            current_data = {"id": clean_id, "filing_date": datetime.now(timezone.utc).isoformat()}

        current_data.update(updates)
        current_data["id"] = clean_id

        if self.use_supabase:
            try:
                self.supabase.table("cases").upsert({"id": clean_id, "data": current_data}).execute()
            except Exception as e:
                logger.error(f"Supabase UPSERT Error on Update for case {clean_id}: {e}")
                raise RuntimeError(f"Failed to update case in database: {e}") from e
        else:
            self._memory_cases[clean_id] = current_data
            
        return current_data

case_manager = CaseManager()
