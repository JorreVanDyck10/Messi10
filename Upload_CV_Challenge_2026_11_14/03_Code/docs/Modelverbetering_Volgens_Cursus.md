# Modelverbetering volgens de cursus

Deze ontwikkelronde van 19 oktober 2026 onderzoekt herkenning op andere wedstrijden en camera's. De resultaten staan in `artifacts/course-improvement-20261019/`. Het geselecteerde spelermodel EXP-P006 is na de vergelijking als standaard ingesteld. Softwaretests en trainingsverlies zijn geen vervanging voor herkenningsmetingen.

## Data en vergelijking

De bevroren selectie bevat 80 beelden uit [SoccerNet Game State Reconstruction](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024), revisie `3cc710eb6d53a23350a3d2863311c1c0a2e645d7`, annotatieversie 1.3. Er zijn 60 trainingsbeelden uit wedstrijden 4, 6 en 9 en 20 validatiebeelden uit wedstrijden 2, 3 en 5. De test- en challengearchieven zijn niet geopend. De selectie ligt vast voordat modelvoorspellingen worden bekeken.

De beelden bevatten 1.152 spelers- en doelmanboxen, 116 officialboxen en 78 balboxen. Gepubliceerde rolannotaties bepalen de klassen; een algemene `person`-detectie wordt niet omgedoopt tot speler. Doelmannen behoren wel tot de gezamenlijke spelerklasse. Een klasse zonder positieve trainingsvoorbeelden wordt niet als geleverde herkenningsfunctie aangeboden.

De oorspronkelijke boxen en veldlijnen blijven met checksums bewaard. Kleine overschrijdingen van de beeldrand in de gepubliceerde veldpolylijnen worden geometrisch afgeknipt. Hierbij verschuift het snijpunt langs de lijn; eenvoudigweg een buitenliggend eindpunt recht naar de rand trekken zou de lijnrichting veranderen. De controle accepteert maximaal 0,5% grensoverschrijding en bewaart de bronannotaties. Dezelfde zichtbare lijngeometrie wordt voor training en evaluatie gebruikt.

Deze kleine ontwikkelset is geen garantie voor elke wedstrijd. Voor het veldmodel is overlap met zijn oorspronkelijke voortraining bovendien niet uitgesloten. De menselijke teamreview en de onafhankelijke eindtest blijven open.

## Experimenten en cursusbegrippen

| Onderdeel | Uitvoering | Cursusbron |
|---|---|---|
| Transfer learning | Spelersmodellen starten opnieuw van YOLO11n; veldnetwerken van vastgelegde PnLCalib-gewichten | Opdracht, p. 2 |
| Gescheiden validatie | Wedstrijden overlappen niet tussen training en validatie | Advanced Deep Learning, slide 30 |
| Preprocessing | Originele boxcoördinaten, reproduceerbare resizing, gecontroleerde randafhandeling | Slides 33–35 |
| Learning rate en optimizer | Adam; spelers starten op 0,0003 met cosine-afbouw; veld op 0,00003 met validatiegestuurde verlaging | Slides 40, 46–48 |
| Regularisatie | Weight decay, early stopping en een afzonderlijke augmentatieproef | Slides 58–59, 62 |
| Fine-tuning en foutanalyse | Beide box-AP-varianten, FP/FN-bestanden, trainingscurves en vergelijking met de oude detector | Opdracht, p. 2 en 4 |
| Homography | Alleen grondpunten en veldlijnen; projectiefouten meten tegen bronannotaties | Opdracht, p. 2 |

EXP-P005 gebruikt de nieuwe wedstrijdselectie zonder augmentatie. EXP-P006 verandert uitsluitend de vooraf beschreven bundel van kleur- en geometrische augmentaties. Beide hebben maximaal 60 epochs en early stopping na 12 epochs zonder verbetering. De oorspronkelijke trainingsinstellingen, de gekozen checkpoints en alle uitgevoerde batches blijven bewaard.

De detectievergelijking gebruikt dezelfde 20 validatiebeelden, dezelfde box-AP-implementatie en confidence 0,001 voor AP. De praktische precision/recall gebruikt confidence 0,25 en IoU 0,5. De oude detector wordt zowel op 1280 als op zijn bestaande productie-instelling 1920 gemeten. Nieuwe resultaten op deze wedstrijden mogen niet rechtstreeks met de eerdere panoramascore worden vergeleken.

