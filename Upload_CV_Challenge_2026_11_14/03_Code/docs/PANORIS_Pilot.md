# Eerste echte PANORIS-minimapproef

**Uitgevoerd op 16 oktober 2026. Status: technische pilot geslaagd, menselijke review en MVP-acceptatie nog open.**

De eerste zes seconden van de gekozen PANORIS-video zijn verwerkt met echte YOLO11n-inference op ieder frame. De uitvoer toont bounding boxes links en de bijbehorende grondprojecties rechts in één H.264-video. Tracking en speleridentificatie staan uit.

## Resultaat openen en opnieuw uitvoeren

De lokale demonstratie staat in `artifacts/panoris-pilot/panoris-minimap-pilot.mp4`. Het controlebeeld staat daarnaast als `panoris-minimap-preview.jpg`. De volledige run, kalibratie, framegegevens en hashes staan onder `artifacts/panoris-pilot/runs/35b0ab30146495261d6ee446f1bb71ca0952e1544c9f3286813bb6c1ec2705d6/`.

Opnieuw uitvoeren vanuit de projectmap:

```powershell
# Alleen nodig wanneer de bron nog een LFS-pointer is:
git lfs pull --include="assets/videos/HBTFZwMdcCw.mp4" --exclude=""

# Gebruik de afzonderlijke pipelineomgeving, niet de trainingsomgeving van persoon 1.
.\.venv\Scripts\python.exe scripts\panoris_pilot.py
```

Het script controleert bronidentiteit, ontwikkelgroep, resolutie, frametijdlijn, cliphash en kalibratie. Een identieke voltooide run wordt op basis van hashes hergebruikt. `--prepare-only` bereidt uitsluitend het fragment en de bronbeelden voor. Kies `--output` met een nieuwe map als je een onafhankelijke herhaling zonder bestaande run wilt uitvoeren. Grote uitvoerbestanden blijven buiten gewone Git-commits.

## Bron en afbakening

| Onderdeel | Werkelijk gecontroleerd |
|---|---|
| Bron | PANORIS, `HBTFZwMdcCw`, opgegeven door de gebruiker |
| Bronbestand | 130.034.094 bytes; geregistreerde SHA-256 komt overeen |
| Resolutie | 3840 × 960, zonder ruimtelijke verkleining |
| Brontijdlijn | 3515 videoframes, constante intervallen van 0,04 seconde |
| Pilot | Bronframes 0 t/m 149, groep `dev-00`, split `train` |
| Clip | 150 frames, 25 fps, zes seconden; laatste frametijd 5,96 s |
| Afgeleide encoding | H.264, CRF 18; pixels zijn niet identiek aan de VP9-bron |
| Gereserveerde testgroepen | Geen inference of visuele beoordeling op de groepen vanaf 112 en 126 seconden |

De volledige bron is voor formaat- en tijdstempelcontrole gedecodeerd; alleen frames 0–149 zijn voor pilotinference en visuele analyse gebruikt. Bronvermelding en definitieve menselijke bevestiging van gebruik blijven onderdeel van de gezamenlijke oplevering.

Bron-SHA-256:

```text
7990708af29a660f089a204b9a39ad16c5ebf9063ed1eaf0ee325c01bbdda611
```

Clip-SHA-256:

```text
9baec79f611f7eae97ef484be181a2b426ea1c6b0ddeab03245afd7a96823836
```

## Geometrie: vier fitpunten en vijf onafhankelijke controles

De punten zijn door Codex visueel ingeschat op uitsneden op oorspronkelijke resolutie. Ze zijn **geen menselijke ground truth**. De oriëntatie is `u=0` bij het linker doel, `u=1` bij het rechter doel; `v=0` bij de verre zijlijn en `v=1` bij de nabije zijlijn. Er zijn geen metrische veldafmetingen aangenomen.

Vier veldhoeken bepalen de matrix. De vijf controles zijn niet gebruikt voor de schatting:

