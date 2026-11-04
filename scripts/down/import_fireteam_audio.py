#!/usr/bin/env python3
"""Copy verified handoff audio unchanged; lifecycle candidates are deliberately excluded."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    source = args.source
    hashes = json.loads((source / 'FILE-HASHES.json').read_text())
    base = source / 'minecraft/assets/destiny_fireteam'
    destination = ROOT / 'src/main/resources/assets/destiny_fireteam'
    copied = {}
    for path in sorted((base / 'sounds').rglob('*.ogg')):
        relative = path.relative_to(source).as_posix()
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if hashes.get(relative) != digest:
            raise ValueError('Source hash mismatch: ' + relative)
        out = destination / path.relative_to(base)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        copied[relative] = digest
    sounds = json.loads((base / 'sounds.json').read_text())
    if (destination / 'sounds.json').exists():
        sounds.update({k: v for k, v in json.loads((destination / 'sounds.json').read_text()).items()
                       if k.startswith('respawn_complete_')})
    for channel in range(64):
        sounds[f'revive_progress_{channel}'] = sounds['revive_progress']
    (destination / 'sounds.json').write_text(json.dumps(sounds, indent=2) + '\n')
    manifest = dict(source=str(source), sha256=copied, category='players',
                    progress_seconds=3.024, progress='Provided Minecraft mono downmix, unchanged bytes',
                    completion='Unconfirmed lifecycle candidates excluded; existing transmat retained')
    out = ROOT / 'src/main/resources/destiny/down/fireteam-audio-provenance.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(f'Imported {len(copied)} verified OGG files')

if __name__ == '__main__':
    main()
