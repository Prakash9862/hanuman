# Hanuman - Catalogue des flux (Brouillon V1)

> Ce document recense uniquement les flux validés.
> Un flux n'entre dans ce catalogue que s'il répond à un besoin concret et apporte un réel gain de temps.
>
> Principe :
> Hanuman n'est pas une collection de connecteurs.
> Hanuman est un orchestrateur qui automatise des tâches du quotidien.

---

# Critères de validation

Un flux doit répondre à trois questions :

- Est-il réellement utile ?
- Fait-il gagner du temps ?
- Évite-t-il une tâche répétitive ou un oubli ?

Si la réponse est non, le flux n'est pas retenu.

---

# Flux validés

## 1. Calendar → Maps → Notion ⭐⭐⭐⭐⭐

### Objectif

Préparer automatiquement un rendez-vous.

### Déclencheur

Création ou modification d'un événement Google Calendar.

### Fonctionnement

Google Calendar
↓
Détection du lieu
↓
Google Maps
↓
Calcul du trajet
↓
Création d'une fiche Notion

### Données possibles

- date
- heure
- adresse
- temps de trajet
- heure de départ conseillée
- lien Maps
- notes
- documents liés
- mails liés (plus tard)

### Pourquoi ce flux ?

C'est un véritable assistant de rendez-vous.

---

## 2. GitHub → Notion ⭐⭐⭐⭐⭐

### Objectif

Suivre automatiquement l'évolution d'un projet.

### État

Flux quasiment terminé.

Il reste uniquement le système de déclencheur automatique.

### Fonctionnement

Push GitHub
↓
Analyse
↓
Mise à jour Notion

### Pourquoi ce flux ?

Évite la mise à jour manuelle de la documentation projet.

---

## 3. Hanuman → Obsidian (Cuisine) ⭐⭐⭐⭐☆

### Objectif

Créer rapidement une fiche recette propre dans Obsidian.

### Déclencheur

Bouton "Nouvelle recette".

### Fonctionnement

Hanuman
↓
Génération d'un modèle Markdown
↓
Création dans Obsidian

### Contenu

- titre
- date automatique
- durée
- ingrédients
- sauces
- cuisson
- photos
- commentaires

### Particularité

Création automatique des liens Obsidian.

Exemple :

[[Poulet]]

[[Curry]]

[[Four]]

[[Poêle]]

[[Sauce soja]]

L'objectif n'est pas d'écrire un livre de cuisine mais de construire progressivement une base de connaissances personnelle.

---

## 4. YouTube → Obsidian ⭐⭐⭐⭐☆

### Objectif

Retrouver facilement une vidéo plusieurs mois plus tard.

### Déclencheur

Ajout manuel depuis Hanuman.

### Fonctionnement

Hanuman
↓
Création d'une fiche Obsidian

### Données

- titre
- chaîne
- URL
- durée
- date
- genre
- sous-genre
- commentaires

### Particularité

Création automatique des liens Obsidian.

Exemple :

[[Python]]

[[Hanuman]]

[[Cuisine]]

[[IA]]

---

# Fonctionnalités validées

## Routines

Une nouvelle section de Hanuman sera dédiée aux routines.

Exemple :

- Routine Matin
- Routine Santé
- Routine Cuisine
- Routine Travail
- Routine Soir

L'objectif est de regrouper plusieurs actions fréquentes dans une interface simple.

---

## Agents IA

Les agents IA font partie de la vision de Hanuman.

En revanche :

- leur rôle exact reste à définir ;
- aucun développement ne sera lancé avant d'avoir clarifié leur fonctionnement.

---

# Règles de conception

Hanuman doit toujours privilégier :

- la simplicité ;
- l'automatisation ;
- le gain de temps.

Un nouveau connecteur n'est accepté que s'il permet plusieurs flux réellement utiles.

Un nouveau flux n'est accepté que s'il répond à un besoin concret du quotidien.

L'objectif n'est jamais de remplacer les logiciels existants (Notion, Obsidian, Gmail, Google Calendar, etc.), mais de les coordonner intelligemment.

---

# Journal de Vie (Hygiène de vie)

## Statut

🟢 Concept validé

---

## Objectif

Créer un bilan quotidien complet en moins de **3 minutes**.

Le rôle de Hanuman n'est pas de remplacer Notion, mais de proposer une interface beaucoup plus agréable et rapide, puis d'enregistrer automatiquement toutes les données dans une base Notion.

Le suivi doit permettre d'obtenir :

- un historique complet des journées ;
- des statistiques à long terme ;
- des corrélations entre habitudes et qualité de vie ;
- un indice global de la journée.

---

## Philosophie

Le système ne doit pas être un simple "tracker d'habitudes".

Il doit mesurer la **qualité globale d'une journée**.

Le questionnaire doit être rapide, majoritairement composé de boutons, cases à cocher, curseurs et listes.

Objectif :

> Temps de saisie maximal : **3 minutes**.

---

# Fonctionnement

Chaque soir :

```
Journal de Vie

≈ 2 à 3 minutes
```

Hanuman pose une série de questions courtes.

À la fin :

