# Gedeelde gelabelde fragmenten

Deze selecties staan samen met de video's, bronbeelden en labels in de repository. Haal na clonen of bijwerken ook de Git LFS-bestanden op met `git lfs pull`.

| Selectie | Fragment | Gelabelde beelden | Persoonsboxen | Balboxen |
| --- | --- | ---: | ---: | ---: |
| [Training: bal en spelers](football48/README.md) | 8 fragmenten van 20 seconden | 48 | 512 | 36 |
| [Panorama 128057](panorama128057/README.md) | 00:54-01:14, 20 seconden | 6 | 143 | 29 |
| [TeamTrack 0720-0750](teamtrack0750/README.md) | 00:00-00:20 van de bronclip | 3 | 74 | 3 |

Per map vind je `images/`, `labels/`, `annotations.coco.json`, `manifest.json` en `previews/`. De README in iedere map linkt naar het juiste MP4-fragment en geeft de geselecteerde tijden, bronverwijzingen, labelregels en het commando om de opgeslagen labels in de lokale editor te openen.

**Klassen:** YOLO 0 = `person`, 1 = `ball`; COCO 1 = `person`, 2 = `ball`. Koppel beelden en YOLO-labels op hun identieke bestandsstam. Coördinaten in YOLO zijn genormaliseerd; de COCO-export gebruikt bronpixels.

De video is het invoerfragment. De genoemde geselecteerde beelden zijn geannoteerd; de clips hebben geen doorlopende labels voor elk frame. Boxaantallen tellen instanties per beeld en zijn geen aantallen unieke objecten. De panorama-selectie bevat ook zichtbare reserveballen.

De labels zijn door AI visueel gecorrigeerd en opgeslagen. Onafhankelijke menselijke review staat nog open. De twee kleine proefselecties bevatten achtergrondgroepen als crowd/ignore-regio's: gebruik COCO-evaluatie die die regio's respecteert; maskeer ze of label ze verder voordat je volledige beelden via gewone YOLO-TXT gebruikt voor training. Hun samenhangende tijdgroepen staan op `val` en horen niet willekeurig over verschillende subsets verdeeld te worden.

De nieuwe [football48-trainingsset](football48/README.md) bevat 48 unieke bronframes en voldoet daarmee aan het gevraagde aantal van 40–80 beelden. Deze set heeft gemaskeerde uitsneden, gewone YOLO-labels, 36 train- en 12 validatiebeelden uit gescheiden tijdgroepen, plus een exportoptie voor alleen de bal. Gebruik de bijbehorende `data.yaml`; de oudere proefselecties zijn daar niet doorheen gemengd. Alle beelden komen uit één wedstrijd en leveren geen onafhankelijke wedstrijdtest of modelprestatiemeting op.
