# Gezamenlijke training en toepassing — 27 oktober 2026

De bestaande lokale data is gecontroleerd en per taak samengebracht. Spelers, rollen, bal en veld hebben elk een echte nieuwe training gekregen. Een kandidaat wordt alleen gekozen als de vooraf vastgelegde vergelijking de verbetering ondersteunt.

## Data

| Taak | Training | Validatie |
|---|---:|---:|
| players | 231 | 83 |
| roles | 5789 | 2243 |
| ball_tiles | 616 | 276 |
| field | 8377 | 1669 |

De balrijen zijn overlappende tegels, de rolrijen persoonscrops. Dit zijn geen aantallen onafhankelijke wedstrijden. Veldtraining gebruikt de volledige beschikbare trainingsindex binnen het tijdsbudget. Heatmapvalidatie en de geometrische vergelijking gebruiken vooraf gekozen 64 beelden: alle 20 course-validatiebeelden en 44 verspreide corpusbeelden. De overige veldvalidatiebeelden zijn geïnventariseerd maar niet als gemeten voorgesteld.

Exacte kopieën en oudere cropannotaties worden ontdubbeld. Gereserveerde testbeelden worden niet geopend. Generieke personen worden geen spelers; alleen positieve balmomenten, ongelabelde voorstellen en incompatibele poseannotaties blijven buiten de bijbehorende training. Bron-, label- en videohashes staan in de inventaris en taakmanifesten.

| Uitsluitingsreden in gezamenlijke inventaris | Records |
|---|---:|
| reserved split; image and labels not opened | 12 |
| duplicate source frame | 16 |
| No complete explicit player/referee labels; person is not player | 41 |

De taakmanifesten bevatten daarnaast taakgebonden uitsluitingen, zoals onbruikbare baltegels en ongeldige veldannotaties; hun aantallen worden niet bij elkaar opgeteld als unieke beelden.

## Training en selectie

| Onderdeel | Nieuwe gewichten gekozen | Uitkomst | Gemeten duur (min) |
|---|---|---|---:|
| players | ja | complete; 60 geregistreerde epochs | 40.54 |
| roles | nee; huidige model behouden | complete; laatste kandidaat: backbone: 20 epochs, role: 400 epochs, team: 400 epochs | 2.77 |
| ball | ja | complete; 27 geregistreerde epochs | 28.87 |
| field | nee; huidige model behouden | keypoints: 0 volledige + 1 gedeeltelijke epochs, 5437 beeldpassages, time_limited; lines: 0 volledige + 1 gedeeltelijke epochs, 1900 beeldpassages, time_limited | 87.32 |

De baltraining is op verzoek gepauzeerd na epoch 15 en met dezelfde optimizer hervat. Het resterende budget was 36,58 minuten; de pauzetijd telt niet als training. Het oorspronkelijke hervatbare checkpoint en zijn SHA-256 zijn bewaard.


Het spelermodel gebruikt twee vastgelegde fasen: 53 epochs in de eerste samenvoeging en zeven aanvullende epochs vanuit het geselecteerde checkpoint op dataset v2. In v2 krijgen 16 volledige bronbeelden voorrang op hun oudere uitsneden. Alle spelerresultaten hieronder zijn opnieuw gemeten op dezelfde 83 v2-validatiebeelden; de eerdere 79-beeldenmeting wordt niet als v2-resultaat gebruikt.


### Spelers en officials

| Model | Speler AP50 | Speler AP50:95 | Speler recall | Official AP50:95 |
|---|---:|---:|---:|---:|
| baseline | 0.4855 | 0.2404 | 0.3967 | 0.0321 |
| candidate | 0.8858 | 0.4846 | 0.8407 | 0.5030 |

Deze AP betreft de detector vóór aanvullende rolclassificatie, teams, tracking en veldprojectie. Het is geen AP-score voor de volledige toepassing.


### Rollen

| Model | Macro-F1 bij 0,65 | Accuracy bij 0,65 |
|---|---:|---:|
| baseline | 0.2617 | 0.4793 |
| candidate | 0.7432 | 0.9340 |

Een aanvullende pixelcontrole verwijderde 16 exact gelijke persoonsuitsneden met verschillend afgeronde boxen: twee trainingscrops en veertien validatiecrops. Er waren geen identieke croppixels tussen training en validatie. De roltraining is vanuit R007 opnieuw uitgevoerd binnen het resterende rolbudget; bovenstaande scores gebruiken uitsluitend de opgeschoonde 2.243 validatiecrops. De eerste vergelijking en oorspronkelijke manifesten blijven bewaard.


| Rol | Baseline recall | Kandidaat recall | Baseline F1 | Kandidaat F1 |
|---|---:|---:|---:|---:|
| player | 0.5777 | 0.9535 | 0.6998 | 0.9702 |
| referee | 0.0959 | 0.8699 | 0.1582 | 0.7913 |
| assistant_referee | 0.9333 | 0.8667 | 0.2857 | 0.8387 |
| steward | 0.6429 | 0.0714 | 0.1475 | 0.1333 |
| spectator | 0.5122 | 0.7561 | 0.2121 | 0.7750 |
| person | 0.0352 | 0.9190 | 0.0669 | 0.9508 |

R007 blijft actief omdat de kandidaat recall verliest voor: assistant_referee, steward. De hogere totaalscore heft die vooraf vastgelegde behoudvoorwaarde niet op.