- calcul d'un Indice Hanuman (/100) ;
- affichage d'un résumé de la journée ;
- enregistrement dans Notion.

---

# Piliers de vie

## ❤️ Santé

Exemples :

- sobriété
- douleurs
- maladie
- médicaments
- énergie

---

## 😴 Sommeil

- durée
- qualité

---

## 🏃 Activité physique

Sous-catégories :

- marche
- musculation
- cardio
- vélo
- étirements
- yoga
- autre

+ durée

---

## 🍎 Alimentation

Exemples :

- repas maison
- fast-food
- restaurant
- alimentation équilibrée
- hydratation

---

## 😊 Humeur

Échelle :

1 → 10

---

## 💻 Informatique

Sous-catégories :

- Hanuman
- développement
- open source
- apprentissage
- veille

---

## 📚 Culture

Sous-catégories :

- lecture
- musique
- piano
- film
- documentaire
- podcast
- conférence
- musée

---

## ✍️ Création

Sous-catégories :

- écriture
- documentation
- composition
- autre

---

## 🙏 Spiritualité

Sous-catégories :

- méditation
- franc-maçonnerie
- réflexion personnelle
- lecture philosophique
- autre

---

## 👥 Vie sociale

Exemples :

- famille
- amis
- sortie
- appel
- rencontre

---

# Événements marquants

Une journée peut contenir plusieurs événements.

Exemples :

- entretien
- voyage
- concert
- dentiste
- sortie
- anniversaire
- premier commit important

---

# Réflexion quotidienne

Deux champs libres très courts.

## Plus belle réussite de la journée

Une phrase.

---

## Point à améliorer

Une phrase.

---

# Indice Hanuman

Calcul automatique.

Exemple :

```
Indice Hanuman

83 /100

★★★★☆
```

L'objectif n'est pas de "noter" l'utilisateur mais de suivre l'évolution de la qualité de vie au fil du temps.

---

# Analyses

Le système doit permettre de répondre automatiquement à des questions comme :

- Quels sont mes meilleurs mois ?
- Est-ce que le sport améliore mon humeur ?
- Est-ce que je dors mieux lorsque je cuisine davantage ?
- Quels jours sont les plus productifs ?
- Quelles activités sont les plus corrélées à une bonne journée ?

---

# Connecteurs utilisés

## Notion

Stockage de toutes les données.

---

## Horloge

- date
- heure
- horodatage du questionnaire
- durée éventuelle

---

## GitHub

Pré-remplissage éventuel de l'activité informatique.

---

## Google Calendar

Pré-remplissage de certains événements.

---

## Google Maps

Pré-remplissage éventuel des déplacements ou de la marche (optionnel).

---

## YouTube

Suggestion automatique de certaines activités culturelles.

---

# Principes

- moins de 3 minutes par jour ;
- interface agréable, jamais un tableur ;
- pré-remplissage dès que possible ;
- stockage dans Notion ;
- analyses automatiques à long terme ;
- Hanuman orchestre les données, il ne remplace pas Notion.

---

# Connecteurs validés

## Productivité

- Gmail
- Google Calendar
- Google Maps
- Notion
- Obsidian
- GitHub

---

## Connaissances

- YouTube
- Chess.com

---

## Services personnels

- Contacts ✅
- Horloge ✅

---

---

# Fonctionnalités transversales

Ces fonctionnalités ne remplacent aucun logiciel existant.

Elles permettent à Hanuman d'orchestrer les différents connecteurs afin de proposer une expérience plus fluide.

---

## Daily (Accueil)

🟢 Concept validé

### Objectif

Offrir, dès l'ouverture de Hanuman, une vue synthétique de la journée.

Le Daily ne stocke aucune nouvelle donnée.

Il agrège uniquement les informations provenant des différents connecteurs.

### Exemples

- prochains rendez-vous Google Calendar ;
- temps de trajet Google Maps ;
- mails importants Gmail ;
- état des synchronisations importantes ;
- rappel des routines (Journal de vie, routine du matin, etc.).

### Philosophie

Le Daily doit permettre de comprendre sa journée en quelques secondes.

Il ne remplace ni Notion, ni Google Calendar.

Il centralise uniquement les informations utiles du moment.

---

## Recherche globale

🟢 Concept validé

### Objectif

Retrouver instantanément une information, quel que soit le connecteur d'origine.

### Fonctionnement

Une unique barre de recherche est disponible depuis l'écran d'accueil.

Elle interroge simultanément les connecteurs disponibles.

Exemples :

- Gmail
- Notion
- Obsidian
- Google Calendar
- GitHub
- YouTube
- Contacts
- données générées par Hanuman

### Exemple

Recherche :

```
dentiste
```

Résultats possibles :

- rendez-vous Google Calendar ;
- mail Gmail ;
- fiche Notion ;
- note Obsidian ;
- itinéraire Google Maps.

### Philosophie

La recherche doit être réellement utile.

Elle doit permettre d'accéder à l'ensemble des données connectées sans avoir à se souvenir dans quel logiciel elles sont stockées.

---

# Connecteurs à explorer

Ces connecteurs présentent un intérêt potentiel mais nécessitent une étude technique avant validation.

