# Audit général de Hanuman — état actuel de `main`

Date d'observation : 27 juillet 2026 (Europe/Paris)

## 1. Résumé exécutif

**FAIT OBSERVÉ.** Hanuman est aujourd'hui un système personnel local-first réellement
substantiel : 254 fichiers suivis ou visibles via `rg --files`, 167 fichiers Python
contrôlés par mypy, un frontend React/Vite de huit espaces fonctionnels, 364 tests
collectés et un domaine Chess désormais fusionné dans `main`. Le commit inspecté est
`baf0db209e8118a47405254dea6a749eef6ec156`, merge de
`feature/chess-stockfish-v2`.

**FAIT OBSERVÉ.** Le working tree n'était pas propre avant l'audit : 13 fichiers suivis
étaient déjà modifiés, tous liés à Chess (détail section 3). Ces changements n'ont pas
été créés ni modifiés par l'audit. Les constats portent donc sur le dépôt effectivement
présent ; les éléments Chess modifiés localement ne sont pas automatiquement attribués
au commit HEAD.

**COMPORTEMENT VÉRIFIÉ.** Ruff, Black, mypy, le build frontend et
`git diff --check` réussissent. La collecte trouve 364 tests. La suite complète se
bloque dès le premier appel `TestClient`; un test isolé dépasse 20 secondes. Un
sous-ensemble excluant tous les fichiers `TestClient` et le test d'endpoint indirect
passe : 326 tests, 33,93 s, deux avertissements Pydantic. Il donne 88 % sur un rapport
qui inclut les tests, mais seulement 80,66 % sur `src/hanuman`. Il est donc factuellement
incorrect de publier « 89 % de couverture source » à partir de cette exécution.

**FAIT OBSERVÉ CRITIQUE.** Le Makefile lance `hanuman.main:app`, qui ne contient que les
cinq routes de `api/routers/orchestrations.py`. L'application complète de 48 opérations
se trouve dans `hanuman.api.core.main:app`. Le frontend appelle Calendar, Gmail,
Resources, Chess, santé et connecteurs qui ne sont pas exposés par le point d'entrée du
Makefile. Ce n'est plus seulement une dette esthétique de « deux applications » :
c'est une rupture opérationnelle entre lancement officiel et interface
(`Makefile:12,119-123`; `src/hanuman/main.py:7-25`;
`src/hanuman/api/core/main.py:30-62`; `frontend/src/App.tsx:35-45,160-171`).

**COMPORTEMENT VÉRIFIÉ.** L'interface n'est pas une coquille Vite. Elle compile 1 605
modules en un bundle de 317,45 kB (96,27 kB gzip) et propose constellation, catalogue
d'orchestrations, Gmail, Calendar, Obsidian/Notion, Wikipédia/Notion, Chess/Obsidian,
Resources et santé. Son identité visuelle est cohérente et différenciée. Toutefois,
plusieurs labels (« moteur connecté », « opérationnelle », « importer ») dépassent les
capacités réellement démontrées.

**FAIT OBSERVÉ.** Obsidian → Notion fonctionne au niveau code, API, CLI et tests :
lecture Markdown, conversion, création d'une page Notion et retour d'URL. Le dashboard
explore le vault, parcourt les pages enfants Notion, rapproche par `notion_page_id`,
calcule les conflits et les statistiques. Aucun chemin Notion → Obsidian n'est
implémenté. La flèche ↔ décrit une vue comparative, pas une synchronisation
bidirectionnelle.

**FAIT OBSERVÉ.** Chess est le module métier le plus industrialisé : acquisition
Chess.com, notes Obsidian, identité déterministe, protections de chemins, zones
générées, analyse Stockfish locale, persistance V1/V2, queue observable, agrégations,
pages ECO, vues, widgets et reconstruction hors ligne. Il est naturellement conforme
à « relier sans remplacer », mais reste très personnalisé et envahit Resources au lieu
d'avoir un espace opératoire unifié.

## 2. Méthode et limites

L'audit a commencé par Git puis par le code et les configurations. Les anciens audits
n'ont été recherchés qu'après la carte du système et les mesures. Chaque documentation
a été traitée comme une affirmation.

