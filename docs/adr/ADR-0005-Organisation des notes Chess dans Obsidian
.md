# ADR-0005 — Organisation des notes Chess dans Obsidian

## Statut

Accepté — 26 juillet 2026

## Contexte

L’orchestration Chess produit des notes de parties analysées, ainsi que des
synthèses par ouverture, adversaire, motif et période.

Le vault Obsidian contient d’autres projets. Hanuman ne doit donc jamais écrire
à sa racine ni disperser les fichiers Chess dans plusieurs emplacements.

La duplication d’une même partie entre les dossiers chronologiques et les
dossiers d’index rendrait le vault ambigu et difficile à maintenir.

## Décision

Toutes les créations Chess sont limitées à :

`<OBSIDIAN_VAULT_PATH>/Echecs/`

Les notes de parties sont stockées une seule fois selon cette structure :

`Echecs/<année>/<année-mois>/<partie>.md`

Les documents de synthèse sont stockés uniquement sous :

`Echecs/_Index/`

La structure initiale de `_Index` est :

- `Dashboard.md`
- `Profil échiquéen.md`
- `Ouvertures/`
- `Motifs/`
- `Gaffes/`
- `Excellents coups/`
- `Opportunités/`

Les fichiers d’index référencent les notes de parties au moyen de liens
Obsidian. Ils ne recopient pas les notes complètes.

Une note thématique distincte n’est créée que lorsqu’un motif est récurrent,
exceptionnellement important ou explicitement conservé par l’utilisateur.

## Source de vérité

- la note de partie est la source de vérité de son analyse détaillée ;
- les notes `_Index` sont des synthèses recalculables ;
- l’état technique d’analyse appartient à Hanuman ;
- le PGN brut reste attribué à Chess.com ou à sa source originale.

## Garde-fous

- aucune écriture à la racine du vault ;
- aucun chemin absolu personnel dispersé dans le code ;
- la racine Chess est dérivée de la configuration ;
- aucune duplication d’une note de partie ;
- toute régénération des index doit être idempotente ;
- un fichier existant ne doit pas être écrasé silencieusement s’il contient
  des annotations humaines non générées.

## Conséquences positives

- séparation nette avec les autres projets du vault ;
- navigation chronologique simple ;
- index pédagogiques lisibles ;
- graphe moins pollué ;
- possibilité de reconstruire les synthèses depuis les notes de parties.

## Limites

- les index nécessitent une stratégie de mise à jour ;
- les liens doivent rester valides lors d’un déplacement manuel ;
- la distinction entre contenu généré et annotations humaines doit être
  explicitement représentée.

## Révision

Cette décision sera réévaluée uniquement si le volume des parties rend la
navigation annuelle et mensuelle insuffisante.

## Seuil de création des synthèses

- moins de 3 occurrences : l’événement reste uniquement dans les notes de parties ;
- de 3 à 4 occurrences : il peut être signalé dans le Dashboard ou le Profil échiquéen ;
- à partir de 5 occurrences : Hanuman peut créer une note thématique dédiée ;
- une exception importante nécessite une validation explicite de l’utilisateur.
