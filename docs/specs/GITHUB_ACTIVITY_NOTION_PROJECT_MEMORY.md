# GitHub Activity → Notion Project Memory

> **Statut :** spécification proposée
>
> **Version du Flux :** `1.0`
>
> **Portée :** définition fonctionnelle et technique ; aucune implémentation
>
> **Référence normative :**
> [Moteur universel de Flux Hanuman](../architecture/HANUMAN_FLOW_ENGINE.md)

## 1. Vision

### 1.1 Problème remplacé

Le Flux historique synchronise principalement :

```text
GitHub Issues → tableau Notion Issues
```

Ce modèle suppose que les Issues décrivent l'évolution du projet. Or une part
importante du travail réel est visible d'abord dans les pushes, commits,
branches, merges et releases. Exiger une Issue tenue à jour pour alimenter
Notion ajoute une tâche administrative et laisse une mémoire incomplète quand
l'utilisateur développe et pousse directement.

Le nouveau modèle est :

```text
GitHub Activity → mémoire de projet Notion
```

Le besoin utilisateur est : « Je développe et je pousse sur GitHub. Sans action
administrative supplémentaire, Hanuman construit dans Notion une mémoire claire
de l'évolution du projet. »

GitHub reste la source de vérité du code et de l'activité technique. Notion
reçoit une représentation plus concise, structurée et lisible de l'évolution du
projet. Hanuman collecte les Données utiles, les transforme, les relie, écrit la
mémoire, vérifie ses effets et journalise chaque Run.

### 1.2 Place des Issues

Les Issues deviennent secondaires et optionnelles :

- elles peuvent expliquer une intention lorsqu'un commit ou une pull request
  les référence ;
- elles ne sont pas requises pour ouvrir ou alimenter une Development Session ;
- leur absence ne dégrade pas le fonctionnement déterministe du Flux ;
- le Flux ne recrée pas dans Notion un tableau complet des Issues.

L'ancien Flux et son tableau Notion restent intacts tant que le nouveau Flux
n'est pas opérationnel et que les critères de migration de la section 17 ne
sont pas atteints.

### 1.3 Résultat attendu

En quelques secondes dans Notion, l'utilisateur doit pouvoir déterminer :

- ce qui a changé et quand ;
- le dépôt et la branche concernés ;
- le contexte disponible expliquant probablement le changement ;
- les commits regroupés en sessions de développement cohérentes ;
- les étapes importantes franchies ;
- les liens permettant de retrouver la preuve technique dans GitHub.

Le succès ne se mesure pas au volume copié, mais à la lisibilité historique
obtenue sans saisie administrative supplémentaire.

## 2. Périmètre

### 2.1 Matrice de portée

| Donnée GitHub | Portée | Usage |
|---|---|---|
| Dépôt | V1 | Contexte, autorisation et rattachement à un projet Notion |
| Push | V1 | Event principal et unité de collecte incrémentale |
| Branche | V1, contexte minimal | Regroupement ; nom, ref et branche par défaut, sans catalogue exhaustif |
| Commit | V1 | Preuve technique et contenu d'une Development Session |
| Pull request | Version ultérieure | Contexte, regroupement et clôture explicite |
| Merge | V1 limité | Push sur la branche par défaut avec commit de merge identifiable ; Event dédié ultérieur |
| Release | Version ultérieure | Jalon important de la mémoire projet |
| Workflow / GitHub Actions | Version ultérieure | Santé et, seulement si utile, signal synthétique dans Notion |
| Tag | Version ultérieure | Repère technique et support des releases |
| Issue | Version ultérieure, secondaire | Contexte lorsqu'elle est explicitement référencée |
| Fichiers modifiés et statistiques | Hors V1 | À collecter ultérieurement seulement si leur valeur de lecture est démontrée |
| Commentaires, reviews, artefacts et logs Actions | Hors périmètre actuel | Trop détaillés ou sensibles pour la mémoire projet |

### 2.2 Limites de la V1

La V1 traite un dépôt pilote autorisé, ses pushes et leurs commits. Elle écrit
une vue du dépôt et des Development Sessions idempotentes. Elle ne collecte pas
un historique complet par défaut : le premier Run reçoit une borne explicite
(SHA de départ, date ou nombre maximal de commits), puis les Runs suivants sont
incrémentaux.

Un push de suppression de branche, un force-push ou un push sans nouveau commit
est observé et journalisé, mais ne provoque pas la suppression de mémoire dans
Notion. Une divergence d'historique est signalée pour rattrapage ; la mémoire
déjà vérifiée n'est pas effacée automatiquement.

## 3. Sources de vérité

### 3.1 Autorités

| Objet ou champ | Autorité | Règle |
|---|---|---|
| Identité du dépôt, propriétaire, nom, visibilité, état, URL et branche par défaut | GitHub | Notion en reçoit une projection create-or-update |
| Ref de branche, SHA, commit, auteur, date, message, URL, merge, tag et release | GitHub | Une correction GitHub remplace la projection générée au Run suivant |
| Titre généré, résumé déterministe et état calculé d'une Development Session | Hanuman | Recalculables ; les identifiants et preuves du Run font foi |
| Identité de session, correspondances GitHub ↔ Notion et état des Runs | Hanuman | Conservés comme preuves techniques nécessaires au Flux |
| Titre éditorial, notes, décisions, commentaires et compléments manuels dans Notion | Notion | Jamais écrasés par une projection GitHub |
| Identifiants de page et relations Notion | Notion pour l'identifiant ; Hanuman pour la correspondance | Vérifiés après écriture et conservés dans le Run |

### 3.2 Propriété des champs Notion

Chaque propriété de la cible doit être classée à la configuration :

- **gérée par le Flux** : identité technique, dépôt, branches, début, fin,
  état calculé, compteurs, références GitHub, résumé généré ;
- **éditoriale** : titre personnalisé, notes, décisions, enseignements ;
- **mixte interdite en V1** : aucun champ ne doit être modifié à la fois
  librement par l'utilisateur et automatiquement par Hanuman.

Si l'utilisateur personnalise un titre, le titre calculé reste dans une
propriété technique distincte. Le Flux ne déduit jamais qu'un changement
Notion doit modifier GitHub. Il n'existe aucune synchronisation
bidirectionnelle implicite.

## 4. Déclencheurs

### 4.1 Modes étudiés

