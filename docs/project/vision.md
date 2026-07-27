# Vision

## Définition

Hanuman est un hub d’orchestration personnel. Il coordonne des outils
spécialisés, transforme les objets qui circulent entre eux et rend les effets
compréhensibles.

```text
outil source ──> capacité ──> orchestration ──> capacité ──> outil cible
                                  │
                                  └──> résultat, provenance, diagnostic
```

Hanuman ne cherche pas à posséder toutes les données. Il possède la logique du
flux : l’intention, l’ordre des opérations, les transformations, les règles de
conflit et les preuves techniques nécessaires.

## Pourquoi il existe

Les outils numériques sont excellents dans leur spécialité mais décrivent un
même travail avec des objets différents :

| Outil | Objet natif |
|---|---|
| GitHub | dépôt, issue |
| Notion | page, base |
| Obsidian | note Markdown, lien |
| Gmail | message |
| Google Calendar | événement |
| Chess.com | partie |
| Stockfish | analyse de position |

L’utilisateur est généralement la seule couche d’intégration. Il copie,
reformate, vérifie et se souvient. Hanuman automatise ces ponts sans diluer la
spécialité des outils.

## Philosophie

1. **Relier, ne pas remplacer.** Une meilleure intégration ne justifie pas un
   nouvel éditeur, calendrier ou gestionnaire de code dans Hanuman.
2. **Orchestrer des intentions.** « Publier une note » est plus stable que la
   suite exacte d’appels HTTP qui l’implémente.
3. **Respecter les sources de vérité.** Chaque flux déclare qui fait autorité
   pour chaque objet ou champ.
4. **Préférer les effets explicites.** Une écriture devrait être planifiable,
   prévisualisable, applicable puis vérifiable.
5. **Rester local-first.** Le modèle actuel est personnel, mono-utilisateur et
   lié au loopback.
6. **Conserver l’humain responsable.** L’automatisation assiste une décision ;
   elle n’élargit pas seule ses permissions.
7. **Documenter la réalité.** Une idée, une spécification et une capacité
   disponible ne sont jamais présentées au même niveau.

## Ce que Hanuman n’est pas

- une base universelle remplaçant les données sources ;
- un clone de Notion, Obsidian, GitHub ou Gmail ;
- une synchronisation bidirectionnelle magique ;
- un SaaS multi-utilisateur ;
- un système d’agents autonomes ;
- un simple proxy exposant toutes les API tierces.

## Critère de succès

Hanuman réussit lorsqu’une intention inter-outils devient répétable,
compréhensible et sûre, tout en laissant les données principales dans les
outils qui les servent le mieux.

Le nombre de connecteurs n’est pas la métrique principale. La qualité d’un petit
nombre de flux réellement utiles l’est.
