"""Plain-English guide per section - what it shows, how to read it, what to do."""

from __future__ import annotations

import html
import re
from typing import NamedTuple

import streamlit as st


class Guide(NamedTuple):
    what: str
    read: str
    actions: tuple[str, ...]


GUIDES: dict[str, Guide] = {
    "sec_action_plan": Guide(
        "Every problem detected in your data, ranked by severity and money at stake.",
        "🔴 High: this week. 🟠 Medium: this month. 🟡 Low: when convenient. "
        "Savings are conservative estimates, projected to 30 days.",
        (
            "Assign each line to the owner shown and export the plan to CSV.",
            "Fix, then come back after a week: fixed items disappear from the list.",
            "Want help to go further? Contact us (link in the sidebar).",
        ),
    ),
    # ── FinOps ──
    "sec_finops_summary": Guide(
        "The cost of the selected period vs the previous period of the same length, and the daily trend.",
        "Cost / month and run-rate let you compare any period; a rise without new projects usually means waste.",
        (
            "Share this number monthly with each team lead.",
            "Set a budget with alerts per workspace or team (Account console → Usage → Budgets).",
        ),
    ),
    "sec_finops_top_spenders": Guide(
        "The clusters, jobs, warehouses and users that cost the most.",
        "About 20% of resources usually make 80% of the cost: this is where optimization pays off.",
        (
            "Top clusters: check auto-termination, size, and whether they run jobs (they should use Jobs compute).",
            "Top jobs: check their failure rate and whether they run on an all-purpose cluster.",
            "Top warehouses: check auto-stop, and size vs queue time in **📊 SQL**.",
        ),
    ),
    "sec_finops_trends": Guide(
        "Daily cost by product.",
        "Watch for new products appearing and for weekend cost on interactive compute (clusters left running).",
        (
            "Match a spike with what was deployed or launched that day.",
            "High weekend cost: see **⚡ Optimization → Weekend clusters**.",
        ),
    ),
    "sec_finops_monthly": Guide(
        "Cost per month.",
        "A trend over 3+ months matters more than a single month. Growth should follow business growth.",
        (
            "Agree a monthly budget per team and review the gap every month.",
            "Explain every month above +15% (new project, migration, or waste).",
        ),
    ),
    "sec_finops_sku": Guide(
        "Top billing SKUs (price lines) and usage types.",
        "ALL_PURPOSE SKUs cost about 2× JOBS SKUs for the same work. Serverless SKUs include the cloud VM cost.",
        (
            "Move scheduled notebooks from All-Purpose to Jobs compute.",
            "For SQL, compare serverless vs classic: serverless has no idle VM cost and starts in seconds.",
        ),
    ),
    "sec_finops_team": Guide(
        "Cost by Team, CostCenter and Environment tags - exportable for chargeback.",
        "`(not set)` is spend that nobody owns. Keep it under 5%.",
        (
            "Make the `Team` tag mandatory with a cluster policy.",
            "Tag serverless usage with budget policies, and tag every job and SQL warehouse.",
            "Send the CSV to each team lead every month.",
        ),
    ),
    "sec_finops_storage": Guide(
        "Storage and networking cost (non-compute).",
        "It grows slowly with data. A sudden jump often means duplicated data, no VACUUM, or cross-region traffic.",
        (
            "Run `VACUUM` on large Delta tables, or enable predictive optimization on Unity Catalog managed tables.",
            "Keep compute in the same region as the data to avoid egress fees.",
        ),
    ),
    "sec_finops_prices": Guide(
        "The list price per SKU used for every cost in this app.",
        "Costs = list price × (1 − your discount).",
        (
            "Set your negotiated discount in `FINOPS_DISCOUNT_PCT` (`app/app.yaml`).",
            "Check your commit consumption with your Databricks account team.",
        ),
    ),
    # ── Optimization ──
    "sec_opt_action": Guide(
        "Top cost, performance and reliability fixes detected in this workspace.",
        "🔴 High: this week. 🟠 Medium: this month. 🟡 Low: when convenient.",
        ("Open **✅ Action plan** for every finding with its step-by-step fix.",),
    ),
    "sec_opt_weekend": Guide(
        "Clusters that consumed DBU on Saturday or Sunday.",
        "Scheduled weekend jobs are fine. Interactive clusters busy on weekends are usually left running.",
        (
            "Set auto-termination to 30 min or less on interactive clusters.",
            "Move real weekend workloads to scheduled jobs.",
            "Enforce it with a cluster policy (`autotermination_minutes` max 30).",
        ),
    ),
    "sec_opt_failed_jobs": Guide(
        "Jobs with failed, timed-out or cancelled runs.",
        "Each failed run is paid compute with no result. The same job failing again and again is a bug, not bad luck.",
        (
            "Open the job → Runs → failed run → read the error and fix the root cause.",
            "Add retries only for transient errors (1–2 retries with a delay).",
            "Set a timeout and failure notifications on every production job.",
        ),
    ),
    "sec_opt_slow_sql": Guide(
        "The longest-running SQL queries.",
        "Dashboard queries over 30 s hurt users and burn warehouse time.",
        (
            "Open Query history → the query → **Query profile** to find the slowest step.",
            "Filter early and select only the columns you need (no `SELECT *`).",
            "Cluster big tables on filter columns: `ALTER TABLE t CLUSTER BY (col)`.",
        ),
    ),
    "sec_opt_spill": Guide(
        "Queries that spilled more than 1 GB to disk.",
        "Spill means not enough memory: the query is slow and expensive.",
        (
            "Rewrite: filter before joins, fewer columns, avoid huge `DISTINCT` / `ORDER BY`.",
            "If one warehouse spills often, try the next size up.",
            "Keep statistics fresh: `ANALYZE TABLE t COMPUTE STATISTICS FOR ALL COLUMNS`.",
        ),
    ),
    "sec_opt_autostop": Guide(
        "The auto-termination setting of every interactive cluster.",
        "0 = never stops (paid while idle). Over 60 min wastes idle time. 10–30 min is a good default.",
        (
            "Edit the cluster → **Terminate after 30 minutes of inactivity**.",
            "Apply a cluster policy so new clusters get it by default.",
        ),
    ),
    "sec_opt_node_usage": Guide(
        "Average CPU and memory per cluster.",
        "CPU under 20% most of the time = oversized. Memory over 90% = undersized (spill, out-of-memory).",
        (
            "Oversized: fewer or smaller workers, or autoscaling with a lower minimum.",
            "Undersized: memory-optimized node types for heavy joins.",
        ),
    ),
    "sec_opt_warehouse": Guide(
        "SQL warehouse start, stop and scaling events.",
        "Many scale-ups = demand above the minimum. Frequent start/stop = bursty use or a very short auto-stop.",
        (
            "If queries queue, raise **max clusters** (scaling) rather than the size.",
            "If mostly idle, reduce the size and shorten auto-stop.",
            "Consider serverless: it starts in seconds and has no idle VM cost.",
        ),
    ),
    # ── Security ──
    "sec_sec_audit": Guide(
        "Audit events per day.",
        "A stable volume is normal. Spikes at night or on weekends deserve a look.",
        (
            "Create a Databricks SQL alert on `system.access.audit` for unusual spikes.",
            "Keep audit history as long as your compliance requires (export it if needed).",
        ),
    ),
    "sec_sec_denied": Guide(
        "Requests refused with HTTP 403 (access denied).",
        "A few are normal. Many from the same identity = a missing grant, or someone probing.",
        (
            "Legitimate need: grant access to a **group**, never to individuals.",
            "No business need: check with the user and your security team.",
            "Check current access with `SHOW GRANTS ON SCHEMA catalog.schema`.",
        ),
    ),
    "sec_sec_top_users": Guide(
        "Identities with the most audit events.",
        "Service principals are expected at the top. A human with automation-level volume is probably running a pipeline with a personal token.",
        (
            "Move automation to service principals.",
            "Confirm that the top human identities are expected (admins, data engineers).",
        ),
    ),
    "sec_sec_heatmap": Guide(
        "Audit events by service and day.",
        "Look for dark cells on unusual days, or activity on services you don't use.",
        (
            "Drill into `system.access.audit` for that service and day.",
            "Disable features you don't use.",
        ),
    ),
    "sec_sec_uc": Guide(
        "Unity Catalog actions: create, grant, delete…",
        "Grants and deletes are sensitive: they should come from a few admins or from CI/CD.",
        (
            "Manage grants as code (Terraform or bundles) instead of by hand.",
            "Grant to groups only, and review `ALL PRIVILEGES` / `MANAGE` grants every quarter.",
            "Protect production catalogs: only a deployment service principal may create or drop objects.",
        ),
    ),
    "sec_sec_secrets": Guide(
        "Secret, token and IAM (users, groups, roles) events.",
        "Secret reads are normal in jobs. Secret writes/deletes and role changes should be rare and expected.",
        (
            "Limit secret scope ACLs to the identities that need them, with READ only.",
            "Review every role or admin change of the period.",
        ),
    ),
    "sec_sec_signin": Guide(
        "Sign-ins by method and source IP.",
        "`tokenLogin` = a personal access token (PAT). One identity from many IPs = a shared or leaked token.",
        (
            "Replace PATs used by automation with service principals and OAuth.",
            "Set a maximum lifetime for tokens (Settings → Advanced → Personal access tokens).",
            "Enable IP access lists for the workspace (Settings → Security).",
        ),
    ),
    # ── Compute ──
    "sec_compute_list": Guide(
        "Every interactive cluster with its size, owner and auto-stop.",
        "Look for clusters without an owner, with many workers, or with auto-stop at 0.",
        (
            "Delete clusters not used for 30+ days.",
            "Fix auto-stop 0 first: it is the biggest waste.",
            "Standardize with cluster policies (size limits, auto-stop, tags).",
        ),
    ),
    "sec_compute_tags": Guide(
        "Team tags, access mode and how clusters were created.",
        "Access mode `NONE` (no isolation) cannot use Unity Catalog securely. No Team tag = cost nobody owns.",
        (
            "Switch clusters to **Standard** (shared) or **Dedicated** (single user) access mode.",
            "Require the Team tag and allowed access modes in a cluster policy.",
        ),
    ),
    "sec_compute_runtime": Guide(
        "Databricks Runtime versions and node types in use.",
        "Old runtimes miss security patches and performance gains. Too many node types are hard to govern.",
        (
            "Upgrade to the latest LTS runtime.",
            "Default `spark_version` to `auto:latest-lts` in cluster policies.",
            "Limit node types to a short approved list.",
        ),
    ),
    "sec_compute_events": Guide(
        "Cluster lifecycle events: start, resize, terminate…",
        "Frequent restarts or resizes = an unstable workload or a bad autoscaling range.",
        (
            "For frequent restarts, check the driver logs.",
            "If a cluster resizes constantly, narrow its autoscaling min/max.",
        ),
    ),
    # ── Jobs ──
    "sec_jobs_overview": Guide(
        "Job runs per day and their outcome.",
        "Failures should be rare and not growing.",
        (
            "Enable failure notifications on every production job.",
            "Track the failure rate every week.",
        ),
    ),
    "sec_jobs_success": Guide(
        "Success rate per job.",
        "A production job under 95% needs a fix.",
        (
            "Fix the job with the lowest success rate and the highest cost first.",
            "Add a timeout on each task to stop runaway runs.",
        ),
    ),
    "sec_jobs_duration": Guide(
        "Average run, queue and execution time per job.",
        "A growing duration = growing data or degrading code. Queue time = waiting for capacity.",
        (
            "Long jobs: check the Spark UI for skew and spill.",
            "Queue time: use serverless jobs or pools for faster start.",
        ),
    ),
    "sec_jobs_team": Guide(
        "Job runs by team tag and outcome.",
        "Shows who owns which workload and who has failures.",
        ("Tag every job with `Team` so cost and incidents go to the right owner.",),
    ),
    "sec_jobs_tasks": Guide(
        "Tasks inside jobs, by type and outcome.",
        "A task type failing more than the others points to a shared cause (library, permission, source).",
        ("Fix shared causes once: cluster libraries, service principal grants, source connections.",),
    ),
    # ── SQL ──
    "sec_sql_perf": Guide(
        "Query count, latency and failures over time.",
        "Watch the P95 (the slow tail your users feel), not only the average.",
        (
            "Target a P95 under 10 s for dashboards.",
            "Look at failed queries first: often permissions or schema changes.",
        ),
    ),
    "sec_sql_queues": Guide(
        "Time queries waited for warehouse capacity.",
        "Waits over 10 s mean the warehouse is saturated at peak time.",
        (
            "Raise **max clusters** (scaling) on the busy warehouse.",
            "Separate ETL and BI on different warehouses.",
            "Move to serverless for faster scale-out.",
        ),
    ),
    "sec_sql_cache": Guide(
        "Result cache hits and disk spill.",
        "Cache hits are free and instant. A low rate often comes from non-deterministic functions or constantly changing tables.",
        (
            "Avoid `now()` / `current_timestamp()` in dashboard queries: they disable the result cache.",
            "Refresh dashboards on a schedule instead of on every view.",
            "For spill, see **⚡ Optimization → Spill**.",
        ),
    ),
    "sec_sql_user": Guide(
        "Query volume and latency by user.",
        "One user with a very high volume is often a tool polling too often.",
        (
            "Check the refresh interval of the tools used by the top users.",
            "Give heavy users a dedicated warehouse to protect the others.",
        ),
    ),
    "sec_sql_warehouses": Guide(
        "Query volume and settings per warehouse.",
        "Warehouses with few queries but a big size or a long auto-stop waste money.",
        (
            "Auto-stop 10 min (serverless: 5 min).",
            "Right-size: start small and scale out with max clusters.",
            "Delete warehouses unused for 30 days.",
        ),
    ),
    "sec_sql_statements": Guide(
        "Statement types (SELECT, INSERT, MERGE…) and their outcome.",
        "Many small INSERT/UPDATE on a warehouse = a row-by-row pattern.",
        (
            "Batch writes with `MERGE` or `COPY INTO`.",
            "Run heavy ETL in jobs, not on BI warehouses.",
        ),
    ),
    # ── Platform ──
    "sec_platform_api": Guide(
        "Live counts of clusters, warehouses and jobs from the Databricks API.",
        "Compare with what you expect: unknown resources = shadow usage.",
        (
            "Delete unused resources.",
            "Remove the *Unrestricted cluster creation* entitlement from users and give them a policy instead.",
        ),
    ),
    "sec_platform_ingestion": Guide(
        "Ingestion pipeline health, from an optional log table.",
        "Empty? Set `FINOPS_INGESTION_LOG_TABLE` in `app.yaml`.",
        ("Point `FINOPS_INGESTION_LOG_TABLE` to your ingestion log table to enable this view.",),
    ),
    "sec_platform_logs": Guide(
        "Sample driver logs, from an optional volume.",
        "Empty? Set `FINOPS_DRIVER_LOG_VOLUME` in `app.yaml`.",
        ("Enable cluster log delivery to a Unity Catalog volume, then set `FINOPS_DRIVER_LOG_VOLUME`.",),
    ),
}


def md_inline(text: str) -> str:
    """Escape, then render `code` and **bold**."""
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)


def render_intro(key: str | None) -> None:
    """One-line explanation under the section title."""
    guide = GUIDES.get(key or "")
    if guide is None:
        return
    st.markdown(f'<p class="section-intro">{md_inline(guide.what)}</p>', unsafe_allow_html=True)
