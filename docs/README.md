# Documentation de Hanuman

Cette documentation décrit Hanuman tel qu’il doit être compris, puis vérifie
chaque capacité contre le code actuel.

## Parcours recommandé

| Ordre | Document | Question traitée |
|---:|---|---|
| 1 | [Vision](project/vision.md) | Qu’est-ce que Hanuman et pourquoi existe-t-il ? |
| 2 | [Concepts](project/concepts.md) | Quel vocabulaire employer ? |
| 3 | [Architecture](project/architecture.md) | Comment les couches collaborent-elles ? |
| 4 | [État actuel](project/current-state.md) | Qu’est-ce qui existe réellement ? |
| 5 | [Guide développeur](developers/guide.md) | Comment contribuer sans brouiller les responsabilités ? |

## Référence

- [Connecteurs](connectors/README.md)
- [Orchestrations](orchestrations/README.md)
- [API](reference/api.md)
- [Configuration](operations/configuration.md)
- [Exploitation locale](operations/local-development.md)
- [Sécurité](operations/security.md)
- [Tests](developers/testing.md)

## Décisions et évolution

- [Index des ADR](adr/README.md)
- [Roadmap](roadmap/README.md)
- [Spécifications proposées](specs/README.md)

Les ADR décrivent des décisions. La roadmap et les spécifications décrivent des
intentions conditionnelles. Elles ne prouvent pas qu’une capacité est
implémentée.

## Histoire

- [Index historique](history/README.md)
- [Audit documentaire du 27 juillet 2026](history/documentation-audit-2026-07-27.md)

Les archives expliquent l’évolution du projet mais ne sont jamais une référence
opérationnelle.

## Politique de vérité

L’ordre de preuve est :

```text
comportement testé > code actif > configuration > documentation de référence
                    > ADR > spécification > roadmap > archive
```

Un document de référence distingue toujours :

- **disponible** : présent dans le code actif ;
- **vérifié** : observé par un test ou une commande datée ;
- **limité** : présent mais incomplet ou fragile ;
- **envisagé** : non disponible, conservé comme direction.

Les nombres de tests, la couverture et les versions de dépendances ne sont pas
des vérités durables. Les commandes permettant de les mesurer font référence.
