# FinOps Optimizer

App Streamlit Databricks (FinOps, system tables). Licence offline liée au workspace.

## 1. Dev local

```bash
pip install -r requirements.txt
```

`config.toml` → `dev_mode = true`, puis :

```bash
streamlit run app.py
```

Données DuckDB factices, pas de licence.

## 2. Clés licence (une fois)

```bash
python tools/license_tool.py keygen
```

Secret : `tools/license_private_key.txt` — ne jamais committer.

Trial : `config.toml` → `[license] trial_days = 7`

## 3. Build + push client

```bash
bash build.sh
git commit -m "Update dist"
git push
```

Produit et stage `dist/` (`.so` Linux + `app.py`). Docker requis.

## 4. Client déploie

Clone le repo, puis :

```bash
databricks sync ./dist /Workspace/Users/<client>/finops-app
```

Databricks App + SQL warehouse. **Pas d'upload UI** (corrompt les `.so`).

## 5. Clé pour le client

App bloquée → client t'envoie son **Workspace ID**.

```bash
python tools/license_tool.py issue --customer "Trial X" --trial --workspace-id <ID>
python tools/license_tool.py issue --customer "ACME" --plan yearly --workspace-id <ID> --days 365
```

Il colle la clé dans l'app.

## Variables prod (optionnel)

`DATABRICKS_WAREHOUSE_ID`, `FINOPS_INGESTION_LOG_TABLE`, `FINOPS_CLUSTER_EVENTS_TABLE`, `FINOPS_DRIVER_LOG_VOLUME`