| Mode | Usage | Décision |
|---|---|---|
| Webhook GitHub | Faible latence, provenance signée, événements natifs | Cible de production |
| GitHub Action | Simple sur un dépôt pilote, peut appeler Hanuman après un push | Déclencheur automatique initial recommandé si Hanuman est joignable de façon sûre |
| Manuel | Sélection d'un dépôt et d'une borne | V1, utile au pilote et à la reprise |
| API | Adaptateur vers le même Flux ; nécessite authentification | Possible en V1 pour usage local, via `hanuman.main:app` uniquement |
| CLI | Simple, testable et cohérente avec l'existant | Déclencheur réaliste de la première V1 |
| Tâche planifiée | Compare une borne connue à GitHub | Rattrapage, pas ordonnanceur générique |

### 4.2 Choix

Le premier chemin réaliste est une commande CLI manuelle sur un dépôt pilote.
Elle permet de valider le regroupement, le modèle Notion et le contrat de Run
sans exposer Hanuman. Une GitHub Action peut ensuite fournir le premier
déclenchement automatique si elle atteint un endpoint authentifié et protégé.
La cible de production est un webhook GitHub signé, avec acquittement rapide
distinct de la réussite du Run.

Une tâche planifiée bornée, ou la même commande CLI lancée périodiquement,
effectue le rattrapage depuis le dernier SHA vérifié. Aucun scheduler, bus
d'Events ou worker générique n'est requis par cette spécification.

Tous les modes construisent un Event ou une commande normalisée puis appellent
la même définition du Flux, avec les mêmes identités, règles de regroupement,
plans, écritures et résultats. Le Trigger ne contient aucune logique métier.

## 5. Event GitHub normalisé

### 5.1 Enveloppe commune

Tout Event respecte le contrat `NormalizedEvent` du moteur :
`event_id`, `event_type`, `source`, `occurred_at`, `received_at`, `subject`,
`payload`, `correlation_id`, `causation_id` et `schema_version`.

Règles communes :

- `source` contient le fournisseur, l'identité d'installation ou d'appelant et
  l'identité stable du dépôt, sans credential ;
- `subject` est une référence stable telle que
  `github:repository:<repository_id>:ref:<full_ref>` ;
- `schema_version` vaut `1` pour les contrats ci-dessous ;
- le payload reste minimal et non fiable avant validation ;
- `correlation_id` vaut par défaut
  `github:<repository_id>:<delivery_or_command_id>` ; un rattrapage peut
  corréler plusieurs Events au même Run ;
- les payloads GitHub complets ne sont ni recopiés dans l'Event normalisé ni
  conservés dans les logs.

### 5.2 Events V1

#### `github.push`

- **Identité :** identifiant de livraison GitHub lorsqu'il existe ; sinon
  `sha256(trigger_id, repository_id, full_ref, before_sha, after_sha)`.
- **Provenance :** GitHub webhook, GitHub Action autorisée ou adaptation
  explicite d'un rattrapage.
- **Subject :** dépôt et ref complète poussée.
- **Payload minimal :** `repository_id`, `owner`, `name`, `repository_url`,
  `default_branch`, `full_ref`, `before_sha`, `after_sha`, `created`,
  `deleted`, `forced`, liste bornée des SHA annoncés et URL de comparaison si
  disponible.
- **Validation :** schéma, dépôt autorisé, format de ref, SHA hexadécimaux,
  cohérence des indicateurs, bornes de taille et fraîcheur.
- **Signature :** HMAC GitHub obligatoire pour un webhook ; pour CLI, API ou
  Action, authentification propre au Trigger et mention explicite de l'absence
  de signature GitHub.
- **Clé de corrélation :** livraison ou commande, dépôt et ref.
- **Version :** `1`.

#### `github.backfill.requested`

Il s'agit d'une commande Hanuman, pas d'un fait émis par GitHub.

- **Identité :** identifiant de commande stable fourni par le Trigger.
- **Provenance :** CLI, API ou tâche planifiée authentifiée.
- **Subject :** dépôt autorisé.
- **Payload minimal :** `repository_id`, borne de départ, borne de fin
  facultative, branches autorisées et limite maximale.
- **Validation :** dépôt et bornes autorisés, volume borné, cible Notion
  configurée.
- **Signature :** non applicable ; authentification et autorisation Hanuman.
- **Clé de corrélation :** commande de rattrapage.
- **Version :** `1`.

### 5.3 Events ultérieurs

| Event | Identité fournisseur | Payload minimal envisagé |
|---|---|---|
| `github.pull_request.merged` | livraison + dépôt + numéro | dépôt, numéro, head/base, merge SHA, titre, URL, merged_at |
| `github.release.published` | livraison + dépôt + release_id | dépôt, release_id, tag, titre, URL, published_at |
| `github.workflow.completed` | livraison + dépôt + run_id | dépôt, run_id, workflow, head SHA, conclusion, URL, timestamps |

Ces Events n'entrent pas dans le contrat exécutable V1. Leur ajout exige une
version de Flux déclarant leurs effets.

## 6. Données manipulées

Dans l'architecture du moteur, ces Données peuvent être représentées
techniquement par le contrat `Resource`. Le terme visible dans le produit reste
« Données ».

### 6.1 Repository

| Champ | Règle |
|---|---|
| `github_repository_id` | Identité GitHub stable ; clé fonctionnelle |
| `owner`, `name`, `full_name` | Valeurs GitHub courantes |
| `url` | URL GitHub autoritaire |
| `default_branch` | Nom courant fourni par GitHub |
| `visibility` | Privé, interne ou public ; ne commande pas seul l'exposition Notion |
| `state` | Actif, archivé ou indisponible |
| `last_activity_at` | Maximum des activités traitées et vérifiées |
| `notion_project_ref` | Identifiant de la page Repository correspondante |

Un renommage ne crée pas un nouveau Repository : l'identité est l'identifiant
GitHub, pas `owner/name`.

### 6.2 Commit

| Champ | Règle V1 |
|---|---|
| `repository_id` + `sha` | Identité stable |
| `short_sha` | Affichage uniquement |
| `full_ref` / branche | Contexte du push, potentiellement multiple |
| `github_author` | Login et identifiant si disponibles |
| `git_author` | Nom affichable ; email exclu par défaut |
| `authored_at`, `committed_at` | Dates GitHub/Git, conservées en UTC |
| `message_subject` | Première ligne, bornée et neutralisée |
| `message_body` | Hors projection V1 par défaut |
| `url` | Preuve technique GitHub |
| `session_id` | Session calculée par le Flux |

Les fichiers modifiés, ajouts et suppressions ne sont pas collectés en V1. Un
même commit aperçu sur plusieurs branches garde une identité unique ; ses
contextes de push peuvent être agrégés sans dupliquer le commit.

