"""Security & governance dashboards."""

import plotly.express as px

from dashboards.chart_help import HELP
from dashboards.components import (
    bar_chart,
    data_table,
    line_chart,
    page_header,
    pie_chart,
    plotly_figure,
    show_error,
    COLORS,
    _coerce_label,
    _drop_blank_categories,
    _prepare_chart_df,
    _sanitize_chart_df,
)
from dashboards.catalog_config import fq
from dashboards.date_filter import f_event_date


def render_audit_overview(run_query) -> None:
    page_header("Audit summary", f"Event volume from {fq('access.audit')}")
    daily, err = run_query(f"""
        SELECT event_dt, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE {f_event_date()}
        GROUP BY 1 ORDER BY 1
    """)
    if show_error(err):
        return
    line_chart(daily, "event_dt", "events", "Daily audit volume", help=HELP["audit_daily"])


def render_permission_denied(run_query) -> None:
    page_header("Access denied", "403 events — permission issues")
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
    bar_chart(by_svc, "service_name", "denied", "403 by service", COLORS["danger"], help=HELP["denied_by_service"])
    data_table(df, height=400, title="Denied access events", help=HELP["tbl_denied_events"])


def render_unity_catalog(run_query) -> None:
    page_header("Unity Catalog", "UC actions: tables, grants, metastore")
    df, err = run_query(f"""
        SELECT action_name, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE service_name = 'unityCatalog'
          AND {f_event_date()}
        GROUP BY 1 ORDER BY events DESC
    """)
    if show_error(err):
        return
    pie_chart(df, "action_name", "events", "UC actions", help=HELP["uc_actions"])
    recent, _ = run_query(f"""
        SELECT user_email, action_name, event_ts, request_params
        FROM access_audit_parsed
        WHERE service_name = 'unityCatalog' AND {f_event_date()}
        ORDER BY event_ts DESC LIMIT 30
    """)
    data_table(recent, title="Recent UC events", help=HELP["tbl_uc_recent"])


def render_secrets_tokens(run_query) -> None:
    page_header("Secrets & tokens", "Secrets, PAT, and IAM events")
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
    bar_chart(counts, "action_name", "n", "Secrets / tokens / IAM", orientation="h", help=HELP["secrets_tokens"])
    data_table(df, title="Secrets and token events", help=HELP["tbl_secrets_events"])


def render_authentication(run_query) -> None:
    page_header("Sign-in", "Sessions, token login, source IP")
    df, err = run_query(f"""
        SELECT source_ip_address, COUNT(*) AS logins
        FROM access_audit_parsed
        WHERE action_name = 'tokenLogin'
          AND {f_event_date()}
        GROUP BY 1 ORDER BY logins DESC LIMIT 20
    """)
    if show_error(err):
        return
    bar_chart(df, "source_ip_address", "logins", "Token login by IP", help=HELP["login_by_ip"])
    agents, _ = run_query(f"""
        SELECT user_agent, COUNT(*) AS n
        FROM access_audit_parsed
        WHERE {f_event_date()}
        GROUP BY 1 ORDER BY n DESC LIMIT 10
    """)
    data_table(agents, title="User agents", help=HELP["tbl_user_agents"])


def render_top_actors(run_query) -> None:
    page_header("Top users", "Most active users in audit log")
    df, err = run_query(f"""
        SELECT user_email, COUNT(*) AS actions,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors
        FROM access_audit_parsed
        WHERE {f_event_date()} AND user_email IS NOT NULL
        GROUP BY 1 ORDER BY actions DESC LIMIT 20
    """)
    if show_error(err):
        return
    bar_chart(df, "user_email", "actions", "Actions by user", orientation="h", help=HELP["top_actors"])
    data_table(df, title="Top users detail", help=HELP["tbl_top_actors"])


def render_activity_heatmap(run_query) -> None:
    page_header("Activity heatmap", "Audit intensity by day and service")
    df, err = run_query(f"""
        SELECT event_dt, service_name, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE {f_event_date()}
        GROUP BY 1, 2
    """)
    if show_error(err) or df is None or df.empty:
        return
    clean = _prepare_chart_df(df, "service_name", "event_dt")
    pivot = clean.pivot_table(index="service_name", columns="event_dt", values="events", fill_value=0)
    pivot.index = pivot.index.map(_coerce_label)
    pivot.columns = [_coerce_label(c) for c in pivot.columns]
    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "Date", "y": "Service", "color": "Events"},
        template="plotly_white",
    )
    plotly_figure(fig, title="Audit heatmap", help=HELP["audit_heatmap"])
