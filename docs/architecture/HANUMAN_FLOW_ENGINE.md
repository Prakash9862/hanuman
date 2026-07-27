# Moteur universel de flux Hanuman

> **Statut :** spécification conceptuelle normative
>
> **Portée :** futurs flux Hanuman et migration progressive des flux existants
>
> **Implémentation :** non prescrite par ce document

## 1. Objet

Hanuman est un système personnel d’orchestration. Il relie des outils
spécialisés, coordonne leurs échanges et observe les effets produits sans
remplacer ces outils ni devenir leur source de vérité universelle.

Le moteur de flux Hanuman est le modèle commun selon lequel un événement ou une
donnée provenant d’un outil est interprété, transformé puis utilisé pour
produire une action utile dans un ou plusieurs autres outils.

```text
événement ou donnée source
          ↓
        Flux
          ↓
coordination de capacités
          ↓
      Connecteurs
          ↓
        Données
```

Un moteur universel ne signifie pas qu’un ordonnanceur, un moteur de graphe ou
une infrastructure générique doivent être construits immédiatement. Cette
spécification définit des responsabilités, des contrats et des invariants
communs. Une implémentation peut rester une fonction déterministe tant que ces
contrats sont respectés.

Le moteur doit pouvoir décrire notamment :

- GitHub Activity → Project Memory ;
- Obsidian → Notion ;
- Notion → Obsidian ;
- Gmail → Notion ;
- Calendar → Maps → Gmail ;
- tout futur flux fondé sur les mêmes invariants.

## 2. Principes normatifs

Les mots **DOIT**, **NE DOIT PAS**, **DEVRAIT**, **NE DEVRAIT PAS** et **PEUT**
expriment respectivement une obligation, une interdiction, une recommandation,
une recommandation négative et une possibilité.

Tout flux Hanuman DOIT respecter les principes suivants :

1. Hanuman orchestre les outils ; il ne les remplace pas.
2. Un Flux porte l’intention, les règles et l’ordre des opérations.
3. Un Connecteur porte exclusivement la frontière technique d’un système.
4. Un service expose une capacité réutilisable et ne forme pas seul un flux
   inter-outils.
5. Un Connecteur NE DOIT PAS contenir de logique métier propre à un Flux.
6. Un Flux NE DOIT PAS appeler directement une API externe.
7. Les routes, CLI, webhooks et tâches planifiées déclenchent un même Flux sans
   modifier sa logique métier.
8. Les sources de vérité, identités et règles de conflit sont définies par Flux
   et, si nécessaire, par champ.
9. Toute écriture importante DEVRAIT tendre vers le cycle
   `plan → preview → apply → verify`.
10. L’unique application FastAPI canonique reste `hanuman.main:app`.

Les rubriques produit officielles restent : **Flux**, **Connecteurs**,
**Données**, **Santé**, **Agents IA** et **Paramètres**. Les concepts techniques
définis ci-dessous précisent le fonctionnement interne de ces rubriques sans
introduire une nouvelle taxonomie produit.

## 3. Définitions officielles

### 3.1 Connector — Connecteur

**Rôle.** Frontière technique entre Hanuman et une API, un système de fichiers,
un programme local ou un autre système externe.

**Peut :**

- s’authentifier auprès de son système ;
- lire et écrire selon des capacités déclarées ;
- gérer transport, pagination, quotas, délais et formats fournisseur ;
- normaliser les erreurs techniques ;
- exposer des capacités réutilisables à un service.

**Ne doit pas :**

- décider de l’intention ou de la stratégie d’un Flux ;
- choisir une Destination inter-outils ;
- connaître une orchestration précise ;
- appeler un autre Connecteur ;
- interpréter seul la valeur métier d’une Resource.

**Relations.** Un service utilise un Connecteur. Un Flux coordonne des services
ou capacités, sans dépendre des détails de transport du Connecteur.

### 3.2 Trigger — Déclencheur

**Rôle.** Mécanisme qui demande l’évaluation ou l’exécution d’un Flow à partir
d’un Event ou d’une commande.

**Peut :**

- recevoir une action manuelle, une requête API, un webhook ou une échéance ;
- produire les métadonnées nécessaires à la traçabilité ;
- refuser une demande non authentifiée ou invalide.

**Ne doit pas :**

- réimplémenter le Flow ;
- transformer différemment les mêmes données selon le canal ;
- contenir de secrets dans l’Event produit.