### 6.3 Development Session

La Development Session est l'objet central de lecture. Elle représente une
séquence cohérente de commits d'un même dépôt, regroupés de manière
déterministe autour d'un contexte de branche et d'une fenêtre d'activité. Elle
n'affirme pas une intention que GitHub ne permet pas d'établir.

| Champ | Définition |
|---|---|
| `session_id` | Identité opaque et stable générée à l'ouverture, par exemple UUID ; jamais le titre |
| `repository_id` | Un seul dépôt en V1 |
| `grouping_key` | Empreinte versionnée de la stratégie et du contexte d'ouverture |
| `started_at` | Date du premier commit associé |
| `last_activity_at` | Date du dernier commit associé |
| `ended_at` | Date de clôture effective ou déterminée |
| `commit_ids` | Ensemble ordonné de `repository_id + SHA` |
| `branches` | Ensemble des branches observées ; une branche primaire en V1 |
| `status` | `open`, `closed` ou `manually_adjusted` |
| `computed_title` | Titre déterministe dérivé de la branche et des thèmes dominants de la session |
| `editorial_title` | Titre Notion facultatif, jamais utilisé comme identité |
| `generated_summary` | Résumé déterministe des sujets de commits |
| `github_links` | Branche, comparaison et commits utiles |
| `related_pr`, `related_release`, `milestone` | Facultatifs ; hors alimentation V1 |
| `grouping_version` | Version de la règle ; `3` pour la Phase 1 révisée |

Une session est une unité de mémoire, pas une branche permanente : plusieurs
sessions peuvent se succéder sur la même branche. Son résumé V1 liste de façon
concise les sujets de commits, sans Agents IA et sans inventer de causalité.

### 6.4 Pull Request / Merge

Une pull request apportera ultérieurement un contexte explicite (titre,
description, branche de tête et base). Son numéro est une clé de regroupement
forte. Une PR fusionnée peut clôturer la session de sa branche et la relier à
une session de livraison sur la branche par défaut.

En V1, seul un commit de merge rencontré dans un push peut servir de signal de
clôture. Il ne déclenche ni collecte détaillée de PR ni déduction incertaine :
si le lien à une PR n'est pas disponible de manière déterministe, le commit
reste un commit de la session de la branche poussée.

### 6.5 Release

Une Release est un jalon durable : tag, titre, date, notes synthétiques et lien
GitHub. Elle pourra clôturer ou relier les sessions dont les commits sont
inclus dans sa portée. Elle mérite une vue Notion dédiée lorsque cette capacité
entre en portée, mais aucune base Releases n'est nécessaire en V1.

### 6.6 Workflow Run

Les résultats GitHub Actions alimenteront d'abord la Santé : dernière
conclusion, durée, workflow, SHA et URL. Une ligne dans la mémoire Notion ne
sera créée que pour un résultat significatif et durable, par exemple une
livraison ou un échec bloquant explicitement sélectionné. Les logs et artefacts
ne doivent pas être copiés dans Notion.

## 7. Règles de regroupement en Development Sessions

### 7.1 Signaux examinés

| Signal | Force | Usage |
|---|---|---|
| Dépôt | Obligatoire | Une session ne traverse pas les dépôts en V1 |
| Identifiant explicitement fourni | Très forte | Permet une association ou correction contrôlée |
| Pull request | Très forte, ultérieure | Regroupe la branche de tête et donne une clôture |
| Branche / ref | Forte | Contexte primaire V1 |
| Continuité de commits | Forte | Confirme la suite `before → after` ou l'ascendance |
| Proximité temporelle | Moyenne | Sépare deux périodes sur une même branche |
| Merge | Forte pour clôture | Clôture possible d'une branche de travail |
| Release | Forte pour jalon | Clôture ou relation ultérieure |
| Message de commit | Faible | Titre et contexte seulement ; jamais identité |

### 7.2 Stratégie V1

Paramètres recommandés, configurables par Flux et figés dans chaque Run :

- `session_inactivity_window = 24 h` mesure l'absence de travail entre deux
  commits consécutifs ;
- `session_max_duration = 12 h` borne la lisibilité d'une session continue
  entre son premier commit et un commit candidat.

Ces deux paramètres sont indépendants et comparent les dates de commits, pas
l'heure de réception tardive d'un webhook. Aucun nombre maximal de commits ne
sert de règle de découpage.

Pour chaque commit d'un push, dans l'ordre d'ascendance :

1. chercher une association manuelle explicite `repository_id + SHA →
   session_id` ; si elle existe, l'appliquer ;
2. sinon rechercher une session `open` du même dépôt et de la même ref
   primaire ;
3. exiger que le commit courant respecte la fenêtre d'inactivité depuis le
   `last_activity_at` et la durée maximale depuis le `started_at` de la
   session ;
4. qualifier la continuité Git en `confirmed`, `unknown` ou `broken` :
   une ascendance prouvée confirme la continuité, des données insuffisantes
   restent inconnues, et seule une incompatibilité explicitement démontrée
   constitue une rupture ;
5. rattacher le commit si la continuité est `confirmed` ou `unknown` ; dans ce
   dernier cas, produire un avertissement non bloquant ;
6. ouvrir une nouvelle session si la continuité est `broken`, si la fenêtre
   est dépassée, si la durée maximale serait dépassée, ou si le dépôt ou la
   ref primaire diffèrent. La fenêtre et une rupture explicite sont évaluées
   avant la durée maximale.

Le `grouping_key` d'ouverture est une empreinte de
`grouping_version + repository_id + full_ref + first_commit_sha +
session_window_hours + session_max_duration_hours`. Il permet de retrouver la
même ouverture et distingue deux configurations temporelles, sans faire du
titre une identité. Une table de correspondance Hanuman conserve `commit_id →
session_id`; cette association vérifiée prévaut lors des retries.

La Phase 1 révisée utilise `grouping_version = 3`, car la durée maximale peut
modifier le regroupement des mêmes commits. La version entre dans le
`grouping_key` : une version donnée reste idempotente, mais la migration ne
conserve pas artificiellement les anciens `session_id`.

### 7.3 Ouverture, mise à jour et clôture

- **Ouverture :** premier commit non associé ne rejoignant aucune session
  admissible. Le titre calculé préfixe le nom lisible de branche à au plus deux
  catégories ou scopes Conventional Commit dominants, à partir de tous les
  commits de la session et avec une longueur bornée. Sans thème déterministe,
  il utilise `branche — Session du YYYY-MM-DD`.
