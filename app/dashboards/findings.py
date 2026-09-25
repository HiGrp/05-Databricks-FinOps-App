"""Findings - concrete problems detected in the data, each with owner and fix.

Every detector runs one or two cached queries and returns a ``Finding`` or
``None``. A detector is attached to the page sections where it is shown; the
Action plan page runs them all.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

import pandas as pd
import streamlit as st

from dashboards import savings
from dashboards.components import download_csv, int_or_zero, show_error
from dashboards.date_filter import f_event_date, f_ts_date, f_usage_date, init_dates, previous_period
from dashboards.guides import GUIDES, md_inline
from dashboards.pricing import cost, fmt_money

SEVERITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
SEVERITY_ICON = {"High": "🔴", "Medium": "🟠", "Low": "🟡"}
DOMAIN_ICON = {"Cost": "💰", "Governance": "🏷️", "Performance": "🚀", "Reliability": "🔧", "Security": "🛡️"}

BASELINE_POLICY = """{
  "autotermination_minutes": {"type": "range", "minValue": 10, "maxValue": 30, "defaultValue": 20},
  "custom_tags.Team": {"type": "unlimited", "isOptional": false},
  "data_security_mode": {"type": "allowlist", "values": ["USER_ISOLATION", "SINGLE_USER"]},
  "spark_version": {"type": "unlimited", "defaultValue": "auto:latest-lts"}
}"""
_POLICY_STEP = "Enforce it: **Compute → Policies → Create policy**, paste the JSON below, assign it to your users."


@dataclass
class Finding:
    id: str
    domain: str
    severity: str
    title: str
    impact: str
    why: str
    steps: tuple[str, ...]
    effort: str
    owner: str
    monthly_usd: float | None = None
    code: str | None = None
    code_lang: str = "sql"
    evidence: pd.DataFrame | None = None


@dataclass(frozen=True)
class Detector:
    id: str
    sections: tuple[str, ...]
    run: Callable


def _sev_money(monthly: float) -> str:
    return "High" if monthly >= 1000 else "Medium" if monthly >= 200 else "Low"


def _n(df: pd.DataFrame) -> int:
    return int(df["total_n"].iloc[0]) if "total_n" in df.columns and not df.empty else len(df)


# --------------------------------------------------------------------------- #
# Savings rules → findings
# --------------------------------------------------------------------------- #

_RULE_PLAYBOOK = {
    "jobs_on_all_purpose": dict(
        domain="Cost", owner="Job owners", sections=("sec_finops_top_spenders", "sec_compute_list"),
        why="Scheduled jobs run on interactive (All-Purpose) clusters, billed about 2× the Jobs compute rate.",
        steps=(
            "Open each job below → **Tasks → Compute**.",
            "Replace the all-purpose cluster by a **new job cluster** (same node type and runtime) or **Serverless**.",
            "Run the job once to validate, then delete the old cluster if nobody uses it interactively.",
        ),
        code="""# Job definition (Asset Bundle / Jobs JSON): use a job cluster, not existing_cluster_id
job_clusters:
  - job_cluster_key: main
    new_cluster:
      spark_version: auto:latest-lts
      node_type_id: <same node type as today>
      num_workers: 2
tasks:
  - task_key: <your task>
    job_cluster_key: main""",
        lang="yaml",
    ),
    "weekend_interactive": dict(
        domain="Cost", owner="Platform admin", sections=("sec_opt_weekend",),
        why="Interactive clusters kept consuming on Saturday/Sunday: most of it is idle time.",
        steps=(
            "Ask each owner below whether the weekend usage was needed.",
            "Set auto-termination to 30 min or less on these clusters.",
            _POLICY_STEP,
        ),
        code=BASELINE_POLICY, lang="json",
    ),
    "no_autostop": dict(
        domain="Cost", owner="Platform admin", sections=("sec_opt_autostop", "sec_compute_list"),
        why="These clusters never stop (or wait over 60 min) when idle: you pay for nothing.",
        steps=(
            "Edit each cluster → **Terminate after 30 minutes of inactivity**.",
            _POLICY_STEP,
        ),
        code=BASELINE_POLICY, lang="json",
    ),
    "failed_runs": dict(
        domain="Reliability", owner="Job owners", sections=("sec_opt_failed_jobs", "sec_jobs_success"),
        why="Failed and timed-out runs consume compute with no result.",
        steps=(
            "Start with the job at the top: open it → **Runs** → failed run → read the error.",
            "Fix the root cause; add 1–2 retries with a delay only for transient errors.",
            "Set a timeout and failure notifications on the job.",
        ),
        code="""-- Most frequent errors per job (last 7 days)
