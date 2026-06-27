"""Composants UI partagés — cartes, charts, headers (100% composants Streamlit natifs)."""

from __future__ import annotations

import html

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboards.theme import PLOTLY_TEMPLATE, THEME

COLORS = {
    "primary": THEME["primary"],
    "brand": THEME["brand"],
    "danger": THEME["danger"],
    "success": THEME["success"],
    "warning": THEME["warning"],
    "muted": THEME["text_muted"],
}

CHART_COLOR_SEQUENCE = PLOTLY_TEMPLATE["layout"]["colorway"]
NULL_LABEL = "(not set)"
_BLANK_LABELS = frozenset({"", "nan", "none", "<na>", "nat", "undefined", "null"})

# Human-readable hover / axis labels (avoids Plotly showing "undefined")
_FIELD_LABELS = {
    "usage_date": "Date",
    "day": "Date",
    "event_dt": "Date",
    "month": "Month",
    "dbu": "DBU",
    "daily_dbu": "DBU",
    "weekend_dbu": "DBU",
    "total_dbu": "DBU",
    "cluster_name": "Cluster",
    "cluster_id": "Cluster",
    "warehouse_name": "Warehouse",
    "warehouse_id": "Warehouse",
    "job_name": "Job",
    "run_as": "User",
    "executed_by": "User",
    "user_email": "User",
    "service_name": "Service",
    "product": "Product",
    "billing_origin_product": "Product",
    "sku_name": "SKU",
    "team": "Team",
    "environment": "Environment",
    "result_state": "Status",
    "task_type": "Task type",
    "statement_type": "Statement",
    "execution_status": "Status",
    "action_name": "Action",
    "event_type": "Event",
    "runs": "Runs",
    "events": "Events",
    "queries": "Queries",
    "failures": "Failures",
    "success_pct": "Success %",
    "avg_ms": "Avg time (ms)",
    "avg_cpu": "Avg CPU %",
    "avg_mem": "Avg memory %",
    "spill_gb": "Spill (GB)",
    "cache_pct": "Cache hit %",
    "avg_min": "Avg duration (min)",
    "avg_queue_ms": "Queue time (ms)",
    "avg_run_s": "Run time (s)",
    "avg_queue_s": "Queue time (s)",
    "avg_exec_s": "Execution time (s)",
    "denied": "Denied",
    "logins": "Logins",
    "actions": "Actions",
    "n": "Count",
    "nombre": "Count",
    "dbr_version": "DBR version",
    "workspace_short": "Workspace",
    "driver_node_type": "Node type",
    "data_security_mode": "Security mode",
    "cluster_source": "Source",
    "usage_type": "Usage type",
    "source_ip_address": "Source IP",
}


def int_or_zero(value) -> int:
    if value is None:
        return 0
    try:
        number = float(value)
        if number != number:  # NaN
            return 0
        return int(number)
    except (TypeError, ValueError):
        return 0


def format_int(value, suffix: str = "") -> str:
    if value is None:
        return "—"
    try:
        number = float(value)
        if number != number:  # NaN
            return "—"
        text = f"{int(number):,}"
        return f"{text} {suffix}".strip() if suffix else text
    except (TypeError, ValueError):
        return "—"


def _coerce_label(value) -> str:
    if value is None:
        return NULL_LABEL
    try:
        if pd.isna(value):
            return NULL_LABEL
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text.lower() in _BLANK_LABELS:
        return NULL_LABEL
    return text


def _chart_labels(*columns: str) -> dict[str, str]:
    return {col: _FIELD_LABELS.get(col, col.replace("_", " ").title()) for col in columns}


def _prepare_chart_df(df: pd.DataFrame, *columns: str, color: str | None = None) -> pd.DataFrame:
    cols = [c for c in columns if c]
    if color:
        cols.append(color)
    if not cols:
        return _sanitize_chart_df(df)
    out = _sanitize_chart_df(df, *cols)
    return _drop_blank_categories(out, *cols)