| Controlepunt op frame 0 | Terugprojectiefout in bronpixels |
|---|---:|
| Middenlijn bij verre zijlijn | 6,81 |
| Middenlijn bij nabije zijlijn | 12,97 |
| Middenstip | 3,75 |
| Doelmidden links | 3,44 |
| Doelmidden rechts | 4,84 |

De doelmiddens zijn benaderd uit de zichtbare grondcontacten van de doelpalen. Een geschatte klikonnauwkeurigheid van enkele pixels en perspectief beïnvloeden die controle.

De mediaan is **4,84 pixels**, het maximum **12,97 pixels**. De vooraf gebruikte grenzen zijn 19,79 pixels voor de mediaan en 39,58 pixels voor het maximum. Op frame 75 en 149 blijven de patchgebaseerde controlefouten eveneens onder die grenzen; de hoogste mediaan is 8,02 pixels.

Voor camerastabiliteit zijn vier hoeken en beide middenlijn-zijlijnpunten vergeleken met referentiepatches. Op begin, midden en einde is de grootste gemeten ankerverschuiving 1,41 pixels. De laagste correlatie is ongeveer 0,835. De technische drempels zijn minimaal 0,80 correlatie en maximaal 2 pixels verschuiving. Dit is een lokale cameracontrole, geen algemene garantie tegen iedere cameraverandering. Patches op egale lijnen en bij de doelmiddens zijn ambigu; daarom bepalen de aanvullende controlepunten niet zelfstandig de camerabeslissing.

**Beperking:** de nabije zijlijn wijkt bij het midden af van de rechte lijn tussen de gekozen hoeken. De grootste controlefout zit daar. Punten vlak langs de grens kunnen daardoor worden afgewezen. De implementatie past geen clipping, randcorrectie of niet-geteste panoramarectificatie toe. Een geslaagde controle op deze punten bewijst geen nauwkeurigheid in meters of op ieder veldpunt.

## Werkelijke detectie en uitvoer

Het afzonderlijke profiel `configs/models-panoris-pilot-1920.json` gebruikt `yolo11n.pt`, `imgsz=1920`, confidence 0,10 en NMS-IoU 0,70 op CPU. De standaardconfiguratie op 640 en de trainingsinstellingen van persoon 1 zijn niet gewijzigd. De softwareversies van beide personen verschillen; deze pilot claimt geen exact identieke voorspellingen aan de eerdere baseline van persoon 1.

| Resultaat | Meting |
|---|---:|
| Invoer- en uitvoerframes | 150 / 150 |
| Uitvoervideo | H.264, 1920 × 720, 25 fps |
| Verwerkingstijd | 26,13 s |
| Verwerkingssnelheid | 5,74 fps |
| Proces-RAM, per frame bemonsterd | 678,34 MiB |
| Persoonsdetecties bij confidence ≥ 0,10 | 3810 over alle frames |
| Geldige persoonsprojecties bij die drempel | 3009 |
| Persoonsdetecties buiten het veldpolygon | 801 |
| Baldetecties zonder grondprojectie | 24 |

De tijd omvat modelladen, inference, rendering, encoding en uitvoercontrole, maar niet de voorafgaande bron-/clipvoorbereiding. De aantallen zijn detectiewaarnemingen over frames, geen unieke personen, true positives, false positives of mAP. De 24 balvoorspellingen zijn nog niet met menselijke labels gecontroleerd.

De weergavedrempel blijft 0,25. Daarboven zijn per frame 10–23 persoonsboxes en 7–19 geldige veldpunten zichtbaar. Personen buiten het veld blijven op de videokant staan. Een ballende speler, scheidsrechter of medewerker blijft semantisch `person`; er worden geen spelersnamen, teams of track-ID's toegekend.

## Visuele controle en concrete aandachtspunten

| Frame | Tijd | Getoonde persoonsboxes | Getoonde veldpunten |
|---|---:|---:|---:|
| 0 | 0,00 s | 17 | 13 |
| 75 | 3,00 s | 15 | 11 |
| 149 | 5,96 s | 22 | 18 |

