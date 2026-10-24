# Extra rolgegevens en echte training — versie 2

Deze versie bewaart de 1.417 oorspronkelijke rolcrops en voegt **111 visueel door AI gecontroleerde crops** toe: 52 train en 59 validatie. De oorspronkelijke versie en haar labels zijn niet overschreven. Menselijke review blijft open.

| Extra labels | Train | Validatie |
|---|---:|---:|
| Speler, inclusief duidelijke doelmannen | 35 | 55 |
| Scheidsrechter | 9 | 4 |
| Lijnrechter | 8 | 0 |
| Overige rollen | 0 | 0 |

De trainingscrops komen uit de twaalf eerder verzamelde volledige ontwikkelbeelden. De validatiecrops komen uit twaalf al geleverde `football48`-beelden in de twee bestaande validatietijdgroepen. Alleen duidelijk interpreteerbare rollen zijn toegevoegd. Twintig validatiecrops met voetenfragmenten, gemaskeerde personen of onvoldoende context zijn expliciet uitgesloten in `ai-label-decisions.json`. De beslissingen en contactbladen zijn bewaard onder `reports/football48-ball-experiments/role-review`.

Dit is **gedeeltelijke cropclassificatie**, geen volledige detectieannotatie van de twaalf beelden. Bestaande YOLO-voorstellen zijn gecontroleerd; hun rol is niet blind overgenomen. Er zijn geen nieuwe steward- of supporterlabels verzonnen. Teams in de toegevoegde opname zijn niet gecontroleerd gelabeld: `team` blijft `null`, en die opname wordt niet toegevoegd aan de bekende wedstrijden van de getrainde teamkop. Runtime gebruikt daar de bestaande neutrale A/B-kleurclustering.

In totaal bevat deze ontwikkelversie **1.528 ongeaugmenteerde crops uit 92 gebruikte beeldbestanden**: 1.097 train en 431 validatie. Train-/validatiegroepen, beeldhashes, cropgrenzen en de uitgesloten nieuwe teamidentiteit zijn gecontroleerd in `validation.json`. Gereserveerde testbeelden zijn niet geopend. Deze roluitbreiding staat afzonderlijk van de 48 beelden van de verplichte bal-data-gap; het hele historische project bevat meer dan 40–80 beelden.

De scores ondersteunen ontwikkelvergelijkingen op deze bronopnamen. Ze bewijzen geen betrouwbare toepassing op alle wedstrijden. De toegevoegde panorama-opname heeft sterke vervorming, en de validatie bevat gecontroleerde gemaskeerde crops. Vooral teamkleurclustering, kleine centrale officials, stewards en supporters blijven beperkt.

## Reproduceren

Na projectinstallatie en `git lfs pull`, vanuit de projectmap:

```powershell
.\.venv\Scripts\python.exe -m persoon1.role_training --output runs\eigen-R009 --fine-tune --encoder-checkpoint artifacts\appearance-v1\roles_teams.pt --manifest datasets\roles-teams-v2\manifest.json
.\.venv\Scripts\python.exe -m persoon1.role_training --output runs\eigen-R010 --fine-tune --fine-tune-blocks 0 --encoder-checkpoint artifacts\appearance-v1\roles_teams.pt --manifest datasets\roles-teams-v2\manifest.json
```

Kies nieuwe uitvoermappen. R009 past drie featureblokken aan; R010 houdt de beeldbackbone aantoonbaar exact gelijk aan R007 en traint de rolkop verder. Beide behouden de warm-startnormalisatie en vergelijken dezelfde validatiecrops. De trainer weigert testsubsets, gemengde groepen, veranderde beelden en ongeldige cropboxen.

De nieuwe gewichten staan via Git LFS onder `artifacts/appearance-v2/`. Gebruik `configs/models-roles-r009.json` of `configs/models-roles-r010.json`. [Resultaten en afwegingen](../../docs/Resultaten_Extra_Dataronde.md) leggen uit waarom het bestaande standaardprofiel behouden blijft.
