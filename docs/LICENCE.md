# Licence & essai gratuit

L'application fonctionne **gratuitement pendant N jours** (essai), puis se
**bloque** jusqu'à la saisie d'une **clé de licence** valide — modèle proche de
Dataiku. Une clé débloque l'app pour une durée définie (1 mois, 1 an, ou une date
d'expiration précise).

## Fonctionnement

- **Signature Ed25519** : les clés sont signées hors-ligne par l'éditeur avec une
  **clé privée**. L'app n'embarque que la **clé publique**
  (`license_public_key.txt`) → une clé ne peut pas être forgée depuis le code livré.
- **Hors-ligne** : aucune connexion à un serveur de licence.
- **Essai** : suivi dans le profil utilisateur
  (`~/.finops-optimizer/trial.json`), protégé par un HMAC d'intégrité.

## Configuration

`config.toml` :

```toml
[license]
enabled = true     # false = désactive complètement le verrou
trial_days = 7     # durée de l'essai gratuit
```

Surcharges par variables d'environnement : `APP_LICENSE_ENABLED`, `APP_TRIAL_DAYS`.

> En **mode dev** (`dev_mode = true`), la licence est ignorée.

## Côté ÉDITEUR — générer les clés et émettre des licences

L'outil est dans `tools/license_tool.py` (à **garder privé**, ne pas distribuer).

### 1. Générer la paire de clés (une seule fois)

```bash
python tools/license_tool.py keygen
```

- Écrit `tools/license_private_key.txt` → **SECRET** (déjà dans `.gitignore`).
- Écrit `license_public_key.txt` → à **inclure** dans l'app distribuée.

> Une paire de démonstration est déjà fournie pour tester immédiatement.
> **Régénérez-la avant toute distribution réelle** (`keygen`).

### 2. Émettre une clé pour un client

```bash
# 1 an
python tools/license_tool.py issue --customer "ACME Corp" --plan yearly --days 365

# 1 mois
python tools/license_tool.py issue --customer "ACME Corp" --plan monthly --months 1

# Date d'expiration précise
python tools/license_tool.py issue --customer "ACME Corp" --until 2027-01-31
```

La commande affiche la **clé de licence** (une longue chaîne `xxx.yyy`) à envoyer
au client.

## Côté CLIENT — activer une licence

Trois façons de fournir la clé (par ordre de priorité) :

1. Variable d'environnement `APP_LICENSE_TOKEN`.
2. Fichier `license.key` à la racine de l'app.
3. **Saisie dans l'UI** : quand l'essai est terminé, un écran demande la clé.
   Avant expiration, la clé peut aussi être saisie via la barre latérale
   (« 🔑 Enter license key »). La clé validée est enregistrée dans
   `~/.finops-optimizer/license.key`.

## États affichés

- ✅ **Licensed** — licence valide (client + date d'expiration).
- ⏳ **Trial** — essai en cours (jours restants). Avertissement à ≤ 3 jours.
- ⛔ **Expired** — essai terminé, app bloquée tant qu'aucune clé valide n'est saisie.

## Limites (à connaître)

- Le suivi d'essai est **best-effort** : un utilisateur avancé peut réinitialiser
  l'essai en supprimant `~/.finops-optimizer/trial.json`. L'obfuscation
  (voir `docs/OBFUSCATION.md`) complique la manipulation mais ne la rend pas
  impossible.
- La **validité des licences**, elle, est cryptographiquement sûre : sans la clé
  privée, impossible de produire une clé acceptée par l'app.
