# Werkverdeling voor drie personen: de bestaande oplossing verbeteren

**Versie:** 26 oktober 2026. **Status:** werkplan; onderstaande taken zijn niet door dit document uitgevoerd of goedgekeurd. **Vertrekpunt:** GitHub `main`, commit `1e430c7`. De oorspronkelijke twee-persoonsdocumenten blijven historische plannen; dit document beschrijft de gevraagde samenwerking met drie personen en verandert geen formele opdrachtvereisten.

Het gezamenlijke product blijft een lokale voetbalvideo met detecties, rollen, Team A/B, betrouwbare veldtelling en een gesynchroniseerde tactical map. Eerst moet het vaste-camera-MVP betrouwbaar worden; tracking en camerabeweging krijgen daarna hun eigen acceptatie. Er wordt geen deadline of willekeurige mAP-/FPS-ondergrens toegevoegd.

**Uitvoering persoon 1:** [de derde uitvoeringsronde](Uitvoering_Persoon_1_Derde_Ronde.md) bevat het inmiddels uitgevoerde technische werk en de echte nieuwe metingen. De menselijke review-/eindtestvoorwaarden hieronder blijven gelden en zijn daarmee niet automatisch afgevinkt.

## 1. Wat bestaat en wat nog ontbreekt

| Onderdeel | Werkelijk aanwezig | Verbeterwerk |
|---|---|---|
| Detectie | Getrainde P004-basis, R007-standaard en R009/R010-alternatieven; vijf minder speler-FP door betere samenvoeging | Kleine/verre personen, gemiste centrale scheidsrechters, samengestelde boxen en verkeerde rollen |
| Data | Kernsets, uitbreidingen, hashes, splits en voorlopige AI-labels | Menselijke review, meer relevante onafhankelijke situaties en complete rolreferenties |
| Bal | Twee echte extra fine-tuningruns; beide verliezen van de baseline op AP@50:95 | Oorzaak onderzoeken en gericht verbeteren; negatieve runs niet als winst presenteren |
| Rollen | Speler, scheidsrechter, lijnrechter, steward, supporter en generieke persoon als uitvoer | Vooral stewards/supporters en overdracht naar andere camera's blijven zwak |
| Teams | Bekende-wedstrijdclassifier en verbeterde videolokale kleurclusters | Afwijkende keepersshirts, onbekende shirts, schaduw/occlusion en stabiliteit over tijd |
| Veld | Handmatige kalibratie en echte automatische veldroute | De onderzochte automatische Commons-proef heeft nog 0/120 bruikbare veldframes |
| Integratie | Volledige pilots van 150 en 120 frames; 217 tests en 4 subtests geslaagd bij het vertrekpunt | Nieuwe wijzigingen gezamenlijk toetsen, werkelijk op de RTX 4050 meten en menselijke acceptatie uitvoeren |

Dit zijn ontwikkelresultaten, geen onafhankelijke eindtest. Een correct teamlabel op een vooraf juiste persoonsbox is een andere meting dan volledige detectienauwkeurigheid. Een technisch geslaagde videorun bewijst evenmin juiste rollen of een juiste telling.

## 2. De hoofdverdeling

| Persoon | Hoofdverantwoordelijkheid | Belangrijkste oplevering |
|---|---|---|
| **1** | Data, annotatiebeleid, persoons-/rol-/baldetectie en modelonderzoek | Gereviewde datasets, aantoonbaar gekozen modellen en eerlijke detectie-/rolmetingen |
| **2** | Velddata, automatische veldherkenning, camerageschiktheid en projectie | Gecontroleerde veldgrenzen, actuele projectie en aantoonbaar correcte afwijzing bij onbetrouwbare geometrie |
| **3** | Team A/B, tracking, telling, interface, integratie en snelheid | Eén bruikbare toepassing met stabiele teams, gecontroleerde telregels en herhaalbare uitvoering op de 4050 |

