"""Check the actual exported images, YOLO labels, COCO and temporal split.

This checks file consistency. It does not grant independent annotation review
or measure the performance of a trained detector.
"""
import argparse
import hashlib
import json
import math
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image
from build_dataset import digest,read,write


def validate(root,ball_only=None,scan=False,clips=None):
    root=Path(root).resolve();manifest=read(root/'manifest.json');spec=read(root/'source-annotations.json')
    frames=manifest['frames'];assert len(frames)==48
    assert len({r['frame_index'] for r in frames})==48
    assert len({r['source_frame_rgb_sha256'] for r in frames})==48
    assert Counter(r['split'] for r in frames)=={'train':36,'val':12}
    source={r['frame_id']:r for r in spec['frames']}
    coco=read(root/'annotations.coco.json');ci={r['file_name']:r['id'] for r in coco['images']}
    ca=defaultdict(list)
    for a in coco['annotations']:ca[a['image_id']].append(a)
    counts=Counter();groups=defaultdict(set);pixel_hashes=defaultdict(set);balls=Counter()
    for f in frames:
        s=source[f['frame_id']];groups[f['group_id']].add(f['split'])
        assert f['crop_xyxy_source']==s['crop_xyxy']
        image_path=root/f['image'];assert digest(image_path)==f['image_sha256']
        with Image.open(image_path) as image:
            assert image.size==(1280,640)
            pixel_hashes[hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()].add(f['split'])
        lines=(root/f['label']).read_text().splitlines();ann=ca[ci[f['image']]]
        assert len(lines)==len(ann)
        expected=[(0,b) for b in s['person_boxes_source']]+ ([(1,s['ball_xyxy'])] if s['ball_xyxy'] else [])
        assert len(expected)==len(lines)
        for line,a,(cls,box) in zip(lines,ann,expected):
            c,x,y,w,h=map(float,line.split());assert c==int(c) and int(c) in (0,1)
            assert all(math.isfinite(v) for v in [x,y,w,h])
            assert w>0 and h>0 and -1e-7<=x-w/2<=x+w/2<=1+1e-7 and -1e-7<=y-h/2<=y+h/2<=1+1e-7
            pixels=[(x-w/2)*1280,(y-h/2)*640,w*1280,h*640]
            assert a['category_id']==int(c)+1 and a['iscrowd']==0
            assert all(abs(v-z)<.001 for v,z in zip(pixels,a['bbox']))
            left,top,_,_=s['crop_xyxy'];x1,y1,x2,y2=box
            assert cls==int(c) and all(abs(v-z)<.001 for v,z in zip(pixels,[x1-left,y1-top,x2-x1,y2-y1]))
            counts['person' if c==0 else 'ball']+=1
        presence=sum(line.startswith('1 ') for line in lines)
        assert presence==int(s['ball_xyxy'] is not None)
        balls['positive' if presence else 'negative']+=1
        assert f['ai_visual_check'] and not f['reviewer'] and f['review_status']=='open'
        if ball_only:
            other=Path(ball_only);assert digest(other/f['image'])==f['image_sha256']
            expected_ball=['0 '+line[2:] for line in lines if line.startswith('1 ')]
            assert (other/f['label']).read_text().splitlines()==expected_ball
    assert len(groups)==8 and all(len(splits)==1 for splits in groups.values())
    assert all(len(splits)==1 for splits in pixel_hashes.values())
    assert len(pixel_hashes)==48
    assert balls=={'positive':36,'negative':12}
    gap=min(abs(a['timestamp_s']-b['timestamp_s']) for a in frames if a['split']=='train' for b in frames if b['split']=='val')
    assert gap>=60
    loader={}
    if scan:
        from ultralytics.data.dataset import YOLODataset
        from ultralytics.data.utils import check_det_dataset
        for name,base in [('joint',root)]+([('ball_only',Path(ball_only).resolve())] if ball_only else []):
            data=check_det_dataset(str(base/'data.yaml'),autodownload=False)
            loader[name]={}
            for split in ['train','val']:
                ds=YOLODataset(img_path=data[split],data=data,task='detect',imgsz=1280,augment=False,cache=False)
                assert len(ds)==(36 if split=='train' else 12)
                assert sum(len(label['cls']) for label in ds.labels)==sum(len((base/f['label']).read_text().splitlines()) for f in frames if f['split']==split)
                loader[name][split]={'images':len(ds),'objects':sum(len(label['cls']) for label in ds.labels)}
    clip_checks={}
    if clips:
        import cv2
        clip_root=Path(clips);clip_manifest=read(clip_root/'manifest.json')
        assert clip_manifest['source']['sha256']==spec['source']['sha256']
        assert len(clip_manifest['clips'])==8
        covered=[]
        for clip in clip_manifest['clips']:
            path=clip_root/clip['file'];assert digest(path)==clip['sha256']
            cap=cv2.VideoCapture(str(path))
            assert round(cap.get(cv2.CAP_PROP_FRAME_COUNT))==500 and cap.get(cv2.CAP_PROP_FPS)==25
            assert [round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]==[4096,1080]
            cap.release()
            for f in clip['selected_frames']:
                s=source[f['frame_id']];assert s['split']==clip['split'] and s['group_id']==clip['group_id']
                assert abs(s['timestamp_s']-clip['source_start_s']-f['clip_time_s'])<1e-6 and 0<=f['clip_time_s']<20
                covered.append(f['frame_id'])
        assert len(covered)==48 and set(covered)==set(source)
        clip_checks={'clips':8,'duration_each_s':20,'frames_each':500,'fps':25,'size':[4096,1080],'checksums_checked':8,'dataset_frames_covered':48}
    report={'status':'passed','frames':48,'unique_source_frames':48,'unique_input_pixel_hashes':48,
        'splits':{'train':36,'val':12},'time_groups':8,'minimum_cross_split_gap_s':gap,'objects':dict(counts),
        'ball_presence':dict(balls),'image_hashes_checked':48,'coco_yolo_source_box_agreement':True,
        'ball_only_export_checked':bool(ball_only),'ultralytics_loader':loader,'reference_clip_checks':clip_checks,
        'independent_human_review_complete':False,'model_training_performed':False,
        'scope':'File integrity, coordinates, class mapping, actual images and temporal separation; no semantic accuracy metric or independent-match test.'}
    write(root/'verification.json',report);print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parent))
    p.add_argument('--ball-only');p.add_argument('--ultralytics-scan',action='store_true')
    p.add_argument('--clips')
    args=p.parse_args();validate(args.root,args.ball_only,args.ultralytics_scan,args.clips)
