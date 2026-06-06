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
FREQ_QID = ["four times daily", "four times a day", "every 6 hours", "every six hours"]
FREQ_Q6H = ["every 6 hours", "every six hours"]
FREQ_QAM = ["every morning", "each morning", "in the morning"]

# Non-oral dosage forms, routes, and verbs for drops, topicals, inhalers,
# and injectables. Each list is a set of acceptable English synonyms; the
# SIG checker only needs one to appear in the user's translation.
FORM_DROP = ["drop", "drops"]
FORM_PUFF = ["puff", "puffs", "inhalation", "inhalations"]

ROUTE_OU = ["in both eyes", "in each eye", "into both eyes"]
ROUTE_OD_EYE = ["in the right eye", "into the right eye"]
ROUTE_AU = ["in both ears", "in each ear", "into both ears"]
ROUTE_INH = ["by inhalation", "inhaled", "by mouth"]
ROUTE_TOPICAL = ["to affected area", "to the affected area", "topically", "to skin", "to the skin"]
ROUTE_SC = ["under the skin", "subcutaneously", "subcutaneous", "sub q", "subcut"]

VERB_INSTILL = ["instill", "place", "use"]
VERB_APPLY = ["apply", "rub", "spread"]
VERB_INHALE = ["inhale", "use", "take"]
VERB_INJECT = ["inject"]

