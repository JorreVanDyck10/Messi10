"""Verify full-frame identity, annotation exports, new source indices and splits."""
import argparse,hashlib,math
from pathlib import Path
from collections import Counter,defaultdict
from PIL import Image
from build_dataset import read,write,digest


def validate(root,source=None,scan=False):
    """Controleer beeldidentiteit, labelboxen, overeenkomst tussen YOLO en COCO en de vastgelegde bron-
    en splitvoorwaarden van deze datasetversie.
    """
    root=Path(root).resolve();spec=read(root/'source-annotations.json');m=read(root/'manifest.json');coco=read(root/'annotations.coco.json')
    names=['player','ball','referee','other_person','crowd','goal','corner_flag','stored_goals'];assert spec['names']==m['names']==names
    frames=m['frames'];assert len(frames)==100 and len({f['frame_index'] for f in frames})==100
    assert Counter(f['split'] for f in frames)=={'train':70,'val':30}
    old_indices=set();group_split={};prior_checked=[]
    for folder in ['football48','football-fullframe40','football-fullscene16','football-fullscene20','football-fullscene50','football-fullscene60','football-fullscene100']:
        prior=root.parent/folder/'manifest.json'
        if not prior.exists():continue
        for f in read(prior)['frames']:
            old_indices.add(f['frame_index']);group_split[f['group_id']]=f['split']
        prior_checked.append(folder)
    assert not old_indices&{f['frame_index'] for f in frames}
    assert all(f['group_id'] not in group_split or f['split']==group_split[f['group_id']] for f in frames)
    by_id={f['frame_id']:f for f in spec['frames']};ci={f['file_name']:f['id'] for f in coco['images']};annotations=defaultdict(list)
    for a in coco['annotations']:annotations[a['image_id']].append(a)
    groups=defaultdict(set);pixel_hashes=set();counts=Counter();kinds=Counter();source_checked=0
    if source:
        import cv2
        assert digest(source)==spec['source']['sha256'];cap=cv2.VideoCapture(str(source))
    try:
        for f in frames:
            s=by_id[f['frame_id']];path=root/f['image'];assert digest(path)==f['image_sha256']
            with Image.open(path) as im:
                assert im.size==(4096,1080) and im.format=='PNG';pixel=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
            assert pixel==f['source_frame_rgb_sha256'];pixel_hashes.add(pixel)
            assert f['preprocessing']=='none' and f['review_status']=='open' and not f['reviewer']
            if source:
                cap.set(cv2.CAP_PROP_POS_FRAMES,f['frame_index']);ok,bgr=cap.read();assert ok
                assert hashlib.sha256(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB).tobytes()).hexdigest()==pixel;source_checked+=1
            lines=(root/f['label']).read_text().splitlines();aa=annotations[ci[f['image']]]
            assert len(lines)==len(aa)==len(s['objects']) and len(lines)==len(set(lines))
            for line,a,o in zip(lines,aa,s['objects']):
                cls,x,y,w,h=map(float,line.split());assert cls==int(cls) and int(cls) in range(8)
                assert all(math.isfinite(v) for v in [x,y,w,h]) and w>0 and h>0
                assert -1e-8<=x-w/2<=x+w/2<=1+1e-8 and -1e-8<=y-h/2<=y+h/2<=1+1e-8
                pixel_box=[(x-w/2)*4096,(y-h/2)*1080,w*4096,h*1080];x1,y1,x2,y2=o['xyxy']
                assert a['category_id']==int(cls)+1 and o['class_id']==int(cls)
                assert all(abs(v-z)<.001 for v,z in zip(pixel_box,a['bbox']))
                assert all(abs(v-z)<.001 for v,z in zip(pixel_box,[x1,y1,x2-x1,y2-y1]))
                assert a['is_group']==(int(cls) in (4,7)) and a['iscrowd']==0
                if a['is_group']:assert a['member_count'] is None
                counts[names[int(cls)]]+=1;kinds[o['kind']]+=1
            assert sum(o['kind']=='in_play_ball' for o in s['objects'])==1
            per_frame=Counter(o['class_id'] for o in s['objects']);assert per_frame[5]==6 and per_frame[6]==4 and per_frame[7]==2 and per_frame[4]==3
            groups[f['group_id']].add(f['split'])
    finally:
        if source:cap.release()
    assert len(pixel_hashes)==100 and len(groups)==6 and all(len(g)==1 for g in groups.values())
    assert counts==read(root/'summary.json')['objects']
    gap=min(abs(a['timestamp_s']-b['timestamp_s']) for a in frames if a['split']=='train' for b in frames if b['split']=='val');assert gap>=60
    loader={}
    if scan:
        from ultralytics.data.dataset import YOLODataset
        from ultralytics.data.utils import check_det_dataset
        # Label-file lengths can remain unchanged after a coordinate correction.
        for folder in ['football-fullscene16','football-fullscene20','football-fullscene50','football-fullscene60','football-fullscene100',root.name]:
            for split in ['train','val']:(root.parent/folder/'labels'/f'{split}.cache').unlink(missing_ok=True)
        data=check_det_dataset(str(root/'data.yaml'),autodownload=False)
        for split in ['train','val']:
            ds=YOLODataset(img_path=data[split],data=data,task='detect',imgsz=2048,augment=False,cache=False)
            assert len(ds)==sum(f['split']==split for f in frames)
            expected=sum(len(by_id[f['frame_id']]['objects']) for f in frames if f['split']==split)
            assert sum(len(l['cls']) for l in ds.labels)==expected
            loader[split]={'images':len(ds),'objects':expected,'corrupt_or_missing_images':0}
    combined_loader={}
    if scan:
        previous=[]
        for folder in ['football-fullscene16','football-fullscene20','football-fullscene50','football-fullscene60','football-fullscene100']:
            pm=read(root.parent/folder/'manifest.json');assert pm['names']==names
            assert pm['source']['sha256']==spec['source']['sha256']
            previous.extend((root.parent/folder,f) for f in pm['frames'])
        combined_frames=frames+[f for _,f in previous]
        assert len(combined_frames)==len({f['frame_index'] for f in combined_frames})==346
        assert len({f['source_frame_rgb_sha256'] for f in combined_frames})==346
        cg=defaultdict(set)
        for f in combined_frames:cg[f['group_id']].add(f['split'])
        assert all(len(s)==1 for s in cg.values())
        gap346=min(abs(a['timestamp_s']-b['timestamp_s']) for a in combined_frames if a['split']=='train' for b in combined_frames if b['split']=='val')
        assert gap346>=60
        data=check_det_dataset(str(root/'data-combined346.yaml'),autodownload=False)
        for split,number in [('train',245),('val',101)]:
            ds=YOLODataset(img_path=data[split],data=data,task='detect',imgsz=2048,augment=False,cache=False)
            assert len(ds)==number and len({Path(p).resolve() for p in ds.im_files})==number
            expected=sum(len(by_id[f['frame_id']]['objects']) for f in frames if f['split']==split)
            expected+=sum(len((p/f['label']).read_text(encoding='utf-8').splitlines()) for p,f in previous if f['split']==split)
            assert sum(len(l['cls']) for l in ds.labels)==expected
            combined_loader[split]={'images':number,'objects':expected,'corrupt_or_missing_images':0}
    report={'status':'passed','images':100,'new_unique_source_frames':100,'native_size':[4096,1080],
        'full_frames_pixel_identical_to_decoded_source':source_checked,'source_video_checksum_checked':bool(source),
        'prior_sets_checked_for_duplicate_source_frames':prior_checked,'existing_time_group_splits_preserved':True,
        'splits':{'train':70,'val':30},'time_groups':6,'minimum_cross_split_gap_s':round(gap,3),
        'classes':dict(counts),'annotation_instances':sum(counts.values()),'kinds':dict(kinds),
        'coco_yolo_source_box_agreement':True,'ultralytics_loader':loader,'combined346_ultralytics_loader':combined_loader,
        'independent_human_review_complete':False,'model_training_performed':False,
        'scope':'Technical consistency and source identity; not an accuracy metric, guaranteed semantic completeness or independent human review. Group boxes do not assert member counts.'}
    write(root/'verification.json',report);print(report)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parent));p.add_argument('--source');p.add_argument('--ultralytics-scan',action='store_true')
    args=p.parse_args();validate(args.root,args.source,args.ultralytics_scan)
