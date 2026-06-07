"""Pharmacy Technician Prescription Entry Simulator.

Streamlit UI layer. This is the only module that imports streamlit.
All validation lives in checker.py, all stats live in tracker.py,
all case data lives in cases.py.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import html
import re
from datetime import date
from io import BytesIO

import streamlit as st

import cases
import checker
import tracker

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


FIELD_LABELS = {
    "drug_name": "Drug name",
    "strength": "Strength",
    "quantity": "Quantity",
    "sig": "SIG (English)",
    "days_supply": "Days supply",
    "refills": "Refills",
    "daw": "DAW",
}

# =====================================================================
# Form widget keys
# Static keys for the seven entry-form widgets. Used when the form is in
# normal mode (user typing their own answers). In example mode the form
# uses different keys (ex_drug_<case_id>, etc.) so example values can be
# passed via the value= parameter directly. advance_case clears these
# keys to blank the form for a new case.
# =====================================================================
WIDGET_KEYS = [
    "in_drug",
    "in_strength",
    "in_quantity",
    "in_sig",
    "in_days",
    "in_refills",
    "in_daw",
]


# =====================================================================
# Drug Knowledge reference data
# Keyed by lowercase generic name. High-yield list assembled from common
# Top-200 pharmacy technician study conventions; not an official exam list
# and not clinical guidance. Entries are kept alphabetical so Prev/Next
# navigation in the Drug Knowledge section moves through them predictably.
# =====================================================================

DRUG_INFO: dict[str, dict] = {
    "acetaminophen": {
        "generic": "Acetaminophen",
        "brand_examples": ["Tylenol"],
        "dosage_forms": ["tablet", "capsule", "oral suspension", "chewable tablet", "suppository"],
        "category": "Non-opioid analgesic / antipyretic. Training-use category: pain and fever relief (non-NSAID).",
        "counseling": (
            "Do not exceed 4 grams in 24 hours from all sources. Avoid combining "
            "with alcohol due to liver toxicity risk. Check OTC cold and flu "
            "products for hidden acetaminophen content."
        ),
        "lasa": "Look-alike / sound-alike with combination products like hydrocodone-acetaminophen and oxycodone-acetaminophen.",
    },
    "albuterol": {
        "generic": "Albuterol",
        "brand_examples": ["ProAir", "Ventolin", "Proventil"],
        "dosage_forms": ["metered-dose inhaler", "nebulizer solution", "tablet", "syrup"],
        "category": "Short-acting beta-2 agonist (SABA). Training-use category: rescue inhaler for asthma and COPD.",
        "counseling": (
            "Use for sudden shortness of breath or wheezing, not for daily "
            "maintenance. Shake the inhaler and prime as directed before each "
            "use. Report needing more than two canisters per month."
        ),
        "lasa": "Look-alike / sound-alike with atenolol (a beta blocker) by spelling; verify the order carefully.",
    },
    "alprazolam": {
        "generic": "Alprazolam",
        "brand_examples": ["Xanax"],
        "dosage_forms": ["tablet", "extended-release tablet", "orally disintegrating tablet", "oral solution"],
        "category": "Short-acting benzodiazepine. Schedule IV controlled substance. Training-use category: anxiety and panic disorder.",
        "counseling": (
            "Take only as prescribed. Avoid alcohol and other CNS depressants. "
            "Do not stop abruptly after long-term use; taper under prescriber "
            "direction to avoid withdrawal."
        ),
        "lasa": "Look-alike / sound-alike with lorazepam and clonazepam (other benzodiazepines).",
    },
    "amlodipine": {
        "generic": "Amlodipine",
        "brand_examples": ["Norvasc"],
        "dosage_forms": ["tablet"],
        "category": "Dihydropyridine calcium channel blocker. Training-use category: antihypertensive.",
        "counseling": (
            "A common side effect is ankle or foot swelling (peripheral edema). "
            "Take at the same time each day. Do not stop abruptly without prescriber input."
        ),
        "lasa": "Look-alike / sound-alike with amiloride (a diuretic) and amantadine (an antiviral).",
    },
    "amoxicillin": {
        "generic": "Amoxicillin",
        "brand_examples": ["Amoxil"],
        "dosage_forms": ["capsule", "tablet", "oral suspension", "chewable tablet"],
        "category": "Aminopenicillin antibiotic. Training-use category: oral antibiotic.",
        "counseling": (
            "Complete the full course as prescribed even if symptoms improve. "
            "Take with or without food. Report rash or breathing difficulty immediately."
        ),
        "lasa": "Look-alike / sound-alike with amoxapine (an antidepressant) and ampicillin (another beta-lactam antibiotic).",
    },
    "apixaban": {
        "generic": "Apixaban",
        "brand_examples": ["Eliquis"],
        "dosage_forms": ["tablet"],
        "category": "Direct-acting oral anticoagulant (DOAC), factor Xa inhibitor. Training-use category: oral anticoagulant.",
        "counseling": (
            "Take exactly as prescribed at the same times daily. Report any "
            "unusual bleeding, bruising, dark stools, or blood in urine. Do not "
            "stop without prescriber direction (clot risk)."
        ),
        "lasa": "Look-alike / sound-alike with other DOACs: rivaroxaban, dabigatran, edoxaban.",
    },
    "atorvastatin": {
        "generic": "Atorvastatin",
        "brand_examples": ["Lipitor"],
        "dosage_forms": ["tablet"],
        "category": "HMG-CoA reductase inhibitor. Training-use category: statin (cholesterol lowering).",
        "counseling": (
            "Take at the same time each day. Report unexplained muscle pain, "
            "weakness, or dark urine. Avoid large quantities of grapefruit juice."
        ),
        "lasa": "Look-alike / sound-alike with other statins: simvastatin, rosuvastatin, pravastatin.",
    },
    "azithromycin": {
        "generic": "Azithromycin",
        "brand_examples": ["Zithromax", "Z-Pak"],
        "dosage_forms": ["tablet", "oral suspension", "extended-release oral suspension", "intravenous"],
        "category": "Macrolide antibiotic. Training-use category: oral antibiotic for respiratory and skin infections.",
        "counseling": (
            "Complete the full course as directed (often a 5-day Z-Pak). Can be "
            "taken with or without food. Report severe diarrhea, hearing changes, "
            "or irregular heartbeat."
        ),
        "lasa": "Look-alike / sound-alike with erythromycin and clarithromycin (other macrolides).",
    },
    "cetirizine": {
        "generic": "Cetirizine",
        "brand_examples": ["Zyrtec"],
        "dosage_forms": ["tablet", "chewable tablet", "orally disintegrating tablet", "oral solution", "capsule"],
        "category": "Second-generation antihistamine. Training-use category: allergy relief (less sedating).",
        "counseling": (
            "Used for sneezing, runny nose, and itchy or watery eyes. Less "
            "drowsy than older antihistamines but can still cause some "
            "drowsiness. One dose usually covers 24 hours."
        ),
        "lasa": "Look-alike / sound-alike with sertraline by spelling; verify the order carefully.",
    },
    "cephalexin": {
        "generic": "Cephalexin",
        "brand_examples": ["Keflex"],
        "dosage_forms": ["capsule", "tablet", "oral suspension"],
        "category": "First-generation cephalosporin antibiotic. Training-use category: oral antibiotic for skin and urinary tract infections.",
        "counseling": (
            "Complete the full course even if symptoms improve. Take with food "
            "if stomach upset. Patients with penicillin allergy require pharmacist "
            "evaluation due to possible cross-reactivity."
        ),
        "lasa": "Look-alike / sound-alike with cefazolin and other cephalosporins; confirm spelling vs ciprofloxacin (different class).",
    },
    "ciprofloxacin": {
        "generic": "Ciprofloxacin",
        "brand_examples": ["Cipro"],
        "dosage_forms": ["tablet", "oral suspension", "ophthalmic solution", "otic solution"],
        "category": "Fluoroquinolone antibiotic. Training-use category: broad-spectrum oral antibiotic.",
        "counseling": (
            "Avoid taking with dairy, antacids, or iron / calcium / zinc "
            "supplements (separate by at least 2 hours). Stay well hydrated. "
            "Report tendon pain."
        ),
        "lasa": "Look-alike / sound-alike with cephalexin and with other fluoroquinolones (levofloxacin, moxifloxacin).",
    },
    "clotrimazole": {
        "generic": "Clotrimazole",
        "brand_examples": ["Lotrimin", "Mycelex"],
        "dosage_forms": ["cream", "topical solution", "lozenge (troche)", "vaginal cream"],
        "category": "Azole antifungal. Training-use category: topical antifungal for skin and yeast infections.",
        "counseling": (
            "Apply a thin layer to the affected area, usually twice daily. "
            "Complete the full course even if the rash clears early. For "
            "external skin use unless the specific product form says otherwise."
        ),
        "lasa": "Look-alike / sound-alike with other '-azole' antifungals such as ketoconazole and miconazole.",
    },
    "clopidogrel": {
        "generic": "Clopidogrel",
        "brand_examples": ["Plavix"],
        "dosage_forms": ["tablet"],
        "category": "P2Y12 platelet inhibitor (antiplatelet). Training-use category: prevention of cardiovascular events after MI or stent placement.",
        "counseling": (
            "Take at the same time each day. Report unusual bruising or "
            "bleeding. Do not stop without prescriber input, especially after "
            "recent stent placement (high clot risk)."
        ),
        "lasa": "Look-alike / sound-alike with clobazam (an anticonvulsant) and clozapine.",
    },
    "escitalopram": {
        "generic": "Escitalopram",
        "brand_examples": ["Lexapro"],
        "dosage_forms": ["tablet", "oral solution"],
        "category": "Selective serotonin reuptake inhibitor (SSRI). Training-use category: depression and generalized anxiety.",
        "counseling": (
            "Effects build over 4 to 6 weeks. Do not stop abruptly. Report "
            "worsening mood or suicidal thoughts immediately, especially in "
            "the first weeks of therapy."
        ),
        "lasa": "Look-alike / sound-alike with citalopram (very similar names and class) and other SSRIs.",
    },
    "fluticasone-salmeterol": {
        "generic": "Fluticasone / Salmeterol",
        "brand_examples": ["Advair Diskus", "Advair HFA", "AirDuo"],
        "dosage_forms": ["dry powder inhaler", "metered-dose inhaler"],
        "category": "Inhaled corticosteroid (ICS) plus long-acting beta-2 agonist (LABA) combination. Training-use category: maintenance inhaler for asthma and COPD.",
        "counseling": (
            "Use daily for maintenance, not as a rescue inhaler. Rinse mouth "
            "and spit after each dose to prevent oral thrush. Do not stop suddenly."
        ),
        "lasa": "Look-alike / sound-alike with budesonide-formoterol (Symbicort) and other ICS/LABA combinations.",
    },
    "gabapentin": {
        "generic": "Gabapentin",
        "brand_examples": ["Neurontin", "Gralise"],
        "dosage_forms": ["capsule", "tablet", "oral solution"],
        "category": "Gabapentinoid. Training-use category: neuropathic pain, partial seizures, postherpetic neuralgia.",
        "counseling": (
            "May cause drowsiness and dizziness, especially early in therapy. "
            "Do not stop abruptly. Adjust dosing if kidney function is reduced "
            "(renal dose adjustment is common)."
        ),
        "lasa": "Look-alike / sound-alike with pregabalin (Lyrica, similar drug class).",
    },
    "glipizide": {
        "generic": "Glipizide",
        "brand_examples": ["Glucotrol", "Glucotrol XL"],
        "dosage_forms": ["tablet", "extended-release tablet"],
        "category": "Sulfonylurea. Training-use category: oral antidiabetic for type 2 diabetes.",
        "counseling": (
            "Take 30 minutes before breakfast. Watch for hypoglycemia signs "
            "(shakiness, sweating, confusion). Carry a fast-acting sugar source."
        ),
        "lasa": "Look-alike / sound-alike with glyburide and glimepiride (other sulfonylureas).",
    },
    "hydrochlorothiazide": {
        "generic": "Hydrochlorothiazide",
        "brand_examples": ["Microzide"],
        "dosage_forms": ["tablet", "capsule"],
        "category": "Thiazide diuretic. Training-use category: antihypertensive and edema management.",
        "counseling": (
            "Take in the morning to avoid nighttime urination. Use sunscreen "
            "due to photosensitivity. Watch for potassium loss; report muscle "
            "cramps or weakness."
        ),
        "lasa": "Look-alike / sound-alike with hydrocortisone (often abbreviated HCTZ vs HC). High-risk medication-error pair.",
    },
    "hydrocortisone": {
        "generic": "Hydrocortisone",
        "brand_examples": ["Cortizone-10", "Cortaid"],
        "dosage_forms": ["cream", "ointment", "lotion", "oral tablet", "injection"],
        "category": "Low-potency topical corticosteroid. Training-use category: topical anti-inflammatory.",
        "counseling": (
            "Apply a thin layer to the affected area only. Avoid use on broken "
            "skin or near the eyes unless directed. Limit duration to prevent "
            "skin thinning."
        ),
        "lasa": "Look-alike / sound-alike with hydrochlorothiazide (a diuretic, often abbreviated HCTZ).",
    },
    "ibuprofen": {
        "generic": "Ibuprofen",
        "brand_examples": ["Motrin", "Advil"],
        "dosage_forms": ["tablet", "capsule", "oral suspension", "chewable tablet"],
        "category": "Non-selective NSAID. Training-use category: analgesic / antipyretic / anti-inflammatory.",
        "counseling": (
            "Take with food or milk to reduce GI upset. Stay well hydrated. "
            "Report GI bleeding signs (black stools, vomiting blood) or "
            "unexplained swelling. Avoid in late pregnancy and in patients on "
            "anticoagulants without prescriber approval."
        ),
        "lasa": "Look-alike / sound-alike with naproxen (a similar NSAID).",
    },
    "insulin glargine": {
        "generic": "Insulin Glargine",
        "brand_examples": ["Lantus", "Basaglar", "Toujeo"],
        "dosage_forms": ["prefilled pen", "vial"],
        "category": "Long-acting basal insulin analog. Training-use category: basal insulin for type 1 and type 2 diabetes.",
        "counseling": (
            "Inject once daily at the same time each day, usually bedtime. "
            "Rotate injection sites. Do not mix in the same syringe with other "
            "insulins."
        ),
        "lasa": "Look-alike / sound-alike with insulin detemir (Levemir) and insulin lispro (Humalog, a rapid-acting). Insulin name and concentration errors are high-risk.",
    },
    "latanoprost": {
        "generic": "Latanoprost",
        "brand_examples": ["Xalatan"],
        "dosage_forms": ["ophthalmic solution"],
        "category": "Prostaglandin analog. Training-use category: ophthalmic - reduces intraocular pressure in glaucoma.",
        "counseling": (
            "Use once daily in the evening. May darken iris color and increase "
            "eyelash growth over time. Press on the inside corner of the eye "
            "for 1 to 2 minutes after instilling."
        ),
        "lasa": "Look-alike / sound-alike with other prostaglandin analogs (bimatoprost, travoprost).",
    },
    "levothyroxine": {
        "generic": "Levothyroxine",
        "brand_examples": ["Synthroid", "Levoxyl", "Tirosint"],
        "dosage_forms": ["tablet", "capsule", "oral solution", "injection"],
        "category": "Synthetic thyroid hormone (T4). Training-use category: hypothyroidism replacement therapy.",
        "counseling": (
            "Take on an empty stomach 30 to 60 minutes before breakfast. "
            "Separate from calcium, iron, and antacids by at least 4 hours. "
            "Do not switch between brand and generic without prescriber awareness."
        ),
        "lasa": "Look-alike / sound-alike with liothyronine (T3) and combination thyroid products. Different strengths look very similar.",
    },
    "lisinopril": {
        "generic": "Lisinopril",
        "brand_examples": ["Prinivil", "Zestril"],
        "dosage_forms": ["tablet"],
        "category": "ACE inhibitor. Training-use category: antihypertensive.",
        "counseling": (
            "Take at the same time each day. Watch for a persistent dry cough "
            "or swelling of the face / throat (angioedema) and report "
            "immediately. Avoid potassium supplements unless directed."
        ),
        "lasa": "Look-alike / sound-alike with fosinopril, enalapril, and other '-pril' ACE inhibitors.",
    },
    "loratadine": {
        "generic": "Loratadine",
        "brand_examples": ["Claritin"],
        "dosage_forms": ["tablet", "orally disintegrating tablet", "chewable tablet", "oral solution", "capsule"],
        "category": "Second-generation antihistamine. Training-use category: non-drowsy allergy relief.",
        "counseling": (
            "Used for seasonal and year-round allergy symptoms. Usually "
            "non-drowsy at the labeled dose. Taken once daily; effects last "
            "about 24 hours."
        ),
        "lasa": "Look-alike / sound-alike with desloratadine and with loratadine-D products (which add the decongestant pseudoephedrine).",
    },
    "losartan": {
        "generic": "Losartan",
        "brand_examples": ["Cozaar"],
        "dosage_forms": ["tablet"],
        "category": "Angiotensin II receptor blocker (ARB). Training-use category: antihypertensive, often used in patients who cannot tolerate ACE inhibitors.",
        "counseling": (
            "Take at the same time each day. Report swelling of the face, "
            "lips, or tongue immediately. Avoid potassium supplements unless "
            "directed."
        ),
        "lasa": "Look-alike / sound-alike with valsartan, irbesartan, and other ARBs ending in '-sartan'.",
    },
    "metformin": {
        "generic": "Metformin",
        "brand_examples": ["Glucophage"],
        "dosage_forms": ["tablet", "extended-release tablet", "oral solution"],
        "category": "Biguanide. Training-use category: oral antidiabetic for type 2 diabetes.",
        "counseling": (
            "Take with meals to reduce GI upset. Hold the dose and call the "
            "prescriber before any contrast imaging procedures (lactic "
            "acidosis risk)."
        ),
        "lasa": "Look-alike / sound-alike with metoprolol (a beta blocker). Verify the spelling carefully.",
    },
    "metoprolol": {
        "generic": "Metoprolol",
        "brand_examples": ["Lopressor (tartrate)", "Toprol-XL (succinate)"],
        "dosage_forms": ["tablet", "extended-release tablet", "injection"],
        "category": "Cardioselective beta-1 blocker. Training-use category: antihypertensive, heart failure, post-MI care.",
        "counseling": (
            "Take with or immediately after meals. Do not stop abruptly "
            "(rebound hypertension and angina risk). Tartrate and succinate "
            "forms are NOT interchangeable."
        ),
        "lasa": "Look-alike / sound-alike with metformin (very common error pair) and misoprostol. Tartrate vs succinate confusion is also high-risk.",
    },
    "naproxen": {
        "generic": "Naproxen",
        "brand_examples": ["Aleve", "Naprosyn"],
        "dosage_forms": ["tablet", "capsule", "oral suspension", "delayed-release tablet"],
        "category": "Non-selective NSAID. Training-use category: pain, inflammation, fever.",
        "counseling": (
            "Take with food or milk to reduce GI upset. Use the lowest "
            "effective dose. Watch for stomach pain, dark stools, or unusual "
            "swelling. Avoid in late pregnancy."
        ),
        "lasa": "Look-alike / sound-alike with naloxone (an opioid reversal agent). Very different drugs despite similar starts.",
    },
    "omeprazole": {
        "generic": "Omeprazole",
        "brand_examples": ["Prilosec"],
        "dosage_forms": ["delayed-release capsule", "delayed-release tablet", "oral suspension"],
        "category": "Proton pump inhibitor (PPI). Training-use category: GERD, peptic ulcer disease, hyperacidity.",
        "counseling": (
            "Take 30 to 60 minutes before the first meal of the day. Do not "
            "crush or chew delayed-release forms. Long-term use is associated "
            "with bone fracture and B12 deficiency risk."
        ),
        "lasa": "Look-alike / sound-alike with other PPIs (pantoprazole, lansoprazole, esomeprazole) and ondansetron (similar starting letters).",
    },
    "pantoprazole": {
        "generic": "Pantoprazole",
        "brand_examples": ["Protonix"],
        "dosage_forms": ["delayed-release tablet", "delayed-release oral suspension", "intravenous"],
        "category": "Proton pump inhibitor (PPI). Training-use category: GERD, erosive esophagitis, hospital ulcer prophylaxis.",
        "counseling": (
            "Take 30 minutes before a meal. Swallow tablets whole; do not "
            "split or crush. Report severe diarrhea (C. difficile risk with "
            "long-term use)."
        ),
        "lasa": "Look-alike / sound-alike with other PPIs (omeprazole, esomeprazole, lansoprazole).",
    },
    "sertraline": {
        "generic": "Sertraline",
        "brand_examples": ["Zoloft"],
        "dosage_forms": ["tablet", "oral concentrate (solution)"],
        "category": "Selective serotonin reuptake inhibitor (SSRI). Training-use category: depression, anxiety, PTSD, OCD.",
        "counseling": (
            "Take with food to improve absorption. Therapeutic effects take "
            "4 to 6 weeks. Do not stop abruptly. Report new agitation or "
            "suicidal thoughts, especially in the first weeks."
        ),
        "lasa": "Look-alike / sound-alike with other SSRIs and with cetirizine by spelling.",
    },
    "simvastatin": {
        "generic": "Simvastatin",
        "brand_examples": ["Zocor"],
        "dosage_forms": ["tablet"],
        "category": "HMG-CoA reductase inhibitor. Training-use category: statin (cholesterol lowering).",
        "counseling": (
            "Take in the evening. Avoid grapefruit juice. Report unexplained "
            "muscle pain or weakness, dark urine, or fatigue."
        ),
        "lasa": "Look-alike / sound-alike with other statins (atorvastatin, rosuvastatin, pravastatin). The 80 mg dose has specific safety restrictions.",
    },
    "timolol": {
        "generic": "Timolol",
        "brand_examples": ["Timoptic"],
        "dosage_forms": ["ophthalmic solution", "ophthalmic gel", "tablet"],
        "category": "Non-selective beta blocker. Training-use category: ophthalmic glaucoma treatment.",
        "counseling": (
            "Press on the inside corner of the eye for 1 to 2 minutes after "
            "each drop to reduce systemic absorption. Report breathing "
            "difficulty, slow heart rate, or unusual fatigue."
        ),
        "lasa": "Look-alike / sound-alike with atenolol and other '-olol' beta blockers.",
    },
    "tramadol": {
        "generic": "Tramadol",
        "brand_examples": ["Ultram"],
        "dosage_forms": ["tablet", "extended-release tablet", "extended-release capsule"],
        "category": "Centrally acting opioid analgesic. Schedule IV controlled substance. Training-use category: moderate pain.",
        "counseling": (
            "Risk of dependence and seizures, particularly at high doses or "
            "when combined with antidepressants. Avoid alcohol. Do not stop "
            "abruptly after long-term use."
        ),
        "lasa": "Look-alike / sound-alike with trazodone (an antidepressant, NOT an opioid). Very common dispensing error.",
    },
    "triamcinolone": {
        "generic": "Triamcinolone Acetonide",
        "brand_examples": ["Kenalog", "Aristocort"],
        "dosage_forms": ["cream", "ointment", "lotion", "dental paste", "nasal spray", "injection"],
        "category": "Medium-potency topical corticosteroid (varies by formulation). Training-use category: topical anti-inflammatory.",
        "counseling": (
            "Apply a thin layer to clean, dry skin. Do not use on the face, "
            "groin, or under occlusive dressings unless directed. Avoid "
            "prolonged use to prevent skin thinning."
        ),
        "lasa": "Look-alike / sound-alike with hydrocortisone and other topical steroids. Strength categories (low, medium, high potency) are easy to confuse.",
    },
    "warfarin": {
        "generic": "Warfarin",
        "brand_examples": ["Coumadin", "Jantoven"],
        "dosage_forms": ["tablet"],
        "category": "Vitamin K antagonist anticoagulant. Training-use category: oral anticoagulant requiring routine INR monitoring.",
        "counseling": (
            "Keep vitamin K intake (leafy greens) consistent. Many drug and "
            "food interactions; check with the pharmacist before starting new "
            "medications. Report unusual bleeding or bruising."
        ),
        "lasa": "Look-alike / sound-alike with other anticoagulants. Strength tablets are color-coded; verify color matches strength on every fill.",
    },
}


# =====================================================================
# Drug Knowledge categories
# Curated, beginner-friendly therapeutic groupings for the Drug Knowledge
# study section. Each "drugs" list holds DRUG_INFO keys (lowercase generic
# names). Grouping is for training / reference only, not clinical guidance.
# =====================================================================

DRUG_CATEGORIES: list[dict] = [
    {
        "id": "hypertension",
        "label": "Hypertension",
        "blurb": (
            "Blood-pressure and heart medications. Watch strengths closely and "
            "learn the '-pril', '-sartan', and '-olol' name endings."
        ),
        "drugs": ["lisinopril", "losartan", "amlodipine", "metoprolol", "hydrochlorothiazide"],
    },
    {
        "id": "antibiotics",
        "label": "Antibiotics",
        "blurb": (
            "Anti-infectives. Stress finishing the full course, and always "
            "check the patient's allergy history before filling."
        ),
        "drugs": ["amoxicillin", "azithromycin", "cephalexin", "ciprofloxacin"],
    },
    {
        "id": "diabetes",
        "label": "Diabetes",
        "blurb": (
            "Blood-sugar medications. Insulin names and concentrations are "
            "high-alert — verify them carefully."
        ),
        "drugs": ["metformin", "glipizide", "insulin glargine"],
    },
    {
        "id": "pain",
        "label": "Pain & fever",
        "blurb": (
            "Analgesics and fever reducers. Note NSAID stomach / bleeding "
            "cautions and the 4 g per day acetaminophen limit."
        ),
        "drugs": ["acetaminophen", "ibuprofen", "naproxen", "tramadol"],
    },
    {
        "id": "allergy",
        "label": "Allergy & asthma",
        "blurb": (
            "Antihistamines and inhalers. Keep rescue inhalers separate from "
            "daily maintenance inhalers."
        ),
        "drugs": ["cetirizine", "loratadine", "albuterol", "fluticasone-salmeterol"],
    },
    {
        "id": "topical",
        "label": "Topical",
        "blurb": (
            "Creams and ointments. Apply a thin layer to the affected area and "
            "mind potency and site cautions."
        ),
        "drugs": ["hydrocortisone", "triamcinolone", "clotrimazole"],
    },
]


# =====================================================================
# Workflow Scenarios - fictional pharmacy workflow decisions
# Each scenario presents a situation, patient/case context, 3-4 actions,
# a best action index, an explanation of the best action, and a reminder
# of when to escalate the issue to the pharmacist. Training only - not
# medical or legal advice.
# =====================================================================

SCENARIOS: list[dict] = [
    {
        "id": "refill_too_soon",
        "title": "Refill Too Soon",
        "situation": (
            "A fictional patient drops off a refill request for amlodipine 5 mg tablet "
            "(90-day supply, quantity 90). The pharmacy system shows the previous fill "
            "was 28 days ago and the plan requires 75% of the prior supply to be "
            "consumed before authorizing another fill."
        ),
        "context": [
            ("Patient", "James Reed, 62 (fictional)"),
            ("Medication", "Amlodipine 5 mg tablet · Qty 90"),
            ("Last fill", "28 days ago (90-day supply)"),
            ("Plan rule", "75% of supply used before refill"),
        ],
        "options": [
            "Process the refill anyway since the patient asked nicely.",
            "Inform the patient the plan considers this refill too soon and provide the next eligible refill date.",
            "Submit the claim through insurance and let the rejection sort itself out.",
            "Bill the patient out of pocket for the full retail price without offering other options.",
        ],
        "best_index": 1,
        "explanation": (
            "Most plans enforce a 75 to 80 percent rule for chronic medications. "
            "Submitting an early claim typically returns NCPDP code 79 (refill too "
            "soon). The standard workflow is to inform the patient of the next "
            "eligible date so they can plan ahead. Cash pricing is an option only "
            "if the patient requests it after being informed of the timing rule."
        ),
        "escalation": (
            "Escalate if the patient says they are out of medication, traveling, or "
            "had a dose change. A pharmacist can request an early-refill override or "
            "vacation supply. Technicians explain the timing rule but do not override "
            "plan limits on their own."
        ),
    },
    {
        "id": "allergy_warning",
        "title": "Allergy Warning",
        "situation": (
            "A new fictional prescription arrives for cephalexin 500 mg capsule for a "
            "patient whose profile shows a documented penicillin allergy reported as "
            "'rash.' The pharmacy system flags a cross-reactivity warning."
        ),
        "context": [
            ("Patient", "Maria Lopez, 47 (fictional)"),
            ("New Rx", "Cephalexin 500 mg capsule"),
            ("Profile", "Penicillin allergy — reported rash"),
            ("System", "Cross-reactivity alert fired"),
        ],
        "options": [
            "Fill the prescription without alerting anyone since rash is mild.",
            "Refuse to fill and tell the patient to go to another pharmacy.",
            "Alert the pharmacist for clinical review of the cephalosporin allergy cross-reactivity.",
            "Remove the allergy entry from the patient's profile since the patient probably outgrew it.",
        ],
        "best_index": 2,
        "explanation": (
            "Pharmacy technicians are not authorized to dismiss allergy alerts or "
            "modify allergy records. Cephalosporins share a beta-lactam ring with "
            "penicillins, so cross-reactivity is possible (estimated 1 to 2 percent "
            "in confirmed penicillin allergy). The pharmacist evaluates the allergy "
            "history and severity before deciding whether to fill, contact the "
            "prescriber, or counsel the patient on the risk."
        ),
        "escalation": (
            "Always escalate allergy alerts. Only the pharmacist can judge the "
            "allergy type and severity and decide whether to fill, call the "
            "prescriber, or counsel the patient. Technicians never edit or remove "
            "allergy records."
        ),
    },
    {
        "id": "prescriber_clarification",
        "title": "Prescriber Clarification",
        "situation": (
            "A handwritten fictional prescription comes in. The drug is clearly "
            "lisinopril but the strength is illegible. It could be 10 mg or 40 mg. "
            "The directions read 'Take 1 tablet by mouth once daily.'"
        ),
        "context": [
            ("Patient", "Edward Kim, 58 (fictional)"),
            ("Drug", "Lisinopril (strength illegible)"),
            ("Possible", "10 mg or 40 mg"),
            ("Directions", "Take 1 tablet by mouth once daily"),
        ],
        "options": [
            "Pick 10 mg since it is a common starting dose.",
            "Call the prescriber's office to clarify the strength before filling.",
            "Fill with whatever strength is most commonly stocked in your pharmacy.",
            "Ask the patient what strength they were told to take.",
        ],
        "best_index": 1,
        "explanation": (
            "Strength is a critical prescription field. Lisinopril is available in "
            "multiple strengths (2.5 mg through 40 mg) and the wrong strength can "
            "cause hypotension or undertreated hypertension. Patients sometimes do "
            "not know their exact doses. Always contact the prescriber to confirm "
            "illegible or ambiguous fields, and document the clarification with the "
            "name of the staff member you spoke with, the date, and the time."
        ),
        "escalation": (
            "When any required field is unreadable or ambiguous, the prescriber's "
            "office must confirm it and the pharmacist verifies the clarification "
            "before dispensing. Technicians may gather information but do not guess "
            "critical fields like strength."
        ),
    },
    {
        "id": "dur_warning",
        "title": "DUR Warning",
        "situation": (
            "A fictional prescription for ibuprofen 600 mg twice daily as needed for "
            "pain comes in. The patient's profile shows they were dispensed warfarin "
            "(an anticoagulant) two weeks ago. The Drug Utilization Review system "
            "flags a major drug-drug interaction."
        ),
        "context": [
            ("Patient", "Susan Park, 71 (fictional)"),
            ("New Rx", "Ibuprofen 600 mg — twice daily as needed"),
            ("Profile", "Warfarin dispensed 2 weeks ago"),
            ("System", "Major interaction (DUR) alert"),
        ],
        "options": [
            "Dispense the ibuprofen and verbally remind the patient to be careful.",
            "Ignore the warning since DUR alerts fire on many prescriptions.",
            "Alert the pharmacist to review the bleeding-risk interaction with the prescriber.",
            "Cancel the prescription unilaterally and tell the patient it was unsafe.",
        ],
        "best_index": 2,
        "explanation": (
            "Ibuprofen plus warfarin significantly raises bleeding risk (NSAID plus "
            "anticoagulant). Major DUR alerts require pharmacist review. The "
            "pharmacist may recommend an alternative (commonly acetaminophen), "
            "confirm the prescriber is aware of both medications, or counsel the "
            "patient on signs of bleeding. Technicians escalate alerts but do not "
            "cancel prescriptions on their own authority."
        ),
        "escalation": (
            "Major DUR alerts always go to the pharmacist, who decides whether to "
            "suggest an alternative, confirm the prescriber is aware, or counsel the "
            "patient. Technicians escalate the alert and never cancel a prescription "
            "on their own."
        ),
    },
    {
        "id": "insurance_rejection",
        "title": "Insurance Rejection",
        "situation": (
            "A claim for atorvastatin 20 mg returns from insurance with rejection "
            "code 75 (Prior Authorization Required). The fictional patient is at the "
            "counter waiting to pick up."
        ),
        "context": [
            ("Patient", "Tom Walsh, 54 (fictional)"),
            ("Claim", "Atorvastatin 20 mg"),
            ("Rejection", "Code 75 — Prior Authorization required"),
            ("Status", "Patient waiting at the counter"),
        ],
        "options": [
            "Tell the patient the prescription is denied and to come back later.",
            "Process it as cash and quote the full retail price without other options.",
            "Inform the patient of the PA requirement, offer to start the PA with the prescriber, and explain expected timing.",
            "Override the rejection in the pharmacy software.",
        ],
        "best_index": 2,
        "explanation": (
            "Prior authorization rejections are common for non-preferred drugs. The "
            "standard workflow is to inform the patient of the PA requirement, "
            "contact the prescriber's office to initiate the PA (typically 24 to 72 "
            "hours), and offer alternatives such as a partial supply to bridge the "
            "wait, a generic substitution if available, or a formulary alternative. "
            "Do not dismiss the patient or default to cash pricing without offering "
            "the PA pathway first."
        ),
        "escalation": (
            "Loop in the pharmacist to start the prior authorization with the "
            "prescriber and to consider a clinical alternative or bridge supply. "
            "Technicians can explain the PA process and timing but cannot override a "
            "plan rejection."
        ),
    },
    {
        "id": "missing_prescriber_info",
        "title": "Missing Rx Information",
        "situation": (
            "A written fictional prescription for tramadol 50 mg tablet (a Schedule IV "
            "controlled substance) is dropped off. The drug, strength, quantity, and "
            "directions are all clear, but the prescriber's DEA number is missing, and "
            "it is required to process a controlled substance."
        ),
        "context": [
            ("Patient", "Grace Miller, 39 (fictional)"),
            ("Rx", "Tramadol 50 mg tablet — Schedule IV"),
            ("Missing", "Prescriber DEA number"),
            ("Other fields", "Drug, strength, quantity, directions clear"),
        ],
        "options": [
            "Process it anyway since the rest of the prescription is complete.",
            "Copy a DEA number from another prescriber already on file.",
            "Hold the prescription and have the prescriber's office provide the missing DEA number for the pharmacist to verify.",
            "Tell the patient the prescription is invalid and discard it.",
        ],
        "best_index": 2,
        "explanation": (
            "Controlled substance prescriptions require complete prescriber "
            "information, including a valid DEA number. Missing required fields "
            "cannot be filled in or guessed by pharmacy staff. The correct step is to "
            "contact the prescriber's office for the missing detail; the pharmacist "
            "verifies the DEA number and confirms the prescription is valid before "
            "dispensing. The prescription is held pending clarification, not "
            "discarded."
        ),
        "escalation": (
            "Any missing or invalid required field — especially a DEA number on a "
            "controlled substance — goes to the pharmacist, who confirms the "
            "corrected information and whether the prescription can be filled. "
            "Technicians collect the missing detail but never supply or assume it."
        ),
    },
    {
        "id": "daw_substitution",
        "title": "Brand / Generic (DAW)",
        "situation": (
            "A fictional prescription is written for the brand Synthroid 100 mcg with "
            "no DAW code marked. The patient says their doctor told them to take the "
            "brand and they do not want the generic levothyroxine."
        ),
        "context": [
            ("Patient", "Linda Hayes, 63 (fictional)"),
            ("Rx", "Synthroid 100 mcg (brand) — no DAW marked"),
            ("Patient request", "Wants brand, not generic levothyroxine"),
            ("Question", "Which DAW code applies?"),
        ],
        "options": [
            "Substitute the generic anyway since no DAW was marked.",
            "Enter DAW 1 (brand medically necessary) on your own since the patient wants brand.",
            "Confirm the patient's brand request, dispense the brand, and enter DAW 2 (patient requested brand), bringing substitution questions to the pharmacist.",
            "Refuse to fill until the prescriber sends a brand-only prescription.",
        ],
        "best_index": 2,
        "explanation": (
            "When no DAW is marked, generic substitution is generally allowed, but a "
            "patient may request the brand. A patient-requested brand is recorded as "
            "DAW 2 — not DAW 1, which means the prescriber documented brand medically "
            "necessary. Technicians do not assign DAW 1 on their own. Confirm the "
            "request, dispense the brand with DAW 2, and bring substitution or cost "
            "questions to the pharmacist. A new prescription is not required just to "
            "honor a brand request."
        ),
        "escalation": (
            "Bring DAW and substitution questions to the pharmacist, especially for "
            "narrow-therapeutic-index drugs like levothyroxine where brand and "
            "generic consistency matters. Technicians enter the DAW that matches what "
            "actually happened; the pharmacist confirms any brand-medically-necessary "
            "(DAW 1) coding."
        ),
    },
    {
        "id": "pickup_counseling",
        "title": "Pickup & Counseling",
        "situation": (
            "A fictional patient is picking up a first-fill prescription for a new "
            "albuterol inhaler. At the register they ask how to use the inhaler "
            "correctly and whether it is safe with their other medications."
        ),
        "context": [
            ("Patient", "David Cho, 28 (fictional)"),
            ("Pickup", "New albuterol inhaler (first fill)"),
            ("Patient asks", "How to use it + drug interactions"),
            ("Requirement", "Counseling offer on new prescriptions"),
        ],
        "options": [
            "Explain the inhaler technique and interactions yourself to save the pharmacist time.",
            "Tell the patient to read the printed leaflet and figure it out at home.",
            "Offer pharmacist counseling and hand the patient off to the pharmacist for the clinical questions.",
            "Tell the patient the pharmacy cannot answer questions.",
        ],
        "best_index": 2,
        "explanation": (
            "How to use a medication, side effects, and drug interactions are "
            "clinical questions for the pharmacist, and an offer to counsel is "
            "required on new prescriptions. The technician completes the sale and "
            "hands off the clinical questions. Technicians can confirm name, address, "
            "and pickup details but do not provide drug-use or interaction advice "
            "themselves."
        ),
        "escalation": (
            "Any question about how to use a medication, side effects, or "
            "interactions is a pharmacist counseling task. Offer the counseling and "
            "route the clinical questions to the pharmacist rather than answering "
            "them yourself."
        ),
    },
]


# =====================================================================
# Custom CSS - pharmacy workstation look
# =====================================================================

CUSTOM_CSS = """
<style>
/* ---------- Hide Streamlit chrome ---------- */
[data-testid="stHeader"]            { display: none; }
[data-testid="stSidebar"]           { display: none; }
[data-testid="collapsedControl"]    { display: none; }
[data-testid="stToolbar"]           { display: none; }
[data-testid="stDeployButton"]      { display: none; }
#MainMenu                           { display: none; }
footer                              { display: none; }

