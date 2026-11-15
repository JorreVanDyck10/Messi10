"""Controleer alle bestanden van de inzendingsmap met SHA-256."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
manifest=json.loads((root/'BESTANDEN_SHA256.json').read_text(encoding='utf-8'))
errors=[]
for item in manifest['files']:
 p=root/item['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
  errors.append(item['path'])
if errors:raise SystemExit('Ontbrekend of gewijzigd: '+', '.join(errors[:12]))
print(f"OK: {len(manifest['files'])} bestanden gecontroleerd. Dit is geen nauwkeurigheidsmeting.")
