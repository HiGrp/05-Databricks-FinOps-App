"""Top-of-page KPI summaries per category (3 metrics each)."""

from __future__ import annotations

from dashboards.components import format_int, int_or_zero, kpi_cards, show_error
from dashboards.date_filter import f_event_date, f_ts_date, f_usage_date, period_label


def _period() -> str:
    return period_label()


def render_finops_summary(run_query) -> None:
    df, err = run_query(f"""
        SELECT
            (SELECT SUM(usage_quantity) FROM billing_usage_full
             WHERE {f_usage_date()}) AS dbu,
            (SELECT COUNT(DISTINCT team) FROM billing_usage_full
             WHERE {f_usage_date()}) AS teams,
            (SELECT SUM(u.usage_quantity
                        * CAST(json_extract_string(p.pricing, '$.default') AS DOUBLE))
             FROM billing_usage_full u
             JOIN billing_list_prices p ON u.sku_name = p.sku_name
             WHERE {f_usage_date('u.usage_date')}) AS cost
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    cost = r["cost"]
    cost_val = f"${float(cost):,.0f}" if cost is not None and cost == cost else "—"
    kpi_cards([
        {"label": "DBU", "value": format_int(r["dbu"]), "icon": "💰", "delta": _period(),
         "help": "Total DBU in the selected period."},
        {"label": "Est. cost", "value": cost_val, "icon": "💵",
         "help": "Estimated cost = usage × SKU list price (USD, list price)."},
        {"label": "Teams", "value": format_int(r["teams"]), "icon": "👥",
         "help": "Distinct teams with usage (chargeback scope)."},
    ])


def render_optimization_summary(run_query) -> None:
    df, err = run_query(f"""
        SELECT
            (SELECT COUNT(DISTINCT cluster_id) FROM billing_usage_full
             WHERE cluster_id IS NOT NULL AND {f_usage_date()}
               AND (CAST(strftime('%w', usage_date) AS INTEGER) + 1) IN (1, 7)) AS weekend_clusters,
            (SELECT COUNT(*) FROM job_run_timeline_parsed
             WHERE result_state = 'FAILED' AND {f_ts_date("start_ts")}) AS failed_jobs,
            (SELECT COUNT(*) FROM query_history_full
             WHERE spilled_local_bytes > 1e9 AND {f_ts_date("start_time")}) AS spill_queries
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    kpi_cards([
        {"label": "Weekend clusters", "value": format_int(r["weekend_clusters"]), "icon": "👻",
         "help": "Clusters with usage on Sat/Sun."},
        {"label": "Failed jobs", "value": format_int(r["failed_jobs"]), "icon": "🛑",
         "help": "Job runs that failed in the period."},
        {"label": "Spill queries", "value": format_int(r["spill_queries"]), "icon": "💾",
         "help": "SQL queries with spill over 1 GB."},
    ])


def render_security_summary(run_query) -> None:
    df, err = run_query(f"""
        SELECT COUNT(*) AS events,
               SUM(CASE WHEN status_code = 403 THEN 1 ELSE 0 END) AS denied,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors
        FROM access_audit_parsed
        WHERE {f_event_date()}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    kpi_cards([
        {"label": "Audit events", "value": format_int(r["events"]), "icon": "📋", "delta": _period(),
         "help": "All audit log events in the period."},
        {"label": "403 denied", "value": format_int(r["denied"]), "icon": "🚫",
         "help": "Access denied events (HTTP 403)."},
        {"label": "Errors 4xx/5xx", "value": format_int(r["errors"]), "icon": "⚠️",
         "help": "All failed audit calls (client + server errors)."},
    ])


def render_compute_summary(run_query) -> None:
    df, err = run_query("""
        SELECT COUNT(*) AS clusters,
               SUM(CASE WHEN worker_count = 0 THEN 1 ELSE 0 END) AS single_node,
               COUNT(DISTINCT dbr_version) AS runtimes
        FROM compute_clusters_parsed
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    kpi_cards([
        {"label": "Clusters", "value": format_int(r["clusters"]), "icon": "🖥️",
         "help": "All-purpose and shared clusters."},
        {"label": "Single-node", "value": format_int(r["single_node"]), "icon": "🧩",
         "help": "Clusters running driver-only (zero workers)."},
        {"label": "DBR versions", "value": format_int(r["runtimes"]), "icon": "⚙️",
         "help": "Distinct runtime versions in use."},
    ])


def render_jobs_summary(run_query) -> None:
    df, err = run_query(f"""
        SELECT COUNT(*) AS runs,
               SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS ok,
               ROUND(AVG(run_duration_ms) / 1000 / 60, 1) AS avg_min
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    total = int_or_zero(r["runs"])
    ok = int_or_zero(r["ok"])
    pct = f"{ok / total * 100:.0f}%" if total else "—"
    avg_min = r["avg_min"]
    if avg_min != avg_min:  # NaN
        avg_min = None
    kpi_cards([
        {"label": "Runs", "value": f"{total:,}", "icon": "🔄", "delta": _period(),
         "help": "Job runs in the period."},
        {"label": "Success rate", "value": pct, "icon": "✅",
         "help": "Share of runs that succeeded."},
        {"label": "Avg duration", "value": f"{avg_min} min" if avg_min is not None else "—", "icon": "⏱️",
         "help": "Average job run duration."},
    ])


def render_sql_summary(run_query) -> None:
    df, err = run_query(f"""
        SELECT COUNT(*) AS queries,
               ROUND(AVG(total_duration_ms), 0) AS avg_ms,
               ROUND(100.0 * SUM(CASE WHEN from_result_cache THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS cache_pct
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    cache_val = r["cache_pct"]
    if cache_val != cache_val:
        cache_val = None
    kpi_cards([
        {"label": "Queries", "value": format_int(r["queries"]), "icon": "📊", "delta": _period(),
         "help": "SQL queries in the period."},
        {"label": "Avg latency", "value": format_int(r["avg_ms"], "ms"), "icon": "⏱️",
         "help": "Average query duration."},
        {"label": "Cache hit", "value": f"{cache_val}%" if cache_val is not None else "—", "icon": "💨",
         "help": "Queries served from result cache."},
    ])


def render_platform_summary(run_query) -> None:
    from dashboards.query_cache import get_cache_key
    from prod_data import fetch_clusters_api_cached, fetch_jobs_api_cached, fetch_warehouses_api_cached

    key = get_cache_key()
    try:
        clusters = fetch_clusters_api_cached(key)
        warehouses = fetch_warehouses_api_cached(key)
        jobs = fetch_jobs_api_cached(key)
        n_clusters = len(clusters.get("clusters", []))
        n_wh = len(warehouses.get("warehouses", []))
        n_jobs = len(jobs.get("jobs", []))
    except Exception:
        n_clusters = n_wh = n_jobs = 0

    kpi_cards([
        {"label": "Clusters (API)", "value": str(n_clusters), "icon": "🖥️",
         "help": "Clusters returned by live API."},
        {"label": "Warehouses (API)", "value": str(n_wh), "icon": "🏭",
         "help": "SQL warehouses from live API."},
        {"label": "Jobs (API)", "value": str(n_jobs), "icon": "🔄",
         "help": "Jobs from live API."},
    ])