/* ---------- Force light palette ----------
   Lock color-scheme to light so Chrome's Auto Dark Mode for Web
   Contents (enabled by default in some recent Chrome incognito
   profiles) cannot invert backgrounds, swallow container borders,
   or render disabled-input text the same color as its background.
   This is the root cause of the symptom where the app looked
   different in incognito vs the owner browser. */
:root                                { color-scheme: light; }
html, body, .stApp                   { color-scheme: light; }

/* ---------- Page baseline ---------- */
.stApp {
    background-color: #f6f7f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
}

.block-container {
    padding-top: 1.25rem;
    padding-bottom: 2rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    max-width: 1400px;
}

[data-testid="stHorizontalBlock"] { gap: 14px; }
.stMarkdown p { margin-bottom: 0.25rem; }

/* ---------- Header bar ---------- */
.app-header {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px 22px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.app-title-block .app-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.68rem;
    font-weight: 700;
    color: #0f766e;
    margin-bottom: 5px;
}

.app-title-block h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    margin: 0;
    line-height: 1.15;
    letter-spacing: -0.02em;
}

.app-title-block .subtitle {
    font-size: 0.84rem;
    color: #6b7280;
    margin-top: 4px;
}

.stat-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.chip {
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 999px;
    padding: 5px 13px;
    font-size: 0.78rem;
    color: #4b5563;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    line-height: 1.4;
}

