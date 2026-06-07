# Rx Entry Simulator

A Streamlit simulator that helps pharmacy technician students practice prescription entry, label interpretation, and common pharmacy workflow scenarios.

## Live Demo

https://donnyphi-rx-lab.streamlit.app/

## Dashboard

![Rx Entry Simulator screenshot](assets/rx-entry-dashboard.png)

## Why I Built This

Built for my pharm-tech cohort ahead of the June certification exam.

## Features

- Prescription-entry practice
- Pharmacy-label interpretation
- Simulated pharmacy workflow questions
- Instant feedback for practice attempts
- Clean Streamlit interface for fast review
- Designed for pharmacy technician certification preparation

## Tech Stack

- Python
- Streamlit
- Pandas
- GitHub
- Streamlit Community Cloud

## Verifying changes (run before merging)

This project ships a lightweight automated check suite (field validation,
case self-validation, and UI contract checks). **Run it before merging any
change** — including AI-generated changes — and only merge when it passes.

```bash
python run_checks.py
```

`run_checks.py` runs every test in `tests/` using only the Python standard
library (no extra install needed) and **exits non-zero if any test fails**, so
it works as a merge gate locally or in CI. Equivalent direct command:

```bash
python -m unittest discover -s tests
```

What the checks cover today:

- `tests/test_checker.py` — numeric fields reject non-whole-number input, SIG
  validation requires the expected components, and every prescription case in
  `cases.py` self-validates against `checker.py`.
- `tests/test_ui_contracts.py` — UI contracts parsed from `app.py` (e.g. the
  Download Label PDF button stays a secondary action; mobile CSS is present).

If you add a case, scenario, or rule, run `python run_checks.py` and confirm it
still exits `0` before opening or merging a PR.

## Author

Donny Nguyen
