#!/usr/bin/env python3
"""Import the source-labelled descent cue; inventory other clips without guessing their roles."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    source, root = args.source.resolve(), args.root.resolve()
    hashes = dict((name.replace('\\', '/'), digest) for digest, name in
                  (line.split(None, 1) for line in (source / 'SHA256SUMS.txt').read_text().splitlines()))

    def verified(name):
        data = (source / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if hashes.get(name) != digest:
            raise ValueError('Source checksum mismatch: ' + name)
        return data

    index = json.loads(verified('music-index.json'))
    banks = json.loads(verified('music-banks.json'))
    validation = json.loads(verified('audio/voice-music-validation.json'))
    descent = next(x for x in index if x.get('type') == 'descent_sequence')
    if descent['wems'] != ['80D715DA'] or not any(
            b['tag'] == descent['bank'] and b['name'] == 'cosmo_portal1_descent' for b in banks):
        raise ValueError('Descent provenance changed; review source mapping')
    rows = []
    for row in validation:
        if not row['file'].startswith('audio/music/'):
            continue
        data = verified(row['file'])
        raw = 'audio_raw/music/' + row['wem'] + '.wem'
        verified(raw)
        rows.append(dict(row, sha256=hashlib.sha256(data).hexdigest(), rawSha256=hashes[raw],
                         assignment='descent' if row['wem'] == '80D715DA' else
                         'excluded_silence' if row['wem'] == '80D63BFA' else 'unreviewed'))
    selected = next(r for r in rows if r['assignment'] == 'descent')
    if selected['status'] != 'decoded_non_silent' or selected['frames'] != selected['oggDecodedFrames']:
        raise ValueError('Descent decode validation failed')
    event = 'devils_descent_80d715da'
    resources = root / 'src/main/resources'
    destination = resources / ('assets/destiny_music/sounds/' + event + '.ogg')
    destination.write_bytes(verified(selected['file']))
    sounds_path = resources / 'assets/destiny_music/sounds.json'
    sounds = json.loads(sounds_path.read_text())
    sounds[event] = {'sounds': [{'name': 'destiny_music:' + event, 'stream': True}]}
    sounds_path.write_text(json.dumps(sounds, indent=2) + '\n')
    catalog_path = resources / 'data/destiny/activity_music.json'
    catalog = json.loads(catalog_path.read_text())
    catalog['devils_descent'] = [{'event': event, 'seconds': selected['frames'] / selected['rate'], 'volume': .3}]
    catalog_path.write_text(json.dumps(catalog, indent=2) + '\n')
    evidence = root / 'docs/qa/2026-11-03/devils-lair/music'
    evidence.mkdir(parents=True, exist_ok=True)
    report = {'source': str(source), 'mapping': descent, 'clips': rows,
              'selectionBasis': 'Source bank labels descent; remaining combat cues require listening and loop review.',
              'processing': 'Original OGG bytes; no trim, gain, remix or transcoding.',
              'mix': 'RECORDS, volume 0.3 provisional; actual speaker/mix acceptance pending.'}
    (evidence / 'source-inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# 악마의 소굴 음악 검토', '', '파일 이름 순서는 재생 순서가 아닙니다. 전투 구간 배정과 루프 검수는 미완료입니다.', '']
    for row in rows:
        lines.append(f"- [{row['wem']}]({source / row['file']}) · {row['seconds']:.3f}s · {row['channels']}ch · {row['assignment']}")
    (evidence / 'audition.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'verifiedClips': len(rows), 'imported': event, 'seconds': selected['frames'] / selected['rate']}))


if __name__ == '__main__':
    main()
