# 40 volledige frames voor training

**40 originele beelden van 4096 × 1080 pixels**, met YOLO- en COCO-labels. De PNG's zijn pixel voor pixel gelijk aan de gedecodeerde bronframes: geen uitsneden, maskers, verkleining of ingetekende boxen in de trainingsbeelden. De kleinere JPG's in `previews/` zijn alleen om labels te bekijken.

De bron is de aangeleverde `128057_panorama_1st_half.mp4`. Er zijn **24 nieuwe bronmomenten** en **16 eerder geselecteerde momenten die opnieuw op het volledige frame zijn gelabeld**. Tel deze 16 niet nog eens als nieuwe onafhankelijke bronframes naast `football48`.

| Subset | Volledige beelden | Spelerboxen | Balboxen | Scheidsrechterboxen |
| --- | ---: | ---: | ---: | ---: |
| train | 30 | 631 | 147 | 60 |
| val | 10 | 212 | 45 | 20 |
| totaal | 40 | 843 | 192 | 80 |

De 192 balboxen bestaan uit 37 speelballen en 155 reserveballen, geteld per beeld. Bij drie onzekere speelbalposities is geen box gegokt; andere zichtbare ballen in die frames zijn wel gelabeld.

## Direct gebruiken

```powershell
git pull
git lfs pull
python assets/annotations/football-fullframe40/validate_dataset.py --ultralytics-scan
```

Gebruik `assets/annotations/football-fullframe40/data.yaml` als dataset. De bestanden hebben dezelfde naamstam in `images/train` / `labels/train` en `images/val` / `labels/val`.

| YOLO-klasse | Naam | Betekenis |
| ---: | --- | --- |
| 0 | player | Herkenbare spelers van beide teams, inclusief doelmannen |
| 1 | ball | Zichtbaar herkenbare voetballen, inclusief reserveballen |
| 2 | referee | Duidelijk herkenbare centrale en nabije assistent-scheidsrechter |

COCO gebruikt dezelfde namen met categorie-ID's 1, 2, 3. YOLO-boxen zijn genormaliseerd naar **4096 × 1080**; COCO en `source-annotations.json` gebruiken pixels van het volledige beeld. `summary.json` bevat de aantallen per klasse en subset. De klassemapping verschilt van de eerdere set met `person` en `ball`: meng labels niet zonder die mapping aan te passen.

Voorbeeld voor een eerste fine-tuning met geïnstalleerde Ultralytics:

```powershell
yolo detect train model=yolo11n.pt data=assets/annotations/football-fullframe40/data.yaml imgsz=2048 rect=True batch=1 epochs=100 patience=20
```

De kleine speelbal is soms maar 4–12 bronpixels breed. Bij `imgsz=640` blijft daar vaak ongeveer één pixel van over. Kies een hogere resolutie passend bij het GPU-geheugen; 2048 is een startconfiguratie, geen gevalideerde optimale trainingsinstelling. Er is voor deze levering geen model getraind.

## Alleen de bal trainen

Alle zichtbare gelabelde voetballen, met klasse 0:

```powershell
python assets/annotations/football-fullframe40/make_ball_only.py --output data/fullframe40-ball
yolo detect train model=yolo11n.pt data=data/fullframe40-ball/data.yaml imgsz=2048 rect=True batch=1 epochs=100
```

Voor alleen de **speelbal** is er een aparte export. Het doel heet dan `in_play_ball`; reserveballen zijn bewust achtergrond. De drie frames met een onzekere of verborgen speelbal worden overgeslagen en niet als negatieve voorbeelden gepresenteerd. De resterende 37 volledige beelden behouden hun oorspronkelijke tijdsplit: 27 train, 10 val.

```powershell
python assets/annotations/football-fullframe40/make_ball_only.py --in-play-only --output data/fullframe40-match-ball
```

Beide exports behouden de ongewijzigde volledige beelden en maken een eigen `data.yaml`. Kies een nieuwe uitvoermap als die al bestaat.

## Selectie en review

Er zijn 30 trainingsbeelden en 10 validatiebeelden, uit acht tijdgroepen. De validatiegroepen liggen rond 09:01–09:07 en 33:31–33:32 in de bron. Nabije frames uit dezelfde groep blijven samen; de bestaande `football48`-splits zijn behouden. Dit is één wedstrijd en geen onafhankelijke wedstrijdtest. Sommige opeenvolgende momenten lijken sterk op elkaar; dit is een kleine startset, geen bewijs van modelgeneralisatie.

De AI heeft detectorvoorstellen op de oorspronkelijke pixels nagekeken, achtergrondfiguren en dubbele voorstellen verwijderd en balboxen gecorrigeerd. Voor eerder geselecteerde bronframes zijn ook eerder gecontroleerde boxen gebruikt. Transfers naar andere frames die niet visueel betrouwbaar waren, zijn verworpen. Publiek, bankzitters en staf zijn geen `player`. De dekking van verre officials en sterk overlappende spelers blijft voorlopig; kleine ambigue objectdelen aan de onderste panoramarand zijn niet op basis van een gok gelabeld. Bronstatus en aandachtspunten staan per frame in de JSON-bestanden.

**Annotator: Codex (AI). Onafhankelijke menselijke review staat open.** Er zijn geen menselijke goedkeuringen of modelprestaties ingevuld. `verification.json` controleert bestandsintegriteit en coördinaten; het is geen annotatienauwkeurigheidsmeting. De dataset is als gewone YOLO-dataset in te lezen, maar verdient menselijke controle voordat je definitieve evaluatieresultaten vastlegt.

## Broncontrole en opnieuw opbouwen

`manifest.json` bewaart voor elk frame de tijd, bronindex, split en SHA256 van zowel de PNG als de oorspronkelijke RGB-pixels. `source-annotations.json` bevat de definitieve boxen en hun herkomst. Met de aangeleverde bronvideo controleer je de pixelidentiteit opnieuw:

```powershell
python assets/annotations/football-fullframe40/validate_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --ultralytics-scan
```

Opnieuw opbouwen naar een nieuwe map:

```powershell
python assets/annotations/football-fullframe40/build_dataset.py --source C:/pad/128057_panorama_1st_half.mp4 --output output/fullframe40-rebuilt
```

Hiervoor zijn Python, OpenCV en Pillow nodig; de dataloaderscan vereist ook Ultralytics. De volledige video van 3,3 GB is niet nodig om de gedeelde PNG's en labels te gebruiken. De bestaande [20-secondenclips](../../clips20/panorama128057-training48/) bieden context bij de tijdgroepen; enkele nieuwe frames liggen net voor zo'n clipgrens.

De bewaarde labels in de editor openen:

```powershell
python -m persoon1 annotate --manifest assets/annotations/football-fullframe40/manifest.json --split train --port 8769
```

Voor de validatieset gebruik je `--split val` en een andere poort. De editor verandert YOLO en reviewstatus; na een wijziging moeten COCO, de bronboxen en afgeleide statistieken opnieuw worden gesynchroniseerd.