Hoofdeigenaarschap betekent beslissingen, code en bewijs samenhouden; het betekent niet dat die persoon alle labels alleen moet maken. Iedere wijziging krijgt een andere reviewer. Iedereen moet bij de verdediging ook de grenzen tussen de drie onderdelen kunnen uitleggen.

## 3. Persoon 1 — data, detectie, rollen en echte modelwinst

### P1-01 — Rond menselijke labelreview en datasetadministratie af

- Maak een overzicht van de kernsets en historische uitbreidingen: gebruikte beelden, losse crops, bronvideo's, fragmentgroepen, labels, subsets en reviewstatus. Tel crops niet als onafhankelijke frames of wedstrijden.
- Controleer samen met persoon 3 de beelden en labels op ontbrekende personen, verkeerde rol, onjuiste boxgrens, duplicaten en onbeslisbare gevallen. Registreer echte namen en correcties pas nadat die review heeft plaatsgevonden.
- Houd `player` voor veldspelers én doelmannen; onderscheid `referee`, `assistant_referee`, `steward`, `spectator` en onzekere `person`. Leg expliciet vast welke klassen een detector voorspelt en welke de aanvullende classifier voorspelt.
- Wijs voor rolvalidatie aan welke beelden volledig geannoteerd zijn. Een fotocrop van één steward is geen volledige referentie voor alle stewards of spelers in die foto.
- Houd samenhangende tijdgroepen en bijna identieke beelden bij elkaar. Controleer ook visuele overlap tussen groepsgrenzen. Leg nieuwe eindtestgroepen vast voordat modeluitvoer wordt bekeken. Reeds gebruikte validatiebeelden blijven ontwikkeldata.
- Houd uitbreiding buiten de oorspronkelijke kernselectie apart geregistreerd. Leg vast waarom extra data nodig is; voeg niet ongecontroleerd bijna gelijke frames toe.

**Klaar als:** bestands-/labelcontroles slagen, conflicten zijn opgelost, groepsscheiding is onderbouwd en de menselijke reviewstatus waarheidsgetrouw is. **Bewijs:** manifesten, annotatiehandleiding, correctie-/reviewregister en splitcontrole. **Reviewer:** persoon 3.

### P1-02 — Verzamel gericht ontbrekende situaties

Begin bij terugkerende fouten, niet bij het maximale aantal downloads. Verzamel ontwikkelvoorbeelden van:

- Kleine/verre spelers, overlap, onscherpte en één box die meerdere mensen bevat.
- Centrale scheidsrechters en lijnrechters op verschillende afstanden.
- Stewards, supporters, staf en reservespelers die met spelers worden verward, ook bij de veldrand en waar mogelijk binnen dezelfde cameraverdeling als de toepassing.
- Verschillende kleding, belichting en relevante nieuwe bronnen om overdracht te onderzoeken.
- Kleine of bewegende ballen en vergelijkbare achtergronden die tot FP leiden.

Laat persoon 2 vooraf beoordelen of een nieuwe video ook voor de veldtaak bruikbaar is. Een bron mag wel rolonderzoek ondersteunen als haar geometrie ongeschikt is, maar rapporteer die beperktere toepassing. Bewaar bron, toegestaan gebruik, oorspronkelijke afmetingen, exacte frames en hashes. De dataset is volledig gelabeld voor de gekozen taak; een zichtbaar maar ongelabeld doelobject mag niet stilzwijgend achtergrond worden.

**Klaar als:** de nieuwe selectie aantoonbaar een geregistreerde foutcategorie dekt en haar labels gecontroleerd zijn. **Bewijs:** bronregister, voor/na-labelvoorbeelden en nieuwe datasetversie. **Reviewer:** persoon 3 voor rollen, persoon 2 voor brongeometrie.

### P1-03 — Verbeter detectie en rolherkenning met vergelijkbare experimenten

