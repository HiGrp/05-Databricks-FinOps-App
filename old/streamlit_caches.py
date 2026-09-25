"""Streamlit @cache_data wrappers — must stay plain Python (not Cython).

Streamlit calls inspect.getsource() on cached functions; Cython .so functions fail.
"""

from __future__ import annotations

import streamlit as st


@st.cache_data(ttl=300, show_spinner=False)
def cached_execute(cache_key: tuple, sql: str):
    from prod_data import _execute_sql_impl

    return _execute_sql_impl(sql)


@st.cache_data(ttl=120, show_spinner=False)
def fetch_clusters_api_cached(_cache_key: tuple) -> dict:
    from prod_data import fetch_clusters_api

    return fetch_clusters_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_warehouses_api_cached(_cache_key: tuple) -> dict:
    from prod_data import fetch_warehouses_api

    return fetch_warehouses_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_jobs_api_cached(_cache_key: tuple) -> dict:
    from prod_data import fetch_jobs_api

    return fetch_jobs_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_cluster_events_cached(_cache_key: tuple):
    from prod_data import fetch_cluster_events_api

    return fetch_cluster_events_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_ingestion_logs_cached(_cache_key: tuple):
    from prod_data import fetch_ingestion_logs

    return fetch_ingestion_logs()
