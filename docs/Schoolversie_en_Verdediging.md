# Schoolversie: starten en zelf kunnen uitleggen

Voor de volledige code-uitleg, coördinaten, algoritmekeuzes en alternatieven:
[Code begrijpen en verdedigen](Code_en_Verdediging.md). De [codekaart](Codekaart.md)
verbindt ieder codebestand met zijn functies en plaats in het project.

De basis volgt de opdracht: een vaste camera, YOLO-detecties, handmatig
aangeduide veldpunten, een homography en een gesynchroniseerde minimap.
De schoolstart gebruikt dezelfde bestaande verwerking als de volledige app.
Tracking, automatische veldherkenning en teammodellen zijn uitbreidingen.

## Starten

Open PowerShell in de projectmap `Messi10`:

```powershell
.\scripts\Start-School.ps1
```

Open het lokale adres dat Streamlit toont. Kies een kort fragment met een
stilstaande camera. Kies daarna **Volledig veld** of een zichtbaar **strafschopgebied**.
Voor het strafschopgebied moeten de vier grote hoeken en twee kleine
doelgebiedhoeken zichtbaar zijn. Controleer daarbij de ingestelde veldafmetingen.
Voor CPU of alleen een
controle van de modelbestanden:

```powershell
.\scripts\Start-School.ps1 -Device cpu
.\scripts\Start-School.ps1 -CheckOnly
```

De basis gebruikt [models-school.json](../configs/models-school.json):
spelermodel P006 voor spelers en scheidsrechters, plus balmodel F005.
Beide verwerken volledige beelden op invoerformaat 1280 en confidence 0,25.
Er worden twee bestaande YOLO-modellen achter elkaar toegepast, omdat ze
voor verschillende klassen zijn getraind. Dit is geen nieuw gezamenlijk
getraind model. Doelmannen vallen onder speler; een algemene persoon wordt
niet automatisch als speler aangeduid.

De schoolmodus kiest handmatige kalibratie en verwerking zonder tracking
of teams. Resultaten worden bewaard onder `runs/school`. De opstart controleert
de modelbestanden, hun checksums en de gekozen CPU/GPU. De oorspronkelijke
profielen worden niet overschreven.

## Wat er met één frame gebeurt

1. OpenCV leest het videoframe.
2. YOLO voorspelt boxen, klassen en confidence. De confidencegrens filtert
   onzekere kandidaten; NMS vermindert overlappende dubbele boxen.
3. Voor een speler wordt het midden onderaan de box genomen als benadering
   van het contactpunt met de grond.
4. De homography zet dat beeldpunt om naar een positie op het vlakke veld.
5. De app tekent de detecties en de minimap op hetzelfde tijdstip.

Een punt buiten het gekalibreerde veld krijgt geen geldige veldpositie.
Een speler die aan de onderrand is afgesneden kan geen betrouwbaar voetpunt
hebben en wordt niet zomaar geprojecteerd. De minimap kan nooit nauwkeuriger
zijn dan de detectie en de kalibratie die ze gebruikt.

De kerncode staat in [detection.py](../src/football_pipeline/detection.py),
[geometry.py](../src/football_pipeline/geometry.py) en
[pipeline.py](../src/football_pipeline/pipeline.py).

## Waarom vier punten en twee controles?

De app koppelt vier zichtbare, bekende veldpunten aan het bovenaanzicht.
Dat kunnen alle veldhoeken zijn, of de hoeken van het gekozen strafschopgebied.
`cv2.findHomography` berekent hieruit de perspectieftransformatie. Je hoeft voor
de opdracht niet de volledige matrixafleiding van buiten te leren; je moet
wel kunnen uitleggen welke punten gekoppeld worden en waarom het veld vlak is.

Vier gebruikte punten kunnen netjes passen terwijl de kalibratie toch verkeerd
is. Daarom klik je ook minstens twee andere, bekende veldpunten aan als
controle. Die worden niet gebruikt om de matrix te berekenen. De app vergelijkt
hun voorspelde en aangeklikte beeldpositie. Ze aanvaardt een mediane fout van
maximaal 0,5% en een maximale fout van 1% van de beelddiagonaal. Dat zijn
projectkeuzes om slechte kalibraties te weigeren, geen nauwkeurigheidsgarantie.

