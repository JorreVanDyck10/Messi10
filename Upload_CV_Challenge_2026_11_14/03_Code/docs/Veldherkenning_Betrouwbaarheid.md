# Onderdeel 2: betrouwbare veldherkenning en projectie

## Status op 26 oktober 2026

Het kandidaatprofiel `configs/field-reliability-candidate.json` voegt zichtbare
veldgrenzen en een temporele controle toe aan de bestaande kalibratie. Het is
**experimenteel en niet standaard geactiveerd**. De bestaande runtime en de
PnLCalib-releasegewichten zijn behouden. Spelerdetectie, training, teams, telling
en spelertracking zijn niet aangepast voor dit werkpakket.

Op dezelfde 1.239 broadcastframes geeft de herhaalde v2-baseline 251 intern
geldige projecties en de kandidaat 149. De kandidaat wijst 94 directe schattingen
af wegens tegenspraak met betrouwbare gemeten camerabeweging. Dat bewijst nog
niet dat deze schattingen werkelijk fout zijn. Op de 150 PANORIS-frames vinden
beide profielen onvoldoende veldpunten en blijven alle posities onbekend.

De vroegere 252/1.239 uit het broadcastrapport is een historische meting.
De huidige vergelijking herberekent beide profielen in dezelfde huidige
omgeving. Gebruik die gepaarde vergelijking voor deze wijziging.

Er zijn per videotype 30 beoordelingsframes geselecteerd, afzonderlijk van de
ontwikkelselectie. De bronnen waren al ontwikkelvideo's; dit is geen nieuwe
onafhankelijke eindtest. Er zijn **geen menselijke referenties ingevuld**.
Correcte dekking, werkelijke projectiefouten en de 90%-acceptatie blijven open.

## Werking en koppeling met persoon 3

Het bestaande publieke gebruik blijft werken:

```python
from football_pipeline.field_motion import CameraCalibration, RELIABLE_SETTINGS, estimate_checked
from football_pipeline.automatic_calibration import project_automatic

# Eén cameraobject per video; gebruik ieder opeenvolgend bronframe.
camera = CameraCalibration(fps, RELIABLE_SETTINGS)
direct = estimate_checked(observation, (width, height), RELIABLE_SETTINGS)
state = camera.update(frame, direct, frame_index)
project_automatic(detection, state, (width, height))
```

De aanroeper levert bestaande veldwaarnemingen en detecties in oorspronkelijke
beeldpixels. `CameraCalibration` houdt alleen camerageometrie bij; het beheert
geen spelers of teamidentiteiten. Projecteer alleen bestaande grondklassen.

| Veld | Betekenis |
|---|---|
| `field_position` | Genormaliseerde `[u,v]` binnen `[0,1]`, anders `null` |
| `projection_status` | Bestaande uitkomsten zoals `valid`, `outside_field`, `truncated_bottom`, `calibration_unavailable` |
| `calibration.status` | Alleen `valid` staat projectie toe; onder andere `temporal_disagreement` weigert projectie |
| `calibration.source` | `detected`, `tracked` of `unavailable` |
| `visible_field_polygon_xy` | Convex zichtbaar veldgebied in oorspronkelijke pixels, of `null` |
| `temporal_quality.status` | `consistent`, `motion_unavailable`, `camera_cut`, `frame_gap`, `temporal_disagreement`, `propagated`, `unavailable`, `no_previous_calibration` of `motion_disabled` |
| `reference_frame`, `age_s` | Laatste zelfstandig aanvaarde herkenning en leeftijd; bij uitval beide `null` |

Een eerste herkenning of herstel heeft `source=detected`. Die uitkomst kan
zonder vorige kalibratie worden geaccepteerd, maar claimt dan geen temporele
bevestiging. Bij te weinig bewegingsinformatie kan een zelfstandig gecontroleerde
directe herkenning geldig blijven; `motion_unavailable` maakt dat zichtbaar.

Het zichtbare veld ontstaat door het beeld te snijden met de homogene
veldgrenzen op dezelfde horizonzijde als de waargenomen veldpunten. Hiervoor
zijn geen zichtbare buitenhoeken nodig. Het voetpunt moet zowel binnen dit
polygon als binnen `[0,1]` vallen. De overlay gebruikt hetzelfde polygon.
Punten worden niet naar een veldrand verschoven.

Bij een directe herkenning met een vorige kalibratie wordt eerst optical flow
gemeten, zonder de nieuwe veldpunten in de bewegingsfit op te nemen. De twee
kalibraties worden vergeleken op de verplaatste ondersteuningspunten in
beeldpixels. Bestaande foutgrenzen blijven mediaan 0,5% en maximum 1% van de
beelddiagonaal. Een conflict wist de kalibratie. Er worden geen matrices gemiddeld.
Camerawissels worden ook bij directe herkenning gecontroleerd. Een nieuwe geldige
herkenning na een wissel start een nieuwe referentie; er is geen relatie met het
vorige camerastandpunt of een vaste fysieke doelidentiteit.

Overbrugging blijft maximaal twee seconden, met dezelfde eisen aan inliers,
spreiding en voorwaartse/achterwaartse beweging. Uitval, framegaten en verlopen
overbrugging wissen het camerageheugen. Meters, snelheid en herstel van
panoramische lensvervorming worden niet aangeboden.

## Kandidaat expliciet proberen