1. Bevries de huidige R007-baseline en bewaar ook R009 als referentie. Behoud bronklassen en bestaande gewichtshashes.
2. Onderzoek eerst of het probleem in het detectorvoorstel zit of in de classifier. Een correcte rolclassifier kan een volledig gemiste persoon niet terughalen.
3. Vergelijk alleen onderbouwde wijzigingen: relevante extra labels, resolutie, gecontroleerde uitsneden, classifiertraining of één passende augmentatie. Houd de rest van de vergelijking gelijk en registreer een eventueel noodzakelijke batchwijziging.
4. Meet speler-/official-/baldetectie met AP@50 en AP@50:95; rapporteer het gemiddelde alleen over expliciet genoemde, volledig gelabelde klassen. Geef daarnaast FP/FN, precision/recall op de afgesproken werkgrens en rolverwarring per klasse.
5. Meet rolclassificatie op correcte crops apart van de volledige detector. Rapporteer abstentie/`person` en het aantal referenties per rol.
6. Vergelijk ook de oude bronnen: winst op de nieuwe opname mag een terugval bij stewards/supporters niet verbergen. Selecteer een nieuw standaardmodel pas met een vastgelegde afweging.

**Klaar als:** de kandidaat aantoonbaar voordeel heeft voor het gekozen doel, regressies zichtbaar zijn en de keuze reproduceerbaar is. Een negatief experiment is een geldig onderzoeksresultaat, maar geen automatische vervanging van de baseline. **Bewijs:** hypothese, instellingen, logs, curves, scores, foutbeelden en gekozen checkpoint. **Reviewer:** persoon 3.

### P1-04 — Pak de bal als afzonderlijke data gap aan

Controleer objectgrootte op bronresolutie én na preprocessing. Bepaal of de dominante oorzaak detailverlies, onvoldoende variatie, labelproblemen of een ongeschikte uitsnede is. Voer alleen een nieuw experiment uit dat dit onderscheid onderzoekt. Vergelijk de pretrained `sports ball` semantisch correct met lokale `ball`, op dezelfde frames en invoerverwerking. De bestaande F001/F002 blijven negatieve referenties.

**Klaar als:** baseline en kandidaat eerlijk gemeten zijn, de gemaakte keuze uit de metingen volgt en de resterende missers verklaarbaar zijn. De bal hoeft geen team te krijgen en krijgt geen grondprojectie die niet is onderbouwd. **Reviewer:** persoon 2.

### P1-05 — Lever de modeloverdracht compleet aan

Lever werkelijke gewichten, SHA-256, echte klasse-ID's/namen, semantische mapping, model-ID, dataset-/codeversie, dependencies, invoerinstellingen en een echt uitvoervoorbeeld. Zet grote bestanden in de bestaande Git LFS-route en controleer downloaden vanuit een lege cache. Meld bron-, label-, split- en afbeeldingswijzigingen aan personen 2 en 3 via de gezamenlijke overdracht in de repository.

**Klaar als:** persoon 3 de detector kan laden en uitvoeren zonder losse handmatige aanpassingen of ontbrekende gewichten. **Reviewer:** persoon 3.

**Primaire bestanden:** `persoon1/role_training.py`, `persoon1/appearance_evaluation.py`, `scripts/build_role_extension.py`, `scripts/evaluate_role_extension.py`, `scripts/football48_ball_experiment.py`, `src/football_pipeline/detection.py`, `src/football_pipeline/appearance.py`; bijbehorende datasets, modelprofielen, trainingconfiguraties en modelrapporten.

## 4. Persoon 2 — veld herkennen en posities betrouwbaar maken

### P2-01 — Diagnoseer de falende automatische veldproef

Gebruik de bestaande echte 120-frameproef om per fase vast te stellen wat ontbreekt: herkenbare veldpunten, juiste semantische punt-ID's, betrouwbare lijnen, voldoende spreiding, geschikte camerahoek of geometrische consistentie. Kijk naast de voorspellingen naar het bronbeeld en maak handmatig gecontroleerde referenties. Verlaag drempels niet uitsluitend om meer frames als geldig te kunnen tellen.

Beoordeel tegelijk de bronkeuze. Een panorama met sterke lensvervorming kan ongeschikt zijn voor één homography zonder aanvullende correctie. Een nauwe uitsnede kan te weinig veldinformatie bevatten. Leg vast welk camerabereik werkelijk wordt ondersteund.

