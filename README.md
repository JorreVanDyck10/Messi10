> **Nieuwe verbeteringen (28 oktober 2026):** handmatige kalibratie werkt nu ook met een zichtbaar strafschopgebied; 33 providergevallen slagen voor de aparte puntcontrole. De optionele broadcastbal v3 verhoogt tegel-AP@50:95 van 23,34% naar 25,74%, met 36 gevonden labels en 5 in plaats van 12 ongekoppelde detecties op dezelfde ontwikkelset. De gekozen gewichten worden via Git LFS gedeeld. [Werking, metingen en beperkingen](docs/Verbeteringen_20261028.md).

> **Schoolversie (28 oktober 2026):** start met `scripts/Start-School.ps1` voor YOLO op volledige beelden, handmatige veldkalibratie en de minimap. De optionele baluitbreiding start met `-BroadcastTiles`. Er staat een bewerkbare set van 80 balbeelden klaar voor je eigen labelreview. [Starten, cursusbegrippen en voorbereiding op de verdediging](docs/Schoolversie_en_Verdediging.md).

> **Broadcastanalyse tijdelijk gepauzeerd (27 oktober 2026):** code, metingen, lokale checkpoints en hervatcommando’s staan in [de overdracht](docs/Broadcast_Hervatten.md). Start met `scripts/Resume-Broadcast.ps1 -Action status`. De nieuwe modelkeuze is nog niet definitief geactiveerd.
> **Broadcastbal v2 werkelijk getraind:** twaalf epochs op native crops en gecontroleerde negatieve voorbeelden. Op 73 ontwikkelbeelden met dezelfde 640-tegels stijgt AP@50:95 van **10,19% naar 23,34%**, met **23 → 36** gevonden ballabels en **33 → 12** ongekoppelde detecties bij confidence 0,25. Het optionele combinatieprofiel werkt met de bestaande spelersdetector. AI-labels, een kleine ontwikkelvalidatie en geen onafhankelijke eindtest. [Metingen, data en profielkeuze](docs/Broadcast_V2_Training.md).

> **Broadcastdata en labelcuratie:** 8.000 beelden uit 115 clips, met 118.012 speler-/doelmanboxen en 11.485 officialboxen. Aanvullend zijn 1.380 officialbeelden geselecteerd en is een balset van 132 bestaande beelden gecontroleerd, met twee gecorrigeerde boxen. Twijfelachtige labels blijven afgezonderd; 7.958 veldlabels voldoen aan de bestaande geometriecontrole. De taken hebben afzonderlijke trainingsconfiguraties en expliciete reviewbeperkingen. [Data, labelkwaliteit en trainingscommando](docs/Broadcast_Trainingsdata.md).

**Samengevoegd op 27 oktober 2026:** alle binnengekomen data-, rol- en balprofielen zijn behouden naast onderdeel 2 en 3. `Start-Spelermodel.ps1` en `configs/models-players.json` gebruiken spelermodel v3. Het afzonderlijke R007-profiel staat nu in `configs/models-roles-r007.json`; `Start-Wedstrijd.ps1` selecteert dat profiel voor de bestaande gezamenlijke rolproef. R009, R010, R015 en de balprofielen blijven afzonderlijk selecteerbaar. De berichten hieronder beschrijven hun oorspronkelijke metingen; hun vroegere standaardkeuzes gelden alleen voor die versie.

> **Spelermodel v3 (19 oktober 2026):** het nieuwe standaardmodel is getraind op drie wedstrijden en geselecteerd op twintig beelden uit drie andere wedstrijden. Spelers: AP@50 **93,17%**, AP@50:95 **58,98%**, recall **91,78%**, precision **80,48%** bij confidence 0,25. Officials blijven zwak; balherkenning wordt niet aangeboden. Dit is een kleine ontwikkelvalidatie met providerlabels, geen onafhankelijke eindtest. [Werkwijze volgens de cursus](docs/Modelverbetering_Volgens_Cursus.md), [modelkaart en exacte beperkingen](artifacts/players-v3/README.md). Het oude model is bewaard als `configs/models-players-v2.json`; algemene persoonsherkenning staat in `configs/models-persons.json`.

