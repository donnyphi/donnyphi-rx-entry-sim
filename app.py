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

INPUT_KEYS = [
    "in_drug",
    "in_strength",
    "in_quantity",
    "in_sig",
    "in_days",
    "in_refills",
    "in_daw",
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

.app-title-block h1 {
    font-size: 1.35rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.01em;
}

.app-title-block .subtitle {
    font-size: 0.82rem;
    color: #6b7280;
    margin-top: 3px;
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
.chip-value { font-weight: 600; color: #0f766e; }
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
    font-size: 1.05rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 10px;
}

.rx-sig-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
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
    font-size: 0.9rem;
    color: #0f766e;
    background: #ecfdf5;
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid #d1fae5;
    display: inline-block;
}

.rx-tags {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
    padding-top: 10px;
    border-top: 1px solid #f3f4f6;
}

.rx-tag { display: flex; flex-direction: column; gap: 2px; }
.rx-tag-value { font-size: 0.95rem; font-weight: 600; color: #111827; }
.rx-tag-value.muted { color: #9ca3af; font-weight: 500; }

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

.stTextInput label,
.stTextArea label {
    font-size: 0.8rem !important;
    color: #374151 !important;
    font-weight: 500 !important;
    padding-bottom: 2px !important;
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

/* ---------- Print / Save Preview action row inside the label card ---------- */
.print-action-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin: 16px auto 0;
    padding-top: 14px;
    border-top: 1px solid #f3f4f6;
    max-width: 620px;
    flex-wrap: wrap;
}

.print-action-btn {
    background-color: #0f766e;
    color: white;
    border: 1px solid #0f766e;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 0.88rem;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: background-color 0.12s ease, border-color 0.12s ease;
    white-space: nowrap;
}

.print-action-btn:hover {
    background-color: #115e59;
    border-color: #115e59;
}

.print-action-btn:active {
    background-color: #134e4a;
}

.print-hint-text {
    flex: 1;
    min-width: 260px;
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
    .label-print-source .section-label,
    .label-print-source .print-action-row {
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


def advance_case() -> None:
    """Mark current case complete, load a new one, clear inputs and feedback.

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
    for k in INPUT_KEYS:
        if k in st.session_state:
            del st.session_state[k]


def try_again() -> None:
    """Return to editing the same case without advancing.

    Inputs are intentionally NOT cleared so the user can fix what was wrong.
    Stats and missed-fields entries from the prior submission remain (each
    Check Entry counts as a real attempt), but handle_submission dedupes
    missed fields per case so retrying does not pile duplicates. Exits
    example mode if it was active.
    """
    st.session_state.submitted = False
    st.session_state.last_feedback = {}
    st.session_state.label_revealed = False
    st.session_state.example_mode = False


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


def show_example() -> None:
    """Pre-fill the form with the correct answers and mark the case as
    submitted in example mode.

    For onboarding: lets a new user see what a completed entry looks like
    plus the full validation + label preview output, without affecting
    stats or the missed-fields list.
    """
    case = st.session_state.current_case
    expected = case["expected"]

    # Pre-populate the seven input session keys so the form shows them on rerun
    st.session_state["in_drug"] = expected["drug_name"]
    st.session_state["in_strength"] = expected["strength"]
    st.session_state["in_quantity"] = str(expected["quantity"])
    st.session_state["in_sig"] = expected.get("sig_english", "")
    st.session_state["in_days"] = str(expected["days_supply"])
    st.session_state["in_refills"] = str(expected["refills"])
    st.session_state["in_daw"] = str(expected["daw"])

    # Run the checker on those (perfect) answers to produce a feedback dict
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
    # Stats and missed-fields queue are intentionally NOT touched.


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
        "123 Sample Street \u00b7 Sample City, TX 78000 \u00b7 (555) 000-0000",
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
    correct, total = overall_accuracy()
    if total:
        acc_pct = correct / total * 100
        acc_str = f"{acc_pct:.0f}%"
        acc_class = "chip" if acc_pct >= 70 else "chip accuracy-low"
    else:
        acc_str = "—"
        acc_class = "chip"

    review_count = len(st.session_state.review_queue)
    missed_class = "chip missed" + ("" if review_count else " empty")

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title-block">
                <h1>Rx Entry Simulator</h1>
                <div class="subtitle">Pharmacy technician training tool</div>
            </div>
            <div class="stat-chips">
                <span class="chip">
                    <span class="chip-label">Completed</span>
                    <span class="chip-value">{st.session_state.cases_completed}</span>
                </span>
                <span class="{acc_class}">
                    <span class="chip-label">Accuracy</span>
                    <span class="chip-value">{acc_str}</span>
                </span>
                <span class="{missed_class}">
                    <span class="chip-label">Missed fields</span>
                    <span class="chip-value">{review_count}</span>
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
        # Header row
        st.markdown(
            '<div class="rx-header-row">'
            f'<div class="section-label">Prescription &middot; {case_id_safe}</div>'
            f'<div class="rx-meta">Date written:<span class="meta-value">{date_safe}</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Drug line + See Example button on the far right of the same row
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
            if st.button(
                "See Example",
                type="secondary",
                key="see_example_btn",
                use_container_width=True,
                disabled=st.session_state.get("submitted", False),
            ):
                show_example()
                st.rerun()

        # Sig row
        st.markdown(
            '<div class="rx-sig-row">'
            '<span class="rx-mini-label">Sig</span>'
            f'<span class="rx-sig">{sig_safe}</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Tags row
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


def render_entry_form() -> dict | None:
    """Render the entry form. Returns user answers if Check Entry was clicked."""
    with st.container(border=True):
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
            drug = st.text_input("Drug name", key="in_drug", placeholder="Generic name")
        with c2:
            strength = st.text_input(
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
            quantity = st.text_input("Quantity", key="in_quantity", placeholder="0")
        with c4:
            days = st.text_input("Days supply", key="in_days", placeholder="0")
        with c5:
            refills = st.text_input("Refills", key="in_refills", placeholder="0")
        with c6:
            daw = st.text_input("DAW code", key="in_daw", placeholder="0")

        # Patient Directions
        st.markdown(
            '<div class="form-group-label">Patient Directions (SIG)</div>',
            unsafe_allow_html=True,
        )
        sig = st.text_area(
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

    if submit:
        return {
            "drug_name": drug,
            "strength": strength,
            "quantity": quantity,
            "sig": sig,
            "days_supply": days,
            "refills": refills,
            "daw": daw,
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
        '123 Sample Street &middot; Sample City, TX 78000 &middot; (555) 000-0000'
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
    """Single label preview using the large print-page style.

    Carries .label-print-source so Ctrl+P / Cmd+P prints just this card.
    The Print / Save Preview button uses window.print() so a single click
    does the same thing. The Download Label PDF button (below the card)
    uses reportlab to produce a one-page PDF for save/share.
    """
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
        '<div class="print-action-row">'
        '<button class="print-action-btn" onclick="window.print()" type="button">'
        'Print / Save Preview'
        '</button>'
        '<div class="print-hint-text">'
        'Use <strong>Ctrl+P</strong> (or <strong>Cmd+P</strong> on Mac) or your '
        "browser's print option to save or print this training label. "
        'Training only &middot; not for dispensing.'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(label_html, unsafe_allow_html=True)

    # Download Label PDF button - separate Streamlit element below the card.
    # The PDF is regenerated on each rerun, which is cheap (small one-page doc).
    col_dl, _ = st.columns([2, 5])
    with col_dl:
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


def render_footer() -> None:
    st.markdown('<div class="footer-row"></div>', unsafe_allow_html=True)
    _, _, col_btn = st.columns([6, 2, 1.5])
    with col_btn:
        if st.button("Start New Session", type="secondary", use_container_width=True):
            reset_session()
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
    case = st.session_state.current_case

    # ---- Top: header with title and stat chips ----
    render_header()

    # Workflow hint just below the header
    st.markdown(
        '<div class="workflow-hint">'
        'Read the prescription, enter the required fields, then check your entry.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Workspace ----
    # Row 1: prescription across the top (the source document)
    render_prescription_card(case)

    # Row 1b: optional SIG decoder right below the prescription
    render_sig_help()

    # Row 2: patient + prescriber side by side
    render_patient_prescriber(case)

    # Row 3: entry form - the main work surface
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
            # Compact success path: success card -> label -> optional details expander.
            render_success_card(total, example_mode=st.session_state.example_mode)
            render_label_preview(case, feedback)
            render_feedback_details_expander(feedback)
        else:
            # Mistakes path: detailed feedback first, then the gated label.
            render_feedback()
            if num_wrong >= gate_threshold and not st.session_state.label_revealed:
                render_label_locked(num_wrong, total)
            else:
                render_label_preview(case, feedback)

    # Missed-fields panel (only when populated)
    render_missed_fields_panel()

    # Footer with reset
    render_footer()


if __name__ == "__main__":
    main()
