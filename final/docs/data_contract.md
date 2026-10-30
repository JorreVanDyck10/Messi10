# Gegevenscontract en overdracht

Schema 1 gebruikt intern dataclasses uit `contracts.py` en per bronframe één JSON-object in UTF-8 JSON Lines. De originele clip wordt niet stilzwijgend gecropt, gespiegeld of geresampled.

| Veld | Betekenis |
|---|---|
| `frame_index` | Nulgebaseerde index binnen deze clip; ieder frame aanwezig |
| `timestamp_s` | `frame_index / fps`; FPS wordt als rationale bronwaarde bewaard |
| `image_size` | `[width,height]` van het oorspronkelijke frame |
| `detection_id` | Uniek per frame, normaal `frame_index:volgnummer` |
| `model_id` | Exact één modelrecord uit het runmanifest |
| `source_class_id` | Klasse-ID van dat specifieke model |
| `semantic_class` | Gezamenlijke betekenis; `person` is geen `player` |
| `bbox_xyxy` | Vier oorspronkelijke beeldpixels als floats, geen genormaliseerde YOLO-labelnotatie |
| `confidence` | Detectorconfidence, niet kans op correcte identiteit of veldpositie |
| `track_id` | Tijdelijke identiteit binnen één clip, anders null |
| `field_position` | `[u,v]` op het veld of null; geen meters |
| `projection_status` | `valid`, `invalid_box`, `outside_field`, `truncated_bottom`, `invalid_transform`, `not_ground_projected` |

Een lege detectielijst is geldig. Een ongeldige box wordt in de uitvoer vervangen door een lege box en confidence 0, met `invalid_box` voor te projecteren personen; zo bevat JSON geen NaN/Infinity. Het originele modelresultaat is niet bedoeld als geldige geometrische waarneming. Een bal/andere klasse wordt niet grondgeprojecteerd.

Veldfitpunten staan in vaste volgorde `(0,0),(1,0),(1,1),(0,1)`. `u` is de lengterichting en `v` de breedterichting. Controlepunten zijn verschillend van alle fitpunten en worden niet gebruikt om de matrix te schatten. Een review koppelt de kalibratie aan de videohash, een referentieframe en de gecontroleerde begin-/midden-/eindframes.

Het minimale handoverpakket van persoon 1 bevat videobron en hash, model/gewichtshash, werkelijke klassennamen, semantische mapping, voorbeeld-detecties, inferenceconfiguratie en dependencyversies. Voor de eindclaim horen dataset-/splitversie en de echte evaluatierun erbij. Klassewijzigingen en dependencywijzigingen vragen een gecoördineerde review.

Grote bestanden worden extern gedeeld volgens de toegangsrechten. Leg hun locatie, identiteit, versie en toegang vast; commit geen ruwe video's, gewichten, omgevingen of trainingsmappen. Onafhankelijke testdata wordt niet gebruikt voor deze integratie of parametertuning.


## Automatische framekalibratie (runmanifestversie 2)

De handmatige schema-1-kalibratie blijft beschikbaar. Automatische runs bevatten aanvullend een
`calibration`-object per frame met `frame_index`, `model_identity`, `status`, `homography` (3×3 of null),
`quality`, `points` en `lines`. `homography` projecteert oorspronkelijke beeldpixels naar hetzelfde
bestaande genormaliseerde veldstelsel. Een ongeldige kalibratie heeft altijd een null-matrix.

De statussen omvatten `valid`, `insufficient_points`, `insufficient_lines`, `inconsistent_points`,
`inconsistent_lines`, `degenerate_geometry`, `orientation_unknown` en `invalid_observation`.
Detecties behouden de bestaande velden. Bij een ontbrekende veldkalibratie hebben personen/spelers
`field_position=null` en `projection_status=calibration_unavailable`; er worden geen vorige posities herhaald.

Het automatische `calibration.json` bevat het bron-/modelmanifest. `observations.jsonl` bevat de
onveranderde semantische punt- en lijnwaarnemingen, gebonden aan videohash, resolutie en tijdlijn.
Replay controleert ook deze bundelidentiteit. Confidence en interne residuals gelden niet als
menselijk vastgestelde nauwkeurigheid. Zie `Automatische_Veldkalibratie.md` voor de beoordelingsprocedure.
