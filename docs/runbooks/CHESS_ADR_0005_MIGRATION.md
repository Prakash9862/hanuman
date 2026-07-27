# Runbook — migration Chess ADR-0005

La migration réelle est une opération humaine. Hanuman ne la déclenche jamais
automatiquement.

## Étape 1 — Vérification Git

```bash
git branch --show-current
git status --short
git log -1 --oneline
poetry run pytest -q
```

Vérifier la branche attendue, un arbre propre, le commit validé et des tests
verts.

## Étape 2 — Sauvegarde du vault

Définir explicitement les chemins, puis archiver sans supprimer la source :

```bash
CHESS_SOURCE=/chemin/du/vault/Echecs
BACKUP=chess-vault-backup-$(date +%Y%m%d-%H%M%S).tar.gz
tar -czf "$BACKUP" -C "$(dirname "$CHESS_SOURCE")" "$(basename "$CHESS_SOURCE")"
tar -tzf "$BACKUP"
```

Conserver l’archive sur un support distinct et vérifier que la liste contient
les notes chronologiques et `_Index`.

## Étape 3 — Copie de preview

Choisir un parent vide ou une destination inexistante. Refuser de continuer si
la destination existe déjà :

```bash
PREVIEW_PARENT=/chemin/vers/preview-independante
test ! -e "$PREVIEW_PARENT/Echecs"
mkdir -p "$PREVIEW_PARENT"
cp -a "$CHESS_SOURCE" "$PREVIEW_PARENT/Echecs"
```

Cette procédure n’utilise ni nettoyage ni synchronisation avec suppression.

## Étape 4 — Reconstruction sur la copie

```bash
poetry run python -m hanuman.orchestrations.chess_rebuild_views \
  --vault-path "$PREVIEW_PARENT/Echecs"
```

Conserver le rapport JSON.

## Étape 5 — Vérifications manuelles

Ouvrir la copie dans Obsidian et vérifier :

- Dashboard et Profil échiquéen ;
- Ouvertures, Gaffes, Excellents coups, Opportunités et Motifs ;
- liens, callouts, CSS et absence de duplication ;
- contenu exact des `Notes personnelles` ;
- fichiers humains et index legacy toujours présents.

## Étape 6 — Comparaison

Avant et après la reconstruction, produire les listes et sommes :

```bash
find "$PREVIEW_PARENT/Echecs" -type f | sort
find "$PREVIEW_PARENT/Echecs" -path '*/[0-9][0-9][0-9][0-9]/[0-9][0-9]/*.md' \
  -type f -print0 | sort -z | xargs -0 sha256sum
```

Comparer les inventaires et confirmer que les notes de parties ont exactement
les mêmes sommes. Inspecter chaque fichier ajouté ou modifié sous `_Index`.

## Étape 7 — Autorisation humaine

Arrêter ici. Une personne doit valider explicitement la preview, le rapport et
les comparaisons avant toute opération sur le vrai vault.

## Étape 8 — Exécution réelle future

Après autorisation explicite seulement, la commande prévue est :

```bash
poetry run python -m hanuman.orchestrations.chess_rebuild_views \
  --vault-path "$CHESS_SOURCE"
```

Ne pas l’exécuter dans le cadre de ce runbook préparatoire. Recalculer ensuite
les sommes des notes sources et contrôler le rapport.

## Étape 9 — Retour arrière

Ne pas écraser le vault en place. Extraire d’abord l’archive dans un répertoire
de restauration distinct :

```bash
RESTORE_PARENT=/chemin/vers/restauration-independante
mkdir -p "$RESTORE_PARENT"
tar -xzf "$BACKUP" -C "$RESTORE_PARENT"
find "$RESTORE_PARENT/Echecs" -type f | sort
```

Comparer la restauration au vault, fermer Obsidian, puis faire valider
manuellement les fichiers à restaurer. Cette procédure évite toute commande de
suppression ou remplacement récursif ambigu.
