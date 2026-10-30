# Hervatten — broadcastbetrouwbaarheid, 30 oktober 2026

## Actuele stand

**Dag 10: inhoudelijk afgerond; Git-overdracht is de laatste stap. Daarna blijven nul werkfasen over in deze ronde.** Dagen betekenen werkfasen, geen kalenderdagen. De gebruiker heeft commit en push expliciet gevraagd. Het halen van de modeldoelen is niet hetzelfde als het afronden van deze onderzoeksronde: `targets_met` blijft false.

Branch: `codex/broadcast-reliability-20261030`. Origin: `https://github.com/JorreVanDyck10/Messi10.git`. Uitgangspunt: main op `4a3f9e51a7be76d4d943e0cafbd4af9b4e706739`. Voor de eerste commit is push dry-run geslaagd. De exacte overgedragen commits staan na de push in het Git-log en worden aan de gebruiker gemeld. Geen merge naar main aangevraagd.

Lees eerst [de actuele resultaten](Broadcast_Betrouwbaarheid_20261030.md). Het [verslag van 28 oktober](Broadcast_Betrouwbaarheid_Resultaten.md) is historisch: de daar voorlopig geselecteerde rank-bridge is op 30 oktober **afgewezen en uit het standaardprofiel verwijderd**. Oude acceptatiecijfers of de run met 255 geldige eigen frames beschrijven die proef, niet het huidige standaardbeleid.

## Limiet en processen

De gebruiker wil tot circa 5–10% resterend vijf-uursbudget werken, met tijd voor push, verificatie en een bruikbaar hervatpunt. Laatste controle vóór Git-afronding: 19% resterend. Controleer opnieuw bij hervatten; dit percentage veroudert. Gebruik geen resetcredits. Start bij circa 10% geen lange nieuwe proef.

Alle in deze ronde gestarte trainingen, inferenties en lokale tests zijn afgerond. Er hoeft geen lokaal proces door te lopen. Bewaar `data`, `artifacts`, `.cache`, `runs` en afgewezen gewichten. Zware datasets, modellen en caches blijven bewust lokaal; compacte rapporten en scripts gaan naar Git.

## Standaardbeleid en uitkomst

- `configs/models-broadcast.json` is inhoudelijk exact gelijk aan het oorspronkelijke geladen profiel uit `artifacts/broadcast-reliability-day2/baseline-before-field-profile.json`. Zie `reports/broadcast-reliability-20261030/profile-restoration.json`.
- Zonder expliciete aanroep- of veldruntime-instelling geldt `DEFAULT_SETTINGS`, met `holdout_rule=two_semantic_tertiles_no_refit`. Detector-, rol-, team- en trackergewichten zijn niet vervangen. Boxfusie blijft 0,5; tracker `match_thresh` 0,8; contextdrempel 0,99.
- Optionele veldinstellingen per modelprofiel blijven ondersteund: expliciete aanroep gaat vóór veldruntime, daarna modelprofiel. `configs/field-motion-rank.json` is uitsluitend een expliciete onderzoeksoptie. Een regressietest bewaakt het standaardbeleid.
- De extra rank-bridgeframes 90 en 92 van SNGS-078 vallen beide buiten de vaste providerlijntolerantie. De 22 extra spelerwaarnemingen wegen niet op tegen de gefaalde grens voor extra projecties buiten tolerantie. Op de nieuwe 1.800 beelden verandert rank-bridge geen projectie.

## Voltooide metingen

De oude 900 en nieuwe 1.800 beelden vormen samen 2.700 beelden: begin-, midden- en eindvensters van zes seconden uit zes bestaande clips. Training: SNGS-060/097/151. Validatie: SNGS-021/039/078. Geen frame-ID/hashoverlap tussen de nieuwe en oude beelden; geen wedstrijdoverlap tussen splits. Dit blijven eerder gebruikte ontwikkelwedstrijden, geen onafhankelijke eindtest.

Huidige automatische keten op 1.350 validatieframes / 19.874 spelerwaarnemingen:

- Precision 93,4641%; recall 82,4595%; correct gevonden én correct team / alle spelers 78,4995%.
- 16.388 TP, 1.146 FP, 3.486 FN. Veld-IDF1 85,7791%, 35 wissels; beeld-IDF1 90,7406%, 44 wissels.
- Projectie beschikbaar op 1.185/1.350 frames. Gemiddelde absolute telfout op beschikbare frames 0,7283 spelers; totaal exact op 536/1.185 frames. Ontbrekende kalibratie is onbekend, niet nul.
- 381 keeperwaarnemingen correct ingedeeld, 179 verkeerd, op 979 referentiewaarnemingen.
- Veldlijnaudit: 596 binnen tolerantie, 561 erbuiten, 162 zonder projectie; 31 referenties buiten het ondersteunde bereik apart gehouden. Alle personenbeelden blijven in de herkenningsmeting.
- Eigen clip: 251/1.239 geldige veldframes (20,26%). Geen menselijke positie- of afstandsreferenties.