**Klaar als:** voor de belangrijkste afwijzingen concrete bronvoorbeelden en onderscheidende controles bestaan. **Bewijs:** veldfoutenregister en diagnosebeelden. **Reviewer:** persoon 1.

### P2-02 — Maak gecontroleerde veldreferenties en verbeter het veldmodel

- Annoteer bekende punten en relevante lijnen met de juiste semantische identiteit; verzin geen onzichtbare punten.
- Houd veldtrain-/validatie-/testgroepen gescheiden en stem ze af met persoon 1, zodat een gezamenlijke eindtest niet via veldtraining uitlekt.
- Gebruik de bestaande keypoint-/lijnmodellen als baseline. Pas, afhankelijk van de diagnose, bronselectie, preprocessing, instellingen of echte fine-tuning aan.
- Vergelijk op dezelfde handmatig gecontroleerde punten/lijnen. Rapporteer pixelafwijking, bruikbare veldframes en onterecht geaccepteerde kalibraties; een hoge geaccepteerde fractie alleen bewijst geen kwaliteit.

**Klaar als:** de veldroute op de gekozen vaste-camera-ontwikkelclip bruikbaar is, met gecontroleerde geometrie en verklaarde uitval. Brede cameraoverdracht blijft een afzonderlijke claim. **Reviewer:** persoon 1 voor labels en metingen, persoon 3 voor het uitvoercontract.

### P2-03 — Maak homography, veldgrens en foutafhandeling correct

Controleer bekende verspreide veldpunten en extra controlepunten die niet voor de fit zijn gebruikt. Verifieer richting, veldgrens en projectie op begin, midden en einde. Een lage fout op fitpunten alleen is onvoldoende. Als lenscorrectie of andere preprocessing wordt gebruikt, moet de keten naar oorspronkelijke beeldcoördinaten expliciet kloppen.

Lever een actuele veldstatus en projectie voor het juiste bronframe. Bij onvoldoende bewijs blijven positie en veldtelling onbekend. Gebruik geen kalibratie van een andere video, geen oude matrix na een cut en geen verzonnen veldpunten. Persoon 3 gebruikt deze status voor de toepassing; die bepaalt de geometrie niet opnieuw.

**Klaar als:** gecontroleerde voetpunten correct projecteren en ongeldige frames aantoonbaar worden afgewezen. **Bewijs:** kalibratiebundel, bronidentiteit, controlepunten, overlays en foutmaten. **Reviewer:** persoon 3.

### P2-04 — Onderzoek camerabeweging pas na de vaste-camera-acceptatie

Test kleine verschuiving, zoom, pan en cuts apart. Valideer wanneer een nieuwe kalibratie nodig is en wanneer state moet worden gereset. Stem met persoon 3 af of tracking in deze modus verantwoord kan worden vrijgegeven. Het aantonen van één werkende homography bewijst geen cameracompensatie.

**Klaar als:** de ondersteunde bewegingen en afwijzingen meetbaar beschreven zijn. Bij onvoldoende bewijs blijft de automatische cameramodus zonder speler-ID's. **Reviewer:** persoon 3.

### P2-05 — Lever veldruntime en veldcontract reproduceerbaar aan

Bewaar code-/gewichtshashes, dependencies, coördinatenstelsel, bronafmetingen, modelinstellingen, confidencebetekenis en afwijsredenen. Behoud de afgescheiden veldomgeving waar dependencies dat vereisen. Geef persoon 3 een geldige bundel, een ongeldige bundel en voorbeelden van veranderde camerabeelden.

**Klaar als:** persoon 3 exact dezelfde clip met de veldruntime kan uitvoeren en de geometrische status correct interpreteert. **Reviewer:** persoon 3.

