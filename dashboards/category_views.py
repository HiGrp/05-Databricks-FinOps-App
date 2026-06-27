"""Single-page category orchestrator — all sections, most relevant first."""

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
from dashboards.chart_help import CAT_HELP, HELP
from dashboards.components import page_header, section_header

_LOADING_HTML = '<p class="section-loading-hint">Loading…</p>'


def _section_shell(title: str, subtitle: str, *, help: str | None = None) -> st.empty:
    """Section title + flat loading line (no fold/unfold)."""
    section_header(title, subtitle, help=help)
    slot = st.empty()
    slot.markdown(_LOADING_HTML, unsafe_allow_html=True)
    return slot


def _run_sections(
    category: str,
    icon: str,
    description: str,
    sections: list[tuple],
    run_query,
    *,
    summary_fn=None,
) -> None:
    page_header(
        category,
        description,
        category=category,
        icon=icon,
        help=CAT_HELP.get(category),
    )

    summary_slot = None
    if summary_fn is not None:
        st.divider()
        summary_slot = _section_shell("Summary", "Key metrics at a glance", help=HELP["sec_summary"])

    # Phase 1 — all section titles + loading hints visible at once
    pending: list[tuple] = []
    for entry in sections:
        sec_icon, title, subtitle, render_fn = entry[:4]
        sec_help = entry[4] if len(entry) > 4 else None
        full_title = f"{sec_icon} {title}".strip()
        st.divider()
        pending.append((_section_shell(full_title, subtitle, help=sec_help), render_fn))

    # Phase 2 — fill each slot (SQL runs sequentially; cache helps on refresh)
    st.session_state["_suppress_page_header"] = True
    try:
        if summary_slot is not None:
            with summary_slot.container():
                summary_fn(run_query)

        for slot, render_fn in pending:
            with slot.container():
                render_fn(run_query)
    finally:
        st.session_state["_suppress_page_header"] = False


def render_accueil(run_query) -> None:
    _run_sections(
        "Overview",
        "📈",
        "FinOps, optimization, security, compute, jobs, and SQL in one place.",
        [
            ("📊", "Key metrics", "DBU, queries, audit, jobs, compute", home.render_overview_kpis, HELP["sec_home_kpis"]),
            ("💰", "Cost & products", "DBU trend and product mix", home.render_overview_cost, HELP["sec_home_cost"]),
            ("🔒", "Audit & jobs", "Top services and run status", home.render_overview_activity, HELP["sec_home_activity"]),
        ],
        run_query,
    )


def render_finops(run_query) -> None:
    _run_sections(
        "FinOps", "💰", "Cost, DBU, and chargeback",
        [
            ("👔", "Summary", "Monthly DBU vs last month", finops.render_executive, HELP["sec_finops_summary"]),
            ("🔥", "Top spenders", "Clusters, jobs, warehouses, users", finops.render_top_consumers, HELP["sec_finops_top_spenders"]),
            ("📉", "DBU trends", "Daily use by product", finops.render_daily_trends, HELP["sec_finops_trends"]),
            ("👥", "By team", "Cost by team and environment", finops.render_team_attribution, HELP["sec_finops_team"]),
            ("📅", "Monthly view", "Month-over-month DBU", finops.render_monthly_comparison, HELP["sec_finops_monthly"]),
            ("🧩", "SKU mix", "Top billing SKUs", finops.render_sku_breakdown, HELP["sec_finops_sku"]),
            ("🌐", "Storage & network", "Non-compute usage", finops.render_storage_network, HELP["sec_finops_storage"]),
            ("💵", "List prices", "Usage vs list prices", finops.render_list_prices, HELP["sec_finops_prices"]),
        ],
        run_query,
        summary_fn=category_summaries.render_finops_summary,
    )


def render_optimisation(run_query) -> None:
    _run_sections(
        "Optimization", "⚡", "Waste, SQL performance, and fixes",
        [
            ("✅", "Action plan", "Priority fixes from signals", optimization.render_remediation, HELP["sec_opt_action"]),
            ("👻", "Weekend clusters", "Clusters active on weekends", optimization.render_ghost_clusters, HELP["sec_opt_weekend"]),
            ("🛑", "Failed jobs", "Failed or timed-out runs", optimization.render_job_failures, HELP["sec_opt_failed_jobs"]),
            ("🐢", "Slow SQL", "Most expensive queries", optimization.render_wall_of_shame, HELP["sec_opt_slow_sql"]),
            ("💾", "Spill", "Queries with high disk spill", optimization.render_spill_analysis, HELP["sec_opt_spill"]),
            ("⏱️", "Auto-stop", "Cluster auto-termination settings", optimization.render_autotermination, HELP["sec_opt_autostop"]),
            ("📊", "Node usage", "CPU and memory per cluster", optimization.render_node_utilization, HELP["sec_opt_node_usage"]),
            ("📐", "Warehouse scaling", "Scale up/down events", optimization.render_warehouse_scaling, HELP["sec_opt_warehouse"]),
        ],
        run_query,
        summary_fn=category_summaries.render_optimization_summary,
    )