Commandes principales : `git status`, branche, log, remotes et HEAD ; inventaires
`rg --files`/`find` ; lectures numérotées ; recherche des imports/routes/appels ;
`pytest --collect-only`; suite complète et test isolé sous délai ; sous-suite
déterministe ; Coverage JSON ; Ruff, Black, mypy, build Vite et `git diff --check`.

Limites :

- aucune API distante n'a été appelée volontairement et aucune donnée distante écrite ;
- l'environnement d'exécution isole les sessions terminal : Uvicorn a annoncé son
  démarrage sur `127.0.0.1:8765`, mais une seconde session n'a pas pu le joindre ;
- la navigation visuelle dans un navigateur n'a donc pas été réalisée ; le frontend a
  été vérifié par code, build et carte de ses appels ;
- la suite complète et sa couverture sont indisponibles à cause du blocage
  `TestClient`; aucune extrapolation n'est présentée comme mesure ;
- les secrets ont été inventoriés par chemin, permissions et taille, sans contenu.

## 3. Commit et état inspectés

- Branche : `main`.
- HEAD : `baf0db209e8118a47405254dea6a749eef6ec156`.
- Décoration : `baf0db2 (HEAD -> main, origin/main, origin/HEAD)`.
- Message : `Merge branch 'feature/chess-stockfish-v2'`.
- Remote : `origin git@github.com:Prakash9862/hanuman.git` en fetch/push.
- Les 15 derniers commits confirment les merges Stockfish V2 puis Chess Obsidian V1.

État local initial préexistant :

`src/hanuman/config/env.py`, `models/chess_insight.py`,
`orchestrations/chess_analysis.py`, `chess_upgrade_analyses.py`, six services Chess,
et trois tests Chess étaient modifiés. **INFORMATION HISTORIQUE DÉSORMAIS PÉRIMÉE :**
les rapports affirmant que Chess est sur une branche non fusionnée sont faux pour HEAD.

## 4. Carte réelle du système

| Zone | Responsabilité et entrée réelle | Appelée | Maturité/effets |
|---|---|---|---|
| `frontend/` | SPA React 19, Vite 6, Router 7 ; `src/main.tsx` → `App.tsx` | `make run` via npm | UI bêta ; lectures et déclenchements d'écritures |
| `src/hanuman/main.py` | fabrique FastAPI minimale | Makefile, Docker prod, tests | active mais incomplète ; cinq routes |
| `src/hanuman/api/core/main.py` | assemble 15 routeurs | import direct et documentation partielle | application complète mais non lancée officiellement |
| `api/core/` | routes unitaires historiques par connecteur | seulement via app complète | hétérogène, majoritairement ping/lecture |
| `api/routers/` | orchestration, dashboard, Gmail, Resources, Chess | app complète ; certaines routes dans app minimale | actif, capacités importantes |
| `services/core/` | clients Notion, GitHub, Calendar, Wikipedia, Chess, Obsidian | routes et orchestrations | alpha à bêta |
| `services/adapters/` | packages Notion/GitHub | clients réels très minces | architecture réservée/dupliquée |
| `orchestrations/` | flux inter-outils et CLI | API, scripts, dashboard | très hétérogène |
| `services/chess_*` | persistance, sécurité, vues, queue, Stockfish | flux Chess/API/tests | domaine le plus robuste |
| `tui/` | Textual, écran d'orchestrations | `python -m hanuman.tui` | prototype ; `_init_.py` est mal nommé |
| `scripts/` | CLI générique, dev Docker, thème Chess/widget | manuel/Docker | utilitaire, plusieurs chemins historiques |
| `config/` | JSON vide suivi ; credentials locaux non suivis | certains services lisent des chemins propres | configuration fragmentée |
| `data/` | seulement `.gitkeep` | non | base de données absente |
| `logs/` | journaux JSON rotatifs, run logs | middleware/service | actif mais volumineux et sensible |
| `docs/` | ADR, guides, specs, audits, stratégie | humain | riche mais sans hiérarchie temporelle fiable |

Le README compte plus de 8 500 lignes et duplique manuel, architecture, roadmap et
audit. Les packages `tests/integration`, `tests/security`, `tests/unit`, `tests/data`
sont presque vides : ce sont des réservations, pas des suites. `config/hanuman_config.json`
est vide. `arbo.txt`, `orchestration_report.txt` et `test.mk` sont des traces
historiques à qualifier, non des entrées actives.

