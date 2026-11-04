#!/usr/bin/env python3
"""W207 Hammerhead: remodeled W123 parts, 61 C1-continuous reload poses.

Import is inert. generate() returns absolute Path -> bytes; the master owns
writing these new assets and applying shared W206 framing/skin-arm overlays.
"""
import bisect
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w207/hammerhead'
KEY = 'weapon_reload_w207_hammerhead/hammerhead'
PARTS = ('body', 'magazine', 'cover')
FP = ('firstperson_righthand', 'firstperson_lefthand')
STEPS = 60
# Retained W114 gameplay-informed timing, NOT recovered source animation.
# progress, body XYZ degrees, view translation, magazine local offset, cover X.
KEYS = (
    (0, (0, 0, 0), (0, 0, 0), (0, 0, 0), 0),
    (.10, (3, -10, -10), (-1.4, 2.8, -.5), (0, 0, 0), 0),
    (.23, (8, -18, -22), (-3.4, 6, -1.4), (0, 0, 0), -78),
    (.34, (10, -22, -28), (-3.6, 6.4, -1.8), (-1.2, -4.5, .3), -92),
    (.48, (10, -22, -28), (-3.6, 6.4, -1.8), (-2.8, -5.2, .8), -92),
    (.63, (8, -20, -26), (-3.4, 6.2, -1.6), (-.6, -2, .2), -92),
    (.72, (8, -20, -24), (-3.2, 5.8, -1.4), (0, 0, 0), -88),
    (.82, (7, -16, -20), (-2.8, 4.5, -1), (0, 0, 0), 0),
    (.90, (13, -10, -9), (-1.3, 2.3, -.5), (0, 0, 0), 0),
    (1, (0, 0, 0), (0, 0, 0), (0, 0, 0), 0),
)
TIMES = tuple(k[0] for k in KEYS)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def tangents(values):
    """Nonuniform PCHIP interior slopes; rest endpoints and plateaus have zero slope.

    Weighted harmonic means preserve monotone spans without overshoot. One shared
    derivative at each knot makes adjacent Hermite pieces C1. Unlike per-segment
    smoothstep, ordinary internal movement keys retain nonzero velocity.
    """
    h = [b - a for a, b in zip(TIMES, TIMES[1:])]
    sec = [(b - a) / dt for a, b, dt in zip(values, values[1:], h)]
    result = [0.0] * len(values)
    for i in range(1, len(values) - 1):
        before, after = sec[i - 1], sec[i]
        if before * after > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            result[i] = (w1 + w2) / (w1 / before + w2 / after)
    return tuple(result)


CHANNELS = tuple(tuple((*k[1], *k[2], *k[3], k[4])[c] for k in KEYS)
                 for c in range(10))
TANGENTS = tuple(tangents(v) for v in CHANNELS)


def sample(progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError(progress)
    i = min(len(TIMES) - 2, max(0, bisect.bisect_right(TIMES, progress) - 1))
    h = TIMES[i + 1] - TIMES[i]
    u = (progress - TIMES[i]) / h
    h00, h10 = 2*u**3 - 3*u*u + 1, u**3 - 2*u*u + u
    h01, h11 = -2*u**3 + 3*u*u, u**3 - u*u
    values = [v[i] if v[i] == v[i+1] else
              h00*v[i] + h10*h*m[i] + h01*v[i+1] + h11*h*m[i+1]
              for v, m in zip(CHANNELS, TANGENTS)]
    return values[:3], values[3:6], values[6:9], values[9]


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vec(m, v):
    return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]


def xyz(angles):
    a, b, c = map(math.radians, angles)
    rx = [[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]]
    ry = [[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]]
    rz = [[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]]
    return mul(rx, mul(ry, rz))


def euler(m):
    return [round(math.degrees(v), 8) for v in
            (math.atan2(-m[1][2], m[2][2]), math.asin(max(-1, min(1, m[0][2]))),
             math.atan2(-m[0][1], m[0][0]))]


def pose_for(part, frame, base, pivot):
    result = copy.deepcopy(base)
    if frame in (0, STEPS):
        return result  # Preserve accepted idle literally, including float representation.
    rotation, translation, feed, angle = sample(frame / STEPS)
    for ctx in FP:
        d = result[ctx]
        # These are bounded, authored W114 Euler channels, with no angular wrap.
        angles = [a+b for a, b in zip(d['rotation'], rotation)]
        body = xyz(angles)
        local = feed if part == 'magazine' else [0, 0, 0]
        if part == 'cover':
            cover = xyz([angle, 0, 0])
            turned = vec(cover, pivot)
            local = [a-b for a, b in zip(pivot, turned)]
            # Hinged cover and its sight rotate together; p-Rp holds the hinge.
            d['rotation'] = euler(mul(body, cover))
        else:
            d['rotation'] = [round(v, 8) for v in angles]
        offset = vec(body, [v*s for v, s in zip(local, d['scale'])])
        d['translation'] = [round(a+b+c, 8) for a, b, c in
                            zip(d['translation'], translation, offset)]
    return result


