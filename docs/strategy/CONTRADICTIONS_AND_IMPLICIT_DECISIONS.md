# Contradictions et décisions implicites

## Contradictions structurantes

### 1. Hub d’orchestration contre système cognitif central

[FAIT] Le README affirme que les données convergent vers un même moteur et décrit une mémoire persistante, un graphe de connaissances et une base de connaissances.

[FAIT] La mission fondatrice affirme que Hanuman ne remplace pas les outils et que les connecteurs communiquent avec les systèmes externes.

[INFÉRENCE] « Convergence » peut signifier convergence des capacités ou copie des données; le dépôt ne tranche pas cette ambiguïté.

[PROPOSITION] Définir Hanuman comme plan de contrôle et limiter son stockage durable à l’état d’exécution, la provenance, les politiques et des références.

[CONTRE-ANALYSE] Cette limite réduit les possibilités de recherche rapide et de raisonnement hors ligne.

[PROPOSITION] Préférer une recherche fédérée et des caches bornés; n’accepter un index que pour un cas mesuré impossible à satisfaire autrement.

### 2. Architecture adapter documentée contre code sans adapters

[FAIT] Le README décrit les adapters comme frontière jetable.

[FAIT] Les clients adapters GitHub et Notion sont vides, tandis que `httpx`, `requests` et `urllib` sont employés ailleurs.

[INFÉRENCE] L’architecture réelle est « routes → orchestrations/services → protocole », avec plusieurs exceptions, et non celle décrite.

[PROPOSITION] Marquer les adapters comme option exploratoire, sans les implémenter avant convergence naturelle de trois connecteurs.

[CONTRE-ANALYSE] Reporter l’unification prolonge la duplication des clients HTTP.

[PROPOSITION] Uniformiser d’abord les politiques observables — timeouts, erreurs, redaction — sans imposer immédiatement une classe commune.

### 3. Local-only contre surface de contrôle puissante

[FAIT] La documentation sécurité suppose un poste local mono-utilisateur.

[FAIT] Des routes lancent des processus, lisent des données et déclenchent des écritures sans garde d’authentification applicative visible.

[INFÉRENCE] Le système est acceptable uniquement tant que la frontière réseau locale est effectivement maintenue.

[PROPOSITION] Faire de « loopback uniquement » un invariant vérifiable jusqu’à décision explicite d’un autre modèle.

[CONTRE-ANALYSE] Cette décision limite l’accès multi-appareils.

[PROPOSITION] Rejeter l’accès distant avant un besoin concret; un tunnel authentifié existant serait préférable à un système d’identité maison.

### 4. Orchestration explicable contre lancement détaché

[FAIT] Le dashboard retourne `started` immédiatement après `subprocess.Popen`.

[FAIT] Le journal de runs est distinct des logs techniques et aucun `run_id` commun n’est imposé.

[INFÉRENCE] « Lancement accepté » peut être confondu avec « orchestration réussie » par une interface ou un utilisateur.

[PROPOSITION] Définir une machine d’état d’exécution avant scheduler ou agents.

[CONTRE-ANALYSE] Une machine d’état peut devenir un moteur de workflow disproportionné.

[PROPOSITION] Commencer avec six états et un journal append-only; ne pas introduire de broker distribué.

### 5. Qualité déclarée contre qualité vérifiable

[FAIT] Le README déclare un nombre de tests et une couverture non reliés à une commande datée.

[FAIT] La mesure locale documentée est partielle à cause d’un blocage HTTP.

[INFÉRENCE] La confiance qualitative est supérieure à la preuve reproductible disponible.

[PROPOSITION] Remplacer les chiffres statiques par une date, une commande et un lien vers CI.

## Décisions implicites à rendre explicites

| Classe | Décision implicite observée | Pourquoi elle compte |
|---|---|---|
| [INFÉRENCE] | Notion sert souvent de destination de publication. | détermine idempotence et propriété |
| [INFÉRENCE] | Obsidian est traité comme filesystem local, non comme API. | détermine atomicité et sécurité des chemins |
| [INFÉRENCE] | Une orchestration est à la fois module Python, commande CLI et action API. | crée trois contrats d’exécution |
| [INFÉRENCE] | Les erreurs sont conçues pour un humain local plus que pour un client stable. | explique les formats divergents |
| [INFÉRENCE] | Le projet optimise l’étendue fonctionnelle par exploration. | explique la croissance Resources/Chess |
| [HYPOTHÈSE] | Chess est peut-être un laboratoire personnel prioritaire plutôt qu’un pilier général de Hanuman. | l’historique récent est fortement concentré sur Chess |
| [HYPOTHÈSE] | Le propriétaire valorise fortement l’expérience visuelle Obsidian. | thèmes et graphes dominent la branche Chess |

## Invariants observés et violations

| Invariant | Classe | Respect | Violation ou tension |
|---|---|---|---|
| Les outils externes restent spécialisés. | [INFÉRENCE] | connecteurs et flux nommés | vision de base centrale |
| Les routes adaptent, les orchestrations coordonnent. | [INFÉRENCE] | séparation générale | routes appelant directement services et gestion d’erreurs métier |
| Les tests évitent les services réels. | [FAIT] | mocks nombreux dans les tests inspectés | CI reçoit néanmoins des secrets réels |
| Les écritures sont explicites. | [INFÉRENCE] | endpoints POST et fonctions nommées | lancement générique de modules détectés |
| La configuration vient de l’environnement. | [FAIT] | mécanisme dominant | chemins/identités codés et plusieurs chargeurs |

## Dettes invisibles

| Priorité | Classe | Dette | Justification |
|---|---|---|---|
| P0 conditionnel | [PROPOSITION] | Frontière réseau non gouvernée | devient critique dès exposition |
| P1 | [PROPOSITION] | Gouvernance de branche Chess | 29 commits et responsabilités concurrentes |
| P1 | [PROPOSITION] | Source de vérité Obsidian/Notion non décidée | bloque une sync sûre |
| P1 | [PROPOSITION] | Sémantique d’exécution absente | bloque reprise, scheduler et agents |
| P1 | [PROPOSITION] | Dette produit d’expansion | connecteurs/features progressent plus vite que les contrats |
| P2 | [PROPOSITION] | Dette UX par pages de connecteurs | l’intention inter-outils reste secondaire |
| P2 | [PROPOSITION] | Dette documentaire de vérité | décisions et chiffres concurrents |
| P2 | [PROPOSITION] | Dette IA de provenance/évaluation | module QA non couvert et politiques futures absentes |
| P2 | [PROPOSITION] | Dette de gouvernance des changements | aucun seuil visible de promotion prototype→stable |
| P3 | [PROPOSITION] | Dette cosmétique et dossiers réservés | bruit réel mais faible impact |

## Simplifications recommandées

[PROPOSITION] Fusionner conceptuellement « service » et « connecteur » dans le langage produit, tout en gardant les modules actuels tant qu’une migration n’est pas justifiée.

[CONTRE-ANALYSE] Une fusion de modules maintenant créerait un refactoring massif sans valeur utilisateur.

[PROPOSITION] Fusionner les documents README techniques redondants par extraction progressive, sans supprimer l’historique en une fois.

[PROPOSITION] Supprimer de la roadmap active les plugins, le graphe de connaissances, la mémoire propriétaire et le SaaS.

[CONTRE-ANALYSE] Cette réduction peut sembler diminuer l’ambition.

[INFÉRENCE] Elle concentre en réalité l’ambition sur une propriété plus rare : des transformations inter-outils gouvernées et prouvables.

