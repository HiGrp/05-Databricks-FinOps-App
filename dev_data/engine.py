"""DuckDB-backed dev engine.

Serves the dashboards' *raw* SQL (the local dialect) against an in-memory DuckDB
loaded with deterministic fake data. No Databricks, no external server.

The dashboards' local dialect is already DuckDB-compatible (``LEFT``, ``strftime``,
``quantile_cont``, ``INTERVAL '1' DAY`` ...). The only Spark-only helpers used are
``split()`` and ``get()``, which we recreate as DuckDB macros.
"""

from __future__ import annotations

import threading

import pandas as pd
import streamlit as st

# Enriched relations that production derives via SQL views (see sql_tables.py).
# We rebuild the small subset the dashboards actually read.
_DERIVED_VIEWS = {
    "compute_clusters_parsed": """
        CREATE OR REPLACE VIEW compute_clusters_parsed AS
        SELECT cluster_id, cluster_name, owned_by, worker_count,
               driver_node_type, auto_termination_minutes, data_security_mode,
               cluster_source, dbr_version, policy_id,
               create_time, change_time, delete_time,
               team, environment, workspace_id, runtime_engine
        FROM compute_clusters
        WHERE cluster_source != 'JOB'
    """,
    "compute_warehouses_parsed": """
        CREATE OR REPLACE VIEW compute_warehouses_parsed AS
        SELECT warehouse_id, warehouse_name, warehouse_size, state,
               workspace_id, warehouse_type
        FROM compute_warehouses
    """,
    "query_history": """
        CREATE OR REPLACE VIEW query_history AS
        SELECT statement_id, session_id, executed_by, execution_status,
               total_duration_ms AS duration_ms, read_bytes, start_time,
               statement_type, spilled_local_bytes, waiting_at_capacity_duration_ms,
               warehouse_name, team, execution_duration_ms, statement_text
        FROM query_history_full
    """,
}

_MACROS = (
    "CREATE OR REPLACE MACRO split(str, delim) AS string_split(str, delim);"
    "CREATE OR REPLACE MACRO get(lst, idx) AS lst[idx + 1];"
)

_LOCK = threading.Lock()


@st.cache_resource(show_spinner="Building local demo dataset...")
def _get_connection():
    import duckdb

    from dev_data.fake_data import build_frames

    con = duckdb.connect(database=":memory:")
    con.execute(_MACROS)

    frames = build_frames()
    for name, df in frames.items():
        con.register(f"_src_{name}", df)
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM _src_{name}")
        con.unregister(f"_src_{name}")

    for ddl in _DERIVED_VIEWS.values():
        con.execute(ddl)

    return con


def _run(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    try:
        con = _get_connection()
        with _LOCK:
            cur = con.cursor()
            cur.execute(_MACROS)  # macros are per-connection; cursor() is a fresh conn
            df = cur.execute(sql).df()
        return df, None
    except Exception as exc:  # noqa: BLE001 - surface as UI error string
        return None, f"[dev] {exc}"


@st.cache_data(ttl=300, show_spinner=False)
def _cached(cache_key: tuple, sql: str):
    return _run(sql)


def execute_sql_dev(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """Dev replacement for ``prod_data.execute_sql`` (5-min cache like prod)."""
    from dashboards.query_cache import get_cache_key

    return _cached(get_cache_key(), sql)


# --------------------------------------------------------------------------- #
# Fake REST API responses (Platform page)
# --------------------------------------------------------------------------- #

def fake_clusters_api() -> dict:
    df, _ = _run(
        "SELECT cluster_id, cluster_name, auto_termination_minutes AS autotermination_minutes, "
        "worker_count AS num_workers FROM compute_clusters LIMIT 50"
    )
    if df is None or df.empty:
        return {"clusters": []}
    states = ["RUNNING", "TERMINATED", "PENDING"]
    clusters = []
    for i, row in enumerate(df.to_dict("records")):
        row["state"] = states[i % len(states)]
        clusters.append(row)
    return {"clusters": clusters}


def fake_warehouses_api() -> dict:
    df, _ = _run(
        "SELECT warehouse_id AS id, warehouse_name AS name, state, "
        "warehouse_type, auto_stop_minutes AS auto_stop_mins FROM compute_warehouses LIMIT 50"
    )
    if df is None or df.empty:
        return {"warehouses": []}
    return {"warehouses": df.to_dict("records")}


def fake_jobs_api() -> dict:
    df, _ = _run(
        "SELECT DISTINCT job_id, job_name FROM job_run_timeline_parsed LIMIT 50"
    )
    if df is None or df.empty:
        return {"jobs": []}
    jobs = [{"job_id": r["job_id"], "settings": {"name": r["job_name"]}} for r in df.to_dict("records")]
    return {"jobs": jobs}


def fake_workspace_status() -> dict:
    return {
        "user": "dev.user@acme.com",
        "display_name": "Dev User",
        "active": True,
        "source": "dev_fake_data",
    }


def fake_cluster_events() -> pd.DataFrame:
    df, _ = _run(
        "SELECT cluster_id, "
        "CASE WHEN driver THEN 'DRIVER_HEALTHY' ELSE 'RUNNING' END AS type, "
        "CAST(epoch_ms(start_time) AS BIGINT) AS timestamp, "
        "'{}' AS details FROM compute_node_timeline LIMIT 300"
    )
    return df if df is not None else pd.DataFrame()