def twohand(display, accepted):
    """W32 charged-crossbow carrier compensation, preserving non-FP displays."""
    result = copy.deepcopy(accepted)
    compensation = xyz([0, -10, 0])
    for ctx in FP:
        d = copy.deepcopy(display[ctx])
        x, y, z = d['translation']
        d['translation'] = [round(v, 8) for v in vec(compensation, [x+.641864*16, y, z])]
        d['rotation'] = euler(mul(compensation, xyz(d['rotation'])))
        result[ctx] = d
    return result


def expected_output_paths():
    paths = {ASSETS / f'items/{KEY}.json', ART / 'manifest.json'}
    for part in PARTS:
        paths.add(ASSETS / f'models/{KEY}_{part}.json')
        for frame in range(STEPS + 1):
            for grip in ('native', 'twohand'):
                paths.add(ASSETS / f'models/{KEY}_{frame:02}_{part}_{grip}.json')
    return paths


def generate():
    inputs = {}

    def read(path):
        raw = path.read_bytes()
        inputs[str(path.relative_to(ROOT))] = sha(raw)
        return json.loads(raw)

    surface = read(ASSETS / 'models/weapon_surface_w123/hammerhead.json')
    geometry = {part: read(ASSETS / f'models/weapon_surface_w123/hammerhead_{part}.json')
                for part in PARTS}
    accepted_two = read(ASSETS / 'models/weapon/machine_gun/hammerhead_twohand.json')['display']
    item = read(ASSETS / 'items/weapon/hammerhead.json')
    design = read(ROOT / 'art/weapons/w123/hammerhead/design.json')
    # Historical footage metadata is evidence only, not an executable dependency.
    read(ROOT / 'art/weapons/w114/hammerhead/gameplay-provenance.json')
    assert surface['elements'] == [e for part in PARTS for e in geometry[part]['elements']]
    assert all(geometry[p]['textures'] == surface['textures'] for p in PARTS)
    assert design['belt_feed_w154']['tip_axis'] == [0, 0, -1]
    pivot = [v-8 for v in design['cover_pivot']]
    native = surface['display']
    output = {ASSETS / f'models/{KEY}_{p}.json': encode(geometry[p]) for p in PARTS}
    entries = []
    for frame in range(STEPS + 1):
        branches = {g: [] for g in ('native', 'twohand')}
        for part in PARTS:
            pose = pose_for(part, frame, native, pivot)
            for grip in branches:
                display = pose if grip == 'native' else (
                    copy.deepcopy(accepted_two) if frame in (0, STEPS) else twohand(pose, accepted_two))
                name = f'{KEY}_{frame:02}_{part}_{grip}'
                output[ASSETS / f'models/{name}.json'] = encode(
                    {'parent': f'destiny:{KEY}_{part}', 'display': display})
                branches[grip].append({'type': 'minecraft:model', 'model': 'destiny:'+name})
        entries.append({'threshold': frame / STEPS, 'model': {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': {'type': 'minecraft:composite', 'models': branches['twohand']},
            'on_false': {'type': 'minecraft:composite', 'models': branches['native']}}})
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {
        'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': {
            'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
            'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}}],
        'fallback': copy.deepcopy(item['model'])}
    output[ASSETS / f'items/{KEY}.json'] = encode(wrapper)
    output[ART / 'manifest.json'] = encode({
        'schemaVersion': 1, 'stage': 'W207', 'weapon': 'hammerhead', 'graphId': 'destiny:'+KEY,
        'generator': 'scripts/generate_reload_w207_hammerhead.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'frames': STEPS+1, 'quantization': STEPS, 'progressFloatIndex': 1, 'gripBooleanIndex': 0,
        'parts': list(PARTS), 'partCounts': {p: len(geometry[p]['elements']) for p in PARTS},
        'keyframes': KEYS, 'interpolation': 'C1 nonuniform monotone Hermite; shared PCHIP interior tangents; rest endpoints',
        'coverPivot': design['cover_pivot'], 'sourceSha256': inputs,
        'assetSha256': {str(p.relative_to(ROOT)): sha(v) for p, v in output.items()},
        'originalGraphFallbackExact': True, 'endpointsExactBaseDisplay': True,
        'wholeGeometryUVTextureUnchanged': True, 'gameplayDurationChanged': False,
        'nativeGameplayVerified': False, 'sourceAnimationRecovered': False,
        'reference': 'https://www.youtube.com/watch?v=1lHv7453rUI&t=101',
        'limitations': [
            '61 pose bank is not a 60fps claim: item-state updates can remain server 20Hz.',
            'W114 authored motion/timing retained; rigid belt and generic hand following are not recovered IK.',
            'Master applies shared W206 framing and skin arms once after generating this unframed bank.',
            'Native hip, ADS exit, both grip modes, cover/feed clearance and reload continuity pending master.']})
    assert set(output) == expected_output_paths()
    assert all(p.is_absolute() and isinstance(v, bytes) for p, v in output.items())
    return output
