"""Vue unique par catégorie — toutes les sections sur un seul écran."""

from __future__ import annotations

import streamlit as st

from dashboards import home, finops, optimization, security, compute, jobs, sql_analytics, platform
from dashboards.components import page_header, section_header
from dashboards.date_filter import period_label


def _run_sections(
    category: str,
    icon: str,
    description: str,
    sections: list[tuple[str, str, str, callable]],
    run_query,
) -> None:
    page_header(category, f"{description} — Période : {period_label()}.", category=category, icon=icon)
    st.session_state["_suppress_page_header"] = True
    try:
        for sec_icon, title, subtitle, render_fn in sections:
            st.divider()
            section_header(f"{sec_icon} {title}".strip(), subtitle)
            render_fn(run_query)
    finally:
        st.session_state["_suppress_page_header"] = False


def render_accueil(run_query) -> None:
    home.render_overview(run_query)


def render_finops(run_query) -> None:
    _run_sections(
        "FinOps",
        "💰",
        "Coûts, DBU, attribution — vue consolidée",
        [
            ("👔", "Executive Summary", "Synthèse exécutive mensuelle", finops.render_executive),
            ("🔥", "Top consommateurs", "Clusters, jobs, warehouses, users", finops.render_top_consumers),
            ("📉", "Tendances DBU", "Consommation par produit", finops.render_daily_trends),
            ("🧩", "Répartition SKU", "Mix SKUs Databricks", finops.render_sku_breakdown),
            ("👥", "Attribution équipes", "Coût par team & environnement", finops.render_team_attribution),
            ("📅", "Comparaison mensuelle", "Évolution mois par mois", finops.render_monthly_comparison),
            ("💵", "List Prices & coût", "Tarifs & estimation", finops.render_list_prices),
            ("🌐", "Storage & Networking", "Usage hors compute", finops.render_storage_network),
        ],
        run_query,
    )


def render_optimisation(run_query) -> None:
    _run_sections(
        "Optimisation",
        "⚡",
        "Waste, performance SQL, remédiation — vue consolidée",
        [
            ("✅", "Plan de remédiation", "Actions priorisées", optimization.render_remediation),
            ("👻", "Ghost Clusters", "Clusters actifs le week-end", optimization.render_ghost_clusters),
            ("🐢", "Wall of Shame SQL", "Requêtes les plus coûteuses", optimization.render_wall_of_shame),
            ("💾", "Spill & mémoire", "Requêtes avec spill disque élevé", optimization.render_spill_analysis),
            ("🛑", "Échecs jobs & SLA", "Runs en échec", optimization.render_job_failures),
            ("⏱️", "Autotermination", "Politiques auto-stop des clusters", optimization.render_autotermination),
            ("📊", "Utilisation nodes", "CPU / RAM par instance", optimization.render_node_utilization),
            ("📐", "Scaling warehouses", "Événements scale up/down", optimization.render_warehouse_scaling),
        ],
        run_query,
    )


def render_securite(run_query) -> None:
    _run_sections(
        "Sécurité & Gouvernance",
        "🔒",
        "Audit, Unity Catalog, accès — vue consolidée",
        [
            ("📋", "Audit Overview", "Volume et répartition des événements", security.render_audit_overview),
            ("🚫", "Accès refusés", "Événements 403", security.render_permission_denied),
            ("🏛️", "Unity Catalog", "Actions UC", security.render_unity_catalog),
            ("🎭", "Top acteurs", "Utilisateurs les plus actifs", security.render_top_actors),
            ("🗓️", "Heatmap activité", "Intensité audit par service × date", security.render_activity_heatmap),
            ("🔑", "Secrets & tokens", "Secrets, PAT, IAM", security.render_secrets_tokens),
            ("🪪", "Authentification", "Logins & origine IP", security.render_authentication),
        ],
        run_query,
    )


def render_compute(run_query) -> None:
    _run_sections(
        "Compute",
        "🖥️",
        "Clusters, runtime, événements — vue consolidée",
        [
            ("📦", "Inventaire clusters", "Parc clusters", compute.render_cluster_inventory),
            ("🏷️", "Politiques & tags", "Tags & data security mode", compute.render_cluster_policies),
            ("⚙️", "Runtime & versions", "DBR & node types", compute.render_runtime_versions),
            ("⏳", "Timeline événements", "Logs cluster events", compute.render_cluster_events),
        ],
        run_query,
    )


def render_jobs(run_query) -> None:
    _run_sections(
        "Jobs & Workflows",
        "🔄",
        "Lakeflow, runs, tasks — vue consolidée",
        [
            ("📈", "Overview runs", "Volume & statuts", jobs.render_runs_overview),
            ("✔️", "Taux de succès", "Fiabilité par job", jobs.render_success_rates),
            ("🛑", "Durées & queues", "Run time vs queue time", jobs.render_durations_queues),
            ("👥", "Runs par équipe", "Attribution par team", jobs.render_runs_by_team),
            ("🧱", "Breakdown tasks", "Tasks par type", jobs.render_task_breakdown),
        ],
        run_query,
    )


def render_sql(run_query) -> None:
    _run_sections(
        "SQL & Warehouses",
        "📊",
        "Query history, warehouses — vue consolidée",
        [
            ("🚀", "Performance globale", "Latences & P95", sql_analytics.render_query_performance),
            ("🚦", "Queues & capacity", "Temps d'attente warehouse", sql_analytics.render_queue_analysis),
            ("💨", "Cache & spill", "Result cache & spill", sql_analytics.render_cache_spill),
            ("👤", "Par utilisateur", "Charge SQL par user", sql_analytics.render_by_user),
            ("🏭", "Activité warehouses", "Requêtes & config WH", sql_analytics.render_warehouse_activity),
            ("📝", "Types de statements", "SELECT, INSERT, OPTIMIZE…", sql_analytics.render_statement_types),
        ],
        run_query,
    )


def render_plateforme(run_query) -> None:
    _run_sections(
        "Plateforme",
        "🛠️",
        "API, ingestion, logs — vue consolidée",
        [
            ("📥", "Pipeline ingestion", "Mirror finops", platform.render_ingestion_health),
            ("🔌", "Inventaire API", "Clusters, warehouses, jobs", platform.render_api_inventory),
            ("📜", "Logs driver", "Échantillon logs driver", platform.render_driver_logs),
        ],
        run_query,
    )
