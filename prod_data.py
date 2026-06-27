"""Accès production — system tables (SQL), API REST, logs optionnels."""

from __future__ import annotations

import os
from functools import lru_cache

import pandas as pd

# Tables Delta optionnelles (logs / miroirs)
INGESTION_LOG_TABLE = os.environ.get("FINOPS_INGESTION_LOG_TABLE", "").strip()
CLUSTER_EVENTS_TABLE = os.environ.get("FINOPS_CLUSTER_EVENTS_TABLE", "").strip()
DRIVER_LOG_VOLUME = os.environ.get("FINOPS_DRIVER_LOG_VOLUME", "").strip()


@lru_cache(maxsize=1)
def _workspace_client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def _sdk_value(value):
    if value is None:
        return None
    if hasattr(value, "value"):
        return value.value
    return value


def fetch_clusters_api() -> dict:
    w = _workspace_client()
    clusters = []
    for c in w.clusters.list():
        clusters.append(
            {
                "cluster_id": c.cluster_id,
                "cluster_name": c.cluster_name,
                "state": _sdk_value(c.state),
                "autotermination_minutes": c.autotermination_minutes,
                "num_workers": c.num_workers,
            }
        )
    return {"clusters": clusters}


def fetch_warehouses_api() -> dict:
    w = _workspace_client()
    warehouses = []
    for wh in w.warehouses.list():
        warehouses.append(
            {
                "id": wh.id,
                "name": wh.name,
                "state": _sdk_value(wh.state),
                "warehouse_type": _sdk_value(wh.warehouse_type),
                "auto_stop_mins": wh.auto_stop_mins,
            }
        )
    return {"warehouses": warehouses}


def fetch_jobs_api() -> dict:
    w = _workspace_client()
    jobs = []
    for job in w.jobs.list(expand_tasks=False):
        jobs.append({"job_id": job.job_id, "settings": {"name": job.settings.name if job.settings else ""}})
    return {"jobs": jobs}


def fetch_workspace_status() -> dict:
    w = _workspace_client()
    me = w.current_user.me()
    return {
        "user": me.user_name,
        "display_name": me.display_name,
        "active": me.active,
        "source": "databricks_api",
    }


def fetch_cluster_events_api(limit_per_cluster: int = 30) -> pd.DataFrame:
    if CLUSTER_EVENTS_TABLE:
        return _query_table(CLUSTER_EVENTS_TABLE, limit=500)

    w = _workspace_client()
    rows = []
    try:
        clusters = list(w.clusters.list())[:12]
        for cluster in clusters:
            try:
                resp = w.api_client.do(
                    "GET",
                    "/api/2.0/clusters/events",
                    query={"cluster_id": cluster.cluster_id},
                )
                for evt in (resp or {}).get("events", [])[:limit_per_cluster]:
                    rows.append(
                        {
                            "cluster_id": cluster.cluster_id,
                            "type": evt.get("type"),
                            "timestamp": evt.get("timestamp"),
                            "details": str(evt.get("details", "")),
                        }
                    )
            except Exception:
                continue
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def fetch_ingestion_logs() -> pd.DataFrame:
    if INGESTION_LOG_TABLE:
        return _query_table(INGESTION_LOG_TABLE, limit=200)
    return pd.DataFrame()


def list_driver_log_files() -> list[str]:
    if not DRIVER_LOG_VOLUME:
        return []
    try:
        w = _workspace_client()
        entries = w.files.list_directory_contents(DRIVER_LOG_VOLUME)
        return sorted(e.path.rsplit("/", 1)[-1] for e in entries if e.path.endswith(".log"))
    except Exception:
        return []


def read_driver_log(filename: str, max_chars: int = 8000) -> str:
    if not DRIVER_LOG_VOLUME:
        return ""
    path = f"{DRIVER_LOG_VOLUME.rstrip('/')}/{filename}"
    try:
        w = _workspace_client()
        resp = w.files.download(path)
        content = resp.contents.read().decode("utf-8", errors="replace")
        return content[:max_chars]
    except Exception as exc:
        return f"Log read error: {exc}"


def _query_table(table: str, limit: int = 200) -> pd.DataFrame:
    from dashboards.sql_tables import adapt_sql_for_databricks

    sql = adapt_sql_for_databricks(f"SELECT * FROM {table} LIMIT {int(limit)}")
    df, err = execute_sql(sql)
    if err or df is None:
        return pd.DataFrame()
    return df


