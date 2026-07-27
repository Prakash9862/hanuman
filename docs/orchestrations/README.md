# Orchestrations

Une orchestration implémente une intention et coordonne des capacités. Elle
possède les transformations et les règles de flux ; elle ne devrait pas parler
directement à une API externe.

## Catalogue actuel

| Flux | Entrée | Effet | Interface | État |
|---|---|---|---|---|
| Obsidian → Notion | note Markdown | création de page Notion | API, UI, CLI | disponible |
| Obsidian / Notion | vault et pages | rapprochement et statistiques | API, UI | lecture/comparaison |
| Wikipédia → Notion | sujet ou page | création de page Notion | API, UI, CLI | disponible |
| Context pack → Notion | sujet Wikipédia | page enrichie | CLI | disponible |
| GitHub issues → Notion | dépôt | création/mise à jour Notion | CLI/service | disponible, alpha |
| GitHub Activity → Notion Project Memory | dépôt et plage de commits | plan de Development Sessions, sans écriture | CLI | Phase 1 |
| Chess.com → Obsidian | utilisateur et limite | notes et vues Chess | API, UI, CLI | disponible |
| Stockfish → Obsidian | notes PGN | analyses et connaissances dérivées | UI Resources, CLI | disponible |
| Chess insights → Notion | base de parties | synthèse Notion | CLI | disponible |
| Wikipédia + OpenAI | question | réponse enrichie | CLI | expérimental |

## Contrat documentaire

Chaque nouvelle orchestration doit préciser :

```text
Intention
Entrées et préconditions
Sources de vérité
Identité des objets
Étapes
Effets de lecture et d’écriture
Idempotence et doublons
Erreurs partielles
Vérification
Limites
```

## Frontière de couches

```text
route/CLI
   |
   v
orchestration
   |  coordonne
   +----> service A ----> connecteur A
   +----> service B ----> connecteur B
```

Une orchestration :

- ne construit pas de réponse FastAPI ;
- ne lit pas directement un token ;
- ne connaît pas les détails HTTP ;
- peut transformer et réconcilier des modèles ;
- déclare tous ses effets importants.

Certaines orchestrations actuelles utilisent encore `urllib` directement.
Elles sont des dettes connues, pas des exemples à reproduire.

## Plan, preview, apply, verify

Le cycle décidé par [ADR-0004](../adr/ADR-0004-plan-preview-apply-verify.md)
est une direction adoptée progressivement :

1. **plan** : calculer les opérations ;
2. **preview** : montrer effets, ambiguïtés et coûts ;
3. **apply** : exécuter le plan approuvé ;
4. **verify** : relire ou contrôler le résultat.

Ce contrat n’est pas encore généralisé. Ne pas documenter un simple calcul
interne comme une preview utilisateur.

## Sources de vérité

La source est définie par flux et par champ. Exemples actuels :

- note Markdown publiée : Obsidian ;
- page publiée : Notion comme destination ;
- partie brute : Chess.com ;
- analyse : résultat Stockfish versionné ;
- note et vues Chess : Obsidian, avec zones générées par Hanuman ;
- événement : Google Calendar ;
- état technique d’exécution : Hanuman.

Voir [ADR-0003](../adr/ADR-0003-source-of-truth-per-flow.md).

## GitHub Project Memory — plan Phase 1

Après avoir configuré `GITHUB_TOKEN` et la liste explicite
`GITHUB_ALLOWED_REPOSITORIES` :

```bash
hanuman flows github-project-memory plan \
  --repository Prakash9862/hanuman \
  --branch main \
  --max-commits 50 \
  --session-window-hours 24
```

`--start-ref` fixe un SHA de départ exclusif, `--end-ref` un SHA ou une ref de
fin, `--detailed-plan` groupe les commits sous chaque session et `--json`
sérialise le Run complet, associations comprises.

Cette Phase 1 lit uniquement GitHub, normalise les commits, calcule des
Development Sessions et produit un plan, un FlowResult et un Run structurés.
Elle n'importe aucun service Notion et ne peut effectuer aucune écriture
Notion. Pull requests, releases, workflows, webhooks et déclenchement
automatique restent hors périmètre.
