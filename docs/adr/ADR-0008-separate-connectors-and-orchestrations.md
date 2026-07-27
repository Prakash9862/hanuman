# ADR-0008 — Séparer les connecteurs des orchestrations

## Statut

Accepté — 27 juillet 2026

## Contexte

Une API externe change pour des raisons techniques. Une orchestration change
pour des raisons de produit ou de flux. Mélanger ces responsabilités couple une
intention à un fournisseur et rend les tests dépendants du réseau.

Le code actuel respecte partiellement cette séparation ; certaines
orchestrations historiques utilisent encore des appels HTTP directs.

## Décision

Un connecteur gère la frontière technique d’un système. Une orchestration
coordonne des capacités et possède les règles du flux.

```text
orchestration -> service -> connecteur -> système externe
```

Le catalogue des connecteurs ne doit pas devenir un catalogue
d’orchestrations, et une page de connecteur ne doit pas définir seule le
produit.

## Conséquences positives

- remplacement d’une API mieux confiné ;
- orchestration testable hors réseau ;
- capacités réutilisables dans plusieurs flux ;
- permissions et quotas visibles à la bonne frontière.

## Coûts et limites

- plus d’interfaces et de fichiers ;
- migration progressive des appels directs ;
- une abstraction n’est créée qu’après un besoin réel, pas pour uniformiser
  artificiellement tous les fournisseurs.

## Révision

Cette décision pourra être précisée par un contrat de connecteur lorsque
plusieurs implémentations auront démontré les mêmes invariants.
