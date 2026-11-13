# Sports Vision studiegids voor de verdediging

Andrew, Milan, Raoul en Jorre

13 november 2026

Deze gids helpt ons uitleggen hoe ons voetbalproject werkt. We beginnen met de basis en bouwen op naar de uitbreidingen. Bij elk onderwerp verbinden we de theorie met onze bestanden, een voorbeeld en een mogelijke verdedigingsvraag. De antwoorden zijn om mee te oefenen. Ze zijn geen bewijs dat iedereen de code al begrijpt of zelf alle beschreven taken heeft uitgevoerd.

De hoofdzaak is dat we één frame kunnen volgen vanaf de video tot de minimap en dat we onze training en resultaten eerlijk kunnen toelichten. Begin met de MVP-hoofdstukken. Leer daarna de extra onderdelen die je tijdens de demonstratie gebruikt. Het aparte bestand Functieindex.md bevat de functies en methoden uit de lokale projectcode, met vindplaatsen en technische leesaanwijzingen.

De huidige repository heeft meerdere routes. Een algemene personendetector, een tweeklassen-spelerdetector en de uitgebreide rolpipeline zijn verschillende keuzes. Niet elke demonstratie gebruikt automatisch alle technieken uit deze gids. De configuratie van de gekozen run bepaalt welke uitleg erbij hoort.

## 1 De opdracht en onze afbakening

### Wat hoort bij de basis

De challenge vraagt een pretrained detector, een gerichte dataset van 40 tot 80 uitdagende frames, echte fine-tuning, evaluatie met mAP@50 en mAP@50:95 en concrete foutanalyse. Daarnaast moeten we minstens vier bekende punten op een vlak veld gebruiken om een homography te berekenen. Een lokale interface moet MP4 verwerken en detecties naast een gesynchroniseerde minimap tonen. De basis gaat uit van één vaste camerahoek.

Bij ons is de kleine voetbal een gerichte datakloof. Daarnaast zijn er aparte spelertrainingen. Een negatief balresultaat mogen we laten zien, mits we goed uitleggen wat getest is en waarom het niet beter werkte. Alleen een pretrained model uitvoeren is geen vervanging voor het trainingsdeel.

Tracking, teamkleuren en automatische keypoints zijn extra's. We hebben daarnaast extra rollen, het samenvoegen van detectoren, tiling en camerabeweging onderzocht. De opdracht noemt het zelf trainen van een keypointmodel als uitbreiding. Alleen de externe PnLCalib-gewichten gebruiken is niet hetzelfde.

### Wat we moeten kunnen verdedigen

De rubric weegt data en annotaties 25%, modellering en fine-tuning 35%, foutanalyse 20%, de gekoppelde pipeline en homography 10% en proces en GenAI 10%. Het meeste studiewerk hoort dus bij de data, training en fouten. Een mooi dashboard alleen is onvoldoende. Voor de hoogste categorie boven 85% noemt de rubric een succesvol verdedigde extra. Dat is geen garantie op een cijfer.

Oefenvraag: Waarom gebruiken jullie niet alleen het grootste beschikbare model?

Voorbeeldantwoord: Een groter model vraagt meer geheugen en rekentijd. Onze data en kleine objecten kunnen een grotere beperking zijn dan het aantal modelparameters. We willen een keuze onderbouwen met dezelfde evaluatie, in plaats van automatisch groter te kiezen.

Bronnen: CV_Challenge_2026_2027.pdf, pagina 2 tot en met 4; docs/Cursuscheck_En_Eenvoud.md.

## 2 De verschillende uitvoeringen

### Het profiel bepaalt de werking

configs/models.json gebruikt de algemene COCO-personendetector. Die voorspelt person en weet daarmee niet of iemand speler is. Het eenvoudige startscript scripts/Start-Cursus.ps1 kiest configs/models-players-base.json. Dat gebruikt alleen onze P004-detector met player en referee, plus handmatige kalibratie als eerste veldkeuze.

configs/models-players.json is uitgebreider. Het combineert P004 met algemene persoonsvoorstellen en de R007-rolclassifier. De naam players in een startoptie betekent hier dus niet dat alleen P004 geladen wordt. scripts/Start-Wedstrijd.ps1 start deze uitgebreide herkenning met automatische veldmodus. R009 en R010 zijn afzonderlijk te kiezen alternatieven.

| Route | Herkenning | Geometrie als eerste keuze |
| --- | --- | --- |
| Rechtstreeks de app starten | Algemene personen, tenzij FOOTBALL_MODELS anders instelt | Handmatig, tenzij de omgeving anders instelt |
| Start-Cursus.ps1 | Alleen P004 player en referee | Handmatig |
| Start-Spelermodel.ps1 met Recognition players | R007 met extra rolclassifier | Handmatig tenzij FieldMode anders is |
| Start-Wedstrijd.ps1 | R007 of expliciet R009/R010 | Automatisch |

### Waarom dit verschil belangrijk is

De historische speler-AP van P004 hoort niet automatisch bij een R007-video. Een profiel kan ook andere confidencegrenzen gebruiken. Noteer voor een verdediging daarom altijd het profiel, de gewichten en de gebruikte evaluatie. De eenvoudige starter verwijdert niets uit de app. Andere keuzes blijven in de interface beschikbaar.

Oefening: Open een modelmanifest en wijs gewichten, echte klassen, imgsz, confidence, iou en device aan. Leg uit welke onderdelen ontbreken als er geen appearance-blok is.

Bronnen: configs/models*.json; scripts/Start-Cursus.ps1; scripts/Start-Spelermodel.ps1; scripts/Start-Wedstrijd.ps1.

## 3 Het gegevenspad van één frame

### Eerst invoer en instellingen

De app controleert de video en leest afmetingen, framerate, frameaantal en bestandsidentiteit. Daarna kiezen we het modelprofiel en de kalibratie. In de automatische route kan een aparte worker de veldwaarnemingen voorbereiden. De pipeline mag niet zomaar een kalibratie van een ander videobestand gebruiken.

### Daarna verwerking per frame

process_video in pipeline.py leest een bronframe. De detector levert boxen in de oorspronkelijke beeldpixels. In het uitgebreide profiel worden voorstellen samengevoegd en krijgen persoonsuitsneden een aanvullende rol en eventueel een team. Daarna wordt elke geldige grondrol geprojecteerd naar het veld.

Pas na de projectie kan een player-waarneming voor spelertracking in aanmerking komen. De telling gebruikt de voorspelde rol, bruikbare veldpositie en weergaveregels. Het programma maakt een FrameRecord en tekent bronbeeld en minimap samen in één uitvoerframe. Ook schrijft het de gegevens naar JSONL.

### Een concreet voorbeeld

Stel dat een persoon een kader [100, 200, 140, 300] krijgt. Het geschatte voetpunt is (120, 300). Met de geldige homography wordt dat bijvoorbeeld een veldpunt (0,40, 0,70). Dit zijn verzonnen voorbeeldgetallen om de berekening uit te leggen, geen gemeten spelerpositie. Als de rol player is en de overige voorwaarden kloppen, kan de waarneming meetellen. Bij steward gebeurt dat niet.

Een slechte telling kan verschillende oorzaken hebben. De detector kan iemand missen, de rolclassifier kan een steward speler noemen, de voetpositie kan fout zijn of de kalibratie kan ontbreken. Zoek de fout dus per stap.

Bronnen: src/football_pipeline/pipeline.py, contracts.py en participants.py.

## 4 Python en de hulpmiddelen

### Welke taak heeft elke bibliotheek

Python stuurt de verwerking aan. NumPy rekent met arrays en matrices. OpenCV leest en bewerkt beelden, berekent geometrie en levert onder meer optical flow. PyTorch verzorgt tensorberekeningen en training. Torchvision levert MobileNetV3 en pretrained gewichten. Ultralytics levert de YOLO- en ByteTrack-implementatie. Streamlit maakt de lokale interface. FFmpeg en ffprobe schrijven respectievelijk controleren video.

JSON is geschikt voor gestructureerde gegevens, zoals een modelmanifest. JSONL bevat per regel één zelfstandig JSON-object, handig voor veel framerecords. YAML wordt onder meer gebruikt voor dataset- en trackerinstellingen. CSV bewaart trainingscurves in rijen en kolommen. Een .pt-bestand bewaart modelgewichten of een PyTorch-checkpoint; het is geen leesbaar trainingsverslag.

### Begrippen uit onze Python-code

Een functie voert één bewerking uit. Een class bundelt gegevens en bijbehorende methoden. Een dataclass zoals Detection geeft velden een vaste structuur. self verwijst naar de huidige instantie. Een property laat een berekende waarde lezen alsof het een veld is. Een generator kan gegevens frame voor frame leveren zonder alles tegelijk in het geheugen te zetten.

Een exception stopt een ongeldige verwerking met uitleg. Een contextmanager met with zorgt dat bestanden of locks ook bij fouten worden afgesloten. Path bouwt bestandspaden zonder overal zelf slashes te plakken. Een typehint zoals list[Detection] beschrijft wat verwacht wordt, maar vervangt geen runtimecontrole.

Oefenvraag: Waarom staat er vaak if __name__ == '__main__'?

Voorbeeldantwoord: Daarmee start een bestand zijn opdracht alleen wanneer het rechtstreeks als script of module wordt uitgevoerd. Bij importeren kunnen andere bestanden de functies gebruiken zonder meteen het hele programma te starten.

Bronnen: pyproject.toml; requirements*.txt; src/football_pipeline/contracts.py; persoon1/__main__.py.

## 5 Pixels tensors en coördinaten

### Een beeld als getallen

