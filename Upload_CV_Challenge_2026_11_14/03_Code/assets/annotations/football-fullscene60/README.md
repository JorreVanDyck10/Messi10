# 60 extra volledige frames, met nadruk op de speelbal

Deze uitbreiding bevat **60 nieuwe, volledige PNG-beelden van 4096 × 1080 pixels**, met **2.969 boxen**. In elk beeld is één zichtbare speelbal gelabeld. De invoerbeelden zijn pixelgelijk aan de gedecodeerde bronvideo: zonder uitsnede, masker, vergroting of ingetekende boxen. Alleen de aparte `previews/` bevatten tekeningen.

## Downloaden en speelballen trainen

Voer vanuit de repository uit:

```powershell
git pull
git lfs pull
python assets/annotations/football-fullscene60/make_in_play_dataset.py --output data/fullscene60-in-play
```

Gebruik vervolgens `data/fullscene60-in-play/data.yaml` voor **uitsluitend de speelbal**: klasse 0 = `in_play_ball`, 40 trainbeelden en 20 validatiebeelden, precies één box per beeld. Deze export gebruikt dezelfde volledige PNG's. Reserveballen zijn hier bewust achtergrond en krijgen geen positief label. Er zijn geen uitsneden nodig; de oorspronkelijke video is voor deze export niet nodig. Kies bij herhaling een nieuwe uitvoermap.

Een stilstaande bal bij een spelhervatting telt ook als speelbal. De selectie bevat kleine ballen op afstand, rollende/vliegende ballen en ballen bij spelers en keepers. Verborgen ballen zijn niet op hun vermoedelijke positie gelabeld; vier oorspronkelijke kandidaten zijn vervangen door frames met zichtbare bal. Witte veldmarkeringen, schoenen en reserveballen zijn afzonderlijk gecontroleerd.

## Volledige scène

De standaard `data.yaml` bevat dezelfde beelden met acht klassen. In deze algemene objectdetectietaak zijn ook herkenbare reserveballen positief voor klasse `ball`. **Gebruik dus de bovenstaande aparte export wanneer je alleen de speelbal wilt trainen.** De bronannotaties en COCO-export bewaren het onderscheid met `kind: in_play_ball` en `kind: reserve_ball`.

| YOLO | Klasse | Boxen |
| ---: | --- | ---: |
| 0 | player | 1.285 |
| 1 | ball | 320: 60 speelballen en 260 reserveballen |
| 2 | referee | 120 |
| 3 | other_person | 344 |
| 4 | crowd | 180 groepen |
| 5 | goal | 360 |
| 6 | corner_flag | 240 |
| 7 | stored_goals | 120 groepen |

Spelers omvatten beide ploegen en keepers. Onduidelijke personenrollen vallen onder `other_person`. Dichte publieks-/bankgroepen en stapels opgeborgen doelen hebben groepsboxen, zonder geschat ledenaantal. De zes afzonderlijke fysieke doelen per frame omvatten twee wedstrijddoelen en vier losse trainingsdoelen; overlappende doelstapels hebben twee aparte groepsboxen. De geschilderde doelvorm op de groene wand is geen fysiek doel. COCO gebruikt klasse-ID's 1–8 en pixelcoördinaten; YOLO gebruikt 0–7 en genormaliseerde coördinaten. Groepsboxen zijn gewone detectieklassen, geen genegeerde regio's.

Voor alle acht klassen samen met de vorige 16 + 20 + 50 scènes is `data-combined146.yaml` beschikbaar: **146 unieke bronframes, 105 train en 41 val**. Oudere labels zijn niet opnieuw semantisch beoordeeld voor het onderscheid speelbal/reservebal; ze worden niet geïmporteerd in de nieuwe speelbalexport.

## Herkomst en splits

Bron: `128057_panorama_1st_half.mp4`, 25 fps. SHA-256: `3bc95a7bb31baec68be8d737e7b99fa083c595ba856e879106223a26548cbf23`. Tijd = frame-index / 25, vanaf het eerste gedecodeerde beeld; de eerste video-PTS is 1 seconde. De bronvideo blijft lokaal.

| Tijdgroep | Selectie in seconden | Split | Beelden |
| --- | --- | --- | ---: |
| phase-0540 | 542,80–556,40 | val | 10 |
| phase-0750 | 756,40–768,40 | train | 10 |
| phase-0960 | 969,12–971,36 | train | 10 |
| phase-1170 | 1183,52–1191,36 | train | 10 |
| phase-1380 | 1395,52–1397,12 | train | 10 |
| phase-2010 | 2012,80–2022,40 | val | 10 |

Alle bronindices zijn nieuw tegenover de eerdere vijf trainingsselecties. De bestaande tijdgroepsplits blijven behouden; tussen train en val zit hier minimaal 200 seconden. Er zijn bewust naburige frames rondom zichtbare balacties geselecteerd, soms slechts 0,04–0,16 seconde uit elkaar. Dit zijn **geen 60 onafhankelijke acties**. Alle beelden komen uit dezelfde wedstrijd; deze splits vormen geen onafhankelijke wedstrijdtest. Verdeel naburige frames niet willekeurig over train en val.

## Controle en bestanden

`source-annotations.json` bewaart de visuele selecties en pixelboxen. `manifest.json` bevat bronindices, splits en beeldchecksums. `labels/` en `annotations.coco.json` zijn de YOLO- en COCO-exports. `summary.json`, `verification.json` en `verification-in-play.json` bevatten aantallen en technische controles. De volledige context, individuele persoonvoorstellen en balboxen zijn door Codex visueel bekeken op de bronbeelden; dit zijn AI-ondersteunde annotaties en **onafhankelijke menselijke review staat open**. Technische controles meten geen labelnauwkeurigheid. Er is voor deze uitbreiding geen model getraind.

Reproduceren en controleren met de oorspronkelijke video:

```powershell
python assets/annotations/football-fullscene60/validate_dataset.py --source C:/Users/jorre/Downloads/128057_panorama_1st_half.mp4 --ultralytics-scan
python assets/annotations/football-fullscene60/build_dataset.py --source C:/Users/jorre/Downloads/128057_panorama_1st_half.mp4 --output output/fullscene60-reproduced
```

De validator controleert beeldidentiteit, nieuwe indices, boxgrenzen, exportovereenkomst, groepssplits en de trainingsloader. De volledige video heeft geen doorlopende frame-annotaties: alleen de 60 opgeslagen frames zijn in deze uitbreiding gelabeld.
