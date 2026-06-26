"""Filtres globaux : période (Du / Au), trigramme, environnement."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st


# ---------------------------------------------------------------------------
# Période
# ---------------------------------------------------------------------------

def init_dates() -> None:
    yesterday = date.today() - timedelta(days=1)
    if "filter_date_start" not in st.session_state:
        st.session_state.filter_date_start = yesterday
    if "filter_date_end" not in st.session_state:
        st.session_state.filter_date_end = yesterday


def render_date_filter(sidebar) -> None:
    init_dates()
    sidebar.markdown("**Période**")
    c1, c2 = sidebar.columns(2)
    with c1:
        st.session_state.filter_date_start = c1.date_input(
            "Du",
            value=st.session_state.filter_date_start,
            key="filter_date_start_input",
            label_visibility="collapsed",
        )
    with c2:
        st.session_state.filter_date_end = c2.date_input(
            "Au",
            value=st.session_state.filter_date_end,
            key="filter_date_end_input",
            label_visibility="collapsed",
        )
    if st.session_state.filter_date_start > st.session_state.filter_date_end:
        st.session_state.filter_date_end = st.session_state.filter_date_start


def _bounds() -> tuple[str, str]:
    init_dates()
    return (
        str(st.session_state.filter_date_start),
        str(st.session_state.filter_date_end),
    )


def f_usage_date(col: str = "usage_date") -> str:
    s, e = _bounds()
    return f"{col} >= '{s}' AND {col} <= '{e}'"


def f_event_date(col: str = "event_dt") -> str:
    s, e = _bounds()
    return f"{col} >= '{s}' AND {col} <= '{e}'"


def period_label() -> str:
    s, e = _bounds()
    return f"{s} → {e}"


def f_ts_date(col: str) -> str:
    s, e = _bounds()
    return (
        f"CAST({col} AS TIMESTAMP) >= TIMESTAMP '{s} 00:00:00' "
        f"AND CAST({col} AS TIMESTAMP) < TIMESTAMP '{e} 00:00:00' + INTERVAL '1' DAY"
    )


# ---------------------------------------------------------------------------
# Filtres Trigramme / Environnement (basés sur workspaces_latest)
# ---------------------------------------------------------------------------

def _load_workspaces(run_query) -> None:
    """Charge la liste des workspaces une seule fois en session."""
    if "_ws_data_loaded" in st.session_state:
        return
    df, err = run_query("""
        SELECT
            CAST(workspace_id AS STRING) AS workspace_id,
            workspace_name,
            UPPER(split(workspace_name, '-')[5]) AS trigramme,
            UPPER(split(workspace_name, '-')[6]) AS environnement
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

    # Nettoyage
    df["trigramme"] = df["trigramme"].fillna("").str.strip()
    df["environnement"] = df["environnement"].fillna("").str.strip()
    df = df[(df["trigramme"] != "") & (df["environnement"] != "")]

    st.session_state["_ws_trigrammes"] = sorted(df["trigramme"].unique().tolist())
    st.session_state["_ws_environnements"] = sorted(df["environnement"].unique().tolist())
    # Mapping : {(trigramme, env) -> [workspace_id, ...]}
    mapping: dict[tuple[str, str], list[str]] = {}
    for _, row in df.iterrows():
        key = (row["trigramme"], row["environnement"])
        mapping.setdefault(key, []).append(row["workspace_id"])
    st.session_state["_ws_mapping"] = mapping
    st.session_state["_ws_data_loaded"] = True


def render_workspace_filter(sidebar, run_query) -> None:
    """Affiche les multiselects Trigramme et Environnement dans la sidebar."""
    _load_workspaces(run_query)

    trigrammes = st.session_state.get("_ws_trigrammes", [])
    environnements = st.session_state.get("_ws_environnements", [])

    if not trigrammes and not environnements:
        return

    sidebar.markdown("**Filtres workspace**")

    selected_tri = sidebar.multiselect(
        "Trigramme",
        options=trigrammes,
        default=st.session_state.get("filter_trigramme", []),
        key="filter_trigramme_input",
        placeholder="Tous",
    )
    st.session_state["filter_trigramme"] = selected_tri

    selected_env = sidebar.multiselect(
        "Environnement",
        options=environnements,
        default=st.session_state.get("filter_environnement", []),
        key="filter_environnement_input",
        placeholder="Tous",
    )
    st.session_state["filter_environnement"] = selected_env


def _get_filtered_workspace_ids() -> list[str] | None:
    """Retourne la liste des workspace_ids filtrés, ou None si aucun filtre actif."""
    selected_tri = st.session_state.get("filter_trigramme", [])
    selected_env = st.session_state.get("filter_environnement", [])

    if not selected_tri and not selected_env:
        return None  # Pas de filtre

    mapping = st.session_state.get("_ws_mapping", {})
    if not mapping:
        return None

    ids: set[str] = set()
    for (tri, env), ws_ids in mapping.items():
        tri_ok = (not selected_tri) or (tri in selected_tri)
        env_ok = (not selected_env) or (env in selected_env)
        if tri_ok and env_ok:
            ids.update(ws_ids)

    return list(ids) if ids else ["__NONE__"]  # Force zéro résultat


def f_workspace(col: str = "workspace_id") -> str:
    """Retourne une clause SQL WHERE pour filtrer par workspace.

    Retourne '1=1' si aucun filtre n'est actif.
    """
    ws_ids = _get_filtered_workspace_ids()
    if ws_ids is None:
        return "1=1"
    quoted = ", ".join(f"'{wid}'" for wid in ws_ids)
    return f"CAST({col} AS STRING) IN ({quoted})"


def workspace_filter_active() -> bool:
    """True si au moins un filtre trigramme/environnement est actif."""
    return bool(
        st.session_state.get("filter_trigramme")
        or st.session_state.get("filter_environnement")
    )
