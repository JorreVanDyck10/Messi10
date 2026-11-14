# Sports Vision

Computer Vision Challenge 2026-2027

<b>Voetbalanalyse met objectdetectie, homography en een gesynchroniseerde tactical map</b>

Andrew, Milan, Raoul en Jorre
14 november 2026

![](figuren/resultaat.jpg)
Werkelijke uitvoer van het fragment van drie seconden. Links staan detecties, rechts de minimap.

Samenvatting

Ons project verwerkt een MP4 met voetbalbeelden en toont detecties naast een gesynchroniseerd bovenaanzicht van het veld. We combineren een bijgetrainde YOLO11s-spelersdetector met Andrews bijgetrainde YOLOv8x, waarvan de gezamenlijke app alleen de baluitvoer gebruikt. Handmatige kalibratie vormt de controleerbare basis. Tracking, teamgroepering, automatische veldherkenning en afstandsschattingen zijn uitbreidingen.

Het uploadpakket bevat de actuele code van main na de technische fixes, de originele Andrew-notebooks, een uitgevoerd overzichtsnotebook, modelgewichten, relevante trainingsdata en een echte demonstratie. De menselijke review van de 80-beeldenselectie is door het team bevestigd. De geregistreerde scores zijn ontwikkelmetingen; er is geen onafhankelijke projecteindtest of bewezen afstandsnauwkeurigheid.

Bronnen: Codeversie: main 524d081a; docs/Afronding_20261114.md; demonstratie/runmanifest.json.


# 1. Opdracht en oplossingsarchitectuur

De opdracht vraagt een samenhangende keten: gerichte annotaties, fine-tuning, kwantitatieve foutanalyse, perspectiefprojectie en een bruikbare lokale interface. Voor het MVP hoort daar een vaste camera zonder snelle camerawissels bij. Het dashboard maakt de keten zichtbaar, maar vervangt de beoordeling van data, experimenten en begrip niet.

Stap | Implementatie | Belangrijkste controle

Video inlezen | OpenCV en ffprobe | Afmetingen, hash, framerate en bronframes

Detecteren | YOLO11s en YOLOv8x | Klassemapping en gewichthashes

Projecteren | OpenCV-homography | Geldige veldpunten en kwaliteitsgrenzen

Volgen en groeperen | ByteTrack en shirtkenmerken | Tijdelijke ID en expliciete onbekendstatus

Weergeven | Streamlit en FFmpeg | Dezelfde tijdlijn voor beeld en minimap

Coherentie tussen onderdelen

Alle detecties bewaren oorspronkelijke beeldcoordinaten. We benaderen het grondcontactpunt van een speler met het midden onderaan de bounding box. De projectie hoort bij hetzelfde frame als de detectie. Een ontbrekende veldpositie wordt niet vervangen door een verzonnen punt of nul spelers.

De app gebruikt nu dezelfde football_pipeline-modules als de CLI en tests. De eerdere import via src.football_pipeline kon een tweede modulekopie laden en maakte interfacetests onbetrouwbaar. Deze fout is hersteld. De uploadstarter opent direct Nieuwe analyse en bindt de meegeleverde modellen aan de uitgepakte map.

Scope van de oplevering

De standaard uploadroute gebruikt de geselecteerde broadcastmodellen en CPU-instellingen. Een handmatige route blijft beschikbaar voor een statische camera. Historische alternatieve profielen zijn bewaard als documentatie; niet ieder oud experiment is een standaardkeuze. De gekozen gewichten staan met hun exacte identiteit in reports/submission/checkpoint_metadata.json.

Bronnen: Opdracht, pagina 2-3; src/football_pipeline/{video,detection,geometry,pipeline,tracking}.py; upload_tools.py.


# 2. Data, annotaties en teamreview

Dataset | Training | Validatie | Test | Gebruik

Reviewselectie | 48 | 32 | 0 | 80 gecontroleerde balbeelden

