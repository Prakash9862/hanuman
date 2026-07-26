# Roadmap pluriannuelle

Les versions sont des seuils de capacité, pas des promesses calendaires. Une version ne commence que lorsque les critères de sortie de la précédente sont observés. Les scores détaillés des fonctionnalités sont dans `FEATURE_PIPELINE.md`.

## V1 — Hanuman fiable (0–6 mois)

**Objectif.** Faire des flux actuels un produit personnel sûr : point d’entrée canonique, exécutions identifiables, contrats d’erreur, tests HTTP fonctionnels, secrets et permissions locales vérifiés.

**Dépendances/prérequis.** Aucun nouveau connecteur. Décisions sur source de vérité Obsidian/Notion et exposition strictement locale.

**Bénéfices.** Confiance, diagnostic, base honnête pour l’automatisation.

**Risques/difficultés.** Travail peu visible; tentation de construire l’UI avant le modèle d’exécution.

**Estimation.** 8–12 semaines à temps partiel.

**Critère de sortie.** Deux orchestrations de référence ont `plan/preview/apply/verify`, une identité, un état final et une reprise testée.

## V2 — Hanuman opérable (6–18 mois)

**Objectif.** Ajouter un journal d’exécution structuré, un inbox d’approbation, des politiques par capacité et une UI centrée sur les effets.

**Dépendances/prérequis.** V1; schéma d’exécution stable; conventions de redaction.

**Bénéfices.** Automatisations supervisées, erreurs réparables, compréhension immédiate.

**Risques/difficultés.** Construire un scheduler ou une file trop tôt. Commencer par déclenchement manuel et reprise explicite.

**Estimation.** 4–8 mois.

**Critère de sortie.** L’utilisateur peut répondre à « qu’est-ce qui va changer ? », « qu’est-ce qui a changé ? » et « comment reprendre ? » depuis une seule surface.

## V3 — Hanuman extensible (18–36 mois)

**Objectif.** Formaliser un contrat de connecteur validé par Notion, Obsidian, GitHub et Google; ajouter Drive seulement sur cas d’usage prouvé; déclencheurs planifiés bornés.

**Dépendances/prérequis.** Trois implémentations convergentes, tests de contrat, budget de quotas.

**Bénéfices.** Ajout de capacités sans exceptions croissantes.

**Risques/difficultés.** Un plugin system peut devenir un produit en soi. Refuser marketplace et exécution tierce non fiable.

**Estimation.** 9–15 mois.

**Critère de sortie.** Un connecteur interne neuf peut être ajouté avec auth, health, pagination, erreurs et tests sans modifier le moteur.

## V4 — Hanuman assisté par agents (3–5 ans)

**Objectif.** Introduire des agents spécialisés de planification, triage et synthèse, toujours bornés par capacités, budget et consentement.

**Dépendances/prérequis.** Audit trail complet, politiques, sandbox d’outils, évaluations, provenance.

**Bénéfices.** Passage de workflows pré-écrits à des plans adaptatifs supervisés.

**Risques/difficultés.** Hallucination, prompt injection via contenus connectés, coûts, boucles d’action. Une autonomie générale reste interdite.

**Estimation.** 12–24 mois après V3.

**Critère de sortie.** Chaque action agentique est attribuable, reproductible ou explicable, budgétée et révocable.

## V5 — Hanuman comme protocole personnel (5–10 ans)

**Objectif.** Permettre plusieurs profils/appareils et des échanges de recettes portables sans centraliser les données; politiques synchronisables et exécution locale/fédérée.

**Dépendances/prérequis.** Formats versionnés, identité cryptographique des recettes, modèle de confiance multi-nœuds.

**Bénéfices.** Durabilité au-delà d’un poste et d’un fournisseur.

**Risques/difficultés.** Complexité distribuée disproportionnée pour un projet personnel. Cette version doit être annulée si l’usage mono-utilisateur reste optimal.

**Estimation.** Pluriannuelle, conditionnelle.

**Critère de sortie.** Une recette peut être déplacée entre deux installations sans déplacer les secrets ni compromettre les données sources.

## Ce qui n’est volontairement pas planifié

- Remplacer Notion/Obsidian par une base ou un éditeur Hanuman.
- Marketplace publique de plugins.
- Agent autonome général.
- Indexation exhaustive de Gmail/Drive.
- Multi-tenant SaaS.

Ces idées augmentent davantage le périmètre et le risque que la valeur d’orchestration.
