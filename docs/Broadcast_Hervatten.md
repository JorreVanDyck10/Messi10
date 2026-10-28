# Broadcastanalyse morgen hervatten

Status: **hervat op 28 oktober 2026**, na “ga door”. Het werk is nog niet af. De gebruiker wil spelers binnen het bestaande veld per team herkennen; personen buiten het veld zijn voor later. De veldmodellen en instellingen blijven behouden. De eerdere grens van vier uur is later expliciet opgeheven met “blijf maar door werken, kijk nie naar tijd”.

Nieuwste voortgang: `reports/broadcast-pitch-v1/progress-20261028.json`. De SportsMOT-download is volledig en de bronhash gecontroleerd. `data/broadcast-multisource-v1` bevat 3.936 trainingsbeelden uit zeven wedstrijden en dezelfde 348 SoccerNet-validatiebeelden. De nieuwe trainingsronde staat onder `artifacts/broadcast-multisource-v7/`, gestart met `python -m football_pipeline.broadcast_multisource_training`. De oudere M-ronde hieronder blijft bewaard en gepauzeerd: de eerste acht epochs waren niet beter.

Daarnaast verzamelt `python -m football_pipeline.broadcast_observed_context collect` echte detectoruitsneden voor aanvullende rolcontext. Alleen één-op-één bronboxmatches met IoU >= 0,5 leveren labels; ongematchte voorspellingen worden geen verzonnen negatieven. Deze cache staat onder `artifacts/broadcast-observed-v8/cache/`; een volledig verzamelrecord is vereist voordat `... train` kan starten. Het standaardprofiel is nog niet veranderd. Onderstaande pauzedetails beschrijven de bewaarde toestand van 27 oktober.

Branch: `codex/broadcast-spelers-teams`. De oorspronkelijke push/pull is uitgevoerd, inclusief het samenvoegen van `origin/main`. Er zijn geen subagents gebruikt. Vraag morgen niet opnieuw toestemming om deze opdracht te hervatten.

## Meteen verder kunnen

Werkmap: `C:\Messi10`. De code en deze overdracht staan in Git. De grote trainingscheckpoints, datasets en downloadcache staan **lokaal** in de genegeerde mappen `artifacts/`, `data/`, `models/`, `.cache/` en `runs/`; behoud die om precies verder te kunnen.

```powershell
# Alleen controleren; start geen training of download.
.\scripts\Resume-Broadcast.ps1 -Action status

# Hervat de SportsMOT-download vanaf de bewaarde bytepositie.
.\scripts\Resume-Broadcast.ps1 -Action download

# Hervat zo nodig de bestaande M-detector met optimizer vanaf epoch 8.
.\scripts\Resume-Broadcast.ps1 -Action training

# Pas uitvoeren nadat de volledige download en SHA-256 zijn gecontroleerd.
.\scripts\Resume-Broadcast.ps1 -Action prepare-data
```

Download en training kunnen in aparte processen naast elkaar lopen. Deze opdrachten zijn nu **niet** gestart: de GPU en download zijn gestopt. Alleen de bestaande Streamlit-server blijft open.

## Wat is exact bewaard?

- De grotere YOLO11m-detector met twee echte getrainde klassen `player`/`referee`: `artifacts/broadcast-detector-v4/paused/last.pt`, inclusief optimizer, na **8 complete epochs**. De gedeeltelijke epoch 9 is weggegooid. `paused/best.pt` is ook gekopieerd. Hashes, datasetfingerprint en het oorspronkelijke uitvoerpad staan in `paused/checkpoint.json`; `training/status.json` staat op `paused_by_user`.
- SportsMOT: **4.857.004.032 van 6.703.191.552 bytes** in `.cache/sportsmot/train.tar.part` (ongeveer 72,5%). Hervatten gebruikt een gecontroleerde HTTP Range; pas na controle van de volledige hash wordt dit `train.tar`.
- SportsMOT-bronrevision: `1b0b418ea611a8e934f1e773313e719e4fa1265e`. Verwachte archief-SHA-256: `dc8edc8126bcb66611e768679f618a14880510944dc0e07959c00c0c14722341`.
- Alleen de officiële SportsMOT-trainset wordt opgehaald. De bevroren selectie bevat 15 voetbalclips uit 4 wedstrijden. De dataset labelt spelers op het speelveld; scheidsrechters, coaches en publiek zijn geen targets. De adapter gebruikt uitsluitend deze voetbal-trainbeelden, elke vijfde frame.
- Het nieuwe gemengde spelersdataset krijgt deterministische hashbestandsnamen. Daardoor worden wedstrijden gemengd wanneer rechthoekige YOLO-training de normale shuffle uitschakelt. De originele SoccerNet-validatiewedstrijden blijven apart.