YOLO11s multisource | 3.936 | 348 | 0 | Spelersdetector

Andrew vier klassen | 612 | 38 | 13 | Bal, keeper, speler en referee

De reviewselectie en de historische trainingssets hebben verschillende doelen. De 80 reviewbeelden komen uit bestaande ontwikkeldata. De registratie van menselijke controle op 14 november verandert geen historische training en is geen nieuwe onafhankelijke test. De multisource-set bevat voetbalbeelden uit SoccerNet en aanvullende SportsMOT-trainclips; de oorspronkelijke validatiewedstrijden blijven apart.

Annotatieafspraken

We gebruiken een strakke box rond de zichtbare bal en beoordelen kleine kandidaten zowel vergroot als in het volledige beeld. Zichtbare bewegingswaas en gedeeltelijke bedekking vragen voorzichtigheid. We verzinnen geen locatie voor een volledig verborgen bal. Schoenen, lichte shirts en veldlijnen zijn geen ballen. De labeltaak ball kan ook zichtbare reserveballen omvatten; zij bepaalt niet welke bal de speelbal is.

Een onzeker beeld wordt niet automatisch een negatief trainingsvoorbeeld. Een negatief label vereist controle dat er werkelijk geen doelobject zichtbaar is. Uitsneden uit hetzelfde bronbeeld behouden dezelfde split. Training en validatie gebruiken gescheiden wedstrijdgroepen om vrijwel gelijke bronbeelden over splits te vermijden.

Hoe we verschillen oplosten

Volgens de expliciete bevestiging van het team hielden we twijfelgevallen buiten de definitieve selectie en stelden we de overige labels samen vast. Alle huidige 80 labels zijn akkoord. De labelbestanden zijn bij deze registratie niet gewijzigd. De oorspronkelijke annotator blijft Codex (AI), met providerlabels als voorstelbron. Er zijn geen individuele reviewersnamen of achteraf bedachte correcties ingevuld.

Deze bevestiging geldt uitsluitend voor de huidige 80 beelden. Andere historische datasets zijn daarmee niet automatisch menselijk goedgekeurd. De exacte status en herkomst staan in de meegeleverde datasetregistratie.

Bronnen: datasets/school-ball80-review-v1/{manifest.json,REVIEW.md}; data/broadcast-multisource-v1/manifest.json; artifacts/andrew-four-class-v1/provenance.json.


# 3. Gekozen spelersmodel: YOLO11s

Voor de huidige broadcastspelers kiezen we een YOLO11s-detector met een gespecialiseerde player-klasse. De meegeleverde gewichten hebben 9.428.179 parameters. De laatste trainingsfase bouwde voort op een eerder detectorcheckpoint. Het uiteindelijke checkpoint bewaart de trainingsinstellingen en validatiemetrics, zodat architectuur, datarol en cijfers controleerbaar blijven.

Instelling | Opgeslagen waarde

Architectuur / uitvoer | YOLO11s / player

Epochlimiet / trainingsinvoer | 40 / 1536 pixels

Batch / optimizer | 2 / AdamW

Learning rate / patience | 0,00005 / 8

Freeze / seed / horizontale spiegeling | 0 / 42 / 0,5

Resultaten uit de checkpointmetadata

Meting | Waarde

mAP@50 | 93,61%

mAP@50:95 | 60,28%

Precision / recall | 90,48% / 86,98%

Dit zijn frameworkmetrics van de eigen detectorvalidatie. Zij meten niet de volledige automatische pipeline met rollen, teams en veldprojectie. De operationele app gebruikt voor deze detector invoerformaat 1920 en een kandidaatconfidence van 0,10. De zichtbare spelersdrempel en trackingregels bepalen vervolgens welke detecties worden getoond en geteld.

Herhaalbaarheid

