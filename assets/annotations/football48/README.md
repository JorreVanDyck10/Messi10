# Trainingsselectie: bal en spelers, 48 beelden

Deze set bevat **48 verschillende bronframes**, met **512 persoonsboxen en 36 balboxen**. Dat valt binnen de gevraagde 40–80 geselecteerde beelden. Er zijn geen augmentaties als extra beelden meegeteld. De bron is `128057_panorama_1st_half.mp4`, aangeleverd door Jorre. De volledige bronvideo van 3,3 GB is niet nodig om de geëxporteerde beelden te gebruiken.

| Subset | Beelden | Persoonsboxen | Balboxen | Beelden zonder bal |
| --- | ---: | ---: | ---: | ---: |
| train | 36 | 433 | 26 | 10 |
| val | 12 | 79 | 10 | 2 |
| totaal | 48 | 512 | 36 | 12 |

De twaalf beelden zonder bal zijn visueel gecontroleerde uitsneden en bevatten wel persoonslabels. Ze leren een baldetector ook om geen bal te voorspellen bij schoenen, veldlijnen en spelers. De bal is alleen gelabeld als hij zichtbaar te identificeren is; er zijn geen geschatte posities achter spelers of reserveballen meegeteld.

## Bestanden ophalen en gebruiken

Voer vanuit de repository uit:

```powershell
git pull
git lfs pull
python assets/annotations/football48/validate_dataset.py
```

`images/train` en `images/val` bevatten de invoerbeelden. `labels/` bevat de bijbehorende YOLO-TXT-bestanden. Klassen: **0 = person, 1 = ball**. Een labelregel is `class x_center y_center width height`, genormaliseerd naar het invoerbeeld. `annotations.coco.json` bevat dezelfde boxen in pixels van het geëxporteerde beeld, met COCO-klassen **1 = person, 2 = ball**. `previews/` toont de opgeslagen labels: cyaan voor personen en geel voor de bal. De trainingsbeelden zelf bevatten geen getekende boxen.

`data.yaml` is de gezamenlijke YOLO-dataset. Voor een eerste lokale fine-tuning met geïnstalleerde Ultralytics:

```powershell
yolo detect train model=yolo11n.pt data=assets/annotations/football48/data.yaml imgsz=1280 epochs=100 batch=2 patience=20
```

Omdat de bal prioriteit heeft, kun je daarnaast een dataset met alleen de balklasse maken. De originele splits blijven behouden en de twaalf beelden zonder bal krijgen lege labelbestanden. Dit zijn dezelfde 48 beelden, geen extra trainingsvoorbeelden.

```powershell
python assets/annotations/football48/make_ball_only.py --output data/football48-ball-only
python assets/annotations/football48/validate_dataset.py --ball-only data/football48-ball-only --ultralytics-scan
yolo detect train model=yolo11n.pt data=data/football48-ball-only/data.yaml imgsz=1280 epochs=100 batch=2 patience=20
```

Kies een nieuwe uitvoermap als de balexport al bestaat. Pas batch en device aan je hardware aan. De trainingscommando's zijn een startconfiguratie: er is bij deze annotatielevering geen model getraind en geen modelprestatie gemeten. Het bestaande `persoon1 train`-traject behoudt zijn eigen vereisten voor teamreview en een aparte testset.

## Fragmenten van 20 seconden

De acht volledige panorama-fragmenten staan in [assets/clips20/panorama128057-training48](../../clips20/panorama128057-training48/). Elk fragment bevat 500 frames op 25 fps en behoudt de oorspronkelijke 4096 × 1080 pixels. De video's dienen als context; alleen de geselecteerde uitsneden hebben labels, niet ieder videoframe.

| Tijdgroep in bron | Subset | Geselecteerde beelden | Met zichtbare bal |
| --- | --- | ---: | ---: |
| 05:30–05:50 | train | 4 | 3 |
| 09:00–09:20 | val | 6 | 4 |
| 12:30–12:50 | train | 7 | 6 |
| 16:00–16:20 | train | 7 | 5 |
| 19:30–19:50 | train | 5 | 3 |
| 23:00–23:20 | train | 6 | 4 |
| 26:30–26:50 | train | 7 | 5 |
| 33:30–33:50 | val | 6 | 6 |

