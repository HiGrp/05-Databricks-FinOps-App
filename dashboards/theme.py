"""Design system & global CSS."""

from __future__ import annotations

THEME = {
    "brand": "#FF3621",
    "brand_soft": "#FFF1EE",
    "primary": "#4338CA",
    "primary_soft": "#EEF2FF",
    "sidebar_bg": "#FFFFFF",
    "sidebar_surface": "#F8FAFC",
    "sidebar_border": "#E2E8F0",
    "sidebar_text": "#0F172A",
    "sidebar_muted": "#64748B",
    "page_bg": "#F1F5F9",
    "card_bg": "#FFFFFF",
    "card_border": "#E2E8F0",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, system-ui, sans-serif", "color": "#475569", "size": 12},
        "title": {"font": {"size": 14, "color": "#0F172A"}, "x": 0, "xanchor": "left"},
        "margin": {"l": 36, "r": 20, "t": 40, "b": 36},
        "colorway": ["#4338CA", "#FF3621", "#0891B2", "#059669", "#7C3AED", "#D97706", "#DB2777"],
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        "xaxis": {"gridcolor": "#F1F5F9", "linecolor": "#E2E8F0", "zerolinecolor": "#F1F5F9"},
        "yaxis": {"gridcolor": "#F1F5F9", "linecolor": "#E2E8F0", "zerolinecolor": "#F1F5F9"},
        "hoverlabel": {"bgcolor": "#0F172A", "font": {"color": "#F8FAFC", "size": 12}},
    }
}


