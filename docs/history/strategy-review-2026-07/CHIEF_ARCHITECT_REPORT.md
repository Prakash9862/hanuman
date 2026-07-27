# Les dix premières décisions du CTO

> Archive non normative — revue stratégique de juillet 2026.

## Cadre

[FAIT] Cette revue repose sur le tree `HEAD`, les tests et documents suivis, les références Git locales, les commits récents et le working tree observé.

[HYPOTHÈSE] Le comportement quotidien réel du propriétaire peut révéler des priorités absentes du dépôt.

[PROPOSITION] Les décisions ci-dessous sont ordonnées par dépendance et réduction de risque, non par visibilité.

## 1. Geler l’expansion fonctionnelle pendant un cycle court

[PROPOSITION] Je n’accepterais aucun nouveau connecteur, agent, graphe ou écran de domaine pendant quatre à six semaines.

[FAIT] Le registre contient déjà 11 connecteurs et dix modules d’orchestration, tandis que les contrats d’exécution et d’erreur restent hétérogènes.

[INFÉRENCE] Une fonctionnalité supplémentaire augmenterait le coût de stabilisation plus vite que la valeur.

[CONTRE-ANALYSE] Un gel peut casser l’élan créatif et retarder un besoin urgent.

[PROPOSITION] J’autoriserais seulement une exception liée à un usage hebdomadaire démontré et impossible avec les capacités présentes.

## 2. Déclarer le modèle local-only comme invariant de V1/V2

[PROPOSITION] Je ferais approuver explicitement : écoute loopback, propriétaire unique, aucune exposition Internet.

[FAIT] Les routes offrent des capacités puissantes sans authentification applicative visible.

[INFÉRENCE] Ce choix transforme un risque P0 latent en contrainte architecturale maîtrisée.

[CONTRE-ANALYSE] Il bloque l’accès distant natif.

[PROPOSITION] Si l’accès distant devient nécessaire, j’évaluerais d’abord un tunnel authentifié existant.

## 3. Arbitrer immédiatement la branche `feat/chess-analysis-v1`

[PROPOSITION] Je déciderais sous une semaine : intégrer par morceaux, réduire, ou archiver avec enseignements.

[FAIT] Cette branche porte 29 commits propres et touche 16 fichiers, dont certains évoluent aussi sur `main`.

[INFÉRENCE] Attendre augmente les conflits techniques et rend l’arbitrage produit plus coûteux.

[CONTRE-ANALYSE] Fusionner vite peut importer 1 833 lignes avant validation de leur cohérence avec Hanuman.

[PROPOSITION] Je ne fusionnerais pas la branche en bloc; je demanderais une carte capacités/effets/tests et des unités indépendantes.

## 4. Décider la source de vérité Obsidian ↔ Notion

[PROPOSITION] Je choisirais pour chaque champ : autorité, direction, identité, conflit et données non représentables.

[FAIT] Obsidian → Notion est implémenté; une vue de rapprochement existe; la documentation emploie parfois « ↔ ».

[INFÉRENCE] L’étiquette bidirectionnelle crée une promesse supérieure au contrat démontré.

[CONTRE-ANALYSE] Un modèle complet de conflit peut être excessif si le besoin réel est seulement de publier.

[PROPOSITION] Si la publication suffit, je renommerais conceptuellement le produit « publication Obsidian → Notion » et rejetterais le retour.

## 5. Adopter le contrat `plan → preview → apply → verify`

[PROPOSITION] Je l’appliquerais d’abord à Obsidian → Notion, sans créer de moteur générique.

[FAIT] Les écritures actuelles sont exécutées dans le même flux qui construit les données.

[INFÉRENCE] Séparer intention et effet améliore simultanément confiance, testabilité et future gouvernance agentique.

[CONTRE-ANALYSE] La preview peut doubler les appels et devenir périmée.

[PROPOSITION] Je commencerais par un dry-run local avec empreinte de source et invalidation explicite.

## 6. Définir une identité et six états d’exécution

[PROPOSITION] Chaque run aurait `planned`, `awaiting_approval`, `running`, `partial`, `succeeded` ou `failed`, avec un `run_id`.

[FAIT] Le dashboard répond `started` après création d’un processus détaché.

[INFÉRENCE] Sans état commun, l’interface ne peut distinguer acceptation, progression et résultat.

[CONTRE-ANALYSE] Un moteur de workflow maison serait une distraction.

[PROPOSITION] Je limiterais V1 à un journal append-only local; aucun broker, worker distribué ou ordonnanceur.

## 7. Désigner un point d’entrée et une convention d’erreur canoniques

[PROPOSITION] Je choisirais `hanuman.main:app` comme candidat à confirmer, puis je documenterais le statut de `api/core/main.py`.

[FAIT] Deux applications FastAPI existent et les routes renvoient des erreurs sous plusieurs formes, dont des objets `ok: false` avec réponse HTTP réussie.

[INFÉRENCE] Cette ambiguïté multiplie les contrats frontend, tests et observabilité.

[CONTRE-ANALYSE] Uniformiser tout en une fois créerait une migration de grande taille.

[PROPOSITION] J’appliquerais la convention uniquement aux routes nouvelles ou modifiées, avec inventaire des exceptions.

## 8. Unifier les politiques de secrets et configuration avant les abstractions

[PROPOSITION] Je définirais une source de configuration, une politique de permissions token et un inventaire de scopes.

[FAIT] Quatre styles de lecture de configuration coexistent et Gmail/Calendar n’appliquent pas la même politique de fichier token.

