"""Sidebar — filters and navigation."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from dashboards.app_metadata import APP_LOGO, APP_NAME, APP_SIDEBAR_TAGLINE
from dashboards.catalog_config import render_catalog_filter
from dashboards.date_filter import render_date_filter
from dashboards.chart_help import HELP, info_tip_html
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
        f"""
        <div class="sidebar-brand">
          <div class="sidebar-brand-row">
            <div class="brand-logo">{APP_LOGO}</div>
            <div>
              <div class="brand-title">{APP_NAME}</div>
              <div class="brand-sub">{APP_SIDEBAR_TAGLINE}</div>
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

    sb.markdown(
        f'<div class="nav-label-row"><p class="nav-section-label">Navigation</p>'
        f"{info_tip_html(HELP['filter_nav'])}</div>",
        unsafe_allow_html=True,
    )
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

    _render_support_footer(sb)

    return st.session_state.nav_category


def _render_support_footer(sb) -> None:
    """Persistent support contact — visible on every page (license, help, etc.)."""
    from dashboards.app_metadata import APP_SUPPORT_EMAIL

    mail = APP_SUPPORT_EMAIL
    sb.markdown(
        f"""
        <div class="sidebar-support">
          <span class="sidebar-support-label">Need help?</span>
          <a class="sidebar-support-link" href="mailto:{mail}">{mail}</a>
          <span class="sidebar-support-hint">License · support</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
