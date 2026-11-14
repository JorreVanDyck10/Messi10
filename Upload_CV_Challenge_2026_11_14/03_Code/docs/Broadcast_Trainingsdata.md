# Broadcastdata met gepubliceerde labels

De volgende ronde heeft native balcrops met gecontroleerde negatieve voorbeelden,
een minder redundante spelerselectie en een werkelijk getraind optioneel balmodel
opgeleverd. Zie [Broadcast v2: data, metingen en gebruik](Broadcast_V2_Training.md).

Deze uitbreiding verzamelt 8.000 echte broadcastbeelden op oorspronkelijke
1920 × 1080-resolutie uit [SoccerNet SN-GSR-2024](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024).
De bronrevisie is `3cc710eb6d53a23350a3d2863311c1c0a2e645d7`, annotatieversie
1.3. Het corpus staat lokaal in `data/broadcast-sngsr-v1/`; beelden, labels en
reviewbestanden blijven buiten Git. Het compacte resultaat staat in
`reports/broadcast-data/summary.json`.

## Aanvullende selectie en gecorrigeerde labels

Er staan nu 9.450 unieke bronbeelden lokaal: de 8.000 SoccerNet-beelden en
1.450 aanvullende officialbeelden. Na de visuele uitsluitingen bevatten de
aanbevolen taken samen 9.380 unieke beelden. De 132 geselecteerde balbeelden
zijn een subset van de oorspronkelijke 8.000 en worden niet dubbel geteld.

| Taak | Train | Validatie | Trainingsbestand |
|---|---:|---:|---|
| Speler/official | 6.000 | 2.000 | `data/broadcast-sngsr-v1/data-players.yaml` |
| Bal, AI geselecteerd | 59 | 73 | `data/broadcast-ball-review-v1/curated/data.yaml` |
| Official, aanvullende bron | 1.115 | 265 | `data/referee-broadcast-v1/curated/data.yaml` |

De balronde controleert 232 oorspronkelijke uitsneden uit alle 115 clips:
130 bronboxen worden behouden, twee worden verplaatst en opnieuw begrensd,
en 100 twijfelgevallen worden uitgesloten. De oorspronkelijke beelden en
labels blijven ongewijzigd. De twee correcties staan ook in de bewerkbare
reviewkopie, met annotator `Codex (AI)`, open reviewstatus en wijzigingshistorie.
`reports/broadcast-data/ball-review-decisions.json` bewaart elke beslissing;
`ball-corrections.json` bevat de oude en nieuwe pixelboxen.

Dit zijn AI-controles, geen menselijke goedkeuringen. De balset bevat alleen
positieve voorbeelden en is klein; hij is bedoeld voor ontwikkeling en
aanvullende training, niet als volledige balbenchmark. Training en validatie
behouden de bestaande gescheiden SoccerNet-wedstrijden. Menselijke review,
negatieve voorbeelden en een onafhankelijke eindtest blijven nodig.

De aanvullende bron is [Infactory Referee Tracking](https://huggingface.co/datasets/infactory-ai/referee-tracking),
revisie `094370666a599016e2e0646525b148046a023498`. Credit: Valentino
Constantinou, Mehdi Iranmanesh en John Kanalakis, Infactory. De bron vermeldt
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) en menselijke
verificatie van zijn voorstellen; onze controle bestaat uit een technische
audit van alle bestanden en een visuele AI-steekproef van 30 beelden.

Twee volledige clips, samen 70 beelden, zijn afgezonderd wegens een box op
een supporter/vlag en twijfelachtige boxen bij sterk overlappende personen.
De aanbevolen officialset bevat 761 positieve beelden met 915 boxen en 619
door de bron expliciet als negatief gemarkeerde beelden. De bron is volledig
bewaard; alleen de nieuwe selectie laat deze twee clips weg.

De officialset scheidt zes bronclips voor training van twee bronclips voor
validatie. De UUID's verbergen de wedstrijdidentiteit: onafhankelijke
wedstrijdscheiding is daarvoor niet bewezen. Deze set wordt daarom als
afzonderlijke aanvullende taak aangeboden. De SoccerNet-release van 2025
bevat dezelfde train-/validatiearchieven als 2024 en is niet opnieuw als extra
data geteld.

