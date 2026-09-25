"""Optimization dashboards."""

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboards.chart_help import HELP
from dashboards.components import (
    bar_chart,
    data_table,
    metrics_row,
    page_header,
    plotly_figure,
    show_error,
    COLORS,
    _chart_labels,
    _prepare_chart_df,
)
from dashboards.date_filter import f_event_date, f_ts_date, f_usage_date, period_label


def render_ghost_clusters(run_query) -> None:
    page_header("Weekend clusters", "Clusters active on Sat/Sun — likely waste")
    wk, _ = run_query(f"""
        SELECT SUM(usage_quantity) AS total,
               SUM(CASE WHEN (CAST(strftime('%w', usage_date) AS INTEGER) + 1) IN (1, 7)
                        THEN usage_quantity ELSE 0 END) AS weekend
        FROM billing_usage_full
        WHERE {f_usage_date()}
    """)
    if wk is not None and not wk.empty:
        total = float(wk.iloc[0]["total"] or 0)
        weekend = float(wk.iloc[0]["weekend"] or 0)
        pct = (weekend / total * 100) if total else 0
        tone = "up" if pct > 0 else "neutral"
        metrics_row([
            {"label": "Weekend DBU", "value": f"{pct:.0f}%", "delta": f"{weekend:,.0f} DBU",
             "delta_tone": tone,
             "help": "Share of DBU consumed on Sat/Sun — typically avoidable waste."},
            {"label": "Weekday DBU", "value": f"{100 - pct:.0f}%",
             "help": "Share of DBU consumed Mon–Fri."},
        ])
    df, err = run_query(f"""
        SELECT COALESCE(c.cluster_name,
               CONCAT('Cluster ', SUBSTRING(b.cluster_id, 1, 8))) AS cluster_name,
               SUM(b.usage_quantity) AS weekend_dbu
        FROM billing_usage_full b
        LEFT JOIN compute_clusters_parsed c ON b.cluster_id = c.cluster_id
        WHERE (CAST(strftime('%w', b.usage_date) AS INTEGER) + 1) IN (1, 7)
          AND {f_usage_date('b.usage_date')}
          AND b.cluster_id IS NOT NULL
        GROUP BY 1 ORDER BY weekend_dbu DESC LIMIT 15
    """)
    if show_error(err):
        return
    bar_chart(df, "cluster_name", "weekend_dbu", "Weekend DBU by cluster", COLORS["danger"], help=HELP["weekend_cluster_dbu"])
    joined, _ = run_query(f"""
        SELECT c.cluster_name, c.auto_termination_minutes, b.weekend_dbu
        FROM (
            SELECT cluster_id, SUM(usage_quantity) AS weekend_dbu
            FROM billing_usage_full
            WHERE (CAST(strftime('%w', usage_date) AS INTEGER) + 1) IN (1, 7)
              AND {f_usage_date()}
              AND cluster_id IS NOT NULL
            GROUP BY 1
        ) b
        JOIN compute_clusters_parsed c ON b.cluster_id = c.cluster_id
        ORDER BY b.weekend_dbu DESC LIMIT 15
    """)
    data_table(joined, title="Weekend cluster details", help=HELP["tbl_weekend_clusters"])


def render_wall_of_shame(run_query) -> None:
    page_header("Slow SQL", "Most expensive queries by duration")
    df, err = run_query(f"""
        SELECT executed_by, duration_ms, read_bytes, spilled_local_bytes,
               LEFT(COALESCE(statement_text, '(no text)'), 120) AS query_preview
        FROM query_history
        WHERE execution_status = 'FINISHED'
          AND {f_ts_date("start_time")}
        ORDER BY duration_ms DESC LIMIT 20
    """)
    if show_error(err):
        return
    data_table(df, height=500, title="Slowest queries", help=HELP["tbl_slow_sql"])


