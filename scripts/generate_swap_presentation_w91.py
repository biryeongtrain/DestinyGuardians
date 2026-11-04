#!/usr/bin/env python3
"""Deterministic W91 swap display samples; --verify is strictly read-only.

STOW shows outgoing geometry on CURRENT incoming carrier; READY shows incoming.
These authored poses have no animation clock, measured source frames, or hand IK.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w91-swap'
PREFIX = 'weapon_swap_w91'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
FAMILIES = {'austringer': 'hand_cannon', 'beloved': 'sniper_rifle'}
SOURCE_HEAD = 'bfd4b4573fd8651bf1ea850bf829622ccce5c3c2'
INITIAL_DIRTY_STATUS_SHA256 = 'e7b410a633f0600ebe4e921d341835beea0308e6452df9ada31f1a3bfd7dd207'
# Normalized cosmetic progress only. No seconds, tick counts, fire/ammo deadlines.
# progress, display rotation delta XYZ, display translation delta XYZ.
KEYS = {
    'stow': [
        (0, [0, 0, 0], [0, 0, 0]),
        (.20, [8, -3, -5], [.3, -1.8, .3]),
        (.55, [34, -11, -18], [1.2, -9, 1.8]),
        (1, [62, -18, -30], [2, -20, 4]),
    ],
    'ready': [
        (0, [55, 18, 24], [1, -20, 4]),
        (.45, [22, 8, 10], [.4, -7, 1.8]),
        (.80, [-3, -1, -1.5], [-.1, .45, -.15]),
        (.90, [-1, -.3, -.5], [-.03, .12, -.04]),
        (1, [0, 0, 0], [0, 0, 0]),
    ],
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def base_key(wid):
    return f'weapon/{FAMILIES[wid]}/{wid}'


def f32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def pose_delta(phase, progress):
    if not 0 <= progress <= 1:
        raise ValueError(progress)
    for a, b in zip(KEYS[phase], KEYS[phase][1:]):
        if progress <= b[0]:
            t = (progress - a[0]) / (b[0] - a[0])
            t = t * t * (3 - 2 * t)
            return tuple([[x + (y - x) * t for x, y in zip(a[k], b[k])]
                          for k in (1, 2)])
    raise ValueError(phase)


def owned(path):
    return (path == ROOT / 'scripts/generate_swap_presentation_w91.py'
            or path.is_relative_to(ASSETS / f'items/{PREFIX}')
            or path.is_relative_to(ASSETS / f'models/item/{PREFIX}')
            or path.parent == ART and path.name.startswith('asset-'))


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def identity():
    return [[float(i == j) for j in range(4)] for i in range(4)]


def translate(x, y, z):
    m = identity()
    m[0][3], m[1][3], m[2][3] = x, y, z
    return m


def rotate(axis, angle):
    c, s = math.cos(angle), math.sin(angle)
    if axis == 0:
        return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
    if axis == 1:
        return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def transform(pose, left):
    sign = -1 if left else 1
    t, r = pose['translation'], pose['rotation']
    m = translate(sign * t[0] / 16, t[1] / 16, t[2] / 16)
    for axis in range(3):
        m = multiply(m, rotate(axis, math.radians(r[axis]) * (sign if axis else 1)))
    scale = identity()
    for axis in range(3):
        scale[axis][axis] = pose['scale'][axis]
    return multiply(m, scale)


def generate():
    output, inputs, originals, models, items, samples, rows = {}, {}, {}, {}, {}, [], []

    def read(path, parse=True):
        raw = path.read_bytes()
        inputs[str(path.relative_to(ROOT))] = sha(raw)
        if path != Path(__file__).resolve():
            originals[path] = raw
        return json.loads(raw) if parse else raw

    # run_path loads existing pure transform helpers without executing their CLI.
    helper = ROOT / 'scripts/build_weapons_w30.py'
    read(helper, False)
    two_hand_display = runpy.run_path(str(helper))['two_hand_display']
    read(Path(__file__).resolve(), False)
    for name in ('generate_aim_models_w70.py', 'generate_reload_models_w69.py'):
        read(ROOT / 'scripts' / name, False)
    catalog = {e['id']: e for e in read(ROOT / 'art/weapons/w30/catalog.json')}
    for wid in FAMILIES:
        key = base_key(wid)
        # Also pin all original fallback dependencies, editable sources and textures.
        for suffix in ('', '_ads', '_inspect', '_twohand', '_ads_twohand', '_inspect_twohand'):
            models[wid, suffix] = read(ASSETS / f'models/{key}{suffix}.json')
        items[wid] = read(ASSETS / f'items/weapon/{wid}.json')
        read(ROOT / f'art/blockbench/weapons/w30/{wid}.bbmodel')
        for tex in set(models[wid, '']['textures'].values()):
            if tex.startswith('destiny:'):
                read(ASSETS / f'textures/{tex.split(":", 1)[1]}.png', False)
        for grip in GRIPS:
            endpoint = read(ASSETS / f'models/weapon_aim_w70/{wid}_00_{grip}.json')
            assert endpoint['display'] == models[wid, '_twohand' if grip == 'twohand' else '']['display']
        assert 8 < len(models[wid, '']['elements']) <= 256
        assert models[wid, '_twohand']['parent'] == 'destiny:' + key
        assert two_hand_display(models[wid, '']['display'], FAMILIES[wid]) == models[wid, '_twohand']['display']

    for outgoing, incoming in (('austringer', 'beloved'), ('beloved', 'austringer')):
        pair = f'{outgoing}_to_{incoming}'
        entries = []
        for phase, start in (('stow', 0), ('ready', 2)):
            rendered = outgoing if phase == 'stow' else incoming
            source = models[rendered, '']
            for frame in range(21):
                progress = frame / 20
                rotation, translation = pose_delta(phase, progress)
                display = copy.deepcopy(source['display'])
                # Apply deltas before current-carrier compensation. Native left reflection
                # is applied by Minecraft; do not mirror the left transform a second time.
                for context in FP:
                    for field, delta in (('rotation', rotation), ('translation', translation)):
                        display[context][field] = [round(v + delta[i], 6)
                                                   for i, v in enumerate(display[context][field])]
                references, displays = {}, {}
                endpoint = phase == 'stow' and frame == 0 or phase == 'ready' and frame == 20
                for grip in GRIPS:
                    source_display = models[rendered, '_twohand' if grip == 'twohand' else '']['display']
                    d = copy.deepcopy(display if grip == 'native' else two_hand_display(display, FAMILIES[rendered]))
                    # Preserve exact existing carrier-specific non-FP overrides, including
                    # crossbow third-person correction; item graph routes non-FP to incoming.
                    for context in source_display:
                        if context not in FP:
                            d[context] = copy.deepcopy(source_display[context])
                    if endpoint:
                        d = copy.deepcopy(source_display)
                    key = f'item/{PREFIX}/{pair}_{phase}_{frame:02}_{grip}'
                    path = ASSETS / f'models/{key}.json'
                    output[path] = encode({'parent': 'destiny:' + base_key(rendered), 'display': d})
                    references[grip] = {'type': 'minecraft:model', 'model': 'destiny:' + key}
                    displays[grip] = d
                    assert set(d) == set(source_display)
                    for context, pose in d.items():
                        if context not in FP:
                            assert pose == source_display[context]
                        for field in ('rotation', 'translation', 'scale'):
                            assert len(pose[field]) == 3 and all(math.isfinite(v) for v in pose[field])
                        assert all(abs(v) <= 80 for v in pose['translation'])
                        assert all(0 < v <= 4 for v in pose['scale'])
                    samples.append(dict(pair=pair, phase=phase.upper(), frame=frame, progress=progress,
                                        selector=start + progress, floatIndex=5, flag0=grip == 'twohand',
                                        currentIncomingCarrier=incoming, renderedGeometry=rendered,
                                        itemModel=f'destiny:{PREFIX}/{pair}', model=references[grip]['model'],
                                        modelPath=str(path.relative_to(ROOT)), parent='destiny:' + base_key(rendered),
                                        firstpersonDisplay={c: d[c] for c in FP}))
                # Independently audit actual matrix compensation for BOTH handednesses.
                for context in FP:
                    left = context.endswith('lefthand')
                    sign = -1 if left else 1
                    carrier = multiply(translate(-.641864 * sign, 0, 0), rotate(1, math.radians(10) * sign))
                    restored = multiply(carrier, transform(displays['twohand'][context], left))
                    native = transform(displays['native'][context], left)
                    assert max(abs(restored[i][j] - native[i][j]) for i in range(4) for j in range(4)) < 3e-6
                entries.append({'threshold': start + progress, 'model': {
                    'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
                    'on_false': references['native'], 'on_true': references['twohand']}})
        # One complete, sorted phase route per pair. READY is independent of STOW.
        fallback = items[incoming]['model']
        route = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                 'index': 5, 'entries': entries, 'fallback': copy.deepcopy(fallback)}
        assert len(entries) == 42
        assert [e['threshold'] for e in entries] == sorted(e['threshold'] for e in entries)
        for i, entry in enumerate(entries):
            for offset in (0, .000999):
                value = f32(entry['threshold'] + offset)
                selected = max(j for j, e in enumerate(entries) if f32(e['threshold']) <= value)
                assert selected == i, (pair, i, value, selected)
        wrapper = copy.deepcopy(items[incoming])
        wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                            'cases': [{'when': list(FP), 'model': route}], 'fallback': copy.deepcopy(fallback)}
        output[ASSETS / f'items/{PREFIX}/{pair}.json'] = encode(wrapper)
        rows.append(dict(pair=pair, itemModel=f'destiny:{PREFIX}/{pair}', outgoing=outgoing, incoming=incoming,
                         samplesPerPhase=21, phases=['STOW', 'READY'], carriers=list(GRIPS)))

    output[ART / 'asset-samples.json'] = encode({
        'purpose': 'Parent offscreen preview inputs; references are generated assets, not captured frames.',
        'samples': samples,
        'suggestedContactFrames': [0, 4, 11, 16, 18, 20],
        'previewContexts': list(FP),
        'previewNotes': 'Resolve source parent and texture; apply sample display plus actual incoming carrier. '
                        'Use a private offscreen view. No app/native screenshot or visual acceptance claimed.',
    })
    output[ART / 'asset-authoring-notes.md'] = (
        '# W91 swap asset authoring\n\n'
        'Only Austringer → Beloved and Beloved → Austringer. Each item contains its entire '
        'STOW and READY route. Float slot 5 is STOW 0..1 and READY 2..3, inclusive, '
        'with 21 samples per phase at .05 spacing. No helper offset is emitted; optional '
        'positive offsets below .001 keep the same sample. The reserved 1..2 gap holds '
        'the final STOW sample; values below 0 use incoming fallback; values above 3 '
        'hold the exact incoming HIP endpoint. Runtime owns valid values and cleanup.\n\n'
        'Vanilla already selected the incoming stack. Flag 0 describes its CURRENT '
        'wire carrier: false = native stick, true = charged crossbow/twohand. It does '
        'not describe the outgoing weapon default grip. STOW inherits outgoing detailed '
        'geometry and corrects it for that carrier; READY inherits incoming geometry. '
        'Both directions have both carriers, including optional Austringer twohand.\n\n'
        'Every model child contains only parent and display. Original cubes, face UVs, '
        'texture bindings, texture bytes, editable bbmodels, source displays and other '
        'item definitions are read-only inputs. Endpoint displays equal existing HIP '
        'native/twohand displays exactly. Only first-person poses animate. Other child '
        'contexts preserve the rendered source carrier variant, including twohand '
        'third-person overrides. The item wrapper always routes GUI, ground, fixed, '
        'head and third-person to the exact selected incoming original graph.\n\n'
        'Pose deltas are locally authored, piecewise smoothstep: STOW exits downward '
        'with a strong pitch/roll; READY rises from below, lightly overshoots, and snaps '
        'back to exact HIP. They are not extracted/measured original game frames, '
        'render-frame interpolation, bone animation, hand motion or hand IK. The W30 '
        'catalog and bbmodels identify geometry provenance; W69/W70 establish generator '
        'and first-person wrapper conventions. No source video was measured here.\n\n'
        'Handling owns all actual phase durations, zero-duration transitions, fire '
        'deadlines and ammo. Samples only describe normalized cosmetic progress. '
        'This generator contains no timing or gameplay mutation.\n\n'
        'Reproduce with `rtk proxy python3 scripts/generate_swap_presentation_w91.py`; '
        'audit with the same command plus `--verify`. Verification reconstructs bytes, '
        'checks source inputs, matrix compensation for both hands, exact endpoints, '
        'non-first-person preservation, float32 phase routing and the output inventory '
        'without writing. No build, client/server, Blockbench or user app was run.\n\n'
        'Parent preview: asset-samples.json lists all 168 children, item IDs, current '
        'carrier flags, selectors, parent models and both first-person displays. '
        'Review both carrier choices in both directions and both hands, especially '
        'STOW 0/.55/1 and READY 0/.8/1. Native pack codecs, actual framebuffer framing, '
        'hand/carrier continuity and gameplay integration remain central verification.\n\n'
        'Review note: the initially observed SwapPresentationW91Test.child compared '
        'all child non-FP contexts to native even for twohand; its endpoint check also '
        'required the full twohand display. Existing twohand third-person overrides '
        'differ from native. Preserve carrier-specific source contexts when reviewing '
        'that assertion; this leaf does not edit tests.\n'
    ).encode()
    # Immutable initial status evidence is intentionally not recomputed from this shared
    # dirty checkout on every verify; inputSha256 pins the actual consumed source bytes.
    source_set = sha(encode(dict(sorted(inputs.items()))))
    manifest = dict(
        stage='W91', generator='scripts/generate_swap_presentation_w91.py',
        sourceHead=SOURCE_HEAD, initialDirtyStatusSha256=INITIAL_DIRTY_STATUS_SHA256,
        initialDirtyStatusEncoding='git status --porcelain=v1 -z bytes; initial observation, not a commit',
        consumedSourceSetSha256=source_set, selectorFloatIndex=5, carrierFlagIndex=0,
        phaseRanges={'STOW': [0, 1], 'READY': [2, 3]}, samplesPerPhase=21, step=.05,
        helperOffset=0, pairs=rows, modelChildren=168, itemDefinitions=2,
        sourceGeometry={wid: {'cubes': len(models[wid, '']['elements']),
                              'model': 'destiny:' + base_key(wid), 'catalogSource': catalog[wid]['source']}
                        for wid in FAMILIES},
        exactHipEndpoints=True, sourceGeometryUvTexturesUnchanged=True,
        otherContexts='Exact incoming item graph; each child preserves its source carrier variant.',
        currentCarrierCompensation=True, phaseTimingOwner='Existing WeaponHandling only',
        authoredDisplayPoses=True, measuredSourceFrames=False, handIK=False,
        nativeGameplayVerified=False, nativeCodecVerified=False, visualPreviewVerified=False,
        keyframes=KEYS, inputSha256=dict(sorted(inputs.items())),
        originalSha256={str(p.relative_to(ROOT)): sha(raw) for p, raw in sorted(originals.items())},
        outputSha256={str(p.relative_to(ROOT)): sha(raw) for p, raw in sorted(output.items())},
        outputHashNote='Manifest excludes its own hash; all other generated outputs are covered.',
    )
    output[ART / 'asset-manifest.json'] = encode(manifest)
    assert len(samples) == 168 and len(output) == 173
    assert all(owned(path) for path in output)
    for path, raw in originals.items():
        assert path.read_bytes() == raw, f'Source changed during generation: {path.relative_to(ROOT)}'
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Reconstruct and audit without any writes')
    args = parser.parse_args()
    output = generate()
    existing = set()
    for directory in (ASSETS / f'items/{PREFIX}', ASSETS / f'models/item/{PREFIX}'):
        if directory.exists():
            existing.update(p for p in directory.rglob('*') if p.is_file())
    if ART.exists():
        existing.update(p for p in ART.glob('asset-*') if p.is_file())
    extra = existing - set(output)
    if extra:
        raise SystemExit('Unexpected owned output (not deleted): ' + ', '.join(str(p.relative_to(ROOT)) for p in sorted(extra)))
    for path, raw in output.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != raw:
                raise SystemExit('W91 asset differs: ' + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f'{"Verified" if args.verify else "Generated"} {len(output)} W91 files; '
          '168 display children, 2 pair items, 3 asset reports; source and carrier audits passed')


if __name__ == '__main__':
    main()