.chip-label { color: #6b7280; }
.chip-value { font-weight: 700; color: #0f766e; }
.chip.missed .chip-value         { color: #b45309; }
.chip.missed.empty .chip-value   { color: #4b5563; }
.chip.accuracy-low .chip-value   { color: #b91c1c; }

/* ---------- Generic card (HTML-only) ---------- */
.section-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px 22px;
    margin-bottom: 12px;
}

.section-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.7rem;
    font-weight: 700;
    color: #6b7280;
    margin-bottom: 10px;
}

/* ---------- Prescription card ---------- */
.rx-header-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid #f3f4f6;
    padding-bottom: 10px;
    margin-bottom: 12px;
}

.rx-header-row .section-label { margin-bottom: 0; }

.rx-meta { font-size: 0.78rem; color: #6b7280; }
.rx-meta .meta-value { color: #1f2937; font-weight: 500; margin-left: 4px; }

.rx-drug {
    font-size: 1.18rem;
    font-weight: 700;
    color: #111827;
    margin: 0;
    letter-spacing: -0.01em;
}

/* Subtle zone labels that make the card read like a structured source
   document: Medication / Directions / Dispensing details. Each label's
   top hairline doubles as the divider between zones. */
.rx-group-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 14px 0 8px 0;
    padding-top: 12px;
    border-top: 1px solid #f3f4f6;
}

.rx-group-label.first {
    margin-top: 2px;
    padding-top: 0;
    border-top: none;
}

.rx-sig-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 2px;
    flex-wrap: wrap;
}

.rx-mini-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.rx-sig {
    font-family: "SF Mono", Menlo, Consolas, "Courier New", monospace;
    font-size: 0.92rem;
    color: #0f766e;
    background: #ecfdf5;
    padding: 5px 12px;
    border-radius: 4px;
    border: 1px solid #d1fae5;
    display: inline-block;
}

/* Dispensing details strip: three connected fields divided by hairlines
   so Disp / Refills / DAW scan like a real Rx detail row. */
.rx-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
}

.rx-tag {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 0 22px;
    min-width: 84px;
}

.rx-tag:first-child { padding-left: 0; }
.rx-tag + .rx-tag { border-left: 1px solid #f3f4f6; }

.rx-tag-value { font-size: 0.98rem; font-weight: 600; color: #111827; }
.rx-tag-value.muted { color: #9ca3af; font-weight: 500; }

/* ---------- DUR / Safety Review ---------- */
.safety-warning-list {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}

.safety-callout {
    border: 1px solid #e5e7eb;
    border-left-width: 4px;
    border-radius: 6px;
    padding: 10px 14px;
    background: #f9fafb;
}

.safety-callout-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 5px;
    flex-wrap: wrap;
}

.safety-callout-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #111827;
}

.safety-callout-badge {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border-radius: 999px;
    padding: 3px 9px;
    background: white;
    border: 1px solid currentColor;
}

.safety-callout-body {
    font-size: 0.86rem;
    color: #374151;
    line-height: 1.55;
}

.safety-callout.safety {
    background: #fffbeb;
    border-color: #fbbf24;
}

.safety-callout.safety .safety-callout-badge {
    color: #92400e;
}

.safety-callout.insurance {
    background: #f0f9ff;
    border-color: #38bdf8;
}

.safety-callout.insurance .safety-callout-badge {
    color: #0369a1;
}

.safety-callout.drug {
    background: #f0fdf4;
    border-color: #34d399;
}

.safety-callout.drug .safety-callout-badge {
    color: #047857;
}

.safety-callout.training {
    background: #f5f3ff;
    border-color: #a78bfa;
}

.safety-callout.training .safety-callout-badge {
    color: #6d28d9;
}

.safety-empty-state {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #34d399;
    border-radius: 6px;
    padding: 11px 14px;
    font-size: 0.88rem;
    color: #166534;
    line-height: 1.5;
}

/* ---------- Patient / Prescriber cards ---------- */
.data-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 6px;
    margin-top: 2px;
}

.data-row {
    display: flex;
    font-size: 0.86rem;
    line-height: 1.5;
}

.data-row .label {
    color: #6b7280;
    min-width: 90px;
    font-weight: 500;
}

.data-row .value { color: #111827; }

/* ---------- Entry form (Streamlit st.container) ---------- */
/* The bordered wrapper around st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 6px 22px 14px 22px !important;
    margin-bottom: 12px !important;
}

/* Small form-group label inside the entry container */
.form-group-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.7rem;
    font-weight: 700;
    color: #6b7280;
    margin: 12px 0 -2px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #f3f4f6;
}

/* First form group label gets less top margin */
.form-group-label.first { margin-top: 12px; }

/* ---------- Widget styling ---------- */
.stTextInput input,
.stTextArea textarea {
    border-radius: 6px;
    border-color: #d1d5db;
    font-size: 0.9rem;
    background: #fafbfc;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #0f766e !important;
    box-shadow: 0 0 0 1px #0f766e !important;
}

/* Force placeholder visibility regardless of browser auto-dark-mode or
   other default rendering quirks. Without this, Chrome's experimental
   "Auto Dark Mode for Web Contents" (enabled by default in some recent
   Chrome incognito sessions) renders the default light-gray placeholders
   as essentially invisible. */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #9ca3af !important;
    opacity: 1 !important;
}

.stTextInput label,
.stTextArea label {
    font-size: 0.8rem !important;
    color: #374151 !important;
    font-weight: 500 !important;
    padding-bottom: 2px !important;
}

/* ---------- Fake inputs for example mode ----------
   Pure HTML mock-ups styled to look IDENTICAL to st.text_input and
   st.text_area. Used when example_mode is True so the canonical
   answer values render as static markup that no browser color mode,
   no Chrome auto-dark inversion, and no Streamlit deployment quirk
   can hide. All colors are explicit and !important-pinned so nothing
   downstream can override them. */
.fake-input-wrapper {
    margin-bottom: 4px;
    color-scheme: light;
}
.fake-input-label {
    font-size: 0.8rem !important;
    color: #374151 !important;
    font-weight: 500 !important;
    padding-bottom: 2px;
    line-height: 1.4;
}
.fake-input,
.fake-textarea {
    border: 1px solid #d1d5db !important;
    border-radius: 6px;
    background: #fafbfc !important;
    color: #0f172a !important;
    font-size: 0.9rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    box-sizing: border-box;
    line-height: 1.5;
    word-break: break-word;
}
.fake-input {
    padding: 7px 12px;
    min-height: 38px;
    display: flex;
    align-items: center;
}
.fake-textarea {
    padding: 8px 12px;
    min-height: 110px;
    white-space: pre-wrap;
}

/* ---------- Buttons ---------- */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.88rem;
    padding: 7px 20px;
    transition: all 0.12s ease;
    min-height: 38px;
}

.stButton > button[kind="primary"] {
    background-color: #0f766e;
    border-color: #0f766e;
    color: white;
}

.stButton > button[kind="primary"]:hover:not(:disabled) {
    background-color: #115e59;
    border-color: #115e59;
}

.stButton > button[kind="secondary"] {
    background-color: white;
    border-color: #d1d5db;
    color: #374151;
}

.stButton > button[kind="secondary"]:hover:not(:disabled) {
    background-color: #f9fafb;
    border-color: #9ca3af;
    color: #111827;
}

.stButton > button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

/* ---------- See Example HTML link ----------
   This is a plain HTML <a> tag, not a Streamlit button, because URL-based
   navigation is reliable across all session types on Streamlit Cloud
   (authenticated owner, anonymous visitor, incognito). It's styled to
   visually match the primary green button. */
.see-example-link {
    display: inline-block;
    background-color: #0f766e;
    color: white !important;
    border: 1px solid #0f766e;
    border-radius: 6px;
    padding: 7px 20px;
    font-weight: 500;
    font-size: 0.88rem;
    line-height: 1.5;
    text-align: center;
    text-decoration: none !important;
    width: 100%;
    box-sizing: border-box;
    transition: background-color 0.12s ease, border-color 0.12s ease;
    min-height: 38px;
    cursor: pointer;
    font-family: inherit;
}

.see-example-link:hover {
    background-color: #115e59;
    border-color: #115e59;
    color: white !important;
    text-decoration: none !important;
}

.see-example-link.see-example-disabled,
span.see-example-link {
    opacity: 0.45;
    cursor: not-allowed;
    pointer-events: none;
}

/* ---------- Feedback panel ---------- */
.feedback-summary {
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 12px;
    font-size: 0.88rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 10px;
}

.feedback-summary.all-correct {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
}

.feedback-summary.partial {
    background: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
}