- **Retrouver :** priorité à l'association persistée, puis au
  `grouping_key`, puis à l'unique session ouverte satisfaisant continuité,
  branche, fenêtre et durée maximale.
- **Mise à jour :** ajout ensembliste des commits, extension des dates,
  recalcul du titre technique seulement s'il n'a jamais été stabilisé, puis
  recalcul du résumé généré.
- **Clôture temporelle :** lorsqu'un nouveau commit arrive plus de 24 heures
  après la dernière activité, l'ancienne session est clôturée à son
  `last_activity_at` et une nouvelle est ouverte.
- **Clôture de lisibilité :** lorsqu'un commit candidat dépasserait la durée
  maximale depuis `started_at`, l'ancienne session est clôturée à son
  `last_activity_at` et une nouvelle est ouverte avec le commit candidat,
  même si la continuité Git est confirmée.
- **Clôture par merge :** si un merge vers la branche par défaut identifie
  sans ambiguïté une session de branche déjà connue, celle-ci est clôturée à la
  date du merge. Cette règle est facultative en V1 si la relation ne peut pas
  être prouvée avec les Données collectées.
- **Clôture explicite :** une commande manuelle peut clôturer une session ; un
  push tardif ouvre alors une nouvelle session sauf association manuelle.

### 7.4 Cas particuliers

- **Plusieurs pushes :** ils prolongent la même session si le dépôt, la ref et
  la fenêtre correspondent, sauf continuité explicitement rompue. Une
  continuité inconnue conserve le regroupement temporel et produit un
  avertissement. La livraison du push n'est pas l'identité de la session.
- **Branche principale :** les commits directs sont regroupés selon la même
  fenêtre de 24 heures. Une absence de preuve de continuité ne suffit pas à
  ouvrir une nouvelle session.
- **Merge :** le commit de merge appartient à la session de la ref poussée. Il
  peut fermer une session de branche liée, mais ne déplace pas ses commits.
- **Force-push :** aucun commit ni contenu éditorial n'est supprimé. Le Run
  signale une continuité rompue et ouvre une session ou demande un rattrapage.
- **Branche supprimée :** la session existante reste lisible et peut être
  clôturée ; aucune page Notion n'est supprimée.
- **Ordre de réception différent :** les dates et l'ascendance GitHub
  déterminent l'ordre ; les associations déjà vérifiées restent stables.

### 7.5 Correction manuelle

L'utilisateur peut, par commande Hanuman explicite :

- rattacher un ou plusieurs commits à une session existante ;
- séparer une session à partir d'un SHA ;
- fusionner deux sessions du même dépôt ;
- clôturer ou rouvrir une session.

La correction porte sur les correspondances Hanuman, produit un nouveau Run
traçable, met `status = manually_adjusted` et réécrit les projections Notion
concernées. Elle ne modifie ni GitHub ni le contenu éditorial Notion. Une
réexécution respecte la correction jusqu'à sa révocation explicite.

Les Agents IA pourront proposer un titre, un résumé ou un regroupement, mais
ne sont ni nécessaires ni autoritaires dans cette stratégie.

## 8. Modèle Notion cible

### 8.1 Compromis recommandé pour la V1

Deux bases suffisent :

1. **Repositories**, petite base de navigation et de contexte ;
2. **Development Sessions**, journal principal, contenant les commits sous
   forme de blocs structurés dans le corps de chaque page.

Une base **Commits** séparée améliorerait les requêtes techniques, mais
augmenterait fortement le nombre de pages, relations et écritures pour une
valeur de lecture faible en V1. GitHub fournit déjà la recherche précise. Une
base **Releases** devient pertinente seulement avec le support des releases.

### 8.2 Base Repositories

| Propriété | Type Notion probable | Visibilité |
|---|---|---|
| Nom | `title` | Visible |
| Dépôt GitHub | `url` | Visible |
| Propriétaire | `rich_text` ou `select` | Visible |
| Branche par défaut | `rich_text` | Visible |
| Dernière activité | `date` | Visible |
| État | `status` ou `select` | Visible |
| Sessions | `relation` | Visible dans la page, masquable en tableau |
| Visibilité GitHub | `select` | Visible selon besoin |
| GitHub Repository ID | `number` ou `rich_text` | Technique masqué |
| Clé Hanuman | `rich_text` | Technique masqué |
| Dernier Run vérifié | `rich_text` | Technique masqué |

Identifiant technique : `github_repository_id`. Un changement de nom met à
jour la page existante.

Vues utiles : dépôts actifs, activité récente et dépôt pilote.

### 8.3 Base Development Sessions

| Propriété | Type Notion probable | Visibilité |
|---|---|---|
| Titre | `title` | Visible ; éditorial si souhaité |
| Titre calculé | `rich_text` | Visible en secours |
| Repository | `relation` | Visible |
| État | `status` | Visible |
| Début | `date` | Visible |
| Fin | `date` | Visible |
| Dernière activité | `date` | Visible |
| Branches | `multi_select` | Visible |
| Résumé | `rich_text` | Visible |
| Nombre de commits | `number` | Visible |
| GitHub | `url` | Visible |
| PR / Release | `url` ou `relation` ultérieure | Visible seulement si renseigné |
| Session ID | `rich_text` | Technique masqué |
| Grouping version | `number` | Technique masqué |
| Grouping key | `rich_text` | Technique masqué |
| SHA premier / dernier | `rich_text` | Technique masqué |
| Dernier Run vérifié | `rich_text` | Technique masqué |

Identifiant technique : `session_id`, unique dans la base.

Le corps de page présente :

1. un court résumé déterministe ;
2. le contexte : dépôt, branche, période et lien GitHub ;
3. une liste chronologique compacte des commits :
   `date — SHA court — sujet — auteur — lien` ;
4. une zone éditoriale clairement séparée et jamais réécrite par Hanuman.

Vues utiles : sessions en cours, activité récente, sessions terminées, journal
chronologique et sessions groupées par Repository.

### 8.4 Modèle ultérieur

Une base Commits n'est ajoutée que si au moins un besoin validé exige des vues
transverses par auteur, SHA ou période, ou si le volume des blocs devient
impraticable. Son identité serait `repository_id + SHA`.

Une base Releases n'est ajoutée qu'avec `github.release.published`. Elle
contiendrait `repository_id + tag`, titre, date, notes, URL et relations aux
sessions. Aucun objet Notion n'est créé « au cas où ».

## 9. Expérience utilisateur dans Notion

La page d'entrée doit donner accès à :

