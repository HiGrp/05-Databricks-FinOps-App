"""Home — spend, savings, top actions."""

from __future__ import annotations

import html
from datetime import date

import pandas as pd
import streamlit as st

from dashboards import findings, savings
from dashboards.components import bar_chart, page_header, show_error
from dashboards.date_filter import comparison_label, f_usage_date, f_usage_date_prev, init_dates
from dashboards.pricing import cost, fmt_money

PRODUCT_LABELS = {
    "ALL_PURPOSE": "Interactive clusters",
    "JOBS": "Jobs",
    "SQL": "SQL warehouses",
    "SERVERLESS_SQL": "Serverless SQL",
    "STORAGE": "Storage",
    "NETWORKING": "Networking",
    "DLT": "Pipelines (DLT)",
    "MODEL_SERVING": "Model serving",
    "INTERACTIVE": "Serverless notebooks",
}


def _pct(cur: float, prev: float) -> float | None:
    return (cur - prev) / prev * 100 if prev else None


def _spend(run_query) -> tuple[float, float] | None:
    df, err = run_query(f"""
        SELECT (SELECT SUM({cost()}) FROM billing_cost WHERE {f_usage_date()}) AS cur,
               (SELECT SUM({cost()}) FROM billing_cost WHERE {f_usage_date_prev()}) AS prev
    """)
    if show_error(err) or df is None or df.empty:
        return None
    return float(df.iloc[0]["cur"] or 0), float(df.iloc[0]["prev"] or 0)


def _summary(spend_m: float, change: float | None, avoidable: float, high: int) -> None:
    trend = "" if change is None else f' <span class="muted">({change:+.0f}% {html.escape(comparison_label())})</span>'
    share = f" — {avoidable / spend_m:.0%} of spend" if spend_m else ""
    risks = (
        f"{high} high-priority issue{'s' if high > 1 else ''} to fix."
        if high else "No high-priority issue detected."
    )
    st.markdown(
        f'<p class="home-summary">'
        f"<strong>{fmt_money(spend_m)}/mo</strong> on Databricks{trend}. "
        f"<strong>{fmt_money(avoidable)}/mo</strong> avoidable{share}. {risks}"
        f"</p>",
        unsafe_allow_html=True,
    )


def _months_back(end: date, n: int) -> date:
    y, m = end.year, end.month - n
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, 1)


def _monthly_chart(run_query) -> None:
    init_dates()
    end = st.session_state.filter_date_end
    df, err = run_query(f"""
        SELECT DATE_TRUNC('month', usage_date) AS month, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE usage_date >= '{_months_back(end, 5)}' AND usage_date <= '{end}'
        GROUP BY 1 ORDER BY 1
    """)
    if show_error(err) or df is None or df.empty:
        return
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%b %Y")
    df.loc[df.index[-1], "month"] += " (to date)"
    title = "Spend per month"
    if len(df) >= 3:
        last, before = float(df["cost"].iloc[-2]), float(df["cost"].iloc[-3])
        change = _pct(last, before)
        if change is not None:
            title = f"Last full month: {fmt_money(last)} ({change:+.0f}% vs prior month)"
    bar_chart(df, "month", "cost", title,
              help="Net cost per calendar month. The last bar is the current month so far.")


def _product_chart(run_query) -> None:
    df, err = run_query(f"""
        SELECT billing_origin_product AS product, SUM({cost()}) AS cost
        FROM billing_cost WHERE {f_usage_date()}
        GROUP BY 1 ORDER BY cost DESC
    """)
    if show_error(err) or df is None or df.empty:
        return
    df = df.copy()
    total = float(df["cost"].sum()) or 1
    top = df.iloc[0]
    df["product"] = df["product"].map(lambda p: PRODUCT_LABELS.get(p, str(p).replace("_", " ").title()))
    title = f"{PRODUCT_LABELS.get(top['product'], top['product'])} = {float(top['cost']) / total:.0%} of spend"
    bar_chart(df.head(6).iloc[::-1], "product", "cost", title, orientation="h",
              help="Where the money goes. Interactive clusters are the most expensive compute: aim under 30%.")


def render_home(run_query) -> None:
    page_header("Overview")
    spend = _spend(run_query)
    if spend is None:
        return
    cur, prev = spend
    spend_m, change = savings._monthly(cur), _pct(cur, prev)
    items = findings.all_findings(run_query)
    avoidable = sum(f.monthly_usd or 0 for f in items)
    high = sum(f.severity == "High" for f in items)

    _summary(spend_m, change, avoidable, high)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Spend / month", fmt_money(spend_m),
              delta=None if change is None else f"{change:+.0f}% {comparison_label()}",
              delta_color="inverse")
    c2.metric("💡 Avoidable / month", fmt_money(avoidable), delta=f"{fmt_money(avoidable * 12)}/yr", delta_color="off")
    c3.metric("📉 Waste removed / month", fmt_money(findings.waste_removed(run_query)))
    c4.metric("🩺 Health score", f"{findings.health_score(items)} / 100")

    left, right = st.columns(2, gap="medium")
    with left:
        _monthly_chart(run_query)
    with right:
        _product_chart(run_query)

    st.markdown('<p class="block-label">✅ Top actions</p>', unsafe_allow_html=True)
    findings.render_top(run_query, n=3, key="home")