.feedback-summary .badge {
    background: white;
    border: 1px solid currentColor;
    border-radius: 4px;
    padding: 1px 8px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* ---------- Feedback report summary (score + performance message) ---------- */
.report-summary {
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 14px;
    border: 1px solid #e5e7eb;
}

.report-score {
    font-size: 0.98rem;
    font-weight: 600;
    color: #111827;
    display: flex;
    align-items: center;
    gap: 10px;
}

.report-badge {
    background: white;
    border: 1px solid currentColor;
    border-radius: 4px;
    padding: 1px 9px;
    font-size: 0.82rem;
    font-weight: 700;
}

.report-perf {
    font-size: 0.86rem;
    margin-top: 5px;
    font-weight: 500;
}

.report-summary.high {
    background: #ecfdf5;
    border-color: #a7f3d0;
}
.report-summary.high .report-score,
.report-summary.high .report-badge,
.report-summary.high .report-perf { color: #047857; }

.report-summary.medium {
    background: #fffbeb;
    border-color: #fde68a;
}
.report-summary.medium .report-score,
.report-summary.medium .report-badge,
.report-summary.medium .report-perf { color: #92400e; }

.report-summary.low {
    background: #fef2f2;
    border-color: #fecaca;
}
.report-summary.low .report-score,
.report-summary.low .report-badge,
.report-summary.low .report-perf { color: #b91c1c; }

/* SIG explanation is the most detailed; give it a touch more breathing room */
.feedback-item.sig-field .feedback-explanation { margin-top: 8px; }

.feedback-item {
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 8px;
    border: 1px solid #e5e7eb;
    background: #fafbfc;
    font-size: 0.86rem;
}

.feedback-item .field-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.feedback-item .field-name {
    font-weight: 600;
    color: #111827;
}

.feedback-item .field-status {
    font-size: 0.74rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 8px;
    border-radius: 4px;
}

.feedback-item.correct {
    border-color: #d1fae5;
    background: #f0fdf4;
}
.feedback-item.correct .field-status {
    color: #047857;
    background: #d1fae5;
}

.feedback-item.incorrect {
    border-color: #fecaca;
    background: #fef2f2;
}
.feedback-item.incorrect .field-status {
    color: #b91c1c;
    background: #fee2e2;
}

.feedback-detail {
    margin-top: 8px;
    font-size: 0.82rem;
    color: #374151;
}

.feedback-detail .answer-box {
    display: inline-block;
    padding: 1px 7px;
    border-radius: 3px;
    background: white;
    border: 1px solid #e5e7eb;
    font-family: "SF Mono", Menlo, Consolas, "Courier New", monospace;
    font-size: 0.78rem;
    margin: 0 3px;
    color: #1f2937;
}

.feedback-explanation {
    margin-top: 6px;
    font-size: 0.8rem;
    color: #4b5563;
    line-height: 1.5;
}

/* ---------- Missed fields panel ---------- */
.missed-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.missed-row {
    display: flex;
    gap: 10px;
    font-size: 0.82rem;
    color: #374151;
    padding: 4px 0;
    border-bottom: 1px dashed #f3f4f6;
}

.missed-row:last-child { border-bottom: none; }

.missed-row .case-id {
    color: #9ca3af;
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.78rem;
    min-width: 60px;
}

.missed-row .field {
    font-weight: 600;
    color: #111827;
    min-width: 110px;
}

.missed-row .expected {
    color: #4b5563;
}

/* ---------- Footer ---------- */
.footer-row {
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid #e5e7eb;
}

/* ---------- Label Preview ---------- */
.label-warning {
    background: #fffbeb;
    border: 1px solid #fde68a;
    color: #92400e;
    padding: 8px 14px;
    border-radius: 6px;
    margin-bottom: 14px;
    font-size: 0.82rem;
    text-align: center;
    font-weight: 500;
}

.label-warning.corrections {
    background: #fef3c7;
    border-color: #f59e0b;
}

.label-paper {
    background: #fefefe;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 22px 28px;
    max-width: 560px;
    margin: 0 auto;
    color: #0f172a;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.label-pharmacy-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 6px;
    margin-bottom: 6px;
}

.label-pharmacy-name {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}

.label-rx-num {
    font-size: 0.82rem;
    font-family: "SF Mono", Menlo, Consolas, "Courier New", monospace;
    color: #1f2937;
}

.label-pharmacy-addr {
    font-size: 0.76rem;
    color: #4b5563;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px dashed #cbd5e1;
}

.label-patient-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 16px;
    font-size: 0.95rem;
}

.label-patient-row .pt-name {
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    color: #0f172a;
}

.label-patient-row .fill-date {
    font-size: 0.8rem;
    color: #4b5563;
}

.label-drug-line {
    font-size: 1.15rem;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 12px;
    line-height: 1.3;
}

.label-sig-block {
    font-size: 1.08rem;
    line-height: 1.6;
    text-transform: uppercase;
    padding: 12px 0;
    border-top: 1px dashed #cbd5e1;
    border-bottom: 1px dashed #cbd5e1;
    margin-bottom: 14px;
    font-weight: 500;
}

.label-fill-row {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    flex-wrap: wrap;
    font-size: 0.92rem;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px dashed #cbd5e1;
}

.label-fill-row .fg-label {
    color: #6b7280;
    text-transform: uppercase;
    font-size: 0.74rem;
    letter-spacing: 0.05em;
    margin-right: 5px;
}

.label-fill-row .fg-value {
    font-weight: 600;
    color: #0f172a;
}

.label-prescriber-row {
    font-size: 0.9rem;
    margin-bottom: 4px;
}

.label-prescriber-row .pr-label {
    color: #6b7280;
    text-transform: uppercase;
    font-size: 0.74rem;
    letter-spacing: 0.05em;
    margin-right: 6px;
}

.label-prescriber-row .pr-name {
    font-weight: 600;
    text-transform: uppercase;
    color: #0f172a;
}

.label-footer-stamp {
    margin-top: 16px;
    padding-top: 12px;
    border-top: 2px solid #0f172a;
    text-align: center;
    font-size: 0.74rem;
    color: #4b5563;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 600;
}

.correction-mark {
    color: #b45309;
    font-weight: 700;
    margin-left: 2px;
}

/* ---------- Label locked (gated) state ---------- */
.label-locked {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 18px 22px;
    text-align: center;
}

.label-locked .lock-title {
    font-weight: 600;
    color: #92400e;
    font-size: 0.95rem;
    margin-bottom: 6px;
}

.label-locked .lock-body {
    color: #78350f;
    font-size: 0.86rem;
    line-height: 1.55;
    max-width: 480px;
    margin: 0 auto;
}

/* ---------- Workflow hint ---------- */
.workflow-hint {
    font-size: 0.84rem;
    color: #6b7280;
    margin: -4px 0 14px 4px;
    line-height: 1.5;
}

/* ---------- Compact success card (all-correct path) ---------- */
.success-card {
    background: #ecfdf5 !important;
    border-color: #a7f3d0 !important;
}

.success-card .success-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #047857;
    line-height: 1.3;
}

.success-card .success-subtitle {
    font-size: 0.88rem;
    color: #065f46;
    margin-top: 4px;
}

/* ---------- Print page mockup ---------- */
.print-page-mockup {
    background: white;
    border: 1px solid #d1d5db;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    padding: 36px 28px;
    border-radius: 4px;
    margin: 0 auto;
    max-width: 620px;
}

/* ---------- See Example button (green) ---------- */
/* The .see-example-anchor div sits in the same column as the button.
   :has() finds the element-container containing the anchor, and the
   adjacent sibling combinator targets the button's element-container. */
.element-container:has(.see-example-anchor) + .element-container .stButton > button,
[data-testid="stElementContainer"]:has(.see-example-anchor) + [data-testid="stElementContainer"] .stButton > button {
    background-color: #047857 !important;
    border-color: #047857 !important;
    color: white !important;
}

.element-container:has(.see-example-anchor) + .element-container .stButton > button:hover:not(:disabled),
[data-testid="stElementContainer"]:has(.see-example-anchor) + [data-testid="stElementContainer"] .stButton > button:hover:not(:disabled) {
    background-color: #065f46 !important;
    border-color: #065f46 !important;
}

.element-container:has(.see-example-anchor) + .element-container .stButton > button:disabled,
[data-testid="stElementContainer"]:has(.see-example-anchor) + [data-testid="stElementContainer"] .stButton > button:disabled {
    background-color: #f0fdf4 !important;
    border-color: #d1fae5 !important;
    color: #6b7280 !important;
    opacity: 1 !important;
}

/* ---------- Success card variant for example mode (light blue) ---------- */
.success-card.example-mode {
    background: #f0f9ff !important;
    border-color: #bae6fd !important;
}

.success-card.example-mode .success-title {
    color: #0369a1;
}

.success-card.example-mode .success-subtitle {
    color: #075985;
}

/* ---------- Card border anchor (forces visible container borders) ----------
   The screenshot from incognito showed st.container(border=True) rendering
   without a visible border because Streamlit 1.57's container DOM differs
   from the version my old [data-testid="stVerticalBlockBorderWrapper"]
   selector targeted. This rule is version-agnostic:

   1. Each bordered container has a <div class="card-border-anchor"></div>
      inserted as its first child (see render_prescription_card,
      render_safety_warnings, render_entry_form, render_drug_knowledge_section,
      render_workflow_scenarios_section).
   2. The :has() selector finds every stVerticalBlock that contains the
      anchor as a descendant.
   3. The :not(:has(...)) clause excludes outer/parent stVerticalBlocks
      that also happen to contain the anchor via nesting, so the rule
      lands ONLY on the innermost block (the container we want bordered).
   4. The marker itself is hidden so it does not take up vertical space. */
[data-testid="stVerticalBlock"]:has(.card-border-anchor):not(:has([data-testid="stVerticalBlock"] .card-border-anchor)) {
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    padding: 14px 18px !important;
    margin-bottom: 12px !important;
}

.card-border-anchor {
    display: none !important;
}

/* Fallback for older Streamlit versions that still use
   stVerticalBlockBorderWrapper for the bordered container. Harmless
   on newer versions where this selector simply does not match. */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color-scheme: light;
}

/* ---------- Label preview action area (button + hint text) ---------- */
.print-hint-text {
    font-size: 0.84rem;
    color: #4b5563;
    line-height: 1.5;
}

.print-hint-text strong {
    color: #0f766e;
    font-family: "SF Mono", Menlo, Consolas, "Courier New", monospace;
    font-weight: 600;
}

/* ---------- SIG decoder ---------- */
.sig-decoder {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 18px;
    margin: 4px 0 14px 0;
}

.sig-decoder-title {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.68rem;
    font-weight: 700;
    color: #6b7280;
    margin-bottom: 8px;
}

.sig-decoder-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.sig-pair {
    display: flex;
    align-items: baseline;
    gap: 6px;
    font-size: 0.86rem;
    padding: 3px 0;
}

.sig-abbr {
    font-family: "SF Mono", Menlo, Consolas, "Courier New", monospace;
    font-weight: 700;
    color: #0f766e;
    min-width: 80px;
}

.sig-eq {
    color: #9ca3af;
    font-weight: 400;
}

.sig-meaning {
    color: #374151;
}

/* ---------- @media print: print just the label-print-source area ---------- */
@media print {
    body * {
        visibility: hidden !important;
    }
    .label-print-source, .label-print-source * {
        visibility: visible !important;
    }
    .label-print-source {
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        width: 100% !important;
        padding: 24px !important;
        background: white !important;
        border: none !important;
        box-shadow: none !important;
    }
    .label-print-source .section-label {
        display: none !important;
    }
    .label-print-source .print-page-mockup {
        box-shadow: none !important;
        border: none !important;
        padding: 0 !important;
        max-width: none !important;
        background: white !important;
    }
    .label-print-source .label-paper {
        max-width: 600px !important;
        margin: 0 auto !important;
        box-shadow: none !important;
        border: 1px solid #000 !important;
    }
    .stApp {
        background: white !important;
    }
}
/* ---------- Top navigation (st.radio horizontal) ---------- */
.top-nav-divider {
    border-bottom: 1px solid #e5e7eb;
    margin: 4px 0 18px 0;
}

/* ---------- Training modules header (frames the nav as a curriculum) ---------- */
.nav-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin: 2px 0 10px 0;
}

.nav-header .section-label {
    margin-bottom: 0;
}

.nav-header-hint {
    font-size: 0.8rem;
    color: #6b7280;
    line-height: 1.4;
}

/* ---------- Top navigation cards (3 large clickable buttons) ---------- */

/* Hidden CSS hooks; one immediately precedes each nav button. */
.nav-marker {
    display: none;
}

/* Base styling for all nav-card buttons (active or inactive) */
[data-testid="stElementContainer"]:has(.nav-marker) + [data-testid="stElementContainer"] .stButton > button,
.element-container:has(.nav-marker) + .element-container .stButton > button {
    min-height: 88px !important;
    padding: 16px 18px !important;
    border-radius: 10px !important;
    font-weight: 400 !important;
    text-align: center !important;
    line-height: 1.4 !important;
    white-space: normal !important;
    transition: border-color 0.15s, color 0.15s, background 0.15s !important;
}

/* Title (the **bold** markdown segment renders as <strong>) */
[data-testid="stElementContainer"]:has(.nav-marker) + [data-testid="stElementContainer"] .stButton > button strong,
.element-container:has(.nav-marker) + .element-container .stButton > button strong {
    font-size: 1.02rem !important;
    font-weight: 700 !important;
    line-height: 1.6 !important;
    letter-spacing: 0.01em !important;
}

/* Description (rest of the markdown <p> after the <br>) */
[data-testid="stElementContainer"]:has(.nav-marker) + [data-testid="stElementContainer"] .stButton > button p,
.element-container:has(.nav-marker) + .element-container .stButton > button p {
    font-size: 0.82rem !important;
    line-height: 1.45 !important;
    margin: 0 !important;
}

/* Active state: solid green background, white title, slightly muted description */
[data-testid="stElementContainer"]:has(.nav-marker.nav-active) + [data-testid="stElementContainer"] .stButton > button,
.element-container:has(.nav-marker.nav-active) + .element-container .stButton > button {
    background: #0f766e !important;
    color: rgba(255, 255, 255, 0.92) !important;
    border: 1px solid #0f766e !important;
}
[data-testid="stElementContainer"]:has(.nav-marker.nav-active) + [data-testid="stElementContainer"] .stButton > button strong,
.element-container:has(.nav-marker.nav-active) + .element-container .stButton > button strong {
    color: white !important;
}

/* Inactive state: white background, subtle border, dark title, muted description */
[data-testid="stElementContainer"]:has(.nav-marker.nav-inactive) + [data-testid="stElementContainer"] .stButton > button,
.element-container:has(.nav-marker.nav-inactive) + .element-container .stButton > button {
    background: white !important;
    color: #6b7280 !important;
    border: 1px solid #d1d5db !important;
}
[data-testid="stElementContainer"]:has(.nav-marker.nav-inactive) + [data-testid="stElementContainer"] .stButton > button strong,
.element-container:has(.nav-marker.nav-inactive) + .element-container .stButton > button strong {
    color: #1f2937 !important;
}

/* Inactive hover: subtle teal hint to signal clickability */
[data-testid="stElementContainer"]:has(.nav-marker.nav-inactive) + [data-testid="stElementContainer"] .stButton > button:hover,
.element-container:has(.nav-marker.nav-inactive) + .element-container .stButton > button:hover {
    background: #f9fafb !important;
    border-color: #0f766e !important;
}
[data-testid="stElementContainer"]:has(.nav-marker.nav-inactive) + [data-testid="stElementContainer"] .stButton > button:hover strong,
.element-container:has(.nav-marker.nav-inactive) + .element-container .stButton > button:hover strong {
    color: #0f766e !important;
}

/* ---------- Training disclaimer banner ---------- */
.info-disclaimer {
    background: #f0f9ff;
    border-left: 3px solid #0369a1;
    padding: 8px 14px;
    margin: 0 0 16px 0;
    font-size: 0.84rem;
    color: #075985;
    border-radius: 4px;
    line-height: 1.5;
}

.info-disclaimer strong {
    color: #0c4a6e;
}

/* ---------- Drug Knowledge section ---------- */
.drug-info-section-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.7rem;
    font-weight: 700;
    color: #6b7280;
    margin-top: 14px;
    margin-bottom: 6px;
}

.drug-info-body {
    font-size: 0.92rem;
    color: #374151;
    line-height: 1.55;
}

.drug-info-pill {
    display: inline-block;
    background: #f3f4f6;
    color: #374151;
    padding: 3px 11px;
    border-radius: 12px;
    font-size: 0.82rem;
    margin: 2px 6px 2px 0;
    border: 1px solid #e5e7eb;
}

.lasa-warning {
    background: #fef3c7;
    border-left: 3px solid #f59e0b;
    padding: 8px 14px;
    margin-top: 6px;
    font-size: 0.88rem;
    color: #78350f;
    border-radius: 4px;
    line-height: 1.5;
}

/* ---------- Drug Knowledge study cards ---------- */
.drug-category-bar {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    flex-wrap: wrap;
    margin: 16px 0 4px 0;
}

.drug-category-title {
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
}

.drug-category-count {
    font-size: 0.8rem;
    color: #6b7280;
    font-weight: 500;
}

.drug-category-blurb {
    font-size: 0.86rem;
    color: #4b5563;
    line-height: 1.5;
    margin: 0 0 12px 0;
}

.drug-study-card { margin-bottom: 12px; }

.drug-study-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 4px;
}

.drug-study-generic {
    font-size: 1.05rem;
    font-weight: 700;
    color: #111827;
}

.drug-study-brand {
    font-size: 0.8rem;
    color: #6b7280;
    font-weight: 500;
}

.drug-study-class {
    font-size: 0.84rem;
    color: #4b5563;
    font-style: italic;
    line-height: 1.45;
    margin-bottom: 4px;
}

.drug-study-pills { margin-top: 2px; }

/* ---------- Workflow Scenarios section ---------- */
.scenario-situation {
    font-size: 0.94rem;
    color: #1f2937;
    line-height: 1.55;
    background: #f9fafb;
    border-left: 3px solid #0f766e;
    padding: 12px 16px;
    margin: 10px 0 6px 0;
    border-radius: 4px;
}

.scenario-feedback-correct {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 6px;
    padding: 14px 18px;
    margin-top: 16px;
}

.scenario-feedback-incorrect {
    background: #fef3c7;
    border: 1px solid #fbbf24;
    border-radius: 6px;
    padding: 14px 18px;
    margin-top: 16px;
}

.scenario-feedback-title {
    font-weight: 700;
    margin-bottom: 6px;
    font-size: 0.95rem;
}

.scenario-feedback-correct .scenario-feedback-title {
    color: #047857;
}

.scenario-feedback-incorrect .scenario-feedback-title {
    color: #92400e;
}

.scenario-feedback-body {
    font-size: 0.9rem;
    line-height: 1.6;
    color: #374151;
}

.scenario-user-pick {
    font-size: 0.82rem;
    color: #6b7280;
    margin-top: 10px;
    font-style: italic;
}

/* ---------- Workflow Scenarios: case details + pharmacist escalation ---------- */
.scenario-context {
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 12px 0 4px 0;
}

.scenario-context-label {
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-size: 0.68rem;
    font-weight: 700;
    color: #6b7280;
    margin-bottom: 6px;
}

/* Purple = the existing "training note" tone; fitting for a scope-of-practice
   reminder. Distinct from the green/amber correct/incorrect feedback boxes. */
.scenario-escalation {
    background: #f5f3ff;
    border: 1px solid #ddd6fe;
    border-left: 3px solid #a78bfa;
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 12px;
    font-size: 0.86rem;
    color: #4b5563;
    line-height: 1.55;
}

.scenario-escalation .esc-label {
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.72rem;
    font-weight: 700;
    color: #6d28d9;
    margin-bottom: 4px;
}

/* ---------- Workflow Scenarios progress + score row ---------- */
.scenario-progress-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.88rem;
    color: #4b5563;
    padding: 8px 4px;
    margin: 10px 0 4px 0;
}

.scenario-progress-row .scen-progress-text {
    font-weight: 500;
}

.scenario-score {
    background: #f3f4f6;
    color: #374151;
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: 600;
    border: 1px solid #e5e7eb;
    font-size: 0.82rem;
}

</style>
"""


# =====================================================================
# State management
# =====================================================================

def init_state() -> None:
    """Initialize all session state on first run."""
    if "current_case" not in st.session_state:
        st.session_state.current_case = cases.get_random_case()
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "last_feedback" not in st.session_state:
        st.session_state.last_feedback = {}
    if "stats" not in st.session_state:
        st.session_state.stats = tracker.init_stats()
    if "review_queue" not in st.session_state:
        st.session_state.review_queue = tracker.init_review_queue()
    if "seen_case_ids" not in st.session_state:
        st.session_state.seen_case_ids = []
    if "cases_completed" not in st.session_state:
        st.session_state.cases_completed = 0
    if "label_revealed" not in st.session_state:
        st.session_state.label_revealed = False
    if "sig_help_open" not in st.session_state:
        st.session_state.sig_help_open = False
    if "example_mode" not in st.session_state:
        st.session_state.example_mode = False
    if "active_section" not in st.session_state:
        st.session_state.active_section = "Prescription Entry"
    if "scenario_id" not in st.session_state:
        st.session_state.scenario_id = SCENARIOS[0]["id"]
    if "scenario_submitted" not in st.session_state:
        st.session_state.scenario_submitted = False
    if "scenario_choice" not in st.session_state:
        st.session_state.scenario_choice = None
    if "drug_category" not in st.session_state:
        # Land on the category that contains the current Prescription Entry
        # case's drug so Drug Knowledge opens on something relevant. After
        # that, the category buttons drive it independently.
        current_drug = st.session_state.current_case["expected"]["drug_name"].lower().strip()
        st.session_state.drug_category = _category_for_drug(current_drug)
    if "scenario_attempted_ids" not in st.session_state:
        st.session_state.scenario_attempted_ids = set()
    if "scenario_correct_ids" not in st.session_state:
        st.session_state.scenario_correct_ids = set()


def advance_case() -> None:
    """Mark current case complete, load a new one, clear feedback and form.

    If the user is leaving example mode, the case is NOT counted toward
    cases_completed (example mode is demo, not practice).
    """
    current_id = st.session_state.current_case["case_id"]
    st.session_state.seen_case_ids.append(current_id)
    if not st.session_state.get("example_mode", False):
        st.session_state.cases_completed += 1
    st.session_state.current_case = cases.get_random_case(
        st.session_state.seen_case_ids
    )
    st.session_state.submitted = False
    st.session_state.last_feedback = {}
    st.session_state.label_revealed = False
    st.session_state.example_mode = False
    # Clear form widgets for the new case
    for key in WIDGET_KEYS:
        st.session_state.pop(key, None)


def try_again() -> None:
    """Return to editing the same case without advancing.

    If the user was in example mode, clear the form so they can type
    their own answer from blank inputs. Otherwise (Try Again after a
    real failed submission), keep their typed values so they can fix
    specific fields without retyping everything.
    """
    was_example = st.session_state.get("example_mode", False)
    st.session_state.submitted = False
    st.session_state.last_feedback = {}
    st.session_state.label_revealed = False
    st.session_state.example_mode = False
    if was_example:
        for key in WIDGET_KEYS:
            st.session_state.pop(key, None)


def reset_session() -> None:
    """Wipe all state and start a fresh session."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_state()


def handle_submission(user_answers: dict) -> None:
    """Run the checker, update stats, append misses to the missed-fields list."""
    case = st.session_state.current_case
    results = checker.check_all(user_answers, case["expected"], case.get("extras"))
    st.session_state.last_feedback = results
    st.session_state.submitted = True
    st.session_state.label_revealed = False  # gate resets on every submission
    st.session_state.example_mode = False    # real submission overrides demo
    tracker.record_results(st.session_state.stats, results)
    # Remove any prior misses from this case so Try Again does not pile up
    # duplicates. The latest attempt's misses are then appended below.
    queue = st.session_state.review_queue
    queue[:] = [item for item in queue if item["case_id"] != case["case_id"]]
    tracker.add_misses_to_review(queue, case["case_id"], results)