def render_securite(run_query) -> None:
    _run_sections(
        "Security", "🔒", "Audit, Unity Catalog, and access",
        [
            ("📋", "Audit summary", "Event volume and trends", security.render_audit_overview, HELP["sec_sec_audit"]),
            ("🚫", "Access denied", "403 events", security.render_permission_denied, HELP["sec_sec_denied"]),
            ("🎭", "Top users", "Most active users", security.render_top_actors, HELP["sec_sec_top_users"]),
            ("🗓️", "Activity heatmap", "Audit by service and date", security.render_activity_heatmap, HELP["sec_sec_heatmap"]),
            ("🏛️", "Unity Catalog", "UC actions", security.render_unity_catalog, HELP["sec_sec_uc"]),
            ("🔑", "Secrets & tokens", "Secrets, PAT, IAM events", security.render_secrets_tokens, HELP["sec_sec_secrets"]),
            ("🪪", "Sign-in", "Logins and source IP", security.render_authentication, HELP["sec_sec_signin"]),
        ],
        run_query,
        summary_fn=category_summaries.render_security_summary,
    )


def render_compute(run_query) -> None:
    _run_sections(
        "Compute", "🖥️", "Clusters, runtime, and events",
        [
            ("📦", "Cluster list", "All clusters", compute.render_cluster_inventory, HELP["sec_compute_list"]),
            ("🏷️", "Tags & policies", "Teams, tags, security mode", compute.render_cluster_policies, HELP["sec_compute_tags"]),
            ("⚙️", "Runtime", "DBR versions and node types", compute.render_runtime_versions, HELP["sec_compute_runtime"]),
            ("⏳", "Cluster events", "Event timeline", compute.render_cluster_events, HELP["sec_compute_events"]),
        ],
        run_query,
        summary_fn=category_summaries.render_compute_summary,
    )


def render_jobs(run_query) -> None:
    _run_sections(
        "Jobs", "🔄", "Runs, tasks, and reliability",
        [
            ("📈", "Run overview", "Volume and status", jobs.render_runs_overview, HELP["sec_jobs_overview"]),
            ("✔️", "Success rate", "Reliability per job", jobs.render_success_rates, HELP["sec_jobs_success"]),
            ("🛑", "Duration & queue", "Run vs queue time", jobs.render_durations_queues, HELP["sec_jobs_duration"]),
            ("👥", "By team", "Runs by team tag", jobs.render_runs_by_team, HELP["sec_jobs_team"]),
            ("🧱", "Tasks", "Tasks by type and status", jobs.render_task_breakdown, HELP["sec_jobs_tasks"]),
        ],
        run_query,
        summary_fn=category_summaries.render_jobs_summary,
    )


def render_sql(run_query) -> None:
    _run_sections(
        "SQL", "📊", "Query history and warehouses",
        [
            ("🚀", "Query performance", "Latency and P95", sql_analytics.render_query_performance, HELP["sec_sql_perf"]),
            ("🚦", "Queues", "Warehouse wait time", sql_analytics.render_queue_analysis, HELP["sec_sql_queues"]),
            ("💨", "Cache & spill", "Result cache and spill", sql_analytics.render_cache_spill, HELP["sec_sql_cache"]),
            ("👤", "By user", "Load per user", sql_analytics.render_by_user, HELP["sec_sql_user"]),
            ("🏭", "Warehouses", "Query volume and config", sql_analytics.render_warehouse_activity, HELP["sec_sql_warehouses"]),
            ("📝", "Statement types", "SELECT, INSERT, etc.", sql_analytics.render_statement_types, HELP["sec_sql_statements"]),
        ],
        run_query,
        summary_fn=category_summaries.render_sql_summary,
    )


def render_plateforme(run_query) -> None:
    _run_sections(
        "Platform", "🛠️", "API, ingestion, and logs",
        [
            ("🔌", "API inventory", "Clusters, warehouses, jobs", platform.render_api_inventory, HELP["sec_platform_api"]),
            ("📥", "Ingestion", "Pipeline health", platform.render_ingestion_health, HELP["sec_platform_ingestion"]),
            ("📜", "Driver logs", "Sample driver logs", platform.render_driver_logs, HELP["sec_platform_logs"]),
        ],
        run_query,
        summary_fn=category_summaries.render_platform_summary,
    )
