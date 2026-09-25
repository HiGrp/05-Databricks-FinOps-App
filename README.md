# FinOps Optimizer

**How much is your Databricks wasting — and how do you fix it?**
Free, open-source Databricks App. Reads your `system` tables, shows spend and savings in money, with the fix for each item.

Powered by [HI Group](https://higroup.systems).

## Try demo (no Databricks)

```bash
pip install -r app/requirements.txt
streamlit run app/app.py
```

## Connect your workspace

1. Open the app → **🚀 Setup**
2. Fill in **Workspace URL**, **SQL warehouse ID**, **token** (or service principal)
3. Click **Connect**
4. Run the **GRANT** SQL (step 2)
5. **Run test** (step 3)

Done. Turn off **Demo data** in the sidebar if needed.

## Deploy on Databricks

```bash
databricks bundle deploy --var="warehouse_id=<WAREHOUSE_ID>"
databricks bundle run finops_optimizer
```

Connection is automatic. Run the GRANT SQL from Setup only.

## License

[MIT](LICENSE)
