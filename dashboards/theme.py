"""Design system & CSS global."""

from __future__ import annotations

# Palette inspirée Databricks / enterprise dark sidebar
THEME = {
    "brand": "#FF3621",
    "brand_dark": "#E02814",
    "primary": "#2563EB",
    "sidebar_bg": "#0B1120",
    "sidebar_surface": "#151D2E",
    "sidebar_border": "#1E293B",
    "sidebar_text": "#E2E8F0",
    "sidebar_muted": "#94A3B8",
    "page_bg": "#F4F6FA",
    "card_bg": "#FFFFFF",
    "card_border": "#E8ECF4",
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
        "font": {"family": "Inter, system-ui, sans-serif", "color": "#334155", "size": 12},
        "title": {"font": {"size": 15, "color": "#0F172A"}, "x": 0, "xanchor": "left"},
        "margin": {"l": 40, "r": 24, "t": 48, "b": 40},
        "colorway": ["#2563EB", "#FF3621", "#059669", "#7C3AED", "#D97706", "#0891B2", "#DB2777"],
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        "xaxis": {"gridcolor": "#EEF2F7", "linecolor": "#CBD5E1", "zerolinecolor": "#EEF2F7"},
        "yaxis": {"gridcolor": "#EEF2F7", "linecolor": "#CBD5E1", "zerolinecolor": "#EEF2F7"},
        "hoverlabel": {"bgcolor": "#0F172A", "font": {"color": "#F8FAFC"}},
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

        .stApp {{
            background: {t["page_bg"]};
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {t["sidebar_bg"]} 0%, #0F172A 100%);
            border-right: 1px solid {t["sidebar_border"]};
        }}
        [data-testid="stSidebar"] * {{
            color: {t["sidebar_text"]} !important;
        }}
        [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{
            color: {t["sidebar_muted"]} !important;
        }}
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {{
            background: {t["sidebar_surface"]} !important;
            border: 1px solid {t["sidebar_border"]} !important;
            color: {t["sidebar_text"]} !important;
            border-radius: 10px !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background: {t["sidebar_surface"]} !important;
            border-color: {t["sidebar_border"]} !important;
            border-radius: 10px !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: {t["sidebar_border"]} !important;
            opacity: 0.6;
        }}
        [data-testid="stSidebar"] .stRadio label {{
            background: transparent;
            padding: 0.45rem 0.65rem;
            border-radius: 8px;
            margin: 2px 0;
            transition: background 0.15s;
        }}
        [data-testid="stSidebar"] .stRadio label:hover {{
            background: {t["sidebar_surface"]};
        }}
        [data-testid="stSidebar"] .stRadio > div {{
            gap: 0.25rem;
        }}
        [data-testid="stSidebar"] .stButton > button {{
            background: {t["sidebar_surface"]} !important;
            border: 1px solid {t["sidebar_border"]} !important;
            color: {t["sidebar_text"]} !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.82rem !important;
            padding: 0.45rem 0.75rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover:not(:disabled) {{
            border-color: {t["brand"]} !important;
            background: #1a2332 !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {t["brand"]}, {t["brand_dark"]}) !important;
            border: none !important;
            color: white !important;
            font-weight: 600 !important;
        }}
        [data-testid="stSidebar"] .stButton > button:disabled {{
            opacity: 1 !important;
            cursor: default !important;
        }}

        /* ── Main area ── */
        .block-container {{
            padding-top: 2.5rem;
            max-width: 1400px;
        }}

        /* En-têtes de page — évite le texte coupé en haut */
        section.main [data-testid="stVerticalBlockBorderWrapper"] {{
            padding-top: 1rem !important;
            padding-bottom: 0.75rem !important;
            overflow: visible !important;
        }}
        section.main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"]:first-child p {{
            margin-top: 0.25rem !important;
            margin-bottom: 0.5rem !important;
            line-height: 1.5 !important;
            color: {t["text_muted"]};
            font-size: 0.9rem;
        }}
        section.main [data-testid="stCaptionContainer"] {{
            padding-top: 0.15rem;
            overflow: visible !important;
        }}

        /* ── Brand header sidebar ── */
        .brand-block {{
            padding: 0.25rem 0 1rem 0;
        }}
        .brand-logo {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px; height: 36px;
            background: linear-gradient(135deg, {t["brand"]}, {t["brand_dark"]});
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.1rem;
            color: white !important;
            margin-right: 10px;
            box-shadow: 0 4px 14px rgba(255,54,33,0.35);
        }}
        .brand-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #F8FAFC !important;
            line-height: 1.2;
        }}
        .brand-sub {{
            font-size: 0.72rem;
            color: {t["sidebar_muted"]} !important;
            margin-top: 2px;
        }}

        /* ── Page header ── */
        .page-hero {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 16px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        }}
        .breadcrumb {{
            font-size: 0.78rem;
            color: {t["text_muted"]};
            margin-bottom: 0.5rem;
        }}
        .breadcrumb span {{ color: {t["primary"]}; font-weight: 500; }}
        .page-title {{
            font-size: 1.65rem;
            font-weight: 700;
            color: {t["text"]};
            margin: 0;
            letter-spacing: -0.02em;
        }}
        .page-subtitle {{
            font-size: 0.92rem;
            color: {t["text_muted"]};
            margin: 0.35rem 0 0 0;
        }}
        .page-badge {{
            display: inline-block;
            background: #EEF2FF;
            color: #4338CA;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin-left: 0.5rem;
            vertical-align: middle;
        }}

        /* ── KPI cards ── */
        .kpi-grid {{
            display: grid;
            gap: 0.85rem;
            margin-bottom: 1rem;
        }}
        .kpi-card {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 1px 2px rgba(15,23,42,0.04);
            height: 100%;
        }}
        .kpi-card:hover {{
            box-shadow: 0 4px 12px rgba(15,23,42,0.06);
            border-color: #D5DCE8;
        }}
        .kpi-icon {{
            font-size: 1.25rem;
            margin-bottom: 0.35rem;
        }}
        .kpi-label {{
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: {t["text_muted"]};
        }}
        .kpi-value {{
            font-size: 1.55rem;
            font-weight: 700;
            color: {t["text"]};
            margin: 0.2rem 0;
            letter-spacing: -0.02em;
        }}
        .kpi-delta {{
            font-size: 0.78rem;
            font-weight: 500;
        }}
        .kpi-delta.up {{ color: {t["danger"]}; }}
        .kpi-delta.down {{ color: {t["success"]}; }}
        .kpi-delta.neutral {{ color: {t["text_muted"]}; }}

        /* ── Chart cards ── */
        .section-card {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 16px;
            padding: 0.25rem 0.5rem 0.5rem 0.5rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        }}
        .section-title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: {t["text"]};
            padding: 0.85rem 1rem 0.25rem 1rem;
        }}

        /* ── Status pill sidebar ── */
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: {t["sidebar_surface"]};
            border: 1px solid {t["sidebar_border"]};
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .status-dot {{
            width: 7px; height: 7px;
            border-radius: 50%;
            background: #34D399;
            box-shadow: 0 0 6px rgba(52,211,153,0.6);
        }}
        .status-dot.remote {{ background: #60A5FA; box-shadow: 0 0 6px rgba(96,165,250,0.6); }}

        .nav-section-label {{
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {t["sidebar_muted"]} !important;
            margin: 0.75rem 0 0.35rem 0;
        }}

        /* Streamlit metric override in main */
        [data-testid="stMetricValue"] {{
            font-size: 1.4rem !important;
            font-weight: 700 !important;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 12px;
        }}

        /* Chart title + hover help */
        .chart-title-row {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.35rem;
        }}
        .chart-title-text {{
            color: {t["text"]};
            font-size: 0.95rem;
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
            width: 1.15rem;
            height: 1.15rem;
            border-radius: 50%;
            background: {t["card_border"]};
            color: {t["text_muted"]};
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1;
        }}
        .chart-info-tip:hover .chart-info-icon,
        .chart-info-tip:focus .chart-info-icon {{
            background: {t["primary"]};
            color: white;
        }}
        .chart-info-popup {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            left: 50%;
            bottom: calc(100% + 8px);
            transform: translateX(-50%);
            width: min(280px, 70vw);
            padding: 0.55rem 0.75rem;
            background: {t["text"]};
            color: #F8FAFC;
            font-size: 0.78rem;
            font-weight: 400;
            line-height: 1.45;
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(15,23,42,0.18);
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
            border: 6px solid transparent;
            border-top-color: {t["text"]};
        }}
        .chart-info-tip:hover .chart-info-popup,
        .chart-info-tip:focus .chart-info-popup {{
            visibility: visible;
            opacity: 1;
        }}

        /* Mobile — stack KPI metrics */
        @media (max-width: 768px) {{
            [data-testid="stSidebar"] {{
                min-width: 100% !important;
            }}
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {{
                flex-wrap: wrap !important;
                gap: 0.5rem !important;
            }}
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div[data-testid="column"] {{
                flex: 1 1 45% !important;
                min-width: 45% !important;
                width: 45% !important;
            }}
            [data-testid="stMetricValue"] {{
                font-size: 1.15rem !important;
            }}
            .chart-info-popup {{
                width: min(240px, 85vw);
                left: 0;
                transform: none;
            }}
        }}
        @media (max-width: 480px) {{
            div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div[data-testid="column"] {{
                flex: 1 1 100% !important;
                min-width: 100% !important;
                width: 100% !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