**Relations.** Un Trigger produit ou transmet un Event et initialise un Run.
Plusieurs Triggers peuvent viser le même Flow.

### 3.3 Event — Événement

**Rôle.** Fait immuable et horodaté qui décrit ce qui s’est produit ou ce qui a
été demandé.

**Peut :**

- référencer une Resource ou transporter un instantané minimal ;
- déclencher un ou plusieurs Flows autorisés ;
- relier causalement plusieurs Runs ou Events.

**Ne doit pas :**

- contenir de secret ;
- être modifié pour représenter un nouvel état ;
- être confondu avec la Resource mutable qu’il décrit.

**Relations.** Un Trigger reçoit ou crée un Event. Un Run conserve sa référence
et le Flow décide comment l’interpréter.

### 3.4 Flow — Flux

**Rôle.** Vue produit et définition exécutable d’une circulation de Données ou
d’actions répondant à une intention explicite. Dans l’architecture existante,
une orchestration est l’implémentation d’un Flow.

**Peut :**

- choisir Sources, Destinations et Resources utiles ;
- ordonner les Steps ;
- transformer, enrichir, réconcilier et filtrer ;
- appliquer identité, idempotence et règles de conflit ;
- produire un Result structuré.

**Ne doit pas :**

- implémenter le transport d’une API externe ;
- lire ou transporter des secrets ;
- dépendre de FastAPI, d’un frontend ou d’un Trigger particulier ;
- reproduire les capacités générales d’un outil externe.

**Relations.** Un Flow consomme un Event, coordonne des capacités de
Connecteurs par l’intermédiaire de services, et produit un Run composé de Steps
et d’un Result.

### 3.5 Resource — Ressource

**Rôle.** Objet lu, transformé, lié ou produit : message, commit, page, note,
événement de calendrier, fichier, résultat de recherche ou artefact dérivé.

**Peut :**

- posséder une identité stable, une provenance et une version ;
- avoir plusieurs représentations dans plusieurs outils ;
- rester uniquement dans son système source.

**Ne doit pas :**

- être supposée persistée par Hanuman ;
- perdre sa provenance lors d’une normalisation ;
- devenir implicitement une source de vérité universelle.

**Relations.** Un Event peut signaler le changement d’une Resource. Un Flow lit
et produit des Resources par les Connecteurs.

### 3.6 Run — Exécution

**Rôle.** Instance traçable d’un Flow pour un Trigger et une entrée déterminés.

**Peut :**

- regrouper Steps, erreurs, métriques et effets ;
- aboutir à un succès, un résultat partiel, un échec ou une absence d’effet ;
- être repris manuellement selon les règles du Flow.

**Ne doit pas :**

- masquer une écriture partielle sous un statut de succès ;
- confondre « tâche démarrée » et « tâche réussie » ;
- être utilisé comme log technique brut.

**Relations.** Un Trigger initialise un Run. Le Flow le fait évoluer et son
résultat alimente le journal métier et la Santé.

### 3.7 Step — Étape

**Rôle.** Unité ordonnée et observable d’un Run : collecte, normalisation,
validation, transformation, écriture ou vérification.

**Peut :**

- lire des entrées et produire une sortie intermédiaire ;
- être facultative, répétée ou ignorée selon le Flow ;
- déclarer ses métriques et son erreur.

**Ne doit pas :**

- devenir un mini-Flow opaque ;
- masquer ses effets externes ;
- décider seule de la stratégie globale.

**Relations.** Les Steps composent un Run et produisent des StepResults agrégés
dans le Result.

### 3.8 Result — Résultat

**Rôle.** Résumé structuré et indépendant de l’interface de ce qu’un Run a
observé, décidé et produit.

**Peut :**

- compter lectures, créations, mises à jour, éléments ignorés et échecs ;
- référencer les Resources affectées sans recopier leurs données sensibles ;
- porter avertissements, vérifications et effets partiels.

**Ne doit pas :**

- être une réponse FastAPI ou un texte de console comme unique contrat ;
- annoncer un succès si la vérification obligatoire a échoué ;
- exposer de secrets.

**Relations.** Le Flow construit le Result à partir des StepResults. Les
interfaces le sérialisent sans en changer le sens.

### 3.9 Log — Journal

**Rôle.** Trace horodatée d’un fait technique ou métier utile à l’explication
d’un Run.

**Peut :**

