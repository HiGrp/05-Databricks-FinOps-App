"""Dashboards SQL & warehouses."""

import plotly.express as px
import streamlit as st

from dashboards.components import (
    bar_chart,
    data_table,
    line_chart,
    metrics_row,
    page_header,
    pie_chart,
    plotly_figure,
    show_error,
    format_int,
    int_or_zero,
    _drop_blank_categories,
    _sanitize_chart_df,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_ts_date, f_workspace, period_label


def render_query_performance(run_query) -> None:
    page_header("Performance globale", f"{fq('query.history')} — latences")
    df, err = run_query(f"""
        SELECT COUNT(*) AS queries,
               ROUND(AVG(total_duration_ms), 0) AS avg_ms,
               ROUND(quantile_cont(total_duration_ms, 0.95), 0) AS p95_ms,
               SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) AS failed
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    metrics_row([
        (f"Requêtes ({period_label()})", format_int(r["queries"]), None),
        ("Latence moy.", format_int(r["avg_ms"], "ms"), None),
        ("P95", format_int(r["p95_ms"], "ms"), None),
        ("Échecs", format_int(r["failed"]), None),
    ])
    daily, _ = run_query(f"""
        SELECT CAST(start_time AS DATE) AS day,
               ROUND(AVG(total_duration_ms), 0) AS avg_ms
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(daily, "day", "avg_ms", "Latence moyenne journalière")


def render_queue_analysis(run_query) -> None:
    page_header("Queues & capacity", "waiting_at_capacity_duration_ms")
    df, err = run_query(f"""
        SELECT warehouse_name,
               ROUND(AVG(waiting_at_capacity_duration_ms), 0) AS avg_queue_ms,
               COUNT(*) AS queries
        FROM query_history_full
        WHERE {f_ts_date("start_time")} AND warehouse_name IS NOT NULL
        GROUP BY 1 ORDER BY avg_queue_ms DESC
    """)
    if show_error(err):
        return
    bar_chart(df, "warehouse_name", "avg_queue_ms", "Temps d'attente moyen par warehouse")
    top, _ = run_query(f"""
        SELECT executed_by, waiting_at_capacity_duration_ms, warehouse_name
        FROM query_history_full
        WHERE waiting_at_capacity_duration_ms > 60000
          AND {f_ts_date("start_time")}
        ORDER BY waiting_at_capacity_duration_ms DESC LIMIT 20
    """)
    data_table(top)


def render_by_user(run_query) -> None:
    page_header("Par utilisateur", "Charge SQL par executed_by")
    df, err = run_query(f"""
        SELECT executed_by,
               COUNT(*) AS queries,
               ROUND(AVG(total_duration_ms), 0) AS avg_ms,
               SUM(read_bytes)/1e12 AS read_tb
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
        GROUP BY 1 ORDER BY queries DESC LIMIT 20
    """)
    if show_error(err):
        return
    c1, c2 = st.columns(2)
    with c1:
        bar_chart(df, "executed_by", "queries", "Nombre de requêtes", orientation="h")
    with c2:
        bar_chart(df, "executed_by", "avg_ms", "Latence moyenne", orientation="h")


def render_statement_types(run_query) -> None:
    page_header("Types de statements", "SELECT, INSERT, OPTIMIZE…")
    df, err = run_query(f"""
        SELECT statement_type, execution_status, COUNT(*) AS n
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
        GROUP BY 1, 2
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        data = _drop_blank_categories(_sanitize_chart_df(df, "statement_type", "execution_status"), "statement_type", "execution_status")
        fig = px.bar(data, x="statement_type", y="n", color="execution_status", template="plotly_white")
        fig.update_xaxes(type="category")
        plotly_figure(fig, title="Statements par type et statut")


def render_warehouse_activity(run_query) -> None:
    page_header("Activité warehouses", "Requêtes et événements WH")
    c1, c2 = st.columns(2)
    with c1:
        q, err = run_query(f"""
            SELECT warehouse_name, COUNT(*) AS queries
            FROM query_history_full
            WHERE warehouse_name IS NOT NULL AND {f_ts_date("start_time")}
            GROUP BY 1 ORDER BY queries DESC
        """)
        if not show_error(err):
            pie_chart(q, "warehouse_name", "queries", "Requêtes par warehouse")
    with c2:
        wh, _ = run_query("""
            SELECT warehouse_name, warehouse_size, state, enable_serverless_compute
            FROM compute_warehouses
        """)
        data_table(wh)


def render_cache_spill(run_query) -> None:
    page_header("Cache & spill", "from_result_cache vs spill")
    df, err = run_query(f"""
        SELECT
            SUM(CASE WHEN from_result_cache THEN 1 ELSE 0 END) AS cached,
            SUM(CASE WHEN spilled_local_bytes > 0 THEN 1 ELSE 0 END) AS spilled,
            COUNT(*) AS total
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    metrics_row([
        ("Total requêtes", format_int(r["total"]), None),
        ("Servies par cache", format_int(r["cached"]), None),
        ("Avec spill", format_int(r["spilled"]), None),
    ])
    ratio, _ = run_query(f"""
        SELECT CAST(start_time AS DATE) AS day,
               ROUND(100.0 * SUM(CASE WHEN from_result_cache THEN 1 ELSE 0 END) / COUNT(*), 1) AS cache_pct
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(ratio, "day", "cache_pct", "Taux cache (%)")
