# ADR-00X — Paramètres comme centre de contrôle d'Hanuman

- **Statut** : Accepté
- **Date** : 2026-07-31
- **Décideurs** : Hanuman
- **Type** : Architecture / Frontend / Backend

---

# Contexte

Hanuman est un moteur d'orchestration.

Il ne remplace pas les outils externes (Notion, Obsidian, Gmail, Google Calendar, GitHub, etc.) mais les coordonne.

À mesure que le projet grandit, Hanuman possède désormais plusieurs éléments internes :

- connecteurs ;
- flux ;
- routines ;
- Journal de Vie ;
- agents IA ;
- paramètres d'application ;
- diagnostics ;
- statistiques ;
- logs ;
- historique.

Il est nécessaire de définir un point d'entrée unique permettant d'administrer l'ensemble du système.

---

# Décision

La section **Paramètres** devient le centre de contrôle complet d'Hanuman.

Toutes les fonctionnalités permettant d'observer, configurer ou diagnostiquer Hanuman sont regroupées dans cette section.

La barre latérale ne contient donc qu'une seule entrée :

```
Paramètres
```

L'organisation interne est la suivante :

```text
Paramètres
├── Général
├── Connecteurs
├── Flux
├── Journal de Vie
├── Apparence
├── IA
├── Diagnostic
└── À propos
```

---

# Philosophie

Les Paramètres concernent exclusivement Hanuman.

Ils ne servent pas à configurer les applications externes elles-mêmes mais leur intégration dans Hanuman.

Exemples :

- configuration OAuth ;
- chemins locaux ;
- préférences internes ;
- état des modules ;
- surveillance ;
- maintenance.

---

# Général

Configuration globale d'Hanuman.

Exemples :

- environnement
- debug
- niveau de logs
- répertoires
- préférences générales

---

# Connecteurs

Configuration des connecteurs enregistrés.

Exemples :

- OAuth
- API Keys
- chemins locaux
- état de connexion
- capacités disponibles

La liste doit être construite dynamiquement à partir des connecteurs enregistrés.

Aucun connecteur ne doit être ajouté manuellement dans le frontend.

---

# Flux

Gestion des flux d'orchestration.

Exemples :

- Obsidian → Notion
- Notion → Obsidian
- GitHub → Notion
- Gmail → Journal

Chaque flux expose notamment :

- son état
- sa dernière exécution
- sa configuration
- ses erreurs éventuelles

La liste est entièrement dynamique.

---

# Journal de Vie

Le Journal de Vie possède sa propre section dans les Paramètres.

Même si aucune routine n'est encore implémentée, cette section existe dès le début.

Son objectif est de permettre :

- la configuration
- l'observation
- le diagnostic

Le développement fonctionnel du Journal de Vie est traité dans un ADR distinct.

---

# Apparence

Préférences de l'interface.

Exemples :

- thème
- animations
- langue
- affichage
- préférences utilisateur

---

# IA

Configuration des modèles d'intelligence artificielle.

Exemples :

- fournisseur
- modèles disponibles
- mémoire
- paramètres d'inférence

---

# Diagnostic

Le Diagnostic est une sous-section des Paramètres.

Il constitue le tableau de bord technique d'Hanuman.

Il regroupe notamment :

- état global
- disponibilité
- latence
- performances
- historique
- statistiques
- logs
- maintenance

Le Diagnostic ne constitue pas une page indépendante dans la navigation principale.

---

# À propos

Informations système.

Exemples :

- version
- licence
- build
- dépendances
- informations techniques

---

# Détection automatique

Les Paramètres ne doivent jamais contenir de listes codées en dur.

Toutes les sections concernées doivent détecter automatiquement les éléments enregistrés dans Hanuman.

Cela concerne notamment :

- connecteurs
- flux
- routines
- Journal de Vie
- agents
- programmes

Le frontend ne connaît pas la liste des modules.

Il affiche uniquement ce que le backend expose.

---

# Architecture

Le backend constitue l'unique source de vérité.

```text
Frontend

        │

        ▼

Paramètres

        │

        ▼

Backend

        │

        ▼

Registres Hanuman

        │

        ▼

Connecteurs
Flux
Routines
Journal de Vie
Agents
Programmes
```

Le frontend ne maintient aucune duplication de configuration.

---

# Principes

## Source unique de vérité

La description d'un module ne doit exister qu'à un seul endroit.

---

## Architecture déclarative

Chaque module décrit lui-même :

- son identité
- ses capacités
- son état
- ses paramètres

Les Paramètres ne font que les afficher.

---

## Zéro maintenance frontend

L'ajout d'un nouveau connecteur, flux ou routine ne doit nécessiter aucune modification du frontend des Paramètres.

---

## Évolutivité

Cette architecture permet d'ajouter de nouveaux modules sans modifier la structure des Paramètres.

Les futures extensions (Journal de Vie, Agents IA, Programmes, etc.) s'intègrent naturellement dans cette organisation.

---

# Conséquences

## Avantages

- une seule entrée d'administration ;
- séparation claire entre fonctionnalités métier et administration ;
- aucune duplication de configuration ;
- architecture extensible ;
- maintenance simplifiée ;
- cohérence avec la philosophie d'Hanuman comme moteur d'orchestration.

## Inconvénients

- nécessite un registre backend robuste ;
- demande une API de diagnostic centralisée ;
- implique une architecture déclarative des modules.

---

# Hors périmètre

Cet ADR ne définit pas :

- le fonctionnement interne du Journal de Vie ;
- les routines ;
- les Agents IA ;
- le contenu détaillé des diagnostics.

Ces sujets feront l'objet d'ADR dédiés.
