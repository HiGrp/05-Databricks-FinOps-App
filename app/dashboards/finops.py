"""FinOps dashboards - net cost (list price × usage, minus discount)."""

import streamlit as st

from dashboards.chart_help import HELP
from dashboards.components import (
    area_chart,
    bar_chart,
    data_table,
    download_csv,
    kpi_cards,
    line_chart,
    metrics_row,
    page_header,
    pie_chart,
    show_error,
)
from dashboards.date_filter import comparison_label, f_usage_date, f_usage_date_prev, period_days
from dashboards.pricing import cost, cost_basis_label, fmt_money


def render_executive(run_query) -> None:
    page_header("Summary", "Cost of the period vs the previous period")
    df, err = run_query(f"""
        SELECT
            (SELECT SUM({cost()}) FROM billing_cost WHERE {f_usage_date()}) AS cur,
            (SELECT SUM({cost()}) FROM billing_cost WHERE {f_usage_date_prev()}) AS prev
    """)
    if show_error(err) or df is None or df.empty:
        return
    cur, prev = float(df.iloc[0]["cur"] or 0), float(df.iloc[0]["prev"] or 0)
    days = period_days()
    delta = f"{(cur - prev) / prev * 100:+.1f}% {comparison_label()}" if prev else None
    tone = "up" if cur > prev else "down" if cur < prev else "neutral"

    kpi_cards([
        {"label": "Cost of the period", "value": fmt_money(cur),
         "delta": delta, "delta_tone": tone,
         "help": f"Net cost over the selected {days} days ({cost_basis_label()})."},
        {"label": "Cost / month", "value": fmt_money(cur * 30 / days),
         "help": "The period's cost scaled to 30 days, so any period can be compared."},
        {"label": "Annual run-rate", "value": fmt_money(cur * 365 / days),
         "help": "What a full year costs at the current pace."},
    ])
    trend, _ = run_query(f"""
        SELECT usage_date, SUM({cost()}) AS cost
        FROM billing_cost WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(trend, "usage_date", "cost", "Daily cost", help=HELP["daily_dbu_trend"])


def render_daily_trends(run_query) -> None:
    page_header("Cost trends", "Daily cost by product")
    df, err = run_query(f"""
        SELECT usage_date, billing_origin_product, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE {f_usage_date()}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if show_error(err):
        return
    area_chart(df, "usage_date", "cost", "billing_origin_product", "Cost by product", help=HELP["dbu_by_product"])


def render_sku_breakdown(run_query) -> None:
    page_header("SKU mix", "Top billing SKUs")
    c1, c2 = st.columns(2)
    with c1:
        df, err = run_query(f"""
            SELECT sku_name, SUM({cost()}) AS cost
            FROM billing_cost WHERE {f_usage_date()}
            GROUP BY 1 ORDER BY cost DESC LIMIT 15
        """)
        if not show_error(err):
            bar_chart(df, "sku_name", "cost", "Top SKUs by cost", orientation="h", help=HELP["top_skus"])
    with c2:
        df2, _ = run_query(f"""
            SELECT usage_type, SUM({cost()}) AS cost
            FROM billing_cost WHERE {f_usage_date()}
            GROUP BY 1
        """)
        pie_chart(df2, "usage_type", "cost", "Usage type mix", help=HELP["usage_type_mix"])


def render_team_attribution(run_query) -> None:
    page_header("Chargeback", "Cost by team, cost center, and environment")
    tag, _ = run_query(f"""
        SELECT SUM({cost()}) AS total,
               SUM(CASE WHEN team IS NULL OR TRIM(team) = '' THEN {cost()} ELSE 0 END) AS untagged
        FROM billing_cost
        WHERE {f_usage_date()}
    """)
    if tag is not None and not tag.empty:
        total = float(tag.iloc[0]["total"] or 0)
        untagged = float(tag.iloc[0]["untagged"] or 0)
        pct = (untagged / total * 100) if total else 0
        metrics_row([
            {"label": "Unallocated cost", "value": fmt_money(untagged), "delta": f"{pct:.0f}% of spend",
             "delta_tone": "up" if pct > 0 else "neutral",
             "help": "Cost with no Team tag - cannot be charged back."},
            {"label": "Allocated cost", "value": fmt_money(total - untagged),
             "help": "Cost carrying a Team tag."},
        ])
    df, err = run_query(f"""
        SELECT team, cost_center, environment, SUM(usage_quantity) AS quantity, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE {f_usage_date()} AND team IS NOT NULL
        GROUP BY 1, 2, 3 ORDER BY cost DESC
    """)
    if show_error(err):
        return
    c1, c2 = st.columns(2)
    with c1:
        by_team = df.groupby("team", as_index=False)["cost"].sum().sort_values("cost", ascending=False) \
            if df is not None and not df.empty else None
        bar_chart(by_team, "team", "cost", "Cost by team", help=HELP["dbu_by_team"])
    with c2:
        env_df = df.groupby("environment", as_index=False)["cost"].sum() if df is not None and not df.empty else None
        pie_chart(env_df, "environment", "cost", "By environment", help=HELP["dbu_by_env"])
    data_table(df, title="Chargeback detail", help=HELP["tbl_team_attribution"])
    download_csv(df, "finops_chargeback.csv", key="dl_chargeback", label="⬇ Export chargeback (CSV)")


def render_monthly_comparison(run_query) -> None:
    page_header("Monthly view", "Cost month over month")
    df, err = run_query(f"""
        SELECT date_trunc('month', usage_date) AS month, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY 1
    """)
    if show_error(err):
        return
    bar_chart(df, "month", "cost", "Monthly cost", help=HELP["monthly_dbu"])


def render_list_prices(run_query) -> None:
    page_header("Unit prices", "Effective unit price per SKU")
    df, err = run_query(f"""
        SELECT sku_name, usage_unit,
               SUM(usage_quantity) AS quantity,
               SUM({cost()}) AS cost,
               SUM({cost()}) / NULLIF(SUM(usage_quantity), 0) AS unit_price
        FROM billing_cost
        WHERE {f_usage_date()}
        GROUP BY 1, 2 ORDER BY cost DESC LIMIT 20
    """)
    if show_error(err):
        return
    data_table(df, title="Unit price by SKU", help=HELP["tbl_list_prices"])


def render_storage_network(run_query) -> None:
    page_header("Storage & network", "Cost outside compute")
    df, err = run_query(f"""
        SELECT usage_date, billing_origin_product, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE billing_origin_product IN ('STORAGE', 'NETWORKING')
          AND {f_usage_date()}
        GROUP BY 1, 2 ORDER BY 1
    """)
    if show_error(err):
        return
    area_chart(df, "usage_date", "cost", "billing_origin_product", "Storage & networking", help=HELP["storage_networking"])


def render_top_consumers(run_query) -> None:
    page_header("Top spenders", "Highest cost: clusters, jobs, warehouses, users")
    tabs = st.tabs(["Clusters", "Jobs", "Warehouses", "Users"])
    specs = [
        ("cluster_name", "cluster_id", "Top clusters", "top_clusters"),
        ("job_name", "job_id", "Top jobs", "top_jobs"),
        ("warehouse_name", "warehouse_id", "Top warehouses", "top_warehouses"),
        ("run_as", "run_as", "Top users", "top_users"),
    ]
    for tab, (label_col, id_col, title, help_key) in zip(tabs, specs):
        with tab:
            df, err = run_query(f"""
                SELECT {label_col}, SUM({cost()}) AS cost
                FROM billing_cost
                WHERE {id_col} IS NOT NULL AND {f_usage_date()}
                GROUP BY 1 ORDER BY cost DESC LIMIT 15
            """)
            if not show_error(err):
                bar_chart(df, label_col, "cost", title, orientation="h", help=HELP[help_key])