## 5. Carte du frontend

| Route frontend | Composants | Endpoints | Capacité réelle |
|---|---|---|---|
| `/` (`/constellation`) | `HanumanOSPage`, inspecteur, zoom, liens | aucun dans la page ; sidebar appelle 9 pings | constellation visuelle statique ; navigation |
| `/orchestrations` | cartes de catalogue | aucun | catalogue statique avec statuts codés en dur |
| `/orchestrations/gmail` | liste, recherche, détail, OAuth | `/gmail/status`, auth, messages, important, détail | lecture distante ; OAuth écrit le token local |
| `/orchestrations/calendar` | calendriers/événements, liens Maps | `/calendar/calendars`, `/calendar/events` | lecture distante ; Maps ouvre des URL |
| `/orchestrations/obsidian-notion` | inventaire, filtres, stats, détail | items, stats, POST Obsidian→Notion | comparaison réelle et création Notion ; aucun import |
| `/orchestrations/wikipedia-notion` | formulaire et résultat | POST Wikipedia→Notion | lecture Wikipédia + écriture Notion |
| `/orchestrations/chess-obsidian` | limite, sync, rapport | POST `/chess/sync` | acquisition distante + écritures locales Obsidian |
| `/resources` | onglets Gallica/YouTube/IMSLP/Maps/Chess | routes `/resources/*` | recherche distante, liens, queue Stockfish et rebuild |
| `/health` | checks, graphes, logs et suivi | 9 pings | checks réels ; historique/logs/follow-up en `localStorage` |

Le frontend possède des états loading/error/success explicites dans toutes les pages
actives. Il n'a aucune bibliothèque de gestion d'état : état React local et
`localStorage` pour la santé. Les appels mélangent URL absolues
`http://127.0.0.1:8000` et proxy `/api`, ce qui limite la configurabilité
(`vite.config.ts:6-14`).

**INFÉRENCE.** L'identité visuelle sombre, constellation, orbites, panneaux de
diagnostic et ambiances par domaine donne une vraie sensation de système, pas seulement
un tableau CRUD. Elle aide à comprendre que Hanuman relie des outils. Sa faiblesse
produit est sémantique : le visuel confère une autorité opérationnelle à des états
codés en dur. `SidebarHealth` considère toute réponse HTTP sans `ok:false` comme saine,
et le pied affiche toujours « Moteur connecté » (`App.tsx:103-157`).

## 6. Carte backend/API

L'application complète assemble les routes suivantes :

- diagnostic/lecture distante : status, pings Obsidian/Notion/OpenAI/GitHub/Wikipedia/
  Calendar/Chess, connecteurs, logs ;
- lecture locale : inventaire vault, statistiques, programmes locaux, queue Chess ;
- lecture distante : Calendar, Gmail, Resources, dashboard Notion ;
- écriture locale : OAuth tokens, Chess→Obsidian, queue/analyses/vues Chess ;
- écriture distante : Obsidian→Notion, Wikipedia→Notion, routes Obsidian legacy ;
- lancement : dashboard subprocess, queue thread, refresh Chess ;
- navigation OAuth : Calendar/Gmail.

Les erreurs sont incohérentes de façon parfois problématique : Obsidian→Notion lève
400/502, Wikipédia→Notion renvoie HTTP 200 avec `ok:false`, Gallica renvoie un fallback
200, et Chess queue exprime un conflit par `ok:false` sans 409. Le fallback Gallica est
volontaire et adapté au domaine ; les erreurs d'écriture en HTTP 200 ne le sont pas.

La validation Pydantic/Query borne plusieurs paramètres (limites Gmail, YouTube,
Stockfish). Les clients externes ont généralement des timeouts de 5 à 30 secondes.
Notion gère la pagination ; Calendar/Gmail/YouTube bornent les listes ; le dashboard
Notion parcourt les enfants avec curseur. Aucune authentification API Hanuman n'existe.

La sécurité des chemins est excellente dans Chess, mais
`_resolve_obsidian_markdown_path()` accepte explicitement un chemin absolu hors vault
et vérifie seulement qu'il s'agit d'un `.md` existant
(`api/routers/orchestrations.py:32-51`). C'est une différence réellement dangereuse,
pas une variation métier.

