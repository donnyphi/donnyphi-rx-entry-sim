
"""Pure validation functions for prescription-entry fields.

Each check_<field> function returns a uniform dict:
    {
        "correct": bool,
        "user": <user input>,
        "expected": <expected value or descriptor>,
        "explanation": <str or None>,
    }

This module does not import streamlit. It is importable and testable
standalone.
"""
from __future__ import annotations

import re
from typing import Any


# ---------- helpers ----------

def _norm(value: Any) -> str:
    """Lowercase, collapse internal whitespace, strip."""
    return " ".join(str(value).lower().split())


def _parse_int(value: Any) -> int | None:
    """Parse an int from user input. Returns None on failure."""
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None


def _contains_phrase(text: str, phrase: str) -> bool:
    """True if phrase appears in text bounded by word edges.

    Word boundaries prevent false positives like 'tab' matching inside
    'tablet' or '1' matching inside '10'. Both text and phrase must
    already be normalized via _norm.
    """
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, text) is not None


# ---------- per-field checkers ----------

def check_drug_name(
    user: str,
    expected: str,
    alternates: list[str] | None = None,
) -> dict[str, Any]:
    alternates = alternates or []
    accepted = {_norm(expected)} | {_norm(a) for a in alternates}
    correct = _norm(user) in accepted
    explanation = None
    if not correct:
        explanation = (
            f"Drug name should be '{expected}'. Spell it exactly as written "
            f"on the prescription. Watch for generic vs brand."
        )
    return {
        "correct": correct,
        "user": user,
        "expected": expected,
        "explanation": explanation,
    }


def check_strength(user: str, expected: str) -> dict[str, Any]:
    user_n = _norm(user).replace(" ", "")
    expected_n = _norm(expected).replace(" ", "")
    correct = user_n == expected_n
    explanation = None
    if not correct:
        explanation = (
            f"Strength should be '{expected}'. Include the number and the "
            f"unit (mg, mcg, mL, etc.)."
        )
    return {
        "correct": correct,
        "user": user,
        "expected": expected,
        "explanation": explanation,
    }


def _check_int_field(
    user: Any,
    expected: int,
    field_label: str,
    calc_explanation: str | None = None,
) -> dict[str, Any]:
    parsed = _parse_int(user)
    if parsed is None:
        msg = f"{field_label} must be a whole number. Expected {expected}."
        if calc_explanation:
            msg += f" {calc_explanation}"
        return {
            "correct": False,
            "user": user,
            "expected": expected,
            "explanation": msg,
        }
    correct = parsed == expected
    explanation = None
    if not correct:
        explanation = f"Expected {expected}."
        if calc_explanation:
            explanation += f" {calc_explanation}"
    return {
        "correct": correct,
        "user": parsed,
        "expected": expected,
        "explanation": explanation,
    }


def check_quantity(
    user: Any,
    expected: int,
    calc_explanation: str | None = None,
) -> dict[str, Any]:
    return _check_int_field(user, expected, "Quantity", calc_explanation)


def check_days_supply(
    user: Any,
    expected: int,
    calc_explanation: str | None = None,
) -> dict[str, Any]:
    return _check_int_field(user, expected, "Days supply", calc_explanation)


def check_refills(user: Any, expected: int) -> dict[str, Any]:
    return _check_int_field(user, expected, "Refills")
    result = _check_int_field(user, expected, "Refills")
    if not result["correct"]:
        base = result["explanation"] or f"Expected {expected}."
        result["explanation"] = (
            base + " The refill count is written on the prescription; copy it exactly."
        )
    return result


def check_daw(user: Any, expected: int) -> dict[str, Any]:
    result = _check_int_field(user, expected, "DAW")
    if not result["correct"]:
        base = result["explanation"] or f"Expected {expected}."
        result["explanation"] = (
            base
            + " DAW 0 = no product selection indicated. "
            "DAW 1 = substitution not allowed by prescriber. "
            "DAW 2 = patient requested brand."
        )
    return result


def check_sig(
    user: str,
    sig_components: dict[str, list[str]],
) -> dict[str, Any]:
    """Verify the user's English SIG contains every required component.

    For each component group, the user's input must contain at least one
    synonym as a whole word or phrase (regex word boundaries).
    """
    user_n = _norm(user)
    missing: list[tuple[str, list[str]]] = []
    for component, synonyms in sig_components.items():
        if not any(_contains_phrase(user_n, _norm(s)) for s in synonyms):
            missing.append((component, synonyms))

    correct = len(missing) == 0
    if correct:
        explanation = None
    else:
        parts = [f"{comp} (e.g. '{syns[0]}')" for comp, syns in missing]
        explanation = (
            "Your SIG is missing: "
            + "; ".join(parts)
            + ". A complete SIG includes a verb, quantity, dosage form, "
            "route, frequency, and a duration when one is specified."
        )

    return {
        "correct": correct,
        "user": user,
        "expected": "All required SIG components present",
        "explanation": explanation,
    }


# ---------- orchestrator ----------

def check_all(
    user_answers: dict[str, Any],
    expected: dict[str, Any],
    extras: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Run every field check for a single case. Returns dict keyed by field."""
    extras = extras or {}
    return {
        "drug_name": check_drug_name(
            user_answers.get("drug_name", ""),
            expected["drug_name"],
            extras.get("drug_alternates"),
        ),
        "strength": check_strength(
            user_answers.get("strength", ""),
            expected["strength"],
        ),
        "quantity": check_quantity(
            user_answers.get("quantity"),
            expected["quantity"],
            extras.get("quantity_calc"),
        ),
        "sig": check_sig(
            user_answers.get("sig", ""),
            expected["sig_components"],
        ),
        "days_supply": check_days_supply(
            user_answers.get("days_supply"),
            expected["days_supply"],
            extras.get("days_calc"),
        ),
        "refills": check_refills(
            user_answers.get("refills"),
            expected["refills"],
        ),
        "daw": check_daw(
            user_answers.get("daw"),
            expected["daw"],
        ),
    }
