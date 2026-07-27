# État actuel

Dernière vérification documentaire : 27 juillet 2026.

Ce document sépare les capacités présentes des intentions. Il ne garantit pas
que les services externes sont configurés sur une machine donnée.

## Produit

| Zone | État | Limite principale |
|---|---|---|
| API FastAPI | disponible | modèle local sans authentification applicative |
| Frontend React/Vite | disponible, buildable | certains statuts et libellés dépassent les preuves backend |
| TUI Textual | prototype | surface réduite, peu centrale |
| Chess | bêta interne | forte personnalisation et dépendances locales |
| Obsidian → Notion | alpha/bêta | applique immédiatement, identité post-publication limitée |
| Wikipédia → Notion | bêta interne | dépend des formats externes |
| GitHub → Notion | alpha | pas d’espace frontend dédié |
| Gmail | lecture seule, alpha | OAuth et données sensibles |
| Calendar | lecture seule, alpha | pas de création d’événement |
| Resources | expérimental | recherche par source, pas de catalogue persistant |
| OpenAI | expérimental | ping et QA sans flux principal |

## Interfaces

Le backend canonique est `hanuman.main:app`. Il assemble les routeurs de
diagnostic, connecteurs, orchestrations, Gmail, Resources, Chess et dashboard.

Le frontend fournit huit espaces fonctionnels. La TUI découvre les modules
d’orchestration et permet des diagnostics simples.

## Connecteurs disponibles

- Obsidian ;
- Notion ;
- Gmail ;
- Google Calendar ;
- GitHub ;
- Wikipédia ;
- Chess.com ;
- OpenAI ;
- YouTube ;
- Gallica ;
- IMSLP ;
- Google Maps sous forme de liens ;
- Stockfish et certains programmes locaux.

Le [catalogue des connecteurs](../connectors/README.md) précise ce que
« disponible » signifie pour chacun.

## Flux disponibles

- publication d’une note Obsidian vers Notion ;
- exploration et comparaison Obsidian/Notion ;
- publication Wikipédia vers Notion ;
- synchronisation d’issues GitHub vers Notion ;
- acquisition Chess.com vers des notes Obsidian ;
- analyse Stockfish et reconstruction de connaissances Chess ;
- création de synthèses Chess dans Notion ;
- context pack Wikipédia vers Notion ;
- question/réponse Wikipédia avec OpenAI en CLI.

Il n’existe pas de synchronisation générale Notion → Obsidian, de moteur de
graphe, de scheduler générique, de système de plugins ou d’agents.

## Qualité vérifiée

Le 27 juillet 2026 :

- l’import de l’application canonique expose 52 opérations ;
- `pytest --collect-only -q` collecte 492 tests ;
- la suite complète `pytest -q` ne produit aucun résultat après plus d’une
  minute et doit être interrompue ;
- le blocage est cohérent avec les rapports historiques liés à `TestClient`.

Ces observations sont un instantané. Pour un verdict courant, exécuter les
commandes du [guide de tests](../developers/testing.md).

La documentation ne publie donc ni nombre permanent de tests ni pourcentage de
couverture statique.

## Écarts architecturaux connus

1. Deux applications FastAPI existent encore, bien que le point d’entrée
   canonique assemble désormais l’application complète.
2. Les routes restent réparties entre `api/core` et `api/routers`.
3. Les accès externes utilisent plusieurs styles : clients fins, services HTTP
   directs et appels directs dans des orchestrations.
4. Le registre de connecteurs décrit un catalogue, pas une interface commune.
5. Les erreurs et résultats de run ne suivent pas un contrat unique.
6. La configuration et les jetons sont répartis entre plusieurs modules et
   fichiers.
7. Le cycle `plan → preview → apply → verify` n’est pas généralisé.

Ces écarts ne doivent pas être masqués par un diagramme idéal.

## Frontières de sécurité

Le modèle sûr suppose :

- un propriétaire unique ;
- une écoute sur `127.0.0.1` ;
- un poste et un vault de confiance ;
- des secrets conservés localement ;
- aucune exposition directe à Internet ou au LAN.

Docker écoute actuellement sur `0.0.0.0` dans le conteneur et publie le port ;
l’opérateur doit contrôler la frontière hôte. Voir
[Sécurité](../operations/security.md).
