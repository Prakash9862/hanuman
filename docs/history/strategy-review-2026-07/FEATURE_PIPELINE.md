# Pipeline de fonctionnalités

> Archive non normative — revue stratégique de juillet 2026.

## Méthode

Scores sur 10. `U` impact utilisateur, `D` impact développeur, `L` valeur long terme, `C` complexité, `R` risque, `O` originalité, `H` cohérence avec Hanuman. Priorité : P0 verrou, P1 prochain, P2 ensuite, P3 exploratoire, Rejet.

La priorité n’est pas une moyenne : une forte cohérence et un risque maîtrisable dominent l’originalité. Toute proposition détaillée dans les autres documents doit être arbitrée par ce registre avant réalisation.

| ID | Fonctionnalité | U | D | L | C | R | O | H | Priorité |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| F01 | Contrat `plan/preview/apply/verify` | 9 | 9 | 10 | 6 | 3 | 6 | 10 | P0 |
| F02 | Identité de run et machine d’état | 8 | 10 | 10 | 5 | 2 | 4 | 10 | P0 |
| F03 | Inbox d’approbation des effets | 9 | 7 | 9 | 6 | 3 | 6 | 10 | P1 |
| F04 | Politiques par capacité/cible/budget | 8 | 8 | 10 | 7 | 4 | 7 | 10 | P1 |
| F05 | Reprise et compensation d’échec partiel | 9 | 9 | 10 | 8 | 5 | 7 | 10 | P1 |
| F06 | Contrat commun de connecteur | 6 | 10 | 9 | 7 | 4 | 4 | 9 | P2 |
| F07 | Briefing quotidien Gmail + Calendar + GitHub | 9 | 5 | 8 | 6 | 5 | 7 | 9 | P2 |
| F08 | Google Drive lecture ciblée | 7 | 6 | 8 | 7 | 6 | 4 | 8 | P2 conditionnel |
| F09 | Déclencheurs planifiés bornés | 8 | 6 | 8 | 7 | 6 | 3 | 9 | P2 |
| F10 | Constellation opérationnelle | 6 | 5 | 6 | 7 | 3 | 8 | 7 | P3 |
| F11 | Agent planificateur en lecture | 7 | 5 | 8 | 8 | 7 | 8 | 8 | P3/V4 |
| F12 | Agent de triage supervisé | 8 | 5 | 8 | 8 | 8 | 7 | 8 | P3/V4 |
| F13 | Recettes portables signées | 5 | 8 | 9 | 8 | 6 | 8 | 9 | P3/V5 |
| F14 | Recherche fédérée à la demande | 8 | 6 | 8 | 7 | 6 | 6 | 9 | P2 |
| F15 | Synchronisation Notion → Obsidian | 7 | 5 | 6 | 9 | 9 | 4 | 6 | P3 conditionnel |
| F16 | Index global propriétaire | 6 | 4 | 4 | 9 | 9 | 4 | 3 | Rejet |
| F17 | Marketplace publique de plugins | 4 | 5 | 5 | 10 | 9 | 6 | 4 | Rejet |
| F18 | Agent général autonome | 5 | 3 | 3 | 10 | 10 | 7 | 1 | Rejet |
| F19 | Éditeur de notes Hanuman | 3 | 2 | 2 | 9 | 6 | 2 | 1 | Rejet |
| F20 | SaaS multi-tenant | 4 | 3 | 4 | 10 | 10 | 3 | 2 | Rejet |
| F21 | Mode local-only explicite jusqu’à V2 | 8 | 8 | 9 | 1 | 1 | 2 | 10 | P0 |
| F22 | Point d’entrée backend canonique documenté | 5 | 8 | 7 | 1 | 1 | 1 | 9 | P1 |
| F23 | Auth applicative avant toute exposition réseau | 10 | 8 | 10 | 6 | 4 | 2 | 10 | P0 conditionnel |
| F24 | Permissions `0600` uniformes pour les tokens | 8 | 7 | 9 | 2 | 2 | 1 | 10 | P1 |
| F25 | Convention d’erreurs publiques | 7 | 9 | 9 | 5 | 3 | 2 | 9 | P1 |
| F26 | Budgets par orchestration | 7 | 8 | 9 | 4 | 2 | 5 | 10 | P1 |
| F27 | Restructuration documentaire progressive | 6 | 9 | 8 | 4 | 2 | 2 | 8 | P1 |
| F28 | Unification progressive des politiques HTTP | 5 | 9 | 8 | 7 | 5 | 2 | 8 | P2 |
| F29 | Adoption immédiate d’une stack d’observabilité externe | 3 | 4 | 4 | 7 | 5 | 2 | 5 | Rejet maintenant |
| F30 | Implémentation immédiate de la couche adapters | 4 | 6 | 6 | 8 | 6 | 2 | 6 | Rejet maintenant |

