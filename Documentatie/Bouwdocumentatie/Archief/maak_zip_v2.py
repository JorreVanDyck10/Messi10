"""Bouw één controleerbare momentopname. Wijzigt final niet en uploadt niets."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

DOC=Path(__file__).resolve().parents[1]
BASE=DOC.parent
FINAL=BASE/'Messi10/final'
if not FINAL.exists(): FINAL=BASE/'final'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DOC/'CV_Challenge_Messi10_ACTUEEL_17a93756.zip')
    parser.add_argument('--latest-source',type=Path,help='Map Nieuwste_bron met SOURCE_SNAPSHOT.json')
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists():raise FileExistsError('Kies een nieuwe ZIP-naam om een eerdere snapshot te bewaren.')
    required=['Rapport_Sports_Vision.pdf','Presentatie_Sports_Vision.pptx','Training_en_Resultaten.ipynb','Requirementscontrole.md']
    for name in required:
        if not (DOC/name).is_file():raise FileNotFoundError(DOC/name)
    latest=args.latest_source
    if latest is None:
        latest=next((p for p in [BASE/'Nieuwste_bron',BASE/'.documentatie_update_20261113/Nieuwste_bron'] if (p/'SOURCE_SNAPSHOT.json').is_file()),None)
    if latest is None:raise FileNotFoundError('Nieuwste_bron ontbreekt; geef --latest-source mee.')
    latest=latest.resolve()
    source_snapshot=json.loads((latest/'SOURCE_SNAPSHOT.json').read_text(encoding='utf-8'))
    original=json.loads((FINAL/'MANIFEST.json').read_text(encoding='utf-8'))
    inputs=[]
    for item in original['files']:
        path=(FINAL/item['path']).resolve()
        if not path.is_relative_to(FINAL.resolve()):raise ValueError('Onveilig pad in bestaand manifest')
        if sha(path)!=item['sha256']:raise ValueError(f"Final is gewijzigd sinds manifest: {item['path']}")
        if not item['path'].startswith('backups/'):
            inputs.append((path,'final/'+item['path'],item['sha256']))
    packaged_manifest={**original,'files':[item for item in original['files'] if not item['path'].startswith('backups/')]}
    packaged_manifest['file_count']=len(packaged_manifest['files'])
    packaged_manifest['total_bytes']=sum(item['bytes'] for item in packaged_manifest['files'])
    packaged_manifest['excluded_runtime_directories']=[*original['excluded_runtime_directories'],'backups']
    packaged_manifest['packaging_note']='Afgeleid van het ongewijzigde oorspronkelijke manifest; alleen twee backupbestanden weggelaten uit het indieningspakket.'
    packaged_manifest['source_manifest_sha256']=sha(FINAL/'MANIFEST.json')
    packaged_bytes=json.dumps(packaged_manifest,indent=2,ensure_ascii=False).encode('utf-8')
    env=FINAL/'reports/environment-local.json'
    inputs.append((env,'final/reports/environment-local.json',sha(env)))
    # Lokale veldreleasegewichten en pretrained basis die de standaardmanifest uitsluit.
    for folder in ['weights','models']:
        for path in (FINAL/folder).rglob('*'):
            if path.is_file() and not path.is_symlink():inputs.append((path,'final/'+path.relative_to(FINAL).as_posix(),sha(path)))
    for path in DOC.rglob('*'):
        if path.is_file() and path.suffix.lower() not in ['.zip','.pyc'] and '__pycache__' not in path.parts:
            inputs.append((path,'Documentatie/'+path.relative_to(DOC).as_posix(),sha(path)))
    for item in source_snapshot['files']:
        path=(latest/item['path']).resolve()
        if not path.is_relative_to(latest):raise ValueError('Onveilig pad in bronmanifest')
        if sha(path)!=item['sha256']:raise ValueError('Nieuwste bron gewijzigd: '+item['path'])
        inputs.append((path,'Nieuwste_bron/'+item['path'],item['sha256']))
    inputs.append((latest/'SOURCE_SNAPSHOT.json','Nieuwste_bron/SOURCE_SNAPSHOT.json',sha(latest/'SOURCE_SNAPSHOT.json')))
    names=[name for _,name,_ in inputs]
    if len(names)!=len(set(names)):raise ValueError('Dubbel archiefpad')
    prefix='CV_Challenge_Messi10/'
    temporary=output.with_suffix('.partial.zip')
    if temporary.exists():raise FileExistsError(temporary)
    records=[]
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
        for path,name,expected in sorted(inputs,key=lambda row:row[1]):
            # Schrijf vanuit de gelezen bytes en controleer de hash op de daadwerkelijk verpakte inhoud.
            digest=hashlib.sha256();size=0
            with path.open('rb') as src,archive.open(prefix+name,'w',force_zip64=True) as target:
                while block:=src.read(1024*1024):
                    digest.update(block);target.write(block);size+=len(block)
            if digest.hexdigest()!=expected:raise RuntimeError(f'Bron wijzigde tijdens inpakken: {name}')
            records.append({'path':name,'bytes':size,'sha256':expected})
        archive.writestr(prefix+'final/MANIFEST.json',packaged_bytes)
        records.append({'path':'final/MANIFEST.json','bytes':len(packaged_bytes),'sha256':hashlib.sha256(packaged_bytes).hexdigest()})
        entry='''SPORTS VISION - DOCUMENTATIEVERSIE 2 - GIT 17a93756

Lees Documentatie/README.md en Requirementscontrole.md.
De opdracht is gedeeltelijk aangetoond. Menselijke labelreview en een actuele
geldige statische minimapdemonstratie staan open. De nieuwste bron behoudt
volgens de gerapporteerde YOLO26-vergelijking het bestaande YOLO11s-model.
De ruwe nieuwe YOLO26- en trackingexperimentbestanden ontbreken in deze kopie.

final is het behouden oude pakket. Nieuwste_bron is de opgehaalde hoofdbron
met lokale aanvullingen, Andrew-bal en herstelbare spelersbediening.

Rapport: Documentatie/Rapport_Sports_Vision.pdf
Presentatie: Documentatie/Presentatie_Sports_Vision.pptx
Training: Documentatie/Training_en_Resultaten.ipynb en final/scripts

Start vanuit de uitgepakte final-map:
  .\\scripts\\Setup-Final.ps1
  .\\scripts\\Start-Final.ps1
Optionele baltegels: .\\scripts\\Start-Final.ps1 -BroadcastTiles

Voor de nieuwste bron, na installatie van final:
  cd ../Nieuwste_bron
  .\\Start-Nieuwste.ps1 -CheckOnly
  .\\Start-Nieuwste.ps1
Deze starter gebruikt de geinstalleerde omgeving en veldruntime van final
met de eigen nieuwste code en eigen modelprofiel. Zie het versieoverzicht.

Python 3.11 en Git aanbevolen. Eerste installatie vereist internet.
Huidige gewichten en veldreleasegewichten zijn inbegrepen. Volledige historische
trainingscorpora, lokale omgevingen en tijdelijke runs zijn niet inbegrepen.
Exacte historische hertraining vraagt de oorspronkelijke datasets/startgewichten.
Oude backupbestanden zijn weggelaten. Het manifest in deze kopie is daarvoor
afgeleid van het originele manifest; de bronmap final blijft ongewijzigd.

Niets is automatisch geüpload. Bouw na inhoudelijke wijzigingen één nieuwe ZIP.
'''
        archive.writestr(prefix+'START_HIER.txt',entry)
        snapshot={'snapshot_date':'2026-11-13','validation_date':'2026-11-14','documentation_version':2,'git_revision':source_snapshot['git_revision'],'status':'concept_with_open_requirements','source':'Preserved final plus latest main with local changes; distinct versions','original_manifest_sha256':sha(FINAL/'MANIFEST.json'),'files':records,'excluded':'runtime environments, caches, uploads, generated runs, all backups, complete historic corpora','yolo26':'Reported completed; current YOLO11s retained. Raw experiment files not available.'}
        archive.writestr(prefix+'PAKKET_MANIFEST.json',json.dumps(snapshot,indent=2,ensure_ascii=False))
    # Lees de volledige verpakte inhoud terug: CRC én SHA-256 op alle payloadbestanden.
    with zipfile.ZipFile(temporary) as archive:
        bad=archive.testzip()
        if bad:raise ValueError('CRC-fout: '+bad)
        for row in records:
            with archive.open(prefix+row['path']) as stream:
                actual=hashlib.file_digest(stream,'sha256').hexdigest()
            if actual!=row['sha256']:raise ValueError('Hashfout in ZIP: '+row['path'])
        forbidden=['/.venv/','/.tools/','/.cache/','/__pycache__/','/data/uploads/','/backups/']
        assert not any(any(part in name for part in forbidden) for name in archive.namelist())
    temporary.rename(output)
    print(json.dumps({'zip':str(output),'payload_files':len(records),'zip_bytes':output.stat().st_size,'sha256':sha(output),'validation':'All payload hashes and ZIP CRC verified'},indent=2))

if __name__=='__main__':main()