## 7. Connecteurs

| Connecteur | Réel | Auth/stockage | Frontend/orchestration | Maturité |
|---|---|---|---|---|
| Obsidian | scan/read/write Markdown | chemin env ; filesystem | dashboard, publication, Chess | bêta |
| Notion | ping, request CRUD, search/query/pagination | token `.env` | plusieurs flux d'écriture | bêta |
| Gmail | OAuth readonly, recherche/liste/détail | `.secrets/gmail-token.json` mode 600 | page dédiée | alpha/bêta |
| Calendar | OAuth readonly, calendriers/événements | `secrets/google_calendar_token.json` mode observé 664 | page dédiée | alpha |
| Google Maps | construit URL search/directions | aucune clé | Calendar/Resources | stable mais ce n'est pas une API |
| GitHub | user, repo, issues ; sync Notion | token env | carte sans page dédiée | alpha |
| OpenAI | ping et QA Wikipedia | clé env | pas d'UI QA | expérimental |
| Wikipédia | recherche/page structurée | aucune | publication Notion | bêta |
| Chess.com | parties publiques récentes | username env/personnalisation | sync Chess | bêta |
| Stockfish | moteur local subprocess/python-chess | binaire local | queue Resources | bêta ; jamais API distante |
| YouTube | recherche/pagination | clé env | Resources | alpha |
| Gallica | SRU + fallback navigateur | aucune | Resources | alpha |
| IMSLP | MediaWiki search + URL | aucune | Resources | alpha |

Le registre contient 11 connecteurs : Gmail, Calendar, GitHub, Notion, Obsidian,
OpenAI, Wikipédia, Chess.com, YouTube, Gallica et IMSLP
(`connectors_registry.py:9-152`). Il omet Stockfish, Maps et programmes locaux. Omettre
Stockfish du registre distant est correct ; l'absence d'une catégorie « capacité
locale » rend toutefois le catalogue incomplet. Le registre sur-déclare parfois :
OpenAI expose quatre capacités alors que le service générique ne fournit qu'un ping ;
GitHub annonce activité, mais le service inspecté couvre surtout utilisateur, dépôts et
issues.

## 8. Orchestrations

### Obsidian ↔ Notion

Exploration : réelle, récursive, exclusions `.git/.obsidian/.trash/node_modules`,
frontmatter et liens `obsidian://` (`obsidian_notion_dashboard.py:57-108`).

Comparaison : réelle mais fondée sur le `notion_page_id` stocké dans la note et
`last_sync_at`; elle détecte obsidian-only, notion-only, newer, conflict et synced
(`:158-236`). Statistiques : réelles, calculées sur ces items.

Publication Obsidian → Notion : réelle et testée ; création de page, conversion des
blocs, fallback parent page/database. **FAIT OBSERVÉ.** La variante « safe » construit
une preview interne mais l'endpoint l'applique immédiatement. L'identité n'est pas
réécrite dans la note après création : une republication peut créer un doublon.

Import Notion → Obsidian : absent. Aucun endpoint, bouton ou writer correspondant.
L'UI affiche néanmoins « À importer » pour `notion_only`. Prévisualisation et validation
humaine : absentes du parcours API/UI. Vérification après écriture : limitée au succès
de l'API Notion, sans relecture. Échecs partiels : pas d'état persistant de run.

### Chess

Entrée : utilisateur Chess configuré et limite. Source brute : Chess.com. Effets :
création/mise à jour de notes sous racine Chess sûre, PGN et frontmatter, graphes et
index. L'identité `game_id`, la collision déterministe et la protection de contenu
humain sont fortement testées.

Stockfish fonctionne localement. La queue utilise un thread daemon, verrou, signal
d'arrêt après position et état atomique `.hanuman-stockfish-state.json` avec
`idle/running/interrupted/stopping/stopped/done/failed`, progression et dix dernières
erreurs (`chess_analysis_queue_service.py:26-227`). V1/V2 sont persistées dans des
zones délimitées des notes ; le refresh relit le vault sans Chess.com ni Stockfish.
Les vues comprennent dashboard, profil, index thématiques, pages ECO et widgets.
La migration historique dispose d'une CLI et d'un runbook avec copie preview.

