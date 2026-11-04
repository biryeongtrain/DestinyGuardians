#!/usr/bin/env python3
"""W208 Recluse: 61 poses, continuous W101 motion, current W126 parts.

Import and generate() never write. The batch integrator owns output writes.
This is authored reference-informed motion, not recovered source-camera/hand IK.
A 61-pose bank removes /20 quantization; network item states remain server-paced.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
SURFACE = ASSET / "models/weapon_surface_w123"
ITEM = ASSET / "items/weapon/the_recluse.json"
TWOHAND = ASSET / "models/weapon/submachine_gun/the_recluse_twohand.json"
KEY = "weapon_reload_w208_the_recluse/the_recluse"
MANIFEST = Path("art/weapons/w208/the_recluse/manifest.json")
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
INTERVALS = 60
SAMPLES = INTERVALS + 1
# Exact W101 authored knots: body hold .24..68, detached magazine hold .40..52,
# seated magazine through .12 and from .78. No source camera/seconds claim.
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.12, (4, -10, -14), (-2, 4, -1), (0, 0, 0)), (0.24, (8, -20, -28), (-4.5, 8, -2), (0.3, -1.5, 0)), (0.4, (8, -22, -32), (-4.5, 8, -2), (0.5, -4.2, 0.3)), (0.52, (7, -20, -30), (-4.5, 8, -2), (0.5, -4.2, 0.3)), (0.68, (6, -18, -28), (-4.5, 8, -2), (0.2, -1.8, 0.1)), (0.78, (8, -16, -26), (-4.2, 7.5, -1.8), (0, 0, 0)), (0.86, (5, -10, -16), (-2.5, 4.5, -1), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]


def tangents(times, values):
    """Shape-preserving PCHIP: shared derivative at knots; zero at holds/extrema.

    Weighted harmonic means preserve monotone spans without overshoot. Endpoint
    slopes are explicitly zero to settle into and out of the accepted idle pose.
    """
    steps = [b-a for a, b in zip(times, times[1:])]
    secants = [(b-a)/h for a, b, h in zip(values, values[1:], steps)]
    slopes = [0.0] * len(times)
    for i in range(1, len(times)-1):
        before, after = secants[i-1], secants[i]
        if before * after > 0:
            w1 = 2*steps[i] + steps[i-1]
            w2 = steps[i] + 2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before + w2/after)
    return slopes


def sample(progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) for v in key[1:])
    times = [k[0] for k in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    result = []
    for channel in range(1, 4):
        vector = []
        for axis in range(3):
            values = [k[channel][axis] for k in KEYS]
            slopes = tangents(times, values)
            vector.append(h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vec(m, v):
    return [sum(m[i][j]*v[j] for j in range(3)) for i in range(3)]


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(m):
    y = math.asin(max(-1, min(1, m[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0])
    else:
        x, z = math.atan2(m[2][1], m[1][1]), 0
    return [round(math.degrees(v), 9) for v in (x, y, z)]


def pose_display(original, twohand, progress, part, grip):
    accepted = original if grip == "native" else twohand
    if progress in (0, 1):
        return copy.deepcopy(accepted)
    rotation, translation, magazine = sample(progress)
    display = copy.deepcopy(accepted)
    for context in FP:
        idle = original[context]
        if max(idle['scale'])-min(idle['scale']) > 1e-8:
            raise ValueError("Recluse reload requires uniform accepted FP scale")
        # Retain W101's authored display-space Euler/body shift convention.
        angles = [v+rotation[i] for i, v in enumerate(idle['rotation'])]
        matrix = xyz(angles)
        offset = vec(matrix, magazine) if part == "magazine" else (0, 0, 0)
        position = [v+translation[i]+offset[i]*idle['scale'][i]
                    for i, v in enumerate(idle['translation'])]
        if grip == "twohand":
            # Derive the static carrier compensation from accepted poses rather
            # than reconstructing or changing any third-person display.
            base = xyz(idle['rotation'])
            compensation = mul(xyz(twohand[context]['rotation']), [list(v) for v in zip(*base)])
            base_position = vec(compensation, idle['translation'])
            shift = [v-base_position[i] for i, v in enumerate(twohand[context]['translation'])]
            position = [v+shift[i] for i, v in enumerate(vec(compensation, position))]
            matrix = mul(compensation, matrix)
            angles = euler(matrix)
        display[context]['rotation'] = [round(v, 9) for v in angles]
        display[context]['translation'] = [round(v, 9) for v in position]
    return display


def generate(root=ROOT):
    """Return absolute output paths -> bytes, solely in the W208 namespace."""
    root = Path(root).resolve()
    inputs = [SURFACE/'the_recluse.json', SURFACE/'the_recluse_body.json',
              SURFACE/'the_recluse_magazine.json', TWOHAND, ITEM,
              Path('scripts/generate_reload_framing_w101.py'),
              Path('scripts/generate_reload_models_w100.py'),
              Path('art/weapons/w123/the_recluse/design.json'),
              Path('art/weapons/w123/the_recluse/manifest.json'),
              Path('art/weapons/w201/contacts.json'),
              Path('art/weapons/w205/rigs/submachine_gun_dc16526f.json'),
              Path('art/weapons/w208/the_recluse/profile.json')]
    source = json.loads((root/inputs[0]).read_bytes())
    geometries = {part: json.loads((root/SURFACE/f'the_recluse_{part}.json').read_bytes()) for part in PARTS}
    twohand = json.loads((root/TWOHAND).read_bytes())['display']
    item = json.loads((root/ITEM).read_bytes())
    # Verify the semantic split, including every face UV, against current full.
    from collections import Counter
    packed = lambda e: json.dumps(e, sort_keys=True, separators=(',', ':'))
    joined = [e for part in PARTS for e in geometries[part]['elements']]
    if Counter(map(packed, joined)) != Counter(map(packed, source['elements'])):
        raise ValueError('Current Recluse body/magazine do not partition canonical surface')
    counts = {part: len(geometries[part]['elements']) for part in PARTS}
    if counts != {'body': 62, 'magazine': 4}:
        raise ValueError('Recluse remodeled partition changed; re-audit current parts')
    output = {}
    def emit(path, value):
        allowed = (ASSET/'models/weapon_reload_w208_the_recluse', ASSET/'items/weapon_reload_w208_the_recluse')
        if path != MANIFEST and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError('Output outside W208 Recluse namespace')
        output[root/path] = encode(value)
    for part in PARTS:
        geo = copy.deepcopy(geometries[part])
        geo.pop('display', None)
        emit(ASSET/f'models/{KEY}_{part}.json', geo)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ('native', 'twohand'):
                emit(ASSET/f'models/{KEY}_{frame:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand, progress, part, grip)})
        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{frame:02}_{part}_{grip}'} for part in PARTS]}
        model = copy.deepcopy(item['model']) if frame in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': model})
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': {
            'type': 'minecraft:select', 'property': 'minecraft:custom_model_data', 'index': 0,
            'cases': [{'when': ['ads', 'inspect'], 'model': copy.deepcopy(item['model'])}],
            'fallback': {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data', 'index': 1,
            'entries': entries, 'fallback': copy.deepcopy(item['model'])}}}],
        'fallback': copy.deepcopy(item['model'])}
    emit(ASSET/f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'stage': 'W208', 'generator': 'scripts/generate_reload_w208_the_recluse.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': f'destiny:{KEY}', 'weapon': 'the_recluse', 'frames': SAMPLES,
        'intervals': INTERVALS, 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'thresholdEncoding': 'float32(i/60), matching runtime float quantization',
        'curve': 'C1 shape-preserving cubic Hermite with weighted harmonic knot tangents; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'sourceCubes': len(source['elements']), 'partCubes': counts,
        'maxAssembledElements': len(joined), 'geometryAndUVUnchanged': True,
        'endpointDisplayExact': True, 'fallbackModelExact': True,
        'gameplayTimingChanged': False, 'nativeGameplayVerified': False,
        'evidence': ['https://www.youtube.com/watch?v=nnr9-n3CdhI',
                     'art/weapons/w100/reference-notes.md',
                     'art/weapons/w123/the_recluse/comparison.png'],
        'assets': len(output), 'partHint': 'magazine', 'rigAction': '80A8A192',
        'authoredTimingSource': 'scripts/generate_reload_framing_w101.py',
        'sourceCameraRecovered': False, 'nativeVisibilityAccepted': False,
        'limitations': ['Authored W101 reference motion, not recovered source IK.',
                       '61 bank poses remove /20 quantization; server updates remain up to 20Hz, not proof of 60fps.',
                       'Shared runtime routing, hands following and native review belong to master.'],
        'inputSha256': {str(p): sha((root/p).read_bytes()) for p in inputs},
        'outputSha256': {str(p.relative_to(root)): sha(raw) for p, raw in output.items()}})
    return output