De oorspronkelijke orchestratielogica en volledige multisource-beelden en labels zijn meegeleverd. Het eerdere tussencheckpoint dat als initialisatie diende, is niet beschikbaar in de lokale bronnen. De nieuwe overzichtsnotebookroute begint daarom expliciet bij pretrained YOLO11s. Dat is een nieuwe training met dezelfde architectuur en data, geen bit-voor-bit reconstructie van de volledige historische reeks. Het geselecteerde eindcheckpoint blijft wel volledig controleerbaar.

Bronnen: reports/submission/checkpoint_metadata.json; src/football_pipeline/broadcast_refine.py; configs/models-broadcast.json.


# 4. Andrews model en baldetectie

Andrew trainde een pretrained YOLOv8x op een publieke voetbalset met vier klassen: ball, goalkeeper, player en referee. Het originele train.ipynb toont een voltooide training van 50 epochs op invoerformaat 1280 en validatie op 38 beelden. Het meegeleverde best.pt bevat dezelfde vier klassen en bevestigt YOLOv8x als basis. In de gezamenlijke app gebruiken we hieruit uitsluitend ball; de andere klassen vervangen ons YOLO11-spelersmodel niet.

Klasse | AP@50 | AP@50:95

Ball | 61,0% | 32,8%

Goalkeeper | 96,5% | 78,2%

Player | 99,3% | 83,7%

Referee | 97,3% | 72,2%

Gemiddeld, alle vier | 88,53% | 66,74%

De tabel komt uit de opgeslagen uitvoer van check_mAP.ipynb. De checkpointmetadata geeft voor de gemiddelde mAP@50:95 66,70%; de aparte evaluatierun geeft 66,74%. We houden die meetbronnen uit elkaar. De gemiddelde vierklassenscore is geen ballenscore en ook geen YOLO11-score. In deze validatie is de bal duidelijk de moeilijkste klasse.

Instellingen en beperkingen

De originele notebookcode vraagt batch 6, terwijl het aangeleverde checkpoint batch 1 registreert. Beide bronnen blijven ongewijzigd bewaard. Het nieuwe overzichtsnotebook gebruikt voor een expliciete herhaalrun batch 1. De historische training draaide volgens het notebook op een RTX 5070 Laptop GPU; de nieuwe lokale videotest draaide op CPU.

De gezamenlijke inferentie gebruikt een lage baldrempel van 0,03. Dat kan kleine ballen zichtbaar maken, maar verhoogt de kans op foutpositieven. De dataset en notebooks zijn meegeleverd, inclusief de 13 testbeelden. De getoonde mAP is een validatiescore, geen nieuwe score op deze testset. De bestaande publieke dataset vervangt de aparte eigen reviewbijdrage van 80 beelden niet.

Bronnen: Andrew_Prototype/train.ipynb en check_mAP.ipynb; artifacts/andrew-four-class-v1/{best.pt,provenance.json}; configs/models-broadcast.json.


# 5. Homography en veldprojectie

Een camera ziet het veld in perspectief. Een homography koppelt punten op het vlakke veld aan een bovenaanzicht. Vier geschikte, bekende puntparen bepalen de acht vrije verhoudingen van de matrix. OpenCV berekent de matrix met findHomography. Bij projectie delen we de eerste twee homogene componenten door de derde. De vlakke-veldaanname geldt voor grondcontactpunten, niet voor een bal hoog in de lucht.

Handmatige basisroute

De gebruiker klikt minstens vier bekende veldpunten aan, bijvoorbeeld de veldhoeken of hoeken van het strafschopgebied. Minstens twee andere bekende punten dienen als onafhankelijke controle. Vier gebruikte punten kunnen exact passen bij een verkeerde keuze; daarom zijn controlepunten noodzakelijk. De app bewaart puntvolgorde, bronhash en beeldafmetingen. De gekozen projectgrenzen zijn mediaan maximaal 0,5% en maximum 1% van de beelddiagonaal.

Automatische uitbreiding

