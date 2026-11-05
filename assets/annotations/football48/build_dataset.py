"""Recreate the fixed dataset from the original video and checked source boxes.

python assets/annotations/football48/build_dataset.py --source path/to/video.mp4
Refuses to overwrite an existing dataset. No model inference is performed.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image,ImageDraw


def read(path):
    """Lees de opgeslagen dataset- of annotatiegegevens uit UTF-8-JSON."""
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path,value):
    """Maak de uitvoermap en schrijf de datasetmetadata als leesbare UTF-8-JSON."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def digest(path):
    """Bereken de SHA-256 van het bron-, beeld- of labelbestand in blokken voor de identiteitscontrole."""
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def make_masked_crop(rgb,record,polygon):
    """Maak het vastgelegde veldmasker, herstel de geselecteerde zichtbare objecten en knip de opgeslagen
    native uitsnede zonder de pixels te herschalen.
    """
    mask=np.zeros(rgb.shape[:2],np.uint8)
    cv2.fillPoly(mask,[np.asarray(polygon,np.int32)],255)
    selected=record['person_boxes_source']
    # Remove visible fragments of out-of-zone people before restoring the
    # selected visible bodies. This is input preprocessing, not a new label.
    for box in record.get('masked_person_regions_source',[]):
        x1,y1,x2,y2=map(round,box)
        mask[max(0,y1):min(rgb.shape[0],y2+1),max(0,x1):min(rgb.shape[1],x2+1)]=0
    restore=selected+([record['ball_xyxy']] if record['ball_xyxy'] else [])
    for box in restore:
        x1,y1,x2,y2=map(round,box)
        mask[max(0,y1):min(rgb.shape[0],y2+1),max(0,x1):min(rgb.shape[1],x2+1)]=255
    masked=rgb.copy();masked[mask==0]=0
    x1,y1,x2,y2=record['crop_xyxy']
    return Image.fromarray(masked[y1:y2,x1:x2])


def export(source,output,spec):
    """Reconstrueer de vastgelegde bronframes en schrijf YOLO-labels, COCO-annotaties, voorbeelden en
    manifest met behouden klassen en splits.
    """
    source,output=Path(source),Path(output)
    if (output/'images').exists() or (output/'labels').exists():
        raise ValueError('Dataset exists; preserve saved images and labels')
    if digest(source)!=spec['source']['sha256']:
        raise ValueError('Original video checksum does not match the annotation source')
    manifest={'schema_version':'1.0','dataset_version':'football48-001','names':['person','ball'],
        'video':spec['source'],'minimum_split_gap_s':60,
        'annotation_origin':'Codex AI, pretrained-assisted and visually checked',
        'independent_human_review':False,'field_polygon_source':spec['field_polygon_source'],
        'preprocessing':'one native 1280x640 crop per unique source frame; masked background/dugout area; no image resizing',
        'frames':[]}
    coco={'info':{'description':'48 checked AI-annotated native-resolution ROI frames','independent_human_review':False},
          'images':[],'annotations':[],'categories':[{'id':1,'name':'person'},{'id':2,'name':'ball'}]}
    stats=Counter();split_stats={s:Counter() for s in ['train','val']}
    cap=cv2.VideoCapture(str(source))
    if cap.get(cv2.CAP_PROP_FPS)!=25:raise ValueError('Expected 25 fps source')
    try:
        for image_id,record in enumerate(spec['frames'],1):
            cap.set(cv2.CAP_PROP_POS_FRAMES,record['frame_index'])
            ok,bgr=cap.read()
            if not ok:raise ValueError(f"Cannot decode {record['frame_index']}")
            rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
            crop=make_masked_crop(rgb,record,spec['field_polygon_source'])
            if crop.size!=(1280,640):raise ValueError('Unexpected crop size')
            fid,split=record['frame_id'],record['split']
            image_rel=f'images/{split}/{fid}.png';label_rel=f'labels/{split}/{fid}.txt'
            image_path=output/image_rel;image_path.parent.mkdir(parents=True,exist_ok=True)
            crop.save(image_path)
            left,top,_,_=record['crop_xyxy']
            objects=[(0,box) for box in record['person_boxes_source']]
            if record['ball_xyxy']:objects.append((1,record['ball_xyxy']))
            lines=[];draw=ImageDraw.Draw(crop)
            for cls,box in objects:
                a,b,c,d=box;x1,y1,x2,y2=a-left,b-top,c-left,d-top
                if not (0<=x1<x2<=1280 and 0<=y1<y2<=640):raise ValueError((fid,box))
                lines.append(f'{cls} {(x1+x2)/2560:.8f} {(y1+y2)/1280:.8f} {(x2-x1)/1280:.8f} {(y2-y1)/640:.8f}')
                coco['annotations'].append({'id':len(coco['annotations'])+1,'image_id':image_id,'category_id':cls+1,
                    'bbox':[x1,y1,x2-x1,y2-y1],'area':(x2-x1)*(y2-y1),'iscrowd':0})
                draw.rectangle((x1,y1,x2,y2),outline='cyan' if cls==0 else 'yellow',width=2)
                if cls==1:draw.text((x1,max(0,y1-12)),'ball',fill='yellow')
                stats['person' if cls==0 else 'ball']+=1
                split_stats[split]['person' if cls==0 else 'ball']+=1
            label=output/label_rel;label.parent.mkdir(parents=True,exist_ok=True)
            label.write_text('\n'.join(lines)+('\n' if lines else ''),encoding='utf-8')
            preview=output/'previews'/f'{fid}.jpg';preview.parent.mkdir(exist_ok=True)
            crop.save(preview,quality=95)
            split_stats[split]['frames']+=1
            split_stats[split]['ball_positive' if record['ball_xyxy'] else 'ball_negative']+=1
            manifest['frames'].append({'frame_id':fid,'video_id':spec['source']['sha256'],
                'frame_index':record['frame_index'],'timestamp_s':record['timestamp_s'],
                'group_id':record['group_id'],'split':split,'width':1280,'height':640,
                'image':image_rel,'label':label_rel,'label_status':'positive' if objects else 'negative',
                'annotator':spec['annotator'],'reviewer':'','review_status':'open','ai_visual_check':True,
                'ball_presence':'visible_labelled' if record['ball_xyxy'] else 'visually_confirmed_absent_in_crop',
                'crop_xyxy_source':record['crop_xyxy'],'image_sha256':digest(image_path),
                'source_frame_rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest()})
            coco['images'].append({'id':image_id,'file_name':image_rel,'width':1280,'height':640,
                'source_frame_index':record['frame_index'],'source_crop_xyxy':record['crop_xyxy']})
    finally:cap.release()
    write(output/'manifest.json',manifest)
    write(output/'annotations.coco.json',coco)
    write(output/'summary.json',{'frames':len(spec['frames']),'objects':dict(stats),
        'splits':{s:dict(c) for s,c in split_stats.items()},'independent_human_review':False,
        'unique_source_frames':len({r['frame_index'] for r in spec['frames']}),
        'source_matches':1,'time_groups':len({r['group_id'] for r in spec['frames']})})
    (output/'data.yaml').write_text('train: images/train\nval: images/val\nnames:\n  0: person\n  1: ball\n',encoding='utf-8')
    print(dict(stats),{s:dict(c) for s,c in split_stats.items()},flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',default=str(Path(__file__).resolve().parent))
    args=parser.parse_args()
    export(args.source,args.output,read(Path(__file__).with_name('source-annotations.json')))
