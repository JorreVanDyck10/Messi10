# Werkpakket persoon 1: data, model en evaluatie

**Status:** uitgewerkt werkplan met bijbehorende software; zie [de actuele uitvoering](Status_Persoon_1.md) voor wat werkelijk is uitgevoerd.

**Team:** twee personen. Persoon 1 coördineert data, modellen en detectie-evaluatie; persoon 2 reviewt en verzorgt geometrie, toepassing en tracking.

**Nieuwe samenwerkingsverdeling, 26 oktober 2026:** gebruik voor de gevraagde uitbreiding naar drie personen [Werkverdeling voor drie personen](Werkverdeling_3_Personen.md). De bovenstaande twee-persoonsindeling is de historische context van dit document.

**Documentversie:** 1.0, 16 oktober 2026.

**Scope:** concrete uitvoering, beslisprocedures, bewijsstukken en acceptatiecriteria. Geen kalenderplanning.

**Invullen tijdens de uitvoering:** [registers en sjablonen](Invulsjablonen_Persoon_1.md).

**Opdrachtbron:** [Computer Vision Challenge 2026–2027](../CV_Challenge_2026_2027.pdf).

## Leeswijzer

Dit document vertelt per fase wat je doet, waarom je het doet, wat je bewaart en wanneer je verder kunt. De fase-ID's 0 tot en met 8 en 13 sluiten aan op de taakverdeling van het oorspronkelijke plan. Fasen 9 tot en met 12 behoren hoofdzakelijk bij persoon 2; jouw overdracht daarvoor staat in hoofdstuk 4.

De termen **voorbeeld**, **voorstel** en **nog te meten** zijn bewust gebruikt. Een voorbeeld is geen waarneming, een voorgestelde instelling is geen uitgevoerde training en een ingevuld sjabloon is pas bewijs wanneer het naar echte bestanden of controles verwijst.

Alle paden in dit document zijn relatief aan deze repository of dit document. Grote video's, modelgewichten, omgevingen en tijdelijke trainingsuitvoer krijgen een afgesproken externe of lokale opslagplaats met identiteit en toegangsinstructies.

## 1. Doel, opdracht en verantwoordelijkheid

### 1.1 Eindproduct en jouw bijdrage

We bouwen een lokale toepassing die een voetbalvideo in `.mp4` verwerkt en de detectievideo naast een gesynchroniseerde tactical map toont. Het MVP ondersteunt één statisch camerastandpunt zonder snelle cuts of extreem pannen. Zoom of kleine camerabewegingen worden ook onderzocht: ze kunnen een vaste homography ongeldig maken.

Jij moet aantonen:

1. Waarom de gekozen beelden en data gap bij de opdracht passen.
2. Hoe automatische labelvoorstellen door mensen zijn gecontroleerd.
3. Waarom de dataset en splits geschikt zijn voor de gemaakte claims.
4. Wat fine-tuning tegenover de pretrained baseline verandert.
5. Welke fouten blijven bestaan en welk onderzoek daaruit volgt.
6. Hoe persoon 2 jouw echte detectoruitvoer reproduceerbaar kan gebruiken.

Een werkend dashboard vervangt geen kwantitatieve evaluatie. Een hoge score vervangt geen controle van de volledige datastroom.

### 1.2 Verplichte resultaten en bewijs

| ID | Vereiste | Concreet bewijs | Eigenaar / reviewer |
|---|---|---|---|
| REQ-01 | Pretrained detector als vertrekpunt | Modelidentiteit, versies, baselineconfiguratie en voorbeeldvoorspellingen | Persoon 1 / persoon 2 |
| REQ-02 | Relevante data gap | Baselinefouten, vergelijking van kandidaten en gemotiveerd besluit | Samen |
| REQ-03 | 40–80 uitdagende frames | Frameoverzicht, selectieredenen en gecontroleerde annotaties | Persoon 1 coördineert / beiden annoteren |
| REQ-04 | Assisted labeling | Voorbeelden van automatische voorstellen en menselijke correcties | Beiden / onderlinge review |
| REQ-05 | Consistente labels en occlusions | Annotatiehandleiding, zes proefbeelden en reviewlog | Samen |
| REQ-06 | Verantwoorde train/val-strategie | Splitmanifest, groepsindeling, aantallen en overlapcontrole | Persoon 1 / persoon 2 |
| REQ-07 | Werkelijke YOLO-fine-tuning | Volledige configuratie, logs, curves en gewichten | Persoon 1 / persoon 2 |
| REQ-08 | mAP@50 en mAP@50:95 | Meetresultaten met klassen, subsets en evaluatie-instellingen | Persoon 1 / persoon 2 |
| REQ-09 | Failure en error analysis | FP/FN-voorbeelden, hypotheses, experimenten en conclusies | Persoon 1 / persoon 2 |
| REQ-10 | Homography met minstens vier veldpunten | Correspondenties en visuele projectiecontrole | Persoon 2 / persoon 1 |
| REQ-11 | Lokale toepassing en synchronisatie | Volledig verwerkte clip en controle van bronmomenten | Persoon 2 / samen |
| REQ-12 | Proces en GenAI-eigenaarschap | Feedback, echte AI-prompts, controles en individuele uitleg | Samen |
| EXT-01 | ByteTrack en spelertrajecten | Referentie-ID's, ID-fouten en voorbeelden van meerwaarde | Persoon 2 / persoon 1 |

De eerste twaalf regels dekken het MVP en het proces. EXT-01 is de gekozen Extra Mile en begint pas na MVP-acceptatie. Volgens de opdracht kan een degelijk MVP tot 85% behalen; een succesvol uitgevoerde en verdedigde uitbreiding is nodig voor hogere beoordelingen.

| Rubriconderdeel | Gewicht | Betekenis voor jouw werk |
|---|---:|---|
| Data & Annotation Strategy | 25% | Selectie, regels, moeilijke gevallen, review en splits verklaren |
| Modeling & Fine-Tuning Core | 35% | Training, augmentaties en gerichte experimenten onderbouwen |
| Failure & Error Analysis | 20% | Concrete fouten analyseren en hypotheses toetsen |
| End-to-End Pipeline & Homography | 10% | Overdracht, coördinaten en projectie begrijpen |
| Process & GenAI Ownership | 10% | Feedback verwerken en zelfstandig keuzes verdedigen |

### 1.3 Vaststaande keuzes en onderzoekskeuzes

