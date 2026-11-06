#!/usr/bin/env python3
"""Deterministic authored approximation, never an extracted D2 skull/background."""
import json
import math
import hashlib
import os
import struct
import subprocess
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'src/main/resources/assets/destiny_activity_failure'
FFMPEG = os.environ.get('FFMPEG', str(ROOT / 'run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'))
FFPROBE = os.environ.get('FFPROBE', 'ffprobe')


def png(path, w, h, pixel):
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value))
    raw = b''.join(b'\0' + bytes(v for x in range(w) for v in pixel(x, y)) for y in range(h))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def distance(x, y, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((x-a[0])*vx + (y-a[1])*vy) / (vx*vx+vy*vy)))
    return math.hypot(x - a[0] - t*vx, y - a[1] - t*vy)


def skull(x, y):
    head = ((x-128)/43)**2 + ((y-112)/43)**2 <= 1
    jaw = 99 <= x <= 157 and 117 <= y <= 164
    teeth = 102 <= x <= 154 and 164 <= y <= 177 and int((x-102)/8) % 2 == 0
    eyes = ((x-108)/14)**2 + ((y-117)/11)**2 <= 1 or ((x-148)/14)**2 + ((y-117)/11)**2 <= 1
    nose = 135 <= y <= 149 and abs(x-128) <= (y-135)*.55
    return (head or jaw or teeth) and not eyes and not nose


def icon(kind):
    points = [(128, 15), (241, 128), (128, 241), (15, 128)] if kind == 'restricted' else [(22, 48), (234, 48), (128, 236)]
    def pixel(x, y):
        line = min(distance(x, y, a, b) for a, b in zip(points, points[1:] + points[:1]))
        if skull(x, y): return (223, 63, 59, 255) if kind == 'restricted' else (238, 239, 233, 255)
        if line < 2: return (203, 59, 56, 255)
        if kind == 'restricted' and abs(abs(x-128)+abs(y-128)-123) < 1: return (219, 221, 215, 230)
        return (0, 0, 0, 0)
    return pixel


names = ['restricted', 'wipe', 'backdrop'] + ['black_' + str(n) for n in range(9)]
for kind in ['restricted', 'wipe']:
    png(ASSETS / ('textures/gui/' + kind + '.png'), 256, 256, icon(kind))
for n in range(9):
    png(ASSETS / ('textures/gui/black_' + str(n) + '.png'), 2, 2, lambda x, y, a=round(n*255/8): (0, 0, 0, a))


def backdrop(x, y):
    # A new quiet geometric field, no copied pixels or branded portfolio background.
    grid = abs((x + y*.577) % 48 - 24) < .4 or abs((x-y*.577) % 48 - 24) < .4 or y % 42 == 0
    edge = min(1, math.hypot((x-256)/340, (y-144)/195))
    v = round((17 if grid else 10) * (1-edge*.65))
    return (v, v+1, v+2, 255)


png(ASSETS / 'textures/gui/backdrop.png', 512, 288, backdrop)
for name in names:
    item = ASSETS / ('items/gui/' + name + '.json')
    model = ASSETS / ('models/gui/' + name + '.json')
    item.parent.mkdir(parents=True, exist_ok=True)
    model.parent.mkdir(parents=True, exist_ok=True)
    item.write_text(json.dumps({'model': {'type': 'minecraft:model', 'model': 'destiny_activity_failure:gui/' + name,
        'tints': [{'type': 'minecraft:custom_model_data', 'index': 0, 'default': 16777215}]}}) + '\n')
    model.write_text(json.dumps({'gui_light': 'front', 'textures': {'layer0': 'destiny_activity_failure:gui/' + name},
        'elements': [{'from': [0, 0, 8], 'to': [16, 16, 8], 'faces': {
            face: {'texture': '#layer0', 'uv': [0, 0, 16, 16], 'tintindex': 0} for face in ['north', 'south']}}]}) + '\n')

