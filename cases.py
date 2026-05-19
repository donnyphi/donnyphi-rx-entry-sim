"""Fake prescription cases for the training simulator.

All patient names, prescriber names, MRNs, NPIs, DEA numbers, and addresses
are fictional. Drug information reflects general references but cases are
constructed for training only and are not medical advice.

Each case dict has the following schema:

    {
        "case_id": str,
        "patient":    {"name", "dob", "mrn", "address", "allergies"},
        "prescriber": {"name", "npi", "dea", "address"},
        "rx_text": {                       # what the user "sees" on the Rx
            "date_written": str,
            "drug_line": str,
            "sig_shorthand": str,
            "quantity_text": str | None,   # omit to hide Disp from user
            "refills_text": str,
            "daw_text": str,
        },
        "expected": {                      # ground truth for checker
            "drug_name": str,
            "strength": str,
            "quantity": int,
            "days_supply": int,
            "refills": int,
            "daw": int,
            "sig_components": dict[str, list[str]],
        },
        "extras": {                        # optional explanations on miss
            "drug_alternates": list[str],
            "quantity_calc": str,
            "days_calc": str,
        },
    }
"""
from __future__ import annotations

import random


# ---------- reusable synonym blocks ----------

VERB_TAKE = ["take"]
FORM_TABLET = ["tablet", "tablets"]
FORM_CAPSULE = ["capsule", "capsules"]
ROUTE_PO = ["by mouth", "orally"]

# Frequency synonyms chosen to avoid substring collisions across frequencies.
# Bare "daily" is intentionally excluded from QD because it is a substring
# of "three times daily" and "twice daily".
FREQ_QD = ["once daily", "once a day", "every day"]
FREQ_BID = [
    "twice daily",
    "twice a day",
    "two times daily",
    "two times a day",
    "every 12 hours",
]
FREQ_TID = [
    "three times daily",
    "three times a day",
    "every 8 hours",
]
FREQ_QHS = [
    "at bedtime",
    "every night at bedtime",
    "nightly at bedtime",
]


# ---------- cases ----------

