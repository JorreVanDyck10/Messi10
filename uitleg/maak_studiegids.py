"""Build the study document and exact source index without ML dependencies.

Run with a Python environment containing python-docx. Does not train models.
"""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

MODULES = {
    'appearance': 'Maakt persoonscrops, CNN- en kleurfeatures en voorspelt aanvullende rollen en teams.',
    'automatic_calibration': 'Leest automatische veldwaarnemingen, schat geometrie en projecteert geldige grondpunten.',
    'calibration_evaluation': 'Vergelijkt automatische veldprojectie met expliciet gereviewde menselijke referenties.',
    'calibration_input': 'Geeft kalibratiepunten herkenbare namen en levert alleen passende pilotsuggesties.',
    'cli': 'Verbindt commandoregelargumenten met de pipelinehandelingen.',
    'contracts': 'Definieert gegevensstructuren, JSON-invoer en uitvoer en hashes.',
    'demo': 'Maakt synthetische demonstratiegegevens voor softwarecontrole, geen voetbalbenchmark.',
    'detection': 'Controleert profielen, voert YOLO uit en combineert waar nodig persoonsvoorstellen.',
    'evaluation': 'Meet trackinggedrag tegen referenties en houdt de scope van de beoordeling bij.',
    'field_data': 'Verzamelt en selecteert velddata binnen opslag- en splitsafspraken.',
    'field_layout': 'Bewaart de namen en genormaliseerde locaties van veldmarkeringen.',
    'field_learning': 'Levert veldtraining, heatmapverlies, voorstellen en vergelijkingen in de aparte runtime.',
    'field_model_spec': 'Legt de toegelaten externe bron en gewichten vast en controleert hun identiteit.',
    'field_motion': 'Controleert veldgeometrie en volgt tijdelijk een schatting met gemeten camerabeweging.',
    'field_review': 'Bewaart echte reviewgegevens en onderzoekt uitvalperiodes.',
    'field_review_ui': 'Toont bronframes en overlays voor handmatige veldbeoordeling.',
    'geometry': 'Berekent en controleert handmatige homography en projecteert voetpunten.',
    'model_handoff': 'Registreert modelgewichten met klassen, instellingen en evaluatieverwijzing.',
    'participants': 'Houdt rol, veldligging, zichtbaarheid en spelertelling gescheiden.',
    'pipeline': 'Orkestreert invoercontrole, verwerking per frame, uitvoer en acceptatie.',
    'point_picker': 'Zet klikken in de kalibratiecomponent om naar de juiste puntgegevens.',
    'render': 'Tekent detecties, kalibratieoverlays, minimap en optionele waargenomen trajecten.',
    'replay': 'Leest opgeslagen detecties opnieuw met controle op frame en video.',
    'teams': 'Maakt shirtkleurfeatures en verzamelt twee videolokale kleurclusters.',
    'tracking': 'Verbindt ByteTrack met onze detectie-indexen en beheert waargenomen trajecten.',
    'video': 'Controleert of voorbereidt video, tijdstempels en framegegevens; de map bepaalt welke route.',
    'core': 'Controleert datasets, labels, groepssplits, reviewstatus en bestandsidentiteit.',
    'modeling': 'Bouwt YOLO-data, start training, voert inference uit en laat resultaten evalueren.',
    'role_training': 'Bouwt rolcrops, leert CNN-/kleurclassificatiekoppen en bewaart rol-/teammetingen.',
    'metrics': 'Berekent IoU, eenmalige boxmatches, AP op 101 recallpunten en TP/FP/FN.',
    'annotation': 'Bewaart annotaties en biedt de lokale annotatiebediening aan.',
    'appearance_evaluation': 'Evalueert de volledige aanvullende rolpipeline op gelabelde frames.',
    'appearance_video_probe': 'Voert een beperkte echte videoproef met rolherkenning uit.',
    'participant_baseline': 'Vergelijkt lokalisatie zonder COCO-person ten onrechte speler te noemen.',
    'preprocessing_audit': 'Onderzoekt hoeveel kleine trainingsboxen na de echte voorbewerking overblijven.',
    'project_dataset': 'Bouwt de oorspronkelijke gerichte projectdataset vanuit de bronselectie.',
    'review_sheets': 'Maakt visuele controlebladen voor beelden en annotaties.',
    'teamtrack_dataset': 'Zet de geselecteerde TeamTrack-bronnen en rollen om naar onze dataset.',
    'error_review': 'Verbindt concrete foutgevallen met beelden en evaluatierecords.',
    'technical_check': 'Controleert de technische omgeving en gerichte modelproeven.',
    'broadcast_field_experiment': 'Voert de ontwikkelvergelijking voor Broadcast-veldherkenning uit.',
    'build_role_extension': 'Bouwt het afzonderlijke v2-manifest voor de extra rolcrops.',
    'collect_development_candidates': 'Verzamelt kandidaatbeelden; voorstellen zijn nog geen gereviewde labels.',
    'evaluate_role_extension': 'Vergelijkt aanvullende roltrainingen en bewaart uitgesplitste resultaten.',
    'evaluate_video_teams': 'Vergelijkt kleurteamindeling op vastgelegde referentiecrops.',
    'export_football_annotations': 'Exporteert annotatievoorstellen naar de lokale voetbalworkflow.',
    'fetch_role_photos': 'Haalt vastgelegde bronfoto’s met bronmetadata op.',
    'field_calibration_diagnostic': 'Onderzoekt veldwaarnemingen en afwijzingen voor diagnose.',
    'field_calibration_pilot': 'Maakt een beperkte echte veldmodelproef met bewaarde instellingen.',
    'field_calibration_worker': 'Voert de externe punt-/lijnnetwerken in de aparte Pythonomgeving uit.',
    'football48_ball_experiment': 'Vergelijkt pretrained sports ball met echte ballen-fine-tuning op Football48.',
    'panoris_pilot': 'Bereidt de statische pilot voor en controleert projectie en technische uitvoer.',
    'run_field_training': 'Stuurt voorbereiding, training en vergelijking aan met aparte logbestanden.',
    'setup_field_model': 'Installeert de geïsoleerde PnLCalib-runtime en gecontroleerde releasegewichten.',
    'setup_field_training': 'Bereidt de afzonderlijke veldtrainingsomgeving voor.',
    'smoke_model': 'Doet een kleine technische modelcontrole, geen onafhankelijke prestatiemeting.',
    'verify_player_pipeline': 'Controleert contracten en echte pipeline-uitvoer op spelers en rollen.',
    'streamlit_app': 'Bedient upload, modelkeuze, veldpunten, review, verwerking en videoweergave.',
}
PURPOSES = {
    'load_model_manifest': 'Leest het profiel en weigert ontbrekende of veranderde gewichten en onjuiste klassemapping.',
    'available_roles': 'Verzamelt welke semantische rollen het gekozen profiel echt kan leveren.',
    'merge_person_proposals': 'Selecteert één waarneming voor bepaalde dubbele persoonsvoorstellen.',
    'validate_detection_devices': 'Controleert of de gevraagde rekenapparaten bruikbaar zijn.',
    'crop_tensor': 'Knipt een persoonsgebied uit en maakt de genormaliseerde RGB-tensor voor de classifier.',
    'jersey_feature': 'Berekent 32 histogramkenmerken van een centraal shirtgebied.',
    'kit_feature': 'Berekent kleurkenmerken voor de afzonderlijke clustering met verzadigingsweging.',
    'backbone': 'Bouwt de MobileNetV3 Small-feature-extractor zonder oorspronkelijke classificatiekop.',
    'create_calibration': 'Past een homography op de fitpunten en meet afwijkingen op controlepunten.',
    'valid_box': 'Controleert boxgeometrie, beeldgrenzen en geldige confidencewaarden.',
    'project_detection': 'Projecteert het onderste midden van de box of bewaart waarom dat niet mag.',
    'point_coordinate_issues': 'Geeft aan welke puntvelden ontbreken of ongeldige getallen bevatten.',
    'player_summary': 'Verzamelt zichtbare spelers, geldige veldtellingen, andere rollen en teamtotalen.',
    'player_exclusion_reason': 'Wijst een waarneming af als de rol of veldpositie geen geldige player is.',
    'field_exclusion_reason': 'Controleert box en huidige veldpositie onafhankelijk van de rol.',
    'count_exclusion_reason': 'Geeft de concrete reden waarom een detectie niet meetelt.',
    'counted_as_player': 'Levert waar op als er geen uitsluitreden voor de spelertelling is.',
    'visible_detection': 'Laat de weergavedrempel of een actuele gekoppelde track gelden.',
    'field_available': 'Bepaalt of voor dit frame bruikbare veldgeometrie beschikbaar is.',
    'code_identity': 'Maakt hashes van de eigen pipelinecode en leest waar mogelijk de commit.',
    'dependencies': 'Bewaart de werkelijk geïnstalleerde versies van relevante pakketten.',
    'processing_lock': 'Voorkomt conflicterende verwerking in dezelfde uitvoerlocatie.',
    'process_video': 'Voert de complete verwerking van bronvideo tot gecontroleerde uitvoer uit.',
    'accept_mvp': 'Registreert de expliciete review van een daarvoor geschikte echte MVP-run.',
    'check_mvp_acceptance': 'Controleert dat een bestaand reviewrecord bij de huidige trackingvoorwaarden hoort.',
    'validate_completed': 'Controleert dat de opgeslagen run als voltooid en bruikbaar geldt.',
    'iou': 'Rekent overlapoppervlakte gedeeld door gezamenlijke boxoppervlakte.',
    'match_class': 'Matcht voorspellingen in confidencevolgorde aan nog niet gebruikte referentieboxen.',
    'ap101': 'Middelt de geïnterpoleerde precisie op 101 recallniveaus.',
    'evaluate': 'Controleert de meetinvoer en berekent AP, werkpuntmetingen en foutrecords.',
    'scores': 'Berekent de verwarringsmatrix en classificatiemetingen per rol en gemiddeld.',
    'validate_dataset': 'Controleert datasetstructuur, bestanden, labels en groepsgrenzen.',
    'require_approval': 'Vereist een passende echte menselijke datasetgoedkeuring.',
    'require_experiment_data': 'Laat alleen de expliciet gekozen en passende reviewroute toe.',
    'read_labels': 'Leest en controleert de YOLO-labelregels.',
    'label_pixels': 'Zet genormaliseerde labelcoördinaten om naar oorspronkelijke beeldpixels.',
    'dataset_path': 'Resolveert datasetbestanden met de toegelaten padgrenzen.',
    'load_manifest': 'Leest de datasetbeschrijving samen met de bijbehorende basislocatie.',
    'class_mapping': 'Verbindt werkelijke modelklassen met expliciete doelklassen.',
    'fresh_output': 'Vereist een nieuwe uitvoerlocatie om bestaand bewijs niet te overschrijven.',
    'assert_final_access': 'Bewaakt de voorwaarden voordat gereserveerde eindtestdata gebruikt wordt.',
    'predict_manifest': 'Voert het model op de geselecteerde subset uit en bewaart voorspellingen.',
    'build_yolo_dataset': 'Maakt een YOLO-train/validatiestructuur vanuit het gecontroleerde manifest.',
    'load_training_manifest': 'Controleert bronbeelden, cropidentiteiten en splits van extra roltraining.',
    'supervised_team_videos': 'Verzamelt alleen de bronidentiteiten met toegelaten teamsupervisie.',
    'masked_heatmap_loss': 'Berekeningsstap voor heatmapverlies met een supervisiemasker.',
    'validate_labels': 'Controleert eindige genormaliseerde veldlabels en toegestane afronding.',
    'register_player_model': 'Maakt een traceerbaar profiel voor echte spelersgewichten.',
    'available_model_profiles': 'Zoekt modelprofielen voor de interface, met de standaard als eerste.',
    'replay_detections': 'Leest opgeslagen detecties met controle op bronframe en video.',
    'render_frame': 'Tekent één gecombineerd bronbeeld en minimapbeeld.',
    'field_pixel': 'Zet genormaliseerde veldcoördinaten om naar minimappixels.',
    'sha256_file': 'Berekent een SHA-256-identiteit van de exacte bestandsbytes.',
    'sha256': 'Berekent een SHA-256-identiteit van de exacte bestandsbytes.',
    'digest_json': 'Berekent een identiteit van genormaliseerd geserialiseerde gegevens.',
    'canonical_hash': 'Maakt een herhaalbare hash van gestructureerde gegevens.',
    'read_json': 'Leest gestructureerde JSON-gegevens.',
    'write_json': 'Schrijft JSON-gegevens; de module bepaalt de precieze schrijfwaarborgen.',
    'transform': 'Voert een projectieve punttransformatie inclusief homogene deling uit.',
    'estimate_checked': 'Schat automatische veldgeometrie met aparte kwaliteitscontroles.',
    'checked_matrix': 'Weigert ongeldige, onstabiele of verkeerd georiënteerde matrices.',
    'line_checks': 'Vergelijkt de schatting met beschikbare lijnwaarnemingen.',
    'evaluate_calibration': 'Vergelijkt de run met onafhankelijk gereviewde menselijke veldpunten.',
}