# 26.3 only auto-collects textures/item and textures/block. Custom gui/ sprites need explicit sources.
atlas_path = ROOT / 'src/main/resources/assets/minecraft/atlases/items.json'
atlas = json.loads(atlas_path.read_text()) if atlas_path.exists() else {'sources': []}
atlas['sources'] = [s for s in atlas.get('sources', [])
    if not str(s.get('resource', '')).startswith('destiny_activity_failure:')]
atlas['sources'] += [{'type': 'minecraft:single', 'resource': 'destiny_activity_failure:gui/' + name,
    'sprite': 'destiny_activity_failure:gui/' + name} for name in names]
atlas_path.parent.mkdir(parents=True, exist_ok=True)
atlas_path.write_text(json.dumps(atlas, indent=2) + '\n')

# User-selected originals, archived verbatim. A rebuild must never restore provisional chirp aliases.
audio_root = ROOT / 'art/audio/activity-failure-w329'
selected = json.loads((audio_root / 'sources.json').read_text())['selected']
audio = []
for source in selected:
    original = audio_root / source['file']
    if hashlib.sha256(original.read_bytes()).hexdigest() != source['sourceSha256']:
        raise RuntimeError('Source archive hash mismatch: ' + str(original))
    output = ASSETS / ('sounds/sfx/' + source['event'] + '.ogg')
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(original),
        '-map', '0:a:0', '-vn', '-c:a', 'libvorbis', '-q:a', '5', '-map_metadata', '-1',
        '-fflags', '+bitexact', '-flags:a', '+bitexact', str(output)], check=True)

    def probe(path):
        info = json.loads(subprocess.check_output([FFPROBE, '-v', 'error', '-show_entries',
            'stream=sample_rate,channels:format=duration', '-of', 'json', str(path)]))
        stream = info['streams'][0]
        pcm = subprocess.check_output([FFMPEG, '-v', 'error', '-i', str(path), '-map', '0:a:0',
            '-f', 's16le', '-c:a', 'pcm_s16le', '-'])
        return {'sampleRate': int(stream['sample_rate']), 'channels': int(stream['channels']),
            'containerSeconds': float(info['format']['duration']),
            'decodedFrames': len(pcm) // (2 * stream['channels'])}

    before, after = probe(original), probe(output)
    if (before['sampleRate'], before['channels'], before['decodedFrames']) != (after['sampleRate'], after['channels'], after['decodedFrames']):
        raise RuntimeError('Full decoded duration/channel preservation failed for ' + source['event'])
    audio.append(dict(source, sourceArchive=str(original.relative_to(ROOT)), sourceProbe=before,
        output=str(output.relative_to(ROOT)), outputSha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        outputBytes=output.stat().st_size, outputProbe=after,
        conversion='Full decoded frames, channels and sample rate preserved; Vorbis quality5; no trim, normalization, filters or pitch changes.'))
(audio_root / 'conversion.json').write_text(json.dumps({'audio': audio,
    'ffmpegSha256': hashlib.sha256(Path(FFMPEG).read_bytes()).hexdigest()}, ensure_ascii=False, indent=2) + '\n')
events = {}
for event in ['restricted_entry', 'team_wipe']:
    for suffix in [''] + ['_' + str(n) for n in range(64)]:
        events[event + suffix] = {'sounds': [{'name': 'destiny_activity_failure:sfx/' + event, 'stream': False}]}
(ASSETS / 'sounds.json').write_text(json.dumps(events, indent=2) + '\n')

provenance = ROOT / 'art/hud/activity-failure-w329/provenance.json'
metadata = json.loads(provenance.read_text())
metadata['audio'] = audio
metadata['policyTiming']['wipePresentationTicks'] = 230
metadata['atlasRegistration'] = {'path': str(atlas_path.relative_to(ROOT)),
    'sha256': hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
    'reason': '26.3 item/block atlas defaults do not scan custom textures/gui paths;12 exact single sources register the owned HUD sprites in minecraft:items without broad directory expansion.'}
metadata['resources'] = [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    'bytes': p.stat().st_size} for p in sorted(ASSETS.rglob('*')) if p.is_file()]
provenance.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
print('Generated', len(names), 'small HUD images/models and replaceable audio events in', ASSETS)