Controleer de veldlijnen aan het begin, midden en einde van het fragment.
Een draaiende camera of camerawissel maakt één vaste matrix onbetrouwbaar.
Kies voor de basisdemonstratie een passend fragment. Voor een bal in de lucht
klopt de aanname van een grondpunt niet; de app berekent geen 3D-balpositie.

## Je eigen labelbijdrage: een overzichtelijke set van 80 beelden

De opdracht vraagt 40–80 uitdagende beelden. De grote broadcastverzameling
is aanvullend materiaal. Er is daarom een afzonderlijke, bewerkbare selectie:
`data/school-ball80-review-v1/manifest.json`. Ze bevat 48 trainingsbeelden en
32 validatiebeelden uit de eerder door AI geselecteerde balset. De wedstrijden
overlappen niet tussen training en validatie. De beelden zijn geen nieuwe data
en zijn al onderdeel van de ontwikkelgegevens; dit is geen onafhankelijke test.

De beelden en labels zijn echte kopieën. Aanpassen verandert de bevroren
trainingsdata en historische scores niet. De selectie is reproduceerbaar met
[prepare_school_review.py](../scripts/prepare_school_review.py); gebruik een
nieuwe uitvoermap als je dat script opnieuw uitvoert. Het overschrijft geen
bestaande review.

Open de bestaande lokale annotatie-editor:

```powershell
$env:PYTHONPATH = 'src;.'
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest data/school-ball80-review-v1/manifest.json --split all --port 8765
```

Controleer zelf de volledige beelden en zoom in voor de kleine bal. De huidige
boxen zijn voorstellen van providerlabels en AI-curatie. Menselijke review
is nog niet uitgevoerd. Gebruik als team dezelfde afspraken:

- Label de zichtbare bal met een zo strak mogelijke box. Controleer ook
  andere zichtbare ballen; de taak herkent ballen en bepaalt niet automatisch
  welke bal in het spel is.
- Noteer twijfel bij bewegingsonscherpte of gedeeltelijke bedekking. Verzin
  geen locatie voor een volledig onzichtbare bal. Houd onbeslisbare beelden
  buiten de volgende trainingsversie.
- Een leeg label betekent alleen een negatief voorbeeld als je het hele
  beeld hebt gecontroleerd en er werkelijk geen doelobject zichtbaar is.
  Deze selectie begint met 80 positieve voorbeelden.
- Bewaar eigen correcties onder je eigen naam. Laat een ander teamlid de
  opgeslagen labels beoordelen; vul geen review in die niet is uitgevoerd.

De bestaande validator heeft de 80 beelden, labels en splits gecontroleerd.
[Het rapport](../reports/school-review-validation.json) meldt twee open punten:
geen onafhankelijke testbeelden en dus geen ballabels in die testset. De
validator weigert daarom terecht deze ontwikkelset als volledige einddataset.
Menselijke review en een verse testset moeten nog worden toegevoegd in een
volgende datasetversie vóór een definitieve evaluatie. Houd bij de bestaande
40–80-framecontrole ruimte voor die testbeelden binnen die volgende selectie.
Je mag de huidige validatie niet achteraf tot een
onafhankelijke test omdopen. Na correcties volgt een nieuwe datasetversie en
een nieuwe meting; oude scores gelden niet automatisch voor gewijzigde labels.

## Training uitleggen met begrippen uit de les

