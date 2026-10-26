# Persoon 1 uitgevoerd: data, detectie, rollen, training en evaluatie

**Datum:** 26 oktober 2026. Dit verslag bevat werkelijk uitgevoerde technische controles, vijf nieuwe roltrainingen, twee baltrainingen, een kopmengproef, een detectorablation en een volledige technische videorun. Menselijke review, inter-annotatorovereenstemming en een onafhankelijke eindtest blijven open. De wijzigingen betreffen werkpakket 1; veldherkenning, tracking en de gedeelde startworkflow zijn niet aangepast.

## 1. Uitvoering per werkpakket

| Werkpakket | Werkelijk uitgevoerd | Nog niet als voltooid te registreren |
|---|---|---|
| P1-01 data/review | Versie-inventaris, box-/hash-/klassecontrole, kopieerlekguard, review-CSV en contextbladen | Echte reviewers en zes onafhankelijke proefannotaties |
| P1-02 extra data | 93 aanvullende AI-gecontroleerde rolcrops, bronlicenties, gescheiden bron-/eventgroepen en versieerbare labelcorrectie | Volledige detectielabels van de nieuwe foto's en brede onafhankelijke wedstrijddekking |
| P1-03 modellen | R011–R014 en R016 werkelijk getraind, R015 compatibele kopmenging; crop-, detector- en gedeeltelijke externe vergelijking | Een universeel beter rolmodel of onafhankelijke eindprestatie |
| P1-04 bal | F003/F004 werkelijk getraind met intacte COCO-kop en persoon-/bal-supervisie; gelijke baselinevergelijking | Betrouwbare detectie op volledige onbewerkte panoramavideo's |
| P1-05 overdracht | Acht echte checkpoints, profielen, hashes, klassen, dependencies, echte JSONL-voorbeelden en technische integratiecontrole | Nieuwe 4050-benchmark of menselijke productacceptatie |

## 2. Data en kwaliteitscontrole

De huidige rolversie **V3.1** heeft 1.621 ongeaugmenteerde crops uit 105 gebruikte beeldbestanden: 1.153 train en 468 validatie. Datasetversies hergebruiken beelden en worden niet als onafhankelijke aantallen opgeteld. De afzonderlijke bal-kernset blijft 36 train/12 val, met 26/10 balobjecten. De historische 47-beeldenset en de 12 TeamTrack-testframes zijn alleen via metadata geïnventariseerd; hun testbeelden zijn niet geopend voor deze ronde.

| Nieuwe rolcrops | Train | Validatie |
|---|---:|---:|
| Steward | 4 | 6 |
| Supporter | 43 | 30 |
| Generieke persoon | 9 | 1 |
| Totaal | 56 | 37 |

De nieuwe gebruikte bronbeelden omvatten elf voetbalfoto's, één aanvullende niet-voetbal-eventstewardfoto en één frame uit de bestaande NZ–Canada-ontwikkelvideo. Een tweede eventfoto is als ongebruikte kandidaat bewaard. Alle bronnen hebben auteur-/licentie-/URL-/hashregistratie. De aangevraagde Commons-thumbbreedte was 1600, maar de daadwerkelijk geleverde afmetingen kunnen daarvan afwijken; die zijn expliciet geregistreerd. De bestaande trainings-/validatie-/testgroepen en oude beeldformaten zijn behouden.

De afbeeldingen leveren geselecteerde **rolcrops**, geen volledige YOLO-labels voor alle mensen in de foto's. Echte automatische persoonsvoorstellen staan naast de AI-correcties. Onder meer stoelvoorstellen, dubbelen en onduidelijke fragmenten zijn niet overgenomen. Bij de Zweedse foto is een box bijgesneden om de naaststaande persoon uit te sluiten.

V3.0 is bewaard als trainingsversie van R011/R012. Eén specifiek trainingslabel is daarna gecorrigeerd: de functie van een persoon met fluorescerend vest was niet voldoende vast te stellen, zodat V3.1 `person` gebruikt in plaats van `spectator`. R013/R014 gebruiken V3.1; de validatielabels veranderden niet. De correctiegeschiedenis blijft zichtbaar, inclusief de eerdere controlebladen. Een titel, shirtkleur of vest is geen zelfstandige rolwaarheid.

