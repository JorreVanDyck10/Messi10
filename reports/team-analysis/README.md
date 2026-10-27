# Teams, tracking en telling — technische controle op 26 oktober 2026

Onderdeel 3 is geïntegreerd in de automatische en handmatige toepassing.
Gebruiksinstructies, telregels, interfaces en beperkingen staan in
[Teams, tracking en telling](../../docs/Teams_Tracking_en_Telling.md).

## Softwarecontrole

- Voor de wijziging: **244 tests en 4 subtests geslaagd**.
- Na de wijziging: **269 tests en 4 subtests geslaagd**, in 100,71 seconden.
- Volledige Ruff-lintcontrole en `pip check`: geslaagd.
- Formattercontrole: 84 bestanden in orde met de reeds bestaande afwijking in
  `tests/test_teamtrack_dataset.py` uitgesloten. De volledige formattercontrole
  signaleert alleen die ongewijzigde opmaakafwijking; het bestand behoort tot
  onderdeel 1 en is hiervoor niet aangepast.
- `git diff --check`: geslaagd.

Bewijs: [JUnit-uitvoer](software-tests.xml) en
[softwarevalidatie met bronidentiteit](software-validation.json).

De 25 toegevoegde tests behandelen kleurindeling, groene/witte/zwarte shirts,
achtergrond en kleine of gemengde uitsneden, ontoereikende waarnemingen,
soortgelijke kleuren, een afwijkende doelmankleur, trackbevestiging,
labelwissels, nieuwe ID’s, onbekende tellingen, lage confidence, oude records,
begrensde steekproeven, correcte overlaykleuren, exports, cachegedrag,
herleidbare correcties, foutgedrag en Streamlit-interacties. Een aanvullende
bestaande apptest is aangepast aan de nieuwe correctievelden na verwerking.

De volledige synthetische proef gebruikt echte ByteTrack-matching en echte
H.264-encoding. Handmatige teamcorrecties veranderen daarin geen bronbox,
modelrol, score, veldpositie, projectiestatus of track-ID. De oorspronkelijke
uitvoer behoudt haar hash. Een tweede correctie blijft aan dezelfde
oorspronkelijke analyse gekoppeld. Deze tests zijn softwarebewijs met
synthetische detectoruitvoer; de acceptatiegrens is uitsluitend voor die
test expliciet gestubd.

## Echte ontwikkelclip

[Het integratierapport](integration-check.json) bevat de volledige bronidentiteit,
runmap, metingen en beperkingen. Er is een bestaande ontwikkelclip van **40
frames, 1,6 seconde, 25 fps, 1920 × 1080** gebruikt met het echte spelersmodel
v3 en bestaande automatische veldwaarnemingen. Detectie, projectie en
cameragecompenseerde tracking zijn opnieuw uitgevoerd. De veldinstellingen
van die opgeslagen analyse zijn behouden; er is geen experimenteel profiel
geactiveerd.

| Meting | Resultaat |
|---|---:|
| Uitvoervideo | 40 frames, 25 fps, H.264, 1920 × 720 |
| Totale verwerking inclusief modellen, tracking, teams en encoding | 7,67 s |
| Teamfit en tweede weergavefase | 2,17 s |
| Verwerkingssnelheid voor de volledige verwerking | 5,22 fps |
| Frames met een intern bruikbare veldprojectie en telling | 6 / 40 |
| Spelerwaarnemingen met team A / B / onbekend, over alle frames | 262 / 96 / 413 |
| Verschillende tijdelijke track-ID’s | 142 |

De aantallen spelerwaarnemingen zijn geen unieke spelers of aantallen binnen
het veld. Het script controleert per frame dat Team A + Team B + onbekend
gelijk is aan de bestaande veldtelling. Bij de 34 frames zonder geldige
veldkalibratie zijn alle veldtellingen onbekend en de CSV-cellen leeg. CSV en
JSONL stemmen overeen; andere rollen krijgen geen spelerteam.

De controlebeelden en het eerste bruikbare frame zijn visueel bekeken. In
frame 18 toont de uitvoer **16 waargenomen spelers: A 8, B 3, onbekend 5**.
Dat is een controle op onderlinge consistentie en geen menselijke bevestiging
van de werkelijkheid. Automatische prototypes in deze clip zijn donker en
door schaduw beïnvloed; de overlay gebruikt daarom afzonderlijke, goed
leesbare rode en blauwe kleuren.

De korte clip heeft duidelijke ID-fragmentatie: 142 tijdelijke ID’s in 40
frames. Een deel van de spelers blijft daardoor onbekend terwijl een nieuwe
track nog kleurwaarnemingen verzamelt. Dit onderdeel behoudt de bestaande
ByteTrack-matching en cameracompensatie; het bewijst geen verbetering van
persoonlijke identiteit. De onvolledige velddekking blijft eveneens een
beperking van de bestaande veldherkenning.

## Reproduceren

De benodigde lokale video, modelgewichten en automatische veldbundel moeten
aanwezig zijn:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=reports/team-analysis/software-tests.xml
.\.venv\Scripts\ruff.exe check src streamlit_app.py scripts tests
.\.venv\Scripts\python.exe scripts/check_team_integration.py .cache/automatic-upload-real-smoke.mp4 .cache/course-v3-integration/73be183cc00e2b3eabf5a17ebd3c463c09230364c3e2283a4bb10d8d438f10cf/calibration.json
```

De nieuwe echte run staat onder `runs/` en kan via **Een opgeslagen teamanalyse
openen** worden bekeken. Grote bron- en uitvoervideo’s blijven in de bestaande
genegeerde lokale mappen.

Menselijke teamlabels en trackingreferenties ontbreken. Er wordt geen
teamaccuracy, telaccuracy, IDF1, MOTA of onafhankelijke testprestatie geclaimd.
Het profiel is een technische eerste versie met correctiemogelijkheden.
