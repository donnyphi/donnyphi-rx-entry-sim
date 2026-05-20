"""Pharmacy Technician Prescription Entry Simulator.

Streamlit UI layer. This is the only module that imports streamlit.
All validation lives in checker.py, all stats live in tracker.py,
all case data lives in cases.py.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import html

import streamlit as st

import cases
import checker
import tracker


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
.chip.review .chip-value         { color: #b45309; }
.chip.review.empty .chip-value   { color: #4b5563; }
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

/* ---------- Review queue panel ---------- */
.review-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.review-row {
    display: flex;
    gap: 10px;
    font-size: 0.82rem;
    color: #374151;
    padding: 4px 0;
    border-bottom: 1px dashed #f3f4f6;
}

.review-row:last-child { border-bottom: none; }

.review-row .case-id {
    color: #9ca3af;
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.78rem;
    min-width: 60px;
}

.review-row .field {
    font-weight: 600;
    color: #111827;
    min-width: 110px;
}

.review-row .expected {
    color: #4b5563;
}

/* ---------- Footer ---------- */
.footer-row {
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid #e5e7eb;
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


def advance_case() -> None:
    """Mark current case complete, load a new one, clear inputs and feedback."""
    current_id = st.session_state.current_case["case_id"]
    st.session_state.seen_case_ids.append(current_id)
    st.session_state.cases_completed += 1
    st.session_state.current_case = cases.get_random_case(
        st.session_state.seen_case_ids
    )
    st.session_state.submitted = False
    st.session_state.last_feedback = {}
    for k in INPUT_KEYS:
        if k in st.session_state:
            del st.session_state[k]


def reset_session() -> None:
    """Wipe all state and start a fresh session."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_state()


def handle_submission(user_answers: dict) -> None:
    """Run the checker, update stats, append misses to the review queue."""
    case = st.session_state.current_case
    results = checker.check_all(user_answers, case["expected"], case.get("extras"))
    st.session_state.last_feedback = results
    st.session_state.submitted = True
    tracker.record_results(st.session_state.stats, results)
    tracker.add_misses_to_review(
        st.session_state.review_queue,
        case["case_id"],
        results,
    )


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
    review_class = "chip review" + ("" if review_count else " empty")

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title-block">
                <h1>Rx Entry Simulator</h1>
                <div class="subtitle">Pharmacy technician training tool</div>
            </div>
            <div class="stat-chips">
                <span class="chip">
                    <span class="chip-label">Cases</span>
                    <span class="chip-value">{st.session_state.cases_completed}</span>
                </span>
                <span class="{acc_class}">
                    <span class="chip-label">Accuracy</span>
                    <span class="chip-value">{acc_str}</span>
                </span>
                <span class="{review_class}">
                    <span class="chip-label">Review queue</span>
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

    st.markdown(
        f"""
        <div class="section-card">
            <div class="rx-header-row">
                <div class="section-label">Prescription &middot; {case_id_safe}</div>
                <div class="rx-meta">
                    Date written:<span class="meta-value">{date_safe}</span>
                </div>
            </div>
            <div class="rx-drug">{drug_line_safe}</div>
            <div class="rx-sig-row">
                <span class="rx-mini-label">Sig</span>
                <span class="rx-sig">{sig_safe}</span>
            </div>
            <div class="rx-tags">
                <div class="rx-tag">
                    <span class="rx-mini-label">Disp</span>
                    <span class="{disp_class}">{disp_value}</span>
                </div>
                <div class="rx-tag">
                    <span class="rx-mini-label">Refills</span>
                    <span class="rx-tag-value">{refills_value}</span>
                </div>
                <div class="rx-tag">
                    <span class="rx-mini-label">DAW</span>
                    <span class="rx-tag-value">{daw_value}</span>
                </div>
            </div>
        </div>
        """,
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
        col_a, col_b, _ = st.columns([1.2, 1.2, 4])
        with col_a:
            submit = st.button(
                "Check Entry",
                type="primary",
                disabled=st.session_state.submitted,
                use_container_width=True,
            )
        with col_b:
            next_case = st.button(
                "Next Case",
                type="secondary",
                disabled=not st.session_state.submitted,
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
    if next_case:
        advance_case()
        st.rerun()
    return None


def render_feedback() -> None:
    if not st.session_state.submitted:
        return

    feedback = st.session_state.last_feedback
    correct_count = sum(1 for r in feedback.values() if r["correct"])
    total = len(feedback)

    if correct_count == total:
        banner = (
            f'<div class="feedback-summary all-correct">'
            f'<span class="badge">{correct_count}/{total}</span>'
            f'All fields correct. Click Next Case to continue.'
            f'</div>'
        )
    else:
        banner = (
            f'<div class="feedback-summary partial">'
            f'<span class="badge">{correct_count}/{total}</span>'
            f'Some fields need review. See details below.'
            f'</div>'
        )

    items_html = ""
    for field, res in feedback.items():
        label = FIELD_LABELS.get(field, field)
        css_class = "correct" if res["correct"] else "incorrect"
        status_text = "Correct" if res["correct"] else "Incorrect"

        detail_html = ""
        if not res["correct"]:
            user_safe = html.escape(str(res["user"])) if res["user"] != "" else "(empty)"
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

    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-label">Validation Results</div>
            {banner}
            {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_review_queue_panel() -> None:
    """Compact review queue summary, shown only when there are misses."""
    queue = st.session_state.review_queue
    if not queue:
        return

    recent = queue[-8:][::-1]  # last 8, newest first
    rows_html = ""
    for item in recent:
        rows_html += (
            f'<div class="review-row">'
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
            <div class="section-label">Review Queue &middot; recent misses</div>
            <div class="review-list">{rows_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown('<div class="footer-row"></div>', unsafe_allow_html=True)
    _, _, col_btn = st.columns([6, 2, 1.5])
    with col_btn:
        if st.button("Reset session", type="secondary", use_container_width=True):
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

    # ---- Workspace ----
    # Row 1: prescription across the top (the source document)
    render_prescription_card(case)

    # Row 2: patient + prescriber side by side
    render_patient_prescriber(case)

    # Row 3: entry form - the main work surface
    submitted_answers = render_entry_form()
    if submitted_answers is not None:
        handle_submission(submitted_answers)
        st.rerun()

    # Row 4: feedback (only after a submission)
    render_feedback()

    # Row 5: review queue (only when populated)
    render_review_queue_panel()

    # Footer with reset
    render_footer()


if __name__ == "__main__":
    main()
