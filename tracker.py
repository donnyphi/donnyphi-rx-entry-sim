
"""Session statistics and review-queue helpers.

All functions operate on plain dicts and lists passed in by the caller.
This module does not import streamlit and holds no global state.
"""
from __future__ import annotations

from typing import Any


FIELDS = [
    "drug_name",
    "strength",
    "quantity",
    "sig",
    "days_supply",
    "refills",
    "daw",
]


def init_stats() -> dict[str, dict[str, int]]:
    """Return a fresh stats dict with zero counters for every tracked field."""
    return {f: {"attempts": 0, "correct": 0} for f in FIELDS}


def init_review_queue() -> list[dict[str, Any]]:
    """Return an empty review queue."""
    return []


def record_attempt(
    stats: dict[str, dict[str, int]],
    field: str,
    correct: bool,
) -> None:
    """Increment attempt and (if applicable) correct counters for a field."""
    if field not in stats:
        stats[field] = {"attempts": 0, "correct": 0}
    stats[field]["attempts"] += 1
    if correct:
        stats[field]["correct"] += 1


def record_results(
    stats: dict[str, dict[str, int]],
    results: dict[str, dict[str, Any]],
) -> None:
    """Record an attempt for every field in a check_all results dict."""
    for field, res in results.items():
        record_attempt(stats, field, bool(res.get("correct")))


def field_accuracy(stats: dict[str, dict[str, int]]) -> dict[str, float]:
    """Return per-field accuracy as a float in [0, 1]. Zero attempts = 0.0."""
    out: dict[str, float] = {}
    for field, counts in stats.items():
        attempts = counts.get("attempts", 0)
        out[field] = (counts.get("correct", 0) / attempts) if attempts else 0.0
    return out


def weakest_field(stats: dict[str, dict[str, int]]) -> str | None:
    """Return the field with the lowest accuracy among those attempted."""
    attempted = {
        f: counts for f, counts in stats.items() if counts.get("attempts", 0) > 0
    }
    if not attempted:
        return None
    return min(
        attempted,
        key=lambda f: attempted[f]["correct"] / attempted[f]["attempts"],
    )


def add_misses_to_review(
    queue: list[dict[str, Any]],
    case_id: str,
    results: dict[str, dict[str, Any]],
) -> None:
    """Append any incorrect fields from results to the review queue."""
    for field, res in results.items():
        if not res.get("correct"):
            queue.append(
                {
                    "case_id": case_id,
                    "field": field,
                    "user": res.get("user"),
                    "expected": res.get("expected"),
                    "explanation": res.get("explanation"),
                }
            )
