# Spelerboxen bij velduitval en gerichte veldtraining — 30 oktober 2026

## Werking en nulmeting

De automatische broadcastpipeline houdt actuele spelerboxen en beeldtracking
beschikbaar wanneer de veldkalibratie ontbreekt. De veldtelling, minimap en
afstanden blijven dan onbekend. Een onderbreking wordt niet met verzonnen
veldposities gevuld. Bestaande cameracompensatie en resets bij camerawissels
blijven actief. Bekende buitenveldspelers en andere rollen worden niet door
deze wijziging als veldspeler getoond.

De gebruiker leverde `samengestelde_video.mp4` aan. Zijn bestand is bytegelijk
aan de oorspronkelijke uitvoer van run
`cdbccee936a74aecbffd40d557e573318a634d7ca6e1688f25bee4a8f3da277e`.
De analyse gebruikt de oorspronkelijke upload van 1920 × 1080 en zijn opgeslagen
waarnemingen; de samengestelde uitvoer wordt niet opnieuw aan modellen aangeboden.

| Nulmeting op deze clip van 30 seconden | Uitkomst |
|---|---:|
| Bronframes | 750 |
| Beschikbare veldprojectie | 455 (60,67%) |
| Ontbrekende veldprojectie | 295 (39,33%) |
| Afzonderlijke uitvalmomenten | 77 |
| Totale uitvalduur | 11,80 s |
| Langste aaneengesloten uitval | 1,68 s |
| Zichtbare spelerkandidaten op ontbrekende veldframes | 18–25 |

De veldstatussen zijn 114 keer `inconsistent_points`, 91 keer
`inconsistent_controls`, 77 keer `motion_semantic_disagreement` en 13 keer
`inconsistent_lines`. Dat wijst niet op een gecrasht spelersmodel. De bestaande
weergave filterde deze spelerboxen weg op basis van hun ontbrekende veldpositie.
Beschikbare kalibratie is nog geen bewijs van correcte kalibratie.

Nieuwe frame-exporten bevatten aanvullende `diagnostics`: behouden voorspellingen,
positief detectorbewijs, rollen, zichtbare spelerkandidaten, beeld-ID's,
weergegeven spelers, veldtelling en redenen voor uitsluiting. Deze aantallen zijn
geen ground truth en geen meting van detectorrecall. Oudere framebestanden blijven
leesbaar; afgeleide samenvattingen worden bij laden opnieuw berekend.

## Spelerherkenning apart gemeten

Op 108 oorspronkelijke beelden uit de bestaande zes ontwikkelwedstrijden is
nieuwe inferentie uitgevoerd met uitsluitend de bestaande spelersspecialist,
zonder rol-, veld- of trackingfilter. Eén beeld per seconde uit de vaste
begin-/midden-/eindvensters; 54 training en 54 validatie. De vergelijking met
behouden pipeline-uitvoer gebruikt precies dezelfde beeld-ID's en bestaande
native waarnemingen. De geometrie en modellen daarvan zijn niet opnieuw getraind.

| Stadium op 54 validatiebeelden / 796 spelerwaarnemingen | Precision | Recall |
|---|---:|---:|
| Nieuwe ruwe spelersdetector, vóór andere filters | 85,31% | 94,10% |
| Bestaande behouden speleruitvoer zonder veldfilter | 92,04% | 94,47% |
| Dezelfde behouden uitvoer met veldfilter | 93,29% | 76,88% |

De ruwe detector heeft 749 TP, 129 FP en 47 FN bij confidence 0,25 en IoU 0,5.
AP@50 is 94,43% en AP@50:95 60,56%. De rol-/geometrieverwerking kan boxen en
rollen verfijnen; de tweede rij is dus niet dezelfde ruwe detector met alleen
een confidencewijziging. De derde rij gebruikt de vaste 0,25-regel voor een
zuivere vergelijking; de aanvullende runtimebenchmark volgt ook gekoppelde
detecties onder 0,25.

Dit is een kleine, eerder gebruikte ontwikkelsteekproef met providerlabels,
geen onafhankelijke eindtest. De foutvoorbeelden zijn opgeslagen met hun
trainingssplit, beeldherkomst en voorlopige kenmerken zoals boxgrootte en
afstand tot de beeldrand. Er zijn geen menselijke oorzaken of reviews ingevuld.
Nieuwe spelertraining wordt niet op onbeoordeelde foutvoorbeelden gestart.

## Coördinaten en veldproef

Er is geen schaalfout aangetoond in de bestaande omzetting van de gestrekte
960 × 540-modelinvoer naar oorspronkelijke pixels. Beide inferentieroutes
gebruiken nu dezelfde omzetting. Tests controleren aparte x/y-schaling en
terugrekening op 1920 × 1080, 1280 × 720, 1920 × 720 en vierkante beelden.
De gedeelde adapter valt onder de cache- en bronhashcontrole.

Een vooraf vastgezette pool bevat 256 providerbeelden uit trainingswedstrijden.
De baseline vindt op 124 daarvan een projectie binnen de referentietolerantie;
132 zijn foutief, ontbrekend of onvoldoende scorebaar. Alleen deze trainingspool
wordt voor hard-exampleselectie gebruikt. De trainingsset bevat 64 moeilijke en
64 goede beelden uit 128 wedstrijden; de 48 validatiebeelden komen uit 48 andere
wedstrijden. Bronbeelden, labels, split en selectie hebben gecontroleerde hashes.

