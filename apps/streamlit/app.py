"""Streamlit entrypoint for the Curie Marketing report.

Docker runs this file at the Streamlit service root. The dashboard code is kept
in `dashboards.marketing` so direct local development can still run the same
report module if needed.
"""

from __future__ import annotations

from dashboards import marketing as _marketing  # noqa: F401