De audit controleert de drie rolversies, de 48 gebruikte TeamTrack-ontwikkelbeelden en de bestaande 48 bal-/persoonscrops. Er zijn geen ongeldige cropboxen, exact dubbele raw crops binnen een rolversie of exact gekopieerde ontwikkelbeelden over train/val gevonden. De loader weigert nu ook gelijke bytes met verschillende bestandsnamen in verschillende subsets; een regressietest toont dit aan. De aanvullende grove visuele hashcontrole op TeamTrack gaf geen kandidaten bij de vastgelegde afstand 8/256. De kleinste vastgelegde bron-tijdafstand tussen verschillende subsets is 33,6 seconden. Dit is geen bewijs van algemene wedstrijdoverdracht of van volledig onafhankelijke acties.

**Reviewmateriaal:** `reports/person1-round3/data-audit-final/human-review.csv` bevat alle 1.621 crops met lege reviewer en status `pending_human_review`. De 93 nieuwe crops hebben zeven controlebladen en dertien contextbeelden. Er is geen menselijke overeenstemmingsscore verzonnen. Zie [de concrete reviewinstructies](../datasets/roles-teams-v3/REVIEW.md).

## 3. Vijf echte roltrainingen en één kopmengproef

Alle roltrainingen starten vanaf R007, behouden dezelfde zes uitvoerklassen en gebruiken seed 42. Er zijn twintig fine-tune-epochs met tien gebalanceerde updates per epoch uitgevoerd; een update bemonstert twaalf crops per rol. De kop-learning-rate is 0,0005 en de eventuele backbone-learning-rate 0,00005. Daarna volgen maximaal 400 volledige kopupdates op de berekende features, met learning-rate 0,005. Checkpointkeuze gebruikt validatie-macro-F1 bij rolconfidence 0,65. Dit zijn geen 400 beeldbackbone-epochs. De labels zijn voorlopig AI-werk.

| Run | Trainingsdata | Aangepaste beeldblokken | Gewicht van kleurfeatures | Werkelijke uitkomst |
|---|---|---:|---:|---|
| R011 | V3.0 | Laatste 3 | 8 | Meer correcte supporters, maar vergeten stewards en regressies |
| R012 | V3.0 | 0 | 8 | Vaste backbone; sterke toegevoegde-spelerherkenning, slechte stewardretentie |
| R013 | V3.1 | 0 | 1 | Minder kleurgewicht lost het stewardprobleem niet op |
| R014 | V3.1 | 0 | 8 | Gelijke data als R013; gecontroleerde kleurgewichtvergelijking |
| R015 | R007 + 25% van de R014-rolkop | Backbone exact R007 | 8 | Gemeten behoud/verbetering als alternatief; geen nieuwe fine-tuningrun |
| R016 | V3.1 | 0 | 8 | Gecontroleerde herhaling met gerepareerde lage-resolutieaugmentatie |

R015 mengt alleen compatibele **lineaire rolkoppen**. Backbone, normalisatie, kleurschaal en klassen moeten exact overeenkomen; anders weigert het script. De bestaande R007-teamkop en bekende teambronidentiteiten blijven intact. De menggewichten 0/0,25/0,50/0,75/1 zijn vóór die mengproef vastgelegd en op dezelfde validatie vergeleken. Dit is ontwikkelmodelselectie, geen ongeziene test. Een herhaling gaf identieke voorspellingen, scores en checkpointbytes. De uiteindelijke uitvoering heeft één rolkop en vereist geen extra encoderpass.

