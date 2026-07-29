1. Connecteur

Définition :

Un connecteur est une application, un logiciel, un service ou un programme connecté individuellement à Hanuman.

Il expose des capacités propres.

Exemples :

YouTube
Obsidian
Notion
Chess.com
SCID
Stockfish
Gmail
DevDocs
Monkeytype

Exemple simple :

YouTube

→ recherche
→ récupération des vidéos
→ playlists
→ commentaires
...

Il n'y a encore aucune orchestration.

2. Flux

Définition :

Un flux est une orchestration de plusieurs connecteurs réalisée par Hanuman pour accomplir une tâche.

Exemples :

Chess.com
      ↓
SCID
      ↓
Stockfish
      ↓
Obsidian

ou

GitHub
      ↓
Notion

Le flux est donc le cœur d'Hanuman.

3. Journal de Vie

C'est probablement le concept que je comprenais le moins bien.

Ce n'est pas un journal intime.

Ce n'est pas une base de données.

C'est un ensemble de routines personnelles, analysées par Hanuman.

Exemples :

Quotidien
Cuisine
Typing
Sport
etc.

Puis Hanuman produit une analyse du type :

« Tu n'as pas cuisiné depuis une semaine. »
« Tu progresses bien en typing. »
« Tu es beaucoup plus régulier ce mois-ci. »

Le Journal de Vie est donc un espace d'analyse de tes habitudes, pas une destination universelle pour les données des connecteurs.

4. Agents IA

À terme :

Les agents IA automatisent un maximum de flux et d'actions afin de faire gagner du temps.

Ils ne remplacent ni les connecteurs ni les flux.

Ils les utilisent.

5. Accueil

L'accueil comporte également deux sections techniques :

Santé

➡️ la santé de Hanuman :

statistiques
performances
utilisation
logs
erreurs
monitoring

Ce n'est pas la santé de l'utilisateur.

Paramètres

Configuration générale d'Hanuman.

---

Pour Santé, je suis d'accord avec toi.

Le problème est qu'en français, Santé signifie spontanément :

santé physique ;
santé mentale ;
santé de l'utilisateur.

Or chez Hanuman, c'est exactement l'inverse.

C'est :

logs ;
performances ;
monitoring ;
erreurs ;
statistiques d'utilisation.

Le nom induit donc en erreur.

Personnellement, je vois trois possibilités.

1. Tout mettre dans Paramètres ⭐⭐⭐⭐⭐

Franchement, c'est peut-être la solution la plus élégante.

Paramètres
├── Général
├── Connecteurs
├── Apparence
├── Sécurité
├── Santé d'Hanuman
├── Logs
├── Statistiques
└── Sauvegardes

L'utilisateur ne va presque jamais consulter ces informations.

Elles sont de nature "administration de l'application".

Donc elles peuvent très bien vivre dans Paramètres.

2. Renommer Santé

Je trouve ça moins bon.

Tu vas chercher un mot qui sera toujours moins naturel.

Par exemple :

Diagnostic
Système
Monitoring
Maintenance

Aucun ne me convainc.

3. Conserver une page dédiée

Je pense que ce n'est justifié que si Hanuman devient très complexe.

Par exemple si un jour tu affiches :

consommation CPU
mémoire
LLM utilisés
coûts API
état des connecteurs
files d'attente
métriques
historique des erreurs

Là, ça devient presque un tableau de bord DevOps.

Mais aujourd'hui, je trouve que c'est prématuré.

Donc si tu me demandes mon avis aujourd'hui :

➡️ je supprimerais carrément "Santé" du menu latéral.

Je mettrais tout dans Paramètres, avec éventuellement un onglet Diagnostic ou État d'Hanuman à l'intérieur.

Je trouve que ça allège la navigation, évite une ambiguïté avec la santé de l'utilisateur, et garde le menu principal concentré sur ce que l'utilisateur vient réellement faire avec Hanuman. C'est cohérent avec notre philosophie : le menu principal doit représenter les grands espaces de travail, pas les aspects techniques de l'application.
