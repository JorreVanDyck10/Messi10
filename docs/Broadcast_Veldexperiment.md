# Veldherkenning op Broadcast video.mp4

## Status en cursusafbakening

Dit is een **experimentele uitbreiding** op het MVP. De opdracht, pagina 2–3 van
`CV_Challenge_2026_2027.pdf`, vraagt minstens vier bekende vlakke veldpunten,
OpenCV-homography en een ruimtelijk correcte minimap op dezelfde tijdlijn. Het
MVP veronderstelt een vaste camera; pan, zoom en automatische herkenning vragen
afzonderlijke validatie. Deze wijziging traint geen veldmodel en voltooit dus ook
niet de optionele cursusuitbreiding waarin je zelf een keypointmodel traint.

Persoon 1 blijft eigenaar van spelersdata, labels, splits, training en evaluatie.
De bestaande COCO-personendetector levert uitsluitend een minimapdemonstratie;
`person` wordt geen `player`. Spelertracking staat uit in de automatische modus.
De gewichten, klassemapping en training van persoon 1 zijn niet aangepast.

## Vooraf vastgelegde ontwikkelbron

De gebruiker heeft `Broadcast video.mp4` lokaal aangeleverd: 1920 × 1080,
25 fps, 1.239 frames, 49,56 seconden. SHA-256:
`6cdaf4089cb578636bc4773bde0ebdc1e68b8554e169d413e855bdf144780f4a`.
Toegestaan gebruik dat hier wordt vastgelegd: lokale ontwikkeling en persoonlijke
beoordeling. Publicatierechten zijn niet bevestigd. Video en afgeleide beelden
blijven lokaal onder genegeerde uitvoermappen.

`configs/broadcast-field-selection.json` is vóór de nieuwe vergelijkingen
geschreven. Tien ontwikkelframes komen uit de even tijdgroepen van vijf seconden;
dertig beoordelingsframes uit de oneven groepen. De selecties hebben marges van
0,4 seconde rond de groepsgrenzen. De oude baseline en een contactblad waren al
bekeken: dit is een ontwikkelvideo, geen onaangeroerde onafhankelijke eindtest.
Naburige frames van dezelfde wedstrijd blijven bovendien sterk gecorreleerd.

Er zijn **geen menselijke referentiepunten of kalibreerbaarheidslabels ingevuld**.
Daarom zijn de menselijke projectiefout, dekking op kalibreerbare overzichtsframes
en de 90%-doelstelling nog open. Deze ene clip bewijst geen algemene betrouwbaarheid.

## Methode en herkomst

