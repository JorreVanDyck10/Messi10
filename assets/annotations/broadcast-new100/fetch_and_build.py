"""Rebuild reviewed full-frame annotations from the exact original broadcast clips.

No inference or model download is needed. Media remains local and gitignored.
"""
import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


def digest(path):
    """Bereken de SHA-256 van het bron-, beeld- of labelbestand in blokken voor de identiteitscontrole."""
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    """Schrijf de exportgegevens als leesbare UTF-8-JSON met behoud van niet-ASCII-tekens."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def yolo_line(category, box, width, height):
    """Reken een bronpixelbox om naar één YOLO-regel met klasse en genormaliseerd centrum, breedte en
    hoogte.
    """
    x, y, z, w = box
    return f'{category} {(x+z)/2/width:.9f} {(y+w)/2/height:.9f} {(z-x)/width:.9f} {(w-y)/height:.9f}'


def link_image(source, target):
    """Hergebruik het volledige bronbeeld via een hardlink of kopie en weiger een al bestaande afwijkende
    taakafbeelding.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if digest(source) != digest(target):
            raise ValueError(f'Existing task image differs: {target}')
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def build(annotation_path, source_dir, out, download=False):
    """Verifieer de vijf bronclips, reconstrueer de geselecteerde volledige frames en schrijf scène-,
    speler- en speelbalexports met hashes en expliciete uitsluitingen.
    """
    data = json.loads(annotation_path.read_text(encoding='utf-8'))
    source_dir.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    if out.resolve() != annotation_path.parent.resolve():
        for name in ('source-annotations.json', 'fetch_and_build.py', 'README.md', 'requirements.txt'):
            seed = annotation_path.parent / name
            if seed.exists():
                shutil.copy2(seed, out / name)
    manifest, coco_images, coco_annotations = [], [], []
    lists = {task: {split: [] for split in ('train', 'val')}
             for task in ('all', 'players', 'in-play-ball')}
    image_hashes = set()
    pixel_checks = 0
    for source in data['sources']:
        path = source_dir / source['filename']
        if not path.exists():
            if not download:
                raise FileNotFoundError(f'{path}; use --download or --source-dir')
            import gdown
            gdown.download(id=source['drive_id'], output=str(path), quiet=False)
        if digest(path) != source['sha256']:
            raise ValueError(f'Source SHA-256 mismatch: {path}')
        cap = cv2.VideoCapture(str(path))
        try:
            if not cap.isOpened() or int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) != source['frames']:
                raise ValueError(f'Unexpected source video: {path}')
            for frame in [f for f in data['frames'] if f['source'] == source['filename']]:
                fid, split = frame['frame_id'], frame['split']
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame['frame_index'])
                ok, bgr = cap.read()
                if not ok:
                    raise ValueError(f'Cannot decode {fid}')
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                width, height = frame['width'], frame['height']
                assert rgb.shape == (height, width, 3)
                image_path = out / 'images' / split / f'{fid}.png'
                image_path.parent.mkdir(parents=True, exist_ok=True)
                if not image_path.exists():
                    Image.fromarray(rgb).save(image_path)
                with Image.open(image_path) as saved:
                    if not np.array_equal(np.asarray(saved), rgb):
                        raise ValueError(f'Image is not the unchanged source frame: {fid}')
                pixel_checks += 1
                sha = digest(image_path)
                assert sha not in image_hashes, f'Duplicate frame {fid}'
                image_hashes.add(sha)
                expected = frame.get('image_sha256')
                if expected and sha != expected:
                    raise ValueError(f'PNG SHA-256 mismatch: {fid}; check Pillow/OpenCV versions')
                eligible = frame['in_play_ball_status'] == 'visible_labelled'
                image_id = len(coco_images) + 1
                coco_images.append({'id': image_id, 'file_name': image_path.relative_to(out).as_posix(),
                                    'width': width, 'height': height, 'split': split,
                                    'in_play_ball_status': frame['in_play_ball_status'],
                                    'human_review_complete': False})
                preview = Image.fromarray(rgb)
                draw = ImageDraw.Draw(preview)
                colors = ['cyan', 'yellow', 'orange', 'lime', 'magenta', 'red', 'white', 'blue']
                task_lines = {task: [] for task in lists}
                for obj in frame['objects']:
                    category, box = obj['class_id'], obj['xyxy']
                    x, y, z, w = box
                    assert 0 <= category < len(data['names'])
                    assert 0 <= x < z <= width and 0 <= y < w <= height
                    task_lines['all'].append(yolo_line(category, box, width, height))
                    if category == 0:
                        task_lines['players'].append(yolo_line(0, box, width, height))
                    if category == 1:
                        assert eligible
                        task_lines['in-play-ball'].append(yolo_line(0, box, width, height))
                    coco_annotations.append({'id': len(coco_annotations)+1, 'image_id': image_id,
                                             'category_id': category+1, 'bbox': [x, y, z-x, w-y],
                                             'area': (z-x)*(w-y), 'iscrowd': 0,
                                             'kind': obj['kind'], 'review_status': 'open'})
                    draw.rectangle(box, outline=colors[category], width=2)
                    draw.text((x, max(0, y-12)), data['names'][category], fill=colors[category])
                assert len(task_lines['in-play-ball']) == int(eligible)
                for task in lists:
                    folder = out if task == 'all' else out / task
                    label = folder / 'labels' / split / f'{fid}.txt'
                    if task == 'in-play-ball' and not eligible:
                        continue
                    label.parent.mkdir(parents=True, exist_ok=True)
                    label.write_text('\n'.join(task_lines[task])+'\n', encoding='utf-8')
                    if task != 'all':
                        link_image(image_path, folder / 'images' / split / image_path.name)
                    if task == 'players' or eligible:
                        lists[task][split].append(f'./images/{split}/{fid}.png')
                pp = out / 'previews' / split / f'{fid}.jpg'
                pp.parent.mkdir(parents=True, exist_ok=True)
                preview.save(pp, quality=92)
                manifest.append({k: frame[k] for k in ('frame_id', 'source', 'frame_index',
                                                     'timestamp_s', 'split', 'in_play_ball_status')}
                                | {'image': image_path.relative_to(out).as_posix(), 'sha256': sha,
                                   'human_review_complete': False})
        finally:
            cap.release()
    for task, splits in lists.items():
        folder = out if task == 'all' else out / task
        names = data['names'] if task == 'all' else ['player' if task == 'players' else 'in_play_ball']
        for split, entries in splits.items():
            (folder / f'{split}.txt').write_text('\n'.join(entries)+'\n', encoding='utf-8')
        yaml = 'train: train.txt\nval: val.txt\nnames:\n'
        yaml += ''.join(f'  {i}: {name}\n' for i, name in enumerate(names))
        (folder / 'data.yaml').write_text(yaml, encoding='utf-8')
    write_json(out / 'manifest.json', manifest)
    write_json(out / 'annotations.coco.json', {
        'info': {'description': '100 AI-reviewed broadcast frames; human review open. Use manifest exclusions.'},
        'images': coco_images, 'annotations': coco_annotations,
        'categories': [{'id': i+1, 'name': n} for i, n in enumerate(data['names'])]})
    counts = Counter(data['names'][o['class_id']] for f in data['frames'] for o in f['objects'])
    report = {'frames': len(manifest), 'pixel_identical_frames_checked': pixel_checks,
              'unique_image_hashes': len(image_hashes), 'verified_source_hashes': len(data['sources']),
              'classes': dict(counts), 'all_frames_split': dict(Counter(f['split'] for f in data['frames'])),
              'training_views': {t: {s: len(v) for s, v in splits.items()} for t, splits in lists.items()},
              'ball_unresolved': [f['frame_id'] for f in data['frames'] if f['in_play_ball_status'] != 'visible_labelled'],
              'human_review_complete': False, 'model_training_performed': False,
              'semantic_accuracy_measured': False, 'opencv_version': cv2.__version__}
    assert len(manifest) == len(data['frames']) == 100
    assert {f['source'] for f in data['frames'] if f['split']=='train'}.isdisjoint(
        {f['source'] for f in data['frames'] if f['split']=='val'})
    write_json(out / 'verification.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    home = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=home / 'sources')
    parser.add_argument('--output', type=Path, default=home)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    build(home / 'source-annotations.json', args.source_dir.resolve(), args.output.resolve(), args.download)
