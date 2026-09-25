# FinOps Optimizer

Free app that reads Databricks **system tables** and shows spend, waste, and what to fix.

Powered by [HI Group](https://higroup.systems).


<img width="1857" height="937" alt="Optim" src="https://github.com/user-attachments/assets/d1ae96e5-edef-4f3f-8bf0-6fa0ea6d8560" />
<img width="1918" height="937" alt="Home" src="https://github.com/user-attachments/assets/f331702b-8728-43ed-9dcd-ebe9825f6c4b" />
<img width="1228" height="625" alt="Cost" src="https://github.com/user-attachments/assets/049a4e09-4893-4fa4-aae1-3ae818a38a98" />
<img width="1245" height="631" alt="Compute" src="https://github.com/user-attachments/assets/030f9988-a9bb-4fc0-8c5f-40123596d70d" />
<img width="1254" height="631" alt="Security" src="https://github.com/user-attachments/assets/a98764ca-a7fc-4b32-a245-dee2c8a3f7ad" />


## Run it

From the project root:

```bash
pip install -r app/requirements.txt
streamlit run app/app.py
```

**Demo data** in the sidebar is off by default. Turn it on to browse with fake data and no Databricks account.

## Connect a workspace

Open **Setup**. Two steps:

1. **In the app** - workspace URL, SQL warehouse ID, then either:
   - **Access token** (your user), or
   - **Service principal** (client ID + secret)
2. **In Databricks** - SQL Editor, same warehouse, run the `GRANT` script shown on the page (metastore admin, once).

Click **Refresh** on any page after that.

On a **Databricks App**, the workspace connection is automatic. You still run the `GRANT` script. Attach a SQL warehouse with resource key `sql-warehouse` (`app/app.yaml`).

## What you see

Sidebar: **catalog** (default `system`), **period** (last 7 / 30 / 90 days, 12 months, or custom - always through yesterday), pages, **Demo data**.

| Page | What it shows |
|---|---|
| Home | Spend, avoidable cost, waste removed, health score, top actions |
| Action plan | Issues to fix, with owner and steps |
| FinOps | Cost, trends, SKUs, chargeback, prices |
| Optimization | Waste, slow SQL, failed jobs, auto-stop |
| Security | Audit, access denied, Unity Catalog, tokens |
| Compute | Clusters, tags, runtime, events |
| Jobs | Runs, success, duration, tasks |
| SQL | Query performance, queues, warehouses |
| Platform | API inventory, ingestion, driver logs |
| Setup | Connect + permissions |
