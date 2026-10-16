# Spelers tellen met rolherkenning en veldherkenning

De telling gebruikt twee verschillende voorspellingen: **welke rol de detector geeft** en **of het voetpunt binnen het geldige veld ligt**. Een steward op het veld blijft een steward als de detector die rol correct aanlevert. De veldlocatie verandert de rol nooit automatisch in `player`.

## Wat de huidige gewichten werkelijk herkennen

Het geleverde `artifacts/players-v2/players_best.pt` heeft exact twee uitvoerklassen:

| Klasse-ID | Werkelijke naam | Betekenis van de trainingslabels |
|---|---|---|
| 0 | `player` | Veldspelers en beide doelmannen |
| 1 | `referee` | Centrale scheidsrechter en de bevestigde nabije lijnrechter, samen in één klasse |

Er is **geen afzonderlijke getrainde klasse** voor `assistant_referee`, `steward`, `spectator` of `staff`. De pipeline kan deze rollen verwerken zodra een detector ze werkelijk levert. De extra ondersteuning is geen bewijs dat de bestaande gewichten deze personen herkennen.

Ook de bestaande officialherkenning is nog beperkt. Op de twaalf validatiebeelden met gedeeltelijke officiallabels haalt de geselecteerde run bij confidence 0,25 en matching-IoU 0,50 **10 TP, 0 FP en 14 FN** voor de gezamenlijke klasse `referee`: recall 41,67%. Dit bewijst geen volledige herkenning van centrale scheidsrechters en beide lijnrechters. Zie [de volledige resultaten](Resultaten_Spelermodel.md) en `reports/players-experiments/EXP-P004/validation-metrics/metrics.json`.

Als een steward ten onrechte de voorspelling `player` krijgt en zijn voetpunt binnen het veld ligt, kan hij nog meetellen. Die fout vraagt nieuwe betrouwbare rollabels en modeltraining of een afzonderlijk gevalideerde rolclassifier. De veldfilter kan die classificatiefout niet oplossen. Er worden geen stewards of supporters als achtergrondlabel verzonnen op basis van alleen kleding, afstand of positie.

## Concrete telregels

| Geval | Spelertelling | Spelertracking | Bronbeeld/detectierecord |
|---|---|---|---|
| `player`, geldig voetpunt binnen veld, zichtbaar boven weergavedrempel | Telt mee | Kandidaat voor ByteTrack | Blijft aanwezig |
| Doelman met rol `player`, dezelfde voorwaarden | Telt mee | Dezelfde spelerklasse | Blijft aanwezig |
| `player` buiten veld | Telt niet mee | Geen actuele speler-ID | Blijft aanwezig met `outside_field` |
| `referee` of `assistant_referee`, ook binnen veld | Telt niet mee | Geen speler-ID | Eigen rol en eventuele veldpositie blijven aanwezig |
| `steward`, `spectator`, `staff` of generieke `person`, ook binnen veld | Telt niet mee | Geen speler-ID | Eigen rol en eventuele veldpositie blijven aanwezig |
| Ongeldige box, afgesneden voeten of ongeldige projectie | Telt niet mee | Geen actuele speler-ID | Afwijsreden blijft aanwezig |
| Geen geldige actuele veldherkenning | **Onbekend**, niet nul | Geen projecteerbare spelerkandidaten | Detecties blijven aanwezig |
| Profiel zonder expliciete `player`-klasse | **Onbekend**, niet nul | Niet toegestaan | Bijvoorbeeld generieke `person`-detecties blijven aanwezig |
| Geldig veld, geen detecties | Nul | Lege trackerupdate | Framerecord met lege detectielijst |

Een voetpunt is het midden van de onderrand van de box in het oorspronkelijke bronbeeld. Bij handmatige kalibratie controleert de bestaande geometrie ook het veldpolygon. Bij automatische kalibratie gebruikt de filter de homography van dat actuele frame en het genormaliseerde bereik `0 <= u,v <= 1`. Een veldpunt op de grens mag meetellen. Het gras buiten de lijnen is geen speelveld.

Dit is een aantal **actuele gedetecteerde spelers**. Het is geen gegarandeerd aantal unieke personen, geen gecontroleerde wedstrijdselectie en geen telling die ontbrekende spelers aanvult tot 22. Duplicaten en verkeerde modelrollen blijven mogelijke detectorfouten.

De detector bewaart kandidaten vanaf confidence 0,10. De normale weergave en telling gebruiken 0,25. Na toegelaten ByteTrack-matching blijft een actuele lagere-confidencewaarneming zichtbaar en telt zij mee als zij aan de rol- en veldvoorwaarden voldoet. Er worden geen alleen voorspelde trackerposities als waargenomen speler geteld.

