# ADR-0004 — Les écritures suivent plan → preview → apply → verify

## Statut

Accepté progressivement — 26 juillet 2026

## Contexte

Plusieurs orchestrations calculent actuellement les données et produisent les
effets distants dans le même flux.

Cela complique :

- la compréhension de ce qui va changer ;
- les tests ;
- l’approbation humaine ;
- la reprise après échec ;
- l’introduction future d’agents supervisés.

## Décision

Toute nouvelle orchestration produisant un effet important doit tendre vers :

1. plan : calculer les opérations prévues sans les exécuter ;
2. preview : présenter créations, mises à jour, suppressions, permissions,
   coûts et incertitudes ;
3. apply : exécuter uniquement le plan approuvé ;
4. verify : relire ou contrôler les résultats réels.

La première implémentation sera faite sur une seule orchestration réelle.
Aucun moteur générique ne sera créé avant que plusieurs flux ne prouvent les
mêmes besoins.

## Première application

Le premier candidat est soit :

- Calendar + Maps + Gmail ;
- soit Obsidian → Notion.

Le choix sera fait selon la simplicité du premier prototype.

## Conséquences positives

- confiance accrue ;
- effets testables ;
- erreurs partielles visibles ;
- préparation naturelle de l’approbation et de la reprise.

## Risques

- preview périmée entre calcul et application ;
- appels supplémentaires ;
- complexité excessive si généralisée trop tôt.

## Garde-fous

- empreinte des données sources ;
- expiration explicite d’une preview ;
- V1 limitée à un dry-run simple ;
- aucune abstraction universelle avant preuve par plusieurs cas.
