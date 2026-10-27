# Nog 20 volledige frames met acht objectklassen

**20 nieuwe bronframes op 4096 × 1080 pixels, met 979 boxen.** De PNG's zijn volledige, ongewijzigde videoframes: geen uitsneden, maskers, verkleining of ingetekende labels. Alleen de afzonderlijke JPG-previews zijn verkleind en tonen boxen.

| YOLO-ID | Klasse | Boxen |
| ---: | --- | ---: |
| 0 | player | 428 |
| 1 | ball | 100 |
| 2 | referee | 40 |
| 3 | other_person | 111 |
| 4 | crowd | 60 |
| 5 | goal | 120 |
| 6 | corner_flag | 80 |
| 7 | stored_goals | 40 |

Aantallen tellen boxen per beeld, geen unieke objecten. Er zijn **15 train- en 5 validatiebeelden** uit acht tijdgroepen. Alle bronindices zijn nieuw ten opzichte van `football48`, `football-fullframe40` en `football-fullscene16`; de bestaande splits per tijdgroep zijn behouden.

## Ophalen en trainen

Voer vanuit de hoofdmap van de repository uit:

```powershell
git pull
git lfs pull
python assets/annotations/football-fullscene20/validate_dataset.py --ultralytics-scan
```

`data.yaml` gebruikt deze 20 nieuwe beelden. **`data-combined36.yaml` combineert deze uitbreiding met de vorige `football-fullscene16`: 36 volledige beelden, 27 train en 9 val, met dezelfde acht klassen.** De configuratie verwijst naar beide bestaande beeldmappen; beelden worden niet gekopieerd. Het validatiecommando hierboven scant ook deze gecombineerde dataloader.

Een startconfiguratie met geïnstalleerde Ultralytics:

```powershell
yolo detect train model=yolo11n.pt data=assets/annotations/football-fullscene20/data-combined36.yaml imgsz=2048 rect=True batch=1 epochs=100 patience=20
```

Er is voor deze levering geen model getraind of optimale trainingsinstelling gemeten. Kleine ballen verliezen detail bij verkleinen naar 640 pixels breedte; kies de resolutie passend bij de hardware. De beelden komen uit één wedstrijd en leveren geen onafhankelijke wedstrijdtest.

YOLO-TXT-bestanden in `labels/train` en `labels/val` hebben dezelfde bestandsstam als hun PNG. Coördinaten zijn genormaliseerd naar het volledige frame. `annotations.coco.json` bevat dezelfde boxen in oorspronkelijke pixels, categorie-ID's 1 t/m 8. Oudere sets met minder klassen missen aanvullende objectlabels en mogen niet zonder aanvulling door deze achtklassenconfiguratie gemengd worden.

## Labels en controle

`player` bevat herkenbare actieve spelers, inclusief doelmannen; `referee` herkenbare wedstrijdscheidsrechters. Andere individueel herkenbare personen en mensen met onzekere rol staan onder `other_person`. Dichtbezette banken en tribune-/trapgroepen krijgen één `crowd`-box, zonder hun onduidelijk overlappende leden daarnaast afzonderlijk te tellen.

De **100 balboxen** omvatten **92 reserveballen en 8 betrouwbaar herkenbare speelballen**. Ook herkenbare gedeeltelijke ballen aan de oorspronkelijke panoramarand zijn meegenomen. Niet betrouwbaar herkenbare of onzichtbare speelballen krijgen geen gegokte positie. Zulke beelden bevatten wel reserveballen en zijn geen balvrije voorbeelden. Verkeerde voorstellen op letters, schoenen, handen, veldmarkeringen en materiaal zijn verwijderd. Reserveballen zijn op de nieuwe bronbeelden uitgelijnd en visueel gecontroleerd.

`goal` omvat afzonderlijk herkenbare fysieke doelen, ook trainingsdoelen. Overlappende stapels opgeborgen doeltjes zijn aparte `stored_goals`-groepen met onbekend ledenaantal. De geschilderde doelomtrek op de groene wand is geen fysiek doel. `corner_flag` omvat vlag en paal, geen kegels of slalompalen. `crowd` en `stored_goals` zijn gewone groep-objectklassen, geen verborgen ignore-maskers. COCO gebruikt daarvoor `is_group: true`, `member_count: null` en `iscrowd: 0`.

**Annotator: Codex (AI); onafhankelijke menselijke controle staat open.** De AI heeft volledige contextbeelden, persoonsvoorstellen, dubbelingen, balvoorstellen, reserveballen, doelen en hoekvlaggen visueel nagekeken. Dit blijft voorlopig AI-labelwerk; zeer kleine en overlappende objecten verdienen menselijke review. Er is geen gegarandeerde semantische volledigheid of gemeten annotatienauwkeurigheid.

`verification.json` bewaart de uitgevoerde technische controles: bronpixels, checksums, nieuwe bronindices, boxgrenzen, gelijke YOLO/COCO/broncoördinaten, tijdgroepen en dataloaders. Dit zijn consistentiecontroles, geen nauwkeurigheidsmeting. `summary.json` bevat aantallen per klasse en subset.

## Bron en reproductie

Bron: de aangeleverde `128057_panorama_1st_half.mp4`. `source-annotations.json` bevat bron-SHA256, frame-indices, definitieve boxen, klassebeleid en modelvoorstellen. `manifest.json` bevat bestandspaden, RGB-checksums en reviewstatus. De video van 3,3 GB blijft lokaal; de PNG's volstaan om de gedeelde dataset te gebruiken.

Pixelidentiteit controleren met de oorspronkelijke video:

```powershell
python assets/annotations/football-fullscene20/validate_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --ultralytics-scan
```

Opnieuw genereren naar een nieuwe map:

```powershell
python assets/annotations/football-fullscene20/build_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --output output/fullscene20-rebuilt
```

De builder gebruikt OpenCV en Pillow en weigert bestaande beeld-/labelmappen te overschrijven. Bekijken of corrigeren in de bestaande editor:

```powershell
python -m persoon1 annotate --manifest assets/annotations/football-fullscene20/manifest.json --split train --port 8771
```

Gebruik `--split val` met een andere poort voor validatie. Na editorwijzigingen moeten ook bronboxen, COCO-export en statistieken gesynchroniseerd worden; de eenvoudige editor doet dat niet automatisch.
