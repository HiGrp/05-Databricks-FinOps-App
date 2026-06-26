"""Page d'accueil — KPIs globaux."""

import streamlit as st

from dashboards.components import (
    bar_chart,
    kpi_cards,
    line_chart,
    page_header,
    pie_chart,
    show_empty,
    show_error,
    status_kpi_cards,
    two_column_charts,
)
from dashboards.date_filter import f_event_date, f_ts_date, f_usage_date, f_workspace, period_label


def render_overview(run_query) -> None:
    page_header(
        "Vue d'ensemble",
        f"Pilotage unifié FinOps, optimisation, sécurité, compute, jobs et SQL. Période : {period_label()}.",
        category="Accueil",
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
        {"label": "DBU consommés", "value": f"{float(row['dbu_period'] or 0):,.0f}", "icon": "💰", "delta": pl},
        {"label": "Requêtes SQL", "value": f"{int(row['queries_period'] or 0):,}", "icon": "📊", "delta": pl},
        {"label": "Events audit", "value": f"{int(row['audit_period'] or 0):,}", "icon": "🔒", "delta": pl},
        {"label": "Jobs en échec", "value": f"{int(row['failed_jobs_period'] or 0):,}", "icon": "⚠️", "delta": pl},
        {"label": "Clusters", "value": str(int(row["cluster_count"] or 0)), "icon": "🖥️"},
        {"label": "Warehouses", "value": str(int(row["warehouse_count"] or 0)), "icon": "🏭"},
    ])

    def left():
        trend, _ = run_query(f"""
            SELECT usage_date, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY 1
        """)
        line_chart(trend, "usage_date", "dbu", "Consommation DBU")

    def right():
        sku, _ = run_query(f"""
            SELECT billing_origin_product AS product, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 8
        """)
        pie_chart(sku, "product", "dbu", "Mix produit")

    two_column_charts(left, right)

    def audit_chart():
        audit, _ = run_query(f"""
            SELECT service_name, COUNT(*) AS events
            FROM access_audit_parsed
            WHERE {f_event_date()}
            GROUP BY 1 ORDER BY events DESC LIMIT 10
        """)
        bar_chart(audit, "service_name", "events", "Top services audit", orientation="h")

    def jobs_chart():
        jobs, _ = run_query(f"""
            SELECT result_state, COUNT(*) AS runs
            FROM job_run_timeline_parsed
            WHERE {f_ts_date("start_ts")}
            GROUP BY 1
        """)
        if jobs is not None and not jobs.empty:
            pie_chart(jobs, "result_state", "runs", "État des job runs")
        else:
            show_empty()

    two_column_charts(audit_chart, jobs_chart)
