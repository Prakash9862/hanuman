# Hanuman — Constellation UI V1

Prototype autonome de l’écran d’accueil de Hanuman.

## Lancer

Depuis la racine du dépôt :

```bash
python -m http.server 4173 --directory ui/constellation
```

Puis ouvrir :

```text
http://127.0.0.1:4173
```

## Ce que contient cette V1

- constellation plein écran et responsive ;
- nœuds pour les intégrations existantes ;
- Gmail affiché comme intégration non connectée ;
- liaison Obsidian ↔ Notion animée ;
- inspecteur latéral interactif ;
- raccourci `Ctrl/⌘ + K` pour la recherche universelle ;
- aucune dépendance JavaScript ni étape de build.

## Étape suivante

Brancher l’interface sur une route FastAPI de type `/api/constellation` renvoyant les nœuds, les orchestrations et leur état réel, puis migrer l’expérience vers l’application frontend définitive si nécessaire.
