# Connecteur Monkeytype

## Statut

Structure initiale générée automatiquement. L'implémentation métier reste à compléter.

## Description

Suivi des performances de frappe et des sessions d’entraînement.

## Métadonnées

- Identifiant : `monkeytype`
- Type : `remote_api`
- Authentification requise : `false`
- Écriture autorisée : `false`
- Profil de workspace : `search`

## Capacités

- `typing.stats.read`
- `typing.sessions.read`

## Intégration attendue

```text
Service
→ API
→ Registre
→ Frontend
→ Workspace
→ Constellation
→ Tests
```
