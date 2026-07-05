# Mode développement (données factices)

Le mode dev permet de lancer l'application **sans Databricks** : les requêtes SQL
sont exécutées sur un moteur **DuckDB en mémoire** alimenté par des données
factices déterministes (générées à partir du schéma `system`).

## Activer / désactiver

Dans `config.toml` :

```toml
[app]
dev_mode = true   # true = données factices | false = Databricks (prod)
```

## Lancer

```bash
pip install -r requirements.txt
streamlit run app.py
```

En mode dev, la licence est **automatiquement ignorée**

## Où sont les données ?

Les données sont construites en mémoire au démarrage par
`dev_data/fake_data.py` (seed fixe = jeu de données stable et reproductible).

Tables/vues exposées (mêmes noms locaux que la prod) : `billing_usage_full`,
`query_history_full`, `access_audit_parsed`, `compute_clusters_parsed`,
`compute_warehouses_parsed`, `job_run_timeline_parsed`, `job_tasks_parsed`,
`workspaces_latest`, `compute_node_timeline`, `compute_warehouse_events`,
`billing_list_prices`, etc.

### Inspecter les données (optionnel)

Pour exporter le jeu factice en fichiers Parquet et les regarder :

```bash
python -m dev_data.generate
# -> écrit dev_data/data/*.parquet (un fichier par table)
```

## Comment ça marche

- `app.py` → `prod_data.execute_sql(sql)`.
- Si `dev_mode` est actif, `execute_sql` route vers `dev_data.engine.execute_sql_dev`,
  qui exécute la requête **telle quelle** sur DuckDB.
- Le dialecte local des dashboards est déjà compatible DuckDB
  (`LEFT`, `strftime`, `quantile_cont`, `INTERVAL '1' DAY`…). Seuls `split()` et
  `get()` (fonctions Spark) sont recréés comme macros DuckDB dans l'engine.
- Les appels REST (page *Platform*) sont également simulés en mode dev.

## Ajuster le volume / la période

Dans `dev_data/fake_data.py` :

- `DAYS_BACK` : profondeur d'historique (défaut : 90 jours, se termine aujourd'hui).
- `SEED` : graine aléatoire (changez-la pour un autre jeu stable).
- Les listes `TEAMS`, `USERS`, `SKUS`, etc. pour personnaliser le contenu.
