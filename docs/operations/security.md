# Sécurité

## Modèle de menace

Hanuman est conçu pour un poste personnel, un propriétaire et une écoute
loopback. Il manipule des tokens, des messages, des calendriers, des notes
locales et des écritures vers des outils externes.

Le modèle change radicalement si l’API est accessible depuis le LAN ou
Internet.

```text
navigateur local ──> API locale ──> APIs tierces
                         │
                         ├──> vault Obsidian
                         └──> programmes locaux
```

L’API ne possède pas d’authentification applicative générale. CORS reste large.
Une exposition réseau est donc hors périmètre sûr.

## Actifs

- tokens OAuth et clés API ;
- contenu Gmail et Calendar ;
- notes et analyses du vault ;
- pages Notion et issues GitHub ;
- journaux et reçus d’exécution ;
- processus locaux déclenchables.

## Règles

1. Lier les serveurs à `127.0.0.1`.
2. Ne jamais committer `.env`, credentials, tokens, logs ou données du vault.
3. Utiliser les scopes minimaux ; Gmail et Calendar sont actuellement en
   lecture seule.
4. Appliquer `0600` aux fichiers de tokens et credentials.
5. Résoudre et confiner tout chemin avant écriture.
6. Refuser les symlinks qui sortent d’une racine autorisée.
7. Expurger tokens, sujets, chemins et contenus avant journalisation ou partage.
8. Prévisualiser les effets importants et sauvegarder la destination.
9. Traiter tout contenu externe comme non fiable.
10. Ne jamais transmettre un secret à un modèle.

## Risques connus

| Risque | Gravité dans le modèle local |
|---|---|
| API sans authentification | modérée localement, critique si exposée |
| CORS permissif | conditionnel à l’exposition |
| chemins absolus de publication | élevé pour les données locales |
| permissions hétérogènes de tokens/logs | modéré |
| résultats HTTP hétérogènes | modéré pour le diagnostic |
| processus sans état commun | modéré |
| prompt injection future | critique si un agent obtient des écritures |

## Docker

Le port publié par Docker peut être accessible au-delà du loopback selon la
configuration hôte. Ne déduisez pas du caractère « local-first » que Compose
est automatiquement confiné.

## Incident

En cas de fuite possible :

1. arrêter Hanuman ;
2. révoquer le token chez le fournisseur ;
3. générer un nouveau credential au scope minimal ;
4. inspecter Git, logs et historique de commandes ;
5. supprimer ou expurger les artefacts locaux après sauvegarde des preuves ;
6. documenter la cause sans recopier le secret.

En cas d’écriture incorrecte, préserver la source et la destination, relever les
identifiants produits, puis restaurer depuis une sauvegarde vérifiée.

## Avant une exposition réseau

Un nouvel ADR et une revue dédiée sont obligatoires : authentification,
autorisation, origines, CSRF, TLS, gestion des sessions, limitation de débit,
isolation des chemins, audit et rotation des secrets.