- enregistrer transitions, durées, codes d’erreur normalisés et identifiants ;
- relier une entrée à `run_id`, `event_id` et `correlation_id` ;
- être expurgé ou agrégé selon sa destination.

**Ne doit pas :**

- contenir de token, secret ou contenu sensible non nécessaire ;
- servir de seule représentation de l’état d’un Run ;
- confondre événements techniques et bilan métier.

**Relations.** Les Steps émettent des logs techniques ; le Run produit un
journal métier ; la Santé agrège des états, pas des lignes de log brutes.

### 3.10 Health — Santé

**Rôle.** État synthétique et daté d’un Connecteur, d’un Flow ou du moteur,
fondé sur des preuves observables.

**Peut :**

- exposer disponibilité, configuration, dernière exécution et tendance ;
- distinguer déclaré, configuré, autorisé, joignable et sain ;
- signaler un fonctionnement dégradé ou un échec récent.

**Ne doit pas :**

- conclure qu’un Connecteur est sain à partir de sa seule présence au catalogue ;
- confondre un ping réussi avec une opération représentative réussie ;
- afficher « opérationnel » sans preuve datée.

**Relations.** Les Connecteurs fournissent des diagnostics techniques. Les Runs
fournissent la preuve fonctionnelle agrégée dans la rubrique Santé.

### 3.11 Source

**Rôle.** Système, Resource ou représentation depuis lequel le Flow lit une
information autoritaire pour un objet ou un champ donné.

**Peut :**

- varier selon l’objet ou le champ ;
- être externe ou locale ;
- différer de l’émetteur initial de l’Event.

**Ne doit pas :**

- être déclarée source de vérité pour tout Hanuman ;
- être choisie implicitement ;
- être écrasée sans règle de conflit.

**Relations.** Un Source Connector fournit les Resources au Flow. La définition
du Flow déclare la provenance et l’autorité de la Source.

### 3.12 Destination

**Rôle.** Système ou représentation qui reçoit l’effet utile produit par le
Flow.

**Peut :**

- recevoir une création, une mise à jour, un lien ou une notification ;
- être multiple dans un même Flow ;
- devenir Source d’un autre Flow.

**Ne doit pas :**

- être choisie par le Connecteur ;
- être supposée capable de représenter toutes les données de la Source ;
- recevoir une écriture sans validation des permissions et de l’identité.

**Relations.** Le Flow choisit la Destination. Le Destination Connector exécute
l’opération technique demandée et retourne une preuve vérifiable.

## 4. Cycle de vie générique

Le cycle de référence est :

```text
Trigger
  ↓
réception d’un Event
  ↓
Source Connector
  ↓
collecte
  ↓
normalisation
  ↓
validation
  ↓
Flow
  ↓
transformation / enrichissement
  ↓
Destination Connector
  ↓
écriture
  ↓
vérification
  ↓
journalisation
  ↓
mise à jour de la Santé
```

Ce diagramme décrit les responsabilités, pas nécessairement une succession de
processus distincts. Un Flow PEUT omettre une étape sans casser le modèle :

- un Event complet peut éviter une collecte supplémentaire ;
- un Flow en lecture seule n’a ni Destination ni écriture ;
- un format déjà canonique peut réduire la normalisation ;
- un Flow sans enrichissement peut transmettre une Resource validée ;
- une commande rejetée comme doublon s’arrête avant l’écriture ;
- une vérification peut être différée si le système externe est asynchrone.

L’omission DOIT être explicite. Elle ne dispense jamais de l’idempotence, de la
traçabilité ni d’un Result exact.

Pour les effets importants, le cycle DEVRAIT être interprété comme :

```text
planifier → prévisualiser → appliquer → vérifier
```

La preview peut être minimale dans une première version, mais un calcul interne
non présenté à l’utilisateur NE DOIT PAS être appelé « preview ».

## 5. Responsabilités des Connecteurs

Un Connecteur DOIT :

- authentifier les appels au système qu’il représente ;
- parler à une API, un système de fichiers ou un programme local ;
- exposer des opérations de lecture et d’écriture explicites ;
- gérer pagination, quotas, timeouts et réponses fournisseur ;
- normaliser les erreurs techniques ;
- déclarer ses capacités, permissions et effets ;
- rester réutilisable par plusieurs services et Flows.

Un Connecteur NE DOIT JAMAIS :

