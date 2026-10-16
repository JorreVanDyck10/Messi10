# Voetbalvideo → tactical map

Een lokale Python-toepassing die detecties en een gekalibreerde minimap **in één gesynchroniseerde video** weergeeft. Streamlit verzorgt de invoer en weergave; de verwerkingspipeline werkt ook zonder interface.

Het project bevat de implementatie van het werkpakket van persoon 2. **Een echte voetbalvideo, definitieve spelersgewichten, handmatige trackingreferenties en gezamenlijke acceptatie moeten nog door het team worden aangeleverd.** De meegeleverde demo bestaat uit synthetische testbeelden en is geen voetbalbenchmark. Er zijn geen mAP- of voetbaltrackingresultaten verzonnen.

## Snel starten op deze laptop

Voer vanuit de projectmap uit:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline doctor
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

De virtuele omgeving, CPU-dependencies, FFmpeg/ffprobe en `weights/yolo11n.pt` zijn lokaal voorbereid. Open de lokale URL die Streamlit toont. Het standaardmodel detecteert **personen** en een eventuele bal; het herkent nog geen spelers of scheidsrechters als afzonderlijke klassen.

## Installeren op een tweede Windows-laptop

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

## Een video verwerken via de interface

1. Kies een legaal te gebruiken `.mp4`, bij voorkeur een ontwikkelfragment van 30–60 seconden. Het volledige veld moet zichtbaar zijn, met vier hoeken en twee onafhankelijke controlepunten. De camera blijft vast: geen zoom, pan of camerawissel.
2. De toepassing controleert ieder frametijdstip, het beeldformaat en de videohash. Variabele framerate en rotatiemetadata worden afgewezen. Normaliseer zo nodig een kopie vooraf en kalibreer die nieuwe kopie opnieuw.
3. Voer de vier veldhoeken in oorspronkelijke pixels in. De vaste volgorde is `(0,0)`, `(1,0)`, `(1,1)`, `(0,1)`. Benoem welke echte veldhoek daarbij hoort; beeldbovenkant en veldoriëntatie zijn niet automatisch hetzelfde.
4. Voer twee onafhankelijke controlepunten in: de middenlijn op beide zijlijnen, met veldposities `(0.5,0)` en `(0.5,1)`. Gebruik deze punten niet opnieuw als fitpunten.
5. Bereken de kalibratie. De terugprojectiefouten moeten aan de grenswaarden voldoen: mediaan ≤ 0,5% van de beelddiagonaal en maximum ≤ 1%.
6. Bekijk begin, midden en einde. Blijven de veldlijnen bij dezelfde markeringen? Bevestig de puntvolgorde, camera, reviewer, videobron en toegelaten gebruik. Download het kalibratierecord.
7. Klik op **Verwerken**. De uitvoer bevat één H.264-video van 1920 × 720, met links het beeld en rechts de minimap. Afspelen, pauzeren en zoeken gelden automatisch voor beide kanten.

Een kalibratie kan alleen worden geladen voor exact dezelfde cliphash en beeldafmetingen. De opgeslagen matrix en controlefouten worden opnieuw uit de puntparen berekend. Een ander bestand met dezelfde resolutie is geen bewijs van dezelfde camera.

## Zonder interface werken

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

## Modeloverdracht en echte spelerklassen

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

Voor een ander interfaceprofiel, stel vóór het starten bijvoorbeeld `$env:FOOTBALL_MODELS = 'C:\pad\models.json'` in. `FOOTBALL_RUNS` stelt de uitvoermap in. Dit zijn voorbereidingsinstellingen; gewone gebruikers hoeven geen trainingsparameters in te voeren.

## ByteTrack en waargenomen trajecten

Tracking is geïmplementeerd, maar blijft achter een expliciete MVP-acceptatie. Controleer eerst een echte modelrun zonder tracking: geometrie, begin/midden/einde, afspeelbaarheid, ontbrekende detecties en runtime. Een run met een synthetische of geïnjecteerde detector kan geen productieacceptatie krijgen.

```powershell
.\.venv\Scripts\python.exe -m football_pipeline accept-mvp runs\RUNMAP --reviewer "Naam reviewer" --confirm-review

.\.venv\Scripts\python.exe -m football_pipeline process data\gekozen_clip.mp4 --calibration data\calibration.json --models configs\players.json --tracker configs\bytetrack.yaml --mvp-acceptance runs\RUNMAP\mvp_acceptance.json
```

De acceptatie moet bij dezelfde video, kalibratie, gewichten, modelinstellingen, code en dependencies horen. Een wijziging daarvan vraagt een nieuwe gecontroleerde MVP-run. Alle betrokken bestanden moeten op de huidige laptop beschikbaar zijn.

