"""SQL query cache — TTL + manual refresh via cache epoch."""

from __future__ import annotations

import streamlit as st


def get_cache_key() -> tuple:
    return (
        st.session_state.get("data_cache_epoch", 0),
        str(st.session_state.get("filter_date_start", "")),
        str(st.session_state.get("filter_date_end", "")),
        st.session_state.get("system_catalog", "system"),
        tuple(st.session_state.get("filter_trigramme", [])),
        tuple(st.session_state.get("filter_environnement", [])),
    )


def bump_cache_epoch() -> None:
    st.session_state["data_cache_epoch"] = st.session_state.get("data_cache_epoch", 0) + 1


@st.cache_data(ttl=300, show_spinner=False)
def cached_execute(cache_key: tuple, sql: str):
    from prod_data import _execute_sql_impl

    return _execute_sql_impl(sql)