- décider du comportement métier d’un Flow ;
- construire une stratégie inter-outils ;
- connaître une orchestration précise ;
- appeler directement un autre Connecteur ;
- déduire seul une règle d’idempotence métier ;
- produire une réponse propre à une interface utilisateur.

La responsabilité peut actuellement être portée par un service ou un client
fin. Cette hétérogénéité d’implémentation est une dette connue ; elle ne change
pas la frontière conceptuelle.

## 6. Responsabilités des Flows

Un Flow DOIT :

- exprimer une intention et un résultat attendu ;
- déclarer ses Sources, Destinations et sources de vérité ;
- choisir les Données nécessaires et limiter leur collecte ;
- transformer, enrichir, filtrer ou réconcilier les Resources ;
- coordonner les capacités des Connecteurs via des services réutilisables ;
- définir identité, idempotence, conflits et effets partiels ;
- produire un FlowResult structuré ;
- exposer suffisamment de métriques pour alimenter la Santé.

Un Flow NE DOIT JAMAIS :

- implémenter HTTP, OAuth ou un protocole fournisseur ;
- contenir ou journaliser des secrets ;
- dupliquer pagination, retry technique ou sérialisation fournisseur ;
- dépendre du mécanisme qui le déclenche ;
- déléguer sa stratégie métier à un Connecteur.

## 7. Modèle des Events

Tout Event normalisé DOIT contenir au minimum :

| Champ | Sens |
|---|---|
| `event_id` | identité unique et stable de l’Event |
| `event_type` | type qualifié, par exemple `github.push` |
| `source` | émetteur et contexte d’origine |
| `occurred_at` | instant où le fait s’est produit |
| `received_at` | instant où Hanuman l’a reçu |
| `subject` | référence stable de la Resource principalement concernée |
| `payload` | données minimales nécessaires au Flow |
| `correlation_id` | regroupement d’Events et de Runs liés |
| `causation_id` | Event ou commande ayant directement causé celui-ci |
| `schema_version` | version du contrat de l’Event |

Les horodatages DOIVENT inclure un fuseau ou être exprimés en UTC. Le `payload`
DOIT être considéré comme non fiable tant qu’il n’est pas validé.

### 7.1 Événement externe

Fait émis par un fournisseur, par exemple un push GitHub ou un message Gmail.
Son identité fournisseur doit être conservée. La signature et la provenance
doivent être vérifiées avant traitement.

### 7.2 Événement interne Hanuman

Fait produit par Hanuman, par exemple `flow.run.completed`. Il décrit une
transition déjà survenue et ne remplace pas le Run autoritaire.

### 7.3 Commande manuelle

Demande explicite d’un utilisateur. Une commande exprime une intention à
exécuter ; elle n’affirme pas qu’un fait externe s’est déjà produit. Une
enveloppe normalisée peut la transmettre au moteur avec un `event_type` dédié,
mais sa nature de commande DOIT rester visible.

### 7.4 Événement planifié

Occurrence produite par une échéance connue. Elle exprime « évaluer ce Flow à
cet instant », pas nécessairement qu’une Resource externe a changé.

## 8. Modèle d’un Run

Tout FlowRun DOIT contenir au minimum :

| Champ | Sens |
|---|---|
| `run_id` | identité unique de l’exécution |
| `flow_id` | identité stable du Flow et référence à sa version |
| `trigger` | type, identité et métadonnées sûres du Trigger |
| `status` | état courant ou final |
| `started_at` | début effectif |
| `finished_at` | fin effective, absente pendant l’exécution |
| `input` | référence ou vue expurgée de l’entrée |
| `result` | FlowResult final ou partiel |
| `errors` | erreurs structurées, classifiées et expurgées |
| `metrics` | compteurs et durées utiles |
| `idempotency_key` | clé définissant l’effet logique unique |

Statuts autorisés :

| Statut | Signification |
|---|---|
| `pending` | accepté, non commencé |
| `running` | au moins une étape est en cours |
| `succeeded` | effets attendus réalisés et vérifications obligatoires réussies |
| `partially_succeeded` | certains effets sont confirmés, d’autres non |
| `failed` | résultat utile attendu non obtenu |
| `skipped` | aucune exécution utile, notamment doublon ou condition non satisfaite |
| `cancelled` | arrêt explicite avant achèvement |

Toute transition DOIT être horodatée. Un Run terminal NE DOIT PAS revenir à
`running` ; une reprise crée un nouveau Run lié au précédent.

