"""Sidebar minimaliste."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from dashboards.catalog_config import render_catalog_filter
from dashboards.date_filter import render_date_filter, render_workspace_filter
from dashboards.nav import CATEGORIES


def _init_nav_state() -> None:
    if "nav_category" not in st.session_state:
        st.session_state.nav_category = "Accueil"


def render_sidebar(run_query: Callable | None = None) -> str:
    _init_nav_state()
    sb = st.sidebar

    sb.markdown("### Audit Databricks")

    render_date_filter(sb)
    render_catalog_filter(sb)

    # Filtres Trigramme / Environnement
    if run_query is not None:
        render_workspace_filter(sb, run_query)

    sb.divider()

    for cat_name, cat in CATEGORIES.items():
        is_active = cat_name == st.session_state.nav_category
        if sb.button(
            f"{cat['icon']}  {cat_name}",
            key=f"cat_{cat_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            disabled=is_active,
        ):
            st.session_state.nav_category = cat_name
            st.rerun()

    return st.session_state.nav_category

