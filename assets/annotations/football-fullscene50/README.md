# 50 extra volledige frames met acht objectklassen

Deze uitbreiding bevat **50 nieuwe bronframes van 4096 × 1080 pixels met 2.451 boxen**. De trainings-PNG's zijn volledige, ongewijzigde gedecodeerde videoframes: geen uitsneden, maskers, verkleining of ingetekende labels. De losse JPG-previews tonen het hele beeld met boxen en zijn alleen voor weergave verkleind.

| YOLO-ID | Klasse | Boxen |
| ---: | --- | ---: |
| 0 | player | 1.078 |
| 1 | ball | 250 |
| 2 | referee | 100 |
| 3 | other_person | 273 |
| 4 | crowd | 150 |
| 5 | goal | 300 |
| 6 | corner_flag | 200 |
| 7 | stored_goals | 100 |

Aantallen tellen boxen per beeld, geen unieke objecten. De set heeft **38 trainingsbeelden en 12 validatiebeelden**, uit acht tijdgroepen. Alle 50 bronindices zijn nieuw ten opzichte van `football48`, `football-fullframe40`, `football-fullscene16` en `football-fullscene20`. De bestaande train/val-indeling per tijdgroep is behouden.

## Ophalen en trainen

Voer vanuit de hoofdmap van de repository uit:

```powershell
git pull
git lfs pull
python assets/annotations/football-fullscene50/validate_dataset.py --ultralytics-scan
```

`data.yaml` gebruikt alleen deze 50 beelden. **`data-combined86.yaml` combineert de nieuwe set met `football-fullscene16` en `football-fullscene20`: 86 volledige beelden, 65 train en 21 val, met 4.209 boxen en dezelfde acht klassen.** De configuratie verwijst naar de drie bestaande beeldmappen; beelden worden niet gekopieerd. Het validatiecommando controleert ook deze gecombineerde dataloader, unieke bronframes en gescheiden tijdgroepen.

Een startconfiguratie met geïnstalleerde Ultralytics:

```powershell
yolo detect train model=yolo11n.pt data=assets/annotations/football-fullscene50/data-combined86.yaml imgsz=2048 rect=True batch=1 epochs=100 patience=20
```

Dit is een startpunt; voor deze levering is geen model getraind of optimale instelling gemeten. Kleine ballen verliezen detail bij verkleinen naar 640 pixels breedte. Kies de resolutie passend bij de hardware. Alle beelden komen uit dezelfde wedstrijd; de combinatie levert geen onafhankelijke wedstrijdtest op.

YOLO-TXT-bestanden in `labels/train` en `labels/val` hebben dezelfde bestandsstam als hun PNG. Coördinaten zijn genormaliseerd naar het volledige frame. `annotations.coco.json` bevat dezelfde boxen in oorspronkelijke pixels en categorie-ID's 1 t/m 8. Oudere sets met minder klassen missen de aanvullende labels en mogen niet zonder aanvulling door deze achtklassenconfiguratie worden gemengd.

## Annotatieregels en controle

`player` omvat herkenbare actieve spelers, inclusief doelmannen; `referee` herkenbare wedstrijdscheidsrechters. Andere individueel herkenbare personen en mensen met onzekere rol krijgen `other_person`. Dichtbezette banken en tribune-/trapgroepen krijgen één `crowd`-box, zonder hun onduidelijk overlappende leden daarnaast afzonderlijk te tellen.

De **250 balboxen** bestaan uit **17 herkenbare speelballen en 233 reserveballen**. Vier speelballen die het voorstelmodel miste, zijn handmatig op de bronpixels toegevoegd. Ook herkenbare gedeeltelijke ballen aan de oorspronkelijke panoramarand zijn meegenomen. Waar de speelbal niet betrouwbaar herkenbaar was, is geen positie gegokt. Zulke frames bevatten wel reserveballen en zijn geen balvrije voorbeelden. Verkeerde voorstellen op schoenen, handen, letters, veldmarkeringen en materiaal zijn verwijderd. Vier mislukte reservebaluitlijningen zijn handmatig gecorrigeerd.

`goal` omvat afzonderlijk herkenbare fysieke doelen, ook trainingsdoelen. Overlappende stapels opgeborgen doelen zijn `stored_goals`-groepen met onbekend ledenaantal. De geschilderde doelomtrek op de groene wand is geen fysiek doel. `corner_flag` omvat vlag en paal, geen kegels of slalompalen. `crowd` en `stored_goals` zijn gewone groep-objectklassen, geen verborgen ignore-maskers. COCO gebruikt daarvoor `is_group: true`, `member_count: null` en `iscrowd: 0`.

**Annotator: Codex (AI); onafhankelijke menselijke controle staat open.** De AI heeft alle volledige contextbeelden, persoonsvoorstellen, dubbele boxen, balvoorstellen, reserveballen, doelen en hoekvlaggen visueel nagekeken. Dit is voorlopig AI-labelwerk; zeer kleine en overlappende objecten verdienen menselijke review. Er is geen gegarandeerde semantische volledigheid of gemeten annotatienauwkeurigheid.

`verification.json` bewaart de uitgevoerde technische controles: bronpixels, checksums, nieuwe bronindices, boxgrenzen, gelijke YOLO/COCO/broncoördinaten, tijdgroepen en dataloaders. Dit zijn consistentiecontroles, geen nauwkeurigheidsmeting. `summary.json` bevat aantallen per klasse en subset.

## Bron en reproductie

Bron: de aangeleverde `128057_panorama_1st_half.mp4`. `source-annotations.json` bevat bron-SHA256, frame-indices, definitieve boxen, klassebeleid en modelvoorstellen. `manifest.json` bevat bestandspaden, RGB-checksums en reviewstatus. De video van 3,3 GB blijft lokaal; de PNG's volstaan om de gedeelde dataset te gebruiken.

Pixelidentiteit controleren met de oorspronkelijke video:

```powershell
python assets/annotations/football-fullscene50/validate_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --ultralytics-scan
```

Beelden en exports opnieuw genereren naar een nieuwe map:

```powershell
python assets/annotations/football-fullscene50/build_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --output output/fullscene50-rebuilt
```

De builder gebruikt OpenCV en Pillow en weigert bestaande beeld-/labelmappen te overschrijven. Bekijken of corrigeren in de bestaande editor:

```powershell
python -m persoon1 annotate --manifest assets/annotations/football-fullscene50/manifest.json --split train --port 8772
```

Gebruik `--split val` met een andere poort voor validatie. Na editorwijzigingen moeten ook bronboxen, COCO-export en statistieken gesynchroniseerd worden; de eenvoudige editor doet dat niet automatisch.