## 9. Idempotence

Un même événement logique NE DOIT PAS produire deux fois le même effet logique.
Chaque Flow DOIT documenter :

- l’identité stable de ses Resources ;
- le périmètre de son `idempotency_key` ;
- la durée de conservation nécessaire à la déduplication ;
- le comportement create-or-update ;
- la politique de retry et de reprise ;
- le traitement d’un doublon confirmé.

Les écritures DEVRAIENT favoriser create-or-update lorsque la Destination le
permet. Un retry DOIT réutiliser l’identité logique initiale. La déduplication
NE DOIT PAS dépendre uniquement d’un titre, d’un libellé humain, d’un timestamp
arrondi ou d’un ordre de liste.

Exemples de clés stables :

| Resource | Identité |
|---|---|
| commit | `repository + SHA` |
| release | `repository + tag` |
| email | `provider + message_id` |
| note Obsidian | `vault + chemin_stable` |
| événement Calendar | `calendar_id + event_id` |

Une clé d’idempotence empêche la répétition d’un effet ; elle ne résout pas à
elle seule les conflits de versions. Un Flow de synchronisation DOIT aussi
définir la direction, l’autorité par champ et la règle de conflit.

## 10. Gestion des erreurs

Les erreurs DOIVENT être classées au minimum comme suit :

| Catégorie | Description | Comportement attendu |
|---|---|---|
| validation | entrée ou Resource non conforme | ne pas écrire ; corriger ou rejeter |
| authentification | credential absent, refusé ou expiré | ne pas retry en boucle ; demander une action |
| connecteur | protocole, format ou capacité en erreur | normaliser ; retry seulement si sûr |
| indisponibilité externe | timeout, quota temporaire, service indisponible | retry borné avec backoff |
| métier | règle du Flow non satisfaite | échouer ou ignorer explicitement |
| écriture partielle | certains effets confirmés | résultat partiel et reprise ciblée |
| conflit | versions incompatibles ou autorité ambiguë | ne pas écraser silencieusement |
| événement dupliqué | effet déjà traité | `skipped` ou mise à jour idempotente |

### 10.1 Retry

Un retry est une nouvelle tentative de la même opération logique. Il DOIT être
borné, observable et réservé aux erreurs transitoires ou explicitement
réparables. Il DOIT conserver la même identité d’effet.

### 10.2 Backoff

Le backoff espace les retries afin de respecter l’indisponibilité, les quotas et
les indications du fournisseur. Sa stratégie précise relève du Connecteur ou
de l’exécuteur, pas de la transformation métier.

### 10.3 Abandon

Le Run doit abandonner lorsque l’erreur est permanente, que le budget de retry
est épuisé ou que continuer risquerait un effet incohérent. L’abandon produit
un état terminal explicite et une erreur exploitable.

### 10.4 Reprise manuelle

Une reprise crée un nouveau Run référant au Run initial. Elle peut reprendre
les seuls effets non confirmés si le Flow sait prouver les effets déjà réalisés.
Elle NE DOIT PAS réexécuter aveuglément toutes les écritures.

### 10.5 Résultat partiel

Un Run est `partially_succeeded` dès lors qu’au moins un effet utile est
confirmé et qu’au moins un effet attendu a échoué ou reste indéterminé. Le
Result DOIT identifier les deux ensembles.

### 10.6 Vérification après écriture

Une écriture importante DEVRAIT être relue ou confirmée par une preuve du
système destination. Une réponse d’acceptation asynchrone peut laisser la
vérification en attente ; elle ne vaut pas succès final si la vérification est
obligatoire.

Cette spécification n’impose ni moteur de retry distribué ni infrastructure de
compensation. Elle impose que ces comportements soient explicites et testables.

## 11. Journalisation et Santé

Chaque Run DOIT exposer au minimum :

- dernière exécution ;
- dernier succès ;
- dernier échec ;
- durée ;
- nombre d’objets lus ;
- nombre créé ;
- nombre mis à jour ;
- nombre ignoré ;
- nombre échoué ;
- erreur principale expurgée.

Ces informations alimentent naturellement la page Santé :

```text
StepResults
    ↓
FlowResult
    ↓
état terminal du Run
    ↓
agrégats datés du Flow
    ↓
Santé
```

Trois niveaux doivent rester distincts :

1. **Logs techniques** : diagnostics fins de transport et d’exécution.
2. **Journal métier** : effets compréhensibles produits par un Run.
3. **État de Santé** : synthèse datée des dernières preuves et tendances.