Limites : personnalisation forte, dépendances système Stockfish/`pdftotext`/Obsidian/
Scid, état thread non partageable entre processus, pas de reprise automatique au
fichier courant, erreurs bornées aux dix dernières, opérateur réparti entre page Chess
sync et onglet Chess de Resources.

### Resources

La « bibliothèque » est une recherche multi-source présentée dans une même UI, mais pas
une recherche fédérée en un appel : l'utilisateur choisit une source. Les schémas sont
normalisés assez pour l'affichage (titre, description, URL, métadonnées). Il n'existe
ni catalogue persistant, ni preview riche commune, ni destination Notion/Obsidian.
Maps retourne des liens universels. La spécification `cultural-library-v1.md` est donc
en avance sur le produit.

### Gmail et Calendar

Deux connecteurs de lecture existent avec OAuth, renouvellement et interfaces
fonctionnelles. Aucune orchestration Gmail→Calendar, Calendar→Notion ou rédaction/
envoi/création d'événement n'est implémentée. Gmail utilise le scope readonly.
Calendar utilise `calendar.readonly`. Les capacités d'écriture sont limitées au stockage
local des jetons OAuth.

### Autres flux

Wikipédia→Notion est un flux réel et visible. Un context pack plus riche existe en CLI
mais pas en UI. GitHub→Notion sait créer ou mettre à jour une issue avec recherche
d'identité et journal de run, mais n'a pas de page frontend dédiée. Chess insights→Notion
existe en code/tests, sans UI principale. Wikipedia QA OpenAI est expérimental et non
exposé.

## 9. Persistance et sources de vérité

| Donnée | Emplacement/format | Source de vérité et durée | Sécurité/reprise |
|---|---|---|---|
| secrets généraux | `.env`, env | services externes ; long terme | non affichés |
| Gmail token | `.secrets/gmail-token.json` | Google ; renouvelable | mode 600, écriture non atomique |
| Calendar token | `secrets/google_calendar_token.json` | Google | mode observé 664, écriture non atomique |
| logs applicatifs | `logs/*.json` rotatifs | Hanuman | jusqu'à 7 MB actif ; modes 664 |
| run logs | fichier du service run-log | Hanuman | append JSONL, reprise limitée |
| notes/analyses Chess | vault externe Markdown/JSON embarqué | Chess.com brut, Hanuman dérivé | écritures atomiques et zones possédées |
| queue Chess | vault Chess `.hanuman-stockfish-state.json` | Hanuman éphémère/persistant | atomique ; running→interrupted |
| identité O/N | frontmatter Obsidian | note locale | seulement lue dans le dashboard |
| santé frontend | `localStorage` | navigateur | locale, non partagée, effaçable |
| build frontend | `frontend/dist` | dérivé | reconstructible |

Il n'existe pas de base de données centrale. **INFÉRENCE.** Hanuman respecte globalement
« relier sans remplacer » : il garde surtout jetons, provenance et dérivés. Chess
duplique nécessairement PGN et analyses dans Obsidian pour rendre la connaissance
locale ; c'est une copie produit assumée, pas encore un hub de données général.

## 10. Tests et qualité mesurés aujourd'hui

- Collecte : 364 tests en 0,33 s.
- Suite complète : bloquée au premier test Calendar ; interrompue après plus de 90 s.
- Test isolé : timeout 20 s sur
  `test_calendar_auth_redirect`, au `client.get("/calendar/auth")`.
- Sous-suite sans appels TestClient : 326 passés en 33,93 s, deux warnings.
- Rapport brut de cette sous-suite : 9 000 statements, 1 106 manqués, 88 %.
- Répartition JSON : source 5 605 statements, 1 084 manqués, **80,66 %** ; tests
  3 395 statements, 22 manqués, **99,35 %**.
- Seuil Makefile : 90 % (`Makefile:14,70-75`).
- Faibles sources du sous-périmètre : Resources 29 %, safe O→N 24 %, routes O/N 38 %,
  Notion route 38 %, Gmail route 40 %, dashboard O/N 43 %, queue Chess 55 %,
  analyse Stockfish 51 %.