Een kleurenbeeld is een rooster met meestal drie kleurwaarden per pixel. OpenCV gebruikt vaak BGR-volgorde, terwijl veel neurale netwerken RGB verwachten. Verwissel je die volgorde, dan veranderen de kleuren die het netwerk ziet. Een NumPy-beeld heeft doorgaans vorm hoogte x breedte x kanalen. PyTorch gebruikt voor een beeld vaak kanalen x hoogte x breedte en zet daar een batchdimensie voor.

Een tensor is een array waarop PyTorch kan rekenen, onder meer op de GPU. float32 gebruikt meer geheugen dan float16. Integerpixels van 0 tot 255 worden voor netwerken vaak naar floats en een andere schaal omgezet. Permute verandert de volgorde van dimensies. Stack voegt een batchdimensie toe. Concatenate plakt features langs een bestaande dimensie aan elkaar.

### Boxformaten niet verwisselen

In de pipeline is een box vaak xyxy: links, boven, rechts, onder in bronpixels. YOLO-labelbestanden gebruiken doorgaans klasse, genormaliseerd middelpunt x/y, breedte en hoogte. Voor een beeld van 1000 x 500 en box [100, 50, 300, 150] zijn die waarden 0,20, 0,20, 0,20 en 0,20. Dit is een rekenvoorbeeld.

Bij een uitsnede veranderen de lokale coördinaten. Tiling moet de tile-offset weer toevoegen. Bij letterboxing moet het framework de voorspelling terugzetten naar bronpixels. De minimapprojectie gebruikt geen verkleinde schermcoördinaten, maar de oorspronkelijke beeldcoördinaten.

Oefenvraag: Waarom projecteren we niet rechtstreeks de box uit een klein schermvoorbeeld?

Voorbeeldantwoord: De kalibratiematrix hoort bij de bronafmetingen. Een schermvoorbeeld kan verkleind, ingezoomd of opgevuld zijn. Zonder correcte omzetting plaatsen we de speler verkeerd.

Bronnen: persoon1/core.py read_labels en label_pixels; appearance.py crop_tensor; detection.py UltralyticsDetector.detect.

## 6 Data labels en annotatiebeleid

### De datasets uit elkaar houden

PANORIS-bal bevat 47 geselecteerde beelden: 27 train, 12 validatie en 8 gereserveerd. Elk geselecteerd beeld bevat een zichtbaar lokaliseerbare bal. Deze versie heeft geen representatieve set bevestigde negatieve beelden. Football48 gebruikt 36 train en 12 validatiebeelden, met 26 en 10 balobjecten en twaalf negatieve beelden. Dit zijn andere invoerbeelden en een andere schaal.

TeamTrack-spelers bevat 60 panoramabeelden van 6500 x 1000, verdeeld als 36/12/12. Er zijn 1320 spelerboxen inclusief doelmannen en 120 boxen van de bekende officials. De uitgebreide rolset v2 bevat 92 beeldbestanden en 1528 ongeaugmenteerde persoonsuitsneden. Een persoonsuitsnede is niet hetzelfde als een onafhankelijk videoframe.

### Labels zijn afspraken

We volgen de zichtbare balgrens, inclusief zichtbare bewegingswaas. Bij volledige occlusie verzinnen we geen locatie. Een onbeslisbaar beeld wordt niet stilzwijgend een negatief. Een negatieve annotatie betekent dat de doelklasse volgens de afgesproken scope werkelijk afwezig is. Een lege modelvoorspelling bewijst dat niet.

De TeamTrack-bronboxen hebben hun eigen herkomst. Aanvullende rollen en correcties zijn met AI gemaakt en blijven als voorlopige AI-review geregistreerd. Verre officials zijn onvolledig gelabeld. Een echte maar ongelabelde official kan tijdens training achtergrond worden of tijdens evaluatie als foutpositief tellen.

Oefenvraag: Waarom is een mens die op het gras staat geen automatisch spelerlabel?

Voorbeeldantwoord: Locatie en rol zijn verschillende eigenschappen. Een steward of scheidsrechter kan ook op het veld staan. Als we die als speler labelen, leert het model een verkeerde grens tussen de klassen.

Bronnen: datasets/teamtrack-players-v2/README.md; datasets/panoris-ball-ai-v1/README.md; docs/Resultaten_Extra_Dataronde.md.

## 7 Train validatie test en datalekken

### Drie verschillende doelen

Trainingsdata wordt gebruikt om gewichten te veranderen. Validatie helpt bij het kiezen van instellingen, checkpoints en modelvarianten. De testset dient voor de beoordeling nadat die keuzes vastliggen. Zodra we op testfouten gaan bijsturen, gebruiken we die gegevens feitelijk ook als ontwikkeldata.

Bij video zijn naburige frames sterk gecorreleerd. Een willekeurige framesplit kan bijna dezelfde speleractie in training en validatie stoppen. Daarom houden we tijdgroepen en uitsneden uit hetzelfde bronbeeld samen. Toch blijven kleding, camera en achtergrond binnen één wedstrijd gelijk. Groepsscheiding maakt de test eerlijker, maar maakt één wedstrijd nog geen representatieve verzameling wedstrijden.

### De beperking in ons project

Later kwamen ontwikkelannotaties uit de gereserveerde TeamTrack-testclip binnen. De groep is daarom niet meer onaangeroerd. Ook het herhaald gebruiken van dezelfde validatiebeelden voor keuzes kan de uiteindelijke score te gunstig maken. Er is geen onafhankelijke projecteindtest afgerond die deze beperkingen wegneemt.

In core.py controleert validate_dataset onder meer bestanden, labels, frame-identiteiten en groepsgrenzen. require_approval verwacht echte menselijke review. require_experiment_data laat alleen onder expliciete voorwaarden een voorlopige AI-route toe. Die aparte route verandert AI-review niet in menselijke goedkeuring.

Oefening: Leg uit waarom 1000 crops uit tien beelden minder variatie kunnen bevatten dan 100 beelden uit verschillende wedstrijden. Noem daarna wat een nieuwe eindtest moet vastleggen: bron, groepen, labels, bevroren instellingen, gewichten en evaluatiemethode.

Bronnen: persoon1/core.py; reports/players-experiments/split-audit.json; docs/Resultaten_Spelermodel.md.

## 8 Neurale netwerken en CNNs

### Hoe een netwerk kenmerken leert

Een neuraal netwerk bestaat uit rekenstappen met instelbare gewichten. Tijdens training veranderen die gewichten om de fout op voorbeelden te verkleinen. Een activatiefunctie voegt niet-lineariteit toe. Zonder zulke niet-lineaire stappen zou een stapeling lineaire lagen veel minder verschillende verbanden kunnen voorstellen.

Een CNN gebruikt filters die op veel plaatsen van een beeld dezelfde berekening uitvoeren. Vroege kenmerken kunnen op randen of texturen reageren. Latere lagen combineren informatie over grotere stukken van het beeld. Die filters worden geleerd; we schrijven niet handmatig een filter voor elke voetballer.

Downsampling maakt featuremaps kleiner en bespaart rekenwerk. Daar staat detailverlies tegenover. Dit is relevant bij een bal die maar enkele pixels groot is. Een classifier geeft een klasse voor een uitsnede. Een detector moet daarnaast locaties en aantallen objecten voorspellen.

### Backbone neck en head

In de uitleg van YOLO gebruiken we backbone voor kenmerkextractie, neck voor het combineren van kenmerken op verschillende schalen en head voor box- en klassevoorspellingen. Dat zijn rollen binnen de architectuur. Onze code gebruikt de Ultralytics-implementatie en bouwt YOLO11 niet zelf van nul.

MobileNetV3 Small is een ander CNN dat we als compacte feature-extractor voor persoonscrops gebruiken. Die extra classifier heeft eigen gewichten, preprocessing en evaluatie. Een CNN-slide uit de les helpt het principe begrijpen, maar bewijst niet dat onze hele extra classifier vanzelf eenvoudig is.

Bronnen: les 2 dia 23 en 66; persoon1/modeling.py yolo; appearance.py backbone.

## 9 Transfer learning en YOLO

### Waarom een pretrained model

Een pretrained model heeft op veel beelden bruikbare kenmerken geleerd. Bij transfer learning hergebruiken we die kennis voor een nieuwe taak. Fine-tuning past gewichten aan op onze voetbalbeelden. Met weinig eigen data is dit praktischer dan een volledig willekeurig gestart netwerk.

Het pretrained COCO-model kent person en sports ball. De echte COCO-ID voor sports ball is 32. Onze ballenspecialist heeft lokaal ball als klasse 0. Het P004-model heeft player 0 en referee 1. Die verschillende nummeringen moeten expliciet gemapt worden. Een nummer heeft alleen betekenis binnen de juiste klassenlijst.

P003 houdt de eerste tien modules vast, P004 maakt alle modules trainbaar. Beide starten vanaf pretrained YOLO11n. Freeze voorkomt updates van bepaalde parameters; het zegt niet dat de rest van het netwerk niets leert. De n-variant is relatief klein en past bij een laptop, maar we claimen daarmee geen perfecte snelheid of nauwkeurigheid.

### Wat we zelf doen

modeling.py laadt YOLO, controleert klassemapping, bouwt een dataset voor training, start model.train en bewaart logs. De leerregels en interne YOLO-lagen komen uit de bibliotheek. Wij zijn verantwoordelijk voor data, configuratie, vergelijking en de correcte interpretatie van de uitvoer.

Oefenvraag: Waarom mag person niet gewoon player worden genoemd?

