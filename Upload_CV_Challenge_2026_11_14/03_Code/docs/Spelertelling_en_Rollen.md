# Spelers tellen met rolherkenning en veldherkenning

**Actuele uitbreiding:** [R007 gebruikt nu een werkelijk getrainde aanvullende rolclassifier en teamindeling](Resultaten_Rollen_en_Teams.md), gekozen met `-Recognition players`. De paragraaf hieronder over twee uitvoerklassen beschrijft de behouden P004-basisdetector. Het rolprofiel combineert die met een persoonsdetector en zes classifieruitgangen: `player`, `referee`, `assistant_referee`, `steward`, `spectator`, `person`. De algemene persoonsroute van persoon 2 blijft daarnaast beschikbaar. Locatie op zichzelf bewijst geen spelersrol. De nieuwe metingen vervangen geen menselijke review of onafhankelijke eindtest.

De telling gebruikt twee verschillende voorspellingen: **welke rol de detector geeft** en **of het voetpunt binnen het geldige veld ligt**. Een steward op het veld blijft een steward als de detector die rol correct aanlevert. De veldlocatie verandert de rol nooit automatisch in `player`.

## Behouden P004-basisdetector en latere uitbreiding

Het geleverde `artifacts/players-v2/players_best.pt` heeft exact twee uitvoerklassen:

| Klasse-ID | Werkelijke naam | Betekenis van de trainingslabels |
|---|---|---|
| 0 | `player` | Veldspelers en beide doelmannen |
| 1 | `referee` | Centrale scheidsrechter en de bevestigde nabije lijnrechter, samen in één klasse |

De P004-basisdetector heeft geen afzonderlijke uitgangen voor lijnrechter, steward of supporter. Die worden nu door de aanvullende getrainde classifier geleverd. `staff` heeft nog geen eigen getrainde uitgang; zulke onduidelijke personen kunnen `person` blijven. De betrouwbaarheid verschilt sterk per rol; zie de actuele resultaten.

Ook de bestaande officialherkenning is nog beperkt. Op de twaalf validatiebeelden met gedeeltelijke officiallabels haalt de geselecteerde run bij confidence 0,25 en matching-IoU 0,50 **10 TP, 0 FP en 14 FN** voor de gezamenlijke klasse `referee`: recall 41,67%. Dit bewijst geen volledige herkenning van centrale scheidsrechters en beide lijnrechters. Zie [de volledige resultaten](Resultaten_Spelermodel.md) en `reports/players-experiments/EXP-P004/validation-metrics/metrics.json`.

Als een steward ten onrechte de voorspelling `player` krijgt en zijn voetpunt binnen het veld ligt, kan hij nog meetellen. De veldfilter kan zo’n classificatiefout niet oplossen. De echte aanvullende training is uitgevoerd; verdere representatieve rollabels en evaluatie blijven nodig voor betere betrouwbaarheid. Er worden geen achtergrondlabels verzonnen op basis van alleen kleding, afstand of positie.

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
4. De automatische cameramodus gebruikt inmiddels cameragecompenseerde tracking met tijdelijke ID’s en resets bij camerawissels. De handmatige modus behoudt haar menselijke MVP-acceptatie. Onderdeel 3 voegt [teamindeling en telling per team](Teams_Tracking_en_Telling.md) toe zonder deze telregels te veranderen.
5. De afzonderlijke rolclassificatie, datasets en modelprofielen zijn toegevoegd. De veldherkenningsalgoritmen blijven behouden; iedere video behoudt haar eigen kalibratievereiste. Bronnen, modelkeuzes en evaluatiebeperkingen staan in de afzonderlijke resultatenverslagen.

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

De oorspronkelijke filtercontrole slaagde met 162 tests en 4 subtests. De uitgebreide rol-/teamversie slaagt met **199 tests en 4 subtests**; de actuele uitvoer staat in `reports/appearance-experiments/software-tests.xml`. De eerdere uitvoer onder `reports/players-experiments/field-role-*` blijft historische software-evidence. Ruff en de dependencycontrole slagen eveneens.

De extra training en overdracht zijn nu uitgevoerd. De totale selectie omvat 80 bronbeelden; menselijke review, betere supporter-/officialdekking en onafhankelijke eindevaluatie blijven open. De bestaande eindtestbeperking blijft gelden; bestaande gereserveerde beelden worden niet opnieuw als onaangeroerde eindtest voorgesteld.
