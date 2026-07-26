# Idées argumentées

Les scores et priorités sont centralisés dans `FEATURE_PIPELINE.md` afin d’éviter des évaluations divergentes.

## 1. Le journal de causalité, pas seulement de logs — F02/F05

**Pourquoi ?** La question décisive n’est pas « quel endpoint a répondu ? » mais « quelle intention a causé quelle modification, à partir de quelle source ? ». Un journal causal rend reprise, audit et confiance possibles.

**Pourquoi pas ?** Il peut dériver vers une base événementielle complexe. Commencer avec un schéma append-only local et quelques états.

**Alternatives.** Temporal, Airflow, Prefect, Dagster. Ils gèrent mieux les workflows à grande échelle; Hanuman ne devrait les orchestrer/adopter que si les besoins de reprise dépassent réellement un moteur local.

## 2. Capability escrow — F04

**Pourquoi ?** Accorder temporairement « créer au plus trois pages sous ce parent » est plus sûr qu’un accès général implicite. Cette idée pourrait distinguer profondément Hanuman.

**Pourquoi pas ?** Les APIs externes ne savent pas toujours limiter aussi finement; l’application doit alors faire respecter une promesse qu’un bug peut contourner.

**Alternatives.** Scopes OAuth, comptes de service dédiés, intégrations Notion limitées. Les utiliser en premier; l’escrow Hanuman ajoute la contrainte métier.

## 3. Briefing inter-outils avec preuves — F07

**Pourquoi ?** C’est une valeur immédiatement compréhensible et introuvable dans chaque outil isolé. Chaque affirmation renvoie au mail, événement ou issue source.

**Pourquoi pas ?** Les briefings deviennent du bruit. Il faut un déclenchement choisi et mesurer les actions utiles, pas la quantité de texte.

**Alternatives.** Gemini/Google Workspace, Microsoft Copilot, Notion AI. Hanuman gagne seulement si l’utilisateur veut croiser des écosystèmes et choisir la destination.

## 4. Recherche fédérée éphémère — F14

**Pourquoi ?** Interroger en direct préserve fraîcheur et évite une copie globale.

**Pourquoi pas ?** Latence, quotas, disponibilité. Un petit cache de références peut être nécessaire.

**Alternatives.** OpenSearch/Elasticsearch, moteurs desktop. Ils sont meilleurs pour le plein texte massif; Hanuman doit les connecter, pas les reproduire.

## 5. Recettes comme documents portables — F13

**Pourquoi ?** Une orchestration pourrait être lisible, diffable et partageable sans code ni secrets.

**Pourquoi pas ?** Un DSL devient vite un langage médiocre. Ne créer un format qu’après plusieurs contrats stables; Python reste acceptable pour les cas complexes.

**Alternatives.** n8n, Make, Zapier, GitHub Actions. Les orchestrer ou exporter vers eux peut être préférable à créer un moteur visuel.

## 6. Mode simulation durable — F01

**Pourquoi ?** Conserver le plan et son empreinte permet d’approuver aujourd’hui et d’appliquer demain après vérification que les sources n’ont pas changé.

**Pourquoi pas ?** Une preview périme vite et crée une illusion de garantie. Elle doit afficher sa fraîcheur et invalider sur changement.

**Alternatives.** Dry-run ponctuel. Plus simple, suffisant pour V1.

## 7. Constellation opérationnelle — F10

**Pourquoi ?** Voir les flux, leurs dépendances et leur santé aide réellement à décider.

**Pourquoi pas ?** Une visualisation spectaculaire peut absorber beaucoup de temps sans améliorer un flux.

**Alternatives.** Tableau et timeline, probablement meilleurs en V1/V2. Le graphe n’arrive que si trois relations ou plus deviennent difficiles à comprendre linéairement.

## 8. « Quiet orchestration »

Une orchestration devrait optimiser le nombre de décisions évitées et de no-op, pas le nombre d’actions. **Pourquoi ?** La meilleure automatisation est celle qui ne dérange que lorsque l’humain apporte une vraie décision. **Pourquoi pas ?** Une action silencieuse peut masquer une panne; l’absence d’action doit rester observable. **Alternative :** notifications systématiques, rejetées car elles déplacent la charge au lieu de la réduire.

Évaluation associée à F03/F04 : U 9, D 7, L 9, C 6, R 4, O 8, H 10, priorité P1.
