"""Runtime configuration - data source and discount."""

from __future__ import annotations

import os

DEMO = "Demo data"
LIVE = "My Databricks"


def running_in_databricks() -> bool:
    return bool(os.environ.get("DATABRICKS_HOST") or os.environ.get("DATABRICKS_APP_NAME"))


def default_data_source() -> str:
    if os.environ.get("APP_DEV_MODE", "").strip().lower() in ("1", "true", "yes"):
        return DEMO
    return LIVE


def is_dev_mode() -> bool:
    """True -> demo data (DuckDB) instead of Databricks system tables."""
    try:
        import streamlit as st

        return st.session_state.get("data_source", default_data_source()) == DEMO
    except Exception:
        return default_data_source() == DEMO


def default_discount_pct() -> float:
    """Negotiated discount vs list price (0-90 %), from FINOPS_DISCOUNT_PCT."""
    raw = os.environ.get("FINOPS_DISCOUNT_PCT", "").strip()
    try:
        return min(90.0, max(0.0, float(raw))) if raw else 0.0
    except ValueError:
        return 0.0