Begin, midden en einde zijn visueel bekeken: dezelfde frame-index en tijd staan op beide helften. Alle JSONL-records hebben de oorspronkelijke beeldafmetingen en correcte tijdstempels. Er zijn geen track-ID's, balprojecties of veldpunten bij afgewezen projecties.

De gecontroleerde voorbeelden onderscheiden:

- **Personen langs de nabije zijlijn:** op frame 0 blijven detecties `0:0`, `0:1` en `0:5` zichtbaar zonder minimappunt. Dat is de veldfiltering; het zijn niet automatisch detectiefouten.
- **Een persoon vlak langs de verre grens:** detectie `0:15` wordt buiten het polygon geplaatst. De boxonderkant en hoekkeuze zijn hier gevoelig voor enkele pixels. Menselijke beoordeling moet aangeven of het een detectie-, projectie- of geldig grensgeval is.
- **Kleine personen zonder getoonde box:** op frame 0 zijn kleine personen zichtbaar waarvoor de weergave niet volledig is. De confidencegrens en gemiste detecties zijn afzonderlijke mogelijke oorzaken; zonder labels tellen we geen false negatives.
- **Dicht bij elkaar staande personen:** op frame 149 overlappen verschillende labels/boxes. Boxlokalisatie, mogelijke duplicaten en voetpunten moeten worden gereviewd. Er is bewust nog geen identiteitskoppeling.

Er kwam geen volledig detectieloos frame voor in dit voetbalfragment. De bestaande tests controleren dat zo'n frame geen oude posities hergebruikt; voor deze pilot worden geen ontbrekende waarnemingen opgevuld.

De voorbeelden, hypothesen en volgende controles staan gestructureerd in `reports/panoris-pilot-observations.json`. Het zijn technische observaties, geen formeel beoordeelde foutencatalogus.

## Technische pilot en menselijke acceptatie blijven onderscheiden

De pipeline heeft nu de expliciete optie `technical_pilot=True`, ook beschikbaar als CLI-vlag `--technical-pilot`. De standaardroute blijft een goedgekeurde kalibratie vereisen. De pilotroute vereist opnieuw berekende geometrie en een expliciet technisch reviewrecord; zij accepteert geen tracking of replay.

De video heeft een pilotbanner. Het runmanifest is gemarkeerd als `ultralytics_technical_pilot`, de kalibratie bewaart `approved=false` en `human_reviewed=false`. `accept-mvp` weigert deze uitvoer. Er is dus geen menselijke goedkeuring nagebootst om de verwerking te laten slagen.

De complete suite slaagt: **70 tests en 4 subtests**, plus lint en formaatcontrole. De 33 bestaande Pillow-deprecatiewaarschuwingen uit de tests van persoon 1 blijven zichtbaar. Nieuwe tests controleren onder meer cameraverschuiving, afwijzing bij slechte geometrie, expliciete technische evidence, blokkeren van tracking en het behoud van de menselijke acceptatiegrens.

## Wat jullie nu samen beoordelen

1. Bekijk de zes seconden en de drie geometriebeelden. Controleer hoekvolgorde, middenlijn, doelmiddens en de afwijking aan de nabije zijlijn.
2. Controleer de genoemde grensgevallen en noteer welke personen werkelijk op het speelveld staan.
3. Bevestig met persoon 1 of video, splits, klassen, gewichtshashes of uitvoerformaat door zijn aanpassingen veranderen.
4. Leg pas daarna een echte gezamenlijke kalibratie-/MVP-review vast. De lijst met puntparen staat lokaal als `artifacts/panoris-pilot/point-correspondences.json`; die kan na werkelijke visuele review aan het bestaande CLI-commando `calibrate` worden gegeven, met de echte reviewer en bronafspraken.
5. Breid vervolgens uit naar andere ontwikkelfragmenten. ByteTrack wacht op de MVP-acceptatie en werkelijk beschikbare spelerklassen; gereserveerde testgroepen blijven buiten die afstemming.