Voorbeeldantwoord: De person-score maakt geen onderscheid tussen spelers, publiek en officials. Een nieuwe naam op de uitvoer verandert niet wat het netwerk heeft geleerd. Daarom weigert onze manifestcontrole die onjuiste semantische mapping.

Bronnen: les 1 dia 4; configs/player-class-mapping.json; configs/models-players-base.json; detection.py load_model_manifest.

## 10 De trainingscyclus

### Van voorspelling naar gewichtsupdate

Een forward pass berekent voorspellingen uit de huidige gewichten. De loss vergelijkt die met de labels. Backpropagation berekent gradients: hoe gevoelig de loss is voor kleine veranderingen van de gewichten. De optimizer gebruikt die gradients voor de update. De juiste volgorde is dus voorspellen, loss berekenen, gradients berekenen en gewichten bijwerken.

Een batch is de groep voorbeelden die tegelijk verwerkt wordt. Een iteratie is een verwerkingsstap van zo'n batch; door gradientaccumulatie hoeft niet elke batch direct een optimizerupdate te geven. Een epoch is een doorgang door de trainingsdata. Shuffle verandert de volgorde, maar in de gebruikte rechthoekige YOLO-dataloader staat shuffle uit.

### Onze loss en optimizer

De YOLO-logs tonen box_loss voor lokalisatie, cls_loss voor klassen en dfl_loss voor het leren van boxgrenzen. DFL staat voor Distribution Focal Loss en ondersteunt een verdelingsvoorstelling van grensafstanden. We gebruiken de implementatie uit Ultralytics; we hebben die loss niet zelf ontworpen. Een lagere totale loss bewijst niet automatisch betere validatie-AP.

Adam gebruikt informatie uit gradients en hun historie om updates te bepalen. De learning rate bepaalt de schaal van die updates. Een te grote stap kan leren instabiel maken; een heel kleine stap kan leren vertragen. Een optimizer garandeert niet dat het model een perfecte of unieke oplossing vindt.

Oefenvraag: Wat gebeurt er als de loss.backward-stap ontbreekt in onze eigen roltrainingslus?

Voorbeeldantwoord: Dan worden geen nieuwe gradients uit die loss berekend. De optimizer kan niet de bedoelde update voor dat trainingsvoorbeeld uitvoeren. zero_grad wist eerder opgebouwde gradients, backward berekent nieuwe en step past gewichten aan.

Bronnen: les 2 dia 28-29, 37-40 en 48; persoon1/role_training.py train.

## 11 Onze trainingsinstellingen

### P003 en P004

Beide proeven gebruiken imgsz 1920, batch 4, maximaal 100 epochs, patience 20, Adam, lr0 0,001, lrf 0,01 en weight decay 0,0005. Warmup staat op drie epochs in de aangevraagde configuratie. De gebruikte software hanteert ook eigen minimale warmup-iteraties. Seed 42 en deterministic beperken toevallige verschillen. Ze garanderen geen identieke uitkomst op elke hardware.

P003 gebruikt freeze 10 en P004 freeze 0. P003 stopte na 73 epochs met een gekozen checkpoint van epoch 53. P004 stopte na 78 epochs met checkpoint 58. Binnen de run kiest het framework het checkpoint. Tussen die twee proeven is vooral speler-AP@50:95 gebruikt en daarna speler-AP@50.

### Geheugen en reproduceerbaarheid

AMP gebruikt mixed precision om onder meer geheugen te besparen. nbs=64 leidt bij batch 4 na warmup nominaal tot accumulatie over 16 minibatches. Er staan dus niet tegelijk 64 beelden in het GPU-geheugen. De code probeert bij een echte CUDA out-of-memory opnieuw met batch 2 en daarna 1, telkens vanaf verse pretrained gewichten. Andere fouten horen niet als geheugenprobleem verborgen te worden.

De historische trainingen draaiden op een RTX 3050 Laptop met 4 GB. De beoogde RTX 4050 is andere hardware. Maak van die historische trainingstijden geen nieuwe 4050- of volledige pipelinesnelheid.

Oefening: Open train-players-reference.json en train-players-unfrozen.json. Wijs freeze als gecontroleerd verschil aan. Leg uit dat hyperparameters vooraf gekozen instellingen zijn, terwijl modelparameters de tijdens training geleerde gewichten zijn.

Bronnen: configs/train-players-*.json; persoon1/modeling.py train; docs/Resultaten_Spelermodel.md.

## 12 Voorbewerking en kleine objecten

### Waarom resolutie zo belangrijk was

TeamTrack-beelden zijn 6500 pixels breed. Bij verkleinen naar 640 kan een kleine speler nog maar enkele pixels groot zijn. De voorbewerkingsaudit vond dat dan slechts 439 van 792 trainingsspelerboxen en 37 van 72 officialboxen behouden bleven. Op 1920 bleven alle boxen behouden.

De PANORIS-baltraining had een nog duidelijker probleem. Bij 640 verwijderde de gebruikte software alle 27 kleine trainingsboxen. Daardoor waren box-loss en DFL-loss nul, terwijl er wel een training liep. Een nulverlies betekende hier ontbrekende boxsupervisie, geen perfect model. Op 1920 bleven de boxen wel over.

### Padding en beeldverhouding

Letterboxing bewaart de beeldverhouding en voegt ruimte toe om een modelcompatibele vorm te krijgen. Rechthoekige batches kunnen padding beperken. De feitelijke tensor hoeft daarom niet letterlijk 1920 x 1920 te zijn. Een grotere invoer bewaart meer broninformatie maar verzint geen ontbrekende details.

In het tweede balexperiment veranderden zowel resolutie als batch/paddinggedrag. Daarom mogen we niet concluderen dat uitsluitend resolutie het verschil veroorzaakt. Voor een zuivere vergelijking moet je zoveel mogelijk hetzelfde houden en resterende verschillen vermelden.

Oefenvraag: Waarom kan één pixel verschil een balmeting sterk beïnvloeden?

Voorbeeldantwoord: Bij een box van enkele pixels neemt één extra randpixel een groot deel van de oppervlakte in. De relatieve overlap daalt daardoor veel sterker dan bij een groot persoonkader.

Bronnen: persoon1/preprocessing_audit.py; reports/players-experiments/preprocessing-audit.json; docs/Resultaten_Balexperimenten.md.

## 13 Overfitting en regularisatie

### Wat overfitting betekent

Een model kan trainingsbeelden goed leren zonder nieuwe situaties goed te begrijpen. Dat is overfitting. We letten daarom op aparte validatieresultaten. Een lage trainingsloss met slechte validatie is een waarschuwing, maar bewijst niet op zichzelf welke oorzaak verantwoordelijk is. Ook onjuiste labels, een andere cameraverdeling of preprocessing kunnen een rol spelen.

Early stopping stopt als de gekozen validatiemaat niet meer voldoende verbetert volgens het gebruikte framework. Patience 20 betekent niet dat een model altijd na twintig epochs stopt. De historische balruns met nulfitness liepen bijvoorbeeld door door het gedrag van de vastgezette frameworkversie.

Weight decay remt grote gewichten en is verwant aan L2-regularisatie; de precieze update hangt af van de optimizer. Dropout laat tijdens training willekeurig activaties weg, maar onze P004-configuratie is niet een bewijs dat wij zelf een nieuwe dropoutstrategie hebben toegevoegd. Batch normalization past activaties aan met statistieken en heeft verschillend train- en evaluatiegedrag.

### Onze augmentatiekeuzes

Horizontaal spiegelen staat bij de YOLO-proeven op kans 0,5. Andere expliciet ingestelde vervormingen staan uit. Een augmentatie moet realistisch blijven en het label correct mee aanpassen. Bij heel kleine objecten kan sterk verkleinen extra schade geven. Bij teamkleuren kunnen willekeurige kleurveranderingen de betekenis veranderen.

De roltraining heeft een eigen cropaugmentatieroute met spiegelen en lager detail. Die mag je niet verwarren met de YOLO-augmentatieconfiguratie. Nieuwe voorbeelden en augmentaties uit dezelfde bron blijven in dezelfde train/val-groep.

Bronnen: les 2 dia 30 en 55-64; configs/train-players-unfrozen.json; persoon1/role_training.py.

## 14 Confidence NMS en dubbele boxen

### Drie soorten drempels

Confidence is een modelscore om kandidaten te filteren. Het is zonder kalibratie geen bewezen kans dat de voorspelling correct is. NMS-IoU gebruikt overlap om dubbele voorspellingen te onderdrukken. Matching-IoU bepaalt tijdens evaluatie of een voorspelling voldoende bij een referentiebox past. De drie rollen zijn verschillend, ook als er toevallig vergelijkbare getallen staan.

In de historische P004-AP-meting gebruiken we een confidencevloer van 0,001, NMS-IoU 0,70 en voor het werkpunt confidence 0,25 met match-IoU 0,50. De uitgebreide rolmetingen bewaren voorstellen vanaf 0,10. Voor tracking moet een lage kandidaatgrens behouden blijven, zodat de tweede ByteTrack-matchingsstap kan werken.

### Onze aanvullende samenvoeging

Een gespecialiseerde detector kan het bovenlichaam vinden en een algemene detector de volledige persoon. Hun IoU kan laag zijn ondanks dat het dezelfde persoon is. merge_person_proposals controleert daarom naast overlap ook insluiting, uitlijning en modelbron. Waar passend krijgt de volledige box de voorkeur. Een gewone overlap tussen twee echte spelers mag niet zomaar worden samengevoegd.

