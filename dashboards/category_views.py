"""Single-page category orchestrator — lazy sections + summary KPIs."""

from __future__ import annotations

import streamlit as st

from dashboards import (
    category_summaries,
    compute,
    finops,
    home,
    jobs,
    optimization,
    platform,
    security,
    sql_analytics,
)
from dashboards.components import page_header, section_header
from dashboards.date_filter import period_label


def _section_label(sec_icon: str, title: str) -> str:
    return f"{sec_icon} {title}".strip()


@st.fragment
def _render_section(title: str, subtitle: str, render_fn, run_query) -> None:
    section_header(title, subtitle)
    with st.spinner(f"Loading {title}..."):
        render_fn(run_query)


def _run_sections(
    category: str,
    icon: str,
    description: str,
    sections: list[tuple[str, str, str, callable]],
    run_query,
    *,
    summary_fn=None,
) -> None:
    page_header(category, f"{description} — Period: {period_label()}.", category=category, icon=icon)

    if summary_fn is not None:
        with st.spinner("Loading summary..."):
            summary_fn(run_query)
        st.divider()

    labels = {_section_label(ic, t): (ic, t, sub, fn) for ic, t, sub, fn in sections}
    options = list(labels.keys())

    nav_key = f"section_nav_{category}"
    if nav_key not in st.session_state:
        st.session_state[nav_key] = options[0]

    load_all = st.session_state.get("load_all_sections", False)

    col_sel, col_mode = st.columns([3, 1])
    with col_sel:
        if load_all:
            st.caption("All sections loaded — scroll down. Turn off **All sections** in the sidebar to load one at a time.")
        else:
            st.selectbox(
                "Section",
                options,
                key=nav_key,
                help="Only the selected section runs SQL queries.",
            )
    with col_mode:
        if st.session_state.get("data_cache_epoch", 0):
            st.caption(f"Cache refresh #{st.session_state.data_cache_epoch}")

    st.session_state["_suppress_page_header"] = True
    try:
        if load_all:
            for sec_icon, title, subtitle, render_fn in sections:
                st.divider()
                _render_section(f"{sec_icon} {title}".strip(), subtitle, render_fn, run_query)
        else:
            selected = st.session_state.get(nav_key, options[0])
            sec_icon, title, subtitle, render_fn = labels[selected]
            st.divider()
            _render_section(_section_label(sec_icon, title), subtitle, render_fn, run_query)
    finally:
        st.session_state["_suppress_page_header"] = False


def render_accueil(run_query) -> None:
    home.render_overview(run_query)


def render_finops(run_query) -> None:
    _run_sections(
        "FinOps", "💰", "Cost, DBU, and chargeback",
        [
            ("👔", "Summary", "Monthly DBU vs last month", finops.render_executive),
            ("🔥", "Top spenders", "Clusters, jobs, warehouses, users", finops.render_top_consumers),
            ("📉", "DBU trends", "Daily use by product", finops.render_daily_trends),
            ("🧩", "SKU mix", "Top billing SKUs", finops.render_sku_breakdown),
            ("👥", "By team", "Cost by team and environment", finops.render_team_attribution),
            ("📅", "Monthly view", "Month-over-month DBU", finops.render_monthly_comparison),
            ("💵", "List prices", "Usage vs list prices", finops.render_list_prices),
            ("🌐", "Storage & network", "Non-compute usage", finops.render_storage_network),
        ],
        run_query,
        summary_fn=category_summaries.render_finops_summary,
    )


