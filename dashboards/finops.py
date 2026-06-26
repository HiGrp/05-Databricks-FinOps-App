"""Dashboards FinOps."""

import streamlit as st

from dashboards.components import (
    area_chart,
    bar_chart,
    data_table,
    kpi_cards,
    line_chart,
    metrics_row,
    page_header,
    pie_chart,
    show_error,
)
from dashboards.date_filter import f_usage_date, f_workspace, period_label


def render_executive(run_query) -> None:
    page_header("Executive Summary", "Synthèse exécutive DBU — mois en cours vs précédent")
    sql = """
        SELECT
            SUM(CASE WHEN usage_date >= date_trunc('month', current_date) THEN usage_quantity ELSE 0 END) AS current_month,
            SUM(CASE WHEN usage_date >= date_trunc('month', current_date - INTERVAL 1 MONTH)
                      AND usage_date < date_trunc('month', current_date) THEN usage_quantity ELSE 0 END) AS last_month,
            SUM(CASE WHEN usage_date >= date_trunc('month', current_date) THEN usage_quantity ELSE 0 END) * 0.2 AS savings_20pct
        FROM billing_usage_full
        WHERE sku_name LIKE '%ALL_PURPOSE%' OR sku_name LIKE '%JOBS%' OR sku_name LIKE '%SQL%'
    """
    df, err = run_query(sql)
    if show_error(err) or df is None or df.empty:
        return
    cur, prev = float(df.iloc[0]["current_month"] or 0), float(df.iloc[0]["last_month"] or 0)
    pct = ((cur - prev) / prev * 100) if prev else 0
    tone = "up" if pct > 0 else "down" if pct < 0 else "neutral"
    kpi_cards([
        {"label": "DBU mois en cours", "value": f"{cur:,.1f}", "icon": "📅"},
        {"label": "DBU mois précédent", "value": f"{prev:,.1f}", "icon": "📆",
         "delta": f"{pct:+.1f}% vs M-1", "delta_tone": tone},
        {"label": "Économies potentielles", "value": f"{float(df.iloc[0]['savings_20pct'] or 0):,.1f} DBU",
         "icon": "💡", "delta": "Estimation −20%", "delta_tone": "neutral"},
    ])
    trend, _ = run_query(f"""
        SELECT usage_date, SUM(usage_quantity) AS daily_dbu
        FROM billing_usage_full WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(trend, "usage_date", "daily_dbu", f"Tendance journalière ({period_label()})")


def render_daily_trends(run_query) -> None:
    page_header("Tendances DBU", "Consommation quotidienne par produit")
    df, err = run_query(f"""
        SELECT usage_date, billing_origin_product, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE {f_usage_date()}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if show_error(err):
        return
    area_chart(df, "usage_date", "dbu", "billing_origin_product", f"DBU par produit ({period_label()})")


def render_sku_breakdown(run_query) -> None:
    page_header("Répartition SKU", "Analyse fine par SKU Databricks")
    c1, c2 = st.columns(2)
    with c1:
        df, err = run_query(f"""
            SELECT sku_name, SUM(usage_quantity) AS dbu
            FROM billing_usage_full WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        if not show_error(err):
            bar_chart(df, "sku_name", "dbu", f"Top 15 SKUs ({period_label()})", orientation="h")
    with c2:
        df2, _ = run_query(f"""
            SELECT usage_type, SUM(usage_quantity) AS dbu
            FROM billing_usage_full WHERE {f_usage_date()}
            GROUP BY 1
        """)
        pie_chart(df2, "usage_type", "dbu", "Par type d'usage")


def render_team_attribution(run_query) -> None:
    page_header("Attribution équipes", "DBU par Team / Cost Center / Environment")
    df, err = run_query(f"""
        SELECT team, cost_center, environment, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE {f_usage_date()} AND team IS NOT NULL
        GROUP BY 1, 2, 3 ORDER BY dbu DESC
    """)
    if show_error(err):
        return
    c1, c2 = st.columns(2)
    with c1:
        by_team, _ = run_query(f"""
            SELECT team, SUM(usage_quantity) AS dbu FROM billing_usage_full
            WHERE {f_usage_date()} AND team IS NOT NULL
            GROUP BY 1 ORDER BY dbu DESC
        """)
        bar_chart(by_team, "team", "dbu", "DBU par équipe")
    with c2:
        env_df = df.groupby("environment", as_index=False)["dbu"].sum() if df is not None and not df.empty else None
        pie_chart(env_df, "environment", "dbu", "Par environnement")
    data_table(df)


def render_monthly_comparison(run_query) -> None:
    page_header("Comparaison mensuelle", "Évolution DBU mois par mois")
    df, err = run_query(f"""
        SELECT date_trunc('month', usage_date) AS month, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY 1
    """)
    if show_error(err):
        return
    bar_chart(df, "month", "dbu", "DBU mensuel total")
    data_table(df)


def render_list_prices(run_query) -> None:
    page_header("List Prices & coût estimé", "Jointure usage × list_prices")
    df, err = run_query(f"""
        SELECT sku_name,
               SUM(usage_quantity) AS total_dbu,
               COUNT(*) AS records
        FROM billing_usage_full
        WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY total_dbu DESC LIMIT 20
    """)
    if show_error(err):
        return
    prices, _ = run_query("SELECT sku_name, pricing, currency_code FROM billing_list_prices LIMIT 20")
    c1, c2 = st.columns(2)
    with c1:
        bar_chart(df, "sku_name", "total_dbu", f"DBU par SKU ({period_label()})", orientation="h")
    with c2:
        data_table(prices)


def render_storage_network(run_query) -> None:
    page_header("Storage & Networking", "Usage non-compute")
    df, err = run_query(f"""
        SELECT usage_date, billing_origin_product, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE billing_origin_product IN ('STORAGE', 'NETWORKING')
          AND {f_usage_date()}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if show_error(err):
        return
    area_chart(df, "usage_date", "dbu", "billing_origin_product", f"Storage & Networking ({period_label()})")


def render_top_consumers(run_query) -> None:
    page_header("Top consommateurs", "Clusters, jobs, warehouses les plus coûteux")
    tabs = st.tabs(["Clusters", "Jobs", "Warehouses", "Utilisateurs"])
    with tabs[0]:
        df, err = run_query(f"""
            SELECT COALESCE(c.cluster_name, b.cluster_id) AS cluster_name,
                   SUM(b.usage_quantity) AS dbu
            FROM billing_usage_full b
            LEFT JOIN compute_clusters_parsed c ON b.cluster_id = c.cluster_id
            WHERE b.cluster_id IS NOT NULL AND {f_usage_date('b.usage_date')}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        if not show_error(err):
            bar_chart(df, "cluster_name", "dbu", "Top clusters", orientation="h")
    with tabs[1]:
        df, _ = run_query(f"""
            SELECT job_name, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE job_name IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        bar_chart(df, "job_name", "dbu", "Top jobs", orientation="h")
    with tabs[2]:
        df, _ = run_query(f"""
            SELECT warehouse_id, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE warehouse_id IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        bar_chart(df, "warehouse_id", "dbu", "Top warehouses", orientation="h")
    with tabs[3]:
        df, _ = run_query(f"""
            SELECT run_as, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE run_as IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        bar_chart(df, "run_as", "dbu", "Top utilisateurs (run_as)", orientation="h")
