# Hanuman — Catalogue des flux
*Version de travail*

---

# 1. Mission

Hanuman est un orchestrateur personnel.

Il ne remplace pas les logiciels existants (Notion, Obsidian, Gmail, Google Calendar, GitHub, etc.).

Son objectif est de les connecter intelligemment afin de réduire les manipulations, les ressaisies et les oublis.

Chaque fonctionnalité doit répondre à un besoin concret du quotidien.

---

# 2. Philosophie

Les principes suivants guident l'ensemble du développement.

## Hanuman est un orchestrateur

Hanuman ne cherche pas à remplacer les outils spécialisés.

Il coordonne les applications existantes afin de créer des automatisations utiles.

---

## Chaque clic supplémentaire est un échec.

Chaque clic supprimé est une réussite.

---

## L'utilisateur doit passer le moins de temps possible dans Hanuman.

L'objectif n'est pas de créer une nouvelle application dans laquelle passer ses journées.

Au contraire, Hanuman doit permettre de retourner le plus rapidement possible aux logiciels réellement utilisés.

---

## Les données restent dans les outils adaptés.

Exemples :

- Notion pour les bases de données.
- Obsidian pour les connaissances personnelles.
- Gmail pour les mails.
- Google Calendar pour les rendez-vous.

Hanuman orchestre ces données mais ne les remplace pas.

---

# 3. Critères de validation

Avant d'ajouter un connecteur ou un flux, trois questions doivent toujours être posées.

## 1.

Cette fonctionnalité sera-t-elle réellement utilisée plusieurs fois par semaine ?

---

## 2.

Fait-elle réellement gagner du temps ou supprimer des manipulations ?

---

## 3.

Une autre application réalise-t-elle déjà cette tâche correctement ?

---

Si l'une de ces réponses est négative, la fonctionnalité ne doit probablement pas être développée.

---

# 4. Catalogue des connecteurs

## Validés

### Productivité

- Gmail
- Google Calendar
- Google Maps
- Notion
- Obsidian
- GitHub

### Connaissances

- YouTube
- Chess.com

### Services personnels

- Contacts
- Horloge

---

## À approfondir

### Temps

Objectif :

Estimer automatiquement la répartition du temps consacré aux différents domaines de vie afin d'enrichir le Journal de Vie sans saisie supplémentaire.

Exemples :

- développement ;
- culture ;
- apprentissage ;
- activité physique ;
- déplacements.

---

### LinkedIn

Flux envisagés :

- LinkedIn → Notion
- LinkedIn → Contacts
- LinkedIn → Google Calendar

Objectif :

Faciliter le suivi d'une recherche d'emploi.

---

### Too Good To Go

Flux envisagés :

- Too Good To Go → Calendar
- Too Good To Go → Maps

Objectif :

Créer automatiquement les rappels de retrait.

---

# 5. Flux validés

## Calendar → Maps → Notion ⭐⭐⭐⭐⭐

Objectif :

Préparer automatiquement un rendez-vous.

Fonctionnement :

Google Calendar

↓

Détection du lieu

↓

Google Maps

↓

Calcul du trajet

↓

Création d'une fiche Notion

Données possibles :

- date
- heure
- adresse
- temps de trajet
- heure de départ
- lien Maps
- notes
- documents
- mails liés (plus tard)

---

## GitHub → Notion ⭐⭐⭐⭐⭐

Objectif :

Mettre automatiquement à jour la documentation projet.

État :

Flux quasiment terminé.

Il reste principalement le déclencheur automatique.

---

## Hanuman → Obsidian (Cuisine) ⭐⭐⭐⭐☆

Objectif :

Créer automatiquement une fiche recette structurée dans Obsidian.

Création automatique :

- modèle Markdown
- liens Obsidian
- catégories
- ingrédients
- cuisson
- commentaires

---

## YouTube → Obsidian ⭐⭐⭐⭐☆

Objectif :

Conserver durablement une vidéo intéressante.

Création automatique :

- fiche Markdown
- métadonnées
- liens Obsidian

---

# 6. Fonctionnalités transversales

Ces fonctionnalités exploitent plusieurs connecteurs simultanément.

---

## Daily

Statut :

✅ Validé

Objectif :

Afficher en quelques secondes tout ce qui est important aujourd'hui.

Exemples :

- prochains rendez-vous ;
- temps de trajet ;
- mails importants ;
- routines ;
- état des synchronisations.

Le Daily ne stocke aucune donnée.

Il agrège simplement les informations utiles.

---

## Recherche globale

Statut :

✅ Validé

Une seule barre de recherche.

Elle interroge simultanément :

