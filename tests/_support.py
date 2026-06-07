"""Shared helpers for tests that need logic living in ``app.py``.

``app.py`` does ``import streamlit as st`` at module load, but the pure helper
functions we want to test (``get_safety_warnings``) and the scenario data /
renderer do not need a real browser. To keep the suite runnable from a clean
checkout (no Streamlit installed), we inject a minimal stub ``streamlit``
module into ``sys.modules`` before importing ``app``. The stub provides no-op
widgets, context-manager ``container``/``columns``, and an attribute-accessible
``session_state`` -- enough to import ``app`` and call render functions without
a browser. This mirrors the stub/parse approach the existing tests use to avoid
importing Streamlit directly.

Not named ``test_*`` on purpose, so unittest discovery does not collect it.
"""
from __future__ import annotations

import contextlib
import importlib
import sys
import types


class State(dict):
    """A dict that also supports attribute access, like st.session_state."""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def _install_streamlit_stub() -> types.ModuleType:
    existing = sys.modules.get("streamlit")
    if existing is not None and getattr(existing, "_is_rx_test_stub", False):
        return existing

    st = types.ModuleType("streamlit")
    st._is_rx_test_stub = True

    @contextlib.contextmanager
    def _ctx(*args, **kwargs):
        yield None

    def _noop(*args, **kwargs):
        return None

    st.session_state = State()
    st.container = _ctx
    st.columns = lambda spec, **kwargs: [
        _ctx() for _ in range(spec if isinstance(spec, int) else len(spec))
    ]
    st.radio = lambda *a, **k: 0
    st.button = lambda *a, **k: False
    st.text_input = lambda *a, **k: ""
    st.text_area = lambda *a, **k: ""
    for name in (
        "markdown", "caption", "download_button", "expander", "set_page_config",
        "rerun", "stop", "write", "title", "header", "subheader", "divider",
        "image", "warning", "info", "error", "success", "metric",
    ):
        setattr(st, name, _noop)

    sys.modules["streamlit"] = st
    return st


def load_app():
    """Import (once) and return the ``app`` module with a stubbed Streamlit."""
    _install_streamlit_stub()
    return importlib.import_module("app")


def make_state(**values) -> State:
    """Build an attribute-accessible session_state for render smoke tests."""
    return State(**values)
