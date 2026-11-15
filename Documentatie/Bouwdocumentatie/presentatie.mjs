// Gebruik binnen een artifactSession.run-callback met de live presentation.
export async function build(presentation, fs, root) {
  const doc = root + '/Documentatie';
  const final = root + '/Messi10/final';
  const C={ink:'#143A48',green:'#16755F',muted:'#586D76',paper:'#F7FAF8',white:'#FFFFFF',gold:'#E9B85B'};
  presentation.theme.defaultFont='Arial';
  if(presentation.slides.items.length) throw new Error('Gebruik een lege presentatie.');
  function text(slide,value,x,y,w,h,size=28,color=C.ink,bold=false){
    const shape=slide.shapes.add({geometry:'textbox',name:value.slice(0,40),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    shape.text=value; shape.text.style={fontFamily:'Arial',fontSize:size,color,bold};return shape;
  }
  function slide(title,source,notes,dark=false){
    const s=presentation.slides.add();s.size={width:1280,height:720};s.background.fill=dark?C.ink:C.paper;
    text(s,'SPORTS VISION',64,30,900,28,18,dark?C.gold:C.green,true);
    text(s,title,64,90,1152,110,46,dark?C.white:C.ink,true);
    text(s,'Team Messi10 · 13 november 2026',64,676,1000,24,16,dark?'#CBDAD9':C.muted);
    text(s,String(presentation.slides.items.length).padStart(2,'0'),1170,676,50,24,16,dark?'#CBDAD9':C.muted);
    s.speakerNotes.text=notes+'\n\nBronnen: '+source+'\nStatus: documentatiesnapshot met open menselijke review en MVP-acceptatie. Exacte individuele bijdragen door team te bevestigen.';
    return s;
  }
  async function image(s,path,x,y,w,h,alt){
    const b=await fs.readFile(path);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/jpeg',alt,fit:'contain',position:{left:x,top:y,width:w,height:h}});
  }
  function lines(s,arr,{x=64,y=220,w=1110,size=29,gap=85,color=C.ink}={}){
    arr.forEach((v,i)=>text(s,v,x,y+i*gap,w,gap-8,size,color));
  }
  function table(s,values,widths,y=230,rowH=80){
    const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height:values.length*rowH,values});
    t.columnWidths=widths;
    t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:'Arial',fontSize:24,color:C.ink},fill:C.white});
    t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.ink,textStyle:{bold:true,typeface:'Arial',fontSize:24,color:C.white}});
    return t;
  }
  let s=slide('Sports Vision &\nTactical Mapping','Aangeleverde opdracht-PDF, p. 1-4; final/README.md.','Open met het doel: een voetbal-MP4 omzetten naar detecties en een gesynchroniseerde minimap. Deze presentatie toont de bestaande oplossing en haar bewijsgrenzen. Namen en eigen bijdragen moeten de teamleden zelf bevestigen.',true);
  text(s,'Voetbalanalyse met detectie, projectie en tijdelijke speler-ID’s',64,342,1050,100,31,C.white);
  text(s,'CV Challenge 2026-2027',64,535,900,50,25,C.gold);
  s=slide('De opdracht en onze scope','Documentatie/Bronnen/CV_Challenge_2026_2027.pdf, p. 1-4.','De kern is een statische camera zonder snelle cuts. Eerst data, fine-tuning en projectie bewijzen. De rubric geeft 25% aan data, 35% aan modeling, 20% aan fouten, 10% aan pipeline en 10% aan eigenaarschap. Geen minimum-mAP of FPS verzinnen. Een uitbreiding is nodig voor de hogere onderscheidingscategorie, maar pas na een solide MVP.');
  lines(s,['Eén statische voetbalclip als MVP','40–80 moeilijke beelden, annotatie en fine-tuning','mAP@50 en mAP@50:95 met concrete foutanalyse','Minstens vier veldpunten en een lokale gesynchroniseerde minimap'],{size:29,gap:88});
  s=slide('De verwerkingsketen','final/docs/Codekaart.md; final/src/football_pipeline; final/configs/models-broadcast.json.','Loop de keten door: video.py, detection.py, automatic_calibration.py of geometry.py, participants.py, tracking en teams, pipeline.py en render.py. Het gedeelde framerecord houdt bronframe en tijdstip samen. De standaard gebruikt broadcastspelers en automatische veldherkenning. Baldetectie met v3-tegels is optioneel. Het P006/F005-profiel is een afzonderlijke route.');
  lines(s,['1  MP4 en bronframes','2  Detectie, rollen en actuele veldgeometrie','3  Voetpuntprojectie, tijdelijke ID’s en teams','4  Detectievideo, minimap en opgeslagen framerecords'],{gap:87});
  s=slide('De gerichte annotatieset','final/datasets/school-ball80-review-v1/manifest.json; final/scripts/verify_final.py.','De echte set staat onder datasets, niet onder het oude data-pad uit sommige documenten. Er zijn 48 train- en 32 validatiebeelden met gescheiden wedstrijden en kloppende oorspronkelijke hashes. Alle beelden beginnen positief. AI-curatie van providerlabels is geen menselijke teamreview. De 80-reviewset verschilt van de 132 bronbeelden voor v2/v3.');
  text(s,'80',64,210,380,165,130,C.green,true);
  text(s,'48 train / 32 validatie',490,225,700,64,38,C.ink,true);
  text(s,'Gescheiden wedstrijdgroepen',490,320,700,70,29);
  text(s,'Menselijke labelreview staat nog open',64,485,1140,80,34,C.ink,true);
  text(s,'Eigen correcties en tweede review vormen de volgende datasetversie',64,580,1130,55,24,C.muted);
  s=slide('Een labelcorrectie bij de kleine bal','Documentatie/Trainingsbewijs/fouten/assisted-label-correction.jpg; final/docs/Resultaten_Balexperimenten.md.','Het oorspronkelijke helderheidsvoorstel omvatte een schoen. In frame 2525 beperkte AI de box van [1409,356,12,10] tot [1413,355,9,9], in x/y/breedte/hoogte. Het voorbeeld laat zien hoe de referentie de training en IoU beïnvloedt. Dit was een AI-correctie. Studenten moeten de labelregel zelf beoordelen. Bij onzichtbare bal geen positie verzinnen; lege labels pas negatief noemen na volledige controle.');
  await image(s,doc+'/Trainingsbewijs/fouten/assisted-label-correction.jpg',64,205,1152,340,'Oorspronkelijk balvoorstel en AI-correctie');
  text(s,'Strakke zichtbare balbox. Geen verzonnen positie bij volledige occlusie.',64,575,1130,70,27);
  s=slide('De trainingsproeven','final/scripts/experiment_broadcast_v2.py; experiment_broadcast_v3.py; Documentatie/Trainingsbewijs.','Leg epoch, batch, optimizer, learning rate en freeze uit. v2 start van F005, v3 van v2. Alleen tussen de twee v3-kandidaten verandert freeze 10 tegenover 0. Tussen v2 en de hele v3-ronde veranderen meer instellingen. De CSV-logs tonen werkelijk gelogde epochs, de tabel toont geplande maxima. Schaal/mosaic/mixup zijn voor deze balproef uitgeschakeld om kleine details te bewaren.');
  table(s,[['Proef','v2','v3-kandidaten'],['Max. epochs','12','16'],['Optimizer / lr','AdamW / 0,0001','Adam / 0,0001'],['Freeze','10','10 tegenover 0'],['Invoer / batch','640 / 4','640 / 4']],[380,340,432],210,72);
  text(s,'282 crops uit 132 bronbeelden. Werkelijke logs staan in het notebook.',64,604,1150,45,23,C.muted);
  s=slide('Balresultaten met dezelfde tegelroute','final/reports/broadcast-data/v2-experiment.json; v3-experiment.json.','De grafiek gebruikt dezelfde 73 volledige ontwikkelbeelden en overlappende 640-tegels. AP@50:95 stijgt van 10,19 naar 23,34 naar 25,74 procent. AP@50 is respectievelijk 27,38, 57,49 en 63,57 procent. Bij confidence 0,25 heeft v2 36 TP en 12 ongekoppelde detecties; v3 36 TP en 5 ongekoppelde detecties. Matching-IoU is 0,50. Hergebruikte AI-gecurateerde validatie is geen onafhankelijke eindtest.');
  s.charts.add('bar',{position:{left:70,top:205,width:1110,height:335},categories:['F005','Bal v2','Bal v3'],series:[{name:'AP@50:95 (%)',values:[10.19,23.34,25.74],fill:C.green}],hasLegend:false,barOptions:{direction:'column'},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{typeface:'Arial',fontSize:23,bold:true,color:C.ink}},xAxis:{textStyle:{fontFamily:'Arial',fontSize:23,color:C.ink}},yAxis:{min:0,max:35,textStyle:{fontFamily:'Arial',fontSize:20,color:C.muted},majorGridlines:{fill:'#D9E3DF',width:1}},title:'AP@50:95 (%)',titleTextStyle:{fontFamily:'Arial',fontSize:22,color:C.ink}});
  text(s,'v2 naar v3: 36 gevonden labels blijven 36. Ongekoppeld: 12 naar 5.',64,568,1150,70,27);
  text(s,'73 ontwikkelbeelden, eerder gebruikt bij selectie, menselijke review open',64,632,1150,32,20,C.muted);
  s=slide('De invoerroute bepaalt de conclusie','final/reports/broadcast-data/v2-experiment.json; v3-experiment.json.','Een hogere score op crops is niet hetzelfde als betere volledige-beelddetectie. De tabel gebruikt v2 en v3 freeze 0. Zonder tegels daalt AP@50:95 bij v3 van 18,01 naar 16,79 procent. Met tegels stijgt die van 23,34 naar 25,74 procent. Tegels bewaren kleine bronpixels maar kosten extra modelaanroepen. Dit motiveert de optionele v3-tegelconfiguratie.');
  table(s,[['AP@50:95','v2','v3'],['Volledig beeld, 1280','18,01%','16,79%'],['640-tegels','23,34%','25,74%']],[540,306,306],235,94);
  text(s,'De v3-verbetering hoort bij de tegelinstellingen',64,560,1140,75,32,C.green,true);
  s=slide('Spelerdetectie en conditionele scores','final/reports/broadcast-pitch-v1/summary.json, selected multisource-m.','De geselecteerde spelerkandidaat haalt 89,13% AP@50 en 53,83% AP@50:95 op 341 evalueerbare beelden met 5.078 spelerreferenties. Er zijn 4.623 TP, 398 FP en 455 FN. Zeven van 348 validatieframes ontbreken door onbruikbare referentiegeometrie. Het bestand noemt de geometrie conditional provider object correspondences. Het is geen evaluatie van automatische veldnauwkeurigheid en geen gezamenlijke score voor alle rollen en bal.');
  text(s,'89,13%',64,215,620,140,96,C.green,true);
  text(s,'speler-AP@50',735,238,480,60,36);
  text(s,'53,83% AP@50:95 op 341 ontwikkelbeelden',64,405,1130,80,34,C.ink,true);
  text(s,'Providergeometrie als voorwaarde. Geen automatische veldscore.',64,542,1130,70,27,C.muted);
  s=slide('Teamindeling en het keeperprobleem','final/reports/broadcast-pitch-v1/summary.json, teams van multisource-m.','Van 4.623 gematchte spelers zijn 4.208 teamlabels correct, 128 fout en 287 onbekend. 97,05% juistheid geldt alleen voor toegewezen gematchte spelers. Over alle 5.078 spelerreferenties heeft 82,87% een correct team. Van 194 keeperreferenties zijn er 176 gematcht maar slechts zestien krijgen het juiste team. Afwijkende shirts verklaren mogelijk de zwakte, maar die oorzaak is niet afzonderlijk bewezen. Onbekend is een geldige uitkomst.');
  table(s,[['Teammeting','Resultaat'],['Juist bij toegewezen gematchte spelers','97,05%'],['Correct team over alle spelerreferenties','82,87%'],['Keepers met correct team','16 van 194']],[870,282],220,84);
  text(s,'Gemiste spelers en onbekende teams blijven zichtbaar in de evaluatie',64,594,1140,52,25,C.muted);
  s=slide('Homography en de minimap','final/src/football_pipeline/geometry.py; final/reports/broadcast-pitch-v1/frame_000000.jpg; demonstration.json.','Koppel minstens vier niet-ontaarde veldpunten aan een vlak bovenaanzicht. OpenCV bepaalt een 3x3-matrix. Deel het homogene resultaat door de derde component. Projecteer het midden onder de spelerbox als benadering van het grondcontact, niet het boxcentrum. Extra controlepunten zitten niet in de fit. Een bal in de lucht en panorama-lensvervorming schenden aannames. Het getoonde beeld is een historische ontwikkelrun en geen actuele eindacceptatie.');
  await image(s,final+'/reports/broadcast-pitch-v1/frame_000000.jpg',64,203,1152,365,'Historische detectievideo met tactical map');
  text(s,'Vier of meer puntparen, extra controles en een werkelijk vlak grondvlak',64,587,1150,58,27);
  s=slide('Actuele kalibratie-uitval','final/reports/herstel-controles.json; herstel-echte-upload*.json.','Drie korte echte GPU-runs met twaalf frames hebben elk 0,0 bruikbare kalibratiefractie. Er zijn wel detecties, tijdelijke tracks en technische resultaatweergaven. Een bestaande oudere demo met 112/150 bruikbare veldframes gebruikt een andere bron/versie en heft deze uitval niet op. De 555 tests plus vier subtests zijn eerdere opgeslagen softwarecontroles. Ze bewijzen geen juiste veldposities. Prioriteit is een actuele statische demo met gecontroleerde homography.');
  text(s,'0 / 36',64,210,800,160,118,C.green,true);
  text(s,'bruikbare kalibraties in de recentste korte echte proeven',64,390,1100,90,34,C.ink,true);
  text(s,'555 softwaretests + 4 subtests geslaagd in het herstelrapport',64,540,1130,55,26,C.muted);
  text(s,'Een actuele geldige MVP-projectie moet nog worden aangetoond',64,606,1140,45,25,C.ink,true);
  s=slide('Uitbreidingen van de toepassing','final/docs/SORT_Tracking.md; Teams_Tracking_en_Telling.md; Afgelegde_Afstand.md; final/reports/broadcast-pitch-v1/frame_000149.jpg.','ByteTrack en optioneel SORT, teamindeling, trajecten, automatische veldmodellen, framecontrole, opgeslagen analyses en exports zijn aanwezig. Tijdelijke ID is geen permanente identiteit. Afstand is alleen een schatting uit geldige opeenvolgende waarnemingen. De actuele korte runs bewijzen geen afstandsnauwkeurigheid. Het beeld is een andere historische frameweergave, geen bewijs dat iedere uitbreiding onafhankelijk geaccepteerd is.');
  await image(s,final+'/reports/broadcast-pitch-v1/frame_000149.jpg',64,211,785,340,'Historisch ontwikkelbeeld met teams en tijdelijke tracks');
  lines(s,['Tracking en teams','Trajecten en schattingen','Framecontrole en export'],{x:900,y:250,w:310,size:25,gap:100});
  text(s,'Tijdelijke identiteit en geldige veldposities bepalen wat verantwoord is',64,588,1150,65,27);
  s=slide('GenAI en individueel eigenaarschap','final/docs/GenAI_Disclosure.md; ai_usage.md; Documentatie/GenAI_en_Eigenaarschap.md.','Codex hielp bij veel meer dan spelling: code, annotatiegereedschap, AI-curatie, experimenten, tests, integratie en documentatie. De precieze model-ID is niet vastgesteld. Providerlabels zijn geen eigen labels en AI-review is geen menselijke teamreview. Deze ronde las bestaand bewijs en maakte documentatie, zonder nieuwe training of YOLO26-resultaten. De afzonderlijke cursuspolicy ontbreekt in de aangetroffen stukken en moet het team controleren. Iedere student moet de hele keten zonder AI kunnen uitleggen.');
  lines(s,['AI-hulp bij code, curatie, experimenten en documentatie','Bronnen, overgenomen keuzes en tegenresultaten expliciet vermeld','Menselijke reviews en eigen bijdragen moeten echt worden bevestigd','Iedere student verdedigt de gebruikte keuzes zelfstandig'],{size:29,gap:87});
  s=slide('De mogelijke YOLO26-vervolgproef','Gebruikersmelding van lopende test; Documentatie/YOLO26_Vervolg.md.','Een ander teamlid test mogelijk YOLO26. Er is nog geen bevestigd checkpoint of resultaat in deze snapshot. Doe geen architectuur- of prestatieclaim. Vergelijk dezelfde labels, splits en evaluatieroute, noteer gewichtshash en versies. Meet beide AP-maten plus TP/FP/FN, volledige runtime en geheugen. Beschrijf afwijkende preprocessing of postprocessing expliciet. Een nieuwe detector lost ongeldige veldkalibratie niet automatisch op. Werk bij promotie rapport, notebook, deck, profielen en ZIP samen bij.');
  lines(s,['Kandidaat in onderzoek, nog geen bevestigd resultaat','Dezelfde referenties en een expliciet vergelijkingsbudget','Beide AP-maten, fouten, volledige runtime en integratie','Na keuze één consistente versie van rapport, code en ZIP'],{gap:87});
  s=slide('De resterende opleverpunten','Documentatie/Requirementscontrole.md; final/docs/acceptance.md.','De opdracht is gedeeltelijk vervuld. Eerst echte labelreview en de definitieve labelversie aan training/evaluatie koppelen. Daarna een actuele volledige statische MP4 met betrouwbare homography en gesynchroniseerde minimap demonstreren. Bevestig de YOLO26-keuze of behoud expliciet de baseline. Controleer de aparte GenAI-policy, namen en persoonlijke bijdragen. Oefen vragen over mislukkingen en afwegingen. Een verse machinecontrole en een onafhankelijke test versterken de claims, maar zijn geen letterlijk aparte indieningsbestanden. Upload pas de actuele samenhangende ZIP.');
  lines(s,['Labels als team beoordelen en aan de training koppelen','Een actuele statische MVP-run met geldige projectie opleveren','Modelkeuze, GenAI-policy en persoonlijke bijdragen afronden','Definitieve documentatie en ZIP samen bijwerken'],{gap:87});
  return {slides:presentation.slides.items.length,title:'Sports Vision & Tactical Mapping'};
}

