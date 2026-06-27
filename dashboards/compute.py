"""Compute dashboards."""

import plotly.express as px
import pandas as pd
import streamlit as st

from dashboards.chart_help import HELP
from dashboards.components import (
    bar_chart,
    data_table,
    metrics_row,
    page_header,
    pie_chart,
    plotly_figure,
    show_empty,
    show_error,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_workspace


def render_cluster_inventory(run_query) -> None:
    page_header("Cluster list", f"{fq('compute.clusters')} — current fleet")
    df, err = run_query(f"""
        SELECT cluster_name, cluster_id, owned_by, worker_count,
               driver_node_type, auto_termination_minutes, data_security_mode
        FROM compute_clusters_parsed
        WHERE {f_workspace('workspace_id')}
        ORDER BY cluster_name
    """)
    if show_error(err):
        return
    metrics_row([
        ("Clusters", str(len(df) if df is not None else 0), None),
        ("Photon", str(len(df[df["runtime_engine"] == "PHOTON"]) if df is not None and "runtime_engine" in df.columns else 0), None),
        ("Single-node", str(len(df[df["worker_count"] == 0]) if df is not None else 0), None),
    ])
    data_table(df)


def render_cluster_policies(run_query) -> None:
    page_header("Tags & policies", "Teams, tags, and security mode")
    c1, c2 = st.columns(2)
    with c1:
        tags, err = run_query("""
            SELECT team, COUNT(*) AS clusters
            FROM compute_clusters_parsed WHERE team IS NOT NULL
            GROUP BY 1
        """)
        if not show_error(err):
            pie_chart(tags, "team", "clusters", "Clusters by team", help=HELP["clusters_by_team"])
    with c2:
        dsm, _ = run_query("""
            SELECT data_security_mode, COUNT(*) AS n
            FROM compute_clusters_parsed GROUP BY 1
        """)
        pie_chart(dsm, "data_security_mode", "n", "Data security mode", help=HELP["data_security_mode"])
    src, _ = run_query("""
        SELECT cluster_source, COUNT(*) AS n FROM compute_clusters_parsed GROUP BY 1
    """)
    bar_chart(src, "cluster_source", "n", "Cluster source", help=HELP["cluster_source"])


def render_cluster_events(run_query) -> None:
    page_header("Cluster events", "Cluster event timeline")
    from dashboards.query_cache import get_cache_key
    from prod_data import CLUSTER_EVENTS_TABLE, fetch_cluster_events_cached

    key = get_cache_key()
    with st.spinner("Loading cluster events..."):
        df = fetch_cluster_events_cached(key)

    if df is None or df.empty:
        if CLUSTER_EVENTS_TABLE:
            show_empty("No cluster events in the configured table.")
        else:
            st.info(
                "Events from clusters/events API (sample), or set "
                "`FINOPS_CLUSTER_EVENTS_TABLE` for full Delta history."
            )
        return

    from dashboards.components import line_chart

    if "timestamp" in df.columns:
        daily = df.copy()
        daily["day"] = pd.to_datetime(daily["timestamp"], errors="coerce").dt.date
        counts = daily.groupby("day", as_index=False).size().rename(columns={"size": "events"})
        line_chart(counts, "day", "events", "Events per day", help="Daily cluster event count.")
    data_table(df.head(200))


def render_runtime_versions(run_query) -> None:
    page_header("Runtime", "DBR versions and node types")

    df_rt, err = run_query("""
        SELECT
            cp.dbr_version,
            COALESCE(
                NULLIF(
                    UPPER(CONCAT(
                        COALESCE(get(split(ws.workspace_name, '-'), 5), ''),
                        '-',
                        COALESCE(get(split(ws.workspace_name, '-'), 6), '')
                    )),
                    '-'
                ),
                UPPER(ws.workspace_name),
                'Other'
            ) AS workspace_short,
            COUNT(*) AS nombre
        FROM (
            SELECT cluster_id, dbr_version, workspace_id
            FROM (
                SELECT cluster_id, dbr_version, workspace_id,
                       ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS _rn
                FROM compute_clusters
                WHERE cluster_source != 'JOB'
            ) WHERE _rn = 1
        ) cp
        LEFT JOIN workspaces_latest ws
            ON CAST(cp.workspace_id AS STRING) = CAST(ws.workspace_id AS STRING)
        WHERE cp.dbr_version IS NOT NULL
        GROUP BY 1, 2
        ORDER BY nombre DESC
    """)
    if not show_error(err) and df_rt is not None and not df_rt.empty:
        df_rt["workspace_short"] = df_rt["workspace_short"].fillna("Other")
        df_rt["workspace_short"] = df_rt["workspace_short"].replace({"-": "Other", "": "Other"})

        runtime_order = (
            df_rt.groupby("dbr_version")["nombre"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )

        fig = px.bar(
            df_rt,
            x="dbr_version",
            y="nombre",
            color="workspace_short",
            template="plotly_white",
            category_orders={"dbr_version": runtime_order},
            labels={"dbr_version": "", "nombre": "Count", "workspace_short": ""},
        )
        fig.update_layout(
            barmode="stack",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
            height=520,
            margin=dict(b=120, r=160),
        )
        fig.update_xaxes(tickangle=-45, type="category")
        plotly_figure(fig, title="DBR version by workspace", help=HELP["dbr_by_workspace"])

    st.markdown("---")
    nodes, _ = run_query("""
        SELECT driver_node_type, COUNT(*) AS n FROM compute_clusters_parsed GROUP BY 1
    """)
    bar_chart(nodes, "driver_node_type", "n", "Node types", orientation="h", help=HELP["node_types"])
