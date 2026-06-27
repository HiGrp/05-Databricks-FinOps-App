"""Mapping SQL local → Databricks production (system tables + vues enrichies)."""

from __future__ import annotations

import re

from dashboards.catalog_config import get_catalog


def _clusters_latest(catalog: str) -> str:
    return f"""(
        SELECT cluster_id, cluster_name
        FROM (
            SELECT cluster_id, cluster_name,
                   ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS _rn
            FROM {catalog}.compute.clusters
        ) WHERE _rn = 1
    )"""


def _warehouses_latest(catalog: str) -> str:
    return f"""(
        SELECT warehouse_id, warehouse_name
        FROM (
            SELECT warehouse_id, warehouse_name,
                   ROW_NUMBER() OVER (PARTITION BY warehouse_id ORDER BY change_time DESC) AS _rn
            FROM {catalog}.compute.warehouses
        ) WHERE _rn = 1
    )"""


def _jobs_latest(catalog: str) -> str:
    return f"""(
        SELECT job_id, name AS job_name
        FROM (
            SELECT job_id, name,
                   ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY change_time DESC) AS _rn
            FROM {catalog}.lakeflow.jobs
        ) WHERE _rn = 1
    )"""


def _billing_usage_full(catalog: str) -> str:
    return f"""
SELECT
    u.record_id,
    u.account_id,
    u.workspace_id,
    u.sku_name,
    u.cloud,
    u.usage_start_time,
    u.usage_end_time,
    u.usage_date,
    u.custom_tags,
    u.usage_unit,
    u.usage_quantity,
    u.usage_metadata,
    u.identity_metadata,
    u.record_type,
    u.ingestion_date,
    u.billing_origin_product,
    u.usage_type,
    u.team,
    u.environment,
    u.cost_center,
    u.owner,
    u.cluster_id,
    u.warehouse_id,
    u.job_id,
    u.node_type,
    COALESCE(
        NULLIF(TRIM(cl.cluster_name), ''),
        CASE WHEN u.cluster_id IS NOT NULL AND TRIM(u.cluster_id) != ''
             THEN CONCAT('Cluster ', SUBSTRING(u.cluster_id, 1, 8)) END
    ) AS cluster_name,
    COALESCE(
        NULLIF(TRIM(wh.warehouse_name), ''),
        CASE WHEN u.warehouse_id IS NOT NULL AND TRIM(u.warehouse_id) != ''
             THEN CONCAT('Warehouse ', SUBSTRING(u.warehouse_id, 1, 8)) END
    ) AS warehouse_name,
    COALESCE(
        NULLIF(TRIM(u.job_name), ''),
        NULLIF(TRIM(j.job_name), ''),
        CASE WHEN u.job_id IS NOT NULL AND TRIM(u.job_id) != ''
             THEN CONCAT('Job ', SUBSTRING(u.job_id, 1, 8)) END
    ) AS job_name,
    CASE
        WHEN u.run_as LIKE '%@%' THEN u.run_as
        WHEN NULLIF(TRIM(u.owner), '') IS NOT NULL THEN u.owner
        WHEN u.run_as IS NOT NULL AND TRIM(u.run_as) != ''
             THEN CONCAT('Identity ', SUBSTRING(u.run_as, 1, 8))
        ELSE NULL
    END AS run_as
FROM (
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
) u
LEFT JOIN {_clusters_latest(catalog)} cl ON u.cluster_id = cl.cluster_id
LEFT JOIN {_warehouses_latest(catalog)} wh ON u.warehouse_id = wh.warehouse_id
LEFT JOIN {_jobs_latest(catalog)} j ON u.job_id = j.job_id
"""


def _query_history_full(catalog: str) -> str:
    return f"""
SELECT
    q.account_id,
    q.workspace_id,
    q.statement_id,
    q.session_id,
    q.execution_status,
    q.compute,
    COALESCE(NULLIF(TRIM(q.executed_as), ''), NULLIF(TRIM(q.executed_by), '')) AS executed_by,
    q.statement_text,
    q.statement_type,
    q.error_message,
    q.client_application,
    q.client_driver,
    CAST(q.total_duration_ms AS BIGINT) AS total_duration_ms,
    CAST(q.total_duration_ms AS BIGINT) AS duration_ms,
    CAST(q.execution_duration_ms AS BIGINT) AS execution_duration_ms,
    CAST(q.compilation_duration_ms AS BIGINT) AS compilation_duration_ms,
    CAST(q.waiting_at_capacity_duration_ms AS BIGINT) AS waiting_at_capacity_duration_ms,
    CAST(q.waiting_for_compute_duration_ms AS BIGINT) AS waiting_for_compute_duration_ms,
    q.start_time,
    q.end_time,
    q.read_rows,
    q.produced_rows,
    q.read_bytes,
    q.written_bytes,
    q.spilled_local_bytes,
    q.shuffle_read_bytes,
    q.from_result_cache,
    q.executed_as,
    q.warehouse_id,
    COALESCE(
        NULLIF(TRIM(wh.warehouse_name), ''),
        CASE WHEN q.warehouse_id IS NOT NULL AND TRIM(q.warehouse_id) != ''
             THEN CONCAT('Warehouse ', SUBSTRING(q.warehouse_id, 1, 8)) END
    ) AS warehouse_name,
    NULL AS team,
    NULL AS workload
FROM (
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
        total_duration_ms,
        execution_duration_ms,
        compilation_duration_ms,
        waiting_at_capacity_duration_ms,
        waiting_for_compute_duration_ms,
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
        compute.warehouse_id AS warehouse_id
    FROM {catalog}.query.history
) q
LEFT JOIN {_warehouses_latest(catalog)} wh ON q.warehouse_id = wh.warehouse_id
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
    t.*,
    t.period_start_time AS start_ts,
    t.period_end_time   AS end_ts,
    COALESCE(
        NULLIF(TRIM(t.run_name), ''),
        NULLIF(TRIM(j.job_name), ''),
        CASE WHEN t.job_id IS NOT NULL AND TRIM(t.job_id) != ''
             THEN CONCAT('Job ', SUBSTRING(t.job_id, 1, 8)) END
    ) AS job_name,
    (UNIX_TIMESTAMP(t.period_end_time) - UNIX_TIMESTAMP(t.period_start_time)) * 1000
                      AS run_duration_ms,
    CAST(NULL AS BIGINT) AS queue_duration_ms,
    CAST(NULL AS BIGINT) AS execution_duration_ms,
    NULL AS team
FROM {catalog}.lakeflow.job_run_timeline t
LEFT JOIN {_jobs_latest(catalog)} j ON t.job_id = j.job_id
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


def _compute_warehouses_parsed(catalog: str) -> str:
    return f"""
SELECT
    warehouse_id, warehouse_name, warehouse_size, state,
    workspace_id, warehouse_type
FROM (
    SELECT
        warehouse_id, warehouse_name, warehouse_size, state,
        workspace_id, warehouse_type,
        ROW_NUMBER() OVER (PARTITION BY warehouse_id ORDER BY change_time DESC) AS _rn
    FROM {catalog}.compute.warehouses
) WHERE _rn = 1
"""


def _enriched_views(catalog: str) -> dict[str, str]:
    return {
        "billing_usage_full": _billing_usage_full(catalog),
        "query_history_full": _query_history_full(catalog),
        "query_history": _query_history(catalog),
        "access_audit_parsed": _access_audit_parsed(catalog),
        "compute_clusters_parsed": _compute_clusters_parsed(catalog),
        "compute_warehouses_parsed": _compute_warehouses_parsed(catalog),
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
