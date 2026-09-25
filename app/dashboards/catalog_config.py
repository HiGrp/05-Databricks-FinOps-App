"""Catalogue Unity Catalog des system tables Databricks (configurable via sidebar)."""

from __future__ import annotations

import re

import streamlit as st

from dashboards.chart_help import HELP

DEFAULT_CATALOG = "system"


def get_catalog() -> str:
    try:
        name = st.session_state.get("system_catalog", DEFAULT_CATALOG)
    except Exception:
        return DEFAULT_CATALOG
    cleaned = (name or DEFAULT_CATALOG).strip()
    return cleaned or DEFAULT_CATALOG


def fq(schema_table: str) -> str:
    """Qualifie schema.table avec le catalogue courant."""
    return f"{get_catalog()}.{schema_table}"


def _sanitize_catalog(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        return DEFAULT_CATALOG
    if not re.fullmatch(r"[A-Za-z0-9_]+", cleaned):
        return DEFAULT_CATALOG
    return cleaned


def render_catalog_filter(sidebar) -> None:
    if "system_catalog" not in st.session_state:
        st.session_state.system_catalog = DEFAULT_CATALOG

    previous = st.session_state.system_catalog
    value = sidebar.text_input(
        "Catalog",
        value=previous,
        key="system_catalog_input",
        placeholder=DEFAULT_CATALOG,
        help=HELP["filter_catalog"],
    )
    st.session_state.system_catalog = _sanitize_catalog(value)

    if st.session_state.system_catalog != previous:
        st.session_state.pop("_ws_data_loaded", None)