def git_output(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()

def make_index():
    files = sorted([ROOT/'streamlit_app.py', *ROOT.glob('src/**/*.py'), *ROOT.glob('persoon1/**/*.py'), *ROOT.glob('scripts/*.py'), *ROOT.glob('tests/*.py')])
    lines=['# Functieindex bij de studiegids','',
           'Gemaakt op 13 november 2026. Dit is een bronindex, geen nieuwe uitvoering van modellen of tests. De korte uitleg hoort bij de bredere hoofdstukken in Studiegids.md. Broncommentaren zijn letterlijk uit de code overgenomen en kunnen Engels zijn.',
           '', 'Elke definitie vermeldt bestand, regels, argumenten, aangeroepen functies en technische kenmerken. Die kenmerken zijn uit de syntax afgeleid: een if-statement bewijst bijvoorbeeld geen inhoudelijk correcte validatie. Ga voor de precieze werking naar de gekoppelde bron.',
           '', 'Definities van externe bibliotheken zijn niet gekopieerd. Het bestand waar een functie staat bepaalt haar context; twee functies met dezelfde naam kunnen iets anders doen.']
    totals={'files':0,'definitions':0,'functions':0,'classes':0,'test_definitions':0}
    hashes={}
    for file in files:
        rel=file.relative_to(ROOT).as_posix();text=file.read_text(encoding='utf-8-sig');tree=ast.parse(text)
        hashes[rel]=hashlib.sha256(file.read_bytes()).hexdigest()
        status=git_output('status','--porcelain','--',rel)
        purpose=MODULES.get(file.stem,'Testmodule voor '+file.stem[5:].replace('_',' ') if file.stem.startswith('test_') else 'Ondersteunende module of pakketstart. Lees de definities hieronder voor de precieze scope.')
        link='../'+rel
        lines.extend(['',f'## {rel}','',purpose,'',f'Bron: [{rel}]({link}).'+(' Lokale wijzigingen of nog niet gecommit bij het samenstellen. Deze bron is niet door het publiceren van de uitleg automatisch meegecommit.' if status else '')])
        module_doc=ast.get_docstring(tree)
        if module_doc: lines.extend(['','Broncommentaar: '+module_doc.replace('\n',' ')])
        totals['files']+=1
        def walk(body,prefix=''):
            for node in body:
                if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    # Also index definitions nested under if, try, with and loops.
                    for _,value in ast.iter_fields(node):
                        if isinstance(value,list):
                            walk([child for child in value if isinstance(child,ast.stmt)],prefix)
                        elif isinstance(value,ast.stmt):
                            walk([value],prefix)
                    continue
                fullname=prefix+node.name;isclass=isinstance(node,ast.ClassDef)
                totals['definitions']+=1;totals['classes' if isclass else 'functions']+=1
                if rel.startswith('tests/'):totals['test_definitions']+=1
                lines.extend(['',f'### {fullname}','',f'Vindplaats: [{rel} regel {node.lineno}]({link}#L{node.lineno}), tot regel {node.end_lineno}.'])
                if isclass:
                    bases=', '.join(ast.unparse(b) for b in node.bases) or 'geen expliciete basisklasse'
                    lines.append('Class die toestand of een vaste gegevensstructuur groepeert. Overerving: '+bases+'.')
                else:
                    signature=ast.unparse(node.args)
                    lines.append('Argumenten: `('+signature+')`. Retourtypehint: `'+(ast.unparse(node.returns) if node.returns else 'niet opgegeven')+'`.')
                    purpose=PURPOSES.get(node.name)
                    if node.name.startswith('test_'):purpose='Controleert het geval '+node.name[5:].replace('_',' ')+'. De test is geen onafhankelijke echte modelbenchmark.'
                    if purpose:lines.append(purpose)
                    calls=sorted({ast.unparse(n.func) for n in ast.walk(node) if isinstance(n,ast.Call)})
                    if calls:lines.append('Lees verder bij aanroepen: '+', '.join('`'+x+'`' for x in calls[:18])+(' en andere aanroepen.' if len(calls)>18 else '.'))
                    features=[]
                    for typ,label in [(ast.Return,'return'),(ast.Yield,'yield of generator'),(ast.Raise,'expliciete foutmelding'),(ast.Try,'foutafhandeling'),(ast.With,'with-context'),(ast.For,'lus'),(ast.If,'voorwaardelijke vertakking')]:
                        if any(isinstance(n,typ) for n in ast.walk(node)):features.append(label)
                    if features:lines.append('Technische leespunten: '+', '.join(features)+'.')
                docstring=ast.get_docstring(node)
                if docstring:lines.extend(['','Broncommentaar: '+docstring.replace('\n',' ')])
                if isclass:walk(node.body,fullname+'.')
                else:
                    walk(node.body,fullname+'.')
        walk(tree.body)
        definitions=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        if not definitions:lines.append('Geen eigen top-level functies of classes. Dit bestand bevat pakketinitialisatie, constanten of direct uitgevoerde scriptcode.')
    lines.extend(['','# PowerShell starters',''])
    for p in sorted((ROOT/'scripts').glob('*.ps1')):
        text=p.read_text(encoding='utf-8-sig');rel=p.relative_to(ROOT).as_posix()
        ps_purpose={'Start-Cursus':'Eenvoudige P004-route met handmatige kalibratie; CheckOnly voert geen inference uit.',
                    'Start-Wedstrijd':'Gecombineerde rolpipeline met automatische veldruntime.',
                    'Start-Spelermodel':'Start app, annotatie, validatie, training of evaluatie volgens Mode.',
                    'Setup-Persoon1':'Bereidt Pythonomgeving, PyTorch-build en appdependencies voor.',
                    'setup_tools':'Haalt FFmpeg en ffprobe naar de lokale toolmap.',
                    'Train-RollenTeams':'Start de afzonderlijke rol-/teamtraining vanuit een eerdere backbone.',
                    'Run-BallExperiment':'Stuurt een baltraining of evaluatie aan.',
                    'Start-Persoon1':'Bedient de oorspronkelijke data-/modelworkflow.',
                    'Start-FootballAnnotations':'Start de lokale voetbalannotatieworkflow.'}.get(p.stem,'Ondersteunt installatie of een specifieke lokale projectworkflow. Lees het param-blok vóór uitvoeren.')
        lines.extend([f'## {p.name}','',ps_purpose,'',f'Bron: [{rel}](../{rel}).',''])
        hashes[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    lines.extend(['','# Configuraties en datasets','',
                  'configs/models*.json kiezen gewichten, klassen en inferentie-instellingen. configs/train*.json kiezen trainingsinstellingen. configs/bytetrack.yaml kiest trackergrenzen. Selectieplannen leggen bronmomenten en subsets vast. De datasetmanifesten leggen frames, labels, bronhashes en reviewstatus vast. Deze gegevensbestanden bevatten geen Pythonfuncties, maar sturen de werking wel aan.',
                  '',f"Dekking van de Pythonindex: {totals['files']} bestanden, {totals['functions']} functies en methoden en {totals['classes']} classes. Daarvan staan {totals['test_definitions']} definities onder tests. De index wordt zonder importeren of uitvoeren van de ML-modules opgebouwd."])
    (OUT/'Functieindex.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'Bronmoment.json').write_text(json.dumps({'date':'2026-11-13','base_commit':git_output('rev-parse','HEAD'),'branch':git_output('branch','--show-current'),'scope':totals,'source_sha256':hashes,'note':'Local source snapshot; uncommitted application changes are not published by this documentation commit.'},indent=2,ensure_ascii=False),encoding='utf-8')
    return totals

def shade(cell,fill):
    prop=cell._tc.get_or_add_tcPr();e=OxmlElement('w:shd');e.set(qn('w:fill'),fill);prop.append(e)

def build_document():
    doc=Document();sec=doc.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.8);sec.left_margin=Cm(2);sec.right_margin=Cm(2)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
        sty=doc.styles[name];sty.font.name='Calibri';sty.font.color.rgb=RGBColor(0,0,0)
        if sty.element.rPr is not None:
            for item in list(sty.element.rPr):
                if item.tag==qn('w:color'):
                    for attr in ['themeColor','themeTint','themeShade']:item.attrib.pop(qn('w:'+attr),None)
    normal=doc.styles['Normal'];normal.font.size=Pt(11);normal.paragraph_format.space_after=Pt(8);normal.paragraph_format.line_spacing=1.1
    doc.styles['Title'].font.size=Pt(28)
    for name,size in [('Heading 1',22),('Heading 2',14),('Heading 3',12)]:
        doc.styles[name].font.size=Pt(size);doc.styles[name].paragraph_format.keep_with_next=True
    doc.styles['Heading 1'].paragraph_format.page_break_before=True
    doc.styles['Heading 2'].paragraph_format.space_before=Pt(12)
    for name in ['TOC 1','TOC 2','TOC 3']:
        if name not in doc.styles:
            from docx.enum.style import WD_STYLE_TYPE
            doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
        sty=doc.styles[name];sty.font.name='Calibri';sty.font.size=Pt(10)
        sty.paragraph_format.space_before=Pt(0);sty.paragraph_format.space_after=Pt(0)
        sty.paragraph_format.line_spacing=1.0
    for style in doc.styles:
        for border in list(style.element.iter(qn('w:pBdr'))):
            border.getparent().remove(border)
    # A restrained page number is useful in a long study manual.
    footer=sec.footer.paragraphs[0];footer.alignment=2
    footer.add_run('Sports Vision   ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    def inline(paragraph,text):
        for i,part in enumerate(re.split(r'`([^`]+)`',text)):
            run=paragraph.add_run(part)
            if i%2:run.font.name='Consolas';run.font.size=Pt(9)
    text=(OUT/'Studiegids.md').read_text(encoding='utf-8');lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('# '):doc.add_paragraph(line[2:],'Title')
        elif line.startswith('## '):
            p=doc.add_paragraph(line[3:],'Heading 1')
            name='chapter'+str(len([x for x in doc.paragraphs if x.style.name=='Heading 1']))
            start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(i+1));start.set(qn('w:name'),name)
            end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(i+1));p._p.insert(0,start);p._p.append(end)
        elif line.startswith('### '):doc.add_paragraph(line[4:],'Heading 2')
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                parts=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(set(x)<=set('-: ') for x in parts):rows.append(parts)
                i+=1
            table=doc.add_table(rows=0,cols=len(rows[0]));table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
            n=len(rows[0]);widths=[5.8]+[(17-5.8)/(n-1)]*(n-1)
            for column,width in zip(table.columns,widths):
                column.width=Cm(width)
            for rownum,row in enumerate(rows):
                cells=table.add_row().cells
                for col,(cell,value) in enumerate(zip(cells,row)):
                    cell.width=Cm(widths[col]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    p=cell.paragraphs[0];p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(4);p.paragraph_format.line_spacing=1.0
                    r=p.add_run(value);r.font.size=Pt(9)
                    if rownum==0:r.bold=True;shade(cell,'DCE6F1')
                    tcPr=cell._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
                    for edge in ['top','left','bottom','right']:
                        e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
                    tcPr.append(b)
                if rownum==0:
                    h=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(h)
            doc.add_paragraph();continue
        else:
            p=doc.add_paragraph();inline(p,line)
            if line.startswith('Bronnen:'):
                for r in p.runs:r.font.size=Pt(9)
        i+=1
    # Place a real, updateable table of contents after the introductory material.
    body=doc._element.body
    chapter=next(p for p in doc.paragraphs if p.style.name=='Heading 1')
    toc=OxmlElement('w:p');pr=OxmlElement('w:pPr');pagebreak=OxmlElement('w:pageBreakBefore');pr.append(pagebreak);toc.append(pr)
    r=OxmlElement('w:r');t=OxmlElement('w:t');t.text='Inhoud';r.append(t);toc.append(r);chapter._p.addprevious(toc)
    p=OxmlElement('w:p');f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'TOC \\o "1-1" \\h \\z \\u');p.append(f);chapter._p.addprevious(p)
    doc.core_properties.title='Sports Vision studiegids voor de verdediging'
    for border in list(doc._element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
    doc.core_properties.author='Andrew, Milan, Raoul en Jorre'
    doc.core_properties.subject='Projecttheorie code resultaten en oefenvragen'
    path=OUT/'Sports_Vision_Studiegids.docx';doc.save(path)
    return path

if __name__=='__main__':
    counts=make_index();output=build_document();print(json.dumps({'document':str(output),'index':counts},indent=2))