[INFÉRENCE] Une politique commune apporte plus de sécurité qu’une couche adapter vide.

[CONTRE-ANALYSE] Centraliser tous les paramètres peut créer un objet de configuration omniscient.

[PROPOSITION] Je centraliserais les règles, pas nécessairement tous les objets ou modules.

## 9. Réparer la preuve de qualité avant d’augmenter le seuil

[PROPOSITION] Je rendrais la suite HTTP reproductible, daterais les métriques et retirerais les chiffres statiques non vérifiables.

[FAIT] Le README annonce 146 tests et 92 %, tandis que le rapport local documente d’autres chiffres et un blocage `TestClient`.

[INFÉRENCE] Un seuil élevé non exécutable produit moins de confiance qu’un périmètre inférieur clairement mesuré.

[CONTRE-ANALYSE] Se concentrer sur l’outillage peut retarder les flux métier.

[PROPOSITION] Je bornerais cette décision à un diagnostic court avec critère d’arrêt, sans mise à jour opportuniste de dépendances.

## 10. Remplacer la roadmap d’accumulation par des critères de promotion

[PROPOSITION] Chaque connecteur et orchestration passerait par expérimental, alpha, bêta et stable selon des critères observables.

[FAIT] Le dépôt contient des intégrations de maturités très différentes présentées dans un même registre.

[INFÉRENCE] La profondeur des capacités utiles est plus importante que leur nombre.

[CONTRE-ANALYSE] Des gates trop rigides peuvent étouffer les prototypes personnels.

[PROPOSITION] Les prototypes resteraient libres sur branche courte; seuls les éléments présentés comme fiables devraient franchir les gates.

## Hanuman dans le temps

[PROPOSITION] **À six mois**, Hanuman devrait avoir deux flux de référence, un point d’entrée, des runs identifiés et une documentation de vérité.

[PROPOSITION] **À deux ans**, Hanuman devrait offrir preview, approbation, reprise et connecteurs mûrs, sans base centrale.

[HYPOTHÈSE] **À cinq ans**, des agents spécialisés en lecture pourraient planifier ou trier si les règles déterministes ne suffisent plus.

[HYPOTHÈSE] **À dix ans**, Hanuman pourrait porter des recettes et politiques portables entre appareils sans déplacer les secrets ni les données sources.

## Scénario d’échec

[HYPOTHÈSE] Hanuman échoue en devenant une collection de pages, connecteurs et prototypes dont aucun contrat n’est stable.

[HYPOTHÈSE] Hanuman échoue si la branche Chess, les resources, les agents et les graphes consomment l’attention pendant que les synchronisations centrales restent opaques.

[HYPOTHÈSE] Hanuman échoue si les outils natifs rattrapent ses automatisations et qu’il ne possède aucun avantage de gouvernance.

## Scénario de succès

[HYPOTHÈSE] Hanuman réussit si quelques intentions inter-outils sont accomplies régulièrement, sans doublon, avec preview, provenance et reprise.

[HYPOTHÈSE] Hanuman réussit si changer Notion, un fournisseur IA ou une API ne détruit ni les intentions ni les politiques.

[INFÉRENCE] Son avantage défendable serait la confiance dans la coordination, pas le volume de données ou de fonctionnalités.

## Cinq plus grands risques

1. [INFÉRENCE] Expansion plus rapide que la stabilisation des contrats.
2. [INFÉRENCE] Branche Chess longue et concurrente non arbitrée.
3. [INFÉRENCE] Exposition accidentelle d’une surface locale puissante.
4. [INFÉRENCE] Synchronisation bidirectionnelle sans identité ni conflits.
5. [INFÉRENCE] Agents futurs amplifiant des exécutions non observables.

## Cinq plus grandes forces

1. [FAIT] La séparation routes, services et orchestrations est déjà lisible.
2. [FAIT] Le registre exprime des capacités indépendantes des écrans.
3. [FAIT] Les transformations Obsidian/Notion et plusieurs services possèdent des tests isolés substantiels.
4. [INFÉRENCE] Le caractère local et personnel permet une gouvernance plus simple qu’un SaaS.
5. [INFÉRENCE] La philosophie « relier sans remplacer » fournit un filtre produit rare et puissant.

## Cinq décisions sur lesquelles j’hésite encore

1. [HYPOTHÈSE] Archiver la branche Chess ou en extraire un laboratoire officiellement séparé.
2. [HYPOTHÈSE] Garder la TUI comme interface durable ou la considérer comme outil de diagnostic.
3. [HYPOTHÈSE] Introduire une persistance légère des runs ou conserver un journal append-only.
4. [HYPOTHÈSE] Formaliser un contrat de connecteur en V2 ou attendre un quatrième cas d’écriture.
5. [HYPOTHÈSE] Construire un briefing inter-outils comme produit phare ou concentrer tout sur la publication Obsidian → Notion.

## Cinq questions que seul le propriétaire peut trancher

1. [HYPOTHÈSE] Quel flux vous fait réellement gagner du temps chaque semaine aujourd’hui ?
2. [HYPOTHÈSE] Obsidian ou Notion est-il autoritaire pour chaque type de contenu partagé ?
3. [HYPOTHÈSE] Chess est-il un pilier de Hanuman, un laboratoire personnel ou un projet adjacent ?
4. [HYPOTHÈSE] Hanuman doit-il rester strictement mono-utilisateur et local pendant deux ans ?
5. [HYPOTHÈSE] Préférez-vous moins d’orchestrations garanties ou davantage de prototypes exploratoires ?
