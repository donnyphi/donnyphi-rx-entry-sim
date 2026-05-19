"""Pharmacy Technician Prescription Entry Simulator.

Streamlit UI layer. This is the only module that imports streamlit.
Validation lives in checker.py, stats and review-queue logic live in
tracker.py, and case data lives in cases.py.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

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


# ---------- state ----------

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


# ---------- render functions ----------

def render_prescription(case: dict) -> None:
    st.subheader("Prescription")
    rx = case["rx_text"]
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**Drug:** {rx['drug_line']}")
            st.markdown(f"**Sig:** `{rx['sig_shorthand']}`")
        with c2:
            st.markdown(f"**Date written:** {rx['date_written']}")
            if rx.get("quantity_text"):
                st.markdown(rx["quantity_text"])
            st.markdown(rx["refills_text"])
            st.markdown(rx["daw_text"])


def render_patient(case: dict) -> None:
    st.subheader("Patient")
    p = case["patient"]
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Name:** {p['name']}")
            st.markdown(f"**DOB:** {p['dob']}")
            st.markdown(f"**MRN:** {p['mrn']}")
        with c2:
            st.markdown(f"**Address:** {p['address']}")
            st.markdown(f"**Allergies:** {', '.join(p['allergies'])}")


def render_prescriber(case: dict) -> None:
    st.subheader("Prescriber")
    pr = case["prescriber"]
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Name:** {pr['name']}")
            st.markdown(f"**NPI:** {pr['npi']}")
        with c2:
            st.markdown(f"**DEA:** {pr['dea']}")
            st.markdown(f"**Address:** {pr['address']}")


def render_entry_form() -> dict | None:
    """Render the entry form. Returns user answers if Check Entry was clicked."""
    st.subheader("Entry Form")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            drug = st.text_input("Drug name", key="in_drug")
            strength = st.text_input(
                "Strength (with unit)",
                key="in_strength",
                placeholder="e.g. 500 mg",
            )
            quantity = st.text_input(
                "Quantity",
                key="in_quantity",
                placeholder="whole number",
            )
            sig = st.text_area(
                "SIG in plain English",
                key="in_sig",
                height=110,
                placeholder=(
                    "Translate the shorthand into English. "
                    "Include verb, quantity, dosage form, route, "
                    "frequency, and duration when applicable."
                ),
            )
        with c2:
            days = st.text_input(
                "Days supply",
                key="in_days",
                placeholder="whole number",
            )
            refills = st.text_input(
                "Refills",
                key="in_refills",
                placeholder="whole number",
            )
            daw = st.text_input(
                "DAW code (0-9)",
                key="in_daw",
                placeholder="0",
            )

        col_a, col_b, _ = st.columns([1, 1, 4])
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
    st.subheader("Feedback")
    correct_count = sum(1 for r in feedback.values() if r["correct"])
    total = len(feedback)

    with st.container(border=True):
        if correct_count == total:
            st.success(f"All {total} fields correct. Click Next Case to continue.")
        else:
            st.warning(
                f"{correct_count} of {total} fields correct. "
                "Review the items below."
            )

        for field, res in feedback.items():
            label = FIELD_LABELS.get(field, field)
            if res["correct"]:
                st.markdown(f"**{label}:** Correct")
            else:
                st.markdown(f"**{label}:** Incorrect")
                st.markdown(f"- Your answer: `{res['user']}`")
                st.markdown(f"- Expected: `{res['expected']}`")
                if res["explanation"]:
                    st.caption(res["explanation"])


def render_sidebar() -> None:
    st.sidebar.header("Session Stats")
    st.sidebar.metric("Cases completed", st.session_state.cases_completed)

    stats = st.session_state.stats
    any_attempted = any(s["attempts"] > 0 for s in stats.values())

    st.sidebar.markdown("**Accuracy by field**")
    if not any_attempted:
        st.sidebar.caption("No attempts yet.")
    else:
        accs = tracker.field_accuracy(stats)
        for field in tracker.FIELDS:
            counts = stats[field]
            if counts["attempts"] == 0:
                continue
            st.sidebar.markdown(
                f"- {FIELD_LABELS[field]}: "
                f"{accs[field]:.0%} ({counts['correct']}/{counts['attempts']})"
            )

        weakest = tracker.weakest_field(stats)
        if weakest:
            st.sidebar.markdown(f"**Weakest field:** {FIELD_LABELS[weakest]}")

    st.sidebar.divider()

    queue = st.session_state.review_queue
    st.sidebar.markdown(f"**Review queue:** {len(queue)} missed items")
    if queue:
        with st.sidebar.expander("View recent misses"):
            for i, item in enumerate(queue[-10:], 1):
                st.markdown(
                    f"{i}. **{FIELD_LABELS[item['field']]}** "
                    f"({item['case_id']}): expected `{item['expected']}`"
                )

    st.sidebar.divider()
    if st.sidebar.button("Reset session"):
        reset_session()
        st.rerun()


# ---------- main ----------

def main() -> None:
    st.set_page_config(
        page_title="Rx Entry Simulator",
        page_icon=None,
        layout="wide",
    )
    init_state()

    st.title("Prescription Entry Simulator")
    st.caption(
        "Pharmacy technician training tool. "
        "All patients, prescribers, and prescriptions are fictional."
    )

    render_sidebar()

    case = st.session_state.current_case
    render_prescription(case)

    col_p, col_d = st.columns(2)
    with col_p:
        render_patient(case)
    with col_d:
        render_prescriber(case)

    submitted_answers = render_entry_form()
    if submitted_answers is not None:
        handle_submission(submitted_answers)
        st.rerun()

    render_feedback()


if __name__ == "__main__":
    main()
