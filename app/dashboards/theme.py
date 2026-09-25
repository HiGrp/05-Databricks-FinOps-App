"""Design system — minimal CSS, Streamlit-native layout."""

from __future__ import annotations

THEME = {
    "brand": "#E11D2E",
    "brand_soft": "#FEF2F2",
    "accent": "#0F6E8C",
    "bg": "#F4F5F7",
    "surface": "#FFFFFF",
    "border": "#E6E8EC",
    "text": "#111827",
    "muted": "#6B7280",
    "success": "#047857",
    "warning": "#B45309",
    "danger": "#B91C1C",
    "ink": "#111827",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, system-ui, sans-serif", "color": "#5E6C84", "size": 12},
        "title": {"font": {"size": 13, "color": "#1B1F23"}, "x": 0, "xanchor": "left"},
        "margin": {"l": 40, "r": 16, "t": 8, "b": 36},
        "colorway": ["#0B6E99", "#FF3621", "#00875A", "#6554C0", "#FF8B00", "#00B8D9", "#DE350B"],
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        "xaxis": {"gridcolor": "#EBECF0", "linecolor": "#DDE1E6", "zerolinecolor": "#EBECF0"},
        "yaxis": {"gridcolor": "#EBECF0", "linecolor": "#DDE1E6", "zerolinecolor": "#EBECF0"},
        "hoverlabel": {"bgcolor": "#1B1F23", "font": {"color": "#FFFFFF", "size": 12}},
    }
}