**Primaire bestanden:** `src/football_pipeline/field_*.py`, `automatic_calibration.py`, `calibration_evaluation.py`, `calibration_input.py`, `geometry.py`, `point_picker.py`, `scripts/field_calibration_*.py`, `scripts/broadcast_field_experiment.py`, `scripts/run_field_training.py`, `scripts/setup_field_*.py`; bijbehorende veldconfiguraties, referenties en rapporten.

## 5. Persoon 3 — teams, tracking en de werkende toepassing

### P3-01 — Verbeter Team A/B zonder onterechte zekerheid

Maak samen met persoon 1 gecontroleerde teamreferenties op ontwikkelsequenties. Neem witte/donkere shirts, schaduw, overlap en doelmannen met afwijkende shirts op. Stel keeperteam vast op voldoende betrouwbare broninformatie; raad het niet uitsluitend uit de afwijkende kleur of één toevallige veldpositie.

Verbeter de bestaande kleur-/teamlogica met metingen van correcte, verkeerde én onbekende koppelingen. Controleer opwarmtijd, wisseling van A/B, late nieuwe observaties en reset bij een nieuwe bron. Beoordeel onterechte zekerheid bij een derde shirtkleur. Behoud onbekend als de relatie onvoldoende is onderbouwd. Een team mag niet bepalen dat iemand automatisch een speler is: eerst rolherkenning door het model van persoon 1.

**Klaar als:** de gekozen methode op meerdere ontwikkelsequenties onderbouwd beter is, met expliciete onbekenden en een gemelde terugval waar die voorkomt. **Reviewer:** persoon 1.

### P3-02 — Controleer de spelertelling als eindfunctie

De bestaande regel blijft: alleen een voorspelde `player`, inclusief doelman, met een bruikbaar actueel voetpunt binnen het veld telt mee. Scheidsrechter, lijnrechter, steward, supporter en generieke persoon tellen niet als speler. Zonder geldig veld is het aantal onbekend, niet nul.

Maak samen met de andere twee korte handmatig getelde ontwikkelsequenties. Controleer afzonderlijk:

1. Gemiste/dubbele personen of verkeerde rol: terug naar persoon 1.
2. Verkeerde veldgrens of voetpuntprojectie: terug naar persoon 2.
3. Onjuiste verwerking, drempel, dubbeltelling of teamsom: persoon 3.

Rapporteer telafwijking tegenover de zichtbare, gecontroleerde referentie per frame en oorzaak. Forceer geen maximum van 22 om fouten te verbergen; zichtbaarheid en echte spelsituatie bepalen de referentie. Team A + Team B + onbekend moet gelijk zijn aan het getelde aantal spelers op het veld.

**Klaar als:** telregels, foutgevallen en teamtotalen op echte voorbeelden gecontroleerd zijn. **Reviewers:** persoon 1 voor rollen; persoon 2 voor projectie.

### P3-03 — Voeg betrouwbare spelertracking toe na MVP-acceptatie

Gebruik de bestaande ByteTrack-route en de juiste detectieklassen. Laat persoon 1 identiteit over korte ontwikkelsequenties, occlusions, herintrede en zichtbare ID-wissels controleren; laat persoon 2 de camerageschiktheid toetsen. Meet ID-wissels en fragmentatie op deze referenties. Gebruik uitgebreidere trackingmetrics alleen als de benodigde volledige referenties beschikbaar zijn.

Controleer de betekenis van voorspelde tegenover werkelijk waargenomen posities. Een tijdelijk door de tracker voorspelde persoon mag niet onzichtbaar als nieuwe actuele waarneming worden geteld. Een cut of nieuwe bron mag geen identiteit uit een andere scène erven. Camerabewegingsmodus blijft apart geblokkeerd zolang die niet gevalideerd is; registreer menselijke MVP-acceptatie alleen wanneer die echt is gegeven.

**Klaar als:** tracking op de geaccepteerde vaste-camera-scope bruikbaar is en meetbare beperkingen heeft. **Reviewers:** persoon 1 en persoon 2.

### P3-04 — Integreer modellen, veld, teams, export en interface

