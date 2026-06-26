"""Dashboards compute."""

import plotly.express as px
import streamlit as st

from dashboards.components import (
    bar_chart,
    data_table,
    metrics_row,
    page_header,
    pie_chart,
    plotly_figure,
    show_error,
    COLORS,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_workspace


def render_cluster_inventory(run_query) -> None:
    page_header("Inventaire clusters", f"{fq('compute.clusters')} — état du parc")
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
        ("Single-node (0 workers)", str(len(df[df["worker_count"] == 0]) if df is not None else 0), None),
    ])
    data_table(df)


def render_cluster_policies(run_query) -> None:
    page_header("Politiques & tags", "Tags, policies, data security mode")
    c1, c2 = st.columns(2)
    with c1:
        tags, err = run_query("""
            SELECT team, COUNT(*) AS clusters
            FROM compute_clusters_parsed WHERE team IS NOT NULL
            GROUP BY 1
        """)
        if not show_error(err):
            pie_chart(tags, "team", "clusters", "Clusters par Team")
    with c2:
        dsm, _ = run_query("""
            SELECT data_security_mode, COUNT(*) AS n
            FROM compute_clusters_parsed GROUP BY 1
        """)
        pie_chart(dsm, "data_security_mode", "n", "Data security mode")
    src, _ = run_query("""
        SELECT cluster_source, COUNT(*) AS n FROM compute_clusters_parsed GROUP BY 1
    """)
    bar_chart(src, "cluster_source", "n", "Source de création")


def render_cluster_events(run_query) -> None:
    page_header("Timeline événements", "Événements cluster (API ou logs)")
    st.info(
        "Événements via API clusters/events, ou configurez "
        "`FINOPS_CLUSTER_EVENTS_TABLE` pour un historique Delta."
    )


def render_runtime_versions(run_query) -> None:
    page_header("Runtime & versions", "DBR version, node types, engines")

    # --- Stacked bar chart : runtime par workspace (comme D_TGV_AUDIT) ---
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
                'Autre'
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
        df_rt["workspace_short"] = df_rt["workspace_short"].fillna("Autre")
        df_rt["workspace_short"] = df_rt["workspace_short"].replace({"-": "Autre", "": "Autre"})

        # Ordre des runtimes par total decroissant
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
            labels={"dbr_version": "", "nombre": "Nombre", "workspace_short": ""},
        )
        fig.update_layout(
            barmode="stack",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
            height=520,
            margin=dict(b=120, r=160),
        )
        fig.update_xaxes(tickangle=-45, type="category")
        plotly_figure(fig, title="Versions DBR par workspace")

    # --- Node types (conserve) ---
    st.markdown("---")
    nodes, _ = run_query("""
        SELECT driver_node_type, COUNT(*) AS n FROM compute_clusters_parsed GROUP BY 1
    """)
    bar_chart(nodes, "driver_node_type", "n", "Node types", orientation="h")