def _execute_sql_impl(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """Run adapted SQL on SQL Warehouse (no cache)."""
    try:
        import time

        w = _workspace_client()
        warehouse_id = _resolve_warehouse_id(w)
        if not warehouse_id:
            return None, "No SQL warehouse available."

        resp = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="50s",
        )
        statement_id = resp.statement_id
        while resp.status.state.value in ("PENDING", "RUNNING"):
            time.sleep(0.5)
            resp = w.statement_execution.get_statement(statement_id=statement_id)

        if resp.status.state.value == "FAILED":
            msg = resp.status.error.message if resp.status.error else "SQL failed"
            return None, msg

        if resp.result and resp.result.data_array:
            columns = [col.name for col in resp.manifest.schema.columns]
            df = pd.DataFrame(resp.result.data_array, columns=columns)
            _NUMERIC = {"BIGINT", "INT", "INTEGER", "SMALLINT", "TINYINT",
                        "DOUBLE", "FLOAT", "DECIMAL", "LONG", "SHORT", "BYTE"}
            _TEMPORAL = {"TIMESTAMP", "TIMESTAMP_NTZ", "DATE"}
            for col_info in resp.manifest.schema.columns:
                base_type = (col_info.type_text or "").upper().split("(")[0].strip()
                if base_type in _NUMERIC:
                    df[col_info.name] = pd.to_numeric(df[col_info.name], errors="coerce")
                elif base_type in _TEMPORAL:
                    df[col_info.name] = pd.to_datetime(df[col_info.name], errors="coerce")
                elif base_type == "BOOLEAN":
                    df[col_info.name] = df[col_info.name].map(
                        {"true": True, "false": False, None: None}
                    )
            return df, None
        return pd.DataFrame(), None
    except Exception as exc:
        return None, str(exc)


def execute_sql(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """Execute SQL with 5-minute cache; bust via sidebar Refresh."""
    from dashboards.query_cache import cached_execute, get_cache_key
    from dashboards.sql_tables import adapt_sql_for_databricks

    adapted = adapt_sql_for_databricks(sql)
    return cached_execute(get_cache_key(), adapted)


def _resolve_warehouse_id(w) -> str | None:
    env_wh = os.environ.get("FINOPS_SQL_WAREHOUSE_ID", "").strip()
    if env_wh:
        return env_wh
    warehouses = list(w.warehouses.list())
    for wh in warehouses:
        if wh.enable_serverless_compute:
            return wh.id
    return warehouses[0].id if warehouses else None


_JSON_FETCHERS = {
    "api/clusters_list.json": fetch_clusters_api,
    "api/warehouses_list.json": fetch_warehouses_api,
    "api/jobs_list.json": fetch_jobs_api,
    "api/workspace_status.json": fetch_workspace_status,
}

_JSONL_FETCHERS = {
    "logs/ingestion_pipeline.jsonl": fetch_ingestion_logs,
    "logs/cluster_events.jsonl": fetch_cluster_events_api,
}


def load_json_file_prod(relative_path: str) -> dict | list | None:
    fetcher = _JSON_FETCHERS.get(relative_path.replace("\\", "/"))
    if fetcher is None:
        return None
    try:
        return fetcher()
    except Exception:
        return None


def load_jsonl_file_prod(relative_path: str) -> pd.DataFrame | None:
    fetcher = _JSONL_FETCHERS.get(relative_path.replace("\\", "/"))
    if fetcher is None:
        return None
    try:
        df = fetcher()
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


import streamlit as st  # noqa: E402 — cache decorators for API helpers


@st.cache_data(ttl=120, show_spinner=False)
def fetch_clusters_api_cached(_cache_key: tuple) -> dict:
    return fetch_clusters_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_warehouses_api_cached(_cache_key: tuple) -> dict:
    return fetch_warehouses_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_jobs_api_cached(_cache_key: tuple) -> dict:
    return fetch_jobs_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_cluster_events_cached(_cache_key: tuple) -> pd.DataFrame:
    return fetch_cluster_events_api()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_ingestion_logs_cached(_cache_key: tuple) -> pd.DataFrame:
    return fetch_ingestion_logs()
