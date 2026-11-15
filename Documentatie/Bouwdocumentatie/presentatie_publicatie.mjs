// Actualisatie van de bestaande versie-2-presentatie voor GitHub-publicatie.
export function updatePublication(presentation) {
  const S=presentation.slides.items;
  if(S.length!==16)throw new Error('Verwacht de bestaande zestien slides.');
  function set(i,name,value){S[i-1].shapes.getItem(name.slice(0,40)).text=value;}
  for(let i=1;i<=16;i++)set(i,i===15?'Team Messi10 · versie 2 · 17a93756':'Team Messi10 · 13 november 2026','Team Messi10 · 15 nov 2026 · 524d081a');
  set(1,'CV Challenge 2026-2027','Versie 3 · Andrew en Jorre verwerkt');
  S[0].speakerNotes.text='Documentatiepublicatie van 15 november 2026, broncommit 524d081a. De bijdragen van Andrew en Jorre zijn verwerkt. De menselijke review van alle huidige 80 labels is geregistreerd op 14 november op basis van gebruikersbevestiging. De hoofdbron en GitHub-final hebben eigen startprocedures. Geen nieuwe modeltraining of onafhankelijke modelbenchmark in deze ronde.';
  set(3,'De verwerkingsketen','Gedeelde hoofdbron en GitHub-final');
  set(3,'1  MP4 en bronframes','1  GitHub main op broncommit 524d081a');
  set(3,'2  Detectie, rollen en actuele veldgeometrie','2  YOLO11s-spelers en Andrew-bal uit YOLOv8x');
  set(3,'3  Voetpuntprojectie, tijdelijke ID’s en teams','3  Rollen, teams, gedeelde ByteTrack en veldprojectie');
  set(3,'4  Detectievideo, minimap en opgeslagen framerecords','4  Het GitHub-final-pakket heeft een eigen schoolroute');
  S[2].speakerNotes.text='De gedeelde hoofdbron wordt beschreven op 524d081a. Het bestaande YOLO11s-spelermodel blijft actief; het broadcastprofiel gebruikt alleen de baluitvoer van Andrews vierklassen-YOLOv8x. De originele prototype-tracking is niet gelijkgesteld aan de gedeelde ByteTrack-route. De getrackte GitHub-final-README beschrijft de eenvoudige schoolstart; een uitgebreidere lokale final-kopie is niet ongemerkt meegepubliceerd. Bronnen: configs/models-broadcast.json, docs/Afronding_20261114.md, docs/VierKlassenModel.md.';
  set(4,'Menselijke labelreview staat nog open','Alle 80 labels goedgekeurd volgens teamverklaring');
  set(4,'Eigen correcties en tweede review vormen de volgende datasetversie','Geregistreerd op 14 november. Labels en de 48/32-split zijn ongewijzigd.');
  S[3].speakerNotes.text='Het team heeft volgens expliciete gebruikersbevestiging alle huidige 80 labels gecontroleerd en goedgekeurd. Jorre heeft de verklaring op 14 november geregistreerd. Twijfelgevallen vielen buiten de selectie. De AI/provider-herkomst en de 48 train/32 validatie blijven behouden; labels en beelden zijn niet gewijzigd. Geen individuele reviewernamen, aantallen meningsverschillen of correcties verzonnen. De verklaring geldt niet automatisch voor andere datasets en is geen nieuwe training of onafhankelijke test. Bron: final/datasets/school-ball80-review-v1/REVIEW.md.';
  set(5,'Strakke zichtbare balbox. Geen verzonnen positie bij volledige occlusie.','Historisch AI-correctievoorbeeld. De huidige 80-labelreview is geregistreerd.');
  S[4].speakerNotes.text+='\nActualisatie: de huidige 80-labelselectie is volgens teamverklaring goedgekeurd. Het getoonde historische AI-voorbeeld is geen achteraf gereconstrueerd individueel reviewlog.';
  set(6,'De trainingsproeven','Historische proeven en Andrews training');
  set(6,'282 crops uit 132 bronbeelden. Werkelijke logs staan in het notebook.','Andrew: YOLOv8x, maximaal 50 epochs, invoer 1280, batch 6');
  S[5].speakerNotes.text='De tabel beschrijft de eerdere v2/v3-balexperimenten. Andrews oorspronkelijke Andrew_Prototype/train.ipynb begint met YOLO(yolov8x.pt), maximaal 50 epochs, imgsz 1280, batch 6, patience 20, workers 2, device 0 en AMP. De procesallocatie is beperkt tot 85% GPU-geheugen; dit voorkomt niet iedere OOM. De naam ball_detector_640 verandert de ingevoerde resolutie 1280 niet. Het bronnotebook bewijst de instellingen, niet zelfstandig het uiteindelijke aantal voltooide epochs of een onafhankelijke mAP-score.';
  set(12,'Actuele kalibratie-uitval','Historische veldcontrole en actuele checks');
  set(12,'bruikbare kalibraties in de recentste korte echte proeven','bruikbare kalibraties in eerdere lokale herstelproeven');
  set(12,'555 softwaretests + 4 subtests geslaagd in het herstelrapport','Gedeelde CPU-controle: 537 tests, 1 skip en 4 subtests');
  set(12,'Een actuele geldige MVP-projectie moet nog worden aangetoond','Actuele geaccepteerde statische minimapdemonstratie blijft nodig');
  S[11].speakerNotes.text='De 0/36 betreft oude lokale herstelproeven, geen nieuwe evaluatie van 524d081a of GitHub-final. Jorres gedeelde afronding van 14 november meldt 537 passed, 1 GPU-skip en 4 subtests passed op CPU. In deze publicatieronde slagen 75 gerichte lokale tests. Deze aantallen horen bij verschillende controles en worden niet opgeteld. Geen nieuwe training of volledige echte videorun. Bron: reports/release-20261114/checks.json en Documentatie/Versiebewijs/gerichte-tests-20261115.xml.';
  set(14,'AI-hulp bij code, curatie, experimenten en documentatie','Andrew: structuur, eerste codeonderdelen en debugging');
  set(14,'Bronnen, overgenomen keuzes en tegenresultaten expliciet vermeld','Jorre: integratie, technische checks en reviewregistratie');
  set(14,'Menselijke reviews en eigen bijdragen moeten echt worden bevestigd','De goedkeuring van alle 80 labels is geregistreerd');
  set(14,'Iedere student verdedigt de gebruikte keuzes zelfstandig','Iedere student blijft verantwoordelijk en verdedigt eigen keuzes');
  S[13].speakerNotes.text='Andrew verantwoordt AI-gebruik in docs/VierKlassenModel.md hoofdstuk 16: documentstructuur, eerste codeonderdelen, trackingopzet en debugging. Volgens zijn verklaring zijn voorstellen handmatig beoordeeld, aangepast en getest. Geen toolnamen of model-ID’s toegevoegd die hij niet specificeert. Jorres afronding registreert technisch herstel en de expliciete teamgoedkeuring van de 80 labels. De gezamenlijke disclosures vermelden bredere Codex-hulp. De huidige publicatie gebruikt Codex voor pull, samenvoeging en documentatie; geen nieuwe modelbenchmark. De aparte GenAI-policy en individuele mondelinge verdediging blijven teamverantwoordelijkheden.';
  set(16,'Labels als team beoordelen en aan de training koppelen','Goedgekeurde labels koppelen aan concreet trainingsbewijs');
  set(16,'Definitieve documentatie en ZIP samen bijwerken','Zelfstandig verdedigen en het definitieve eindpakket controleren');
  S[15].speakerNotes.text='De menselijke 80-labelreview staat niet meer open. Nog nodig: de exacte koppeling tussen de eigen definitieve selectie en training/evaluatie, een actuele geaccepteerde statische minimapdemo, ruwe nieuwe YOLO26-/trackingbewijzen, de aparte GenAI-policy en individuele verdediging. De compacte documenten worden op GitHub gedeeld. Oude lokale ZIP’s zijn geen actuele gedeelde release.';
  return {slides:S.length,revision:'524d081a',documentationVersion:3};
}
