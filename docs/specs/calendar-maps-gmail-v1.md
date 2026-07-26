# Calendar + Maps + Gmail — Spécification V1

## Intention utilisateur

Créer dans Hanuman un événement enrichi, puis recevoir les informations utiles
à son déplacement.

## Exemple

« Rendez-vous à la Bibliothèque nationale à 14 h vendredi, départ depuis mon
domicile. »

## Sources de vérité

- événement, date, heure et adresse : Google Calendar ;
- géographie et itinéraire : Google Maps ;
- adresse de départ : configuration personnelle locale ;
- récapitulatif envoyé : Gmail ;
- état et preuve de l’exécution : Hanuman.

## Entrées V1

- titre ;
- date ;
- heure de début ;
- heure de fin facultative ;
- adresse ;
- notes facultatives ;
- destination du récapitulatif ;
- adresse de départ configurée localement.

## Plan

Hanuman prépare :

1. l’événement Calendar ;
2. le lien Maps vers la destination ;
3. le lien d’itinéraire depuis le domicile ;
4. un récapitulatif ;
5. la liste exacte des effets prévus.

## Preview

Afficher avant validation :

- titre et horaires ;
- adresse comprise par Hanuman ;
- événement qui sera créé ;
- liens Maps générés ;
- destinataire du mail ;
- informations manquantes ou ambiguës.

## Apply

Après approbation :

1. créer l’événement Calendar ;
2. vérifier qu’il existe ;
3. générer le récapitulatif ;
4. envoyer le mail.

## Verify

- relecture de l’événement par son identifiant ;
- confirmation du destinataire Gmail ;
- état final `succeeded`, `partial` ou `failed`.

## Hors périmètre V1

- trafic en temps réel ;
- choix automatique multimodal ;
- surveillance continue ;
- modification automatique de l’heure de départ ;
- notification mobile Hanuman ;
- actions sans approbation.

## Critères d’acceptation

- aucun événement en double ;
- aucune écriture avant preview ;
- adresse de domicile jamais exposée dans les logs ;
- échec Gmail n’annule pas silencieusement l’événement Calendar ;
- l’utilisateur sait exactement ce qui a réussi ou échoué.
