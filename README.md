# FinOps Optimizer

App Streamlit Databricks (FinOps, system tables). Licence offline.

## 1. Dev local

```bash
pip install -r requirements.txt
```

`config.toml` → `dev_mode = true`, puis :

```bash
streamlit run app.py
```

## 2. Clés licence (une fois, chez toi)

```bash
python tools/license_tool.py keygen
```

Secret : `tools/license_private_key.txt` — ne jamais committer.

Durée essai auto (sans clé) : `config.toml` → `[license] trial_days = 7`

## 3. Build + push client

```bash
bash build.sh
git add .
git commit -m "Update dist"
git push
```

## 4. Client déploie

```bash
export DATABRICKS_HOST="https://adb-7405611146197933.13.azuredatabricks.net"
export DATABRICKS_TOKEN="dapi677c294ebda4035d303a86c136c5dd26-2"
export MSYS_NO_PATHCONV=1

databricks sync ./dist /Users/issame.hamaoui@hi-group.fr/finops-app --full
```

Databricks App + SQL warehouse. Pas d'upload UI.

## 5. Licence

**Auto :** le client déploie → essai `trial_days` jours, sans clé, sans te contacter.

**Payant :** après l'essai, tu émets une clé :

```bash
python tools/license_tool.py issue --customer "ACME" --plan yearly --days 365
```

Le client la colle dans la sidebar. Pas de lien workspace.

## Variables prod (optionnel)

`DATABRICKS_WAREHOUSE_ID`, `FINOPS_INGESTION_LOG_TABLE`, `FINOPS_CLUSTER_EVENTS_TABLE`, `FINOPS_DRIVER_LOG_VOLUME`
