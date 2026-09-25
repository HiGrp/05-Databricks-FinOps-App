"""Navigation - sidebar pages, in display order, grouped."""

from __future__ import annotations

from dashboards import category_views, executive, setup

CATEGORIES: dict[str, dict] = {
    "Home": {"icon": "🏠", "description": "Spend, savings and risks at a glance", "render": executive.render_home},
    "Action plan": {"icon": "✅", "description": "What to fix, who, and how much it saves", "render": category_views.render_action_plan},
    "FinOps": {"icon": "💰", "description": "Cost, trends, chargeback", "render": category_views.render_finops, "group": "Technical details"},
    "Optimization": {"icon": "⚡", "description": "Waste, SQL perf, fixes", "render": category_views.render_optimisation, "group": "Technical details"},
    "Security": {"icon": "🛡️", "description": "Audit, Unity Catalog, access", "render": category_views.render_securite, "group": "Technical details"},
    "Compute": {"icon": "🖥️", "description": "Clusters and runtime", "render": category_views.render_compute, "group": "Technical details"},
    "Jobs": {"icon": "🔄", "description": "Runs, tasks, reliability", "render": category_views.render_jobs, "group": "Technical details"},
    "SQL": {"icon": "📊", "description": "Queries and warehouses", "render": category_views.render_sql, "group": "Technical details"},
    "Platform": {"icon": "🛠️", "description": "API, ingestion, logs", "render": category_views.render_plateforme, "group": "Technical details"},
    "Setup": {"icon": "🚀", "description": "Connect your Databricks", "render": setup.render_setup},
}


def get_category_render_fn(category: str):
    cat = CATEGORIES.get(category)
    return cat["render"] if cat else None


def get_category_meta(category: str) -> dict:
    cat = CATEGORIES.get(category, {})
    return {"category": category, "icon": cat.get("icon", ""), "desc": cat.get("description", "")}
