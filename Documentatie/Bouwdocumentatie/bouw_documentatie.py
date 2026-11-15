"""Maak rapport en inspectienotebook uit lokale projectbewijzen. Geen modeltraining."""
from pathlib import Path
import sys, json, shutil, hashlib, re, collections

DOC = Path(__file__).resolve().parents[1]
ROOT = DOC.parent
FINAL = ROOT / 'Messi10' / 'final'
if not FINAL.exists():
    FINAL = ROOT / 'final'
PROJECT = FINAL.parent
WORK = ROOT.parent / '.documentatie_update_20261115' / 'build'
WORK.mkdir(parents=True,exist_ok=True)

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def evidence():
    sources = [(FINAL/'reports/broadcast-pitch-v1/frame_000075.jpg', DOC/'Trainingsbewijs/historische_demo.jpg')]
    for name, rel in [('bal-v2', 'artifacts/broadcast-ball-v2/fine-tune'),
                      ('bal-v3-freeze0','artifacts/broadcast-ball-v3/freeze-0'),
                      ('bal-v3-freeze10','artifacts/broadcast-ball-v3/freeze-10')]:
        for filename in ('args.yaml','results.csv'):
            sources.append((PROJECT / rel / filename, DOC / 'Trainingsbewijs' / name / filename))
    for name in ('assisted-label-correction.jpg','baseline-false-positive.jpg','baseline-localisation.jpg'):
        sources.append((PROJECT/'reports/ball-experiments'/name,DOC/'Trainingsbewijs/fouten'/name))
    manifest=[]
    for src,dst in sources:
        if src.is_file():
            dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():shutil.copy2(src,dst)
            if sha(src)!=sha(dst):raise ValueError(f'Gewijzigde bron: {src}')
            manifest.append({'source':str(src),'copy':str(dst.relative_to(DOC)), 'sha256':sha(dst)})
        elif not dst.exists():raise FileNotFoundError(src)
    if manifest:
        (DOC/'Trainingsbewijs/herkomst.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    opdracht=Path(r'C:\Users\steve\Downloads\CV_Challenge_2026_2027 (2).pdf')
    target=DOC/'Bronnen/CV_Challenge_2026_2027.pdf'
    target.parent.mkdir(exist_ok=True)
    if opdracht.exists() and not target.exists():shutil.copy2(opdracht,target)

def notebook():
    import nbformat as nbf
    n=nbf.v4.new_notebook()
    cells=[]
    def md(s):cells.append(nbf.v4.new_markdown_cell(s))
    def code(s):cells.append(nbf.v4.new_code_cell(s))
    md('''# Sports Vision: training en resultaten
Uitgevoerd inspectienotebook bij de documentatiesnapshot van **15 november 2026**.
Dit notebook toont de echte meegeleverde trainingslogs, datasetindeling, gewichten en ontwikkelmetrics.
Het reconstrueert geen nieuwe historische training. De modelruns zijn eerder uitgevoerd.
Versie 4 na pull naar 524d081a. De menselijke teamreview van alle 80 beelden is op 14 november geregistreerd.
De nieuwste handleiding meldt behoud van YOLO11s na de YOLO26-proef. Nieuwe cijfers zijn
bronrapportages zolang de ruwe lokale experimentmappen ontbreken.

Benodigd voor inspectie: Python 3.11 of 3.12, pandas, matplotlib, PyYAML en een Jupyter-kernel.
Alle inspectiecellen lezen lokale bestanden. De laatste trainingscel staat expliciet uit. Dit notebook publiceert geen nieuwe trainingsresultaten.''')
    code('''from pathlib import Path
import json, hashlib
import pandas as pd
import matplotlib.pyplot as plt
import yaml
from IPython.display import display, Markdown, Image

here = Path.cwd().resolve()
possibilities = [here, here / 'Documentatie', here.parent / 'Documentatie']
DOC = next(p for p in possibilities if (p / 'Rapport_Sports_Vision.md').is_file())
base = DOC.parent
FINAL = next(p for p in [base / 'final', base / 'Messi10' / 'final'] if (p/'streamlit_app.py').is_file())
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def checksum(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
print('Documentatie:', DOC)
print('Applicatie:', FINAL)
SOURCE = next(p for p in [base,base/'Messi10',base/'Nieuwste_bron'] if (p/'configs/models-broadcast.json').is_file())
print('Hoofdbron:',SOURCE)
print('Status: ontwikkelmetingen; 80 labels goedgekeurd volgens teamverklaring; geen onafhankelijke eindtest.')''')
    md('''## 1. Dataset en annotatie
De meegeleverde onderwijsselectie telt 80 beelden. Zij is een aparte reviewselectie uit bestaande
ontwikkeldata, met **48 train / 32 validatie** en gescheiden wedstrijden. De latere v2/v3-training
gebruikt 282 crops uit 132 bronbeelden. Die datasets zijn niet onderling uitwisselbaar.
Alle huidige 80 labels zijn volgens de geregistreerde teamverklaring goedgekeurd.
De labelbestanden en de 48/32-split zijn ongewijzigd. De oorspronkelijke AI/provider-herkomst blijft vermeld.
Deze registratie keurt andere historische datasets niet automatisch goed.''')
    code('''dataset = FINAL / 'datasets/school-ball80-review-v1'
manifest = read(dataset/'manifest.json')
frames = pd.DataFrame(manifest['frames'])
display(frames.groupby(['split','group_id']).size().rename('beelden').to_frame())
assert len(frames) == 80
assert frames['split'].value_counts().to_dict() == {'train':48,'val':32}
assert not (set(frames.loc[frames.split=='train','group_id']) & set(frames.loc[frames.split=='val','group_id']))
for row in manifest['frames']:
    for kind in ['image','label']:
        assert checksum(dataset/row[kind]) == row[f'initial_{kind}_sha256']
print('80 beeld-labelparen en hashes gecontroleerd; geen overlap tussen wedstrijdgroepen.')
print('Menselijke review voltooid:', manifest['human_review_completed'])
assert manifest['human_review_completed'] is True
assert all(row['review_status']=='approved' for row in manifest['frames'])
print('Registratie:',manifest['human_review_record'])
display(frames[['frame_id','split','annotator','reviewer','review_status']].head())''')
    md('''## 2. Wat de huidige app laadt
De nieuwste hoofdbron gebruikt YOLO11s-spelers, persoons-/rol-/teammodellen en uitsluitend de
baluitvoer uit Andrews YOLOv8x-vierklassencheckpoint. Het GitHub-final-pakket heeft een eigen
schoolroute. Lokale niet-gepubliceerde uitbreidingen worden niet als GitHub-functionaliteit voorgesteld.
Een SHA-256 bevestigt de identiteit van het bestand, niet de juistheid van voorspellingen.''')
    code('''profile=read(SOURCE/'configs/models-broadcast.json')
rows=[]
for model in profile['models']:
    p=(SOURCE/'configs'/model['weights']).resolve()
    actual=checksum(p)
    assert actual == model['weights_sha256']
    rows.append({'model':model['model_id'],'invoer':model['imgsz'],'confidence':model['confidence'],'NMS-IoU':model['iou'],'SHA256':actual})
display(pd.DataFrame(rows))
display(pd.DataFrame([{'onderdeel':key,'model':profile[key]['model_id']} for key in ['appearance','kit_embedding','role_context']]))''')
    md('''## 3. Historische trainingsinstellingen en loss
De oorspronkelijke args.yaml en results.csv zijn als bewijs gekopieerd. Hun bron en checksum staan in
Trainingsbewijs/herkomst.json. v2 start van F005. v3 start van v2 en vergelijkt freeze 10 en freeze 0.
v2: maximaal 12 epochs, AdamW, batch 4, invoer 640, lr0 0.0001.
v3: maximaal 16 epochs, Adam, patience 8, batch 4, invoer 640, lr0 0.0001.
De multisource-spelerconfiguratie plant maximaal 40 epochs met early stopping. De CSV bepaalt hoeveel
epochs daadwerkelijk zijn gelogd. Een lossdaling bewijst geen verbetering op ongeziene wedstrijden.''')
    code('''logs={}
settings=[]
for name in ['bal-v2','bal-v3-freeze10','bal-v3-freeze0']:
    folder=DOC/'Trainingsbewijs'/name
    cfg=yaml.safe_load((folder/'args.yaml').read_text())
    table=pd.read_csv(folder/'results.csv')
    table.columns=table.columns.str.strip()
    logs[name]=table
    settings.append({'run':name,'gepland_epochs':cfg['epochs'],'gelogde_epochs':len(table),**{k:cfg.get(k) for k in ['imgsz','batch','optimizer','lr0','freeze','patience','seed']}})
cfg=yaml.safe_load((FINAL/'reports/broadcast-pitch-v1/multisource-training-20261028.yaml').read_text())
logs['spelers-multisource']=pd.read_csv(FINAL/'reports/broadcast-pitch-v1/multisource-training-20261028.csv')
settings.append({'run':'spelers-multisource','gepland_epochs':cfg['epochs'],'gelogde_epochs':len(logs['spelers-multisource']),**{k:cfg.get(k) for k in ['imgsz','batch','optimizer','lr0','freeze','patience','seed']}})
display(pd.DataFrame(settings))''')
    code('''fig,axes=plt.subplots(2,2,figsize=(13,8))
for ax,(name,table) in zip(axes.flat,logs.items()):
    for col in ['train/box_loss','val/box_loss','train/cls_loss','val/cls_loss']:
        if col in table: ax.plot(table['epoch'],table[col],label=col)
    ax.set_title(name); ax.set_xlabel('Gelogde epoch'); ax.set_ylabel('Loss')
    ax.legend(fontsize=8); ax.grid(alpha=.2)
fig.suptitle('Werkelijke historische trainingslogs, geen nieuwe training')
plt.tight_layout(); plt.show()''')
    md('''## 4. Eerlijke vergelijking van de balmodellen
AP gebruikt confidencevloer 0.001, de tellingen confidence 0.25 en matching-IoU 0.50.
De projectevaluator gebruikt 101-punts box-AP zonder volledige COCO-crowd/ignorebehandeling.
Alle onderstaande volledige-beelden- en tegelmetingen gebruiken dezelfde 73 ontwikkelbeelden.
De scores van native crops horen bij een andere inferentieroute en worden hier niet gemengd.''')
    code('''v2=read(FINAL/'reports/broadcast-data/v2-experiment.json')
v3=read(FINAL/'reports/broadcast-data/v3-experiment.json')
chosen=v3['selected_candidate']
measurements=[('F005 volledig 1280',v2['baseline']['full']),('v2 volledig 1280',v2['candidate']['full']),('F005 tegels',v2['baseline']['tiled']),('v2 tegels',v2['candidate']['tiled']),('v3 tegels',v3['candidates'][chosen]['measurements']['tiled']),('v3 volledig 1280',v3['candidates'][chosen]['measurements']['full'])]
rows=[]
for name,m in measurements:
    c=m['per_class'][0]
    rows.append({'modelroute':name,'beelden':m['frames'],'AP50_%':100*m['mAP50'],'AP50_95_%':100*m['mAP50_95'],**{k:c[k] for k in ['TP','FP','FN']}})
ball_results=pd.DataFrame(rows)
display(ball_results.round(2))
assert chosen=='freeze-0'
assert checksum(FINAL/'artifacts/broadcast-ball-v3/broadcast_ball_v3.pt')==v3['candidates'][chosen]['weights_sha256']
print('Geselecteerde v3:',chosen)
print('v3 verbetert de tegelroute, maar is zonder tegels zwakker dan v2.')''')
    code('''ax=ball_results.iloc[[2,3,4]].plot.bar(x='modelroute',y=['AP50_%','AP50_95_%'],color=['#16836a','#18324f'],figsize=(9,4),rot=0)
ax.set_ylabel('AP (%)'); ax.set_title('Dezelfde 73 ontwikkelbeelden met 640-tegels')
ax.set_ylim(0,100); ax.grid(axis='y',alpha=.2)
plt.tight_layout();plt.show()''')
    md('''## 5. Spelers en teams, conditionele evaluatie
Het geselecteerde broadcastmodel gebruikt **341 evalueerbare frames** met providergeometrie.
Deze evaluatie meet de automatische veldnauwkeurigheid niet. Het hoge aandeel correcte teamlabels
onder toegewezen gematchte spelers omvat gemiste spelers niet. Keeperteams blijven een zwak punt.''')
    code('''summary=read(FINAL/'reports/broadcast-pitch-v1/summary.json')
c=summary['candidates'][summary['selected']]
metrics=c['player_detection_and_roles']; t=c['teams']
display(pd.DataFrame([{'kandidaat':summary['selected'],'frames':c['frames'],'AP50_%':100*metrics['mAP50'],'AP50_95_%':100*metrics['mAP50_95'],'geometrie':summary['geometry_kind']}]))
display(pd.DataFrame([{k:t[k] for k in ['matched_players','correct','wrong','unknown','missed_players','false_positive_players','goalkeepers_total','goalkeepers_matched','goalkeepers_correct_team']}]))
print('Teamjuistheid toegewezen gematchte spelers:',round(100*t['accuracy_assigned'],2),'%')
print('Correct team over alle spelerreferenties:',round(100*t['correct_fraction_all_players'],2),'%')
print('Targets gehaald:',summary['targets_met'],'Menselijke review:',summary['human_review_completed'])''')
    md('''## 6. Softwaretests zijn geen nauwkeurigheidsmeting
De cijfers hieronder komen uit eerdere herstelcontroles van 13 november. Dit notebook voert die
volledige testsuite niet opnieuw uit. Drie echte korte runs hebben gezamenlijk **0/36** bruikbare
automatische kalibraties. Daardoor is een juiste actuele minimap of afstand niet aangetoond.''')
    code('''checks=read(FINAL/'reports/herstel-controles.json')
display(pd.DataFrame([checks['software_tests']]))
runs=pd.DataFrame(checks['real_gpu_runs'])
display(runs[['frames','tracker','teams','ball_tiles','calibration_usable_fraction']])
assert runs['frames'].sum()==36 and runs['calibration_usable_fraction'].sum()==0
print(checks['field_quality_limitation'])''')
    md('''## 7. Concrete historische annotatiefout
Het oorspronkelijke voorstel omvatte een schoen. AI beperkte in frame 2525 de box van
`[1409,356,12,10]` naar `[1413,355,9,9]` in x/y/breedte/hoogte. Dit is een AI-correctie,
geen bewijs van een uitgevoerde menselijke review. De bijlage is ongewijzigd gekopieerd.''')
    code("display(Image(filename=str(DOC/'Trainingsbewijs/fouten/assisted-label-correction.jpg'),width=900))")
    md('''## 8. Historische training opnieuw uitvoeren
De echte scripts staan onder final/scripts en src/football_pipeline. Voor exacte v3-herhaling zijn
de oorspronkelijke `data/broadcast-training-v2` (ball-coco én balls),
`data/broadcast-ball-review-v1/curated` en `artifacts/broadcast-ball-v2/broadcast_ball_v2.pt` nodig.
Deze volledige corpora en v2-startgewichten ontbreken in het compacte apppakket.
De 80 reviewbeelden zijn geen vervangende dataset met dezelfde historische scores.

Vanuit een complete oorspronkelijke projectkopie gebruikt de historische route:
```powershell
$env:PYTHONPATH = 'src;.'
.\\.venv\\Scripts\\python.exe scripts/experiment_broadcast_v3.py --output artifacts/bal-v3-herhaling-nieuw
```
Bewaar een nieuwe outputmap. Controleer eerst fingerprints, CUDA, gewichten en dependencies.
De oorspronkelijke args.yaml bevat absolute machinepaden als herkomstbewijs, niet als universele paden.

## 9. Eventuele nieuwe training op de gereviewde 80 beelden
De volgende cel staat uit. Zij is **nieuwe training**, geen reconstructie van de historische v2/v3-run.
De menselijke review is nu geregistreerd. Bij toekomstige labelcorrecties maakt het team een
nieuwe datasetversie; bij ongewijzigde goedkeuring bewaart het de bestaande labels en reviewregistratie. De cel start alleen na expliciete wijziging
van de schakelaar en ingevulde paden. Zij kiest bewust geen onbevestigd YOLO26-model.''')
    code('''RUN_NEW_TRAINING=False
REVIEWED_MANIFEST=None  # Pad naar een nieuwe, werkelijk gereviewde datasetversie.
DATA_YAML=None          # De bijbehorende train/val-configuratie.
START_WEIGHTS=None      # Expliciet gekozen checkpoint; noteer SHA-256 en libraryversie.
if RUN_NEW_TRAINING:
    assert all(x is not None for x in [REVIEWED_MANIFEST,DATA_YAML,START_WEIGHTS]), 'Vul echte paden in.'
    reviewed=read(REVIEWED_MANIFEST)
    assert reviewed.get('human_review_completed') is True, 'Menselijke review is nog open.'
    output=FINAL/'artifacts/nieuwe-gereviewde-baltraining'
    assert not output.exists(), 'Kies een nieuwe uitvoermap.'
    from ultralytics import YOLO
    model=YOLO(str(START_WEIGHTS))
    model.train(data=str(Path(DATA_YAML).resolve()),epochs=16,imgsz=640,batch=4,
                optimizer='Adam',lr0=0.0001,freeze=0,patience=8,seed=42,
                mosaic=0.0,mixup=0.0,scale=0.0,fliplr=0.5,
                project=str(output.parent),name=output.name,exist_ok=False)
    result=model.val(data=str(Path(DATA_YAML).resolve()),split='val',imgsz=640)
    print('Nieuwe ontwikkelmetrics:',result.box.map50,result.box.map)
else:
    print('Geen training gestart. De 80-labelreview is geregistreerd; concrete trainingskoppeling en ruwe nieuwe experimentbijlagen blijven open.')''')
    md('''## 10. Wat het team zelfstandig moet uitleggen
Hoe de eigen labels invloed hebben op kleine-objecttraining, waarom buurframes niet over splits
horen, wat beide AP-maten betekenen, hoe de freezeproef is opgezet en waarom v3 bij tegels hoort.
Daarnaast: minimaal vier veldpunten, grondcontact in plaats van boxcentrum, ongeldige kalibratie,
tijdelijke ID's en de beperkingen van team- en afstandsschattingen.

Lees ook Requirementscontrole.md, GenAI_en_Eigenaarschap.md en YOLO26_Vervolg.md.
Dit notebook en de uitleg zijn met Codex-hulp gemaakt. Er is geen menselijke review nagebootst.''')
    md('''## 11. Nieuwste Git-versie en verschil met final
De pull bracht de gedeelde hoofdbron op **524d081a**. De nieuwe bron bevat ook de geregistreerde
teamreview in final en Jorres technische afronding. De GitHub-final-versie heeft een schoolroute.
De nieuwste bron gebruikt Andrew voor de bal en heeft een herstelbare spelersdrempel.
De gekopieerde handleidingen/configuraties zijn hieronder op hun opgeslagen hash gecontroleerd.
De bronkopie in de ZIP staat onder Nieuwste_bron. In deze workspace staat zij onder Messi10.''')
    code('''version=read(DOC/'Versiebewijs/repository-versie.json')
print('Git-versie:',version['revision'])
print(version['source_scope'])
for row in version['copied_evidence']:
    assert checksum(DOC/'Versiebewijs'/row['path'])==row['sha256']
latest_profile=read(DOC/'Versiebewijs/configs/models-broadcast.json')
display(pd.DataFrame([{'model':m['model_id'],'invoer':m['imgsz'],'confidence':m['confidence'],'klassen':str(m['class_mapping'])} for m in latest_profile['models']]))
latest_root=next((p for p in [base,base/'Nieuwste_bron',base/'Messi10'] if (p/'configs/models-broadcast.json').exists()),None)
if latest_root is not None:
    andrew=(latest_root/'configs'/latest_profile['models'][-1]['weights']).resolve()
    assert checksum(andrew)==latest_profile['models'][-1]['weights_sha256']
    print('Andrew-gewicht gecontroleerd:',andrew.stat().st_size,'bytes')
print('Bewaarde final-modellen:',[m['model_id'] for m in profile['models']])
print('Hoofdbron en GitHub-final hebben verschillende startprocedures. Raadpleeg de README van de gekozen versie.')''')
    md('''## 12. YOLO26-uitkomst volgens de opgehaalde handleiding
De tabel gebruikt **bronrapportages**, niet de ruwe comparison.json of een nieuwe modelrun.
Die lokale experimentmap is niet meegecommit en ontbreekt hier. De bestaande YOLO11s blijft gekozen.
De scores gebruiken ontwikkelvalidatie, één seed, 348 detectorbeelden en 341 pipelinebeelden.
F1 middelt over drie wedstrijden. Binnen 0,5 procentpunt bepaalt detectorstacktijd de voorkeur.
De tijden bevatten geen decoding, rol/teamclassificatie of veldherkenning en zijn geen video-FPS.
Nieuwe exacte AP-getallen zijn niet uit de bron beschikbaar en worden niet ingevuld.''')
    code('''yolo26_reported=pd.DataFrame(version['yolo26_rows'])
display(yolo26_reported)
display(Markdown('**Bron:** Versiebewijs/docs/Yolo26_Spelersvergelijking.md. Ruwe lokale metingen ontbreken.'))
print('Gerapporteerde keuze: huidig YOLO11s behouden; Andrew alleen voor bal.')
print('Volgens handleiding: YOLO26 stopt epoch 24 (beste 4), YOLO11 epoch 31 (beste 11).')
print('Nieuwe training begon na OOM opnieuw op 1280. Geen nieuwe AP-resultaten hier herberekend.')''')
    md('''## 13. Tracking volgens de opgehaalde handleiding
Ook dit is een bronrapportage; de lokale ruwe auditmap ontbreekt. Drie clips bevatten elk 150
opeenvolgende gelabelde ontwikkelframes met providergeometrie. De totale IDF1 is een gerapporteerde
aggregatie en mag niet worden vervangen door het gemiddelde van de drie percentages.
Deze meting hoort bij de nieuwste hoofdbron en geldt niet automatisch voor de bewaarde final.''')
    code('''display(pd.DataFrame(version['tracking_rows']))
display(pd.DataFrame([version['tracking_aggregate']]))
print('Bron: Versiebewijs/docs/Spelersdrempel_en_tracking.md; ruwe auditmap ontbreekt.')
print('Huidige lokale documentatiecontrole: 75 gerichte regressietests geslaagd; gedeelde CPU-controle meldt 537 + 4 subtests en 1 GPU-skip.')
print('Geen nieuwe volledige echte videorun en geen nieuwe training uitgevoerd.')''')
    md("""## 14. Andrews model, prototype en AI-verantwoording
De bron is docs/VierKlassenModel.md, met AI-gebruik in hoofdstuk 16, plus het oorspronkelijke
trainingsnotebook. Het model traint vier klassen, het oorspronkelijke deploymentprototype toont
bal en scheidsrechters en de gedeelde broadcastpipeline gebruikt alleen de baluitvoer.
De eigen extrapolatie en greedy matching uit Andrews prototype zijn geen ByteTrack of automatisch
een Kalmanfilter. Zijn AI-verklaring noemt documentstructuur, eerste codeonderdelen en debugging,
met handmatige beoordeling en verantwoordelijkheid bij de auteur. Toolnamen/model-ID's zijn niet ingevuld.
""")
    code("""original=read(DOC/'Versiebewijs/Andrew_Prototype/train.ipynb')
for cell in original['cells']:
    source=''.join(cell['source'])
    if cell['cell_type']=='code' and 'model.train(' in source:
        print(source)
review=read(DOC/'Versiebewijs/final/datasets/school-ball80-review-v1/manifest.json')
print('Teamreview:',review['human_review_completed'],len(review['frames']),'beelden')
print('Voorbereiding en labels behouden; registratie is geen nieuwe training.')
shared=read(DOC/'Versiebewijs/reports/release-20261114/checks.json')
display(pd.DataFrame([shared['tests']]))
print('Broncontrole van Jorre; niet als dezelfde run opgeteld bij de lokale 75 tests.')""")
    n.cells=cells
    n.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}}
    path=DOC/'Training_en_Resultaten.ipynb'
    nbf.write(n,path)
    # Execute read-only cells in process; capture real outputs including the figures.
    from IPython.core.interactiveshell import InteractiveShell
    import contextlib, io, base64
    shell=InteractiveShell.instance()
    import matplotlib
    matplotlib.use('Agg')
    scope={}
    import os
    old=os.getcwd();os.chdir(DOC)
    try:
        for cell in n.cells:
            if cell.cell_type!='code':continue
            captured=[]
            def display_obj(obj):
                data={}
                if isinstance(obj, pd.DataFrame):data={'text/html':obj.to_html(index=False),'text/plain':obj.to_string(index=False)}
                elif getattr(obj,'data',None) is not None and getattr(obj,'format',None) in ('jpeg','jpg','png'):
                    fmt='image/png' if obj.format=='png' else 'image/jpeg'
                    data={fmt:base64.b64encode(obj.data).decode(),'text/plain':'Afbeelding uit oorspronkelijk bewijs'}
                elif hasattr(obj,'_repr_png_') and obj._repr_png_() is not None:
                    raw=obj._repr_png_()
                    if isinstance(raw,tuple):raw=raw[0]
                    data={'image/png':base64.b64encode(raw).decode(),'text/plain':'Afbeelding uit oorspronkelijk bewijs'}
                else:data={'text/plain':str(obj)}
                captured.append(nbf.v4.new_output('display_data',data=data))
            import pandas as pd
            from unittest.mock import patch
            import matplotlib.pyplot as plt
            def show():
                for number in plt.get_fignums():
                    fig=plt.figure(number);buf=io.BytesIO();fig.savefig(buf,format='png',dpi=110,bbox_inches='tight')
                    captured.append(nbf.v4.new_output('display_data',data={'image/png':base64.b64encode(buf.getvalue()).decode(),'text/plain':'Grafiek uit echte trainingslogs'}))
                plt.close('all')
            out=io.StringIO()
            with patch('IPython.display.display',display_obj),patch.object(plt,'show',show),contextlib.redirect_stdout(out):
                exec(compile(cell.source,'notebook','exec'),scope)
            if out.getvalue():captured.append(nbf.v4.new_output('stream',name='stdout',text=out.getvalue()))
            cell.outputs=captured
            cell.execution_count=sum(c.cell_type=='code' and c.get('execution_count') is not None for c in n.cells)+1
    finally:os.chdir(old)
    nbf.validate(n)
    nbf.write(n,path)
    print('Notebook:',len([c for c in n.cells if c.cell_type=='code']),'cellen uitgevoerd, geen training gestart')

