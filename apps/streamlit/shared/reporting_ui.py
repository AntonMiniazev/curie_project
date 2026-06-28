"""Reusable Streamlit UI helpers backed by shared CSS classes."""

from __future__ import annotations

import html
import logging
from functools import lru_cache
from pathlib import Path

import cssutils
import streamlit as st


STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
REPORTING_CSS_PATH = STREAMLIT_ROOT / "styles" / "reporting.css"
THEME_ATTRIBUTE = "data-curie-report-theme"
THEME_NAMES = {"day", "night"}


@lru_cache
def _reporting_css() -> str:
    """Return the shared reporting stylesheet text."""
    return REPORTING_CSS_PATH.read_text(encoding="utf-8")


@lru_cache
def _reporting_sheet() -> cssutils.css.CSSStyleSheet:
    """Parse the shared reporting stylesheet once for class and token lookup."""
    parser = cssutils.CSSParser(loglevel=logging.CRITICAL)
    return parser.parseString(_reporting_css())


@lru_cache
def available_css_classes() -> frozenset[str]:
    """Return class selectors declared in the shared Streamlit stylesheet.

    `cssutils` parses the stylesheet and exposes selector tokens, so class
    discovery does not depend on ad hoc regex parsing of CSS text.
    """
    return frozenset(_classes_from_rules(_reporting_sheet().cssRules))


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
    st.markdown(
        f"<style>{_reporting_css()}\n{_theme_override_css()}</style>",
        unsafe_allow_html=True,
    )


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
        f'<div class="{css_classes("reporting-kpis")}">{cards}</div>',
        unsafe_allow_html=True,
    )


def _kpi_card_html(label: str, value: str) -> str:
    return (
        f'<div class="{css_classes("reporting-kpis__card")}">'
        f'<div class="{css_classes("reporting-kpis__label")}">{html.escape(label)}</div>'
        f'<div class="{css_classes("reporting-kpis__value")}">{html.escape(value)}</div>'
        "</div>"
    )


def current_report_theme() -> str:
    """Return the website-selected report theme mode from iframe query params."""
    mode = st.query_params.get("curie_theme", "day")
    if isinstance(mode, list):
        mode = mode[-1] if mode else "day"
    return "night" if mode == "night" else "day"


def current_report_colors() -> dict[str, str]:
    """Return Curie color tokens parsed from the shared stylesheet."""
    colors: dict[str, str] = {}
    for name, value in reporting_theme_tokens(current_report_theme()).items():
        if name == "--curie-color-scheme":
            continue
        key = name.removeprefix("--curie-").replace("-", "_")
        if key == "text_muted":
            key = "muted"
        colors[key] = value
    return colors


@lru_cache
def reporting_theme_tokens(theme: str) -> dict[str, str]:
    """Return CSS custom properties for one reporting theme from reporting.css."""
    selected_theme = theme if theme in THEME_NAMES else "day"
    tokens: dict[str, str] = {}

    for rule in _reporting_sheet().cssRules:
        if not _rule_matches_theme(rule, selected_theme):
            continue

        style = getattr(rule, "style", None)
        if style is None:
            continue

        for property_ in style:
            name = property_.name
            if name.startswith("--curie-"):
                tokens[name] = property_.value

    if not tokens:
        raise ValueError(f"No reporting CSS theme tokens found for {selected_theme!r}.")
    return tokens


def _classes_from_rules(rules: object) -> set[str]:
    classes: set[str] = set()
    for rule in rules:
        nested_rules = getattr(rule, "cssRules", None)
        if nested_rules is not None:
            classes.update(_classes_from_rules(nested_rules))
            continue

        selector_list = getattr(rule, "selectorList", None)
        if selector_list is None:
            continue

        for selector in selector_list:
            for item in getattr(selector, "seq", []):
                value = getattr(item, "value", item)
                if isinstance(value, str) and value.startswith("."):
                    classes.add(value[1:])
    return classes


def _theme_override_css() -> str:
    declarations = "\n".join(
        f"  {name}: {value};"
        for name, value in reporting_theme_tokens(current_report_theme()).items()
    )
    return f":root {{\n{declarations}\n}}\n"


def _rule_matches_theme(rule: object, theme: str) -> bool:
    selector_list = getattr(rule, "selectorList", None)
    if selector_list is None:
        return False
    return any(
        _selector_matches_theme(selector.selectorText, theme)
        for selector in selector_list
    )


def _selector_matches_theme(selector_text: str, theme: str) -> bool:
    selector = selector_text.replace("'", '"').replace(" ", "")
    theme_selector = f':root[{THEME_ATTRIBUTE}="{theme}"]'
    return selector == theme_selector or (theme == "day" and selector == ":root")
