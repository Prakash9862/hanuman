# ADR-0011 — `hanuman.main:app` est le point d’entrée FastAPI canonique

## Statut

Accepté — 27 juillet 2026

## Contexte

Le dépôt contient deux applications FastAPI. Historiquement,
`hanuman.main:app` n’exposait que les orchestrations tandis que
`hanuman.api.core.main:app` assemblait l’application complète. Le code actuel a
inversé cette situation : `hanuman.main:app` assemble tous les routeurs et
l’autre application reste minimale.

Cette ambiguïté a rendu le Makefile, le frontend et la documentation
contradictoires.

## Décision

Le seul point d’entrée documenté et utilisé pour lancer Hanuman est :

```text
hanuman.main:app
```

`hanuman.api.core.main:app` est historique. Tant qu’il existe, il doit être
décrit comme un sous-ensemble non canonique.

## Conséquences positives

- commande de lancement unique ;
- frontend et Swagger alignés ;
- tests et opérations moins ambigus.

## Coûts et limites

- l’application historique reste dans le code ;
- sa suppression ou redirection exige une modification de code distincte de
  cette mission documentaire.

## Révision

Un changement de point d’entrée exige un ADR de remplacement et la mise à jour
simultanée du Makefile, Docker, tests et documentation.