Voer vanuit de repository uit; vervang `data/wedstrijd.mp4` door de eigen video:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline process data/wedstrijd.mp4 --auto-field --field-settings configs/field-reliability-candidate.json --source "Eigen bron" --usage "Lokaal toegestaan gebruik" --models configs/models.json --output runs/field-candidate
```

Zonder dit expliciete profiel blijft het bestaande v2-profiel actief.
`field_settings.version=3` staat in het runmanifest; de afgeleide
kalibratieframes hebben `schema_version=3`. De versie van het ruwe
waarnemingsformaat verandert niet. De cache-identiteit bevat profiel en
geometriecode. Laden van `RUNMAP/calibration.json` herstelt het opgeslagen
profiel uit het bijbehorende runmanifest. Bestaande v1/v2-bundels en v2-beleid
blijven ondersteund; gewijzigde code levert een nieuwe berekeningsidentiteit.

Echte voorbeelden van geldige, ontbrekende en herstelde projectie staan in
`reports/field-reliability/handoff-examples.json`. Ze zijn modeluitvoer,
geen menselijke referentiewaarheid.

## Vergelijking herhalen en menselijke review

`scripts/compare_field_reliability.py` heeft vier opdrachten:

1. `prepare VIDEO --kind broadcast|fixed --output MAP [--selection JSON]` bevriest
   de bronhash, ontwikkel-/beoordelingsselectie, beide profielen en de geometriecode.
   Gebruik voor een nieuwe vergelijking een nieuwe map. Voor broadcast kan
   `configs/broadcast-field-selection.json` worden hergebruikt.
2. `run --bundle BUNDEL/automatic_calibration.json --detections RUNMAP/framegegevens.jsonl --output MAP`
   controleert de volledige bestaande run en herberekent beide profielen op
   dezelfde ruwe veldwaarnemingen en detecties. Het levert `baseline.jsonl`,
   `candidate.jsonl`, `comparison.json` en de gesynchroniseerde `comparison.mp4`.
   `--skip-video` laat alleen het renderen weg.
3. `export-review MAP` schrijft de geselecteerde oorspronkelijke beelden en een
   contactblad naar `review-frames`. De beelden bevatten geen modelvoorspellingen.
   `guide.json` bevat punt-ID's met hun bekende `[u,v]`.
4. `evaluate BROADCASTMAP VASTECAMERAMAP --output RAPPORT.json` berekent de
   menselijke vergelijkingsmetrics en de geschiktheid voor activering. Deze
   opdracht wijzigt geen runtimeconfiguratie.

De huidige concrete mappen zijn
`artifacts/field-reliability-20261026/broadcast` en
`artifacts/field-reliability-20261026/fixed`. Hun `comparison.json` bewaart de
gebruikte detectorrun en hun bronvideo. Beide gebruiken dezelfde ongewijzigde
releasegewichten en uitsluitend opgeslagen detecties.

De reviewer kopieert `reference-template.json` naar `human-reference.json` in
beide mappen. Beoordeel de volledige afzonderlijke bronbeelden in oorspronkelijke
pixels. Vul voor ieder geselecteerd frame `frame_index`, `calibratable`,
`human_reviewed: true` en `points` in. Gebruik voor ieder kalibreerbaar frame
minstens twee verschillende zichtbare, bekende veldpunten met `x,y,u,v`.
Niet-kalibreerbare frames krijgen `points: []`. Vul de eigen naam als `reviewer`
in en zet de overkoepelende `human_reviewed` pas op `true` na volledige review.
Bevestig zelf ook of de selectie overzicht, gedeeltelijk veld, afdekking en
herkenningsuitval voldoende vertegenwoordigt; deze categorieën zijn niet door
de software als menselijke labels ingevuld.

De bestaande functies `field_review.save_review` en `finalize_review` kunnen
hiervoor worden gebruikt met dit template. Zij bewaren beoordelingen apart
van modelinvoer. Verander de geselecteerde frames, bevroren tijdstippen en
`used_for_tuning: false` niet. Referenties van deze beoordeling mogen niet
achteraf voor parameterafstemming worden gebruikt.

```powershell
.\.venv\Scripts\python.exe scripts/compare_field_reliability.py evaluate artifacts/field-reliability-20261026/broadcast artifacts/field-reliability-20261026/fixed --output reports/field-reliability/comparison.json
```

De activeringscontrole vereist voor **beide** videotypes een bewezen verbetering
op dezelfde menselijke referenties. De correcte dekking mag maximaal vijf
procentpunten dalen. Minder foutieve projecties mogen geen hogere mediaan-,
p95- of maximumfout opleveren; lagere mediaanfout mag geen extra foutieve
projecties of hogere p95-/maximumfout opleveren. Zonder menselijke beoordeling
of meetbare projecties volgt geen positieve beslissing. Volledige acceptatie
vereist daarnaast minimaal 90% correcte dekking zonder foutief geaccepteerde
beoordelingsframes. De huidige beslissing is negatief wegens ontbrekende review.

## Controle en overdracht

De volledige testset slaagt met **244 tests en vier subtests**, inclusief geometrie, automatische
kalibratie, echte optical flow, pipeline, replay en de bestaande appcontroles.
Nieuwe regressietests behandelen semantische sprongen, horizonclipping,
afgesneden voeten, pan/zoom, camerawissels, herstel, ouderdom, opgeslagen
profielen, ongeldige referenties en de activeringsvoorwaarden.

De baseline met bestaande lokale wijzigingen is bewaard onder
`artifacts/field-reliability-baseline-20261026`. De oude cameraklasse is met de
AST van die snapshot vergeleken en is inhoudelijk gelijk. Runtime en werkelijke
gewichtshashes zijn opnieuw gecontroleerd. De bronvideo's en afgeleide media
blijven in de bestaande genegeerde lokale uitvoermappen.

De beperking op PANORIS is onvoldoende modelherkenning. Het huidige werk lost
dat niet op door bewijs te verzinnen of drempels te verlagen. Dit is een concrete
overdrachtsbevinding voor de verantwoordelijke voor de veldgewichten.
