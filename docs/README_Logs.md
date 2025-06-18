# 📘 Documentation technique — Système de logs Hanuman

## 🧭 Objectif

Ce système de logs a pour but de fournir une **traçabilité structurée**, **lisible** et **exploitable** des événements internes de l’API Hanuman. Il est conçu pour :

- garantir une clarté parfaite entre la console développeur et les fichiers de log persistants,
- permettre des analyses post-mortem et du debug à froid,
- respecter les standards pro (rotation, ségrégation, structure JSON, etc.),
- être extensible dans tous les modules métiers.

---

## 🏗️ Architecture technique

### 📂 Fichiers clés

- `src/hanuman/core/logging.py` → configuration des loggers et handlers
- `src/hanuman/core/log_helpers.py` → helpers structurants (notamment `get_logger`)
- `src/hanuman/core/decorators.py` → décorateurs de logging (ex: `@log_function`)
- `src/hanuman/core/middleware.py` → middleware FastAPI pour logger toutes les requêtes HTTP entrantes/sortantes

---

## ⚙️ Fonctionnement

### 🔹 Structlog + logging

- `structlog` utilisé pour la structure du message log (clé-valeur)
- `logging` utilisé pour gérer les handlers, niveaux, fichiers, rotation, etc.

### 🔹 Deux outputs simultanés

1. **Console** (stdout)

   - Niveau : `INFO` minimum
   - Format : human-readable via `ConsoleRenderer`

2. **Fichiers `.json`** dans le dossier `logs/`

   - Fichiers séparés par niveau : `hanuman_info.json`, `hanuman_debug.json`, etc.
   - Rotation automatique via `TimedRotatingFileHandler`
   - Format structuré JSON via `structlog.processors.JSONRenderer`

### 🔹 Rotation des fichiers

- Format : `TimedRotatingFileHandler`
- Périodicité : journalier (`when='midnight'`)
- Suppression automatique : `backupCount=5` → 5 fichiers maximum conservés

### 🔹 Nom des fichiers

- Générés automatiquement à chaque rotation avec suffixe horodaté :

  ```
  hanuman_info.json.2025-06-18_12-00-00
  ```

---

## 🔍 Middleware FastAPI

Ajouté dès l’initialisation de l’app :

```python
app.add_middleware(
    Middleware(log_requests)
)
```

**Résultat loggé** à chaque requête :

```json
{
  "event": "Incoming request",
  "method": "GET",
  "url": "http://127.0.0.1:8000/status",
  "request_id": "xyz",
  "duration_ms": 34.2
}
```

Et réciproquement pour la réponse sortante.

---

## 🧪 Utilisation développeur

### Log simple

```python
logger.info("Connexion réussie")
```

### Log structuré

```python
logger.info("Lancement tâche cron", job="notion_sync", dry_run=False)
```

### Décorateur intelligent

```python
@log_function
async def ping():
    return {"pong": True}
```

---

## 🔐 Sécurité et exclusions

### 🔒 Filtres en place

- Aucun log en production ne doit contenir de `token`, `secret`, `password`, etc.
- Les valeurs sensibles doivent être manuellement exclues

### 🚫 Règles Semgrep

Des règles Semgrep personnalisées sont en place pour détecter :

- les `except:` sans type
- les `input()` interdits dans `src/`
- les loggers non déclarés dans les modules Python
- les clés sensibles hardcodées (`sk-`, `ghp-`, etc.)

---

## 🧩 Intégration future

- Ajout de contextes enrichis : `user_id`, `session_id`, `service`
- Intégration avec Sentry (en option)
- Logging des erreurs métiers avec codes spécifiques (ex: `E204`, `E503`)
- Ajout d’un `LogViewer` pour visualiser les logs au sein d’un dashboard local

---

## ✅ Checklist de vérification

- [x] Format JSON structuré
- [x] Rotation automatique activée
- [x] Aucun secret loggé
- [x] Middleware activé
- [x] Logger accessible dans tous les modules
- [x] Séparation console / fichiers

---

## 🏁 Conclusion

Le système de logs Hanuman respecte des standards **professionnels** : clarté, sécurité, maintenabilité, extensibilité. Il est prêt pour un déploiement **en environnement réel** et peut évoluer en intégration avec des outils de monitoring avancés.