def inject_theme() -> None:
    import streamlit as st

    t = THEME
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }}

        #MainMenu, footer, header[data-testid="stHeader"] {{
            visibility: hidden;
            height: 0;
            min-height: 0;
        }}

        .stApp {{
            background: {t["page_bg"]};
        }}

        /* ── Sidebar layout ── */
        [data-testid="stSidebar"] {{
            background: {t["sidebar_bg"]} !important;
            border-right: 1px solid {t["sidebar_border"]};
            box-shadow: 1px 0 0 rgba(15, 23, 42, 0.04);
        }}
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 0.65rem !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            padding-top: 0.25rem !important;
        }}
        [data-testid="stSidebar"] [data-testid="block-container"] {{
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
        }}
        [data-testid="stSidebar"] hr {{
            border: none;
            border-top: 1px solid {t["sidebar_border"]};
            margin: 0.85rem 0 !important;
            opacity: 1;
        }}

        /* ── Sidebar brand ── */
        .sidebar-brand {{
            padding: 0.15rem 0 0.85rem 0;
            margin-bottom: 0.15rem;
            border-bottom: 1px solid {t["sidebar_border"]};
        }}
        .sidebar-brand-row {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }}
        .brand-logo {{
            flex-shrink: 0;
            width: 34px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(145deg, {t["brand"]}, #E02814);
            border-radius: 9px;
            font-weight: 700;
            font-size: 0.95rem;
            color: white !important;
            box-shadow: 0 2px 8px rgba(255, 54, 33, 0.28);
        }}
        .brand-title {{
            font-size: 0.98rem;
            font-weight: 700;
            color: {t["sidebar_text"]} !important;
            line-height: 1.15;
            letter-spacing: -0.02em;
        }}
        .brand-sub {{
            font-size: 0.72rem;
            color: {t["sidebar_muted"]} !important;
            margin-top: 1px;
            font-weight: 500;
        }}

        /* ── Sidebar filters ── */
        .filter-label, .nav-section-label {{
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: {t["sidebar_muted"]} !important;
            margin: 0 0 0.4rem 0;
            padding: 0;
        }}
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {t["sidebar_surface"]} !important;
            border-color: {t["sidebar_border"]} !important;
            border-radius: 10px !important;
            padding: 0.55rem 0.65rem !important;
            margin-bottom: 0.45rem;
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {{
            color: {t["sidebar_text"]} !important;
        }}
        [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{
            color: {t["sidebar_muted"]} !important;
        }}
        [data-testid="stSidebar"] input {{
            background: {t["sidebar_bg"]} !important;
            border: 1px solid {t["sidebar_border"]} !important;
            color: {t["sidebar_text"]} !important;
            border-radius: 8px !important;
            font-size: 0.82rem !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] {{
            background: {t["sidebar_bg"]} !important;
            border-color: {t["sidebar_border"]} !important;
            border-radius: 8px !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="tag"] {{
            background: {t["primary_soft"]} !important;
            color: {t["primary"]} !important;
        }}

        /* ── Sidebar navigation ── */
        [data-testid="stSidebar"] .stButton {{
            margin-bottom: 0.2rem;
        }}
        [data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            background: transparent !important;
            border: 1px solid transparent !important;
            color: {t["sidebar_muted"]} !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.84rem !important;
            padding: 0.5rem 0.65rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
            box-shadow: none !important;
            transition: all 0.15s ease;
        }}
        [data-testid="stSidebar"] .stButton > button:hover:not(:disabled) {{
            background: {t["sidebar_surface"]} !important;
            color: {t["sidebar_text"]} !important;
            border-color: {t["sidebar_border"]} !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: {t["sidebar_surface"]} !important;
            border: 1px solid {t["sidebar_border"]} !important;
            border-left: 3px solid {t["brand"]} !important;
            color: {t["sidebar_text"]} !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
        }}
        [data-testid="stSidebar"] .stButton > button:disabled {{
            opacity: 1 !important;
            cursor: default !important;
        }}

        /* ── Main layout ── */
        section.main [data-testid="block-container"] {{
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
            max-width: 1320px;
        }}
        section.main [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]} !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            padding: 0.85rem 1rem !important;
            overflow: visible !important;
        }}
        section.main hr {{
            border: none;
            border-top: 1px solid {t["card_border"]};
            margin: 1.25rem 0 !important;
        }}

        /* ── Page toolbar ── */
        .page-toolbar-wrap {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 12px;
            padding: 0.65rem 0.85rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }}
        .page-toolbar-meta {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.5rem 1rem;
            min-height: 2.4rem;
        }}
        .toolbar-period {{
            font-size: 0.88rem;
            font-weight: 600;
            color: {t["text"]};
        }}
        .toolbar-cache {{
            font-size: 0.75rem;
            color: {t["text_muted"]};
            background: {t["sidebar_surface"]};
            border: 1px solid {t["card_border"]};
            border-radius: 999px;
            padding: 0.15rem 0.55rem;
        }}
        section.main [data-testid="block-container"] > div > div:first-child [data-testid="column"]:last-child .stButton > button {{
            background: {t["card_bg"]} !important;
            border: 1px solid {t["card_border"]} !important;
            color: {t["text"]} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            min-height: 2.4rem !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
        }}
        section.main [data-testid="block-container"] > div > div:first-child [data-testid="column"]:last-child .stButton > button:hover {{
            border-color: {t["primary"]} !important;
            color: {t["primary"]} !important;
            background: {t["primary_soft"]} !important;
        }}

        /* ── Page hero ── */
        .page-hero {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 14px;
            padding: 1.1rem 1.25rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }}
        .page-hero-breadcrumb {{
            font-size: 0.75rem;
            font-weight: 500;
            color: {t["text_muted"]};
            margin-bottom: 0.35rem;
        }}
        .page-hero-breadcrumb span {{
            color: {t["primary"]};
            font-weight: 600;
        }}
        .page-hero-title {{
            font-size: 1.45rem;
            font-weight: 700;
            color: {t["text"]};
            margin: 0;
            letter-spacing: -0.025em;
            line-height: 1.2;
        }}
        .page-hero-sub {{
            font-size: 0.88rem;
            color: {t["text_muted"]};
            margin: 0.35rem 0 0 0;
            line-height: 1.45;
        }}
        .page-hero-badge {{
            display: inline-block;
            background: {t["brand_soft"]};
            color: {t["brand"]};
            font-size: 0.68rem;
            font-weight: 700;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            margin-left: 0.45rem;
            vertical-align: middle;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        /* ── Section headers ── */
        .section-head {{
            border-left: 3px solid {t["primary"]};
            padding: 0.15rem 0 0.15rem 0.75rem;
            margin: 0.15rem 0 0.65rem 0;
        }}
        .section-head-title {{
            font-size: 1rem;
            font-weight: 700;
            color: {t["text"]};
            margin: 0;
            letter-spacing: -0.01em;
        }}
        .section-head-hint {{
            font-size: 0.8rem;
            color: {t["text_muted"]};
            margin: 0.2rem 0 0 0;
        }}

        /* ── Metrics & charts ── */
        [data-testid="stMetric"] {{
            background: {t["sidebar_surface"]};
            border: 1px solid {t["card_border"]};
            border-radius: 10px;
            padding: 0.65rem 0.75rem !important;
        }}
        [data-testid="stMetricLabel"] {{
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            color: {t["text_muted"]} !important;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            color: {t["text"]} !important;
        }}

        .chart-title-row {{
            display: flex;
            align-items: center;
            gap: 0.45rem;
            margin-bottom: 0.25rem;
        }}
        .chart-title-text {{
            color: {t["text"]};
            font-size: 0.9rem;
            font-weight: 600;
        }}
        .chart-info-tip {{
            position: relative;
            display: inline-flex;
            align-items: center;
            cursor: help;
            outline: none;
        }}
        .chart-info-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.1rem;
            height: 1.1rem;
            border-radius: 50%;
            background: {t["sidebar_surface"]};
            border: 1px solid {t["card_border"]};
            color: {t["text_muted"]};
            font-size: 0.68rem;
            font-weight: 700;
        }}
        .chart-info-tip:hover .chart-info-icon,
        .chart-info-tip:focus .chart-info-icon {{
            background: {t["primary"]};
            border-color: {t["primary"]};
            color: white;
        }}
        .chart-info-popup {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            left: 50%;
            bottom: calc(100% + 8px);
            transform: translateX(-50%);
            width: min(260px, 70vw);
            padding: 0.5rem 0.7rem;
            background: {t["text"]};
            color: #F8FAFC;
            font-size: 0.76rem;
            line-height: 1.4;
            border-radius: 8px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.15);
            z-index: 1000;
            pointer-events: none;
            transition: opacity 0.15s ease;
        }}
        .chart-info-popup::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 5px solid transparent;
            border-top-color: {t["text"]};
        }}
        .chart-info-tip:hover .chart-info-popup,
        .chart-info-tip:focus .chart-info-popup {{
            visibility: visible;
            opacity: 1;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 10px;
            border: 1px solid {t["card_border"]};
        }}

        @media (max-width: 768px) {{
            section.main [data-testid="block-container"] {{
                padding-top: 0.75rem !important;
            }}
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {{
                flex-wrap: wrap !important;
                gap: 0.45rem !important;
            }}
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div[data-testid="column"] {{
                flex: 1 1 45% !important;
                min-width: 45% !important;
            }}
        }}
        @media (max-width: 480px) {{
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div[data-testid="column"] {{
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
