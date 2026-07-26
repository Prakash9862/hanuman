# Quick wins (< 2 heures chacun)

Ce sont des propositions, pas des modifications réalisées. ROI combine valeur et faible coût. Scores : U/D/L/C/R/O/H selon `FEATURE_PIPELINE.md`.

| Rang | Action | Pourquoi maintenant | Scores | ROI |
|---:|---|---|---|---|
| 1 | Déclarer officiellement `hanuman.main:app` comme point d’entrée canonique dans README | retire une ambiguïté opérationnelle | 5/8/8/1/1/2/9 | Très élevé |
| 2 | Ajouter à chaque orchestration une fiche source de vérité/effets/idempotence | force les bonnes décisions avant code | 7/9/10/2/1/4/10 | Très élevé |
| 3 | Inventorier les scopes et chemins de tokens sans valeurs secrètes | rend le risque OAuth visible | 6/8/9/2/2/2/10 | Très élevé |
| 4 | Distinguer dans la doc `configured`, `reachable`, `authorized`, `healthy` | évite les faux diagnostics | 6/8/8/2/1/3/9 | Élevé |
| 5 | Marquer les chiffres de tests/couverture du README comme snapshots datés | élimine les affirmations trompeuses | 4/8/7/1/1/1/9 | Élevé |
| 6 | Documenter le caractère local-only comme invariant de déploiement actuel | empêche une exposition accidentelle | 8/7/9/1/2/1/10 | Très élevé |
| 7 | Créer un runbook « token expiré » Gmail/Calendar | réduit le temps de récupération | 7/6/7/2/1/2/9 | Élevé |
| 8 | Étiqueter les adapters vides comme réservés/non implémentés | aligne documentation et réalité | 3/7/6/1/1/1/8 | Moyen |
| 9 | Ajouter une checklist de redaction aux revues | prévient les fuites futures | 7/7/9/1/2/2/10 | Très élevé |
| 10 | Définir les critères de rejet d’un nouveau connecteur | limite la collection de plateformes | 5/8/9/2/1/5/10 | Élevé |

## À ne pas appeler « quick win »

- Introduire Redis/Celery.
- Créer un plugin SDK.
- Ajouter Drive.
- Construire la constellation.
- Uniformiser tous les clients HTTP.
- Réécrire le README en une fois.

Chacun ouvre des décisions d’architecture ou dépasse deux heures malgré une apparence simple.
