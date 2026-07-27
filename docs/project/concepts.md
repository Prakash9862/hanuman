# Concepts

Ce vocabulaire est normatif pour la documentation et le nouveau code.

## Vue d’ensemble

```text
Événement ou action utilisateur
              │
              v
        Orchestration
        /     |      \
   Service  Pipeline  Agent éventuel
      │
  Connecteur
      │
Outil externe ou programme local

Les données échangées sont des ressources.
Une synchronisation est un flux qui réconcilie des représentations liées.
```

## Définitions

### Connecteur

Frontière technique avec un système extérieur à Hanuman : API web, système de
fichiers ou programme local. Il gère les détails de transport,
d’authentification, de format et d’erreur propres à cette frontière.

Dans le code actuel, cette responsabilité peut être portée par un module
`core`, un service ou un client `services/adapters`. La notion est stable même
si l’implémentation n’est pas encore uniforme.

### Service

Interface Python réutilisable qui expose une capacité cohérente. Un service
traduit les détails d’un connecteur en opérations compréhensibles par le reste
de Hanuman. Il ne décide pas d’un flux inter-outils complet.

Exemple : récupérer des issues GitHub ou créer une page Notion.

### Orchestration

Coordination d’une ou plusieurs capacités pour réaliser une intention. Elle
possède les règles de transformation, d’ordre, d’identité, d’idempotence,
d’échec partiel et d’effet.

Une orchestration ne devrait pas contenir de détails d’API externe. Le code
historique comporte encore des exceptions, notamment des appels HTTP directs
dans certaines orchestrations.

### Flux

Vue produit d’une circulation de données ou d’actions. Le flux décrit le
chemin, la direction et le résultat attendus. Une orchestration est
l’implémentation exécutable d’un flux.

Un connecteur isolé n’est pas un flux.

### Ressource

Objet lu, transformé, lié ou produit : message, issue, page, note, événement,
partie, vidéo, partition ou résultat de recherche. Une ressource conserve sa
provenance et n’est pas nécessairement persistée par Hanuman.

### Agent

Décideur probabiliste borné par un rôle, des outils, un budget et une politique.
Un agent propose ou choisit des étapes ; il ne remplace pas le moteur
déterministe, la validation des cibles ou l’approbation humaine.

Les agents ne sont pas implémentés aujourd’hui.

### Pipeline

Suite ordonnée d’étapes au sein d’une orchestration. Le terme décrit la forme
d’exécution, pas une couche supplémentaire.

```text
lire -> normaliser -> transformer -> écrire -> vérifier
```

### Événement

Fait horodaté susceptible de déclencher ou d’expliquer une action : requête
utilisateur, changement d’une ressource, échéance ou résultat d’étape. Le code
actuel ne possède pas de bus d’événements général.

Un événement Google Calendar est par ailleurs une ressource métier ; le
contexte permet de distinguer les deux sens.

### Synchronisation

Flux qui maintient une relation explicite entre plusieurs représentations d’un
objet. Elle exige au minimum une identité, une direction et une règle de
conflit. Copier un objet une seule fois est une publication ou un export, pas
nécessairement une synchronisation.

### Source de vérité

Système ou artefact autoritaire pour un objet ou un champ dans un flux donné.
Il n’existe pas de source de vérité universelle pour Hanuman.

## Termes à éviter

| Terme vague | Préférer |
|---|---|
| intégration | connecteur ou orchestration, selon le sens |
| intelligence | transformation, décision ou enrichissement précis |
| sync bidirectionnelle | directions et conflits explicitement définis |
| opérationnel | capacité et vérification datée |
| mémoire | artefact réellement persisté et sa durée |