De rolmeting gebruikt correcte referentiecrops en is geen detectie-AP. Per rol, verwarringsmatrices en voorspellingen staan in het vergelijkingsbestand.

### Bal

| Model | AP50 | AP50:95 | Precision | Recall |
|---|---:|---:|---:|---:|
| baseline | 0.7250 | 0.3592 | 0.7951 | 0.7224 |
| candidate | 0.7980 | 0.4114 | 0.8261 | 0.7792 |

Balmetingen gebruiken dezelfde volledige validatiebeelden en multiscale-tegelverwerking. Labels omvatten reserveballen; dit meet geen automatische selectie van de speelbal.

### Veld

| Model | Intern geldig | Daarvan fout | Zonder lijnreferentie | Mediane lijnfout (px) |
|---|---:|---:|---:|---:|
| baseline | 42/64 | 15 | 0 | 1.515295402265059 |
| candidate | 0/64 | 0 | 0 | niet beschikbaar |

Veldcorpus en voortraining overlappen. Geometrische referenties zijn afzonderlijk van interne geldigheid beoordeeld; deze ontwikkelvergelijking is geen onafhankelijke eindtest.

## Werkende toepassing

Start met `scripts/Start-Gezamenlijk.ps1`. Het profiel `configs/models-integrated-20261027.json` koppelt de geselecteerde onderdelen aan teams, cameracompensatie, tracking en de minimap.

| Demonstratie | Frames | Frames met telling | Tijd (s) |
|---|---:|---:|---:|
| broadcast | 150 | 112 | 105.7 |
| panorama | 150 | 0 | 111.5 |
Video, JSONL en CSV zijn op gelijke frameaantallen en teamtotalen gecontroleerd. Elke bronclip krijgt eigen automatische veldherkenning; er wordt geen kalibratie van een andere opname geleend. ID's zijn tijdelijk en worden bij camerawissels vernieuwd.

## Bestanden en beperkingen

- Actuele inventaris: `C:\Messi10\data\joint-local-20261027-v2\inventory-final.json`; de oorspronkelijke inventaris blijft bewaard.
- Gewichten, configuraties, logs en vergelijkingen: `C:\Messi10\artifacts\joint-retrain-20261027-v2`.
- Samenvatting met checksums: `reports/joint-retrain-20261027/summary.json`.
- Versieerbare data-inventaris en herkomst: `reports/joint-retrain-20261027/data-inventory.json`, `source-provenance.json` en `audit-index.json`.
- Voorlopige AI-labels blijven voorlopig. Er is geen menselijke nauwkeurigheidsreview of acceptatie ingevuld.
- Teamfouten, gemiste rollen, reserveballen, onvolledige veldherkenning en gefragmenteerde track-ID's blijven mogelijk.


Softwarecontrole: 344 tests geregistreerd, 0 failures en 0 errors. De console-uitvoer en XML zijn bij de trainingsronde bewaard.

De dependencycontrole slaagt voor de app- en veldruntimeomgeving. De aparte veldtrainer gebruikt upstream PyTorch 2.3.1; `pip check` meldt daar ontbrekende algemene app-dependencies en afwijkende app-versie-eisen. Die app draait daar niet. De vereiste veldimports, bron-/gewichtencontrole en CUDA-preflight zijn wel uitgevoerd; echte training en resultaten staan hierboven. De volledige uitvoer is bewaard in `environment-checks.json`.

## Visuele controle en concrete beperkingen

Codex (AI) heeft voor beide video's frames 0, 75 en 149 bekeken. Dit is geen menselijke acceptatie of onafhankelijke nauwkeurigheidsmeting.

- Broadcast: veldprojectie is beschikbaar op 112/150 frames; op de overige 38 frames blijven veldpositie en telling onbekend.
- Broadcast: meerdere zichtbare spelers krijgen het label lijnrechter of person. De actieve R007-classifier blijft een belangrijke foutbron; de getoonde spelertelling is geen betrouwbare volledige bezetting.
- Broadcast: automatische teamgroepering is onvoldoende; alle 1.833 spelerwaarnemingen blijven qua team onbekend.
- Panorama: 0/150 frames met bruikbare veldkalibratie. Er worden geen veldpunten of teamtotalen verzonnen; beeldlabels en tijdelijke IDs blijven zichtbaar.
- Panorama: Team A/B-kleurgroepen worden getoond, maar kleine spelers en overlappende labels maken visuele inspectie lastig.
- Tracking: 170 verschillende tijdelijke IDs op broadcast en 56 op panorama in zes seconden; zichtbare fragmentatie, geen gemeten identiteitnauwkeurigheid.
- Beide clips bevatten geen gedetecteerde cameracuts. Camerawisselgedrag wordt door de regressietests gedekt; deze clips leveren daarvoor geen zelfstandige nauwkeurigheidsmeting.
- De eerste als broadcast benoemde bron bleek bij visuele controle een drone-opname. Die proef is apart bewaard; de definitieve broadcast gebruikt de gecontroleerde zijlijnbron 6cdaf4089cb5.

De volledige suite: 340 tests en 4 subtests geslaagd (de XML registreert samen 344 gevallen).

- [broadcast: openen in de app](http://127.0.0.1:8501/?run=63d6a606d9cda9ade4c1719aecc03e50f573ec97469e7d5b3904a0d1f72425cb).
- [panorama: openen in de app](http://127.0.0.1:8501/?run=4434349444f416df7ddf05c6fcba10ece8b5533b9b03fd01cb62d4f99a91c82f).
