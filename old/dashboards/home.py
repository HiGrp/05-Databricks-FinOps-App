"""Home page - global KPIs."""

from dashboards.chart_help import HELP
from dashboards.components import (
    bar_chart,
    kpi_cards,
    line_chart,
    pie_chart,
    show_empty,
    show_error,
    two_column_charts,
)
from dashboards.date_filter import (
    f_event_date,
    f_event_date_prev,
    f_ts_date,
    f_ts_date_prev,
    f_usage_date,
    f_usage_date_prev,
)


def _delta(cur, prev, tone: str = "off"):
    """Return (delta_text, tone) comparing current vs previous period.

    tone="off"  -> neutral grey (informational).
    tone="up"   -> "inverse" colouring: an increase shows red (cost/reliability).
    """
    cur = float(cur or 0)
    prev = float(prev or 0)
    if prev <= 0:
        return None, "off"
    pct = (cur - prev) / prev * 100
    return f"{pct:+.0f}% vs prev", tone


def render_overview_kpis(run_query) -> None:
    kpi_sql = f"""
        SELECT
            (SELECT SUM(usage_quantity) FROM billing_usage_full
             WHERE {f_usage_date()}) AS dbu_period,
            (SELECT SUM(usage_quantity) FROM billing_usage_full
             WHERE {f_usage_date_prev()}) AS dbu_prev,
            (SELECT COUNT(*) FROM query_history_full
             WHERE {f_ts_date("start_time")}) AS queries_period,
            (SELECT COUNT(*) FROM query_history_full
             WHERE {f_ts_date_prev("start_time")}) AS queries_prev,
            (SELECT COUNT(*) FROM access_audit_parsed
             WHERE {f_event_date()}) AS audit_period,
            (SELECT COUNT(*) FROM access_audit_parsed
             WHERE {f_event_date_prev()}) AS audit_prev,
            (SELECT COUNT(*) FROM job_run_timeline_parsed
             WHERE result_state = 'FAILED'
               AND {f_ts_date("start_ts")}) AS failed_jobs_period,
            (SELECT COUNT(*) FROM job_run_timeline_parsed
             WHERE result_state = 'FAILED'
               AND {f_ts_date_prev("start_ts")}) AS failed_jobs_prev,
            (SELECT COUNT(*) FROM compute_clusters_parsed) AS cluster_count,
            (SELECT COUNT(*) FROM compute_warehouses) AS warehouse_count
    """
    df, err = run_query(kpi_sql)
    if show_error(err) or df is None or df.empty:
        return

    row = df.iloc[0]
    dbu_delta, dbu_tone = _delta(row["dbu_period"], row["dbu_prev"], tone="up")
    q_delta, q_tone = _delta(row["queries_period"], row["queries_prev"])
    a_delta, a_tone = _delta(row["audit_period"], row["audit_prev"])
    f_delta, f_tone = _delta(row["failed_jobs_period"], row["failed_jobs_prev"], tone="up")
    kpi_cards([
        {
            "label": "DBU used",
            "value": f"{float(row['dbu_period'] or 0):,.0f}",
            "icon": "💰",
            "delta": dbu_delta,
            "delta_tone": dbu_tone,
            "help": "Total Databricks Units (DBU) in the period, vs the previous equal-length period.",
        },
        {
            "label": "SQL queries",
            "value": f"{int(row['queries_period'] or 0):,}",
            "icon": "📊",
            "delta": q_delta,
            "delta_tone": q_tone,
            "help": "Number of SQL queries run in the period, vs the previous period.",
        },
        {
            "label": "Audit events",
            "value": f"{int(row['audit_period'] or 0):,}",
            "icon": "🔒",
            "delta": a_delta,
            "delta_tone": a_tone,
            "help": "Security and admin actions logged in audit, vs the previous period.",
        },
        {
            "label": "Failed jobs",
            "value": f"{int(row['failed_jobs_period'] or 0):,}",
            "icon": "⚠️",
            "delta": f_delta,
            "delta_tone": f_tone,
            "help": "Job runs that ended with FAILED status, vs the previous period.",
        },
        {
            "label": "Clusters",
            "value": str(int(row["cluster_count"] or 0)),
            "icon": "🖥️",
            "help": "All-purpose and shared clusters (not job clusters).",
        },
        {
            "label": "Warehouses",
            "value": str(int(row["warehouse_count"] or 0)),
            "icon": "🏭",
            "help": "SQL warehouses in the workspace.",
        },
    ])


def render_overview_cost(run_query) -> None:
    def left():
        trend, _ = run_query(f"""
            SELECT usage_date, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY 1
        """)
        line_chart(trend, "usage_date", "dbu", "DBU usage", help=HELP["dbu_usage"])

    def right():
        sku, _ = run_query(f"""
            SELECT billing_origin_product AS product, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 8
        """)
        pie_chart(sku, "product", "dbu", "Product mix", help=HELP["product_mix"])

    two_column_charts(left, right)


def render_overview_activity(run_query) -> None:
    def audit_chart():
        audit, _ = run_query(f"""
            SELECT service_name, COUNT(*) AS events
            FROM access_audit_parsed
            WHERE {f_event_date()}
            GROUP BY 1 ORDER BY events DESC LIMIT 10
        """)
        bar_chart(
            audit, "service_name", "events", "Top audit services",
            orientation="h", help=HELP["top_audit_services"],
        )

    def jobs_chart():
        jobs, _ = run_query(f"""
            SELECT result_state, COUNT(*) AS runs
            FROM job_run_timeline_parsed
            WHERE {f_ts_date("start_ts")}
            GROUP BY 1
        """)
        if jobs is not None and not jobs.empty:
            pie_chart(jobs, "result_state", "runs", "Job run status", help=HELP["job_run_status"])
        else:
            show_empty()

    two_column_charts(audit_chart, jobs_chart)