Op de gebruikte validatiebeelden verwijderde de latere aanpassing vijf foutieve spelerobservaties zonder correcte spelerwaarnemingen te verliezen. Dat maakt nog geen nieuwe onafhankelijke wedstrijdmeting. Een heuristiek is een praktische beslisregel met voorwaarden, geen natuurwet.

Oefenvraag: Kan NMS een echte speler verwijderen?

Voorbeeldantwoord: Ja, als twee echte spelers sterk overlappen en de regels hun voorstellen als duplicaat behandelen. Daarom onderzoeken we overlapgevallen en kiezen we drempels op basis van gecontroleerde voorbeelden.

Bronnen: detection.py merge_person_proposals en UltralyticsDetector.detect; docs/Verbetering_Teams_en_Boxen.md.

## 15 IoU precision recall en F1

### Rekenvoorbeeld

IoU is overlapoppervlakte gedeeld door de oppervlakte van de vereniging van twee boxen. Voor twee boxen met elk oppervlakte 100 en overlap 60 is de vereniging 140 en de IoU 60/140 = 0,429. Bij een matchgrens van 0,50 is dat geen geldige match. Dit is een didactisch voorbeeld.

Bij evaluatie moeten de klasse en de overlap kloppen. Eén referentiebox kan maximaal één voorspelling matchen. Een tweede voorspelling rond dezelfde speler kan dus FP worden. Een slecht passende voorspelling kan tegelijk een FP opleveren en de echte speler als FN achterlaten.

Precision = TP/(TP+FP). Recall = TP/(TP+FN). F1 = 2 x precision x recall / (precision+recall). Precision vraagt hoeveel voorspellingen juist zijn. Recall vraagt hoeveel gelabelde objecten gevonden zijn. Macro-F1 middelt de F1-score per klasse, zodat grote klassen niet automatisch alles domineren.

P004 heeft op het historische werkpunt voor spelers 199 TP, 65 FP en 65 FN. Precision en recall zijn daar beide 199/264 = 75,38%. Gewone accuracy is voor objectdetectie minder bruikbaar: er is geen natuurlijke lijst van alle mogelijke negatieve achtergrondboxen.

### Verwarringsmatrix

Een confusion matrix laat zien welke echte klasse als welke andere klasse wordt voorspeld. Onze rolclassificatie kan ook een unknown-kolom hebben. Veel correcte spelers kunnen anders de zwakke resultaten op zeldzame supporters verbergen. Een overzicht van de klassen is informatiever dan alleen één gemiddelde.

Bronnen: persoon1/metrics.py iou en match_class; persoon1/role_training.py scores; les 1 dia 52.

## 16 AP mAP en onze eigen evaluator

### Een curve in plaats van één grens

Wanneer we de confidencegrens veranderen, verandert de verhouding tussen gevonden en foutieve objecten. Een precision-recallcurve toont dat over meerdere grenzen. AP vat de curve van één klasse samen. Onze ap101-functie neemt op 101 recallniveaus de beste beschikbare precision vanaf dat recallniveau en middelt die waarden.

AP@50 gebruikt IoU 0,50. AP@50:95 middelt over tien IoU-grenzen van 0,50 tot 0,95. mAP middelt daarna over beoordeelde klassen. Speler-AP is dus niet hetzelfde als mAP over speler en scheidsrechter. Geen van deze maten betekent het percentage volledig juiste videoframes.

### Hoe onze code rekent

match_class sorteert voorspellingen op dalende confidence en matcht per klasse en frame met een nog ongebruikte referentie. evaluate controleert de invoer, berekent de AP-reeksen en maakt afzonderlijk TP/FP/FN op het werkpunt. Ook lege voorspelframes moeten in de invoer staan. Anders verdwijnen moeilijke beelden uit de evaluatie.

De eigen evaluator heeft geen volledige crowd/ignore-afhandeling of alle onderdelen van de officiële COCO-benchmark. Binnen onze gelijk uitgevoerde vergelijkingen is hij bruikbaar. Een frameworkscore en deze eigen projectscore kunnen afwijken. Je mag niet de beste score uit verschillende meetmethodes kiezen alsof alles gelijk is.

Oefenvraag: Is een model met vier gevonden ballen altijd beter dan een model met drie?

Voorbeeldantwoord: Niet automatisch. Dat hangt af van de confidencegrens, foutpositieven en boxkwaliteit. In Football48 had F002 op het werkpunt een extra TP, terwijl de AP over de hele curve juist slechter was.

Bronnen: persoon1/metrics.py; reports/players-experiments/EXP-P004/validation-metrics/metrics.json.

## 17 Onze echte resultaten

### Spelers en scheidsrechters

| Historische P004 vergelijking | Speler AP@50 | Speler AP@50 tot 95 | Speler TP FP FN |
| --- | --- | --- | --- |
| P003 freeze 10 | 68,62% | 24,90% | 191 / 88 / 73 |
| P004 freeze 0 | 74,50% | 26,55% | 199 / 65 / 65 |

Die vergelijking gebruikt twaalf validatiebeelden met 264 spelers. P004 wint op spelers, maar official-recall daalt van 50,00% naar 41,67%. De P004-mAP over beide klassen is 62,16% en 31,41%. Onvolledige officiallabels beperken de betekenis van dat gemiddelde.

Na de latere boxsamenvoeging heeft R007 speler-AP 75,96% en 26,26%, met 197 TP, 48 FP en 67 FN. R009 haalt 77,07% en 26,85%, met 197 TP, 46 FP en 67 FN. Deze uitgebreide meting gebruikt proposals vanaf 0,10 en is niet rechtstreeks dezelfde opzet als de historische P004-meting. Van de 197 gematchte spelers hebben er in die bekende wedstrijdmeting 192 het juiste team.

### De bal en het veld

| Football48 op dezelfde validatieset | AP@50 | AP@50 tot 95 | TP FP FN |
| --- | --- | --- | --- |
| Pretrained YOLO11n | 67,82% | 34,23% | 3 / 0 / 7 |
| F001 | 60,40% | 28,57% | 3 / 0 / 7 |
| F002 | 43,07% | 24,36% | 4 / 0 / 6 |

Beide nieuwe ballentrainingen verliezen van de baseline. Op de andere PANORIS-selectie bleven de validatie-AP's nul. Die twee datasets en schalen mogen niet als één voor/na-verbetering worden voorgesteld.

Het Broadcast-veldexperiment gaf 252 van 1239 intern bruikbare kalibraties, 20,3%. Dat is interne dekking en geen onafhankelijke menselijke nauwkeurigheid. De Commons-ontwikkelpilot had 0/120 betrouwbare veldframes. Een technisch voltooide run kan dus toch nauwelijks bruikbare veldposities hebben.

Bronnen: docs/Resultaten_Spelermodel.md; docs/Resultaten_Extra_Dataronde.md; docs/Verbetering_Teams_en_Boxen.md; docs/Broadcast_Veldexperiment.md.

## 18 Foutanalyse met echte oorzaken

### Waarneming en verklaring uit elkaar houden

Een waarneming is wat we kunnen aantonen: bijvoorbeeld een speler ontbreekt bij confidence 0,25. Een hypothese is een mogelijke verklaring: de speler is te klein, de klasse is verkeerd of NMS verwijderde een voorstel. Zonder verdere controle weten we niet welke verklaring klopt. Schrijf een vermoeden dus niet als bewezen oorzaak op.

Bij ons zijn er kleine gemiste spelers, grote gemiste spelers en boxen die twee personen omvatten. Kleine objecten verklaren daardoor niet alles. Controleer de bronpixels, kandidaatboxen, klassescores, gekozen confidence en IoU. Bij een minimapfout controleer je ook het voetpunt en de kalibratie.

Een bruikbaar foutenrecord bewaart bronvideo, frame, referentiebox, voorspelling, foutsoort, hypothese en vervolgstap. reviewed-error-examples.json en de bijbehorende afbeeldingen maken de historische spelerfouten controleerbaar. De foutoorzaak moet niet automatisch door het programma worden ingevuld als er geen bewijs is.

### Een vervolgeperiment ontwerpen

Wil je weten of een hogere resolutie helpt, vergelijk dan dezelfde beelden, gewichten, evaluator en drempels met een andere resolutie. Wil je een ander checkpoint beoordelen, houd de inferentie-instellingen juist gelijk. Noteer ook extra rekentijd en foutpositieven. Een verbeterde score op dezelfde ontwikkelbeelden is nog geen nieuwe onafhankelijke eindtest.

Oefenvraag: Waarom veranderden jullie de validatielabels niet zodat de voorspelde box beter paste?

Voorbeeldantwoord: De labels horen de afgesproken werkelijkheid te beschrijven. Ze aanpassen aan de voorspelling zou de vergelijking vertekenen. Een echte labelfout mag worden gecorrigeerd, maar dan moeten alle vergeleken modellen opnieuw op dezelfde gecorrigeerde set worden gemeten.

Bronnen: persoon1/error_review.py; reports/players-experiments/reviewed-error-examples.json; reports/ball-experiments/error-analysis.json.

## 19 De extra MobileNet rolclassifier

### Een tweede herkenningsvraag

YOLO vraagt waar objecten zitten en welke detectieklasse erbij hoort. De aanvullende classifier vraagt welke rol een al gevonden persoonsuitsnede heeft. De zes uitvoerrollen zijn player, referee, assistant_referee, steward, spectator en person. Een classifier kan een persoon die nooit als voorstel gevonden is niet alsnog terugvinden.

crop_tensor neemt een persoonsbox met wat extra marge, maakt een RGB-uitsnede van 128 bij 192 en zet die om naar een PyTorch-tensor. De pixelwaarden en kanalen worden genormaliseerd volgens de gebruikte ImageNet-preprocessing. Dit is een andere normalisatie dan die van de later samengestelde featurevector.

