# Configuration

Hanuman combine variables d’environnement et fichiers de credentials locaux.
La configuration n’est pas encore centralisée dans un contrat unique.

## Principes

- Copier les paramètres localement ; ne jamais les committer.
- Utiliser le moindre scope.
- Lier l’API à `127.0.0.1`.
- Donner le mode `0600` aux fichiers de tokens.
- Ne pas placer un vault, une adresse personnelle ou un secret dans un exemple
  versionné.

## Variables principales

Les noms exacts sont définis dans `src/hanuman/config/env.py`,
`src/hanuman/core/config.py` et les services concernés. Les familles courantes
sont :

| Domaine | Configuration |
|---|---|
| Notion | token, version d’API, parent ou base cible |
| GitHub | token, propriétaire et dépôts selon le flux |
| OpenAI | clé API et paramètres du modèle |
| Obsidian | chemin du vault et racine Chess |
| Chess.com | nom d’utilisateur |
| Stockfish | chemin du binaire |
| Google | client OAuth, secret, redirection et fichiers de token |
| YouTube | clé API |

Ne recopiez pas cette table dans un `.env` sans vérifier les modules : certains
noms sont spécifiques au flux.

### GitHub Activity → Notion Project Memory — Phase 1

La commande de planification utilise :

| Variable | Rôle |
|---|---|
| `GITHUB_TOKEN` | Jeton GitHub en lecture |
| `GITHUB_ALLOWED_REPOSITORIES` | Liste séparée par des virgules des dépôts autorisés au format `owner/name` |

Le dépôt passé avec `--repository` doit être présent dans
`GITHUB_ALLOWED_REPOSITORIES`. Aucun paramètre Notion n'est lu par cette
commande.

## Gmail

Gmail utilise le scope lecture seule et stocke son token dans :

```text
.secrets/gmail-token.json
```

Les credentials peuvent être fournis par l’environnement ou un fichier local
ignoré. Le parcours OAuth est accessible depuis l’interface Gmail.

## Google Calendar

Calendar utilise également un parcours OAuth en lecture seule. Son token est
stocké séparément de Gmail. Vérifier les permissions du fichier après la
première autorisation.

## Obsidian et Chess

Définir une racine de vault et une racine Chess explicites. Les commandes de
reconstruction Chess exigent une cible existante et sûre ; elles ne doivent pas
viser la racine du dépôt ni le vrai vault lors d’une preview.

Le PDF ECO suivi dans `docs/chess/` est une donnée de référence, pas une
configuration secrète.

## Vérification

Après configuration :

1. lancer l’API sur loopback ;
2. ouvrir Swagger ;
3. tester uniquement le diagnostic du connecteur concerné ;
4. examiner les scopes avant une action d’écriture ;
5. utiliser une donnée de test et une destination dédiée.

Un connecteur « déclaré » ou « joignable » n’est pas nécessairement autorisé à
effectuer toutes ses opérations.