def _apply_plotly_theme(fig: go.Figure) -> go.Figure:
    layout = {k: v for k, v in PLOTLY_TEMPLATE["layout"].items() if k not in ("xaxis", "yaxis", "title")}
    fig.update_layout(**layout)
    fig.update_layout(
        title=None,
        hovermode="closest",
        legend_title_text=None,
    )
    fig.update_xaxes(
        title=None,
        gridcolor="#F1F5F9",
        linecolor="#E2E8F0",
        zerolinecolor="#F1F5F9",
    )
    fig.update_yaxes(
        title=None,
        gridcolor="#F1F5F9",
        linecolor="#E2E8F0",
        zerolinecolor="#F1F5F9",
    )
    _fix_plotly_traces(fig)
    return fig


def _fix_plotly_traces(fig: go.Figure) -> None:
    for trace in fig.data:
        name = trace.name
        if name is None or str(name).strip().lower() in _BLANK_LABELS:
            trace.name = NULL_LABEL
            if trace.type in ("bar", "scatter", "pie", "sunburst", "funnelarea", "histogram"):
                trace.showlegend = False
    fig.update_traces(hoverlabel=dict(namelength=-1))


def _sanitize_chart_df(df: pd.DataFrame, *columns: str) -> pd.DataFrame:
    out = df.copy()
    target_cols = columns or tuple(
        c for c in out.columns if out[c].dtype == object or pd.api.types.is_string_dtype(out[c])
    )
    for col in target_cols:
        if col not in out.columns:
            continue
        out[col] = out[col].map(_coerce_label)
    return out


def _drop_blank_categories(df: pd.DataFrame, *columns: str) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out = out[out[col] != NULL_LABEL]
    return out


def _refresh_page_data() -> None:
    from dashboards.query_cache import bump_cache_epoch

    bump_cache_epoch()
    st.cache_data.clear()
    st.rerun()


def _info_tip_html(help_text: str) -> str:
    from dashboards.chart_help import info_tip_html

    return info_tip_html(help_text)


def page_header(
    title: str,
    subtitle: str,
    *,
    category: str | None = None,
    badge: str | None = None,
    icon: str | None = None,
    help: str | None = None,
) -> None:
    if st.session_state.get("_suppress_page_header"):
        return

    from dashboards.date_filter import period_display

    category = category or st.session_state.get("nav_category") or ""
    icon = icon or st.session_state.get("nav_icon") or ""
    if subtitle == "":
        subtitle = st.session_state.get("nav_desc") or ""

    heading = f"{icon} {title}".strip() if icon else title
    badge_html = (
        f'<span class="page-hero-badge">{html.escape(badge)}</span>' if badge else ""
    )
    breadcrumb = (
        f'<div class="page-hero-breadcrumb"><span>{html.escape(category)}</span></div>'
        if category else ""
    )
    sub_html = (
        f'<p class="page-hero-sub">{html.escape(subtitle)}</p>' if subtitle else ""
    )
    period = html.escape(period_display())
    from dashboards.chart_help import HELP

    title_tip = _info_tip_html(help) if help else ""

    col_main, col_btn = st.columns([9, 3], gap="small", vertical_alignment="top")
    with col_main:
        st.markdown(
            f'<div class="page-hero">{breadcrumb}'
            f'<h1 class="page-hero-title">{html.escape(heading)}{badge_html}{title_tip}</h1>'
            f"{sub_html}"
            f'<div class="page-hero-meta">'
            f'<span class="page-context-pill">📅 {period}</span>'
            f'<span class="page-context-hint">Change dates in the sidebar</span>'
            f"{_info_tip_html(HELP['ctx_period'])}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button(
            "↻ Refresh data",
            key=f"refresh_{category}",
            help=HELP["ctx_refresh"],
            use_container_width=True,
        ):
            _refresh_page_data()


def render_page_toolbar() -> None:
    """Deprecated — context is shown inside page_header()."""
    return


def section_header(title: str, hint: str | None = None, *, help: str | None = None) -> None:
    tip = _info_tip_html(help) if help else ""
    hint_html = (
        f'<p class="section-head-hint">{html.escape(hint)}</p>' if hint else ""
    )
    st.markdown(
        f'<div class="section-head">'
        f'<p class="section-head-title">{html.escape(title)}{tip}</p>'
        f"{hint_html}</div>",
        unsafe_allow_html=True,
    )


def show_error(err: str | None) -> bool:
    if err:
        st.error(err)
        return True
    return False


def show_empty(message: str = "No data for this period.") -> None:
    st.info(message)