backbone gebruikt MobileNetV3 Small zonder de oorspronkelijke ImageNet-classificatiekop. Er blijven 576 beeldkenmerken over. jersey_feature voegt 32 kleurkenmerken toe. Samen vormen die een vector van 608 waarden. Een lineaire rolkop geeft zes scores en een aparte teamkop twee scores.

### Een score mag onbekend blijven

Softmax zet de uitvoerscores om naar een verdeling met som 1. Argmax kiest de grootste. Bij rolconfidence onder 0,65 valt de voorspelling terug op person. Dat voorkomt een deel van de geforceerde keuzes, maar softmaxconfidence is nog geen gekalibreerde zekerheid.

In classify worden de oorspronkelijke detectorrol en de classifiermetadata bewaard. De uiteindelijke semantic_class kan dus verschillen van de eerste YOLO-klasse. Bij debuggen moet je beide bekijken. Inference gebruikt eval en inference_mode. Daardoor trainen de gewichten niet tijdens het bekijken van een video.

Oefenvraag: Waarom is 58/59 correcte rollen geen detectierecall van 98% op de hele video?

Voorbeeldantwoord: Die proef kreeg geselecteerde persoonscrops als invoer. De detector moest ze niet eerst vinden. Gemiste voorstellen, achtergrondpersonen en andere videomomenten worden met dat ene cropcijfer niet beoordeeld.

Bronnen: appearance.py crop_tensor, jersey_feature, backbone en AppearanceClassifier.classify; docs/Resultaten_Extra_Dataronde.md.

## 20 De eigen training van de rollen

### Meer stappen dan de YOLO starter

role_training.py bouwt of leest een eigen manifest met crops, rollen, teams en groepen. De controle weigert gewijzigde bronbeelden en ongeoorloofde train/val-overlap. De features worden eerst uit de beelden gehaald. Het gemiddelde en de standaardafwijking worden op trainingsdata berekend. Bij warm-startfine-tuning worden de bij het eerdere model horende normalisatiewaarden behouden.

Voor de uitgebreide roltraining worden de laatste featureblokken geselecteerd als trainbaar. R009 gebruikt drie laatste blokken; R010 houdt de backbone vast. De batchnorm-statistieken blijven in evaluatiestand. Dat is niet hetzelfde als alle gradients uitzetten: parameters met requires_grad kunnen ook bij encoder.eval nog worden geleerd.

### Waarom er 576 en maal 8 staat

De eerste 576 features komen uit MobileNet. De laatste 32 zijn HSV-histogramkenmerken. Voor de rolkop worden de genormaliseerde kleurfeatures met 8 vermenigvuldigd. Dat is een specifieke projectkeuze om hun invloed te vergroten, geen algemene regel uit de cursus. De teamkop krijgt niet automatisch diezelfde rolweging. Je moet deze keuze als experimentele instelling benoemen.

De fine-tuning gebruikt cross-entropy, twintig epochs en tien gebalanceerde updates per epoch. Het samplingmechanisme neemt voorbeelden per rol, zodat de grootste klasse niet elke batch domineert. Daarna worden aparte lineaire koppen opnieuw aangepast, tot maximaal 400 epochs, met validatiecontroles om de vijf epochs. Die koptraining heeft dus een andere trainingsduur dan de CNN-fine-tuning.

### Onbalans en keuze van het model

De koptraining gebruikt inverse klassefrequenties als gewichten in cross-entropy. Dit geeft zeldzame klassen meer invloed, maar schept geen ontbrekende visuele variatie. Macro-F1 op validatie helpt de rolkop selecteren. R009 verbeterde de toegevoegde speler-/officialcrops maar verzwakte enkele zeldzame rollen. Daarom is het niet stilzwijgend overal de standaard geworden.

Bronnen: persoon1/role_training.py train, load_training_manifest en scores; configs/models-roles-r009.json; docs/Resultaten_Extra_Dataronde.md.

## 21 HSV en teamkleurclustering

### Kleur als handmatig ontworpen kenmerk

HSV verdeelt kleur in hue, saturation en value. Hue is kleurtoon, saturation verzadiging en value helderheid. Bij OpenCV heeft hue voor 8-bitbeelden een ander bereik dan een gewone gradenmaat. Onze code gebruikt daarom histogramranges die bij OpenCV passen.

kit_feature neemt vooral het centrale bovenlichaam. Zo tellen benen en gras minder mee. Het maakt zestien huevakken, acht verzadigingsvakken en acht helderheidsvakken. Hue krijgt een gewicht op basis van verzadiging, zodat bijna grijze pixels niet een toevallige kleurtoon laten domineren. De helderheidsbijdrage krijgt factor 0,6. Dit zijn handmatig ontworpen features, naast de door de CNN geleerde features van de andere route.

### Groepen zonder clubnamen

Voor onbekende video's verzamelt VideoTeams eerst voldoende zekere player-observaties. Het wacht op minstens 24 samples en drie updates en verfijnt met maximaal 200 verzamelde samples. De eigen twee-clusterprocedure zoekt twee kleurcentra met verschillende starts. De A/B-namen worden bij het verfijnen uitgelijnd, zodat een omgewisselde clustervolgorde niet zomaar de teamnamen omdraait.

Verdere regels kijken of de groepen voldoende groot en verschillend zijn. Afstandsgrenzen en een marge bepalen of een speler een team krijgt. team_confidence is hier een kleurafstandsmarge en geen softmaxkans. Bij twijfel blijft het team onbekend.

Voor bekende video-identiteiten kan de getrainde teamkop worden gebruikt. De match op videohash gaat over de toegelaten teamsupervisie, niet over geometrie. Het maakt een kalibratie van een andere clip niet geldig.

Oefenvraag: Waarom is een keeper lastig voor twee shirtclusters?

Voorbeeldantwoord: De keeper draagt vaak een derde kleur. Kleur alleen toont dan niet tot welk veldspelerteam hij behoort. Extra informatie zou nodig zijn en moet afzonderlijk worden gecontroleerd.

Bronnen: teams.py kit_feature en VideoTeams.update; appearance.py AppearanceClassifier.classify; docs/Verbetering_Teams_en_Boxen.md.

## 22 Homography stap voor stap

### Een vlak verbinden met een ander vlak

Perspectief maakt dat afstanden in camerabeeld en bovenaanzicht niet overal dezelfde schaal hebben. Een homography is een 3 bij 3 matrix die punten tussen twee vlakke projectieve afbeeldingen verbindt. Ze heeft, afgezien van schaal, acht vrijheidsgraden. Daarom zijn minstens vier geschikte puntparen nodig. De punten mogen geen onbruikbare of vrijwel rechte-lijnconfiguratie vormen.

Voor beeldpunt (x,y) rekenen we H maal (x,y,1). Dat geeft drie waarden (a,b,c). De veldpositie is (a/c,b/c), zolang c niet nul of bijna nul is. Alleen de eerste twee waarden nemen zou de perspectiefdeling missen. In de code wordt onder meer de eindigheid gecontroleerd.

Onze veldcoördinaten zijn genormaliseerd. (0,0) en (1,1) liggen bij tegenoverliggende hoeken van de gekozen veldoriëntatie. Een waarde 0,5 betekent het midden langs die as. Het modelveld van 105 bij 68 is een aanname; daarmee is niet bewezen dat een bronveld exact zo groot is of dat we nauwkeurige meters per seconde meten.

### Handmatig kalibreren

create_calibration past de matrix met OpenCV aan op de fitpunten. Twee extra middenlijnpunten dienen als onafhankelijke controles van die puntkeuze. De app controleert een mediaanfout van maximaal 0,5% van de beelddiagonaal en een maximum van 1%. Dat zijn projectgrenzen, geen universele garanties voor voetbalbeelden.

Calibration.validate_for controleert video-identiteit en afmetingen en rekent de matrix en fouten opnieuw uit. Het vertrouwt dus niet blind op een geladen JSON met approved=true. Een nieuwe clip met dezelfde resolutie kan een andere camera of uitsnede bevatten.

Oefenvraag: Waarom gebruiken we de controlepunten niet nogmaals om de fit te verbeteren?

Voorbeeldantwoord: Dan zijn het geen onafhankelijke controles van die fit meer. Een lage fout op de punten die de matrix bepaalden bewijst minder dan controle op andere bekende punten.

Bronnen: geometry.py Calibration, create_calibration en project_detection; calibration_input.py; point_picker.py.

## 23 Voetpunten en spelertelling

### Van een kader naar een grondpositie

Voor box [x1,y1,x2,y2] nemen we ((x1+x2)/2,y2) als voetpunt. Een volledig lichaam geeft meestal een bruikbaarder punt dan alleen een bovenlichaam. Een afgekapt kader bij de onderrand van het beeld krijgt niet zomaar een zekere grondpositie. Ook een ongeldige box of een punt buiten het veld wordt afgewezen.

project_detection beschrijft de uitkomst met statussen zoals valid, outside_field, truncated_bottom en invalid_transform. Een afgewezen waarneming krijgt geen verzonnen veldpositie. De vlakke transformatie geldt voor het grondvlak. Een bal in de lucht wordt in de pipeline niet als een gewone grondrol geprojecteerd.

### Tellen vraagt meerdere voorwaarden

player_exclusion_reason controleert eerst de rol en veldligging. count_exclusion_reason voegt modelbeschikbaarheid, kalibratie en zichtbaarheid toe. visible_detection accepteert een voorspelling boven de schermconfidence of een actuele gekoppelde track. Zo kunnen lage actuele matchingsdetecties zichtbaar blijven met een bestaande ID.

