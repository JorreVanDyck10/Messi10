"""Reproduce full, untouched frames and saved annotations from the source video."""
import argparse
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
import cv2
from PIL import Image,ImageDraw


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def export(source,output,spec):
    output=Path(output)
    if (output/'images').exists() or (output/'labels').exists():raise ValueError('Choose a new output directory')
    if digest(source)!=spec['source']['sha256']:raise ValueError('Source checksum mismatch')
    names=spec['names'];manifest={k:spec[k] for k in ['schema_version','dataset_version','source','names','preprocessing','independent_human_review_complete']}
    manifest.update(video=spec['source'],minimum_split_gap_s=60,frames=[])
    coco={'info':{'description':'Full original panorama frames; AI-assisted annotations, human review open'},
        'images':[],'annotations':[],'categories':[{'id':i+1,'name':name} for i,name in enumerate(names)]}
    counts=Counter();splits=defaultdict(Counter);cap=cv2.VideoCapture(str(source))
    try:
        for image_id,f in enumerate(spec['frames'],1):
            cap.set(cv2.CAP_PROP_POS_FRAMES,f['frame_index']);ok,bgr=cap.read()
            if not ok:raise ValueError(f"Cannot decode frame {f['frame_index']}")
            rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
            if rgb.shape!=(1080,4096,3):raise ValueError('Expected the full 4096x1080 source frame')
            fid,split=f['frame_id'],f['split'];image_rel=f'images/{split}/{fid}.png';label_rel=f'labels/{split}/{fid}.txt'
            path=output/image_rel;path.parent.mkdir(parents=True,exist_ok=True)
            image=Image.fromarray(rgb);image.save(path)
            # Draw only on a separate preview, never on the training input.
            preview=image.copy();draw=ImageDraw.Draw(preview);lines=[]
            for a in f['objects']:
                cls=a['class_id'];x1,y1,x2,y2=a['xyxy']
                if not (cls in range(3) and 0<=x1<x2<=4096 and 0<=y1<y2<=1080):raise ValueError((fid,a))
                lines.append(f'{cls} {(x1+x2)/8192:.9f} {(y1+y2)/2160:.9f} {(x2-x1)/4096:.9f} {(y2-y1)/1080:.9f}')
                color=['cyan','yellow','magenta'][cls];draw.rectangle((x1,y1,x2,y2),outline=color,width=2)
                if cls==1:draw.text((x1,max(0,y1-12)),'ball',fill=color)
                coco['annotations'].append({'id':len(coco['annotations'])+1,'image_id':image_id,'category_id':cls+1,
                    'bbox':[x1,y1,x2-x1,y2-y1],'area':(x2-x1)*(y2-y1),'iscrowd':0,'kind':a['kind']})
                counts[names[cls]]+=1;splits[split][names[cls]]+=1
                if cls==1:splits[split][a['kind']]+=1
            label=output/label_rel;label.parent.mkdir(parents=True,exist_ok=True);label.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
            pp=output/'previews'/f'{fid}.jpg';pp.parent.mkdir(exist_ok=True);preview.thumbnail((2048,540));preview.save(pp,quality=90)
            splits[split]['images']+=1
            manifest['frames'].append({k:f[k] for k in ['frame_id','frame_index','timestamp_s','group_id','split','annotator','reviewer','review_status','previously_selected_in_cropped_set','visual_check','unresolved_regions','in_play_ball_status']}|
                {'video_id':spec['source']['sha256'],'width':4096,'height':1080,'image':image_rel,'label':label_rel,'label_status':'positive',
                 'image_sha256':digest(path),'source_frame_rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),'preprocessing':'none'})
            coco['images'].append({'id':image_id,'file_name':image_rel,'width':4096,'height':1080,'source_frame_index':f['frame_index'],'split':split})
            print(fid,len(lines),'boxes',flush=True)
    finally:cap.release()
    write(output/'manifest.json',manifest);write(output/'annotations.coco.json',coco)
    write(output/'summary.json',{'images':len(spec['frames']),'unique_source_frames':len({f['frame_index'] for f in spec['frames']}),
        'new_source_frames_vs_football48':sum(not f['previously_selected_in_cropped_set'] for f in spec['frames']),
        'objects':dict(counts),'splits':{s:dict(c) for s,c in splits.items()},'native_size':[4096,1080],
        'preprocessing':'none','independent_human_review_complete':False,'model_training_performed':False})
    (output/'data.yaml').write_text('train: images/train\nval: images/val\nnames:\n  0: player\n  1: ball\n  2: referee\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default=str(Path(__file__).resolve().parent))
    args=p.parse_args();export(args.source,args.output,read(Path(__file__).with_name('source-annotations.json')))
