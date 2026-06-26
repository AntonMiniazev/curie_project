"""Streamlit entrypoint that routes Curie report metadata to dashboard modules."""

from __future__ import annotations

import runpy

import streamlit as st


REPORT_MODULES = {
    "marketing": "dashboards.marketing",
    "finance": "dashboards.finance",
    "delivery": "dashboards.delivery",
}


def _selected_report() -> str:
    report = st.query_params.get("report", "marketing")
    if isinstance(report, list):
        report = report[-1] if report else "marketing"
    return report if report in REPORT_MODULES else "marketing"


runpy.run_module(REPORT_MODULES[_selected_report()], run_name="__main__")