Providergeometrie geeft precision 93,9531%, recall 93,8160% en correct team / alle spelers 89,4687%. Het is een voorwaardelijke vergelijking om geometrie te onderzoeken, geen automatische veldnauwkeurigheid of gegarandeerde bovengrens.

De runtime-score volgt de echte appregel, inclusief gekoppelde detecties onder 0,25. Oude confidence-0,25-scores blijven apart reproduceerbaar. Voor latere automatische beelden zijn native waarnemingen alleen hergebruikt nadat exacte gelijkheid van alle projectie-inputs met DEFAULT bewezen was. Geen gewijzigde geometrie als nieuwe inference voorgesteld.

## Niet gekozen en wel bewaard

Backward backfill, track-/kleurmodellen, crop/pixelpaint, sparse veldhead, head-ensemble en contextdrempel 0,95 faalden minstens één vooraf gebruikte poort. De volledige-layout-motionproef gaf geen extra projectie op 2.700 gelabelde beelden; de zeven gewonnen eigen frames hebben geen nauwkeurigheidsreferentie. Ook die blijft uit de standaard. Zie de aparte `*-rejected.json`-rapporten en bronmomentopnamen in `reports/broadcast-reliability-20261030`.

De sparse head gebruikte 1.024 bestaande beelden uit 289 trainingswedstrijden (231 train, 58 interne holdout). De gekozen gewichten en featurecache blijven onder `artifacts/broadcast-reliability-20261030/sparse-field-head-v1`. Validatie koos geen checkpoint. Herhaal deze training niet zonder nieuw onderzoeksdoel.

## Reproduceren en controleren

Werkmap `C:/Messi10`; Python `.venv/Scripts/python.exe`; `PYTHONPATH=src;.;scripts` voor de evaluatiescripts. Veldnetwerkinferentie gebruikte waar nodig `.tools/pnlcalib-env/Scripts/python.exe`; volg de vastgelegde runtime/bronhashes, installeer niet stilzwijgend andere versies.

Belangrijkste ingangen:

- `scripts/prepare_temporal_extension.py`: vaste latere vensters en download-/splitcontrole.
- `scripts/evaluate_temporal_extension_field.py`: gecachte veldwaarnemingen, baseline/layoutvergelijking en referentiebereik.
- `scripts/audit_motion_rank_release.py`: DEFAULT tegenover de historische rank-bridge op alle 2.700 beelden.
- `scripts/evaluate_temporal_broadcast.py` en `scripts/score_broadcast_runtime.py`: native detectie/tracking en runtimeconforme score.
- `scripts/summarize_broadcast_reliability.py`: actuele aggregatie naar `reports/broadcast-reliability-20261030/summary.json`.
- `scripts/verify_broadcast_release.py`: uitsluitend de historische rank-bridgeproef, niet de actuele standaardselectie.

Bronmanifesten: `data/broadcast-temporal-v1/manifest.json` en `data/broadcast-temporal-v2/manifest.json`. Nieuwe fingerprint: `7753f1295304e3325d0a8d0390dad025d6df7f858992bbb2908659681acfb015`. Nieuwe manifest-SHA256: `d167ede2a68fa2e97f0ca10f967df0a541da20590b15bb68d6a99f3dd4e8dfbc`.

Actuele scores gebruiken `runtime-default-first-v1`, `runtime-provider-baseline-v1`, `runtime-extension-automatic-v1` en `runtime-extension-provider-v1` onder `artifacts/broadcast-reliability-20261030`. `runtime-baseline-v1` is de tijdelijke rank-bridge en mag niet als huidige standaard worden gelabeld. De releaseaudit bewaart `default-states.json` per venster. Volledige inference en caches zijn af; voer ze niet opnieuw uit om alleen een verslag te herstellen.

Na profielherstel: **455 tests en 4 subtests geslaagd**; `reports/broadcast-reliability-20261030/final-tests.xml`. Ruff check/format slagen; doctor controleerde FFmpeg/FFprobe en geïnstalleerde afhankelijkheden. Herhaal de volledige suite alleen bij nieuwe codewijzigingen of een concrete fout. Een documentwijziging vereist geen nieuwe modelinferentie.

## Na deze ronde

Er zijn nul fasen over in het afgesproken plan, maar geen onderbouwde einddatum voor alle modeldoelen. Grootste vervolgvraag is betrouwbare veldprojectie op de eigen camera, daarna officials/keeperteams en identiteitsbehoud over langere tijd. Een volgende ronde heeft nieuwe onafhankelijke referenties nodig voor acceptatie en afstandsclaims. Menselijke review, onafhankelijke eindtest en afstandsvalidatie zijn niet voltooid.

Controleer bij hervatten eerst `git status --short`, branch en remote; behoud lokale resultaten. Gebruik de actuele samenvatting en dit document boven historische acceptaties. De scope `on_pitch_players` toont uitsluitend getelde veldspelers; een leeg overlay bij ongeldige kalibratie betekent niet dat ruwe detecties zijn verwijderd. Dat gedrag is deze ronde niet gewijzigd.
