"""Verifieer de 80-reviewselectie tegen de historische bal-v2-training. Geen training."""
from pathlib import Path
import argparse
import collections
import hashlib
import json


def checksum(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def audit(root):
    root = Path(root).resolve()
    def read(path):
        return json.loads((root / path).read_text(encoding='utf-8-sig'))
    review = read('datasets/school-ball80-review-v1/manifest.json')
    curated = read('data/broadcast-ball-review-v1/curated/manifest.json')
    crop = read('data/broadcast-training-v2/balls/manifest.json')
    coco = read('data/broadcast-training-v2/ball-coco/manifest.json')
    experiment = read('reports/broadcast-data/v2-experiment.json')
    fingerprint = hashlib.sha256(json.dumps(
        {k: v for k, v in crop.items() if k != 'fingerprint'},
        sort_keys=True, allow_nan=False).encode()).hexdigest()
    assert fingerprint == crop['fingerprint'] == coco['source_fingerprint']
    assert fingerprint == experiment['preregistration']['dataset_fingerprint']
    assert review['source_fingerprint'] == curated['fingerprint']
    cur_map = {f['frame_id']: f for f in curated['frames']}
    coco_map = {f['frame_id']: f for f in coco['frames']}
    mapped = []
    for frame in review['frames']:
        source = cur_map[frame['frame_id']]
        assert source['image_sha256'] == frame['initial_image_sha256']
        assert source['label_sha256'] == frame['initial_label_sha256']
        assert source['split'] == frame['split']
        for kind in ['image', 'label']:
            assert checksum(root / 'datasets/school-ball80-review-v1' / frame[kind]) == frame[f'initial_{kind}_sha256']
            assert checksum(root / 'data/broadcast-ball-review-v1/curated' / source[kind]) == source[f'{kind}_sha256']
        children = [c for c in crop['frames'] if c.get('parent_frame_id') == frame['frame_id'] and c['kind'] == 'positive']
        assert children
        for c in children:
            assert c['split'] == frame['split']
            assert c['source_image_sha256'] == frame['initial_image_sha256']
            x, y = c['window_xyxy'][:2]
            expected = [source['bbox_xyxy'][0]-x, source['bbox_xyxy'][1]-y,
                        source['bbox_xyxy'][2]-x, source['bbox_xyxy'][3]-y]
            assert max(abs(a-b) for a, b in zip(c['bbox_xyxy'], expected)) < .01
            t = coco_map[c['frame_id']]
            assert t['image_sha256'] == c['image_sha256']
            assert t['split'] == c['split']
            for kind in ['image', 'label']:
                assert checksum(root / 'data/broadcast-training-v2/ball-coco' / t[kind]) == t[f'{kind}_sha256']
        mapped.append({'frame_id': frame['frame_id'], 'split': frame['split'],
                       'image_sha256': frame['initial_image_sha256'],
                       'label_sha256': frame['initial_label_sha256'],
                       'positive_training_or_validation_crops': [c['frame_id'] for c in children]})
    counts = dict(collections.Counter(f['split'] for f in mapped))
    assert len(mapped) == 80 and counts == {'train': 48, 'val': 32}
    model = root / 'artifacts/broadcast-ball-v2/broadcast_ball_v2.pt'
    assert checksum(model) == experiment['candidate_weights_sha256']
    start = root / 'artifacts/fullscene-ball-v1/fullscene_ball_f005.pt'
    assert checksum(start) == experiment['preregistration']['weights_sha256']
    for frame in coco['frames']:
        for kind in ['image', 'label']:
            assert checksum(root / 'data/broadcast-training-v2/ball-coco' / frame[kind]) == frame[f'{kind}_sha256']
    return {'checked_review_frames': len(mapped), 'split': counts,
            'positive_crops_from_review_set': sum(len(f['positive_training_or_validation_crops']) for f in mapped),
            'full_training_dataset_crops': len(coco['frames']), 'full_source_images': len(curated['frames']),
            'dataset_fingerprint': fingerprint, 'candidate_weights_sha256': checksum(model),
            'historical_v2_full_mAP50': experiment['candidate']['full']['mAP50'],
            'historical_v2_full_mAP50_95': experiment['candidate']['full']['mAP50_95'],
            'historical_v2_tiled_mAP50': experiment['candidate']['tiled']['mAP50'],
            'historical_v2_tiled_mAP50_95': experiment['candidate']['tiled']['mAP50_95'],
            'meaning': 'The approved 80-frame set is an unchanged subset of the corpus used for historical v2 training/validation. No separate new run on exactly 80 frames.',
            'limits': 'Review approval is later than the historical run. Other source images are not thereby human-approved. Metrics cover the full historical validation, not an isolated 32-frame re-evaluation or the deployed Andrew model.',
            'new_training_or_accuracy_evaluation': False, 'frames': mapped}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.code_root)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'frames'}, indent=2, ensure_ascii=False))
