#!/usr/bin/env python3
"""Convert the user-provided reward chest cue, retaining the complete decoded MP3 recording."""
import argparse
import json
from pathlib import Path
import subprocess
from build_loot_acquisition_audio import ROOT, digest, probe

SOURCE_HASH = 'e83c126dc8f306c64e32e21754d44a56a3f378e251e2fddb616a0fc2df4ef458'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path('/Users/qf/Downloads/0242-00001106.mp3'))
    parser.add_argument('--ffmpeg', type=Path, default=ROOT / 'run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
    args = parser.parse_args()
    assert digest(args.source) == SOURCE_HASH
    before = probe(args.source)
    pcm = subprocess.check_output([str(args.ffmpeg), '-nostdin', '-v', 'error', '-i', str(args.source), '-f', 's16le', '-acodec', 'pcm_s16le', '-'])
    frames = len(pcm) // (2 * before['channels'])
    target = ROOT / 'src/main/resources/assets/destiny/sounds/loot/chest_open.ogg'
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(args.ffmpeg), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(args.source),
                    '-map_metadata', '-1', '-c:a', 'libvorbis', '-q:a', '6', str(target)], check=True)
    after = probe(target)
    assert after['codec_name'] == 'vorbis' and before['channels'] == after['channels'] == 2
    assert before['sample_rate'] == after['sample_rate'] == '48000' and frames == after['duration_ts']
    subprocess.run([str(args.ffmpeg), '-nostdin', '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True)
    assert digest(args.source) == SOURCE_HASH
    manifest = dict(source=str(args.source), sourceSha256=SOURCE_HASH, sourceInfo=before, sourceDecodedFrames=frames,
                    output=str(target.relative_to(ROOT)), outputInfo=after, outputSha256=digest(target), outputBytes=target.stat().st_size,
                    soundEvent='destiny:loot.chest.open', sourceDeclaration='User supplied: successful strike reward chest opening',
                    conversion='libvorbis quality 6; full decoder output with standard MP3 delay/padding handling; no artistic trim, gain, remix, resampling or pitch change',
                    ffmpeg=str(args.ffmpeg), ffmpegSha256=digest(args.ffmpeg))
    art = ROOT / 'art/audio/reward-chest'
    art.mkdir(parents=True, exist_ok=True)
    (art / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (art / 'sounds-fragment.json').write_text(json.dumps({'loot.chest.open':dict(replace=True,sounds=[dict(name='destiny:loot/chest_open',stream=False)])},indent=2) + '\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
