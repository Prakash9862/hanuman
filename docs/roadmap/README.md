# Roadmap

La roadmap décrit des seuils conditionnels. Elle ne promet ni date ni
fonctionnalité.

## Maintenant : fiabiliser

Objectif : rendre les capacités existantes cohérentes et vérifiables.

- résoudre le blocage de la suite HTTP ;
- unifier le statut du point d’entrée historique ;
- rendre les états frontend factuels ;
- borner les chemins Obsidian hors Chess ;
- harmoniser permissions et redaction des tokens/logs ;
- documenter un contrat de run sur deux flux d’écriture.

Critère de sortie : deux orchestrations réelles permettent de répondre à
« qu’est-ce qui va changer ? », « qu’est-ce qui a changé ? » et « comment
reprendre ? ».

## Ensuite : rendre les flux opérables

- appliquer `plan → preview → apply → verify` à des cas réels ;
- définir identité, état final et erreurs partielles ;
- produire un reçu d’exécution ;
- rendre les relances et doublons explicites ;
- consolider le catalogue de connecteurs depuis plusieurs implémentations.

Pas de moteur générique avant convergence de plusieurs flux.

## Plus tard : étendre avec preuve

- formaliser un contrat de connecteur si les cas actuels convergent ;
- ajouter des déclencheurs planifiés bornés ;
- développer une collecte culturelle vers Notion ou Obsidian ;
- proposer un briefing inter-outils en lecture seule ;
- évaluer des agents spécialisés uniquement après l’audit trail et les
  politiques d’autorisation.

## Non planifié

- remplacer Notion ou Obsidian ;
- centraliser tous les contenus dans une base Hanuman ;
- créer un SaaS multi-tenant ;
- ouvrir une marketplace publique de plugins ;
- construire un agent autonome général ;
- promettre une synchronisation bidirectionnelle universelle.

## Promotion d’une capacité

| Niveau | Critère |
|---|---|
| expérimental | preuve technique locale |
| alpha | cas utile, limites connues, tests isolés |
| bêta | erreurs et effets maîtrisés, documentation opératoire |
| stable | contrat versionné, reprise et compatibilité démontrées |

Le passage de niveau repose sur des preuves, pas sur l’ancienneté.
