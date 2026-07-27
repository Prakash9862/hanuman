# Hanuman Chess — Stockfish V2

Stockfish V2 enrichit le bloc JSON `HANUMAN_CHESS_INSIGHTS` déjà stocké dans chaque
note de partie. Le Markdown visible reste compatible avec V1.

## Format persistant

Une nouvelle analyse écrit `schema_version: 2`, avec :

- `analysis_metadata` : moteur, instant UTC, profondeur atteinte, limite réellement
  utilisée (`depth`), unité, perspective et configuration influente ;
- `opening_exit` : ply, numéro de coup, couleur au trait, dernier coup SAN/UCI, FEN,
  évaluation typée (`centipawn`, `mate` ou `unknown`), perspective, profondeur et PV ;
- `insights` : événements tactiques avec coup SAN/UCI, meilleur coup SAN/UCI,
  `fen_before`, `fen_after`, évaluations, perte, phase, ECO et PV.

`fen_before` est toujours la position exacte avant le coup joué ; `fen_after` est la
position exacte après ce coup. Les regroupements retirent uniquement les compteurs de
demi-coups et de coups complets. Ils conservent placement, couleur au trait, droits de
roque et case de prise en passant. La FEN originale est toujours conservée.

Les évaluations des événements restent exprimées du point de vue du camp qui joue,
comme en V1, afin de préserver le calcul de perte. L’évaluation de `opening_exit` est
explicitement exprimée du point de vue du joueur Hanuman (`hanuman-player`) ; un score
positif lui est favorable. Les pages ECO utilisent des seuils centralisés de `+50 cp`
et `-50 cp`.

La sortie d’ouverture réutilise la définition V1 : le dernier ply de la phase
`opening_plies` (24 par défaut), ou le dernier ply de la partie si elle est plus courte.
Elle n’est pas inventée si le joueur Hanuman ne peut pas être identifié.

## Compatibilité

Les enveloppes de schéma 1 et 2 sont lisibles. En l’absence de JSON V2, les vues
retombent sur le parseur du bloc Markdown V1. Une absence de FEN ou d’évaluation de
sortie produit une couverture nulle et un message explicite, jamais une valeur simulée.
Aucune migration destructive ni réanalyse automatique n’est effectuée.

## Commandes

Analyser les notes en attente avec Stockfish :

```bash
poetry run python -m hanuman.orchestrations.chess_analysis --limit 10 --depth 18
```

Reconstruire les connaissances depuis les données persistées, sans Stockfish ni
Chess.com :

```bash
poetry run python -m hanuman.orchestrations.chess_rebuild_views \
  --vault-path "/chemin/explicite/vers/Echecs"
```

Mettre volontairement à niveau un petit lot V1 :

```bash
poetry run python -m hanuman.orchestrations.chess_upgrade_analyses \
  --limit 5 --depth 18
```

`--filter TEXTE` restreint les chemins. Les analyses déjà V2 sont ignorées ; `--force`
les recalcule explicitement. La progression et le bilan (`analysed`, `skipped`,
`failed`, `already_current`) sont affichés. Une note V1 n’est remplacée qu’après la
production complète de sa V2.

Analyser appelle Stockfish et modifie les données persistées. Reconstruire les
connaissances relit seulement ces données et régénère les pages dérivées de manière
déterministe.
