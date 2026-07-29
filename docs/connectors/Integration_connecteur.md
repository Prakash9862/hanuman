Avec Anki, vous avez surtout validé le modèle d'intégration : un nouveau connecteur se branche désormais toujours de la même façon (service → API → registre → frontend → workspace → constellation → tests).

---

Plan du générateur de connecteurs
Phase 1 — Définir un manifeste unique

Chaque nouveau connecteur sera décrit dans un seul fichier, par exemple :

id: devdocs
label: DevDocs
description: Recherche et consultation de documentation technique.
kind: remote_api
auth: false
writable: false

capabilities:
  - documentation.search
  - documentation.open

workspace:
  enabled: true
  type: search
  eyebrow: Documentation technique
  placeholder: Rechercher une API, une fonction ou un framework…

constellation:
  enabled: true
  size: small
  palette: jade
  family: crystalline

Le manifeste devient la source de vérité. On ne ressaisit plus id, label, route, capacités et type dans cinq fichiers différents.

Emplacement proposé :

connectors/
└── devdocs.yaml
Phase 2 — Créer le moteur scaffold

Structure :

src/hanuman/scaffold/
├── __init__.py
├── connector.py
├── manifest.py
├── planner.py
├── writer.py
├── markers.py
└── templates/
    ├── service.py.tpl
    ├── service_test.py.tpl
    ├── api_routes.py.tpl
    ├── registry.py.tpl
    ├── frontend_definition.ts.tpl
    ├── frontend_workspace.ts.tpl
    ├── constellation.ts.tpl
    └── documentation.md.tpl

Responsabilités :

manifest.py : charge et valide le YAML ;
planner.py : calcule les créations et modifications ;
writer.py : applique le plan ;
markers.py : injecte le code dans des zones sûres ;
connector.py : commande principale et orchestration.
Phase 3 — Installer des points d’extension balisés

Le générateur ne doit pas chercher arbitrairement « après Anki » ou « avant OpenAI ».

On ajoute des marqueurs stables dans les fichiers centraux.

Registre backend
_CONNECTORS: tuple[ConnectorDescriptor, ...] = (
    # scaffold:connectors:registry:start

    # scaffold:connectors:registry:end
)
Routes API
# scaffold:connectors:imports:start

# scaffold:connectors:imports:end
# scaffold:connectors:routes:start

# scaffold:connectors:routes:end
Tests du registre
EXPECTED_CONNECTOR_IDS = {
    # scaffold:connectors:test-ids:start

    # scaffold:connectors:test-ids:end
}
Modèle frontend
// scaffold:connectors:imports:start
// scaffold:connectors:imports:end
export const connectorDefinitions = [
  // scaffold:connectors:definitions:start

  // scaffold:connectors:definitions:end
]
Workspaces
export type ConnectorWorkspaceId =
  // scaffold:connectors:workspace-ids:start
  // scaffold:connectors:workspace-ids:end
export const connectorWorkspaces = [
  // scaffold:connectors:workspaces:start

  // scaffold:connectors:workspaces:end
]
Constellation
const visualMetadata = {
  // scaffold:connectors:constellation:start

  // scaffold:connectors:constellation:end
}

Le générateur n’écrit qu’entre ces limites. Aucun replace() fondé sur le nom d’un connecteur voisin.

Phase 4 — Deux modes de génération

Tous les connecteurs n’ont pas le même workspace. Le générateur proposera des profils.

catalog-only

Pour une capacité sans interface dédiée :

registre
statut API
catalogue
constellation
tests
documentation
search

Pour DevDocs, Paperless-ngx, Contacts :

barre de recherche
appel API
résultats normalisés
états vide/chargement/erreur
dashboard

Pour Horloge, Monkeytype :

chargement automatique
cartes d’indicateurs
actualisation
aucune barre de recherche imposée
custom

Le générateur prépare seulement le conteneur :

{active === 'connector-id' && (
  <ConnectorWorkspace />
)}

puis on développe l’interface métier à la main.

C’est essentiel : le scaffold accélère la plomberie, sans prétendre deviner le métier.

Phase 5 — Commandes CLI

La CLI actuelle utilise argparse. On lui ajoute :

poetry run python -m hanuman.cli scaffold connector connectors/devdocs.yaml

Puis, quand l’entrée hanuman sera déclarée dans pyproject.toml :

hanuman scaffold connector connectors/devdocs.yaml

Options indispensables :

--dry-run
--check
--force
--no-workspace
--dry-run

Affiche :

Créations
  + src/hanuman/services/core/devdocs_service.py
  + tests/services/test_devdocs_service.py
  + docs/connectors/devdocs.md

Modifications
  ~ connectors_registry.py
  ~ resources.py
  ~ connectors.ts
  ~ constellationModel.ts
  ~ test_connectors_registry.py

Aucune écriture.

--check

Vérifie qu’un connecteur existant est complètement intégré :

Service              OK
API                  OK
Registry             OK
Frontend             OK
Workspace             MANQUANT
Constellation        OK
Tests                OK
Documentation        MANQUANTE

Cette commande sera presque aussi utile que la génération elle-même : elle détectera les demi-cadavres architecturaux.

Phase 6 — Sécurité et idempotence

Le générateur devra :

refuser un identifiant invalide ;
refuser un connecteur déjà déclaré ;
ne jamais écraser un service existant sans --force ;
créer une sauvegarde ou travailler en mémoire avant écriture ;
appliquer toutes les modifications ou aucune ;
produire le même résultat s’il est relancé ;
vérifier que chaque marqueur existe exactement une fois ;
afficher le diff prévu ;
ne jamais lancer de commit automatiquement.

En cas d’échec au quatrième fichier, les trois premiers ne doivent pas rester modifiés. On prépare tout, on valide, puis on écrit atomiquement.

Phase 7 — Validation automatique

Après génération :

Black
Ruff
mypy
pytest ciblé
build frontend

Commande envisagée :

hanuman scaffold connector connectors/devdocs.yaml --validate

Le générateur ne dira pas « connecteur terminé ». Il dira :

Structure intégrée.
Implémentation métier restante :
- client DevDocs
- recherche réelle
- transformation des résultats
Phase 8 — Premier test réel : DevDocs

DevDocs est un excellent cobaye :

lecture seule ;
pas d’authentification ;
workspace de recherche ;
peu de risques ;
suffisamment réel pour révéler les faiblesses du scaffold.

Séquence :

1. créer le manifeste DevDocs ;
2. lancer --dry-run ;
3. inspecter le plan ;
4. générer ;
5. implémenter uniquement le client réel ;
6. mesurer ce qu’on a encore dû faire à la main ;
7. améliorer le scaffold ;
8. seulement ensuite intégrer Contacts et Paperless-ngx.
Ordre de réalisation

Je suivrais exactement ceci :

Ajouter les marqueurs d’extension.
Écrire les tests du système de marqueurs.
Créer et valider le modèle de manifeste.
Construire le planificateur --dry-run.
Générer service, tests et documentation.
Automatiser registre et routes API.
Automatiser catalogue et constellation.
Automatiser les workspaces par profil.
Ajouter --check.
Tester l’ensemble avec DevDocs.

La première livraison ne cherchera donc pas à tout générer d’un coup. Elle devra déjà savoir faire parfaitement :

manifeste
→ plan déterministe
→ fichiers créés
→ registre/API intégrés
→ contrôle d’intégrité

Ensuite seulement, on attaquera l’automatisation du frontend. C’est moins spectaculaire qu’un énorme script omnipotent, mais beaucoup plus solide — les divinités omnipotentes finissent souvent mal, surtout dans les monorepos. 😏