def _render_chart_title(title: str, help: str | None = None) -> None:
    if not help:
        st.markdown(f"**{title}**")
        return
    st.markdown(
        f'<div class="chart-title-row">'
        f'<strong class="chart-title-text">{html.escape(title)}</strong>'
        f"{_info_tip_html(help)}"
        f"</div>",
        unsafe_allow_html=True,
    )


def kpi_cards(items: list[dict]) -> None:
    """KPIs via st.metric — max 3 per row (mobile-friendly)."""
    if not items:
        return
    for start in range(0, len(items), 3):
        chunk = items[start : start + 3]
        cols = st.columns(len(chunk))
        for col, item in zip(cols, chunk):
            with col:
                icon = item.get("icon", "")
                label = item.get("label", "")
                display_label = f"{icon} {label}".strip() if icon else label
                delta = item.get("delta")
                tone = item.get("delta_tone", "neutral")
                delta_color = "inverse" if tone == "up" else "normal"
                st.metric(
                    label=display_label,
                    value=item.get("value", "—"),
                    delta=delta,
                    delta_color=delta_color if delta else "off",
                    help=item.get("help"),
                )


def metrics_row(items: list) -> None:
    cards: list[dict] = []
    for item in items:
        if isinstance(item, dict):
            cards.append(item)
            continue
        label, value = item[0], item[1]
        delta = item[2] if len(item) > 2 else None
        tip = item[3] if len(item) > 3 else None
        cards.append({"label": label, "value": value, "delta": delta, "help": tip})
    kpi_cards(cards)


def _chart_container(title: str | None, render_fn, *, help: str | None = None) -> None:
    with st.container(border=True):
        if title:
            _render_chart_title(title, help)
        render_fn()


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = COLORS["primary"],
    *,
    help: str | None = None,
) -> None:
    if df is None or df.empty:
        show_empty()
        return

    def _render():
        data = _prepare_chart_df(df, x, y)
        if data.empty:
            show_empty()
            return
        fig = px.line(data, x=x, y=y, labels=_chart_labels(x, y), template="plotly_white")
        fig.update_traces(line_color=color, line_width=2.5)
        _apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    _chart_container(title, _render, help=help)


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = COLORS["primary"],
    orientation: str = "v",
    *,
    help: str | None = None,
) -> None:
    if df is None or df.empty:
        show_empty()
        return

    def _render():
        data = _prepare_chart_df(df, x, y)
        if data.empty:
            show_empty()
            return
        labels = _chart_labels(x, y)
        if orientation == "h":
            fig = px.bar(data, x=y, y=x, orientation="h", labels=labels, template="plotly_white")
            fig.update_yaxes(type="category")
        else:
            fig = px.bar(data, x=x, y=y, labels=labels, template="plotly_white")
            fig.update_xaxes(type="category")
        fig.update_traces(marker_color=color)
        _apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    _chart_container(title, _render, help=help)


def pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
    *,
    help: str | None = None,
) -> None:
    if df is None or df.empty:
        show_empty()
        return

    def _render():
        data = _prepare_chart_df(df, names, values)
        if data.empty:
            show_empty()
            return
        fig = px.pie(
            data,
            names=names,
            values=values,
            hole=0.45,
            labels=_chart_labels(names, values),
            template="plotly_white",
        )
        _apply_plotly_theme(fig)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    _chart_container(title, _render, help=help)


def area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None,
    title: str,
    *,
    help: str | None = None,
) -> None:
    if df is None or df.empty:
        show_empty()
        return

    def _render():
        cols = [x] + ([color] if color else [])
        data = _prepare_chart_df(df, *cols, color=color)
        if data.empty:
            show_empty()
            return
        label_cols = cols if color else [x, y]
        fig = px.area(
            data,
            x=x,
            y=y,
            color=color,
            labels=_chart_labels(*label_cols),
            template="plotly_white",
        )
        _apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    _chart_container(title, _render, help=help)


def plotly_figure(fig: go.Figure, *, title: str | None = None, help: str | None = None) -> None:
    _apply_plotly_theme(fig)
    with st.container(border=True):
        if title:
            _render_chart_title(title, help)
        st.plotly_chart(fig, use_container_width=True)


