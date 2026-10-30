# Automatische veldkalibratie

Deze uitbreiding hoort bij persoon 2. Persoon 1 blijft verantwoordelijk voor `player` (inclusief doelman),
`referee`, eventueel `ball`, labels, splits, training, evaluatie en modeloverdracht. Nieuwe bronvideo's
worden afzonderlijk gekalibreerd; de kalibratie wordt bij bewegende beelden per frame opnieuw bepaald.

**Actuele versie:** nieuwe modelbundels bewaren alle vlakke piekscores vóór
filtering en gebruiken gecontroleerde fit-/controlepunten plus maximaal twee
seconden gemeten camerabeweging. De verplichte twee-lijncontrole hieronder
beschrijft de behouden legacy-versie, niet de nieuwe standaard. Nieuwe runs
gebruiken schema 3; oude bundels behouden hun oude identiteit en gedrag.
Zie [het Broadcast-experiment](Broadcast_Veldexperiment.md) voor de nieuwe methode,
de gemeten 252/1.239 frames (20,3%), visuele framecontrole en open menselijke beoordeling.

## Installatie en gebruik

Voer vanuit de projectmap met Python 3.11 uit:

```powershell
python scripts/setup_field_model.py
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

De setup maakt uitsluitend `.tools/pnlcalib-env`, een vastgezette externe PnLCalib-checkout,
`weights/pnlcalib` en `.tools/field-runtime.json`. Hij installeert niet in de pipelineomgeving of
trainingsomgeving van persoon 1. De eerste installatie downloadt enkele GB aan CUDA-dependencies.
Zonder geschikte CUDA-GPU: `python scripts/setup_field_model.py --device cpu`.

Upload een MP4 en kies **Automatische veldkalibratie**. Vul de videobron en het toegelaten gebruik in,
kies het bestaande modelprofiel voor personen/spelers en klik **Verwerken**. De veldmodellen draaien
eerst in een apart proces; daarna verwerkt de pipeline detecties, veldprojecties en de samengestelde video.
`FOOTBALL_FIELD_RUNTIME` kan een andere lokale runtimeconfiguratie aanwijzen.

CLI, direct van video naar uitvoer:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline process data\wedstrijd.mp4 --auto-field --source "Videobron" --usage "Toegelaten gebruik" --models configs\models.json --output runs
```

