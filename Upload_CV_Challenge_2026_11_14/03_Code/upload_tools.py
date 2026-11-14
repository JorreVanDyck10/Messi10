"""Maak lokale paden vanuit de meegeleverde, herleidbare configuraties."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def bind_field(python):
    """Koppel de originele bron- en gewichtshashes aan deze uitgepakte map."""
    config = json.loads((ROOT / '.tools/field-runtime.template.json').read_text(encoding='utf-8'))
    config.update(python=str(Path(python).resolve()), repository=str(ROOT / '.tools/PnLCalib'), device='cpu')
    for role, name in [('keypoints', 'SV_kp'), ('lines', 'SV_lines')]:
        path = str(ROOT / 'weights/pnlcalib' / name)
        config['weights_' + role] = path
        config['models'][role]['path'] = path
    (ROOT / '.tools/field-runtime.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    print('CPU-veldruntime gekoppeld aan de uitgepakte map.')

def bind_profile(device):
    """Behoud de gekozen modellen en zet relatieve paden en het device expliciet."""
    source = ROOT / 'configs/models-broadcast.json'
    config = json.loads(source.read_text(encoding='utf-8'))
    for spec in config['models'] + [config[k] for k in ['appearance', 'kit_embedding', 'role_context']]:
        spec['weights'] = str((source.parent / spec['weights']).resolve())
        if 'device' in spec:
            spec['device'] = device
    for key, value in config.get('handoff', {}).items():
        if key.endswith('_record'):
            config['handoff'][key] = str((source.parent / value).resolve())
    (ROOT / '.cache').mkdir(exist_ok=True)
    path = ROOT / '.cache/models-upload.json'
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    print(path)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['field', 'profile'])
    p.add_argument('--python')
    p.add_argument('--device', default='cpu')
    args = p.parse_args()
    bind_field(args.python) if args.action == 'field' else bind_profile(args.device)
