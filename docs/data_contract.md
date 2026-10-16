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