La Santé ne doit pas lire des messages libres pour deviner le résultat. Elle
doit consommer les champs structurés des Runs et les diagnostics des
Connecteurs.

## 12. Modes de déclenchement

Un Flow PEUT être déclenché par :

- une action manuelle dans Hanuman ;
- une commande CLI ;
- une requête API ;
- un webhook signé ;
- une GitHub Action ;
- une tâche cron ;
- une surveillance locale ;
- un Event interne Hanuman.

Chaque mécanisme adapte son entrée vers le même Event ou la même commande
normalisée. Le mécanisme de déclenchement NE DOIT PAS modifier :

- la transformation métier ;
- l’identité des Resources ;
- la clé d’idempotence ;
- les règles de conflit ;
- le sens du Result.

Les interfaces peuvent choisir une représentation synchrone ou asynchrone du
même Run, sans créer deux implémentations du Flow.

## 13. Exécution synchrone et asynchrone

Une exécution synchrone convient lorsque :

- la durée est courte et bornée ;
- le volume est faible ;
- le résultat final peut être retourné avant le timeout de l’interface ;
- aucune attente externe prolongée n’est nécessaire.

Une exécution asynchrone convient lorsque :

- la collecte ou l’écriture est longue ;
- le volume est élevé ou paginé ;
- des retries ou vérifications différées sont probables ;
- le Trigger doit être acquitté rapidement ;
- plusieurs Destinations produisent des effets indépendants.

En mode asynchrone, l’acquittement DOIT distinguer « Run accepté » de « Run
réussi » et fournir `run_id`. En mode synchrone, le résultat retourné reste un
FlowResult sérialisé.

Ce document n’impose ni file de messages, ni processus worker, ni technologie
d’ordonnancement.

## 14. Sécurité

Tout Flow et tout Trigger DOIVENT respecter les règles suivantes :

- secrets, tokens et credentials hors Events, Results et logs ;
- validation de la signature et de la fraîcheur des webhooks ;
- authentification et autorisation des déclenchements API ;
- aucune exposition publique non protégée ;
- validation de tout `payload` externe avant utilisation ;
- collecte et conservation limitées aux Données nécessaires ;
- logs expurgés des contenus sensibles et données personnelles non requises ;
- permissions minimales pour chaque Connecteur ;
- cible d’écriture explicitement autorisée ;
- aucune donnée externe traitée comme instruction de confiance.

Une preuve de Santé NE DOIT PAS révéler un secret ni reproduire le contenu
complet d’une Resource sensible.

## 15. Versionnement

### 15.1 Version du Flow

Chaque FlowDefinition DOIT posséder une version. Une modification est
incompatible lorsqu’elle change notamment l’identité, les effets, les sources
de vérité, les règles de conflit ou la signification du Result.

### 15.2 Version du schéma d’Event

Chaque Event DOIT porter `schema_version`. Une évolution compatible peut ajouter
des champs facultatifs. La suppression, le renommage ou le changement de sens
d’un champ exige une nouvelle version.

### 15.3 Compatibilité ascendante

Un consommateur DEVRAIT ignorer les champs additionnels qu’il ne connaît pas,
mais NE DOIT PAS deviner la signification d’une version incompatible. Les
versions acceptées doivent être déclarées par le Flow.

### 15.4 Migrations

Une migration DOIT préciser :

- versions source et cible ;
- transformation des données ;
- impact sur l’idempotence ;
- possibilité de retour arrière ;
- traitement des Events en attente.

### 15.5 Historique des Runs

L’historique DOIT conserver au minimum `run_id`, la version du Flow, la version
de l’Event, les statuts, les métriques, les erreurs expurgées et les références
d’effets nécessaires à l’audit. Sa durée de conservation doit être explicite.

## 16. Contrats conceptuels

Les structures suivantes décrivent des contrats, pas des classes de production.
Elles restent indépendantes de FastAPI, Pydantic, Celery ou toute bibliothèque.

### 16.1 FlowDefinition

```text
FlowDefinition
  flow_id
  version
  intent
  accepted_event_types
  sources
  destinations
  required_capabilities
  source_of_truth_rules
  steps
  idempotency_rule
  conflict_policy
  verification_policy
  result_contract
```

### 16.2 TriggerDefinition