- **Activité récente** : dernières sessions tous états confondus ;
- **Sessions en cours** : travail actif, dernière activité et branche ;
- **Sessions terminées** : historique filtrable par dépôt et période ;
- **Dépôts** : contexte et accès GitHub ;
- **Journal chronologique** : sessions triées par début décroissant ;
- **Releases** : vue ultérieure, absente en V1.

Une ligne de session doit rendre lisibles immédiatement le titre, le dépôt, la
branche, l'état, la période, le nombre de commits et le résumé. La page doit
répondre ensuite à « quels commits le prouvent ? » par des liens GitHub.

Notion ne montre pas par défaut les payloads d'Events, identifiants de
livraison, clés de corrélation, auteurs email, listes de fichiers ni logs. Les
champs techniques sont masqués des vues courantes mais restent disponibles
pour l'idempotence et le diagnostic.

## 10. Idempotence

### 10.1 Identités minimales

| Donnée | Identité |
|---|---|
| Repository | `github_repository_id` |
| Commit | `github_repository_id + SHA` |
| Pull request | `github_repository_id + number` |
| Release | `github_repository_id + tag` |
| Workflow Run | `github_repository_id + run_id` |
| Push Event | livraison GitHub ; sinon empreinte stable définie en 5.2 |
| Development Session | `session_id` opaque persisté ; `grouping_key` pour retrouver l'ouverture |

Le `idempotency_key` d'un Run V1 est
`flow_id + flow_version + event_id + target_notion_space_id`. Un retry du même
effet conserve cette clé. Un rattrapage possède son propre Run, mais les
identités de Données empêchent les doublons d'écriture.

### 10.2 Create-or-update

- rechercher les pages par propriété d'identité technique, jamais par titre ;
- refuser ou signaler plus d'une page pour la même identité ;
- créer si aucune correspondance n'existe ;
- mettre à jour uniquement les champs gérés par le Flux ;
- ajouter les commits par identité ensembliste et ordre GitHub ;
- conserver les champs éditoriaux Notion ;
- enregistrer l'identifiant Notion et la vérification dans le Run.

Une page déjà présente et conforme produit un effet `skipped`, pas une seconde
création. Une page présente mais obsolète est mise à jour.

### 10.3 Retry, rattrapage et écriture partielle

Les retries de transport sont bornés et suivent la politique du Connecteur.
Une reprise manuelle crée un nouveau Run relié au précédent, relit les preuves
et ne retente que les effets absents ou non confirmés.

Si l'écriture des commits dans le corps réussit mais la mise à jour de la
session échoue, le Run conserve l'identifiant de page et l'empreinte des blocs
confirmés. La reprise relit la page, calcule la différence et complète la
session. Elle ne réajoute pas aveuglément les commits.

Un rattrapage compare la borne GitHub demandée au dernier SHA vérifié, collecte
une plage bornée, puis applique les mêmes identités et regroupements. La durée
de conservation des correspondances Hanuman doit couvrir au minimum la durée
de vie active du Flux et sa période de migration ; elles ne doivent pas être
supprimées tant qu'une réexécution historique est possible.

## 11. Pipeline du Flux

Le pipeline applique le moteur existant ; il ne crée pas une architecture
générale supplémentaire.

```text
Trigger
→ Event
→ collecte GitHub
→ normalisation
→ validation
→ regroupement
→ plan d'écriture
→ écriture Notion
→ vérification
→ FlowResult
→ Run
→ Santé
```

| Step | Entrée | Sortie | Effet | Erreurs principales | Métriques |
|---|---|---|---|---|---|
| Trigger | Livraison ou commande | Event/commande normalisée | Acquittement, aucun effet Notion | Authentification, signature, format | reçus, rejetés, latence de réception |
| Event | Données minimales | Event validable et référence de Run | Création de la trace de Run | Version non supportée, doublon | event type, âge, doublons |
| Collecte GitHub | Dépôt, ref, SHA/bornes | Repository et commits complets utiles | Lecture GitHub | Non autorisé, introuvable, quota, réponse incomplète | appels, commits lus, durée |
| Normalisation | Réponses GitHub | Données canoniques avec provenance | Aucun effet externe | Format inattendu, horodatage invalide | normalisés, rejetés |
| Validation | Données normalisées et paramètres | Ensemble admissible | Aucun effet externe | SHA/ref invalide, cible absente, volume dépassé | valides, invalides, ignorés |
| Regroupement | Commits et correspondances | Sessions et associations proposées | Lecture des correspondances Hanuman | Ambiguïté, continuité rompue | sessions ouvertes/retrouvées/clôturées |
| Plan d'écriture | État désiré + état Notion lu | Opérations ordonnées et empreinte | Lecture Notion, aucune écriture | Schéma incompatible, identité dupliquée | créations/mises à jour/ignorés planifiés |
| Écriture Notion | Plan valide | Preuves d'effets | Create-or-update des pages et blocs | Quota, indisponibilité, effet partiel | créés, mis à jour, ignorés, échoués |
| Vérification | Preuves et propriétés attendues | Vérifications par effet | Relecture Notion ciblée | Page/relations/propriétés non confirmées | vérifiés, non conformes, indéterminés |
| FlowResult | StepResults | Bilan structuré | Aucun effet externe | Agrégation incohérente | tous compteurs métier |
| Run | Event, plan, résultats | Statut terminal et journal métier | Persistance des preuves nécessaires | Journal indisponible | durée, statut, erreur principale |
| Santé | Runs et diagnostics Connecteurs | Synthèse datée | Mise à jour de la Santé | Données trop anciennes | retard, dernier succès/échec |

L'ordre d'écriture recommandé est Repository, session, contenu des commits,
relations, puis propriétés finales. Les StepResults portent leurs entrées,
sorties, effets, métriques et erreurs expurgées.

## 12. Plan, preview, apply, verify

### 12.1 Plan

Le plan est le calcul interne, traçable et sans écriture :

- cible Notion et version de schéma attendue ;
- créations, mises à jour et absences d'effet ;
- champs gérés concernés ;
- associations commit/session ;
- ordre des opérations ;
- empreinte des Données sources et état Notion lu ;
- ambiguïtés, permissions et coût estimé en appels.

Un Run automatique produit toujours ce plan, même sans confirmation humaine.

### 12.2 Preview

La preview est la présentation du plan à l'utilisateur lors d'une commande
manuelle : nombre de sessions et commits concernés, pages créées ou mises à
jour, regroupements proposés, avertissements et cible exacte. Un plan seulement
journalisé ou calculé en mémoire n'est pas une preview.