Gebruik de taken afzonderlijk: klasse 0 betekent `ball` in de balset,
`referee` in de aanvullende officialset en `player` in de spelersset.
De aanvullende officialbeelden hebben geen spelerlabels en kunnen dus niet
zonder nieuwe volledige annotatie in de speler-/officialdetector worden gemengd.

De controles en nieuwe datasetidentiteiten staan in
`reports/broadcast-data/follow-up-summary.json`. De oorspronkelijke dataronde
trainde geen model. De volgende v2-ronde voegt een apart balexperiment toe;
inmiddels slagen 48 gerichte softwaretests. De actieve standaard blijft behouden.

De aanvullende bestanden opnieuw opbouwen vanuit de projectmap:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
.\.venv\Scripts\python.exe -m scripts.curate_broadcast_balls --decisions reports/broadcast-data/ball-review-decisions.json
.\.venv\Scripts\python.exe -m football_pipeline.referee_dataset
.\.venv\Scripts\python.exe -m scripts.curate_referee_data --decisions reports/broadcast-data/referee-review-decisions.json
.\.venv\Scripts\python.exe -m scripts.audit_broadcast_extensions
```

De contactbladen en baluitvergrotingen staan in
`data/broadcast-ball-review-v1/` en `data/referee-broadcast-v1/visual-review/`.
`data/broadcast-ball-review-v1/corrected-examples.png` toont de twee
balcorrecties: rood is de bronbox, groen de gecorrigeerde box.

## Verdeling en inhoud

Er zijn 6.000 trainingsbeelden uit wedstrijden 4, 6 en 9 en 2.000
validatiebeelden uit wedstrijden 2, 3 en 5. Geen wedstrijd komt in beide splits.
De selectie wisselt clips af en neemt gelijkmatig verdeelde, volledig
geannoteerde frames, met minstens vijf bronframes afstand (0,2 seconde).
Beelden uit één clip blijven sterk gecorreleerd: dit zijn zes wedstrijden,
geen 8.000 onafhankelijke situaties. Het corpus bevat meer temporele dekking
dan de eerdere selectie van 80 beelden, met dezelfde zes wedstrijdidentiteiten.

Alleen de officiële train- en validatiearchieven worden aangesproken. Test en
challenge blijven ongeopend. Deze validatiewedstrijden zijn al bij eerdere
modelontwikkeling gebruikt en gelden niet als onaangeroerde eindtest.

| Klasse | Bestaande detector, `data.yaml` | Rollenmodel, `data-roles.yaml` |
|---|---:|---:|
| Speler | 0 | 0 |
| Doelman | 0, samengevoegd met speler | 1 |
| Official | 1 | 2 |
| Bal | 2 | 3 |
| Overige persoon | 3 | 4 |

Beide bronformaten bevatten YOLO-boxlabels. De aanbevolen trainingsingang is
`data-players.yaml` met uitsluitend `player` en `referee`, passend bij het
bestaande spelersmodel. `data-participants.yaml` houdt doelmannen apart:
`player`, `goalkeeper`, `referee`. Deze twee expliciete deelnemertaken bevatten
geen bal als te leren klasse.

De visuele steekproef toont namelijk enkele verschoven balboxen in de
gepubliceerde bron, bijvoorbeeld `SNGS-071_000371` en `SNGS-097_000376`.
Gebruik de oorspronkelijke vier-/vijfklassensets pas voor baltraining nadat
de balannotaties zijn gecontroleerd en gecorrigeerd. De ruwe bron blijft
bewaard zodat fouten en verbeteringen traceerbaar zijn. Voor de hierboven
geselecteerde 132 balvoorbeelden bestaat inmiddels een afzonderlijke export.

`attributes/` bewaart per beeld de
oorspronkelijke objecten met rollen, teamzijde, rugnummer, track-ID en
veldposities, voor zover de bron die heeft ingevuld. Teamzijde is de
oorspronkelijke links/rechts-aanduiding binnen de clip; ze is geen vaste
clubidentiteit over verschillende wedstrijden.

`field/train` en `field/valid` bevatten dezelfde beelden via hardlinks,
oorspronkelijke veldpolylijnen en `match_info.json`, voor de bestaande
veldtrainer. De bronlijnen blijven ongewijzigd; de bestaande veldpreprocessing
behandelt eventuele lijnoverschrijdingen aan de beeldrand. De veldcontrole
accepteert 7.958 labels (5.977 train, 1.981 validatie) en sluit 42 labels uit
waarvan lijnen te ver buiten de beeldrand liggen. Die uitsluitingen staan
in `field-quality-report.json`; de bestaande veldtrainer sluit ze eveneens
expliciet uit. De boxlabels van deze beelden blijven bruikbaar. Er zijn geen
veldpunten of menselijke kalibratiereferenties verzonnen.

## Labelcontrole

De labels zijn gepubliceerde datasetannotaties. Modelvoorspellingen worden niet
als waarheid toegevoegd. De import controleert bronversie en categorienamen,
HTTP-ranges, ZIP-CRC en bestandsgroottes, beeldafmetingen en eindige positieve
boxen. Boxen worden geometrisch tot het zichtbare beeld begrensd; volledig
buitenliggende boxen worden uitgesloten en apart geteld. Gemarkeerde
negeergebieden worden uitgesloten uit de selectie.

De audit controleert alle checksums, decodeert alle beelden, leest alle
YOLO-labels onafhankelijk opnieuw in, vergelijkt ze met de pixelboxen en
controleert op exacte beeldduplicaten en wedstrijdoverlap. Het volledige
rapport staat in `quality-report.json`. `manifest.json` bevat de hashes en
herkomst per frame; `selection.json` bevriest de selectie vóór modelgebruik.

`visual-review/` bevat contactbladen van vier clips per wedstrijd en afzonderlijke
baluitvergrotingen. Dit is een visuele steekproef, geen volledige menselijke
labelreview. `project_human_review_completed` blijft daarom onwaar.

Voor echte correcties is er `review-workspace/`: beelden zijn via hardlinks
gedeeld en labels zijn afzonderlijke, bewerkbare kopieën. Het opnieuw draaien
van de verzamelaar overschrijft die correcties niet. Voer geen beeldbewerkingen
uit op hardlinks: maak daarvoor een nieuwe fysieke kopie.

## Gebruiken

Verzamelen, hervatten en controleren vanuit de projectmap:

```powershell
.\scripts\Collect-BroadcastData.ps1
```

Alleen de volledige audit en reviewvoorbeelden opnieuw maken:

```powershell
.\scripts\Collect-BroadcastData.ps1 -AuditOnly
```

Een andere hoeveelheid vraagt een nieuwe datasetmap:

```powershell
.\scripts\Collect-BroadcastData.ps1 -Dataset data/broadcast-sngsr-next -TrainCount 7000 -ValidCount 3000
```

De verzamelaar gebruikt acht downloadthreads, hervat gecontroleerde downloads
en weigert gelijktijdige schrijvers. Na een geforceerde procesbeëindiging kan
`.writer.lock` achterblijven; verwijder die alleen nadat de betreffende
verzamelaar werkelijk gestopt is. Instellingen en selectie mogen niet stil
wijzigen binnen dezelfde datasetversie.

De boxeditor openen:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest data/broadcast-sngsr-v1/review-workspace/manifest.json --split all --port 8765
```

Spelertraining kan rechtstreeks met `data/broadcast-sngsr-v1/data-players.yaml`;
voor afzonderlijke doelmannen gebruik je `data-participants.yaml`. Bijvoorbeeld in een bestaande
Ultralytics-omgeving met CUDA:

```powershell
.\.venv\Scripts\yolo.exe detect train model=yolo11n.pt data=data/broadcast-sngsr-v1/data-players.yaml imgsz=1280 batch=2 epochs=60 patience=12 workers=0 device=0 project=runs/broadcast name=baseline
```

Deze dataverzameling start zelf geen training en vervangt geen actief model.
Een rollenmodel heeft een andere klassenmapping; gebruik de bijbehorende echte
klassennamen bij de modeloverdracht. Meet kleine ballen ook op volledige
bronresolutie of met de bestaande tegelroute: meer beelden alleen bewijzen
geen betere baldetectie.

De bronrepository vermeldt GPL-3.0. Dat is vastgelegde bronmetadata; afzonderlijke
rechten op publicatie van de oorspronkelijke uitzendingen worden niet geclaimd.
De [officiële taakbeschrijving](https://www.soccer-net.org/tasks/game-state-reconstruction)
beschrijft de broadcastclips en rol-/teamannotaties.
