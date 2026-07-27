# ADR — Génération des pages d'ouverture Hanuman

**Statut :** Validé  
**Date :** 27/07/2026  
**Module :** Chess  
**Décision :** Architecture définitive des pages ECO

---

# Contexte

Hanuman génère actuellement une page par code ECO à partir des parties présentes dans le vault.

Les premières versions étaient essentiellement des index de parties.

L'objectif est désormais beaucoup plus ambitieux :

Une page d'ouverture ne doit pas être une fiche encyclopédique sur une ouverture d'échecs.

Elle doit devenir le dossier d'étude personnel du joueur sur cette ouverture.

Autrement dit :

> Hanuman ne décrit pas l'ouverture.
> Hanuman décrit la manière dont le joueur pratique cette ouverture.

Chaque page doit pouvoir répondre notamment aux questions suivantes :

- Est-ce que je joue réellement cette ouverture ?
- Quelle est ma variante principale ?
- Est-ce que je m'éloigne rapidement de la théorie ?
- Est-ce que mes résultats sont bons ?
- Est-ce que certaines variantes fonctionnent mieux que d'autres ?
- Est-ce que je fais toujours les mêmes erreurs ?
- Est-ce que je progresse avec le temps ?
- Où dois-je concentrer mon travail ?

Toutes ces informations doivent être produites automatiquement à partir du vault.

---

# Principes directeurs

Les pages ECO sont :

- personnelles ;
- entièrement générées ;
- entièrement régénérables.

Elles ne doivent jamais contenir de contenu rédigé manuellement.

Une reconstruction complète du module Chess doit permettre de les recréer intégralement.

Le vault constitue l'unique source de vérité.

---

# Source des données

Les informations proviennent exclusivement de :

- notes de parties ;
- PGN persistés ;
- analyses Stockfish persistées ;
- métadonnées Chess.com ;
- référence ECO officielle.

Aucune statistique ne doit être inventée.

Aucune information théorique ne doit être inventée.

Lorsque les données sont insuffisantes, Hanuman doit l'indiquer explicitement.

---

# Structure définitive

L'ordre des sections est figé.

```
YAML

👑 Vue d'ensemble

📖 Mon répertoire

    ⭐ Variante principale

    📚 Variantes secondaires

    📖 Référence théorique

❤️ Santé de l'ouverture

    Analyse générale

    Position type de sortie d'ouverture

📈 Évolution

❌ Gaffes récurrentes

💡 Opportunités manquées

🎯 Conclusion

🗂️ Parties
```

Aucune autre section ne doit être ajoutée.

---

# YAML

Le YAML représente la carte d'identité de l'ouverture.

Il doit être le plus riche possible.

Il est destiné à être exploité par :

- Dataview
- Graph View
- Dashboards
- recherches Obsidian
- automatisations futures
- autres modules Hanuman

Le YAML ne contient pas de longs commentaires.

Uniquement des métadonnées structurées.

Exemples :

- ECO
- nom officiel
- alias
- couleurs jouées
- nombre de parties
- statistiques
- période
- couverture Stockfish
- variante principale
- tags
- version du schéma
- statut
- etc.

---

# Vue d'ensemble

Cette section fournit un résumé immédiat.

Elle contient notamment :

- code ECO
- nom
- nombre total de parties
- parties avec Blancs
- parties avec Noirs
- V / N / D
- taux de réussite
- période couverte
- couverture Stockfish

Cette section doit rester compacte.

---

# Mon répertoire

Cette section décrit uniquement le répertoire réellement joué.

Elle comporte trois sous-parties.

---

## Variante principale

La variante principale correspond à la ligne la plus jouée.

Elle affiche :

- ligne SAN
- nombre de parties
- V / N / D
- taux de réussite
- commentaire synthétique

Elle constitue la référence personnelle du joueur.

---

## Variantes secondaires

Une variante secondaire est retenue uniquement si :

- au moins 5 parties

ou

- au moins 3 parties avec au moins 80 % de victoires.

Toutes les autres variantes sont regroupées dans :

> Autres essais

Les lignes SAN doivent être visibles immédiatement.

Aucune ouverture de panneau ne doit être nécessaire pour connaître la variante.

---

## Référence théorique

Cette partie ne constitue pas une analyse.

Elle sert uniquement de comparaison.

Elle affiche :

- nom officiel ECO
- ligne théorique officielle
- ligne réellement jouée
- premier point de divergence

Elle ne contient :

- aucun conseil ;
- aucune analyse ;
- aucune explication stratégique ;
- aucun jugement.

Son unique rôle est de montrer l'écart entre la théorie officielle et la pratique réelle.

---

# Référence ECO

La nomenclature officielle provient du document :

