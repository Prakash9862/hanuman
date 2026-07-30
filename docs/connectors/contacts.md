# Connecteur Google Contacts

## Statut

Structure initiale générée automatiquement. L'implémentation métier reste à compléter.

## Description

Consultation et gestion des contacts Google.

## Métadonnées

- Identifiant : `contacts`
- Type : `remote_api`
- Authentification requise : `false`
- Écriture autorisée : `false`
- Profil de workspace : `search`

## Capacités

- `contacts.read`
- `contacts.write`

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
