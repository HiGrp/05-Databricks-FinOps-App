# Obfuscation (distribuer sans livrer le code source)

Objectif : distribuer l'application **sans exposer le code Python lisible**.
L'outil recommandé est **PyArmor** — simple, éprouvé, et compatible avec un
lancement `streamlit run`.

> PyArmor transforme vos `.py` en modules protégés qui s'exécutent normalement
> mais ne sont pas lisibles. Le code source original n'est pas distribué.

## 1. Installer PyArmor

```bash
pip install pyarmor
```

## 2. Obfusquer le projet

Depuis la racine du projet (`05-my-databricks-app/`) :

```bash
pyarmor gen --recursive --output dist \
    app.py app_config.py prod_data.py licensing.py dashboards dev_data
```

- `--recursive` : inclut les sous-modules des dossiers `dashboards/` et `dev_data/`.
- `--output dist` : la version protégée est écrite dans `dist/`.

PyArmor crée dans `dist/` une copie obfusquée de vos fichiers + un dossier runtime
`pyarmor_runtime_*` nécessaire à l'exécution.

## 3. Compléter le paquet distribuable

Copiez à côté du code obfusqué les fichiers **non-code** requis à l'exécution :

```
dist/
├── app.py                    (obfusqué)
├── app_config.py             (obfusqué)
├── prod_data.py              (obfusqué)
├── licensing.py              (obfusqué)
├── dashboards/               (obfusqué)
├── dev_data/                 (obfusqué)
├── pyarmor_runtime_*/        (généré par PyArmor)
│
├── config.toml               ← à copier (dev_mode=false pour la prod)
├── license_public_key.txt    ← à copier (clé publique, non secrète)
├── requirements.txt          ← à copier
├── app.yaml                  ← à copier (Databricks App)
└── manifest.yaml             ← à copier
```

⚠️ **Ne jamais inclure** `tools/` (contient la clé privée de signature).
Le dossier `tools/` sert uniquement côté éditeur (voir `docs/LICENCE.md`).

## 4. Tester le paquet

```bash
cd dist
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- **Compatibilité version Python** : obfusquez avec la **même version majeure de
  Python** que celle de la cible (ex. Python 3.11 pour Databricks Apps).
- **Databricks Apps** : le point d'entrée reste `streamlit run app.py` (déjà
  défini dans `app.yaml`). Déployez le contenu de `dist/`.
- L'obfuscation protège aussi le secret d'intégrité de l'essai et complique la
  falsification, mais la **sécurité des licences repose sur la signature Ed25519**
  (clé privée jamais distribuée), pas sur l'obfuscation.
- Alternatives possibles : `Nuitka` (compilation en binaire) ou `Cython`, plus
  lourdes à mettre en place. PyArmor reste le plus simple pour ce cas.
