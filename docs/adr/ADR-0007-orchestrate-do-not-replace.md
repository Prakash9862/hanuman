# ADR-0007 — Hanuman orchestre sans remplacer les outils

## Statut

Accepté — 27 juillet 2026

## Contexte

Hanuman relie des outils déjà spécialisés : GitHub pour le code, Notion pour
les pages structurées, Obsidian pour les notes locales, Gmail pour le courrier
et Google Calendar pour les événements.

Créer dans Hanuman un équivalent de chaque outil dupliquerait leurs fonctions,
centraliserait inutilement les données et détournerait le projet de sa valeur
distinctive.

## Décision

Hanuman possède la logique d’orchestration, pas les domaines complets des outils
connectés.

Il peut :

- présenter une vue opératoire nécessaire à un flux ;
- normaliser et transformer des ressources ;
- conserver provenance, identité et état d’exécution ;
- produire un artefact dans l’outil le plus adapté.

Il ne doit pas créer un éditeur de notes, une forge, un client mail ou un
calendrier général lorsque l’outil spécialisé demeure disponible.

## Conséquences positives

- périmètre produit plus clair ;
- moins de données dupliquées ;
- remplacement possible d’un fournisseur ;
- effort concentré sur les flux inter-outils.

## Coûts et limites

- l’expérience dépend de plusieurs outils installés ou autorisés ;
- certains écrans Hanuman restent nécessaires pour prévisualiser et superviser ;
- un mode dégradé dépend des capacités de chaque fournisseur.

## Révision

Un nouvel outil natif Hanuman exige de démontrer qu’il sert directement
l’orchestration et qu’aucun outil spécialisé ne remplit ce rôle.