Tijden zijn relatief aan het eerste gedecodeerde videoframe: `frame_index / 25`. De container heeft een eerste video-PTS van 1 seconde. Het clipmanifest bewaart de verwijzingen naar de gelabelde frames. Een pixelvergelijking op één geselecteerd beeld per fragment vindt de overeenkomst binnen één frame (0,04 seconde) van deze tijdkoppeling; de gecomprimeerde clips zijn contextbeelden. De lossless PNG's met hun SHA256 zijn de vaste invoer voor training.

## Selectie en labelregels

Elk bronframe levert precies één uitsnede van **1280 × 640 op oorspronkelijke pixelschaal**. Daardoor blijft de kleine bal beter zichtbaar dan bij het verkleinen van het volledige panorama. De uitsnede wisselt van plaats; de bal staat niet steeds centraal. Kleine/verre ballen, beweging, overlap tussen spelers, het doelgebied, veldlijnen en verschillende veldposities komen voor.

De buitenkant van het veld en de dug-out/tribuneachtergrond zijn zwart gemaskeerd. Gedetecteerde personen buiten het geselecteerde veldgebied zijn eveneens gemaskeerd; geselecteerde personen en de bal zijn op hun boxpositie uit de originele pixels teruggezet. Hierdoor bevat deze gewone YOLO-export geen onbehandelde crowd/ignore-regio's. De maskering is deel van de invoervoorbewerking: gebruik bij toepassing op volledige panoramavideo's vergelijkbare veldmaskers en uitsneden. Dit is geen dataset voor rechtstreeks trainen op onbewerkte volledige panoramabeelden.

`person` omvat de zichtbare personen op het veld, inclusief scheidsrechters. Eén box per persoon; bij afsnijding of overlap wordt het zichtbare lichaamsdeel begrensd. Automatische YOLO11n-voorstellen zijn visueel nagekeken. Er zijn 51 dubbele of samengevoegde persoonsvoorstellen verwijderd, meerdere boxen aangepast en twee zichtbare personen toegevoegd. Ballen zijn op originele pixels bekeken en gecorrigeerd; een detectorvoorstel alleen was geen voldoende bewijs.

De splits volgen hele tijdgroepen. De dichtstbijzijnde train- en validatiebeelden liggen 195 seconden uit elkaar. Nabije beelden binnen een tijdgroep kunnen sterk op elkaar lijken. Alles komt uit **één wedstrijd**: deze set is voldoende voor een eerste kleine fine-tuning, maar een onafhankelijke wedstrijdtest en extra wedstrijdvariatie blijven nodig om generalisatie te beoordelen.

## Controle, herkomst en review

`verification.json` rapporteert de werkelijk uitgevoerde controles: unieke bronframes en invoerpixels, beeldchecksums, boxgrenzen, gelijke COCO/YOLO/broncoördinaten, klassemapping en tijdscheiding. De Ultralytics-dataloader is afzonderlijk voor beide subsets en de balexport gecontroleerd. Dit is bestandscontrole, geen meting van annotatienauwkeurigheid.

**Annotator: Codex (AI), met visuele correctie. Onafhankelijke menselijke review staat open.** Er zijn geen menselijke goedkeuringen ingevuld. Controleer vooral de kleinste ballen en sterk overlappende spelers voordat je een definitieve evaluatieset vastzet.

`source-annotations.json` bevat de bron-SHA256, oorspronkelijke boxen, cropcoördinaten, maskerveld, automatische persoonsvoorstellen en de correcties. `manifest.json` koppelt de opgeslagen bestanden aan bronframe, tijd, split en reviewstatus. Om de beelden identiek opnieuw te genereren met de oorspronkelijke bronvideo, kies je een nieuwe map:

```powershell
python assets/annotations/football48/build_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --output output/football48-rebuilt
python assets/annotations/football48/build_clips.py --source C:/pad/128057_panorama_1st_half.mp4 --output output/football48-clips
```

Hiervoor zijn Python, OpenCV, NumPy, Pillow en imageio-ffmpeg nodig; de dataloaderscan vereist ook Ultralytics. De scripts weigeren bestaande uitvoer te overschrijven. De editor voor opgeslagen labels open je met:

```powershell
python -m persoon1 annotate --manifest assets/annotations/football48/manifest.json --split train --port 8768
```

Gebruik `--split val` en een andere poort om de validatiebeelden te bekijken. Na labelwijzigingen moeten COCO, statistieken en verificatie opnieuw worden bijgewerkt; de eenvoudige editor herschrijft die afgeleide exports niet automatisch.