```
docs/chess/File_ECOMast-Codes_ECO.pdf
```

Ce document est considéré comme la référence officielle du module Chess.

Hanuman doit s'appuyer dessus pour :

- les noms officiels ;
- les variantes ;
- les lignes de référence lorsque celles-ci sont disponibles.

Si le document est incomplet, Hanuman doit le signaler.

Il ne doit jamais compléter la théorie de lui-même.

---

# Santé de l'ouverture

Cette section ne doit pas être calculée sur toutes les parties.

Elle doit être calculée uniquement sur :

- la variante principale

et

- les variantes secondaires dont le taux de réussite est supérieur ou égal à 80 %.

Les variantes expérimentales ne doivent pas influencer cette analyse.

Cette section contient deux parties.

---

## Analyse générale

Elle résume :

- résultats
- qualité globale
- couverture Stockfish
- limites des données

Lorsque les analyses sont insuffisantes, Hanuman doit l'indiquer.

---

## Position type de sortie d'ouverture

Cette partie décrit le milieu de jeu obtenu après l'ouverture.

Elle doit s'appuyer sur une position réellement récurrente.

Si aucune position n'est suffisamment récurrente, Hanuman doit le signaler.

Il ne doit jamais fabriquer une position représentative.

---

# Échiquiers

Les échiquiers sont générés sous forme de SVG.

Ils doivent rester autonomes.

À terme, chaque échiquier devra permettre :

- l'ouverture directe dans SCID ;
- le chargement de Stockfish ;
- l'accès au FEN ;
- l'accès aux parties correspondantes.

Le SVG constitue uniquement la représentation graphique.

Les métadonnées associées portent l'intelligence fonctionnelle.

---

# Évolution

Cette section montre la progression dans le temps.

Le graphique actuel est conservé.

Il présente notamment :

- évolution mensuelle
- réussite
- nombre de parties

Les mois sans partie sont ignorés.

---

# Gaffes récurrentes

Cette section recense uniquement les erreurs réellement récurrentes.

Une erreur n'est affichée que si une récurrence peut être démontrée.

Sans identité de position (FEN), aucune récurrence ne doit être inventée.

Lorsqu'une récurrence existe, la section pourra afficher :

- échiquier ;
- coup joué ;
- meilleur coup ;
- perte moyenne ;
- fréquence ;
- parties concernées.

---

# Opportunités manquées

Même philosophie que les gaffes.

Aucune opportunité ne doit être inventée.

Une position n'est retenue que si elle est démontrable.

---

# Conclusion

La conclusion synthétise l'ensemble de la page.

Elle contient :

- synthèse globale ;
- axes de progression ;
- confiance des statistiques ;
- confiance de la qualité de jeu.

Une représentation visuelle est utilisée.

Par exemple :

```
Confiance résultats

★★★★★

Confiance qualité

★★☆☆☆
```

Cette représentation complète le texte.

Elle ne le remplace pas.

---

# Parties

Cette section est toujours située en dernière position.

Elle est repliée par défaut.

Elle contient uniquement les liens vers les parties.

Elle ne doit jamais perturber la lecture analytique de la page.

---

# Principes de génération

Une page ECO est entièrement générée.

Elle peut être reconstruite à tout moment.

Les anciennes pages pourront être remplacées lorsque le générateur définitif sera validé.

Les statistiques sont toujours recalculées.

Aucun contenu manuel n'est conservé.

---

# Principes esthétiques

Les pages doivent devenir une référence visuelle du module Chess.

Elles privilégient :

- callouts Obsidian ;
- hiérarchie visuelle claire ;
- icônes cohérentes ;
- tableaux limités ;
- texte synthétique ;
- lecture rapide.

Elles évitent :

- pavés de texte ;
- répétitions ;
- encyclopédisme ;
- tableaux inutiles.

---

# Contraintes

Hanuman ne doit jamais :

- inventer de statistiques ;
- inventer de théorie ;
- fabriquer une récurrence ;
- extrapoler une analyse ;
- modifier l'architecture de la page.

En cas de données insuffisantes, la limitation est affichée explicitement.

---

# Évolutions futures prévues

Les évolutions envisagées sont :

- persistance systématique des FEN ;
- échiquiers SVG interactifs ;
- ouverture directe dans SCID ;
- lancement automatique de Stockfish ;
- amélioration progressive de la couverture Stockfish ;
- enrichissement automatique de la théorie via des sources structurées.

Ces évolutions ne remettent pas en cause l'architecture définie dans cette ADR.

---

# Décision

Cette ADR fige l'architecture fonctionnelle des pages ECO de Hanuman.

Les développements futurs devront respecter cette structure.

Toute amélioration devra s'intégrer dans cette architecture sans en modifier l'organisation générale.
