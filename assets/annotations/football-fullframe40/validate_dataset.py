"""Verify native full images, coordinates, file mapping and temporal separation."""
import argparse
import hashlib
import math
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image
from build_dataset import read,write,digest


def validate(root,source=None,scan=False,ball_views=None):
    root=Path(root).resolve();spec=read(root/'source-annotations.json');manifest=read(root/'manifest.json');coco=read(root/'annotations.coco.json')
    frames=manifest['frames'];assert len(frames)==40
    assert len({f['frame_index'] for f in frames})==40
    assert manifest['names']==['player','ball','referee']
    assert Counter(f['split'] for f in frames)=={'train':30,'val':10}
    assert sum(not f['previously_selected_in_cropped_set'] for f in frames)==24
    old=read(root.parent/'football48'/'manifest.json') if (root.parent/'football48'/'manifest.json').exists() else None
    if old:
        prior={f['frame_index']:f['split'] for f in old['frames']}
        assert len(set(prior)&{f['frame_index'] for f in frames})==16
        assert all(f['frame_index'] not in prior or prior[f['frame_index']]==f['split'] for f in frames)
    source_by={f['frame_id']:f for f in spec['frames']};ci={im['file_name']:im['id'] for im in coco['images']};ann=defaultdict(list)
    for a in coco['annotations']:ann[a['image_id']].append(a)
    counts=Counter();kinds=Counter();groups=defaultdict(set);image_hashes=set();source_verified=0
    if source:
        import cv2
        assert digest(source)==spec['source']['sha256'];cap=cv2.VideoCapture(str(source))
    try:
        for f in frames:
            s=source_by[f['frame_id']];path=root/f['image'];assert digest(path)==f['image_sha256']
            with Image.open(path) as image:
                assert image.size==(4096,1080) and image.format=='PNG'
                rgb=image.convert('RGB').tobytes();ph=hashlib.sha256(rgb).hexdigest()
                assert ph==f['source_frame_rgb_sha256'];image_hashes.add(ph)
            assert f['preprocessing']=='none' and f['width']==4096 and f['height']==1080
            assert f['review_status']=='open' and not f['reviewer']
            if source:
                cap.set(cv2.CAP_PROP_POS_FRAMES,f['frame_index']);ok,bgr=cap.read();assert ok
                assert hashlib.sha256(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB).tobytes()).hexdigest()==ph
                source_verified+=1
            lines=(root/f['label']).read_text().splitlines();a=ann[ci[f['image']]]
            assert len(lines)==len(a)==len(s['objects']) and len(lines)==len(set(lines))
            for line,c,o in zip(lines,a,s['objects']):
                cls,x,y,w,h=map(float,line.split());assert cls==int(cls) and int(cls) in (0,1,2)
                assert all(math.isfinite(v) for v in [x,y,w,h]) and w>0 and h>0
                assert -1e-8<=x-w/2<=x+w/2<=1+1e-8 and -1e-8<=y-h/2<=y+h/2<=1+1e-8
                pixels=[(x-w/2)*4096,(y-h/2)*1080,w*4096,h*1080];x1,y1,x2,y2=o['xyxy']
                assert c['category_id']==int(cls)+1 and o['class_id']==int(cls) and c['iscrowd']==0
                assert all(abs(v-z)<.001 for v,z in zip(pixels,c['bbox']))
                assert all(abs(v-z)<.001 for v,z in zip(pixels,[x1,y1,x2-x1,y2-y1]))
                counts[manifest['names'][int(cls)]]+=1;kinds[o['kind']]+=1
            groups[f['group_id']].add(f['split'])
    finally:
        if source:cap.release()
    assert len(image_hashes)==40 and len(groups)==8 and all(len(v)==1 for v in groups.values())
    gap=min(abs(a['timestamp_s']-b['timestamp_s']) for a in frames if a['split']=='train' for b in frames if b['split']=='val');assert gap>=60
    assert kinds['in_play_ball']==37 and kinds['reserve_ball']==155
    assert counts==read(root/'summary.json')['objects']
    loader={}
    if scan:
        from ultralytics.data.dataset import YOLODataset
        from ultralytics.data.utils import check_det_dataset
        data=check_det_dataset(str(root/'data.yaml'),autodownload=False)
        for split,n in [('train',30),('val',10)]:
            ds=YOLODataset(img_path=data[split],data=data,task='detect',imgsz=2048,augment=False,cache=False)
            assert len(ds)==n
            expected=sum(len(source_by[f['frame_id']]['objects']) for f in frames if f['split']==split)
            assert sum(len(label['cls']) for label in ds.labels)==expected
            loader[split]={'images':n,'objects':expected,'corrupt_or_missing_images':0}
    views={}
    for view_path in ball_views or []:
        view=Path(view_path).resolve();metadata=read(view/'source.json');target=metadata['target'];in_play=target=='in_play_ball'
        selected=[f for f in frames if not in_play or source_by[f['frame_id']]['in_play_ball_status']=='visible_labelled']
        assert {f['frame_id'] for f in metadata['frames']}=={f['frame_id'] for f in selected}
        objects=0
        for f in selected:
            assert digest(view/f['image'])==f['image_sha256']
            expected=[a for a in source_by[f['frame_id']]['objects'] if a['class_id']==1 and (not in_play or a['kind']=='in_play_ball')]
            lines=(view/f['label']).read_text().splitlines();assert len(lines)==len(expected)
            for line,a in zip(lines,expected):
                cls,x,y,w,h=map(float,line.split());assert cls==0
                x1,y1,x2,y2=a['xyxy'];pixels=[(x-w/2)*4096,(y-h/2)*1080,w*4096,h*1080]
                assert all(abs(v-z)<.001 for v,z in zip(pixels,[x1,y1,x2-x1,y2-y1]))
            objects+=len(lines)
        if scan:
            data=check_det_dataset(str(view/'data.yaml'),autodownload=False)
            assert data['names']=={0:target}
            for split in ['train','val']:
                ds=YOLODataset(img_path=data[split],data=data,task='detect',imgsz=2048,augment=False,cache=False)
                assert len(ds)==sum(f['split']==split for f in selected)
        views[target]={'images':len(selected),'objects':objects,'splits':dict(Counter(f['split'] for f in selected)),
            'full_image_checksums_checked':len(selected),'ultralytics_loader_checked':scan}
    report={'status':'passed','frames':40,'native_size':[4096,1080],'unique_source_frames':40,'unique_pixel_hashes':40,
        'new_source_frames_vs_football48':24,'previous_source_frames_relabelled_full_size':16,'objects':dict(counts),
        'ball_kinds':{'in_play_ball':kinds['in_play_ball'],'reserve_ball':kinds['reserve_ball']},
        'splits':{'train':30,'val':10},'time_groups':8,'minimum_cross_split_gap_s':gap,
        'source_video_checksum_checked':bool(source),'full_frames_pixel_identical_to_decoded_source':source_verified,
        'coco_yolo_source_box_agreement':True,'existing_dataset_split_overlap_checked':bool(old),
        'ultralytics_loader':loader,'ball_only_exports':views,'independent_human_review_complete':False,'model_training_performed':False,
        'scope':'File and geometry checks; no human review, semantic accuracy score or independent-match test is claimed.'}
    write(root/'verification.json',report);print(report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parent));p.add_argument('--source');p.add_argument('--ultralytics-scan',action='store_true')
    p.add_argument('--ball-view',action='append',default=[])
    args=p.parse_args();validate(args.root,args.source,args.ultralytics_scan,args.ball_view)
