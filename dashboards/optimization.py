"""Dashboards optimisation."""

import streamlit as st
import pandas as pd

from dashboards.components import (
    bar_chart,
    data_table,
    line_chart,
    metrics_row,
    page_header,
    plotly_figure,
    show_empty,
    show_error,
    COLORS,
    _drop_blank_categories,
    _sanitize_chart_df,
)
from dashboards.date_filter import f_event_date, f_ts_date, f_usage_date, f_workspace, period_label


def render_ghost_clusters(run_query) -> None:
    page_header("Ghost Clusters", "Clusters actifs le week-end — gaspillage probable")
    df, err = run_query(f"""
        SELECT cluster_id, SUM(usage_quantity) AS weekend_dbu
        FROM billing_usage_full
        WHERE (CAST(strftime('%w', usage_date) AS INTEGER) + 1) IN (1, 7)
          AND {f_usage_date()}
          AND cluster_id IS NOT NULL
        GROUP BY 1 ORDER BY weekend_dbu DESC LIMIT 15
    """)
    if show_error(err):
        return
    bar_chart(df, "cluster_id", "weekend_dbu", "DBU week-end par cluster", COLORS["danger"])
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
    data_table(joined)


def render_wall_of_shame(run_query) -> None:
    page_header("Wall of Shame SQL", "Requêtes les plus coûteuses")
    df, err = run_query(f"""
        SELECT executed_by, duration_ms, read_bytes, spilled_local_bytes,
               LEFT(COALESCE(statement_text, '(sans texte)'), 120) AS query_preview
        FROM query_history
        WHERE execution_status = 'FINISHED'
          AND {f_ts_date("start_time")}
        ORDER BY duration_ms DESC LIMIT 20
    """)
    if show_error(err):
        return
    data_table(df, height=500)


def render_spill_analysis(run_query) -> None:
    page_header("Spill & mémoire", "Requêtes avec spill disque élevé")
    df, err = run_query(f"""
        SELECT executed_by, spilled_local_bytes, read_bytes, total_duration_ms AS duration_ms,
               LEFT(COALESCE(statement_text, '(sans texte)'), 100) AS query_preview
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
        bar_chart(df.head(15), "query_label", "spill_gb", "Spill (GB) — top requêtes", orientation="h")
    data_table(df)


def render_autotermination(run_query) -> None:
    page_header("Autotermination", "Clusters sans auto-termination = risque de waste")
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
            ("Clusters total", str(len(df)), None),
            ("Sans auto-termination", str(at_risk), None),
            ("Avec auto-term ≤20min", str(len(df[(df["auto_termination_minutes"] > 0) & (df["auto_termination_minutes"] <= 20)])), None),
        ])
    data_table(df)


def render_node_utilization(run_query) -> None:
    page_header("Utilisation nodes", "CPU / mémoire par instance (node_timeline)")
    df, err = run_query("""
        SELECT cluster_id,
               ROUND(AVG(cpu_user_percent + cpu_system_percent), 1) AS avg_cpu,
               ROUND(AVG(mem_used_percent), 1) AS avg_mem,
               COUNT(*) AS samples
        FROM compute_node_timeline
        GROUP BY 1 ORDER BY avg_mem DESC LIMIT 20
    """)
    if show_error(err):
        return
    c1, c2 = st.columns(2)
    with c1:
        bar_chart(df, "cluster_id", "avg_cpu", "CPU moyen (%)", orientation="h")
    with c2:
        bar_chart(df, "cluster_id", "avg_mem", "Mémoire moyenne (%)", COLORS["warning"], orientation="h")


def render_job_failures(run_query) -> None:
    page_header("Échecs jobs & SLA", "Runs FAILED / TIMEDOUT — impact fiabilité")
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
    bar_chart(failed, "job_name", "failures", "Jobs les plus en échec", COLORS["danger"], orientation="h")
    data_table(df)


def render_warehouse_scaling(run_query) -> None:
    page_header("Scaling warehouses", "Événements scale up/down SQL warehouses")
    df, err = run_query(f"""
        SELECT event_type, COUNT(*) AS events
        FROM compute_warehouse_events
        WHERE {f_ts_date("event_time")}
        GROUP BY 1 ORDER BY events DESC
    """)
    if show_error(err):
        return
    bar_chart(df, "event_type", "events", "Types d'événements warehouse")
    timeline, _ = run_query(f"""
        SELECT CAST(event_time AS DATE) AS day, event_type, COUNT(*) AS n
        FROM compute_warehouse_events
        WHERE {f_ts_date("event_time")}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if timeline is not None and not timeline.empty:
        import plotly.express as px
        data = _drop_blank_categories(_sanitize_chart_df(timeline, "event_type", "day"), "event_type")
        fig = px.bar(data, x="day", y="n", color="event_type", template="plotly_white")
        fig.update_xaxes(type="category")
        plotly_figure(fig, title=f"Timeline événements ({period_label()})")


def render_remediation(run_query) -> None:
    page_header("Plan de remédiation", "Actions priorisées basées sur les signaux")
    actions = []

    ghosts, _ = run_query(f"""
        SELECT COUNT(DISTINCT cluster_id) AS n FROM billing_usage_full
        WHERE (CAST(strftime('%w', usage_date) AS INTEGER) + 1) IN (1, 7)
          AND cluster_id IS NOT NULL AND {f_usage_date()}
    """)
    if ghosts is not None and int(ghosts.iloc[0]["n"] or 0) > 0:
        actions.append(("Enforcer auto-termination week-end", "Compute Waste", "Facile", f"{ghosts.iloc[0]['n']} clusters actifs WE"))

    spill, _ = run_query(f"""
        SELECT COUNT(*) AS n FROM query_history_full
        WHERE spilled_local_bytes > 5e9 AND {f_ts_date("start_time")}
    """)
    if spill is not None and int(spill.iloc[0]["n"] or 0) > 0:
        actions.append(("Optimiser requêtes avec spill >5GB", "SQL Performance", "Moyen", f"{spill.iloc[0]['n']} requêtes"))

    fails, _ = run_query(f"""
        SELECT COUNT(*) AS n FROM job_run_timeline_parsed
        WHERE result_state = 'FAILED' AND {f_ts_date("start_ts")}
    """)
    if fails is not None and int(fails.iloc[0]["n"] or 0) > 0:
        actions.append(("Investiguer jobs FAILED récurrents", "Reliability", "Moyen", f"{fails.iloc[0]['n']} échecs"))

    denied, _ = run_query(f"""
        SELECT COUNT(*) AS n FROM access_audit_parsed
        WHERE status_code = 403 AND {f_event_date()}
    """)
    if denied is not None and int(denied.iloc[0]["n"] or 0) > 0:
        actions.append(("Revoir permissions UC", "Gouvernance", "Facile", f"{denied.iloc[0]['n']} accès refusés"))

    actions.extend([
        ("Migrer AP dev vers serverless SQL", "Idle Compute", "Moyen", "Estimation -20% DBU AP"),
        ("VACUUM tables bronze/silver", "Storage", "Facile", "Rétention 7j recommandée"),
        ("Activer policies serverless", "Cost Control", "Facile", "Tags CostCenter obligatoires"),
    ])

    st.dataframe(pd.DataFrame(actions, columns=["Action", "Domaine", "Effort", "Signal"]), use_container_width=True)
