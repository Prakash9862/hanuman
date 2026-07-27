# Documentation stratégique de Hanuman

Ce dossier distingue désormais les **références actives** des **rapports d’audit** et des **documents de travail**.

Le but est simple : une décision importante doit avoir une seule source de vérité. Les autres documents peuvent l’expliquer, l’évaluer ou conserver son historique, mais ne doivent pas créer une stratégie parallèle.

## Ordre de lecture canonique

1. [`HANUMAN.md`](HANUMAN.md) — constitution, mission, limites et règles immuables.
2. [`ROADMAP.md`](ROADMAP.md) — seuils de capacité et ordre de réalisation.
3. [`FEATURE_PIPELINE.md`](FEATURE_PIPELINE.md) — évaluation et sélection des fonctionnalités candidates.
4. [`TECH_DEBT.md`](TECH_DEBT.md) — dette active, priorisée et vérifiable.
5. Les documents spécialisés encore actifs : sécurité, observabilité, performance, UX et agents.

Les décisions architecturales irréversibles ou structurantes doivent être enregistrées dans `docs/adr/`, pas ajoutées sous forme d’un nouveau rapport stratégique.

## Documents canoniques

| Document | Rôle | Décision |
|---|---|---|
| `HANUMAN.md` | Constitution du projet | **Garder et rendre canonique** |
| `ROADMAP.md` | Ordre des capacités et critères de sortie | **Garder, resserrer sur les phases utiles** |
| `FEATURE_PIPELINE.md` | Entrée et classement des fonctionnalités | **Garder** |
| `TECH_DEBT.md` | Registre de dette active | **Garder si chaque élément possède une preuve et une priorité** |
| `SECURITY.md` | Politique de sécurité produit | **Garder, relier aux runbooks** |
| `OBSERVABILITY.md` | Modèle d’exécution et de preuve | **Garder** |
| `PERFORMANCE.md` | Budgets et contraintes mesurables | **Garder seulement les exigences vérifiables** |
| `UX.md` | Principes d’interface centrés sur l’intention et les effets | **Garder** |
| `AGENTS.md` | Conditions d’introduction d’agents bornés | **Garder comme politique future, hors roadmap immédiate** |

## Rapports d’audit à archiver après intégration

Ces documents décrivent un état du dépôt à une date donnée. Ils sont utiles comme preuves historiques, mais ne doivent pas rester des sources concurrentes de stratégie.

| Document | Destination prévue | Éléments à intégrer avant archivage |
|---|---|---|
| `ARCHITECTURE_REVIEW.md` | `docs/history/strategy/` | Constats encore vrais, décisions nécessitant un ADR |
| `CHIEF_ARCHITECT_REPORT.md` | `docs/history/strategy/` | Recommandations acceptées et risques ouverts |
| `CONNECTORS_REVIEW.md` | `docs/history/strategy/` | Contrats de connecteurs et écarts réels |
| `CONTRADICTIONS_AND_IMPLICIT_DECISIONS.md` | `docs/history/strategy/` | Décisions explicites, dettes et invariants |
| `CTO_REVIEW.md` | `docs/history/strategy/` | Priorités retenues et preuves techniques |
| `EVIDENCE_LEDGER.md` | `docs/history/strategy/` ou registre actif dédié | Conserver seulement si maintenu et daté |
| `ORCHESTRATIONS_REVIEW.md` | `docs/history/strategy/` | Contrats d’exécution et écarts réels |
| `README_REVIEW.md` | `docs/history/strategy/` | Corrections encore absentes du README principal |

Un rapport archivé ne doit plus être modifié, sauf correction factuelle clairement signalée.

## Documents à fusionner ou reclasser

| Document | Décision cible | Motif |
|---|---|---|
| `LONG_TERM_VISION.md` | **Fusionner les principes durables dans `HANUMAN.md`; conserver ensuite en historique** | La constitution et la roadmap couvrent déjà l’essentiel de la trajectoire |
| `QUICK_WINS.md` | **Fusionner les actions retenues dans `ROADMAP.md` ou `TECH_DEBT.md`, puis archiver** | Une liste de gains rapides vieillit vite et crée une seconde roadmap |
| `IDEAS.md` | **Reclasser en incubateur non engageant** | Une idée n’est ni une décision ni un engagement de roadmap |

## Règles documentaires

1. **Une responsabilité, un document canonique.**
2. **Le README principal est une porte d’entrée**, pas une constitution ni un rapport d’audit.
3. **Un audit est daté et archivable.** Il décrit, mais ne gouverne pas durablement.
4. **Une décision structurante devient un ADR.**
5. **Une fonctionnalité candidate passe par `FEATURE_PIPELINE.md`.**
6. **Une action retenue apparaît dans `ROADMAP.md` ou `TECH_DEBT.md`, jamais dans plusieurs listes concurrentes.**
7. **Les chiffres volatils** — nombre de tests, couverture, versions, état CI — doivent provenir d’une commande reproductible ou d’un badge automatisé, pas d’une phrase figée.
8. **Toute nouvelle documentation doit indiquer son statut** : canonique, proposition, audit daté, runbook, spécification ou historique.

## Migration prévue

La consolidation se fait sans suppression brutale :

1. identifier les informations uniques de chaque rapport ;
2. intégrer les décisions retenues dans les documents canoniques ou les ADR ;
3. déplacer les rapports terminés vers `docs/history/strategy/` ;
4. simplifier le README principal ;
5. vérifier les liens et supprimer uniquement les doublons devenus sans valeur.

## Invariant éditorial

> Toute abstraction documentaire doit payer son coût de maintenance.

Un document doit soit gouverner une décision, expliquer un contrat, guider une opération, spécifier un comportement ou conserver une preuve historique. S’il ne remplit aucun de ces rôles, il doit être fusionné ou supprimé.
