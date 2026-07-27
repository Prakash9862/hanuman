# Vues Chess Obsidian

## Rôle et source de vérité

Hanuman conserve chaque partie une seule fois sous
`Echecs/YYYY/MM/date - ECO - adversaire.md`. Ces notes, leur PGN, leur analyse
visible et leur bloc `ChessInsight` sont les sources de vérité. Les fichiers
sous `Echecs/_Index` sont uniquement des vues dérivées et recalculables.

La reconstruction hors ligne suit cette chaîne :

1. `chess_vault_reader_service` relit le frontmatter des notes chronologiques ;
2. `chess_analysis_summary_service` relit le bilan Stockfish visible existant ;
3. `chess_insight_storage_service` désérialise les blocs structurés ;
4. `chess_insight_aggregation_service` déduplique et agrège les occurrences ;
5. `chess_insight_view_service` rend les accueils et synthèses thématiques ;
6. `chess_index_service` orchestre toutes les vues et les écrit atomiquement.

La commande de reconstruction n’importe aucun client Chess.com et ne lance
aucun moteur Stockfish.

## Analyse visible et ChessInsight

Le bloc d’analyse entre `HANUMAN_CHESS_ANALYSIS_START` et
`HANUMAN_CHESS_ANALYSIS_END` est le rapport lisible par l’utilisateur. Le bloc
technique entre `HANUMAN_CHESS_INSIGHTS_START` et
`HANUMAN_CHESS_INSIGHTS_END` contient un JSON UTF-8 déterministe :

```json
{
  "eco": "B20",
  "game_id": "identifiant",
  "insights": [],
  "schema_version": 1
}
```

Le schéma courant est la version 1. Une version inconnue ou un JSON invalide
est diagnostiqué et ne produit aucun événement. Une ancienne analyse sans bloc
structuré reste valide, mais ne peut produire de synthèse sans une analyse
Stockfish explicitement demandée.

## Seuils et synthèses

Les seuils portent sur les parties uniques, pas sur le nombre brut
d’occurrences :

- 3 parties : « Signal émergent », affiché dans l’accueil sans note dédiée ;
- 4 parties : « Tendance confirmée », affichée distinctement sans note dédiée ;
- 5 parties ou plus : « Synthèse durable », avec une note dédiée.

Une synthèse qui repasse sous cinq parties est conservée et marquée
« Inactive — seuil actuellement non atteint ». Aucune vue n’est supprimée.
Toutes les occurrences sont affichées par partie dans un ordre déterministe.
Aucun détecteur de motif supplémentaire n’est actif.

## Commande de reconstruction

La cible doit être une racine Chess explicite et existante :

```bash
poetry run python -m hanuman.orchestrations.chess_rebuild_views \
  --vault-path /chemin/vers/une-copie/Echecs
```

La commande refuse un chemin vide, inexistant, un fichier, `/`, le dossier
personnel seul et tout chemin situé dans le dépôt Hanuman. Elle ne lit ni
`CHESS_OBSIDIAN_PATH` ni `OBSIDIAN_VAULT_PATH`. Elle n’offre aucune option
`reset`, `clean` ou `delete`.

Le rapport JSON indique les notes découvertes, exploitables et ignorées, les
catégories de vues écrites, la couverture des blocs structurés, les doublons,
les fichiers humains protégés et les erreurs de lecture.

Il n’existe volontairement pas de `--dry-run` : tester toujours sur une copie
indépendante. La commande ne modifie aucune note chronologique et vérifie après
génération qu’aucun fichier existant n’a disparu.

## Guide utilisateur

1. Sauvegarder le dossier `Echecs` et vérifier l’archive.
2. Créer une copie indépendante, sans supprimer une destination existante.
3. Lancer `rebuild-views` sur cette copie.
4. Examiner dans Obsidian le Dashboard, le Profil, les Ouvertures et les quatre
   catégories thématiques.
5. Vérifier les liens, l’esthétique et les sections `Notes personnelles`.
6. Comparer les sommes SHA-256 des notes chronologiques avant et après.

La commande génère Dashboard, Profil, Ouvertures, accueils Motifs/Gaffes/
Excellents coups/Opportunités et synthèses durables. Elle ne modifie jamais les
notes de parties, PGN, analyses, blocs d’insights, fichiers legacy ou fichiers
humains sans marqueurs. Des marqueurs générés incomplets ou dupliqués provoquent
une erreur lisible : corriger manuellement la structure sur la copie ou
restaurer le fichier depuis la sauvegarde avant de recommencer.

Pour enrichir une ancienne partie dépourvue d’insights, lancer séparément et
explicitement l’analyse de cette seule partie après validation humaine. La
reconstruction des vues ne la réanalyse jamais.

## Preview reproductible

Sur une copie sûre uniquement :

```bash
find /tmp/hanuman-chess-adr-preview -type f -print0 | sort -z | xargs -0 sha256sum \
  > /tmp/chess-preview-before.sha256
find /tmp/hanuman-chess-adr-preview -type f | sort \
  > /tmp/chess-preview-before-files.txt
poetry run python -m hanuman.orchestrations.chess_rebuild_views \
  --vault-path /tmp/hanuman-chess-adr-preview
```

Répéter la commande, recalculer les sommes et comparer avec `diff -u`.
Calculer séparément les sommes des notes `YYYY/MM/*.md` et des sentinelles
legacy.

## Checklist de conformité ADR-0005

- [x] Dashboard et Profil sous `_Index`.
- [x] Vues Ouvertures, Motifs, Gaffes, Excellents coups et Opportunités.
- [x] Seuils 3–4–5 calculés sur les parties uniques.
- [x] Synthèse durable à partir de cinq parties.
- [x] Régression sans suppression et Notes personnelles préservées.
- [x] Fichiers humains sans marqueurs protégés.
- [x] Écritures des vues via `atomic_write_text()`.
- [x] Aucun reset destructif ni suppression automatique.
- [x] Reconstruction indépendante de Chess.com et Stockfish.
- [x] Blocs ChessInsight versionnés et diagnostics des blocs invalides.
- [x] Génération déterministe et idempotente.
- [ ] Détection de motifs tactiques : volontairement hors périmètre.
- [ ] Backfill des anciennes analyses sans insights : exige une réanalyse
  explicite et n’est pas automatisé.

## Limites et retour arrière

Le lecteur exige le frontmatter Hanuman et la convention de chemin
`YYYY/MM/date - ECO - adversaire.md`. Une note incomplète est ignorée et
signalée. La reconstruction ne supprime pas les anciennes vues devenues
orphelines. Pour revenir en arrière, conserver le vault actuel, extraire la
sauvegarde dans un dossier séparé, comparer, puis remplacer manuellement les
fichiers après validation ; ne jamais extraire aveuglément par-dessus le vault.
