# 16 nieuwe volledige frames: personen, ballen, doelen en vlaggen

Deze set bevat **16 nieuwe bronframes op de originele 4096 × 1080 pixels** en **779 boxen**. De trainings-PNG's zijn ongewijzigde volledige videoframes: geen uitsneden, maskers, verkleining of ingetekende labels. De JPG-previews tonen het hele beeld met boxen en zijn alleen voor weergave verkleind.

| YOLO-ID | Klasse | Boxen | Betekenis |
| ---: | --- | ---: | --- |
| 0 | player | 339 | Herkenbare actieve spelers, inclusief doelmannen |
| 1 | ball | 82 | Zichtbaar herkenbare voetballen, ook reserveballen |
| 2 | referee | 32 | Herkenbare wedstrijdscheidsrechters |
| 3 | other_person | 86 | Andere individueel herkenbare personen, of personen met een onzekere precieze rol |
| 4 | crowd | 48 | Groepsboxen rond dichtbezette banken en tribune-/trapgroepen |
| 5 | goal | 96 | Afzonderlijk herkenbare fysieke doelen met frame en net, ook trainingsdoelen |
| 6 | corner_flag | 64 | De hoekvlag en paal; geen losse kegels of slalompalen |
| 7 | stored_goals | 32 | Groepsboxen rond overlappende opgeborgen doeltjes |

De aantallen tellen boxen **per beeld**, geen unieke mensen, ballen of doelen. Een `crowd`- of `stored_goals`-box stelt één groep voor; het aantal groepsleden is onbekend. Zo worden onduidelijk overlappende objecten niet als verzonnen afzonderlijke instanties gepresenteerd. De geschilderde doelomtrek op de groene trainingswand is geen fysiek doel en valt buiten `goal`.

Er zijn 12 trainingsbeelden en 4 validatiebeelden, verdeeld over acht gescheiden tijdgroepen. Alle 16 bronindices zijn nieuw ten opzichte van `football48` en `football-fullframe40`. De oorspronkelijke train/val-indeling van de tijdgroepen blijft behouden. Alles komt uit dezelfde aangeleverde wedstrijdvideo; dit is extra ontwikkeldata, geen onafhankelijke wedstrijdtest.

## Ophalen en trainen

```powershell
git pull
git lfs pull
python assets/annotations/football-fullscene16/validate_dataset.py --ultralytics-scan
```

Gebruik `assets/annotations/football-fullscene16/data.yaml` voor de volledige set met acht klassen. YOLO-TXT-bestanden staan naast de overeenkomstige naamstammen in `images/train` / `labels/train` en `images/val` / `labels/val`. Coördinaten zijn genormaliseerd naar het **volledige** frame. COCO gebruikt dezelfde klassen met ID's 1 t/m 8 en boxen in oorspronkelijke pixels.

Voorbeeld voor een eerste fine-tuning met geïnstalleerde Ultralytics:

```powershell
yolo detect train model=yolo11n.pt data=assets/annotations/football-fullscene16/data.yaml imgsz=2048 rect=True batch=1 epochs=100 patience=20
```

De speelbal is soms maar enkele bronpixels groot. Bij 640 pixels breedte gaat veel detail verloren; kies de trainingsresolutie passend bij je hardware. De instelling hierboven is een startpunt en is niet als optimale trainingsinstelling gemeten. Er is voor deze levering geen model getraind.

De eerste drie klassen komen overeen met `football-fullframe40`. Die oudere set mist echter labels voor de vijf aanvullende klassen. Meng beide sets niet rechtstreeks voor training van alle acht klassen: dan zouden doelen en andere nieuwe objectklassen in oudere beelden ten onrechte als achtergrond gelden.

## Wat gecontroleerd is

De AI heeft de volledige context, individuele persoonsvoorstellen, groepjes, balvoorstellen en de vaste doelen en hoekvlaggen visueel bekeken. Verkeerde voorstellen op letters, schoenen, trainingsmateriaal, bomen en bouwonderdelen zijn verwijderd. Reserveballen die langs de zijlijn zijn verplaatst, zijn opnieuw uitgelijnd en gecontroleerd; drie mislukte templatevoorstellen zijn visueel gecorrigeerd.

Van de 82 balboxen zijn 74 reserveballen en 8 betrouwbaar geïdentificeerde speelballen. Herkenbare ballen aan de onderste panoramarand hebben boxen om hun zichtbare deel. Waar de speelbal niet betrouwbaar herkenbaar was, is geen positie gegokt. Zulke beelden zijn niet als balvrije beelden geregistreerd: ze bevatten nog steeds zichtbare reserveballen. Zeer kleine onherkenbare objectdelen blijven als aandachtspunt in de bronmetadata staan.

**Annotator: Codex (AI); onafhankelijke menselijke review staat open.** De labels zijn voorlopig AI-labelwerk. De dekking van zeer kleine of overlappende objecten verdient menselijke controle; deze levering claimt geen gegarandeerde semantische volledigheid of annotatienauwkeurigheid.

`verification.json` bewaart de werkelijk uitgevoerde technische controles: pixelidentiteit met alle 16 oorspronkelijke gedecodeerde frames, checksums, nieuwe bronindices, tijdscheiding, boxgrenzen, gelijke YOLO/COCO/broncoördinaten en de Ultralytics-dataloader. `summary.json` bevat de uitsplitsing per klasse en subset.

`crowd` en `stored_goals` zijn in deze set gewone groep-objectklassen. Hun COCO-annotaties hebben `is_group: true`, `member_count: null` en `iscrowd: 0`; dit zijn geen verborgen ignore-maskers of afzonderlijke persoonslabels.

## Bron en reproductie

Bron: de door Jorre aangeleverde `128057_panorama_1st_half.mp4`. Bron-SHA256, bronframe-index, tijd, definitieve boxen en modelvoorstellen staan in `source-annotations.json`. `manifest.json` koppelt de bestanden aan de bron en reviewstatus. De volledige video van 3,3 GB is niet nodig om de gedeelde PNG's en labels te gebruiken.

Met de oorspronkelijke video kun je de pixelidentiteit controleren:

```powershell
python assets/annotations/football-fullscene16/validate_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --ultralytics-scan
```

Opnieuw opbouwen naar een nieuwe map:

```powershell
python assets/annotations/football-fullscene16/build_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --output output/fullscene16-rebuilt
```

Deze scripts gebruiken Python, OpenCV en Pillow; de dataloaderscan vereist ook Ultralytics. De builder weigert bestaande beeld- en labelmappen te overschrijven. Voor bekijken of corrigeren in de bestaande editor:

```powershell
python -m persoon1 annotate --manifest assets/annotations/football-fullscene16/manifest.json --split train --port 8770
```

Gebruik `--split val` met een andere poort voor de validatiebeelden. Na editorwijzigingen moeten de bronboxen, COCO-export en statistieken eveneens worden gesynchroniseerd; de eenvoudige editor schrijft die afgeleide bestanden niet automatisch bij.
