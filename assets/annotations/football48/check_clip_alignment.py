"""Check temporal correspondence in lossy reference clips against the source.

Checks one selected frame per clip. The closest pixel match must be within
one source frame of the nominal frame index. It does not claim exact pixels.
"""
import argparse
from pathlib import Path
import cv2
import numpy as np
from build_dataset import read,write,digest


def check(source,clips,output):
    root=Path(clips);manifest=read(root/'manifest.json')
    if digest(source)!=manifest['source']['sha256']:raise ValueError('Source checksum mismatch')
    video=cv2.VideoCapture(str(source));records=[]
    try:
        for clip in manifest['clips']:
            cap=cv2.VideoCapture(str(root/clip['file']));f=clip['selected_frames'][0]
            local=round(f['clip_time_s']*25);original=clip['source_start_s']*25+local
            try:
                cap.set(cv2.CAP_PROP_POS_FRAMES,local);ok,a=cap.read()
                if not ok:raise ValueError('Cannot decode reference frame')
                errors={}
                for offset in [-25,-1,0,1,25]:
                    video.set(cv2.CAP_PROP_POS_FRAMES,original+offset);ok,b=video.read()
                    if not ok:raise ValueError('Cannot decode source frame')
                    errors[offset]=float(np.abs(a.astype(np.float32)-b.astype(np.float32)).mean())
                best=min(errors,key=errors.get)
                if abs(best)>1:raise ValueError((clip['file'],errors))
                records.append({'file':clip['file'],'checked_source_frame':original,'checked_clip_frame':local,
                    'closest_source_frame_offset':best,'pixel_differences_by_source_frame_offset':errors})
            finally:cap.release()
    finally:video.release()
    if len(records)!=8:raise ValueError('Expected eight complete clips')
    result={'status':'passed','sampled_clips':8,'frames_checked_per_clip':1,
        'accepted_source_frame_tolerance':1,'time_tolerance_s':.04,
        'scope':'Lossy pixel correspondence, with original source checksum; exported PNG training data stays lossless.',
        'records':records}
    write(output,result);print('Temporal correspondence passed for eight clips (within one frame).')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--clips',required=True)
    p.add_argument('--output',default=str(Path(__file__).with_name('clip-alignment.json')))
    args=p.parse_args();check(args.source,args.clips,args.output)