Bij de laatste preprocessingcontrole is vastgesteld dat de lage-resolutie-fotovarianten in de eerdere fine-tuningfase opnieuw door oorspronkelijke crops werden vervangen. De huidige trainer gebruikt één transformatiefunctie in beide fasen; een checkerboard-regressietest verifieert dat detail werkelijk verdwijnt en de cropvorm behouden blijft. R016 herhaalt R014 met alleen deze bugfix: de gemeten macro-F1 stijgt van 0,7402 naar 0,7458, maar overschrijdt R015 niet. De oude broncode blijft bewaard; historische runs worden met de hash-gecontroleerde replay-helper herhaald, niet stilzwijgend met de nieuwe code.

De algemene vergelijkingsnotitie voor R011/R012 is na de start van R011 geschreven, vóór inspectie van zijn uitkomsten. Zij wordt daarom nadrukkelijk **geen preregistratie van de R011-training** genoemd. De latere R013/R014-/mengproeven hebben afzonderlijke vooraf opgeslagen hypothesen. Alle werkelijke curves, configuraties en bronversies zijn bewaard.

## 4. Rolmetingen: verbetering met concrete regressies

Onderstaande scores gebruiken de werkelijke runtime-classifier op **dezelfde 468 correcte persoonscrops** bij rolconfidence 0,65. Dit meet geen detectie-mAP.

| Model | Correcte rollen / 468 | Macro-F1, alle 6 rollen |
|---|---:|---:|
| R007, bestaande standaard | 396 | 0,7444 |
| R009, eerder alternatief | 430 | 0,7722 |
| R011 | 430 | 0,7544 |
| R012 | 440 | 0,7394 |
| R013 | 433 | 0,7252 |
| R014 | 430 | 0,7402 |
| R015 | 413 | 0,7648 |
| R016 | 431 | 0,7458 |

Een hogere totale accuracy kan samengaan met slechtere zeldzame rollen: de meeste referenties zijn spelers. Daarom zijn per-klasse-F1, de verwarringsmatrix en de aparte broncohorten nodig.

| Rol op dezelfde referenties | R007 correct | R015 correct |
|---|---:|---:|
| Speler | 335/369 | 349/369 |
| Centrale scheidsrechter | 12/19 | 11/19 |
| Lijnrechter | 14/15 | 14/15 |
| Steward | 9/14 | 8/14 |
| Supporter | 21/41 | 26/41 |
| Generieke persoon | 5/10 | 5/10 |

R015 verbetert de supporter-F1 van 0,6462 naar 0,7536. De steward-F1 stijgt ondanks één minder correcte steward van 0,5806 naar 0,6154, doordat er minder verkeerde stewardlabels worden uitgegeven. Dat is een afweging, geen verbetering van stewardrecall.

Op de 37 nieuwe zeldzame-rolcrops zijn R007, R009 en R015 respectievelijk **20, 18 en 24** keer correct. Op de 59 eerder toegevoegde wedstrijdcrops zijn dat **28, 58 en 40**. Op de 372 behouden crops heeft R015 macro-F1 0,7874 tegenover R007 0,7935 en R009 0,8151. R015 is dus niet het beste model voor iedere bron of iedere rol.

De opgeslagen cohort-macro-F1 blijft de zes uitvoerklassen middelen, ook als een cohort maar twee of drie rollen bevat. Vergelijk daarom alleen dezelfde cohorten en gebruik de bijbehorende aantallen/per-klasse-resultaten; rangschik verschillende populaties niet op die ruwe cohortmacro's.

## 5. Volledige detectie en de afgewezen personendetectorvariant

De twaalf oorspronkelijke TeamTrack-validatiebeelden met 264 spelerlabels en 24 bekende officiallabels zijn opnieuw volledig verwerkt. De verwerking en AP101-instellingen zijn gelijk aan de actuele R007-/R009-vergelijking na de eerdere boxsamenvoeging: imgsz 1920, proposal-floor 0,10, NMS-IoU 0,70. TP/FP/FN gebruiken confidence 0,25 en match-IoU 0,50. Verre officials zijn niet volledig gelabeld; de score betreft de beschikbare referentiedekking.

