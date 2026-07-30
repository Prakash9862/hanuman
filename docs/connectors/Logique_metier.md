Phase I — Définir un modèle universel de connecteur

Avant de développer chaque connecteur indépendamment, on définit ce qu'est un "espace connecteur" dans Hanuman.

Tous les connecteurs devraient partager une structure commune.

Présentation
│
├── Données
├── Recherche
├── Actions
├── Statistiques
├── Configuration
├── Informations techniques
└── Logs

Chaque section peut être vide ou absente selon le connecteur.

L'objectif est que l'utilisateur retrouve toujours la même logique.

Phase II — Définir chaque connecteur

Là, on ne code pas.

On rédige la fiche métier de chaque connecteur.

Par exemple :

DevDocs
Mission

Accéder rapidement à la documentation technique.

Données
documentation
technologies
pages
historique
Recherche
texte libre
langage
bibliothèque
Actions
ouvrir une page
copier le lien
Statistiques
recherches récentes
documents ouverts
Informations techniques
disponibilité
version
temps de réponse
Google Contacts

Mission :

Être le carnet d'adresses universel de Hanuman.

Recherche :

nom
téléphone
mail
entreprise

Actions :

créer
modifier
supprimer
fusionner (si Google le permet)

Informations :

groupes
anniversaires
organisation
Monkeytype

Mission :

Exposer toutes les statistiques de frappe.

Statistiques :

WPM
précision
meilleurs scores
historique
progression
temps de pratique
langues
modes
graphiques
heatmap (si disponible)

Actions :

ouvrir Monkeytype
lancer une synchronisation
actualiser les données

Informations techniques :

utilisateur connecté
dernière synchronisation
Phase III — Définir les ressources

C'est probablement la couche qui manque aujourd'hui.

Chaque connecteur expose des ressources.

Exemple :

Google Contacts

Contacts

Groupes

Anniversaires

DevDocs :

Documentation

Technologies

Historique

Monkeytype :

Sessions

Statistiques

Records

Ces ressources sont ce que les flux utiliseront ensuite.

Phase IV — Définir les capacités

Chaque ressource possède des capacités standardisées.

Par exemple :

read

search

create

update

delete

export

sync

Tous les connecteurs n'ont pas toutes les capacités, mais ils parlent le même langage.

Phase V — Concevoir l'interface

Seulement une fois la logique métier définie.

Je vois une navigation du type :

Monkeytype

────────────────────

Présentation

Statistiques

Historique

Synchronisation

Configuration

Informations techniques

Logs

Et exactement la même philosophie pour tous les connecteurs.

Phase VI — Construire les flux

Une fois les connecteurs terminés.

À ce moment-là seulement, on commence à les relier.

Par exemple :

Monkeytype
      ↓
Notion

rapport hebdomadaire

ou

Contacts
      ↓
Gmail

envoyer un mail

ou

DevDocs
      ↓
OpenAI

résumer une documentation