PnLCalib herkent veldpunten en lijnen. De adapter controleert geometrie en kwaliteit voordat hij een matrix gebruikt. Een recent betrouwbaar anker mag onder gecontroleerde camerabeweging kort worden overbrugd. Ontbrekende of afgewezen kalibratie blijft zichtbaar als onbekend. De broncode, vastgelegde upstreamrevisie, GPL-2.0-licentie en releasegewichten zijn bijgevoegd.

![](figuren/resultaat2.jpg)
De automatische route combineert directe herkenning met gecontroleerde bewegingscompensatie.

Op de nieuwe clip zijn rechtstreeks 12 van 75 frames bruikbaar. Met de bestaande bewegingscompensatie beschikt de pipeline uiteindelijk op 73 van 75 frames over een projectie (97,3%). Dit is interne beschikbaarheid volgens de controles. Zonder onafhankelijke grondreferenties is het geen nauwkeurigheidspercentage.

Bronnen: src/football_pipeline/{geometry,automatic_calibration,field_motion}.py; scripts/field_calibration_worker.py; 04_Demonstratie/runmanifest.json.


# 6. Obstakels en foutanalyse

Observatie | Verklaring of hypothese | Aanpak en grens

Kleine bal verdwijnt | Verkleinen kan balboxen tot minder dan enkele pixels reduceren | Bronresolutie/crops en tegelproeven; rapporteer extra rekentijd

Schoen of veldlijn als bal | Lokaal uiterlijk lijkt op een klein helder object | Contextcontrole van labels en expliciete FP-voorbeelden

Team overal onbekend | Bij velduitval ontbreken geldige teamvoorbeelden | Eerst veldstatus onderzoeken; geen geforceerde teamnaam

Veldmodel faalt op panorama | Sterke vervorming en afwijkend camerabeeld passen slecht bij de geleerde geometrie | Geschiktere camerahoek of handmatige basisroute

Testmocks worden genegeerd | Dubbele module-import onder twee pakketnamen | Consistente imports; volledige testsuite opnieuw uitgevoerd

Een fout terugvoeren naar het juiste onderdeel

De eerste panoramademo leverde op alle 75 frames onvoldoende veldpunten. Teamkalibratie kreeg nul bruikbare voorbeelden en bleef insufficient_groups. Dat probleem zat dus niet alleen in shirtkleuren. Bij de nieuwe broadcastclip worden de teams wel beschikbaar. Deze diagnose toont waarom we detectie, projectie, tracking en teamindeling afzonderlijk inspecteren.

In de vroege balexperimenten leverde fine-tuning geen validatiewinst. Op 640 verdwenen alle 27 trainingsboxen uit de voorbewerking door de minimumgroottefilter. De grotere 1920-run behield de boxen, maar vond op de twaalf validatiebeelden nog geen ballen bij het werkpunt. Die negatieve uitkomst blijft bewaard; een lagere loss geldt niet automatisch als betere herkenning.

Latere tegelproeven behouden meer detail, maar kunnen ook reserveballen en achtergrondvoorstellen toevoegen. Daarom horen mAP, concrete FP/FN-gevallen, resolutie en de betekenis van de klasse ball samen in de beoordeling. Niet ieder onderzocht alternatief is in de huidige standaard opgenomen.

Bronnen: docs/Resultaten_Balexperimenten.md; docs/Verbetering_Baldetectie_Detailbehoud.md; docs/Afronding_20261114.md; lokale demoresultaten.


# 7. Extra uitbreidingen

Tracking en trajecten

ByteTrack koppelt detecties aan tijdelijke ID's en gebruikt ook lage-confidencekandidaten in een tweede associatiestap. De pipeline compenseert gemeten camerabeweging. Camerawissels of onbetrouwbare beweging kunnen een reset veroorzaken. Een ID is geen blijvende spelersidentiteit; ontbrekende waarnemingen onderbreken trajecten.

Teams en tellingen

