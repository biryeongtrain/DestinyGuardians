#!/usr/bin/env python3
"""Beloved reference-informed body + moving magazine; original models remain byte-identical.

21 sampled first-person poses, native/two-hand compensation, exact original fallback elsewhere.
Not ripped animation, hand IK, bolt action, or an animation for the remaining 62 weapons.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
KEY = 'weapon_reload_w47/beloved'
# Audited side elevation: lower box ahead of trigger; receiver/magazine well stays in body.
MAGAZINE = [107, 108, 109, 110, 111, 115, 120, 194, 195, 203]
# progress, XYZ rotation delta, XYZ translation delta, local magazine pull distance.
# Muzzle rises/rolls toward left; magazine pulled down, briefly absent, pushed home, gun returns.
KEYS = [
    (0, [0, 0, 0], [0, 0, 0], 0),
    (.18, [24, -12, -18], [-2.2, .3, -1], 0),
    (.38, [28, -16, -22], [-2.5, .3, -1], 5),
    (.52, [27, -15, -21], [-2.5, .2, -1], 6),
    (.72, [24, -12, -18], [-2.2, .3, -1], 0),
    (.82, [29, -10, -14], [-2, .6, -.8], 0),
    (1, [0, 0, 0], [0, 0, 0], 0),
]


def encode(v): return (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()


def sample(progress):
    for a, b in zip(KEYS, KEYS[1:]):
        if progress <= b[0]:
            t = max(0, min(1, (progress - a[0]) / (b[0] - a[0])))
            t = t * t * (3 - 2 * t)
            return ([a[1][i] + (b[1][i] - a[1][i]) * t for i in range(3)],
                    [a[2][i] + (b[2][i] - a[2][i]) * t for i in range(3)],
                    a[3] + (b[3] - a[3]) * t)
    raise ValueError(progress)


def rotate(v, rotation):
    # ItemTransform quaternion rotationXYZ, rightmost Z first.
    x, y, z = v
    a, b, c = map(math.radians, rotation)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return [x, y, z]


def generate():
    src = ASSETS / 'models/weapon/sniper_rifle/beloved.json'
    item = ASSETS / 'items/weapon/beloved.json'
    transform_src = ROOT / 'scripts/build_weapons_w30.py'
    original = json.loads(src.read_bytes())
    original_item = json.loads(item.read_bytes())
    output = {}
    for name, indices in [('body', set(range(len(original['elements']))) - set(MAGAZINE)),
                          ('magazine', set(MAGAZINE))]:
        geo = {k: copy.deepcopy(v) for k, v in original.items() if k not in ('elements', 'display')}
        geo['elements'] = [copy.deepcopy(e) for i, e in enumerate(original['elements']) if i in indices]
        output[ASSETS / f'models/{KEY}_{name}.json'] = encode(geo)
    two_hand = runpy.run_path(str(transform_src))['two_hand_display']
    entries = []
    for frame in range(21):
        progress = frame / 20
        rot, translation, pull = sample(progress)
        parts = {}
        for name in ('body', 'magazine'):
            display = copy.deepcopy(original['display'])
            for context in ('firstperson_righthand', 'firstperson_lefthand'):
                d = display[context]
                d['rotation'] = [round(v + rot[i], 6) for i, v in enumerate(d['rotation'])]
                delta = rotate([0, -pull, 0], d['rotation']) if name == 'magazine' else [0, 0, 0]
                d['translation'] = [round(v + translation[i] + delta[i] * d['scale'][i], 6)
                                    for i, v in enumerate(d['translation'])]
            for grip in ('native', 'twohand'):
                key = f'{KEY}_{frame:02}_{name}_{grip}'
                output[ASSETS / f'models/{key}.json'] = encode({
                    'parent': f'destiny:{KEY}_{name}',
                    'display': display if grip == 'native' else two_hand(display, 'sniper_rifle')})
                parts[name, grip] = {'type': 'minecraft:model', 'model': 'destiny:' + key}
        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [parts['body', grip], parts['magazine', grip]]}
        entries.append({'threshold': progress, 'model': {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}})
    wrapper = copy.deepcopy(original_item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': ['firstperson_righthand', 'firstperson_lefthand'], 'model': {
            'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data', 'index': 1,
            'entries': entries, 'fallback': original_item['model']}}],
        'fallback': original_item['model']}
    output[ASSETS / f'items/{KEY}.json'] = encode(wrapper)
    output[ROOT / 'art/weapons/w47/manifest.json'] = encode({
        'generator': 'scripts/generate_reload_models_w47.py', 'ids': ['beloved'], 'frames': 21,
        'sourceCubes': len(original['elements']), 'magazineIndices': MAGAZINE,
        'firstPersonContexts': ['firstperson_righthand', 'firstperson_lefthand'], 'progressFloatIndex': 1,
        'sourceSha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (src, item, transform_src)},
        'originalsUnchanged': True, 'cubeBudget': 'Body + magazine exactly source count, <=256 per frame',
        'limitations': 'Reference-informed approximation; no hands/IK/bolt or 3rd-person animation. Beloved only.',
        'keyframes': KEYS, 'sha256': {str(p.relative_to(ROOT)): sha(v) for p, v in output.items()}})
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = generate()
    for path, data in outputs.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f'W47 asset differs: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'{"Verified" if args.verify else "Generated"} {len(outputs)} W47 files')
