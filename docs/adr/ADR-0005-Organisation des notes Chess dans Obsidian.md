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

Les seuils sont calculés exclusivement à partir du nombre de **parties
uniques** contenant un même groupe d’insights, défini par sa catégorie et son
sous-type. Plusieurs occurrences du même groupe dans une partie augmentent le
nombre total d’occurrences, mais ne comptent que pour une partie dans le seuil.

- moins de 3 parties uniques : le groupe ne reçoit aucun statut officiel et
  n’apparaît pas dans les tendances actives ;
- à partir de 3 parties uniques : le groupe reçoit le statut exact
  **« Signal émergent »** et apparaît dans la page d’accueil de sa catégorie,
  sans note individuelle ;
- à partir de 4 parties uniques : le groupe reçoit le statut exact
  **« Tendance confirmée »** et reste présenté de manière visuellement
  distincte dans la page d’accueil de sa catégorie, sans note individuelle ;
- à partir de 5 parties uniques : le groupe reçoit le statut exact
  **« Synthèse durable »** et une note thématique individuelle est
  automatiquement créée puis mise à jour. Au-delà de 5, ce statut est
  conservé.

Aucun insight ne peut contourner ces seuils automatiquement. La notion
d’exception importante et tout mécanisme de validation humaine associé sont
hors du périmètre de cette décision et nécessiteront un workflow explicite
ultérieur.

## Régression d’une synthèse

Une note thématique existante n’est jamais supprimée automatiquement.

Lorsqu’une Synthèse durable repasse sous 5 parties uniques :

- sa note et ses annotations humaines sont conservées ;
- son statut devient exactement
  **« Inactive — seuil actuellement non atteint »** ;
- ce statut de synthèse inactive prévaut sur les statuts Signal émergent ou
  Tendance confirmée tant que la note durable existante reste sous le seuil 5 ;
- elle n’est plus présentée comme une synthèse active ;
- elle apparaît dans une section distincte des synthèses inactives sur la page
  d’accueil de sa catégorie.

Si elle atteint de nouveau 5 parties uniques, elle redevient automatiquement
une Synthèse durable active. Un groupe qui passe de 4 à 3 adopte simplement le
statut correspondant à son nombre courant de parties uniques.

## Navigation thématique

Les pages d’accueil de `Gaffes`, `Excellents coups` et `Opportunités`
distinguent au minimum :

- les Synthèses durables actives ;
- les Tendances confirmées ;
- les Signaux émergents ;
- les Synthèses inactives, uniquement lorsqu’il en existe.

Les Signaux émergents et Tendances confirmées sont présentés directement dans
la page d’accueil, sans note individuelle. Les Synthèses durables actives et
inactives possèdent une note individuelle. Aucun lien ne doit pointer vers une
note inexistante.

## Exemples dans les synthèses

Toutes les occurrences sont conservées et affichées, regroupées par partie.
Les parties sont ordonnées de la plus récente à la plus ancienne. En cas
d’égalité ou de date absente, l’ordre est déterminé par le chemin de note ou
l’identifiant de partie. Dans une partie, les occurrences sont ordonnées par
`ply` croissant, puis par `insight_id`.

Une partie n’est affichée qu’une fois comme groupe, mais peut contenir plusieurs
occurrences. Chaque occurrence affiche uniquement les données réellement
disponibles.

## Nommage des synthèses structurées

Les seuls groupes structurés actuellement autorisés sont :

- Gaffes : `opening` (« En ouverture », fichier `En ouverture.md`) et
  `middlegame_or_endgame` (« Milieu de jeu ou finale », fichier
  `Milieu de jeu ou finale.md`) ;
- Excellents coups : `opening` (« En ouverture », fichier `En ouverture.md`)
  et `middlegame_or_endgame` (« Milieu de jeu ou finale », fichier
  `Milieu de jeu ou finale.md`) ;
- Opportunités : `missed_excellent` (« Excellents coups manqués », fichier
  `Excellents coups manqués.md`).

Les noms de fichiers proviennent exclusivement de cette table contrôlée. Aucun
nom de fichier n’est dérivé directement d’une valeur libre. Aucun motif
échiquéen supplémentaire n’est déduit sans règle déterministe dédiée.
