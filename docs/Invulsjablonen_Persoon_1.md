# Invulsjablonen voor persoon 1

Kopieer de gewenste sectie voor een echt record. `INVULLEN` en lege tabellen zijn geen bewijs. Gebruik echte bronlinks, reviewerhandelingen en runresultaten. Raadpleeg [het werkplan](01_Persoon_1_Data_Model_Evaluatie.md) voor de besliscriteria.

## 1. Beslisrecord

| Veld | Inhoud |
|---|---|
| Besluit-ID | DEC-INVULLEN |
| Vraag en aanleiding | INVULLEN |
| Onderzochte alternatieven | INVULLEN |
| Bewijs: frames, run of bron | INVULLEN |
| Gekozen route en reden | INVULLEN |
| Afgewezen route en reden | INVULLEN |
| Eigenaar / reviewer | INVULLEN |
| Status en datum | INVULLEN |
| Gevolgen voor data en overdracht | INVULLEN |

## 2. Bronnenregister en video

| Bronlink | Camera en fragment | Veldpunten | Labelbaarheid | Gebruik/toegang | Besluit en reden |
|---|---|---|---|---|---|

Bewaar bij de gekozen video bron-ID, bestandsnaam, SHA-256, resolutie, tijdsbasis, werkelijke duur, clipgrenzen en conversie. Noteer apart wie de bron koos en of persoon 2 de geometrie werkelijk heeft gecontroleerd.

## 3. Baseline en keuze van de data gap

| Kandidaattarget | Echte foutvoorbeelden | Relevantie | Labelbaarheid | Variatie | Besluit |
|---|---|---|---|---|---|

Voeg modelidentiteit, gewichtenchecksum, softwareversie, ontwikkelfragment en inference-instellingen toe. Aantallen voorspellingen bewijzen zonder referentielabels geen recall, precision of mAP.

## 4. Proefannotatie en labelregels

| Proefframe | Moeilijk geval | Annotator A | Annotator B | Verschil | Eindregel / reviewer |
|---|---|---|---|---|---|

Controleer zes gevallen: duidelijk object, klein object, occlusion, blur, beeldrand en werkelijke afwezigheid. Leg aanwezigheid, klasse en boxbegrenzing vast. Bewaar automatische voorstellen naast menselijke correcties.

| Regelversie | Klasse | Inclusie / exclusie | Boxdefinitie | Occlusion / blur / rand | Voorbeelden |
|---|---|---|---|---|---|

## 5. Frame- en splitmanifest

De software schrijft het manifest bij extractie. Benodigde velden zijn `frame_id`, `video_id`, `frame_index`, `timestamp_s`, `width`, `height`, `group_id`, `split`, `image`, `label`, `label_status`, `annotator`, `reviewer`, `review_status` en `selection_reason`.

| Subset | Fragmentgroepen | Frames | Objecten per klasse | Negatieven | Moeilijke situaties | Beperking |
|---|---|---|---|---|---|---|

Noteer de goedgekeurde datasetfingerprint, overlapcontrole, onderzoek van groepsgrenzen en conclusie over generalisatie. Een vaste tijdafstand alleen is geen bewijs van onafhankelijke beelden.

## 6. Reviewlog

| Frame / pakket | Annotator | Reviewer | Gevonden probleem | Correctie | Hercontrole | Status |
|---|---|---|---|---|---|---|

De annotatietool maakt daarnaast `review-history.jsonl`. Vul geen menselijke namen in voor werk dat alleen een model of AI uitvoerde. Veranderde annotaties moeten opnieuw worden gereviewd.

## 7. Experimentrecord

| Veld | Inhoud |
|---|---|
| Experiment-ID / eigenaar / reviewer | EXP-INVULLEN |
| Vraag en hypothese | INVULLEN |
| Referentierun | INVULLEN |
| Precies één hoofdwijziging | INVULLEN |
| Gelijk gehouden omstandigheden | INVULLEN |
| Verwachte uitkomst en beslisregel | INVULLEN vóór uitvoering |
| Code / dataset / split / gewichten | INVULLEN met versies en checksums |
| Omgeving / werkelijk geheugen / duur | INVULLEN na uitvoering |
| Werkelijke trainings- en evaluatie-instellingen | Verwijzing naar bewaarde configuraties |
| Metrics en concrete verbeteringen/regressies | Alleen gemeten waarden |
| Conclusie, onzekerheid en vervolg | INVULLEN |

## 8. Resultaten en modelvergelijking

| Run | Subset / versie | Klasse | Frames / objecten | mAP@50 | mAP@50:95 | Precision / werkpunt | Recall / werkpunt |
|---|---|---|---|---|---|---|---|

Schrijf bij ontbrekende metingen `nog niet gemeten`, nooit `0`. Leg evaluator, class mapping, resolutie, confidence-ondergrens, NMS en maximale detecties vast. Bij andere labels is een nieuwe referentiemeting nodig.

## 9. Foutencatalogus

| Veld | Inhoud |
|---|---|
| Fout-ID / run / frame | ERR-INVULLEN |
| Fouttype en vaste matchingregels | INVULLEN |
| Waarneming | Wat op het beeld en in de labels zichtbaar is |
| Hypothese | Vermoedelijke oorzaak, niet als bewezen formuleren |
| Alternatieve verklaring | INVULLEN |
| Onderscheidende controle | INVULLEN |
| Experiment en uitkomst | Verwijzing naar EXP-record of nog open |

## 10. Overdrachtscontrole

| Controle | Verwacht | Werkelijk bewijs | Reviewer / status |
|---|---|---|---|
| Video-identiteit | Dezelfde bronchecksum | INVULLEN | INVULLEN |
| Normaal frame | Boxen op oorspronkelijke beeldcoördinaten | INVULLEN | INVULLEN |
| Moeilijk frame | Beperkingen correct uitgelegd | INVULLEN | INVULLEN |
| Lege uitvoer | Framerecord met lege lijst blijft aanwezig | INVULLEN | INVULLEN |
| Tijd en synchronisatie | Zelfde bronmoment | INVULLEN | INVULLEN |
| Modelrollen | Noodzakelijke klassen behouden | INVULLEN | INVULLEN |

## 11. Freeze en eindclaim

Leg code, datasetfingerprint, gewichtenchecksum, inferenceconfiguratie, kalibratieversie en reviewers vast vóór de onafhankelijke eindtest. Bewaar het testtoegangslog. Noteer na de test wat wel en niet wordt ondersteund; een aangepast model op dezelfde beelden is een nieuwe onderzoeksronde.

## 12. GenAI en feedback

| AI-ID / datum | Tool / model indien bekend | Werkelijke prompt | Betrokken onderdeel | Overgenomen / gewijzigd / verworpen | Eigen controle |
|---|---|---|---|---|---|

| Feedback / datum | Herkomst | Besluit | Concrete aanpassing | Bewijs van controle |
|---|---|---|---|---|

Bewaar drie tot vijf echte representatieve prompts. Vermeld ook hulp bij plan, code, tests en verslag. AI-gegenereerde tests en een geslaagde uitvoering vervangen het begrip en de review van beide studenten niet.