- Gmail
- Notion
- Obsidian
- Google Calendar
- GitHub
- Contacts
- YouTube
- données Hanuman

Objectif :

Retrouver une information sans avoir à se souvenir où elle est stockée.

---

# 7. Routines

## Statut

Concept validé.

Objectif :

Regrouper plusieurs actions fréquentes dans une interface unique.

Exemples :

- Routine Matin
- Routine Santé
- Routine Travail
- Routine Cuisine
- Routine Soir

Le Journal de Vie constitue la première routine importante.

---

# 8. Journal de Vie

## Statut

✅ Validé

### Objectif

Créer un bilan quotidien complet en moins de trois minutes.

Toutes les données sont enregistrées dans Notion.

Hanuman fournit uniquement une interface plus rapide et agréable.

---

## Philosophie

Le Journal de Vie mesure la qualité globale d'une journée.

Ce n'est pas un simple tracker d'habitudes.

Le questionnaire doit être essentiellement composé :

- de boutons ;
- de curseurs ;
- de listes ;
- de cases à cocher.

Temps maximal :

3 minutes.

---

## Fonctionnement

Chaque soir :

Journal de Vie

↓

Questionnaire

↓

Calcul de l'Indice Hanuman

↓

Résumé

↓

Enregistrement dans Notion

---

## Piliers

- Santé
- Sommeil
- Activité physique
- Alimentation
- Humeur
- Informatique
- Culture
- Création
- Spiritualité
- Vie sociale

---

## Événements marquants

Une journée peut contenir plusieurs événements.

Exemples :

- entretien
- voyage
- concert
- dentiste
- anniversaire
- premier commit important

---

## Réflexion quotidienne

Deux réponses très courtes :

- plus belle réussite
- point à améliorer

---

## Indice Hanuman

Calcul automatique.

Objectif :

Suivre l'évolution de la qualité de vie.

---

## Analyses

Exemples :

- Quels sont mes meilleurs mois ?
- Le sport améliore-t-il mon humeur ?
- Quels jours sont les plus productifs ?
- Quelles habitudes sont les plus bénéfiques ?

---

## Pré-remplissage

Connecteurs utilisés :

- Horloge
- GitHub
- Google Calendar
- Google Maps
- YouTube

Notion reste le stockage principal.

---

# 9. Fonctionnalités à approfondir

## Gmail intelligent

Objectif :

Réduire drastiquement le temps passé à gérer sa boîte mail.

Idées :

- suppression intelligente des newsletters ;
- archivage automatique ;
- détection des mails administratifs ;
- création éventuelle d'événements Calendar.

---

## Générateur de prompts

Concept retenu.

Objectif :

Produire automatiquement des prompts adaptés au contexte.

Hanuman connaît déjà :

- le projet ;
- les fichiers ;
- les connecteurs ;
- les données disponibles.

Le fonctionnement précis reste à définir.

---

## Gestion administrative

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
- documents ;
- échéances.

Les connecteurs (principalement Gmail et Google Calendar) alimentent automatiquement cette page.

Notion reste la source de vérité.

---

# 10. Vision

## Agents IA

Concept retenu.

Leur rôle exact reste à définir.

Aucun développement ne sera lancé avant d'avoir clarifié leur architecture et leur utilité.

---

# 11. Roadmap

À compléter progressivement.

L'objectif est de classer chaque fonctionnalité selon son niveau de priorité afin de conserver une vision claire du développement futur.

---

Accueil

Flux

Connecteurs

Journal de Vie

Santé

Agents IA

Paramètres

Et à l'intérieur de "Journal de Vie" :

Quotidien

Administration

Cuisine

...

---

Domaine	Connecteurs retenus
Notes	Obsidian, Notion
IA	ChatGPT, Claude, Ollama, Open WebUI
Développement	GitHub, DevDocs, Bruno
Clavier	Monkeytype, Typing.io
Réflexion visuelle	Excalidraw, Penpot
Échecs	Chess.com, Lichess, Stockfish, Leela Zero
Santé	OpenFoodFacts, Cronometer (à confirmer)
Apprentissage	Anki
Calendrier	Google Calendar
Mail	Gmail

Retenus
ChatGPT
Claude
Ollama
Open WebUI
DevDocs
Bruno
Monkeytype
Typing.io
Excalidraw
Penpot
Lichess
Stockfish
Leela Chess Zero
SCID
Anki
OpenFoodFacts
Cronometer — encore à confirmer
Contacts
Horloge

Cette liste correspond notamment au tableau récapitulatif ajouté à la fin du catalogue.

À explorer ou à approfondir
LinkedIn
Too Good To Go
