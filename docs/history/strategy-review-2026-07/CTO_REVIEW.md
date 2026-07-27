# Revue CTO — synthèse décisionnelle

> Archive non normative — revue stratégique de juillet 2026.

## Découvertes majeures

1. Hanuman possède déjà une vraie séparation routes/orchestrations/services, mais la documentation surestime la couche adapter et l’uniformité des contrats.
2. Le registre de connecteurs fondé sur des capacités est probablement la meilleure graine architecturale du dépôt.
3. Le manque structurant n’est pas un connecteur : c’est le modèle d’exécution (`preview`, identité, état, reprise, preuve).
4. Obsidian → Notion et GitHub → Notion sont les deux meilleurs flux pour faire émerger ce modèle.
5. L’interface actuelle est organisée par domaines; l’interface cible devrait être organisée par intentions, effets et décisions.
6. Le modèle local-only protège Hanuman. Toute exposition réseau ou ambition SaaS crée un autre produit.
7. La documentation contient beaucoup de pensée utile, mais mélange constitution, réalité, historique et futur au point de fragiliser la décision.

Les évaluations chiffrées de toutes les propositions structurantes sont consolidées dans
`FEATURE_PIPELINE.md`. Ce rapport privilégie les décisions plutôt que de répéter ces scores.

## Idée la plus transformatrice

Faire de Hanuman un **plan de contrôle à capacités sous séquestre** : l’utilisateur n’accorde pas « Notion en écriture », mais « créer au plus trois pages sous ce parent pour ce run, après preview ». Cette gouvernance rendrait Hanuman distinct des outils d’automatisation et des agents généraux.

Pourquoi la retenir : elle renforce simultanément sécurité, confiance, agents et UX. Pourquoi elle peut échouer : elle demande un modèle d’effets précis et peut rendre les flux pénibles. Il faut commencer avec trois niveaux simples d’autonomie, pas un langage de politiques.

## Idées prometteuses

- Journal causal et reprise d’exécution.
- Briefing inter-outils sourcé, publié dans l’outil choisi.
- Recherche fédérée éphémère plutôt qu’index global.
- Constellation opérationnelle des flux, après une timeline utile.
- Recettes portables, seulement après stabilisation des contrats.

## Risques les plus importants

1. Automatiser ou agentifier avant idempotence et observabilité.
2. Exposer une API locale non authentifiée.
3. Confondre rapprochement Obsidian/Notion et synchronisation bidirectionnelle sûre.
4. Ajouter des plateformes plus vite que les connecteurs existants ne mûrissent.
5. Laisser le récit du projet diverger de son code et de ses mesures.

## Cinq prochaines décisions du propriétaire

1. Confirmer que le mode local mono-utilisateur est un invariant de V1/V2.
2. Désigner explicitement la source de vérité et la politique de conflit pour Obsidian ↔ Notion.
3. Adopter ou rejeter le contrat `plan → preview → apply → verify`.
4. Choisir le point d’entrée backend canonique et le statut des surfaces historiques.
5. Décider si la priorité produit des six prochains mois est la fiabilité de deux flux ou l’ajout de connecteurs. Recommandation : deux flux fiables.

## Désaccords avec l’état actuel

- **« La logique métier appartient entièrement à Hanuman »** est trop absolu. Les outils sources conservent leurs règles et leur sémantique; Hanuman possède la logique de coordination, pas toute la vérité métier.
- **La base de connaissances centrale** contredit la constitution sauf si elle ne stocke que références, provenance et état d’exécution.
- **Le plugin system** est prématuré : les adapters vides montrent que l’abstraction n’est pas encore prouvée.
- **Le graphe de connaissances** est une mauvaise priorité. Un graphe opérationnel est cohérent; la connaissance doit rester dans les outils spécialisés.
- **Les agents spécialisés** ne sont pas une prochaine étape. Ils viennent après gouvernance et preuve d’exécution.

## Verdict CTO

Hanuman n’a pas besoin de devenir plus grand; il doit devenir plus précis. Sa trajectoire exceptionnelle consiste à être le meilleur système personnel pour comprendre, autoriser et prouver des transformations entre outils. Le prochain avantage ne viendra pas d’une nouvelle intégration, mais d’une exécution à laquelle l’utilisateur peut faire confiance.