def overall_accuracy() -> tuple[int, int]:
    """Return (correct, total) across all attempted fields this session."""
    stats = st.session_state.stats
    correct = sum(s["correct"] for s in stats.values())
    total = sum(s["attempts"] for s in stats.values())
    return correct, total


def _strip_label(text: str) -> str:
    """For lines like 'Refills: 0' return '0'. If no colon, return text unchanged."""
    if ":" in text:
        return text.split(":", 1)[1].strip()
    return text.strip()


# =====================================================================
# SIG decoder: parse a shorthand SIG into (token, meaning) pairs
# =====================================================================

# Ordered list of (compiled_regex, meaning_function). Earlier patterns
# take precedence on overlap, so put longer / more specific patterns first.
SIG_DECODE_PATTERNS: list[tuple[re.Pattern, callable]] = [
    # Quantity + dosage form
    (re.compile(r'\b(\d+(?:\.\d+)?)\s+tab(?:s|let|lets)?\b', re.IGNORECASE),
     lambda m: f"{m.group(1)} tablet{'s' if float(m.group(1)) != 1 else ''}"),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s+cap(?:s|sule|sules)?\b', re.IGNORECASE),
     lambda m: f"{m.group(1)} capsule{'s' if float(m.group(1)) != 1 else ''}"),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s+gtt(?:s)?\b', re.IGNORECASE),
     lambda m: f"{m.group(1)} drop{'s' if float(m.group(1)) != 1 else ''}"),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s+puff(?:s)?\b', re.IGNORECASE),
     lambda m: f"{m.group(1)} puff{'s' if float(m.group(1)) != 1 else ''}"),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s+m[lL]\b'),
     lambda m: f"{m.group(1)} milliliters"),
    # Routes
    (re.compile(r'\bPO\b'), lambda m: "by mouth"),
    (re.compile(r'\bSL\b'), lambda m: "under the tongue"),
    (re.compile(r'\bIV\b'), lambda m: "intravenous"),
    (re.compile(r'\bIM\b'), lambda m: "intramuscular"),
    (re.compile(r'\bINH\b'), lambda m: "inhaled"),
    (re.compile(r'\bOU\b'), lambda m: "in both eyes"),
    (re.compile(r'\bOD\b'), lambda m: "in the right eye"),
    (re.compile(r'\bOS\b'), lambda m: "in the left eye"),
    (re.compile(r'\bAU\b'), lambda m: "in both ears"),
    (re.compile(r'\bAD\b'), lambda m: "in the right ear"),
    (re.compile(r'\bAS\b'), lambda m: "in the left ear"),
    (re.compile(r'\bTOP\b'), lambda m: "topically"),
    # Frequencies - more specific patterns first
    (re.compile(r'\bQ\s*(\d+)\s*H\b', re.IGNORECASE),
     lambda m: f"every {m.group(1)} hours"),
    (re.compile(r'\bQAM\b'), lambda m: "every morning"),
    (re.compile(r'\bQPM\b'), lambda m: "every evening"),
    (re.compile(r'\bQHS\b'), lambda m: "at bedtime"),
    (re.compile(r'\bQID\b'), lambda m: "four times daily"),
    (re.compile(r'\bTID\b'), lambda m: "three times daily"),
    (re.compile(r'\bBID\b'), lambda m: "twice daily"),
    (re.compile(r'\bQD\b'), lambda m: "once daily"),
    (re.compile(r'\bPRN\b'), lambda m: "as needed"),
    # Duration
    (re.compile(r'x\s+(\d+)\s+days?\b', re.IGNORECASE),
     lambda m: f"for {m.group(1)} day{'s' if int(m.group(1)) != 1 else ''}"),
    (re.compile(r'x\s+(\d+)\s+weeks?\b', re.IGNORECASE),
     lambda m: f"for {m.group(1)} week{'s' if int(m.group(1)) != 1 else ''}"),
]


def decode_sig(sig_shorthand: str) -> list[tuple[str, str]]:
    """Return [(matched_token, plain_english_meaning), ...] in order of appearance.

    Earlier patterns in SIG_DECODE_PATTERNS take precedence on overlapping
    matches, so a 'Q6H' is decoded once, not also as 'QID' / 'QD' etc.
    """
    matches: list[tuple[int, str, str]] = []
    used_spans: list[tuple[int, int]] = []
    for pattern, meaning_fn in SIG_DECODE_PATTERNS:
        for match in pattern.finditer(sig_shorthand):
            start, end = match.span()
            if any(s < end and start < e for s, e in used_spans):
                continue
            matches.append((start, match.group(0), meaning_fn(match)))
            used_spans.append((start, end))
    matches.sort(key=lambda mt: mt[0])
    return [(token, meaning) for _, token, meaning in matches]


# =====================================================================
# DUR / Safety Review helpers
# =====================================================================

SAFETY_META = {
    "allergy": ("Allergy warning", "⚠️ Safety warning", "safety"),
    "interaction": ("Drug interaction warning", "⚠️ Safety warning", "safety"),
    "duplicate": ("Duplicate therapy warning", "💊 Drug verification", "drug"),
    "refill": ("Refill review", "🧾 Insurance / refill issue", "insurance"),
    "lasa": ("LASA warning", "💊 Drug verification", "drug"),
    "high_alert": ("High-alert medication", "⚠️ Safety warning", "safety"),
    "clarification": ("Prescriber clarification needed", "🧠 Training note", "training"),
    "daw": ("DAW verification", "💊 Drug verification", "drug"),
    "training": ("Training note", "🧠 Training note", "training"),
}

HIGH_ALERT_DRUG_GROUPS = {
    "insulin": ("insulin",),
    "warfarin": ("warfarin", "coumadin", "jantoven"),
    "opioid": (
        "opioid",
        "codeine",
        "fentanyl",
        "hydrocodone",
        "hydromorphone",
        "morphine",
        "oxycodone",
        "tramadol",
    ),
    "methotrexate": ("methotrexate",),
    "digoxin": ("digoxin",),
    "enoxaparin": ("enoxaparin", "lovenox"),
}

ALLERGY_RELATED_TERMS = {
    "penicillin": (
        "amoxicillin",
        "amoxil",
        "ampicillin",
        "augmentin",
        "cephalexin",
        "cefazolin",
        "cef",
        "keflex",
        "penicillin",
    ),
    "sulfa": (
        "bactrim",
        "celecoxib",
        "furosemide",
        "hydrochlorothiazide",
        "sulfamethoxazole",
        "sulfasalazine",
        "trimethoprim-sulfamethoxazole",
    ),
    "aspirin": (
        "aspirin",
        "diclofenac",
        "ibuprofen",
        "ketorolac",
        "meloxicam",
        "naproxen",
        "nsaid",
    ),
    "nsaid": (
        "aspirin",
        "diclofenac",
        "ibuprofen",
        "ketorolac",
        "meloxicam",
        "naproxen",
        "nsaid",
    ),
    "opioid": (
        "codeine",
        "hydrocodone",
        "hydromorphone",
        "morphine",
        "oxycodone",
        "tramadol",
    ),
    "codeine": (
        "codeine",
        "hydrocodone",
        "hydromorphone",
        "morphine",
        "oxycodone",
        "tramadol",
    ),
    "morphine": (
        "codeine",
        "hydrocodone",
        "hydromorphone",
        "morphine",
        "oxycodone",
        "tramadol",
    ),
}

DRUG_CLASS_TERMS = {
    "NSAID": ("aspirin", "diclofenac", "ibuprofen", "ketorolac", "meloxicam", "naproxen"),
    "opioid": ("codeine", "fentanyl", "hydrocodone", "morphine", "oxycodone", "tramadol"),
    "benzodiazepine": ("alprazolam", "clonazepam", "diazepam", "lorazepam"),
    "SSRI": ("citalopram", "escitalopram", "fluoxetine", "paroxetine", "sertraline"),
    "statin": ("atorvastatin", "pravastatin", "rosuvastatin", "simvastatin"),
    "ACE inhibitor": ("benazepril", "enalapril", "lisinopril", "ramipril"),
    "ARB": ("irbesartan", "losartan", "olmesartan", "valsartan"),
    "beta blocker": ("atenolol", "metoprolol", "propranolol", "timolol"),
    "PPI": ("esomeprazole", "lansoprazole", "omeprazole", "pantoprazole"),
    "anticoagulant": ("apixaban", "dabigatran", "enoxaparin", "rivaroxaban", "warfarin"),
    "insulin": ("insulin",),
}


def _normalize_safety_type(value: object) -> str:
    raw = str(value or "").lower().replace("_", " ").replace("-", " ")
    if "allerg" in raw:
        return "allergy"
    if "interact" in raw or "drug drug" in raw or raw == "dur":
        return "interaction"
    if "duplicate" in raw or "therapy" in raw:
        return "duplicate"
    if "refill" in raw or "insurance" in raw or "too soon" in raw:
        return "refill"
    if "lasa" in raw or "look alike" in raw or "sound alike" in raw:
        return "lasa"
    if "high" in raw and "alert" in raw:
        return "high_alert"
    if "clarif" in raw or "prescriber" in raw or "direction" in raw:
        return "clarification"
    if "daw" in raw or "brand medically necessary" in raw:
        return "daw"
    return "training"


def _add_safety_warning(
    warnings: list[dict],
    warning_type: str,
    message: str,
    title: str | None = None,
    badge: str | None = None,
    tone: str | None = None,
) -> None:
    if not message:
        return
    normalized_type = _normalize_safety_type(warning_type)
    default_title, default_badge, default_tone = SAFETY_META[normalized_type]
    warnings.append(
        {
            "type": normalized_type,
            "title": title or default_title,
            "badge": badge or default_badge,
            "tone": tone or default_tone,
            "message": message,
        }
    )


def _as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _safe_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else default


def _case_drug_text(case: dict) -> str:
    expected = case.get("expected") or {}
    rx = case.get("rx_text") or {}
    extras = case.get("extras") or {}
    return " ".join(
        str(part)
        for part in (
            expected.get("drug_name"),
            rx.get("drug_line"),
            " ".join(extras.get("drug_alternates", []))
            if isinstance(extras.get("drug_alternates"), list)
            else "",
        )
        if part
    ).lower()


def _case_sig_text(case: dict) -> str:
    expected = case.get("expected") or {}
    rx = case.get("rx_text") or {}
    return f'{rx.get("sig_shorthand", "")} {expected.get("sig_english", "")}'.lower()


def _patient_medications(case: dict) -> list[str]:
    patient = case.get("patient") or {}
    meds: list[str] = []
    for source in (case, patient):
        for key in ("medications", "current_medications", "current_meds", "active_meds"):
            meds.extend(str(item) for item in _as_list(source.get(key)) if item)
    profile = case.get("profile") or patient.get("profile") or {}
    if isinstance(profile, dict):
        for key in ("medications", "current_medications", "current_meds", "active_meds"):
            meds.extend(str(item) for item in _as_list(profile.get(key)) if item)
    return meds


def _drug_classes(text: str) -> set[str]:
    normalized = text.lower()
    return {
        class_name
        for class_name, terms in DRUG_CLASS_TERMS.items()
        if any(term in normalized for term in terms)
    }