La sortie terminal détaillée présente le Repository, puis chaque Development
Session avec son identité, sa clé abrégée, son état, ses dates, ses
avertissements et ses commits. Les effets sont regroupés par Repository,
sessions, fermetures et absence de changement. La sortie terminal par défaut
reste synthétique ; les associations complètes restent disponibles dans le
JSON structuré, dont le schéma de plan reste `2` : les paramètres, causes
d'ouverture et métriques de séparation sont des ajouts compatibles.

La preview doit expirer ou être invalidée si l'empreinte GitHub, la cible ou
l'état Notion pertinent change avant l'application.

### 12.3 Apply

L'apply exécute uniquement un plan valide et autorisé. En mode automatique,
l'approbation est fournie par la configuration du Flux pour les dépôts,
branches et cibles autorisés. Aucun dialogue humain n'est requis, mais le plan
reste lié au Run.

La V1 ne planifie aucune suppression Notion.

### 12.4 Verify

La vérification relit ou confirme au minimum :

- l'identifiant technique et l'URL de chaque page créée ou mise à jour ;
- la cible parente ;
- la relation session → Repository ;
- le `session_id`, les SHA premier/dernier et le nombre de commits ;
- la présence des références de commits essentielles ;
- l'absence de duplication connue.

Une réponse HTTP réussie sans preuve suffisante ne vaut pas vérification. Un
échec de vérification obligatoire interdit le statut `succeeded`.

## 13. Erreurs et résultats partiels

| Situation | Comportement |
|---|---|
| Dépôt non autorisé | Rejet avant collecte et écriture ; `failed`, ou `skipped` si une règle de filtre attendue l'exclut |
| Signature invalide ou évent trop ancien | Rejet sans Run métier exécutable ; trace de sécurité ; si Run créé, `failed` |
| Commit introuvable | Nouvelle lecture bornée ; sinon élément échoué, aucun commit inventé |
| Branche supprimée | Conserver et éventuellement clôturer la session ; `skipped` sans nouvel effet |
| Réponse GitHub incomplète | Retry borné ; ne pas écrire la partie non validée |
| Base Notion absente ou cible non autorisée | Échec avant apply ; `failed` |
| Propriété Notion incompatible | Échec du plan avant écriture ; `failed` |
| Page déjà présente | Vérifier l'identité ; mise à jour ou `skipped` si conforme |
| Identité technique présente sur plusieurs pages | Conflit ; ne pas choisir arbitrairement ; `failed` ou `partially_succeeded` si d'autres effets sont confirmés |
| Commits écrits, session finale échouée | Conserver les preuves ; reprise ciblée ; `partially_succeeded` |
| Quota ou indisponibilité | Retry borné avec backoff ; état partiel fidèle si effets déjà confirmés |
| Vérification impossible | Effet `indeterminate` ; `partially_succeeded` si une écriture utile est prouvée, sinon `failed` |

### 13.1 Statuts terminaux

- **`succeeded`** : tous les effets attendus sont réalisés et toutes les
  vérifications obligatoires réussissent ; des éléments déjà conformes peuvent
  être ignorés.
- **`partially_succeeded`** : au moins un effet utile est confirmé et au moins
  un effet attendu a échoué ou reste indéterminé.
- **`failed`** : aucun résultat utile attendu n'est obtenu, une précondition
  obligatoire échoue, ou l'intégrité globale ne peut être garantie.
- **`skipped`** : aucun effet utile n'est nécessaire : Event déjà traité et
  conforme, push sans commit pertinent, branche filtrée ou condition
  explicitement non satisfaite.

Le FlowResult distingue `resources_read`, `resources_created`,
`resources_updated`, `resources_skipped` et `resources_failed`, ainsi que les
effets confirmés, non confirmés et les avertissements.

## 14. Santé

### 14.1 Santé du Connecteur GitHub

Elle distingue déclaré, configuré, autorisé, joignable et sain. Preuves :
authentification, accès au dépôt pilote, dernière lecture représentative,
latence, quotas, erreurs et fraîcheur. Un ping ou la seule présence du
Connecteur ne suffit pas.

### 14.2 Santé du Connecteur Notion

Elle distingue les mêmes états et vérifie en particulier l'accès en lecture et
écriture aux bases autorisées, la compatibilité minimale du schéma, la latence,
les quotas et la dernière écriture représentative vérifiée.

### 14.3 Santé du Flux

Les Runs structurés alimentent :

- dernière réception GitHub ;
- dernier Run, dernier succès et dernier échec ;
- statut, durée et erreur principale expurgée ;
- commits lus, créés dans la mémoire, mis à jour et ignorés ;
- sessions créées, mises à jour et clôturées ;
- releases traitées, à zéro tant que hors portée ;
- vérifications réussies, échouées ou indéterminées ;
- retard entre `occurred_at` GitHub et la vérification Notion ;
- ancienneté du dernier SHA vérifié par dépôt ;
- volume de rattrapage restant lorsqu'il est connu.

Un Flux peut être `healthy`, `degraded`, `failing` ou `unknown` selon des seuils
configurés et datés. Par exemple, un Connecteur joignable avec un dernier Run
partiel donne une Santé de Flux dégradée, pas saine. La Santé ne déduit jamais
le statut depuis des messages libres.

## 15. Sécurité

- Vérifier la signature HMAC, le type d'Event et la fraîcheur des webhooks
  avant toute collecte.
- Utiliser une liste explicite de `github_repository_id` autorisés ; ne pas se
  fier au seul nom.
- Restreindre les branches si le projet l'exige ; en V1, autoriser
  explicitement la branche par défaut et les branches du dépôt pilote.
- Garder tokens, secrets webhook et credentials hors Events, plans,
  FlowResults, previews et logs.
- Utiliser les permissions GitHub minimales en lecture : métadonnées et contenu
  des commits ; Issues, PR, Actions et administration ne sont pas requises en
  V1.
- Donner à l'intégration Notion l'accès uniquement aux bases Repositories et
  Development Sessions de test ou de production choisies.
- Valider les identifiants exacts de l'espace et des bases Notion avant apply ;
  ne jamais accepter une cible fournie librement par un payload GitHub.
- Ne pas stocker par défaut emails d'auteurs, diffs, fichiers, payloads
  complets, logs Actions, secrets détectés ou contenu privé inutile.
- Neutraliser le texte GitHub avant affichage ; il reste une Donnée non fiable,
  jamais une instruction pour Hanuman ou un Agent IA.
- Authentifier et autoriser API, CLI distante et GitHub Action. Le modèle local
  actuel ne doit pas conduire à exposer directement `hanuman.main:app` sur
  Internet.