## Afspraak met persoon 2

1. Lever per frame de actuele veldstatus en homography via de bestaande automatische kalibratie. Bij onbetrouwbare herkenning levert de veldmodule een andere status dan `valid`.
2. De pipeline projecteert **vóór** ByteTrack. Alleen `player` met geldige projectie gaat naar de spelertracker. Uitgesloten detecties blijven in het framerecord; hun index wordt correct teruggekoppeld na filtering.
3. Stewards, supporters en officials kunnen als afzonderlijke rol op beeld en minimap verschijnen wanneer het geladen model die echte klasse levert. Een generieke `person` mag via een manifest niet stilzwijgend worden hernoemd naar een van deze rollen.
4. De automatische cameramodus houdt haar bestaande trackingblokkade totdat cameracompensatie is gevalideerd. Deze wijziging heft de menselijke MVP-acceptatie en andere bestaande controles niet op.
5. De veldherkenningscode, bronnen, beeldafmetingen, datasetlabels en gewichten zijn voor deze wijziging niet aangepast. Een andere video behoudt haar eigen kalibratievereiste.

## Uitvoer voor telling en controle

`framegegevens.jsonl` bevat aanvullend per frame `player_summary`:

```json
{
  "status": "available",
  "on_field": 18,
  "visible_player_candidates": 20,
  "outside_field": 2,
  "unlocated": 0,
  "other_roles": {"referee": 1},
  "display_confidence": 0.25,
  "include_matched_low_confidence": true
}
```

Dit is een formaatvoorbeeld, geen meting van de voetbalvideo. Bij ontbrekende geldige veldherkenning wordt `status` gelijk aan `field_unavailable` en `on_field` gelijk aan `null`. Ook `outside_field` wordt dan `null`: zonder veld is die indeling niet betrouwbaar. `other_roles` telt zichtbare detecties per andere rol over het hele bronbeeld.

Een profiel zonder expliciete `player`-klasse krijgt `player_model_available: false` in het framerecord en samenvattingsstatus `player_model_unavailable`, eveneens met een onbekend spelersaantal. Een lege lijst generieke personen wordt dus niet als bewijs voor nul spelers gebruikt. Bij het opnieuw openen van opgeslagen frames worden afgeleide telvelden opnieuw berekend; zij gelden niet als invoer voor de detector of tracker.

Ieder detectierecord krijgt `counted_as_player` en `player_exclusion_reason`, bijvoorbeeld `not_player`, `outside_field`, `calibration_unavailable`, `truncated_bottom` of `below_display_confidence`. De modelklasse, confidence en oorspronkelijke box blijven beschikbaar. De minimap gebruikt dezelfde telling als de JSON-uitvoer.

Het runmanifest bevat `player_policy`. De policy en de gewijzigde broncode zitten in de cache-identiteit. Oude video's worden daarom niet stilzwijgend opnieuw gebruikt als resultaat van de nieuwe telregels. Een toegelaten detectiereplay herberekent projectie en telling met de actuele kalibratie; oude getelde aantallen worden niet overgenomen.

De ruwe detectoroverdracht van persoon 1 in `reports/handoff/players-v2` bevat nog geen veldfilter. Gebruik voor de telling de geïntegreerde `framegegevens.jsonl` of dezelfde functies in `football_pipeline.participants` na projectie.

## Verificatie en resterend werk

De regressietests controleren rollen binnen het veld, spelers buiten het veld, lage scores, lege frames, veldverlies/herstel, veranderende framegeometrie, afgesneden voeten en de detectie-indexen van de echte ByteTrack-implementatie. De volledige verwerkingsproeven gebruiken expliciet synthetische detectoruitvoer en echte video-encoding. Zij bewijzen de telregels en softwarekoppeling, geen nauwkeurigheid voor stewards of supporters.

De volledige suite slaagt met **162 tests en 4 subtests**. De afzonderlijke JUnit-uitvoer staat in `reports/players-experiments/field-role-software-tests.xml`; bronhashes en de afbakening van dit bewijs staan in `reports/players-experiments/field-role-software-validation.json`. Ruff en de dependencycontrole slagen eveneens.

Voor echte extra rolherkenning blijft nodig: een gereviewde uitbreiding van de klassen en annotaties, een expliciete beslissing over de datasetomvang, training met die klassen, validatie op voldoende afzonderlijke voorbeelden en een nieuwe overdracht met werkelijke namen en gewichtshash. De bestaande onafhankelijke eindtestbeperking blijft gelden; bestaande gereserveerde beelden worden niet opnieuw als onaangeroerde eindtest voorgesteld.
