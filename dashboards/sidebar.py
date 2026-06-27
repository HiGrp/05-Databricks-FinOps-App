"""Sidebar — filters and navigation."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from dashboards.catalog_config import render_catalog_filter
from dashboards.date_filter import render_date_filter, render_workspace_filter
from dashboards.nav import CATEGORIES

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

    sb.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-brand-row">
            <div class="brand-logo">A</div>
            <div>
              <div class="brand-title">Audit Databricks</div>
              <div class="brand-sub">Workspace insights</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with sb.container(border=True):
        render_date_filter(sb)

    with sb.container(border=True):
        render_catalog_filter(sb)

    if run_query is not None:
        with sb.container(border=True):
            render_workspace_filter(sb, run_query)

    sb.markdown('<p class="nav-section-label">Navigation</p>', unsafe_allow_html=True)
    for cat_name, cat in CATEGORIES.items():
        is_active = cat_name == st.session_state.nav_category
        label = f"{cat['icon']}  {cat_name}"
        if sb.button(
            label,
            key=f"cat_{cat_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            disabled=is_active,
        ):
            st.session_state.nav_category = cat_name
            st.rerun()

    return st.session_state.nav_category