Zorg voor één startopdracht en één bronmoment voor beeld, detecties en tactical map. Laad de overgedragen modellen met gewichtshash- en klassecontrole. Maak modelkeuze, onzekerheid, kalibratie-uitval en lege detecties begrijpelijk zichtbaar. Toon geen technische instellingen die een gewone gebruiker niet nodig heeft om de video te verwerken.

Controleer JSONL-export en replay, oorspronkelijke boxcoördinaten, rol-/teamherkomst, frame-index, presentatie-tijd en de gecachte code-/data-identiteit. Onderzoek foutieve uploads, onleesbare video, ontbrekende gewichten en onbeschikbare GPU met concrete foutmeldingen. Behoud bestaande werkende routes tijdens integratie.

**Klaar als:** de andere twee personen vanuit een eigen checkout de volledige toepassing kunnen starten en een clip kunnen verwerken. **Reviewers:** persoon 1 voor modeloverdracht en persoon 2 voor veldkoppeling.

### P3-05 — Meet op de echte RTX 4050 en beheer de gezamenlijke controle

Controleer eerst werkelijk GPU-type, VRAM, driver en CUDA-beschikbaarheid. Meet volledige verwerkingstijd, detectietijd, veldtijd, piekgeheugen en hergebruik apart. Gebruik dezelfde clips, invoerresolutie en uitvoerinstellingen bij een vergelijking. Een losse detector-FPS is geen totale verwerkingssnelheid. Bewaar dependencyversies en startcommando's, en controleer zowel een eerste run als hergebruik waar dat wordt geclaimd.

Optimaliseer pas het gemeten knelpunt en controleer daarna herkennings-/projectiekwaliteit opnieuw als resolutie, framesampling, model of preprocessing verandert. Sla geen bronframes over terwijl de uitvoer doet alsof ieder frame actueel is verwerkt.

**Klaar als:** een reproduceerbare 4050-meting bestaat en de volledige verwerking technisch slaagt. Er is nog geen willekeurige FPS-eis afgesproken. **Reviewers:** personen 1 en 2 op de invloed op hun onderdelen.

**Primaire bestanden:** `src/football_pipeline/teams.py`, `tracking.py`, `participants.py`, `pipeline.py`, `render.py`, `video.py`, `replay.py`, `contracts.py`, `cli.py`, `streamlit_app.py`, `scripts/evaluate_video_teams.py`, `scripts/verify_player_pipeline.py` en de gezamenlijke startscripts; bijbehorende team-/trackingreferenties, integratietests en benchmarkrapporten.

## 6. Afspraken waardoor jullie tegelijk kunnen werken

### Vast overdrachtscontract

| Overdracht | Eigenaar → gebruiker | Verplichte inhoud |
|---|---|---|
| Persoon/rol/ballvoorstel | P1 → P3; P2 gebruikt boxen waar nodig | Videohash, nulgebaseerde frame-index, presentatietijd in seconden, oorspronkelijke breedte/hoogte, pixelbox `x1,y1,x2,y2`, confidence, echte modelklasse, semantische rol en model/configuratie-identiteit |
| Veld/projectie | P2 → P3 | Dezelfde bronidentiteit en frame-index, coördinatenstelsel, actuele geldigheidsstatus, veldgrens/projectie, bronafmetingen en concrete afwijsreden |
| Team/track/telling | P3 → gezamenlijke uitvoer | A/B/onbekend, teammethode en scorebetekenis, eventuele track-ID, actuele/voorspelde herkomst, telstatus en uitsluitreden |
| Geen resultaat | Iedere eigenaar → P3 | Bestaand framerecord met lege detectielijst of expliciet onbekende veld-/teamstatus; geen ontbrekend frame of verzonnen nul |

Voer schaal/letterboxcorrectie uit vóór overdracht. Verander de betekenis van bestaande contractvelden niet stilzwijgend. Een modelrol is een voorspelling, geen bewezen menselijk label. Persoon 2 bepaalt geometrie; persoon 1 bepaalt detector-/rolbetekenis; persoon 3 past de afgesproken telregels toe.

### Bestanden en Git