SELECT job_id, termination_code, COUNT(*) AS runs
FROM system.lakeflow.job_run_timeline
WHERE result_state IN ('FAILED', 'TIMEDOUT')
  AND period_start_time >= current_date() - INTERVAL 7 DAYS
GROUP BY ALL ORDER BY runs DESC;""",
    ),
    "warehouse_autostop": dict(
        domain="Cost", owner="SQL admin", sections=("sec_sql_warehouses", "sec_opt_warehouse"),
        why="These SQL warehouses stay up more than 30 min after the last query.",
        steps=(
            "**SQL Warehouses** → warehouse → **Edit** → Auto stop: **10 min** (serverless: **5 min**).",
            "If users complain about start time, move the warehouse to serverless (starts in seconds).",
        ),
    ),
}


def _rule_detector(rule: savings.Rule) -> Detector:
    pb = _RULE_PLAYBOOK[rule.id]

    def run(run_query) -> Finding | None:
        df, err = run_query(rule.detail_sql())
        if err:
            raise RuntimeError(err)
        if df is None or df.empty:
            return None
        ev = df.copy()
        ev["est_savings_month"] = ev["cost"].astype(float).map(lambda v: savings._monthly(v * rule.factor))
        monthly = float(ev["est_savings_month"].sum())
        if monthly < 1:
            return None
        return Finding(
            id=rule.id, domain=pb["domain"], severity=_sev_money(monthly),
            title=f"{rule.title} - {len(ev)} found",
            impact=f"~{fmt_money(monthly)} / month",
            why=f"{pb['why']} Estimate: {rule.assumption}",
            steps=pb["steps"], effort=rule.effort, owner=pb["owner"], monthly_usd=monthly,
            code=pb.get("code"), code_lang=pb.get("lang", "sql"), evidence=ev,
        )

    return Detector(rule.id, pb["sections"], run)


# --------------------------------------------------------------------------- #
# Governance
# --------------------------------------------------------------------------- #

def _untagged(run_query) -> Finding | None:
    total, untagged = savings._unallocated_cost(run_query)
    if not total or untagged / total < 0.01:
        return None
    share = untagged / total
    ev, err = run_query(f"""
        SELECT COALESCE(cluster_name, warehouse_name, job_name, billing_origin_product) AS resource,
               billing_origin_product AS product, run_as AS owner, SUM({cost()}) AS cost
        FROM billing_cost
        WHERE (team IS NULL OR TRIM(team) = '') AND {f_usage_date()}
        GROUP BY 1, 2, 3 ORDER BY cost DESC LIMIT 50
    """)
    if err:
        raise RuntimeError(err)
    return Finding(
        id="untagged_spend", domain="Governance",
        severity="High" if share >= 0.2 else "Medium" if share >= 0.05 else "Low",
        title=f"{share:.0%} of spend has no Team tag",
        impact=f"~{fmt_money(savings._monthly(untagged))} / month unallocated",
        why="Untagged cost cannot be charged back: nobody feels responsible for it, so nobody optimizes it.",
        steps=(
            "Ask the owners below to add a `Team` tag on their clusters, jobs and warehouses.",
            "Tag serverless usage with **budget policies** (Settings → Compute → Serverless budget policies).",
            _POLICY_STEP,
        ),
        effort="Easy", owner="FinOps / Platform admin", code=BASELINE_POLICY, code_lang="json", evidence=ev,
    )


def _legacy_access_mode(run_query) -> Finding | None:
    df, err = run_query("""
        SELECT cluster_name, owned_by AS owner, data_security_mode, dbr_version
        FROM compute_clusters_parsed
        WHERE delete_time IS NULL
          AND (COALESCE(data_security_mode, 'NONE') = 'NONE' OR data_security_mode LIKE 'LEGACY%')
        ORDER BY cluster_name
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    return Finding(
        id="legacy_access_mode", domain="Security", severity="High",
        title=f"{len(df)} clusters without Unity Catalog isolation",
        impact="Data access not governed by Unity Catalog",
        why="Access mode `NONE` or legacy modes bypass Unity Catalog permissions and auditing.",
        steps=(
            "Edit each cluster → **Access mode** → **Standard** (shared) or **Dedicated** (single user).",
            "Test the notebooks that run on it (some legacy libraries need Dedicated mode).",
            _POLICY_STEP,
        ),
        effort="Medium", owner="Platform admin", code=BASELINE_POLICY, code_lang="json", evidence=df,
    )


