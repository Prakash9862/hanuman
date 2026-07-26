# ADR-0001 — Hanuman reste local-first pendant V1 et V2

## Statut

Accepté — 26 juillet 2026

## Contexte

Hanuman s’exécute sur l’ordinateur personnel de son propriétaire, mais utilise
des services accessibles sur Internet : Gmail, Google Calendar, Maps, Notion,
GitHub, YouTube, Chess.com et d’autres.

Le dépôt du code sur GitHub ne signifie pas que l’application Hanuman est
elle-même accessible publiquement.

Certaines routes peuvent lire des données, écrire dans des outils externes ou
lancer des processus locaux. Une exposition réseau publique exigerait donc une
authentification et une revue de sécurité spécifiques.

## Décision

Hanuman reste local-first et mono-utilisateur pendant V1 et V2.

Par défaut :

- l’application écoute uniquement sur l’interface loopback ;
- Hanuman peut appeler des services web externes ;
- aucune route Hanuman n’est exposée directement sur Internet ;
- un accès distant futur devra utiliser une solution authentifiée et faire
  l’objet d’un nouvel ADR.

## Conséquences positives

- modèle de sécurité plus simple ;
- données et secrets sous le contrôle du propriétaire ;
- pas de complexité SaaS ou multi-utilisateur prématurée ;
- possibilité d’utiliser normalement les API web.

## Limites

- pas d’accès natif direct depuis un autre appareil ;
- une future version mobile ou distante demandera une architecture dédiée.

## Révision

Cette décision sera réévaluée si un besoin réel et fréquent d’accès distant
apparaît.
