# Obsidian ↔ Notion — direction visuelle V1

## Objectif

Donner rapidement un rendu visible dans Hanuman pour éviter de développer l’orchestration uniquement dans Swagger.

## Principes

- Hanuman conserve son identité propre ; il ne devient pas un clone d’Obsidian.
- La palette générale évolue vers une ambiance plus moderne, sombre et minérale.
- Le violet inspiré d’Obsidian devient la couleur d’accent principale.
- Les informations techniques restent secondaires face aux intentions utilisateur.
- L’écran doit immédiatement montrer : les notes, les pages Notion, leur état et les actions possibles.

## Palette proposée

- Fond principal : noir bleuté / aubergine très sombre
- Surfaces : gris violet profond
- Accent principal : violet lumineux
- Accent secondaire : lavande froide
- Succès : vert désaturé
- Avertissement : ambre
- Conflit : rouge framboise sombre
- Texte : blanc cassé

## Premier écran à produire

`Orchestrations > Obsidian ↔ Notion`

Il contient :

1. un en-tête avec les statistiques essentielles ;
2. une barre de recherche ;
3. des filtres par statut ;
4. une liste unifiée Obsidian / Notion ;
5. des boutons directs vers Obsidian et Notion ;
6. les actions Publier, Importer et Comparer.

## Priorité de développement

1. obtenir un écran réel dans Hanuman avec données API ;
2. valider l’ambiance visuelle ;
3. ajouter Publier ;
4. ajouter Importer ;
5. ajouter Comparer ;
6. seulement ensuite construire la synchronisation intelligente.

## Règle

Aucune nouvelle fonction backend ne doit être ajoutée sans représentation claire dans l’interface, sauf nécessité technique indispensable.