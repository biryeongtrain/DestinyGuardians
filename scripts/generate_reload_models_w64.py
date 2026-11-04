#!/usr/bin/env python3
"""Duke Mk.44 reference-informed swing-out reload. Not ripped animation or hand IK.

Source 232 cubes/UVs are preserved: 211 receiver + 21 cylinder, plus two small
textured yoke links (234 total). Samples follow the actual captured reload phase.
Only first-person contexts use this wrapper; every other context retains its
original item graph. --verify is read-only and independently reconstructs outputs.
"""
import argparse
import copy
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
KEY = 'weapon_reload_w64/duke_mk_44'
# Audited exploded original model in Blockbench; NOT a bounding-box runtime guess.
# Includes the cylindrical shell and its rear rim, not barrel rail or trigger frame.
CYLINDER = [7, 8, 11, 12, 48, 52, 55, 56, 57, 73, 80, 82, 83,
            164, 178, 179, 181, 182, 183, 186, 230]
PIVOT = [8, 10.2, 5.17]
# Normalized stage, body rotation delta, translation delta, local cylinder swing.
# Reference: muzzle rises, cylinder opens to shooter's left, loading hold,
# gun lowers for support-hand interaction, cylinder closes, HIP restoration.
# Angles/timing below are authored approximations, NOT measured source animation.
KEYS = [
    (0, [0, 0, 0], [0, 0, 0], 0),
    (.15, [25, -8, -8], [-1, -1, -.3], 0),
    (.30, [62, -16, -14], [-1.8, -4, -.5], 80),
    (.48, [65, -16, -14], [-1.8, -4.2, -.5], 80),
    (.64, [36, -10, -22], [-2.2, -2.6, -.4], 80),
    (.76, [20, -6, -16], [-1.8, -1.4, -.3], 80),
    (.88, [12, 2, 8], [-.7, -.4, -.1], 0),
    (1, [0, 0, 0], [0, 0, 0], 0),
]
HELPER = runpy.run_path(str(ROOT / 'scripts/generate_reload_models_w47.py'))
rotate, encode, sha = HELPER['rotate'], HELPER['encode'], HELPER['sha']


def sample(progress):
    if not 0 <= progress <= 1:
        raise ValueError(progress)
    for a, b in zip(KEYS, KEYS[1:]):
        if progress <= b[0]:
            t = (progress - a[0]) / (b[0] - a[0])
            t = t * t * (3 - 2 * t)
            return ([a[1][i] + (b[1][i] - a[1][i]) * t for i in range(3)],
                    [a[2][i] + (b[2][i] - a[2][i]) * t for i in range(3)],
                    a[3] + (b[3] - a[3]) * t)
    raise ValueError(progress)


def generate():
    src = ASSETS / 'models/weapon/hand_cannon/duke_mk_44.json'
    item = ASSETS / 'items/weapon/duke_mk_44.json'
    original = json.loads(src.read_bytes())
    original_item = json.loads(item.read_bytes())
    output = {}
    # Two modest mechanical links. Reuse source rear-frame metal UV, no new texture
    # or fake cartridges. Their exposed surfaces are an approximation of the yoke.
    yoke = []
    for a, b in [([7.78, 10.2, 4.97], [8.22, 12.25, 5.37]),
                 ([7.78, 12.05, 3.7], [8.22, 12.45, 5.37])]:
        e = copy.deepcopy(original['elements'][120])
        e['from'], e['to'] = a, b
        yoke.append(e)
    for name in ('body', 'cylinder'):
        geo = {k: copy.deepcopy(v) for k, v in original.items() if k not in ('elements', 'display')}
        geo['elements'] = [copy.deepcopy(e) for i, e in enumerate(original['elements'])
                           if (i in CYLINDER) == (name == 'cylinder')]
        if name == 'cylinder':
            geo['elements'] += yoke
        output[ASSETS / f'models/{KEY}_{name}.json'] = encode(geo)
    transform_src = ROOT / 'scripts/build_weapons_w30.py'
    two_hand = runpy.run_path(str(transform_src))['two_hand_display']
    entries = []
    for frame in range(21):
        rot, translation, swing = sample(frame / 20)
        parts = {}
        for name in ('body', 'cylinder'):
            display = copy.deepcopy(original['display'])
            for context in ('firstperson_righthand', 'firstperson_lefthand'):
                d = display[context]
                body_rot = [v + rot[i] for i, v in enumerate(d['rotation'])]
                local_offset = [0, 0, 0]
                if name == 'cylinder':
                    # R_body * (P + R_z(swing) * (v-P)): item origin is [8,8,8].
                    p = [v - 8 for v in PIVOT]
                    turned = rotate(p, [0, 0, swing])
                    local_offset = rotate([p[i] - turned[i] for i in range(3)], body_rot)
                d['rotation'] = [round(body_rot[i] + (swing if name == 'cylinder' and i == 2 else 0), 6)
                                 for i in range(3)]
                d['translation'] = [round(v + translation[i] + local_offset[i] * d['scale'][i], 6)
                                    for i, v in enumerate(d['translation'])]
            for grip in ('native', 'twohand'):
                key = f'{KEY}_{frame:02}_{name}_{grip}'
                output[ASSETS / f'models/{key}.json'] = encode({
                    'parent': f'destiny:{KEY}_{name}',
                    'display': display if grip == 'native' else two_hand(display, 'hand_cannon')})
                parts[name, grip] = {'type': 'minecraft:model', 'model': 'destiny:' + key}
        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [parts['body', grip], parts['cylinder', grip]]}
        entries.append({'threshold': frame / 20, 'model': {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}})
    wrapper = copy.deepcopy(original_item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': ['firstperson_righthand', 'firstperson_lefthand'], 'model': {
            'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data', 'index': 1,
            'entries': entries, 'fallback': original_item['model']}}],
        'fallback': original_item['model']}
    output[ASSETS / f'items/{KEY}.json'] = encode(wrapper)
    output[ROOT / 'art/weapons/w64/manifest.json'] = encode({
        'stage': 'W64', 'generator': 'scripts/generate_reload_models_w64.py',
        'ids': ['duke_mk_44'], 'frames': 21, 'progressFloatIndex': 1,
        'sourceCubes': 232, 'bodyCubes': 211, 'cylinderSourceCubes': 21,
        'addedYokeCubes': 2, 'compositeCubes': 234, 'cylinderIndices': CYLINDER,
        'pivot': PIVOT, 'keyframes': KEYS, 'originalsUnchanged': True,
        'firstPersonContexts': ['firstperson_righthand', 'firstperson_lefthand'],
        'nativeGameplayVerified': False, 'handIK': False, 'exactAnimationRip': False,
        'limitations': 'Authored body/yoke swing approximation. No hands, loader/cartridges, '
                       'per-round ejection, native visibility certification or third-person reload. Duke only.',
        'sourceSha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in
                        (src, item, transform_src, ROOT / 'scripts/generate_reload_models_w47.py')},
        'sha256': {str(p.relative_to(ROOT)): sha(v) for p, v in output.items()}})
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = generate()
    for path, data in outputs.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f'W64 asset differs: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'{"Verified" if args.verify else "Generated"} {len(outputs)} W64 files')