def render_optimisation(run_query) -> None:
    _run_sections(
        "Optimization", "⚡", "Waste, SQL performance, and fixes",
        [
            ("✅", "Action plan", "Priority fixes from signals", optimization.render_remediation),
            ("👻", "Weekend clusters", "Clusters active on weekends", optimization.render_ghost_clusters),
            ("🐢", "Slow SQL", "Most expensive queries", optimization.render_wall_of_shame),
            ("💾", "Spill", "Queries with high disk spill", optimization.render_spill_analysis),
            ("🛑", "Failed jobs", "Failed or timed-out runs", optimization.render_job_failures),
            ("⏱️", "Auto-stop", "Cluster auto-termination settings", optimization.render_autotermination),
            ("📊", "Node usage", "CPU and memory per cluster", optimization.render_node_utilization),
            ("📐", "Warehouse scaling", "Scale up/down events", optimization.render_warehouse_scaling),
        ],
        run_query,
        summary_fn=category_summaries.render_optimization_summary,
    )


def render_securite(run_query) -> None:
    _run_sections(
        "Security", "🔒", "Audit, Unity Catalog, and access",
        [
            ("📋", "Audit summary", "Event volume and trends", security.render_audit_overview),
            ("🚫", "Access denied", "403 events", security.render_permission_denied),
            ("🏛️", "Unity Catalog", "UC actions", security.render_unity_catalog),
            ("🎭", "Top users", "Most active users", security.render_top_actors),
            ("🗓️", "Activity heatmap", "Audit by service and date", security.render_activity_heatmap),
            ("🔑", "Secrets & tokens", "Secrets, PAT, IAM events", security.render_secrets_tokens),
            ("🪪", "Sign-in", "Logins and source IP", security.render_authentication),
        ],
        run_query,
        summary_fn=category_summaries.render_security_summary,
    )


def render_compute(run_query) -> None:
    _run_sections(
        "Compute", "🖥️", "Clusters, runtime, and events",
        [
            ("📦", "Cluster list", "All clusters", compute.render_cluster_inventory),
            ("🏷️", "Tags & policies", "Teams, tags, security mode", compute.render_cluster_policies),
            ("⚙️", "Runtime", "DBR versions and node types", compute.render_runtime_versions),
            ("⏳", "Cluster events", "Event timeline", compute.render_cluster_events),
        ],
        run_query,
        summary_fn=category_summaries.render_compute_summary,
    )


def render_jobs(run_query) -> None:
    _run_sections(
        "Jobs", "🔄", "Runs, tasks, and reliability",
        [
            ("📈", "Run overview", "Volume and status", jobs.render_runs_overview),
            ("✔️", "Success rate", "Reliability per job", jobs.render_success_rates),
            ("🛑", "Duration & queue", "Run vs queue time", jobs.render_durations_queues),
            ("👥", "By team", "Runs by team tag", jobs.render_runs_by_team),
            ("🧱", "Tasks", "Tasks by type and status", jobs.render_task_breakdown),
        ],
        run_query,
        summary_fn=category_summaries.render_jobs_summary,
    )


def render_sql(run_query) -> None:
    _run_sections(
        "SQL", "📊", "Query history and warehouses",
        [
            ("🚀", "Query performance", "Latency and P95", sql_analytics.render_query_performance),
            ("🚦", "Queues", "Warehouse wait time", sql_analytics.render_queue_analysis),
            ("💨", "Cache & spill", "Result cache and spill", sql_analytics.render_cache_spill),
            ("👤", "By user", "Load per user", sql_analytics.render_by_user),
            ("🏭", "Warehouses", "Query volume and config", sql_analytics.render_warehouse_activity),
            ("📝", "Statement types", "SELECT, INSERT, etc.", sql_analytics.render_statement_types),
        ],
        run_query,
        summary_fn=category_summaries.render_sql_summary,
    )


def render_plateforme(run_query) -> None:
    _run_sections(
        "Platform", "🛠️", "API, ingestion, and logs",
        [
            ("📥", "Ingestion", "Pipeline health", platform.render_ingestion_health),
            ("🔌", "API inventory", "Clusters, warehouses, jobs", platform.render_api_inventory),
            ("📜", "Driver logs", "Sample driver logs", platform.render_driver_logs),
        ],
        run_query,
        summary_fn=category_summaries.render_platform_summary,
    )
