# Registre de dette technique

Échelle : priorité P0 immédiate, P1 prochain cycle, P2 planifiée, P3 opportuniste. Les coûts sont relatifs : XS < 2 h, S < 1 j, M 2–5 j, L > 1 sem.

## Critique

Aucun défaut observé ne justifie P0 tant que Hanuman reste strictement local et non exposé. Cette conclusion devient fausse dès qu’il écoute au-delà du loopback.

## Élevée

| Dette | Impact | Urgence | Coût | Priorité |
|---|---|---:|---:|---:|
| Absence de garde d’authentification applicative sur des routes capables d’écrire/lancer | prise de contrôle locale ou réseau si exposition | avant toute exposition | M | P1 |
| Cycle d’exécution non gouverné (`Popen`, pas d’ID/état/annulation) | doubles lancements, effets invisibles | avant agents/scheduling | M | P1 |
| Configuration fragmentée et `load_dotenv(..., override=True)` | environnement écrasé, diagnostics difficiles | prochain cycle | M | P1 |
| Tokens Calendar sauvegardés sans permission explicite `0600` | confidentialité locale moins robuste que Gmail | prochain cycle | S | P1 |
| Valeurs personnelles codées dans Chess → Obsidian | non-portabilité et mauvaise cible possible | prochain changement du flux | S | P1 |
| Suite HTTP bloquée dans l’environnement local | régressions de routes non détectées | immédiat pour la CI locale | S–M | P1 |

## Moyenne

| Dette | Impact | Urgence | Coût | Priorité |
|---|---|---:|---:|---:|
| Clients HTTP hétérogènes (`urllib`, `requests`, `httpx`) | politiques timeout/erreur dispersées | graduelle | L | P2 |
| Erreurs publiques non uniformes, parfois HTTP 200 | observabilité et UX incohérentes | avant client stable | M | P2 |
| Deux surfaces backend/points d’entrée documentés | confusion opérationnelle | courte | XS | P2 |
| Adapters vides mais abondamment documentés | fausse confiance architecturale | courte | XS doc | P2 |
| Idempotence inégale selon les orchestrations | doublons Notion/Obsidian | avant automatisation | M–L | P2 |
| Pas de schéma commun de résultat d’exécution | dashboard et agents difficiles | avant V2 | M | P2 |
| Couverture faible de `obsidian_to_notion_safe`, resources et IA Wikipedia | risques non protégés | progressive | M | P2 |
| README de plus de 8 000 lignes et chiffres périmés | onboarding et décisions brouillés | prochain cycle doc | M | P2 |
| Pipeline CI dépendant de secrets réels pour tests | couplage CI inutile, risque de fuite | prochain changement CI | S | P2 |

## Faible

| Dette | Impact | Urgence | Coût | Priorité |
|---|---|---:|---:|---:|
| Quatre écarts Black préexistants | bruit qualité | opportuniste | XS | P3 |
| `datetime.utcnow()` déprécié via modèles | avertissements futurs | avant upgrade Pydantic | XS | P3 |
| Fichiers/dossiers vides (`types`, adapters, tests integration) | bruit mental | revue structurelle future | XS | P3 |
| Nommage `chess-com` vs modules `chess` | cohérence du catalogue | prochain contrat | XS | P3 |
| Documentation Docker et version largement historique | commandes trompeuses | avec README | S | P3 |

## Règle de remboursement

Ne pas lancer un « sprint dette ». Chaque évolution doit payer la dette qu’elle traverse. Les dettes P1 forment toutefois un verrou : aucune autonomie, exposition réseau ou planification récurrente avant leur traitement.

