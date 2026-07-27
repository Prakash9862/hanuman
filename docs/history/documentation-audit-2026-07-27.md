# Audit documentaire — 27 juillet 2026

## Périmètre

L’audit couvre le README, tous les fichiers sous `docs/`, le schéma PNG et la
référence ECO PDF. Les affirmations ont ensuite été comparées au code, aux
routes importées, aux manifestes et à la collecte pytest.

Décisions :

- **conserver** : contenu déjà fiable et singulier ;
- **fusionner** : valeur reprise dans une nouvelle référence ;
- **réécrire** : sujet nécessaire mais document non fiable ;
- **archiver** : preuve datée sans autorité actuelle ;
- **supprimer** : aucune valeur restante après fusion.

## Audit document par document

| Document d’origine | Rôle observé | Diagnostic | Décision |
|---|---|---|---|
| `README.md` | présentation, manuel, API, architecture, audit, roadmap, ADR | 8 684 lignes, répétitif et contradictoire | réécrire entièrement |
| `docs/architecture/HANUMAN_CONCEPTS.md` | vocabulaire connecteur/flux/ressource | utile mais incomplet | fusionner dans `project/concepts.md` |
| `docs/assets/hanuman_architecture.png` | schéma idéal de l’ancienne architecture | esthétique, mais adapters et point d’entrée inexacts | supprimer |
| `docs/chess/ecomast-codes-eco.pdf` | référence de nomenclature ECO | actif dans le code Chess | conserver |
| ADR-0001 | local-first | cohérent avec le modèle actuel | conserver |
| ADR-0002 | appartenance du domaine Chess | décision valide, contraintes de branche périmées | conserver, lire historiquement ces contraintes |
| ADR-0003 | sources de vérité par flux | central et actuel | conserver |
| ADR-0004 | plan/preview/apply/verify | décision valide, application partielle | conserver |
| ADR-0005 | organisation des notes Chess | riche et majoritairement implémenté | conserver |
| ADR-0006 | pages ECO Chess | spécification décisionnelle liée au code actuel | conserver |
| `reviews/chess-analysis-v1.md` | canevas de revue de branche | incomplet et dépassé | supprimer |
| `runbooks/CHESS_ADR_0005_MIGRATION.md` | migration sûre du vault | procédure singulière et prudente | conserver |
| `runbooks/README_DOCKER.md` | ancien guide Docker v2 | commandes et outils partiellement faux | fusionner puis supprimer |
| `runbooks/README_LOGS.md` | ancien détail structlog | chemins, rotation et garanties périssables | fusionner puis supprimer |
| `runbooks/README_SECURITY.md` | modèle de menace | utile mais inachevé après la section 3 | réécrire puis supprimer |
| `runbooks/README_TESTS.md` | tests v2.4 | arborescence, statut et métriques faux | réécrire puis supprimer |
| `specs/calendar-maps-gmail-v1.md` | proposition de flux | clairement future, connecteurs seuls présents | conserver comme spécification |
| `specs/cultural-library-v1.md` | proposition de bibliothèque fédérée | en avance sur Resources | conserver comme spécification |
| `strategy/AGENTS.md` | vision agentique V4 | futur conditionnel, non implémenté | archiver |
| `strategy/ARCHITECTURE_REVIEW.md` | revue du code de juillet 2026 | plusieurs constats désormais datés | archiver |
| `strategy/CHIEF_ARCHITECT_REPORT.md` | décisions proposées au CTO | rapport daté, répétitif | archiver |
| `strategy/CONNECTORS_REVIEW.md` | maturité des connecteurs | chiffres périssables | archiver |
| `strategy/CONTRADICTIONS_AND_IMPLICIT_DECISIONS.md` | contradictions doc/code | source utile de cet audit | archiver |
| `strategy/CTO_REVIEW.md` | synthèse décisionnelle | doublonne le rapport principal | archiver |
| `strategy/EVIDENCE_LEDGER.md` | preuves d’une inspection datée | précieux mais non courant | archiver |
| `strategy/FEATURE_PIPELINE.md` | notation d’idées | roadmap spéculative détaillée | archiver |
| `strategy/HANUMAN.md` | constitution et vision | contenu central mais répétitif | fusionner dans vision/concepts/ADR |
| `strategy/IDEAS.md` | idées argumentées | non implémentées | archiver |
| `strategy/LONG_TERM_VISION.md` | vision à dix ans | hypothétique | archiver |
| `strategy/OBSERVABILITY.md` | stratégie proposée | dépasse le système actuel | archiver |
| `strategy/ORCHESTRATIONS_REVIEW.md` | portefeuille et contrat proposé | constats utiles mais datés | archiver |
| `strategy/PERFORMANCE.md` | budgets proposés | aucune mesure courante | archiver |
| `strategy/QUICK_WINS.md` | actions de moins de deux heures | liste datée | archiver |
| `strategy/README_REVIEW.md` | audit de l’ancien README | diagnostic juste, mission accomplie ici | archiver |
| `strategy/ROADMAP.md` | roadmap pluriannuelle | trop calendrier et détaillée | fusionner, puis archiver |
| `strategy/SECURITY.md` | audit stratégique de sécurité | utile, daté | archiver après fusion |
| `strategy/TECH_DEBT.md` | registre daté | priorités périssables | archiver |
| `strategy/UX.md` | vision cockpit d’orchestrations | futur produit, non référence actuelle | archiver |
| `history/ARBO_SNAPSHOT_v4.txt` | ancien arbre du dépôt | entièrement périmé | supprimer |
| `history/Audit_codex.md` | audit Chess complet | preuve détaillée, correctifs ensuite livrés | conserver comme archive |
| `history/CHESS_ANALYSIS_V1.md` | guide Stockfish V1 | nécessaire pour compatibilité historique | conserver comme archive |
| `history/CHESS_OBSIDIAN_VIEWS.md` | fonctionnement des vues Chess | précis mais versionné historiquement | conserver comme archive |
| `history/CHESS_STOCKFISH_V2.md` | format persistant V2 | valeur de référence historique | conserver comme archive |
| `history/CODEX_NIGHT_REPORT.md` | rapport de tests/couverture | preuve datée, métriques périmées | conserver comme archive |
| `history/GMAIL_SETUP.md` | ancien parcours Gmail | routes utiles, détails déplacés | fusionner puis supprimer |
| `history/HANUMAN_AUDIT_CURRENT_MAIN.md` | audit général récent | meilleure preuve historique avant cette refonte | conserver comme archive |
| `history/OBSIDIAN_NOTION_UI_V1.md` | direction visuelle | décision de design datée et partiellement livrée | conserver comme archive |
| `history/ORCHESTRATION_REPORT.txt` | résultat de recherche de fichiers | vide de conclusion et périmé | supprimer |
| `history/Plan.md` | proposition Tauri/Next/Figma | contredit le frontend React/Vite actuel | supprimer |
| `history/README_OBSIDIAN_NOTION.md` | guide Obsidian → Notion v5 | chemins personnels, version et limites datées | fusionner puis supprimer |
| `history/README_VERSION.md` | snapshot technique 2025 et plan Docker | largement faux, concatène un plan inachevé | supprimer |

