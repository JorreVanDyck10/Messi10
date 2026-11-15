# YOLO26-spelersvergelijking

## Afgeronde ontwikkelmeting — 13 november 2026

| Spelersmodel | Gemiddelde pipeline-F1 over drie wedstrijden | Mediaan detectorstack |
|---|---:|---:|
| Huidig YOLO11s (`broadcast-pitch-players-v7`) | **91,81%** | **250,81 ms** |
| Opnieuw getraind YOLO11s | 91,62% | 251,18 ms |
| Opnieuw getraind YOLO26s | 91,45% | 252,67 ms |

Alle verschillen vallen binnen de afgesproken 0,5 procentpunt. Het huidige
model scoorde iets hoger en was ook iets sneller, en blijft daarom actief.
YOLO26 stopte met patience na epoch 24 (beste epoch 4); YOLO11 na epoch 31
(beste epoch 11). Geen kandidaat is automatisch geactiveerd. Andrew blijft
uitsluitend de bal leveren.

Dit is ontwikkelvalidatie met één trainingsseed. De losse detector is op 348
beelden gemeten; de pipeline op 341, omdat zeven beelden geen bruikbare
providergeometrie hadden. Detectorstacktijden sluiten rol/teamclassificatie,
videodecodering en veldherkenning uit. Het zijn geen volledige video-FPS.
De volledige lokale meetgegevens, curves, gewichten, hervatbare checkpoints
en video's staan in `artifacts/yolo26-players-20261113-v1/`.

## Werkwijze

Dit lokale experiment vergelijkt het actieve YOLO11-spelerscheckpoint met opnieuw
getrainde YOLO11s- en YOLO26s-modellen. Het vervangt alleen de spelersdetector;
Andrews checkpoint levert uitsluitend de bal. De persoonsvoorstellen, rollen,
teams, tracking en veldherkenning blijven gelijk. Kandidaten worden niet
automatisch standaard in de app.

## Omgeving en data

De aparte omgeving staat in `.tools/yolo26-env`, met Ultralytics 8.4.211 en
de bestaande PyTorch 2.6.0+cu124 / torchvision 0.21.0+cu124. Ze gebruikt dezelfde
lokale CUDA-packages via een `.pth`-verwijzing naar `.venv`; de gewone omgeving
blijft Ultralytics 8.3.221 gebruiken. Verplaats deze omgeving dus niet los van
de checkout. De concrete pakketversies staan in de experimentmap.

De bestaande `data/broadcast-multisource-v1` bevat 3.936 trainingsbeelden uit
zeven wedstrijden en 348 validatiebeelden uit drie andere wedstrijden.
Vooraf worden alle beeld- en labelhashes, labels en wedstrijdsplits gecontroleerd.
Gereserveerde testbeelden worden niet gebruikt. De eerder gebruikte validatieset
en één trainingsseed leveren ontwikkelmetingen, geen onafhankelijke eindtest.

De twee nieuwe modellen beginnen bij hun officiële COCO-startgewichten en
gebruiken 100 epochs als maximum, patience 20, seed 42, batch 1, resolutie 1536,
AdamW met lr 0,001, cosine learning rate, drie warm-upepochs, AMP en workers 0.
Na blijvend geheugentekort starten beide modellen opnieuw op 1280. De mislukte
1536-proef blijft bewaard en telt niet mee in de uiteindelijke vergelijking.

## Uitvoeren en hervatten

Voer deze commando's uit vanuit de projectmap. Lees eerst de huidige
Codex-accountlimieten via de beschikbare accounttool. Gebruik het laagste
resterende percentage van de toepasselijke vensters; neem niet een oud
percentage uit deze handleiding over.

```powershell
$python = '.\.tools\yolo26-env\Scripts\python.exe'
# Vervang 75 door het zojuist werkelijk uitgelezen resterende percentage.
& $python -m football_pipeline.yolo26_comparison --record-remaining 75
& $python -m football_pipeline.yolo26_comparison --phase all --resume
```

De standaarduitvoer staat in `artifacts/yolo26-players-20261113-v1`.
Met `--output` kies je een nieuwe experimentmap. Beschikbare fasen zijn
`prepare`, `train`, `evaluate`, `videos`, `report`, `all`, `status` en `pause`.
Een lock voorkomt gelijktijdige runners op dezelfde experimentmap.

Vernieuw de limietsnapshot ongeveer iedere vijf minuten en vóór grote fasen.
Bij 10% of minder begint geen nieuwe lange fase. Bij 5% of minder pauzeert
training na het volgende volledig opgeslagen epoch. Een snapshot ouder dan
vijftien minuten verhindert verdere uitvoering. Dit is een vangnet voor een
verdwenen begeleidende chat, geen vervanging van echte limietcontroles.
Als uitlezen mislukt, markeer de snapshot direct met `--record-unavailable`;
dan kan geen nieuwe lange fase beginnen.

```powershell
& $python -m football_pipeline.yolo26_comparison --phase pause
& $python -m football_pipeline.yolo26_comparison --phase status
```

Forceer geen processtop zolang een volledig checkpoint wordt opgeslagen.
`resume.pt` wordt gekopieerd vóór Ultralytics bij normale afsluiting optimizer-
en epochinformatie verwijdert. Bij hervatten worden die gegevens en de
datasetidentiteit gecontroleerd. `HANDOFF.md` bevat de stand en vervolgstappen.

## Metingen en kandidaat openen

Precision, recall en F1 gebruiken confidence 0,25 en matching-IoU 0,5. AP50 en
AP50–95 worden ook gerapporteerd, voor de losse detector en de pipeline, totaal
en per wedstrijd. De pipeline gebruikt vaste providergeometrie om spelerfouten
te onderscheiden van veldherkenningsfouten. De losse detector gebruikt een lage
confidencegrens voor de AP-curve; de pipeline behoudt zijn productiedrempels.

De modellen worden gerangschikt op gemiddelde F1 over de drie wedstrijden.
Binnen 0,5 procentpunt van het beste resultaat bepaalt de detectorsnelheid de
voorkeur. De snelheidstest gebruikt dezelfde 200 beelden, 30 opwarmbeelden,
drie herhalingen, batch 1 en expliciete CUDA-synchronisatie. De detectorstack-
meting bevat de vaste persoons- en baldetector, zonder videodecodering,
rol-/teamclassificatie of het veldnetwerk. Ze is dus geen volledige video-FPS.

`COMPARISON.md` en `comparison.json` bevatten de uitslag. Onder `evaluation`
staan de afzonderlijke metingen en foutvoorbeelden. De native trainingsmappen
bevatten de trainingscurves; `video-*.json` verwijst naar de uitvoervideo's.

```powershell
.\scripts\Start-Yolo26-Players.ps1 -Model yolo26s -Port 8502
# Alternatieven: -Model yolo11s of -Model current
```

Deze starter gebruikt de aparte omgeving. De gewone starter en het bestaande
standaardprofiel worden niet omgezet naar YOLO26.
