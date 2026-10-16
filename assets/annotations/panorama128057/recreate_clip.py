"""Recreate the exact excerpt: python recreate_clip.py /path/to/original.mp4"""
import sys
from fractions import Fraction
from pathlib import Path

import av

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from persoon1.core import read_json, sha256

root = Path(__file__).resolve().parent
manifest = read_json(root / 'manifest.json')
source = Path(sys.argv[1])
if sha256(source) != manifest['video']['video_id']:
    raise ValueError('Original video checksum differs from the annotated source')
target = (root / manifest['video']['file']).resolve()
if target.exists():
    raise ValueError('Clip already exists; preserve it instead of overwriting')
target.parent.mkdir(parents=True, exist_ok=True)
with av.open(str(source)) as src:
    video = src.streams.video[0]
    start = video.start_time * video.time_base + 54
    src.seek(int(start / video.time_base), stream=video, backward=True)
    with av.open(str(target), 'w', options={'movflags': '+faststart'}) as out:
        encoder = out.add_stream('libx264', rate=25)
        encoder.width, encoder.height, encoder.pix_fmt = 4096, 1080, 'yuv420p'
        encoder.options = {'crf': '18', 'preset': 'fast', 'threads': '4'}
        count = 0
        for frame in src.decode(video):
            stamp = frame.pts * frame.time_base
            if stamp < start:
                continue
            if stamp != start + Fraction(count, 25):
                raise ValueError('Unexpected frame timestamp in the source')
            frame.pts, frame.time_base = count, Fraction(1, 25)
            frame.pict_type = av.video.frame.PictureType.NONE
            for packet in encoder.encode(frame):
                out.mux(packet)
            count += 1
            if count == 500:
                break
        for packet in encoder.encode():
            out.mux(packet)
        if count != 500:
            raise ValueError('Source ended before 500 frames were decoded')
print('Recreated 500 original frames / 20 seconds')
