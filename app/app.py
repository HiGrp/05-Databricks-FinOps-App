import streamlit as st

from app_config import is_dev_mode
from connection import init_connection, is_connected
from dashboards.app_metadata import APP_ICON, APP_NAME
from dashboards.date_filter import sync_period
from dashboards.findings import reset_run_state
from dashboards.nav import get_category_meta, get_category_render_fn
from dashboards.sidebar import render_sidebar
from dashboards.theme import inject_theme
from prod_data import execute_sql

st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
init_connection()
inject_theme()
st.session_state["_error_hint_shown"] = None
reset_run_state()
sync_period()

category = render_sidebar(execute_sql)
meta = get_category_meta(category)
st.session_state["nav_icon"] = meta["icon"]
st.session_state["nav_desc"] = meta["desc"]

if not is_dev_mode() and not is_connected() and category != "Setup":
    from dashboards.components import render_connect_gate

    render_connect_gate()
else:
    get_category_render_fn(category)(execute_sql)
