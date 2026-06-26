"""Mapping SQL local → Databricks production (system tables + vues enrichies)."""

from __future__ import annotations

import re

from dashboards.catalog_config import get_catalog


def _billing_usage_full(catalog: str) -> str:
    return f"""
SELECT
    record_id,
    account_id,
    workspace_id,
    sku_name,
    cloud,
    usage_start_time,
    usage_end_time,
    usage_date,
    custom_tags,
    usage_unit,
    usage_quantity,
    usage_metadata,
    identity_metadata,
    record_type,
    ingestion_date,
    billing_origin_product,
    usage_type,
    custom_tags['Team'] AS team,
    custom_tags['Environment'] AS environment,
    custom_tags['CostCenter'] AS cost_center,
    custom_tags['Owner'] AS owner,
    usage_metadata.cluster_id AS cluster_id,
    usage_metadata.warehouse_id AS warehouse_id,
    usage_metadata.job_id AS job_id,
    usage_metadata.job_name AS job_name,
    usage_metadata.node_type AS node_type,
    identity_metadata.run_as AS run_as
FROM {catalog}.billing.usage
"""


def _query_history_full(catalog: str) -> str:
    return f"""
SELECT
    account_id,
    workspace_id,
    statement_id,
    session_id,
    execution_status,
    compute,
    executed_by,
    statement_text,
    statement_type,
    error_message,
    client_application,
    client_driver,
    CAST(total_duration_ms AS BIGINT) AS total_duration_ms,
    CAST(total_duration_ms AS BIGINT) AS duration_ms,
    CAST(execution_duration_ms AS BIGINT) AS execution_duration_ms,
    CAST(compilation_duration_ms AS BIGINT) AS compilation_duration_ms,
    CAST(waiting_at_capacity_duration_ms AS BIGINT) AS waiting_at_capacity_duration_ms,
    CAST(waiting_for_compute_duration_ms AS BIGINT) AS waiting_for_compute_duration_ms,
    start_time,
    end_time,
    read_rows,
    produced_rows,
    read_bytes,
    written_bytes,
    spilled_local_bytes,
    shuffle_read_bytes,
    from_result_cache,
    executed_as,
    compute.warehouse_id AS warehouse_id,
    NULL AS warehouse_name,
    NULL AS team,
    NULL AS workload
FROM {catalog}.query.history
"""


def _query_history(catalog: str) -> str:
    return f"""
SELECT
    statement_id,
    session_id,
    executed_by,
    execution_status,
    total_duration_ms AS duration_ms,
    read_bytes,
    start_time,
    statement_type,
    spilled_local_bytes,
    waiting_at_capacity_duration_ms,
    NULL AS warehouse_name,
    NULL AS team,
    execution_duration_ms,
    statement_text
FROM {catalog}.query.history
"""


def _access_audit_parsed(catalog: str) -> str:
    return f"""
SELECT
    *,
    event_time AS event_ts,
    event_date AS event_dt,
    user_identity.email AS user_email,
    response.status_code AS status_code,
    response.error_message AS error_message
FROM {catalog}.access.audit
"""


def _compute_clusters_parsed(catalog: str) -> str:
    return f"""
SELECT
    cluster_id, cluster_name, owned_by, worker_count,
    driver_node_type, auto_termination_minutes, data_security_mode,
    cluster_source, dbr_version, policy_id,
    create_time, change_time, delete_time,
    team, environment, workspace_id
FROM (
    SELECT
        cluster_id, cluster_name, owned_by, worker_count,
        driver_node_type, auto_termination_minutes, data_security_mode,
        cluster_source, dbr_version, policy_id,
        create_time, change_time, delete_time,
        tags['Team']        AS team,
        tags['Environment'] AS environment,
        workspace_id,
        ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS _rn
    FROM {catalog}.compute.clusters
    WHERE cluster_source != 'JOB'
) WHERE _rn = 1
"""


def _job_run_timeline_parsed(catalog: str) -> str:
    return f"""
SELECT
    *,
    period_start_time AS start_ts,
    period_end_time   AS end_ts,
    run_name          AS job_name,
    (UNIX_TIMESTAMP(period_end_time) - UNIX_TIMESTAMP(period_start_time)) * 1000
                      AS run_duration_ms,
    CAST(NULL AS BIGINT) AS queue_duration_ms,
    CAST(NULL AS BIGINT) AS execution_duration_ms,
    NULL AS team
FROM {catalog}.lakeflow.job_run_timeline
"""


def _job_tasks_parsed(catalog: str) -> str:
    return f"""
SELECT
    *,
    period_start_time AS start_ts,
    period_end_time   AS end_ts,
    task_key          AS task_type
FROM {catalog}.lakeflow.job_task_run_timeline
"""