player_summary telt huidige waargenomen spelers op het veld. Het getal is geen gecontroleerde wedstrijdselectie of aantal unieke personen over de hele video. Bij ontbrekende kalibratie is het aantal onbekend, niet nul. Een verkeerde player-rol kan ondanks de veldfilter tot een verkeerde telling leiden.

Oefening: Leg drie gevallen uit. Een correct herkende steward binnen het veld telt niet als speler. Een speler buiten het veld telt niet mee. Bij ontbrekende kalibratie weten we het veldtotaal niet. Noem bij elk geval de codevoorwaarde die het verschil maakt.

Bronnen: geometry.py project_detection; participants.py; contracts.py FrameRecord.to_dict.

## 24 Automatische veldpunten en lijnen

### Een aparte externe omgeving

PnLCalib is externe code met bestaande gewichten voor veldpunten en lijnen. setup_field_model.py bereidt een geïsoleerde Python 3.11-omgeving voor. De eigen app-/detectieomgeving wordt niet over dezelfde dependencies heen geïnstalleerd. Revisie en gewichthashes maken de gebruikte versie controleerbaar.

field_calibration_worker.py voert de externe netwerken uit en zet hun uitvoer om naar ons eigen contract. Dit is een adapter. De worker gebruikt grondpunten plus controle met het lijnnetwerk. Hij voert niet automatisch de hele PnL-3D-refinementmethode van het externe project uit.

De netwerken leveren heatmapwaarnemingen. Een piek geeft een kandidaatlocatie. Een ruwe heatmapscore is geen gekalibreerde kans. De uitgebreide uitvoer bewaart daarom ruwe scores en gefilterde waarnemingen. Punten boven het grondvlak mogen niet zomaar als vlakke veldreferentie worden gebruikt.

### Een geldige fit vraagt meer dan vier willekeurige pieken

estimate_checked gebruikt verspreide grondpunten, achtergehouden controlepunten waar mogelijk en aparte lijnen voor geometrische controle. Spreiding, oriëntatie, eindigheid en projectieve horizon worden gecontroleerd. Een lijn kan een schatting tegenspreken. Een model dat zichzelf op modelpunten controleert, levert nog geen menselijke ground truth.

Oefenvraag: Waarom kunnen veel herkende punten toch een slechte minimap geven?

Voorbeeldantwoord: De semantische namen kunnen verkeerd zijn, punten kunnen dicht bij elkaar liggen of de locaties kunnen onnauwkeurig zijn. Een fit kan zulke fouten gedeeltelijk volgen. Daarom controleren we geometrie en gebruiken we voor echte nauwkeurigheid onafhankelijke referenties.

Bronnen: automatic_calibration.py; field_motion.py estimate_checked; scripts/field_calibration_worker.py; field_model_spec.py.

## 25 Camerabeweging optical flow en RANSAC

### Beweging tussen opeenvolgende beelden

Optical flow schat hoe zichtbare beeldkenmerken tussen frames verplaatsen. Lucas-Kanade volgt lokale kenmerken. Een piramide maakt het mogelijk beweging op verschillende schalen te bekijken. De voorwaartse/achterwaartse controle volgt heen en terug en wijst onbetrouwbare matches af.

RANSAC probeert een transformatie te vinden die door voldoende overeenkomende punten wordt ondersteund en negeert daarbij sommige uitschieters. Een inlier is een match die bij de gevonden transformatie past. Niet elke gevolgde grasspriet of spelerbeweging vertelt iets bruikbaars over de camerabeweging.

CameraCalibration gebruikt daarom onder meer minstens twintig motion-inliers, minstens 60% inliers, ruimtelijke spreiding en maximaal 1,5 pixel voorwaarts/achterwaarts verschil. Voor motion wordt een verkleind beeld tot breedte 960 gebruikt. De gemeten beweging wordt naar bronpixels omgerekend.

### De richting van de matrix

Als beweging M een oud beeldpunt naar zijn nieuwe beeldpunt omzet en H_oud van oud beeld naar veld gaat, dan geldt H_nieuw = H_oud maal inverse(M). Je moet dus rekening houden met de richting van de transformatie. De oude matrix simpelweg kopiëren zou geen camerabeweging corrigeren.

De gevolgde schatting mag maximaal twee seconden na de laatste zelfstandig gecontroleerde herkenning worden gebruikt. Camerawissels, onvoldoende matches of tegensprekende geometrie resetten de toestand. Lang blijven voorspellen kan drift veroorzaken. Bij uitval hoort onbekend op de minimap te staan.

Bronnen: field_motion.py CameraCalibration en DEFAULT_SETTINGS; docs/Broadcast_Veldexperiment.md.

## 26 Velddata en mogelijke veldtraining

### Code die bestaat is niet automatisch uitgevoerd bewijs

Het project heeft ook een route om SoccerNet-velddata en ontwikkelbeelden te verzamelen, labels te controleren, modellen bij te trainen en met bestaande gewichten te vergelijken. Dit staat in field_data.py en field_learning.py. Het bestaan van train-functies bewijst niet dat er een afgeronde, betere eigen veldtraining is opgeleverd.

collect_dataset, collect_highlights en prepare_frames organiseren bronbestanden en selecties. CorpusBudget bewaakt de ingestelde opslaggrens. De splits moeten wedstrijden en samenhangende groepen scheiden. Nieuwe automatische voorstellen worden niet zonder review trainingswaarheid.

FieldDataset maakt invoer en targets voor de veldnetwerken. masked_heatmap_loss rekent alleen mee waar het labelmasker supervisie toestaat. Een onzichtbaar of ongelabeld punt moet niet zomaar als zeker negatief meetellen. run_epoch voert een trainings- of evaluatie-epoch uit. Checkpoints worden zorgvuldig gepubliceerd zodat een onvolledig geschreven bestand niet als bruikbaar model wordt overgenomen.

make_runtime maakt een runtimeverwijzing naar traceerbare gewichten. propose maakt voorstellen, compare vergelijkt de nieuwe en oorspronkelijke modellen op dezelfde selectie. Dezelfde bronidentiteiten en gewichthashes moeten blijven kloppen.

Oefenvraag: Hebben jullie het automatische veldmodel zelf getraind?

Voorbeeldantwoord: Onze getoonde automatische route gebruikt pretrained PnLCalib-gewichten. Er is daarnaast trainings- en datavoorbereidingscode. We claimen alleen een eigen afgeronde veldtraining als we de echte run, gewichten en onafhankelijke vergelijking kunnen aanwijzen. De aanwezigheid van code alleen is niet genoeg.

Bronnen: field_data.py; field_learning.py; scripts/run_field_training.py; docs/Veldmodel_Training.md.

## 27 ByteTrack en trajecten

### Detectie en identiteit zijn verschillende taken

Een detector vindt objecten per frame. Een tracker probeert opeenvolgende waarnemingen aan dezelfde identiteit te koppelen. ByteTrack gebruikt sterke detecties voor een eerste matching en kan daarna lagere-confidencewaarnemingen met bestaande tracks koppelen. Alle lage kandidaten vooraf wegfilteren kan die tweede stap onbruikbaar maken.

De configuratie bevat high 0,25, low 0,10, new 0,25, match 0,80 en buffer 30. De effectieve bufferwerking wordt uit de gebruikte bibliotheek gelezen en in de run bewaard. Bij 25 updates per seconde zijn dertig updates 1,2 seconde. Het is geen garantie dat iedere speler na een occlusie dezelfde ID houdt.

Een Kalmanfilter is een onderdeel van de onderliggende bewegingsschatting. Het houdt een toestand en onzekerheid bij, voorspelt een volgende toestand en past die met een waarneming aan. Dat is niet hetzelfde als een werkelijk gezien voetpunt. Onze minimap tekent geen ongeobserveerde Kalmanpositie alsof die gemeten is.

### Onze adapter

ByteTrackAdapter filtert op geldige players en verwacht opeenvolgende frames. Voor Ultralytics 8.3.221 is een speciale SourceIndexedTracker en _IndexedBoxes-wrapper nodig om oorspronkelijke detectie-indexen door de confidencepartities te bewaren. Anders kan een ID aan de verkeerde box gekoppeld worden. Dit is versiecompatibiliteit, geen zelf ontworpen nieuwe tracker.

Trajectories bewaart maximaal vijf seconden waargenomen pad. Bij een ontbrekende of ongeldige waarneming wordt de lijn onderbroken. Tracking is achter MVP-review geplaatst en staat uit in de automatische bewegende-cameraroute. We hebben nog geen onafhankelijke set referentie-ID's voor sterke trackingclaims.

Bronnen: tracking.py; configs/bytetrack.yaml; pipeline.py accept_mvp en check_mvp_acceptance.

## 28 Video synchronisatie en Streamlit

### Eén tijdlijn

inspect_video controleert metadata en daadwerkelijke videotijdstempels. De pipeline verwacht een ondersteunde constante framerate en afmetingen. Een variabele framerate kan anders bij de koppeling tussen frame-index en tijd problemen geven. Het project weigert ook sommige rotatiegevallen in plaats van onzichtbaar de geometrie te veranderen.

De framerate wordt als teller en noemer bewaard. Frame i hoort dan bij i/fps. VideoWriter schrijft bronbeeld en minimap samen als één H.264-video van 1920 bij 720. Zo hebben beide weergaven dezelfde pause-, seek- en afspeeltijd. De uitvoer wordt gecontroleerd op frameaantal, codec, resolutie en framerate. Audio wordt niet behouden.