De app vormt per video neutrale Team A/B-groepen op basis van shirtkenmerken, met bevestiging over opeenvolgende waarnemingen. Zij herkent geen clubnaam of thuis-/uitploeg. Onzekere gevallen blijven onbekend. Afwijkende keeperkleding en officials zijn bekende beperkingen. Een gebruiker kan teamcorrecties expliciet opslaan zonder het oorspronkelijke resultaat te overschrijven.

Afstandsschattingen

De app zet geldige veldposities met de ingestelde veldafmetingen om naar meters. Een kort mediaanfilter en een spronggrens beperken jitter. Gaten, ongeldige kalibratie en trackingresets onderbreken een segment. Meetdekking toont hoeveel tijd daadwerkelijk bruikbaar is. We extrapoleren niet naar een hele wedstrijd en claimen geen gevalideerde GPS-nauwkeurigheid.

Trainingsinterface en reproduceerbaarheid

De volledige bron bevat een trainingswerkbank, taakselectie, logs, hardwarecontrole en gescheiden kandidaatgewichten. Voor de onderwijsinzending staan de twee detectortrajecten overzichtelijk in de notebooks. De app bewaart modelhashes, instellingen en runtimegegevens per analyse. Opgeslagen analyses en downloads maken controle achteraf mogelijk.

Tracking en teamgroepering sluiten rechtstreeks aan bij de extra-creditvoorbeelden uit de opdracht. Automatische veldherkenning is een extra integratie van bestaand modelwerk. Eigen veldtraining is onderzocht, maar een afgewezen kandidaat wordt niet als bewezen verbetering gepresenteerd.

Bronnen: docs/Frontend_en_Afstanden.md; docs/Broadcast_Betrouwbaarheid_20261030.md; src/football_pipeline/{tracking,teams,distances}.py.


# 8. Resultaten en technische verificatie

Controle | Werkelijke uitkomst

Volledige hoofdsuite | 537 tests + 4 subtests geslaagd; 1 GPU-test overgeslagen

Lint en opmaak | Ruff check en format geslaagd

Functie-uitleg / codekaart | 784 functies zonder ontbrekende docstring; kaart actueel

Reviewselectie | 80/80 approved; 48 train en 32 val

Nieuwe demonstratie | 75 frames; volledige analyse voltooid

Beschikbare veldprojectie | 73/75 frames na bewegingscompensatie

Teamwaarnemingen | 1.626 toegewezen; 85 onbekend

De aantallen teamwaarnemingen tellen herhaalde observaties in opeenvolgende frames, niet verschillende spelers. Een toewijzing is een modelbeslissing en bewijst niet dat die beslissing inhoudelijk juist is. De demo duurde op de gebruikte CPU-omgeving ongeveer 1.047 seconden voor drie seconden video. Dit is geen realtime systeem.

Breder ontwikkelonderzoek

De vastgelegde bredere evaluatie van de automatische keten gebruikt 1.350 validatiebeelden en 19.874 spelerwaarnemingen. Zij rapporteert 93,46% spelerprecision, 82,46% spelerrecall en 78,50% correct gevonden en correct ingedeelde spelerwaarnemingen. Deze cijfers volgen andere meetregels dan de losse YOLO-checkpointmetrics. De wedstrijden zijn herhaald gebruikt voor ontwikkeling; de meting is geen onafhankelijke eindtest.

Wat de controles wel en niet aantonen

Softwaretests controleren onder meer synchronisatie, coordinaten, kalibratieafwijzing, retries, trackinggaten, teamcorrecties en export. De recente interfacetestfouten zijn opgelost in de gemergede main. De pakketcontrole controleert bestanden, labels en paden. Geen van beide bewijst algemene herkenningsnauwkeurigheid. De nieuwe uploadinstallatie is niet opnieuw op een volledig lege CUDA-laptop uitgevoerd.

Bronnen: reports/release-20261114/checks.json; docs/Broadcast_Betrouwbaarheid_20261030.md; 04_Demonstratie/runmanifest.json.


# 9. GenAI en eigenaarschap

