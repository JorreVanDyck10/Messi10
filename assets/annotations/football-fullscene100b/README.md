# 100 extra volledige frames, met focus op de speelbal

Deze uitbreiding bevat **100 nieuwe volledige PNG-beelden van 4096 × 1080 pixels**, met **4.909 boxen** en **één zichtbare speelbal per beeld**. De beelden hebben geen uitsnede, vergroting, masker of ingetekende labels. Tekeningen staan uitsluitend in `previews/`.

## Download en gebruik

Vanuit de repository:

```powershell
git pull
git lfs pull
python assets/annotations/football-fullscene100b/make_in_play_dataset.py --output data/fullscene100b-in-play
```

Gebruik voor het herkennen van **de speelbal** vervolgens `data/fullscene100b-in-play/data.yaml`: klasse 0 = `in_play_ball`, **70 train en 30 val**, samen 100 speelbalboxen. De export gebruikt dezelfde volledige beelden; reserveballen zijn bewust achtergrond en krijgen geen positief label. De oorspronkelijke video is hiervoor niet nodig. Kies bij herhaling een nieuwe uitvoermap.

De standaard `data.yaml` bevat acht klassen voor de volledige scène. In die algemene detectietaak vallen speel- én reserveballen onder `ball`; het onderscheid staat als `kind` in de bronannotaties en COCO-export. Gebruik de aparte export hierboven wanneer uitsluitend de speelbal het doel is.

| YOLO | Klasse | Boxen |
| ---: | --- | ---: |
| 0 | player | 2.145 |
| 1 | ball | 558: 100 speelballen en 458 reserveballen |
| 2 | referee | 200 |
| 3 | other_person | 506 |
| 4 | crowd | 300 groepsboxen |
| 5 | goal | 600 |
| 6 | corner_flag | 400 |
| 7 | stored_goals | 200 groepsboxen |

Spelers omvatten beide ploegen en keepers; onduidelijke personenrollen zijn `other_person`. Dichte publieks-/bankgroepen en overlappende doelstapels hebben groepsboxen zonder geschat ledenaantal. Per beeld zijn zes fysieke doelen gelabeld: twee wedstrijddoelen en vier losse trainingsdoelen, naast twee groepen opgeborgen doelen. Een geschilderde doelvorm op de wand telt niet mee. Groepsboxen zijn gewone detectieklassen, geen ignore-regio's. YOLO gebruikt klasse-ID's 0–7 en genormaliseerde coördinaten; COCO gebruikt 1–8 en pixels.

`data-combined346.yaml` combineert deze uitbreiding met de vorige volledige-scènesets van 16, 20, 50, 60 en 100 beelden: **346 unieke bronframes, 245 train en 101 val**, met dezelfde acht klassen. Oudere beelden missen soms een betrouwbaar onderscheid tussen speelbal en reservebal; ze worden niet automatisch in de nieuwe speelbalexport opgenomen.

## Selectie en annotatiemethode

De 100 bronindices verschillen van alle eerdere selecties `football48`, `football-fullframe40`, `football-fullscene16`, `football-fullscene20`, `football-fullscene50`, `football-fullscene60` en `football-fullscene100`. Ze liggen binnen 0,48 seconde van eerder beoordeelde referentieframes; sommige nieuwe beelden liggen onderling slechts één frame (0,04 seconde) uit elkaar. Uit 128 kandidaten zijn 100 beelden met een herkenbare speelbal behouden. Een stilstaande wedstrijdsbal bij een spelhervatting telt als speelbal.

Dit zijn **aanvullende tijdstappen van dezelfde acties, geen 100 onafhankelijke acties of nieuwe wedstrijdsituaties**. De visuele variatie blijft beperkt, vooral bij stilstaande ballen. Gebruik deze uitbreiding niet als onafhankelijke test voor een model dat op naburige frames is getraind. De bestaande tijdgroepen blijven volledig in hun oorspronkelijke split. Verdeel naburige beelden niet willekeurig over train en val. Alle beelden komen uit één wedstrijd; de tijdgroepen van train en val blijven ruim gescheiden.

| Tijdgroep | Tijd vanaf eerste videoframe | Split | Beelden |
| --- | --- | --- | ---: |
| phase-0540 | 542.20–556.12 s | val | 20 |
| phase-0750 | 755.80–769.00 s | train | 28 |
| phase-0960 | 968.84–971.92 s | train | 13 |
| phase-1170 | 1182.92–1191.96 s | train | 19 |
| phase-1380 | 1395.20–1397.56 s | train | 10 |
| phase-2010 | 2012.44–2022.68 s | val | 10 |

Persoonsrollen zijn overgenomen van nabijgelegen beoordeelde frames, waarna nieuwe YOLO11s-voorstellen op de oorspronkelijke resolutie zijn toegewezen aan de referentiepersonen. Vaste objecten zijn vanuit de vaste camera overgenomen; reserveballen zijn lokaal uitgelijnd. De volledige context is visueel gecontroleerd. Ontbrekende/ambigue persoonsvoorstellen en overlappende boxen zijn ook in detail bekeken en waar nodig gecorrigeerd. Enkele bordjes die als persoon waren overgenomen zijn verwijderd.

**Elke speelbal is afzonderlijk op de originele pixels visueel bekeken.** Foutieve voorstellen op handen, schoenen en veldlijnen zijn handmatig gecorrigeerd. Er zijn geen verborgen ballen op een vermoede positie gelabeld. Deze labels zijn AI-ondersteund; onafhankelijke menselijke review staat open. Er is voor deze uitbreiding geen nieuw model getraind en de controles vormen geen nauwkeurigheidsmeting of garantie op volledige semantische dekking.

## Herkomst, bestanden en controle

Bron: `128057_panorama_1st_half.mp4`, 25 fps, SHA-256 `3bc95a7bb31baec68be8d737e7b99fa083c595ba856e879106223a26548cbf23`. Tijd is frame-index / 25 vanaf het eerste gedecodeerde beeld; eerste video-PTS = 1 seconde. De video blijft lokaal. Alleen deze 100 opgeslagen frames zijn in deze uitbreiding geannoteerd, geen doorlopende video.

`source-annotations.json` bewaart pixelboxen, referentieframes en annotatiemethode. `manifest.json` bewaart bronindices, splits en beeldchecksums. `labels/` en `annotations.coco.json` bevatten de trainingslabels. `verification.json` controleert beeldidentiteit, nieuwe indices, boxgrenzen, YOLO/COCO-overeenkomst, tijdgroepsplits en de trainingsloader, ook voor de gecombineerde 346 beelden. `verification-in-play.json` controleert de aparte speelbalexport.

```powershell
python assets/annotations/football-fullscene100b/validate_dataset.py --source C:/Users/jorre/Downloads/128057_panorama_1st_half.mp4 --ultralytics-scan
python assets/annotations/football-fullscene100b/validate_in_play.py --output data/fullscene100b-in-play
python assets/annotations/football-fullscene100b/build_dataset.py --source C:/Users/jorre/Downloads/128057_panorama_1st_half.mp4 --output output/fullscene100b-reproduced
```
