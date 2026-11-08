#!/usr/bin/env python3
"""Import the 62 Exodus Crash Korean voice lines byte-for-byte (OGG copy) plus their subtitle table and sound events.

Requires soundfile. The Downloads source is read-only. Music is intentionally not imported (90 MB; pack budget).
"""
import argparse, csv, json, math, shutil
from pathlib import Path
import soundfile as sf

SPEAKERS = {'Ghost': '고스트', 'Saint-14': '세인트-14', 'Failsafe': '안전장치'}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--resources', type=Path, required=True)
    a = ap.parse_args()
    lines, sounds = {}, {}
    out = a.resources / 'assets/destiny_exodus/sounds/voice'
    out.mkdir(parents=True, exist_ok=True)
    for row in csv.DictReader((a.source / 'audio/dialogue-ko.csv').open(encoding='utf-8-sig', newline='')):
        key = row['wem'].lower()
        src = a.source / row['file'].replace('\\', '/')
        if key in lines or not src.is_file(): raise SystemExit('bad row ' + key)
        info = sf.info(str(src)); seconds = info.frames / info.samplerate
        if seconds <= 0: raise SystemExit('empty ' + key)
        shutil.copyfile(src, out / (key + '.ogg'))
        lines[key] = dict(speaker=SPEAKERS[row['speaker']], text=row['ko'], ticks=math.ceil(seconds * 20), seconds=seconds,
                          event='destiny_exodus:voice.' + key, voice=True, authored=False)
        sounds['voice.' + key] = {'sounds': [{'name': 'destiny_exodus:voice/' + key, 'stream': True}]}
    enc = lambda v: json.dumps(v, indent=2, ensure_ascii=False, sort_keys=True) + '\n'
    (a.resources / 'assets/destiny_exodus/sounds.json').write_text(enc(sounds), encoding='utf-8')
    d = a.resources / 'destiny/exodus_crash'; d.mkdir(parents=True, exist_ok=True)
    (d / 'subtitles_ko.json').write_text(enc({'lines': lines}), encoding='utf-8')
    print(len(lines), 'lines')

if __name__ == '__main__': main()
