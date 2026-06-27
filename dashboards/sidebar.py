"""Sidebar — filters, navigation, refresh."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from dashboards.catalog_config import render_catalog_filter
from dashboards.date_filter import render_date_filter, render_workspace_filter
from dashboards.nav import CATEGORIES
from dashboards.query_cache import bump_cache_epoch

_LEGACY_NAV = {
    "Accueil": "Home",
    "Optimisation": "Optimization",
    "Sécurité & Gouvernance": "Security",
    "Jobs & Workflows": "Jobs",
    "SQL & Warehouses": "SQL",
    "Plateforme": "Platform",
}


def _init_nav_state() -> None:
    if "nav_category" not in st.session_state:
        st.session_state.nav_category = "Home"
    elif st.session_state.nav_category in _LEGACY_NAV:
        st.session_state.nav_category = _LEGACY_NAV[st.session_state.nav_category]
    elif st.session_state.nav_category not in CATEGORIES:
        st.session_state.nav_category = "Home"
    if "data_cache_epoch" not in st.session_state:
        st.session_state.data_cache_epoch = 0


def render_sidebar(run_query: Callable | None = None) -> str:
    _init_nav_state()
    sb = st.sidebar

    sb.markdown("### Audit Databricks")

    render_date_filter(sb)
    render_catalog_filter(sb)

    if run_query is not None:
        render_workspace_filter(sb, run_query)

    sb.divider()

    sb.markdown('<p class="nav-section-label">Pages</p>', unsafe_allow_html=True)
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

    sb.divider()
    sb.markdown('<p class="nav-section-label">Data</p>', unsafe_allow_html=True)

    if sb.button("Refresh data", use_container_width=True, help="Clear cache and reload all queries."):
        bump_cache_epoch()
        st.cache_data.clear()
        st.rerun()

    epoch = st.session_state.get("data_cache_epoch", 0)
    if epoch:
        sb.caption(f"Cache cleared {epoch} time(s) this session.")

    return st.session_state.nav_category