De proef traint beide bestaande PnLCalib-netwerken afzonderlijk, volledig vrij,
met drie epochs, batch 1, Adam, learning rate 0,00001 en seed 42. Dezelfde twee
trainingen leveren precies drie vergelijkingen: alleen nieuwe puntengewichten,
alleen nieuwe lijngewichten en beide samen. Er is geen nieuwe confidencezoektocht,
extra overbruggingsduur of herhaling van afgewezen uitvoerlaagproeven.

Een kandidaat moet meer correcte validatieframes geven, zonder meer foutieve
of onscorebare geaccepteerde frames en zonder hogere mediane of p95-lijnfout.
Een geslaagde ontwikkelcontrole is nog geen release: daarna zijn de doorlopende
benchmark, de eigen clip en de onafhankelijke menselijke referenties nodig.
De 90%-dekking en halvering van het aantal uitvalmomenten blijven doelen,
geen vooraf beloofde resultaten.

## Review en herhalen

De training en de drie vergelijkingen zijn voltooid. De drie puntenepochs
verbeterden het validatieverlies niet; het oorspronkelijke puntencheckpoint
bleef daarom behouden. Voor lijnen werd epoch 2 geselecteerd, maar die variant
haalt de afzonderlijke geometrische controle niet:

| Variant op 48 vaste validatiebeelden | Correct | Buiten tolerantie | Ontbreekt |
|---|---:|---:|---:|
| Oorspronkelijke gewichten | 23 | 6 | 19 |
| Alleen punten, geselecteerd checkpoint | 23 | 6 | 19 |
| Alleen nieuwe lijnen | 22 | 6 | 20 |
| Punten en nieuwe lijnen samen | 22 | 6 | 20 |

De lagere mediane/p95-lijnfout van de lijnvariant weegt niet op tegen de
verloren correcte projectie. Geen kandidaat is standaard geactiveerd. De
90%-dekking en halvering van uitval zijn niet aangetoond.

De uiteindelijke herverwerking van de eigen video behoudt boxen en beeld-ID's
op alle 295 ontbrekende veldframes. Alle 750 kalibratiestatussen en
projectiematrices zijn exact gelijk aan de nulmeting. De veldtelling blijft op
die 295 frames onbekend. Er is geen nieuwe detectorinferentie geclaimd voor
deze replay: bronpixels, gewichten en geometrie zijn gelijk, zodat alleen
weergave/beeldtracking worden onderzocht. De bestaande 900 + 1.800 gelabelde
benchmarkbeelden zijn opnieuw gescoord; tel-, herkennings- en ID-metrics zijn
bytegelijk aan de oorspronkelijke scores. Dit is geen nieuwe trackinginferentie.

De volgende gebruikersvraag is ook uitgevoerd: alle geleerde modellen kunnen
via de app in lokale achtergrondtaken trainen. Er zijn echte technische
trainingsproeven uitgevoerd voor de spelerworker en het afzonderlijke
veldpuntennetwerk. De GPU-contexttrainer is ook met echte CUDA-stappen getest.
Deze kleine technische proeven zijn geen nauwkeurigheidsbenchmark. Zie
[Trainen op een andere laptop](Trainen_op_Andere_Laptop.md).

Er staan 47 ongeannoteerde oorspronkelijke eigen beelden klaar in
`artifacts/player-field-reliability-20261030/ownclip-review`.
Daarnaast reserveert `final-review` drie reeds als test gemarkeerde bronvideo's,
met 30 oorspronkelijke beelden per bron. Er zijn geen modelvoorspellingen op
die reviewbeelden getekend. Wedstrijdidentiteit, eventuele overlap met
voortraining en de referenties moeten nog door een echte reviewer worden
bevestigd. De drie bronvideo's zijn geen drie voltooide onafhankelijke tests.
De losse beelden bewijzen geen uitvalduur op een doorlopende video.

Werk vanuit de projectroot. Zware data, checkpoints en video's blijven lokaal;
compacte metingen staan onder `reports/player-field-reliability-20261030`.

```powershell
$env:PYTHONPATH='src;.;scripts'
.venv/Scripts/python.exe -m football_pipeline.dropout_analysis audit runs/cdbccee936a74aecbffd40d557e573318a634d7ca6e1688f25bee4a8f3da277e --output reports/player-field-reliability-20261030/baseline
.venv/Scripts/python.exe scripts/measure_raw_players.py --dataset data/broadcast-temporal-v1/manifest.json --dataset data/broadcast-temporal-v2/manifest.json --output artifacts/player-field-reliability-20261030/raw-players
.tools/pnlcalib-env/Scripts/python.exe -m football_pipeline.field_recovery prepare --output artifacts/player-field-reliability-20261030/field-recovery
.tools/field-training-env/Scripts/python.exe -m football_pipeline.field_learning train --dataset-index artifacts/player-field-reliability-20261030/field-recovery/training-index.json --output artifacts/player-field-reliability-20261030/field-recovery/training --epochs 3 --lr 0.00001 --patience 3 --weight-decay 0.0001
.tools/pnlcalib-env/Scripts/python.exe -m football_pipeline.field_recovery compare --output artifacts/player-field-reliability-20261030/field-recovery --candidate artifacts/player-field-reliability-20261030/field-recovery/training/field-runtime.json
```

Training gebruikt bewust `field-training-env`; de kleinere inferenceomgeving
heeft niet alle bibliotheken voor labeltargets. Herstarten controleert de
bevroren invoer en hervat alleen bij identieke instellingen. Geen van deze
commando's verandert het standaardmodel automatisch.