def grouped_bar_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: list[str],
    title: str,
    *,
    barmode: str = "group",
    help: str | None = None,
) -> None:
    if df is None or df.empty:
        show_empty()
        return

    def _render():
        data = _prepare_chart_df(df, x)
        if data.empty:
            show_empty()
            return
        fig = px.bar(
            data,
            x=x,
            y=y_cols,
            barmode=barmode,
            labels=_chart_labels(x, *y_cols),
            template="plotly_white",
        )
        fig.update_xaxes(type="category")
        _apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    _chart_container(title, _render, help=help)


def data_table(
    df: pd.DataFrame | None,
    height: int | None = None,
    title: str | None = None,
    *,
    help: str | None = None,
) -> None:
    if df is None or df.empty:
        show_empty()
        return
    with st.container(border=True):
        if title or help:
            _render_chart_title(title or "Details", help)
        st.dataframe(
            df,
            use_container_width=True,
            height=height,
            hide_index=True,
        )


def two_column_charts(left_fn, right_fn) -> None:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        left_fn()
    with c2:
        right_fn()


# ---------------------------------------------------------------------------
# Status KPI Cards — coloration conditionnelle (vert / orange / rouge)
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "ok": {"bg": "#ECFDF5", "border": "#059669", "text": "#065F46", "badge": "OK"},
    "warning": {"bg": "#FFFBEB", "border": "#D97706", "text": "#92400E", "badge": "Warning"},
    "danger": {"bg": "#FEF2F2", "border": "#DC2626", "text": "#991B1B", "badge": "Critical"},
}


def _resolve_status(value: float, thresholds: dict) -> str:
    """Détermine le statut selon les seuils.

    thresholds = {"warning": 5, "danger": 15, "direction": "higher_is_worse"}
    - direction="higher_is_worse" (défaut) : vert si < warning, orange si >= warning, rouge si >= danger
    - direction="lower_is_worse" : vert si > warning, orange si <= warning, rouge si <= danger
    """
    warn = thresholds.get("warning", 0)
    crit = thresholds.get("danger", 0)
    direction = thresholds.get("direction", "higher_is_worse")

    if direction == "higher_is_worse":
        if value < warn:
            return "ok"
        elif value < crit:
            return "warning"
        else:
            return "danger"
    else:  # lower_is_worse (ex: taux de succès)
        if value > warn:
            return "ok"
        elif value > crit:
            return "warning"
        else:
            return "danger"


def status_kpi_cards(items: list[dict]) -> None:
    """KPI cards avec coloration conditionnelle basée sur des seuils.

    Chaque item = {
        "label": str,
        "value": str (affiché),
        "raw_value": float (pour calcul du seuil),
        "icon": str (optionnel),
        "thresholds": {"warning": N, "danger": N, "direction": "higher_is_worse"|"lower_is_worse"},
        "hint": str (explication pédagogique, optionnel),
    }

    Si "thresholds" est absent, la carte reste neutre (style standard).
    """
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            thresholds = item.get("thresholds")
            raw = item.get("raw_value")
            if thresholds and raw is not None:
                status = _resolve_status(float(raw), thresholds)
                style = _STATUS_COLORS[status]
            else:
                style = {"bg": THEME["card_bg"], "border": THEME["card_border"], "text": THEME["text"], "badge": ""}
                status = None

            icon = item.get("icon", "")
            label = item.get("label", "")
            value = item.get("value", "\u2014")
            hint = item.get("hint", "")
            badge_text = style["badge"] if status else ""

            badge_html = ""
            if badge_text:
                badge_html = f'<span style="font-size:0.6rem;font-weight:600;background:{style["border"]};color:white;padding:2px 8px;border-radius:999px;margin-left:6px;vertical-align:middle;">{badge_text}</span>'

            hint_html = ""
            if hint:
                hint_html = f'<div style="font-size:0.68rem;color:{style["text"]};opacity:0.8;margin-top:0.4rem;font-style:italic;">{hint}</div>'

            card_html = f"""
            <div style="
                background: {style['bg']};
                border: 2px solid {style['border']};
                border-radius: 12px;
                padding: 1rem 1.2rem;
                text-align: center;
                min-height: 130px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                margin-bottom: 0.5rem;
            ">
                <div style="font-size:0.78rem;color:{style['text']};font-weight:500;margin-bottom:0.3rem;">
                    {icon} {label} {badge_html}
                </div>
                <div style="font-size:1.8rem;font-weight:700;color:{style['text']};line-height:1.2;">
                    {value}
                </div>
                {hint_html}
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
