"""Jobs & workflows dashboards."""

import plotly.express as px

from dashboards.chart_help import HELP
from dashboards.components import (
    bar_chart,
    data_table,
    grouped_bar_chart,
    line_chart,
    page_header,
    plotly_figure,
    show_error,
    COLORS,
    _drop_blank_categories,
    _chart_labels,
    _prepare_chart_df,
    _sanitize_chart_df,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_ts_date


def render_runs_overview(run_query) -> None:
    page_header("Run overview", fq("lakeflow.job_run_timeline"))
    daily, err = run_query(f"""
        SELECT CAST(start_ts AS DATE) AS day, COUNT(*) AS runs
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
        GROUP BY 1 ORDER BY 1
    """)
    if show_error(err):
        return
    line_chart(daily, "day", "runs", "Runs per day", help=HELP["runs_per_day"])


def render_success_rates(run_query) -> None:
    page_header("Success rate", "Reliability per job")
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
    bar_chart(
        df, "job_name", "success_pct", "Success rate (%) - fix low bars first",
        COLORS["success"], orientation="h", help=HELP["success_rate"],
    )
    data_table(df, title="Success rate by job", help=HELP["tbl_job_success"])


def render_durations_queues(run_query) -> None:
    page_header("Duration & queue", "Run time vs queue time")
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
        "Avg duration per job (s)",
        help=HELP["job_durations"],
    )


def render_task_breakdown(run_query) -> None:
    page_header("Tasks", "Tasks by type and result")
    df, err = run_query(f"""
        SELECT task_type, result_state, COUNT(*) AS tasks
        FROM job_tasks_parsed
        WHERE {f_ts_date("start_ts")}
        GROUP BY 1, 2 ORDER BY tasks DESC
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        data = _prepare_chart_df(df, "task_type", "result_state")
        fig = px.sunburst(
            data,
            path=["task_type", "result_state"],
            values="tasks",
            labels=_chart_labels("task_type", "result_state", "tasks"),
            template="plotly_white",
        )
        plotly_figure(fig, title="Task breakdown", help=HELP["tasks_hierarchy"])
    data_table(df.head(50) if df is not None else None, title="Task breakdown", help=HELP["tbl_job_tasks"])


def render_runs_by_team(run_query) -> None:
    page_header("By team", "Runs by team tag")
    df, err = run_query(f"""
        SELECT team, result_state, COUNT(*) AS runs
        FROM job_run_timeline_parsed
        WHERE team IS NOT NULL AND {f_ts_date("start_ts")}
        GROUP BY 1, 2
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        data = _prepare_chart_df(df, "team", "runs", color="result_state")
        fig = px.bar(
            data,
            x="team",
            y="runs",
            color="result_state",
            labels=_chart_labels("team", "runs", "result_state"),
            template="plotly_white",
        )
        fig.update_xaxes(type="category")
        plotly_figure(fig, title="Runs by team", help=HELP["runs_by_team"])