> **Baldetectie verder verbeterd:** verwerking in tegels behoudt baldetail. Op 51 volledige ontwikkelbeelden haalt het nieuwe F005-model met dezelfde tegelverwerking AP@50 75,70% en AP@50:95 37,88%, met meer correcte detecties én meer foutmeldingen. Nieuwe optionele profielen combineren dit met R007-rollen en Team A/B; de standaard blijft behouden. 238 tests en vier subtests slagen. [Resultaten, gebruik en beperkingen](docs/Verbetering_Baldetectie_Detailbehoud.md).

> **Werkpakket persoon 1 technisch uitgevoerd:** 93 extra rolcrops, data-audit, vijf echte roltrainingen, twee baltrainingen en een gecontroleerd R015-alternatief. De later ontvangen 56 panoramabeelden zijn gecontroleerd. De bal verbetert op native crops, maar alle drie gemeten modellen halen nul bal-AP op de nieuwe volledige validatiebeelden bij imgsz 1280. R007 blijft standaard; 225 tests en 4 subtests slagen. [Nieuwe resultaten en complete overdracht](docs/Uitvoering_Persoon_1_Derde_Ronde.md).

> **Samenwerken met drie personen:** de actuele taakverdeling geeft persoon 1 data en modellen, persoon 2 veldherkenning en projectie, en persoon 3 teams, tracking en integratie. Inclusief concrete taken, bestanden, overdrachten, review en acceptatie. [Werkverdeling voor drie personen](docs/Werkverdeling_3_Personen.md).

> **Teamindeling en dubbele boxen verbeterd:** de gezamenlijke rolpipeline houdt op dezelfde validatiebeelden vijf foutieve spelersdetecties minder over, met behoud van de correcte detecties. De kleurindeling voor nieuwe video's is opnieuw gemeten en aangepast. Deze softwareverbeteringen werken ook in het standaardprofiel R007. [Voor/na, voorbeelden en beperkingen](docs/Verbetering_Teams_en_Boxen.md).

> **Nieuwe dataronde uitgevoerd:** 111 extra rolcrops, twee echte roltrainingen en twee echte ballentrainingen. R009 verbetert spelers/officials, met afwegingen bij andere rollen; kies het met `scripts/Start-Wedstrijd.ps1 -Recognition roles-r009`. R007 blijft standaard. [Nieuwe metingen, fouten en reproductie](docs/Resultaten_Extra_Dataronde.md).

> **Samen starten:** `scripts/Start-Wedstrijd.ps1` selecteert rollen, Team A/B en automatische veldherkenning. De gezamenlijke pipeline is technisch uitgevoerd; herkenningsfouten en ontbrekende veldkalibratie blijven mogelijk. [Gezamenlijke controle, installatie en beperkingen](docs/Gezamenlijke_Integratie.md).

> **Rollen en teams toegevoegd:** kies het R007-rolprofiel of start met `scripts/Start-Spelermodel.ps1 -Recognition players`. Dit voert werkelijk getrainde aanvullende rol- en teamherkenning uit. Supporters en kleine officials blijven zwak. De op de 4050 gecontroleerde algemene persoonsherkenning van persoon 2 blijft de standaard voor zijn veldproef. [Echte rolmetingen en beperkingen](docs/Resultaten_Rollen_en_Teams.md).

De bestaande tweeklassen-P004-detector blijft de basis. Zijn historische speler-validatie is AP@50 74,50% en AP@50:95 26,55%; dit is geen score voor de volledige nieuwe rolpipeline. [Oorspronkelijke detectorresultaten](docs/Resultaten_Spelermodel.md).

**Veldherkenning blijft een beperking:** drie nieuwe trainingsopzetten zijn vergeleken. De beste validatiekandidaat presteerde slechter op de eigen ontwikkelclip en is afgewezen; de bestaande veldgewichten blijven actief. De definitieve combinatie met het nieuwe spelermodel is echt verwerkt en gecontroleerd. [Metingen en modelbeslissing](reports/course-improvement/README.md).

**Automatische uploadanalyse (19 oktober 2026):** start met `scripts/Start-Spelermodel.ps1` en upload een MP4. De app start zelf veldherkenning, het echte `player`/`referee`-model, ByteTrack met cameracompensatie en de gesynchroniseerde minimap met trajecten. Er zijn geen handmatige kalibratiepunten of acceptatiebestanden nodig. ID’s blijven bij ontbrekende veldherkenning op het beeld beschikbaar; veldposities en trajecten worden dan onderbroken. Camerawissels of onbetrouwbare bewegingsmetingen starten nieuwe ID’s. Deze technische ondersteuning is geen bewijs van onafhankelijke trackingnauwkeurigheid; de bekende detector- en veldbeperkingen blijven gelden.

