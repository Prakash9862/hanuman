# ADR-0003 — La source de vérité est définie par flux et par objet

## Statut

Accepté — 26 juillet 2026

## Contexte

Obsidian n’a pas un rôle unique :

- il reçoit les analyses d’échecs ;
- il contient des notes Markdown personnelles ;
- il peut publier certains contenus vers Notion ;
- il pourra participer à d’autres orchestrations.

Notion peut être une destination de publication ou un catalogue structuré.
Chess.com, Calendar et d’autres outils restent propriétaires de leurs propres
objets.

Une source de vérité globale pour tout Hanuman serait artificielle.

## Décision

Chaque orchestration doit déclarer explicitement :

- la source de vérité de chaque objet ou champ ;
- la direction autorisée de la transformation ;
- l’identité entre objets de plusieurs outils ;
- la règle de conflit ;
- les informations impossibles à représenter dans la destination.

Exemples initiaux :

- partie brute : Chess.com ;
- analyse moteur : résultat Stockfish identifié et versionné ;
- note personnelle Markdown : Obsidian ;
- événement : Google Calendar ;
- fiche de catalogue culturel : Notion ;
- état d’exécution et provenance : Hanuman.

## Conséquences positives

- conflits plus compréhensibles ;
- idempotence testable ;
- pas de « synchronisation bidirectionnelle magique » ;
- chaque outil conserve sa spécialité.

## Limites

- une même information peut avoir plusieurs représentations ;
- certaines règles devront être définies champ par champ ;
- les flux bidirectionnels restent interdits tant que les conflits ne sont pas
  explicitement résolus.
