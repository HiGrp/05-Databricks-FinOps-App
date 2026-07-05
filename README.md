# FinOps Optimizer

**Track DBU spend and find cost savings on Databricks.**

FinOps Optimizer is a Streamlit app for platform and FinOps teams: monitor DBU consumption, spot waste, and prioritize optimization — plus security, jobs, compute, and SQL views powered by system tables.

## Features

| Area | What you get |
|------|----------------|
| **Overview** | DBU, queries, audit events, failed jobs, cluster and warehouse counts |
| **FinOps** | DBU trends, top spenders, team chargeback, SKU mix, monthly comparison |
| **Optimization** | Action plan, weekend clusters, failed jobs, slow SQL, spill, auto-stop |
| **Security** | Audit summary, access denied, Unity Catalog, secrets & tokens, sign-in |
| **Compute** | Cluster inventory, tags, DBR versions, events |
| **Jobs** | Run volume, success rates, duration, tasks |
| **SQL** | Query performance, queues, cache, warehouses |
| **Platform** | API inventory, ingestion health, driver logs (optional) |

## Requirements

- Databricks **Premium** or **Enterprise** workspace
- **System tables** enabled on the account
- A **SQL warehouse** (serverless recommended) with access to system tables
- **Unity Catalog** (recommended) for the catalog filter in the sidebar

## Deploy as a Databricks App

The app ships with `app.yaml` and `manifest.yaml` for Databricks Apps and Marketplace distribution.

At install time, the workspace admin binds:

- **SQL warehouse** → `DATABRICKS_WAREHOUSE_ID` (required)

Optional environment variables for extended views:

| Variable | Description |
|----------|-------------|
| `FINOPS_INGESTION_LOG_TABLE` | Delta table for ingestion logs (e.g. `catalog.schema.ingestion_runs`) |
| `FINOPS_CLUSTER_EVENTS_TABLE` | Delta table for cluster events |
| `FINOPS_DRIVER_LOG_VOLUME` | Unity Catalog volume path for driver logs |

## Local development

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Configure `~/.databrickscfg` or set `DATABRICKS_WAREHOUSE_ID` / `FINOPS_SQL_WAREHOUSE_ID` for SQL warehouse access.

### Dev mode (no Databricks needed)

Set `dev_mode = true` in `config.toml` (or `APP_DEV_MODE=1`) to run the whole app
against **local fake data** served by an in-memory DuckDB engine — no Databricks,
Docker, or database required. See [`docs/MODE_DEV.md`](docs/MODE_DEV.md).

### Licensing & free trial

The app can run free for a configurable number of days, then lock until a signed
license key is entered (offline, Ed25519). Configure in `config.toml` under
`[license]`. Vendor tooling to issue keys is in `tools/license_tool.py`.
See [`docs/LICENCE.md`](docs/LICENCE.md).

### Distributing without source code

To ship the app without exposing the Python source, obfuscate with PyArmor.
Step-by-step guide in [`docs/OBFUSCATION.md`](docs/OBFUSCATION.md).

For the full end-to-end packaging + licensing flow for multiple Databricks
customers, see [`INSTALL.md`](INSTALL.md).

## System tables used

The app queries Databricks system tables including (non-exhaustive):

- `system.billing.usage`
- `system.billing.list_prices`
- `system.access.audit`
- `system.query.history`
- `system.compute.clusters`
- `system.compute.warehouses`
- `system.lakeflow.job_run_timeline`
- `system.lakeflow.job_tasks`

See `dashboards/sql_tables.py` for the full view definitions and catalog adaptation logic.

## Repository layout

```
app.py                 # Streamlit entry point (+ license gate)
app.yaml               # Databricks App runtime config
manifest.yaml          # Marketplace / app manifest
config.toml            # dev_mode + license settings
app_config.py          # Config loader (config.toml + env overrides)
metadata/meta.yaml     # Listing metadata for Provider Console
dashboards/            # UI modules (FinOps, Security, etc.)
prod_data.py           # SQL warehouse & API access (routes to dev in dev mode)
dev_data/              # Local fake-data DuckDB engine (dev mode)
licensing.py           # Trial + license enforcement (public key only)
license_public_key.txt # Public key shipped with the app
tools/                 # Vendor-only license tooling (NOT distributed)
docs/                  # MODE_DEV / LICENCE / OBFUSCATION guides
requirements.txt       # Python dependencies
SECURITY.md            # Vulnerability reporting
```

## License

Set your license URL in the Marketplace Provider Console when publishing the listing.