- Un endpoint public éventuel doit être dédié, limité en taille et débit,
  protégé contre le rejeu, acquitter rapidement la réception et ne jamais
  révéler l'état interne ou les credentials.

## 16. Compatibilité avec l'existant

### 16.1 Inventaire conceptuel

| Élément existant | Classement | Réutilisation ou écart |
|---|---|---|
| `GitHubService` | Adapter | Authentification, erreurs et lectures de base réutilisables ; ajouter ultérieurement des capacités commits sans logique de session |
| `NotionService` | Garder / adapter | Transport, pagination, recherche et CRUD réutilisables ; les opérations idempotentes et la vérification doivent rester pilotées par le Flux |
| Clients fins GitHub et Notion dans `services/adapters` | Garder si utiles | Frontières techniques possibles, sans imposer une couche universelle |
| Registre des Connecteurs | Garder | Catalogue et diagnostics ; pas moteur d'exécution |
| Configuration et authentification existantes | Adapter | Conserver les secrets locaux ; ajouter des paramètres explicites de dépôt et cible sans les placer dans les Events |
| `run_log_service` et journal JSONL | Adapter ou remplacer progressivement | Preuve utile mais contrat trop léger pour FlowRun, StepResults, idempotence et effets partiels |
| Tests GitHub, Notion et orchestration | Garder / adapter | Doubles réseau, erreurs et create-or-update réutilisables ; ajouter des tests du nouveau contrat sans faire dépendre la suite du réseau |
| Orchestration `github_to_notion` centrée Issues | Garder intacte puis déprécier | Ne correspond pas au nouveau besoin ; ne pas l'étendre au prix de deux intentions mélangées |
| Wrapper historique `github_sync_notion_services` | Déprécier plus tard avec l'ancien Flux | Compatibilité de chemin, pas fondation du nouveau Flux |
| Application `hanuman.main:app` | Garder | Seul point d'entrée FastAPI canonique pour une future API |

Le nouveau Flux doit respecter :

```text
Trigger / interface
→ orchestration du Flux
→ services réutilisables
→ Connecteurs GitHub et Notion
```

Il ne doit ni appeler une API externe directement, ni faire choisir la
Destination Notion par un Connecteur.

### 16.2 Coexistence avec l'ancien Flux

L'ancien Flux Issues, sa configuration, ses tests et son tableau Notion restent
intacts pendant les phases 0 à 5. Les deux Flux ont des identités, Runs,
paramètres et cibles distincts. Le nouveau Flux ne réutilise pas comme cible la
base Issues.

L'ancien Flux peut être arrêté seulement lorsque :

1. le nouveau Flux a réussi sur tous les dépôts activés pendant une période
   d'observation validée par le propriétaire ;
2. aucun Run partiel non résolu ni retard de rattrapage ne subsiste ;
3. les utilisateurs confirment que les Issues ne sont plus nécessaires comme
   projection Notion active ;
4. les liens ou contenus éditoriaux encore utiles du tableau Issues sont
   inventoriés ;
5. un retour à l'ancien déclenchement reste documenté.

Après l'arrêt, sa configuration peut être archivée seulement quand le dernier
Run, les paramètres non secrets et la date d'arrêt sont conservés. Le tableau
Issues peut être supprimé seulement après une nouvelle période d'archive, une
validation humaine explicite et la confirmation qu'aucun lien, contenu
éditorial ou processus ne le dépend. L'archivage Notion réversible est préféré
avant toute suppression.

## 17. Migration

| Phase | Contenu | Critères de sortie |
|---|---|---|
| 0 — Spécification et validation | Valider autorités, V1, regroupement, cible et sécurité | Décisions bloquantes tranchées ; spécification acceptée ; ancien Flux inchangé |
| 1 — Manuel / CLI, dépôt pilote | Collecte bornée et plan sans écriture de production | Events, identités, regroupements et FlowResults vérifiés sur cas nominaux, doublons, force-push et reprises |
| 2 — Cible Notion de test | Preview, apply et verify sur deux bases dédiées | Schéma pratique validé ; zéro doublon après réexécution ; effets partiels récupérables |
| 3 — Déclenchement automatique | GitHub Action sûre puis webhook signé cible | Signature/authentification, acquittement, replay, rattrapage et même Flux démontrés |
| 4 — Dépôts choisis | Activation explicite, un dépôt puis extension | Chaque dépôt autorisé, cible validée, borne initiale fixée et propriétaire informé |
| 5 — Observation et stabilisation | Suivre Santé, retard, erreurs et qualité de regroupement | Période et seuils approuvés ; aucun partiel ouvert ; rattrapage nul ; corrections manuelles rares et comprises |
| 6 — Dépréciation ancien Flux Issues | Arrêter ses déclencheurs sans supprimer code, configuration ni tableau | Conditions 16.2 satisfaites ; date, responsable et retour arrière documentés |
| 7 — Archivage puis suppression éventuelle | Archiver configuration et tableau ; supprimer seulement après validation | Contenu utile migré ou conservé, dépendances nulles, délai d'archive écoulé, accord humain explicite |

Chaque changement de phase est réversible jusqu'à la suppression finale. Une
phase échouée n'autorise pas l'arrêt de l'ancien Flux.

## 18. V1 minimale

### 18.1 Contenu recommandé

- un dépôt pilote identifié par son ID GitHub ;
- `github.push` et une commande `github.backfill.requested` bornée ;
- CLI manuelle en premier, API locale facultative ;
- Repository, branche de contexte et commits minimaux ;
- Development Sessions déterministes avec fenêtre de 24 heures ;
- deux bases Notion : Repositories et Development Sessions ;
- commits affichés dans le corps de la session, sans base dédiée ;
- create-or-update par identités techniques ;
- plan interne pour tous les Runs et preview pour le manuel ;
- apply automatique seulement après configuration explicite ;
- vérification Notion obligatoire ;
- FlowResult, Run et StepResults structurés ;
- métriques de Santé et reprise ciblée.

### 18.2 Repoussé

Sont repoussés : webhook public de production si la frontière sûre n'est pas
prête, pull requests détaillées, Events de merge dédiés, releases, tags,
GitHub Actions, Issues contextuelles, base Commits, fichiers et statistiques,
multi-dépôts, multi-espaces Notion, roadmap et Agents IA.

Cette V1 est utile même sans ces capacités : elle transforme déjà les pushes
en un journal de sessions lisible et prouvé par GitHub.

## 19. Évolutions futures