| Pipeline | mAP@50: player + official | mAP@50:95: dezelfde 2 klassen | Speler TP/FP/FN | Official TP/FP/FN |
|---|---:|---:|---|---|
| R007, actuele standaard | 70,08% | 31,87% | 197 / 48 / 67 | 12 / 3 / 12 |
| R009, eerder alternatief | 72,88% | 32,56% | 197 / 46 / 67 | 12 / 3 / 12 |
| R015 | 72,48% | 33,47% | 197 / 48 / 67 | 13 / 3 / 11 |
| D001: R015 + F003 als persoonsvoorstelmodel | 68,61% | 30,90% | 200 / 76 / 64 | 14 / 4 / 10 |

R015 houdt de spelersdetectie op deze set gelijk en vindt één extra official met betere gezamenlijke official-AP. Zijn speler-AP@50/@50:95 blijft 75,96%/26,26%; official-AP wordt 69,00%/40,68%. De bekende teamkoppelingen blijven 192 correct op 197 gematchte spelers.

De gedeeltelijke externe fotoproef blijft zwak en verslechtert bij R015: geselecteerde correct gevonden/geclassificeerde stewards gaan van **3/8 naar 2/8**, supporters van **4/11 naar 3/11**, vergeleken met de actuele R007-pipeline. Dit is voorstel-/rolcoverage op geselecteerde crops, geen volledige beeldrecall of mAP. Het verschil met de correcte-cropmeting toont waarom de gehele keten afzonderlijk nodig is.

F003 is ook gecontroleerd als vervanging van alleen de generieke persoonsvoorstellen: klasse 0 blijft daarbij `person`, niet `player`. Die D001-variant vindt meer spelerreferenties maar veroorzaakt veel extra speler-FP en verliest de vier eerder gevonden geselecteerde stewardvoorstellen. **Die vervanging wordt afgewezen.** De pretrained persoonsleverancier blijft behouden.

**Modelkeuze:** R007 blijft standaard. R009 blijft het bestaande alternatief voor spelers/officials; R015 is een nieuw controleerbaar alternatief met andere afwegingen. Er is geen universele promotie op basis van alleen een betere cropscore.

## 6. Bal: echte winst op native crops, nog geen bruikbare ruwe-video-overdracht

De eerdere éénklasse-runs wijzigden `nc=80` naar `nc=1` en laadden 448/499 pretrained onderdelen. F003/F004 behouden de 80-klassen-COCO-kop, met 499/499 geladen onderdelen. De bestaande persoonslabels worden daarbij ook gebruikt: `person` blijft werkelijke klasse **0** en `sports ball` klasse **32**. Dit is een gezamenlijke wijziging van kopbehoud en persoonssupervisie; het experiment is geen geïsoleerd causaal bewijs voor slechts één van die factoren.

Beide nieuwe runs starten vanaf dezelfde pretrained YOLO11n en gebruiken imgsz 1280, rect-batches 4, maximaal 100 epochs, patience 20, Adam, eerste tien modules vast, seed 42 en AMP. De beperkte augmentatie blijft gelijk aan de eerdere vastgelegde native-cropreferentie. F003 gebruikt learning-rate 0,001, F004 0,0001. Zij eindigen na 23 en 21 epochs, met beste checkpoint van epoch 3 en 1. Checkpointselectie gebruikt frameworkfitness over **persoon én bal**; de hieronder gerapporteerde projectscore evalueert uitsluitend de bal.

| Dezelfde 12 validatiecrops, 10 ballen | Bal AP@50 | Bal AP@50:95 | TP / FP / FN bij 0,25 |
|---|---:|---:|---|
| Pretrained baseline | 67,82% | 34,23% | 3 / 0 / 7 |
| F003: COCO-kop + persoon/bal | 66,70% | 37,16% | 4 / 0 / 6 |
| F004: gelijke route, lagere learning-rate | 67,82% | 33,56% | 2 / 0 / 8 |

De baseline en beide kandidaten zijn met dezelfde mapping, AP101-berekening, confidencevloer 0,001, IoU 0,70 en inputresolutie gemeten. F003 wint 2,92 procentpunt op de primaire AP@50:95 en vindt bij de werkgrens één extra bal; AP@50 daalt 1,13 procentpunt. F004 wordt afgewezen. De referentie is klein: tien ballen uit één opname en twee validatiegroepen, met AI-labels en gemaskeerde native crops.