De tracker ontvangt alleen `player` en wordt ieder bronframe bijgewerkt, ook bij nul detecties. De bronconfidence moet ≤ 0,10 én ≤ `track_low_thresh` zijn. Eerst een hoge schermdrempel toepassen zou de tweede matchingstap onbruikbaar maken; dat gebeurt hier niet. Een actuele match met lage confidence blijft met dezelfde ID zichtbaar op beeld en minimap.

De begininstellingen zijn `high=0.25`, `low=0.10`, `new=0.25`, `buffer=30`, `match=0.80` en `fuse_score=true`. In de geteste Ultralytics-versie 8.4.178 zijn 30 bufferupdates bij 25 fps gelijk aan 1,2 seconde. Dit is de effectieve instelling, geen garantie dat iedere occlusion dezelfde ID behoudt. Het runmanifest bewaart de werkelijke bufferwerking.

Kalmanvoorspellingen worden niet als veldwaarneming getekend. De adapter gebruikt de actuele detectie-index van ByteTrack en projecteert het onderste midden van die oorspronkelijke box. Trajecten omvatten maximaal vijf seconden. Een ontbrekende of ongeldige waarneming onderbreekt de lijn. Een verse clip krijgt een verse tracker.

## Detecties hergebruiken en tracking evalueren

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

## Uitvoer en foutgedrag

Elke uitvoering krijgt een eigen map met:

- `samengestelde_video.mp4`: uitsluitend aanwezig na geslaagde encoding en uitvoercontrole;
- `framegegevens.jsonl`: één record per frame, inclusief lege detectielijsten;
- `calibration.json`: de gebruikte puntparen en review;
- `controlebeelden/`: frame 0, midden en laatste frame;
- `runmanifest.json`: status, hashes, code-identiteit, omgeving, instellingen en metingen.

Een run wordt alleen hergebruikt bij dezelfde invoer, kalibratie, gewichten, instellingen, code, dependencies en toolversies. Ook de uitvoerhashes worden gecontroleerd. Beschadigde en mislukte runs blijven als bewijs bestaan en worden niet overschreven. Er draait één verwerking per uitvoermap; een OS-bestandslock komt bij procesbeëindiging vrij.

Ongeldige boxes worden geteld en krijgen geen punt. Personen buiten het veld, afgesneden voeten, een ongeldige homogene deler en posities buiten het veld krijgen een afwijsreden. Posities worden niet naar de rand getrokken. De bal wordt zichtbaar gedetecteerd indien het model hem vindt, maar krijgt geen grondprojectie: een bal kan in de lucht zijn.

De gemeten verwerkingstijd omvat modelladen, inference/replay, rendering, encoding en uitvoercontrole. De voorafgaande invoercontrole is een aparte voorbereidende stap. Proces-RAM wordt per frame bemonsterd; GPU-geheugen betreft PyTorch-allocaties indien CUDA beschikbaar is. Dit is geen algemene systeembrede geheugensensor.

## Technische controle en synthetische demo

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src streamlit_app.py scripts tests
.\.venv\Scripts\ruff.exe format --check src streamlit_app.py scripts tests
.\.venv\Scripts\python.exe -m football_pipeline demo
```

De demo maakt 20 frames, bevat een frame zonder detectie en produceert de volledige samengestelde H.264-uitvoer. De tests gebruiken daarnaast echte ByteTrack-matching en Streamlit AppTest. Een test van de trackingpipeline stubt uitsluitend de acceptatiegrens; dat is geen menselijke acceptatie of evaluatie op voetbalbeelden.

Voor een lokale YOLO-inferenceproef op een eigen afbeelding: `python scripts/smoke_model.py pad_naar_afbeelding.jpg`. Het rapport controleert klassensemantiek en oorspronkelijke coördinaten, niet mAP.

## Beperkingen en gezamenlijk vervolg

Automatische camerabewegingsdetectie, lenscorrectie, teamherkenning, namen, baltracking, metrische snelheid en training vallen buiten deze implementatie. Het veld en zijn cirkel zijn schematisch; er worden geen echte veldafmetingen aangenomen. Het onderste boxmidden blijft bij overlap en springen een benadering.

Het team moet nog de echte video kiezen en reviewen, de definitieve modellen leveren, 40–80 frames annoteren en onderling controleren, leakage beoordelen, echte mAP meten en trackingreferenties opstellen. Persoon 2 annoteert ongeveer de helft en reviewt de andere helft. Zie `docs/acceptance.md`, `docs/data_contract.md` en de logboeken voor de verdere overdracht en verdediging.

Ultralytics is een externe dependency met eigen licentievoorwaarden. Bewaar de bijbehorende licentie-informatie bij verspreiding van model/code. Raadpleeg de [officiële modeluitvoer](https://docs.ultralytics.com/modes/predict/), [trackingdocumentatie](https://docs.ultralytics.com/modes/track/) en [OpenCV-homography](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html) bij wijzigingen.