- Ruff : réussi.
- Black : 169 fichiers inchangés.
- mypy strict : 167 fichiers, aucun problème.
- frontend build : réussi, 1 605 modules.
- aucun test frontend n'est défini dans `package.json`.
- `git diff --check` : réussi.

**INFORMATION HISTORIQUE DÉSORMAIS PÉRIMÉE.** Les chiffres 70 %, 146/160 tests ou Chess
non fusionné ne décrivent plus le dépôt. **LIMITATION.** Le résultat récent « 89 % et
seul fail-under=90 » n'a pas été reproduit : la suite bloque ici et le seul 88/89
proche inclut les tests. Le précédent blocage `TestClient` n'est pas résolu.

## 11. Sécurité

Modèle réel : mono-utilisateur, écoute par défaut `127.0.0.1` dans le Makefile. À ce
niveau, l'absence d'auth n'est pas critique. Docker publie cependant `8000:8000` et
l'entrypoint écoute `0.0.0.0`; toute exposition LAN change la gravité.

Risques principaux :

1. P0 conditionnel à l'exposition : application complète sans auth, CORS `*` avec
   credentials, routes d'écriture distante/locales et subprocess.
2. P1 local : chemin absolu Markdown hors vault accepté par publication Notion.
3. P1 confidentialité : logs JSON volumineux en mode 664 susceptibles de contenir
   chemins, sujets d'emails, erreurs API et adresse personnelle.
4. P1 : token Calendar et credentials observés mode 664 contre Gmail 600.
5. P1 : dashboard subprocess valide une liste de noms, mais les processus n'ont ni
   run_id fiable ni capture structurée de PID/résultat.
6. P2 : `token_manager` construit le nom de fichier depuis `service` sans validation ;
   usages actuels constants, risque futur si entrée utilisateur.
7. P2 : données Wikipédia, Gmail, Calendar, issues ou notes peuvent alimenter OpenAI/
   génération ; aucun traitement explicite de prompt injection ou politique de
   minimisation n'est visible.

Points forts : timeouts généralisés, tokens Gmail mode 600, chemins Chess défensifs,
écritures Chess atomiques, limites Query, refus des symlinks et préservation des zones
humaines.

## 12. Documentation correcte ou périmée

Normatif : ADR-0001 à 0006, particulièrement sources de vérité, Chess et
plan/preview/apply/verify. Guides actuels : `GMAIL_SETUP.md`, `CHESS_*`,
`CHESS_OBSIDIAN_VIEWS.md`, runbook migration. Specs : intention, pas vérité.

Historique : `Audit_codex.md`, `CODEX_NIGHT_REPORT.md`, `docs/reviews/*`,
`docs/strategy/*` doivent être datés/étiquetés comme rapports. Plusieurs contiennent
des faits désormais faux : branche Chess longue non fusionnée, 146/160 tests, 70 %,
frontend sous-estimé.

Le README annonce 92 % (`README.md:14`) et décrit à la fois deux points d'entrée puis
affirme que `hanuman.main` est complet (`README.md:2784-2800,6621-6641`) : contradiction
interne. Sa taille empêche son rôle de vérité opérationnelle.

Hiérarchie proposée :

1. `README` court + `docs/current/` pour vérité actuelle ;
2. `docs/adr/` pour décisions ;
3. `docs/guides/` et `docs/runbooks/` pour utilisateurs/opérations ;
4. `docs/specs/` pour fonctionnalités non garanties ;
5. `docs/history/` pour audits/reviews ;
6. `docs/roadmap/` pour propositions datées.

## 13. Forces

1. Frontend réellement différencié, cohérent et connecté à des APIs.
2. Chess robuste, idempotent, sûr sur les chemins et utile dans Obsidian.
3. Publication Obsidian→Notion et Wikipédia→Notion concrètes.
4. Connecteurs de lecture Gmail/Calendar et Resources déjà exploitables.
5. Excellente discipline statique : Ruff, Black, mypy et build verts.
6. Architecture local-first sans base centrale inutile.
7. Tests métier Chess et Notion profonds, pas seulement tests de présence.

## 14. Faiblesses

