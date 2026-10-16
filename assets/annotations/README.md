# Gedeelde gelabelde fragmenten

Deze selecties staan samen met de video's, bronbeelden en labels in de repository. Haal na clonen of bijwerken ook de Git LFS-bestanden op met `git lfs pull`.

| Selectie | Fragment | Gelabelde beelden | Persoonsboxen | Balboxen |
| --- | --- | ---: | ---: | ---: |
| [Panorama 128057](panorama128057/README.md) | 00:54-01:14, 20 seconden | 6 | 143 | 29 |
| [TeamTrack 0720-0750](teamtrack0750/README.md) | 00:00-00:20 van de bronclip | 3 | 74 | 3 |

Per map vind je `images/`, `labels/`, `annotations.coco.json`, `manifest.json` en `previews/`. De README in iedere map linkt naar het juiste MP4-fragment en geeft de geselecteerde tijden, bronverwijzingen, labelregels en het commando om de opgeslagen labels in de lokale editor te openen.

**Klassen:** YOLO 0 = `person`, 1 = `ball`; COCO 1 = `person`, 2 = `ball`. Koppel beelden en YOLO-labels op hun identieke bestandsstam. Coördinaten in YOLO zijn genormaliseerd; de COCO-export gebruikt bronpixels.

De video is het invoerfragment. De genoemde geselecteerde beelden zijn geannoteerd; de clips hebben geen doorlopende labels voor elk frame. Boxaantallen tellen instanties per beeld en zijn geen aantallen unieke objecten. De panorama-selectie bevat ook zichtbare reserveballen.

De labels zijn door AI visueel gecorrigeerd en opgeslagen. Onafhankelijke menselijke review staat nog open. Beide exports bevatten achtergrondgroepen als crowd/ignore-regio's: gebruik COCO-evaluatie die die regio's respecteert; maskeer ze of label ze verder voordat je volledige beelden via gewone YOLO-TXT gebruikt voor training. De samenhangende tijdgroepen staan op `val` en horen niet willekeurig over verschillende subsets verdeeld te worden.

Dit zijn kleine bijdragen aan de grotere challenge-dataset. De geselecteerde beelden samen zijn nog geen volledige set van 40-80 frames en leveren geen onafhankelijke wedstrijdtest of modelprestatiemeting op.