### De interface is een bediening bovenop de pipeline

Streamlit voert de appcode opnieuw uit bij interactie. session_state bewaart relevante keuzes tussen die heruitvoeringen. Zware verwerking hoort daarom achter een expliciete actie en moet passen bij de actuele invoeridentiteit. Het puntklikcomponent zet schermklikken terug naar bronpixels. Zoom en padding mogen de kalibratie niet ongemerkt veranderen.

render_frame tekent boxen, labels en veldpunten. Het tekent alleen wat de records als bruikbaar aangeven. field_review_ui laat bestaande uitvoer per bronframe bekijken en maakt menselijke referenties mogelijk. Die referenties moeten echte handmatige keuzes blijven, geen automatisch ingevulde goedkeuring.

Oefenvraag: Waarom kan een mooie uitvoervideo toch inhoudelijk slecht zijn?

Voorbeeldantwoord: Synchronisatie en afspeelbaarheid zeggen dat de techniek werkt. Ze bewijzen niet dat rollen, posities of aantallen kloppen. Daarvoor moeten we labels, geometrie en voorspellingen vergelijken.

Bronnen: video.py; render.py; point_picker.py; streamlit_app.py; field_review_ui.py.

## 29 Architectuur bestanden en controleerbaarheid

### Gegevens met een vaste betekenis

Detection bewaart bronklasse, semantische klasse, box, confidence en optioneel rol-, team-, veld- en trackinggegevens. FrameRecord groepeert detecties bij één bronframe. VideoMetadata bewaart de videokenmerken. RunResult verwijst naar de uitvoermap. Deze dataclasses voorkomen dat elke module een andere betekenis aan dezelfde losse lijst geeft.

SHA-256 maakt een identiteit van bestandsbytes. Een andere hash bewijst dat de bytes verschillen. Een gelijke hash betekent niet dat de labels inhoudelijk juist of de bron vrij te gebruiken zijn. digest_json maakt vergelijkbare identiteiten voor gestructureerde instellingen. code_identity bewaart codehashes en waar beschikbaar de Git-commit.

### Cache replay en bestandsveiligheid

Een runmanifest verbindt uitvoer aan video, code, dependencies, modellen en instellingen. Een bestaande output mag alleen onder passende voorwaarden hergebruikt worden. Replay leest eerder opgeslagen detecties zodat een andere downstreaminstelling met dezelfde waarnemingen kan worden onderzocht. Dat is geen nieuwe detectorinference.

processing_lock voorkomt gelijktijdige conflicterende verwerking in dezelfde uitvoerlocatie. Tijdelijke bestandsnamen en een uiteindelijke vervanging beperken het risico dat halve uitvoer als voltooid geldt. Een JSON- of modelhashcontrole is een integriteitscontrole, geen nauwkeurigheidstest.

model_handoff registreert gewichten met echte modelklassen en evaluatieverwijzingen. Git LFS bewaart grote bestanden via objecten buiten gewone Git-blobs. Een pointerbestand van ongeveer 132 bytes is geen werkend checkpoint. Voor gebruik moeten de echte bytes aanwezig zijn.

Bronnen: contracts.py; pipeline.py code_identity, processing_lock en validate_completed; replay.py; model_handoff.py; .gitattributes.

## 30 Installatie starten en problemen oplossen

### Omgevingen uit elkaar houden

Een virtuele Python-omgeving houdt pakketversies per project apart. De detectie-/trainingsomgeving en de externe veldomgeving hebben verschillende dependencybehoeften. Installeer niet zonder overleg een andere torch- of ultralytics-versie over de werkende omgeving. De historische lockbestanden beschrijven verschillende omgevingen; ze zijn niet allemaal samen één installatieopdracht.

Setup-Persoon1.ps1 bereidt de app-/YOLO-omgeving voor en kiest een passende CPU- of vastgelegde CUDA-build. CUDA voert geschikte tensorberekeningen op een NVIDIA-GPU uit. Een GPU-optie in JSON betekent niet dat de driver en build werkelijk werken. setup_tools.ps1 bereidt FFmpeg en ffprobe voor. setup_field_model.py is apart voor PnLCalib.

### Een veilige demonstratie

Start voor de basis met scripts/Start-Cursus.ps1. Dat selecteert de getrainde P004-detector en handmatige veldpunten. CheckOnly controleert bestanden en hashes zonder video-inference. Device cpu is een alternatief voor GPU 0. Gebruik een toegelaten overzichtsclip met vaste camera en laat tracking voor de basis uit.

Bij model ontbreekt controleer je LFS en het manifestpad. Bij CUDA-fout controleer je Pythonomgeving, torch-build en driver. Bij kalibratiefout bekijk je puntvolgorde en onafhankelijke controlepunten. Bij onbekende telling controleer je kalibratie en echte spelerklassen. Bij slechte teams kijk je of de video bekend is of de kleurclusters nog opwarmen.

Oefening: Toon zonder hulp welk startscript jullie demo gebruikt, welke config daarbij hoort en waar de resulterende uitvoer en framerecords staan. Noem ook wat je doet wanneer de automatische veldroute uitvalt: terug naar een geschikte statische clip en handmatige kalibratie, zonder resultaten te verzinnen.

Bronnen: scripts/Start-Cursus.ps1; scripts/Setup-Persoon1.ps1; README.md; docs/Gezamenlijke_Integratie.md.

## 31 Softwaretests en modelevaluatie

### Twee verschillende soorten bewijs

Een unit test kan controleren dat een homography een bekend synthetisch punt correct omzet. Een integratietest kan controleren dat een lege detectielijst toch een uitvoerframe oplevert. Een regressietest kan voorkomen dat twee echte overlappende personen door een boxregel samenvallen. Dit is nuttig softwarebewijs.

Maar een synthetische detectorfixture bewijst geen herkenningskwaliteit op voetbalbeelden. Een test met een verzonnen perfecte box zegt niet dat YOLO die box vindt. Daarom bewaren we echte modelmetingen apart van pytest-resultaten. Ook de historische testaantallen horen bij de toenmalige commit en omgeving en zijn geen automatisch nieuw testresultaat.

tests/test_geometry.py controleert geometriegevallen. test_participants.py controleert telregels. test_tracking.py kijkt naar matchinggedrag en compatibiliteit. test_app.py en de andere apptests controleren interfacegedrag. De veldtests onderzoeken onder meer uitval, verlopen schattingen en camerabeweging. tests/conftest.py en fixtures leveren gedeelde testvoorbeelden.

### Hoe we kwaliteit verder beoordelen

Een goede end-to-endreview gebruikt echte gewichten en een echte clip. We bekijken begin, midden en einde, controleframes, lege detecties, projectie-uitval en runtime. De review moet bij precies die run horen. Voor tracking zijn echte referentie-ID's nodig. Voor automatische geometrie zijn onafhankelijk aangeklikte punten nodig.

Oefenvraag: Als alle softwaretests slagen, mogen jullie dan zeggen dat er altijd 22 spelers correct worden geteld?

Voorbeeldantwoord: Nee. Tests tonen dat geselecteerde codegevallen werken. De echte detector kan nog mensen missen of rollen verwarren. We tellen waarnemingen die aan onze voorwaarden voldoen, geen gegarandeerd juiste wedstrijdselectie.

Bronnen: tests/; docs/acceptance.md; docs/validation.md; calibration_evaluation.py; evaluation.py.

## 32 Functies die we live moeten kunnen uitleggen

### Data en training

validate_dataset in persoon1/core.py leest het manifest en controleert labels, groepen, duplicaten en bronmetadata. require_experiment_data kiest de toegelaten reviewroute. build_yolo_dataset kopieert train- en validatiegegevens naar de YOLO-structuur. train in modeling.py start de configuratie en bewaart runprovenance. predict_manifest voert het gekozen model op een subset uit en bewaart voorspellingen. evaluate_run verbindt die uitvoer met de juiste referentielabels.

In metrics.py rekent iou overlap uit. match_class koppelt voorspellingen aan nog ongebruikte labels. ap101 maakt de geïnterpoleerde AP. evaluate bundelt klassemetingen en foutrecords. In role_training.py bouwt build het basismanifest, controleert load_training_manifest een uitbreiding, maakt scores de classificatiemetingen en voert train de rol-/teamtraining uit.

### Verwerking van video

load_model_manifest in detection.py controleert modelpaden, hashes, klassen en semantiek. UltralyticsDetector.detect voert inference uit en zet uitvoer om naar Detection-records. merge_person_proposals verwijdert bepaalde dubbele persoonsvoorstellen. AppearanceClassifier.classify verandert waar nodig de voorspelde rol en kiest een toegelaten teammethode. VideoTeams.update verzamelt kleurvoorbeelden en deelt zekere spelers in.

create_calibration berekent de handmatige matrix. project_detection zet het voetpunt om en bewaart een geldigheidsstatus. player_summary verzamelt de telinformatie. ByteTrackAdapter.update koppelt alleen geldige actuele player-waarnemingen aan IDs. Trajectories.update beheert de waargenomen paden. render_frame tekent één gecombineerd frame.

### De bovenste laag

process_video in pipeline.py orkestreert de hele run en schrijft video, records en manifest. accept_mvp registreert een expliciete menselijke beoordeling. check_mvp_acceptance controleert of die beoordeling bij de gevraagde trackingrun hoort. De CLI main-functies lezen argumenten en roepen de juiste onderliggende functies aan.

De volledige vindlijst staat in Functieindex.md. Die index omvat ook hulpscripts, methoden en tests. Niet elke helper is een nieuw theoretisch onderwerp. Gebruik de index om een functie terug te vinden en volg daarna invoer, aangeroepen functies, neveneffecten en uitvoer in de broncode.