- Gebruik drie eigen checkouts en omgevingen. Zo overschrijven de afzonderlijke PyTorch-/velddependencies elkaar niet.
- Iedereen haalt eerst de nieuwste `main` op en pusht kleine, afgeronde wijzigingen. Werk rechtstreeks op `main` zoals gevraagd; gebruik geen `/codex`-branches en geen force-push.
- Laat slechts één persoon tegelijk een gedeeld bestand wijzigen. P3 beheert `contracts.py`, `pipeline.py`, `participants.py`, startworkflow en UI; contractwijzigingen worden eerst kort afgestemd met P1 en P2. P1 beheert `configs/models*.json`; P2 beheert veldinstellingen. P3 vraagt een wijziging daar via de eigenaar aan.
- Meld vóór het pushen welke gedeelde bestanden en bron-/modelidentiteiten veranderen. Voeg een concrete runopdracht, relevante controles en bekende regressies toe.
- Houd bestaande datasets, gewichten en rapporten versieerbaar; overschrijf een eerder experiment of labelreview niet. Grote bestanden gebruiken de bestaande opslagafspraken en worden op echte downloadbaarheid gecontroleerd.

### Reviewrotatie

| Werk | Eerste reviewer |
|---|---|
| P1-rol-/detectielabels en modelselectie | P3 |
| P2-veldlabels en geometrische meting | P1 |
| P3-teamreferenties en teamlogica | P1 |
| P3-identiteitssequenties en trackeruitvoer | P1; P2 controleert camera/projectie |
| P1-modelcontract of P2-veldcontract | P3 |
| Gezamenlijke eindvideo en presentatie | Alle drie |

Reviews zijn werkelijke controles op bronbeelden, labels en uitvoer. Een geslaagde softwaretest, AI-review of commit is geen vervanging van menselijke review.

## 7. Werkvolgorde zonder elkaar te blokkeren

| Stap | Persoon 1 begint met | Persoon 2 begint met | Persoon 3 begint met |
|---|---|---|---|
| **1. Referentie vastzetten** | Data-/reviewoverzicht, huidige gewichten en complete detectiereferentie | Diagnose 0/120 veldframes en geschikte vaste-camera-bron | Huidige app uitvoeren; foutregister voor team, telling en integratie |
| **2. Onafhankelijk verbeteren** | Ontbrekende roldata, menselijke review en gericht detector-/rolexperiment; balonderzoek apart | Veldreferenties, punt-/lijnverbetering en geometrische controles | Team-/keeperreferenties en teamlogica; app-/telcontroles met huidige modellen |
| **3. Eerste overdracht** | Echt geladen kandidaatmodel plus uitvoervoorbeelden; ook huidige baseline blijft bruikbaar | Eén gecontroleerd geldig en ongeldig veldvoorbeeld plus bijbehorende bundel | Beide contracten koppelen; gezamenlijke ontwikkelvideo en foutmeldingen controleren |
| **4. Vast MVP beoordelen** | Label-/model-/foutbewijs uitleggen | Kalibratie en bronbeperkingen uitleggen | App, telling en 4050-meting demonstreren |
| **5. Uitbreiden en afronden** | Referentietracks en modelregressiecontrole | Camerabeweging onderzoeken als het vaste MVP geaccepteerd is | Tracking binnen de vrijgegeven scope; integratie, testuitvoering en eindpakket coördineren |

P3 kan vanaf stap 1 met bestaande detectoruitvoer en kalibratievoorbeelden ontwikkelen. P1 en P2 wachten niet op de definitieve UI. Nieuwe proeftraining wordt niet geblokkeerd door nog open menselijke review, mits de voorlopige status expliciet blijft en die run niet als definitief goedgekeurd wordt voorgesteld.

## 8. Eén gezamenlijke acceptatie en eindtest

### Functionele referentiegevallen