De echte 30-frameproef op het volledige 4096×1080-panorama laat een concrete FP zien: een **wit ovaal veldlogo** wordt als bal voorspeld met confidence 0,282. De vergrote bronpatch staat in `reports/person1-round3/ball-raw-error-0.jpg`. De andere schaal en ontbrekende achtergrondvariatie zijn hypotheses. Op dat moment was er geen volledige raw-video-balreferentie; de later ontvangen volledige beeldlabels zijn afzonderlijk gemeten in paragraaf 9.

**Keuze:** F003 is de beste nieuwe kandidaat voor de gemeten native-croptaak. Hij wordt niet als betrouwbare full-frame-baldetector gepromoveerd. De overdracht onderscheidt de AP-confidencevloer 0,001 van de applicatiegrens 0,25. Een volgende ontwikkelronde moet gecontroleerde logo-/veldmarkeringsnegatieven en crop-versus-full-frameverwerking onderzoeken.

## 7. Overdracht, klassen en echte uitvoering

| Onderdeel | Werkelijke uitvoerbetekenis |
|---|---|
| P004 YOLO-basis, ongewijzigd | 0 `player`, 1 gecombineerde `referee` |
| Aanvullende rolclassifier | 0 speler, 1 scheidsrechter, 2 lijnrechter, 3 steward, 4 supporter, 5 generieke persoon |
| Teamkop | 0 Team A, 1 Team B; alleen de bestaande gecontroleerde wedstrijden |
| F003/F004 YOLO | Werkelijk 80 COCO-klassen; gebruikt 0 generieke persoon en 32 `sports ball` |

Bronklasse, semantische detectorrol en classifierklasse blijven verschillende velden in de export. Een klasse-ID wordt niet stilzwijgend tussen modellen hergebruikt. Doelmannen blijven spelers; specifieke rollen worden door de classifier voorspeld en zijn niet bewezen door hun naam alleen.

De profielen `configs/models-roles-r015.json` en `configs/models-ball-f003.json` verwijzen relatief naar de echte checkpoints en bevatten gewichtshashes, klassebetekenis en instellingen. De volledige overdracht en dependencies staan in `artifacts/appearance-v3/handoff.json` en `artifacts/football48-ball-v2/handoff.json`. Alle acht checkpoints, inclusief negatieve proeven, worden via Git LFS gedeeld.

`reports/person1-round3/handoff-examples-final` bevat twee echte detectiestromen op bronframes 0–29 van dezelfde ontwikkelclip, met videohash, originele 4096×1080-pixelboxen en tijdstempels. Bij de balgrens 0,25 zijn er **14 werkelijk lege ballendetectorrecords**. Dat betekent geen lege scène: de rollenstroom bevat wel mensen. Er zijn begin-/moeilijke controlebeelden en de bronklasse 32 blijft zichtbaar. Lege uitvoer is niet nagebootst door voorspellingen achteraf weg te laten.

Daarnaast is R015 op alle 120 frames van de bestaande Commons-clip door de complete pipeline uitgevoerd: detector, classifier, teams, huidige veldwaarnemingen, tellingbeleid, JSONL en H.264-uitvoer. De technische audit slaagt. De veldwaarnemingen worden voor exact dezelfde videohash hergebruikt; het veldmodel is niet opnieuw getraind. Het veld blijft op 0/120 frames bruikbaar en de veldtelling blijft terecht onbekend. Omdat één frame nu roltraining is, is deze hele sequentie uitsluitend een technische ontwikkelproef.

Werkelijke hardware: **RTX 3050 Laptop GPU, 4 GiB**. Doelhardware van de gebruiker: RTX 4050. Dit zijn geen nieuwe 4050-metingen. De gezamenlijke videorun overlapte met andere controles en geldt niet als vergelijkende snelheidsbenchmark.

## 8. Gebruiken, reproduceren en verdedigen