PRN_TERMS = ["as needed", "if needed", "when needed"]


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
            "npi": "1487523796",
            "dea": "FT4287563",
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
            "sig_english": "Take 1 capsule by mouth three times daily for 10 days",
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
            "npi": "1760395284",
            "dea": "FC2950837",
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
            "sig_english": "Take 1 tablet by mouth once daily",
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
            "quantity_calc": "Disp line on the Rx shows 30 tablets.",
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
            "npi": "1928461735",
            "dea": "FM6182947",
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
            "sig_english": "Take 1 tablet by mouth twice daily",
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
            "quantity_calc": "Disp line on the Rx shows 60 tablets.",
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
            "npi": "1364297805",
            "dea": "FI9374518",
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
            "sig_english": "Take 1 tablet by mouth at bedtime",
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
            "quantity_calc": "Disp line on the Rx shows 30 tablets.",
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
            "npi": "1487523796",
            "dea": "FT4287563",
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
            "sig_english": "Take 1 tablet by mouth twice daily for 7 days",
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
            "npi": "1928461735",
            "dea": "FM6182947",
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
            "sig_english": "Take 1 tablet by mouth once daily",
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
            "quantity_calc": "Disp line on the Rx shows 90 tablets.",
            "days_calc": "90 tablets at 1 tablet per day = 90 days supply.",
        },
    },

    # ---- Case 7: Liquid antibiotic for a child ----
    {
        "case_id": "rx_007",
        "patient": {
            "name": "Sam Childpatient",
            "dob": "06/12/2019",
            "mrn": "MRN-10007",
            "address": "212 Pediatric Way, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "1364297805",
            "dea": "FI9374518",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "05/19/2026",
            "drug_line": "Amoxicillin 250 mg/5 mL suspension",
            "sig_shorthand": "5 mL PO TID x 10 days",
            "quantity_text": None,
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Amoxicillin",
            "strength": "250 mg/5 mL",
            "quantity": 150,
            "days_supply": 10,
            "refills": 0,
            "daw": 0,
            "sig_english": "Take 5 mL by mouth three times daily for 10 days",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["5 ml", "5ml", "five ml", "five milliliters"],
                "route": ROUTE_PO,
                "frequency": FREQ_TID,
                "duration": ["10 days", "ten days"],
            },
        },
        "extras": {
            "drug_alternates": ["amoxil"],
            "quantity_calc": "5 mL x 3 times/day x 10 days = 150 mL total.",
            "days_calc": "Duration written on the Rx is 10 days.",
        },
    },

    # ---- Case 8: Eye drops, twice daily ----
    {
        "case_id": "rx_008",
        "patient": {
            "name": "Margaret Trialperson",
            "dob": "10/08/1945",
            "mrn": "MRN-10008",
            "address": "318 Reference Dr, Training Town, TX 78002",
            "allergies": ["Aspirin"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "1928461735",
            "dea": "FM6182947",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "05/19/2026",
            "drug_line": "Timolol 0.5% ophthalmic solution",
            "sig_shorthand": "1 gtt OU BID",
            "quantity_text": "Disp: 5 mL",
            "refills_text": "Refills: 2",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Timolol",
            "strength": "0.5%",
            "quantity": 5,
            "days_supply": 30,
            "refills": 2,
            "daw": 0,
            "sig_english": "Instill 1 drop in both eyes twice daily",
            "sig_components": {
                "verb": ["instill", "place", "use"],
                "quantity": ["1", "one"],
                "form": ["drop", "drops"],
                "route": ["in both eyes", "in each eye", "into both eyes"],
                "frequency": FREQ_BID,
            },
        },
        "extras": {
            "drug_alternates": ["timoptic"],
            "quantity_calc": "Disp line on the Rx shows 5 mL (one bottle).",
            "days_calc": "A 5 mL bottle of eye drops typically lasts about 30 days at twice-daily dosing.",
        },
    },

    # ---- Case 9: Topical cream, twice daily ----
    {
        "case_id": "rx_009",
        "patient": {
            "name": "Diego Sampleson",
            "dob": "04/22/1990",
            "mrn": "MRN-10009",
            "address": "424 Practice Ave, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "1760395284",
            "dea": "FC2950837",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "05/19/2026",
            "drug_line": "Hydrocortisone 1% cream",
            "sig_shorthand": "Apply to affected area BID",
            "quantity_text": "Disp: 30 g",
            "refills_text": "Refills: 2",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Hydrocortisone",
            "strength": "1%",
            "quantity": 30,
            "days_supply": 30,
            "refills": 2,
            "daw": 0,
            "sig_english": "Apply to the affected area twice daily",
            "sig_components": {
                "verb": ["apply", "rub", "spread"],
                "route": ["to affected area", "to the affected area", "topically", "to skin"],
                "frequency": FREQ_BID,
            },
        },
        "extras": {
            "quantity_calc": "Disp line on the Rx shows 30 g (one tube).",
            "days_calc": "Estimated 30 days for a 30 g tube of cream at twice-daily dosing.",
        },
    },

    # ---- Case 10: PRN analgesic ----
    {
        "case_id": "rx_010",
        "patient": {
            "name": "Patricia Demofield",
            "dob": "01/16/1978",
            "mrn": "MRN-10010",
            "address": "535 Mock St, Practice City, TX 78001",
            "allergies": ["Penicillin"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "1487523796",
            "dea": "FT4287563",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "05/19/2026",
            "drug_line": "Ibuprofen 600 mg tablet",
            "sig_shorthand": "1 tab PO Q6H PRN pain",
            "quantity_text": "Disp: 30",
            "refills_text": "Refills: 1",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Ibuprofen",
            "strength": "600 mg",
            "quantity": 30,
            "days_supply": 7,
            "refills": 1,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth every 6 hours as needed for pain",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": ["every 6 hours"],
                "prn": ["as needed", "if needed", "when needed"],
            },
        },
        "extras": {
            "drug_alternates": ["motrin", "advil"],
            "quantity_calc": "Disp line on the Rx shows 30 tablets.",
            "days_calc": "30 tablets at maximum 4 doses per day = 7 days supply (PRN max).",
        },
    },

    # ---- Case 11: Antibiotic, QID, quantity calculation ----
    {
        "case_id": "rx_011",
        "patient": {
            "name": "Nina Practicefield",
            "dob": "08/30/1991",
            "mrn": "MRN-10011",
            "address": "131 Trainee Ct, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "1487523796",
            "dea": "FT4287563",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/01/2026",
            "drug_line": "Cephalexin 500 mg capsule",
            "sig_shorthand": "1 cap PO QID x 7 days",
            "quantity_text": None,
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Cephalexin",
            "strength": "500 mg",
            "quantity": 28,
            "days_supply": 7,
            "refills": 0,
            "daw": 0,
            "sig_english": "Take 1 capsule by mouth four times daily for 7 days",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_CAPSULE,
                "route": ROUTE_PO,
                "frequency": FREQ_QID,
                "duration": ["7 days", "seven days"],
            },
        },
        "extras": {
            "drug_alternates": ["keflex"],
            "quantity_calc": "1 cap x 4 times/day x 7 days = 28 capsules.",
            "days_calc": "Duration written on the Rx is 7 days.",
        },
    },

    # ---- Case 12: Antibiotic, BID, documented penicillin allergy (DUR) ----
    {
        "case_id": "rx_012",
        "patient": {
            "name": "Owen Sampleton",
            "dob": "04/17/1969",
            "mrn": "MRN-10012",
            "address": "242 Mock Ln, Practice City, TX 78001",
            "allergies": ["Penicillin"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "1760395284",
            "dea": "FC2950837",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "06/01/2026",
            "drug_line": "Amoxicillin 875 mg tablet",
            "sig_shorthand": "1 tab PO BID x 10 days",
            "quantity_text": None,
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Amoxicillin",
            "strength": "875 mg",
            "quantity": 20,
            "days_supply": 10,
            "refills": 0,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth twice daily for 10 days",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_BID,
                "duration": ["10 days", "ten days"],
            },
        },
        "extras": {
            "drug_alternates": ["amoxil"],
            "quantity_calc": "1 tab x 2 times/day x 10 days = 20 tablets.",
            "days_calc": "Duration written on the Rx is 10 days.",
        },
    },

    # ---- Case 13: Liquid antibiotic, mL dose, quantity calculation ----
    {
        "case_id": "rx_013",
        "patient": {
            "name": "Priya Demochild",
            "dob": "02/09/2020",
            "mrn": "MRN-10013",
            "address": "353 Pediatric Pl, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "1364297805",
            "dea": "FI9374518",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/02/2026",
            "drug_line": "Cephalexin 250 mg/5 mL suspension",
            "sig_shorthand": "10 mL PO BID x 10 days",
            "quantity_text": None,
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Cephalexin",
            "strength": "250 mg/5 mL",
            "quantity": 200,
            "days_supply": 10,
            "refills": 0,
            "daw": 0,
            "sig_english": "Take 10 mL by mouth twice daily for 10 days",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["10 ml", "10ml", "ten ml", "ten milliliters"],
                "route": ROUTE_PO,
                "frequency": FREQ_BID,
                "duration": ["10 days", "ten days"],
            },
        },
        "extras": {
            "drug_alternates": ["keflex"],
            "quantity_calc": "10 mL x 2 times/day x 10 days = 200 mL total.",
            "days_calc": "Duration written on the Rx is 10 days.",
        },
    },

    # ---- Case 14: Hypertension (ARB), once daily maintenance ----
    {
        "case_id": "rx_014",
        "patient": {
            "name": "Grace Mockley",
            "dob": "07/25/1963",
            "mrn": "MRN-10014",
            "address": "464 Sample Row, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "1928461735",
            "dea": "FM6182947",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "06/02/2026",
            "drug_line": "Losartan 50 mg tablet",
            "sig_shorthand": "1 tab PO QD",
            "quantity_text": "Disp: 30",
            "refills_text": "Refills: 11",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Losartan",
            "strength": "50 mg",
            "quantity": 30,
            "days_supply": 30,
            "refills": 11,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth once daily",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QD,
            },
        },
        "extras": {
            "drug_alternates": ["cozaar"],
            "quantity_calc": "Disp line on the Rx shows 30 tablets.",
            "days_calc": "30 tablets at 1 tablet per day = 30 days supply.",
        },
    },

    # ---- Case 15: Hypertension (thiazide), QAM, 90-day, sulfa allergy (DUR) ----
    {
        "case_id": "rx_015",
        "patient": {
            "name": "Henry Trialson",
            "dob": "11/03/1957",
            "mrn": "MRN-10015",
            "address": "575 Demo Blvd, Sample City, TX 78000",
            "allergies": ["Sulfa drugs"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "1487523796",
            "dea": "FT4287563",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/03/2026",
            "drug_line": "Hydrochlorothiazide 25 mg tablet",
            "sig_shorthand": "1 tab PO QAM",
            "quantity_text": "Disp: 90",
            "refills_text": "Refills: 3",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Hydrochlorothiazide",
            "strength": "25 mg",
            "quantity": 90,
            "days_supply": 90,
            "refills": 3,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth every morning",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QAM,
            },
        },
        "extras": {
            "drug_alternates": ["microzide", "hctz"],
            "quantity_calc": "Disp line on the Rx shows 90 tablets.",
            "days_calc": "90 tablets at 1 tablet per day = 90 days supply.",
        },
    },

    # ---- Case 16: Hypertension (beta blocker), BID maintenance ----
    {
        "case_id": "rx_016",
        "patient": {
            "name": "Bianca Sampford",
            "dob": "05/14/1974",
            "mrn": "MRN-10016",
            "address": "686 Practice Pkwy, Practice City, TX 78001",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "1760395284",
            "dea": "FC2950837",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "06/03/2026",
            "drug_line": "Metoprolol tartrate 50 mg tablet",
            "sig_shorthand": "1 tab PO BID",
            "quantity_text": "Disp: 60",
            "refills_text": "Refills: 5",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Metoprolol",
            "strength": "50 mg",
            "quantity": 60,
            "days_supply": 30,
            "refills": 5,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth twice daily",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_BID,
            },
        },
        "extras": {
            "drug_alternates": ["lopressor", "metoprolol tartrate"],
            "quantity_calc": "Disp line on the Rx shows 60 tablets.",
            "days_calc": "60 tablets at 2 tablets per day = 30 days supply.",
        },
    },

    # ---- Case 17: Diabetes, BID with meals ----
    {
        "case_id": "rx_017",
        "patient": {
            "name": "Victor Demopoulos",
            "dob": "09/29/1966",
            "mrn": "MRN-10017",
            "address": "797 Education Ct, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "1928461735",
            "dea": "FM6182947",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "06/04/2026",
            "drug_line": "Metformin 1000 mg tablet",
            "sig_shorthand": "1 tab PO BID with meals",
            "quantity_text": "Disp: 60",
            "refills_text": "Refills: 5",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Metformin",
            "strength": "1000 mg",
            "quantity": 60,
            "days_supply": 30,
            "refills": 5,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth twice daily with meals",
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
            "quantity_calc": "Disp line on the Rx shows 60 tablets.",
            "days_calc": "60 tablets at 2 tablets per day = 30 days supply.",
        },
    },

    # ---- Case 18: Diabetes, basal insulin (units -> mL), days calc, DAW 1 ----
    {
        "case_id": "rx_018",
        "patient": {
            "name": "Ruth Practiceman",
            "dob": "01/19/1960",
            "mrn": "MRN-10018",
            "address": "808 Faculty Row, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "1364297805",
            "dea": "FI9374518",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/04/2026",
            "drug_line": "Insulin glargine (Lantus) 100 units/mL",
            "sig_shorthand": "Inject 20 units SC QHS",
            "quantity_text": "Disp: 10 mL (1 vial)",
            "refills_text": "Refills: 5",
            "daw_text": "DAW: 1 (Brand medically necessary)",
        },
        "expected": {
            "drug_name": "Insulin glargine",
            "strength": "100 units/mL",
            "quantity": 10,
            "days_supply": 50,
            "refills": 5,
            "daw": 1,
            "sig_english": "Inject 20 units under the skin at bedtime",
            "sig_components": {
                "verb": VERB_INJECT,
                "quantity": ["20 units", "20 unit", "twenty units"],
                "route": ROUTE_SC,
                "frequency": FREQ_QHS,
            },
        },
        "extras": {
            "drug_alternates": ["lantus", "basaglar"],
            "quantity_calc": "One U-100 vial = 10 mL, which contains 1000 units.",
            "days_calc": "1000 units per vial divided by 20 units per day = 50 days supply.",
        },
    },

    # ---- Case 19: Pain/fever (NSAID), TID with food, maintenance-style ----
    {
        "case_id": "rx_019",
        "patient": {
            "name": "Felix Trainerton",
            "dob": "03/08/1985",
            "mrn": "MRN-10019",
            "address": "919 Practice Way, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "1487523796",
            "dea": "FT4287563",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/05/2026",
            "drug_line": "Ibuprofen 800 mg tablet",
            "sig_shorthand": "1 tab PO TID with food",
            "quantity_text": "Disp: 90",
            "refills_text": "Refills: 1",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Ibuprofen",
            "strength": "800 mg",
            "quantity": 90,
            "days_supply": 30,
            "refills": 1,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth three times daily with food",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_TID,
            },
        },
        "extras": {
            "drug_alternates": ["motrin", "advil"],
            "quantity_calc": "Disp line on the Rx shows 90 tablets.",
            "days_calc": "90 tablets at 3 tablets per day = 30 days supply.",
        },
    },

    # ---- Case 20: Pain/fever, two-tablet PRN dose, days supply calc ----
    {
        "case_id": "rx_020",
        "patient": {
            "name": "Carmen Mockford",
            "dob": "12/12/1982",
            "mrn": "MRN-10020",
            "address": "151 Mock Ave, Practice City, TX 78001",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "1760395284",
            "dea": "FC2950837",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "06/05/2026",
            "drug_line": "Acetaminophen 500 mg tablet",
            "sig_shorthand": "2 tabs PO Q6H PRN pain",
            "quantity_text": "Disp: 50",
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Acetaminophen",
            "strength": "500 mg",
            "quantity": 50,
            "days_supply": 6,
            "refills": 0,
            "daw": 0,
            "sig_english": "Take 2 tablets by mouth every 6 hours as needed for pain",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["2", "two"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_Q6H,
                "prn": PRN_TERMS,
            },
        },
        "extras": {
            "drug_alternates": ["tylenol"],
            "quantity_calc": "Disp line on the Rx shows 50 tablets.",
            "days_calc": "50 tablets divided by 8 per day (2 tablets up to 4 times daily) = about 6 days supply (PRN max).",
        },
    },

    # ---- Case 21: Allergy, once-daily antihistamine ----
    {
        "case_id": "rx_021",
        "patient": {
            "name": "Iris Sampleby",
            "dob": "06/21/1994",
            "mrn": "MRN-10021",
            "address": "262 Trainee Ave, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "1928461735",
            "dea": "FM6182947",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "06/06/2026",
            "drug_line": "Cetirizine 10 mg tablet",
            "sig_shorthand": "1 tab PO QD",
            "quantity_text": "Disp: 30",
            "refills_text": "Refills: 11",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Cetirizine",
            "strength": "10 mg",
            "quantity": 30,
            "days_supply": 30,
            "refills": 11,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth once daily",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QD,
            },
        },
        "extras": {
            "drug_alternates": ["zyrtec"],
            "quantity_calc": "Disp line on the Rx shows 30 tablets.",
            "days_calc": "30 tablets at 1 tablet per day = 30 days supply.",
        },
    },

    # ---- Case 22: Asthma maintenance (leukotriene), QHS ----
    {
        "case_id": "rx_022",
        "patient": {
            "name": "Theo Demoson",
            "dob": "10/05/2012",
            "mrn": "MRN-10022",
            "address": "373 Demo Dr, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "1364297805",
            "dea": "FI9374518",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/06/2026",
            "drug_line": "Montelukast 10 mg tablet",
            "sig_shorthand": "1 tab PO QHS",
            "quantity_text": "Disp: 30",
            "refills_text": "Refills: 5",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Montelukast",
            "strength": "10 mg",
            "quantity": 30,
            "days_supply": 30,
            "refills": 5,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth at bedtime",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_QHS,
            },
        },
        "extras": {
            "drug_alternates": ["singulair"],
            "quantity_calc": "Disp line on the Rx shows 30 tablets.",
            "days_calc": "30 tablets at 1 tablet per day = 30 days supply.",
        },
    },

    # ---- Case 23: Topical corticosteroid cream, grams quantity ----
    {
        "case_id": "rx_023",
        "patient": {
            "name": "Mabel Practicewell",
            "dob": "08/02/1978",
            "mrn": "MRN-10023",
            "address": "484 Faculty Ave, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "1487523796",
            "dea": "FT4287563",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/07/2026",
            "drug_line": "Triamcinolone 0.1% cream",
            "sig_shorthand": "Apply to affected area BID",
            "quantity_text": "Disp: 30 g",
            "refills_text": "Refills: 2",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Triamcinolone",
            "strength": "0.1%",
            "quantity": 30,
            "days_supply": 30,
            "refills": 2,
            "daw": 0,
            "sig_english": "Apply to the affected area twice daily",
            "sig_components": {
                "verb": VERB_APPLY,
                "route": ROUTE_TOPICAL,
                "frequency": FREQ_BID,
            },
        },
        "extras": {
            "drug_alternates": ["kenalog"],
            "quantity_calc": "Disp line on the Rx shows 30 g (one tube).",
            "days_calc": "Estimated 30 days for a 30 g tube of cream at twice-daily dosing.",
        },
    },

    # ---- Case 24: Topical antibiotic ointment, short course ----
    {
        "case_id": "rx_024",
        "patient": {
            "name": "Andre Sampleman",
            "dob": "04/30/2001",
            "mrn": "MRN-10024",
            "address": "595 Mock Ct, Practice City, TX 78001",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "1760395284",
            "dea": "FC2950837",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "06/07/2026",
            "drug_line": "Mupirocin 2% ointment",
            "sig_shorthand": "Apply to affected area TID x 10 days",
            "quantity_text": "Disp: 22 g",
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Mupirocin",
            "strength": "2%",
            "quantity": 22,
            "days_supply": 10,
            "refills": 0,
            "daw": 0,
            "sig_english": "Apply to the affected area three times daily for 10 days",
            "sig_components": {
                "verb": VERB_APPLY,
                "route": ROUTE_TOPICAL,
                "frequency": FREQ_TID,
                "duration": ["10 days", "ten days"],
            },
        },
        "extras": {
            "drug_alternates": ["bactroban"],
            "quantity_calc": "Disp line on the Rx shows 22 g (one tube).",
            "days_calc": "Duration written on the Rx is 10 days.",
        },
    },

    # ---- Case 25: Ear drops, both ears, short course ----
    {
        "case_id": "rx_025",
        "patient": {
            "name": "Lucia Trialfield",
            "dob": "07/16/2015",
            "mrn": "MRN-10025",
            "address": "606 Education Way, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "1928461735",
            "dea": "FM6182947",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "06/08/2026",
            "drug_line": "Ofloxacin 0.3% otic solution",
            "sig_shorthand": "5 gtt AU BID x 7 days",
            "quantity_text": "Disp: 10 mL",
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Ofloxacin",
            "strength": "0.3%",
            "quantity": 10,
            "days_supply": 7,
            "refills": 0,
            "daw": 0,
            "sig_english": "Instill 5 drops in both ears twice daily for 7 days",
            "sig_components": {
                "verb": VERB_INSTILL,
                "quantity": ["5", "five"],
                "form": FORM_DROP,
                "route": ROUTE_AU,
                "frequency": FREQ_BID,
                "duration": ["7 days", "seven days"],
            },
        },
        "extras": {
            "drug_alternates": ["floxin otic"],
            "quantity_calc": "Disp line on the Rx shows 10 mL (one bottle).",
            "days_calc": "Duration written on the Rx is 7 days.",
        },
    },

    # ---- Case 26: Eye drops, right eye only (OD), QID, short course ----
    {
        "case_id": "rx_026",
        "patient": {
            "name": "Oscar Demoby",
            "dob": "02/27/1953",
            "mrn": "MRN-10026",
            "address": "717 Demo Pkwy, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "1364297805",
            "dea": "FI9374518",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/08/2026",
            "drug_line": "Ciprofloxacin 0.3% ophthalmic solution",
            "sig_shorthand": "1 gtt OD QID x 7 days",
            "quantity_text": "Disp: 5 mL",
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Ciprofloxacin",
            "strength": "0.3%",
            "quantity": 5,
            "days_supply": 7,
            "refills": 0,
            "daw": 0,
            "sig_english": "Instill 1 drop in the right eye four times daily for 7 days",
            "sig_components": {
                "verb": VERB_INSTILL,
                "quantity": ["1", "one"],
                "form": FORM_DROP,
                "route": ROUTE_OD_EYE,
                "frequency": FREQ_QID,
                "duration": ["7 days", "seven days"],
            },
        },
        "extras": {
            "drug_alternates": ["ciloxan"],
            "quantity_calc": "Disp line on the Rx shows 5 mL (one bottle).",
            "days_calc": "Duration written on the Rx is 7 days.",
        },
    },

    # ---- Case 27: Rescue inhaler, PRN, quantity is one device ----
    {
        "case_id": "rx_027",
        "patient": {
            "name": "Daria Mockwell",
            "dob": "09/11/1988",
            "mrn": "MRN-10027",
            "address": "828 Practice Ln, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Jane Trainer, MD",
            "npi": "1487523796",
            "dea": "FT4287563",
            "address": "200 Practice Blvd, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/09/2026",
            "drug_line": "Albuterol HFA 90 mcg/actuation inhaler",
            "sig_shorthand": "2 puffs INH Q6H PRN shortness of breath",
            "quantity_text": "Disp: 1 inhaler (200 actuations)",
            "refills_text": "Refills: 2",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Albuterol",
            "strength": "90 mcg",
            "quantity": 1,
            "days_supply": 30,
            "refills": 2,
            "daw": 0,
            "sig_english": "Inhale 2 puffs by mouth every 6 hours as needed for shortness of breath",
            "sig_components": {
                "verb": VERB_INHALE,
                "quantity": ["2", "two"],
                "form": FORM_PUFF,
                "route": ROUTE_INH,
                "frequency": FREQ_Q6H,
                "prn": PRN_TERMS,
            },
        },
        "extras": {
            "drug_alternates": ["proair", "ventolin", "proventil"],
            "quantity_calc": "An inhaler is counted as 1 device (here a 200-actuation canister), not by puffs.",
            "days_calc": "A rescue inhaler is typically processed as a 30-day supply.",
        },
    },

    # ---- Case 28: Maintenance inhaler, doses -> days supply calculation ----
    {
        "case_id": "rx_028",
        "patient": {
            "name": "Niko Practicely",
            "dob": "05/03/1971",
            "mrn": "MRN-10028",
            "address": "939 Trainer Ct, Practice City, TX 78001",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Robert Coach, MD",
            "npi": "1760395284",
            "dea": "FC2950837",
            "address": "300 Trainer Ave, Practice City, TX 78001",
        },
        "rx_text": {
            "date_written": "06/09/2026",
            "drug_line": "Fluticasone-salmeterol 250/50 mcg (Advair Diskus)",
            "sig_shorthand": "1 puff INH BID",
            "quantity_text": "Disp: 1 inhaler (60 doses)",
            "refills_text": "Refills: 2",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Fluticasone-salmeterol",
            "strength": "250/50 mcg",
            "quantity": 1,
            "days_supply": 30,
            "refills": 2,
            "daw": 0,
            "sig_english": "Inhale 1 puff by mouth twice daily",
            "sig_components": {
                "verb": VERB_INHALE,
                "quantity": ["1", "one"],
                "form": FORM_PUFF,
                "route": ROUTE_INH,
                "frequency": FREQ_BID,
            },
        },
        "extras": {
            "drug_alternates": ["advair", "advair diskus"],
            "quantity_calc": "The device is counted as 1 inhaler (here a 60-dose Diskus).",
            "days_calc": "60 doses divided by 2 doses per day = 30 days supply.",
        },
    },

    # ---- Case 29: Short-course oral steroid, quantity calculation ----
    {
        "case_id": "rx_029",
        "patient": {
            "name": "Wendy Sampleton",
            "dob": "11/28/1990",
            "mrn": "MRN-10029",
            "address": "104 Education Pl, Training Town, TX 78002",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "Sarah Mentor, DO",
            "npi": "1928461735",
            "dea": "FM6182947",
            "address": "500 Education Ln, Training Town, TX 78002",
        },
        "rx_text": {
            "date_written": "06/10/2026",
            "drug_line": "Prednisone 10 mg tablet",
            "sig_shorthand": "1 tab PO TID x 5 days",
            "quantity_text": None,
            "refills_text": "Refills: 0",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Prednisone",
            "strength": "10 mg",
            "quantity": 15,
            "days_supply": 5,
            "refills": 0,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth three times daily for 5 days",
            "sig_components": {
                "verb": VERB_TAKE,
                "quantity": ["1", "one"],
                "form": FORM_TABLET,
                "route": ROUTE_PO,
                "frequency": FREQ_TID,
                "duration": ["5 days", "five days"],
            },
        },
        "extras": {
            "drug_alternates": ["deltasone"],
            "quantity_calc": "1 tab x 3 times/day x 5 days = 15 tablets.",
            "days_calc": "Duration written on the Rx is 5 days.",
        },
    },

    # ---- Case 30: Maintenance statin, QHS, 90-day supply ----
    {
        "case_id": "rx_030",
        "patient": {
            "name": "Hugo Trainberg",
            "dob": "03/22/1959",
            "mrn": "MRN-10030",
            "address": "215 Faculty Ln, Sample City, TX 78000",
            "allergies": ["NKDA"],
        },
        "prescriber": {
            "name": "David Instructor, MD",
            "npi": "1364297805",
            "dea": "FI9374518",
            "address": "720 Faculty Pkwy, Sample City, TX 78000",
        },
        "rx_text": {
            "date_written": "06/10/2026",
            "drug_line": "Atorvastatin 40 mg tablet",
            "sig_shorthand": "1 tab PO QHS",
            "quantity_text": "Disp: 90",
            "refills_text": "Refills: 3",
            "daw_text": "DAW: 0",
        },
        "expected": {
            "drug_name": "Atorvastatin",
            "strength": "40 mg",
            "quantity": 90,
            "days_supply": 90,
            "refills": 3,
            "daw": 0,
            "sig_english": "Take 1 tablet by mouth at bedtime",
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
            "quantity_calc": "Disp line on the Rx shows 90 tablets.",
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
