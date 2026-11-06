#!/usr/bin/env python3
"""Deterministic authored approximation, never an extracted D2 skull/background."""
import json
import math
import hashlib
import os
import shutil
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


def original_banner_crop():
    """Original shape crop with user-requested black-paper-to-alpha colour decomposition only."""
    source = ROOT / 'art/hud/activity-failure-w329/user-source/wipe-original.png'
    data = source.read_bytes(); offset = 8; packed = b''
    while offset < len(data):
        size = struct.unpack('>I', data[offset:offset+4])[0]
        kind, value = data[offset+4:offset+8], data[offset+8:offset+8+size]
        if kind == b'IHDR': w, h, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', value)
        if kind == b'IDAT': packed += value
        offset += size + 12
    if depth != 8 or color not in [2, 6] or interlace != 0: raise ValueError('Unsupported original PNG encoding')
    channels = 4 if color == 6 else 3; stride = w * channels; decoded = zlib.decompress(packed)
    rows = []; previous = bytearray(stride); position = 0
    def paeth(a, b, c):
        p = a+b-c; ds = [abs(p-a), abs(p-b), abs(p-c)]
        return [a, b, c][ds.index(min(ds))]
    for y in range(h):
        mode = decoded[position]; position += 1
        row = bytearray(decoded[position:position+stride]); position += stride
        for i in range(stride):
            left = row[i-channels] if i >= channels else 0
            up = previous[i]; corner = previous[i-channels] if i >= channels else 0
            predictor = [0, left, up, (left+up)//2, paeth(left, up, corner)][mode]
            row[i] = (row[i]+predictor) & 255
        rows.append(bytes(row)); previous = row
    if (w, h) != (1107, 702): raise ValueError('Source dimensions changed; crop must be reviewed')
    def pixel(x, y):
        value = tuple(rows[y][x*channels:(x+1)*channels])
        rgb = value[:3]; neutral = min(rgb)
        # Remove only the neutral dark-paper pedestal; preserve every chromatic red-line residual.
        white = max(0, (neutral - 24) * 255 / 231)
        premultiplied = [min(255, white + c - neutral) for c in rgb]
        alpha = max(premultiplied)
        if alpha <= 0: return (0, 0, 0, 0)
        return tuple(round(c * 255 / alpha) for c in premultiplied) + (round(alpha),)
    png(ASSETS / 'textures/gui/failure_banner.png', 460, 702, pixel)
    for step in range(1, 8):
        png(ASSETS / ('textures/gui/failure_banner_f0' + str(step) + '.png'), 460, 702,
            lambda x, y, s=step: pixel(x, y)[:3] + (round(pixel(x, y)[3] * s / 8),))


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


names = ['restricted', 'wipe', 'backdrop', 'failure_banner', 'table_row', 'rule'] + ['black_' + str(n) for n in range(9)]
names += [base + '_f0' + str(step) for base in ['failure_banner', 'table_row', 'rule'] for step in range(1, 8)]
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
original_banner_crop()
for retired in ['failure_skull', 'failure_lines']:
    for folder, extension in [('items', '.json'), ('models', '.json'), ('textures', '.png')]:
        (ASSETS / (folder + '/gui/' + retired + extension)).unlink(missing_ok=True)
png(ASSETS / 'textures/gui/table_row.png', 2, 2, lambda x, y: (255, 255, 255, 70))
png(ASSETS / 'textures/gui/rule.png', 2, 2, lambda x, y: (255, 255, 255, 255))
for step in range(1, 8):
    png(ASSETS / ('textures/gui/table_row_f0' + str(step) + '.png'), 2, 2, lambda x, y, s=step: (255, 255, 255, round(70*s/8)))
    png(ASSETS / ('textures/gui/rule_f0' + str(step) + '.png'), 2, 2, lambda x, y, s=step: (255, 255, 255, round(255*s/8)))
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