| Vaststaand uitgangspunt | Betekenis |
|---|---|
| Twee personen | Eén gezamenlijke dataset en onderlinge review |
| YOLO11n Detect, `yolo11n.pt` | Pretrained vertrekpunt voor baseline en fine-tuning |
| Bounding boxes | Geen segmentatiemaskers nodig voor deze route |
| 40–80 eigen frames | Totaal voor het team, inclusief eventueel opgenomen testframes |
| RTX 4050 Laptop GPU | Beschikbaarheid uit het plan; hardware en vrij geheugen nog controleren |
| Beide mAP-varianten | Geen zelf verzonnen minimumscore |
| Geen kalenderplanning | Wel afhankelijkheden en controlemomenten |

Nog te onderzoeken: videobron, fragmenten, data gap, annotatietool, exacte labelregels, modelrollen, splits en inference-instellingen. De procedures hieronder bepalen hoe jullie die keuzes nemen.

## 2. Samenwerking, versiebeheer en bewijsvoering

### 2.1 Verantwoordelijkheden

| Onderdeel | Persoon 1 | Persoon 2 |
|---|---|---|
| Bronkeuze en scope | Zoeken en vergelijken | Camera en veld beoordelen |
| Baseline en data gap | Uitvoeren en onderbouwen | Bevindingen reviewen |
| Annotaties | Eigen helft maken; andere helft reviewen | Eigen helft maken; andere helft reviewen |
| Dataset en splits | Manifest en controles beheren | Onafhankelijkheid reviewen |
| Training en evaluatie | Runs uitvoeren en analyseren | Configuraties en conclusies reviewen |
| Geometrie en toepassing | Detectoruitvoer leveren; inhoud reviewen | Hoofdverantwoordelijk |
| Tracking | Referentie-ID's en fouten mee beoordelen | Hoofdverantwoordelijk |
| Eindverslag en verdediging | Detectie- en datadeel | Geometrie- en toepassingsdeel; gezamenlijke review |

De GPU-eigenaar hoeft niet automatisch persoon 1 te zijn. Bewaar de omgeving en configuratie zo dat de andere persoon de uitvoering kan begrijpen en opzetten.

### 2.2 Werken met kleine, controleerbare wijzigingen

1. Maak per afgebakende taak een issue met doel, eigenaar, afhankelijkheden, bewijs en Definition of Done.
2. Werk op een taakbranch, bijvoorbeeld `feature/baseline-evaluation`.
3. Leg samenhangende wijzigingen in kleine commits vast.
4. Beschrijf in de pull request wat veranderde, waarom, welke controle gebeurde en welke gegevensoverdracht wordt geraakt.
5. De ander controleert relevante labels, instellingen, resultaten en uitleg.
6. Merge na geslaagde controles en inhoudelijke review; werk daarna beide checkouts bij.

Een klassewijziging raakt annotaties, modeluitvoer, evaluatie en mogelijk de toepassing. Coördineer zo'n wijziging gezamenlijk en versieer de bijbehorende data. Pas niet alleen een klassenaam aan terwijl oude resultaten dezelfde naam houden.

### 2.3 Registers en bewijsstatus

Gebruik de invulsjablonen voor een beslisregister (`DEC`), experimentregister (`EXP`), foutencatalogus (`ERR`) en AI-log (`AI`). Een record krijgt pas de status afgerond wanneer de controle en reviewer werkelijk bekend zijn.

Een experiment verwijst minimaal naar codeversie, datasetversie, splitversie, modelidentiteit en volledige instellingen. Bestandsnamen zoals `best.pt` zijn geen unieke modelidentiteit: noteer ook een checksum en de bijbehorende run.

Gebruik voor controles de statussen `open`, `bezig`, `wacht op review`, `goedgekeurd` en `afgewezen`. Een open regel wordt niet automatisch goedgekeurd omdat de volgende fase al begonnen is.

## 3. Werkpakket per fase

### Fase 0 — Scope en werkafspraken controleerbaar maken

**Doel:** beiden weten wat moet worden bewezen en waar dat bewijs terechtkomt.

**Stappen**

1. Neem REQ-01 tot en met REQ-12 en EXT-01 over in de bewijschecklist.
2. Verbind iedere vereiste met een concrete oplevering, eigenaar en reviewer.
3. Spreek opslag en toegang tot video, annotaties en gewichten af. Bewaar grote bestanden buiten gewone commits.
4. Maak de vier registers aan met de bijgeleverde sjablonen; vul nog geen fictieve resultaten in.
5. Inventariseer GPU, videogeheugen, Python, PyTorch, CUDA-beschikbaarheid, Ultralytics en besturingssysteem.
6. Leg vast welke omgeving tijdens de experimentreeks wordt gebruikt en hoe versies later worden vastgezet.

**Concrete controle:** laat beide personen de route video → detecties → projectie → gesynchroniseerde weergave uitleggen. Laat ze ook het verschil tussen training, validatie en eindtest toelichten.

**Bewaren:** scopechecklist, afspraken over bestanden, omgevingsinventaris en eerste beslisrecords.

**Klaar wanneer:** alle vereisten een bewijsplaats hebben en beiden de rolverdeling en projectgrenzen begrijpen. Een hardware-inventaris is nog geen bewijs dat batch 4 past; dat wordt in fase 5 gemeten.

### Fase 1 — Geschikte videodata vinden en de evaluatie begrenzen

**Doel:** een bron kiezen die tegelijk detectie, annotatie, kalibratie en evaluatie mogelijk maakt.

**Stappen**

1. Zoek doorlopende voetbalvideo's met een vast tactisch of broadcaststandpunt. Beoordeel onderzoeksdata, beschikbare tactische beelden of een eigen vaste opname als die voorhanden is.
2. Noteer bronlink, aanbieder, beschikbare bestanden, toegangsvoorwaarden en relevant fragment. Noteer ook waarom een kandidaat afvalt.
3. Bekijk een doorlopend fragment op cuts, pannen en zoomen. Beoordeel een opname niet op één mooi stilstaand frame.
4. Laat persoon 2 minstens vier bekende, verspreide veldpunten controleren. De punten mogen niet allemaal op één lijn liggen. Het hele veld hoeft niet zichtbaar te zijn, zolang de ondersteunde zone verdedigbaar is.
5. Onderzoek op bronresolutie of relevante kleine of snel bewegende objecten in voldoende verschillende situaties labelbaar zijn.
6. Controleer of losse fragmentgroepen beschikbaar zijn voor ontwikkeling en eindevaluatie.
7. Leg goedgekeurde video, clipgrenzen, resolutie, duur, framerate, eventuele conversie en bestandschecksum vast.
8. Spreek af welke generalisatie wordt onderzocht en reserveer eindtestfragmenten vóór analyse van modeluitvoer.