```powershell
git pull --ff-only origin main
git lfs pull
powershell -ExecutionPolicy Bypass -File scripts\Start-Wedstrijd.ps1
```

R007 blijft de standaard. Kies in de bestaande dropdown **Modelprofiel** het experimentele R015-profiel om dat alternatief te onderzoeken. Het balprofiel is een afzonderlijke onderzoeksroute, geen automatische vervanging van de gezamenlijke standaard.

Voor herhaling, na installatie volgens de README en met het project op het Pythonpad:

```powershell
python -m scripts.audit_person1_data --output runs/eigen-data-audit
python -m scripts.football48_ball_experiment --run runs/eigen-F003 --config configs/train-football48-ball-reference.json --provisional-ai-labels --preserve-coco-head
python -m persoon1.appearance_evaluation --models configs/models-roles-r015.json --output runs/eigen-R015-detectie
python -m scripts.export_person1_handoff --video assets/clips20/panorama128057-training48/128057_phase-0540_20s.mp4 --output runs/eigen-P1-overdracht
python -m pytest -q
```

Roltraining en kopmenging staan in [de dataset-README](../datasets/roles-teams-v3/README.md). Uitvoermappen worden niet overschreven. Behoud de gearchiveerde datasets voor historische modellen; pas geen oude rapporten aan om nieuwe scores gunstiger te laten lijken.

De softwarecontrole na samenvoeging slaagt met **225 tests en 4 subtests** (`software-tests-merged.xml`; de eerdere XML-bestanden bewaren 222 en 223 historische tests). Er zijn gerichte tests voor gekopieerde train/val-beelden, correcte COCO-klassemapping, blokkering van testbeelden, gescheiden evaluatiecohorten, compatibele kopmenging en de nieuwe full-framemetriek. De technische audit en voorbeeldexport zijn daarnaast echt uitgevoerd. Er is geen formele menselijke MVP-acceptatie geregistreerd.

Verdedigingsvoorbeelden zijn concreet beschikbaar: de gecorrigeerde persoonsbox bij de Zweedse foto, het ambigue vestlabel met versiegeschiedenis, het betere maar beperkte F003-balresultaat, het misleidende ovaal-logo-FP, de vergeten stewards, de afgewezen D001-vervanging en de gekozen R015-afweging. `error-register.json`, `model-selection.json` en `final-test-readiness.json` maken onderscheid tussen observatie, hypothese, keuze en nog open bewijs.

**Resterend:** echte menselijke review en proefannotaties, nieuwe gereserveerde eindtestgroepen, betere voetbalsteward-/supporter-proposaldekking, bruikbare raw-video-baldetectie en een werkelijke 4050-meting. De eindtest wordt pas na systeemfreeze uitgevoerd; hergebruikte ontwikkelvalidatie krijgt geen nieuwe naam als onaangeroerde test.

## 9. Later ontvangen volledige beelden: controle en aanvullende balmeting

Bij het synchroniseren kwamen GitHub-commits `903fb2b` en `d889a91` binnen met **40 volledige frames** (`football-fullframe40`) en **16 volledige frames** (`football-fullscene16`). Alle beelden zijn 4096×1080. Die levering zat niet in de hierboven beschreven trainingen; de vastgelegde trainingsdatasets, gewichten en eerdere scores blijven ongewijzigd. De 40-beeldenlevering bevat zestien opnieuw volledig gelabelde bronmomenten uit de eerdere cropset. Tel 40+16+48 daarom niet als 104 onafhankelijke momenten.

De technische validators en echte Ultralytics-dataloader zijn opnieuw uitgevoerd. Bestandschecksums, opgeslagen RGB-pixelchecksums, YOLO/COCO/bronboxen, klassennummers en tijdgroepen slagen. De sets hebben respectievelijk 30/10 en 12/4 train/val-beelden; de minimale tijdafstand over de splitgrens is respectievelijk 203,52 en 207 seconden. De 16 nieuwe bronindices komen niet voor in de andere twee sets. De oorspronkelijke 3,3-GB-video is bij deze aanvullende controle niet opnieuw gedecodeerd; dit is dus een controle tegen de geleverde pixelhashes. De bestaande upstream-broncontrole wordt daardoor niet overschreven. Bewijs: `incoming-fullframe40-verification.json` en `incoming-fullscene16-verification.json` in de rapportmap.

