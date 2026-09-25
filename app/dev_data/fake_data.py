"""Deterministic fake data mirroring the Databricks ``system`` catalog.

The frames returned here match the *local* view/table names the dashboards
query (see ``dashboards/sql_tables.py``): ``billing_usage_full``,
``query_history_full``, ``access_audit_parsed``, ``compute_clusters``, etc.

Everything is seeded, so the generated dataset is stable across runs (handy for
screenshots and demos). Regenerate on-disk copies with ``python -m dev_data.generate``.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

SEED = 42
DAYS_BACK = 90  # history depth, ending today (so "yesterday" default filter has data)

ACCOUNT_ID = "acct-11111111-2222-3333-4444-555555555555"
CLOUD = "AZURE"
CURRENCY = "USD"

TRIGRAMMES = ["ABC", "XYZ", "DAT", "FIN"]
ENVIRONMENTS = ["DEV", "UAT", "PRD"]
TEAMS = ["Data Platform", "Analytics", "ML", "Finance", "Marketing"]
COST_CENTERS = ["CC-1001", "CC-1002", "CC-1003", "CC-2001", "CC-3005"]
USERS = [
    "alice@acme.com", "bob@acme.com", "carol@acme.com", "dan@acme.com",
    "erin@acme.com", "frank@acme.com", "grace@acme.com", "heidi@acme.com",
]
NODE_TYPES = ["Standard_DS3_v2", "Standard_DS4_v2", "Standard_E8s_v3", "Standard_F16s_v2"]
DBR_VERSIONS = ["13.3.x-scala2.12", "14.3.x-scala2.12", "15.4.x-scala2.12", "16.1.x-scala2.12"]
SECURITY_MODES = ["SINGLE_USER", "USER_ISOLATION", "NONE"]
CLUSTER_SOURCES = ["UI", "API", "JOB"]
SKUS = [
    ("PREMIUM_ALL_PURPOSE_COMPUTE", "COMPUTE_TIME", "DBU"),
    ("PREMIUM_JOBS_COMPUTE", "COMPUTE_TIME", "DBU"),
    ("PREMIUM_SQL_COMPUTE", "COMPUTE_TIME", "DBU"),
    ("PREMIUM_SERVERLESS_SQL", "COMPUTE_TIME", "DBU"),
    ("PREMIUM_STORAGE", "STORAGE_SPACE", "GB"),
    ("PREMIUM_NETWORKING", "NETWORK_BYTES", "GB"),
]
PRODUCTS = ["ALL_PURPOSE", "JOBS", "SQL", "SERVERLESS_SQL", "STORAGE", "NETWORKING"]
SERVICES = ["unityCatalog", "clusters", "jobs", "sqlAnalytics", "secrets", "accounts", "iam", "notebook"]
ACTIONS = {
    "unityCatalog": ["getTable", "createTable", "grantPermission", "deleteTable", "updateMetastore"],
    "clusters": ["create", "start", "delete", "resize"],
    "jobs": ["runNow", "create", "update", "cancel"],
    "sqlAnalytics": ["executeQuery", "createWarehouse", "stopWarehouse"],
    "secrets": ["getSecret", "putSecret", "deleteSecret"],
    "accounts": ["tokenLogin", "logout", "aadBrowserLogin"],
    "iam": ["add", "removeMember", "updateRole"],
    "notebook": ["runCommand", "attachNotebook", "export"],
}
RESULT_STATES = ["SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "SUCCEEDED", "FAILED", "TIMEDOUT", "CANCELED"]
STMT_TYPES = ["SELECT", "SELECT", "SELECT", "INSERT", "UPDATE", "DELETE", "OPTIMIZE", "MERGE"]
TASK_TYPES = ["notebook_task", "python_task", "sql_task", "dlt_pipeline", "spark_jar_task"]


def _rng():
    return np.random.default_rng(SEED)


def _dates() -> list[date]:
    today = date.today()
    return [today - timedelta(days=i) for i in range(DAYS_BACK, -1, -1)]


def _ts(d: date, rng) -> datetime:
    return datetime.combine(d, time(0)) + timedelta(seconds=int(rng.integers(0, 86400)))


# --------------------------------------------------------------------------- #
# Reference dimensions
# --------------------------------------------------------------------------- #

def _build_workspaces(rng) -> pd.DataFrame:
    rows = []
    wid = 100000000000001
    for tri in TRIGRAMMES:
        for env in ENVIRONMENTS:
            name = f"prod-dbx-eu-west-1-{tri}-{env}"
            rows.append({
                "account_id": ACCOUNT_ID,
                "workspace_id": str(wid),
                "workspace_name": name,
                "workspace_url": f"https://{name}.azuredatabricks.net",
                "create_time": datetime(2023, 1, 1) + timedelta(days=int(rng.integers(0, 400))),
                "status": "RUNNING",
            })
            wid += 1
    return pd.DataFrame(rows)


def _build_clusters(rng, workspace_ids) -> pd.DataFrame:
    rows = []
    for i in range(24):
        source = CLUSTER_SOURCES[int(rng.integers(0, len(CLUSTER_SOURCES)))]
        team = TEAMS[int(rng.integers(0, len(TEAMS)))]
        env = ENVIRONMENTS[int(rng.integers(0, len(ENVIRONMENTS)))]
        auto_term = int(rng.choice([0, 10, 15, 20, 30, 60, 120]))
        change = datetime(2024, 1, 1) + timedelta(days=int(rng.integers(0, 700)))
        rows.append({
            "account_id": ACCOUNT_ID,
            "workspace_id": str(rng.choice(workspace_ids)),
            "cluster_id": f"0{100 + i}-{rng.integers(100000, 999999)}-abc{i:03d}",
            "cluster_name": f"{team.split()[0].lower()}-{env.lower()}-cluster-{i:02d}",
            "owned_by": USERS[int(rng.integers(0, len(USERS)))],
            "create_time": change - timedelta(days=int(rng.integers(1, 200))),
            "delete_time": pd.NaT,
            "driver_node_type": NODE_TYPES[int(rng.integers(0, len(NODE_TYPES)))],
            "worker_node_type": NODE_TYPES[int(rng.integers(0, len(NODE_TYPES)))],
            "worker_count": int(rng.choice([0, 2, 4, 8, 16])),
            "auto_termination_minutes": auto_term,
            "data_security_mode": SECURITY_MODES[int(rng.integers(0, len(SECURITY_MODES)))],
            "cluster_source": source,
            "dbr_version": DBR_VERSIONS[int(rng.integers(0, len(DBR_VERSIONS)))],
            "change_time": change,
            "change_date": change.date(),
            "policy_id": f"POL-{rng.integers(1000, 9999)}",
            "team": team,
            "environment": env,
            "runtime_engine": str(rng.choice(["PHOTON", "STANDARD"])),
        })
    return pd.DataFrame(rows)


def _build_warehouses(rng, workspace_ids) -> pd.DataFrame:
    sizes = ["2X_SMALL", "X_SMALL", "SMALL", "MEDIUM", "LARGE"]
    types = ["PRO", "CLASSIC", "SERVERLESS"]
    states = ["RUNNING", "STOPPED", "STARTING"]
    rows = []
    for i in range(8):
        change = datetime(2024, 1, 1) + timedelta(days=int(rng.integers(0, 700)))
        rows.append({
            "account_id": ACCOUNT_ID,
            "workspace_id": str(rng.choice(workspace_ids)),
            "warehouse_id": f"wh-{1000 + i}",
            "warehouse_name": f"sql-warehouse-{i:02d}",
            "warehouse_type": types[int(rng.integers(0, len(types)))],
            "warehouse_channel": "CURRENT",
            "warehouse_size": sizes[int(rng.integers(0, len(sizes)))],
            "min_clusters": 1,
            "max_clusters": int(rng.choice([1, 2, 4, 8])),
            "auto_stop_minutes": int(rng.choice([5, 10, 30, 60])),
            "change_time": change,
            "delete_time": pd.NaT,
            "created_by": USERS[int(rng.integers(0, len(USERS)))],
            "state": states[int(rng.integers(0, len(states)))],
        })
    return pd.DataFrame(rows)


def _build_jobs(rng, workspace_ids) -> list[dict]:
    jobs = []
    for i in range(16):
        team = TEAMS[int(rng.integers(0, len(TEAMS)))]
        jobs.append({
            "job_id": str(rng.integers(100000, 999999)),
            "job_name": f"{team.split()[0].lower()}_pipeline_{i:02d}",
            "team": team,
            "workspace_id": str(rng.choice(workspace_ids)),
        })
    return jobs


# --------------------------------------------------------------------------- #
# Fact tables
# --------------------------------------------------------------------------- #

def _build_billing(rng, clusters, warehouses, jobs, dates) -> pd.DataFrame:
    rows = []
    rid = 0
    non_job_clusters = clusters[clusters["cluster_source"] != "JOB"].to_dict("records")
    wh_records = warehouses.to_dict("records")
    for d in dates:
        n = int(rng.integers(30, 55))
        for _ in range(n):
            sku, usage_type, unit = SKUS[int(rng.integers(0, len(SKUS)))]
            product = {
                "PREMIUM_ALL_PURPOSE_COMPUTE": "ALL_PURPOSE",
                "PREMIUM_JOBS_COMPUTE": "JOBS",
                "PREMIUM_SQL_COMPUTE": "SQL",
                "PREMIUM_SERVERLESS_SQL": "SERVERLESS_SQL",
                "PREMIUM_STORAGE": "STORAGE",
                "PREMIUM_NETWORKING": "NETWORKING",
            }[sku]

            cluster_id = warehouse_id = job_id = None
            cluster_name = warehouse_name = job_name = node_type = None
            run_as = None
            team = TEAMS[int(rng.integers(0, len(TEAMS)))]
            env = ENVIRONMENTS[int(rng.integers(0, len(ENVIRONMENTS)))]

            if product in ("ALL_PURPOSE",):
                c = non_job_clusters[int(rng.integers(0, len(non_job_clusters)))]
                cluster_id, cluster_name = c["cluster_id"], c["cluster_name"]
                node_type = c["driver_node_type"]
                team, env = c["team"], c["environment"]
                run_as = c["owned_by"]
                # ~25% of all-purpose usage comes from jobs scheduled on interactive clusters.
                if rng.random() < 0.25:
                    j = jobs[int(rng.integers(0, len(jobs)))]
                    job_id, job_name = j["job_id"], j["job_name"]
            elif product == "JOBS":
                j = jobs[int(rng.integers(0, len(jobs)))]
                job_id, job_name = j["job_id"], j["job_name"]
                team = j["team"]
                run_as = USERS[int(rng.integers(0, len(USERS)))]
            elif product in ("SQL", "SERVERLESS_SQL"):
                w = wh_records[int(rng.integers(0, len(wh_records)))]
                warehouse_id, warehouse_name = w["warehouse_id"], w["warehouse_name"]
                run_as = USERS[int(rng.integers(0, len(USERS)))]

            base = {"ALL_PURPOSE": 40, "JOBS": 25, "SQL": 18, "SERVERLESS_SQL": 12,
                    "STORAGE": 3, "NETWORKING": 1}[product]
            qty = float(abs(rng.normal(base, base * 0.4)) + 0.1)
            start = _ts(d, rng)

            # ~12% of usage has no cost-allocation tags (untagged / non chargeable).
            untagged = bool(rng.random() < 0.12)
            row_team = None if untagged else team
            row_cost_center = None if untagged else COST_CENTERS[int(rng.integers(0, len(COST_CENTERS)))]
            rows.append({
                "record_id": f"rec-{rid:08d}",
                "account_id": ACCOUNT_ID,
                "workspace_id": str(rng.choice([j["workspace_id"] for j in jobs])),
                "sku_name": sku,
                "cloud": CLOUD,
                "usage_start_time": start,
                "usage_end_time": start + timedelta(hours=1),
                "usage_date": d,
                "usage_unit": unit,
                "usage_quantity": round(qty, 4),
                "billing_origin_product": product,
                "usage_type": usage_type,
                "team": row_team,
                "environment": env,
                "cost_center": row_cost_center,
                "owner": run_as,
                "cluster_id": cluster_id,
                "warehouse_id": warehouse_id,
                "job_id": job_id,
                "node_type": node_type,
                "cluster_name": cluster_name,
                "warehouse_name": warehouse_name,
                "job_name": job_name,
                "run_as": run_as,
                "record_type": "ORIGINAL",
                "ingestion_date": d,
            })
            rid += 1
    return pd.DataFrame(rows)


def _build_query_history(rng, warehouses, dates) -> pd.DataFrame:
    rows = []
    wh_records = warehouses.to_dict("records")
    stmt_samples = [
        "SELECT * FROM sales.orders WHERE order_date > '2024-01-01'",
        "INSERT INTO gold.kpi SELECT * FROM silver.events",
        "MERGE INTO dim_customer USING staging ON ...",
        "OPTIMIZE bronze.raw_events ZORDER BY (event_time)",
        "SELECT country, SUM(amount) FROM fct_sales GROUP BY 1",
        "UPDATE inventory SET qty = qty - 1 WHERE sku = 'X'",
        "DELETE FROM tmp.scratch WHERE created < current_date - 7",
    ]
    sid = 0
    for d in dates:
        n = int(rng.integers(40, 70))
        for _ in range(n):
            status = "FINISHED" if rng.random() > 0.08 else "FAILED"
            stmt_type = STMT_TYPES[int(rng.integers(0, len(STMT_TYPES)))]
            w = wh_records[int(rng.integers(0, len(wh_records)))]
            total = int(abs(rng.normal(8000, 12000)) + 50)
            waiting_cap = int(max(0, rng.normal(2000, 8000)))
            exec_ms = int(total * rng.uniform(0.5, 0.9))
            comp_ms = int(total * rng.uniform(0.02, 0.1))
            spill = int(rng.choice([0, 0, 0, 0, 2e8, 1.2e9, 6e9], p=[0.5, 0.15, 0.1, 0.08, 0.08, 0.06, 0.03]))
            start = _ts(d, rng)
            rows.append({
                "statement_id": f"stmt-{sid:08d}",
                "session_id": f"sess-{rng.integers(1, 400)}",
                "executed_by": USERS[int(rng.integers(0, len(USERS)))],
                "execution_status": status,
                "statement_type": stmt_type,
                "statement_text": stmt_samples[int(rng.integers(0, len(stmt_samples)))],
                "total_duration_ms": total,
                "execution_duration_ms": exec_ms,
                "compilation_duration_ms": comp_ms,
                "waiting_at_capacity_duration_ms": waiting_cap,
                "waiting_for_compute_duration_ms": int(max(0, rng.normal(500, 1500))),
                "start_time": start,
                "end_time": start + timedelta(milliseconds=total),
                "read_rows": int(abs(rng.normal(1e5, 5e5))),
                "produced_rows": int(abs(rng.normal(1e3, 5e3))),
                "read_bytes": int(abs(rng.normal(5e8, 2e9))),
                "written_bytes": int(abs(rng.normal(1e7, 5e7))),
                "spilled_local_bytes": spill,
                "shuffle_read_bytes": int(abs(rng.normal(1e8, 5e8))),
                "from_result_cache": bool(rng.random() < 0.22),
                "warehouse_id": w["warehouse_id"],
                "warehouse_name": w["warehouse_name"],
                "team": TEAMS[int(rng.integers(0, len(TEAMS)))],
                "workload": None,
                "account_id": ACCOUNT_ID,
                "workspace_id": w["workspace_id"],
            })
            sid += 1
    return pd.DataFrame(rows)


def _build_audit(rng, workspace_ids, dates) -> pd.DataFrame:
    rows = []
    ips = [f"10.0.{rng.integers(0, 255)}.{rng.integers(1, 254)}" for _ in range(15)]
    agents = ["Mozilla/5.0", "databricks-sdk-py/0.20", "Apache-HttpClient/4.5", "python-requests/2.31"]
    eid = 0
    for d in dates:
        n = int(rng.integers(45, 80))
        for _ in range(n):
            svc = SERVICES[int(rng.integers(0, len(SERVICES)))]
            action = ACTIONS[svc][int(rng.integers(0, len(ACTIONS[svc])))]
            roll = rng.random()
            status = 200 if roll > 0.2 else (403 if roll > 0.08 else 500)
            ts = _ts(d, rng)
            rows.append({
                "account_id": ACCOUNT_ID,
                "workspace_id": str(rng.choice(workspace_ids)),
                "version": "2.0",
                "event_time": ts,
                "event_date": d,
                "event_ts": ts,
                "event_dt": d,
                "source_ip_address": ips[int(rng.integers(0, len(ips)))],
                "user_agent": agents[int(rng.integers(0, len(agents)))],
                "session_id": f"sess-{rng.integers(1, 900)}",
                "service_name": svc,
                "action_name": action,
                "request_id": f"req-{eid:08d}",
                "request_params": '{"path": "/api/2.1/...", "scope": "workspace"}',
                "status_code": status,
                "error_message": None if status == 200 else ("Permission denied" if status == 403 else "Internal error"),
                "user_email": USERS[int(rng.integers(0, len(USERS)))],
                "audit_level": "WORKSPACE_LEVEL",
                "event_id": f"evt-{eid:08d}",
            })
            eid += 1
    return pd.DataFrame(rows)


def _build_job_runs(rng, jobs, dates) -> pd.DataFrame:
    rows = []
    run = 0
    for d in dates:
        n = int(rng.integers(20, 40))
        for _ in range(n):
            j = jobs[int(rng.integers(0, len(jobs)))]
            state = RESULT_STATES[int(rng.integers(0, len(RESULT_STATES)))]
            start = _ts(d, rng)
            run_ms = int(abs(rng.normal(180000, 240000)) + 5000)
            queue_ms = int(max(0, rng.normal(15000, 30000)))
            exec_ms = int(run_ms * rng.uniform(0.7, 0.95))
            rows.append({
                "account_id": ACCOUNT_ID,
                "workspace_id": j["workspace_id"],
                "job_id": j["job_id"],
                "run_id": f"run-{run:08d}",
                "period_start_time": start,
                "period_end_time": start + timedelta(milliseconds=run_ms),
                "start_ts": start,
                "end_ts": start + timedelta(milliseconds=run_ms),
                "trigger_type": str(rng.choice(["SCHEDULED", "MANUAL", "CONTINUOUS"])),
                "result_state": state,
                "run_type": "JOB_RUN",
                "run_name": j["job_name"],
                "job_name": j["job_name"],
                "run_duration_ms": run_ms,
                "queue_duration_ms": queue_ms,
                "execution_duration_ms": exec_ms,
                "team": j["team"],
                "termination_code": "SUCCESS" if state == "SUCCEEDED" else "USER_ERROR",
            })
            run += 1
    return pd.DataFrame(rows)


def _build_job_tasks(rng, job_runs) -> pd.DataFrame:
    rows = []
    for r in job_runs.to_dict("records"):
        for _ in range(int(rng.integers(1, 4))):
            state = r["result_state"] if rng.random() > 0.2 else RESULT_STATES[int(rng.integers(0, len(RESULT_STATES)))]
            tkey = TASK_TYPES[int(rng.integers(0, len(TASK_TYPES)))]
            rows.append({
                "account_id": ACCOUNT_ID,
                "workspace_id": r["workspace_id"],
                "job_id": r["job_id"],
                "run_id": r["run_id"],
                "period_start_time": r["period_start_time"],
                "period_end_time": r["period_end_time"],
                "start_ts": r["start_ts"],
                "end_ts": r["end_ts"],
                "task_key": tkey,
                "task_type": tkey,
                "result_state": state,
            })
    return pd.DataFrame(rows)


def _build_node_timeline(rng, clusters, dates) -> pd.DataFrame:
    rows = []
    recent = dates[-30:]
    cl = clusters.to_dict("records")
    for d in recent:
        for c in cl:
            for _ in range(2):
                start = _ts(d, rng)
                cpu_u = float(min(100, abs(rng.normal(35, 20))))
                cpu_s = float(min(100 - cpu_u, abs(rng.normal(10, 6))))
                rows.append({
                    "account_id": ACCOUNT_ID,
                    "workspace_id": c["workspace_id"],
                    "cluster_id": c["cluster_id"],
                    "instance_id": f"inst-{rng.integers(10000, 99999)}",
                    "start_time": start,
                    "end_time": start + timedelta(minutes=15),
                    "driver": bool(rng.random() < 0.2),
                    "cpu_user_percent": round(cpu_u, 1),
                    "cpu_system_percent": round(cpu_s, 1),
                    "cpu_wait_percent": round(float(abs(rng.normal(3, 2))), 1),
                    "mem_used_percent": round(float(min(100, abs(rng.normal(55, 22)))), 1),
                    "mem_swap_percent": round(float(abs(rng.normal(2, 2))), 1),
                    "network_sent_bytes": int(abs(rng.normal(1e7, 5e6))),
                    "network_received_bytes": int(abs(rng.normal(1e7, 5e6))),
                    "node_type": c["driver_node_type"],
                    "private_ip": f"10.1.{rng.integers(0, 255)}.{rng.integers(1, 254)}",
                })
    return pd.DataFrame(rows)


def _build_warehouse_events(rng, warehouses, dates) -> pd.DataFrame:
    rows = []
    types = ["STARTING", "RUNNING", "SCALED_UP", "SCALED_DOWN", "STOPPING", "STOPPED"]
    wh = warehouses.to_dict("records")
    for d in dates:
        n = int(rng.integers(5, 14))
        for _ in range(n):
            w = wh[int(rng.integers(0, len(wh)))]
            rows.append({
                "account_id": ACCOUNT_ID,
                "workspace_id": w["workspace_id"],
                "warehouse_id": w["warehouse_id"],
                "event_type": types[int(rng.integers(0, len(types)))],
                "cluster_count": int(rng.integers(1, 5)),
                "event_time": _ts(d, rng),
            })
    return pd.DataFrame(rows)


LIST_PRICES = {
    "PREMIUM_ALL_PURPOSE_COMPUTE": 0.55,
    "PREMIUM_JOBS_COMPUTE": 0.30,
    "PREMIUM_SQL_COMPUTE": 0.22,
    "PREMIUM_SERVERLESS_SQL": 0.70,
    "PREMIUM_STORAGE": 0.023,
    "PREMIUM_NETWORKING": 0.01,
}


def _build_list_prices(rng) -> pd.DataFrame:
    """Two price rows per SKU (a price change 45 days ago), like the real price history."""
    change = datetime.combine(date.today() - timedelta(days=45), time(0))
    rows = []
    for sku, _usage_type, unit in SKUS:
        price = LIST_PRICES[sku]
        for start, end, value in (
            (datetime(2024, 1, 1), change, round(price * 1.1, 4)),
            (change, pd.NaT, price),
        ):
            rows.append({
                "account_id": ACCOUNT_ID,
                "price_start_time": start,
                "price_end_time": end,
                "sku_name": sku,
                "cloud": CLOUD,
                "currency_code": CURRENCY,
                "usage_unit": unit,
                "pricing": f'{{"default": {value}}}',
            })
    return pd.DataFrame(rows)


def build_frames() -> dict[str, pd.DataFrame]:
    """Return every base table + enriched relation keyed by its local name."""
    rng = _rng()
    workspaces = _build_workspaces(rng)
    workspace_ids = workspaces["workspace_id"].tolist()

    clusters = _build_clusters(rng, workspace_ids)
    warehouses = _build_warehouses(rng, workspace_ids)
    jobs = _build_jobs(rng, workspace_ids)
    dates = _dates()

    billing = _build_billing(rng, clusters, warehouses, jobs, dates)
    query_history = _build_query_history(rng, warehouses, dates)
    audit = _build_audit(rng, workspace_ids, dates)
    job_runs = _build_job_runs(rng, jobs, dates)
    job_tasks = _build_job_tasks(rng, job_runs)
    node_timeline = _build_node_timeline(rng, clusters, dates)
    warehouse_events = _build_warehouse_events(rng, warehouses, dates)
    list_prices = _build_list_prices(rng)

    return {
        "workspaces_latest": workspaces,
        "compute_clusters": clusters,
        "compute_warehouses": warehouses,
        "compute_node_timeline": node_timeline,
        "compute_warehouse_events": warehouse_events,
        "billing_list_prices": list_prices,
        "billing_usage_full": billing,
        "query_history_full": query_history,
        "access_audit_parsed": audit,
        "job_run_timeline_parsed": job_runs,
        "job_tasks_parsed": job_tasks,
    }