## 33 Verdedigingsvragen met voorbeeldantwoorden

### Waarom kozen jullie voor transfer learning

We hebben weinig eigen voetbalbeelden vergeleken met grote pretrainingdatasets. We starten daarom met geleerde visuele kenmerken en passen ze aan. Dat maakt goede labels en een eerlijke validatie nog steeds noodzakelijk.

### Wat is het verschil tussen train en eval in PyTorch

model.train en model.eval veranderen het gedrag van lagen zoals batchnorm en dropout. Ze zetten niet zelf alle gradients aan of uit. Daarvoor zijn requires_grad, no_grad of inference_mode van belang. Onze roltraining houdt bijvoorbeeld batchnormgedrag vast terwijl geselecteerde gewichten nog trainbaar zijn.

### Waarom is AP bij strenge IoU veel lager

Het object kan ongeveer gevonden zijn terwijl de box nog onnauwkeurig is. Kleine verschuivingen tellen bij kleine objecten relatief zwaar. Een juiste boxonderkant is ook voor onze minimap belangrijk.

### Waarom is één datasetgemiddelde onvoldoende

Een model kan spelers verbeteren en tegelijk scheidsrechters verslechteren. Een grote spelersklasse kan bovendien zeldzame rollen overheersen. Daarom bekijken we klassen, precision/recall, foutvoorbeelden en de evaluatiescope apart.

### Wat is supervised en wat unsupervised bij ons

Detectie- en roltraining leren van labels en zijn supervised. De kleurclusters voor een nieuwe video groeperen op kenmerken zonder dat wij de juiste teamlabels als invoer meegeven. Dat is unsupervised. De getrainde teamkop op bekende wedstrijden is juist supervised.

### Waarom kunnen jullie geen snelheid in meters per seconde garanderen

Daarvoor moeten de veldschaal, positie en tijdmeting voldoende betrouwbaar zijn. Ons 105 bij 68 veld is een aanname en de voetpunten kunnen afwijken. We tonen vooral genormaliseerde veldposities en waargenomen trajecten.

### Wat was jullie belangrijkste negatieve resultaat

De baltrainingen verbeterden de gekozen validatiemaat niet. Op PANORIS bleven de scores nul. Op Football48 was pretrained beter dan F001/F002. Dat leerde ons dat training uitvoeren iets anders is dan aantoonbare verbetering behalen.

### Wat is de eerstvolgende inhoudelijke verbetering

Menselijke labelreview en een werkelijk onafhankelijke eindtest geven sterker bewijs dan nog een model toevoegen. Daarna kiezen we op basis van concrete fouten een gerichte dataronde of gecontroleerde modelaanpassing.

### Wat deed AI en wat moeten jullie zelf kennen

Codex hielp bij code, annotaties, proeven en documentatie, ook bij deze gids. We moeten de gekozen route zelf kunnen uitleggen, resultaten kunnen aanwijzen en de code zonder hulp doorlopen. AI-review mag niet als onafhankelijke menselijke review worden voorgesteld.

## 34 Oefensessie voor het hele team

### Eerste ronde zonder computer

Leg in één minuut het doel en de volledige route uit. Definieer daarna epoch, batch, loss, learning rate, confidence, IoU, precision, recall en AP. Gebruik eigen woorden en één rekenvoorbeeld. Wissel wie uitlegt; een goed antwoord van één teamlid bewijst niet dat iedereen het begrijpt.

### Tweede ronde met de bestanden

Open één trainingsconfig, één modelmanifest, één evaluatie-JSON en één foutvoorbeeld. Laat zien welke score bij welke bron en confidencevloer hoort. Ga daarna naar process_video, volg een Detection naar project_detection en leg uit hoe player_summary besluit om wel of niet te tellen.

### Derde ronde met de extra onderdelen

Wie de rolpipeline demonstreert, moet 576 plus 32 features, de kleurweging en de twee koppen kunnen uitleggen. Wie automatische geometrie toont, moet punt-/lijncontrole, camerabeweging en uitval kennen. Wie tracking toont, moet ID-wissels, lage confidencekandidaten en ontbrekende referenties bespreken. Leg geen extra aan het examen op die niemand kan verdedigen.

### Laatste controle

Bereid een echte geschikte demo voor. Controleer installatie, brongebruik, modelbytes, kalibratie en afspelen op de doellaptop. Noteer de echte individuele bijdragen van Andrew, Milan, Raoul en Jorre. Vul menselijke reviewers en acceptatie pas in nadat die handelingen werkelijk zijn gedaan.

Een goede proefverdediging bevat ook tegenvragen: Welke aanname kan falen? Waar zien we dat terug? Welke meting zou de hypothese controleren? Een eerlijk antwoord met een concreet bestand is sterker dan een ingewikkelde term zonder bewijs.

## 35 Begrippenlijst

Annotatie: een label of geometrische aanduiding bij een voorbeeld. Augmentatie: een labelbehoudende verandering van trainingsinvoer. Backbone: het deel van een netwerk dat kenmerken uit de invoer haalt. Batch: de tegelijk verwerkte groep voorbeelden. Checkpoint: een opgeslagen modeltoestand. Classifier: een model dat voor een gegeven invoer een klasse bepaalt.

Confidence: de score van een voorspelling, zonder automatische garantie op kalibratie. Crop: een uitsnede uit een bronbeeld. Datalek: informatie uit beoordeling die onbedoeld het leren of kiezen beïnvloedt. Detector: een model dat objectlocaties en klassen voorspelt. Epoch: een doorgang door de trainingsset. Feature: een kenmerk, geleerd of handmatig berekend.

Fine-tuning: een bestaand model verder aanpassen. Freeze: bepaalde parameters niet bijwerken. Gradient: de afgeleide informatie voor een gewichtsupdate. Ground truth: de referentielabels, die zelf fouten kunnen bevatten. Heuristiek: een praktische beslisregel. Homography: een projectieve vlak-naar-vlaktransformatie.

Inference: voorspellen met een model. Inlier: een waarneming die bij een geschatte relatie past. IoU: overlap gedeeld door gezamenlijke oppervlakte. Latent representation: interne kenmerken die niet rechtstreeks de oorspronkelijke pixels zijn. Leakage: zie datalek. Loss: de trainingsfout die geoptimaliseerd wordt.

Manifest: een bestand dat data, modellen of uitvoer met metadata beschrijft. NMS: overlapgebaseerde onderdrukking van dubbele voorstellen. Occlusie: een object dat geheel of gedeeltelijk achter iets anders zit. Optimizer: het algoritme dat modelgewichten bijwerkt. Overfitting: te sterk leren van ontwikkelvoorbeelden ten koste van nieuwe situaties.

Precision: aandeel juiste detecties onder de voorspellingen. Recall: aandeel gevonden objecten onder de labels. Reprojection error: afwijking bij het terugprojecteren naar bekende referenties. Seed: begininstelling van een toevalsgenerator. Tensor: een meerdimensionale rekenarray. Tracking: waarnemingen over de tijd aan identiteiten koppelen.

Validatie: ontwikkelbeoordeling om keuzes te maken. Weight decay: een beperking op gewichten tijdens optimalisatie. YAML en JSON: formaten voor gestructureerde instellingen of gegevens. YOLO: de detectorfamilie waarvan we een bestaande implementatie en pretrained gewichten gebruiken.

## 36 Bronnen en leskoppeling

### Onze lesdecks

1_DL_Setting_the_Scene.pptx behandelt onder meer pretrained aanpassen op dia 4, databetrouwbaarheid op 14, menselijke betrokkenheid op 49, confusion matrix op 52 en bias op 68-69. 2_DL_Adv_Deep_Learning.pptx behandelt trainingscyclus op 28, epoch/batch op 29, validatie op 30, preprocessing op 33-35, loss en learning rate op 37-40, Adam op 48, regularisatie op 55-64 en CNN's op 66. Het dianummer is de positie in het bestand inclusief titelblad.

### Directe projectbronnen

De opdracht staat in CV_Challenge_2026_2027.pdf. Resultaten en beperkingen staan in docs/Resultaten_Spelermodel.md, Resultaten_Balexperimenten.md, Resultaten_Rollen_en_Teams.md, Resultaten_Extra_Dataronde.md, Verbetering_Teams_en_Boxen.md en Broadcast_Veldexperiment.md. Gebruik de precieze rapporten en hashes bij een cijfer. Historische teksten kunnen een vroegere standaardconfiguratie beschrijven.

De actuele code staat onder src/football_pipeline, persoon1, scripts en streamlit_app.py. De configuraties staan in configs, trainingsidentiteiten in datasets en echte runbewijzen onder reports. docs/acceptance.md bevat de nog menselijke beoordelingsstappen. docs/GenAI_Disclosure.md en docs/ai_usage.md beschrijven de AI-hulp.

### Hoe we deze gids gebruiken

Deze uitleg is samengesteld op 13 november 2026 op branch codex/cursus-eenvoud. De functie-index beschrijft de aanwezige lokale code en vermeldt welke bestanden nog niet in een commit stonden bij het maken. De gids is geen nieuwe modelmeting. Nieuwe trainingen, menselijke labelreview, onafhankelijke eindevaluatie en gezamenlijke acceptatie zijn hiermee niet uitgevoerd.

De functie-index en README in deze map horen bij dit studiedocument. Broncode blijft de nauwkeurigste plek om een actuele parameter of controle te verifiëren. Als we een configuratie veranderen, moeten we de uitleg en de bijbehorende resultaten opnieuw op elkaar laten aansluiten.
