# Uitvoeringsstatus persoon 1

**Datum:** 16 oktober 2026. **Doelhardware:** laptop met RTX 4050, volgens de gebruiker. **Werkelijk gebruikte ontwikkelhardware:** RTX 3050 Laptop GPU, 4 GB. De resultaten worden niet als 4050-metingen voorgesteld.

## Werkelijk uitgevoerd

- Repository en oorspronkelijke opdracht onderzocht; uitgebreid werkplan en invulsjablonen toegevoegd.
- Afzonderlijke Python 3.12-omgeving ingericht met vastgezette YOLO-, CUDA-, video- en beeldbibliotheken. De werkelijk geïnstalleerde versies staan in `requirements-lock.txt` en het omgevingsrapport.
- Openbare videobronnen vergeleken. Drie korte Alfheim-segmenten bekeken en afgewezen als directe MVP-bron wegens zichtbare lensvervorming.
- De door de gebruiker opgegeven PANORIS-video volledig gedownload: 3840 × 960 pixels, 25 fps, 3515 gedecodeerde videoframes en ongeveer 140,7 seconden containerduur. De video is zonder ruimtelijke verkleining naar MP4 gemuxt.
- De volledige MP4, bronvermelding en checksum klaargezet voor Git LFS in de bestaande repository.
- Vóór inference een selectie met tien tijdgroepen vastgelegd: 36 train-, 12 validatie- en 12 gereserveerde testframes. Alle zestig kandidaatframes zijn geëxtraheerd met oorspronkelijke frame-index en presentatietijd.
- Pretrained YOLO11n daadwerkelijk uitgevoerd op de 36 trainframes en 12 validatieframes op 640. Geen modelinference op de gereserveerde testframes uitgevoerd.
- Een aanvullende inferentieproef op dezelfde 36 trainframes uitgevoerd op 1920, met dezelfde pretrained gewichten. Dit is geen fine-tuningexperiment.
- Automatische labelvoorstellen, detectie-overdracht en overlays gemaakt. De lokale annotatietool is in de browser geopend en het laden van voorstellen is gecontroleerd. Er zijn geen verzonnen annotator- of reviewernamen opgeslagen.
- 32 automatische softwaretests geslaagd, waaronder expliciete AP-voorbeelden, labelkwaliteit, leakage, onafhankelijke review, VFR-tijdstempels en class mapping.
- Een echte technische GPU-trainingsproef van één epoch op 16 gegenereerde rechthoekbeelden uitgevoerd, met batch 4, resolutie 640, pretrained initialisatie, freeze 10 en AMP. De proef voltooide en schreef checkpoints. Dit is uitsluitend een softwarecontrole, geen voetbalmodel of bewijs van project-mAP.

## Wat de baseline daadwerkelijk laat zien

Op de 36 ontwikkelframes waren bij een confidencewerkpunt van 0,25 in totaal 29 persoonsvoorspellingen bij `imgsz=640` en 691 bij `imgsz=1920`. Het aantal balvoorspellingen op dat werkpunt was respectievelijk 0 en 1.

Dit zijn **aantallen voorspellingen over 36 frames**, geen aantallen unieke personen, true positives of gemiste ballen. De bekeken 1920-overlay bevat zichtbaar meer gelokaliseerde personen, maar een betrouwbare uitspraak over precision, recall en mAP vraagt volledige gecontroleerde labels. De bal blijft een relevante kandidaat voor de gerichte data gap; zijn labelbaarheid en de daadwerkelijke modelmissers moeten nog worden beoordeeld.

De globale beeldvergelijking waarschuwt voor sterke gelijkenis tussen subsets. Het vaste veld en de achtergrond veroorzaken veel overeenkomst. Tijdgroepen alleen bewijzen geen onafhankelijkheid; de actie-inhoud en groepsgrenzen moeten visueel worden gereviewd. Claims blijven beperkt tot nieuwe momenten uit dezelfde opname.