def render_spill_analysis(run_query) -> None:
    page_header("Spill", "Queries with high disk spill")
    df, err = run_query(f"""
        SELECT executed_by, spilled_local_bytes, read_bytes, total_duration_ms AS duration_ms,
               LEFT(COALESCE(statement_text, '(no text)'), 100) AS query_preview
        FROM query_history_full
        WHERE spilled_local_bytes > 1000000000
          AND {f_ts_date("start_time")}
        ORDER BY spilled_local_bytes DESC LIMIT 25
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        df = df.copy()
        df["spill_gb"] = df["spilled_local_bytes"] / 1e9
        df["query_label"] = df["query_preview"].astype(str).str.slice(0, 45)
        bar_chart(df.head(15), "query_label", "spill_gb", "Top spill (GB)", orientation="h", help=HELP["query_spill"])
    data_table(df, title="Spill query details", help=HELP["tbl_spill_queries"])


def render_autotermination(run_query) -> None:
    page_header("Auto-stop", "Clusters without auto-termination may waste money")
    df, err = run_query("""
        SELECT cluster_name, auto_termination_minutes, team, worker_count,
               driver_node_type, data_security_mode
        FROM compute_clusters_parsed
        ORDER BY auto_termination_minutes ASC, cluster_name
    """)
    if show_error(err):
        return
    if df is not None and not df.empty:
        at_risk = len(df[df["auto_termination_minutes"] == 0])
        metrics_row([
            ("No auto-stop", str(at_risk), None, HELP["kpi_autostop_none"]),
            ("Auto-stop ≤20 min", str(len(df[(df["auto_termination_minutes"] > 0) & (df["auto_termination_minutes"] <= 20)])), None, HELP["kpi_autostop_short"]),
        ])
    data_table(df, title="Auto-termination settings", help=HELP["tbl_autostop"])


def render_node_utilization(run_query) -> None:
    page_header("Node usage", "CPU and memory per cluster")
    df, err = run_query("""
        SELECT COALESCE(c.cluster_name,
               CONCAT('Cluster ', SUBSTRING(n.cluster_id, 1, 8))) AS cluster_name,
               ROUND(AVG(n.cpu_user_percent + n.cpu_system_percent), 1) AS avg_cpu,
               ROUND(AVG(n.mem_used_percent), 1) AS avg_mem,
               COUNT(*) AS samples
        FROM compute_node_timeline n
        LEFT JOIN compute_clusters_parsed c ON n.cluster_id = c.cluster_id
        GROUP BY 1 ORDER BY avg_mem DESC LIMIT 20
    """)
    if show_error(err):
        return
    c1, c2 = st.columns(2)
    with c1:
        bar_chart(df, "cluster_name", "avg_cpu", "Avg CPU (%)", orientation="h", help=HELP["avg_cpu"])
    with c2:
        bar_chart(df, "cluster_name", "avg_mem", "Avg memory (%)", COLORS["warning"], orientation="h", help=HELP["avg_memory"])


def render_job_failures(run_query) -> None:
    page_header("Failed jobs", "FAILED / TIMEDOUT / CANCELED runs")
    df, err = run_query(f"""
        SELECT job_name, result_state, COUNT(*) AS runs
        FROM job_run_timeline_parsed
        WHERE {f_ts_date("start_ts")}
        GROUP BY 1, 2 ORDER BY runs DESC
    """)
    if show_error(err):
        return
    failed, _ = run_query(f"""
        SELECT job_name, COUNT(*) AS failures
        FROM job_run_timeline_parsed
        WHERE result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED')
          AND {f_ts_date("start_ts")}
        GROUP BY 1 ORDER BY failures DESC LIMIT 15
    """)
    bar_chart(failed, "job_name", "failures", "Most failed jobs", COLORS["danger"], orientation="h", help=HELP["top_failed_jobs"])
    data_table(df, title="Job run results", help=HELP["tbl_job_failures"])


def render_warehouse_scaling(run_query) -> None:
    page_header("Warehouse scaling", "SQL warehouse scale up/down events")
    df, err = run_query(f"""
        SELECT event_type, COUNT(*) AS events
        FROM compute_warehouse_events
        WHERE {f_ts_date("event_time")}
        GROUP BY 1 ORDER BY events DESC
    """)
    if show_error(err):
        return
    bar_chart(df, "event_type", "events", "Warehouse event types", help=HELP["warehouse_event_types"])
    timeline, _ = run_query(f"""
        SELECT CAST(event_time AS DATE) AS day, event_type, COUNT(*) AS n
        FROM compute_warehouse_events
        WHERE {f_ts_date("event_time")}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if timeline is not None and not timeline.empty:
        data = _prepare_chart_df(timeline, "day", "n", color="event_type")
        fig = px.bar(
            data,
            x="day",
            y="n",
            color="event_type",
            labels=_chart_labels("day", "n", "event_type"),
            template="plotly_white",
        )
        fig.update_xaxes(type="category")
        plotly_figure(fig, title="Warehouse events over time", help=HELP["warehouse_event_timeline"])


def render_remediation(run_query) -> None:
    page_header("Action plan", "Priority fixes based on signals")
    actions = []

    ghosts, _ = run_query(f"""
        SELECT COUNT(DISTINCT cluster_id) AS n FROM billing_usage_full
        WHERE (CAST(strftime('%w', usage_date) AS INTEGER) + 1) IN (1, 7)
          AND cluster_id IS NOT NULL AND {f_usage_date()}
    """)
    if ghosts is not None and int(ghosts.iloc[0]["n"] or 0) > 0:
        actions.append(("Enable weekend auto-stop", "Compute waste", "Easy", f"{ghosts.iloc[0]['n']} weekend clusters"))

    spill, _ = run_query(f"""
        SELECT COUNT(*) AS n FROM query_history_full
        WHERE spilled_local_bytes > 5e9 AND {f_ts_date("start_time")}
    """)
    if spill is not None and int(spill.iloc[0]["n"] or 0) > 0:
        actions.append(("Fix queries with spill >5GB", "SQL performance", "Medium", f"{spill.iloc[0]['n']} queries"))

    fails, _ = run_query(f"""
        SELECT COUNT(*) AS n FROM job_run_timeline_parsed
        WHERE result_state = 'FAILED' AND {f_ts_date("start_ts")}
    """)
    if fails is not None and int(fails.iloc[0]["n"] or 0) > 0:
        actions.append(("Investigate failed jobs", "Reliability", "Medium", f"{fails.iloc[0]['n']} failures"))

    denied, _ = run_query(f"""
        SELECT COUNT(*) AS n FROM access_audit_parsed
        WHERE status_code = 403 AND {f_event_date()}
    """)
    if denied is not None and int(denied.iloc[0]["n"] or 0) > 0:
        actions.append(("Review UC permissions", "Governance", "Easy", f"{denied.iloc[0]['n']} denied access"))

    if not actions:
        st.success("No priority signals detected for the selected period. 🎉")
        return

    data_table(
        pd.DataFrame(actions, columns=["Action", "Area", "Effort", "Signal"]),
        title="Recommended actions",
        help=HELP["tbl_action_plan"],
    )