1. Le point d'entrée officiel ne sert pas l'essentiel du frontend.
2. Tests HTTP toujours bloqués ; couverture globale invérifiable.
3. Observabilité hétérogène hors queue Chess.
4. Promesses UI supérieures aux capacités (↔, import, moteur connecté).
5. Secrets/logs et frontière vault inégalement sécurisés.
6. Configuration éclatée entre deux modules, env directs et fichiers.
7. Documentation massive, contradictoire et non temporalisée.

## 15. Problèmes classés

- **P0 :** aligner factuellement le point d'entrée utilisé et l'API attendue par le
  frontend ; bénéfice : application réellement utilisable après `make run`.
- **P0 qualité :** isoler/résoudre le blocage TestClient en CI propre ; bénéfice :
  signal de régression et couverture honnête.
- **P1 sécurité :** interdire les chemins absolus hors vault pour O→N ; faible coût,
  fort gain.
- **P1 produit :** corriger les libellés d'import/bidirectionnel et statuts dynamiques.
- **P1 opérations :** étendre le modèle d'état Chess à deux flux d'écriture.
- **P2 :** consolider secrets/config et permissions.
- **P2 :** séparer Resources culturel de l'opérateur Chess.
- **P3 :** nettoyer adapters/TUI/fichiers historiques après preuve d'inusage.

## 16. Avantages distinctifs

Le meilleur avantage n'est pas le nombre de connecteurs : c'est la transformation de
données appartenant à des outils externes en connaissance personnelle locale,
inspectable et préservant les sources. Chess.com→Stockfish→Obsidian en est aujourd'hui
la démonstration la plus convaincante. Wikipédia→Notion est la démonstration courte la
plus accessible à une personne extérieure, tandis que la constellation explique
visuellement la philosophie.

## 17. Maturité par module

| Module | Statut | Justification |
|---|---|---|
| frontend global | bêta | riche et buildable, mais entrée backend cassée |
| constellation | alpha | identité forte, données/statuts statiques |
| santé système | alpha | checks réels, historique local simulé |
| Obsidian ↔ Notion | alpha | comparaison/publication réelles, pas de retour ni identité écrite |
| Gmail | alpha | readonly utile, OAuth, erreurs ; données sensibles |
| Calendar | alpha | readonly utile, OAuth, interface |
| GitHub | alpha | service/sync testés, faible UX |
| Resources | expérimental | recherches réelles, pas de bibliothèque/destination |
| Chess.com | bêta | acquisition, identité, notes et tests solides |
| Stockfish | bêta | V2 persistée, queue/refresh, dépendances locales |
| Wikipédia/OpenAI | Wikipédia bêta / OpenAI expérimental | flux Notion solide ; QA non exposée |
| dashboard historique HTML | prototype | subprocess et HTML legacy |
| TUI | prototype | peu couvert, entrée `_init_.py` suspecte |

## 18. Propositions priorisées

1. **P0, faible : rendre le lancement cohérent.** Bénéfice : toutes les pages fonctionnent
   avec la commande documentée. Dépendance : décider l'app canonique. Risque : révéler
   des tests/routes jusque-là masqués. Rendu : Health, Gmail, Calendar, Resources et
   Chess joignables.
2. **P0, moyen : rétablir la suite HTTP et un rapport `--source=src/hanuman`.** Bénéfice :
   qualité mesurable. Dépendances : matrice FastAPI/Starlette/httpx/anyio et CI.
   Risque faible. Rendu : 364 tests terminaux et seuil non ambigu.
3. **P1, faible : vérité des statuts frontend.** Bénéfice : confiance. Dépendance :
   endpoints santé/capacités. Rendu : badges dérivés du backend, import marqué absent.
4. **P1, moyen : identité post-publication O→N.** Bénéfice : évite doublons et rend le
   dashboard fiable. Dépendance : politique d'écriture frontmatter/validation humaine.
   Risque : modification de notes. Rendu : publish/update explicite et vérifié.
5. **P1, moyen : run observable sur O→N et Wikipédia→Notion.** Bénéfice : savoir demandé/
   commencé/terminé/modifié. Dépendance : petit contrat de run. Rendu : historique,
   résultat et retry ciblé.
6. **P2, faible : permissions tokens/logs.** Bénéfice confidentialité ; risque faible.
7. **P2, moyen : page opérateur Chess unique.** Bénéfice UX ; réunit sync, queue,
   progression, refresh et diagnostics.