Beide leveringen gebruiken 0 `player`, 1 `ball`, 2 `referee`. De achtklassenset voegt `other_person`, `crowd`, `goal`, `corner_flag` en `stored_goals` toe. **Een groepsbox `crowd` is geen afzonderlijk gelabelde supporter en levert geen personenaantal.** `other_person` bewijst geen stewardrol. De extra klassen zijn niet door deze P1-ronde getraind. Meng de sets niet rechtstreeks voor achtklassentraining: de oudere beelden missen vijf van die klassen als supervisie. Menselijke review blijft voor beide leveringen open.

De nieuwe volledige validatiebeelden zijn wel gebruikt voor een vooraf vastgelegde **overdrachtsmeting van de drie al bevroren balgewichten**. Alle modellen krijgen het volledige panorama op imgsz 1280, zonder uitsneden of sliding windows, met confidencevloer 0,001, NMS-IoU 0,70, maxdet 300 en dezelfde AP101-implementatie. De modelklasse 32 `sports ball` wordt aan de datasetklasse 1 `ball` gekoppeld en voor de metriek naar klasse 0 vertaald. Trainingsbeelden worden niet voor deze scores gebruikt. Een nieuwe regressietest controleert de semantische mapping en oorspronkelijke pixelcoördinaten; een tweede blokkeert testbeelden vóór het openen van pixels.

| Model | 10 volledige validatieframes, 45 balreferenties: TP / FP / FN | 4 volledige validatieframes, 22 balreferenties: TP / FP / FN | AP@50 én AP@50:95, beide sets |
|---|---|---|---:|
| Pretrained | 0 / 3 / 45 | 0 / 1 / 22 | 0% |
| F003 | 0 / 10 / 45 | 0 / 6 / 22 | 0% |
| F004 | 0 / 0 / 45 | 0 / 0 / 22 | 0% |

TP/FP/FN gelden bij confidence 0,25 en IoU 0,50. Ook onder die confidencegrens levert geen model een correcte match voor de AP op deze beelden. F003 voorspelt onder meer de witte punt boven een letter in de geschilderde universiteitsnaam als bal, met confidence 0,453. De voorspellingen zijn teruggebracht naar het oorspronkelijke beeld; de opgeslagen voorbeeld-JPG toont groene referentieboxen en rode voorspellingen.

Dit is **voorlopige ontwikkel-AP tegen beschikbare AI-labels**, inclusief reserveballen. Kleine onbeslisbare randregio's zijn in de bronmetadata vermeld en krijgen geen verzonnen box of verborgen ignore-masker. De uitkomst bewijst geen afzonderlijke speelbalrecall, gegarandeerd complete annotatie of prestatie op andere wedstrijden. De twee subsets delen dezelfde opname en dezelfde validatie-tijdgroepen; tel ze niet als twee onafhankelijke wedstrijdtests.

De uitkomst versterkt de eerdere afwijzing voor de volledige video: meer vertrouwen of minder FP bij F004 betekent hier niet betere detectie; alle 67 referenties blijven gemist. F003 blijft uitsluitend kandidaat voor de gemeten native-croptaak. De passende volgende ontwikkelhypothese is bronresolutie behouden via gecontroleerde tiles/hogere resolutie en full-frameachtergronden, met dezelfde tijdsplits en menselijke labelreview. Er is na deze meting geen extra training of drempeltuning uitgevoerd.

Alle voorspellingen, labels, gewichtshashes, beeld-/labelhashes, instellingen, softwareversies en negatieve uitkomsten staan in `reports/person1-round3/fullframe-ball-development`. Herhalen naar een nieuwe map:

```powershell
python -m scripts.evaluate_fullframe_ball --output runs/eigen-fullframe-balmeting --imgsz 1280
```