## Nog niet uitgevoerd of niet gezamenlijk goedgekeurd

| Fase | Wat nog werkelijk moet gebeuren | Waarom dit niet als afgerond geldt |
|---|---|---|
| 0–1 | Gezamenlijke scope- en geometriecontrole | De gebruiker koos de bron; persoon 2 heeft veldpunten en projectie nog niet bevestigd |
| 2 | Definitieve data gap vastleggen | Er zijn modelvoorspellingen, nog geen gecontroleerde referenties voor foutaantallen |
| 3 | Zes proefannotaties, labelregels, modelrollen en toolbesluit bespreken | Softwaretests vervangen de gezamenlijke inhoudelijke keuzes niet |
| 4 | Zestig kandidaten op moeilijkheid en labelbaarheid beoordelen, annoteren en onderling reviewen | Automatische voorstellen zijn geen goedgekeurde ground truth |
| 4 | Groepsgrenzen en visuele gelijkenis beoordelen; definitieve splits goedkeuren | De huidige indeling is een vooraf vastgelegde kandidaatselectie |
| 5 | Echte fine-tuning op de goedgekeurde voetbaldata uitvoeren | De synthetische technische proef telt daarvoor niet mee |
| 6 | Formele baseline en fine-tuning met beide mAP-varianten meten | Zonder gecontroleerde annotaties zijn zulke scores niet verantwoord |
| 7–8 | Getelde FP/FN, hypotheses en gerichte trainingsverbeteringen beoordelen | Voorspellingsaantallen zijn geen vastgestelde foutaantallen |
| 13 | Systeemfreeze, onafhankelijke eindtest en definitieve claims | Modelkeuze, echte training en integratie zijn nog niet afgerond |

De datasetcontrole is daadwerkelijk uitgevoerd en weigert de kandidaatdataset terecht wegens ontbrekende definitieve labels. Training wordt niet gestart door automatisch voorstellen tot menselijke labels te promoveren of goedkeuringen te verzinnen.

## Bewijsstukken in de repository

| Bestand | Betekenis |
|---|---|
| `assets/videos/HBTFZwMdcCw.mp4` | Volledige gekozen bronvideo, via Git LFS |
| `assets/videos/HBTFZwMdcCw.source.json` | Bron, formaat, bestandsgrootte en checksum |
| `reports/environment.json` | Werkelijk gebruikte omgeving en ontwikkel-GPU |
| `reports/youtube-video-inspection.json` | Werkelijke videoframes en tijdsintervallen |
| `reports/panoris-frame-selection.json` | Alle zestig bronmomenten en subsets |
| `reports/baseline-panoris-train-summary.json` | Feitelijke pretrained uitvoer op 640; project-mAP is leeg |
| `reports/baseline-panoris-train-detections.jsonl` | Echte overdrachtsgegevens voor 36 geselecteerde frames |
| `reports/inference-resolution-diagnostic.json` | Gelijke gewichten en frames op 640 en 1920 |
| `reports/baseline-panoris-1920-preview.jpg` | Werkelijk baselinevoorbeeld; geen menselijke ground truth |
| `reports/panoris-dataset-validation.json` | Open labelproblemen en waarschuwingen voor gelijkenis |
| `reports/training-software-check.json` | Duidelijk gemarkeerde synthetische softwareproef |

Grote gegenereerde werkbestanden blijven lokaal onder `data/`, `models/`, `runs/` en `output/`. Op de 4050-laptop zijn de kandidaatframes en voorstellen vanuit de bronvideo en scripts opnieuw te maken.

## Eerstvolgende concrete handeling op de 4050-laptop

Volg de startstappen in de README. Maak daarna de zes proefannotaties en bespreek klassen, boxregels en de modelrollen. Rond annotatie en onderlinge review af vóór de echte training. Leg pas na geldige controles de daadwerkelijke datasetgoedkeuring vast.
