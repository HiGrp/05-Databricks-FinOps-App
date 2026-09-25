"""Technical pages — sections with charts and to-do lists."""

from __future__ import annotations

from functools import partial

import streamlit as st

from dashboards import (
    compute,
    findings,
    finops,
    jobs,
    optimization,
    platform,
    security,
    sql_analytics,
)
from dashboards.components import page_header, section_header
from dashboards.guides import GUIDES

_LOADING = '<div class="section-loading-wrap"><div class="section-spinner"></div></div>'


def _section_shell(title: str, sec_key: str | None, subtitle: str | None, icon: str = "") -> st.empty:
    guide = GUIDES.get(sec_key or "")
    section_header(title, guide.what if guide else subtitle, icon=icon or None)
    slot = st.empty()
    slot.markdown(_LOADING, unsafe_allow_html=True)
    return slot


def _run_sections(category: str, _icon: str, _description: str, sections: list[tuple], run_query) -> None:
    page_header(category)
    pending: list[tuple] = []
    for icon, title, subtitle, render_fn, sec_key in sections:
        pending.append((_section_shell(title, sec_key, subtitle, icon), render_fn, sec_key))

    st.session_state["_suppress_page_header"] = True
    try:
        for slot, render_fn, sec_key in pending:
            with slot.container():
                with st.spinner(""):
                    render_fn(run_query)
                    findings.render_section_todo(sec_key, run_query)
    finally:
        st.session_state["_suppress_page_header"] = False


def render_action_plan(run_query) -> None:
    page_header("Action plan")
    findings.render_plan(run_query)


def render_finops(run_query) -> None:
    _run_sections(
        "FinOps", "💰", "",
        [
            ("📊", "Summary", None, finops.render_executive, "sec_finops_summary"),
            ("🔥", "Top spenders", None, finops.render_top_consumers, "sec_finops_top_spenders"),
            ("📉", "Cost trends", None, finops.render_daily_trends, "sec_finops_trends"),
            ("📅", "Monthly view", None, finops.render_monthly_comparison, "sec_finops_monthly"),
            ("🧩", "SKU mix", None, finops.render_sku_breakdown, "sec_finops_sku"),
            ("👥", "Chargeback", None, finops.render_team_attribution, "sec_finops_team"),
            ("🌐", "Storage & network", None, finops.render_storage_network, "sec_finops_storage"),
            ("💵", "Unit prices", None, finops.render_list_prices, "sec_finops_prices"),
        ],
        run_query,
    )


def render_optimisation(run_query) -> None:
    _run_sections(
        "Optimization", "⚡", "",
        [
            ("✅", "Priority fixes", None,
             partial(findings.render_top, n=5, key="opt", domains=("Cost", "Performance", "Reliability")),
             "sec_opt_action"),
            ("👻", "Weekend clusters", None, optimization.render_ghost_clusters, "sec_opt_weekend"),
            ("🛑", "Failed jobs", None, optimization.render_job_failures, "sec_opt_failed_jobs"),
            ("🐢", "Slow SQL", None, optimization.render_wall_of_shame, "sec_opt_slow_sql"),
            ("💾", "Spill", None, optimization.render_spill_analysis, "sec_opt_spill"),
            ("⏱️", "Auto-stop", None, optimization.render_autotermination, "sec_opt_autostop"),
            ("📊", "Node usage", None, optimization.render_node_utilization, "sec_opt_node_usage"),
            ("📐", "Warehouse scaling", None, optimization.render_warehouse_scaling, "sec_opt_warehouse"),
        ],
        run_query,
    )


def render_securite(run_query) -> None:
    _run_sections(
        "Security", "🔒", "",
        [
            ("📋", "Audit summary", None, security.render_audit_overview, "sec_sec_audit"),
            ("🚫", "Access denied", None, security.render_permission_denied, "sec_sec_denied"),
            ("🎭", "Top users", None, security.render_top_actors, "sec_sec_top_users"),
            ("🗓️", "Activity heatmap", None, security.render_activity_heatmap, "sec_sec_heatmap"),
            ("🏛️", "Unity Catalog", None, security.render_unity_catalog, "sec_sec_uc"),
            ("🔑", "Secrets & tokens", None, security.render_secrets_tokens, "sec_sec_secrets"),
            ("🪪", "Sign-in", None, security.render_authentication, "sec_sec_signin"),
        ],
        run_query,
    )


def render_compute(run_query) -> None:
    _run_sections(
        "Compute", "🖥️", "",
        [
            ("📦", "Cluster list", None, compute.render_cluster_inventory, "sec_compute_list"),
            ("🏷️", "Tags & policies", None, compute.render_cluster_policies, "sec_compute_tags"),
            ("⚙️", "Runtime", None, compute.render_runtime_versions, "sec_compute_runtime"),
            ("⏳", "Cluster events", None, compute.render_cluster_events, "sec_compute_events"),
        ],
        run_query,
    )


def render_jobs(run_query) -> None:
    _run_sections(
        "Jobs", "🔄", "",
        [
            ("📈", "Run overview", None, jobs.render_runs_overview, "sec_jobs_overview"),
            ("✔️", "Success rate", None, jobs.render_success_rates, "sec_jobs_success"),
            ("🛑", "Duration & queue", None, jobs.render_durations_queues, "sec_jobs_duration"),
            ("👥", "By team", None, jobs.render_runs_by_team, "sec_jobs_team"),
            ("🧱", "Tasks", None, jobs.render_task_breakdown, "sec_jobs_tasks"),
        ],
        run_query,
    )


def render_sql(run_query) -> None:
    _run_sections(
        "SQL", "📊", "",
        [
            ("🚀", "Query performance", None, sql_analytics.render_query_performance, "sec_sql_perf"),
            ("🚦", "Queues", None, sql_analytics.render_queue_analysis, "sec_sql_queues"),
            ("💨", "Cache & spill", None, sql_analytics.render_cache_spill, "sec_sql_cache"),
            ("👤", "By user", None, sql_analytics.render_by_user, "sec_sql_user"),
            ("🏭", "Warehouses", None, sql_analytics.render_warehouse_activity, "sec_sql_warehouses"),
            ("📝", "Statement types", None, sql_analytics.render_statement_types, "sec_sql_statements"),
        ],
        run_query,
    )


def render_plateforme(run_query) -> None:
    _run_sections(
        "Platform", "🛠️", "",
        [
            ("🔌", "API inventory", None, platform.render_api_inventory, "sec_platform_api"),
            ("📥", "Ingestion", None, platform.render_ingestion_health, "sec_platform_ingestion"),
            ("📜", "Driver logs", None, platform.render_driver_logs, "sec_platform_logs"),
        ],
        run_query,
    )
