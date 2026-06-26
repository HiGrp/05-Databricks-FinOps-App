"""Dashboards sécurité & gouvernance."""

import streamlit as st
import plotly.express as px

from dashboards.components import (
    bar_chart,
    data_table,
    line_chart,
    metrics_row,
    page_header,
    pie_chart,
    plotly_figure,
    show_error,
    COLORS,
    _coerce_label,
    _drop_blank_categories,
    _sanitize_chart_df,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_event_date, f_workspace, period_label


def render_audit_overview(run_query) -> None:
    page_header("Audit Overview", f"Volume et répartition des événements {fq('access.audit')}")
    df, err = run_query(f"""
        SELECT COUNT(*) AS total,
               COUNT(DISTINCT user_email) AS users,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors
        FROM access_audit_parsed
        WHERE {f_event_date()}
    """)
    if show_error(err) or df is None or df.empty:
        return
    r = df.iloc[0]
    metrics_row([
        (f"Events ({period_label()})", f"{int(r['total']):,}", None),
        ("Utilisateurs uniques", str(int(r["users"])), None),
        ("Events erreur (4xx/5xx)", str(int(r["errors"])), None),
    ])
    daily, _ = run_query(f"""
        SELECT event_dt, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE {f_event_date()}
        GROUP BY 1 ORDER BY 1
    """)
    line_chart(daily, "event_dt", "events", "Volume audit journalier")


def render_permission_denied(run_query) -> None:
    page_header("Accès refusés", "Événements 403 — risque gouvernance")
    df, err = run_query(f"""
        SELECT user_email, service_name, action_name, event_ts, error_message
        FROM access_audit_parsed
        WHERE status_code = 403
          AND {f_event_date()}
        ORDER BY event_ts DESC LIMIT 50
    """)
    if show_error(err):
        return
    by_svc, _ = run_query(f"""
        SELECT service_name, COUNT(*) AS denied
        FROM access_audit_parsed
        WHERE status_code = 403 AND {f_event_date()}
        GROUP BY 1 ORDER BY denied DESC
    """)
    bar_chart(by_svc, "service_name", "denied", "403 par service", COLORS["danger"])
    data_table(df, height=400)


def render_unity_catalog(run_query) -> None:
    page_header("Unity Catalog", "Actions UC — tables, grants, metastore")
    df, err = run_query(f"""
        SELECT action_name, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE service_name = 'unityCatalog'
          AND {f_event_date()}
        GROUP BY 1 ORDER BY events DESC
    """)
    if show_error(err):
        return
    pie_chart(df, "action_name", "events", "Actions Unity Catalog")
    recent, _ = run_query(f"""
        SELECT user_email, action_name, event_ts, request_params
        FROM access_audit_parsed
        WHERE service_name = 'unityCatalog' AND {f_event_date()}
        ORDER BY event_ts DESC LIMIT 30
    """)
    data_table(recent)


def render_secrets_tokens(run_query) -> None:
    page_header("Secrets & tokens", "Accès secrets, tokenLogin, IAM")
    df, err = run_query(f"""
        SELECT service_name, action_name, user_email, event_ts
        FROM access_audit_parsed
        WHERE service_name IN ('secrets', 'accounts', 'iam')
          AND {f_event_date()}
        ORDER BY event_ts DESC LIMIT 40
    """)
    if show_error(err):
        return
    counts, _ = run_query(f"""
        SELECT service_name, action_name, COUNT(*) AS n
        FROM access_audit_parsed
        WHERE service_name IN ('secrets', 'accounts', 'iam')
          AND {f_event_date()}
        GROUP BY 1, 2 ORDER BY n DESC
    """)
    bar_chart(counts, "action_name", "n", "Secrets / tokens / IAM", orientation="h")
    data_table(df)


def render_authentication(run_query) -> None:
    page_header("Authentification", "Sessions, tokenLogin, origine IP")
    df, err = run_query(f"""
        SELECT source_ip_address, COUNT(*) AS logins
        FROM access_audit_parsed
        WHERE action_name = 'tokenLogin'
          AND {f_event_date()}
        GROUP BY 1 ORDER BY logins DESC LIMIT 20
    """)
    if show_error(err):
        return
    bar_chart(df, "source_ip_address", "logins", "tokenLogin par IP")
    agents, _ = run_query(f"""
        SELECT user_agent, COUNT(*) AS n
        FROM access_audit_parsed
        WHERE {f_event_date()}
        GROUP BY 1 ORDER BY n DESC LIMIT 10
    """)
    data_table(agents)


def render_top_actors(run_query) -> None:
    page_header("Top acteurs", "Utilisateurs les plus actifs (audit)")
    df, err = run_query(f"""
        SELECT user_email, COUNT(*) AS actions,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors
        FROM access_audit_parsed
        WHERE {f_event_date()} AND user_email IS NOT NULL
        GROUP BY 1 ORDER BY actions DESC LIMIT 20
    """)
    if show_error(err):
        return
    bar_chart(df, "user_email", "actions", "Actions par utilisateur", orientation="h")
    data_table(df)


def render_activity_heatmap(run_query) -> None:
    page_header("Heatmap activité", "Intensité audit par jour et service")
    df, err = run_query(f"""
        SELECT event_dt, service_name, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE {f_event_date()}
        GROUP BY 1, 2
    """)
    if show_error(err) or df is None or df.empty:
        return
    clean = _drop_blank_categories(_sanitize_chart_df(df, "service_name"), "service_name")
    pivot = clean.pivot_table(index="service_name", columns="event_dt", values="events", fill_value=0)
    pivot.index = pivot.index.map(_coerce_label)
    pivot.columns = [_coerce_label(c) for c in pivot.columns]
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="Blues", template="plotly_white")
    plotly_figure(fig, title=f"Heatmap audit (service × date) — {period_label()}")