De veldtraining bewaart ook de ongewijzigde baseline als mogelijk beste checkpoint. Een lagere trainingsloss bewijst geen betere homography. Daarom volgt een aparte vergelijking van zichtbare veldlijnen: per beeld mediaan maximaal 0,5% en maximum maximaal 1% van de beelddiagonaal. Niet-geprojecteerde beelden en intern geldige maar foutieve projecties blijven afzonderlijk geteld. Confidencebeleid wordt op trainingswedstrijden onderzocht; validatie blijft modelselectie, geen eindtest.

## Gemeten spelerresultaten

| Model | Spelers AP@50 | Spelers AP@50:95 | Spelers recall bij 0,25 | Officials AP@50 |
|---|---:|---:|---:|---:|
| Bestaand TeamTrack-model, 1280 | 1,61% | 0,22% | 1,71% | 0,03% |
| EXP-P005, zonder augmentatie | 89,07% | 55,26% | 86,30% | 29,29% |
| EXP-P006, met augmentatie | 93,17% | 58,98% | 91,78% | 31,93% |

EXP-P006 levert bij confidence 0,25 en IoU 0,5 268 TP, 65 FP en 24 FN voor spelers: precision 80,48%. Voor officials zijn dit 10 TP, 16 FP en 16 FN. Deze AP-percentages gelden voor afzonderlijke klassen; alle drie positief geannoteerde klassen samen leveren mAP@50 41,70% en mAP@50:95 25,14%. Bal-AP is nul. Het nieuwe applicatieprofiel gebruikt uitsluitend de getrainde speler- en officialklassen, op invoerformaat 1280 met NMS-IoU 0,70. De detector geeft kandidaten vanaf 0,10 door omdat ByteTrack die voor zijn tweede associatiestap nodig heeft; nieuwe tracks starten vanaf 0,25. De precision/recall bij 0,25 mag niet als score voor alle getoonde boxen vanaf 0,10 worden gelezen.

De geometrische foutanalyse in `reports/course-improvement/error-audit.json` onderscheidt overlap met een andere rol, lokalisatiefouten, concurrerende boxen en ontbrekende matches. Dit zijn automatisch berekende foutcategorieën, geen door mensen bewezen oorzaken. Op één bestaand ontwikkelbeeld is bovendien de oude en nieuwe detector met dezelfde instellingen getekend; die illustratie is geen aanvullende benchmark.

## Veldexperimenten en correcte geometrische meting

De bestaande veldgewichten produceren op de twintig validatiebeelden veertien intern geldige kalibraties. Daarvan voldoen twaalf aan de externe lijnreferenties; twee zijn fout en zes beelden blijven zonder projectie. Intern geldig is dus geen nauwkeurigheidsscore. De evaluatie gebruikt nu homogene lijncoëfficiënten: zichtbare referenties blijven meetellen wanneer hun denkbeeldige volledige veldeindpunten de projectiehorizon kruisen. De oude rapporten `field-comparison` en `field-policy*` vóór deze reparatie zijn historische tussenresultaten en overschatten de correcte projecties. Gebruik de rapporten `corrected-*` en de uiteindelijke samenvatting.

Er zijn drie trainingsopzetten uitgevoerd: volledige fine-tuning met learning rate 0,00003; uitsluitend de uitvoerconvolutie met 0,0001; en een voorzichtige uitvoerlaagproef met 0,00001 zonder extra L2. Bij de uitvoerlaagproeven blijven de pretrained beeldkenmerken en BatchNorm-statistieken vast. De fine-tuning gebruikt exact dezelfde bevroren wedstrijdverdeling. Het ongewijzigde model, het beste checkpoint volgens heatmapverlies en de werkelijk getrainde laatste epoch worden onderscheiden. Ook combinaties van oorspronkelijke en getrainde punten-/lijnnetwerken worden vergeleken.

Een afzonderlijke geometrische proef past een duale homography uitsluitend aan semantische lijnen aan en houdt de voorspelde veldpunten apart als controles. Deze proef blijft experimenteel: hij gaf geen hogere validatiedekking zonder extra fouten. De controlepunten zijn modelvoorspellingen en worden niet als onafhankelijke menselijke referenties voorgesteld.