Schakel **Alles automatisch analyseren na upload** uit voor de bestaande handmatige instellingen. Het standaardprofiel gebruikt nu het nieuwe speler-/officialmodel. Algemene persoonsherkenning blijft selecteerbaar. Voor CPU gebruik je expliciet `-Device cpu`; dit geldt ook voor het automatische spelersmodel. Het afzonderlijke veldmodel heeft zijn eigen runtimeconfiguratie.

De lokale combinatie van spelerherkenning en veldprojectie wordt beschreven in
[Spelerintegratie op de 4050](docs/Spelerintegratie_4050.md), inclusief de GPU-controle
en een herhaalbare integratiecheck op een volledige clip.

**Spelertelling en veldherkenning:** alleen voorspelde spelers met hun voetpunt binnen het geldige veld tellen mee. Andere rollen blijven afzonderlijk zichtbaar. Bij ontbrekende veldherkenning is het aantal onbekend. De aanvullende rolclassifier is echt getraind, maar kan nog verkeerde rollen geven. [Telregels en beperkingen](docs/Spelertelling_en_Rollen.md).

**Onderdeel 2, betrouwbaarheid (26 oktober 2026):** er is een afzonderlijk kandidaatprofiel met zichtbare veldgrenzen en controle van directe herkenning tegen camerabeweging. De volledige vergelijking op broadcast en PANORIS is uitgevoerd. De kandidaat blijft experimenteel en wordt niet standaard geactiveerd: menselijke referenties ontbreken en PANORIS levert nog onvoldoende veldpunten. [Werking, metingen en overdracht](docs/Veldherkenning_Betrouwbaarheid.md).

# Sports Vision — data, modellen en tactical map

## Gezamenlijke trainingsronde van 27 oktober

`scripts/Run-GezamenlijkeTraining.ps1` inventariseert de lokale gegevens per taak en voert de begrensde trainingen achter elkaar uit. Voltooide modelvergelijkingen worden bij hervatten hergebruikt. De ronde gebruikt maximaal vier uur GPU-training; gereserveerde testbeelden blijven buiten training en selectie.

Na de modelselectie start `scripts/Start-Gezamenlijk.ps1` het gezamenlijke profiel voor spelers, rollen, bal, teams, tracking en automatische veldherkenning. Een opgeslagen resultaat kun je rechtstreeks openen met `http://127.0.0.1:8501/?run=RUN_ID`, waarbij `RUN_ID` de volledige naam van een voltooide uitvoermap onder `runs` is.

De gegevensinventaris staat in `data/joint-local-20261027-v2/inventory.json`; configuraties, checkpoints, logs en vergelijkingen staan in `artifacts/joint-retrain-20261027-v2`. Het [vergelijkingsrapport](docs/Gezamenlijke_Training_20261027.md) wordt na de echte broadcast- en panoramademonstraties geschreven. Alleen kandidaten die aan hun vooraf vastgelegde validatiecriteria voldoen worden gekozen. Voorlopige AI-labels, menselijke review en onafhankelijke nauwkeurigheidsmetingen worden afzonderlijk gerapporteerd.

**Onderdeel 3, teams en toepassing (26 oktober 2026):** de automatische uploadanalyse
stelt nu twee teams op shirtkleur voor. De video en tactical map tonen dezelfde
teamkleuren en actuele telling per team, inclusief onbekend. Na analyse kun je
teamnamen, shirtprototypes en tijdelijke speler-ID’s corrigeren; dat maakt een
nieuwe uitvoer zonder nieuwe detectie, veldprojectie of tracking. Zie
[Teams, tracking en telling](docs/Teams_Tracking_en_Telling.md) voor gebruik,
CLI, bestanden en beperkingen. Dit is kleurindeling met technische tests;
menselijke team- en trackingnauwkeurigheid zijn nog niet gemeten.

Deze repository bevat beide werkpakketten: persoon 1 beheert data, annotaties, training en detectie-evaluatie; persoon 2 beheert kalibratie, videopipeline, minimap en tracking.

**Gebruik een eigen lokale checkout en virtuele omgeving per werkpakket.** Persoon 1 gebruikt Python 3.12, `requirements.txt` en `requirements-lock.txt`; de geteste pipelineomgeving gebruikt Python 3.11 en `requirements.lock`. Installeer deze verschillende PyTorch-/Ultralytics-versies niet over elkaars `.venv` heen. `Setup-Persoon1.ps1` beheert de `.venv` van zijn eigen checkout.

