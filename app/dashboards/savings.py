"""Savings engine - waste rules priced in money, from system tables.

Each rule returns the cost in scope and an estimated saving. Saving factors are
deliberately conservative and shown to the user next to each estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from dashboards.date_filter import f_ts_date, f_usage_date, period_days
from dashboards.pricing import cost

_WEEKEND = "(CAST(strftime('%w', {col}) AS INTEGER) + 1) IN (1, 7)"


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    area: str
    effort: str
    factor: float
    assumption: str
    fix: str
    summary_sql: Callable[[], str]
    detail_sql: Callable[[], str]


def _jobs_on_all_purpose_summary() -> str:
    return f"""
        SELECT SUM({cost()}) AS scope_cost, COUNT(DISTINCT job_id) AS items
        FROM billing_cost
        WHERE billing_origin_product = 'ALL_PURPOSE' AND job_id IS NOT NULL AND {f_usage_date()}
    """


def _jobs_on_all_purpose_detail() -> str:
    return f"""
        SELECT job_name, cluster_name, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE billing_origin_product = 'ALL_PURPOSE' AND job_id IS NOT NULL AND {f_usage_date()}
        GROUP BY 1, 2 ORDER BY cost DESC LIMIT 100
    """


def _weekend_interactive_summary() -> str:
    return f"""
        SELECT SUM({cost()}) AS scope_cost, COUNT(DISTINCT cluster_id) AS items
        FROM billing_cost
        WHERE billing_origin_product = 'ALL_PURPOSE' AND job_id IS NULL
          AND {_WEEKEND.format(col='usage_date')} AND {f_usage_date()}
    """


def _weekend_interactive_detail() -> str:
    return f"""
        SELECT cluster_name, run_as AS owner, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE billing_origin_product = 'ALL_PURPOSE' AND job_id IS NULL
          AND {_WEEKEND.format(col='usage_date')} AND {f_usage_date()}
        GROUP BY 1, 2 ORDER BY cost DESC LIMIT 100
    """


_NO_AUTOSTOP = (
    "(k.auto_termination_minutes IS NULL OR k.auto_termination_minutes = 0 "
    "OR k.auto_termination_minutes > 60)"
)


def _no_autostop_summary() -> str:
    return f"""
        SELECT SUM({cost('b.list_cost')}) AS scope_cost, COUNT(DISTINCT b.cluster_id) AS items
        FROM billing_cost b
        JOIN compute_clusters_parsed k ON b.cluster_id = k.cluster_id
        WHERE b.billing_origin_product = 'ALL_PURPOSE' AND {_NO_AUTOSTOP}
          AND {f_usage_date('b.usage_date')}
    """


def _no_autostop_detail() -> str:
    return f"""
        SELECT k.cluster_name, k.owned_by AS owner, k.auto_termination_minutes,
               SUM({cost('b.list_cost')}) AS cost
        FROM billing_cost b
        JOIN compute_clusters_parsed k ON b.cluster_id = k.cluster_id
        WHERE b.billing_origin_product = 'ALL_PURPOSE' AND {_NO_AUTOSTOP}
          AND {f_usage_date('b.usage_date')}
        GROUP BY 1, 2, 3 ORDER BY cost DESC LIMIT 100
    """


def _failed_runs_base() -> str:
    return f"""
        SELECT c.job_id, c.job_name, c.cost, r.runs, r.failed,
               c.cost * r.failed / r.runs AS failed_cost
        FROM (
            SELECT job_id, MAX(job_name) AS job_name, SUM({cost()}) AS cost
            FROM billing_cost
            WHERE job_id IS NOT NULL AND {f_usage_date()}
            GROUP BY job_id
        ) c
        JOIN (
            SELECT job_id,
                   COUNT(DISTINCT run_id) AS runs,
                   COUNT(DISTINCT CASE WHEN result_state IN ('FAILED', 'TIMEDOUT') THEN run_id END) AS failed
            FROM job_run_timeline_parsed
            WHERE {f_ts_date("start_ts")}
            GROUP BY job_id
        ) r ON c.job_id = r.job_id
        WHERE r.failed > 0
    """


def _failed_runs_summary() -> str:
    return f"SELECT SUM(failed_cost) AS scope_cost, COUNT(*) AS items FROM ({_failed_runs_base()}) f"


def _failed_runs_detail() -> str:
    return f"""
        SELECT job_name, runs, failed, cost AS total_cost, failed_cost AS cost
        FROM ({_failed_runs_base()}) f
        ORDER BY failed_cost DESC LIMIT 100
    """


_LONG_AUTOSTOP = "(w.auto_stop_minutes = 0 OR w.auto_stop_minutes > 30)"


def _warehouse_autostop_summary() -> str:
    return f"""
        SELECT SUM({cost('b.list_cost')}) AS scope_cost, COUNT(DISTINCT b.warehouse_id) AS items
        FROM billing_cost b
        JOIN compute_warehouses_parsed w ON b.warehouse_id = w.warehouse_id
        WHERE {_LONG_AUTOSTOP} AND {f_usage_date('b.usage_date')}
    """


def _warehouse_autostop_detail() -> str:
    return f"""
        SELECT w.warehouse_name, w.warehouse_type, w.warehouse_size, w.auto_stop_minutes,
               SUM({cost('b.list_cost')}) AS cost
        FROM billing_cost b
        JOIN compute_warehouses_parsed w ON b.warehouse_id = w.warehouse_id
        WHERE {_LONG_AUTOSTOP} AND {f_usage_date('b.usage_date')}
        GROUP BY 1, 2, 3, 4 ORDER BY cost DESC LIMIT 100
    """


RULES: list[Rule] = [
    Rule(
        id="jobs_on_all_purpose",
        title="Jobs running on all-purpose clusters",
        area="Compute",
        effort="Easy",
        factor=0.5,
        assumption="Jobs Compute is billed roughly half the All-Purpose rate.",
        fix="Move each scheduled job to a job cluster (or serverless jobs) in the job's compute settings.",
        summary_sql=_jobs_on_all_purpose_summary,
        detail_sql=_jobs_on_all_purpose_detail,
    ),
    Rule(
        id="weekend_interactive",
        title="Interactive clusters running on weekends",
        area="Compute",
        effort="Easy",
        factor=0.5,
        assumption="Half of weekend interactive usage is assumed to be idle clusters left running.",
        fix="Set auto-termination to 30 min or less and enforce it with a cluster policy.",
        summary_sql=_weekend_interactive_summary,
        detail_sql=_weekend_interactive_detail,
    ),
    Rule(
        id="no_autostop",
        title="Clusters without auto-termination (or > 60 min)",
        area="Compute",
        effort="Easy",
        factor=0.25,
        assumption="A 30 min auto-termination typically removes a quarter of interactive cost.",
        fix="Edit the cluster → Advanced → Terminate after 30 minutes of inactivity; add a policy.",
        summary_sql=_no_autostop_summary,
        detail_sql=_no_autostop_detail,
    ),
    Rule(
        id="failed_runs",
        title="Compute burnt by failed job runs",
        area="Reliability",
        effort="Medium",
        factor=1.0,
        assumption="Cost of each job × its share of failed or timed-out runs.",
        fix="Fix the top failing jobs first; add retries with backoff only for transient errors.",
        summary_sql=_failed_runs_summary,
        detail_sql=_failed_runs_detail,
    ),
    Rule(
        id="warehouse_autostop",
        title="SQL warehouses with long auto-stop (> 30 min)",
        area="SQL",
        effort="Easy",
        factor=0.15,
        assumption="Idle time before auto-stop is ~15% of warehouse cost at these settings.",
        fix="Set auto-stop to 10 min (serverless: 5 min) in the warehouse settings.",
        summary_sql=_warehouse_autostop_summary,
        detail_sql=_warehouse_autostop_detail,
    ),
]


def _monthly(value: float) -> float:
    return value * 30 / max(1, period_days())


def _unallocated_cost(run_query) -> tuple[float, float]:
    df, _ = run_query(f"""
        SELECT SUM({cost()}) AS total,
               SUM(CASE WHEN team IS NULL OR TRIM(team) = '' THEN {cost()} ELSE 0 END) AS untagged
        FROM billing_cost WHERE {f_usage_date()}
    """)
    if df is None or df.empty:
        return 0.0, 0.0
    return float(df.iloc[0]["total"] or 0), float(df.iloc[0]["untagged"] or 0)