**Besliscriteria**

| Vraag | Een kandidaat gaat alleen verder wanneer |
|---|---|
| Kan de video worden gebruikt? | Toegang en lokaal gebruik voldoende duidelijk zijn |
| Blijft kalibratie bruikbaar? | Camerastabiliteit en geschikte veldpunten zijn gecontroleerd |
| Kunnen we zinvol annoteren? | Genoeg moeilijke, maar betrouwbaar herkenbare situaties beschikbaar zijn |
| Kunnen we evalueren? | Ontwikkeling en eindevaluatie op onderbouwde wijze te scheiden zijn |
| Kunnen we reproduceren? | Beiden exact dezelfde beelden kunnen verkrijgen |

Bij twijfel over de camera beslist de geometriecontrole vóór de definitieve bronkeuze. Bij onvoldoende onafhankelijke fragmenten onderzoek je een andere bron voordat je de annotaties vastlegt.

**Generalisatie:** nieuwe momenten uit dezelfde opname zijn een beperkter doel dan andere wedstrijden of camera's. Kies de claim die je data ondersteunt. Een moeilijke selectie beschrijft bovendien prestaties op die selectie; ze is niet automatisch representatief voor een volledige wedstrijd.

**Testdiscipline:** bronkwaliteit en veldgeometrie mogen vooraf worden beoordeeld. Modeluitvoer op gereserveerde testfragmenten gebruiken om fouten, thresholds of architectuur te kiezen maakt die fragmenten ontwikkeldata.

**Bewaren:** bronnenregister, bronbesluit, videorecord, fragmentgroepschema en beoogde generalisatie.

**Klaar wanneer:** beide personen dezelfde goedgekeurde video openen en persoon 2 geometrie en camerastabiliteit heeft beoordeeld. Er is een uitvoerbare route naar voldoende gevarieerde frames en een eerlijke eindbeoordeling.

### Fase 2 — Pretrained baseline onderzoeken en de data gap kiezen

**Doel:** aantonen wat het bestaande model mist voordat je gericht data gaat maken.

**Stappen**

1. Laad de ongewijzigde `yolo11n.pt` en leg modelidentiteit, softwareversie en inference-instellingen vast.
2. Controleer de werkelijke modelklassen. `person` bewijst geen onderscheid tussen speler, scheidsrechter, trainer en publiek.
3. Gebruik uitsluitend de ontwikkelfragmenten voor deze verkenning.
4. Bekijk voorspellingen naast de bronbeelden en noteer detecties, missers en twijfelgevallen.
5. Bewaar herkenbare succes- én foutvoorbeelden met frame-identiteit.
6. Onderzoek meerdere mogelijke tekortkomingen, maar kies een data gap die voldoet aan de opdracht: een klein of snel bewegend object, of sportspecifiek materiaal.
7. Lever nu al echte detectoruitvoer voor een vast ontwikkelfragment aan persoon 2.

| Mogelijk patroon, nog geen resultaat | Wat je controleert |
|---|---|
| Kleine bal wordt gemist | Objectgrootte en zichtbaar detail na preprocessing |
| Reclame veroorzaakt een baldetectie | Terugkeer van dezelfde achtergrondverwarring |
| Bewegende bal heeft wisselende detecties | Blur, confidence en zichtbaarheid in de bron |
| Personen worden gemist bij overlap | Occlusion, boxen en nabewerking |

**Beslisprocedure voor de data gap:** kies alleen een kandidaat die aantoonbare terugkerende baselinefouten heeft, relevant is, betrouwbaar labelbaar is en voldoende verschillende voorbeelden oplevert. Leg de afweging per kandidaat vast. Algemene persoonsdetectiefouten zijn nuttig onderzoek, maar vervangen niet zonder onderbouwing de gerichte target uit de opdracht.

De bal blijft een kandidaat totdat het bronnenonderzoek en de baseline hem ondersteunen. Als de bal in vrijwel alle moeilijke beelden onbeslisbaar is, kies je andere beelden of een passend alternatief; je verzint geen locaties.

**Baseline versus meting:** deze fase levert een kwalitatieve fouteninventaris. De formele kwantitatieve baseline volgt zodra data, splits en klassen vastliggen in fase 6.

**Bewaren:** baselineconfiguratie, modelchecksum, ontwikkelfragment, foutrecords en gemotiveerd data-gapbesluit.

**Klaar wanneer:** beide personen aan concrete frames kunnen uitleggen waarom de gekozen target eigen annotaties nodig heeft. Persoon 2 kan de eerste uitvoer in het afgesproken formaat lezen.

### Fase 3 — Annotatietool, labelregels en modelrollen bepalen

**Doel:** één betekenis van de labels vastleggen en een export testen voordat iedereen veel werk uitvoert.

#### 3A. Kies de tool met een werkelijke proef

Beoordeel bijvoorbeeld CVAT of Roboflow op mogelijkheden en beschikbare toegang; hun namen vormen geen vooraf gemaakte keuze. Een tool is geschikt als je automatische boxvoorstellen kunt maken of importeren, ze handmatig kunt corrigeren en naar YOLO-detectieformaat kunt exporteren. Bewaar ook een controleerbaar voorbeeld van voorstel en eindlabel.

Importeer proefbeelden en laat het trainingsframework de export lezen. Visualiseer de teruggelezen boxen. Een geslaagde exportknop alleen bewijst geen juiste klassevolgorde of coördinaten.

Een YOLO-detectieregel beschrijft `class_id x_center y_center width height`, met genormaliseerde coördinaten. Verwar dat trainingsformaat niet met het pixelgebaseerde `xyxy`-overdrachtsformaat voor persoon 2.

#### 3B. Doe een gezamenlijke proef op zes frames

Kies een duidelijk object, een klein object, occlusion, blur, een object aan de beeldrand en een frame zonder target. Laat beiden eerst onafhankelijk annoteren. Vergelijk daarna aanwezigheid, klasse en boxbegrenzing.

Bespreek ieder verschil. Leg de eindregel vast met beeldverwijzing, reden en reviewer. Begin pas aan de volledige ronde wanneer de proefgevallen volgens dezelfde regels worden behandeld. De zes proefbeelden mogen binnen de 40–80 frames meetellen als ze aan de definitieve selectievoorwaarden voldoen.