- [Persoon 2: pipeline, minimap en tracking](#persoon-2-pipeline-minimap-en-tracking)
- [Persoon 1: data, annotaties, training en evaluatie](#persoon-1-data-annotaties-training-en-evaluatie)

De PANORIS-bronvideo van persoon 1 wordt via Git LFS gedeeld. De gezamenlijke acceptatie van de eerste technische kalibratieproef staat nog open. Datasetlabels, menselijke reviews en eindprestaties worden niet automatisch goedgekeurd door deze integratie.

**Eerste echte minimapproef:** bronframes 0–149 zijn inmiddels technisch gecontroleerd en volledig verwerkt. Zie [het PANORIS-pilotrapport](docs/PANORIS_Pilot.md) voor de video, kalibratiefouten, runtime en nog openstaande menselijke review. Reproduceren in de pipelineomgeving: `python scripts/panoris_pilot.py`. Deze technische pilot geldt niet als menselijke MVP-acceptatie.

## Persoon 2: pipeline, minimap en tracking

Een lokale Python-toepassing die detecties en een gekalibreerde minimap **in één gesynchroniseerde video** weergeeft. Streamlit verzorgt de invoer en weergave; de verwerkingspipeline werkt ook zonder interface.

Het project bevat de implementatie van het werkpakket van persoon 2. **De bronvideo, 60 TeamTrack-beelden en werkelijk getrainde player/referee-gewichten zijn geleverd. De labelreview is door AI uitgevoerd; volledige officialdekking, handmatige trackingreferenties en gezamenlijke MVP-acceptatie blijven open.** De meegeleverde demo bestaat uit synthetische testbeelden en is geen voetbalbenchmark. Er zijn geen mAP- of voetbaltrackingresultaten verzonnen.

### Snel starten op deze laptop

Voer vanuit de projectmap uit:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline doctor
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

FFmpeg/ffprobe en de modelbestanden zijn lokaal voorbereid. Open de lokale URL die Streamlit toont. Het standaardprofiel gebruikt het geselecteerde `player`/`referee`-model v3 op GPU-device 0. Het afzonderlijke profiel `models-persons.json` toont algemene personen met onbekende rollen. Alleen echte spelerklassen ondersteunen spelertelling en spelertracking op basis van rol.

### Installeren op een tweede Windows-laptop

Vereist: Python 3.11, Git, PowerShell en internet tijdens installatie. Grote bestanden en de virtuele omgeving staan niet in Git.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
powershell -ExecutionPolicy Bypass -File scripts\setup_tools.ps1
.\.venv\Scripts\python.exe -m football_pipeline download-baseline
.\.venv\Scripts\python.exe -m football_pipeline doctor
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

`requirements.lock` bevat de geteste CPU-omgeving en de PyTorch CPU-package-index. Dit vervangt de trainingsomgeving van persoon 1 niet. Voor CUDA: maak een aparte omgeving, installeer de bij jullie driver passende officiële PyTorch-build en leg de volledige omgeving opnieuw vast. Verander dependencyversies gezamenlijk en voer de tests opnieuw uit.

FFmpeg wordt door het script in `.tools/` uitgepakt, zonder de systeembrede PATH te veranderen. De downloader gebruikt een Windows-build van BtbN, een provider op [ffmpeg.org/download.html](https://ffmpeg.org/download.html). Een nieuwe download kan een nieuwere build opleveren; runmanifesten bewaren de daadwerkelijk gebruikte versie. Voor identieke herhaling delen jullie dezelfde build en zijn SHA-256. Bestaande tools kunnen ook via PATH of `FOOTBALL_FFMPEG` en `FOOTBALL_FFPROBE` worden aangewezen.

### Een video verwerken via de interface (handmatige modus)

1. Kies een legaal te gebruiken `.mp4`, bij voorkeur een ontwikkelfragment van 30–60 seconden. Het volledige veld moet zichtbaar zijn, met vier hoeken en twee onafhankelijke controlepunten. De camera blijft vast: geen zoom, pan of camerawissel.
2. De toepassing controleert ieder frametijdstip, het beeldformaat en de videohash. Variabele framerate en rotatiemetadata worden afgewezen. Normaliseer zo nodig een kopie vooraf en kalibreer die nieuwe kopie opnieuw.
3. Kies **Linksboven**, **Rechtsboven**, **Rechtsonder** en **Linksonder** en klik telkens op de echte veldhoek in het referentiebeeld. De app vult oorspronkelijke pixelcoördinaten in en selecteert het volgende ontbrekende punt. Zoom tot 4× en gebruik de schuifbalken voor nauwkeuriger klikken. In deze handmatige workflow wordt de beeldoriëntatie gekoppeld aan de vaste veldhoeken `(0,0)`, `(1,0)`, `(1,1)`, `(0,1)`; die oriëntatie blijft gedurende de clip gelijk.
4. Klik **Middenlijn boven** en **Middenlijn onder**: waar de middenlijn de twee zijlijnen raakt, dus niet de middenstip. Dit zijn onafhankelijke controlepunten met veldposities `(0.5,0)` en `(0.5,1)`. Een schema staat onder **Waar horen de zes punten?**. Selecteer een punt opnieuw om het te verplaatsen; de puntentabel blijft beschikbaar voor precieze correcties. Bij een herkende PANORIS-bron of het exacte pilotfragment kun je **Pilotpunten invullen** gebruiken; die suggesties moeten nog visueel worden gecontroleerd en goedgekeurd.
5. Bereken de kalibratie. De terugprojectiefouten moeten aan de grenswaarden voldoen: mediaan ≤ 0,5% van de beelddiagonaal en maximum ≤ 1%.
6. Bekijk begin, midden en einde. Blijven de veldlijnen bij dezelfde markeringen? Bevestig de puntvolgorde, camera, reviewer, videobron en toegelaten gebruik. Download het kalibratierecord.
7. Klik op **Verwerken**. De uitvoer bevat één H.264-video van 1920 × 720, met links het beeld en rechts de minimap. Afspelen, pauzeren en zoeken gelden automatisch voor beide kanten.

Een kalibratie kan alleen worden geladen voor exact dezelfde cliphash en beeldafmetingen. De opgeslagen matrix en controlefouten worden opnieuw uit de puntparen berekend. Een ander bestand met dezelfde resolutie is geen bewijs van dezelfde camera.

### Automatische veldkalibratie bij pan en zoom

Naast de handmatige modus is er **Automatische veldkalibratie**. Een afzonderlijke PnLCalib-omgeving herkent veldpunten en lijnen per frame; de minimap gebruikt de kalibratie van datzelfde frame. De vier buitenhoeken hoeven niet allemaal zichtbaar te zijn. Bij te weinig betrouwbare markeringen blijft de veldpositie onbekend. Spelertracking gebruikt nu gemeten achtergrondbeweging voor cameracompensatie. Camerawissels en onbetrouwbare bewegingsmetingen starten nieuwe ID’s; onafhankelijke trackingnauwkeurigheid is nog niet bewezen.

Eenmalig met Python 3.11: `python scripts/setup_field_model.py`. Kies vervolgens de automatische modus na het uploaden van een MP4, vul videobron en toegelaten gebruik in en klik op **Verwerken**. Dit gebruikt een aparte omgeving en verandert de trainingsomgeving van persoon 1 niet. De bestaande spelersmodeloverdracht blijft gelden.

Zie [Automatische veldkalibratie](docs/Automatische_Veldkalibratie.md) voor CLI-gebruik, modelherkomst, technische proef, uitvoerformaat en onafhankelijke evaluatie. De implementatie en technische bruikbaarheid vormen geen bewijs van algemene nauwkeurigheid op wedstrijdbeelden.

Voor extra velddata en echte lokale fine-tuning op Windows: zie
[Veldmodeltraining](docs/Veldmodel_Training.md). Deze route verzamelt SoccerNet en
officiële highlights binnen 20 GiB, houdt ongecontroleerde voorstellen buiten de
training en vergelijkt eigen punten- en lijngewichten met de bestaande modellen.

De nieuwe [Broadcast-veldtest](docs/Broadcast_Veldexperiment.md) verbetert de
intern bruikbare kalibraties van 0 naar **252/1.239 frames (20,3%)** met gecontroleerde
veldpunten en korte overbrugging via optical flow. Dit blijft experimenteel;
menselijke projectiefouten en de 90%-doelstelling zijn nog open. Kies bovenaan
**Een opgeslagen veldtest visueel openen** om het bronbeeld, overlay en minimap
per exact frame te vergelijken, naar uitval te springen en eigen referenties op te slaan.

### Zonder interface werken

Hieronder zijn paden met `gekozen_clip` en `RUNMAP` voorbeelden die je vervangt door de echte bestanden.

```powershell
# Metadata en CFR controleren
.\.venv\Scripts\python.exe -m football_pipeline inspect data\gekozen_clip.mp4

# Vul in een kopie van configs/calibration_points.example.json echte pixelwaarden in.
# Controleer de punten vooraf op begin, midden en einde.
.\.venv\Scripts\python.exe -m football_pipeline calibrate data\gekozen_clip.mp4 configs\mijn_punten.json data\calibration.json --reviewer "Naam reviewer" --source "Videobron" --usage "Toegelaten gebruik" --confirm-static-camera

# Volledige verwerking
.\.venv\Scripts\python.exe -m football_pipeline process data\gekozen_clip.mp4 --calibration data\calibration.json --models configs\models.json --output runs
```

De CLI gebruikt dezelfde validatie en verwerkingsfunctie als Streamlit. Ruwe pixels worden eerst gedetecteerd en geprojecteerd; verkleinen en opvullen gebeuren alleen voor de weergave. De video behoudt iedere bronframe-index en de oorspronkelijke rationale framerate. Audio wordt weggelaten.

### Modeloverdracht en echte spelerklassen

De standaardconfiguratie staat in `configs/models.json`. Gewichtspaden zijn relatief aan dat manifest. Iedere semantische klasse heeft precies één modelleverancier. Zo kunnen spelers en een afzonderlijke data gap uit verschillende modellen komen.

Persoon 1 levert:

- geselecteerde gewichten met SHA-256 en een verwijzing naar de geëvalueerde run;
- werkelijke klasse-ID's en namen uit `model.names`;
- de gezamenlijke mapping naar bijvoorbeeld `player`, `referee`, `person`, `ball`;
- resolutie, confidence, NMS-IoU, device en dependencyversies;
- een ontwikkelclip met hash en voorbeelddetecties in oorspronkelijke beeldpixels;
- datasetversie, splitmanifest en afzonderlijke detectiemetrics.

Voorbeeld voor een **daadwerkelijk zo getraind** model:

```json
{
  "schema_version": 1,
  "profile_name": "Geselecteerde spelersdetector",
  "models": [{
    "model_id": "players_v1",
    "weights": "../weights/players_best.pt",
    "class_mapping": {"0": "player", "1": "referee"},
    "expected_names": {"0": "player", "1": "referee"},
    "imgsz": 640,
    "confidence": 0.10,
    "iou": 0.70,
    "device": "cpu"
  }]
}
```

Een optioneel veld `weights_sha256` wordt tegen het werkelijke bestand gecontroleerd. Zonder dat veld berekent en bewaart de pipeline de hash zelf. De adapter controleert ook of de opgegeven klassennamen overeenkomen met het geladen model. `person` mag niet naar `player` of `referee` worden omgezet. Een doelmanklasse mag wel naar de gezamenlijke spelerklasse worden gemapt.

De frontend heeft een keuzelijst **Modelprofiel** voor de profielen `configs/models*.json`. `FOOTBALL_MODELS` bepaalt het eerste aangeboden profiel en mag ook een extern manifest aanwijzen; `FOOTBALL_RUNS` stelt de uitvoermap in. Gewone gebruikers hoeven geen trainingsparameters in te voeren.

Nieuwe gelabelde data wordt eerst door persoon 1 gebruikt voor training en evaluatie. Daarna kan `register-player-model` de getrainde gewichten en expliciete klassemapping controleren en een profiel voor de frontend maken. Zie [de concrete overdracht naar spelertracking](docs/Spelermodel_Overdracht.md) voor de labelafspraken, het importcommando en de eerste trackingrun. ByteTrack is al aanwezig; een baseline met alleen `person` blijft uitgesloten van spelertracking.

### ByteTrack en waargenomen trajecten

Tracking is geïmplementeerd, maar blijft achter een expliciete MVP-acceptatie. Controleer eerst een echte modelrun zonder tracking: geometrie, begin/midden/einde, afspeelbaarheid, ontbrekende detecties en runtime. Een run met een synthetische of geïnjecteerde detector kan geen productieacceptatie krijgen.

```powershell
.\.venv\Scripts\python.exe -m football_pipeline accept-mvp runs\RUNMAP --reviewer "Naam reviewer" --confirm-review

.\.venv\Scripts\python.exe -m football_pipeline process data\gekozen_clip.mp4 --calibration data\calibration.json --models configs\players.json --tracker configs\bytetrack.yaml --mvp-acceptance runs\RUNMAP\mvp_acceptance.json
```

De acceptatie moet bij dezelfde video, kalibratie, gewichten, modelinstellingen, code en dependencies horen. Een wijziging daarvan vraagt een nieuwe gecontroleerde MVP-run. Alle betrokken bestanden moeten op de huidige laptop beschikbaar zijn.

De tracker ontvangt alleen `player` en wordt ieder bronframe bijgewerkt, ook bij nul detecties. De bronconfidence moet ≤ 0,10 én ≤ `track_low_thresh` zijn. Eerst een hoge schermdrempel toepassen zou de tweede matchingstap onbruikbaar maken; dat gebeurt hier niet. Een actuele match met lage confidence blijft met dezelfde ID zichtbaar op beeld en minimap.

De begininstellingen zijn `high=0.25`, `low=0.10`, `new=0.25`, `buffer=30`, `match=0.80` en `fuse_score=true`. In de geteste Ultralytics-versie 8.4.178 zijn 30 bufferupdates bij 25 fps gelijk aan 1,2 seconde. Dit is de effectieve instelling, geen garantie dat iedere occlusion dezelfde ID behoudt. Het runmanifest bewaart de werkelijke bufferwerking.

Kalmanvoorspellingen worden niet als veldwaarneming getekend. De adapter gebruikt de actuele detectie-index van ByteTrack en projecteert het onderste midden van die oorspronkelijke box. Trajecten omvatten maximaal vijf seconden. Een ontbrekende of ongeldige waarneming onderbreekt de lijn. Een verse clip krijgt een verse tracker.

### Detecties hergebruiken en tracking evalueren

Vergelijk trackerinstellingen op exact dezelfde opgeslagen detecties:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline process data\gekozen_clip.mp4 --calibration data\calibration.json --models configs\players.json --tracker configs\bytetrack.yaml --mvp-acceptance runs\MVP\mvp_acceptance.json --replay-run runs\MVP
```

Replay controleert de complete run, hashes, video, modelinstellingen, beeldschaal en iedere frame-index/tijdstempel. Alleen echte modeluitvoer kan als productie-replay worden gebruikt.

Maak voor drie ontwikkelfragmenten een handmatige referentie zoals `configs/tracking_reference.example.json`. Vul ieder frame van het onderzochte interval in, ook een frame met nul zichtbare spelers. Iedere speler heeft een door mensen vastgesteld `reference_id`, een `visible`-boolean en een box in oorspronkelijke pixels. Bij volledige occlusion is `visible=false`. De beoordeling gebruikt geen systeem-ID's als waarheid.

```powershell
.\.venv\Scripts\python.exe -m football_pipeline evaluate-tracking runs\TRACKING_RUN data\tracking_reference.json --output artifacts\tracking_evaluation.json
```

Er is één-op-één boxmatching bij IoU ≥ 0,5. De rapportage telt ID-wissels, ID-overnames, zichtbare onderbrekingen, gemiste zichtbare waarnemingen en onterechte trackwaarnemingen. ID-wissels en ID-overnames kunnen hetzelfde incident beschrijven: tel deze niet samen. Dit zijn projectspecifieke tellingen, geen IDF1/HOTA/MOTA. DetectiemAP wordt afzonderlijk door persoon 1 gerapporteerd.

### Uitvoer en foutgedrag

Elke uitvoering krijgt een eigen map met:

- `samengestelde_video.mp4`: uitsluitend aanwezig na geslaagde encoding en uitvoercontrole;
- `framegegevens.jsonl`: één record per frame, inclusief lege detectielijsten;
- `calibration.json`: de gebruikte puntparen en review;
- `controlebeelden/`: frame 0, midden en laatste frame;
- `runmanifest.json`: status, hashes, code-identiteit, omgeving, instellingen en metingen.

Een run wordt alleen hergebruikt bij dezelfde invoer, kalibratie, gewichten, instellingen, code, dependencies en toolversies. Ook de uitvoerhashes worden gecontroleerd. Beschadigde en mislukte runs blijven als bewijs bestaan en worden niet overschreven. Er draait één verwerking per uitvoermap; een OS-bestandslock komt bij procesbeëindiging vrij.

Ongeldige boxes worden geteld en krijgen geen punt. Personen buiten het veld, afgesneden voeten, een ongeldige homogene deler en posities buiten het veld krijgen een afwijsreden. Posities worden niet naar de rand getrokken. De bal wordt zichtbaar gedetecteerd indien het model hem vindt, maar krijgt geen grondprojectie: een bal kan in de lucht zijn.

De gemeten verwerkingstijd omvat modelladen, inference/replay, rendering, encoding en uitvoercontrole. De voorafgaande invoercontrole is een aparte voorbereidende stap. Proces-RAM wordt per frame bemonsterd; GPU-geheugen betreft PyTorch-allocaties indien CUDA beschikbaar is. Dit is geen algemene systeembrede geheugensensor.

### Technische controle en synthetische demo

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src streamlit_app.py scripts tests
.\.venv\Scripts\ruff.exe format --check src streamlit_app.py scripts tests
.\.venv\Scripts\python.exe -m football_pipeline demo
```

De demo maakt 20 frames, bevat een frame zonder detectie en produceert de volledige samengestelde H.264-uitvoer. De tests gebruiken daarnaast echte ByteTrack-matching en Streamlit AppTest. Een test van de trackingpipeline stubt uitsluitend de acceptatiegrens; dat is geen menselijke acceptatie of evaluatie op voetbalbeelden.

Voor een lokale YOLO-inferenceproef op een eigen afbeelding: `python scripts/smoke_model.py pad_naar_afbeelding.jpg`. Het rapport controleert klassensemantiek en oorspronkelijke coördinaten, niet mAP.

### Beperkingen en gezamenlijk vervolg

De handmatige modus veronderstelt een vaste camera. De automatische modus herkalibreert per frame bij pan en zoom; namen, baltracking en metrische snelheid vallen buiten deze pipeline. Teamindeling gebruikt shirtkleuren en biedt handmatige correcties; persoonlijke identiteit over camerawissels blijft onbekend. Het veld en zijn cirkel zijn schematisch; er worden geen echte veldafmetingen aangenomen. Het onderste boxmidden blijft bij overlap en springen een benadering.

Er zijn nu 60 gelabelde TeamTrack-beelden, getrainde gewichten en echte validatie-AP. Het team moet de eerste echte pilot gezamenlijk reviewen, de labels onafhankelijk menselijk beoordelen, een nieuwe onafhankelijke testgroep reserveren en trackingreferenties opstellen. De huidige officiallabels hebben beperkte dekking. Zie `docs/acceptance.md`, `docs/data_contract.md` en de logboeken voor de verdere overdracht en verdediging.

Ultralytics is een externe dependency met eigen licentievoorwaarden. Bewaar de bijbehorende licentie-informatie bij verspreiding van model/code. Raadpleeg de [officiële modeluitvoer](https://docs.ultralytics.com/modes/predict/), [trackingdocumentatie](https://docs.ultralytics.com/modes/track/) en [OpenCV-homography](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html) bij wijzigingen.

## Persoon 1: data, training, metingen en overdracht

- [Uitgevoerde spelerexperimenten en starten op de 4050](docs/Resultaten_Spelermodel.md): selectie, werkelijke scores, fouten, software, beperkingen en reproductiecommando's.
- [60 TeamTrack-beelden en hun labels](datasets/teamtrack-players-v2/README.md): 36 train, 12 validatie, 12 gereserveerd; 0=player inclusief doelmannen, 1=referee met beperkte dekking.
- [Getrainde gewichten](artifacts/players-v2/players_best.pt), [actief modelprofiel](configs/models-players.json), [overdrachtrecord](reports/players-experiments/handoff.json) en [geslaagde downloadcontrole](reports/players-experiments/remote-download-verification.json).
- De eerdere [balexperimenten](docs/Resultaten_Balexperimenten.md) en [PANORIS-werkwijze](docs/Persoon1_Handleiding.md) blijven apart bewaard. Hun kandidaatframes en negatieve balresultaten worden niet met de spelerdataset verward.

Vanuit de projectmap op de GPU-laptop:

```powershell
git pull --no-rebase origin main
git lfs pull
.\scripts\Setup-Persoon1.ps1
.\scripts\Start-Spelermodel.ps1
```

Gebruik `-Mode evaluate` om het bewaarde checkpoint op validatie na te meten, `-Mode annotate` om alle 60 beelden met boxen te bekijken en `-Mode train` om een nieuwe run van de geselecteerde configuratie te starten. Menselijke review en een onafhankelijke eindtest zijn niet als voltooid geregistreerd.
