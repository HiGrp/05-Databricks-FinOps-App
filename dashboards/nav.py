"""Navigation — une vue consolidée par catégorie."""

from __future__ import annotations

from dashboards import category_views

CATEGORIES: dict[str, dict] = {
    "Accueil": {
        "icon": "🏠",
        "description": "Vue globale du workspace",
        "render": category_views.render_accueil,
    },
    "FinOps": {
        "icon": "💰",
        "description": "Coûts, DBU, attribution",
        "render": category_views.render_finops,
    },
    "Optimisation": {
        "icon": "⚡",
        "description": "Waste, perf, remédiation",
        "render": category_views.render_optimisation,
    },
    "Sécurité & Gouvernance": {
        "icon": "🔒",
        "description": "Audit, UC, accès",
        "render": category_views.render_securite,
    },
    "Compute": {
        "icon": "🖥️",
        "description": "Clusters & runtime",
        "render": category_views.render_compute,
    },
    "Jobs & Workflows": {
        "icon": "🔄",
        "description": "Lakeflow, runs, tasks",
        "render": category_views.render_jobs,
    },
    "SQL & Warehouses": {
        "icon": "📊",
        "description": "Query history, warehouses",
        "render": category_views.render_sql,
    },
    "Plateforme": {
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
