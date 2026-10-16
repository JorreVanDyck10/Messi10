# Sports Vision — data, modellen en tactical map

Deze repository bevat beide werkpakketten: persoon 1 beheert data, annotaties, training en detectie-evaluatie; persoon 2 beheert kalibratie, videopipeline, minimap en tracking.

**Gebruik een eigen lokale checkout en virtuele omgeving per werkpakket.** Persoon 1 gebruikt Python 3.12, `requirements.txt` en `requirements-lock.txt`; de geteste pipelineomgeving gebruikt Python 3.11 en `requirements.lock`. Installeer deze verschillende PyTorch-/Ultralytics-versies niet over elkaars `.venv` heen. `Setup-Persoon1.ps1` beheert de `.venv` van zijn eigen checkout.

- [Persoon 2: pipeline, minimap en tracking](#persoon-2-pipeline-minimap-en-tracking)
- [Persoon 1: data, annotaties, training en evaluatie](#persoon-1-data-annotaties-training-en-evaluatie)

De PANORIS-bronvideo van persoon 1 wordt via Git LFS gedeeld. De gezamenlijke acceptatie van de eerste technische kalibratieproef staat nog open. Datasetlabels, menselijke reviews en eindprestaties worden niet automatisch goedgekeurd door deze integratie.

**Eerste echte minimapproef:** bronframes 0–149 zijn inmiddels technisch gecontroleerd en volledig verwerkt. Zie [het PANORIS-pilotrapport](docs/PANORIS_Pilot.md) voor de video, kalibratiefouten, runtime en nog openstaande menselijke review. Reproduceren in de pipelineomgeving: `python scripts/panoris_pilot.py`. Deze technische pilot geldt niet als menselijke MVP-acceptatie.

## Persoon 2: pipeline, minimap en tracking

Een lokale Python-toepassing die detecties en een gekalibreerde minimap **in één gesynchroniseerde video** weergeeft. Streamlit verzorgt de invoer en weergave; de verwerkingspipeline werkt ook zonder interface.

Het project bevat de implementatie van het werkpakket van persoon 2. **De bronvideo van persoon 1 is beschikbaar via Git LFS; een geschikt fragment, definitieve spelersgewichten, handmatige trackingreferenties en gezamenlijke acceptatie voor de pipeline moeten nog worden bevestigd.** De meegeleverde demo bestaat uit synthetische testbeelden en is geen voetbalbenchmark. Er zijn geen mAP- of voetbaltrackingresultaten verzonnen.

### Snel starten op deze laptop

Voer vanuit de projectmap uit:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline doctor
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

De virtuele omgeving, CPU-dependencies, FFmpeg/ffprobe en `weights/yolo11n.pt` zijn lokaal voorbereid. Open de lokale URL die Streamlit toont. Het standaardmodel detecteert **personen** en een eventuele bal; het herkent nog geen spelers of scheidsrechters als afzonderlijke klassen.

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

Naast de handmatige modus is er **Automatische veldkalibratie**. Een afzonderlijke PnLCalib-omgeving herkent veldpunten en lijnen per frame; de minimap gebruikt de kalibratie van datzelfde frame. De vier buitenhoeken hoeven niet allemaal zichtbaar te zijn. Bij te weinig betrouwbare markeringen blijft de veldpositie onbekend. Spelertracking bij bewegende camera’s staat voorlopig uit.

Eenmalig met Python 3.11: `python scripts/setup_field_model.py`. Kies vervolgens de automatische modus na het uploaden van een MP4, vul videobron en toegelaten gebruik in en klik op **Verwerken**. Dit gebruikt een aparte omgeving en verandert de trainingsomgeving van persoon 1 niet. De bestaande spelersmodeloverdracht blijft gelden.

Zie [Automatische veldkalibratie](docs/Automatische_Veldkalibratie.md) voor CLI-gebruik, modelherkomst, technische proef, uitvoerformaat en onafhankelijke evaluatie. De implementatie en technische bruikbaarheid vormen geen bewijs van algemene nauwkeurigheid op wedstrijdbeelden.

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

De handmatige modus veronderstelt een vaste camera. De automatische modus herkalibreert per frame bij pan en zoom; lenscorrectie, teamherkenning, namen, baltracking en metrische snelheid vallen buiten deze pipeline. Het veld en zijn cirkel zijn schematisch; er worden geen echte veldafmetingen aangenomen. Het onderste boxmidden blijft bij overlap en springen een benadering.

Het team moet de eerste echte pilot gezamenlijk reviewen, de definitieve modellen leveren, 40–80 frames annoteren en onderling controleren, leakage beoordelen, echte mAP meten en trackingreferenties opstellen. Persoon 2 annoteert ongeveer de helft en reviewt de andere helft. Zie `docs/acceptance.md`, `docs/data_contract.md` en de logboeken voor de verdere overdracht en verdediging.

Ultralytics is een externe dependency met eigen licentievoorwaarden. Bewaar de bijbehorende licentie-informatie bij verspreiding van model/code. Raadpleeg de [officiële modeluitvoer](https://docs.ultralytics.com/modes/predict/), [trackingdocumentatie](https://docs.ultralytics.com/modes/track/) en [OpenCV-homography](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html) bij wijzigingen.

## Persoon 1: data, annotaties, training en evaluatie

Werkende hulpmiddelen voor video-inspectie, frame-extractie, assisted bounding-boxannotatie, datasetcontrole, YOLO-training en vergelijkbare detectie-evaluatie. De doellaptop heeft een **RTX 4050**. GPU en geheugen worden op die laptop opnieuw gecontroleerd.

De door de gebruiker gekozen [PANORIS-video](https://www.youtube.com/watch?v=HBTFZwMdcCw) staat volledig in `assets/videos/HBTFZwMdcCw.mp4`, op 3840 × 960 pixels, met bronmetadata en checksum. De MP4 wordt met **Git LFS** beheerd. De lokale ontwikkelmachine heeft een RTX 3050; metingen daarop gelden niet als 4050-benchmark.

### Starten op de 4050-laptop

Installeer Python **3.12**, Git met Git LFS en een werkende NVIDIA-driver. Gebruik voor iedere laptop een eigen projectomgeving; kopieer `.venv` niet van een andere machine.

Het werkpakket is geïntegreerd uit `feature/persoon1-data-model-evaluatie`. Maak voor de trainingsomgeving een eigen checkout van `main`:

```powershell
git clone --branch main https://github.com/JorreVanDyck10/Messi10.git
cd Messi10
```

Voer daar uit:

```powershell
git lfs install --local
git lfs pull
.\scripts\Setup-Persoon1.ps1
.\scripts\Start-Persoon1.ps1 -Mode prepare
.\scripts\Start-Persoon1.ps1 -Mode baseline -Split train
.\scripts\Start-Persoon1.ps1 -Mode annotate -Split train
```

Open daarna [de lokale annotatietool](http://127.0.0.1:8765) in je browser. De tool toont bronbeelden, automatische voorstellen, boxcorrectie en aparte review. Hij blijft alleen op de eigen computer bereikbaar. Stoppen kan met Ctrl+C in het terminalvenster.

Voor kleine objecten kun je in de annotatietool tot 800% inzoomen en door het vergrote beeld scrollen. Voor de bekeken panorama leverde een aanvullende pretrained proef op 1920 pixels meer bruikbare persoonsvoorstellen op. Je kunt die apart maken en laden:

```powershell
.\scripts\Start-Persoon1.ps1 -Mode baseline -Split train -InferenceSize 1920
.\scripts\Start-Persoon1.ps1 -Mode annotate -Split train -InferenceSize 1920
```

`InferenceSize` verandert alleen inference en de gekozen voorstellenmap; de eerste trainingsreferentie blijft 640. Meer voorstellen of hogere confidence bewijzen zonder referentielabels geen betere nauwkeurigheid.

Wanneer `python` naar een andere versie verwijst, gebruik je bijvoorbeeld `Setup-Persoon1.ps1 -Python 'C:\pad\naar\Python312\python.exe'`. Als PowerShell lokale scripts blokkeert, kun je één script starten met `powershell -ExecutionPolicy Bypass -File .\scripts\Setup-Persoon1.ps1`; dit wijzigt geen blijvend beleid.

Een bestaande uitvoermap wordt niet overschreven. Gebruik voor herhaalde baselines een nieuwe naam, bijvoorbeeld `-RunName baseline-train-640-02`. De annotatiestarter gebruikt standaard de voorstellen uit `runs/baseline-train-640/proposals`; voor een andere map gebruik je de CLI hieronder.

### Wat al is uitgevoerd en wat nog nodig is

Zie [de uitvoeringsstatus](docs/Status_Persoon_1.md) voor echte resultaten en resterende stappen. De oorspronkelijke [uitgebreide werkinstructie](docs/01_Persoon_1_Data_Model_Evaluatie.md) en [invulsjablonen](docs/Invulsjablonen_Persoon_1.md) staan naast de software.

De zestig geselecteerde beelden zijn **kandidaatframes**, nog geen goedgekeurde trainingsdataset. De eerste configuratie bevat `person` en `ball` om de baseline te onderzoeken. De definitieve target, klassendekking en keuze voor één of twee modellen moeten worden vastgelegd voordat training begint. De scripts verzinnen geen menselijke reviewers of modelprestaties.

De selectie is vóór modelinference vastgelegd: 36 trainframes uit zes tijdgroepen, 12 validatieframes uit twee groepen en 12 gereserveerde testframes uit twee groepen. Het zijn nieuwe momenten uit dezelfde opname, geen onafhankelijke wedstrijden. De genoemde tijdafstand is een controlehulpmiddel en bewijst op zichzelf geen onafhankelijkheid.

### Annoteren en reviewen

1. Voer de baseline uit op train en desgewenst val; voer geen ontwikkelbaseline uit op test.
2. Laad automatische voorstellen in de annotatietool, controleer gemiste objecten en corrigeer boxen en klassen.
3. Vul de echte annotatornaam in en bewaar. Een leeg frame moet expliciet als werkelijk negatief worden bevestigd.
4. Laat de andere persoon de bewaarde labels controleren en met een andere naam goedkeuren. Iedere wijziging maakt de oude review ongeldig.
5. Bewaar review en exportvoorbeelden voor het verslag. Onbeslisbare frames blijven buiten de definitieve scored dataset of worden door andere geschikte frames vervangen.

Testannotaties kunnen apart worden gemaakt met `-Mode annotate -Split test`. Gebruik de daarbij opgedane modelinzichten niet voor tuning; automatische modelinference op test vereist een latere systeemfreeze. De tool registreert namen en handelingen, maar verifieert geen menselijke identiteit.

Voor een eigen voorstellenmap:

```powershell
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest data/panoris/manifest.json --proposals runs/mijn-run/proposals --split train
```

### Datasetcontrole en training

```powershell
.\scripts\Start-Persoon1.ps1 -Mode validate
```

De controle geeft fouten bij ontbrekende labels, ongeldige boxen, directe overlap, te korte tijdafstand tussen subsets en ontbrekende onafhankelijke reviews. Nabije visuele duplicaten leveren een waarschuwing voor menselijke controle. Dat labels daadwerkelijk correct zijn, moet visueel worden beoordeeld.

Na de controles kopieer je `configs/approvals-example.json` naar `configs/approvals.json`. Vul alleen echte besluiten en de actuele `dataset_fingerprint` uit het validatierapport in. Beide teamleden moeten labels, splits, klassendekking, bron en modelrollen hebben beoordeeld. Deze voorbeeldgoedkeuring staat bewust standaard op onwaar.

```powershell
.\scripts\Start-Persoon1.ps1 -Mode train
```

De eerste trainingsinstellingen staan in `configs/train-reference.json`: pretrained YOLO11n, 640, batch 4, Adam, learning rate 0.001, maximaal 100 epochs en patience 20. Alleen CUDA-geheugentekort activeert de terugval naar batch 2 en vervolgens 1, steeds vanuit verse pretrained gewichten. Gewichten, werkelijke frameworkconfiguratie, logs en provenance blijven per poging bewaard. Testbeelden worden niet in de trainingsdataset opgenomen.

Een aparte technische proef kan met `python -m persoon1 train ... --smoke`; ook die vereist de echte datasetcontrole en is duidelijk als technische proef gemarkeerd. Een CPU-run is mogelijk met `--device cpu`, maar vormt een andere hardwaremeting.

### Evaluatie en foutenanalyse

Maak voor ieder model expliciet de mapping van **modelklassenaam** naar **datasetklassenaam**. Gebruik voor de pretrained referentie het voorbeeld met `person` en `sports ball`; pas de mapping aan de gekozen definitieve dataset aan. Bij een gespecialiseerde detector gebruik je de werkelijke klassen van dat model.

```powershell
.\.venv\Scripts\python.exe -m persoon1 predict --manifest data/panoris/manifest.json --weights models/yolo11n.pt --mapping configs/mapping-pretrained-example.json --output runs/baseline-val-640 --split val --device 0
.\.venv\Scripts\python.exe -m persoon1 evaluate --manifest data/panoris/manifest.json --predictions runs/baseline-val-640 --output runs/baseline-val-metrics
```

Gebruik voor een fine-tuned model een nieuwe uitvoermap en de bijpassende mapping. Vergelijk daarna:

```powershell
.\.venv\Scripts\python.exe -m persoon1 compare --baseline runs/baseline-val-metrics/metrics.json --candidate runs/fine-val-metrics/metrics.json --output reports/comparison.json
```

Beide modellen worden met **dezelfde evaluator** gemeten: 101-punts geïnterpoleerde box-AP bij IoU 0.50 tot 0.95. Dit is een expliciete projectmeting zonder crowd/ignore-regio's; het is geen claim dat de volledige COCO-benchmark is uitgevoerd. Klassen zonder geannoteerde objecten krijgen geen verzonnen nul-AP. De datasetcontrole verlangt voldoende klassendekking vóór training.

Het vaste confidencewerkpunt voor FP/FN staat los van de laag ingestelde confidence-ondergrens voor de AP-curve. Iedere evaluatie maakt `metrics.json`, `per-class.csv`, `errors.json` en `report.md`. De foutrecords bevatten echte mismatches; hun oorzaken moeten nog visueel worden vastgesteld. De vergelijking weigert verschillende labels, subsets, klassen of relevante inference-instellingen.

### Onafhankelijke eindtest

Leg na modelselectie een freeze vast op basis van de voltooide ontwikkelrun:

```powershell
.\.venv\Scripts\python.exe -m persoon1 freeze --manifest data/panoris/manifest.json --approvals configs/approvals.json --weights models/yolo11n.pt --inference runs/baseline-val-640/run.json --output reports/final-freeze.json
.\.venv\Scripts\python.exe -m persoon1 predict --manifest data/panoris/manifest.json --weights models/yolo11n.pt --mapping configs/mapping-pretrained-example.json --output runs/final-test --split test --freeze reports/final-freeze.json --approvals configs/approvals.json
.\.venv\Scripts\python.exe -m persoon1 evaluate --manifest data/panoris/manifest.json --predictions runs/final-test --output runs/final-test-metrics --freeze reports/final-freeze.json --approvals configs/approvals.json
```

Vervang de voorbeeldgewichten en mapping door de werkelijk geselecteerde configuratie. Dataset, model en inference moeten met de freeze overeenkomen. Testtoegang wordt bij de dataset vastgelegd. Gewijzigde configuraties krijgen niet opnieuw dezelfde beelden als onafhankelijke eindtest. Die discipline blijft ook een verantwoordelijkheid van het team; de bestanden zijn geen onveranderlijk extern auditregister.

### Overdracht en controles

Iedere inferentierun levert `detections.jsonl` met bronvideo-ID, oorspronkelijke frame-index, presentatietijd, beeldafmetingen en boxen in bronpixels. Ook een leeg detectieframe wordt geschreven. `run.json` bevat instellingen, gewichtenchecksum, beeldchecksums en de werkelijke omgeving. Voorstellen staan gescheiden van definitieve labels. Op geselecteerde beelden wordt geen volledige videoverwerking of volledige trackingclaim gebaseerd.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m persoon1 --help
```

De tests gebruiken herkenbaar synthetische fixtures en controleren onder meer AP met handmatig verifieerbare gevallen, dubbele matches, leakage, reviews, coördinaten, variabele framerate en semantische klassekoppeling. Testfixtures tellen niet mee als projectannotaties of trainingsresultaten.

Een extra volledige softwarecontrole van de GPU-trainingsroute is beschikbaar als `python -m persoon1.technical_check`. Die genereert uitsluitend synthetische rechthoeken, voert één epoch uit en bewaart een duidelijk als synthetisch gemarkeerd rapport. Die uitkomst bewijst geen prestatie op voetbalbeelden of geschiktheid van de echte annotaties.

De volledige video wordt via Git LFS gedeeld; de grote gegenereerde datasets, gewichten, lokale omgevingen en trainingsruns blijven buiten gewone commits. Reproduceer hun inhoud via de bronvideo, vastgelegde selectie, versies en manifests.