| Geval | Afspraak die in de handleiding moet staan |
|---|---|
| Gedeeltelijke occlusion | Welke zichtbare aanwijzingen voldoende zijn; zichtbare of geschatte volledige box consequent kiezen |
| Volledig verborgen | Geen objectlocatie verzinnen |
| Beeldrand | Box correct begrenzen; afsnijding registreren |
| Blur | Uitleggen wanneer aanwezigheid én begrenzing nog betrouwbaar zijn |
| Zeer klein | Bronresolutie beoordelen; twijfel niet door een gok vervangen |
| Werkelijk afwezig | Gecontroleerd negatief frame met expliciet lege annotatie |
| Mogelijk aanwezig, onbeslisbaar | Voorlopig buiten supervisie en scored evaluatie houden; reden registreren |

Bewaar moeilijke uitgesloten frames desgewenst als kwalitatieve voorbeelden met de status onbeslisbaar. Behandel ze niet als betrouwbare negatieve trainingsbeelden. Als het exportformaat geen ignore-regio's ondersteunt, is een onbeslisbaar target simpelweg ongelabeld laten geen veilige oplossing.

#### 3C. Leg modelrollen vast

| Route | Voorwaarden | Belangrijkste controle |
|---|---|---|
| Eén model voor personen en target | Alle opgenomen klassen volledig en consistent gelabeld; passende evaluatie beschikbaar | Behoud van personendetectie na fine-tuning |
| Pretrained personendetector plus specialist | Gerichte labels dekken vooral de target; beide modeluitvoeren blijven herkenbaar | Samenvoeging, klassebetekenis en verwerkingstijd |

Vergelijk annotatiebelasting, klassendekking, behoud van functies en uitvoerbaarheid. Kies de eenvoudigste route die alle vereiste detectiefuncties verantwoord behoudt. Leg de gekozen route, afgewezen route en redenen vast vóór training.

Bij een gezamenlijk model zijn ongelabelde personen in trainingsbeelden geen onschuldige weglating. Bij een specialist hoeft een trainingsklasse voor personen niet te bestaan, maar die specialist wordt dan ook niet voorgesteld als vervanging van de personendetector.

**Bewaren:** toolproef, klassenlijst, annotatiehandleiding, zes besproken proefbeelden, correctievoorbeelden en besluit over modelrollen.

**Klaar wanneer:** export en teruglezing werken, meningsverschillen zijn opgelost en beiden kunnen uitleggen welke detector welke functie vervult.

### Fase 4 — Frames selecteren, annoteren, reviewen en splits vastzetten

**Doel:** één gecontroleerde dataset maken zonder kunstmatig gunstige evaluatie door bijna identieke frames.

#### 4A. Selecteer en registreer de frames

Selecteer ontwikkelframes op basis van de aangetoonde fouttypen. Selecteer testframes met vooraf vastgelegde tijd- en situatiecriteria, zonder te kijken waar het model goed of slecht presteert. Gebruik voor een verplichte uitdagende eindselectie criteria als zichtbaarheid, objectgrootte en blur, onafhankelijk van voorspellingen.

Registreer per frame minimaal: frame-ID, video-ID, oorspronkelijke frame-index, presentatietijd, breedte, hoogte, fragmentgroep, selectiereden, situatiekenmerken, annotator, reviewer, reviewstatus, subset en datasetversie.

Een frame kan meerdere kenmerken hebben. Een beeld met blur én occlusion telt als één frame en kan in beide beschrijvende categorieën vallen. Sommeer zulke categorieën niet alsof ze onderling exclusief zijn.

#### 4B. Annoteren en volledig reviewen

1. Genereer automatische voorstellen met geregistreerd model en instellingen.
2. Bekijk ieder relevant object op het bronbeeld; zoek ook buiten de voorgestelde boxen naar gemiste objecten.
3. Corrigeer foutieve klassen, afmetingen, locaties en gemiste objecten.
4. Leg negatieve frames bewust vast; een ontbrekend labelbestand is niet automatisch een negatieve annotatie.
5. Laat de ander alle beelden en labels in het pakket reviewen.
6. Los verschillen volgens de handleiding op en laat correcties bevestigen.
7. Bewaar representatieve beelden vóór en na correctie.

Automatische voorstellen voor testlabels mogen de menselijke controle ondersteunen, maar testvoorspellingen en correctieanalyses worden niet gebruikt voor modelkeuze. Laat testreview waar mogelijk door het teamlid zonder actieve tuningrol uitvoeren en bespreek de modelproblemen pas na de freeze.

#### 4C. Controleer de dataset

| Controle | Vereiste uitkomst |
|---|---|
| Beelden | Allemaal leesbaar, juiste afmetingen en identiteit |
| Koppeling | Elk opgenomen beeld heeft een gecontroleerde annotatiestatus |
| Klassen | Alleen vastgelegde klasse-ID's en betekenissen |
| Boxen | Eindige coördinaten, positieve afmetingen, binnen de afgesproken grenzen |
| Duplicaten | Identieke beelden opgespoord; bijna identieke beelden onderzocht |
| Review | Alle gebruikte annotaties door de ander goedgekeurd |
| Negatieven | Onderscheiden van ontbrekende of onbeslisbare labels |

#### 4D. Splits op fragmentgroepen

Houd samenhangende of bijna identieke momenten bij elkaar. Splits niet willekeurig op losse frames. Gebruik tijd, scène-inhoud en groepsgrenzen om te onderzoeken of ontwikkel- en evaluatiebeelden te sterk op elkaar lijken.

1. Leg onafhankelijke fragmentgroepen vast.
2. Wijs groepen toe aan train, validatie en eindtest volgens het vooraf gereserveerde schema.
3. Onderzoek de grenzen van de groepen op bijna identieke beelden.
4. Tel frames, objecten, positieve en negatieve frames en moeilijke situaties per subset.
5. Controleer of evaluatiesubsets de relevante target daadwerkelijk bevatten.
6. Laat persoon 2 de indeling en beperkingen reviewen.
7. Zet manifest en datasetversie vast vóór de formele experimentreeks.

Leg geen percentages op voordat de groepsstructuur is onderzocht. **Rekenvoorbeeld, geen gekozen split:** 60 frames kunnen 36/12/12 worden verdeeld, maar dat zegt zonder onafhankelijke groepen en voldoende objecten niets over de kwaliteit van de evaluatie.

Als een afzonderlijke testset niet verantwoord mogelijk is, onderzoek eerst een andere bron of een expliciet afgesproken scopewijziging. Blijft alleen een beperkte ontwikkelmeting mogelijk, rapporteer dat eerlijk. Gebruik geen validatiebeelden als zogenaamd onaangeraakte eindtest.

**Bewaren:** definitieve annotaties, frame- en splitmanifest, kwaliteitsrapport, aantallen per subset en goedkeuringen.