def _old_runtime(run_query) -> Finding | None:
    df, err = run_query("""
        SELECT cluster_name, owned_by AS owner, dbr_version
        FROM compute_clusters_parsed
        WHERE delete_time IS NULL
          AND TRY_CAST(regexp_extract(dbr_version, '^([0-9]+)', 1) AS INTEGER) < 15
        ORDER BY dbr_version, cluster_name
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    return Finding(
        id="old_runtime", domain="Governance", severity="Medium",
        title=f"{len(df)} clusters on Databricks Runtime older than 15.x",
        impact="Security patches and performance gains missed",
        why="Old runtimes are at or past end of support and are slower than current LTS versions.",
        steps=(
            "Edit each cluster → **Databricks Runtime** → latest **LTS**; test the main notebooks.",
            "Default new clusters to `auto:latest-lts` with a policy.",
        ),
        effort="Medium", owner="Platform admin", code=BASELINE_POLICY, code_lang="json", evidence=df,
    )


def _no_policy(run_query) -> Finding | None:
    df, err = run_query("""
        SELECT cluster_name, owned_by AS owner, auto_termination_minutes, worker_count
        FROM compute_clusters_parsed
        WHERE delete_time IS NULL AND (policy_id IS NULL OR TRIM(policy_id) = '')
        ORDER BY worker_count DESC
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    return Finding(
        id="no_policy", domain="Governance", severity="Medium",
        title=f"{len(df)} clusters created without a cluster policy",
        impact="No guardrails on size, auto-stop or tags",
        why="Without a policy, anyone can create any size of cluster that never stops and has no owner tag.",
        steps=(
            _POLICY_STEP,
            "Remove the *Unrestricted cluster creation* entitlement from users (Settings → Identity and access).",
        ),
        effort="Easy", owner="Platform admin", code=BASELINE_POLICY, code_lang="json", evidence=df,
    )


# --------------------------------------------------------------------------- #
# Performance
# --------------------------------------------------------------------------- #

def _spill(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT executed_by, warehouse_name, ROUND(spilled_local_bytes / 1e9, 1) AS spill_gb,
               ROUND(total_duration_ms / 1000.0, 1) AS duration_s,
               LEFT(COALESCE(statement_text, ''), 120) AS query, COUNT(*) OVER () AS total_n
        FROM query_history_full
        WHERE spilled_local_bytes > 1e9 AND {f_ts_date("start_time")}
        ORDER BY spilled_local_bytes DESC LIMIT 50
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    n = _n(df)
    return Finding(
        id="sql_spill", domain="Performance", severity="High" if n >= 100 else "Medium",
        title=f"{n} SQL queries spilled more than 1 GB to disk",
        impact="Slow queries and wasted warehouse time",
        why="Spill means the query did not fit in memory: it is several times slower and costlier.",
        steps=(
            "Open the top queries in **Query history → Query profile** to see the step that spills.",
            "Rewrite: filter before joins, select fewer columns, avoid large `DISTINCT` / `ORDER BY`.",
            "Cluster the big tables on the filter/join columns (SQL below). Still spilling? Try the next warehouse size.",
        ),
        effort="Medium", owner="Data engineers",
        code="""ALTER TABLE <catalog>.<schema>.<table> CLUSTER BY (<filter_column>);
OPTIMIZE <catalog>.<schema>.<table>;
ANALYZE TABLE <catalog>.<schema>.<table> COMPUTE STATISTICS FOR ALL COLUMNS;""",
        evidence=df.drop(columns=["total_n"]),
    )


def _slow_sql(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT executed_by, warehouse_name, ROUND(total_duration_ms / 1000.0, 1) AS duration_s,
               LEFT(COALESCE(statement_text, ''), 120) AS query, COUNT(*) OVER () AS total_n
        FROM query_history_full
        WHERE execution_status = 'FINISHED' AND total_duration_ms > 30000 AND {f_ts_date("start_time")}
        ORDER BY total_duration_ms DESC LIMIT 50
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    n = _n(df)
    return Finding(
        id="slow_sql", domain="Performance", severity="Medium" if n >= 20 else "Low",
        title=f"{n} SQL queries took more than 30 s",
        impact="Slow dashboards, users waiting",
        why="Long queries block users and keep warehouses scaled up.",
        steps=(
            "Open each query in **Query history → Query profile**: find the slowest operator.",
            "Remove `SELECT *`, filter on clustered columns, pre-aggregate in a gold table for dashboards.",
            "Use a materialized view for heavy dashboard queries that repeat.",
        ),
        effort="Medium", owner="Data engineers / BI",
        code="""CREATE MATERIALIZED VIEW <catalog>.<schema>.<dashboard_mv> AS
SELECT <dimensions>, SUM(<measure>) AS <measure>
FROM <catalog>.<schema>.<big_table>
GROUP BY ALL;""",
        evidence=df.drop(columns=["total_n"]),
    )


def _queue(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT warehouse_name, COUNT(*) AS queries,
               SUM(CASE WHEN waiting_at_capacity_duration_ms > 10000 THEN 1 ELSE 0 END) AS queued_over_10s,
               ROUND(AVG(waiting_at_capacity_duration_ms) / 1000.0, 1) AS avg_wait_s
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
        GROUP BY 1 ORDER BY queued_over_10s DESC
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    total, queued = float(df["queries"].sum()), float(df["queued_over_10s"].sum())
    share = queued / total if total else 0
    if share < 0.05:
        return None
    return Finding(
        id="sql_queue", domain="Performance", severity="High" if share >= 0.2 else "Medium",
        title=f"{share:.0%} of SQL queries waited more than 10 s for capacity",
        impact=f"{int(queued):,} queries queued",
        why="The warehouse is saturated at peak: users wait before their query even starts.",
        steps=(
            "**SQL Warehouses** → busiest warehouse below → **Edit** → raise **Maximum clusters** (scaling).",
            "Move ETL/batch queries to a separate warehouse or to jobs.",
            "Serverless warehouses scale out in seconds.",
        ),
        effort="Easy", owner="SQL admin", evidence=df[df["queued_over_10s"] > 0],
    )


def _low_cache(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT warehouse_name, COUNT(*) AS selects,
               SUM(CASE WHEN from_result_cache THEN 1 ELSE 0 END) AS cache_hits
        FROM query_history_full
        WHERE statement_type = 'SELECT' AND execution_status = 'FINISHED' AND {f_ts_date("start_time")}
        GROUP BY 1 ORDER BY selects DESC
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    total, hits = float(df["selects"].sum()), float(df["cache_hits"].sum())
    rate = hits / total if total else 1
    if total < 100 or rate >= 0.3:
        return None
    df = df.assign(cache_pct=(df["cache_hits"] / df["selects"] * 100).round(0))
    return Finding(
        id="low_cache", domain="Performance", severity="Medium" if rate < 0.1 else "Low",
        title=f"Only {rate:.0%} of SELECT queries hit the result cache",
        impact="Identical queries recomputed",
        why="Cached results are free and instant. A low rate usually comes from `now()`-style functions or dashboards refreshing on every view.",
        steps=(
            "Replace `now()` / `current_timestamp()` in dashboard queries with a date parameter.",
            "Schedule dashboard refreshes instead of refreshing on every open.",
        ),
        effort="Easy", owner="BI developers", evidence=df,
    )


def _oversized(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT COALESCE(c.cluster_name, n.cluster_id) AS cluster_name,
               ROUND(AVG(n.cpu_user_percent + n.cpu_system_percent), 1) AS avg_cpu,
               ROUND(AVG(n.mem_used_percent), 1) AS avg_mem, COUNT(*) AS samples
        FROM compute_node_timeline n
        LEFT JOIN compute_clusters_parsed c ON n.cluster_id = c.cluster_id
        WHERE {f_ts_date("n.start_time")}
        GROUP BY 1
        HAVING COUNT(*) >= 20 AND AVG(n.cpu_user_percent + n.cpu_system_percent) < 20
        ORDER BY avg_cpu
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    return Finding(
        id="oversized_clusters", domain="Cost", severity="Medium",
        title=f"{len(df)} clusters use less than 20% CPU on average",
        impact="Paying for idle cores",
        why="These clusters are bigger than their workload needs.",
        steps=(
            "Reduce the number of workers, or enable autoscaling with a lower minimum.",
            "Pick a smaller node type if memory usage is also low.",
        ),
        effort="Easy", owner="Cluster owners", evidence=df,
    )


# --------------------------------------------------------------------------- #
# Reliability
# --------------------------------------------------------------------------- #

def _failed_sql(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT executed_by, COUNT(*) AS queries,
               SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) AS failed
        FROM query_history_full
        WHERE {f_ts_date("start_time")}
        GROUP BY 1 ORDER BY failed DESC
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    total, failed = float(df["queries"].sum()), float(df["failed"].sum())
    share = failed / total if total else 0
    if share < 0.05:
        return None
    return Finding(
        id="failed_sql", domain="Reliability", severity="High" if share >= 0.15 else "Medium",
        title=f"{share:.0%} of SQL queries failed ({int(failed):,})",
        impact="Broken dashboards and reports",
        why="Failed queries are usually missing permissions, renamed columns or dropped tables.",
        steps=(
            "Run the SQL below to list the most frequent errors.",
            "Permission errors: grant to the user's group. Schema errors: fix the dashboard or pipeline.",
        ),
        effort="Medium", owner="BI developers",
        code="""SELECT executed_by, error_message, COUNT(*) AS n
FROM system.query.history
WHERE execution_status = 'FAILED' AND start_time >= current_date() - INTERVAL 7 DAYS
GROUP BY ALL ORDER BY n DESC LIMIT 20;""",
        evidence=df[df["failed"] > 0],
    )


# --------------------------------------------------------------------------- #
# Security
# --------------------------------------------------------------------------- #

def _access_denied(run_query) -> Finding | None:
    tot, err = run_query(f"""
        SELECT COUNT(*) AS events, SUM(CASE WHEN status_code = 403 THEN 1 ELSE 0 END) AS denied
        FROM access_audit_parsed WHERE {f_event_date()}
    """)
    if err:
        raise RuntimeError(err)
    if tot is None or tot.empty:
        return None
    events, denied = int_or_zero(tot.iloc[0]["events"]), int_or_zero(tot.iloc[0]["denied"])
    if not denied:
        return None
    share = denied / events if events else 0
    ev, _ = run_query(f"""
        SELECT user_email, service_name, action_name, COUNT(*) AS denied
        FROM access_audit_parsed
        WHERE status_code = 403 AND {f_event_date()}
        GROUP BY 1, 2, 3 ORDER BY denied DESC LIMIT 30
    """)
    return Finding(
        id="access_denied", domain="Security",
        severity="High" if share >= 0.05 else "Medium" if share >= 0.01 else "Low",
        title=f"{int(denied):,} access-denied events ({share:.1%} of all requests)",
        impact="Missing grants, or someone probing",
        why="Many 403 errors from the same identity mean either a missing permission or unauthorized attempts.",
        steps=(
            "Look at the identities at the top: is the access legitimate?",
            "Legitimate: grant it to their **group** (SQL below). Not legitimate: alert your security team.",
        ),
        effort="Easy", owner="Security / Data governance",
        code="""SHOW GRANTS ON SCHEMA <catalog>.<schema>;
GRANT USE CATALOG ON CATALOG <catalog> TO `<group>`;
GRANT USE SCHEMA, SELECT ON SCHEMA <catalog>.<schema> TO `<group>`;""",
        evidence=ev,
    )


def _personal_tokens(run_query) -> Finding | None:
    df, err = run_query(f"""
        SELECT user_email, COUNT(*) AS token_logins, COUNT(DISTINCT source_ip_address) AS source_ips
        FROM access_audit_parsed
        WHERE action_name = 'tokenLogin' AND {f_event_date()}
        GROUP BY 1 ORDER BY token_logins DESC LIMIT 50
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    many_ips = int((df["source_ips"] >= 5).sum())
    return Finding(
        id="personal_tokens", domain="Security", severity="High" if many_ips else "Medium",
        title=f"{len(df)} users sign in with personal access tokens"
              + (f" - {many_ips} from 5+ IP addresses" if many_ips else ""),
        impact="Long-lived secrets tied to people",
        why="Personal access tokens (PAT) are long-lived and often shared in scripts. One token used from many IPs may be leaked.",
        steps=(
            "Move automation to **service principals** with OAuth (Settings → Identity and access → Service principals).",
            "Set a maximum token lifetime: **Settings → Advanced → Personal access tokens**.",
            "Revoke tokens used from unexpected IPs, and enable **IP access lists** (Settings → Security).",
        ),
        effort="Medium", owner="Security admin",
        code="""-- Who still uses personal access tokens (last 30 days)
SELECT user_identity.email, COUNT(*) AS logins, COUNT(DISTINCT source_ip_address) AS ips
FROM system.access.audit
WHERE action_name = 'tokenLogin' AND event_date >= current_date() - INTERVAL 30 DAYS
GROUP BY ALL ORDER BY logins DESC;""",
        evidence=df,
    )


_SENSITIVE_ACTIONS = (
    "grantPermission", "updatePermissions", "deleteTable", "updateMetastore",
    "putSecret", "deleteSecret", "add", "removeMember", "updateRole",
    "setAdmin", "addPrincipalToGroup", "removePrincipalFromGroup",
)


def _off_hours_admin(run_query) -> Finding | None:
    actions = ", ".join(f"'{a}'" for a in _SENSITIVE_ACTIONS)
    df, err = run_query(f"""
        SELECT user_email, service_name, action_name, COUNT(*) AS events
        FROM access_audit_parsed
        WHERE action_name IN ({actions}) AND {f_event_date()}
          AND (hour(event_time) < 7 OR hour(event_time) >= 20
               OR (CAST(strftime('%w', event_time) AS INTEGER) + 1) IN (1, 7))
        GROUP BY 1, 2, 3 ORDER BY events DESC LIMIT 50
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    total = int(df["events"].sum())
    return Finding(
        id="off_hours_admin", domain="Security", severity="Medium",
        title=f"{total:,} sensitive changes at night or on weekends",
        impact="Grants, secrets and role changes outside working hours",
        why="Permission, secret and group changes outside 07:00–20:00 UTC or on weekends are unusual and worth a check.",
        steps=(
            "Confirm each identity below with its manager or the change calendar.",
            "Create a Databricks SQL alert with the query below to be notified next time.",
        ),
        effort="Easy", owner="Security admin",
        code=f"""SELECT event_time, user_identity.email, service_name, action_name
FROM system.access.audit
WHERE action_name IN ({actions})
  AND (hour(event_time) < 7 OR hour(event_time) >= 20 OR dayofweek(event_time) IN (1, 7))
  AND event_date >= current_date() - INTERVAL 1 DAY;""",
        evidence=df,
    )


# --------------------------------------------------------------------------- #
# Cost trend
# --------------------------------------------------------------------------- #

def _cost_spike(run_query) -> Finding | None:
    init_dates()
    end = st.session_state.filter_date_end
    cur_start, prev_start = end - timedelta(days=6), end - timedelta(days=13)
    df, err = run_query(f"""
        SELECT billing_origin_product AS product,
               SUM(CASE WHEN usage_date >= '{cur_start}' THEN {cost()} ELSE 0 END) AS last_7_days,
               SUM(CASE WHEN usage_date < '{cur_start}' THEN {cost()} ELSE 0 END) AS previous_7_days
        FROM billing_cost
        WHERE usage_date >= '{prev_start}' AND usage_date <= '{end}'
        GROUP BY 1
    """)
    if err:
        raise RuntimeError(err)
    if df is None or df.empty:
        return None
    df = df.assign(change=df["last_7_days"] - df["previous_7_days"])
    up = df[(df["last_7_days"] >= df["previous_7_days"] * 1.25) & (df["change"] >= 100)]
    if up.empty:
        return None
    extra = float(up["change"].sum())
    return Finding(
        id="cost_spike", domain="Cost", severity=_sev_money(extra * 30 / 7),
        title="Spend up 25%+ this week on " + ", ".join(up["product"].astype(str)),
        impact=f"+{fmt_money(extra)} vs previous week",
        why="A sudden increase usually means a new workload, a bigger cluster, or something left running.",
        steps=(
            "Open **💰 FinOps → Top spenders** for the last 7 days and compare with the week before.",
            "Run the SQL below to find the resources that grew.",
            "If it is expected (new project), update the team budget; otherwise stop or resize the resource.",
        ),
        effort="Easy", owner="FinOps",
        code="""SELECT usage_date, billing_origin_product,
       usage_metadata.cluster_id, usage_metadata.job_id, usage_metadata.warehouse_id,
       SUM(usage_quantity) AS dbu
FROM system.billing.usage
WHERE usage_date >= current_date() - INTERVAL 14 DAYS
GROUP BY ALL ORDER BY dbu DESC LIMIT 50;""",
        evidence=df.sort_values("change", ascending=False),
    )


_RULE_DETECTORS = {r.id: _rule_detector(r) for r in savings.RULES}

DETECTORS: list[Detector] = list(_RULE_DETECTORS.values()) + [
    Detector("untagged_spend", ("sec_finops_team", "sec_compute_tags", "sec_jobs_team"), _untagged),
    Detector("legacy_access_mode", ("sec_compute_tags", "sec_sec_uc"), _legacy_access_mode),
    Detector("old_runtime", ("sec_compute_runtime",), _old_runtime),
    Detector("no_policy", ("sec_compute_tags",), _no_policy),
    Detector("sql_spill", ("sec_opt_spill", "sec_sql_cache"), _spill),
    Detector("slow_sql", ("sec_opt_slow_sql", "sec_sql_perf"), _slow_sql),
    Detector("sql_queue", ("sec_sql_queues", "sec_opt_warehouse"), _queue),
    Detector("low_cache", ("sec_sql_cache",), _low_cache),
    Detector("oversized_clusters", ("sec_opt_node_usage",), _oversized),
    Detector("failed_sql", ("sec_sql_perf",), _failed_sql),
    Detector("access_denied", ("sec_sec_denied",), _access_denied),
    Detector("personal_tokens", ("sec_sec_signin",), _personal_tokens),
    Detector("off_hours_admin", ("sec_sec_heatmap", "sec_sec_secrets"), _off_hours_admin),
    Detector("cost_spike", ("sec_finops_trends",), _cost_spike),
]


# --------------------------------------------------------------------------- #
# Evaluation (memoized per script run)
# --------------------------------------------------------------------------- #

def reset_run_state() -> None:
    st.session_state["_findings_memo"] = {}
    st.session_state["_findings_errors"] = []
    st.session_state["_findings_shown"] = set()


def _evaluate(det: Detector, run_query) -> Finding | None:
    memo = st.session_state.setdefault("_findings_memo", {})
    if det.id not in memo:
        try:
            memo[det.id] = det.run(run_query)
        except Exception as exc:  # noqa: BLE001 - a failing check must never break a page
            memo[det.id] = None
            st.session_state.setdefault("_findings_errors", []).append(str(exc))
    return memo[det.id]


def _sort_key(f: Finding):
    return SEVERITY_RANK[f.severity], -(f.monthly_usd or 0)


def all_findings(run_query) -> list[Finding]:
    found = [f for d in DETECTORS if (f := _evaluate(d, run_query)) is not None]
    return sorted(found, key=_sort_key)


def health_score(items: list[Finding]) -> int:
    """100 = nothing detected. High −8, Medium −3, Low −1."""
    penalty = {"High": 8, "Medium": 3, "Low": 1}
    return max(0, 100 - sum(penalty[f.severity] for f in items))


def waste_removed(run_query) -> float:
    """Monthly waste of the savings rules that went down vs the previous period."""
    current = {f.id: f.monthly_usd or 0 for f in all_findings(run_query) if f.id in _RULE_DETECTORS}
    removed = 0.0
    with previous_period():
        for rule_id, det in _RULE_DETECTORS.items():
            try:
                before = det.run(run_query)
            except Exception:  # noqa: BLE001
                continue
            if before is not None:
                removed += max(0.0, (before.monthly_usd or 0) - current.get(rule_id, 0))
    return removed


# --------------------------------------------------------------------------- #
# Rendering - one To-do item style everywhere
# --------------------------------------------------------------------------- #

def _fmt_evidence(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in ("cost", "total_cost", "est_savings_month", "last_7_days", "previous_7_days", "change"):
            out[col] = out[col].map(fmt_money)
    return out


def render_todo_item(f: Finding, context: str) -> None:
    st.markdown(
        f'<div class="todo-item sev-{f.severity.lower()}">'
        f'<div class="todo-line">{SEVERITY_ICON[f.severity]} <strong>{html.escape(f.title)}</strong></div>'
        f'<div class="todo-meta"><strong>{html.escape(f.impact)}</strong> · {DOMAIN_ICON.get(f.domain, "")} '
        f"{f.domain} · Owner: {html.escape(f.owner)} · Effort: {f.effort}</div></div>",
        unsafe_allow_html=True,
    )
    with st.expander("How to fix"):
        st.markdown(f.why)
        st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(f.steps, 1)))
        if f.code:
            st.code(f.code, language=f.code_lang)
        if f.evidence is not None and not f.evidence.empty:
            st.markdown("**Resources concerned**")
            st.dataframe(_fmt_evidence(f.evidence), use_container_width=True, hide_index=True)
            download_csv(f.evidence, f"finops_{f.id}.csv", key=f"dl_{context}_{f.id}")


def render_section_todo(section_key: str | None, run_query) -> None:
    """The To-do box at the end of every section: detected problems first, then good practices."""
    guide = GUIDES.get(section_key or "")
    shown = st.session_state.setdefault("_findings_shown", set())
    detected = []
    for det in DETECTORS:
        if section_key in det.sections and det.id not in shown:
            f = _evaluate(det, run_query)
            if f is not None:
                shown.add(det.id)
                detected.append(f)
    if not detected and guide is None:
        return
    with st.container(border=True):
        st.markdown('<p class="todo-title">✅ To do</p>', unsafe_allow_html=True)
        if detected:
            st.caption("Detected from your data - gone automatically once the issue is fixed.")
            for f in sorted(detected, key=_sort_key):
                render_todo_item(f, section_key)
        elif guide is not None:
            st.success("Nothing wrong detected for this period.")
        if guide is not None:
            items = "".join(f'<div class="todo-check">☐ {md_inline(a)}</div>' for a in guide.actions)
            label = "Good practices" if detected else "Good practices to verify"
            st.markdown(f'<p class="todo-sub">{label}</p>{items}', unsafe_allow_html=True)
            if not detected:
                st.caption("These stay visible - they are a manual checklist, not tracked automatically.")


def _go_to_plan() -> None:
    st.session_state.nav_category = "Action plan"


def render_top(run_query, *, n: int, key: str, domains: tuple[str, ...] | None = None) -> None:
    items = [f for f in all_findings(run_query) if domains is None or f.domain in domains]
    if not items:
        if not _report_errors():
            st.success("Nothing urgent detected for this period. 🎉")
        return
    shown = st.session_state.setdefault("_findings_shown", set())
    for f in items[:n]:
        shown.add(f.id)
        render_todo_item(f, key)
    more = f" · {len(items) - n} more" if len(items) > n else ""
    st.button(f"See all actions{more} →", key=f"goto_plan_{key}", on_click=_go_to_plan)


def _report_errors() -> bool:
    errors = st.session_state.get("_findings_errors") or []
    if errors:
        show_error(errors[0])
        return True
    return False


def _plan_frame(items: list[Finding]) -> pd.DataFrame:
    return pd.DataFrame([{
        "Priority": f.severity,
        "Domain": f.domain,
        "Action": f.title,
        "Impact": f.impact,
        "Savings / month": round(f.monthly_usd or 0),
        "Effort": f.effort,
        "Owner": f.owner,
        "How to fix": " | ".join(s.replace("**", "").replace("`", "") for s in f.steps),
    } for f in items])


def render_plan(run_query) -> None:
    items = all_findings(run_query)
    if not items:
        if not _report_errors():
            st.success("Nothing to fix detected for this period. 🎉")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("💡 Savings / month", fmt_money(sum(f.monthly_usd or 0 for f in items)),
              help="Sum of the money-quantified actions. Estimates may overlap.")
    c2.metric("📋 Actions", len(items))
    c3.metric("🔴 High priority", sum(f.severity == "High" for f in items))
    st.caption("Issues below are detected from your data and disappear once fixed.")

    domains = ["All"] + [d for d in DOMAIN_ICON if any(f.domain == d for f in items)]
    choice = st.radio("Domain", domains, horizontal=True, key="plan_domain", label_visibility="collapsed",
                      format_func=lambda d: d if d == "All" else f"{DOMAIN_ICON[d]} {d}")
    if choice != "All":
        items = [f for f in items if f.domain == choice]

    for f in items:
        render_todo_item(f, "plan")
    download_csv(_plan_frame(items), "finops_action_plan.csv", key="dl_action_plan",
                 label="⬇ Export the action plan (CSV)")
