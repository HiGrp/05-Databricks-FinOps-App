"""Global period filter — presets or custom, always ending yesterday."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, timedelta

import streamlit as st

PERIODS: dict[str, int | None] = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "Last 12 months": 365,
    "Custom": None,
}
DEFAULT_PERIOD = "Last 30 days"


def _last_complete_day() -> date:
    return date.today() - timedelta(days=1)


def _apply_preset() -> None:
    days = PERIODS.get(st.session_state.period_preset)
    if days:
        end = _last_complete_day()
        st.session_state.filter_date_start = end - timedelta(days=days - 1)
        st.session_state.filter_date_end = end


def init_dates() -> None:
    if st.session_state.get("period_preset") not in PERIODS:
        st.session_state.period_preset = DEFAULT_PERIOD
    if "filter_date_start" not in st.session_state or "filter_date_end" not in st.session_state:
        _apply_preset()


def sync_period() -> None:
    init_dates()
    _apply_preset()


def period_days() -> int:
    init_dates()
    return (st.session_state.filter_date_end - st.session_state.filter_date_start).days + 1


def comparison_label() -> str:
    return f"vs prev. {period_days()}d"


def _fmt(d: date) -> str:
    return d.strftime("%b %d, %Y")


def period_display() -> str:
    init_dates()
    start, end = st.session_state.filter_date_start, st.session_state.filter_date_end
    if start == end:
        return _fmt(start)
    if start.year == end.year and start.month == end.month:
        return f"{start.strftime('%b %d')} – {end.strftime('%d, %Y')}"
    return f"{_fmt(start)} – {_fmt(end)}"


def period_label() -> str:
    return period_display()


def _on_preset_change() -> None:
    st.session_state.period_preset = st.session_state._period_preset_w
    _apply_preset()


def _on_custom_change() -> None:
    picked = st.session_state._period_custom_w
    if isinstance(picked, (list, tuple)) and len(picked) == 2:
        st.session_state.filter_date_start, st.session_state.filter_date_end = picked


def render_period_picker(container=None) -> None:
    init_dates()
    ui = container or st
    options = list(PERIODS)
    ui.selectbox(
        "Period",
        options,
        index=options.index(st.session_state.period_preset),
        key="_period_preset_w",
        on_change=_on_preset_change,
    )
    if st.session_state.period_preset == "Custom":
        ui.date_input(
            "Dates",
            value=(st.session_state.filter_date_start, st.session_state.filter_date_end),
            max_value=_last_complete_day(),
            key="_period_custom_w",
            on_change=_on_custom_change,
            label_visibility="collapsed",
            format="YYYY-MM-DD",
        )


def _bounds() -> tuple[str, str]:
    init_dates()
    return str(st.session_state.filter_date_start), str(st.session_state.filter_date_end)


def f_usage_date(col: str = "usage_date") -> str:
    s, e = _bounds()
    return f"{col} >= '{s}' AND {col} <= '{e}'"


def f_event_date(col: str = "event_dt") -> str:
    s, e = _bounds()
    return f"{col} >= '{s}' AND {col} <= '{e}'"


def f_ts_date(col: str) -> str:
    s, e = _bounds()
    return (
        f"CAST({col} AS TIMESTAMP) >= TIMESTAMP '{s} 00:00:00' "
        f"AND CAST({col} AS TIMESTAMP) < TIMESTAMP '{e} 00:00:00' + INTERVAL '1' DAY"
    )


def _bounds_prev() -> tuple[str, str]:
    init_dates()
    start = st.session_state.filter_date_start
    end = st.session_state.filter_date_end
    span = (end - start).days
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=span)
    return str(prev_start), str(prev_end)


@contextmanager
def previous_period():
    init_dates()
    start, end = st.session_state.filter_date_start, st.session_state.filter_date_end
    prev_start, prev_end = (date.fromisoformat(d) for d in _bounds_prev())
    st.session_state.filter_date_start, st.session_state.filter_date_end = prev_start, prev_end
    try:
        yield
    finally:
        st.session_state.filter_date_start, st.session_state.filter_date_end = start, end


def f_usage_date_prev(col: str = "usage_date") -> str:
    s, e = _bounds_prev()
    return f"{col} >= '{s}' AND {col} <= '{e}'"


def f_event_date_prev(col: str = "event_dt") -> str:
    s, e = _bounds_prev()
    return f"{col} >= '{s}' AND {col} <= '{e}'"


def f_ts_date_prev(col: str) -> str:
    s, e = _bounds_prev()
    return (
        f"CAST({col} AS TIMESTAMP) >= TIMESTAMP '{s} 00:00:00' "
        f"AND CAST({col} AS TIMESTAMP) < TIMESTAMP '{e} 00:00:00' + INTERVAL '1' DAY"
    )


def _load_workspaces(run_query) -> None:
    if "_ws_data_loaded" in st.session_state:
        return
    df, err = run_query("""
        SELECT
            CAST(workspace_id AS STRING) AS workspace_id,
            workspace_name,
            UPPER(get(split(workspace_name, '-'), 5)) AS trigramme,
            UPPER(get(split(workspace_name, '-'), 6)) AS environnement
        FROM workspaces_latest
        WHERE status = 'RUNNING'
        ORDER BY workspace_name
    """)
    if err or df is None or df.empty:
        st.session_state["_ws_trigrammes"] = []
        st.session_state["_ws_environnements"] = []
        st.session_state["_ws_mapping"] = {}
        st.session_state["_ws_data_loaded"] = True
        return
    df["trigramme"] = df["trigramme"].fillna("").str.strip()
    df["environnement"] = df["environnement"].fillna("").str.strip()
    df = df[(df["trigramme"] != "") & (df["environnement"] != "")]
    st.session_state["_ws_trigrammes"] = sorted(df["trigramme"].unique().tolist())
    st.session_state["_ws_environnements"] = sorted(df["environnement"].unique().tolist())
    mapping: dict[tuple[str, str], list[str]] = {}
    for _, row in df.iterrows():
        key = (row["trigramme"], row["environnement"])
        mapping.setdefault(key, []).append(row["workspace_id"])
    st.session_state["_ws_mapping"] = mapping
    st.session_state["_ws_data_loaded"] = True


def render_workspace_filter(sidebar, run_query) -> None:
    from dashboards.chart_help import HELP, info_tip_html

    _load_workspaces(run_query)
    trigrammes = st.session_state.get("_ws_trigrammes", [])
    environnements = st.session_state.get("_ws_environnements", [])
    if not trigrammes and not environnements:
        return
    sidebar.markdown(
        f'<div class="filter-label-row"><p class="filter-label">Workspace</p>'
        f"{info_tip_html(HELP['filter_trigramme'])}</div>",
        unsafe_allow_html=True,
    )
    st.session_state["filter_trigramme"] = sidebar.multiselect(
        "Trigramme", trigrammes,
        default=st.session_state.get("filter_trigramme", []),
        key="filter_trigramme_input", placeholder="All", help=HELP["filter_trigramme"],
    )
    st.session_state["filter_environnement"] = sidebar.multiselect(
        "Environment", environnements,
        default=st.session_state.get("filter_environnement", []),
        key="filter_environnement_input", placeholder="All", help=HELP["filter_environment"],
    )


def _get_filtered_workspace_ids() -> list[str] | None:
    selected_tri = st.session_state.get("filter_trigramme", [])
    selected_env = st.session_state.get("filter_environnement", [])
    if not selected_tri and not selected_env:
        return None
    mapping = st.session_state.get("_ws_mapping", {})
    if not mapping:
        return None
    ids: set[str] = set()
    for (tri, env), ws_ids in mapping.items():
        if (not selected_tri or tri in selected_tri) and (not selected_env or env in selected_env):
            ids.update(ws_ids)
    return list(ids) if ids else ["__NONE__"]


def f_workspace(col: str = "workspace_id") -> str:
    ws_ids = _get_filtered_workspace_ids()
    if ws_ids is None:
        return "1=1"
    quoted = ", ".join(f"'{wid}'" for wid in ws_ids)
    return f"CAST({col} AS STRING) IN ({quoted})"


def workspace_filter_active() -> bool:
    return bool(st.session_state.get("filter_trigramme") or st.session_state.get("filter_environnement"))
