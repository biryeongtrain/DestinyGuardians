#!/usr/bin/env python3
"""Convert the three user-supplied pickup recordings without trimming or changing their mix."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCES = Path('/Users/qf/Downloads/drive-download-20261109T043839Z-1-001')
ROWS = [
    (40, 'basic', ['common', 'uncommon', 'rare'], '075c8478b61bf214778d89f5ef11cbf4b20e75b445c1ba9f5f065aef0244e2cc'),
    (41, 'legendary', ['legendary'], 'eab91049a13e4eb58d30613f33233aabdabe518803538b706422097382c0abf6'),
    (42, 'exotic', ['exotic'], '092ae4a1c800ebcdf529f78a0cf7ec3a07b54b026fdb6c56398b4c5e1fd1117d'),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def probe(path):
    stream = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(path)
    ]))['streams'][0]
    return {k: stream[k] for k in ('codec_name', 'sample_rate', 'channels', 'duration', 'duration_ts')}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', type=Path, default=SOURCES)
    parser.add_argument('--ffmpeg', type=Path, default=ROOT / 'run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
    args = parser.parse_args()
    files = []
    for number, tier, rarities, expected in ROWS:
        source = args.sources / f'File{number:04d}.wav'
        assert digest(source) == expected, f'Source changed: {source}'
        target = ROOT / f'src/main/resources/assets/destiny/sounds/loot/acquire_{tier}.ogg'
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(args.ffmpeg), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                        '-i', str(source), '-map_metadata', '-1', '-c:a', 'libvorbis', '-q:a', '6', str(target)], check=True)
        before, after = probe(source), probe(target)
        for key in ('sample_rate', 'channels', 'duration_ts'):
            assert before[key] == after[key], (source, key, before, after)
        assert after['codec_name'] == 'vorbis'
        # Verify the complete output decodes, including the long exotic tail.
        subprocess.run([str(args.ffmpeg), '-nostdin', '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True)
        files.append(dict(source=str(source), sourceSha256=expected, sourceInfo=before,
                          output=str(target.relative_to(ROOT)), outputSha256=digest(target),
                          outputBytes=target.stat().st_size, outputInfo=after,
                          rarities=rarities, soundEvent=f'destiny:loot.acquire.{tier}'))
        assert digest(source) == expected
    manifest = dict(source='User supplied 2026-11-09; rarity mapping explicitly specified by user',
                    conversion='libvorbis quality 6; no trim, gain, remix, resampling or pitch change',
                    ffmpeg=str(args.ffmpeg), ffmpegSha256=digest(args.ffmpeg), files=files)
    target = ROOT / 'art/audio/loot-acquisition/manifest.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    fragment = {f['soundEvent'].split(':', 1)[1]: dict(replace=True, sounds=[dict(
        name='destiny:loot/acquire_' + f['soundEvent'].rsplit('.', 1)[1], stream=False)]) for f in files}
    target.with_name('sounds-fragment.json').write_text(json.dumps(fragment, indent=2) + '\n')
    print(json.dumps(dict(bytes=sum(f['outputBytes'] for f in files), files=files), indent=2))

if __name__ == '__main__':
    main()
