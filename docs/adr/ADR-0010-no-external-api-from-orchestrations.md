# ADR-0010 — Une orchestration ne parle pas directement à une API externe

## Statut

Accepté progressivement — 27 juillet 2026

## Contexte

Certaines orchestrations historiques construisent des requêtes `urllib`
directement. Elles lisent alors les tokens, connaissent les versions d’API et
mélangent transport, transformation et effets.

Cette situation rend les politiques de timeout, d’authentification, de retry et
de redaction hétérogènes.

## Décision

Toute nouvelle orchestration utilise un service pour une interaction externe.
Elle ne construit ni URL fournisseur, ni en-tête d’authentification, ni requête
HTTP.

Les orchestrations existantes sont migrées lorsqu’une évolution traverse leur
code. Aucune réécriture globale n’est imposée.

## Conséquences positives

- transport simulable ;
- politique de secret mieux confinée ;
- fournisseur remplaçable ;
- logique de flux lisible.

## Coûts et limites

- dette maintenue temporairement dans les flux historiques ;
- extraction parfois délicate quand transport et transformation sont mêlés ;
- pas de couche Adapter universelle imposée : le service peut porter la
  frontière tant que son contrat reste clair.

## Révision

La décision sera considérée complètement appliquée quand aucune orchestration
active ne lira de credential ni n’effectuera d’appel HTTP fournisseur.
