#!/usr/bin/env python3
"""Import the 12 base-strike Korean lines byte-for-byte, validating hashes and complete decoding.

Requires soundfile and numpy. Downloads remains read-only. Does not select or remix music.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(source):
    hashes = {}
    for line in (source / 'SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        hashes[name.lstrip('*').replace('\\', '/')] = digest.lower()
    table = source / 'audio/dialogue-ko.csv'
    lines, sounds, outputs, evidence = {}, {}, {}, []
    for row in csv.DictReader(table.open(encoding='utf-8-sig', newline='')):
        if row['group'] != 'strike':
            continue
        key = row['wem'].lower()
        if key in lines or len(key) != 8 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('Invalid or duplicate voice id: ' + key)
        relative = row['file'].replace('\\', '/')
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('Unsafe source path')
        path = source / relative
        digest = sha(path)
        if hashes.get(relative) != digest:
            raise ValueError('Source hash mismatch: ' + relative)
        samples, rate = sf.read(path, dtype='float32', always_2d=True)
        if not samples.size or rate <= 0 or not np.isfinite(samples).all():
            raise ValueError('Invalid decoded samples: ' + relative)
        peak = float(np.max(np.abs(samples)))
        if peak < .0001:
            raise ValueError('Silent voice: ' + relative)
        seconds = len(samples) / rate
        lines[key] = dict(speaker={'Ghost': '고스트', 'Zavala': '자발라'}[row['speaker']],
                          text=row['ko'], ticks=math.ceil(seconds * 20), seconds=seconds,
                          event='destiny_devils:voice.' + key, voice=True, authored=False)
        sounds['voice.' + key] = {'sounds': [{'name': 'destiny_devils:voice/' + key, 'stream': True}]}
        outputs['assets/destiny_devils/sounds/voice/' + key + '.ogg'] = path.read_bytes()
        evidence.append(dict(id=key, source=relative, sha256=digest, frames=len(samples),
                             rate=rate, channels=samples.shape[1], peak=peak,
                             textHash=row['textHash'], table=row['table']))
    if len(lines) != 12:
        raise ValueError('Expected twelve base-strike lines')
    def encode(value):
        return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode()
    outputs['assets/destiny_devils/sounds.json'] = encode(sounds)
    outputs['destiny/devils_lair/subtitles_ko.json'] = encode({'lines': lines})
    outputs['destiny/devils_lair/audio-manifest.json'] = encode(dict(
        source=str(source), dialogueTableSha256=sha(table), voice=evidence,
        conversion='byte-identical OGG copy; full decode, finite/non-silent sample verification',
        musicSelection='pending listening and cue mapping',
        excluded='variant_candidates; no Hecate/Micah lines in the base strike',
        audibleAcceptance=False))
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--resources', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    source, resources = args.source.resolve(), args.resources.resolve()
    if source == resources or source in resources.parents:
        raise ValueError('Output may not be inside read-only source')
    outputs = generate(source)
    for relative, raw in outputs.items():
        path = resources / relative
        if args.verify:
            if path.read_bytes() != raw:
                raise ValueError('Generated output differs: ' + relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({'files': len(outputs), 'voices': 12, 'verified': args.verify}, ensure_ascii=False))


if __name__ == '__main__':
    main()
