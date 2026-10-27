# Spelerherkenning en veldprojectie op de RTX 4050

**Latere roluitbreiding:** de metingen hieronder blijven de daadwerkelijke controles van de persoonsdetector en oorspronkelijke P004-detector. Het P004-profiel is nu apart bewaard als `configs/models-players-base.json`. `configs/models-players.json` bevat inmiddels [R007 met extra rollen en teams](Resultaten_Rollen_en_Teams.md), gestart met `-Recognition players`. Die uitbreiding is nog niet op de Broadcast-clip of de 4050 gemeten. De algemene persoonsroute blijft standaard; de historische metingen worden niet aan nieuwe gewichten toegeschreven.

Het standaardprofiel `configs/models.json` gebruikt algemene persoonsherkenning
op GPU, met invoerresolutie 1920. Het geleverde TeamTrack-model met `player` en
`referee` blijft apart beschikbaar via `configs/models-players.json`. Beide
worden op SHA-256 en echte klassenamen gecontroleerd. Geen van beide herkent
namen of teams.

De echte Broadcast-test liet zien dat het TeamTrack-model veel mensen mist en
soms kleine boxen op hoofden of voeten geeft. Zijn eerdere panorama-validatie
bewijst geen kwaliteit op deze andere camera. De algemene detector geeft op de
bekeken controlebeelden bruikbaardere lichaamsboxen. Daarom is algemene
persoonsherkenning de standaard geworden. Dit is een visuele AI-diagnose,
geen nieuwe mAP-meting of menselijke referentie.

De eerste lokale controle vond PyTorch met alleen CPU-ondersteuning, terwijl het
profiel GPU 0 vraagt. De app en CLI controleren dit nu vóór de veldanalyse.
Een onbruikbare GPU-configuratie geeft een herstelopdracht. De afzonderlijke
veldmodel- en trainingsomgevingen onder `.tools` blijven zelfstandig.

## Starten

Gebruik de eigen projectomgeving met Python 3.11 of 3.12:

```powershell
git pull --ff-only origin main
git lfs pull
.\scripts\Setup-Persoon1.ps1
.\scripts\Start-Spelermodel.ps1
```

Kies de video, de kalibratiemethode en het modelprofiel. Personenboxen worden
ook getoond wanneer de veldpositie onbekend is. Alleen personen met een bruikbare
veldprojectie tellen mee bij ‘Personen op veld’; hun rollen blijven onbekend.
Het aparte rolmodel gebruikt de bestaande spelertelling. Een onbekende veldpositie
levert een onbekende telling op.

Start het geleverde rolmodel expliciet met `Start-Spelermodel.ps1 -Recognition players`.

Een expliciete CPU-start kan met `Start-Spelermodel.ps1 -Device cpu`.
Installeer `requirements.lock` niet over de GPU-omgeving.

## De volledige integratie opnieuw controleren

Gebruik een bestaande automatische kalibratiebundel voor dezelfde video:

```powershell
.\.venv\Scripts\python.exe scripts\verify_player_pipeline.py C:\pad\clip.mp4 --automatic-calibration C:\pad\bundel\automatic_calibration.json --models configs\models.json --runs runs --report reports\player-pipeline-local.json
```

Dit voert echte modelinference uit op ieder frame, projecteert de detecties en
schrijft een H.264-video. De audit controleert framevolgorde, tijdstempels,
broncoördinaten, eindige scores, genormaliseerde veldposities, de rolfilter,
spelertelling, uitvoerafmetingen en bestandshashes. Bestaande gecontroleerde
uitvoer wordt hervatbaar hergebruikt.

De technische controle is geen nieuwe nauwkeurigheidsmeting. Het model is op
één panoramawedstrijd getraind; prestaties op een andere wedstrijd of een
uitzendcamera zijn daarmee niet bewezen. Scheidsrechters worden nog geregeld
gemist. Individuele ID's en trajecten bij een bewegende camera zijn nog niet
gevalideerd en blijven daar uitgeschakeld. Er is geen menselijke MVP-acceptatie
ingevuld.

Zie [de oorspronkelijke modelmetingen](Resultaten_Spelermodel.md) en
[de telregels](Spelertelling_en_Rollen.md).

## Werkelijk gecontroleerd op deze laptop

De Broadcast-clip van 49,56 seconden is met beide modellen volledig verwerkt:
1.239 bronframes op 25 fps, met gesynchroniseerde H.264-uitvoer van 1920 × 720.
De omgeving gebruikt PyTorch 2.6.0+cu124, torchvision 0.21.0+cu124 en Ultralytics
8.3.221 op de RTX 4050 Laptop GPU. De pakketcontrole slaagt.

- [Echte persoonsinference](../reports/person-inference-4050.json): 140,51 seconden
  voor detecties, geometrie en encoding. De eerder berekende veldwaarnemingen
  zijn hergebruikt. De veldtraining draaide tegelijk; dit is geen geïsoleerde
  snelheidsbenchmark of realtimeclaim.
- [Rolmodelcontrole](../reports/player-pipeline-4050.json): technisch voltooid,
  maar de bekeken frames 0 en 619 tonen veel gemiste lichamen en te kleine
  boxen. Er is geen onafhankelijke nauwkeurigheidsscore voor deze clip.
- [Definitieve personenvideo](../reports/person-pipeline-4050.json): de laatste
  legenda-aanpassing is opnieuw gerenderd met gecontroleerde echte detecties.
  Het rapport benoemt die replay en bewaart de oorspronkelijke inferentiemeting.
- Dezelfde veldinstellingen geven voor beide modellen 251 bruikbare frames
  (20,26%). De overige 988 frames krijgen een onbekende veldtelling. ‘Bruikbaar’
  betekent dat de geometrische filters slagen; het bewijst geen menselijke
  kalibratienauwkeurigheid. De aparte veldtraining is nog niet voltooid.
- De volledige suite slaagt met 190 tests en 4 subtests. Daarnaast is het
  opgeslagen echte resultaat in de Streamlit-testomgeving geopend en is naar
  frame 18 gesprongen, zonder applicatiefout of ingediende menselijke review.

De bronvideo, controlebeelden en vergelijkingsafbeelding blijven lokale
bestanden onder `runs/` en `artifacts/player-integration-4050/`. De rapporten
leggen hun uitvoerpaden en modelidentiteiten vast. Het eerdere rolrapport
verwijst naar het profiel dat tijdens die eerste proef nog de standaard was;
zijn volledige gewichtsidentiteit is in dat rapport bewaard.