**Klaar wanneer:** alle labels gereviewd zijn, de split geen directe of onderzochte bijna-dubbele overlap bevat en de beperkingen van de evaluatie expliciet zijn. Start training niet vóór deze controle.

### Fase 5 — Preprocessing controleren en de eerste fine-tuning uitvoeren

**Doel:** één herleidbare trainingsreferentie opzetten die op de beschikbare laptop werkt.

#### 5A. Voer een technische proef uit

Controleer de GPU, laad kleine hoeveelheden goedgekeurde train/val-data en bekijk de door de loader getoonde beelden en boxen. Bewaar de werkelijk gebruikte softwareversies. De technische proef krijgt een eigen identiteit en wordt niet als formeel experiment gerapporteerd.

Controleer dat resizing en letterboxing maar op de bedoelde plek gebeuren. Dubbele preprocessing kan de beeldkwaliteit en coördinaten verstoren.

**Rekenvoorbeeld:** een bal van 12 pixels breed in een beeld van 1920 pixels breed wordt bij een schaalfactor van 640/1920 ongeveer 4 pixels breed, vóór eventuele overige bewerkingen. Controleer de werkelijke loaderuitvoer; gebruik dit voorbeeld niet als gemeten objectgrootte.

#### 5B. Gebruik de vaste startconfiguratie

| Instelling | Waarde | Betekenis of controle |
|---|---:|---|
| Model | `yolo11n.pt` | Pretrained initialisatie, geen willekeurige nieuwe training |
| Taak | Detectie | Bounding boxes |
| `imgsz` | 640 | Eerste referentieresolutie |
| `batch` | 4 | Werkelijke accumulation en effectieve batch ook bewaren |
| `epochs` | 100 | Bovengrens |
| `patience` | 20 | Stopregel op de vastgelegde validatiefitness |
| `optimizer` | Adam | Expliciet; geen automatische optimizerkeuze |
| `lr0` | 0.001 | Initiële learning rate |
| `lrf` | 0.01 | Geplande eindfactor |
| `cos_lr` | False | Referentie gebruikt geen cosineschema |
| `warmup_epochs` | 3 | Warmup aan begin |
| `warmup_bias_lr` | 0.0 | Bias-warmup vanaf deze waarde |
| `weight_decay` | 0.0005 | Effectieve frameworkinstelling bewaren |
| `freeze` | 10 | Modules 0–9; niet als volledige backbone omschrijven |
| `amp` | True | Compatibiliteitscontrole laten uitvoeren |
| `seed` | 42 | Willekeur vastleggen |
| `deterministic` | True | Vergelijkbaarheid bevorderen; geen garantie op alle hardware |
| Validatie en opslaan | Aan | Curves en checkpoints bewaren |

**Geheugenregel:** probeer batch 4, daarna 2 en zo nodig 1. Verander tijdens deze terugval niet tegelijk resolutie, optimizer en learning rate. De eerste werkende vaste batch wordt de referentie. Als zelfs batch 1 niet werkt, registreer je de fout en neem je eerst een nieuw technisch besluit; je presenteert een aangepaste configuratie niet als dezelfde referentie.

#### 5C. Houd augmentatie beperkt en expliciet

Gebruik `fliplr=0.5`. Zet `flipud`, `degrees`, `translate`, `scale`, `shear`, `perspective`, `hsv_h`, `hsv_s`, `hsv_v`, `mosaic`, `mixup`, `copy_paste` en `close_mosaic` op 0. Inventariseer verdere automatische augmentaties van de gekozen versie. Als iets actief blijft, leg dat vast vóór de eerste formele run.

Pas trainingsaugmentaties niet toe op validatie, test of kalibratiebeelden. Een horizontale spiegeling kan klassen behouden, maar verandert wel de relatie met een bestaande veldkalibratie.

#### 5D. Train, selecteer en archiveer

Start iedere zelfstandige vergelijkingsrun vanuit de afgesproken pretrained initialisatie, tenzij doorgaan vanuit een vorig checkpoint juist de expliciete hypothese is. Gebruik een verse modelinstantie om onbedoeld verder trainen te voorkomen.

Bewaar de volledige uiteindelijke configuratie, terminal- of uitvoeringslog, trainings- en validatiecurves, checkpoints, duur, geheugen en eventuele crashes. Gebruik het door validatie geselecteerde `best.pt` met de vastgelegde fitnessdefinitie. De laatste epoch is niet automatisch het beste checkpoint. Early stopping kan verhinderen dat de geplande eindwaarde van de learning rate wordt bereikt.

**Klaar wanneer:** de formele run zonder onopgeloste datafouten voltooid is en persoon 2 de uitvoering kan reconstrueren. Testdata is niet gebruikt voor instellingen of checkpointselectie.

### Fase 6 — Baseline en fine-tuning eerlijk vergelijken

**Doel:** verandering in detectiekwaliteit meten op dezelfde annotaties en onder vergelijkbare voorwaarden.

#### 6A. Maak klassen vergelijkbaar

Leg de semantische mapping vast: modelidentiteit + lokaal klasse-ID → betekenis in de evaluatie. Een nummer 0 heeft niet in elk model dezelfde betekenis. Voor een balvergelijking kan de pretrained klasse `sports ball` aan de lokale balclass worden gekoppeld wanneer de scope dat rechtvaardigt. Neem andere pretrained klassen niet onbedoeld in het targetgemiddelde mee.

Bij een custom éénklassige dataset is alleen de datasetconfiguratie wijzigen niet voldoende om pretrained voorspellingen betrouwbaar te hernoemen. Verifieer filtering en mapping met een gecontroleerd voorbeeld in de gekozen evaluator.

Rapporteer persoonsmetrics alleen als de evaluatiebeelden de bedoelde personen volledig volgens dezelfde semantiek annoteren. Een subset van spelers is geen volledige referentie voor een algemene klasse `person`.

#### 6B. Houd de meting vast

Gebruik dezelfde subset, labels, inferentieresolutie, preprocessing en relevante nabewerkingsinstellingen. Registreer onder meer confidence-ondergrens, NMS-instellingen en maximale detecties. Kies instellingen voor vergelijkbaarheid; optimaliseer ze niet afzonderlijk op de eindtest.

| Run | Dataset / split | Klasse | Frames / objecten | mAP@50 | mAP@50:95 | Precision | Recall |
|---|---|---|---|---|---|---|---|
| Pretrained baseline | Nog vast te leggen | Gekozen target | Nog tellen | Nog meten | Nog meten | Nog meten | Nog meten |
| Eerste fine-tuning | Dezelfde evaluatieset | Dezelfde target | Dezelfde aantallen | Nog meten | Nog meten | Nog meten | Nog meten |