Na de oorspronkelijke eis van meer correcte projecties is aanvullend onderzocht of evenveel correcte projecties met minder fouten mogelijk zijn. Deze secundaire ontwikkelanalyse wordt expliciet vastgelegd met `--allow-error-reduction`; het is geen vooraf blind bevestigde eindtest. De laatste epoch van de uitvoerlaagproef haalt twaalf correcte, één foutieve en zeven ontbrekende projecties. De echte integratieclip geeft hiermee echter nul van veertig intern bruikbare frames, tegenover zes van veertig bij de bestaande gewichten. Daarom is deze kandidaat **niet geactiveerd**. De voorzichtige derde training geeft evenmin een geaccepteerde verbetering. De actieve veldruntime en zijn gewichten blijven de bestaande release; de nieuwe spelersdetector is wel geactiveerd.

Deze ronde heeft dus een duidelijke spelerverbetering opgeleverd, maar heeft de zwakke veldherkenning nog niet opgelost. Een geslaagde softwaretest, minder validatiefouten op één kleine selectie of een dalende heatmaploss mag die beperking niet verbergen. De mislukte kandidaat, metingen en trainingsrapporten blijven bewaard voor analyse.

De menselijke veldreview en een onafhankelijke eindtest blijven nodig. Uit een kleine ontwikkelvalidatie mag geen algemene belofte voor alle camera's of wedstrijden volgen.

## Gebruik van generatieve AI

Codex heeft in deze ronde de cursusbestanden gelezen, de gegevensselectie en trainingscode opgesteld, experimenten uitgevoerd, foutanalyses gemaakt en de applicatie gekoppeld aan het geselecteerde model. De opdracht van de gebruiker was veld- en spelerherkenning verbeteren volgens de cursus; de aanvullende instructie was testen op andere wedstrijden en camera's. De code, experimentconfiguraties, bronchecksums, logs en meetresultaten zijn lokaal bewaard. Deze vermelding vervangt geen eigen toelichting tijdens de verdediging. Er is geen menselijke annotatie, teamreview, goedkeuring of onafhankelijke eindtest door AI ingevuld.

## Reproduceren en zelf reviewen

Start de volledige experimentreeks vanuit de projectmap met `scripts/Run-CourseImprovement.ps1 -Output artifacts/course-improvement-next -FieldBaseline .tools/field-runtime-baseline-before-course.json`. Dit voert spelertraining, drie veldopzetten en projectievergelijkingen na elkaar uit. Nieuwe configuraties krijgen een nieuwe uitvoermap. De runtime wordt vooraf in die map vastgelegd en modellen worden niet automatisch vervangen door dit experimentscript. `src/football_pipeline/course_dataset.py` haalt alleen geselecteerde ZIP-onderdelen op; volledige datasetarchieven zijn niet nodig.

Voeg `-AllowFieldErrorReduction` toe om de beschreven secundaire selectie te herhalen. Ook zo'n selectie moet de eigen ontwikkelvideo doorstaan voordat een model kan worden geactiveerd. Het bewaarde kandidaatprofiel is experimenteel en wordt niet door de app gekozen.

De oorspronkelijke ronde is stapsgewijs uitgebreid. De volledige fine-tuning gebruikte de oudere bronversie uit `source-snapshots`; de latere proeven voegen deterministische targetgeneratie en een exacte float32-cache toe. Gewichten en rapporten bewaren de daadwerkelijke trainerhash en configuratie. De huidige wrapper reproduceert de beschreven methode met de huidige broncode; hij claimt geen bitidentieke herhaling van de historische tussenstappen.

Er staat een aparte, bewerkbare kopie in `data/course-multimatch-v1/review-workspace/`. Open de bestaande annotatie-editor met:

```powershell
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest data/course-multimatch-v1/review-workspace/manifest.json --split all --port 8765
```

Een echte annotator moet beelden controleren/corrigeren en onder de eigen naam opslaan; een ander teamlid reviewt die labels. Er zijn geen namen, goedkeuringen of menselijke controles ingevuld. Correcties veranderen de bevroren experimentresultaten niet: maak daarvoor een volgende datasetversie en meet opnieuw.

De opdracht vraagt ook een eigen assisted-labelingbijdrage en individueel begrip tijdens de verdediging. Publieke annotaties en door AI geschreven code vervangen die bijdrage niet. Leg concrete correcties vast en licht zelf toe waarom gegevensverdeling, augmentaties, learning rate en fouten de resultaten beïnvloeden. Het statische MVP en de uitbreiding voor bewegende camera's blijven afzonderlijke claims.

Bronnen: [Computer Vision Challenge](../CV_Challenge_2026_2027.pdf), [Setting the Scene](../1_DL_Setting_the_Scene.pptx), [Advanced Deep Learning](../2_DL_Adv_Deep_Learning.pptx).