| Begrip | Wat je in dit project moet kunnen uitleggen |
|---|---|
| Transfer learning | YOLO begint met eerder geleerde gewichten; fine-tuning past die aan voetbalbeelden aan. |
| Epoch | Eén volledige ronde door de trainingsset. |
| Batch | Een kleine groep beelden waarmee een gewichtsupdate wordt berekend. |
| Learning rate | Bepaalt hoe groot een optimalisatiestap is; te groot kan instabiel zijn, te klein leert langzaam. |
| Loss en optimizer | De loss meet trainingsfouten; backpropagation en de optimizer passen gewichten aan. |
| Validatie | Beelden die niet voor de gewichtsupdates gebruikt worden; hiermee vergelijk je ontwikkelkeuzes. |
| Overfitting | Goed op de trainingsbeelden, maar minder goed op andere situaties. Naburige videoframes over splits verdelen kan dit verbergen. |
| Augmentatie | Realistische variatie, zoals spiegelen of beperkte kleurverandering, zonder de labels verkeerd te maken. |
| Early stopping | Stoppen als de validatie niet meer verbetert; trainingsloss alleen is onvoldoende. |

P006 is de eerder getrainde spelerverbetering; de cursusvergelijking staat in
[Modelverbetering volgens de cursus](Modelverbetering_Volgens_Cursus.md).
De grote nieuwe spelerset is nog geen opnieuw getraind, beter spelermodel.

Broadcastbal v2 is wél getraind: 12 epochs, batch 4, learning rate 0,0001 en
de eerste tien lagen vast. Het gebruikt AdamW, een variant van Adam met
afzonderlijke weight decay. Adam komt in de les aan bod; de keuze voor AdamW
is een implementatiekeuze van dit experiment. Verander historische parameters
niet om ze achteraf met de les gelijk te laten lijken. De echte instellingen
en beperkingen staan in [Broadcast v2](Broadcast_V2_Training.md) en lokaal in
`artifacts/broadcast-ball-v2/fine-tune/args.yaml`.

## Metingen en fouten eerlijk uitleggen

Een true positive is een detectie die met de juiste klasse en voldoende
boxoverlap bij een label past. Een false negative is een gemist label. Een
ongekoppelde detectie kan een false positive zijn; bij onvolledige labels kan
het ook een werkelijk object zijn dat niet geannoteerd werd.

Precision is `TP / (TP + FP)`: hoeveel voorspellingen kloppen. Recall is
`TP / (TP + FN)`: hoeveel gelabelde objecten gevonden worden. Confidence is
de score van het model; IoU is de overlap van twee boxen. Dat zijn verschillende
begrippen. Matching-IoU van 0,5 bij evaluatie is ook iets anders dan de
NMS-IoU van 0,7 die dubbele voorspellingen helpt onderdrukken.

AP gebruikt de precision-recallcurve over confidencegrenzen. AP@50 gebruikt
matching-IoU 0,5; AP@50:95 middelt over meerdere, strengere overlapgrenzen.
mAP middelt ook over de geëvalueerde klassen. In een taak met alleen de klasse
bal is AP gelijk aan mAP voor die ene klasse. Een speler-AP is geen gezamenlijke
score voor spelers, scheidsrechters en bal.

Op 73 volledige ontwikkelbeelden, met dezelfde invoer 1280:

| Balmodel | AP@50 | AP@50:95 | Gevonden labels bij confidence 0,25 | Ongekoppelde detecties |
|---|---:|---:|---:|---:|
| F005, schoolbasis | 32,62% | 10,95% | 28 van 73 | 33 |
| Broadcastbal v2, zonder tegels | 41,64% | 18,01% | 22 van 73 | 10 |

De nieuwe training verbetert hier AP en vermindert ongekoppelde detecties,
maar vindt bij deze vaste confidence minder labels. Daarom vervangt de
schoolbasis F005 niet automatisch door v2 zonder tegels. De gezamenlijke
nauwkeurigheid van de schoolconfiguratie is nog niet als één systeem gemeten.
Een geslaagde softwaretest bewijst de herkenningsnauwkeurigheid niet.

## Optionele uitbreiding: kleine ballen met tegels

```powershell
.\scripts\Start-School.ps1 -BroadcastTiles
```

