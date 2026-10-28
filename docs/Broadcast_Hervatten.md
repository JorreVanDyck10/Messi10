# Broadcastanalyse: actuele overdracht

Bijgewerkt op **28 oktober 2026**. De pauze van gisteren is hervat na “ga door”. Een verbeterd **ontwikkelprofiel** is nu standaard beschikbaar; de nauwkeurigheid is nog niet definitief goedgekeurd. De gebruiker wil spelers op het veld per team herkennen. Buitenveldse personen blijven uitgesteld. De eerdere tijdslimiet is expliciet opgeheven. Vraag bij een volgende “ga door” niet opnieuw toestemming om hiermee verder te werken.

## Meteen terugvinden

- Werkmap `C:\Messi10`, branch `codex/broadcast-spelers-teams`.
- Verslag: `reports/broadcast-pitch-v1/summary.json`, `docs/Broadcast_Spelers_en_Teams.md` en `reports/broadcast-pitch-v1/progress-20261028.json`.
- Profielen: `configs/models-broadcast.json` en `configs/teams-broadcast.json`. De gewichten staan via Git LFS in `artifacts/broadcast-players-v1/`; ze zijn voldoende voor de applicatie. Eerdere profielen zijn behouden.
- Starten: `scripts/Start-Gezamenlijk.ps1` of `scripts/Start-Spelermodel.ps1 -Recognition broadcast`. Deze starters kiezen broadcast ook standaard wanneer Recognition niet expliciet is meegegeven.
- Nieuwe video: [broadcastanalyse](http://127.0.0.1:8501/?run=d3cff1b2360bb235635d9e2dcd99870a462d153a6b253913c73afb2f07b61664).
- Lokale run: `runs/d3cff1b2360bb235635d9e2dcd99870a462d153a6b253913c73afb2f07b61664`. Video, minimap en CSV zijn volledig verwerkt. Alle **150 veldkalibraties zijn exact gelijk** aan de oorspronkelijke analyse.

## Werkelijk uitgevoerd

SportsMOT is volledig gedownload en op SHA-256 gecontroleerd: `.cache/sportsmot/train.tar`, 6.703.191.552 bytes, SHA `dc8edc8126bcb66611e768679f618a14880510944dc0e07959c00c0c14722341`. Bronrevision `1b0b418ea611a8e934f1e773313e719e4fa1265e`, uitsluitend de officiële voetbal-trainselectie: 15 clips uit vier wedstrijden, CC-BY-NC-4.0. Geen SportsMOT-val/testbeelden geopend.

`data/broadcast-multisource-v1` bevat **3.936 trainingsbeelden uit zeven wedstrijden**: 1.710 SoccerNet-beelden uit wedstrijden 4/6/9 en 2.226 SportsMOT-beelden. Dezelfde 348 SoccerNet-validatiebeelden uit wedstrijden 2/3/5 blijven apart. Hashbestandsnamen mengen wedstrijden tijdens rechthoekige training. Beelden en labels zijn gecontroleerd op bytes en kruisende splits. Zie `reports/broadcast-pitch-v1/data-20261028.json`.

De nieuwe YOLO11s-spelerdetector is echt verder getraind vanaf de gecontroleerde V2-spelercheckpoint: 1536, rect, batch 2, workers 4, AdamW 5e-5, maximaal 40 epochs, patience 8, geen tijdslimiet. Vroeg stoppen na **11 complete epochs** behield epoch 3; looptijd 3341 seconden. Gewichten: `artifacts/broadcast-multisource-v7/detector/batch-2/weights/best.pt`, SHA `fb6deea2d6c51bada9d3f8bfd666882212f45d1a1584547d02dc98aa59aaaa25`. Curve en native argumenten staan in `reports/broadcast-pitch-v1/multisource-training-20261028.*`.

Aanvullende scènecontext is getraind op **echte detectoruitsneden**, één-op-één gekoppeld aan providerboxen bij IoU >= 0,5. Ongematchte voorspellingen leveren geen verzonnen negatieve labels. Cache en training: `artifacts/broadcast-observed-v8/`; trainer `football_pipeline.broadcast_observed_context`. Contextcheckpoint: `training/role_context.pt`, SHA `fa9fd730d668a4225279fe31ffacb450e2b5bc1c2f7674df7550006b7ba76541`. PCA is uitsluitend op training gefit en aan de echte rol- en shirtgewichten gebonden.

Geselecteerd: **multisource-m**. Nieuwe speler-YOLO11s en echte COCO-person-voorstellen van YOLO11m op 1920, gecombineerde boxen met gewicht 0,5, V2-MobileNet-rollen, V8-context en verzadigingsgewogen shirtkleurhistogrammen. De getrainde neurale shirtprojectie was slechter en is niet gekozen. Generieke `person`-bronklassen zijn niet als `player` gemapt.

Aanvullende scheidsrechterafwijzing vereist tegelijk crop-referee >= 0,85, context-nonplayer >= 0,75 en ten minste 0,4 cosineafstand tot beide teamtenues. Dit gebeurt alleen in de middelste 60% van het veld en beschermt herkende keepers. Elke beslissing bewaart de drie aanwijzingen. Dit lost niet alle officials op.

ByteTrack-cameracompensatie is hersteld: de bibliotheek behandelde aspect/hoogte als XY-paar. Rotatie mengde pixelhoogte in aspect en brak IDs. De eigen omzetting gebruikt de begrenzende box en Jacobiaan voor de XYAH-Kalmanstaat. Een geïsoleerde herhaling op exact dezelfde detecties en bewegingen daalde van 393 naar 28 tijdelijke IDs; de uiteindelijke native run heeft 29. Dit is geen onafhankelijke trackingnauwkeurigheidstest.

## Resultaten en resterend werk

Op 341 beelden met bruikbare **providerreferentiegeometrie** (7 zonder referentie apart gemeld), bbox-IoU 0,5 en één A/B-omwisseling per hele clip:

| Meting | Oude R007-baseline | Nieuwe combinatie |
|---|---:|---:|
| Spelerprecision | 87,31% | 92,07% |
| Spelerrecall | 37,40% | 91,04% |
| Team correct onder toegewezen gematchte spelers | 93,31% | 97,05% |
| Teamdekking onder gematchte spelers | 33,07% | 93,79% |

Dit zijn ontwikkelmetingen. Validatie is herhaald gebruikt voor checkpoint-, drempel- en modelkeuze. Het is **geen onafhankelijke eindtest** of score voor automatische veldherkenning. De zelf gestelde spelerprecision van 95% is nog niet bereikt. Niet als definitief goedgekeurd of foutloos presenteren.

Volgende verbeteringen:

1. In de eigen clip telt de hoofdscheidsrechter op **frame 75 nog als Team B**. Op frame 149 is hij correct uitgesloten. Crop- en contextvoorspellingen wisselen tussen voor- en achteraanzicht. Meer diverse echte officials en gecontroleerde consistentie over de tijd zijn logische onderzoeken. Niet één classifier overal laten winnen: dat verwijdert ook echte spelers in onbekende tenues.
2. Overlappende/fragmentarische boxen blijven mogelijk. Tracking is stabieler; IDs zijn geen geverifieerde identiteit.
3. Keepers: 176 van 194 gematcht, slechts 16 met correct team. Afwijkende tenues blijven meestal onbekend. Betrouwbare teamkoppeling ontbreekt nog; niet in een veldspelerskleur dwingen.
4. Behoud vaste validatie en primaire IoU-grens. Er is geen label-frameverschuiving toegepast; een eerdere audit bewees geen globale indexeringsfout. Geen labels op voorspellingen aanpassen.

Laatste softwarecontrole: **377 tests en vier subtests geslaagd**, geen fouten; Ruff en `git diff --check` slagen. Native video/minimap/CSV-integratie slaagt. Het resultaat opent zonder AppTest-fouten.

## Bewaarde lokale proeven en opnieuw uitvoeren

Behoud `.cache/`, `data/`, `models/`, `artifacts/` en `runs/`. Alleen het draagbare applicatiemodel is gepubliceerd; opnieuw trainen vereist lokale brondata en eerdere V2-warmstart. De historische pauzetoestand staat in `reports/broadcast-pitch-v1/progress-20261027.json`.

```powershell
# Status van de historische M-pauze én de afgeronde multisource-ronde.
.\scripts\Resume-Broadcast.ps1 -Action status

# Bestaande brondata controleren/voorbereiden, geen nieuwe training.
.\scripts\Resume-Broadcast.ps1 -Action prepare-data

# Nieuwe proef: altijd een NIEUWE uitvoermap.
.venv\Scripts\python.exe -m football_pipeline.broadcast_multisource_training --output artifacts/broadcast-multisource-v10

# Lokale vergelijking en demonstratie opnieuw uitvoeren.
.venv\Scripts\python.exe -m football_pipeline.broadcast_release --candidates artifacts/broadcast-final-20261028/candidates.json --refined artifacts/broadcast-refine-v2
```

De oudere YOLO11m-ronde met twee rollen staat nog **gepauzeerd na epoch 8** in `artifacts/broadcast-detector-v4/paused/last.pt`, met optimizer en gecontroleerde hashes. Deze is bewust niet hervat: hij was niet beter. `Resume-Broadcast.ps1 -Action training` start specifiek deze oude M-ronde. Herstart `Run-BroadcastSpelersTraining.ps1` evenmin blind: die hoort bij eerdere begrensde proeven.

Afgewezen proeven blijven lokaal: PRTReID (`broadcast-expert-v3`), Roboflow (`broadcast-roboflow`), sterk kleurinvariante rollen (`broadcast-refine-v3`) en neurale shirtprojecties (`broadcast-pitch-v1`). Hun validatie was slechter. Veldmodel/PnLCalib is niet opnieuw getraind. Er zijn geen subagents gebruikt.
