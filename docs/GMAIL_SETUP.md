# Gmail → Hanuman — configuration V1

Cette intégration est strictement en lecture seule et utilise le scope OAuth :

```text
https://www.googleapis.com/auth/gmail.readonly
```

## 1. Google Cloud

1. Créer ou ouvrir un projet Google Cloud.
2. Activer **Gmail API**.
3. Configurer l’écran de consentement OAuth.
4. Créer un client OAuth **Application de bureau**.
5. Télécharger le JSON et l’enregistrer ici :

```text
config/gmail_credentials.json
```

Ce fichier est ignoré par Git.

## 2. Lancer Hanuman

```bash
make run
```

Ouvrir ensuite :

```text
http://127.0.0.1:5173/orchestrations/gmail
```

Cliquer sur **Ouvrir l’autorisation Google**, accepter l’accès puis revenir dans Hanuman et cliquer sur **Actualiser**.

Le jeton est stocké localement dans :

```text
.secrets/gmail-token.json
```

Il est également ignoré par Git et créé avec des permissions restreintes.

## 3. Routes disponibles

```text
GET /gmail/status
GET /gmail/auth/start
GET /gmail/auth/callback
GET /gmail/messages
GET /gmail/important
GET /gmail/messages/{message_id}
```

Aucune route d’envoi, de suppression, d’archivage ou de modification n’existe dans cette V1.
