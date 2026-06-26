"""Dashboards jobs & workflows."""

import plotly.express as px
import streamlit as st

from dashboards.components import (
    bar_chart,
    data_table,
    grouped_bar_chart,
    line_chart,
    metrics_row,
    page_header,
    pie_chart,
    plotly_figure,
    show_error,
    status_kpi_cards,
    COLORS,
    _drop_blank_categories,
    _sanitize_chart_df,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_ts_date, f_workspace, period_label


def render_runs_overview(run_query) -> None:
    page_header("Overview runs", fq("lakeflow.job_run_timeline"))
    df, err = run_query(f"""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS ok,
               SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) AS ko,
               ROUND(AVG(run_duration_ms)/1000/60, 1) AS avg_min
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    total = int(r["total"] or 1)
    metrics_row([
        (f"Runs ({period_label()})", f"{total:,}", None),
        ("Succès", f"{int(r['ok']):,}", f"{int(r['ok'])/total*100:.0f}%"),
        ("Échecs", f"{int(r['ko']):,}", None),
        ("Durée moy.", f"{r['avg_min']} min", None),
    ])
    daily, _ = run_query(f"""
        SELECT CAST(start_ts AS DATE) AS day, COUNT(*) AS runs
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(daily, "day", "runs", "Runs par jour")


def render_success_rates(run_query) -> None:
    page_header("Taux de succès", "Fiabilité par job")
    df, err = run_query(f"""
        SELECT job_name,
               COUNT(*) AS runs,
               ROUND(100.0 * SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_pct
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
        GROUP BY 1 HAVING COUNT(*) >= 3
        ORDER BY success_pct ASC
    """)
    if show_error(err):
        return
    bar_chart(df, "job_name", "success_pct", "Taux de succès (%) — plus bas = priorité", COLORS["success"], orientation="h")
    data_table(df)


def render_durations_queues(run_query) -> None:
    page_header("Durées & queues", "run_duration vs queue_duration")
    df, err = run_query(f"""
        SELECT job_name,
               ROUND(AVG(run_duration_ms)/1000, 0) AS avg_run_s,
               ROUND(AVG(queue_duration_ms)/1000, 0) AS avg_queue_s,
               ROUND(AVG(execution_duration_ms)/1000, 0) AS avg_exec_s
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
        GROUP BY 1 ORDER BY avg_run_s DESC
    """)
    if show_error(err) or df is None or df.empty:
        return
    grouped_bar_chart(
        df,
        "job_name",
        ["avg_run_s", "avg_queue_s", "avg_exec_s"],
        "Durées moyennes par job (s)",
    )


def render_task_breakdown(run_query) -> None:
    page_header("Breakdown tasks", "job_tasks — types et résultats")
    df, err = run_query(f"""
        SELECT task_type, result_state, COUNT(*) AS tasks
        FROM job_tasks
        WHERE {f_ts_date("start_time")}
        GROUP BY 1, 2 ORDER BY tasks DESC
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        data = _drop_blank_categories(_sanitize_chart_df(df, "task_type", "result_state"), "task_type", "result_state")
        fig = px.sunburst(data, path=["task_type", "result_state"], values="tasks", template="plotly_white")
        plotly_figure(fig, title="Tasks hierarchy")
    data_table(df.head(50) if df is not None else None)


def render_runs_by_team(run_query) -> None:
    page_header("Runs par équipe", "Attribution via custom_tags")
    df, err = run_query(f"""
        SELECT team, result_state, COUNT(*) AS runs
        FROM job_run_timeline_parsed
        WHERE team IS NOT NULL AND {f_ts_date("start_ts")}
        GROUP BY 1, 2
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        data = _drop_blank_categories(_sanitize_chart_df(df, "team", "result_state"), "team", "result_state")
        fig = px.bar(data, x="team", y="runs", color="result_state", template="plotly_white")
        fig.update_xaxes(type="category")
        plotly_figure(fig, title="Runs par équipe")