8. **P2, moyen : Resources “collecter”.** Bénéfice concret ; preview d'une ressource
   vers Notion ou Obsidian, sans bâtir une base centrale.

## 19. Idées nouvelles

- « Briefing du jour » en lecture seule combinant Calendar, Gmail important et GitHub,
  avec provenance et aucun LLM par défaut (P2, moyen).
- « Reçu d'orchestration » Markdown local : entrée, hash, destination, objets créés,
  vérification (P1, moyen).
- Depuis une ressource culturelle, générer une note Obsidian sourcée et ouvrable dans
  l'outil d'origine (P2, moyen).
- Démonstration guidée avec données mock : constellation → Wikipédia → preview Notion
  → reçu, sans secrets (P2, moyen).

## 20. Ce qu'il faut explicitement éviter

- annoncer une synchronisation bidirectionnelle avant un writer Notion→Obsidian ;
- ajouter Drive ou d'autres connecteurs avant de rendre deux runs observables ;
- centraliser les contenus externes dans une base Hanuman ;
- exposer l'API au LAN avant auth/origines/path boundary ;
- faire dépendre le cœur du produit d'OpenAI ou d'agents ;
- réécrire tout le backend pour uniformiser des différences de domaine légitimes ;
- supprimer les interfaces historiques avant vérification d'usage ;
- viser artificiellement 90 % en couvrant des tests ou des getters sans risque.

## 21. Roadmap recommandée

**1 mois.** Point d'entrée canonique, suite HTTP, couverture source, frontière vault,
permissions, statuts UI honnêtes, opérateur Chess regroupé.

**3 mois.** Identité O→N persistée, plan/preview/apply/verify sur O→N, reçus de run,
vérification Notion, première collecte Resources→Obsidian.

**6 mois.** Deuxième orchestration de référence observable (Wikipédia→Notion ou
GitHub→Notion), briefing read-only inter-outils, déclenchements bornés, documentation
réorganisée. Notion→Obsidian seulement après décision explicite de source de vérité.

## 22. Dix décisions proposées au propriétaire

1. Déclarer l'application complète comme cible fonctionnelle canonique.
2. Considérer tout audit antérieur comme historique daté.
3. Mesurer la couverture exclusivement sur `src/hanuman`.
4. Nommer l'espace « Obsidian / Notion » tant que le retour est absent.
5. Faire d'Obsidian la source du Markdown publié, Notion la destination.
6. Autoriser la réécriture d'identité frontmatter seulement après preview.
7. Faire de Chess un domaine officiel et un laboratoire d'orchestration locale.
8. Garder Stockfish comme capacité locale, pas connecteur API.
9. Faire de Resources un collecteur vers les outils existants, pas un catalogue central.
10. Refuser toute exposition réseau avant durcissement explicite.

## 23. Questions nécessitant réellement arbitrage

1. Une publication O→N doit-elle mettre à jour une page liée ou toujours créer ?
2. Hanuman peut-il écrire `notion_page_id` et un hash dans les notes après accord ?
3. Notion→Obsidian est-il réellement souhaité, et pour quels types de contenu ?
4. Chess doit-il apparaître comme orchestration ou comme domaine de premier niveau ?
5. L'usage cible restera-t-il strictement sur le poste local ?
6. Les logs doivent-ils conserver sujets Gmail/chemins complets ou les expurger ?

## 24. Verdict final honnête

Hanuman n'est plus un prototype global ni une simple API : c'est une **alpha produit
avancée**, avec deux poches de maturité bêta — Chess et publication de connaissance —
portées par une interface déjà convaincante. Sa valeur est réelle aujourd'hui pour son
propriétaire. Son principal risque n'est pas l'absence de fonctions, mais l'écart entre
ce que l'interface et la documentation affirment et ce que le lancement canonique rend
accessible.

La priorité n'est ni un gel ni une réarchitecture. Il faut rendre l'application
existante cohérente et observable, puis continuer à livrer des résultats visibles :
opérateur Chess unifié, publication O→N sans doublon et collecte culturelle sourcée.
Avec ces corrections, Hanuman peut démontrer de manière crédible son principe
« relier sans remplacer ».