CASES: list[dict] = [
    # ---- Case 1: Acute antibiotic (the example from the spec) ----
    {
        "case_id": "rx_001",
        "patient": {
            "name": "John Sample",
            "dob": "03/15/1958",
            "mrn": "MRN-10001",
            "address": "100 Training Way, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "0000000001",
            "dea": "XT0000001",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "05/15/2026",
            "drug_line": "Amoxicillin 500 mg capsule",
            "sig_shorthand": "1 cap PO TID x 10 days",
            "quantity_text": None,   # force quantity calculation
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Amoxicillin",
            "strength": "500 mg",
            "quantity": 30,
            "days_supply": 10,
            "refills": 0,
            "daw": 0,
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_CAPSULE,
                "route": ROUTE_PO,
                "frequency": FREQ_TID,
                "duration": ["10 days", "ten days"],
            },
        },
        "extras": {
            "drug_alternates": ["amoxil"],
            "quantity_calc": "1 cap x 3 times/day x 10 days = 30 capsules.",
            "days_calc": "Duration written on the Rx is 10 days.",
        },
    },

    # ---- Case 2: Chronic BP, QD ----
    {
        "case_id": "rx_002",
        "patient": {
            "name": "Maria Testpatient",
            "dob": "11/22/1972",
            "mrn": "MRN-10002",
            "address": "215 Sample St, Practice City, TX 78001",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "0000000002",
            "dea": "XT0000002",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "05/16/2026",
            "drug_line": "Lisinopril 10 mg tablet",
            "sig_shorthand": "1 tab PO QD",
            "quantity_text": "Disp: 30",
            "refills_text": "Refills: 5",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Lisinopril",
            "strength": "10 mg",
            "quantity": 30,
            "days_supply": 30,
            "refills": 5,
            "daw": 0,
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QD,
            },
        },
        "extras": {
            "drug_alternates": ["prinivil", "zestril"],
            "days_calc": "30 tablets at 1 tablet per day = 30 days supply.",
        },
    },

    # ---- Case 3: Chronic diabetes, BID ----
    {
        "case_id": "rx_003",
        "patient": {
            "name": "Robert Practiceman",
            "dob": "07/04/1965",
            "mrn": "MRN-10003",
            "address": "410 Demo Drive, Training Town, TX 78002",
            "allergies": ["Penicillin"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "0000000003",
            "dea": "XT0000003",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "05/17/2026",
            "drug_line": "Metformin 500 mg tablet",
            "sig_shorthand": "1 tab PO BID",
            "quantity_text": "Disp: 60",
            "refills_text": "Refills: 5",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Metformin",
            "strength": "500 mg",
            "quantity": 60,
            "days_supply": 30,
            "refills": 5,
            "daw": 0,
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_BID,
            },
        },
        "extras": {
            "drug_alternates": ["glucophage"],
            "days_calc": "60 tablets at 2 tablets per day = 30 days supply.",
        },
    },

    # ---- Case 4: Chronic statin, QHS ----
    {
        "case_id": "rx_004",
        "patient": {
            "name": "Linda Example",
            "dob": "02/28/1980",
            "mrn": "MRN-10004",
            "address": "612 Mock Rd, Sample City, TX 78000",
            "allergies": ["Sulfa drugs"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "0000000004",
            "dea": "XT0000004",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "05/18/2026",
            "drug_line": "Atorvastatin 20 mg tablet",
            "sig_shorthand": "1 tab PO QHS",
            "quantity_text": "Disp: 30",
            "refills_text": "Refills: 11",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Atorvastatin",
            "strength": "20 mg",
            "quantity": 30,
            "days_supply": 30,
            "refills": 11,
            "daw": 0,
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QHS,
            },
        },
        "extras": {
            "drug_alternates": ["lipitor"],
            "days_calc": "30 tablets at 1 tablet per day = 30 days supply.",
        },
    },

    # ---- Case 5: Acute antibiotic, BID with duration ----
    {
        "case_id": "rx_005",
        "patient": {
            "name": "Carlos Demoperson",
            "dob": "09/18/1955",
            "mrn": "MRN-10005",
            "address": "808 Fake Circle, Practice City, TX 78001",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "0000000001",
            "dea": "XT0000001",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "05/18/2026",
            "drug_line": "Ciprofloxacin 500 mg tablet",
            "sig_shorthand": "1 tab PO BID x 7 days",
            "quantity_text": None,   # force quantity calculation
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Ciprofloxacin",
            "strength": "500 mg",
            "quantity": 14,
            "days_supply": 7,
            "refills": 0,
            "daw": 0,
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_BID,
                "duration": ["7 days", "seven days"],
            },
        },
        "extras": {
            "drug_alternates": ["cipro"],
            "quantity_calc": "1 tab x 2 times/day x 7 days = 14 tablets.",
            "days_calc": "Duration written on the Rx is 7 days.",
        },
    },

    # ---- Case 6: Chronic BP, 90-day supply, DAW 1 ----
    {
        "case_id": "rx_006",
        "patient": {
            "name": "Anna Mockpatient",
            "dob": "12/01/1988",
            "mrn": "MRN-10006",
            "address": "919 Example Ct, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "0000000003",
            "dea": "XT0000003",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "05/19/2026",
            "drug_line": "Amlodipine 5 mg tablet",
            "sig_shorthand": "1 tab PO QD",
            "quantity_text": "Disp: 90",
            "refills_text": "Refills: 3",
            "daw_text": "DAW: 1 (Brand medically necessary)",
        },
        "expected": {
            "drug_name": "Amlodipine",
            "strength": "5 mg",
            "quantity": 90,
            "days_supply": 90,
            "refills": 3,
            "daw": 1,
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QD,
            },
        },
        "extras": {
            "drug_alternates": ["norvasc"],
            "days_calc": "90 tablets at 1 tablet per day = 90 days supply.",
        },
    },
]


# ---------- selection ----------

def get_random_case(exclude_ids: list[str] | None = None) -> dict:
    """Return a random case whose id is not in exclude_ids.

    If every case has been seen, the exclusion list is reset and a random
    case is returned from the full pool.
    """
    exclude_ids = exclude_ids or []
    pool = [c for c in CASES if c["case_id"] not in exclude_ids]
    if not pool:
        pool = CASES
    return random.choice(pool)


def get_case_by_id(case_id: str) -> dict | None:
    """Return the case with the given id, or None if not found."""
    for c in CASES:
        if c["case_id"] == case_id:
            return c
    return None
