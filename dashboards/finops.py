"""FinOps dashboards."""

import streamlit as st

from dashboards.chart_help import HELP
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
from dashboards.date_filter import f_usage_date, period_label


def render_executive(run_query) -> None:
    page_header("Summary", "Monthly DBU: this month vs last month")
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
        {"label": "DBU this month", "value": f"{cur:,.1f}", "icon": "📅",
         "help": HELP["kpi_dbu_month"]},
        {"label": "DBU last month", "value": f"{prev:,.1f}", "icon": "📆",
         "delta": f"{pct:+.1f}% vs prior", "delta_tone": tone,
         "help": HELP["kpi_dbu_last_month"]},
        {"label": "Potential savings", "value": f"{float(df.iloc[0]['savings_20pct'] or 0):,.1f} DBU",
         "icon": "💡", "delta": "Rough −20% estimate", "delta_tone": "neutral",
         "help": HELP["kpi_savings_est"]},
    ])
    trend, _ = run_query(f"""
        SELECT usage_date, SUM(usage_quantity) AS daily_dbu
        FROM billing_usage_full WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(trend, "usage_date", "daily_dbu", "Daily DBU trend", help=HELP["daily_dbu_trend"])


def render_daily_trends(run_query) -> None:
    page_header("DBU trends", "Daily usage by product")
    df, err = run_query(f"""
        SELECT usage_date, billing_origin_product, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE {f_usage_date()}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if show_error(err):
        return
    area_chart(df, "usage_date", "dbu", "billing_origin_product", "DBU by product", help=HELP["dbu_by_product"])


def render_sku_breakdown(run_query) -> None:
    page_header("SKU mix", "Top billing SKUs")
    c1, c2 = st.columns(2)
    with c1:
        df, err = run_query(f"""
            SELECT sku_name, SUM(usage_quantity) AS dbu
            FROM billing_usage_full WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        if not show_error(err):
            bar_chart(df, "sku_name", "dbu", "Top SKUs", orientation="h", help=HELP["top_skus"])
    with c2:
        df2, _ = run_query(f"""
            SELECT usage_type, SUM(usage_quantity) AS dbu
            FROM billing_usage_full WHERE {f_usage_date()}
            GROUP BY 1
        """)
        pie_chart(df2, "usage_type", "dbu", "Usage type mix", help=HELP["usage_type_mix"])


def render_team_attribution(run_query) -> None:
    page_header("By team", "DBU by team, cost center, and environment")
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
        bar_chart(by_team, "team", "dbu", "DBU by team", help=HELP["dbu_by_team"])
    with c2:
        env_df = df.groupby("environment", as_index=False)["dbu"].sum() if df is not None and not df.empty else None
        pie_chart(env_df, "environment", "dbu", "By environment", help=HELP["dbu_by_env"])
    data_table(df, title="Team attribution detail", help=HELP["tbl_team_attribution"])


def render_monthly_comparison(run_query) -> None:
    page_header("Monthly view", "DBU month over month")
    df, err = run_query(f"""
        SELECT date_trunc('month', usage_date) AS month, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY 1
    """)
    if show_error(err):
        return
    bar_chart(df, "month", "dbu", "Monthly DBU", help=HELP["monthly_dbu"])
    data_table(df, title="Monthly DBU detail", help=HELP["tbl_monthly_dbu"])


def render_list_prices(run_query) -> None:
    page_header("List prices", "Usage vs Databricks list prices")
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
        bar_chart(df, "sku_name", "total_dbu", "DBU by SKU", orientation="h", help=HELP["dbu_by_sku"])
    with c2:
        data_table(prices, title="List prices", help=HELP["tbl_list_prices"])


def render_storage_network(run_query) -> None:
    page_header("Storage & network", "Usage outside compute")
    df, err = run_query(f"""
        SELECT usage_date, billing_origin_product, SUM(usage_quantity) AS dbu
        FROM billing_usage_full
        WHERE billing_origin_product IN ('STORAGE', 'NETWORKING')
          AND {f_usage_date()}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if show_error(err):
        return
    area_chart(df, "usage_date", "dbu", "billing_origin_product", "Storage & networking", help=HELP["storage_networking"])


def render_top_consumers(run_query) -> None:
    page_header("Top spenders", "Highest DBU: clusters, jobs, warehouses, users")
    tabs = st.tabs(["Clusters", "Jobs", "Warehouses", "Users"])
    with tabs[0]:
        df, err = run_query(f"""
            SELECT cluster_name, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE cluster_id IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        if not show_error(err):
            bar_chart(df, "cluster_name", "dbu", "Top clusters", orientation="h", help=HELP["top_clusters"])
    with tabs[1]:
        df, _ = run_query(f"""
            SELECT job_name, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE job_id IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        bar_chart(df, "job_name", "dbu", "Top jobs", orientation="h", help=HELP["top_jobs"])
    with tabs[2]:
        df, _ = run_query(f"""
            SELECT warehouse_name, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE warehouse_id IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        bar_chart(df, "warehouse_name", "dbu", "Top warehouses", orientation="h", help=HELP["top_warehouses"])
    with tabs[3]:
        df, _ = run_query(f"""
            SELECT run_as, SUM(usage_quantity) AS dbu
            FROM billing_usage_full
            WHERE run_as IS NOT NULL AND {f_usage_date()}
            GROUP BY 1 ORDER BY dbu DESC LIMIT 15
        """)
        bar_chart(df, "run_as", "dbu", "Top users", orientation="h", help=HELP["top_users"])
