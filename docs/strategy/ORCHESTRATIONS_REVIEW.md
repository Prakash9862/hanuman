# Revue des orchestrations

## Portefeuille observé

| Orchestration | Maturité / qualité | Robustesse / couverture | Documentation / évolutivité | Risque / décision |
|---|---|---|---|---|
| Obsidian → Notion | Bêta avancée; parsing riche | principal ~90 %, safe ~24 % | doc forte; évolutive après identité | stabiliser preview et conflits |
| GitHub issues → Notion | Bêta; logique create/update | ~81 %, doubles contrôlés | doc moyenne; bon flux de référence | clarifier source de vérité |
| Wikipedia → Notion | Bêta; transformation riche | ~81 % | doc abondante; évolution simple en lecture | duplication encyclopédique |
| Wikipedia Context Pack → Notion | Bêta; composition ciblée | ~86 % | doc moyenne; niche | conserver seulement si réutilisé |
| Wikipedia + OpenAI | Prototype; sortie probabiliste | 0 % sur module QA | vision riche, contrat faible | exiger preuves/citations |
| Chess.com → Obsidian | Alpha; utile mais personnelle | ~97 % | doc faible; portabilité faible | valeurs codées en dur |
| Chess insights → Notion | Alpha/Bêta; niche | ~77 % | doc moyenne; dépend du schéma Notion | maintenir si usage réel |
| Dashboard Obsidian ↔ Notion | Alpha; diagnostic | ~43 % | direction UX claire; modèle de conflit absent | ne pas appeler cela une sync |

## Forces

- Les noms décrivent généralement une intention et des systèmes.
- Les transformations Markdown/Notion sont testées en profondeur.
- GitHub → Notion possède déjà une logique de recherche/update, rare signe d’idempotence.
- Les orchestrations restent exécutables indépendamment de l’UI.

## Faiblesses communes

- Pas de contrat standard : entrée, plan, effets, résultat, erreur partielle, reprise.
- L’identité d’un même objet à travers deux outils est ad hoc.
- Le journal d’exécution n’est pas une machine d’état fiable.
- Certaines orchestrations parlent directement au protocole externe.
- Le dashboard peut lancer tout module détecté, sans politique par orchestration.

## Fiche obligatoire avant évolution

Chaque orchestration doit documenter :

```text
Intention / propriétaire / déclencheur
Source(s) de vérité
Entrées et préconditions
Étapes sans effet puis effets
Clé d’idempotence et stratégie de conflit
Permissions et données transmises
Résultat vérifiable
Échec partiel, reprise, compensation
Budget temps/requêtes/coût
```

## Analyse Obsidian ↔ Notion

La promesse « bidirectionnelle » est prématurée. Le code prouve surtout Obsidian → Notion et une vue de rapprochement. Avant tout retour Notion → Obsidian, il faut décider quelle propriété est autoritaire, comment reconnaître une page, que faire de deux modifications concurrentes et comment préserver le Markdown non représentable dans Notion. Sans cela, la sync bidirectionnelle est dangereuse.

## Recommandation

Choisir deux flux de référence :

1. Obsidian → Notion pour le modèle `preview/apply/verify`.
2. GitHub → Notion pour le modèle `identity/update/conflict`.

Ne généraliser un moteur qu’après avoir extrait leurs invariants. Les orchestrations Wikipedia et Chess restent de bons laboratoires, pas des fondations architecturales.
