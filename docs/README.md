# FinOps Optimizer — guide

App Streamlit Databricks (FinOps, system tables). Offline, sans serveur de licence.

**Prérequis :** Docker (build), Git Bash, Python 3.11+, workspace Premium/Enterprise avec system tables.

---

## 1. Dev local (sans Databricks)

```bash
pip install -r requirements.txt
```

Dans `config.toml` :

```toml
[app]
dev_mode = true
```

```bash
streamlit run app.py
```

→ Données factices DuckDB, licence ignorée.  
→ Prod locale Databricks : `dev_mode = false` + `DATABRICKS_WAREHOUSE_ID` configuré.

---

## 2. Build client (une fois + à chaque release)

**2.1 — Clés de signature (une seule fois)**

```bash
python tools/license_tool.py keygen
```

Garde `tools/license_private_key.txt` secret. Ne jamais le distribuer.

**2.2 — Compiler**

```bash
bash scripts/build-dist.sh
```

→ Produit le dossier `dist/` (IP en `.so` ; `app.py` + `streamlit_caches.py` restent en Python).  
→ Nécessite Docker (Ubuntu 22.04 / Python 3.11).

---

## 3. Distribuer chez le client

`dist/` est **versionné sur GitHub** — le client clone le repo (ou une release) et déploie :

```bash
databricks sync ./dist /Workspace/Users/<client>/finops-app
```

Crée ou mets à jour la **Databricks App** sur ce dossier. Lie un SQL warehouse.

⚠️ Utilise `databricks sync`, pas l'upload UI (risque sur les `.so`).

Après chaque release : `bash scripts/build-dist.sh` puis `git add dist/` + commit + push.

---

## 4. Émettre une clé licence

Durée trial par défaut : `config.toml` → `[license] trial_days` (ou env `APP_TRIAL_DAYS`).

Le client ouvre l'app → écran bloqué avec son **Workspace ID**. Il te l'envoie.

```bash
# Trial
python tools/license_tool.py issue --customer "Trial ACME" --trial --workspace-id <ID>

# Payant 1 an
python tools/license_tool.py issue --customer "ACME" --plan yearly --workspace-id <ID> --days 365
```

Envoie la clé au client → il la colle dans l'app → accès jusqu'à la date d'expiration.

La clé est liée au workspace : copie vers un autre workspace = refusée.

---

## 5. Variables optionnelles (prod)

| Variable | Rôle |
|----------|------|
| `DATABRICKS_WAREHOUSE_ID` | SQL warehouse (requis) |
| `FINOPS_INGESTION_LOG_TABLE` | Logs ingestion |
| `FINOPS_CLUSTER_EVENTS_TABLE` | Events clusters |
| `FINOPS_DRIVER_LOG_VOLUME` | Driver logs |

---

## Sécurité

Vulnérabilité → email contact éditeur (pas d'issue publique). Données restent dans le workspace client.
