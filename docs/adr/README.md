# Architecture Decision Records

Un ADR explique une décision structurante, son contexte et ses conséquences. Il
ne remplace ni la référence du code actuel ni une spécification détaillée.

## Statuts

- **proposé** : en discussion ;
- **accepté** : décision active ;
- **accepté progressivement** : direction active, migration incomplète ;
- **remplacé** : conservé pour l’histoire, avec lien vers son successeur.

## Index

| ADR | Décision | Statut |
|---|---|---|
| [0001](ADR-0001-local-first.md) | Hanuman reste local-first en V1/V2 | accepté |
| [0002](ADR-0002-chess-belongs-to-hanuman.md) | Chess appartient au domaine Hanuman | accepté |
| [0003](ADR-0003-source-of-truth-per-flow.md) | Source de vérité par flux et objet | accepté |
| [0004](ADR-0004-plan-preview-apply-verify.md) | Écritures en plan, preview, apply, verify | accepté progressivement |
| [0005](ADR-0005-Organisation%20des%20notes%20Chess%20dans%20Obsidian.md) | Organisation Chess dans Obsidian | accepté |
| [0006](ADR-0006-%20Architecture%20des%20pages%20d%27ouverture%20%28Chess%20Knowledge%29.md) | Pages d’ouverture Chess | accepté |
| [0007](ADR-0007-orchestrate-do-not-replace.md) | Orchestrer sans remplacer les outils | accepté |
| [0008](ADR-0008-separate-connectors-and-orchestrations.md) | Séparer connecteurs et orchestrations | accepté |
| [0009](ADR-0009-reusable-services.md) | Garder les services réutilisables | accepté |
| [0010](ADR-0010-no-external-api-from-orchestrations.md) | Interdire les API externes dans les orchestrations | accepté progressivement |
| [0011](ADR-0011-canonical-fastapi-entrypoint.md) | Point d’entrée FastAPI canonique | accepté |

## Créer un ADR

Utiliser les sections :

```text
Titre
Statut et date
Contexte
Décision
Conséquences positives
Coûts et limites
Révision
```

Un ADR est requis lorsqu’un changement modifie une frontière de confiance, la
direction des dépendances, une source de vérité ou un invariant produit.
