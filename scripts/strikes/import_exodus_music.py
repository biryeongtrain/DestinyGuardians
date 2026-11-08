#!/usr/bin/env python3
"""Re-encode the Exodus Crash score stems to ~50 kbps Vorbis and write the tier table.

Tiers are by loudness: 0 travel, 1 combat, 2 intense, 3 climax. Clips under 10 s, near-silent clips and the
200 s+ full-length alternates are skipped. Requires soundfile (libsndfile Vorbis, level 1.0 = about 50 kbps)."""
import argparse, glob, json
from pathlib import Path
import numpy as np, soundfile as sf

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--source', type=Path, required=True); ap.add_argument('--resources', type=Path, required=True)
    a = ap.parse_args()
    out = a.resources / 'assets/destiny_exodus_music/sounds/music'; out.mkdir(parents=True, exist_ok=True)
    tiers = [[], [], [], []]; sounds = {}
    for f in sorted(glob.glob(str(a.source / 'audio/music/*.ogg'))):
        key = Path(f).stem
        x, r = sf.read(f, dtype='float32', always_2d=True); sec = len(x) / r; rms = float(np.sqrt((x ** 2).mean()))
        if sec < 10 or sec > 120 or rms < .02: continue
        tier = 0 if rms < .075 else 1 if rms < .12 else 2 if rms < .17 else 3
        sf.write(str(out / (key + '.ogg')), x, r, format='OGG', subtype='VORBIS', compression_level=1.0)  # ~50 kbps
        sounds[key] = {'sounds': [{'name': 'destiny_exodus_music:music/' + key, 'stream': True}]}
        tiers[tier].append(dict(event=key, seconds=round(sec, 3)))
    (a.resources / 'assets/destiny_exodus_music/sounds.json').write_text(json.dumps(sounds, indent=1))
    d = a.resources / 'destiny/exodus_crash'; d.mkdir(parents=True, exist_ok=True)
    (d / 'music.json').write_text(json.dumps(dict(namespace='destiny_exodus_music', tiers=tiers)))
    print([len(t) for t in tiers])

if __name__ == '__main__': main()