// Actualiseer de bestaande 16-slidepresentatie met behoud van lay-out en bestaande objecten.
// Voor een nieuwe bouw: eerst build(...), daarna updateExisting(...).
export async function updateExisting(presentation) {
  const slides=presentation.slides.items;
  if(slides.length!==16) throw new Error('Verwacht de bestaande zestien slides.');
  const C={ink:'#143A48',green:'#16755F',muted:'#586D76',paper:'#F7FAF8',white:'#FFFFFF'};
  function change(i,oldValue,newValue){
    const shape=slides[i-1].shapes.getItem(oldValue.slice(0,40));
    shape.text=newValue;
  }
  function addText(s,value,x,y,w,h,size=28,color=C.ink,bold=false){
    const t=s.shapes.add({geometry:'textbox',name:value.slice(0,40),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    t.text=value;t.text.style={fontFamily:'Arial',fontSize:size,color,bold};return t;
  }
  for(let i=1;i<=16;i++)change(i,'Team Messi10 · 13 november 2026','Team Messi10 · versie 2 · 17a93756');
  change(1,'CV Challenge 2026-2027','CV Challenge 2026-2027 · bijgewerkt na pull');
  change(3,'De verwerkingsketen','Nieuwste bron en bewaarde final');
  change(3,'1  MP4 en bronframes','1  Nieuwe hoofdbron op Git-versie 17a93756');
  change(3,'2  Detectie, rollen en actuele veldgeometrie','2  YOLO11s-spelers en Andrew-bal in het broadcastprofiel');
  change(3,'3  Voetpuntprojectie, tijdelijke ID’s en teams','3  Spelersdrempel, tijdelijke ID’s, teams en veldprojectie');
  change(3,'4  Detectievideo, minimap en opgeslagen framerecords','4  De oudere final-map is afzonderlijk behouden');
  slides[2].speakerNotes.text='De pull bracht de gewone projectcode naar 17a93756. De nieuwe upstream-commit wijzigt final niet. De nieuwste code bevat Andrew-bal, spelersbediening en YOLO26-vergelijkingscode. De ZIP onderscheidt final en Nieuwste_bron. Andrew levert in het nieuwste broadcastprofiel uitsluitend klasse 0: ball, invoer 1280, confidence 0,03. Bestaande speler- en teammodellen blijven actief. De starter van Nieuwste_bron gebruikt de geïnstalleerde omgeving en veldruntime van de naastliggende final-map met de eigen actuele code en modellen. Bron: Versie_en_Wijzigingen.md en Versiebewijs/configs/models-broadcast.json.';
  change(7,'Balresultaten met dezelfde tegelroute','Historische balresultaten met tegels');
  change(7,'73 ontwikkelbeelden, eerder gebruikt bij selectie, menselijke review open','73 ontwikkelbeelden. Historisch v2/v3-bewijs, geen score voor Andrew-bal.');
  slides[6].speakerNotes.text+='\nActualisatie: dit zijn historische v2/v3-balmetingen. Andrews balmodel is nieuw in het hoofdprofiel; daarvoor zijn geen onafhankelijke AP-scores in deze actualisatie vastgesteld.';
  change(12,'Actuele kalibratie-uitval','Veldcontrole van het final-pakket');
  change(12,'bruikbare kalibraties in de recentste korte echte proeven','bruikbare kalibraties in de bewaarde final-herstelproeven');
  change(12,'Een actuele geldige MVP-projectie moet nog worden aangetoond','Nieuwste hoofdbron: geen nieuwe volledige videoproef in deze ronde');
  slides[11].speakerNotes.text+='\nVersiegrens: 0/36 hoort bij de oude final-herstelproef. Er is na deze pull geen nieuwe volledige echte videorun van de hoofdbron uitgevoerd. De cijfers mogen niet als een nieuwe evaluatie van de bron 17a93756 worden voorgesteld.';
  change(13,'Uitbreidingen van de toepassing','Spelersweergave en tracking');
  change(13,'Tracking en teams','Schuif 0,10–0,95');
  change(13,'Trajecten en schattingen','Herstelknop');
  change(13,'Framecontrole en export','Beleid per run');
  change(13,'Tijdelijke identiteit en geldige veldposities bepalen wat verantwoord is','Bronrapportage: IDF1 93,95% en 9 ID-wissels op 450 frames');
  addText(slides[12],'Historisch beeld. Nieuwe ruwe trackingaudit ontbreekt in deze checkout.',64,187,1152,30,20,C.muted);
  slides[12].speakerNotes.text='De nieuwe spelersschuif loopt van 0,10 tot 0,95 met beginwaarde 0,25. Aanpassen maakt de weergave strikt, ook voor bestaande ID’s, terwijl interne lage-confidence-detecties beschikbaar blijven. De herstelknop herstelt zowel 0,25 als het oorspronkelijke beleid voor actuele gevolgde spelers. Verwerken moet bewust opnieuw worden gekozen. Het effectieve player_policy hoort bij cache en runmanifest. De trackinghandleiding rapporteert 93,95% gezamenlijke IDF1 en negen ID-wissels op 450 frames met providergeometrie. Het is geen rekenkundig gemiddelde van de drie percentages. De lokale ruwe auditmap ontbreekt, dus dit is bronrapportage. Het beeld is een oudere ontwikkelrun en geen screenshot van de nieuwe bediening. Bron: Versiebewijs/docs/Spelersdrempel_en_tracking.md.';
  slides[13].speakerNotes.text+='\nVersie 2: Codex heeft de pull en conflictoplossing uitgevoerd, bestaand lokaal werk behouden en de actuele documenten bijgewerkt. 117 gerichte regressietests slagen. Nieuwe YOLO26- en trackingwaarden zijn duidelijk toegeschreven aan opgehaalde handleidingen; de ruwe lokale experimentmappen ontbreken. Geen nieuwe training uitgevoerd.';
  const s=slides[14];s.shapes.deleteAll();
  addText(s,'SPORTS VISION',64,30,900,28,18,C.green,true);
  addText(s,'YOLO26-uitkomst volgens projecthandleiding',64,90,1152,110,46,C.ink,true);
  const values=[['Spelersmodel','Pipeline-F1','Stacktijd'],['Huidig YOLO11s','91,81%','250,81 ms'],['Nieuw YOLO11s','91,62%','251,18 ms'],['Nieuw YOLO26s','91,45%','252,67 ms']];
  const t=s.tables.add({rows:4,columns:3,left:64,top:222,width:1152,height:296,values});
  t.columnWidths=[530,300,322];
  t.cells.block({row:0,column:0,rowCount:4,columnCount:3}).assign({fill:C.white,textStyle:{fontSize:25,typeface:'Arial',color:C.ink}});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:3}).assign({fill:C.ink,textStyle:{fontSize:25,typeface:'Arial',color:C.white,bold:true}});
  addText(s,'Het bestaande YOLO11s blijft gekozen',64,545,1152,52,31,C.green,true);
  addText(s,'Bronrapportage, ruwe experimentmap ontbreekt. Stacktijd is geen video-FPS.',64,610,1152,48,23,C.muted);
  addText(s,'Team Messi10 · versie 2 · 17a93756',64,676,1000,24,16,C.muted);
  addText(s,'15',1170,676,50,24,16,C.muted);
  s.speakerNotes.text='Bron: Versiebewijs/docs/Yolo26_Spelersvergelijking.md uit de pull op 17a93756. De vergelijking wordt daar als afgerond gerapporteerd. Alle drie kandidaten liggen binnen 0,5 procentpunt; het bestaande model heeft iets hogere F1 en lagere detectorstacktijd. Eén seed, hergebruikte ontwikkelvalidatie: 3.936 train, 348 detectorvalidatie, 341 pipelinebeelden met providergeometrie. Na OOM op 1536 starten beide nieuwe modellen opnieuw op 1280. YOLO26 stopt epoch 24, beste 4; YOLO11 epoch 31, beste 11. Detectorstack bevat vaste persoons- en baldetector, maar geen decoding, rol/team of veldnetwerk. De lokale ruwe experimentmap ontbreekt en is niet opnieuw berekend. Exacte nieuwe AP-getallen staan niet in de opgehaalde samenvatting. Andrew blijft uitsluitend de bal leveren.';
  change(16,'Modelkeuze, GenAI-policy en persoonlijke bijdragen afronden','Ruwe nieuwe experimentbewijzen, GenAI-policy en eigen bijdragen');
  change(16,'Definitieve documentatie en ZIP samen bijwerken','Bewust kiezen welke pakketversie je demonstreert');
  slides[15].speakerNotes.text='De modelkeuze is volgens de nieuwe bron gemaakt: behoud YOLO11s. Nog open: menselijke labelreview, koppeling van definitieve labels aan training/evaluatie, actuele statische MVP met geldige projectie, persoonlijke bijdragen en aparte GenAI-policy. Deel de ruwe nieuwe YOLO26-/trackingbewijzen. Demonstreer bewust final of Nieuwste_bron en schrijf de resultaten aan die versie toe. Nieuwe documentatie, notebook en bronbewijzen zijn bijgewerkt naar 17a93756; geen nieuwe training of volledige echte videoproef in deze ronde.';
  return {slides:slides.length,revision:'17a93756',updated:[1,3,7,12,13,14,15,16]};
}