```text
TriggerDefinition
  trigger_id
  trigger_type
  target_flow_id
  authentication_policy
  event_mapping
  acknowledgement_mode
```

### 16.3 NormalizedEvent

```text
NormalizedEvent
  event_id
  event_type
  source
  occurred_at
  received_at
  subject
  payload
  correlation_id
  causation_id
  schema_version
```

### 16.4 FlowRun

```text
FlowRun
  run_id
  flow_id
  flow_version
  event_id
  trigger
  status
  started_at
  finished_at
  input
  step_results
  result
  errors
  metrics
  idempotency_key
```

### 16.5 FlowResult

```text
FlowResult
  status
  summary
  resources_read
  resources_created
  resources_updated
  resources_skipped
  resources_failed
  effects
  warnings
  verification
```

### 16.6 StepResult

```text
StepResult
  step_id
  status
  started_at
  finished_at
  input_refs
  output_refs
  effects
  metrics
  errors
```

### 16.7 ConnectorCapability

```text
ConnectorCapability
  connector_id
  capability_id
  operation
  resource_type
  read_or_write
  permissions
  limits
  error_contract
```

Ces contrats n’imposent pas une classe de base universelle. Une fonction simple
peut les satisfaire lorsqu’elle expose les mêmes garanties.

## 17. Exemple complet : GitHub Activity → Project Memory

Cet exemple applique le modèle ; il ne définit pas le moteur entier.

### 17.1 Intention et autorités

GitHub reste la source de vérité du code, des commits et de leur identité.
Notion reçoit une mémoire structurée du projet. Hanuman conserve la provenance,
les liens d’identité et l’état des Runs.

« Project Memory » désigne ici les artefacts réellement persistés dans Notion
et leur historique ; ce terme ne désigne pas une mémoire implicite de Hanuman.
La durée de conservation du journal Hanuman doit être définie séparément.

### 17.2 Déroulement d’un push

1. Un webhook signé ou une GitHub Action transmet un push.
2. Le Trigger valide la provenance et crée un Event `github.push`.
3. L’Event référence le repository, la branche et les SHA annoncés.
4. Le service GitHub utilise le Source Connector pour récupérer les commits
   nécessaires.
5. Les commits sont normalisés en Resources conservant repository, SHA,
   auteur, date, message et URL.
6. Le Flow valide le repository autorisé et les champs obligatoires.
7. Chaque commit reçoit l’identité `repository + SHA`.
8. Le Flow ignore les doublons confirmés et planifie les create-or-update.
9. Un enrichissement déterministe rattache les commits à une Development
   Session existante ou explicitement identifiée.
10. Le service Notion utilise le Destination Connector pour créer ou mettre à
    jour les commits et la Development Session.
11. Le Flow vérifie les identifiants et relations retournés par Notion.
12. Le FlowResult compte les éléments lus, créés, mis à jour, ignorés et
    échoués.
13. Le Run est finalisé et son journal métier alimente la Santé du Flow.

### 17.3 Idempotence et résultat partiel

Deux livraisons du même push réutilisent les identités `repository + SHA`. Elles
ne créent pas de second commit dans la Destination. L’identité d’une
Development Session NE DOIT PAS reposer uniquement sur son titre.

Si trois commits sont écrits et un quatrième échoue, le Run est
`partially_succeeded`. La reprise relit les preuves existantes et ne retente que
l’effet manquant ou non confirmé.

### 17.4 Limites

Le Flow ne recopie pas l’intégralité de GitHub. Les issues, pull requests,
releases et workflows constituent d’autres Events ou Resources possibles. Un
résumé par Agents IA reste optionnel et extérieur au cœur déterministe.

## 18. Autres exemples

### 18.1 Obsidian → Notion

- Trigger : commande manuelle, API ou surveillance locale.
- Source : note identifiée par `vault + chemin stable`.
- Flow : lire, normaliser le Markdown, valider la cible et transformer les
  éléments représentables.
- Destination : page Notion créée ou mise à jour.
- Vérification : relire l’identifiant, la cible et les propriétés essentielles.
- Santé : dernière publication, objets créés/mis à jour et erreurs.

Obsidian reste source de vérité de la note publiée sauf règle contraire
explicite par champ.

### 18.2 Gmail → Notion

- Trigger : commande, échéance ou nouvel email autorisé.
- Source : message identifié par `provider + message_id`.
- Flow : sélectionner les messages utiles, extraire les métadonnées nécessaires
  et limiter les données personnelles conservées.