IoU is de overlap van voorspelling en label gedeeld door hun vereniging. AP vat de precision-recallcurve per klasse samen. Bij één klasse komt mAP over die ene klasse overeen met die klasse-AP. mAP@50 gebruikt IoU 0,50; mAP@50:95 middelt over 0,50 tot en met 0,95 met stappen van 0,05.

Een vaste confidence voor de toepassing is een apart werkpunt. Gebruik die niet ongemerkt om lage-confidencevoorspellingen weg te gooien voordat een volledige AP-vergelijking wordt gemaakt. Vermeld bij precision en recall op welk werkpunt of volgens welke evaluatorselectie ze zijn bepaald.

**Rekenvoorbeeld:** bij 8 correcte detecties, 2 onterechte detecties en 4 gemiste objecten is precision 8/10 = 0,80 en recall 8/12 ≈ 0,67. Dit is een uitlegvoorbeeld, geen projectresultaat.

#### 6C. Kies een model met vaste criteria

Gebruik voor vergelijking tussen runs primair mAP@50:95 van de gekozen target, daarna mAP@50 en concrete foutvoorbeelden. Bij gelijke metrics en vergelijkbare bruikbaarheid krijgt de eenvoudigere, lichtere configuratie de voorkeur. Verklaar een klein verschil op weinig objecten niet automatisch als overtuigende winst.

Checkpointselectie binnen een run blijft gebaseerd op de vooraf geregistreerde frameworkfitness. Verwar die selectie niet met de vergelijking tussen zelfstandige experimenten.

Controleer noodzakelijke functies: een gezamenlijk model mag bruikbare personendetectie niet ongemerkt verliezen. Een hogere targetscore maakt een onbruikbare geïntegreerde pipeline niet acceptabel.

Meet snelheid alleen wanneer relevant. Maak onderscheid tussen modelinference, laden/decoderen en volledige verwerking. Geef hardware, beeldgrootte, warmup en meetmethode aan; beloof geen realtimewerking zonder meting.

**Bewaren:** resultaatrecords, evaluatieconfiguraties, curves, aantallen en gekoppelde succes- en foutbeelden.

**Klaar wanneer:** beide mAP-varianten aanwezig en herleidbaar zijn en de vergelijking dezelfde semantiek gebruikt. Er is geen verzonnen minimumscore.

### Fase 7 — Fouten verklaren en hypotheses opstellen

**Doel:** een volgende ingreep laten volgen uit concrete observaties.

Bekijk voorspelling, annotatie en bronbeeld naast elkaar. Leg voor ieder belangrijk patroon frame-identiteit, fouttype, situatie, observatie, hypothese, alternatief en voorgestelde controle vast.

| Fout | Betekenis | Eerste controles |
|---|---|---|
| False positive | Voorspelling zonder correcte match volgens de evaluatieregels | Achtergrond, duplicaat, klasse en mogelijk ontbrekend label |
| False negative | Geannoteerd object zonder geldige match | Zichtbaarheid, grootte, confidence, nabewerking en klasse |
| Verkeerde klasse | Object gevonden maar verkeerd benoemd | Labelbetekenis en mapping |
| Lokalisatiefout | Box overlapt onvoldoende | Annotatieregel, preprocessing en afmetingen |
| Dubbele detectie | Meerdere voorspellingen voor hetzelfde object | Matching en nabewerking |

Gebruik voor getelde FP/FN een vast confidencewerkpunt, een vaste matchregel en een één-op-éénmatching. Eén object mag niet twee true positives opleveren. Een verkeerde klasse kan bij formele telling zowel een FP als een FN veroorzaken; leg uit hoe je rapportage daarmee omgaat.

**Uitgewerkt voorbeeld, geen waarneming**

- Observatie: kleine ballen op afstand lijken vaak gemist te worden.
- Hypothese: verkleinen verwijdert bruikbaar detail.
- Alternatief: dit type situatie ontbreekt in training of de labels zijn onbetrouwbaar.
- Controle: vergelijk objectgroottes, bronbeelden, loaderbeelden en de verdeling van situaties.
- Experiment: hogere trainingsresolutie als detailverlies voldoende aannemelijk is.
- Tegenspraak: geen verbetering op dezelfde validatieset en dezelfde inferentieresolutie.

Maak onderscheid tussen foutaantallen en aantallen frames. Een frame kan meerdere fouten en meerdere moeilijke kenmerken bevatten. Bekijk ook voorbeelden waarin dezelfde moeilijke situatie wél goed gaat; dat helpt alternatieve verklaringen toetsen.

Corrigeer evaluatielabels alleen wanneer een echte annotatiefout is vastgesteld. Laat de ander dat bevestigen, verhoog de datasetversie en meet de betrokken referenties opnieuw. Wijzig labels niet om voorspellingen gunstiger te laten scoren.

**Klaar wanneer:** de belangrijkste terugkerende fouten concrete voorbeelden en ten minste één toetsbare hypothese hebben. 'De bal is moeilijk' is onvoldoende als verklaring.

### Fase 8 — Gecontroleerde verbeterexperimenten uitvoeren

**Doel:** met een passende vergelijking bepalen welke wijziging helpt.

| Onderbouwde aanleiding | Eerste gerichte proef | Gelijk houden |
|---|---|---|
| Detailverlies bij kleine objecten | `imgsz=960` tegenover 640 | Data, model en overige keuzes; batch alleen volgens geheugenregel |
| Onvoldoende aanpassing na labelcontrole | `freeze=0` tegenover 10 | Overige referentie-instellingen |
| Instabiele updates | `lr0=0.0001` tegenover 0.001 | Model, data en overige configuratie |
| Te specifieke trainingsaanblik | Eén extra realistische augmentatie | Rest van de vergelijking |

Vul vóór iedere run vraag, hypothese, referentie, wijziging, verwachte uitkomst en beslisregel in. Verander niet een volledig pakket instellingen tegelijk.

Bij 640 tegenover 960 evalueer je beide modellen ook onder dezelfde inferentieresolutie. Vermeld een noodzakelijke batchverandering als bijkomend verschil. Zo voorkom je dat groter invoeren tijdens inference als zuiver trainingseffect wordt gepresenteerd.

Gebruik de modelselectiecriteria uit fase 6. Behoud een wijziging als kandidaat wanneer de validatie en relevante foutvoorbeelden voordeel ondersteunen en noodzakelijke functies bruikbaar blijven. Bij gemengde effecten rapporteer je de afweging. Bij onduidelijke winst is de eenvoudigere referentie de standaard; claim geen bewezen verbetering.

