#!/usr/bin/env python3
"""Project verification gate for the Rx Entry Simulator.

Run this before merging any change:

    python run_checks.py

It discovers and runs the unittest suite in ``tests/`` (checker validation,
case self-validation, and UI contract checks). It uses only the Python
standard library -- no third-party test runner is required, and it does not
import Streamlit, so it runs from a clean checkout.

Exit code:
    0  -> every test passed (safe to merge)
    1  -> at least one test failed (do not merge)
"""
from __future__ import annotations

import sys
import unittest


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
