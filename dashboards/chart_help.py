"""Short hover help text — simple English for the whole app."""

from __future__ import annotations

import html


def info_tip_html(help_text: str) -> str:
    return (
        f'<span class="chart-info-tip" tabindex="0">'
        f'<span class="chart-info-icon">ⓘ</span>'
        f'<span class="chart-info-popup">{html.escape(help_text)}</span>'
        f"</span>"
    )


HELP = {
    # ── Categories (main page headers) ──
    "cat_home": "Quick view of cost, SQL, security, jobs, and compute for the selected period.",
    "cat_finops": "Track DBU usage, costs, chargeback, and top spenders.",
    "cat_optimization": "Find waste, slow SQL, failed jobs, and quick fixes.",
    "cat_security": "Audit logs, access denied events, Unity Catalog, and tokens.",
    "cat_compute": "Cluster inventory, tags, runtime versions, and events.",
    "cat_jobs": "Job run volume, success rate, duration, and tasks.",
    "cat_sql": "SQL query performance, queues, warehouses, and cache.",
    "cat_platform": "Live API inventory, ingestion logs, and driver log samples.",

    # ── Sidebar filters ──
    "filter_period_from": "First day included in all charts and KPIs.",
    "filter_period_to": "Last day included in all charts and KPIs.",
    "filter_catalog": "Unity Catalog that holds Databricks system tables.",
    "filter_trigramme": "Short workspace code from the workspace name. Leave empty for all.",
    "filter_environment": "Environment tag (dev, prod, etc.). Leave empty for all.",
    "filter_nav": "Jump to a dashboard section. The current page is highlighted.",

    # ── Section headers (category pages) ──
    "sec_finops_summary": "Monthly DBU totals and daily trend for the selected period.",
    "sec_finops_top_spenders": "Highest DBU use by cluster, job, warehouse, and user.",
    "sec_finops_trends": "Daily DBU split by Databricks product.",
    "sec_finops_team": "DBU grouped by team, cost center, and environment tags.",
    "sec_finops_monthly": "Total DBU per calendar month in the selected range.",
    "sec_finops_sku": "Top billing SKUs and usage types.",
    "sec_finops_storage": "DBU for storage and networking (not compute).",
    "sec_finops_prices": "Your DBU use compared to Databricks list prices.",

    "sec_opt_action": "Suggested fixes ranked by signals from your workspace data.",
    "sec_opt_weekend": "Clusters that ran on Saturday or Sunday — often idle waste.",
    "sec_opt_failed_jobs": "Job runs that failed, timed out, or were canceled.",
    "sec_opt_slow_sql": "Slowest finished SQL queries by total duration.",
    "sec_opt_spill": "Queries that wrote large amounts of data to disk.",
    "sec_opt_autostop": "Clusters without auto-termination keep billing when idle.",
    "sec_opt_node_usage": "Average CPU and memory use per cluster from node metrics.",
    "sec_opt_warehouse": "SQL warehouse scale-up and scale-down events.",

    "sec_sec_audit": "How many audit events happened and how they trend over time.",
    "sec_sec_denied": "403 access denied events — users blocked by permissions.",
    "sec_sec_top_users": "Users with the most actions in the audit log.",
    "sec_sec_heatmap": "Audit activity by service and day. Darker means more events.",
    "sec_sec_uc": "Unity Catalog actions like grants, creates, and deletes.",
    "sec_sec_secrets": "Events about secrets, personal access tokens, and IAM.",
    "sec_sec_signin": "Token logins and client IP addresses.",

    "sec_compute_list": "All clusters in the workspace with key settings.",
    "sec_compute_tags": "Team tags, security mode, and how clusters were created.",
    "sec_compute_runtime": "Databricks Runtime (DBR) versions and node types in use.",
    "sec_compute_events": "Cluster lifecycle events from API or Delta table.",

    "sec_jobs_overview": "Job run counts, success vs failure, and daily volume.",
    "sec_jobs_success": "Success rate per job — low bars need attention first.",
    "sec_jobs_duration": "Average run, queue, and execution time per job.",
    "sec_jobs_team": "Job runs grouped by team tag and result status.",
    "sec_jobs_tasks": "Individual tasks inside jobs, by type and result.",

    "sec_sql_perf": "Query counts, average latency, P95, and failures.",
    "sec_sql_queues": "Time queries waited because the warehouse was at capacity.",
    "sec_sql_cache": "Share of queries served from cache vs queries with spill.",
    "sec_sql_user": "SQL load and latency broken down by user.",
    "sec_sql_warehouses": "Query volume per warehouse and warehouse settings.",
    "sec_sql_statements": "SQL statement types (SELECT, INSERT, etc.) and status.",

    "sec_platform_api": "Live counts from the Databricks REST API (not billing).",
    "sec_platform_ingestion": "FinOps pipeline run logs from your ingestion table.",
    "sec_platform_logs": "Sample cluster driver log files from a Unity Volume.",

    "sec_summary": "Key numbers for this category in the selected date range.",

    "sec_home_kpis": "DBU, SQL queries, audit events, failed jobs, clusters, and warehouses.",
    "sec_home_cost": "Daily DBU trend and split by Databricks product.",
    "sec_home_activity": "Top audit services and job run outcomes.",

    # ── Charts ──
    "dbu_usage": "Daily Databricks Units (DBU) used. More DBU means higher cost.",
    "product_mix": "Share of DBU by Databricks product (Jobs, SQL, All-Purpose, etc.).",
    "top_audit_services": "Services with the most audit events. Helps spot busy or risky areas.",
    "job_run_status": "Job runs grouped by result: succeeded, failed, or canceled.",
    "daily_dbu_trend": "DBU used each day in the selected period.",
    "dbu_by_product": "Daily DBU split by product. Shows which product drives spend.",
    "top_skus": "Top billing SKUs by DBU. Useful to find expensive line items.",
    "usage_type_mix": "DBU split by usage type (compute, storage, etc.).",
    "dbu_by_team": "DBU tagged per team. Shows who consumes the most.",
    "dbu_by_env": "DBU split by environment tag (dev, prod, etc.).",
    "monthly_dbu": "Total DBU per month. Good for month-over-month trends.",
    "dbu_by_sku": "DBU per SKU for the selected period.",
    "storage_networking": "DBU for storage and networking only (not compute).",
    "top_clusters": "Clusters with the highest DBU spend.",
    "top_jobs": "Jobs with the highest DBU spend.",
    "top_warehouses": "SQL warehouses with the highest DBU spend.",
    "top_users": "Users (run_as) with the highest DBU spend.",
    "weekend_cluster_dbu": "DBU on weekends (Sat/Sun). High values may mean idle clusters.",
    "query_spill": "Queries that wrote a lot of data to disk (spill). Often means not enough memory.",
    "avg_cpu": "Average CPU use per cluster. Low values may mean oversized clusters.",
    "avg_memory": "Average memory use per cluster. Low values may mean waste.",
    "top_failed_jobs": "Jobs with the most failed, timed out, or canceled runs.",
    "warehouse_event_types": "SQL warehouse events (scale up, scale down, start, stop).",
    "warehouse_event_timeline": "Warehouse events per day. Shows scaling activity over time.",
    "cluster_events_daily": "Number of cluster lifecycle events per day.",
    "audit_daily": "Number of audit events per day.",
    "denied_by_service": "403 (access denied) events per service.",
    "uc_actions": "Unity Catalog actions (create, grant, delete, etc.).",
    "secrets_tokens": "Events about secrets, tokens, and IAM.",
    "login_by_ip": "Logins using a token, grouped by source IP.",
    "top_actors": "Users with the most audit actions.",
    "audit_heatmap": "Audit activity by service and date. Darker = more events.",
    "clusters_by_team": "Number of clusters per team tag.",
    "data_security_mode": "Clusters split by data security mode.",
    "cluster_source": "How clusters were created (UI, API, job, etc.).",
    "dbr_by_workspace": "Databricks Runtime (DBR) versions per workspace.",
    "node_types": "Driver node types used by clusters.",
    "runs_per_day": "Job runs per day in the selected period.",
    "success_rate": "Success rate per job. Lower bars need attention first.",
    "job_durations": "Average run, queue, and execution time per job (seconds).",
    "tasks_hierarchy": "Tasks split by type and result status.",
    "runs_by_team": "Job runs per team tag, colored by result.",
    "daily_latency": "Average SQL query time per day (milliseconds).",
    "warehouse_queue": "Average time queries waited for warehouse capacity.",
    "queries_by_user": "Number of SQL queries per user.",
    "latency_by_user": "Average query time per user.",
    "statements_by_type": "SQL statements by type and status.",
    "queries_by_warehouse": "Query count per SQL warehouse.",
    "cache_rate": "Daily share of queries served from result cache (%).",

    # ── KPI metrics (metrics_row & inline) ──
    "kpi_dbu_month": "DBU used since the start of the current calendar month.",
    "kpi_dbu_last_month": "DBU used during the previous full calendar month.",
    "kpi_savings_est": "Rough estimate if you cut compute waste by about 20%.",
    "kpi_job_runs": "Total job runs started in the selected period.",
    "kpi_job_success": "Runs that finished with SUCCEEDED status.",
    "kpi_job_failed": "Runs that finished with FAILED status.",
    "kpi_job_avg_duration": "Average wall-clock time per run, in minutes.",
    "kpi_audit_events": "All rows in the audit log for the selected period.",
    "kpi_audit_users": "Distinct user emails seen in the audit log.",
    "kpi_audit_errors": "Audit events with HTTP 4xx or 5xx status codes.",
    "kpi_sql_queries": "SQL statements executed in the selected period.",
    "kpi_sql_avg_latency": "Mean query duration in milliseconds.",
    "kpi_sql_p95": "95th percentile query duration — slow outlier queries.",
    "kpi_sql_failed": "Queries that did not finish successfully.",
    "kpi_cache_total": "All SQL queries in the period.",
    "kpi_cache_hits": "Queries answered from the result cache (faster, no recompute).",
    "kpi_cache_spill": "Queries that spilled data from memory to disk.",
    "kpi_clusters_total": "Interactive clusters in the workspace right now.",
    "kpi_clusters_photon": "Clusters using the Photon acceleration engine.",
    "kpi_clusters_single": "Single-node clusters (zero workers).",
    "kpi_autostop_total": "All clusters in the inventory table.",
    "kpi_autostop_none": "Clusters set to never auto-terminate (0 minutes).",
    "kpi_autostop_short": "Clusters that stop after 20 minutes or less of idle time.",
    "kpi_api_clusters": "Clusters returned by the live Clusters API.",
    "kpi_api_warehouses": "SQL warehouses returned by the live Warehouses API.",
    "kpi_api_jobs": "Jobs returned by the live Jobs API.",
    "kpi_ingestion_rows": "Rows in the ingestion log table.",
    "kpi_ingestion_cols": "Number of columns in the ingestion log.",
    "kpi_log_warnings": "Lines containing WARN, ERROR, or OOM in the log sample.",

    # ── Data tables ──
    "tbl_weekend_clusters": "Weekend clusters with names and auto-stop settings.",
    "tbl_slow_sql": "Slowest queries with user, duration, bytes read, and preview text.",
    "tbl_spill_queries": "Queries with high disk spill and a short preview.",
    "tbl_autostop": "Cluster auto-termination settings. Zero means never stops.",
    "tbl_job_failures": "All job run results grouped by job name and status.",
    "tbl_team_attribution": "DBU detail by team, cost center, and environment.",
    "tbl_monthly_dbu": "Raw monthly DBU totals for export or drill-down.",
    "tbl_list_prices": "Databricks list prices per SKU from billing metadata.",
    "tbl_job_success": "Per-job run counts and success percentage.",
    "tbl_job_tasks": "Task counts by type and result status.",
    "tbl_denied_events": "Recent 403 events with user, service, and error message.",
    "tbl_uc_recent": "Latest Unity Catalog audit events with request details.",
    "tbl_secrets_events": "Recent secrets, token, and IAM audit events.",
    "tbl_user_agents": "Most common HTTP user-agent strings in the audit log.",
    "tbl_top_actors": "Users ranked by audit actions and error count.",
    "tbl_queue_waits": "Queries that waited over 60 seconds for warehouse capacity.",
    "tbl_warehouses": "SQL warehouse size, state, and serverless setting.",
    "tbl_cluster_list": "Full cluster inventory with owner, nodes, and security mode.",
    "tbl_cluster_events": "Raw cluster event rows (start, stop, resize, etc.).",
    "tbl_api_clusters": "Cluster objects from the REST API response.",
    "tbl_api_warehouses": "Warehouse objects from the REST API response.",
    "tbl_api_jobs": "Job id and name from the REST API response.",
    "tbl_ingestion_log": "Latest ingestion pipeline log entries.",
    "tbl_action_plan": "Recommended actions with effort level and supporting signal.",
    "tbl_log_file": "Choose which driver log file to inspect.",

    # ── Page context ──
    "ctx_period": "Date range applied to all charts. Change it in the sidebar.",
    "ctx_refresh": "Clear cached queries and reload all data (cache lasts 5 minutes).",
}

CAT_HELP = {
    "Home": HELP["cat_home"],
    "FinOps": HELP["cat_finops"],
    "Optimization": HELP["cat_optimization"],
    "Security": HELP["cat_security"],
    "Compute": HELP["cat_compute"],
    "Jobs": HELP["cat_jobs"],
    "SQL": HELP["cat_sql"],
    "Platform": HELP["cat_platform"],
}
