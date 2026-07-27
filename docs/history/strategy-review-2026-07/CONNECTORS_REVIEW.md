# Revue des connecteurs

> Archive non normative — revue stratégique de juillet 2026.

## Méthode

Maturité évalue l’usage réel, pas la présence dans le registre. Couverture reprend la mesure locale disponible quand connue; sinon elle est qualitative. Un connecteur mature doit isoler auth, transport, pagination, quotas, erreurs et modèles.

| Connecteur | Maturité | Robustesse / couverture | Documentation | Évolutivité | Risque principal |
|---|---|---|---|---|---|
| Notion | Bêta avancée | service très testé (~88 %), mais chemins HTTP multiples | riche, parfois périmée | bonne si chemin canonique | divergence API/version, doublons |
| Obsidian | Bêta | parsing testé (~84 %), filesystem direct | bonne sur O→N | simple, locale | écrasement/chemins, atomicité |
| GitHub | Bêta | service testé (~73 %), filtres d’issues | correcte | bonne | pagination/quota et identité repo |
| Gmail | Alpha solide lecture seule | cœur à ~80 % après audit; routes non validées localement | setup clair | bonne si scope readonly conservé | données très sensibles, OAuth |
| Calendar | Alpha | refresh et erreurs testés (~69 %) | dispersée | moyenne | token local et dates/timezones |
| Wikipedia | Bêta | parsing riche (~79 %) | abondante | bonne en lecture | HTML/API changeants |
| Chess.com | Alpha/Bêta | service ~84 %, orchestration liée à un utilisateur | limitée | faible sans configuration | valeurs personnelles codées |
| OpenAI | Alpha | ping testé, orchestration QA non couverte | conceptuelle | dépend du contrat de sortie | coût, hallucination, fuite contexte |
| YouTube | Alpha | service récent, couverture faible | UI/code surtout | moyenne | quota et clé API |
| Gallica | Expérimental | fallback et HTTP directs | faible | incertaine | stabilité de recherche |
| IMSLP | Expérimental | recherche/open plutôt qu’intégration | faible | limitée | scraping/API non contractuelle |
| Google Drive | Absent | non mesuré | vision seulement | fort potentiel | permissions et explosion du périmètre |

## Constats transverses

- Le registre de capacités est une excellente graine, mais il décrit mieux que le code ne garantit.
- Aucun contrat commun n’impose timeout, retry, pagination, health check ou redaction.
- « Status » mélange configuration, connectivité et santé du fournisseur.
- Les plateformes en lecture publique sont moins risquées; les connecteurs d’écriture doivent avoir un niveau de maturité supérieur.

## Barre de maturité proposée

1. **Expérimental** : lecture manuelle, aucun SLA.
2. **Alpha** : contrat local, doubles de test, erreurs explicites.
3. **Bêta** : pagination, quotas, auth lifecycle, observabilité, compatibilité documentée.
4. **Stable** : idempotence d’écriture, tests de contrat enregistrés, politique de dépréciation, runbook.

## Priorités

1. Rendre Notion et Obsidian « stables » avant d’ajouter Drive.
2. Faire de Gmail/Calendar un domaine Google cohérent sans fusionner leurs capacités.
3. Garder YouTube/Gallica/IMSLP comme ressources de lecture; ne pas surinvestir avant un usage récurrent.
4. Ne pas créer de SDK plugin tant que trois connecteurs n’implémentent pas naturellement le même contrat.
