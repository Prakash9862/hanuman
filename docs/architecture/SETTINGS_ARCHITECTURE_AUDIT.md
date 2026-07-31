# Audit d'architecture --- Module **Paramètres** (Hanuman)

*Date : Audit réalisé au fil de l'inspection des fichiers du projet*

------------------------------------------------------------------------

# 1. Objectif

L'objectif de cet audit était de déterminer si le module **Paramètres**
reposait sur une architecture saine ou s'il souffrait de duplications,
de responsabilités mal réparties ou de données simulées.

Le principe retenu est le suivant :

-   **Paramètres ne doit posséder aucune logique métier.**
-   Il doit agréger les informations produites par les services
    existants.
-   Le backend est la source de vérité.
-   Le frontend ne doit jamais inventer l'état d'un connecteur.

------------------------------------------------------------------------

# 2. Travaux réalisés

## Frontend

### Supprimés

-   `HealthPage.tsx`
-   `health.css`

Constat : - la page reposait sur des listes codées en dur ; - score
global simulé ; - localStorage utilisé comme source de diagnostic ; -
aucun lien réel avec l'état du backend.

Décision : suppression définitive.

------------------------------------------------------------------------

### Conservés

-   `SettingsPage.tsx`
-   `settings.css`
-   `App.tsx`
-   `main.tsx`
-   `models/navigation.ts`

Ces fichiers constituent désormais la base du futur module Paramètres.

------------------------------------------------------------------------

## ResourcesPage

Constat :

-   environ **1 500 lignes**
-   plusieurs espaces fonctionnels regroupés dans un seul composant
-   nombreuses requêtes API
-   styles inline nombreux

Le fichier fonctionne mais représente une dette technique.

Décision :

-   ne pas modifier maintenant ;
-   prévoir un découpage futur en plusieurs composants.

------------------------------------------------------------------------

## models/connectors.ts

Constat :

Le frontend possède encore :

-   labels
-   descriptions
-   statuts
-   routes
-   catalogue

codés manuellement.

Cela fait doublon avec :

`services/connectors_registry.py`

Décision :

Conserver provisoirement pour la page Connecteurs, mais **ne jamais
l'utiliser comme source de vérité pour Paramètres**.

------------------------------------------------------------------------

## models/flows.ts

Même constat.

Les flux sont décrits manuellement.

À terme ils devraient provenir du backend.

Conserver provisoirement.

------------------------------------------------------------------------

# 3. Backend

## connectors_registry.py

Excellent découpage.

Responsabilité unique :

-   catalogue officiel des connecteurs

Il expose :

-   list_connectors()
-   get_connector()
-   list_capabilities()
-   providers_for()

Décision :

Conserver.

Il devient la référence officielle des connecteurs.

------------------------------------------------------------------------

## models/connectors.py

Responsabilité :

-   modèles Pydantic

Très propre.

À conserver.

Le champ `ConnectorState` existe déjà mais n'est pas encore réellement
calculé.

------------------------------------------------------------------------

## routers/connectors.py

Routeur très sain.

Il expose simplement le registre.

Aucune duplication.

À conserver.

------------------------------------------------------------------------

## status.py

Important :

Il ne s'agit **pas** d'un système de diagnostic.

Il indique uniquement que l'API répond.

Exemple :

-   /status
-   /status/ping

Décision :

Le conserver uniquement comme endpoint de disponibilité.

Ne pas l'utiliser pour Paramètres.

------------------------------------------------------------------------

## local_programs_service.py

Très bon découpage.

Responsabilité unique :

-   détection des programmes locaux
-   version
-   chemin
-   présence

À conserver.

Le futur module Paramètres devra consommer ce service.

------------------------------------------------------------------------

## env.py

Le commentaire annonce explicitement :

> source unique de vérité pour les variables d'environnement.

Cette philosophie est excellente.

Toutes les variables critiques sont centralisées.

À conserver.

------------------------------------------------------------------------

## core/config.py

Observation :

Une seconde manière de charger la configuration existe.

Cela peut constituer un doublon conceptuel avec `env.py`.

Aucun changement immédiat.

À surveiller.

------------------------------------------------------------------------

# 4. Architecture validée

    env.py
            │
    core/config.py
            │
    connectors_registry.py
            │
    local_programs_service.py
            │
    status.py
            │
    -------------------------
            │
    (settings)
            │
    SettingsPage

Le futur module Settings doit être un **agrégateur**.

Il ne doit pas relire les fichiers de configuration ni redétecter les
programmes.

------------------------------------------------------------------------

# 5. Décisions prises

## Garder

Backend

-   models/connectors.py
-   services/connectors_registry.py
-   services/local_programs_service.py
-   api/routers/connectors.py
-   api/core/status.py
-   config/env.py
-   api/core/main.py

Frontend

-   SettingsPage.tsx
-   settings.css
-   App.tsx
-   main.tsx
-   models/navigation.ts
-   ResourcesPage.tsx (provisoirement)
-   models/connectors.ts (provisoirement)
-   models/flows.ts (provisoirement)

------------------------------------------------------------------------

## Supprimer

-   HealthPage.tsx
-   health.css

------------------------------------------------------------------------

## À surveiller

-   duplication possible entre `env.py` et `core/config.py`
-   duplication entre `connectors_registry.py` et `models/connectors.ts`
-   duplication entre `flowDefinitions` et un futur registre backend des
    flux

------------------------------------------------------------------------

# 6. Dettes techniques

## Priorité faible

Découper `ResourcesPage.tsx`.

## Priorité moyenne

Clarifier la gestion de la configuration (`env.py` / `core/config.py`).

## Priorité élevée

Faire disparaître les catalogues frontend comme source de vérité.

------------------------------------------------------------------------

# 7. Ce qui manque réellement

Le backend ne possède pas encore un service d'agrégation des
informations nécessaires à Paramètres.

Il manque uniquement :

    models/settings.py
    services/settings_service.py
    api/routers/settings.py

Ces éléments devront uniquement agréger :

-   configuration
-   registre des connecteurs
-   programmes locaux
-   état API

sans réimplémenter leur logique.

------------------------------------------------------------------------

# 8. Conclusion

L'audit montre que le backend est globalement bien structuré.

Le principal problème identifié ne réside pas dans les services
existants mais dans certaines représentations frontend encore statiques.

La stratégie retenue est donc de **réutiliser** les briques existantes
plutôt que d'en créer de nouvelles.

Le futur module Paramètres deviendra un tableau de bord transversal,
construit comme un agrégateur de services, respectant le principe de
source de vérité unique et limitant au maximum les duplications.
