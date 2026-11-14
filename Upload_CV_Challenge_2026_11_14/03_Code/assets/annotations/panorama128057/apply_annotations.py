"""Reproduce the saved, visually corrected AI annotations, without model inference.

Run from the repository root. Refuses to overwrite any saved annotation.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from PIL import Image, ImageDraw
from persoon1.annotation import save_annotation
from persoon1.core import now, read_json, write_json

root = Path(__file__).resolve().parent
manifest_path = root / 'manifest.json'
manifest = read_json(manifest_path)
corrections = read_json(root / 'corrections.json')
raw = read_json(root / 'automatic-proposals.json')
if any(f['label_status'] != 'unlabelled' for f in manifest['frames']):
    raise ValueError('Saved annotations exist: preserve edits instead of replaying corrections')

coco = {'info': {'description': 'Small AI-annotated excerpt with person crowd ignore regions',
                 'created_at': now(), 'independent_human_review': False},
        'images': [], 'annotations': [],
        'categories': [{'id': 1, 'name': 'person'}, {'id': 2, 'name': 'ball'}]}
counts = Counter()
summary = []
(root / 'previews').mkdir(exist_ok=True)

for image_id, record in enumerate(raw, 1):
    frame = record['frame']
    rule = corrections['frames'][str(int(frame['timestamp_s']))]
    selected = []
    for candidate in record['boxes']:
        key = 'keep_person_ids' if candidate['class_id'] == 0 else 'keep_ball_ids'
        if candidate['id'] in rule[key]:
            selected.append([candidate['class_id'], *rule['updates_xyxy'].get(str(candidate['id']), candidate['xyxy'])])
    selected.extend(rule['additional_boxes'])
    selected.extend(corrections['additional_visible_partial_balls_all_frames'])
    normalized = []
    im = Image.open(root / frame['image']).convert('RGB')
    draw = ImageDraw.Draw(im)
    frame_counts = Counter()
    for cls, x1, y1, x2, y2 in selected:
        normalized.append([cls, (x1+x2)/2/frame['width'], (y1+y2)/2/frame['height'],
                           (x2-x1)/frame['width'], (y2-y1)/frame['height']])
        frame_counts[manifest['names'][cls]] += 1
        coco['annotations'].append({'id': len(coco['annotations'])+1, 'image_id': image_id,
            'category_id': cls+1, 'bbox': [x1,y1,x2-x1,y2-y1], 'area': (x2-x1)*(y2-y1),
            'iscrowd': 0, 'annotation_source': 'AI visually corrected; human review pending'})
        color = '#00d4ff' if cls == 0 else '#ffdc00'
        draw.rectangle((x1,y1,x2,y2), outline=color, width=2)
        if cls == 1:
            draw.text((x1,max(0,y1-14)), 'ball', fill=color)
    for x1,y1,x2,y2 in corrections['ignore_regions_xyxy']:
        coco['annotations'].append({'id':len(coco['annotations'])+1,'image_id':image_id,
            'category_id':1,'bbox':[x1,y1,x2-x1,y2-y1], 'area':(x2-x1)*(y2-y1), 'iscrowd':1,
            'segmentation': [[x1,y1,x2,y1,x2,y2,x1,y2]], 'annotation_source':'background crowd ignore region'})
        draw.rectangle((x1,y1,x2,y2),outline='#ff8800',width=2)
        draw.text((x1,y1-14),'background crowd: ignore',fill='#ff8800')
    save_annotation(manifest_path, {'frame_id':frame['frame_id'], 'action':'save',
        'boxes':normalized, 'negative':False, 'annotator':corrections['annotator']})
    coco['images'].append({'id': image_id,'file_name':frame['image'],'width':frame['width'],
        'height':frame['height'],'source_timestamp_s':frame['timestamp_s'],
        'source_frame_index':frame['frame_index'],'clip_timestamp_s':frame['clip_timestamp_s']})
    im.save(root/'previews'/f"{frame['frame_id']}.jpg",quality=94)
    counts.update(frame_counts)
    summary.append({'frame_id':frame['frame_id'],'timestamp_s':frame['timestamp_s'],
                    'counts':dict(frame_counts),'notes':rule['notes']})

data = read_json(manifest_path)
data.update(annotation_origin='AI, model-assisted and visually corrected',
            independent_human_review=False, ignore_regions=corrections['ignore_regions_xyxy'],
            ignore_policy='COCO person crowds; foreground GT takes precedence. Plain YOLO TXT cannot encode ignore regions.')
write_json(manifest_path,data)
write_json(root/'annotations.coco.json',coco)
write_json(root/'annotation-summary.json',{'created_at':now(),'annotator':corrections['annotator'],
    'frames':len(raw),'object_counts':dict(counts),'crowd_ignore_regions_per_frame':2,
    'independent_human_review':False,'frames_detail':summary,
    'note':'Six validation excerpt frames, not a complete training dataset. Ball counts include stationary spare balls and partly visible spare balls.'})
print(dict(counts))
