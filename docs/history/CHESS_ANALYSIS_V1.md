# Analyse Stockfish V1

Cette V1 analyse les fichiers Markdown contenant un bloc `pgn` dans le dossier `Echecs/Parties` du vault Obsidian.

## Classification

- `??` : perte >= 200 centipions
- `?` : perte de 100 à 199 centipions
- `?!` : perte de 50 à 99 centipions
- `!!` : meilleur coup quasi unique, tactique ou sacrifice correct, avec forte confiance

Une position qui passe de `+7` à `+5` perd 200 centipions et reçoit donc `??`, même si elle reste gagnante.

## Configuration

Variables facultatives dans `.env` :

```env
OBSIDIAN_VAULT_PATH=/home/vince/Prakash/projets/Obsidian_Priv
CHESS_OBSIDIAN_PATH=/home/vince/Prakash/projets/Obsidian_Priv/Echecs
STOCKFISH_PATH=/usr/games/stockfish
```

## Première vérification rapide

Commencer par une seule partie et une profondeur modérée :

```bash
poetry run python -m hanuman.orchestrations.chess_analysis --limit 1 --depth 14
```

Puis cinq parties :

```bash
poetry run python -m hanuman.orchestrations.chess_analysis --limit 5 --depth 16
```

Analyse complète :

```bash
poetry run python -m hanuman.orchestrations.chess_analysis --depth 18
```

Stockfish reste ouvert pendant tout le lot puis est fermé proprement à la fin. Le script ne se lance pas automatiquement depuis Santé.

## Fichiers produits

Pour chaque partie :

- le Markdown est enrichi entre deux marqueurs Hanuman ;
- un fichier voisin `.analysis.json` conserve les données détaillées par coup.

Dans `Echecs/` :

- `Analyse Stockfish.md` : synthèse globale et tableau par ECO ;
- `Qualite/Gaffe.md` ;
- `Qualite/Erreur.md` ;
- `Qualite/Douteux.md` ;
- `Qualite/Excellent.md` ;
- `Qualite/Excellent manque.md`.

Les marqueurs rendent l'opération réexécutable : une nouvelle analyse remplace l'ancien bloc Hanuman sans dupliquer le contenu.

## Limites de la V1

- `??`, `?` et `?!` reposent sur la perte brute par rapport au meilleur coup ;
- `!!` est volontairement conservateur ;
- la détection sémantique des thèmes récurrents viendra après validation sur les premières parties ;
- les fichiers JSON sont la source de données prévue pour les futurs regroupements par motif, ouverture et phase de jeu.
