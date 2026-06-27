"""Home page — global KPIs."""

import streamlit as st

from dashboards.chart_help import HELP
from dashboards.components import (
    bar_chart,
    kpi_cards,
    line_chart,
    page_header,
    pie_chart,
    render_page_toolbar,
    show_empty,
    show_error,
    two_column_charts,
)
from dashboards.date_filter import f_event_date, f_ts_date, f_usage_date, period_label


def render_overview(run_query) -> None:
    render_page_toolbar()
    page_header(
        "Overview",
        "FinOps, optimization, security, compute, jobs, and SQL in one place.",
        category="Home",
        badge="Live",
        icon="📈",
    )

    kpi_sql = f"""
        SELECT
            (SELECT SUM(usage_quantity) FROM billing_usage_full
             WHERE {f_usage_date()}) AS dbu_period,
            (SELECT COUNT(*) FROM query_history_full
             WHERE {f_ts_date("start_time")}) AS queries_period,
            (SELECT COUNT(*) FROM access_audit_parsed
             WHERE {f_event_date()}) AS audit_period,
            (SELECT COUNT(*) FROM job_run_timeline_parsed
             WHERE result_state = 'FAILED'
               AND {f_ts_date("start_ts")}) AS failed_jobs_period,
            (SELECT COUNT(*) FROM compute_clusters_parsed) AS cluster_count,
            (SELECT COUNT(*) FROM compute_warehouses) AS warehouse_count
    """
    df, err = run_query(kpi_sql)
    if show_error(err) or df is None or df.empty:
        return

    row = df.iloc[0]
    pl = period_label()
    kpi_cards([
        {
            "label": "DBU used",
            "value": f"{float(row['dbu_period'] or 0):,.0f}",
            "icon": "💰",
            "delta": pl,
            "help": "Total Databricks Units (DBU) in the selected period.",
        },
        {
            "label": "SQL queries",
            "value": f"{int(row['queries_period'] or 0):,}",
            "icon": "📊",
            "delta": pl,
            "help": "Number of SQL queries run in the period.",
        },
        {
            "label": "Audit events",
            "value": f"{int(row['audit_period'] or 0):,}",
            "icon": "🔒",
            "delta": pl,
            "help": "Security and admin actions logged in audit.",
        },
        {
            "label": "Failed jobs",
            "value": f"{int(row['failed_jobs_period'] or 0):,}",
            "icon": "⚠️",
            "delta": pl,
            "help": "Job runs that ended with FAILED status.",
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