| Geval | Wat moet zichtbaar kloppen | Verantwoordelijke controle |
|---|---|---|
| Speler en doelman binnen geldig veld | Beide kunnen als speler tellen; geen automatisch gegokt keeperteam | P1 rol; P2 locatie; P3 telling/team |
| Steward op het veld | Als de rol correct steward is, geen spelerpunt/telling; rol mag zichtbaar blijven | P1 + P3 |
| Supporter of reserve buiten het veld | Geen onterechte veldspeler door alleen de persoonsbox | P1 + P2 + P3 |
| Centrale en assistent-scheidsrechter | Verschillende rollen waar ondersteund; geen spelers in de telling | P1 + P3 |
| Dubbele/gecombineerde box of occlusion | Geen ongemelde dubbeltelling; fout en herkomst controleerbaar | P1 + P3 |
| Leeg frame of onzekere rol/team | Geldig exportrecord; expliciet onbekend waar nodig | P3 |
| Slecht veld, cut of nieuwe video | Oude projectie/team-/trackstate niet onterecht hergebruiken | P2 + P3 |

Een referentiegeval slaagt pas op gecontroleerde uitvoer; het bestaan van de regel in code alleen is onvoldoende. Rolfouten en geometriefouten worden apart geregistreerd, zodat de juiste eigenaar de oorzaak aanpakt.

### Vrijgaveprocedure

1. Spreek vóór de laatste meting de ondersteunde bron/camera, modelversies, preprocessing, thresholds, primaire maten en gewenste afwegingen af. Verzin geen minimumscore achteraf.
2. Bevries de geïntegreerde configuratie. Voer alle relevante softwarechecks uit en laat de andere personen een verse checkout opzetten.
3. Gebruik alleen werkelijk gereserveerde, nog niet voor selectie gebruikte testgroepen voor de eindevaluatie. Als die ontbreken, selecteer eerst geschikte nieuwe ongeziene groepen. Noem een herhaalde ontwikkelmeting geen eindtest.
4. P1 levert detectie-/rol-/balmetingen en fouten; P2 veldmetingen en geometrische uitval; P3 team-/tracking-/telmetingen en volledige runtime. Presenteer conditionele cropscores en volledige pipelineprestaties afzonderlijk.
5. Bekijk samen echte succes- én foutgevallen. Bewaar de slechtere uitkomsten, bronidentiteiten en beperkingen.
6. Verandert iemand de oplossing na inzage in testfouten, registreer dat als nieuwe ontwikkelronde; diezelfde beelden zijn daarna geen onaangeroerde eindtest meer.

### Eindpakket per persoon

- **P1:** datasets en reviewbewijs; baseline-/kandidaatgewichten; klasse-/configuratie-/hashoverdracht; experimenten en detectie-/rol-/balfoutenanalyse.
- **P2:** veldreferenties; veldmodel/runtime; kalibratiebundels, controlepunten en geldigheidsbeleid; geometrie-/camerafoutenanalyse.
- **P3:** team-/trackingreferenties en resultaten; werkende UI, telling en export; installatie/start, 4050-benchmark, integratie-/softwarechecks en demonstratievideo.
- **Samen:** eisen-/bewijsregister, bron-/licentieoverzicht, versieoverzicht, menselijke reviews, betekenisvol AI-gebruik en een verdediging waarin alle drie de totale keten kunnen uitleggen.

## 9. Startdocumentatie en bestaande metingen

- [Laatste verbetering en concrete resterende fouten](Verbetering_Teams_en_Boxen.md).
- [Extra data, echte trainingen en negatieve balresultaten](Resultaten_Extra_Dataronde.md).
- [Gezamenlijke installatie en integratiegrenzen](Gezamenlijke_Integratie.md).
- [Historisch werkpakket persoon 1](01_Persoon_1_Data_Model_Evaluatie.md).
- [Bestaande telregels](Spelertelling_en_Rollen.md).
- [AI-gebruik en voorlopige reviewstatus](GenAI_Disclosure.md).

De nummers P1-01 tot en met P3-05 zijn taken voor de drie menselijke teamleden. Zij wijzen geen automatische agents toe en leveren geen fictieve goedkeuringen op.
