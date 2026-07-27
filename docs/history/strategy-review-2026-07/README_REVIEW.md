# Revue de la documentation

> Archive non normative — revue stratégique de juillet 2026.

## Excellent

- Le README exprime avec force le rôle de pont et contient une connaissance architecturale riche.
- Les documents Gmail et Obsidian → Notion donnent des parcours concrets.
- La documentation sécurité reconnaît le modèle personnel local et les actifs sensibles.
- Le Makefile constitue une meilleure référence opérationnelle que des commandes dispersées.
- Les choix d’architecture et la philosophie sont déjà abondamment explicités.

## Problèmes

### README monolithique

Plus de 8 000 lignes mêlent manifeste, manuel, référence, audit, ADR, roadmap et tutoriel. Cette richesse devient une faiblesse : répétitions, contradictions et impossibilité de savoir ce qui est normatif.

### Réalité et aspiration confondues

- Adapters décrits comme couche active alors que leurs clients sont vides.
- Plugin system, mémoire et graphe présentés comme trajectoire quasi acquise.
- Deux points d’entrée décrits sans statut clair.

### Données périssables

Le badge annonce 146 tests et 92 %; l’audit local a collecté 160 puis 171 tests et mesuré 67–70 % sur un périmètre partiel. `README_TESTS.md` décrit un ancien Makefile et affirme que tous les tests passent sans variables manquantes. Les chiffres doivent être générés ou datés.

### Redondances

`README_VERSION.md`, de larges parties du README, `Plan.md` et les sections roadmap racontent des futurs différents. Docker et logs décrivent parfois des fichiers ou pipelines non présents.

### Informations personnelles

Des chemins absolus et exemples personnels apparaissent dans documentation/code. Même sans secret, ils réduisent portabilité et confidentialité.

## Architecture documentaire recommandée

```text
README.md              150–250 lignes : promesse, quickstart, état réel
docs/getting-started/  installation et configuration
docs/reference/        API, connecteurs, orchestrations
docs/operations/       tests, logs, Docker, sécurité, runbooks
docs/strategy/         constitution, audits, roadmap
docs/adr/              décisions numérotées et statut
```

## Politique de vérité

Chaque document porte `statut`, `dernière vérification`, `propriétaire` et, si périssable, la commande de vérification. Les aspirations utilisent « proposé »; le code observé utilise « implémenté »; les fonctionnalités testées utilisent « vérifié ».

## Ce qui manque

- Index documentaire et source de vérité par sujet.
- Matrice routes → orchestration/service → effets.
- Contrats d’orchestrations et source de vérité.
- Inventaire des scopes/permissions.
- Runbooks d’incident.
- Politique de dépréciation documentaire.

## Plan prudent

Ne pas réécrire le README maintenant. D’abord ajouter un bandeau d’état et un index, puis extraire une section à la fois en conservant les liens. Une « grande documentation propre » en un commit serait difficile à relire et risquerait de supprimer un contexte utile.