De afzonderlijke PnLCalib-omgeving blijft behouden, met bronrevisie
`8c87391d6f4ea40c5e4d65e61529916c7a49ce62` van
[de oorspronkelijke implementatie](https://github.com/mguti97/PnLCalib).
De GPL-2.0-licentie en gehashte bronbestanden staan in het runtime-/modelmanifest.
De releasegewichten blijven:

| Model | SHA-256 |
|---|---|
| SV_kp | `7ea78fa76aaf94976a8eca428d6e3c59697a93430cba1a4603e20284b61f5113` |
| SV_lines | `d72f4ed71734a2e3df9fa084f666e9b8adaef21bf69bac8952d6d3f970ff7455` |

De worker schrijft nu alle 53 vlakke semantische puntpieken en alle 17 vlakke
lijnwaarnemingen vóór confidencefiltering. Bij lijnen worden beide ruwe scores
bewaard. De originele scores blijven beschikbaar als `raw_score`/`raw_scores`;
`confidence` wordt begrensd op [0,1] voor het bestaande contract. Heatmapscores
zijn geen gekalibreerde kansen. Boven het grondvlak gelegen doelpunten worden
niet voor de vlakke homography gebruikt. Beeldcoördinaten blijven bronpixels.

De nieuwe schatter gebruikt minstens vier verspreide grondpunten. Bij minstens
zes punten blijven twee vooraf op semantische volgorde gekozen punten buiten de
fit (index n/3 en 2n/3). De schatter past de controles achteraf niet opnieuw in.
Vier of vijf punten vereisen aanvullende, niet-parallelle lijnen uit het aparte
lijnnetwerk. Aanwezige zekere lijnen mogen de schatting ook tegenspreken. Ontbrekende
lijnen blokkeren een gecontroleerde puntschatting niet. Afgeleide snijpunten
worden niet als extra waarnemingen gemaakt.

RANSAC-residuen van fitpunten, fouten op achtergehouden punten en lijnafstanden
behouden de bestaande grenzen: mediaan 0,5% en maximum 1% van de oorspronkelijke
beelddiagonaal, hier 11,01 en 22,03 pixels. Spreiding, oriëntatie, eindigheid,
matrixconditie en projectieve horizon worden gecontroleerd. Modelcontroles
blijven zelfconsistentie, geen onafhankelijke menselijke waarheid.

Daarna volgt Lucas–Kanade met piramides, voorwaartse/achterwaartse controle en
RANSAC, volgens de [OpenCV optical-flow-documentatie](https://docs.opencv.org/4.13.0/d4/dee/tutorial_optical_flow.html).
Kenmerken worden geselecteerd binnen gras én het eerder zichtbare veld, op
maximaal 960 pixels breed. Vereist: bidirectionele fout ≤1,5 pixel, minstens
20 RANSAC-inliers, minstens 60% inliers en ruimtelijke spreiding. Nieuwe zekere
punten en lijnen mogen een gevolgde schatting niet tegenspreken.

De matrix wordt berekend als `H_actueel = H_vorig × inverse(beweging)`, met de
gemeten beweging omgerekend naar bronpixels. Een kopie van de vorige matrix is
geen overbrugging. De leeftijd blijft gekoppeld aan de laatste zelfstandig
gecontroleerde herkenning, maximaal twee seconden. Camerawissels, slechte
overeenkomsten, ongeldige geometrie, ontbrekende opeenvolgende frames en het
verlopen van die termijn resetten de schatting. Een nieuwe geldige herkenning
start opnieuw. Bij onvoldoende tekstuur, langdurige close-up of een langere
puntuitval volgt dus bewust geen minimappositie.

Het 105 × 68-modelveld blijft een expliciete geometrische aanname. Uitvoer is
genormaliseerd; meters en snelheid worden niet geclaimd.

## Vergelijking en beslissing

De stappen gebruiken dezelfde nieuwe ruwe netwerkuitvoer. De echte oude run
blijft apart bewaard als baseline; alle detecties voor de nieuwe demo worden
uit die run hergebruikt. Het spelersnetwerk draait daarbij niet opnieuw.

| Stap | Intern geldige frames | Alle frames | Ontwikkelselectie |
|---|---:|---:|---:|
| Bestaande controle met twee lijnen | 0 / 1.239 | 0,0% | 0 / 10 |
| Gecontroleerde geometrie, confidence 0,3434 | 228 / 1.239 | 18,4% | 2 / 10 |
| Alleen confidence gewijzigd naar 0,25 | 277 / 1.239 | 22,4% | 2 / 10 |
| Gekozen geometrie plus camerabeweging | 252 / 1.239 | 20,3% | 2 / 10 |

Op de ontwikkelselectie is de uitkomst gelijk: daarom blijft de strengere
confidence **0,3434** behouden. De hogere dekking van 0,25 over de hele video
wordt beschrijvend gerapporteerd; de beoordelingsgroepen worden niet gebruikt
om toch die instelling te kiezen. Zonder menselijke labels is deze keuze
voorlopig. Instellingen worden vóór de beoordelingsreferenties vastgezet.

De mediane fout op de modelcontroles bij de gekozen directe schattingen is
4,21 pixels; het maximum is 18,31 pixels. Dit zijn geen menselijke projectiefouten.
De oorspronkelijke baseline strandt op 830 frames met te weinig punten, 24 met
inconsistente punten en 385 zonder twee gecontroleerde lijnen. Ook na de
verbetering ontbreken lange stukken met voldoende betrouwbare veldinformatie.
De nieuwe kandidaat blijft experimenteel.

Camerabeweging voegt 24 gevolgde frames toe aan 228 directe herkenningen. De
langste ononderbroken uitval blijft 16,64 seconden. De laatste extra lijncontrole
verwijdert vier frames uit de eerste technische kandidaat van 256 frames. Die
eerste poging blijft lokaal bewaard; de oplevering gebruikt de strengere controle.
De volledige nieuwe netwerkinference duurde 364,55 seconden op de RTX 4050 Laptop
GPU. De aparte afgeleide kalibratie en het renderen met detectiereplay hebben
hun eigen tijdmetingen; samenvoegen met de oude detector-runtime zou geen nieuwe
volledig gemeten end-to-endtijd opleveren.

De volledige actuele metingen, gewichten, omgeving, instellingen, afwijsredenen,
uitvalintervallen, verwerkingstijden en codehashes staan in
`reports/broadcast-field-experiment.json`. De gehashte ruwe modelbundel en alle
vier afgeleide JSONL-bestanden staan lokaal onder `artifacts/broadcast-field-v2`.
De dedicated worker kan een ander diagnostisch RANSAC-resultaat tellen dan de
hoofdomgeving; de vergelijkende stappen gebruiken allemaal dezelfde hoofdomgeving.

## Zelf visueel controleren

Start de bestaande lokale app met
`.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py`. Kies bovenaan
**Een opgeslagen veldtest visueel openen**, en selecteer de nieuwste voltooide
veldtest. Uploaden en opnieuw verwerken zijn daarvoor niet nodig.

1. Speel de samengestelde video af, pauzeer en zoek naar een interessant moment.
2. Gebruik **Exact bronframe** of spring naar een mislukt interval. Het originele
   beeld, de overlay en minimap horen bij exact hetzelfde frame.
3. Geel toont herkende veldpunten, paars gevolgde grasveldkenmerken en blauw
   teruggeprojecteerde veldlijnen. Punten zijn afzonderlijk uitzetbaar.
4. Controleer de status **Opnieuw herkend**, **Gevolgd met camerabeweging** of
   **Veldpositie onbekend**, plus afwijsreden, aantallen en tijd sinds herkenning.
5. Kies de ontwikkel- of beoordelingsset en spring naar een vooraf gekozen frame.
   Selecteer een bekend vlak veldpunt op het schema en klik het in het bronbeeld.
   Gebruik minstens twee verschillende zichtbare punten per kalibreerbaar frame.
   Niet-kalibreerbare beelden krijgen geen verzonnen controlepunten.
6. Vul je naam in en sla jouw beoordeling van ieder frame expliciet op. Alleen
   na alle beoordelingen en jouw bevestiging krijgt de hele set `human_reviewed`.
   De beoordelingsset vraagt eerst de instellingen vast te zetten. Bij afronding
   maakt de app het gemeten evaluatierapport.

Referenties staan in `data/field-reviews/VIDEOHASH/`, los van modelinvoer en van
de onveranderlijke runbestanden. Ontwikkelreferenties hebben `used_for_tuning: true`;
de formele evaluator weigert die als onafhankelijke beoordeling. Referenties zijn
aan de kandidaat gekoppeld. De beoordelaar ziet de visuele uitvoer; deze procedure
claimt geen geblindeerde annotatie of extern auditregister.

Het evaluatierapport telt correcte uitvoer binnen de foutgrenzen én de dekking op
menselijk kalibreerbaar verklaarde frames. Ook ontbrekende uitvoer, onterecht
geldige uitvoer en de ruwe uitvoerdekking worden gerapporteerd. Menselijke
inhoudelijke acceptatie wordt niet automatisch ingevuld.

## Reproduceren en softwarecontrole

```powershell
.\.venv\Scripts\python.exe -m football_pipeline calibrate-auto "C:\Users\raoul\Downloads\Broadcast video.mp4" --output data/field-calibration-v2 --source "Lokaal aangeleverd door gebruiker" --usage "Lokale ontwikkeling; publicatierechten niet bevestigd"
.\.venv\Scripts\python.exe scripts/broadcast_field_experiment.py "C:\Users\raoul\Downloads\Broadcast video.mp4" --bundle data/field-calibration-v2/BUNDEL/automatic_calibration.json --baseline runs/9fd00e0e1f535a74b32902671872843928a24866902f284c644ed9e9c9d3d107
```

Voor gecontroleerde herkalibratie biedt de CLI `--recalibrate-replay` samen met
`--replay-run` en eventueel `--field-settings PROFIEL.json`. Gewone replay blijft
dezelfde kalibratie-identiteit eisen. Een andere video, detector of modelinstelling
wordt afgewezen. Instellingen en afgeleide kalibraties zitten in runidentiteit,
uitvoerhashes en replay; wijzigingen krijgen een andere cache-identiteit.

Nieuwe ruwe modelbundels gebruiken schema 2, framekalibraties schema 2 en runs
schema 3. Oude bundels behouden standaard hun oude schatter en identiteit.
Bestaande handmatige kalibraties blijven in de handmatige workflow bruikbaar.

De softwaretests controleren echte OpenCV-beweging op synthetische tekstuur,
pan/zoom, puntuitval, leeftijd, drift, camerawissels, onscherpte, lijntegenspraak,
inliereisen, herstel, lege frames, nieuwe en oude replay, referentieopslag,
de framekiezer en de handmatige workflow. Synthetische tests bewijzen de
softwarewerking; ze vervangen geen beoordeling van de echte voetbalbeelden.

Voor de echte clip zijn nog geen handmatige scenarioannotaties voor camerawissels
of close-ups beschikbaar; daarvoor wordt geen echte scenariodekking geclaimd.
De uiteindelijke softwarecontrole slaagt met 141 tests en 4 subtests. Beide
oplevervideo's bevatten exact 1.239 H.264-frames op 25 fps en 1920 × 720.
Video's, referentie-invoer en volledige framegegevens blijven lokaal beschikbaar
onder `artifacts/broadcast-field-v2` en de in het JSON-rapport genoemde runmap.
