# Gedeelde gelabelde fragmenten

Deze selecties staan samen met de video's, bronbeelden en labels in de repository. Haal na clonen of bijwerken ook de Git LFS-bestanden op met `git lfs pull`.

| Selectie | Fragment | Gelabelde beelden | Persoonsboxen | Balboxen |
| --- | --- | ---: | ---: | ---: |
| [60 extra volledige scènes, focus op speelbal](football-fullscene60/README.md) | 60 nieuwe volledige 4096 × 1080-beelden | 60 | 1.749 | 320, waarvan 60 speelballen |
| [50 extra volledige scènes](football-fullscene50/README.md) | 50 nieuwe volledige 4096 × 1080-beelden | 50 | 1.451 | 250 |
| [20 extra volledige scènes](football-fullscene20/README.md) | 20 nieuwe volledige 4096 × 1080-beelden | 20 | 579 | 100 |
| [Volledige scène, ook doelen en hoekvlaggen](football-fullscene16/README.md) | 16 nieuwe volledige 4096 × 1080-beelden | 16 | 457 | 82 |
| [Volledige originele frames](football-fullframe40/README.md) | 8 tijdgroepen; onbewerkte 4096 × 1080-beelden | 40 | 923 | 192 |
| [Training: bal en spelers](football48/README.md) | 8 fragmenten van 20 seconden | 48 | 512 | 36 |
| [Panorama 128057](panorama128057/README.md) | 00:54-01:14, 20 seconden | 6 | 143 | 29 |
| [TeamTrack 0720-0750](teamtrack0750/README.md) | 00:00-00:20 van de bronclip | 3 | 74 | 3 |

Per map vind je `images/`, `labels/`, `annotations.coco.json`, `manifest.json` en `previews/`. De README in iedere map linkt naar het juiste MP4-fragment en geeft de geselecteerde tijden, bronverwijzingen, labelregels en het commando om de opgeslagen labels in de lokale editor te openen.

**Klassen:** `football-fullscene16`, `football-fullscene20` en `football-fullscene50` hebben acht klassen: spelers, ballen, scheidsrechters, overige personen, publieksgroepen, doelen, hoekvlaggen en groepen opgeborgen doelen. `football-fullframe40` gebruikt YOLO 0 = `player`, 1 = `ball`, 2 = `referee`; COCO 1, 2, 3. De oudere selecties gebruiken YOLO 0 = `person`, 1 = `ball`; COCO 1 = `person`, 2 = `ball`. Koppel beelden en YOLO-labels op hun identieke bestandsstam. Coördinaten in YOLO zijn genormaliseerd; COCO gebruikt pixels van het opgeslagen invoerbeeld. In de tabel tellen persoonsboxen de afzonderlijk gelabelde personen; groepsboxen zijn daar niet bij opgeteld.

De video is het invoerfragment. De genoemde geselecteerde beelden zijn geannoteerd; de clips hebben geen doorlopende labels voor elk frame. Boxaantallen tellen instanties per beeld en zijn geen aantallen unieke objecten. De panorama-selectie bevat ook zichtbare reserveballen.

De labels zijn door AI visueel gecorrigeerd en opgeslagen. Onafhankelijke menselijke review staat nog open. De twee kleine proefselecties bevatten achtergrondgroepen als crowd/ignore-regio's: gebruik COCO-evaluatie die die regio's respecteert; maskeer ze of label ze verder voordat je volledige beelden via gewone YOLO-TXT gebruikt voor training. Hun samenhangende tijdgroepen staan op `val` en horen niet willekeurig over verschillende subsets verdeeld te worden.

De nieuwe [football48-trainingsset](football48/README.md) bevat 48 unieke bronframes en voldoet daarmee aan het gevraagde aantal van 40–80 beelden. Deze set heeft gemaskeerde uitsneden, gewone YOLO-labels, 36 train- en 12 validatiebeelden uit gescheiden tijdgroepen, plus een exportoptie voor alleen de bal. Gebruik de bijbehorende `data.yaml`; de oudere proefselecties zijn daar niet doorheen gemengd. Alle beelden komen uit één wedstrijd en leveren geen onafhankelijke wedstrijdtest of modelprestatiemeting op.

Voor training op **volledige ongewijzigde frames** gebruik je [football-fullframe40/data.yaml](football-fullframe40/data.yaml): 30 train, 10 val, zonder uitsneden of maskers. Deze set heeft 24 nieuwe bronmomenten en 16 opnieuw gelabelde volledige frames uit `football48`. De splits blijven behouden. De README bevat ook exports voor alle ballen of uitsluitend de speelbal. Door de overlappende bronframes en verschillende klassen moet je beide sets niet willekeurig door elkaar verdelen.

De uitbreiding [football-fullscene16](football-fullscene16/README.md) bevat 16 andere bronframes met 12 train en 4 val. Ook overige personen, publieksgroepen, doelen en hoekvlaggen zijn meegenomen. Gebruik de eigen `data.yaml` voor deze acht klassen; oudere beelden missen de nieuwe objectklassen en mogen voor die taak niet zonder aanvullende annotaties worden meegemengd.

De uitbreiding [football-fullscene20](football-fullscene20/README.md) voegt nog 20 nieuwe volledige beelden met 979 boxen toe (15 train, 5 val). Gebruik `football-fullscene20/data-combined36.yaml` om deze samen met de vorige 16 scènes te trainen: 36 beelden, 27 train en 9 val, met dezelfde acht klassen en behouden tijdgroepen.

De uitbreiding [football-fullscene50](football-fullscene50/README.md) voegt 50 nieuwe volledige beelden met 2.451 boxen toe (38 train, 12 val). Met `football-fullscene50/data-combined86.yaml` gebruik je deze samen met de vorige 36 scènes: 86 beelden, 65 train en 21 val, met dezelfde acht klassen en behouden tijdgroepen.

De uitbreiding [football-fullscene60](football-fullscene60/README.md) voegt 60 nieuwe volledige beelden met 2.969 boxen toe (40 train, 20 val). Elk beeld bevat één gelabelde speelbal. Gebruik de beschreven `make_in_play_dataset.py`-export om uitsluitend de speelbal te trainen, met reserveballen als bewuste achtergrond. `data-combined146.yaml` combineert de vier volledige-scènesets voor alle acht klassen: 146 beelden, 105 train en 41 val. De 60 nieuwe frames liggen deels dicht bij elkaar rondom balacties en zijn geen 60 onafhankelijke acties.
