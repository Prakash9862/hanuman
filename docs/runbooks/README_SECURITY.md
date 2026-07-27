# SECURITY.md

## 1. Introduction

Hanuman est une API / boîte à outils personnelle écrite en Python, utilisée pour
orchestrer des services externes (Notion, Obsidian, GitHub, Chess.com, Wikipédia,
OpenAI, etc.).

Même si le projet est pour l’instant utilisé **uniquement en local** sur une
machine personnelle, il manipule :

- des **tokens d’API sensibles**,
- des **données personnelles et familiales**,
- des **fichiers locaux structurés** (notes, documents, journaux).

Ce document décrit le modèle de menace, les mesures de sécurité existantes et
les points d’attention à conserver lors de l’évolution du projet.

---

## 2. Modèle de menace

### 2.1 Hypothèses de contexte

- Hanuman tourne sur un **poste unique** (Linux) contrôlé par l’utilisateur.
- Aucune instance Hanuman n’est exposée publiquement sur Internet.
- L’API (FastAPI) est, par défaut, accessible en local uniquement
  (loopback / développement).
- Il n’y a **pas d’utilisateurs multi-compte** : un seul propriétaire légitime.

### 2.2 Actifs sensibles

Principaux actifs à protéger :

1. **Secrets / credentials**

   - Tokens Notion
   - Tokens GitHub
   - Clé OpenAI
   - Éventuels tokens Google / Calendar / autres services

2. **Données applicatives**

   - Fichiers Markdown Obsidian (journaux personnels, projets, enquête Sri Lanka)
   - Données synchronisées depuis Notion / GitHub / Chess.com, etc.
   - Logs d’exécution (run logs) pouvant contenir des métadonnées sensibles.

3. **Code et configuration**
   - Le code de Hanuman (scripts, orchestrations, services)
   - Le fichier `.env`
   - Le dépôt Git local + remote GitHub

### 2.3 Menaces principales

- Divulgation de secrets (tokens d’API) :
  - fuite dans le code source
  - fuite dans les logs
  - fuite via copie / capture d’écran / partage
- Corruption de données locales :
  - bug dans une orchestration qui écrit au mauvais endroit
  - suppression ou écrasement de fichiers sensibles
- Abus d’API :
  - script mal configuré envoyant trop de requêtes
  - erreur logique exposant plus de données que prévu dans un endpoint
- Compromission du poste :
  - malware ou utilisateur non autorisé ayant accès au compte Linux local

---

## 3. Gestion des secrets

### 3.1 Stockage

- Les tokens sont fournis à Hanuman via **variables d’environnement**
  (chargées depuis un fichier `.env` qui n’est jamais committé).
- Le fichier `.env` est listé dans `.gitignore`.
- Recommandation : permissions restrictives sur `.env` :

  ```bash
  chmod 600 .env
  ```
