"""Export eight native-resolution, 20-second reference clips from the source."""
import argparse
import json
import subprocess
from pathlib import Path
import cv2
import imageio_ffmpeg
from build_dataset import digest,read,write


def build(source,output):
    root=Path(__file__).resolve().parent;spec=read(root/'source-annotations.json')
    if digest(source)!=spec['source']['sha256']:raise ValueError('Source checksum mismatch')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    records=[]
    for group in sorted({r['group_id'] for r in spec['frames']}):
        start=int(group.split('-')[1]);path=output/f'128057_{group}_20s.mp4'
        if path.exists():raise ValueError(f'Refusing to overwrite {path}')
        # This source's video starts at PTS 1 while the container starts at 0.
        # Seek by absolute timestamp: the container starts at 0.01 seconds,
        # while video starts at 1.00. Relative seeking would round up a frame.
        seek=start+spec['source']['first_video_pts_s']
        command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-seek_timestamp','1','-ss',str(seek),'-i',str(source),
            '-map','0:v:0','-an','-frames:v','500','-c:v','libx264','-preset','veryfast','-crf','25',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
        subprocess.run(command,check=True)
        cap=cv2.VideoCapture(str(path));count=round(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS)
        size=[round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))];cap.release()
        assert count==500 and fps==25 and size==[4096,1080],(group,count,fps,size)
        selected=[f for f in spec['frames'] if f['group_id']==group]
        assert all(start<=f['timestamp_s']<start+20 for f in selected)
        records.append({'group_id':group,'file':path.name,'source_start_s':start,'ffmpeg_absolute_seek_s':seek,'duration_s':20,'frame_count':count,
            'fps':fps,'size':size,'sha256':digest(path),'split':selected[0]['split'],
            'selected_frames':[{'frame_id':f['frame_id'],'clip_time_s':round(f['timestamp_s']-start,4)} for f in selected]})
        write(output/'manifest.json',{'source':spec['source'],'clips':records,'note':'Reference videos; only selected dataset crops have labels, not every clip frame.'})
        print(group,path.stat().st_size,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();build(args.source,args.output)
