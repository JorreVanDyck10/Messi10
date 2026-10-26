# Rolgegevens V3.1 — gecontroleerde uitvoering persoon 1

Deze versie bevat **1.621 ongeaugmenteerde persoonscrops uit 105 gebruikte bronbeelden**: 1.153 train en 468 validatie. Zij bewaart alle 1.528 crops van V2 en voegt 93 visueel door AI gecontroleerde crops toe. Menselijke review is niet uitgevoerd of ingevuld.

| Toegevoegde labels, huidige V3.1 | Train | Validatie |
|---|---:|---:|
| Steward | 4 | 6 |
| Supporter (`spectator`) | 43 | 30 |
| Generieke persoon, specifieke rol onvoldoende vastgesteld | 9 | 1 |
| Totaal | 56 | 37 |

De nieuwe gebruikte beelden bestaan uit elf voetbalbronfoto's, één aanvullende foto van eventstewards buiten voetbal en één frame uit de bestaande Commons-ontwikkelvideo. De eventfoto is een beperkte aanvullende rolbron, geen onafhankelijke voetbalwedstrijd. Een tweede eventfoto is als kandidaat bewaard maar niet in de labels opgenomen. Bronlicenties, auteurs, download-URL's, werkelijke beeldafmetingen en hashes staan in `source-provenance.json` en [ATTRIBUTION.md](ATTRIBUTION.md). De aanvullende videobron staat in `extracted-video-source.json`.

De uitsneden zijn **gedeeltelijke classificatiereferenties**: zij leveren geen complete boxannotatie van alle personen in de foto's en mogen niet rechtstreeks als volledige YOLO-detectielabels worden gebruikt. Suggesties komen van echte COCO-`person`-detectie; stoelen, fragmenten, duplicaten en gecombineerde personen zijn niet automatisch trainingswaarheid. Broncontext en individuele uitsnede zijn door AI bekeken. Een supporter met een shirt in teamkleur is niet automatisch een speler.

## Versies en splits

De extra foto-/eventgroepen zijn vóór de voorstellen en labels over train/val verdeeld in `configs/role-sources-v3.json`. Bestaande tijdgroepen en gereserveerde tests zijn behouden. Alle samples uit één foto/event blijven bij elkaar. V3 voegt geen teamlabels of nieuwe bekende wedstrijden voor de teamkop toe.

`manifest-v3.0.json` bewaart de versie waarmee R011/R012 zijn getraind. Bij verdere visuele controle bleek de specifieke rol van één persoon met fluorescerend vest niet betrouwbaar vast te stellen. V3.1 gebruikt daarom `person` in plaats van `spectator`; de wijziging staat in `label-corrections-v3.1.json`. Alleen dat **trainingslabel** veranderde. Validatielabels zijn niet aangepast. R013/R014 gebruiken V3.1. De oorspronkelijke voorstelbeslissingen staan in `ai-label-decisions.json`; pas voor de huidige versie de afzonderlijke correctie toe.

De bestaande NZ–Canada-ontwikkelclip bevat nu één roltrainingsframe. De volledige samenhangende sequentie mag dus niet als ongeziene eindtest van het geïntegreerde systeem worden gepresenteerd. Haar bronformaat of veldkalibratie is niet veranderd. Nieuwe fotoafmetingen krijgen evenmin een kalibratie van een andere video.

## Controle en menselijke review

De technische audit controleert hashes, leesbaarheid, boxgrenzen, klassebetekenis, dubbele crops en exact gekopieerde beelden onder verschillende bestandsnamen. De loader weigert een trainings-/validatiegroep of identieke bronbytes in beide subsets. Voor de bestaande spelerreferentie zijn ook visuele hashkandidaten en tijdafstanden onderzocht; dit bewijst geen algemene onafhankelijkheid tussen wedstrijden.

Alle 1.621 rolcrops staan als **nog te reviewen** in `reports/person1-round3/data-audit-final/human-review.csv`. De 93 nieuwe crops en hun context staan in `new-crops/` naast dat bestand. Zie [de reviewinstructies](REVIEW.md). Er zijn geen reviewersnamen, inter-annotatorovereenstemming of menselijke goedkeuring verzonnen.

## Trainen en vergelijken

Na installatie volgens de project-README en `git lfs pull`, vanuit de repository met het project geïnstalleerd op het Pythonpad:

```powershell
# Huidige trainer met gerepareerde lage-resolutieaugmentatie (R016):
python -m persoon1.role_training --output runs/eigen-R016 --fine-tune --encoder-checkpoint artifacts/appearance-v1/roles_teams.pt --manifest datasets/roles-teams-v3/manifest.json --fine-tune-blocks 0 --role-colour-scale 8

# Historische vergelijking met de toenmalige bron en dataset:
python -m scripts.replay_role_training --run R014 --output runs/eigen-historisch-R014
python -m scripts.replay_role_training --run R013 --output runs/eigen-historisch-R013

# De geleverde kopmenging R015 reproduceren:
python -m scripts.merge_role_heads --base artifacts/appearance-v1/roles_teams.pt --candidate artifacts/appearance-v3/roles_teams_r014.pt --manifest datasets/roles-teams-v3/manifest.json --output runs/eigen-R015

# Werkelijke runtime-classifier op exact dezelfde validatiecrops:
python -m scripts.evaluate_role_extension --manifest datasets/roles-teams-v3/manifest.json --candidate artifacts/appearance-v3/roles_teams_r015.pt --output runs/eigen-R015-evaluatie
```

Kies nieuwe uitvoermappen. Het script voor kopmenging weigert verschillende backbones, normalisatie, kleurschalen en uitvoerbetekenissen. Het bewaart de bestaande teamkop. De bronnen-/bouwscripts overschrijven geen bestaande datasetreview.

R016 controleert een echte preprocessingcorrectie: de lage-resolutie-fotovarianten werden eerder in de fine-tuningfase opnieuw door oorspronkelijke crops vervangen. Eén gedeelde transformatiefunctie past nu in beide fasen dezelfde spiegel-/resolutiebewerking toe. De torsokleurhistogrammen blijven bewust van het oorspronkelijke beeld afkomstig. De replay-helper bewaart de toenmalige bron en datasetversie voor historische resultaten.

De kernset van 48 balbeelden en de roluitbreiding zijn afzonderlijke taken/datasets. Historische versies worden niet bij elkaar opgeteld als onafhankelijke nieuwe data. [Alle echte resultaten en beperkingen](../../docs/Uitvoering_Persoon_1_Derde_Ronde.md) horen bij de keuze van een model.
