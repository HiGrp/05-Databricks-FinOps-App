"""Sidebar - brand, scope, navigation, data source."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from app_config import DEMO, LIVE, default_data_source
from dashboards.app_metadata import (
    APP_CONTACT_URL,
    APP_LOGO,
    APP_NAME,
    APP_VENDOR,
    APP_VENDOR_URL,
    APP_VERSION,
)
from dashboards.catalog_config import render_catalog_filter
from dashboards.date_filter import render_period_picker
from dashboards.nav import CATEGORIES


def _init_state() -> None:
    if st.session_state.get("nav_category") not in CATEGORIES:
        st.session_state.nav_category = "Home"
    st.session_state.setdefault("data_cache_epoch", 0)
    st.session_state.setdefault("data_source", default_data_source())


def _section_divider(container) -> None:
    container.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)


def _nav_buttons(container, names: list[str]) -> None:
    current = st.session_state.nav_category
    for name in names:
        icon = CATEGORIES[name].get("icon", "")
        btn_label = f"{icon}  {name}" if icon else name
        if container.button(
            btn_label,
            key=f"nav_{name}",
            use_container_width=True,
            type="primary" if name == current else "secondary",
            disabled=name == current,
        ):
            st.session_state.nav_category = name
            st.rerun()


def render_sidebar(run_query: Callable | None = None) -> str:
    _init_state()
    sb = st.sidebar

    sb.markdown(
        f"""
        <div class="sidebar-brand">
          <div class="sidebar-brand-row">
            <div class="brand-logo">{APP_LOGO}</div>
            <div class="brand-title">{APP_NAME}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _section_divider(sb)
    render_catalog_filter(sb)
    render_period_picker(sb)

    _section_divider(sb)
    _nav_buttons(sb, ["Home", "Action plan"])
    _nav_buttons(sb, [n for n, c in CATEGORIES.items() if c.get("group") == "Technical details"])
    _nav_buttons(sb, ["Setup"])

    _section_divider(sb)
    demo = sb.toggle(
        "Demo data",
        value=st.session_state.data_source == DEMO,
        key="demo_toggle",
        help="On = demo data. Off = your workspace (connect in Setup first).",
    )
    st.session_state.data_source = DEMO if demo else LIVE

    sb.markdown(
        f"""
        <div class="sidebar-foot">
          Powered by <a href="{APP_VENDOR_URL}" target="_blank">{APP_VENDOR}</a><br>
          <a href="{APP_CONTACT_URL}">Contact us</a> · v{APP_VERSION}
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.session_state.nav_category