De hervatfunctie verifieert checkpoint, optimizer, epoch, bronbeelden, labels en datasetfingerprint voordat training start. Herstart de oorspronkelijke `Run-BroadcastSpelersTraining.ps1` niet blind: die hoort bij de eerdere experimentele rondes, heeft nog een oude gezamenlijke tijdslimiet en bevat de nieuwste SportsMOT-ronde niet.

## Uitgevoerde training en resultaten

SoccerNet-GSR is vastgezet op revision `3cc710eb6d53a23350a3d2863311c1c0a2e645d7`: 1.710 trainingsbeelden uit 57 clips en 348 validatiebeelden uit 58 clips. Trainwedstrijden zijn 4/6/9; validatie 2/3/5. Team-, keeper- en tracklabels blijven bewaard. Samen met eerder verzamelde data zijn 39.802 rolcrops gebruikt. Er zijn geen officiële test- of challengebeelden geopend.

- `artifacts/broadcast-pitch-v1/`: eerste detectorronde en frozen-feature-experimenten. De kleine detector en aangeleerde shirtprojectie waren onvoldoende; niet als eindmodel publiceren.
- `artifacts/broadcast-refine-v2/`: afgeronde grotere spelerdetector, 25 epochs; `detector/status.json` bevat de definitieve `best.pt` en hash. Dit model heeft één daadwerkelijk getrainde klasse `player`. Daarnaast is een MobileNet-rolmodel met drie klassen (`player`, `referee`, `person`) echt bijgetraind. Het staat in `roles/roles_teams.pt`.
- Shirtindeling: de verzadigingsgewogen histogramreferentie presteerde beter dan de getrainde projectie. De gekozen `teams/kit_embedding.pt` heeft formaat `broadcast-kit-hist-v2`, met de werkelijk gemeten instellingen in `teams/metrics.json`. Niet beweren dat een neurale teamprojectie de verbetering leverde.
- `artifacts/broadcast-role-context-v5/` en `...-v6/`: getrainde scènecontext op relatieve shirtsimilariteit, rolcrops en veldposities. PCA en normalisatie zijn uitsluitend op training gefit; foutieve individuele rolvoorspellingen zijn per tenue gesimuleerd om hele teams te beschermen. V5 heeft een gecontroleerde runtime-export `runtime_context.pt`; V6 is reproduceerbaar met `python -m football_pipeline.broadcast_context_training` en heeft `role_context.pt`.

De laatste volledige vergelijking vóór de laatste technische aanpassing:

| Combinatie | Spelerprecision | Recall | Team correct/toegewezen | Teamdekking gematcht |
|---|---:|---:|---:|---:|
| Oude R007-baseline | circa 87% | circa 37% | circa 93% | circa 33% |
| Nieuwe context + gecombineerde boxen, persoonsmodel S | 91,76% | 90,39% | 97,12% | 93,73% |
| Nieuwe context + gecombineerde boxen, persoonsmodel M | 91,83% | 90,27% | 96,93% | 93,87% |

Deze cijfers gebruiken **341 beelden met referentiehomografie uit providerannotaties**, bbox-IoU 0,5 en één vaste A/B-omwisseling per hele clip. Het zijn ontwikkelmetingen, geen onafhankelijke eindtest of score voor automatische veldherkenning. De validatie is gebruikt voor model- en drempelselectie. Gemiste spelers, foutpositieven en keepers staan afzonderlijk in de JSON-rapporten.

De brondata-audit testte een vaste label-frameverschuiving; er is **geen labelverschuiving toegepast** en geen label op voorspellingen aangepast. Een deel van de kleine, bewogen boxen sluit visueel niet goed aan op de gelabelde box. Dit rechtvaardigt geen versoepeling van de primaire meetgrenzen.

## Belangrijke resterende problemen

**Nog niet activeren als definitief standaardmodel.** De grens van 95% spelerprecision is niet bereikt. `configs/models-broadcast.json` is nog niet gepubliceerd. De bestaande startprofielen blijven daardoor actief.

De eigen clip blijft een noodzakelijke controle: de hoofdscheidsrechter wordt op frame 149 nog als Team B getoond. Ook dubbele/fragmentarische detecties en sterk wisselende tijdelijke IDs blijven zichtbaar. De contextverbetering is dus geen bewijs dat officials in deze clip correct verdwenen zijn.

Nieuwste voorbeeldrun:

`runs/9472cb5a2fb4217c651aedb6a988ccf707f23021d429f00c92293f62d6d66e3f`

