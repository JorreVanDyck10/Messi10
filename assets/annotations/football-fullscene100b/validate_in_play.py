"""Check the generated match-ball view against saved full-scene annotations."""
import argparse
from pathlib import Path
from build_dataset import read,write,digest


def validate(output):
    """Controleer dat de afgeleide speelbalset dezelfde volledige bronbeelden en splits bevat en
    uitsluitend de goedgekeurde speelballabels gebruikt.
    """
    root=Path(__file__).resolve().parent;output=Path(output).resolve()
    spec=read(root/'source-annotations.json');manifest=read(root/'manifest.json')
    records={f['frame_id']:f for f in spec['frames']};counts={}
    for f in manifest['frames']:
        assert digest(output/f['image'])==f['image_sha256']
        target=[a for a in records[f['frame_id']]['objects'] if a['kind']=='in_play_ball']
        assert len(target)==1
        lines=(output/f['label']).read_text().splitlines();assert len(lines)==1
        cls,x,y,w,h=map(float,lines[0].split());assert cls==0
        a,b,c,d=target[0]['xyxy'];expected=[(a+c)/8192,(b+d)/2160,(c-a)/4096,(d-b)/1080]
        assert all(abs(v-z)<1e-8 for v,z in zip([x,y,w,h],expected))
    from ultralytics.data.dataset import YOLODataset
    from ultralytics.data.utils import check_det_dataset
    data=check_det_dataset(str(output/'data.yaml'),autodownload=False)
    assert data['names']=={0:'in_play_ball'}
    for split,n in [('train',70),('val',30)]:
        (output/'labels'/f'{split}.cache').unlink(missing_ok=True)
        ds=YOLODataset(img_path=data[split],data=data,task='detect',imgsz=2048,augment=False,cache=False)
        assert len(ds)==n and all(len(l['cls'])==1 for l in ds.labels)
        counts[split]={'images':len(ds),'in_play_ball_boxes':sum(len(l['cls']) for l in ds.labels)}
    report={'status':'passed','images':100,'in_play_ball_boxes':100,'reserve_ball_positive_boxes':0,
        'reserve_balls_are_intentional_background':True,'images_identical_to_full_scene_pngs':100,
        'boxes_agree_with_source_annotations':True,'ultralytics_loader':counts,
        'independent_human_review_complete':False,'model_training_performed':False}
    write(root/'verification-in-play.json',report);print(report)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);validate(p.parse_args().output)