def pdf():
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from xml.sax.saxutils import escape
    fontdir=Path('C:/Windows/Fonts')
    for name,file in [('Body','calibri.ttf'),('Body-Bold','calibrib.ttf'),('Body-Italic','calibrii.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=10.4,leading=14.4,spaceAfter=7,textColor=colors.HexColor('#263746')))
    styles.add(ParagraphStyle(name='H1x',fontName='Body-Bold',fontSize=20,leading=24,spaceBefore=16,spaceAfter=10,textColor=colors.HexColor('#143a48'),keepWithNext=True))
    styles.add(ParagraphStyle(name='H2x',fontName='Body-Bold',fontSize=13,leading=17,spaceBefore=12,spaceAfter=7,textColor=colors.HexColor('#15725f'),keepWithNext=True))
    styles.add(ParagraphStyle(name='Cell',parent=styles['Text'],fontSize=8.4,leading=11,spaceAfter=0))
    styles.add(ParagraphStyle(name='CodeX',fontName='Courier',fontSize=8,leading=11,spaceAfter=2,backColor=colors.HexColor('#edf3f3')))
    styles.add(ParagraphStyle(name='CaptionX',fontName='Body-Italic',fontSize=9,leading=12,spaceAfter=12,textColor=colors.HexColor('#566876')))
    def rich(s):
        s=escape(s)
        s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
        s=re.sub(r'`([^`]+)`',r'<font color="#15725f">\1</font>',s)
        return s
    story=[]
    story.extend([Spacer(1,75),Paragraph('CV CHALLENGE 2026-2027',styles['H2x']),Spacer(1,15),Paragraph('Sports Vision &amp;<br/>Tactical Mapping',ParagraphStyle(name='Cover',fontName='Body-Bold',fontSize=34,leading=39,textColor=colors.HexColor('#143a48'))),Spacer(1,24),Paragraph('Projectrapport met bijdragen van Milan, Andrew en Jorre',styles['H1x']),Paragraph('Andrew, Milan Wouters, Raoul en Jorre<br/>Versie 4 - 15 november 2026<br/>Broncommit 524d081a',styles['Text']),Spacer(1,35),Paragraph('Bijgewerkt met Milans persoonlijke bijdrage en AI-gebruik, Andrews oorspronkelijke model en Jorres uploadpakket en presentatie. De menselijke review van alle 80 labels is geregistreerd. Open bewijs- en opleverpunten blijven herkenbaar.',styles['Text']),Spacer(1,30),Paragraph('Persoonlijke bijdrage Milan Wouters en AI-gebruik opgenomen; overige bijdragen volgen de aangeleverde bronnen.',styles['CaptionX']),PageBreak()])
    text=(DOC/'Rapport_Sports_Vision.md').read_text(encoding='utf-8')
    text=text[text.index('## 1. Samenvatting'):]
    lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('```'):
            i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):
                story.append(Paragraph(escape(lines[i]).replace(' ','&#160;'),styles['CodeX']));i+=1
            story.append(Spacer(1,7));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                vals=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',v) for v in vals):rows.append(vals)
                i+=1
            cols=len(rows[0]);widths={2:[105,390],3:[100,190,205],4:[65,130,150,150],6:[220,55,65,40,65,40]}.get(cols,[495/cols]*cols)
            values=[[Paragraph(rich(v),styles['Cell']) for v in row] for row in rows]
            table=Table(values,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebe6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#15725f')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f6')])]))
            story.extend([table,Spacer(1,12)]);continue
        if line.startswith('!['):
            m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
            if m:
                path=(DOC/m[2]).resolve()
                if not path.exists() and '../Messi10/final/' in m[2]:path=FINAL/m[2].split('../Messi10/final/',1)[1]
                w,h=ImageReader(str(path)).getSize();factor=min(495/w,210/h)
                story.append(KeepTogether([Image(str(path),width=w*factor,height=h*factor),Spacer(1,5),Paragraph(rich(m[1]),styles['CaptionX'])]))
            i+=1;continue
        if line.startswith('### '):
            if line.startswith('### Aanvullende figuren'):story.append(PageBreak())
            story.append(Paragraph(rich(line[4:]),styles['H2x']));i+=1;continue
        if line.startswith('## '):
            if line.startswith('## Bronnen'):story.append(PageBreak())
            story.append(Paragraph(rich(line[3:]),styles['H1x']));i+=1;continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','![')):
            para.append(lines[i].strip());i+=1
        story.append(Paragraph(rich(' '.join(para)),styles['Text']))
    def page(canvas,doc):
        canvas.saveState();canvas.setFont('Body',8);canvas.setFillColor(colors.HexColor('#607780'))
        canvas.drawString(50,815,'SPORTS VISION / TEAM MESSI10')
        canvas.drawString(50,26,'Versie 4 - 15 november 2026 - Git 524d081a - teamreview geregistreerd')
        canvas.drawRightString(545,26,str(doc.page));canvas.restoreState()
    dest=DOC/'Rapport_Sports_Vision.pdf'
    SimpleDocTemplate(str(dest),pagesize=(595.28,841.89),leftMargin=50,rightMargin=50,topMargin=51,bottomMargin=48,title='Sports Vision & Tactical Mapping',author='Team Messi10; documentatie met Codex-hulp').build(story,onFirstPage=page,onLaterPages=page)
    print('PDF:',dest)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    evidence();notebook();pdf()