def _enriched_views(catalog: str) -> dict[str, str]:
    return {
        "billing_usage_full": _billing_usage_full(catalog),
        "query_history_full": _query_history_full(catalog),
        "query_history": _query_history(catalog),
        "access_audit_parsed": _access_audit_parsed(catalog),
        "compute_clusters_parsed": _compute_clusters_parsed(catalog),
        "job_run_timeline_parsed": _job_run_timeline_parsed(catalog),
        "job_tasks_parsed": _job_tasks_parsed(catalog),
    }


def _base_tables(catalog: str) -> dict[str, str]:
    prefix = f"{catalog}."
    return {
        "billing_list_prices": f"{prefix}billing.list_prices",
        "access_audit": f"{prefix}access.audit",
        "compute_clusters": f"{prefix}compute.clusters",
        "compute_warehouses": f"{prefix}compute.warehouses",
        "compute_node_timeline": f"{prefix}compute.node_timeline",
        "compute_warehouse_events": f"{prefix}compute.warehouse_events",
        "job_run_timeline": f"{prefix}lakeflow.job_run_timeline",
        "job_tasks": f"{prefix}lakeflow.job_task_run_timeline",
        "workspaces_latest": f"{prefix}access.workspaces_latest",
    }


def _adapt_spark_dialect(sql: str) -> str:
    adapted = sql
    adapted = re.sub(
        r"\bLEFT\s*\(\s*([^,]+?)\s*,\s*(\d+)\s*\)",
        r"substring(\1, 1, \2)",
        adapted,
        flags=re.IGNORECASE,
    )
    adapted = re.sub(
        r"\(CAST\s*\(\s*strftime\s*\(\s*'%w'\s*,\s*([^)]+)\)\s*AS\s*INTEGER\s*\)\s*\+\s*1\)\s*IN\s*\(\s*1\s*,\s*7\s*\)",
        r"dayofweek(\1) IN (1, 7)",
        adapted,
        flags=re.IGNORECASE,
    )
    adapted = re.sub(
        r"\bquantile_cont\s*\(\s*([^,]+?)\s*,\s*([\d.]+)\s*\)",
        r"approx_percentile(\1, \2)",
        adapted,
        flags=re.IGNORECASE,
    )
    adapted = re.sub(
        r"INTERVAL\s+'(\d+)'\s+DAY",
        r"INTERVAL \1 DAY",
        adapted,
        flags=re.IGNORECASE,
    )
    adapted = re.sub(
        r"INTERVAL\s+'(\d+)'\s+MONTH",
        r"INTERVAL \1 MONTH",
        adapted,
        flags=re.IGNORECASE,
    )
    return adapted


_SQL_KEYWORDS = frozenset({
    "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "CROSS", "ON",
    "GROUP", "ORDER", "HAVING", "LIMIT", "UNION", "SELECT", "FROM", "AS",
    "AND", "OR", "NOT", "IN", "IS", "NULL", "BY", "ASC", "DESC", "CASE",
    "WHEN", "THEN", "ELSE", "END", "WITH", "FULL",
})


def _substitute_enriched_views(adapted: str, enriched_views: dict[str, str]) -> str:
    """Inline enriched views; preserve an optional table alias (e.g. ``billing_usage_full b``)."""
    for view_name, subquery in sorted(enriched_views.items(), key=lambda x: -len(x[0])):
        wrapped = f"({subquery.strip()})"

        def _with_alias(match: re.Match) -> str:
            alias = match.group(1)
            if alias.upper() in _SQL_KEYWORDS:
                return match.group(0)
            return f"{wrapped} AS {alias}"

        adapted = re.sub(
            rf"\b{re.escape(view_name)}\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)\b",
            _with_alias,
            adapted,
            flags=re.IGNORECASE,
        )
        adapted = re.sub(
            rf"\b{re.escape(view_name)}\b",
            f"{wrapped} AS {view_name}",
            adapted,
            flags=re.IGNORECASE,
        )
    return adapted


def adapt_sql_for_databricks(sql: str) -> str:
    catalog = get_catalog()
    base_tables = _base_tables(catalog)
    enriched_views = _enriched_views(catalog)

    adapted = _adapt_spark_dialect(sql)

    # BASE_TABLES must run first: replaces short aliases in the user's original SQL.
    # ENRICHED_VIEWS run second: their subqueries already contain fully-qualified names
    # and must not be subject to a second BASE_TABLES pass (which would cause
    # double-qualification such as system.lakeflow.system.lakeflow.job_run_timeline).
    for local_name, remote_name in sorted(base_tables.items(), key=lambda x: -len(x[0])):
        adapted = re.sub(
            rf"\b{re.escape(local_name)}\b",
            remote_name,
            adapted,
            flags=re.IGNORECASE,
        )

    adapted = _substitute_enriched_views(adapted, enriched_views)

    return adapted