Daar staan `samengestelde_video.mp4`, `framegegevens.jsonl`, `teamtelling.csv` en drie controlebeelden. Alle **150 veldkalibraties zijn exact gelijk** aan de oude run `63d6a606d9cda9ade4c1719aecc03e50f573ec97469e7d5b3904a0d1f72425cb`. `artifacts/broadcast-role-context-v5/preview-check.json` legt dat vast. Dit is visuele AI-controle, geen menselijke acceptatie.

De laatste code projecteert gecombineerde boxen opnieuw **vóór** rolcontext wordt berekend. Dat was een noodzakelijke technische correctie na de bovenstaande meetronde. Voer de finale vergelijking dus opnieuw uit met vastgezette code en nieuwe uitvoermappen; hergebruik geen metrics met gewijzigde bronhashes.

## Logische volgende stappen

1. Controleer de hervatstatus. Rond de SportsMOT-download en bronhashcontrole af en maak met `-Action prepare-data` het nieuwe gemengde spelerdataset.
2. Beslis of de gepauzeerde M-ronde nog moet worden uitgedraaid. De eerste 8 epochs verbeteren de oude beste detector nog niet; de native gemiddelde score verbergt zwakke scheidsrechterherkenning en lage spelerrecall. De per-klasse diagnose staat in `artifacts/broadcast-detector-v4/diagnostic-classes.json`.
3. Train een nieuwe spelerdetector op `data/broadcast-multisource-v1`, warm gestart vanaf de **daadwerkelijk getrainde** spelercheckpoint uit `broadcast-refine-v2/detector/status.json`. Gebruik de nieuwe `train_yolo`-ondersteuning voor `minutes=None` en workers 4. Een redelijke volgende proef is YOLO11s, imgsz 1536, rect=True, batch 2, lage leersnelheid en eindige epochs met early stopping. De drie-/zeven-wedstrijdenmix en bronnegatieven zijn belangrijker dan opnieuw dezelfde overfitronde starten.
4. Vergelijk detector, rollen, gecombineerde boxen en context V5/V6 op exact dezelfde SoccerNet-validatie. Nieuwe `broadcast_release --candidates <json>` kan expliciet gekozen profiel-/team-bestanden en trainingsrecords vergelijken. Houd de echte bronklassen intact; een COCO-`person` mag niet stilzwijgend `player` heten.
5. Controleer vooral echte officials, keepers, kleine spelers, gedeeltelijke boxen en de eigen video. Een werkelijk getrainde keeperklasse blijft speler; onzekere teamkoppelingen mogen onbekend blijven. Alles buiten een geldig huidig veld blijft buiten de spelersanalyse.
6. Pas na de keuze de draagbare gewichten via Git LFS publiceren in `artifacts/broadcast-players-v1/`, met de juiste profielpaden, hashes, contextgewichten en verslag. Controleer opnieuw video, minimap, CSV, veldgelijkheid en app. Geen productie- of onafhankelijke nauwkeurigheid claimen.

## Niet opnieuw verspillen aan afgewezen proeven

- Officiële PRTReID-baseline: numeriek correcte TorchScript-export, maar circa 82% spelerrecall op deze referentiecrops; slechter dan het eigen rolmodel. Bestanden blijven lokaal in `artifacts/broadcast-expert-v3/`.
- Roboflow-voetbalmodel: echte vier bronklassen gecontroleerd, maar slechts circa 78% precision / 81,5% recall op dezelfde veldvalidatie; afgewezen. Bronmodel en herkomst staan lokaal onder `models/roboflow-football-players*`.
- Sterke kleuraugmentatie zonder kleurfeatures: echt getraind, maar circa 88,5% spelerrecall op referentiecrops. De gecontroleerde constant-bias-export staat in `artifacts/broadcast-refine-v3/roles/`; niet verwarren met het betere V2-rolmodel.
- Uitsneden vergroten recall licht maar voegen te veel dubbele boxen toe. Geen ongecontroleerde tilingvariant standaard maken.

## Software en bewaarde bewijsbestanden

Laatste volledige suite: **369 tests en 4 subtests geslaagd**, nul fouten. Ruff en `git diff --check` slagen. De laatste hervathulp is daarnaast met `-Action status` getest: checkpoint hash klopt, epoch 8 en de gedeeltelijke download worden correct gevonden. Training en download zijn daarbij niet gestart.

Compact voortgangsrecord: `reports/broadcast-pitch-v1/progress-20261027.json`. Gedetailleerde logs en pytest-XML staan in `.cache/`; brongebonden kandidaatsrapporten staan in de genoemde artefactmappen. Het veldmodel/PnLCalib is in deze opdracht niet opnieuw getraind.
