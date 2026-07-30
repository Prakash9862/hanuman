# Connecteur DevDocs

## Statut

Structure initiale générée automatiquement. L'implémentation métier reste à compléter.

## Description

Recherche et consultation de documentation technique.

## Métadonnées

- Identifiant : `devdocs`
- Type : `remote_api`
- Authentification requise : `false`
- Écriture autorisée : `false`
- Profil de workspace : `search`

## Capacités

- `documentation.search`
- `documentation.open`

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
