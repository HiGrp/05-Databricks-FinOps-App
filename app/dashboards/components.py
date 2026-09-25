"""Composants UI partagés - cartes, charts, headers (100% composants Streamlit natifs)."""

from __future__ import annotations

import html

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboards.theme import PLOTLY_TEMPLATE, THEME

COLORS = {
    "primary": THEME["accent"],
    "brand": THEME["brand"],
    "danger": THEME["danger"],
    "success": THEME["success"],
    "warning": THEME["warning"],
    "muted": THEME["muted"],
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
    "cost": "Cost ($)",
    "quantity": "Quantity",
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
        return "-"
    try:
        number = float(value)
        if number != number:  # NaN
            return "-"
        text = f"{int(number):,}"
        return f"{text} {suffix}".strip() if suffix else text
    except (TypeError, ValueError):
        return "-"


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
    """Never use empty strings - Plotly.js shows them as 'undefined'."""
    return {
        col: _FIELD_LABELS.get(col, col.replace("_", " ").title())
        for col in columns
        if col
    }


def _prepare_chart_df(df: pd.DataFrame, *columns: str, color: str | None = None) -> pd.DataFrame:
    dim_cols = [c for c in columns if c]
    if color:
        dim_cols.append(color)
    out = df.copy()
    cat_cols = [
        c for c in dim_cols
        if c in out.columns
        and (out[c].dtype == object or pd.api.types.is_string_dtype(out[c]))
    ]
    if not cat_cols:
        return out
    out = _sanitize_chart_df(out, *cat_cols)
    return _drop_blank_categories(out, *cat_cols)


def _clean_trace_name(name) -> str:
    if name is None:
        return NULL_LABEL
    text = str(name).strip()
    if not text or text.lower() in _BLANK_LABELS:
        return NULL_LABEL
    return text


def _fix_plotly_traces(fig: go.Figure) -> None:
    # Trace types that do not expose a `showlegend` property.
    _NO_SHOWLEGEND = ("sunburst", "treemap", "icicle")
    for trace in fig.data:
        trace.name = _clean_trace_name(trace.name)
        if trace.name == NULL_LABEL and trace.type not in _NO_SHOWLEGEND:
            trace.showlegend = False

        ttype = trace.type
        orient = getattr(trace, "orientation", None)
        if ttype == "bar":
            if orient == "h":
                trace.hovertemplate = "%{y}: %{x:,}<extra></extra>"
            else:
                trace.hovertemplate = "%{x}: %{y:,}<extra></extra>"
        elif ttype in ("scatter", "scattergl") and trace.mode and "lines" in trace.mode:
            trace.hovertemplate = "%{x}: %{y:,}<extra></extra>"
        elif ttype == "pie":
            trace.hovertemplate = "%{label}: %{value:,} (%{percent})<extra></extra>"
        elif ttype == "heatmap":
            trace.hovertemplate = "%{x}: %{y}<br>Count: %{z:,}<extra></extra>"
        elif ttype in ("sunburst", "treemap"):
            trace.hovertemplate = "%{label}: %{value:,}<extra></extra>"

        if trace.name != NULL_LABEL and trace.hovertemplate and "<extra></extra>" in trace.hovertemplate:
            trace.hovertemplate = trace.hovertemplate.replace(
                "<extra></extra>", f"<extra>{trace.name}</extra>"
            )

    fig.update_traces(hoverlabel=dict(namelength=-1))


def _fix_plotly_layout(fig: go.Figure) -> None:
    """Drop axis titles - chart titles live in Streamlit markdown above the figure."""
    fig.update_layout(
        title=None,
        hovermode="closest",
        legend_title_text=None,
        xaxis_title=None,
        yaxis_title=None,
    )
    fig.update_xaxes(
        title_text=None,
        showspikes=False,
        gridcolor="#F3F4F6",
        linecolor="#E5E7EB",
        zerolinecolor="#F3F4F6",
    )
    fig.update_yaxes(
        title_text=None,
        showspikes=False,
        gridcolor="#F3F4F6",
        linecolor="#E5E7EB",
        zerolinecolor="#F3F4F6",
    )
    fig.update_coloraxes(colorbar=dict(title=dict(text="")))


def _show_plotly_chart(fig: go.Figure) -> None:
    """theme=None - Streamlit's default plotly theme renders empty axis titles as 'undefined'."""
    st.plotly_chart(fig, use_container_width=True, theme=None)


def _apply_plotly_theme(fig: go.Figure) -> go.Figure:
    layout = {k: v for k, v in PLOTLY_TEMPLATE["layout"].items() if k not in ("xaxis", "yaxis", "title")}
    fig.update_layout(**layout)
    _fix_plotly_layout(fig)
    _fix_plotly_traces(fig)
    return fig


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


def refresh_data() -> None:
    from dashboards.query_cache import bump_cache_epoch

    bump_cache_epoch()
    st.cache_data.clear()
    st.rerun()


def _info_tip_html(help_text: str) -> str:
    from dashboards.chart_help import info_tip_html

    return info_tip_html(help_text)


def page_header(title: str, subtitle: str = "", **_) -> None:
    if st.session_state.get("_suppress_page_header"):
        return
    from dashboards.catalog_config import get_catalog
    from dashboards.date_filter import period_display

    icon = st.session_state.get("nav_icon", "")
    prefix = f'<span class="page-icon">{html.escape(icon)}</span> ' if icon else ""
    refresh_help = (
        f"Reload data from catalog « {get_catalog()} » "
        f"for {period_display()} ({st.session_state.get('period_preset', 'Last 30 days')})."
    )

    title_col, refresh_col = st.columns([1, 0.22], gap="small", vertical_alignment="center")
    with title_col:
        st.markdown(
            f'<h1 class="page-title">{prefix}{html.escape(title)}</h1>',
            unsafe_allow_html=True,
        )
    with refresh_col:
        if st.button(
            "↻ Refresh",
            key="page_refresh_data",
            help=refresh_help,
            type="secondary",
        ):
            refresh_data()


def section_header(title: str, description: str | None = None, *, icon: str | None = None, **_) -> None:
    icon_html = f'<span class="section-icon">{html.escape(icon)}</span>' if icon else ""
    st.markdown(f'<p class="section-title">{icon_html}{html.escape(title)}</p>', unsafe_allow_html=True)
    if description:
        from dashboards.guides import md_inline
        st.markdown(f'<p class="section-desc">{md_inline(description)}</p>', unsafe_allow_html=True)


_ERROR_HINTS = (
    (("INSUFFICIENT_PERMISSIONS", "USE SCHEMA", "USE CATALOG", "PERMISSION_DENIED"),
     "Missing permissions on system tables - complete **Setup → Permissions** (step 2)."),
    (("No SQL warehouse", "warehouse"),
     "SQL warehouse missing or unreachable - check **Setup → Connect** (step 1)."),
    (("TABLE_OR_VIEW_NOT_FOUND", "SCHEMA_NOT_FOUND"),
     "System schema not available - ask an account admin to enable system tables."),
    (("default auth", "cannot configure default credentials", "Config: host", "discovery_url", "Not connected"),
     "Not connected to Databricks - complete **Setup → Connect** (step 1)."),
)

_CONNECTION_ERRORS = (
    "insufficient_permissions", "use schema", "use catalog", "permission_denied",
    "no sql warehouse", "warehouse", "schema_not_found", "table_or_view_not_found",
    "default auth", "cannot configure default credentials", "config: host",
    "discovery_url", "not connected",
)


def go_to_setup(*, key: str = "go_setup") -> None:
    if st.button("Open Setup", key=key, type="primary"):
        st.session_state.nav_category = "Setup"
        st.rerun()


def render_connect_gate() -> None:
    st.markdown('<h1 class="page-title">Connect Databricks</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="lead">Enter your workspace in Setup, then run the permission SQL in Databricks.</p>',
        unsafe_allow_html=True,
    )
    go_to_setup(key="connect_gate_btn")


def show_error(err: str | BaseException | None) -> bool:
    if err is None:
        return False
    if not isinstance(err, str):
        err = str(err)
    if not err:
        return False
    from app_config import is_dev_mode
    from connection import is_connected

    if not is_dev_mode() and not is_connected() and any(k in err.lower() for k in _CONNECTION_ERRORS):
        return True
    hint = next((h for keys, h in _ERROR_HINTS if any(k.lower() in err.lower() for k in keys)), None)
    if hint is None:
        st.error(err)
        return True
    if st.session_state.get("_error_hint_shown") == hint:
        return True
    st.session_state["_error_hint_shown"] = hint
    st.warning(hint)
    if any(k in err.lower() for k in _CONNECTION_ERRORS):
        go_to_setup(key=f"err_setup_{abs(hash(err)) % 10_000}")
    with st.expander("Technical details"):
        st.code(err[:2000])
    return True


def show_empty(message: str = "No data for this period.") -> None:
    st.info(message)


def _render_chart_title(title: str, help: str | None = None) -> None:
    caption = f'<p class="chart-caption">{html.escape(help)}</p>' if help else ""
    st.markdown(
        f'<div class="chart-title-row"><strong class="chart-title-text">{html.escape(title)}</strong></div>'
        f"{caption}",
        unsafe_allow_html=True,
    )


def kpi_cards(items: list[dict]) -> None:
    """KPIs via st.metric - max 3 per row (mobile-friendly)."""
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
                if tone == "up":
                    delta_color = "inverse"
                elif tone == "off":
                    delta_color = "off"
                else:
                    delta_color = "normal"
                st.metric(
                    label=display_label,
                    value=item.get("value", "-"),
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
        _show_plotly_chart(fig)

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
        _show_plotly_chart(fig)

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
        _show_plotly_chart(fig)

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
        _show_plotly_chart(fig)

    _chart_container(title, _render, help=help)


def plotly_figure(fig: go.Figure, *, title: str | None = None, help: str | None = None) -> None:
    _apply_plotly_theme(fig)
    with st.container(border=True):
        if title:
            _render_chart_title(title, help)
        _show_plotly_chart(fig)


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
        _show_plotly_chart(fig)

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


def download_csv(df: pd.DataFrame | None, filename: str, *, key: str, label: str = "⬇ Export CSV") -> None:
    if df is None or df.empty:
        return
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def two_column_charts(left_fn, right_fn) -> None:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        left_fn()
    with c2:
        right_fn()


# ---------------------------------------------------------------------------
# Status KPI Cards - coloration conditionnelle (vert / orange / rouge)
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