def _allergy_is_nkda(allergy: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", allergy.lower()).strip()
    return normalized in {
        "",
        "nkda",
        "nka",
        "none",
        "no known allergies",
        "no known drug allergies",
    }


def _allergy_matches_drug(allergy: str, drug_text: str) -> bool:
    normalized_allergy = allergy.lower()
    simple_allergy = re.sub(
        r"\b(allergy|allergic|drugs?|medications?)\b",
        "",
        normalized_allergy,
    ).strip()
    if simple_allergy and simple_allergy in drug_text:
        return True
    for allergy_key, related_terms in ALLERGY_RELATED_TERMS.items():
        if allergy_key in normalized_allergy and any(term in drug_text for term in related_terms):
            return True
    return False


def _collect_explicit_safety_warnings(case: dict, warnings: list[dict]) -> None:
    def parse_item(item: object, fallback_type: str = "training") -> None:
        if isinstance(item, dict):
            if any(key in item for key in ("message", "text", "detail", "description", "title", "type")):
                warning_type = item.get("type") or item.get("kind") or item.get("category") or fallback_type
                message = (
                    item.get("message")
                    or item.get("text")
                    or item.get("detail")
                    or item.get("description")
                    or ""
                )
                if not message and item.get("title"):
                    message = str(item["title"])
                _add_safety_warning(
                    warnings,
                    str(warning_type),
                    str(message),
                    title=str(item["title"]) if item.get("title") else None,
                    badge=str(item["badge"]) if item.get("badge") else None,
                    tone=str(item["tone"]) if item.get("tone") else None,
                )
            else:
                for key, value in item.items():
                    parse_item(value, str(key))
        elif isinstance(item, (list, tuple, set)):
            for child in item:
                parse_item(child, fallback_type)
        elif isinstance(item, str) and item.strip():
            _add_safety_warning(warnings, fallback_type, item.strip())

    for key in ("safety_warnings", "dur_warnings", "warnings"):
        parse_item(case.get(key), key)

    safety = case.get("safety") or case.get("dur") or {}
    if isinstance(safety, dict):
        parse_item(safety.get("warnings") if "warnings" in safety else safety, "safety")
    else:
        parse_item(safety, "safety")


def _collect_allergy_warnings(case: dict, warnings: list[dict], drug_text: str) -> None:
    patient = case.get("patient") or {}
    allergies = [str(item).strip() for item in _as_list(patient.get("allergies")) if str(item).strip()]
    for allergy in allergies:
        if _allergy_is_nkda(allergy):
            continue
        if _allergy_matches_drug(allergy, drug_text):
            _add_safety_warning(
                warnings,
                "allergy",
                (
                    f"Patient has a documented {allergy} allergy. "
                    "Review before dispensing."
                ),
            )


def _collect_lasa_warnings(warnings: list[dict], drug_text: str) -> None:
    if "hydralazine" in drug_text or "hydroxyzine" in drug_text:
        _add_safety_warning(
            warnings,
            "lasa",
            (
                "Hydralazine and hydroxyzine are commonly confused. "
                "Verify drug name carefully."
            ),
        )


def _collect_high_alert_warnings(warnings: list[dict], drug_text: str) -> None:
    for group_name, terms in HIGH_ALERT_DRUG_GROUPS.items():
        if any(term in drug_text for term in terms):
            _add_safety_warning(
                warnings,
                "high_alert",
                (
                    "Double-check dose, route, and directions before dispensing. "
                    f"This case involves a high-alert {group_name} medication."
                ),
            )
            return


def _collect_refill_and_daw_warnings(case: dict, warnings: list[dict]) -> None:
    expected = case.get("expected") or {}
    rx = case.get("rx_text") or {}
    refills = _safe_int(expected.get("refills", rx.get("refills_text")), default=0)
    days_supply = _safe_int(expected.get("days_supply"), default=0)
    daw_text = str(rx.get("daw_text", ""))
    daw_value = _safe_int(expected.get("daw", daw_text), default=0)

    previous_fill_days_ago = _safe_int(
        case.get("previous_fill_days_ago")
        or case.get("days_since_last_fill")
        or rx.get("previous_fill_days_ago"),
        default=0,
    )
    if previous_fill_days_ago and days_supply and previous_fill_days_ago < days_supply * 0.75:
        _add_safety_warning(
            warnings,
            "refill",
            (
                "Refill too soon: Insurance may reject this claim if the patient "
                "is attempting to refill early."
            ),
        )
    elif refills >= 6:
        _add_safety_warning(
            warnings,
            "refill",
            (
                "Refill review: Refills are unusually high for this training case. "
                "Verify the authorized refills and plan limits before processing."
            ),
        )
    elif days_supply and days_supply <= 14 and refills > 0:
        _add_safety_warning(
            warnings,
            "refill",
            (
                "Refill review: Acute or short-course prescriptions with refills "
                "may need pharmacist or prescriber review."
            ),
        )

    if daw_value == 1 or "brand medically necessary" in daw_text.lower():
        _add_safety_warning(
            warnings,
            "daw",
            (
                "DAW verification: Brand medically necessary / DAW 1 is indicated. "
                "Verify the DAW code is entered exactly as written."
            ),
        )


def _collect_sig_clarity_warnings(case: dict, warnings: list[dict]) -> None:
    sig_text = _case_sig_text(case)
    if re.search(r"\bprn\b", sig_text, re.IGNORECASE) or "as needed" in sig_text:
        _add_safety_warning(
            warnings,
            "clarification",
            (
                "Directions need clarity: PRN directions should include an indication "
                "and enough detail to confirm maximum daily use when applicable."
            ),
        )


def _collect_interaction_and_duplicate_warnings(
    case: dict,
    warnings: list[dict],
    drug_text: str,
) -> None:
    current_meds = _patient_medications(case)
    if not current_meds:
        return

    drug_classes = _drug_classes(drug_text)
    for med in current_meds:
        med_text = med.lower()
        med_classes = _drug_classes(med_text)
        shared_classes = sorted(drug_classes & med_classes)
        if shared_classes:
            _add_safety_warning(
                warnings,
                "duplicate",
                (
                    f"Duplicate therapy warning: Patient profile already lists {med}. "
                    f"Review possible duplicate {shared_classes[0]} therapy."
                ),
            )
            break

    med_profile_text = " ".join(current_meds).lower()
    interaction_pairs = [
        (
            ("ibuprofen", "naproxen", "diclofenac", "ketorolac", "meloxicam", "aspirin"),
            ("warfarin", "coumadin", "jantoven"),
            "NSAID plus warfarin can raise bleeding risk. Escalate the DUR alert to the pharmacist.",
        ),
        (
            ("codeine", "fentanyl", "hydrocodone", "morphine", "oxycodone", "tramadol"),
            ("alprazolam", "clonazepam", "diazepam", "lorazepam"),
            "Opioids with benzodiazepines can increase sedation and breathing risk. Escalate for pharmacist review.",
        ),
        (
            ("tramadol",),
            ("citalopram", "escitalopram", "fluoxetine", "paroxetine", "sertraline"),
            "Tramadol with SSRIs may increase serotonin-related adverse effect risk. Escalate for pharmacist review.",
        ),
        (
            ("lisinopril", "benazepril", "enalapril", "losartan", "valsartan"),
            ("potassium", "spironolactone"),
            "ACE inhibitor / ARB therapy with potassium-raising medications may require monitoring review.",
        ),
        (
            ("methotrexate",),
            ("ibuprofen", "naproxen", "trimethoprim", "sulfamethoxazole", "bactrim"),
            "Methotrexate has important interaction concerns with several antibiotics and NSAIDs.",
        ),
    ]
    for current_terms, profile_terms, message in interaction_pairs:
        profile_matches_current = any(term in med_profile_text for term in current_terms)
        profile_matches_other = any(term in med_profile_text for term in profile_terms)
        current_matches_current = any(term in drug_text for term in current_terms)
        current_matches_other = any(term in drug_text for term in profile_terms)
        if (current_matches_current and profile_matches_other) or (
            current_matches_other and profile_matches_current
        ):
            _add_safety_warning(warnings, "interaction", message)
            break


def _dedupe_safety_warnings(warnings: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for warning in warnings:
        key = (warning.get("type", ""), warning.get("message", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(warning)
    return unique


def get_safety_warnings(case: dict) -> list[dict]:
    """Return DUR-style warnings for a case using explicit data plus fallbacks."""
    warnings: list[dict] = []
    if not isinstance(case, dict):
        return warnings

    drug_text = _case_drug_text(case)
    _collect_explicit_safety_warnings(case, warnings)
    _collect_allergy_warnings(case, warnings, drug_text)
    _collect_interaction_and_duplicate_warnings(case, warnings, drug_text)
    _collect_lasa_warnings(warnings, drug_text)
    _collect_high_alert_warnings(warnings, drug_text)
    _collect_refill_and_daw_warnings(case, warnings)
    _collect_sig_clarity_warnings(case, warnings)
    return _dedupe_safety_warnings(warnings)


# =====================================================================
# PDF builder using reportlab
# =====================================================================

def build_label_pdf(case: dict, feedback: dict) -> bytes:
    """Build a one-page training label PDF using reportlab.

    Uses the same field-resolution as the on-screen label: user's value
    if correct, expected value with '*' marker if wrong. Disclaimer is
    placed both at the top and bottom of the page.
    """
    expected = case["expected"]
    patient = case["patient"]
    prescriber = case["prescriber"]

    corrected_fields: list[str] = []

    def resolve(field_key: str, corrected_value):
        res = feedback.get(field_key, {})
        if res.get("correct"):
            return str(res["user"]), False
        corrected_fields.append(field_key)
        return str(corrected_value), True

    drug_val, drug_corr = resolve("drug_name", expected["drug_name"])
    strength_val, strength_corr = resolve("strength", expected["strength"])
    sig_val, sig_corr = resolve("sig", expected.get("sig_english", ""))
    qty_val, qty_corr = resolve("quantity", expected["quantity"])
    days_val, days_corr = resolve("days_supply", expected["days_supply"])
    refills_val, refills_corr = resolve("refills", expected["refills"])

    def mark(corrected: bool) -> str:
        return " *" if corrected else ""

    digits = "".join(c for c in case["case_id"] if c.isdigit()) or "0"
    rx_num = f"Rx# {int(digits):07d}"
    fill_date = date.today().strftime("%m/%d/%Y")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Training Label",
        author="Rx Entry Simulator",
    )

    # Paragraph styles
    pharm_style = ParagraphStyle(
        "pharm", fontName="Helvetica-Bold", fontSize=12,
        textColor=colors.black, alignment=0,
    )
    rx_num_style = ParagraphStyle(
        "rxnum", fontName="Courier", fontSize=10,
        textColor=colors.black, alignment=2,
    )
    address_style = ParagraphStyle(
        "addr", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#4b5563"),
    )
    patient_style = ParagraphStyle(
        "patient", fontName="Helvetica-Bold", fontSize=12,
        textColor=colors.black,
    )
    fill_date_style = ParagraphStyle(
        "filldate", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#4b5563"), alignment=2,
    )
    drug_style = ParagraphStyle(
        "drug", fontName="Helvetica-Bold", fontSize=14,
        textColor=colors.black,
    )
    sig_style = ParagraphStyle(
        "sig", fontName="Helvetica", fontSize=13,
        textColor=colors.black, leading=18,
    )
    fill_field_style = ParagraphStyle(
        "fill", fontName="Helvetica", fontSize=11,
        textColor=colors.black, alignment=1,
    )
    presc_style = ParagraphStyle(
        "presc", fontName="Helvetica", fontSize=11,
        textColor=colors.black,
    )
    footer_style = ParagraphStyle(
        "footer", fontName="Helvetica-Bold", fontSize=10,
        textColor=colors.black, alignment=1,
    )
    warning_style = ParagraphStyle(
        "warn", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#92400e"), alignment=1,
        backColor=colors.HexColor("#fef3c7"),
        borderPadding=8,
        borderColor=colors.HexColor("#f59e0b"),
        borderWidth=0.5,
    )

    story: list = []

    # Top disclaimer
    story.append(Paragraph("TRAINING ONLY \u2014 NOT FOR DISPENSING", footer_style))
    story.append(Spacer(1, 12))

    # Corrections banner if any
    if corrected_fields:
        n = len(corrected_fields)
        plural = "s" if n != 1 else ""
        story.append(Paragraph(
            f"{n} field{plural} shown corrected (marked *) \u2014 "
            "training preview only \u2014 not for dispensing",
            warning_style,
        ))
        story.append(Spacer(1, 14))

    # Pharmacy header row
    pharmacy_table = Table(
        [[Paragraph("TRAINING PHARMACY", pharm_style),
          Paragraph(rx_num, rx_num_style)]],
        colWidths=[4 * inch, 2.5 * inch],
    )
    pharmacy_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(pharmacy_table)

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "7420 Mockingbird Lane \u00b7 Practice City, TX 78001 \u00b7 (555) 214-8096",
        address_style,
    ))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"),
        spaceBefore=8, spaceAfter=10, dash=(2, 2),
    ))

    # Patient + fill date row
    patient_table = Table(
        [[Paragraph(patient["name"].upper(), patient_style),
          Paragraph(f"Filled: {fill_date}", fill_date_style)]],
        colWidths=[4 * inch, 2.5 * inch],
    )
    patient_table.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(patient_table)

    story.append(Spacer(1, 14))

    # Drug line
    drug_text = (
        f"{drug_val.upper()}{mark(drug_corr)} "
        f"{strength_val.upper()}{mark(strength_corr)}"
    )
    story.append(Paragraph(drug_text, drug_style))

    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"),
        spaceBefore=12, spaceAfter=12, dash=(2, 2),
    ))

    # SIG
    story.append(Paragraph(f"{sig_val.upper()}{mark(sig_corr)}", sig_style))

    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"),
        spaceBefore=12, spaceAfter=12, dash=(2, 2),
    ))

    # Qty / Days / Refills row (use Table for clean columns)
    fill_table = Table(
        [[
            Paragraph(f"<b>Qty:</b> {qty_val}{mark(qty_corr)}", fill_field_style),
            Paragraph(f"<b>Days supply:</b> {days_val}{mark(days_corr)}", fill_field_style),
            Paragraph(f"<b>Refills:</b> {refills_val}{mark(refills_corr)}", fill_field_style),
        ]],
        colWidths=[2.17 * inch, 2.17 * inch, 2.17 * inch],
    )
    fill_table.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(fill_table)

    story.append(Spacer(1, 14))

    # Prescriber
    story.append(Paragraph(
        f"<b>Prescriber:</b> {prescriber['name']}",
        presc_style,
    ))

    # Bottom footer
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=colors.black,
        spaceBefore=18, spaceAfter=10,
    ))
    story.append(Paragraph("TRAINING ONLY \u00b7 NOT FOR DISPENSING", footer_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# =====================================================================
# Render functions
# =====================================================================

def render_header() -> None:
    # Field-level accuracy across every checked field this session.
    correct, total = overall_accuracy()
    if total:
        acc_pct = correct / total * 100
        acc_str = f"{acc_pct:.0f}%"
        acc_class = "chip" if acc_pct >= 70 else "chip accuracy-low"
    else:
        acc_str = "—"
        acc_class = "chip"

    # Focus area: name the weakest field so the chip is actionable rather
    # than a bare miss count. Falls back to "On track" once everything
    # attempted is correct, and to a neutral dash before any practice.
    stats = st.session_state.stats
    weakest = tracker.weakest_field(stats)
    acc_by_field = tracker.field_accuracy(stats)
    if weakest is not None and acc_by_field.get(weakest, 1.0) < 1.0:
        focus_value = FIELD_LABELS.get(weakest, weakest)
        focus_class = "chip missed"
    elif total:
        focus_value = "On track"
        focus_class = "chip"
    else:
        focus_value = "—"
        focus_class = "chip missed empty"

    cases_practiced = st.session_state.cases_completed

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title-block">
                <div class="app-eyebrow">Training workstation</div>
                <h1>Rx Entry Simulator</h1>
                <div class="subtitle">Pharmacy technician training tool</div>
            </div>
            <div class="stat-chips">
                <span class="chip">
                    <span class="chip-label">Cases practiced</span>
                    <span class="chip-value">{cases_practiced}</span>
                </span>
                <span class="{acc_class}">
                    <span class="chip-label">Field accuracy</span>
                    <span class="chip-value">{acc_str}</span>
                </span>
                <span class="{focus_class}">
                    <span class="chip-label">Focus area</span>
                    <span class="chip-value">{html.escape(str(focus_value))}</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prescription_card(case: dict) -> None:
    rx = case["rx_text"]
    case_id_safe = html.escape(case["case_id"])
    drug_line_safe = html.escape(rx["drug_line"])
    sig_safe = html.escape(rx["sig_shorthand"])
    date_safe = html.escape(rx["date_written"])

    if rx.get("quantity_text"):
        disp_value = html.escape(_strip_label(rx["quantity_text"]))
        disp_class = "rx-tag-value"
    else:
        disp_value = "Not specified"
        disp_class = "rx-tag-value muted"

    refills_value = html.escape(_strip_label(rx["refills_text"]))
    daw_value = html.escape(_strip_label(rx["daw_text"]))

    with st.container(border=True):
        # Border marker so CSS can force a visible outline regardless of
        # the Streamlit version's default container rendering. See the
        # .card-border-anchor rule in CUSTOM_CSS.
        st.markdown(
            '<div class="card-border-anchor"></div>',
            unsafe_allow_html=True,
        )
        # Header row
        st.markdown(
            '<div class="rx-header-row">'
            f'<div class="section-label">Prescription &middot; {case_id_safe}</div>'
            f'<div class="rx-meta">Date written:<span class="meta-value">{date_safe}</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ---- Medication zone: drug line + See Example button ----
        st.markdown(
            '<div class="rx-group-label first">Medication</div>',
            unsafe_allow_html=True,
        )
        col_drug, col_btn = st.columns([5, 1.4])
        with col_drug:
            st.markdown(
                f'<div class="rx-drug">{drug_line_safe}</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            # Anchor for the green :has() CSS selector to find this button
            st.markdown(
                '<div class="see-example-anchor"></div>',
                unsafe_allow_html=True,
            )
            # show_example only sets the example_mode flag (and feedback);
            # it does NOT write to widget keys. render_entry_form below
            # renders example-mode widgets with value= directly, which
            # bypasses session_state widget-key propagation issues that
            # affect anonymous Streamlit Cloud sessions.
            st.button(
                "See Example",
                type="secondary",
                key="see_example_btn",
                use_container_width=True,
                disabled=st.session_state.get("submitted", False),
                on_click=show_example,
            )

        # ---- Directions zone: the SIG shorthand ----
        st.markdown(
            '<div class="rx-group-label">Directions</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rx-sig-row">'
            '<span class="rx-mini-label">SIG</span>'
            f'<span class="rx-sig">{sig_safe}</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ---- Dispensing details zone: Disp / Refills / DAW strip ----
        st.markdown(
            '<div class="rx-group-label">Dispensing details</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rx-tags">'
            '<div class="rx-tag">'
            '<span class="rx-mini-label">Disp</span>'
            f'<span class="{disp_class}">{disp_value}</span>'
            '</div>'
            '<div class="rx-tag">'
            '<span class="rx-mini-label">Refills</span>'
            f'<span class="rx-tag-value">{refills_value}</span>'
            '</div>'
            '<div class="rx-tag">'
            '<span class="rx-mini-label">DAW</span>'
            f'<span class="rx-tag-value">{daw_value}</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


def render_safety_warnings(warnings: list[dict]) -> None:
    """Render the DUR / Safety Review panel for the current case."""
    with st.container(border=True):
        st.markdown(
            '<div class="card-border-anchor"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-label">DUR / Safety Review</div>',
            unsafe_allow_html=True,
        )

        if not warnings:
            st.markdown(
                (
                    '<div class="safety-empty-state">'
                    'No major safety warnings found for this training case.'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )
            return

        callouts = ""
        allowed_tones = {"safety", "insurance", "drug", "training"}
        for warning in warnings:
            tone = str(warning.get("tone", "training"))
            if tone not in allowed_tones:
                tone = "training"
            title = html.escape(str(warning.get("title", "Training note")))
            badge = html.escape(str(warning.get("badge", "🧠 Training note")))
            message = html.escape(str(warning.get("message", "")))
            callouts += (
                f'<div class="safety-callout {tone}">'
                '<div class="safety-callout-header">'
                f'<div class="safety-callout-title">{title}</div>'
                f'<div class="safety-callout-badge">{badge}</div>'
                '</div>'
                f'<div class="safety-callout-body">{message}</div>'
                '</div>'
            )

        st.markdown(
            f'<div class="safety-warning-list">{callouts}</div>',
            unsafe_allow_html=True,
        )


def _party_card_html(title: str, rows: list[tuple[str, str]]) -> str:
    """Build HTML for a small data card (Patient or Prescriber)."""
    rows_html = "".join(
        f'<div class="data-row">'
        f'<span class="label">{html.escape(label)}</span>'
        f'<span class="value">{html.escape(value)}</span>'
        f'</div>'
        for label, value in rows
    )
    return f"""
    <div class="section-card">
        <div class="section-label">{html.escape(title)}</div>
        <div class="data-grid">{rows_html}</div>
    </div>
    """


def render_patient_prescriber(case: dict) -> None:
    p = case["patient"]
    pr = case["prescriber"]

    patient_rows = [
        ("Name", p["name"]),
        ("DOB", p["dob"]),
        ("MRN", p["mrn"]),
        ("Address", p["address"]),
        ("Allergies", ", ".join(p["allergies"])),
    ]
    prescriber_rows = [
        ("Name", pr["name"]),
        ("NPI", pr["npi"]),
        ("DEA", pr["dea"]),
        ("Address", pr["address"]),
    ]

    col_p, col_pr = st.columns(2)
    with col_p:
        st.markdown(_party_card_html("Patient", patient_rows), unsafe_allow_html=True)
    with col_pr:
        st.markdown(_party_card_html("Prescriber", prescriber_rows), unsafe_allow_html=True)


def render_sig_help() -> None:
    """Optional SIG abbreviation decoder. Toggled via a small button.

    Sits just below the prescription card so students can quickly look up
    shorthand they don't yet recognize.
    """
    is_open = st.session_state.get("sig_help_open", False)
    btn_label = "Hide SIG decoder" if is_open else "Decode SIG"
    col_btn, _ = st.columns([1.6, 5])
    with col_btn:
        if st.button(
            btn_label,
            type="secondary",
            use_container_width=True,
            key="sig_help_toggle",
        ):
            st.session_state.sig_help_open = not is_open
            st.rerun()

    if not is_open:
        return

    sig_shorthand = st.session_state.current_case["rx_text"]["sig_shorthand"]
    decoded = decode_sig(sig_shorthand)

    if decoded:
        pair_html = "".join(
            '<div class="sig-pair">'
            f'<span class="sig-abbr">{html.escape(token)}</span>'
            '<span class="sig-eq">=</span>'
            f'<span class="sig-meaning">{html.escape(meaning)}</span>'
            '</div>'
            for token, meaning in decoded
        )
    else:
        pair_html = (
            '<div style="font-size: 0.85rem; color: #6b7280;">'
            'No standard abbreviations detected in this SIG.'
            '</div>'
        )

    decoder_html = (
        '<div class="sig-decoder">'
        f'<div class="sig-decoder-title">Breakdown of: {html.escape(sig_shorthand)}</div>'
        '<div class="sig-decoder-list">'
        + pair_html
        + '</div>'
        '</div>'
    )
    st.markdown(decoder_html, unsafe_allow_html=True)


def _fake_input_html(label: str, value: str) -> str:
    """Build static HTML that mimics st.text_input visually.

    Used in example mode to render the canonical answer fields as
    pure HTML so no Streamlit widget machinery is involved. The
    .fake-input and .fake-input-label classes are styled in CUSTOM_CSS
    to match Streamlit's real text_input styling pixel for pixel.
    """
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    return (
        '<div class="fake-input-wrapper">'
        f'<div class="fake-input-label">{safe_label}</div>'
        f'<div class="fake-input">{safe_value}</div>'
        '</div>'
    )


def _fake_textarea_html(label: str, value: str) -> str:
    """Build static HTML that mimics st.text_area visually (multi-line)."""
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    return (
        '<div class="fake-input-wrapper">'
        f'<div class="fake-input-label">{safe_label}</div>'
        f'<div class="fake-textarea">{safe_value}</div>'
        '</div>'
    )


def render_entry_form() -> dict | None:
    """Render the entry form. Returns user answers if Check Entry was clicked.

    Two completely separate render paths based on example_mode:

    Example mode (after See Example click):
        Renders pure HTML divs styled to look pixel-identical to
        Streamlit's text_input / text_area widgets, with the canonical
        answers baked into the markup. No Streamlit widgets are
        instantiated for the fields. This bypasses every browser CSS
        rendering quirk, every Chrome auto-dark inversion, every
        widget-state propagation issue, and every Streamlit Cloud
        deployment caching pattern that has caused the seven prior
        attempts to fail visually. The user sees what looks like the
        same entry form, just filled in.

    Normal mode (user is typing their own answer):
        Real editable st.text_input / st.text_area widgets with
        key="in_drug" etc. and placeholders. User input persists across
        reruns via Streamlit's standard widget state mechanism.

    The Check Entry / Try Again / Next Case button row renders the same
    way in both modes (real Streamlit buttons, because the user must
    actually click them).
    """
    example = st.session_state.get("example_mode", False)
    case = st.session_state.current_case
    expected = case["expected"] if example else None

    with st.container(border=True):
        # Border marker (see .card-border-anchor rule in CUSTOM_CSS)
        st.markdown(
            '<div class="card-border-anchor"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-label" style="margin: 6px 0 4px 0;">'
            'Rx Processing &middot; Entry Form'
            '</div>',
            unsafe_allow_html=True,
        )

        # Drug Entry
        st.markdown(
            '<div class="form-group-label first">Drug Entry</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1, 1])
        with c1:
            if example:
                st.markdown(
                    _fake_input_html("Drug name", str(expected["drug_name"])),
                    unsafe_allow_html=True,
                )
            else:
                st.text_input(
                    "Drug name",
                    key="in_drug",
                    placeholder="Generic name",
                )
        with c2:
            if example:
                st.markdown(
                    _fake_input_html("Strength", str(expected["strength"])),
                    unsafe_allow_html=True,
                )
            else:
                st.text_input(
                    "Strength",
                    key="in_strength",
                    placeholder="e.g. 500 mg",
                )

        # Fill Details
        st.markdown(
            '<div class="form-group-label">Fill Details</div>',
            unsafe_allow_html=True,
        )
        c3, c4, c5, c6 = st.columns(4)
        with c3:
            if example:
                st.markdown(
                    _fake_input_html("Quantity", str(expected["quantity"])),
                    unsafe_allow_html=True,
                )
            else:
                st.text_input(
                    "Quantity", key="in_quantity", placeholder="0"
                )
        with c4:
            if example:
                st.markdown(
                    _fake_input_html("Days supply", str(expected["days_supply"])),
                    unsafe_allow_html=True,
                )
            else:
                st.text_input(
                    "Days supply", key="in_days", placeholder="0"
                )
        with c5:
            if example:
                st.markdown(
                    _fake_input_html("Refills", str(expected["refills"])),
                    unsafe_allow_html=True,
                )
            else:
                st.text_input(
                    "Refills", key="in_refills", placeholder="0"
                )
        with c6:
            if example:
                st.markdown(
                    _fake_input_html("DAW code", str(expected["daw"])),
                    unsafe_allow_html=True,
                )
            else:
                st.text_input(
                    "DAW code", key="in_daw", placeholder="0"
                )

        # Patient Directions
        st.markdown(
            '<div class="form-group-label">Patient Directions (SIG)</div>',
            unsafe_allow_html=True,
        )
        if example:
            st.markdown(
                _fake_textarea_html(
                    "Translate shorthand into plain English",
                    str(expected.get("sig_english", "")),
                ),
                unsafe_allow_html=True,
            )
        else:
            st.text_area(
                "Translate shorthand into plain English",
                key="in_sig",
                height=110,
                placeholder=(
                    "Include verb, quantity, dosage form, route, "
                    "frequency, and duration when applicable."
                ),
            )

        # Action buttons
        st.markdown(
            '<div style="margin-top: 8px;"></div>',
            unsafe_allow_html=True,
        )

        # Conditional button styling: Check Entry is primary before
        # submission, Next Case is primary after a perfect entry.
        submitted = st.session_state.submitted
        last_fb = st.session_state.last_feedback
        all_correct = (
            submitted
            and bool(last_fb)
            and all(r["correct"] for r in last_fb.values())
        )
        check_type = "primary" if not submitted else "secondary"
        next_type = "primary" if all_correct else "secondary"

        col_a, col_b, col_c, _ = st.columns([1.3, 1.3, 1.3, 3])
        with col_a:
            submit = st.button(
                "Check Entry",
                type=check_type,
                disabled=submitted,
                use_container_width=True,
            )
        with col_b:
            try_again_clicked = st.button(
                "Try Again",
                type="secondary",
                disabled=not submitted,
                use_container_width=True,
            )
        with col_c:
            next_case = st.button(
                "Next Case",
                type=next_type,
                disabled=not submitted,
                use_container_width=True,
            )

    # In example mode, Check Entry is disabled (submitted=True), so this
    # branch never executes. The field values are read from the real
    # widget state on real submissions only.
    if submit:
        return {
            "drug_name": st.session_state.get("in_drug", ""),
            "strength": st.session_state.get("in_strength", ""),
            "quantity": st.session_state.get("in_quantity", ""),
            "sig": st.session_state.get("in_sig", ""),
            "days_supply": st.session_state.get("in_days", ""),
            "refills": st.session_state.get("in_refills", ""),
            "daw": st.session_state.get("in_daw", ""),
        }
    if try_again_clicked:
        try_again()
        st.rerun()
    if next_case:
        advance_case()
        st.rerun()
    return None


def _build_field_details_html(feedback: dict) -> str:
    """Build the per-field result row HTML used by both feedback views."""
    items_html = ""
    for field, res in feedback.items():
        label = FIELD_LABELS.get(field, field)
        css_class = "correct" if res["correct"] else "incorrect"
        status_text = "Correct" if res["correct"] else "Incorrect"

        detail_html = ""
        if not res["correct"]:
            user_safe = (
                html.escape(str(res["user"])) if res["user"] != "" else "(empty)"
            )
            expected_safe = html.escape(str(res["expected"]))
            detail_html = (
                f'<div class="feedback-detail">'
                f'Your answer:<span class="answer-box">{user_safe}</span>'
                f'&nbsp;&nbsp;Expected:<span class="answer-box">{expected_safe}</span>'
                f'</div>'
            )
            if res.get("explanation"):
                explanation_safe = html.escape(res["explanation"])
                detail_html += (
                    f'<div class="feedback-explanation">{explanation_safe}</div>'
                )

        items_html += (
            f'<div class="feedback-item {css_class}">'
            f'  <div class="field-row">'
            f'    <span class="field-name">{html.escape(label)}</span>'
            f'    <span class="field-status">{status_text}</span>'
            f'  </div>'
            f'  {detail_html}'
            f'</div>'
        )
    return items_html


def _performance_message(correct: int, total: int) -> tuple[str, str]:
    """Map a score to a (tone, message) pair for the feedback summary.

    Tones map to the green / amber / red palette used elsewhere:
        high   (>= ~85%, i.e. 6-7 of 7) -> green
        medium (>= 50%,  i.e. 4-5 of 7) -> amber
        low    (< 50%,   i.e. 0-3 of 7) -> red
    """
    ratio = (correct / total) if total else 0.0
    if ratio >= 0.85:
        return "high", "Great job — ready for a harder case."
    if ratio >= 0.5:
        return "medium", "Close — review the missed fields."
    return "low", "Needs practice — use the example and try again."


def _expected_display(field: str, case: dict) -> str:
    """Human-readable expected value for a field in the feedback report.

    The SIG checker stores a generic descriptor as its "expected" value,
    so for display we substitute the full plain-English SIG instead.
    """
    expected = case["expected"]
    if field == "sig":
        return str(expected.get("sig_english", ""))
    return str(expected.get(field, ""))


# DAW code meanings, keyed by the expected integer code. Used to explain
# why the expected DAW value is correct on a per-case basis.
_DAW_MEANINGS = {
    0: "DAW 0 = no product selection indicated; generic substitution is allowed.",
    1: "DAW 1 = substitution not allowed; the prescriber marked brand medically necessary.",
    2: "DAW 2 = the patient requested the brand name product.",
}


def _why_explanation(field: str, case: dict) -> str:
    """Short explanation of why the expected answer is correct for a field.

    These are derived from the case data (expected values, the extras
    calculation strings, and the SIG decoder) so every field — correct or
    incorrect — gets a teaching note in the feedback report.
    """
    expected = case["expected"]
    extras = case.get("extras") or {}

    if field == "drug_name":
        return (
            f"The prescription is written for {expected['drug_name']}. Enter the "
            "drug name exactly as written, and watch for generic vs brand names."
        )
    if field == "strength":
        return (
            f"The strength is {expected['strength']}. Always include both the "
            "number and the unit (mg, mcg, mL, %, etc.)."
        )
    if field == "quantity":
        base = "Quantity is the total amount dispensed for this fill."
        calc = extras.get("quantity_calc")
        return f"{base} {calc}" if calc else base
    if field == "days_supply":
        base = (
            "Days supply = total quantity ÷ number of doses taken per day. "
            "It tells the insurer how long the fill should last."
        )
        calc = extras.get("days_calc")
        return f"{base} {calc}" if calc else base
    if field == "refills":
        return (
            f"The prescriber authorized {expected['refills']} refill(s). Copy the "
            "refills line from the prescription exactly — do not add or assume refills."
        )
    if field == "daw":
        return _DAW_MEANINGS.get(
            expected["daw"],
            "The DAW (Dispense As Written) code records why a specific product was dispensed.",
        )
    if field == "sig":
        shorthand = case["rx_text"]["sig_shorthand"]
        english = expected.get("sig_english", "")
        msg = (
            f'The shorthand "{shorthand}" translates to "{english}". '
            "A complete SIG names the action, amount, dosage form, route, "
            "frequency, and a duration when one is given."
        )
        decoded = decode_sig(shorthand)
        if decoded:
            pieces = "; ".join(f"{token} = {meaning}" for token, meaning in decoded)
            msg += f" Piece by piece: {pieces}."
        return msg
    return ""


def render_feedback_report(case: dict, feedback: dict) -> None:
    """Detailed pharmacy-tech feedback report shown after Check Entry.

    Renders:
      * an overall score ("X/7 fields correct"),
      * a performance message keyed to that score,
      * one row per field (correct AND incorrect) showing the status, the
        value entered, the expected answer, and a short explanation of why
        the expected answer is correct.

    This is intentionally exhaustive (all seven fields, always) so the panel
    reads like a graded report rather than only flagging mistakes.
    """
    if not feedback:
        return

    total = len(feedback)
    correct = sum(1 for r in feedback.values() if r["correct"])
    tone, perf_msg = _performance_message(correct, total)

    summary_html = (
        f'<div class="report-summary {tone}">'
        f'<div class="report-score">'
        f'<span class="report-badge">{correct} / {total}</span>'
        f'<span>{correct}/{total} fields correct</span>'
        f'</div>'
        f'<div class="report-perf">{html.escape(perf_msg)}</div>'
        f'</div>'
    )

    items_html = ""
    for field, res in feedback.items():
        label = FIELD_LABELS.get(field, field)
        css_class = "correct" if res["correct"] else "incorrect"
        if field == "sig":
            css_class += " sig-field"
        status_text = "Correct" if res["correct"] else "Incorrect"

        user_value = res["user"]
        user_safe = (
            html.escape(str(user_value)) if str(user_value) != "" else "(empty)"
        )
        expected_safe = html.escape(_expected_display(field, case))
        why = _why_explanation(field, case)
        why_html = (
            f'<div class="feedback-explanation">{html.escape(why)}</div>'
            if why
            else ""
        )

        items_html += (
            f'<div class="feedback-item {css_class}">'
            f'<div class="field-row">'
            f'<span class="field-name">{html.escape(label)}</span>'
            f'<span class="field-status">{status_text}</span>'
            f'</div>'
            f'<div class="feedback-detail">'
            f'You entered:<span class="answer-box">{user_safe}</span>'
            f'&nbsp;&nbsp;Expected:<span class="answer-box">{expected_safe}</span>'
            f'</div>'
            f'{why_html}'
            f'</div>'
        )

    st.markdown(
        '<div class="section-card">'
        '<div class="section-label">Feedback Report</div>'
        + summary_html
        + items_html
        + '</div>',
        unsafe_allow_html=True,
    )


def render_feedback() -> None:
    """Render the detailed Validation Results card for the mistakes path.

    On all-correct, this function early-returns. main() uses the compact
    render_success_card + render_feedback_details_expander pair instead.
    """
    if not st.session_state.submitted:
        return

    feedback = st.session_state.last_feedback
    if not feedback:
        return
    correct_count = sum(1 for r in feedback.values() if r["correct"])
    total = len(feedback)

    # All-correct case is handled separately by main() so the user does
    # not have to scroll past seven green rows to reach the label.
    if correct_count == total:
        return

    banner = (
        f'<div class="feedback-summary partial">'
        f'<span class="badge">{correct_count}/{total}</span>'
        f'Some fields need review. See details below.'
        f'</div>'
    )
    items_html = _build_field_details_html(feedback)
    full_html = (
        '<div class="section-card">'
        '<div class="section-label">Validation Results</div>'
        + banner
        + items_html
        + '</div>'
    )
    st.markdown(full_html, unsafe_allow_html=True)


def render_success_card(total: int, example_mode: bool = False) -> None:
    """Compact card shown after a perfect entry.

    When example_mode is True (the user clicked See Example), the copy
    and color switch to a 'demo' palette so it is visually distinct from
    a real perfect score and the user knows their stats are untouched.
    """
    if example_mode:
        card_class = "section-card success-card example-mode"
        title = "Example shown"
        subtitle = (
            f"All {total} fields pre-filled with the correct answer. "
            "This does not count toward your stats. Click Try Again to "
            "practice on your own, or Next Case to continue."
        )
    else:
        card_class = "section-card success-card"
        title = f"{total}/{total} fields correct"
        subtitle = "Label preview is ready."

    html_str = (
        f'<div class="{card_class}">'
        f'<div class="success-title">{title}</div>'
        f'<div class="success-subtitle">{subtitle}</div>'
        '</div>'
    )
    st.markdown(html_str, unsafe_allow_html=True)


def render_feedback_details_expander(feedback: dict) -> None:
    """Collapsible per-field detail rows; only used on the all-correct path."""
    if not feedback:
        return
    items_html = _build_field_details_html(feedback)
    with st.expander("View field details"):
        st.markdown(items_html, unsafe_allow_html=True)


def render_missed_fields_panel() -> None:
    """Compact panel showing recent missed fields. Hidden when empty."""
    queue = st.session_state.review_queue
    if not queue:
        return

    recent = queue[-8:][::-1]  # last 8, newest first
    rows_html = ""
    for item in recent:
        rows_html += (
            f'<div class="missed-row">'
            f'  <span class="case-id">{html.escape(item["case_id"])}</span>'
            f'  <span class="field">{html.escape(FIELD_LABELS.get(item["field"], item["field"]))}</span>'
            f'  <span class="expected">Expected: '
            f'    <code>{html.escape(str(item["expected"]))}</code>'
            f'  </span>'
            f'</div>'
        )

    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-label">Missed Fields &middot; recent</div>
            <div class="missed-list">{rows_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_label_locked(num_wrong: int, total: int) -> None:
    """Show a 'try again first' panel when too many fields are wrong.

    Includes a Reveal Label Preview button that flips st.session_state
    .label_revealed to True so the full label can be rendered.
    """
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-label">Label Preview</div>
            <div class="label-locked">
                <div class="lock-title">Try again first</div>
                <div class="lock-body">
                    {num_wrong} of {total} fields were incorrect. Fix your
                    entry and re-check, or reveal the corrected label anyway.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_a, _ = st.columns([2, 5])
    with col_a:
        if st.button(
            "Reveal Label Preview",
            type="secondary",
            use_container_width=True,
            key="reveal_label_btn",
        ):
            st.session_state.label_revealed = True
            st.rerun()


def _build_label_inner_html(case: dict, feedback: dict) -> tuple[str, int]:
    """Build the inner HTML of the label (content inside .label-paper).

    Returns (inner_html, num_corrections). The HTML is a single flat
    string with NO embedded newlines or leading whitespace, so it can
    be safely interpolated into other markdown calls without triggering
    CommonMark code-block parsing.
    """
    expected = case["expected"]
    patient = case["patient"]
    prescriber = case["prescriber"]
    corrected_fields: list[str] = []

    def resolve(field_key: str, corrected_value):
        res = feedback.get(field_key, {})
        if res.get("correct"):
            return str(res["user"]), False
        corrected_fields.append(FIELD_LABELS.get(field_key, field_key))
        return str(corrected_value), True

    drug_val, drug_corr = resolve("drug_name", expected["drug_name"])
    strength_val, strength_corr = resolve("strength", expected["strength"])
    sig_val, sig_corr = resolve("sig", expected.get("sig_english", ""))
    qty_val, qty_corr = resolve("quantity", expected["quantity"])
    days_val, days_corr = resolve("days_supply", expected["days_supply"])
    refills_val, refills_corr = resolve("refills", expected["refills"])

    def mark(was_corrected: bool) -> str:
        return '<span class="correction-mark">*</span>' if was_corrected else ""

    digits = "".join(c for c in case["case_id"] if c.isdigit()) or "0"
    rx_num = f"Rx# {int(digits):07d}"
    fill_date = date.today().strftime("%m/%d/%Y")

    inner_html = (
        '<div class="label-pharmacy-row">'
        '<div class="label-pharmacy-name">TRAINING PHARMACY</div>'
        f'<div class="label-rx-num">{rx_num}</div>'
        '</div>'
        '<div class="label-pharmacy-addr">'
        '7420 Mockingbird Lane &middot; Practice City, TX 78001 &middot; (555) 214-8096'
        '</div>'
        '<div class="label-patient-row">'
        f'<span class="pt-name">{html.escape(patient["name"])}</span>'
        f'<span class="fill-date">Filled: {fill_date}</span>'
        '</div>'
        '<div class="label-drug-line">'
        f'{html.escape(drug_val)}{mark(drug_corr)} '
        f'{html.escape(strength_val)}{mark(strength_corr)}'
        '</div>'
        '<div class="label-sig-block">'
        f'{html.escape(sig_val)}{mark(sig_corr)}'
        '</div>'
        '<div class="label-fill-row">'
        '<span>'
        '<span class="fg-label">Qty:</span> '
        f'<span class="fg-value">{html.escape(str(qty_val))}{mark(qty_corr)}</span>'
        '</span>'
        '<span>'
        '<span class="fg-label">Days supply:</span> '
        f'<span class="fg-value">{html.escape(str(days_val))}{mark(days_corr)}</span>'
        '</span>'
        '<span>'
        '<span class="fg-label">Refills:</span> '
        f'<span class="fg-value">{html.escape(str(refills_val))}{mark(refills_corr)}</span>'
        '</span>'
        '</div>'
        '<div class="label-prescriber-row">'
        '<span class="pr-label">Prescriber:</span> '
        f'<span class="pr-name">{html.escape(prescriber["name"])}</span>'
        '</div>'
        '<div class="label-footer-stamp">'
        'Training Only &middot; Not for Dispensing'
        '</div>'
    )
    return inner_html, len(corrected_fields)


def _build_label_banner_html(num_corrections: int) -> str:
    """Build the 'training only' banner above the label."""
    if num_corrections == 0:
        return (
            '<div class="label-warning">'
            'Training preview only &middot; not for dispensing'
            '</div>'
        )
    plural = "s" if num_corrections != 1 else ""
    return (
        f'<div class="label-warning corrections">'
        f'{num_corrections} field{plural} shown corrected (marked '
        f'<span class="correction-mark">*</span>) &middot; '
        f'training preview only &middot; not for dispensing'
        f'</div>'
    )


def render_label_preview(case: dict, feedback: dict) -> None:
    """Label preview card + single Download Label PDF action.

    The card itself shows the on-screen label mockup so the user can read
    every field before deciding to download. No embedded iframe (Chrome
    blocks data:application/pdf iframes); just a clean download button
    that streams the same reportlab-generated PDF to the user's machine,
    where their PDF viewer handles printing and saving.
    """
    # ---- Label card (on-screen mockup, .label-print-source for @media print) ----
    inner_html, num_corrections = _build_label_inner_html(case, feedback)
    banner = _build_label_banner_html(num_corrections)
    label_html = (
        '<div class="section-card label-print-source">'
        '<div class="section-label">Label Preview</div>'
        + banner
        + '<div class="print-page-mockup">'
        + '<div class="label-paper">'
        + inner_html
        + '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(label_html, unsafe_allow_html=True)

    # ---- Download Label PDF action row ----
    col_btn, col_hint = st.columns([2, 5])
    with col_btn:
        if REPORTLAB_AVAILABLE:
            try:
                pdf_bytes = build_label_pdf(case, feedback)
                st.download_button(
                    label="Download Label PDF",
                    data=pdf_bytes,
                    file_name=f"training_label_{case['case_id']}.pdf",
                    mime="application/pdf",
                    type="secondary",
                    key=f"download_label_pdf_{case['case_id']}",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"PDF generation failed: {e}")
        else:
            st.caption(
                "Install reportlab to enable PDF download: `pip install reportlab`"
            )
    with col_hint:
        st.markdown(
            '<div class="print-hint-text" style="padding-top: 8px;">'
            'Open the downloaded PDF to print or save this training label. '
            'Training only &middot; not for dispensing.'
            '</div>',
            unsafe_allow_html=True,
        )


def render_footer() -> None:
    st.markdown('<div class="footer-row"></div>', unsafe_allow_html=True)
    _, _, col_btn = st.columns([6, 2, 1.5])
    with col_btn:
        if st.button("Start New Session", type="secondary", use_container_width=True):
            reset_session()
            st.rerun()


# =====================================================================
# Top navigation
# =====================================================================

def render_top_nav() -> None:
    """Three large clickable nav cards across the top.

    Each card is a Streamlit button whose label uses markdown so the
    module number, title, and description render as distinct lines inside
    one large click target. A hidden marker div before each button gives
    CSS a :has() hook to style the active card green and the inactive
    cards white. A "Training modules" header above the row frames the
    three as a curriculum (practiced in any order). Clicking a card sets
    session_state.active_section and reruns.
    """
    nav_items = [
        ("Prescription Entry",
         "Enter the seven Rx fields and translate SIG shorthand to plain English."),
        ("Drug Knowledge",
         "Review brand and generic names, dosage forms, and LASA pairs."),
        ("Workflow Scenarios",
         "Decide on refill, allergy, DUR, and insurance situations."),
    ]

    active = st.session_state.get("active_section", "Prescription Entry")

    # Curriculum framing: a labeled header so the row reads as training
    # modules rather than browser tabs.
    st.markdown(
        '<div class="nav-header">'
        '<span class="section-label">Training modules</span>'
        '<span class="nav-header-hint">Pick a module &mdash; practice in any order.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3, gap="small")

    for idx, (col, (title, desc)) in enumerate(zip(cols, nav_items), start=1):
        with col:
            state_class = "nav-active" if title == active else "nav-inactive"
            st.markdown(
                f'<div class="nav-marker {state_class}"></div>',
                unsafe_allow_html=True,
            )
            # Two-space-then-newline is markdown's hard line break; renders as <br>.
            # The zero-padded module index reads as a curriculum step.
            label = f"**{idx:02d} · {title}**  \n{desc}"
            btn_key = f"nav_{title.lower().replace(' ', '_')}"
            if st.button(label, key=btn_key, use_container_width=True):
                st.session_state.active_section = title
                st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)


# =====================================================================
# Section: Prescription Entry
# Wraps the existing simulator workflow. No logic change.
# =====================================================================

def show_example() -> None:
    """The on_click callback for the See Example button.

    Sets feedback + flags only. Does NOT write to widget session_state keys
    (in_drug, in_strength, etc.) because those writes fail to propagate for
    anonymous Streamlit Cloud sessions. Instead, render_entry_form renders
    different widgets when example_mode is True, with the canonical answers
    passed directly via the value= parameter (which bypasses session_state
    entirely and always works).
    """
    case = st.session_state.current_case
    expected = case["expected"]

    user_answers = {
        "drug_name": expected["drug_name"],
        "strength": expected["strength"],
        "quantity": expected["quantity"],
        "sig": expected.get("sig_english", ""),
        "days_supply": expected["days_supply"],
        "refills": expected["refills"],
        "daw": expected["daw"],
    }
    results = checker.check_all(user_answers, expected, case.get("extras"))

    st.session_state.last_feedback = results
    st.session_state.submitted = True
    st.session_state.label_revealed = False
    st.session_state.example_mode = True


def render_prescription_entry_section() -> None:
    """The prescription-entry simulator workflow (was the body of main)."""
    case = st.session_state.current_case

    st.markdown(
        '<div class="workflow-hint">'
        'Read the prescription, enter the required fields, then check your entry.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Row 1: prescription source document
    render_prescription_card(case)

    # Row 1b: DUR / safety review
    render_safety_warnings(get_safety_warnings(case))

    # Row 1c: optional SIG decoder
    render_sig_help()

    # Row 2: patient + prescriber
    render_patient_prescriber(case)
    st.caption(
        "All prescriber identifiers (NPI / DEA) are fictional and used "
        "for training only."
    )

    # Row 3: entry form
    submitted_answers = render_entry_form()
    if submitted_answers is not None:
        handle_submission(submitted_answers)
        st.rerun()

    # Rows 4+: post-submission output. Two paths so the user does not
    # have to scroll past a long validation section to reach the label.
    if st.session_state.submitted:
        feedback = st.session_state.last_feedback
        total = len(feedback)
        num_wrong = sum(1 for r in feedback.values() if not r["correct"])
        all_correct = num_wrong == 0
        gate_threshold = 4

        if all_correct:
            render_success_card(total, example_mode=st.session_state.example_mode)
            render_feedback_report(case, feedback)
            render_label_preview(case, feedback)
        else:
            render_feedback_report(case, feedback)
            if num_wrong >= gate_threshold and not st.session_state.label_revealed:
                render_label_locked(num_wrong, total)
            else:
                render_label_preview(case, feedback)

    # Missed-fields panel (only when populated)
    render_missed_fields_panel()

    # Footer with Start New Session button - lives at the bottom of
    # Prescription Entry only, not on other sections.
    render_footer()


# =====================================================================
# Section: Drug Knowledge
# Reads the drug from the current Prescription Entry case so switching
# cases in the simulator updates what this section shows.
# =====================================================================

def _drug_study_card_html(info: dict) -> str:
    """Build one compact study card for the Drug Knowledge section.

    Shows generic name, brand (when useful), drug class, dosage forms, a
    short technician note, and a LASA / safety line when one applies.
    Reuses the existing .drug-info-* pill / body / lasa styles.
    """
    if info["brand_examples"]:
        brand = "Brand: " + ", ".join(info["brand_examples"])
    else:
        brand = "Generic only"

    forms_html = "".join(
        f'<span class="drug-info-pill">{html.escape(form)}</span>'
        for form in info["dosage_forms"]
    )

    lasa = info.get("lasa")
    lasa_html = (
        '<div class="drug-info-section-label">Safety &middot; LASA</div>'
        f'<div class="lasa-warning">{html.escape(lasa)}</div>'
    ) if lasa else ""

    return (
        '<div class="section-card drug-study-card">'
        '<div class="drug-study-head">'
        f'<span class="drug-study-generic">{html.escape(info["generic"])}</span>'
        f'<span class="drug-study-brand">{html.escape(brand)}</span>'
        '</div>'
        f'<div class="drug-study-class">{html.escape(info["category"])}</div>'
        '<div class="drug-info-section-label">Dosage forms</div>'
        f'<div class="drug-study-pills">{forms_html}</div>'
        '<div class="drug-info-section-label">Technician note</div>'
        f'<div class="drug-info-body">{html.escape(info["counseling"])}</div>'
        + lasa_html
        + '</div>'
    )


def _category_for_drug(drug_key: str) -> str:
    """Return the category id that contains drug_key, else the first category."""
    for category in DRUG_CATEGORIES:
        if drug_key in category["drugs"]:
            return category["id"]
    return DRUG_CATEGORIES[0]["id"]


def render_drug_knowledge_section() -> None:
    """Categorized drug study cards for pharmacy technician review.

    A row of category buttons filters DRUG_INFO down to a curated,
    beginner-friendly set per therapeutic area (hypertension, antibiotics,
    diabetes, pain/fever, allergy/asthma, topical). Each drug renders as a
    compact study card via _drug_study_card_html. Training / reference
    content only; the disclaimer banner stays in view. Category selection
    is independent of the Prescription Entry flow.
    """
    # ---- Disclaimer banner ----
    st.markdown(
        '<div class="info-disclaimer">'
        '<strong>Training reference only</strong> &middot; not clinical guidance. '
        'High-yield study set based on common pharmacy technician patterns; '
        'not an official exam list.'
        '</div>',
        unsafe_allow_html=True,
    )

    valid_ids = {c["id"] for c in DRUG_CATEGORIES}
    active_id = st.session_state.get("drug_category", DRUG_CATEGORIES[0]["id"])
    if active_id not in valid_ids:
        active_id = DRUG_CATEGORIES[0]["id"]

    # ---- Category selector ----
    st.markdown(
        '<div class="section-label">Study categories</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(DRUG_CATEGORIES))
    for col, category in zip(cols, DRUG_CATEGORIES):
        with col:
            btn_type = "primary" if category["id"] == active_id else "secondary"
            if st.button(
                category["label"],
                type=btn_type,
                use_container_width=True,
                key=f"drugcat_{category['id']}",
            ):
                st.session_state.drug_category = category["id"]
                st.rerun()

    active = next(c for c in DRUG_CATEGORIES if c["id"] == active_id)
    drugs = [DRUG_INFO[key] for key in active["drugs"] if key in DRUG_INFO]
    count = len(drugs)
    plural = "s" if count != 1 else ""

    # ---- Category header + blurb ----
    st.markdown(
        f'<div class="drug-category-bar">'
        f'<span class="drug-category-title">{html.escape(active["label"])}</span>'
        f'<span class="drug-category-count">{count} drug{plural}</span>'
        f'</div>'
        f'<div class="drug-category-blurb">{html.escape(active["blurb"])}</div>',
        unsafe_allow_html=True,
    )

    # ---- Study cards (two per row) ----
    for i in range(0, count, 2):
        left, right = st.columns(2)
        with left:
            st.markdown(_drug_study_card_html(drugs[i]), unsafe_allow_html=True)
        if i + 1 < count:
            with right:
                st.markdown(
                    _drug_study_card_html(drugs[i + 1]),
                    unsafe_allow_html=True,
                )


# =====================================================================
# Section: Workflow Scenarios
# Decision-making prototype with fictional pharmacy situations.
# =====================================================================

def render_workflow_scenarios_section() -> None:
    """Pick a scenario, read the situation, choose an action, get feedback.

    Scoring: a scenario is counted as 'attempted' the first time its
    Submit is clicked; if that first answer matched best_index, it is
    counted as 'correct'. Try Again does not retroactively change the
    score, and switching scenarios does not affect it either. The score
    is fully separate from Prescription Entry stats.
    """
    st.markdown(
        '<div class="info-disclaimer">'
        '<strong>Training reference only</strong> &middot; not medical or legal '
        'advice. All scenarios use fictional patients and prescriptions.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Scenario picker (rows of up to 4 so longer titles stay readable) ----
    active_id = st.session_state.get("scenario_id", SCENARIOS[0]["id"])
    picker_cols = 4
    for row_start in range(0, len(SCENARIOS), picker_cols):
        cols = st.columns(picker_cols)
        for col, scen in zip(cols, SCENARIOS[row_start:row_start + picker_cols]):
            with col:
                btn_type = "primary" if scen["id"] == active_id else "secondary"
                if st.button(
                    scen["title"],
                    type=btn_type,
                    use_container_width=True,
                    key=f"scen_pick_{scen['id']}",
                ):
                    if st.session_state.get("scenario_id") != scen["id"]:
                        st.session_state.scenario_id = scen["id"]
                        st.session_state.scenario_submitted = False
                        st.session_state.scenario_choice = None
                    st.rerun()

    scenario = next(s for s in SCENARIOS if s["id"] == active_id)
    scenario_index = next(
        i for i, s in enumerate(SCENARIOS) if s["id"] == active_id
    )

    # ---- Progress + score row ----
    attempted = len(st.session_state.scenario_attempted_ids)
    correct = len(st.session_state.scenario_correct_ids)
    st.markdown(
        f'<div class="scenario-progress-row">'
        f'<span class="scen-progress-text">'
        f'Scenario {scenario_index + 1} of {len(SCENARIOS)}'
        f'</span>'
        f'<span class="scenario-score">Scenario score: {correct}/{attempted}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---- Active scenario card ----
    with st.container(border=True):
        # Border marker (see .card-border-anchor rule in CUSTOM_CSS)
        st.markdown(
            '<div class="card-border-anchor"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="section-label">Scenario &middot; '
            f'{html.escape(scenario["title"])}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="scenario-situation">{html.escape(scenario["situation"])}</div>',
            unsafe_allow_html=True,
        )

        # Patient / case context details
        if scenario.get("context"):
            context_rows = "".join(
                '<div class="data-row">'
                f'<span class="label">{html.escape(str(label))}</span>'
                f'<span class="value">{html.escape(str(value))}</span>'
                '</div>'
                for label, value in scenario["context"]
            )
            st.markdown(
                '<div class="scenario-context">'
                '<div class="scenario-context-label">Case details</div>'
                f'<div class="data-grid">{context_rows}</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="rx-mini-label" style="margin-top: 14px; '
            'margin-bottom: 6px;">What would you do?</div>',
            unsafe_allow_html=True,
        )

        selected_index = st.radio(
            "Options",
            options=list(range(len(scenario["options"]))),
            format_func=lambda i: scenario["options"][i],
            label_visibility="collapsed",
            key=f"radio_{scenario['id']}",
        )

        submitted = (
            st.session_state.get("scenario_submitted", False)
            and st.session_state.get("scenario_id") == scenario["id"]
        )

        col_btn, _ = st.columns([1.6, 5])
        with col_btn:
            if not submitted:
                if st.button(
                    "Submit answer",
                    type="primary",
                    use_container_width=True,
                    key=f"scen_submit_{scenario['id']}",
                ):
                    # Score only the first attempt per scenario
                    if scenario["id"] not in st.session_state.scenario_attempted_ids:
                        st.session_state.scenario_attempted_ids.add(scenario["id"])
                        if selected_index == scenario["best_index"]:
                            st.session_state.scenario_correct_ids.add(scenario["id"])
                    st.session_state.scenario_id = scenario["id"]
                    st.session_state.scenario_choice = selected_index
                    st.session_state.scenario_submitted = True
                    st.rerun()
            else:
                if st.button(
                    "Try again",
                    type="secondary",
                    use_container_width=True,
                    key=f"scen_retry_{scenario['id']}",
                ):
                    st.session_state.scenario_submitted = False
                    st.session_state.scenario_choice = None
                    st.rerun()

    # ---- Feedback + Next Scenario after submission ----
    if submitted:
        user_choice = st.session_state.scenario_choice
        best = scenario["best_index"]
        is_correct = user_choice == best
        best_text = scenario["options"][best]

        if is_correct:
            st.markdown(
                '<div class="scenario-feedback-correct">'
                '<div class="scenario-feedback-title">Best action selected.</div>'
                '<div class="scenario-feedback-body">'
                f'<strong>Why:</strong> {html.escape(scenario["explanation"])}'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            user_pick_text = (
                scenario["options"][user_choice]
                if user_choice is not None
                else "(no choice)"
            )
            st.markdown(
                '<div class="scenario-feedback-incorrect">'
                '<div class="scenario-feedback-title">Not the best action.</div>'
                '<div class="scenario-feedback-body">'
                f'<strong>Best action:</strong> {html.escape(best_text)}<br><br>'
                f'<strong>Why:</strong> {html.escape(scenario["explanation"])}'
                '</div>'
                '<div class="scenario-user-pick">'
                f'You chose: {html.escape(user_pick_text)}'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        # Pharmacist escalation reminder (shown after both correct and incorrect)
        if scenario.get("escalation"):
            st.markdown(
                '<div class="scenario-escalation">'
                '<span class="esc-label">When to escalate to the pharmacist</span>'
                f'{html.escape(scenario["escalation"])}'
                '</div>',
                unsafe_allow_html=True,
            )

        # Next Scenario advance button (wraps around)
        col_next, _ = st.columns([1.6, 5])
        with col_next:
            if st.button(
                "Next Scenario \u2192",
                type="primary",
                use_container_width=True,
                key="scen_advance",
            ):
                next_idx = (scenario_index + 1) % len(SCENARIOS)
                st.session_state.scenario_id = SCENARIOS[next_idx]["id"]
                st.session_state.scenario_submitted = False
                st.session_state.scenario_choice = None
                st.rerun()


# =====================================================================
# Main
# =====================================================================

def main() -> None:
    st.set_page_config(
        page_title="Rx Entry Simulator",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    init_state()

    # ---- Top: header with title and stat chips ----
    render_header()

    # ---- Top navigation ----
    render_top_nav()

    # ---- Section dispatch ----
    active = st.session_state.active_section
    if active == "Drug Knowledge":
        render_drug_knowledge_section()
    elif active == "Workflow Scenarios":
        render_workflow_scenarios_section()
    else:
        # Default and "Prescription Entry" - the main simulator.
        # This section renders its own footer (Start New Session) at the
        # bottom; other sections deliberately do not show that button.
        render_prescription_entry_section()


if __name__ == "__main__":
    main()
