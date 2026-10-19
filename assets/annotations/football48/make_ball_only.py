"""Create a separate one-class view; keeps the original temporal split."""
import argparse
import json
import os
import shutil
from pathlib import Path


def create(output):
    root=Path(__file__).resolve().parent
    output=Path(output).resolve()
    if output.exists():raise ValueError('Choose a new output directory')
    manifest=json.loads((root/'manifest.json').read_text())
    for frame in manifest['frames']:
        src=root/frame['image'];dst=output/frame['image']
        dst.parent.mkdir(parents=True,exist_ok=True)
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
        lines=[]
        for line in (root/frame['label']).read_text().splitlines():
            fields=line.split()
            if fields[0]=='1':lines.append('0 '+' '.join(fields[1:]))
        label=output/frame['label'];label.parent.mkdir(parents=True,exist_ok=True)
        label.write_text('\n'.join(lines)+ ('\n' if lines else ''),encoding='utf-8')
    (output/'data.yaml').write_text('train: images/train\nval: images/val\nnames:\n  0: ball\n',encoding='utf-8')
    (output/'source.json').write_text(json.dumps({'source_dataset':'football48-001',
        'frames':[{'frame_id':f['frame_id'],'split':f['split']} for f in manifest['frames']],
        'mapping':{'original_class_1_ball':0},'empty_labels':'Visually confirmed ball-absent crops'},indent=2)+'\n')
    print(output/'data.yaml')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    create(p.parse_args().output)
