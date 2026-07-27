# Connecteurs

Un connecteur représente une frontière avec un outil externe ou une capacité
locale. Le registre applicatif n’est pas encore un contrat d’exécution commun.

## Catalogue

| Connecteur | Capacités présentes | Écriture | Maturité |
|---|---|---:|---|
| Obsidian | lire, scanner et écrire du Markdown | oui | bêta interne |
| Notion | ping, recherche, lecture et création/mise à jour selon le flux | oui | bêta interne |
| GitHub | utilisateur, dépôts et issues | non côté GitHub | alpha |
| Gmail | OAuth, liste, recherche et détail | token local seulement | alpha, lecture seule |
| Google Calendar | OAuth, calendriers et événements | token local seulement | alpha, lecture seule |
| Wikipédia | recherche et extraction structurée | non | bêta interne |
| Chess.com | profil et parties publiques | non | bêta interne |
| OpenAI | ping et appels de QA ciblés | requêtes payantes | expérimental |
| YouTube | recherche et pagination | non | alpha |
| Gallica | recherche SRU et repli vers le navigateur | non | alpha |
| IMSLP | recherche MediaWiki | non | alpha |
| Google Maps | URL de recherche et d’itinéraire | non | simple générateur de liens |
| Stockfish | analyse locale de parties | fichiers dérivés | bêta interne |

« Maturité » évalue le périmètre démontré, pas la qualité intrinsèque de
l’outil externe.

## Anatomie actuelle

Il n’existe pas une classe de base universelle. Un connecteur peut être
implémenté par :

- un service dans `services/core/` ;
- un module spécialisé comme `core/gmail.py` ;
- un client fin dans `services/adapters/` ;
- un service local comme `local_programs_service.py`.

Le registre `connectors_registry.py` expose les descripteurs consommés par
l’API et l’interface.

## États

Ne pas confondre :

| État | Signification |
|---|---|
| déclaré | présent dans le catalogue |
| configuré | paramètres ou credentials disponibles |
| autorisé | permissions accordées par le fournisseur |
| joignable | transport accessible au moment du test |
| sain | opération représentative réussie |

Un endpoint `ping` ne prouve pas toujours les cinq états.

## Ajouter un connecteur

Avant tout code, vérifier :

1. qu’un flux inter-outils réel le nécessite ;
2. que Hanuman ne recrée pas l’outil ;
3. que les scopes et données sensibles sont inventoriés ;
4. que timeouts, pagination, quotas et erreurs sont définis ;
5. qu’un service réutilisable peut masquer les détails du fournisseur ;
6. que les tests n’exigent ni réseau ni secrets réels ;
7. que le catalogue et la documentation sont mis à jour.

Créer un ADR seulement si le connecteur introduit une nouvelle frontière de
confiance ou modifie un principe transversal.
