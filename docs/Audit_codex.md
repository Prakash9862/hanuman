
• # 1. Résumé exécutif

  Confiance globale : élevée. L’audit porte sur le code réellement présent au commit
  fe6447d, ses appels, ses tests et sa documentation.

  Verdict :

  - Prêt pour inspection visuelle : non, car les défauts P0 touchent précisément la
    sécurité de la preview et la préservation des fichiers.

  - Prêt pour migration réelle : non.
  - Défauts bloquants P0 : 4.
  - Défauts importants P1 : 8.
  - Défauts mineurs P2 : 6.
  - Améliorations facultatives P3 : 3.
  - Conclusion retenue : C — bloquer toute migration et préparer un lot correctif
    prioritaire.

  Validations exécutées :

  - 107 tests Chess ciblés hors test API : réussis.
  - mypy sur les 15 fichiers principaux : réussi.
  - Ruff : réussi.
  - Black --check : réussi, 149 fichiers inchangés.
  - Le test API atteint ses assertions mais son processus ne se termine pas
    spontanément, probablement à cause du TestClient global non fermé.

  Les tests verts ne couvrent pas les scénarios les plus dangereux : collisions de
  noms, écrasement de contenu humain, symlinks et reconstruction partielle.

  # 2. Architecture réelle

  Les frontières principales existent, mais ne sont pas entièrement respectées :

  - Connexion externe : ChessService interroge Chess.com et normalise les réponses.
  - Modèle et nommage : ChessGame calcule adversaire, chemin, nom et lien.
  - Analyse : StockfishAnalyzer produit GameAnalysis et MoveAnalysis.
  - Construction structurée : build_chess_insights() transforme les coups en
    événements.

  - Persistance : les blocs d’analyse et ChessInsight sont injectés dans les notes.
  - Relecture : chess_vault_reader_service reconstruit des ChessGame sans PGN.
  - Agrégation : chess_analysis_summary_service et chess_insight_aggregation_service.
  - Rendu : chess_index_service et chess_insight_view_service.
  - Orchestration : synchronisation, analyse et rebuild CLI.

  chess_index_service.py est devenu le coordinateur central des vues : statistiques,
  lecture des insights, groupement des ouvertures, rendu général, protection partielle
  et appel des vues thématiques. Ce n’est pas encore un monolithe incontrôlable, mais
  il concentre environ six responsabilités.

  Fonctions longues justifiées comme difficiles à comprendre :

  - StockfishAnalyzer._analyse_game(), lignes 174–283 : environ 110 lignes, au moins
    six responsabilités — appels moteur, calcul des évaluations, classification,
    détection des excellents coups, construction des mouvements et synthèse globale.

  - render_analysis_markdown(), lignes 140–233 : environ 94 lignes, rendu de cinq
    sections avec plusieurs branches.

  - _game_note(), lignes 120–211 : environ 92 lignes, frontmatter, parsing PGN, statut
    d’analyse, navigation et rendu complet.

  - write_chess_insight_views_report(), lignes 353–431 : environ 79 lignes, cycle de
    vie actif/inactif, protection, rendu des accueils et comptage.

  - write_chess_indexes_report(), lignes 261–316 : environ 56 lignes, mais six
    responsabilités et plusieurs écritures successives non transactionnelles.

  ## Flux réel

  ### A. Chess.com vers Obsidian

  sync_chess_to_obsidian() → ChessService.get_latest_games() → _game_from_raw() →
  chess_game_path()/chess_game_filename() → extraction éventuelle de l’analyse et des
  insights existants → _game_note() → atomic_write_text() → write_chess_indexes().

  Écritures : chaque note récupérée, puis toutes les vues dérivées.

  Préservation réelle : uniquement le bloc d’analyse et le bloc ChessInsight reconnus.
  Aucun autre contenu de la note existante n’est préservé.

  ### B. Analyse Stockfish d’une note

  analyse_note() → lecture Markdown → extract_pgn() → StockfishAnalyzer.analyse_pgn()
  → _analyse_game() → métadonnées du frontmatter → build_chess_insights() → rendu de
  l’analyse → injection des deux blocs → une écriture atomique de la note complète.

  Le calcul précède l’écriture. Une erreur de parsing/injection avant
  atomic_write_text() laisse la note intacte.

  ### C. Construction des ChessInsight

  Pour chaque mouvement trié par ply :

  - classification == blunder → blunder;
  - excellent ou classification excellent → excellent;
  - missed_excellent → opportunity;
  - rôle déterminé par la couleur du joueur;
  - identifiant : game_id:ply:category:role, sinon hash dérivé.

  Une même position peut produire blunder et opportunity.

  ### D. Sérialisation et injection

  ChessInsightEnvelope.to_json() produit du JSON trié, UTF-8 et indenté.
  inject_insight_block() remplace exactement une zone valide ou ajoute le bloc en fin
  de note.

  Les marqueurs absents sont acceptés. Les marqueurs incomplets, inversés ou dupliqués
  sont refusés pour ChessInsight, mais pas correctement pour le bloc d’analyse
  visible.

  ### E. Rebuild hors ligne

  CLI → validate_chess_vault_path() → rebuild_chess_views() → read_chess_vault() →
  snapshots en mémoire → write_chess_indexes_report() → contrôles après écriture.

  Le flux n’importe directement ni Chess.com ni Stockfish. Il est donc hors ligne au
  sens réseau/moteur, mais pas sûr contre les redirections par symlink.

  ### F. Synthèses 3–4–5

  aggregate_persisted_chess_insights() lit les blocs → déduplique globalement par
  insight_id → groupe par catégorie/sous-type → compte les parties uniques →
  write_chess_insight_views_report().

  - 3 : signal émergent dans l’index.
  - 4 : tendance confirmée dans l’index.
  - 5 : synthèse durable individuelle.
  - Régression : une synthèse Hanuman existante devient inactive.

  # 3. Défauts bloquants — P0

  ## AUDIT-CHESS-001 — P0

  Fichiers et lignes : chess_to_obsidian.py:232-247, _game_note():120-211.

  Comportement observé : une note existante est entièrement reconstruite. Seuls le
  bloc d’analyse et le bloc ChessInsight sont extraits puis réinjectés.

  Scénario : l’utilisateur ajoute ## Notes personnelles, des liens, commentaires ou
  sections ailleurs dans une note de partie. La synchronisation suivante remplace le
  fichier et supprime tout ce contenu.

  Preuve : _game_note() ne reçoit que game, analysis_block et insight_block. Le test
  test_sync_preserves_existing_analysis, lignes 187–208, ne teste aucune annotation
  humaine hors marqueurs.

  Correction minimale : si la note existe, ne remplacer que des zones Hanuman
  explicitement délimitées ; à défaut de marqueurs complets, protéger le fichier et
  signaler un conflit.

  ## AUDIT-CHESS-002 — P0

  Fichiers et lignes : chess.py:41-47, chess_to_obsidian.py:232-247.

  Comportement observé : le nom ne contient pas game_id, seulement date, ECO et
  adversaire.

  Scénario : deux parties contre le même adversaire, le même jour et avec le même ECO
  produisent le même chemin. La seconde écriture remplace silencieusement la première,
  PGN compris.

  Preuve : chess_game_filename() retourne exactement date - ECO - adversaire.md; la
  boucle synchronise sans vérification d’identité du fichier existant.

  Correction minimale : intégrer une composante stable du game_id au nom, ou refuser
  explicitement toute collision lorsque le game_id du frontmatter diffère.

  ## AUDIT-CHESS-003 — P0

  Fichiers et lignes : chess_rebuild_views.py:16-31, chess_index_service.py:265-306,
  atomic_write_service.py:11-24.

  Comportement observé : seule la racine donnée est résolue. Les répertoires internes,
  notamment _Index, ne sont pas contrôlés après résolution.

  Scénario : <copie>/Echecs/_Index est un symlink vers le vrai vault ou un autre
  répertoire. La commande acceptée comme preview écrit en réalité dans la cible
  externe.

  Preuve : les écritures construisent root / "_Index" / ...; mkdir, mkstemp et replace
  suivent le symlink du parent.

  Correction minimale : résoudre et valider chaque destination avant écriture, refuser
  tout composant symlink ou garantir que destination.resolve() reste sous
  root.resolve().

  ## AUDIT-CHESS-004 — P0

  Fichiers et lignes : chess_index_service.py:274-286.

  Comportement observé : Dashboard et index d’ouverture sont écrasés
  inconditionnellement, sans marqueurs ni protection.

  Scénario : un humain possède déjà _Index/Dashboard.md ou _Index/Ouvertures/B20.md
  avec des annotations. Le rebuild remplace intégralement le fichier.

  Preuve : appels directs à atomic_write_text() aux lignes 280 et 286.
  _write_protected() n’est utilisé que pour Profil, Motifs et vues structurées.

  Correction minimale : appliquer le même mécanisme de zones générées à Dashboard et
  aux ouvertures, et protéger tout fichier existant sans marqueurs.

  # 4. Défauts importants — P1

  ## AUDIT-CHESS-005 — P1

  Fichiers et lignes : chess_index_service.py:274-306,
  chess_view_rebuild_service.py:48-55.

  Comportement : la génération est multi-fichiers mais non transactionnelle. Les
  contrôles de préservation arrivent après toutes les écritures.

  Scénario : cinq vues sont remplacées, puis un fichier avec marqueurs invalides
  déclenche une exception. La commande sort avec code 2, mais laisse un vault
  partiellement reconstruit.

  Preuve : aucune phase de préparation globale ni rollback ; le test d’erreur CLI,
  lignes 130–149, ne compare pas les fichiers avant/après.

  Correction minimale : valider toutes les destinations et tous les marqueurs avant la
  première écriture.

  ## AUDIT-CHESS-006 — P1

  Fichiers et lignes : chess_to_obsidian.py:220-250.

  Comportement : après une synchronisation limitée, les vues sont reconstruites
  uniquement depuis les parties fraîchement reçues.

  Scénario : limit=200 dans un vault de 1004 notes. Dashboard, ouvertures,
  statistiques et synthèses ne considèrent plus que 200 parties ; une synthèse durable
  peut être marquée inactive à tort.

  Preuve : write_chess_indexes(root, games) reçoit la liste réseau limitée,
  contrairement au rebuild qui relit tout le vault.

  Correction minimale : après synchronisation, reconstruire la liste complète depuis
  le vault, ou séparer clairement « vues partielles » et rebuild complet.

  ## AUDIT-CHESS-007 — P1

  Fichiers et lignes : chess_analysis_summary_service.py:167-185,
  chess_index_service.py:177-182.

  Comportement : la « perte moyenne globale par coup joué » est la moyenne simple des
  moyennes de chaque partie.

  Scénario : une partie de 10 coups à 100 cp et une partie de 100 coups à 10 cp
  affichent 55 cp au lieu d’environ 18 cp par coup.

  Preuve : sum(losses) / len(losses) ne possède pas le nombre de coups de chaque
  partie.

  Correction minimale : persister ou parser le nombre de coups joueur et calculer une
  moyenne pondérée, ou renommer précisément la mesure en moyenne des moyennes par
  partie.

  ## AUDIT-CHESS-008 — P1

  Fichiers et lignes : chess_analysis_service.py:253-282, chess_analysis.py:123-
  130,140-157.

  Comportement : turning_point_ply est le premier point de bascule de toute la partie,
  y compris un coup adverse, mais il est affiché sous « Ton bilan ».

  Scénario : l’adversaire commet la première gaffe décisive ; le bilan du joueur
  affiche ce coup adverse comme son moment de bascule.

  Preuve : next(... for move in analysed_moves ...) ne filtre pas la couleur joueur ;
  _turning_label() l’utilise sans filtre.

  Correction minimale : calculer séparément le premier tournant global et le premier
  tournant imputable au joueur.

  ## AUDIT-CHESS-009 — P1

  Fichiers et lignes : chess_insight_aggregation_service.py:115-162.

  Comportement : l’enveloppe et les insights peuvent contenir un game_id différent du
  frontmatter. L’agrégation l’ignore, rattache l’occurrence au ChessGame, puis
  déduplique globalement par insight_id.

  Scénario : un bloc copié dans une autre note conserve ses identifiants. Une
  occurrence légitime est supprimée comme doublon et les seuils deviennent faux.

  Preuve : aucune comparaison entre envelope.game_id, insight.game_id et game.game_id.

  Correction minimale : refuser ou diagnostiquer toute incohérence d’identité avant
  agrégation ; dédupliquer dans un contexte incluant la partie validée.

  ## AUDIT-CHESS-010 — P1

  Fichiers et lignes : chess_service.py:146-159.

  Comportement : les timestamps epoch sont convertis par datetime.fromtimestamp() dans
  le fuseau local, sans timezone. Une date absente utilise l’heure courante.

  Scénario : une partie proche de minuit change de date et de chemin selon la
  machine ; une donnée sans timestamp change de chemin entre deux synchronisations.

  Preuve : utilisation de fromtimestamp(end_ts) et utcnow(), alors que l’identité de
  chemin dépend de la date.

  Correction minimale : employer un datetime UTC conscient et rejeter ou isoler les
  parties sans timestamp stable.

  ## AUDIT-CHESS-011 — P1

  Fichiers et lignes : chess_analysis.py:236-242, chess_to_obsidian.py:92-97.

  Comportement : le bloc d’analyse n’applique pas les contrôles stricts utilisés pour
  ChessInsight.

  Scénario : marqueur unique, marqueurs dupliqués ou inversés. L’analyse peut être
  ajoutée à côté d’une zone invalide, ou la synchronisation extraire une portion
  ambiguë.

  Preuve : tests de simple appartenance puis split(..., 1) ; aucun comptage ni
  contrôle d’ordre.

  Correction minimale : partager un parseur de bornes strict validant exactement un
  début et une fin dans le bon ordre.

  ## AUDIT-CHESS-012 — P1

  Fichiers et lignes : chess.py:50-56, chess_index_service.py:59-85,89-124,
  chess_insight_view_service.py:244-284, chess_to_obsidian.py:175-198.

  Comportement : des valeurs externes sont injectées sans échappement dans titres
  Markdown, libellés de wikiliens et tableaux.

  Scénario : un adversaire contenant | ou ]], ou une ouverture contenant un retour
  Markdown, casse le lien ou injecte du contenu visuel trompeur.

  Preuve : le nom de fichier est nettoyé, mais le label utilise game.opponent brut.
  Les titres et métadonnées utilisent également les valeurs brutes.

  Correction minimale : centraliser un échappement Markdown/wikilink limité aux champs
  externes et valider strictement ECO.

  # 5. Défauts mineurs — P2

  ## AUDIT-CHESS-013 — P2

  Fichiers et lignes : chess.py:9-21, chess_insight.py:25-53,
  chess_analysis_service.py:16-63.

  Comportement : les modèles runtime protègent peu d’invariants : couleur et résultat
  libres dans ChessGame, ply <= 0, pertes négatives, incohérence move_number/ply,
  catégories de classification libres.

  Preuve : seuls catégorie/couleur/rôle des insights et version de schéma sont
  contrôlés.

  Correction minimale : valider les invariants réellement nécessaires aux chemins,
  identités et agrégations.

  ## AUDIT-CHESS-014 — P2

  Fichiers et lignes : chess_vault_reader_service.py:37-62,
  chess_insight_storage_service.py:79-105.

  Comportement : deux parseurs de frontmatter différents, sans YAML réel. Ils
  divergent sur espaces, fin de frontmatter et clés indentées.

  Risques réels : BOM et CRLF font échouer les notes ; les guillemets simples restent
  littéraux. Le format Hanuman actuel LF/doubles quotes fonctionne.

  Correction minimale : un parseur commun strict correspondant au sous-ensemble
  effectivement produit.

  ## AUDIT-CHESS-015 — P2

  Fichiers et lignes : chess_analysis_queue_service.py:50-75, chess_analysis.py:26-28.

  Comportement : l’état de file utilise write_text() non atomique ; lire le statut
  peut écrire interrupted. Importer l’orchestration exige immédiatement
  CHESS_COM_USERNAME.

  Scénario : arrêt pendant l’écriture de l’état → JSON tronqué ; simple import d’une
  route de ressources impossible sans variable d’environnement.

  Correction minimale : utiliser l’écriture atomique pour l’état et déplacer la
  validation de configuration dans les fonctions d’entrée.

  ## AUDIT-CHESS-016 — P2

  Fichiers et lignes : chess_index_service.py:261-316, chess_analysis.py:140-233,
  chess_to_obsidian.py:120-211.

  Comportement : responsabilités de coordination et rendu mêlées ; difficultés de test
  des interactions et scénarios d’échec intermédiaire.

  Correction minimale : extraire uniquement les phases validables — plan de
  destinations, validation préalable, puis écriture.

  ## AUDIT-CHESS-017 — P2

  Fichiers et lignes : chess_rebuild_views.py:47-56, chess_view_rebuild_service.py:58-
  74.

  Comportement : les notes ignorées apparaissent dans errors, mais la commande
  retourne 0. Le rapport ne distingue pas avertissement, erreur récupérable et erreur
  fatale.

  Scénario : 998 notes illisibles peuvent produire une commande « réussie ».

  Correction minimale : ajouter un statut global et des catégories de diagnostics,
  sans nécessairement rendre tout avertissement fatal.

  ## AUDIT-CHESS-018 — P2

  Fichiers et lignes : atomic_write_service.py:14-27, test
  test_atomic_write_service.py:6-16.

  Comportement : l’écriture remplace le mode du fichier par celui du temporaire et ne
  synchronise pas le répertoire parent après replace().

  Preuve : le test vérifie contenu final et nettoyage du temporaire, pas permissions,
  panne avant/après remplacement ni durabilité après crash.

  Correction minimale : préserver le mode existant et documenter ou renforcer la
  garantie de durabilité.

  # 6. Améliorations facultatives — P3

  ## AUDIT-CHESS-019 — P3

  Le rebuild relit chaque note au moins pour le frontmatter, le bilan et les insights,
  puis lit deux fois tous les octets pour la vérification :
  chess_vault_reader_service.py:72-132, chess_analysis_summary_service.py:192-194,
  chess_insight_aggregation_service.py:115-131, chess_view_rebuild_service.py:30-53.

  À 1004 notes, le coût reste raisonnable. À plusieurs dizaines de milliers, le
  snapshot intégral en mémoire et les relectures deviendront visibles. Une structure
  de note parsée une seule fois serait alors utile.

  ## AUDIT-CHESS-020 — P3

  Helpers dupliqués :

  - _yaml_quote() dans chess_to_obsidian.py:44-45 et chess_index_service.py:51-52;
  - _replace_generated() dans chess_index_service.py:236-247 et
    chess_insight_view_service.py:106-117.

  La duplication est petite, mais a déjà produit des politiques de protection
  différentes.

  ## AUDIT-CHESS-021 — P3

  Références vérifiées :

  - GameAnalysis.to_dict() n’a pas d’appel trouvé dans src.
  - write_chess_insight_views() n’est utilisé que directement par les tests.
  - _game_link() est un wrapper d’une ligne autour de chess_game_note_link().

  Ce sont des candidats à simplification, pas des défauts fonctionnels.

  # 7. Lacunes de tests prioritaires

  1. Synchronisation d’une note contenant des Notes personnelles hors blocs :
     comparaison octet/section avant-après.

  2. Deux parties ayant date, ECO et adversaire identiques mais game_id différents.
  3. _Index ou une destination finale représentée par un symlink vers l’extérieur.
  4. Erreur tardive de marqueurs : vérifier qu’aucune vue antérieure n’a été modifiée.
  5. Synchronisation limitée dans un vault plus grand : vues construites depuis toutes
     les notes.

  6. Dashboard et index d’ouverture humains sans marqueurs.
  7. Incohérence entre game_id du frontmatter, de l’enveloppe et de l’insight.
  8. Moment de bascule causé par l’adversaire dans une partie vue côté Noir.
  9. Échappement d’adversaires et ouvertures contenant |, ]], #, retours ligne ou
     backticks.

  10. Atomicité sous échec injecté avant/après replace(), permissions et nettoyage.

  La fixture CLI actuelle ne reproduit pas une vraie note historique : elle contient
  une phrase à la place du frontmatter complet, du PGN cité, de l’analyse visible et
  du bloc ChessInsight.

  # 8. Vérification ADR et documentation

   Exigence       Écritures sous Echecs
   Code concerné  résolution CLI et _chess_root()
   Test concerné  chemins racine/home/dépôt
   État           Partiel
   Justification  _Index symlink peut sortir de la racine.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Aucune suppression
   Code concerné  rebuild lignes 53–55
   Test concerné  inventaire avant/après
   État           Conforme au sens strict
   Justification  Aucun appel de suppression métier ; les remplacements restent
                  toutefois destructifs pour le contenu.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Notes de parties non modifiées par rebuild
   Code concerné  rebuild lignes 30–52
   Test concerné  test CLI par SHA-256
   État           Conforme
   Justification  Les notes chronologiques sont relues, pas écrites.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Synchronisation non destructive
   Code concerné  sync lignes 232–247
   Test concerné  analyse/insights seulement
   État           Non conforme
   Justification  Le contenu humain hors deux blocs est perdu.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Fichiers humains protégés
   Code concerné  _write_protected()
   Test concerné  Profil et synthèses
   État           Partiel
   Justification  Dashboard et ouvertures ne sont pas protégés.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Hors ligne
   Code concerné  imports du rebuild
   Test concerné  mocks ChessService/Stockfish
   État           Conforme
   Justification  Aucun appel réseau ou moteur dans ce flux.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Idempotence
   Code concerné  tous les rendus
   Test concerné  tests double exécution
   État           Partiel
   Justification  Vraie idempotence sur fixtures stables, mais pas atomicité multi-
                  fichiers ni protection universelle.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Seuils 3–4–5 sur parties uniques
   Code concerné  agrégation lignes 174–189
   Test concerné  tests 0/2/3/4/5/8
   État           Conforme
   Justification  Calcul correct après déduplication ; identité persistée
                  insuffisamment validée.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Synthèses inactives
   Code concerné  view service lignes 365–390
   Test concerné  test de régression
   État           Conforme
   Justification  Une synthèse Hanuman existante est conservée et marquée inactive.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Aucun lien vers note inexistante
   Code concerné  view service lignes 370–424
   Test concerné  fichier humain non lié
   État           Conforme sur les synthèses
   Justification  Les liens de partie peuvent néanmoins être cassés par caractères
                  spéciaux.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Écritures atomiques des vues
   Code concerné  tous les appels d’index
   Test concerné  test atomic_write minimal
   État           Partiel
   Justification  Chaque fichier est remplacé atomiquement, mais la reconstruction
                  globale ne l’est pas.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Génération déterministe
   Code concerné  tri jeux/occurrences
   Test concerné  tests d’ordre inversé
   État           Partiel
   Justification  Stable pour entrées valides ; timestamps locaux et collisions
                  rendent la synchronisation instable.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Procédure de restauration
   Code concerné  runbook lignes 95–109
   Test concerné  aucun test
   État           Non vérifiable
   Justification  Procédure humaine raisonnable, non automatisée.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       Structure ADR année/année-mois
   Code concerné  ADR lignes 24–27
   Test concerné  code YYYY/MM
   État           Non conforme documentaire
   Justification  Le code utilise YYYY/MM, pas YYYY/YYYY-MM.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       « aucun chemin absolu personnel dispersé »
   Code concerné  chess_to_obsidian.py:25, chess_analysis.py:40
   Test concerné  aucun
   État           Non conforme
   Justification  Deux chemins personnels sont codés en dur comme fallback.
  ────────────────────────────────────────────────────────────────────────────────────
   Exigence       « ne modifie jamais les fichiers humains sans marqueurs »
   Code concerné  documentation lignes 89–94
   Test concerné  partiel
   État           Non conforme
   Justification  Dashboard et ouvertures sont écrasés directement.

  # 9. Points nécessitant une validation visuelle

  Après correction des P0/P1, inspecter dans Obsidian :

  - rendu des wikiliens avec accents et adversaires spéciaux ;
  - absence de liens fantômes après protection d’un fichier humain ;
  - Dashboard vide, partiellement analysé et avec 1004 parties ;
  - lisibilité de la ligne contenant toutes les ouvertures du Dashboard ;
  - longueur et navigation des pages de synthèse contenant toutes les occurrences ;
  - callouts Stockfish et Chess avec le thème/CSS réellement installé ;
  - sections actives, confirmées, émergentes et inactives ;
  - affichage des 998 notes sans bloc ChessInsight ;
  - cohérence des liens retour Dashboard/accueil thématique ;
  - rendu des Notes personnelles autour des marqueurs ;
  - vocabulaire et pluriels français ;
  - éventuel ralentissement d’Obsidian sur les pages très longues.

  # 10. Proposition de suite

  Conclusion C : au moins un P0.

  Bloquer toute preview considérée comme sûre et toute migration réelle. Préparer un
  lot correctif prioritaire limité à :

  1. identité et collisions des notes ;
  2. préservation des notes synchronisées ;
  3. confinement des destinations résolues et symlinks ;
  4. protection de Dashboard et des ouvertures ;
  5. validation globale avant la première écriture ;
  6. reconstruction des vues depuis l’intégralité du vault après synchronisation.

  Les autres P1 peuvent être intégrés au même lot uniquement s’ils ne diluent pas ces
  six corrections de sécurité.

  # 11. État Git final

  $ git status --short

  Sortie vide, identique à l’état initial. git diff --stat et git diff -- src/hanuman
  tests docs sont également vides.

  Aucun fichier n’a été modifié pendant l’audit.

  Aucun commit n’a été créé.

  Aucune migration ou réanalyse de partie n’a été exécutée.

