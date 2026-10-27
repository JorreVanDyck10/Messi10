"""Export full-frame ball-only training; optionally restrict the target to match ball."""
import argparse
import os
import shutil
from pathlib import Path
from build_dataset import read,write


def create(output,in_play_only=True):
    root=Path(__file__).resolve().parent;spec=read(root/'source-annotations.json');manifest=read(root/'manifest.json')
    output=Path(output).resolve()
    if output.exists():raise ValueError('Choose a new output directory')
    by_id={f['frame_id']:f for f in spec['frames']};selected=[];counts={'train':0,'val':0}
    for f in manifest['frames']:
        source=by_id[f['frame_id']]
        if in_play_only and source['in_play_ball_status']!='visible_labelled':continue
        src=root/f['image'];dst=output/f['image'];dst.parent.mkdir(parents=True,exist_ok=True)
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
        lines=[]
        for a in source['objects']:
            if a['class_id']!=1 or (in_play_only and a['kind']!='in_play_ball'):continue
            x1,y1,x2,y2=a['xyxy'];lines.append(f'0 {(x1+x2)/8192:.9f} {(y1+y2)/2160:.9f} {(x2-x1)/4096:.9f} {(y2-y1)/1080:.9f}')
        label=output/f['label'];label.parent.mkdir(parents=True,exist_ok=True);label.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
        counts[f['split']]+=1;selected.append({'frame_id':f['frame_id'],'split':f['split'],'ball_boxes':len(lines),'image_sha256':f['image_sha256']})
    name='in_play_ball' if in_play_only else 'ball'
    (output/'data.yaml').write_text(f'train: images/train\nval: images/val\nnames:\n  0: {name}\n',encoding='utf-8',newline='\n')
    write(output/'source.json',{'dataset_version':spec['dataset_version'],'target':name,'splits':counts,'frames':selected,
        'reserve_balls_are_intentional_background':True,'independent_human_review_complete':False,'uncertain_in_play_frames_skipped':in_play_only,'images_are_unchanged_full_frames':True})
    print(output/'data.yaml',counts)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--in-play-only',action='store_true')
    args=p.parse_args();create(args.output,True)