- **Pull requests :** clé forte de regroupement, contexte et clôture.
- **Releases et tags :** jalons, vue Releases et liens aux sessions.
- **GitHub Actions :** Santé des validations et livraisons ; persistance Notion
  seulement pour des résultats sélectionnés.
- **Agents IA :** propositions de titres et résumés avec provenance, modèle et
  possibilité de refus ; aucun rôle dans l'identité ou l'idempotence.
- **Roadmap :** proposition de mise à jour, jamais écriture implicite.
- **Documentation :** liens vers documents modifiés ou publiés, sans copier le
  contenu du dépôt.
- **Constellation :** représentation du Flux et de sa Santé, pas nouvelle
  source de vérité.
- **Plusieurs dépôts :** activation explicite, paramètres et retard par dépôt.
- **Plusieurs espaces Notion :** routage configuré et autorisé ; identités
  qualifiées par cible.
- **Journal quotidien ou hebdomadaire :** vue ou synthèse dérivée des sessions,
  sans dupliquer leur identité.
- **Base Commits :** seulement après validation d'un besoin de requête
  transverse ou d'une limite pratique des blocs.

## 20. Hors périmètre

Sont explicitement exclus :

- le remplacement de GitHub ;
- la copie complète de GitHub dans Notion ;
- la création automatique de code ;
- la revue automatique de pull requests ;
- un nouveau moteur générique ;
- Kafka, Redis, Celery, RabbitMQ ou équivalent sans besoin prouvé ;
- la synchronisation bidirectionnelle GitHub ↔ Notion ;
- la refonte générale de Notion ;
- la collecte systématique des diffs, fichiers, logs et payloads bruts ;
- la suppression ou modification immédiate du tableau Issues ;
- la migration globale des autres Flux ;
- une dépendance obligatoire aux Agents IA.

## 21. Décisions ouvertes

Ces décisions nécessitent une validation produit ou métier. Les détails
d'implémentation ordinaires ne sont pas des décisions ouvertes.

### 21.1 Structure Notion finale

| Option | Avantages | Inconvénients |
|---|---|---|
| Deux bases, commits dans les sessions | Lisible, peu d'écritures, V1 rapide | Requêtes transverses sur commits limitées |
| Trois bases avec Commits | Relations et filtres précis | Beaucoup de pages, risque de recopier GitHub |
| Une seule base Sessions | Minimal | Navigation par dépôt et métadonnées moins propres |

**Recommandation :** deux bases en V1 ; réévaluer la base Commits sur usage
réel.

### 21.2 Définition exacte d'une Development Session

| Option | Avantages | Inconvénients |
|---|---|---|
| Dépôt + branche + continuité + fenêtre 24 h | Déterministe, explicable, sans discipline supplémentaire | Peut séparer une session longue ou regrouper une journée dense |
| Une session par branche | Très simple | Branches longues et branche principale illisibles |
| Regroupement IA | Titres et thèmes potentiellement meilleurs | Non déterministe, coûteux, difficile à corriger |

**Recommandation :** stratégie déterministe 24 heures, configurable après le
pilote et complétée plus tard par les PR.

### 21.3 Déclencheur automatique initial

| Option | Avantages | Inconvénients |
|---|---|---|
| GitHub Action | Mise en place ciblée par dépôt | Nécessite une route Hanuman sûre et joignable |
| Webhook GitHub | Natif, signé, faible latence | Exposition et acquittement à sécuriser |
| Tâche planifiée | Aucun endpoint entrant | Latence et polling |

**Recommandation :** CLI pour le premier pilote ; GitHub Action comme premier
automatisme si l'accès est sûr ; webhook signé comme cible de production.

### 21.4 Dépôt pilote

| Option | Avantages | Inconvénients |
|---|---|---|
| Hanuman | Activité réelle et connaissance du domaine | Risque de bruit pendant le développement du Flux |
| Petit dépôt de test représentatif | Contrôle et sécurité | Moins représentatif des usages |

**Recommandation :** commencer par un dépôt de test représentatif, puis Hanuman
avant toute extension.

### 21.5 Niveau de détail des commits

| Option | Avantages | Inconvénients |
|---|---|---|
| SHA, date, auteur, sujet, URL | Suffisant pour la preuve, lecture rapide | Moins de contexte local |
| Ajouter corps, fichiers et statistiques | Plus riche | Coût, bruit et risque sensible |

**Recommandation :** détail minimal en V1 ; GitHub porte le détail technique.

### 21.6 Conditions de clôture

| Option | Avantages | Inconvénients |
|---|---|---|
| Inactivité 24 h + clôture manuelle | Disponible dès les pushes | Une session peut être clôturée avant reprise tardive |
| Merge uniquement | Signal métier fort | Ne couvre pas branches principales et travail sans PR |
| Inactivité + merge/PR lorsque prouvé | Couverture et précision | Règle un peu plus riche |

**Recommandation :** inactivité de 24 heures en V1, clôture manuelle possible,
puis merge/PR comme signal fort dans une version ultérieure. Valider la durée
sur le dépôt pilote.

## 22. Critères d'acceptation

La spécification et, ultérieurement, le Flux conforme sont acceptés si :

- le vocabulaire produit est **Flux**, **Connecteurs**, **Données**,
  **Santé**, **Agents IA** et **Paramètres** ;
- le Flux applique `HANUMAN_FLOW_ENGINE` sans en redéfinir l'architecture ;
- GitHub reste la source de vérité des identités et Données techniques ;
- Notion apporte une mémoire structurée et conserve ses contenus éditoriaux ;
- aucune direction Notion → GitHub n'est implicite ;
- les Issues sont secondaires et absentes du cœur V1 ;
- la V1 reste limitée à un dépôt, aux pushes, commits et sessions ;
- la Development Session possède une identité opaque, une règle de
  regroupement versionnée et une correction manuelle ;
- les identités et règles d'idempotence ne reposent jamais sur un titre ;
- un Run structuré représente les Steps, effets, erreurs partielles,
  vérifications et métriques ;
- la Santé du Flux est distincte de celle de chaque Connecteur ;
- le plan existe pour l'automatique et la preview est réellement présentée
  dans le manuel ;
- les écritures Notion sont vérifiées et reprises sans duplication ;
- la migration maintient l'ancien Flux jusqu'à stabilisation prouvée ;
- aucune suppression prématurée du tableau Issues n'est proposée ;
- aucune infrastructure générique ou distribuée inutile n'est imposée ;
- le nouveau Flux utilise des services réutilisables et aucun appel externe
  direct depuis l'orchestration ;
- toute future API utilise uniquement `hanuman.main:app`.