## Fiches synthétiques

### F01 — Preview transactionnelle

**Description/valeur.** Montrer les effets avant écriture et vérifier après. C’est le principal multiplicateur de confiance.
**Difficulté/dépendances.** Séparer calcul et effet; modèles de diff par plateforme; dépend de l’identité des objets.
**Pourquoi Hanuman.** C’est précisément la valeur d’un orchestrateur. Aucun outil source ne voit tout le flux.

### F02 — Run state

**Description/valeur.** Remplacer « processus lancé » par un état durable et corrélé.
**Difficulté/dépendances.** Schéma versionné et écriture atomique. Pas besoin initialement d’une file distribuée.
**Pourquoi Hanuman.** Sans cela, agents, scheduler et reprise sont irresponsables.

### F03/F04 — Consentement et politiques

**Description/valeur.** Une file de décisions et des règles comme « lecture libre, écriture Notion approuvée, jamais supprimer ».
**Difficulté.** Une politique trop complexe devient incompréhensible; commencer par trois niveaux d’autonomie.
**Alternative.** Permissions OAuth seules : nécessaires mais insuffisantes, car elles ne capturent pas l’intention.

### F05 — Reprise

**Description/valeur.** Rejouer seulement les étapes manquantes ou compenser.
**Pourquoi pas maintenant partout.** La compensation universelle n’existe pas; la définir flux par flux.

### F06 — Contrat connecteur

**Valeur.** Uniformiser erreurs, quotas, pagination et health.
**Pourquoi pas tout de suite.** Une interface abstraite inventée avant trois implémentations conformes cristalliserait de mauvaises hypothèses.

### F07 — Briefing quotidien

**Valeur.** Cas d’usage phare : messages importants, agenda, issues et contexte, publié où l’utilisateur choisit.
**Alternative.** Utiliser les résumés natifs Google/Microsoft. Hanuman n’est préférable que pour la synthèse inter-outils et la provenance.

### F08 — Drive ciblé

**Valeur.** Fournir des documents explicitement sélectionnés à une orchestration.
**Pourquoi pas aspiration globale.** Permissions, coût d’indexation et données sensibles explosent. Le mode ciblé est le seul cohérent.

### F09 — Scheduling

**Valeur.** Déclencher des recettes fiables.
**Dépendance.** F02/F04/F05. Un cron qui lance une orchestration non idempotente est une fabrique à incidents.

### F10 — Constellation

**Valeur.** Comprendre relations opérationnelles, fraîcheur et erreurs.
**Pourquoi pas graphe de connaissance.** Obsidian/Notion font mieux la connaissance; Hanuman doit visualiser les flux.

### F11/F12 — Agents

**Valeur.** Plans adaptatifs et triage.
**Alternative.** Règles déterministes, préférables tant qu’elles suffisent. L’agent n’est retenu que si l’ambiguïté apporte une valeur mesurée.

### F13 — Recettes portables

**Valeur.** Pérennité sans partager secrets ni données.
**Risque.** Supply chain de recettes; signature et permissions lisibles obligatoires.

### F14 — Recherche fédérée

**Valeur.** Interroger les outils en direct selon une intention, agréger des références.
**Alternative rejetée.** Index central exhaustif. La fédération est plus lente mais respecte fraîcheur et souveraineté.

### F15 — Notion → Obsidian

**Valeur.** Rapatrier certains contenus édités.
**Condition.** Mapping explicite et conflits résolus. Tant que « qui gagne ? » n’a pas de réponse, cette idée est dangereuse.

### F16–F20 — Rejets

Ils transforment Hanuman en base de données, plateforme, éditeur ou SaaS. Chacun impose un nouveau métier, un modèle de sécurité et une exploitation qui détournent du hub personnel. Ils ne sont pas « pour plus tard »; ils sont rejetés sauf changement explicite de constitution.

### F21–F30 — Gouvernance et fondations

F21–F27 sont des décisions de maîtrise du système : préserver le modèle local, réduire les
ambiguïtés, sécuriser les tokens, rendre erreurs et budgets explicites, puis remettre la
documentation en ordre. F23 ne demande pas de construire une authentification maintenant :
il interdit l’exposition réseau tant qu’elle n’existe pas.

F28 doit être remboursé au passage plutôt que par une réécriture de tous les clients HTTP.
F29 est rejeté jusqu’à ce que les événements locaux aient un schéma cohérent. F30 est rejeté
jusqu’à ce que trois connecteurs prouvent une interface commune; des dossiers vides ne sont
pas une raison suffisante pour fabriquer une abstraction.
