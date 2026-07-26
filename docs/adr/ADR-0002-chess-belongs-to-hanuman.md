# ADR-0002 — Le domaine Chess appartient à Hanuman

## Statut

Accepté — 26 juillet 2026

## Contexte

Le flux Chess relie plusieurs outils spécialisés :

- Chess.com fournit les parties ;
- Stockfish analyse les positions ;
- Hanuman coordonne les étapes et transforme les résultats ;
- Obsidian reçoit et organise les analyses.

Hanuman ne doit remplacer ni Chess.com, ni Stockfish, ni Obsidian.

## Décision

Chess reste un domaine fonctionnel de Hanuman.

Hanuman y joue uniquement un rôle d’orchestration :

Chess.com → Hanuman → Stockfish → Hanuman → Obsidian.

Les capacités échiquéennes doivent rester séparées des responsabilités propres
aux outils sources.

## Conséquences positives

- cas d’usage personnel réel et cohérent avec « relier sans remplacer » ;
- démonstration forte de l’orchestration entre service web, moteur local et
  outil de connaissance ;
- possibilité de réutiliser les futurs contrats d’exécution de Hanuman.

## Contraintes

- la branche `feat/chess-analysis-v1` ne sera pas fusionnée aveuglément ;
- ses capacités seront inventoriées et intégrées par unités testables ;
- les valeurs personnelles codées en dur devront devenir configurables ;
- Chess ne doit pas imposer son architecture aux autres domaines.

## Révision

Chess pourra devenir un module interne clairement délimité si son périmètre
continue de croître, sans quitter pour autant Hanuman.
