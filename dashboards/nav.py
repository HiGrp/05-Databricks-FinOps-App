"""Navigation — one consolidated view per category."""

from __future__ import annotations

from dashboards import category_views

CATEGORIES: dict[str, dict] = {
    "Home": {
        "icon": "🏠",
        "description": "Workspace overview",
        "render": category_views.render_accueil,
    },
    "FinOps": {
        "icon": "💰",
        "description": "Cost, DBU, chargeback",
        "render": category_views.render_finops,
    },
    "Optimization": {
        "icon": "⚡",
        "description": "Waste, SQL perf, fixes",
        "render": category_views.render_optimisation,
    },
    "Security": {
        "icon": "🔒",
        "description": "Audit, Unity Catalog, access",
        "render": category_views.render_securite,
    },
    "Compute": {
        "icon": "🖥️",
        "description": "Clusters and runtime",
        "render": category_views.render_compute,
    },
    "Jobs": {
        "icon": "🔄",
        "description": "Runs, tasks, reliability",
        "render": category_views.render_jobs,
    },
    "SQL": {
        "icon": "📊",
        "description": "Queries and warehouses",
        "render": category_views.render_sql,
    },
    "Platform": {
        "icon": "🛠️",
        "description": "API, ingestion, logs",
        "render": category_views.render_plateforme,
    },
}


def get_category_render_fn(category: str):
    cat = CATEGORIES.get(category)
    if not cat:
        return None
    fn = cat.get("render")
    return fn if callable(fn) else None


def get_category_meta(category: str) -> dict:
    cat = CATEGORIES.get(category, {})
    return {
        "category": category,
        "icon": cat.get("icon", ""),
        "desc": cat.get("description", ""),
    }