Als een hypothese geen steun krijgt, registreer je dat en kies je een andere onderbouwde richting. Stop met experimenteren wanneer geen concrete nieuwe hypothese resteert of verdere tuning de beperkte validatieset vooral dreigt te exploiteren.

Bij gewijzigde labels of data komt er een nieuwe datasetversie en een opnieuw gemeten referentie. Nieuwe data toevoegen buiten de afgesproken 40–80 frames wordt eerst gezamenlijk als scopewijziging beoordeeld.

**Bewaren:** complete experimentrecords, resultaten, verbeterde én verslechterde voorbeelden en verworpen hypotheses.

**Klaar wanneer:** de modelkeuze navolgbaar is en alle claims bij passende referenties horen. De testset is ongebruikt voor tuning gebleven.

### Fase 13 — Eindevaluatie, verslag en verdediging

**Doel:** een bevroren systeem eerlijk beoordelen en de uiteindelijke claims zelfstandig verdedigen.

**Stappen**

1. Leg code, dataset, split, gewichten, preprocessing, inference-instellingen en geïntegreerde configuratie vast in een freeze-record.
2. Laat beiden controleren dat geen open instelling nog van de testuitkomst afhankelijk is.
3. Voer de afgesproken onafhankelijke eindevaluatie uit; meet waar passend ook de vaste baseline op dezelfde testbeelden.
4. Bewaar alle resultaten en relevante fouten, ook als het eindmodel tegenvalt.
5. Rapporteer de grenzen van de kleine, gerichte selectie en van de ondersteunde camera.
6. Werk verslag, presentatie, startinstructies, bestandsidentiteiten en GenAI-disclosure af.
7. Laat ieder teamlid ook het hoofdonderdeel van de ander uitleggen.

Na inzage in testresultaten mag verder onderzoek, maar een verbeterde versie op dezelfde beelden is geen nieuwe onafhankelijke eindtest. Registreer die als nieuwe ontwikkelronde.

**Opbouw van jouw verslagdeel**

1. Probleem, ondersteunde video en generalisatie.
2. Baseline en keuze van de data gap.
3. Assisted labeling, regels, meningsverschillen en review.
4. Dataset, onafhankelijke groepen en splits.
5. Training, gerichte experimenten en modelkeuze.
6. Metrics, foutpatronen, resterende beperkingen en conclusie.

Bereid vijf echte verdedigingsvoorbeelden voor: een gecorrigeerd automatisch label, een false positive, een false negative, een nuttig experiment en een verworpen hypothese. Ontbreekt overtuigende winst, leg dan uit wat wel en niet uit de metingen volgt.

**Klaar wanneer:** de resultaten herleidbaar zijn en beiden de datastroom, training, evaluatie, annotatieregels en planaire aanname zonder AI kunnen uitleggen.

## 4. Overdracht en samenwerking met persoon 2

### 4.1 Intern detectiecontract

Dit contract is geïmplementeerd voor de geselecteerde bronframes. De geïntegreerde koppeling met persoon 2 moet nog worden gecontroleerd. Gebruik JSON Lines: één JSON-object per verwerkt bronframe, ook wanneer er geen detecties zijn.

| Veld | Afspraak |
|---|---|
| `schema_version` | `1.0` voor deze structuur |
| `video_id` | Verwijst naar het vastgelegde bronbestand en videorecord |
| `frame_index` | Nulgebaseerde index in die bronvideo; geen hernummering bij overslaan |
| `timestamp_s` | Presentatietijd vanaf het eerste gepresenteerde bronframe |
| `width`, `height` | Afmetingen van het oorspronkelijke, gedecodeerde frame |
| `run_id` | Verwijst naar de model- en inferenceconfiguratie |
| `detections` | Lijst; leeg als er geen detecties zijn |
| `model_id` per detectie | Identiteit van het model; checksum staat in het runrecord |
| `class_id` | Lokaal klasse-ID van dat model |
| `dataset_class_id` | Expliciete koppeling aan de klassevolgorde van deze dataset |
| `class_name` | Werkelijke modelklassenaam |
| `semantic_class` | Afgesproken betekenis, bijvoorbeeld `person` of gekozen target |
| `confidence` | Eindige score van 0 tot en met 1 |
| `bbox_xyxy` | Vier pixelcoördinaten `[x1, y1, x2, y2]` in het bronframe |

Coördinaten zijn continu; de rechter- en ondergrens mogen respectievelijk breedte en hoogte bereiken. Vereis `0 <= x1 < x2 <= width` en `0 <= y1 < y2 <= height`. Retourneer eventuele schaal- en letterboxtransformaties vóór overdracht. Een foutieve box wordt niet stilzwijgend als correcte positie doorgegeven.

Bij constante framerate controleer je tijd tegen `frame_index / fps`. Bij variabele framerate gebruik je geregistreerde presentatietijden. Als betrouwbare tijdstempels ontbreken, normaliseer je de bron gezamenlijk, geef je het nieuwe bestand een eigen identiteit en registreer je de conversie. Gebruik geen tijdstempels uit een ander bronbestand zonder mapping.

Een leeg detectieframe is iets anders dan een niet verwerkt frame. Een decodeer- of inferentiefout wordt met bronidentiteit gemeld en blijft een zichtbare verwerkingsfout. Presenteer zo'n fout niet als geldig leeg resultaat.

Dezelfde detectie krijgt niet automatisch de betekenis `player` omdat zij op een voetbalveld staat. Eventuele rolclassificatie of veldfiltering krijgt eigen regels en controles. Laat het model-ID behouden bij samenvoeging van meerdere detectoren.

### 4.2 Overdrachtsmomenten

| Moment | Jij levert | Samen controleren |
|---|---|---|
| Na fase 1 | Video-identiteit en ontwikkelfragment | Zelfde frames en afmetingen |
| Na fase 2 | Echte baseline-uitvoer en runrecord | Normaal, moeilijk en leeg frame; boxen op bronbeeld |
| Na fase 3 | Klassen en modelrollen | Geen stille betekeniswijziging |
| Na fase 8 | Geselecteerde modellen, versies en instellingen | Werkelijke uitvoer en resterende beperkingen |
| Voor eindtest | Freeze-record | Eén geïntegreerde configuratie |

De positiepunten voor veldprojectie worden met persoon 2 afgesproken. Een punt in een personenbox is niet automatisch het werkelijke grondcontactpunt. De homography geldt voor het speelvlak; een vliegende bal kan niet zonder meer als nauwkeurige grondpositie worden geïnterpreteerd.

### 4.3 Bijdrage aan ByteTrack

