# Revue de performance

## Diagnostic

Hanuman est aujourd’hui un service personnel dominé par la latence réseau et le parsing, non par le CPU. Il n’existe aucune preuve qu’une optimisation générale soit nécessaire. Le risque principal est opérationnel : appels séquentiels, pagination incomplète, processus détachés et absence de budgets.

## Axes

### Latence

- Les listes Gmail récupèrent chaque message individuellement : coût N+1 assumé mais à mesurer.
- Les orchestrations Notion peuvent multiplier recherches, créations et blocs.
- Plusieurs bibliothèques HTTP empêchent une politique commune de connexion et timeout.

### Mémoire

Les Markdown, HTML Wikipedia et listes de parties sont souvent chargés en mémoire. Acceptable à l’échelle personnelle; un streaming prématuré compliquerait le code. Fixer d’abord des limites d’entrée explicites.

### Cache

Bon candidat : métadonnées publiques, data source Notion, réponses de health check très courtes. Mauvais candidat : mails, tokens, contenu personnel ou résultats dont la fraîcheur détermine une écriture. Tout cache doit exposer âge et invalidation.

### Parallélisme

Paralléliser les lectures indépendantes d’un briefing peut réduire la latence. Paralléliser les écritures avant idempotence et reprise est dangereux. Ordre : identité → reprise → limites → parallélisme.

### Montée en charge

La montée en charge utile est le nombre d’orchestrations et d’objets personnels, pas le nombre d’utilisateurs. Un SaaS multi-tenant n’est pas un objectif. Une file externe, Redis ou Kubernetes seraient prématurés.

## Budgets recommandés

Chaque orchestration devrait déclarer : durée maximale, nombre d’appels, volume lu, volume écrit, coût IA et concurrence. Un dépassement arrête proprement et produit un état reprenable.

## Mesures avant optimisation

- p50/p95 de durée par orchestration et étape.
- appels externes, retries, rate-limit et octets.
- taille des lots et taux de no-op.
- temps de preview versus apply.
- mémoire maximale uniquement pour les flux lourds.

## Conclusion

La priorité performance est la **prévisibilité**, pas la vitesse. L’utilisateur tolère une synchronisation de 20 secondes s’il voit le progrès et peut la reprendre; il ne tolère pas une action rapide qui double ou perd ses données.