Codex hielp bij broncode, annotatievoorstellen, datasetcuratie, technische controles, foutdiagnose, documentatie en het samenstellen van deze inzending. Ook dit verslag en de presentatie zijn met GenAI opgesteld en op formulering en samenhang nagekeken. De oorspronkelijke provider- en AI-herkomst van de labels blijft zichtbaar.

Menselijke controle

Het team bevestigde dat alle huidige 80 labels zijn gecontroleerd en akkoord bevonden. Twijfelgevallen vielen buiten deze selectie. Deze verklaring is geregistreerd als gebruikersbevestiging; de AI heeft geen menselijke bespreking nagebootst. De oorspronkelijke labels zijn bij de registratiestap niet veranderd. Andere datasets, trainingsruns en een mondelinge verdediging krijgen daarmee geen fictieve goedkeuring.

Voorbeelden van werkelijke instructies

Tijdens de technische afronding vroeg het team onder meer: "Test of de AN-Laptop-ver branch goed werkt", "Voer het uit met de nieuwe video" en "fix de dingen die jij kan doen nu". De review is verduidelijkt met "Twijfelgevallen uitgesloten; overige labels samen vastgelegd" en "Buiten de selectie; alle huidige 80 labels zijn akkoord". Deze korte citaten komen uit de werkelijke gesprekshistorie.

Kritische controle van AI-uitvoer

Niet alle voorstellen zijn aanvaard. Trainingsruns zonder validatiewinst blijven negatieve resultaten. Afgewezen veldvarianten zijn niet stilzwijgend standaard geworden. Een oorspronkelijke panoramakeuze bleek ongeschikt voor automatische kalibratie en is vervangen door een beter passend broadcastfragment. Een onjuiste gelijkstelling van Andrews model met YOLO11 is gecorrigeerd: zijn checkpoint is YOLOv8x.

De studenten blijven verantwoordelijk voor de inhoud en moeten de geselecteerde code en keuzes zelfstandig kunnen uitleggen. De presentatie is voorbereidingsmateriaal. Het pakket claimt niet dat de verdediging al heeft plaatsgevonden, dat alle externe gegevens eigen annotaties zijn of dat ontwikkelmetingen een onafhankelijke test vormen.

Bronnen: docs/GenAI_Disclosure.md; docs/ai_usage.md; datasets/school-ball80-review-v1/REVIEW.md; oorspronkelijke notebookmetadata.


# 10. Uitvoeren en training nakijken

De inzending staat in een GitHub-map met rapport, bewerkbare presentatie, code en demonstratie. Haal de volledige map en Git LFS-bestanden op zodat de relatieve paden behouden blijven. Installeer Python 3.11 en Git voor Windows. Voer vanuit 03_Code eerst Setup-Upload.ps1 en daarna Start-Upload.ps1 uit. De standaardroute gebruikt CPU. De gekozen gewichten, veldgewichten en originele PnLCalib-broncode zijn meegeleverd; Python-bibliotheken en FFmpeg worden bij de installatie gedownload.

Lokale paden

Een virtuele omgeving hoort niet in een uploadarchief. De installatie maakt daarom eigen app- en veldomgevingen aan. upload_tools.py bindt de originele hashregistratie aan de uitgepakte map. De app en het oudere PnLCalib-model houden afzonderlijke PyTorch-/NumPy-omgevingen. Dat voorkomt dat een wijziging aan de veldruntime de detectoromgeving overschrijft.

Notebookvolgorde

Training_en_Evaluatie.ipynb toont eerst de datasets, reviewstatus en echte checkpointmetadata. De standaard acht codecellen zijn tijdens het verpakken uitgevoerd zonder nieuwe training. De originele Andrew-notebooks blijven bewaard met historische outputs. Voor een nieuwe run zet de gebruiker RUN_TRAINING bewust aan; uitvoer gaat naar een nieuwe runmap.