De veldherkenning kan ook apart worden uitgevoerd. De eerste opdracht print het concrete bundelpad:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline calibrate-auto data\wedstrijd.mp4 --source "Videobron" --usage "Toegelaten gebruik"
.\.venv\Scripts\python.exe -m football_pipeline process data\wedstrijd.mp4 --automatic-calibration data\field-calibration\BUNDEL\automatic_calibration.json --models configs\models.json
```

`--calibration`, `--automatic-calibration` en `--auto-field` zijn onderling exclusief. Bestaande handmatige
kalibratiebestanden en de CLI met `--calibration` blijven werken. Automatische verwerking ondersteunt nog
geen ByteTrack: daarvoor moet cameracompensatie afzonderlijk worden gevalideerd.

## Modellen en oorspronkelijke geometriecontrole (legacy)

De adapter gebruikt de officiële **SV_kp**- en **SV_lines**-netwerken uit
[PnLCalib](https://github.com/mguti97/PnLCalib), revisie `8c87391d6f4ea40c5e4d65e61529916c7a49ce62`.
Het is een conservatieve vlakke homography-adapter, zonder de upstream 3D/PnL-refinement en
lensvervormingsoptimalisatie. Code/licentie blijven in de afzonderlijke GPL-2.0-checkout. Runtime en
bundel bewaren release-URL's, gecontroleerde gewichtshashes, bronhashes, licentie-identiteit en dependencies.

- De vier bovenste doelpaal-/latpunten zijn uitgesloten van de grondprojectie. Geen afgeleide
  lijnsnijpunten worden als onafhankelijke waarnemingen toegevoegd.
- Ten minste zes voldoende verspreide grondpunten bepalen met RANSAC de transformatie. Ten minste
  twee herkende grondlijnen uit het tweede netwerk controleren de aansluiting. Dat is een interne
  consistentiecontrole tussen modellen, geen onafhankelijke nauwkeurigheidsmeting.
- De oorspronkelijke confidencegrenzen zijn 0,3434 voor punten en 0,7867 voor lijnen. De interne
  pixelgrenzen zijn mediaan 0,5% en maximum 1% van de beelddiagonaal. Minstens 70% van de punten moet
  bij de geometrie passen; minstens zes punten moeten inliers zijn.
- Het aangenomen veld is het standaardmodel van 105 × 68. Uitvoer is uitsluitend genormaliseerd
  `[u,v]`; de werkelijke veldafmetingen zijn niet vastgesteld. Geen snelheid of afstand in meters.
- De oriëntatieconventie veronderstelt een hoofdcamera langs de zijlijn, met `u` naar rechts en `v`
  naar beneden in het beeld. Gespiegelde, gedraaide en geometrisch onduidelijke schattingen worden
  afgewezen. De symmetrie van een veld geeft geen bewijs van teamrichting of een vaste fysieke doelidentiteit
  over verschillende camerastandpunten; daarvoor is aanvullende informatie nodig.
- Elk frame wordt zelfstandig geschat. Geen vasthouden, extrapoleren of interpoleren van de vorige matrix.
  Camerawissels kunnen daardoor geen oude kalibratie overnemen. Nadeel: korte herkenningsgaten blijven zichtbaar.

De bron-overlay toont gele veldpunten, groene waargenomen lijnen en blauwe teruggeprojecteerde lijnen.
Bij uitval blijven detectieboxen zichtbaar, veldposities worden `null` en de minimap meldt
**Veldpositie onbekend**. Personen buiten het geprojecteerde veld en afgesneden voeten blijven afgewezen.
De bal krijgt ook hier geen grondprojectie.

## Uitvoer, cache en replay

Legacy-runs gebruiken manifestversie 2; nieuwe runs versie 3 met `field_settings`,
kalibratiebron, referentieframe, ouderdom en bewegingskwaliteit. Beide bevatten:

- `calibration.json`: portable automatisch bundelmanifest met videohash, modelidentiteit en bronvermelding;
- `observations.jsonl`: semantische punten en lijnen in oorspronkelijke pixels, één record per bronframe;
- `framegegevens.jsonl`: per frame de opnieuw berekende kalibratie, status, kwaliteitsmetingen en detecties;
- `runmanifest.json`: kalibratiemodus, bruikbare fractie, afwijsredenen en verwerkingstijden.

De kalibratie wordt bij laden opnieuw uit de waarnemingen berekend. Hash, resolutie, volledige framevolgorde
en tijdstempels worden gecontroleerd. Cache-identiteit omvat video, veldbundel, spelersmodel, code en omgeving.
Gewone automatische replay vereist dezelfde kalibratie-identiteit en controleert alle uitvoerhashes.
Expliciete `--recalibrate-replay` hergebruikt alleen echte detecties van dezelfde
video en hetzelfde spelersmodel en maakt een nieuwe run met opnieuw berekende
veldposities; de detecties worden niet als nieuwe inference voorgesteld. De benodigde
veldwaarnemingen worden naar de run gekopieerd, zodat de bundel daar opnieuw kan worden geladen.

## Technische proef en onafhankelijke beoordeling

De reproduceerbare technische proef gebruikt een afzonderlijke, toegelaten Commons-video en maakt vooraf
een selectie van dertig frames. Hij schrijft geen menselijke labels of goedkeuringen:

```powershell
.\.venv\Scripts\python.exe scripts/field_calibration_pilot.py --prepare-only
.\.venv\Scripts\python.exe scripts/field_calibration_pilot.py
```

De standaardbron is **2018 FIFA U-17 Women's World Cup — New Zealand vs Canada — 24**, van **NaBUru38**,
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_24.webm),
onder [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Wijzigingen: eerste twaalf seconden,
H.264, tien frames per seconde, audio verwijderd en detectie-/veldoverlay met minimap. De afgeleide video
wordt onder CC BY-SA 4.0 aangeboden. Geen endorsement wordt gesuggereerd. Deze clip is een opname vanaf
de tribune; hij is geen gevalideerde vervanger voor een volledige tv-hoofdcamera-benchmark.

Met `--source latvia` kan daarnaast de CC0-opname van Letland–Gibraltar worden voorbereid.
Beide bronnen blijven buiten de dataset en splits van persoon 1. De bronkeuze, originele checksum,
conversie en selectie staan in `provenance.json`. De technische uitvoer staat onder
`artifacts/automatic-field-pilot/BRON/`; `technical-report.json` vermeldt de werkelijke bruikbaarheid en
runtime. Een percentage bruikbare frames is geen gemeten projectienauwkeurigheid.

In `reference-to-review.json` vult een reviewer voor elk geselecteerd frame in of kalibratie mogelijk is.
Voor kalibreerbare frames zijn minstens twee verschillende zichtbare referentiepunten nodig, met originele
`x,y` en bekende `u,v`. Deze worden niet aan de veldmodellen of de schatter doorgegeven. Vul reviewer en
`human_reviewed: true` pas in na echte menselijke controle; `used_for_tuning` blijft `false`.

```powershell
.\.venv\Scripts\python.exe -m football_pipeline evaluate-calibration artifacts\automatic-field-pilot\nz-canada\runs\RUNMAP artifacts\automatic-field-pilot\nz-canada\reference-to-review.json --output reports\field-calibration-evaluation.json
```

Het rapport bevat terugprojectiefouten, dekking op kalibreerbare frames en onterecht geldige schattingen
op onkalibreerbare frames. Het weigert minder dan dertig unieke frames, ontbrekende review, andere videohashes
en data die voor afstemming is gebruikt. Zonder die beoordeling blijven onafhankelijke nauwkeurigheid,
algemene pan-/zoomkwaliteit en menselijke acceptatie expliciet open.

## Gemeten technische status op 16 oktober 2026

De afzonderlijke omgeving is daadwerkelijk geïnstalleerd en beide releasegewichten zijn met hun
vastgezette SHA-256 gecontroleerd. CUDA-inference is uitgevoerd op een RTX 4050 Laptop GPU met 6 GB.

| Proef | Werkelijke uitkomst | Betekenis |
|---|---|---|
| Letland–Gibraltar, 422 frames op 25 fps | 0 bruikbare framekalibraties; onvoldoende veldpunten | Lage tribunehoek, rook en afdekking worden niet betrouwbaar gekalibreerd |
| Nieuw-Zeeland–Canada, 120 frames op 10 fps | 0 bruikbare framekalibraties; onvoldoende veldpunten | Ook deze lage tribuneopname valt buiten de bruikbare beelden van deze eerste modelintegratie |
| Kunstmatige pan/zoom van upstream voorbeeldbeeld, 50 frames | 32 bruikbare framekalibraties; vijf lege frames zonder posities; herstel op frame 27 | Technische werking met echte gewichten, geen bewijs op echte camerabeweging |

De kunstmatige proef is apart reproduceerbaar:

```powershell
.\.venv\Scripts\python.exe scripts/field_calibration_diagnostic.py
```

Deze schrijft `artifacts/automatic-field-diagnostic/demonstratie.mp4`, `preview.jpg`, bronherkomst en een
technisch rapport. Het beeld zelf vermeldt dat de pan/zoom kunstmatig is. Het onderliggende stilbeeld
komt uit de externe PnLCalib-voorbeeldmap; deze proef blijft een lokale engineeringdiagnose, zonder
afzonderlijke claim op rechten voor verspreiding van het oorspronkelijke wedstrijdbeeld.

**De kandidaat is dus aangesloten, maar algemene werking op bewegende wedstrijdvideo's is niet
aangetoond.** Een geschikte opname van de hoofdcamera langs de zijlijn en de onafhankelijke menselijke
controle op minimaal dertig frames blijven nodig. De confidencegrenzen zijn niet versoepeld om de
twee mislukte tribuneproeven alsnog als geslaagd voor te stellen. Er zijn geen testbeelden van persoon 1
gebruikt en geen menselijke referenties of goedkeuringen verzonnen.

De vastgelegde controles en gemeten uitkomsten staan ook in
[`reports/automatic-field-technical-check.json`](../reports/automatic-field-technical-check.json).
De volledige softwarecontrole slaagt met 117 tests en vier subtests; Ruff-controle en formatteringscontrole slagen.
