"""Cost helpers — list cost from billing_cost, adjusted by the negotiated discount."""

from __future__ import annotations

import streamlit as st

from app_config import default_discount_pct

CURRENCY_SYMBOL = "$"


def discount_pct() -> float:
    return float(st.session_state.get("discount_pct", default_discount_pct()))


def cost(col: str = "list_cost") -> str:
    """SQL expression for the net cost of a billing_cost column."""
    factor = round(1 - discount_pct() / 100, 4)
    return f"COALESCE({col}, 0) * {factor}"


def fmt_money(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if number != number:
        return "—"
    return f"{CURRENCY_SYMBOL}{number:,.0f}"


def cost_basis_label() -> str:
    d = discount_pct()
    return f"list price −{d:g}%" if d else "list price"

