"""Replace the selected Ghost dialogue with verified Korean recordings; keep sources read-only."""
import csv
import hashlib
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/Users/qf/Downloads/Destiny-Ghost-Korean-2026-10-31')
ASSETS = ROOT / 'src/main/resources/assets/destiny'
FFMPEG = ROOT / 'run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    previous = json.loads((ROOT / 'art/ghost/w280/audio-manifest.json').read_text())
    hashes = json.loads((SOURCE / 'FILE-HASHES.json').read_text())
    with (SOURCE / 'manifest-ko.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    selected = {}
    # Validate the complete selection before replacing any shipped file.
    for key, old in previous.items():
        if key.startswith('chirp'):
            continue
        matches = [r for r in rows if r['file'].startswith('audio/voice/')
                   and Path(r['file']).name == Path(old['source']).name]
        if len(matches) != 1:
            raise ValueError(f'{key}: expected one Korean counterpart, found {len(matches)}')
        row = matches[0]
        source = SOURCE / row['file']
        if row['locale'] != 'ko' or row['status'] != 'decoded_non_silent' or not row['korean'].strip():
            raise ValueError(f'{key}: Korean recording/subtitle unavailable')
        if sha(source) != row['sha256'] or sha(source) != hashes[row['file']]:
            raise ValueError(f'{key}: source integrity mismatch')
        with wave.open(str(source)) as wav:
            duration = wav.getnframes() / wav.getframerate()
            if abs(duration - float(row['duration_sec'])) > 1 / wav.getframerate():
                raise ValueError(f'{key}: source duration mismatch')
        selected[key] = (row, source, duration)

    report = {}
    with tempfile.TemporaryDirectory(prefix='destiny-ghost-ko-') as temporary:
        temp = Path(temporary)
        for key, old in previous.items():
            if key.startswith('chirp'):
                output = ASSETS / f'sounds/tutorial/ghost/{key}.ogg'
                if sha(output) != old['output_sha256']:
                    raise ValueError(f'{key}: retained chirp changed')
                report[key] = dict(old, locale='nonverbal', source_delivery='Destiny-Ghost-Tutorial-2026-10-31')
                continue
            row, source, duration = selected[key]
            output = temp / f'{key}.ogg'
            subprocess.run([str(FFMPEG), '-v', 'error', '-y', '-i', str(source),
                            '-ac', '1', '-ar', '48000', '-af', 'loudnorm=I=-19:TP=-2:LRA=7',
                            '-c:a', 'libvorbis', '-q:a', '4', str(output)], check=True)
            # Fully decode the shipped encoding and check it contains nonzero PCM.
            decoded = subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(output),
                                      '-f', 's16le', '-ac', '1', '-ar', '48000', '-'],
                                     capture_output=True, check=True).stdout
            if not any(decoded) or abs(len(decoded) / 96000 - duration) > .05:
                raise ValueError(f'{key}: silent/truncated encoded audio')
            report[key] = dict(text=row['korean'].strip(), english=row['english'],
                               ticks=math.ceil(duration * 20) + 10, duration_sec=duration,
                               locale='ko', dialogue_tag=row['dialogue_tag'], wem=row['wem'],
                               source=row['file'], source_delivery=SOURCE.name,
                               source_package=row['source_package'], source_patch=row['source_patch'],
                               semantic_match=row['match'], source_sha256=sha(source),
                               output_sha256=sha(output), output_bytes=output.stat().st_size)
        for key in selected:
            (ASSETS / f'sounds/tutorial/ghost/{key}.ogg').write_bytes((temp / f'{key}.ogg').read_bytes())
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (ROOT / 'src/main/resources/data/destiny/tutorial/ghost_lines.json').write_text(encoded)
    destination = ROOT / 'art/ghost/w282'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'audio-manifest.json').write_text(encoded)
    print(f'Korean voices: {len(selected)}, retained chirps: 3, total bytes: '
          f'{sum(r["output_bytes"] for r in report.values())}')


if __name__ == '__main__':
    main()
