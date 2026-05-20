# Pharmacy Technician Prescription Entry Simulator

A beginner-friendly Streamlit app for pharmacy technician students to practice
entering prescriptions into a pharmacy-style system. All patient, prescriber,
drug, and prescription data is fictional. This is a training tool, not real
pharmacy software, and is not medical advice.

## What you practice

For each fake prescription you see, you enter:

- Drug name
- Strength (with unit)
- Quantity
- SIG in plain English
- Days supply
- Refills
- DAW code

The app checks each field, explains mistakes in detail, tracks accuracy by
field type, and queues missed items for review.

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL (typically `http://localhost:8501`). Open it
in a browser.

## Project layout

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit UI and session-state wiring. Only file importing streamlit. |
| `cases.py` | Fake prescription cases and a random-case selector. |
| `checker.py` | Pure per-field validation functions. No streamlit dependency. |
| `tracker.py` | Session stats and missed-fields helpers. Operate on plain dicts. |
| `requirements.txt` | Pinned to streamlit only for v1. |
| `README.md` | This file. |

## How a case works

Each case has five sub-objects:

- `patient` and `prescriber` are display-only.
- `rx_text` is what the user sees on the prescription, written in clinical
  shorthand. For some cases the `Disp` line is hidden so the student has to
  calculate quantity from the SIG.
- `expected` is the ground truth for the checker. SIG is stored as a
  component-synonym map rather than a single string so multiple valid
  phrasings pass.
- `extras` holds optional per-field calculation hints, shown only when the
  student gets the field wrong.

## How SIG checking works

A complete English SIG contains a verb, quantity, dosage form, route,
frequency, and a duration when one is specified. The checker requires the
user's input to contain at least one synonym from each component group as a
whole word or phrase (regex word boundaries, so `tab` does not match inside
`tablet` and `1` does not match inside `10`). When a component is missing the
feedback says which one and gives an example phrasing.

Frequency synonyms are tuned to avoid cross-contamination across QD, BID,
TID, and QHS. For example `daily` alone is excluded from QD because it is a
substring of `three times daily`.

## What v1 does

- 6 prescription cases covering acute antibiotics and chronic oral medications
- Per-field validation with English explanations and calculation hints
- Per-field session accuracy and weakest-field identification
- Missed fields panel showing recent misses, rendered in-page (no sidebar)
- Reset-session button

## What v1 does not do

- No login, no user accounts
- No database; everything lives in `st.session_state` and is lost on refresh
- No PRN, taper, IV, inhaled, topical, or compounded medications
- No imitation of any specific commercial pharmacy software

## Extending

To add a case, append a dict to `CASES` in `cases.py`. The schema is
documented at the top of that file. Reuse the existing `FREQ_QD`, `FREQ_BID`,
`FREQ_TID`, `FREQ_QHS` synonym blocks when possible.

To add a new field type to the checker, add a `check_<field>` function in
`checker.py` returning the standard result dict, then register it in
`check_all` and in the `FIELDS` list in `tracker.py` and the `FIELD_LABELS`
and `INPUT_KEYS` lists in `app.py`.