Begin na MVP-acceptatie met korte ontwikkelsequenties. Leg voor zichtbare spelers referentie-ID's, occlusions, verdwijnen en herintrede vast. Markeer onbeslisbare identiteiten als onzeker in plaats van een ID te verzinnen.

Vergelijk zichtbare ID-wissels, verloren trajecten en onterechte koppelingen. Laat persoon 2 trackerinstellingen, gebruikte confidencegrenzen en verwerking van overgeslagen frames documenteren. Detectieverbetering en trackingverbetering zijn afzonderlijke claims.

## 5. Controle, acceptatie en eindoplevering

### 5.1 Scenario's die je daadwerkelijk controleert

| Scenario | Verwachte controle | Bewijs |
|---|---|---|
| Proefexport met kleine en afgesneden box | Teruggelezen box blijft op het juiste object | Bronbeeld plus overlay |
| Negatief frame | Bewust lege annotatie en lege detectielijst blijven geldig | Reviewrecord en uitvoer |
| Ontbrekend label | Kwaliteitscontrole merkt ontbreken op | Controlelog |
| Bijna dubbele beelden bij groepsgrens | Samenvoegen of gemotiveerd anders indelen vóór splitfreeze | Overlapreview |
| Pretrained en lokale klasse-ID verschillen | Evaluator gebruikt gecontroleerde semantische mapping | Mappingproef |
| Batch 4 past niet | Alleen afgesproken batchterugval; werkelijke instellingen bewaard | Technisch log |
| Niet-vierkant beeld | Letterboxing komt correct terug in broncoördinaten | Detectie-overlay |
| Overgeslagen frames | Bronindex blijft behouden; tijd past bij bronmoment | Frame/tijdcontrole |
| Fine-tuning helpt niet | Negatief resultaat wordt volledig gerapporteerd | Vergelijking en conclusie |
| Geïntegreerde clip | Video en tactical map tonen hetzelfde bronmoment | Gesynchroniseerde demonstratie |

Deze scenario's zijn een controleplan. Ze zijn pas geslaagd wanneer de bijbehorende uitvoering en review bestaan.

### 5.2 Eindchecklist

- [ ] Bron, toegang, camerabeperkingen en beoogde generalisatie zijn beschreven.
- [ ] Baseline en data gap zijn onderbouwd met echte voorbeelden.
- [ ] De gezamenlijke dataset bevat 40–80 gecontroleerde frames.
- [ ] Assisted labeling, zes proefbeelden, labelregels en review zijn aantoonbaar.
- [ ] Dataset en splits zijn geversioneerd; overlap en kleine aantallen zijn onderzocht.
- [ ] Training is werkelijk uitgevoerd en aan configuratie en gewichten gekoppeld.
- [ ] Beide mAP-varianten zijn correct en vergelijkbaar gerapporteerd.
- [ ] Foutpatronen hebben voorbeelden, hypotheses en passende experimenten.
- [ ] Modelrollen behouden de noodzakelijke detectiefuncties.
- [ ] Persoon 2 gebruikt echte detectoruitvoer in juiste broncoördinaten.
- [ ] Minstens vier veldcorrespondenties en de projectie zijn gecontroleerd.
- [ ] De toepassing verwerkt de ondersteunde clip met gesynchroniseerde weergave.
- [ ] Het andere teamlid kan de uitvoering opzetten.
- [ ] Eindtestdiscipline, feedback en GenAI-gebruik zijn gedocumenteerd.
- [ ] Beiden kunnen het volledige systeem zelfstandig verdedigen.
- [ ] ByteTrack is na MVP-acceptatie afzonderlijk onderzocht en beoordeeld.

Er wordt geen mAP-ondergrens of snelheid verzonnen. Acceptatie berust op echte uitvoering, vergelijkbare metingen, verklaarde beperkingen en een werkende geïntegreerde toepassing.

## 6. Open beslissingen en hun beslismoment

| Beslissing | Eerst nodig | Beslisprocedure | Uiterlijk vóór |
|---|---|---|---|
| Videobron en fragment | Kandidaten en geometriecontrole | Alle noodzakelijke broncriteria uit fase 1 | Baselineanalyse |
| Generalisatie | Beschikbare onafhankelijke opnamen/groepen | Claim beperken tot wat evaluatie kan dragen | Splitreservering |
| Data gap | Baselinefouten en labelbaarheid | Criteria uit fase 2 | Definitieve selectie |
| Annotatietool | Werkelijke proefexport | Import, correctie, export en teruglezing aantonen | Volledige annotatie |
| Labelregels | Zes onafhankelijke proefannotaties | Verschillen bespreken en regels vastleggen | Volledige annotatie |
| Modelrollen | Klassendekking en annotatiebelasting | Routevergelijking uit fase 3 | Training |
| Splits | Onafhankelijke groepen en objectaantallen | Groepssplit en onderlinge review | Formele experimenten |
| Extra augmentatie | Onderbouwd foutpatroon | Eén gerichte ingreep met hypothese | Betreffend experiment |
| Inferencewerkpunt | Validatie en FP/FN-afweging | Vastleggen zonder testtuning | Systeemfreeze |
| Eindclaims | Bevroren systeem en eindresultaten | Beperken tot werkelijk getoetste uitkomsten | Verslag en verdediging |

Geen regel in dit overzicht is al als gezamenlijk goedgekeurd bedoeld. De uitvoerders vullen het beslisregister met werkelijke onderbouwing en reviewer in.

## 7. Technische bronnen

De exacte startconfiguratie is een projectkeuze, geen letterlijk voorgeschreven cursusconfiguratie. Controleer de betekenis en effectieve uitvoering tegen de versie die tijdens de technische proef wordt vastgezet.

- [Oorspronkelijke opdracht](../CV_Challenge_2026_2027.pdf).
- [Ultralytics YOLO11: modellen en taken](https://docs.ultralytics.com/models/yolo11/).
- [Ultralytics: detectiedatasets en annotatieformaat](https://docs.ultralytics.com/datasets/detect/).
- [Ultralytics: training en instellingen](https://docs.ultralytics.com/modes/train/).
- [Ultralytics: configuratiereferentie](https://docs.ultralytics.com/usage/cfg/).
- [Ultralytics: trainingsaugmentatie](https://docs.ultralytics.com/guides/yolo-data-augmentation/).
- [Ultralytics: validatie en metrics](https://docs.ultralytics.com/modes/val/).

Het oorspronkelijke aangeleverde werkpakket is inhoudelijke basis voor deze verdieping. De gekozen routes worden pas projectresultaten na uitvoering, controle en gezamenlijke goedkeuring.