De lokale YAML-bindingen vermijden historische C:/Messi10-paden. Het eerdere tussencheckpoint van de laatste YOLO11s-fase ontbreekt; de herhaalcel gebruikt daarom pretrained YOLO11s en noemt dit expliciet een nieuwe run. Het aangeleverde eindcheckpoint en Andrews originele training blijven controleerbaar. Exact dezelfde oude GPU-uitkomst is niet gegarandeerd.

Demonstratie en bronnen

De map 04_Demonstratie bevat de invoer van drie seconden en de werkelijk berekende samengestelde video. Die kan zonder installatie worden afgespeeld. De originele runmetadata bewaart historische absolute paden als meetbewijs; de nieuwe starters gebruiken deze paden niet. De meegeleverde upstreambron heeft haar originele GPL-2.0-licentie. Providerdata en Ultralytics behouden hun eigen bron- en licentievoorwaarden.

Bronnen: 00_LEESMIJ.md; 03_Code/START_HIER.md; Setup-Upload.ps1; Training_en_Evaluatie.ipynb; .tools/PnLCalib/LICENSE.


# 11. Eindbeschouwing en bronnen

De belangrijkste opbrengst is een controleerbare end-to-endketen. We kunnen van dezelfde bronframes detecties, tijdelijke tracks, teams en veldposities bewaren en een gesynchroniseerde video maken. De huidige demonstratie toont die samenhang. De diagnostiek maakt ook zichtbaar waarom een technisch geslaagde run inhoudelijk beperkingen kan hebben.

Onze belangrijkste lessen zijn dat invoerresolutie de herkenbaarheid van een bal kan bepalen, dat correcte veldgeometrie nodig is voor betrouwbare tactische afleiding en dat een hoge gemiddelde detectiescore fouten bij een moeilijke klasse kan verbergen. Datasetherkomst, splitkeuze en concrete foutvoorbeelden zijn daarom even belangrijk als het dashboard.

De volgende inhoudelijke stap is een systeemfreeze met onafhankelijke, niet voor ontwikkeling gebruikte beelden en menselijke referenties voor projectie, teams en tracking. Keeperteams, officials, camera-overgangen en afstandsschattingen blijven aandachtspunten. We claimen geen foutloze wedstrijdanalyse, 3D-balpositie of realtime werking.

Bronnen en controleerbare bijlagen

<b>[1]</b> Computer Vision Challenge 2026-2027, de aangeleverde opdracht.
<b>[2]</b> Projectrepository: https://github.com/JorreVanDyck10/Messi10, main 524d081a.
<b>[3]</b> Ultralytics YOLO en ByteTrack-adapter: originele frameworkpackages en projectcode.
<b>[4]</b> PnLCalib: https://github.com/mguti97/PnLCalib, revisie 8c87391d6f4ea40c5e4d65e61529916c7a49ce62.
<b>[5]</b> SoccerNet SN-GSR-2024 en SportsMOT: bron-ID's, splits en hashes in de meegeleverde multisource-manifesten.
<b>[6]</b> Andrews publieke datasetbron: github.com/aaditya29/DFL-Bundesliga-Data-Shootout-Analysis, training/football-players-detection-1.
<b>[7]</b> De oorspronkelijke projectdocumenten en meetbestanden staan onder 03_Code/docs en 03_Code/reports. De checkpointmetadata en originele notebooks koppelen iedere score aan het juiste model.

Wat deze inzending bewijst

De code, uitgevoerde trainingen en ontwikkelmetingen zijn aanwezig. De gebruiker bevestigt de menselijke review van de 80 geselecteerde beelden. Het pakket bevat daarnaast de broncode en hulpmiddelen om het systeem te draaien en nieuwe experimenten uit te voeren. De zelfstandige presentatie en de inhoudelijke verdediging blijven bij het team.

Bronnen: Bronverwijzingen horen bij de betreffende data en experimenten; resultaten worden niet tussen modelprofielen uitgewisseld.
