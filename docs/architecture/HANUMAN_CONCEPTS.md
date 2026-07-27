# Concepts fondamentaux de Hanuman

## Principe général

Hanuman est un système d'orchestration personnel dont le rôle est de relier des outils spécialisés, coordonner leurs interactions, surveiller leur fonctionnement et construire progressivement un écosystème numérique intelligent.

Son architecture fonctionnelle repose sur deux notions principales :

- les connecteurs ;
- les flux.

## Connecteur

Un connecteur est un système individuel avec lequel Hanuman communique ou qu’il pilote.

Un connecteur peut être :

- une API distante ;
- un service web ;
- un système de fichiers ;
- un programme local ;
- un moteur local ;
- un fournisseur d’intelligence artificielle.

Exemples :

- Gmail ;
- Google Calendar ;
- Google Maps ;
- Notion ;
- Obsidian ;
- GitHub ;
- Wikipédia ;
- Chess.com ;
- Stockfish ;
- SCID ;
- Gallica ;
- IMSLP ;
- YouTube ;
- OpenAI.

Un connecteur peut disposer dans Hanuman :

- d’un état de connexion ;
- de capacités ;
- d’une configuration ;
- de statistiques ;
- d’une interface de consultation ;
- de la liste des flux qui l’utilisent.

L’utilisation d’un connecteur seul n’est pas un flux.

## Flux

Un flux est une opération organisée par Hanuman qui coordonne au moins deux
connecteurs afin de produire un résultat.

Un flux peut être simple ou complexe.

Exemples de flux :

- Obsidian → Notion ;
- Wikipédia → Notion ;
- GitHub Issues → Notion ;
- Google Calendar → Google Maps ;
- Chess.com → Stockfish → Obsidian → SCID.

Ne sont pas des flux :

- Gmail ;
- Calendar ;
- Notion ;
- Stockfish ;
- Gallica.

Ces éléments sont des connecteurs individuels.

Chaque espace de flux doit réunir tout ce qui est nécessaire à son fonctionnement :

- les connecteurs utilisés ;
- la configuration requise ;
- les actions disponibles ;
- les données manipulées ;
- la progression ;
- les résultats ;
- les erreurs ;
- l’historique ;
- les statistiques et diagnostics utiles.

## Ressource

Une ressource est un objet manipulé ou découvert par Hanuman.

Exemples :

- une vidéo YouTube ;
- une partition IMSLP ;
- un document Gallica ;
- une page Wikipédia ;
- un message Gmail ;
- une partie d’échecs.

« Ressource » ne désigne pas une catégorie principale de l’architecture de Hanuman.

## Résumé

- **Ressource** : objet manipulé.
- **Connecteur** : système utilisé.
- **Flux** : coordination entre plusieurs systèmes.
