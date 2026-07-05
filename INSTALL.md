# Installation & distribution (multi-clients)

Guide court pour distribuer l'app à plusieurs clients ayant leur propre workspace
Databricks, **sans livrer le code source** et avec **licence + essai gratuit**.

> Il y a **2 rôles** :
> - **ÉDITEUR (toi)** : prépares **un seul** paquet obfusqué, puis signes une clé par client.
> - **CLIENT** : déploie le paquet dans son workspace, colle sa clé.
>
> Le **paquet livré est identique pour tous les clients**. Seule la **clé de licence** change.

---

## A. ÉDITEUR — préparer le paquet (une seule fois)

### 1. Générer ta paire de clés de signature
```bash
python tools/license_tool.py keygen
```
- `tools/license_private_key.txt` → **SECRET** (ne jamais distribuer, déjà dans `.gitignore`).
- `license_public_key.txt` → clé publique (sert seulement à *vérifier* les licences).

> ⚠️ La paire fournie par défaut est une démo. **Régénère-la avant toute vraie distribution.**

### 2. Ancrer la clé publique dans le code (recommandé)
Ouvre `licensing.py` et remplace la valeur de `_EMBEDDED_PUBLIC_KEY_B64` par le
contenu de `license_public_key.txt` (la ligne base64). Ainsi la clé est **à
l'intérieur du code obfusqué**, donc non remplaçable facilement (voir section E).

### 3. Passer la config en mode production
Dans `config.toml` :
```toml
[app]
dev_mode = false        # false = vraies données Databricks (plus de fake data)

[license]
enabled   = true        # verrou licence actif
trial_days = 7          # durée de l'essai gratuit
```

### 4. Obfusquer avec PyArmor
```bash
pip install pyarmor
pyarmor gen --recursive --output dist \
    app.py app_config.py prod_data.py licensing.py dashboards dev_data
```

### 5. Compléter le paquet `dist/`
Copie à côté du code obfusqué les fichiers **non-code** nécessaires :
```
dist/
├── (fichiers .py obfusqués + pyarmor_runtime_*/)
├── config.toml            ← dev_mode=false
├── requirements.txt
├── app.yaml               ← point d'entrée Databricks App
└── manifest.yaml
```
- **N'inclus PAS** `tools/` (clé privée).
- **N'inclus PAS** `license_public_key.txt` si tu as fait l'étape 2 (clé déjà embarquée).

### 6. Zipper `dist/` → c'est ton livrable
Ce zip est le même pour tous les clients.

📄 Détails : `docs/OBFUSCATION.md`.

---

## B. ÉDITEUR — émettre une clé par client

```bash
# 1 an
python tools/license_tool.py issue --customer "ACME Corp" --plan yearly --days 365

# 1 mois
python tools/license_tool.py issue --customer "ACME Corp" --plan monthly --months 1

# date précise
python tools/license_tool.py issue --customer "ACME Corp" --until 2027-01-31
```
La commande imprime une longue chaîne `xxxxx.yyyyy` → **c'est la clé** à envoyer au client.

📄 Détails : `docs/LICENCE.md`.

---

## C. CLIENT — déployer dans son workspace Databricks

1. Importer le contenu du zip dans le workspace (dossier Git ou upload).
2. Créer une **Databricks App** pointant sur ce dossier — elle lit `app.yaml`
   (`streamlit run app.py`) automatiquement.
   Alternative CLI : `databricks sync ./dist <workspace_path>` puis créer l'app.
3. À l'installation, l'admin **lie un SQL warehouse** (demandé par `manifest.yaml`).

➡️ L'app démarre en **essai gratuit de 7 jours**, aucune clé requise pour tester.

---

## D. CLIENT — activer sa licence

Au choix (le plus simple = la 3e) :
1. Variable d'environnement `APP_LICENSE_TOKEN=<clé>`.
2. Fichier `license.key` à la racine de l'app.
3. **Dans l'UI** : coller la clé dans la barre latérale (« 🔑 Enter license key »),
   ou dans l'écran de blocage qui apparaît à la fin de l'essai.

État affiché en bas de la sidebar : ✅ Licensed · ⏳ Trial · ⛔ Expired.

---

## E. `license_public_key.txt` : c'est quoi, et est-ce piratable ?

**Ce que c'est.** Deux clés vont ensemble :
- 🔒 **clé privée** (chez toi seulement) → sert à **créer/signer** les licences.
- 🔓 **clé publique** (`license_public_key.txt`) → sert seulement à **vérifier**
  qu'une clé a bien été signée par ta clé privée.

C'est de la crypto asymétrique (**Ed25519**). La clé publique **n'est pas secrète** :
la lire ne sert à rien pour un pirate.

**Peut-on forger une licence ?** Non. Créer une clé acceptée exige la **clé privée**,
que tu ne distribues jamais. Impossible de la déduire de la clé publique.

**Le vrai risque = remplacer la clé.** Si tu livres `license_public_key.txt` en
clair, un client malin pourrait le remplacer par **sa propre** clé publique, puis
se signer des licences avec **sa propre** clé privée. La parade :
- **Étape A.2** : embarquer la clé publique dans le code, puis
- **Étape A.5** : ne pas livrer le `.txt` et **obfusquer** (A.4).
Modifier la clé revient alors à casser l'obfuscation — beaucoup plus dur.

**L'essai (trial).** Le compteur de 7 jours est stocké dans
`~/.finops-optimizer/trial.json` (protégé par un HMAC anti-altération). C'est du
**best-effort** : un utilisateur avancé peut le réinitialiser en supprimant ce
fichier. L'obfuscation complique la chose sans la rendre impossible.

**À retenir.** Aucune app côté client n'est incassable à 100 %. Ici :
- ✅ **les licences sont cryptographiquement infalsifiables** (signature Ed25519) ;
- ⚠️ la protection contre le **remplacement de clé** et le **reset d'essai**
  repose sur l'**obfuscation** ;
- 🔐 si tu veux un verrou plus fort, il faut un **serveur de licence en ligne**
  (vérification à distance) — non couvert ici.
