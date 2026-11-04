#!/usr/bin/env python3
"""Split existing W33 shotgun source into paid-insert / natural-final cues. No downloads.

rtk proxy python3 scripts/audio/build_shotgun_reload_sounds_w210.py [--check]
"""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'src/main/resources'
SOURCE = RES / 'assets/destiny/sounds/w33/weapon/shotgun/reload.ogg'
EXPECTED = 'ce2d804c3981daff6ff9ee6f120c1a8ce9ecc7ea80a2c2dd001837af9c96af9f'
RATE = 32000
INSERT = (43840, 55040)  # existing OGG [1.370, 1.720)
CLOSE = (95040, 125120)  # existing OGG [2.970, 3.910)
GAP = 1920  # authored 60ms gap, not an extracted animation event


def document(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    ffmpeg = shutil.which('ffmpeg') or str(ROOT / 'run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')

    def audio(arguments, data=None):
        return subprocess.run(['rtk', 'proxy', ffmpeg, '-hide_banner', '-v', 'error', *arguments],
                              input=data, capture_output=True, check=True).stdout

    def decode(path):
        values = array.array('f', audio(['-i', str(path), '-ac', '1', '-ar', str(RATE), '-f', 'f32le', '-']))
        if sys.byteorder != 'little':
            values.byteswap()
        assert values and all(math.isfinite(x) for x in values)
        return values

    def fade(values):
        values = list(values)
        for i in range(64):
            values[i] *= i / 63
        for i in range(256):
            values[-256 + i] *= (255 - i) / 255
        return values

    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED, 'W33 source drift'
    provenance = json.loads((RES / 'destiny/sounds/w33.json').read_text())['events']['weapon.shotgun.reload']
    samples = decode(SOURCE)
    assert len(samples) == 125120
    insert, close = fade(samples[slice(*INSERT)]), fade(samples[slice(*CLOSE)])
    final = insert + [0.0] * GAP + close
    assert final[:len(insert)] == insert
    generated = {}
    assets = {}
    with tempfile.TemporaryDirectory(prefix='destiny-w210-shell-audio-') as temp:
        for name, values in [('insert', insert), ('finish', final)]:
            pcm = array.array('f', values)
            if sys.byteorder != 'little':
                pcm.byteswap()
            output = Path(temp) / (name + '.ogg')
            audio(['-y', '-f', 'f32le', '-ar', str(RATE), '-ac', '1', '-i', 'pipe:0', '-c:a', 'libvorbis',
                   '-q:a', '4', '-fflags', '+bitexact', '-flags:a', '+bitexact', str(output)], pcm.tobytes())
            decoded = decode(output)
            assert abs(len(decoded) - len(values)) <= 1024 and max(abs(x) for x in decoded) < 1
            relative = 'assets/destiny/sounds/w210/shotgun/' + name + '.ogg'
            data = output.read_bytes()
            generated[RES / relative] = data
            assets[name] = dict(asset=relative, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                                preparedSamples=len(values), decodedSamples=len(decoded),
                                peakDbfs=round(20 * math.log10(max(abs(x) for x in decoded)), 5))
    manifest = dict(source='assets/destiny/sounds/w33/weapon/shotgun/reload.ogg', sourceSha256=EXPECTED,
                    originalName=provenance['original_name'], sourceFolder=provenance['source_folder'],
                    sourceUrl=provenance['source_url'], encoderVersion=audio(['-version']).decode().splitlines()[0],
                    sampleRateHz=RATE, channels=1, insertionSamples=INSERT, closingSamples=CLOSE,
                    authoredGapSamples=GAP, fadeInSamples=64, fadeOutSamples=256, pitchChange=False,
                    gainChangeDb=0, assets=assets,
                    lifecycle='One cue per real positive shell transfer; finish replaces insert only on natural completion. No cue on cancellation.',
                    limitations=['Mindbenders Ambition family representative; not an exact FILO recording.',
                                 'Waveform-derived cuts pending user semantic listening review; no acoustic-output proof.',
                                 'Final cue includes insertion, 60ms authored gap, then closing tail; it may continue after a shot made after natural completion.'])
    generated[ROOT / 'art/weapons/w210/shotgun-audio-manifest.json'] = document(manifest)
    sound_path = RES / 'assets/destiny/sounds.json'
    sounds = json.loads(sound_path.read_text())
    for name in ('insert', 'finish'):
        sounds['weapon.shotgun.reload_' + name] = {
            'subtitle': 'subtitles.destiny.weapon.shotgun.reload_' + name,
            'sounds': [{'name': 'destiny:w210/shotgun/' + name, 'stream': False, 'attenuation_distance': 32}]}
    generated[sound_path] = document(sounds)
    for locale, insert_label, finish_label in [('en_us', 'Shotgun shell inserted', 'Shotgun reload complete'),
                                              ('ko_kr', '산탄총 탄 삽입', '산탄총 장전 마무리')]:
        path = RES / 'assets/destiny/lang' / (locale + '.json')
        strings = json.loads(path.read_text())
        strings.update({'subtitles.destiny.weapon.shotgun.reload_insert': insert_label,
                        'subtitles.destiny.weapon.shotgun.reload_finish': finish_label})
        generated[path] = document(strings)
    for path, data in generated.items():
        if args.check:
            assert path.read_bytes() == data, 'Generated audio drift: ' + str(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps(dict(checked=args.check, outputs=len(generated), assets=assets)))


if __name__ == '__main__':
    main()