def inject_theme() -> None:
    import streamlit as st

    t = THEME
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; color: {t["text"]}; }}

        #MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"] {{
            display: none !important; height: 0 !important; visibility: hidden;
        }}
        .stApp, [data-testid="stAppViewContainer"], section.stAppViewMain {{
            background: {t["bg"]} !important;
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background: {t["surface"]} !important;
            border-right: 1px solid {t["border"]};
        }}
        [data-testid="stSidebarHeader"], [data-testid="stSidebar"] [data-testid="stLogoSpacer"] {{
            display: none !important; height: 0 !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSidebarContent"],
        [data-testid="stSidebar"] [data-testid="block-container"] {{
            padding: 1rem 0.85rem 1.25rem 0.85rem !important;
        }}
        .sidebar-brand {{ margin-bottom: 0.15rem; }}
        .sidebar-brand-row {{ display: flex; align-items: center; gap: 0.55rem; }}
        .brand-logo {{
            width: 28px; height: 28px; border-radius: 7px;
            background: {t["brand"]}; color: #fff !important;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 0.75rem;
        }}
        .brand-title {{ font-size: 0.92rem; font-weight: 600; color: {t["text"]} !important; letter-spacing: -0.02em; }}
        .sidebar-divider {{ height: 1px; background: {t["border"]}; margin: 0.85rem 0; }}
        [data-testid="stSidebar"] [data-testid="stTextInput"] label p,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label p {{
            font-size: 0.68rem !important; font-weight: 600 !important;
            letter-spacing: 0.04em; text-transform: uppercase; color: {t["muted"]} !important;
        }}
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background: {t["bg"]} !important;
            border-color: {t["border"]} !important;
            border-radius: 8px !important;
        }}
        [data-testid="stSidebar"] .stButton {{ margin: 0 0 0.1rem 0; }}
        [data-testid="stSidebar"] .stButton > button {{
            width: 100%; background: transparent !important; border: none !important;
            box-shadow: none !important; color: {t["muted"]} !important;
            border-radius: 8px !important; font-weight: 500 !important;
            font-size: 0.875rem !important; padding: 0.42rem 0.55rem !important;
            text-align: left !important; justify-content: flex-start !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover:not(:disabled) {{
            background: {t["bg"]} !important; color: {t["text"]} !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: {t["bg"]} !important; color: {t["text"]} !important; font-weight: 600 !important;
        }}
        [data-testid="stSidebar"] .stButton > button:disabled {{ opacity: 1 !important; cursor: default !important; }}
        .sidebar-foot {{
            margin-top: 0.85rem; padding-top: 0.75rem; border-top: 1px solid {t["border"]};
            font-size: 0.72rem; color: {t["muted"]} !important; line-height: 1.55;
        }}
        .sidebar-foot a {{ color: {t["text"]} !important; text-decoration: none; font-weight: 600; }}

        /* ── Page ── */
        [data-testid="stMainBlockContainer"],
        section.main [data-testid="block-container"],
        section.main .block-container {{
            padding: 1.15rem 1.35rem 2.25rem 1.35rem !important;
            max-width: 100% !important;
        }}
        h1.page-title {{
            font-size: 1.5rem; font-weight: 700; color: {t["text"]};
            margin: 0 !important; letter-spacing: -0.03em; line-height: 1.2;
            display: flex; align-items: center; gap: 0.45rem;
        }}
        .page-icon {{ font-size: 1.2rem; }}
        p.lead {{
            font-size: 0.95rem; color: {t["muted"]}; margin: 0.4rem 0 1rem 0; line-height: 1.5;
        }}
        div[data-testid="stHorizontalBlock"]:has(h1.page-title) {{
            align-items: center !important;
            flex-wrap: nowrap !important;
            margin: 0 0 1.1rem 0 !important;
            padding-bottom: 0.85rem;
            border-bottom: 1px solid {t["border"]};
        }}
        div[data-testid="stHorizontalBlock"]:has(h1.page-title) > div[data-testid="column"]:last-child {{
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 7.5rem !important;
        }}
        .st-key-page_refresh_data,
        .st-key-page_refresh_data .stButton {{
            width: auto !important;
        }}
        .st-key-page_refresh_data button,
        .st-key-page_refresh_data [data-testid="baseButton-secondary"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {t["muted"]} !important;
            font-weight: 500 !important;
            font-size: 0.82rem !important;
            padding: 0.2rem 0 !important;
            min-height: 0 !important;
            width: auto !important;
            white-space: nowrap !important;
        }}
        .st-key-page_refresh_data button:hover {{
            color: {t["text"]} !important;
            background: transparent !important;
            border: none !important;
        }}
        .st-key-connect_gate_btn button {{
            margin-top: 0.25rem;
        }}

        /* ── Type + sections ── */
        section.main h3 {{
            font-size: 1rem !important; font-weight: 600 !important;
            letter-spacing: -0.02em; color: {t["text"]} !important;
            margin-top: 0 !important;
        }}
        .section-title {{
            font-size: 1rem; font-weight: 600; color: {t["text"]};
            margin: 1.75rem 0 0.35rem 0; padding: 0;
            border: none;
            display: flex; align-items: center; gap: 0.4rem;
            letter-spacing: -0.02em;
        }}
        .section-title:first-of-type {{ margin-top: 0.25rem; }}
        .section-desc {{
            font-size: 0.84rem; color: {t["muted"]}; margin: 0 0 0.75rem 0; line-height: 1.5;
        }}
        p.block-label {{
            font-size: 0.95rem !important; font-weight: 600 !important;
            color: {t["text"]} !important; margin: 1.35rem 0 0.55rem 0 !important;
        }}

        /* ── Cards: metrics, charts, setup steps ── */
        [data-testid="stMetric"] {{
            background: {t["surface"]};
            border: 1px solid {t["border"]};
            border-radius: 12px;
            padding: 0.85rem 1rem 0.7rem 1rem;
        }}
        [data-testid="stMetricLabel"] {{
            font-size: 0.72rem !important; font-weight: 600 !important;
            color: {t["muted"]} !important; letter-spacing: 0.01em;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.45rem !important; font-weight: 700 !important;
            color: {t["text"]} !important; letter-spacing: -0.03em;
        }}
        section.main [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {t["surface"]} !important;
            border: 1px solid {t["border"]} !important;
            border-radius: 12px !important;
            padding: 1rem 1.1rem !important;
            box-shadow: none !important;
        }}
        .chart-title-text {{ font-size: 0.9rem; font-weight: 600; color: {t["text"]}; letter-spacing: -0.01em; }}
        .chart-caption {{
            font-size: 0.82rem !important; color: {t["muted"]} !important;
            margin: 0.2rem 0 0.65rem 0 !important; line-height: 1.45 !important;
        }}

        /* ── Controls ── */
        section.main .stButton > button[kind="primary"] {{
            background: {t["ink"]} !important;
            color: #fff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.45rem 0.95rem !important;
            box-shadow: none !important;
        }}
        section.main .stButton > button[kind="primary"]:hover {{
            background: #1F2937 !important;
            color: #fff !important;
            border: none !important;
        }}
        section.main .stButton > button[kind="secondary"] {{
            background: {t["surface"]} !important;
            color: {t["text"]} !important;
            border: 1px solid {t["border"]} !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }}
        [data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
        }}
        section.main [data-baseweb="input"] > div,
        section.main [data-baseweb="select"] > div {{
            border-radius: 8px !important;
            border-color: {t["border"]} !important;
            background: {t["bg"]} !important;
        }}
        [data-testid="stAlert"] {{
            border-radius: 10px !important;
            border: none !important;
        }}
        section.main [data-testid="stCode"],
        section.main pre {{
            border-radius: 10px !important;
        }}

        /* ── To-do ── */
        p.todo-title {{
            font-size: 0.78rem !important; font-weight: 600 !important;
            color: {t["muted"]} !important; letter-spacing: 0.04em;
            text-transform: uppercase; margin: 0.4rem 0 0.45rem 0 !important;
        }}
        .todo-item {{
            background: {t["bg"]};
            border-radius: 8px;
            border-left: 3px solid {t["warning"]};
            padding: 0.55rem 0.75rem; margin: 0.4rem 0;
        }}
        .todo-item.sev-high {{ border-left-color: {t["danger"]}; }}
        .todo-line {{ font-size: 0.875rem; color: {t["text"]}; line-height: 1.45; }}
        .todo-meta {{ font-size: 0.75rem; color: {t["muted"]}; margin-top: 0.15rem; }}
        p.todo-sub {{
            font-size: 0.7rem !important; font-weight: 600 !important;
            text-transform: uppercase; letter-spacing: 0.04em;
            color: {t["muted"]} !important; margin: 0.7rem 0 0.2rem 0 !important;
        }}
        .todo-check {{ font-size: 0.84rem; color: {t["text"]}; line-height: 1.45; }}
        .home-summary {{
            font-size: 0.95rem; color: {t["text"]}; line-height: 1.55; margin: 0 0 1rem 0;
        }}
        .home-summary .muted {{ color: {t["muted"]}; }}

        .section-loading-wrap {{ padding: 0.75rem 0; }}
        .section-spinner {{
            width: 1.1rem; height: 1.1rem;
            border: 2px solid {t["border"]}; border-top-color: {t["text"]};
            border-radius: 50%; animation: spin 0.6s linear infinite;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

        @media (max-width: 768px) {{
            [data-testid="stMainBlockContainer"],
            section.main .block-container {{
                padding: 0.85rem 0.85rem 1.5rem 0.85rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
