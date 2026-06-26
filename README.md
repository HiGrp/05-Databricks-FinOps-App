# Audit Databricks

Application Streamlit multi-dashboards (FinOps, Optimisation, Sécurité, Compute, Jobs, SQL, Plateforme).

## Lancement

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Prérequis :
- App déployée sur **Databricks** (Apps / notebook) **ou** machine locale avec `~/.databrickscfg` configuré
- **System tables** activées sur le compte
- Accès à un **SQL Warehouse** (serverless recommandé)

Variables d'environnement optionnelles :

| Variable | Description |
|----------|-------------|
| `FINOPS_SQL_WAREHOUSE_ID` | ID warehouse SQL à utiliser |
| `FINOPS_INGESTION_LOG_TABLE` | Table Delta logs ingestion (ex. `catalog.schema.ingestion_runs`) |
| `FINOPS_CLUSTER_EVENTS_TABLE` | Table Delta événements cluster |
| `FINOPS_DRIVER_LOG_VOLUME` | Chemin Volume logs driver (ex. `/Volumes/catalog/schema/logs`) |

En production, les requêtes SQL ciblent directement les **system tables** Databricks (`system.billing.usage`, `system.query.history`, etc.).
