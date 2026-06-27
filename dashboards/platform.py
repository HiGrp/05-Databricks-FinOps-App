"""Platform dashboards — API, ingestion, logs."""

import pandas as pd
import streamlit as st

from dashboards.components import data_table, metrics_row, page_header, show_empty
from dashboards.query_cache import get_cache_key
from prod_data import (
    DRIVER_LOG_VOLUME,
    INGESTION_LOG_TABLE,
    fetch_clusters_api_cached,
    fetch_ingestion_logs_cached,
    fetch_jobs_api_cached,
    fetch_warehouses_api_cached,
    list_driver_log_files,
    read_driver_log,
)


def render_api_inventory(run_query) -> None:
    page_header("API inventory", "Live Databricks REST API")
    key = get_cache_key()
    try:
        with st.spinner("Calling Databricks API..."):
            clusters = fetch_clusters_api_cached(key)
            warehouses = fetch_warehouses_api_cached(key)
            jobs = fetch_jobs_api_cached(key)
    except Exception as exc:
        st.error(f"API error: {exc}")
        return

    metrics_row([
        ("Clusters", str(len(clusters.get("clusters", []))), None),
        ("Warehouses", str(len(warehouses.get("warehouses", []))), None),
        ("Jobs", str(len(jobs.get("jobs", []))), None),
    ])

    tabs = st.tabs(["Clusters", "Warehouses", "Jobs"])
    with tabs[0]:
        df = pd.DataFrame(clusters.get("clusters", []))
        data_table(df if not df.empty else None)
    with tabs[1]:
        df = pd.DataFrame(warehouses.get("warehouses", []))
        data_table(df if not df.empty else None)
    with tabs[2]:
        rows = [
            {"job_id": j.get("job_id"), "name": (j.get("settings") or {}).get("name", "")}
            for j in jobs.get("jobs", [])
        ]
        data_table(pd.DataFrame(rows) if rows else None)


def render_ingestion_health(run_query) -> None:
    page_header("Ingestion pipeline", "FinOps ingestion run tracking")
    if not INGESTION_LOG_TABLE:
        st.info(
            "Set `FINOPS_INGESTION_LOG_TABLE` (catalog.schema.table) "
            "to track ingestion runs."
        )
        return

    key = get_cache_key()
    with st.spinner("Loading ingestion logs..."):
        df = fetch_ingestion_logs_cached(key)

    if df is None or df.empty:
        show_empty("No ingestion log rows found.")
        return

    metrics_row([
        ("Rows", f"{len(df):,}", None),
        ("Columns", str(len(df.columns)), None),
    ])
    data_table(df.head(100))


def render_driver_logs(run_query) -> None:
    page_header("Driver logs", "Sample cluster driver logs")
    _render_driver_logs_prod()


def _render_driver_logs_prod() -> None:
    if not DRIVER_LOG_VOLUME:
        st.info(
            "Set `FINOPS_DRIVER_LOG_VOLUME` (Unity Volume path) "
            "or use cluster log delivery to cloud storage."
        )
        return
    files = list_driver_log_files()
    if not files:
        st.warning(f"No .log files in {DRIVER_LOG_VOLUME}")
        return
    selected = st.selectbox("Log file", files)
    with st.spinner("Reading log file..."):
        content = read_driver_log(selected)
    _show_log_content(content)


def _show_log_content(content: str) -> None:
    errors = [line for line in content.splitlines() if "ERROR" in line or "OOM" in line or "WARN" in line]
    st.metric(
        "WARN/ERROR lines",
        len(errors),
        help="Lines containing WARN, ERROR, or OOM in the log sample.",
    )
    st.code(content[:8000], language="log")
