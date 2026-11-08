#!/usr/bin/env python3
"""Raise the Devils' Lair score by a fixed global factor (default x4.5) from the previously imported OGGs.

import_devils_music_linkage.py wrote every segment at x0.3 of the rendered bank ("provisional"); the result sat 18-20 dB
under the voice lines and SFX (mean about -37 dB against -17 dB) and was close to inaudible in play. One fixed factor keeps
the relative bank levels; the loudest segment peaks at 0.59 after the change. Frame counts must not change because the
runtime schedules segments by their rendered duration.

usage: regain_devils_music.py ORIGINALS_DIR [--gain 4.5]   (writes into src/main/resources/assets/destiny_music/sounds/devils)
"""
import argparse, hashlib, json, os, sys
from pathlib import Path
import numpy as np, soundfile as sf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('originals', type=Path)
    ap.add_argument('--gain', type=float, default=4.5)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    a = ap.parse_args()
    out_dir = a.root / 'src/main/resources/assets/destiny_music/sounds/devils'
    rows = []
    for src in sorted(a.originals.glob('*.ogg')):
        with sf.SoundFile(src) as i:
            rate, ch, frames = i.samplerate, i.channels, i.frames
            target = out_dir / src.name
            tmp = target.with_suffix('.tmp')
            with sf.SoundFile(tmp, 'w', samplerate=rate, channels=ch, format='OGG', subtype='VORBIS', compression_level=0.7) as o:
                for block in i.blocks(blocksize=65536, dtype='float32'):
                    o.write(np.clip(block * a.gain, -1, 1))
        os.replace(tmp, target)
        with sf.SoundFile(target) as n:
            if n.frames != frames: sys.exit('Frame count changed: ' + src.name)
        rows.append(dict(segment=src.stem, frames=frames, rate=rate,
                         inputSha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                         output=str(target.relative_to(a.root)), outputSha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (a.root / 'art/audio/devils-music-gain/manifest.json').write_text(json.dumps(
        dict(gain=a.gain, relativeTo='segments produced by import_devils_music_linkage.py (x0.3)', files=rows), indent=2) + '\n')

if __name__ == '__main__': main()
