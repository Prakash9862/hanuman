# ADR-0009 — Les services restent réutilisables

## Statut

Accepté — 27 juillet 2026

## Contexte

GitHub, Notion, Wikipédia ou Chess peuvent participer à plusieurs flux. Si un
service encode une destination particulière ou une réponse HTTP, sa capacité
ne peut plus être réutilisée depuis une CLI, la TUI ou une autre orchestration.

## Décision

Un service expose une capacité cohérente dans son domaine et ignore l’interface
utilisateur ainsi que le workflow complet.

Un service peut :

- valider et normaliser des données de son domaine ;
- appeler le connecteur correspondant ;
- traduire les erreurs techniques en erreurs utiles ;
- offrir une API Python stable.

Il ne doit pas :

- construire une réponse FastAPI ;
- appeler un service d’une autre plateforme pour former un flux ;
- choisir seul une destination inter-outils ;
- dépendre d’un composant frontend.

## Conséquences positives

- tests isolés ;
- réutilisation entre API, CLI, TUI et orchestrations ;
- responsabilités plus lisibles ;
- évolution d’un flux sans modification du service source.

## Coûts et limites

- certains services historiques portent encore du transport ;
- une classe par plateforme n’est pas obligatoire si des fonctions simples
  suffisent ;
- la réutilisation ne justifie pas une abstraction générique prématurée.

## Révision

Réévaluer lorsqu’un service possède plusieurs raisons indépendantes de changer
ou lorsque deux services exposent un contrat réellement identique.
