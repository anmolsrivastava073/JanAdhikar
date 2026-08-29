import unittest
from datetime import datetime, timedelta, timezone
from api.watchdog_engine import (
    calculate_deadlines,
    calculate_section_20_penalty,
    evaluate_watchdog_state,
    notify_case_event,
    run_scheduled_watchdog,
    SECTION_20_DAILY_PENALTY_INR,
    SECTION_20_MAX_PENALTY_INR
)
from api.case_manager import CaseManager

class TestWatchdogEngine(unittest.TestCase):

    def setUp(self):
        self.now = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.manager = CaseManager()
        self.manager.use_supabase = False
        self.manager._memory_cases = {}

    def test_case_a_filed_today(self):
        """Case A: Filed today -> ACTIVE status, 30 days remaining, no penalty."""
        case = {
            "id": "CR-TEST-AAAA",
            "status": "FILED",
            "filing_date": self.now.isoformat(),
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["watchdog_status"], "ACTIVE")
        self.assertEqual(evaluated["days_remaining"], 30)
        self.assertFalse(evaluated["is_overdue"])
        self.assertEqual(evaluated["days_overdue"], 0)
        self.assertEqual(evaluated["section_20_penalty_inr"], 0)
        
        event_types = [e["type"] for e in evaluated["watchdog_events"]]
        self.assertIn("WATCHDOG_STARTED", event_types)

    def test_case_b_deadline_in_7_days(self):
        """Case B: Deadline in 7 days -> DUE_SOON status, DEADLINE_7_DAYS event emitted."""
        filing_date = self.now - timedelta(days=23)
        case = {
            "id": "CR-TEST-BBBB",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": (filing_date + timedelta(days=30)).isoformat(),
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["watchdog_status"], "DUE_SOON")
        self.assertEqual(evaluated["days_remaining"], 7)
        self.assertFalse(evaluated["is_overdue"])
        
        event_types = [e["type"] for e in evaluated["watchdog_events"]]
        self.assertIn("DEADLINE_7_DAYS", event_types)

    def test_case_c_deadline_today(self):
        """Case C: Deadline today -> DUE_TODAY status, DEADLINE_TODAY event emitted."""
        filing_date = self.now - timedelta(days=30)
        case = {
            "id": "CR-TEST-CCCC",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": self.now.isoformat(),
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["watchdog_status"], "DUE_TODAY")
        self.assertEqual(evaluated["days_remaining"], 0)
        
        event_types = [e["type"] for e in evaluated["watchdog_events"]]
        self.assertIn("DEADLINE_TODAY", event_types)

    def test_case_d_deadline_passed_no_response(self):
        """Case D: Deadline passed with zero response -> DEEMED_REFUSAL under Sec 7(2)."""
        filing_date = self.now - timedelta(days=35)
        case = {
            "id": "CR-TEST-DDDD",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": (filing_date + timedelta(days=30)).isoformat(),
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["watchdog_status"], "DEEMED_REFUSAL")
        self.assertTrue(evaluated["is_overdue"])
        self.assertEqual(evaluated["days_overdue"], 5)
        self.assertTrue(evaluated["appeal_eligible"])
        
        event_types = [e["type"] for e in evaluated["watchdog_events"]]
        self.assertIn("DEADLINE_BREACHED", event_types)
        self.assertIn("DEEMED_REFUSAL", event_types)
        self.assertIn("APPEAL_ELIGIBLE", event_types)

    def test_case_e_10_days_overdue_penalty(self):
        """Case E: 10 days overdue -> ₹2,500 Section 20 potential statutory liability."""
        filing_date = self.now - timedelta(days=40)
        case = {
            "id": "CR-TEST-EEEE",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": (filing_date + timedelta(days=30)).isoformat(),
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["days_overdue"], 10)
        self.assertEqual(evaluated["section_20_penalty_inr"], 2500)
        self.assertEqual(evaluated["watchdog_status"], "DEEMED_REFUSAL")

    def test_case_f_100_days_overdue_penalty_cap(self):
        """Case F: 100+ days overdue -> Penalty strictly capped at ₹25,000 maximum."""
        filing_date = self.now - timedelta(days=150)
        case = {
            "id": "CR-TEST-FFFF",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": (filing_date + timedelta(days=30)).isoformat(),
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["days_overdue"], 120)
        self.assertEqual(evaluated["section_20_penalty_inr"], 25000)

    def test_case_g_response_received_on_time(self):
        """Case G: Response received on time -> RESPONSE_RECEIVED, no overdue penalty."""
        filing_date = self.now - timedelta(days=20)
        response_date = self.now - timedelta(days=5)
        case = {
            "id": "CR-TEST-GGGG",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": (filing_date + timedelta(days=30)).isoformat(),
            "response_received_at": response_date.isoformat(),
            "pio_response_text": "Information supplied as requested under Section 7(1).",
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["watchdog_status"], "RESPONSE_RECEIVED")
        self.assertFalse(evaluated["is_overdue"])
        self.assertEqual(evaluated["section_20_penalty_inr"], 0)
        
        event_types = [e["type"] for e in evaluated["watchdog_events"]]
        self.assertIn("RESPONSE_RECEIVED", event_types)

    def test_case_h_response_received_after_deadline(self):
        """Case H: Response received 10 days late -> response recorded, penalty locked to late duration (₹2500)."""
        filing_date = self.now - timedelta(days=45)
        due_date = filing_date + timedelta(days=30)
        response_date = due_date + timedelta(days=10) # received 10 days late
        
        case = {
            "id": "CR-TEST-HHHH",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": due_date.isoformat(),
            "response_received_at": response_date.isoformat(),
            "pio_response_text": "Late reply provided by public authority.",
            "watchdog_enabled": True
        }
        evaluated = evaluate_watchdog_state(case, now=self.now)
        self.assertEqual(evaluated["watchdog_status"], "RESPONSE_RECEIVED")
        self.assertTrue(evaluated["is_overdue"])
        self.assertEqual(evaluated["days_overdue"], 10)
        self.assertEqual(evaluated["section_20_penalty_inr"], 2500)
        
        event_types = [e["type"] for e in evaluated["watchdog_events"]]
        self.assertIn("RESPONSE_RECEIVED", event_types)

    def test_idempotency_50_evaluations(self):
        """Running the watchdog evaluator 50 consecutive times must produce 0 duplicate events."""
        filing_date = self.now - timedelta(days=35)
        case = {
            "id": "CR-TEST-IDEM",
            "status": "FILED",
            "filing_date": filing_date.isoformat(),
            "response_due_date": (filing_date + timedelta(days=30)).isoformat(),
            "watchdog_enabled": True
        }
        
        # First evaluation
        case = evaluate_watchdog_state(case, now=self.now)
        initial_events_count = len(case["watchdog_events"])
        initial_status = case["watchdog_status"]
        
        # Run 50 more times
        for _ in range(50):
            case = evaluate_watchdog_state(case, now=self.now)
            
        self.assertEqual(len(case["watchdog_events"]), initial_events_count)
        self.assertEqual(case["watchdog_status"], initial_status)

    def test_scheduled_batch_cron_execution(self):
        """Test batch cron execution across multiple active cases."""
        case_id_1 = self.manager.create_case()
        case_id_2 = self.manager.create_case()
        
        # Modify case 2 to be overdue
        case_2 = self.manager.get_case(case_id_2)
        past_date = self.now - timedelta(days=40)
        case_2["filing_date"] = past_date.isoformat()
        case_2["response_due_date"] = (past_date + timedelta(days=30)).isoformat()
        self.manager.update_case(case_id_2, case_2)
        
        report = run_scheduled_watchdog(self.manager, now=self.now)
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["processed_count"], 2)
        
        updated_c2 = self.manager.get_case(case_id_2)
        self.assertEqual(updated_c2["watchdog_status"], "DEEMED_REFUSAL")
        self.assertEqual(updated_c2["section_20_penalty_inr"], 2500)

if __name__ == "__main__":
    unittest.main()
