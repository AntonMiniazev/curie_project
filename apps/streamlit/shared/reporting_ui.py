"""Reusable Streamlit UI helpers backed by shared CSS classes."""

from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path

import streamlit as st


STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
REPORTING_CSS_PATH = STREAMLIT_ROOT / "styles" / "reporting.css"
CLASS_SELECTOR_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_-]*)")


@lru_cache
def _reporting_css() -> str:
    """Return the shared reporting stylesheet text."""
    return REPORTING_CSS_PATH.read_text(encoding="utf-8")


@lru_cache
def available_css_classes() -> frozenset[str]:
    """Return class selectors declared in the shared Streamlit stylesheet."""
    return frozenset(CLASS_SELECTOR_RE.findall(_reporting_css()))


def css_classes(*names: str) -> str:
    """Return an escaped class attribute value after validating class names.

    This keeps HTML helpers tied to classes that actually exist in
    `styles/reporting.css`, so typos fail during development instead of silently
    producing unstyled cards.
    """
    known_classes = available_css_classes()
    missing = [name for name in names if name not in known_classes]
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Unknown reporting CSS class(es): {missing_text}")
    return html.escape(" ".join(names), quote=True)


def apply_shared_css() -> None:
    """Inject the shared reporting stylesheet into the current Streamlit page."""
    st.markdown(f"<style>{_reporting_css()}</style>", unsafe_allow_html=True)


def kpi_card(label: str, value: str) -> None:
    """Render one KPI card using shared report CSS classes."""
    st.markdown(
        _kpi_card_html(label, value),
        unsafe_allow_html=True,
    )


def kpi_grid(items: list[tuple[str, str]]) -> None:
    """Render a responsive KPI card grid from label/value pairs."""
    cards = "".join(_kpi_card_html(label, value) for label, value in items)
    st.markdown(
        f'<div class="{css_classes("curie-kpi-grid")}">{cards}</div>',
        unsafe_allow_html=True,
    )


def _kpi_card_html(label: str, value: str) -> str:
    return (
        f'<div class="{css_classes("curie-kpi")}">'
        f'<div class="{css_classes("curie-kpi-label")}">{html.escape(label)}</div>'
        f'<div class="{css_classes("curie-kpi-value")}">{html.escape(value)}</div>'
        "</div>"
    )