Dit behoudt de handmatige veldkalibratie en gebruikt het
combinatieprofiel met broadcastbal v3. Voor de bal worden overlappende stukken
van 640 × 640 pixels verwerkt. Zo blijft een kleine bal groter in de
modelinvoer. De boxen worden teruggezet naar het volledige beeld; dubbele
boxen worden samengevoegd. Het is dezelfde detector op meerdere uitsneden,
met extra rekentijd. De spelerinstellingen van dit experimentele profiel
blijven hun bestaande confidence 0,10 gebruiken; dat wijkt af van de basis.
De geselecteerde v2- en v3-gewichten worden via Git LFS gedeeld. Na een nieuwe
checkout is daarom ook `git lfs pull` nodig. De grote datasets en volledige
trainingsmappen blijven lokaal.

De eerdere v2-vergelijking met dezelfde tegels verhoogde bal-AP@50:95 van
10,19% naar 23,34%. De nieuwe v3-vergelijking verhoogt dit van 23,34% naar
25,74%, met 36 → 36 gevonden labels en 12 → 5 ongekoppelde detecties.
Zie [de nieuwe training en kalibratiecontrole](Verbeteringen_20261028.md).
Dit zijn andere inferentie-instellingen dan de volledige-beeldenrijen
hierboven. De labels zijn door AI nagekeken en de validatieset is klein en
eerder gebruikt bij ontwikkeling. Dit is geen bewijs voor alle wedstrijden.

## Voorbereiding op je mondelinge verdediging

Oefen zonder AI de volgende uitleg bij je eigen uitvoer:

1. Waarom koos je deze beelden en hoe voorkom je overlap tussen de splits?
2. Welke box heb je zelf gecorrigeerd, en welke labelafspraak verklaart die correctie?
3. Wat veranderde door fine-tuning en welke fout bleef bestaan?
4. Waarom neem je het voetpunt en wanneer faalt de aanname van een vlak veld?
5. Waarom gebruik je controlepunten die niet voor de matrix zijn gebruikt?
6. Welke getallen zijn ontwikkelscores, en wat moet je nog onafhankelijk testen?

Bewaar concrete voor/na-labels en voorbeelden van een gemiste bal,
een verkeerd geplaatste box en een onjuiste voorspelling. Leg vermoedelijke
oorzaken uit als hypotheses en controleer ze op het oorspronkelijke beeld.

Codex heeft de broncode aangepast, data geselecteerd, experimenten uitgevoerd
en deze uitleg geschreven. Publieke annotaties en AI-curatie zijn als zodanig
vermeld. Eigen menselijke labelbijdragen, teamreview en beheersing tijdens de
verdediging blijven werk dat de studenten werkelijk zelf moeten uitvoeren.

## Technische controle op 28 oktober 2026

De volledige softwaretestreeks slaagt: **404 tests en 4 subtests**. De nieuwe
schooltest doorloopt de verwerking en videoweergave met een expliciet synthetische
detector en controleert dat oude instellingen geen tracking, teams of automatische
veldherkenning inschakelen. De gewone app blijft eveneens getest.

Beide echte modelprofielen zijn daarnaast op de lokale GPU op één broadcastbeeld
uitgevoerd; zie [de runtimecontrole](../reports/school-runtime-smoke.json).
Dat controleert het laden en voorspellen, en meet geen herkenningsnauwkeurigheid.
De 80 werkkopieën zijn tegen de bronchecksums gecontroleerd. Een tweede poging
om dezelfde reviewmap te maken wordt geweigerd, zodat correcties bewaard blijven.

## Cursusbronnen

- [Computer Vision Challenge](../CV_Challenge_2026_2027.pdf), p. 1–4:
  vaste camera voor het MVP, 40–80 frames, fine-tuning, AP, homography,
  lokale interface, uitbreidingen en GenAI-transparantie.
- [Setting the Scene](../1_DL_Setting_the_Scene.pptx), slide 4: transfer learning.
- [Advanced Deep Learning](../2_DL_Adv_Deep_Learning.pptx), slides 28–31
  (trainen, batches, validatie, inference), 33–40 (preprocessing en leren),
  46–48 (leertempo en optimizer), 58–59 (regularisatie), 62–64 (augmentatie).
