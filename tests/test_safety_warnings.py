"""Deterministic coverage for the DUR / Safety Review warning engine.

These tests lock in the *current intended* behavior of
``app.get_safety_warnings`` for representative fictional cases. They assert the
expected warning categories are present (not medical perfection), plus the
structural invariants the renderer relies on. They do not change app behavior.
"""
import unittest

import cases
from tests._support import load_app

app = load_app()

# Tones the DUR panel renderer (render_safety_warnings) is allowed to display.
ALLOWED_TONES = {"safety", "insurance", "drug", "training"}
VALID_TYPES = set(app.SAFETY_META.keys())
REQUIRED_KEYS = {"type", "title", "badge", "tone", "message"}


def case_by_id(case_id: str) -> dict:
    return next(case for case in cases.CASES if case["case_id"] == case_id)


def warning_types(case: dict) -> set:
    return {w["type"] for w in app.get_safety_warnings(case)}


class SafetyWarningInvariantsTest(unittest.TestCase):
    def test_get_safety_warnings_never_raises_and_is_wellformed(self):
        for case in cases.CASES:
            warnings = app.get_safety_warnings(case)
            self.assertIsInstance(warnings, list)
            for warning in warnings:
                with self.subTest(case=case["case_id"], type=warning.get("type")):
                    self.assertTrue(REQUIRED_KEYS.issubset(warning.keys()))
                    self.assertIn(warning["type"], VALID_TYPES)
                    self.assertIn(warning["tone"], ALLOWED_TONES)
                    self.assertTrue(str(warning["message"]).strip())


class SafetyWarningCategoryTest(unittest.TestCase):
    def test_allergy_warnings_fire(self):
        # rx_012: penicillin allergy + amoxicillin
        # rx_015: sulfa allergy + hydrochlorothiazide
        for case_id in ("rx_012", "rx_015"):
            with self.subTest(case=case_id):
                self.assertIn("allergy", warning_types(case_by_id(case_id)))

    def test_high_alert_medication_fires(self):
        # rx_018: insulin glargine is a high-alert medication
        self.assertIn("high_alert", warning_types(case_by_id("rx_018")))

    def test_daw_brand_generic_fires(self):
        # rx_006 and rx_018 are DAW 1 (brand medically necessary)
        for case_id in ("rx_006", "rx_018"):
            with self.subTest(case=case_id):
                self.assertIn("daw", warning_types(case_by_id(case_id)))

    def test_prn_clarity_fires(self):
        # PRN directions should prompt an indication / max-daily clarity note
        for case_id in ("rx_010", "rx_020", "rx_027"):
            with self.subTest(case=case_id):
                self.assertIn("clarification", warning_types(case_by_id(case_id)))

    def test_refill_review_fires(self):
        # rx_004: unusually high authorized refills -> refill review
        self.assertIn("refill", warning_types(case_by_id("rx_004")))

    def test_interaction_cross_reactivity_fires(self):
        # No bundled case carries a current-medication profile, so this uses a
        # synthetic fictional input to exercise the interaction path directly:
        # an NSAID dispensed for a patient already on warfarin (bleeding risk).
        synthetic = {
            "case_id": "synthetic_interaction",
            "patient": {
                "name": "Test Patient",
                "allergies": ["NKDA"],
                "medications": ["Warfarin 5 mg tablet"],
            },
            "prescriber": {"name": "Dr Test"},
            "rx_text": {
                "drug_line": "Ibuprofen 600 mg tablet",
                "sig_shorthand": "1 tab PO TID",
                "refills_text": "Refills: 0",
                "daw_text": "DAW: 0",
            },
            "expected": {
                "drug_name": "Ibuprofen",
                "strength": "600 mg",
                "quantity": 30,
                "days_supply": 10,
                "refills": 0,
                "daw": 0,
                "sig_english": "Take 1 tablet by mouth three times daily",
            },
        }
        self.assertIn("interaction", warning_types(synthetic))

    def test_clean_cases_have_no_warnings(self):
        # Routine fills: NKDA, DAW 0, no PRN, modest refills -> empty panel.
        for case_id in ("rx_001", "rx_016"):
            with self.subTest(case=case_id):
                self.assertEqual([], app.get_safety_warnings(case_by_id(case_id)))


if __name__ == "__main__":
    unittest.main()
