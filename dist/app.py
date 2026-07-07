import streamlit as st

from app_config import is_dev_mode, license_enabled
from dashboards.app_metadata import APP_ICON, APP_NAME
from dashboards.nav import get_category_meta, get_category_render_fn
from dashboards.sidebar import render_sidebar
from dashboards.theme import inject_theme
from prod_data import execute_sql

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

# License / trial gate (skipped in dev mode). Blocks the app when the trial has
# ended and no valid license is installed.
if license_enabled() and not is_dev_mode():
    from licensing import render_license_gate

    render_license_gate()


def run_query(sql_query: str):
    return execute_sql(sql_query)


category = render_sidebar(run_query)

if license_enabled() and not is_dev_mode():
    from licensing import render_status_sidebar

    render_status_sidebar()

meta = get_category_meta(category)
st.session_state["nav_category"] = category
st.session_state["nav_icon"] = meta.get("icon") or ""
st.session_state["nav_desc"] = meta.get("desc") or ""

render_fn = get_category_render_fn(category)
if render_fn is None:
    st.error(f"Page not found: **{category}**")
else:
    render_fn(run_query)