---

## LinkedIn

### Flux envisagés

- LinkedIn → Notion (offres d'emploi)
- LinkedIn → Contacts (contacts professionnels)
- LinkedIn → Google Calendar (suivi des entretiens et relances)

Objectif :

Centraliser le suivi d'une recherche d'emploi sans remplacer LinkedIn.

---

## Too Good To Go

### Flux envisagés

- Too Good To Go → Google Calendar
- Too Good To Go → Google Maps

Objectif :

Ajouter automatiquement un rappel de retrait ainsi que les informations pratiques (adresse, heure, itinéraire).

À confirmer selon les possibilités offertes par l'application.

---

# Pistes retenues (À approfondir)

Cette section regroupe les idées jugées suffisamment pertinentes pour être conservées, mais qui nécessitent encore une réflexion plus poussée avant d'être transformées en flux ou en fonctionnalités.

---

# Fonctionnalités transversales

## Daily (Accueil)

🟢 Concept validé

### Objectif

Le Daily constitue le point d'entrée principal de Hanuman.

Il offre une vue synthétique de la journée sans créer de nouvelles données.

Il centralise les informations importantes provenant des différents connecteurs.

### Exemples

- prochains rendez-vous Google Calendar ;
- temps de trajet Google Maps ;
- mails importants Gmail ;
- état des synchronisations ;
- rappel des routines (Journal de vie, routine du matin, etc.).

### Philosophie

Le Daily doit permettre de comprendre sa journée en quelques secondes.

Il ne remplace aucun logiciel existant.

Il centralise uniquement les informations utiles au bon moment.

---

## Recherche globale

🟢 Concept validé

### Objectif

Retrouver instantanément une information, quel que soit le logiciel dans lequel elle est stockée.

### Connecteurs concernés

- Gmail
- Notion
- Obsidian
- Google Calendar
- GitHub
- Contacts
- YouTube
- données générées par Hanuman

### Philosophie

Une seule barre de recherche.

L'utilisateur ne doit plus avoir à se demander où se trouve une information.

Hanuman se charge de la retrouver.

---

# Connecteurs

## Contacts

🟢 Validé

Permet de relier automatiquement plusieurs informations autour d'une même personne.

---

## Horloge

🟢 Validé

Utilisations envisagées :

- horodatage ;
- routines ;
- rappels ;
- statistiques ;
- gestion du temps.

---

## Temps

🟡 À approfondir

Objectif :

Estimer automatiquement la répartition du temps passé dans les différents domaines de vie.

Exemples :

- développement ;
- culture ;
- apprentissage ;
- activité physique ;
- déplacements.

Le but n'est pas de surveiller l'utilisateur mais d'enrichir automatiquement le Journal de vie avec le minimum de saisie.

---

# Flux à explorer

## Gmail intelligent

🟡 À approfondir

Objectif :

Réduire le temps passé à gérer sa boîte mail.

Exemples de flux :

- suppression intelligente des newsletters ;
- archivage automatique ;
- identification des mails administratifs importants ;
- proposition de création d'un rendez-vous Calendar lorsque cela est pertinent.

---

## Générateur de prompts

🟟 Concept retenu

Objectif :

Générer automatiquement des prompts adaptés au contexte.

Hanuman connaît déjà :

- le projet ;
- les connecteurs ;
- les données disponibles ;
- les fichiers concernés.

Il peut donc construire un prompt beaucoup plus pertinent sans que l'utilisateur ait à réécrire tout le contexte.

Cette fonctionnalité devra être définie plus précisément.

---

## Gestion administrative

🟡 À approfondir

Objectif :

Créer une page Notion unique regroupant toute l'administration personnelle.

Exemples :

- impôts ;
- CAF ;
- banque ;
- mutuelle ;
- assurances ;
- salaire ;
- abonnements ;
- échéances ;
- documents importants.

Les connecteurs (principalement Gmail et Google Calendar) viendront alimenter automatiquement cette page afin de limiter au maximum les saisies manuelles.

Hanuman n'a pas vocation à remplacer Notion.

Il facilite simplement l'organisation des données administratives.

---

# Règles de validation

Avant d'ajouter un nouveau connecteur ou un nouveau flux, trois questions doivent toujours être posées.

## 1.

Est-ce que cette fonctionnalité sera réellement utilisée plusieurs fois par semaine ?

---

## 2.

Est-ce qu'elle fait réellement gagner du temps ou supprime des clics ?

---

## 3.

Est-ce qu'une autre application (Notion, Obsidian, Gmail...) ne fait pas déjà cela correctement ?

---

Si l'une de ces réponses est négative, la fonctionnalité ne doit probablement pas être intégrée à Hanuman.

---

# Philosophie

Hanuman n'est pas un logiciel qui remplace les autres.

Hanuman est un orchestrateur.

Chaque nouvelle fonctionnalité doit :

- réduire le nombre de manipulations ;
- éviter les ressaisies ;
- centraliser les informations utiles ;
- exploiter intelligemment les connecteurs existants.

Chaque clic supplémentaire est un échec.

Chaque clic supprimé est une réussite.
