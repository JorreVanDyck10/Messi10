# Spelerdataset: TeamTrack v2.1

Dit pakket bevat 60 oorspronkelijke beelden van 6500 × 1000 pixels, gekoppelde YOLO-detectielabels, `data.yaml`, een manifest, bronannotaties, automatische voorstellen en visuele controlebladen. Het is een **voorlopige dataset met AI-review**. `human_review_completed` blijft `false`.

| ID | Naam | Betekenis en dekking |
| --- | --- | --- |
| 0 | player | De 22 spelers uit de openbare trackingannotaties, inclusief de rode en gele doelman; geen onderscheid tussen veldspeler en doelman nodig voor tracking. |
| 1 | referee | Centrale scheidsrechter en de duidelijk herkenbare assistent dichtbij de camera. Verre zijlijnrollen zijn onzeker en niet als scheidsrechter gegokt; de klassendekking is onvolledig. |

Er is geen baluitvoer uit dit model. Brontrack 22 is de bal en is uitgesloten. De oorspronkelijke MOT-klassekolom is -1: de rolbetekenis komt dus niet uit een bewezen bronklasse. De roltoewijzing van spelertracks 0–21 is visueel gecontroleerd, met brontracks 0 en 13 als doelmannen.

## Herkomst en aantallen

De drie bronclips staan onder `assets/videos/teamtrack/` in de repository. Dit zijn clips uit dezelfde wedstrijd `F_20200220_1`, uit de publieke **train**-partitie van [TeamTrack](https://github.com/AtomScott/TeamTrack), aangeboden via de [officiële Kaggle-dataset](https://www.kaggle.com/datasets/atomscott/teamtrack). Onze projectverdeling is geen officiële TeamTrack-benchmarkverdeling.

| Subset | Bronclip | Selectie, nulgebaseerde clipframes | Beelden | Spelerboxen | Bekende officialboxen |
| --- | --- | --- | ---: | ---: | ---: |
| train | 0540–0570 | 0, 20, …, 700 | 36 | 792 | 72 |
| val | 0660–0690 | 0, 60, …, 660 | 12 | 264 | 24 |
| test, gereserveerd | 0720–0750 | 0, 60, …, 660 | 12 | 264 | 24 |
| totaal | | | 60 | 1320 | 120 |

De beeldbestanden zijn JPEG quality 94 op bronresolutie. Er is geen uitsnede of verkleining van de geleverde beelden. Bron-MOT-frame 1 hoort bij clipframe 0. Het manifest bewaart clipindex, cliptijd, oorspronkelijke wedstrijdindex, oorspronkelijke wedstrijdtijd en SHA-256 van de video. Iedere clip duurt 30 seconden bij 25 fps. Het gewone YOLO-formaat is `klasse xc yc breedte hoogte`, genormaliseerd op 6500 × 1000.

De testgroep mag momenteel **geen onafhankelijke projecteindtest worden genoemd**: op `main` staan ook drie nabijgelegen ontwikkelannotaties van deze clip, op frames 225, 250 en 275. Er worden daarom geen formele testresultaten geclaimd. Verdeel die nabije beelden niet alsnog over training en test. Kies voor een onafhankelijke eindevaluatie een nieuwe, vooraf gereserveerde groep buiten alle ontwikkelbijdragen.

## Wat daadwerkelijk is gecontroleerd

- Alle 60 beelden zijn als volledig beeld en als uitsneden van de 22 spelerboxen bekeken; beide doelmannen blijven `player`.
- De centrale official en nabije assistent zijn afzonderlijk ingezoomd gecontroleerd. Een voorstel op een witte speler in validatieframe 420 is verworpen en naar de assistent met vlag verplaatst.
- De eerste labelversie miste de centrale official. Die is toegevoegd. Twee verkeerd geplaatste centrale-officialboxen in validatieframes 120 en 600 zijn tijdens de laatste controle gecorrigeerd.
- Verre rolvoorstellen bleken niet betrouwbaar genoeg. Ze staan als **afgewezen onderzoek** onder `reports/players-experiments/rejected-role-proposals/`; ze zijn geen trainingslabels.
- Alle beelden zijn leesbaar, alle labels bestaan, boxen liggen binnen het beeld en hebben positieve afmetingen. Exact gelijke gedecodeerde beelden zijn niet gevonden.
- De globale gelijkeniscontrole geeft waarschuwingen door het statische panorama. De gecontroleerde acties en bronmomenten verschillen; volledige tijdclips blijven als groep bij elkaar. Zie `validation.json` en het splitonderzoek in het experimentrapport.

De onvolledige verre officialdekking beperkt de referee-meting: echte verre officials kunnen als FP worden geteld of tijdens training onbedoeld achtergrond zijn. Dit is geen volledig gereviewde, algemene scheidsrechterdataset. Ook 60 beelden uit één wedstrijd bewijzen geen generalisatie naar andere stadions, kleding of camera's.

## Zelf openen en opnieuw controleren

Na `git lfs pull`, vanuit de projectmap:

```powershell
.\scripts\Start-Spelermodel.ps1 -Mode annotate
```

Open `http://127.0.0.1:8765`. De 60 beelden en bewaarde boxen staan in de keuzelijst. Groen zijn gewone boxen; de geselecteerde box wordt geel. Controleer bij inzoomen klasse, gemiste objecten, dubbele boxen, overlap en hoofd-tot-voetenbegrenzing. Voer alleen echte namen in bij werkelijk verrichte menselijke annotatie en review. Een wijziging maakt de oude review ongeldig.

Onder `review/all-boxes/` staan `frames-*` met hele beelden, `boxes-*` met alle speleruitsneden en `referees-*` met ingezoomde bekende officials. Die laatste bladen zijn in het manifest met checksum gekoppeld. Opnieuw genereren:

```powershell
.\.venv\Scripts\python.exe -m persoon1.teamtrack_dataset
.\scripts\Start-Spelermodel.ps1 -Mode validate
```

Dit bouwt labels uit de bewaarde brongeometrie en rolcorrecties, zonder nieuwe voorstellen of menselijke review te verzinnen. Na inhoudelijke labelwijzigingen: maak een nieuwe datasetversie, controleer opnieuw en meet de referentiemodellen opnieuw.

## Overdracht van geometrie

Detecties horen bij oorspronkelijke pixels, niet bij de verkleinde modelinvoer. Deze clips vereisen een eigen kalibratie. Het panorama heeft zichtbare kromming van veldlijnen; alleen vier punten kiezen bewijst daarom geen nauwkeurige homography. Persoon 2 moet de passende automatische kalibratie of vervormingscorrectie en projectiefouten voor deze bronnen beoordelen. Gebruik PANORIS-punten niet opnieuw op deze video's.