## Actifs

### Schéma PNG

Le schéma présente une couche Adapter complète pour chaque plateforme, un
« point d’entrée unique » alors ambigu et plusieurs capacités futures comme
actuelles. Il a été retiré du README puis supprimé afin de ne pas conserver un
diagramme séduisant mais faux.

### PDF ECO

Le PDF contient une nomenclature française des codes et variantes ECO. Le
service `chess_eco_page_service.py` le résout et l’extrait avec `pdftotext`.
Il reste donc un actif documentaire fonctionnel.

## Contradictions avec le code

1. Le README décrivait tour à tour `hanuman.main` comme application complète et
   incomplète. Le code actuel en fait bien l’application complète.
2. La couche Adapter était présentée comme universelle ; seuls GitHub et Notion
   possèdent des clients fins, et plusieurs flux contournent cette couche.
3. Les badges annonçaient 146 tests et 92 %. La collecte actuelle trouve 492
   tests et la suite complète bloque dans l’environnement audité.
4. Plusieurs documents annonçaient Python 3.13, 3.12+ ou 3.12. Le manifeste
   exige `>=3.12,<4.0`.
5. Le guide Docker mentionnait des cibles, outils et workflows absents ou
   modifiés.
6. La « synchronisation Obsidian ↔ Notion » n’a pas de writer général
   Notion → Obsidian.
7. Calendar et Gmail étaient parfois décrits avec des capacités d’écriture ;
   les implémentations actuelles sont en lecture seule hors stockage OAuth.
8. Resources était décrit comme une bibliothèque fédérée ; il s’agit
   actuellement de recherches séparées, sans catalogue persistant.
9. Des documents annonçaient agents, plugins, base de données, graphe,
   workers et scheduler comme trajectoire établie ; aucun n’est disponible.
10. La structure Chess documentée `YYYY/YYYY-MM` diverge de la convention
    actuelle `YYYY/MM` dans les notes et runbooks historiques.

## Résultat

La nouvelle documentation possède un point de vérité par sujet. Les archives
restent accessibles, mais leur index indique explicitement qu’elles ne sont pas
normatives.