- Destination : entrée Notion create-or-update.
- Vérification : identité du message et propriétés attendues.

Le Connecteur Gmail ne décide jamais quels messages constituent une information
projet ; cette règle appartient au Flow.

### 18.3 Calendar → Maps → Gmail

- Trigger : échéance avant un événement Calendar.
- Source : événement identifié par `calendar_id + event_id`.
- Flow : valider l’heure et le lieu, demander une capacité Maps pour construire
  un itinéraire, puis préparer une notification.
- Destinations : lien Maps dérivé et message Gmail envoyé ou préparé selon la
  politique du Flow.
- Résultat : itinéraire produit, notification confirmée, ignorée ou échouée.

Calendar, Maps et Gmail restent trois Connecteurs indépendants. Aucun ne connaît
le workflow complet ni n’appelle directement un autre Connecteur.

### 18.4 Notion → Obsidian

Ce sens constitue un Flow distinct d’Obsidian → Notion. Il doit définir sa
propre identité, les champs dont Notion est la Source, la cible de fichier, les
zones modifiables et les règles de conflit. Les deux directions ne forment pas
une « synchronisation bidirectionnelle » tant que ces règles ne sont pas
explicitement résolues.

## 19. Écarts et formulation de compatibilité

La documentation et le code actuels présentent plusieurs écarts avec ce contrat :

1. Il n’existe pas encore de modèle universel de Resource, Event, FlowResult ou
   Run.
2. Les résultats et erreurs des orchestrations sont hétérogènes.
3. Le registre des Connecteurs est un catalogue, pas un contrat d’exécution.
4. Certains services portent directement le transport, ce qui reste compatible
   si leur frontière de Connecteur demeure claire.
5. Certaines orchestrations historiques appellent encore des API externes ;
   elles sont une dette à migrer progressivement, pas un précédent.
6. Deux applications FastAPI existent, mais seule `hanuman.main:app` est
   canonique.
7. Le cycle plan/preview/apply/verify et le journal commun ne sont pas encore
   généralisés.

L’ADR-0004 précise qu’aucun moteur générique ne doit être construit avant que
plusieurs flux aient prouvé les mêmes besoins. La présente spécification ne
contredit pas cette décision : elle normalise les concepts et comportements,
mais n’autorise ni infrastructure générique immédiate ni migration globale. Les
contrats doivent être validés progressivement sur des flux réels.

La spécification `GitHub Activity → Project Memory` décrit un Flow particulier
en statut Draft. Lorsque sa formulation « Hanuman est la mémoire » pourrait
être comprise comme une persistance universelle, la formulation retenue ici
est : Hanuman orchestre la production d’artefacts de mémoire dans les outils
désignés et conserve seulement les preuves d’exécution nécessaires.

## 20. Hors périmètre

Cette spécification ne décide pas :

- d’une file de messages ;
- d’une base de données interne ;
- de Celery, Redis, Kafka ou RabbitMQ ;
- du déploiement ;
- d’un scheduler générique ;
- du système d’Agents IA ;
- du schéma détaillé des bases Notion ;
- de l’interface frontend finale ;
- d’une classe de base universelle pour les Connecteurs ;
- d’une migration immédiate de tous les flux existants.

Elle ne modifie pas la responsabilité de la rubrique **Données** : les systèmes
externes restent propriétaires de leurs objets, et Hanuman ne devient pas un
entrepôt central par défaut.

## 21. Critères d’acceptation

Le contrat du moteur est satisfait si :

- les responsabilités des Flows, services et Connecteurs sont non ambiguës ;
- aucun Connecteur ne contient de stratégie métier inter-outils ;
- aucun nouveau Flow n’appelle directement une API externe ;
- chaque Flow déclare Sources, Destinations, identités et règles de conflit ;
- le modèle couvre les exemples de cette spécification sans exception ad hoc ;
- Events, Runs, Results et erreurs possèdent des contrats structurés ;
- l’idempotence empêche les doublons lors des retries et reprises ;
- les écritures partielles et vérifications sont représentées honnêtement ;
- les Runs alimentent naturellement la Santé par des métriques structurées ;
- un même Flow conserve son sens quel que soit son Trigger ;
- aucune technologie d’exécution inutile n’est imposée ;
- `hanuman.main:app` reste l’unique application FastAPI canonique ;
- l’adoption reste progressive et respecte les ADR existants.
