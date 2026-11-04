#!/usr/bin/env python3
"""W113 authored swap approximation; --verify reconstructs bytes without writes.

Only display-transform children; no original geometry, timing, hand animation or IK.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w113-swap'
PREFIX = 'weapon_swap_w113'
FAMILIES = {'austringer': 'hand_cannon', 'beloved': 'sniper_rifle',
            'ammit_ar2': 'auto_rifle', 'the_recluse': 'submachine_gun'}
OLD_PAIRS = {('austringer', 'beloved'), ('beloved', 'austringer')}
PAIRS = tuple((a, b) for a in FAMILIES for b in FAMILIES if a != b and (a, b) not in OLD_PAIRS)
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
SOURCE_SNAPSHOT = '32e2ccbd5c0fd7a212587576505ecf045516ebca9a7424e4e3a953670f18e070'
# Frozen before generating W113. Refuse to silently bless changed original inputs.
IMMUTABLE_INPUT_SHA256 = '04df3cbe7e5ef4c262f4ce973c51f4473090150bf8355226c8a486bed27e3019'
W91 = runpy.run_path(str(ROOT / 'scripts/generate_swap_presentation_w91.py'))
encode, sha, f32 = (W91[n] for n in ('encode', 'sha', 'f32'))
pose_delta, multiply, translate, rotate, transform = (W91[n] for n in
    ('pose_delta', 'multiply', 'translate', 'rotate', 'transform'))


def base_key(wid):
    return f'weapon/{FAMILIES[wid]}/{wid}'


def owned_paths():
    """Exact 858-file worker scope; generator writes only its 853 asset outputs."""
    result = {'scripts/generate_swap_presentation_w113.py', 'scripts/qa/test_swap_w113.py',
              'src/main/java/kim/biryeong/destiny/weapon/WeaponSwapPresentation.java',
              'src/test/java/kim/biryeong/destiny/weapon/SwapPresentationW113Test.java',
              'docs/qa/2026-10-25/w113/swap-worker.md'}
    result.update(f'art/weapons/w113-swap/{n}' for n in
                  ('manifest.json', 'asset-samples.json', 'authoring-notes.md'))
    for a, b in PAIRS:
        pair = f'{a}_to_{b}'
        result.add(f'src/main/resources/assets/destiny/items/{PREFIX}/{pair}.json')
        result.update(f'src/main/resources/assets/destiny/models/item/{PREFIX}/{pair}_{phase}_{i:02}_{grip}.json'
                      for phase in ('stow', 'ready') for i in range(21) for grip in GRIPS)
    assert len(result) == 858
    return result


def source_paths():
    paths = {ROOT / 'scripts' / name for name in ('generate_swap_presentation_w91.py',
             'build_weapons_w30.py', 'generate_aim_models_w70.py', 'generate_reload_models_w69.py')}
    paths.add(ROOT / 'art/weapons/w30/catalog.json')
    # Pin every original W91 asset/report byte, including its two item graphs.
    for directory in (ASSETS / 'items/weapon_swap_w91', ASSETS / 'models/item/weapon_swap_w91',
                      ROOT / 'art/weapons/w91-swap'):
        paths.update(p for p in directory.rglob('*') if p.is_file())
    for wid in FAMILIES:
        paths.add(ROOT / f'art/blockbench/weapons/w30/{wid}.bbmodel')
        paths.add(ASSETS / f'items/weapon/{wid}.json')
        paths.update(ASSETS / f'models/{base_key(wid)}{s}.json' for s in
                     ('', '_ads', '_inspect', '_twohand', '_ads_twohand', '_inspect_twohand'))
        paths.update(ASSETS / f'models/weapon_aim_w70/{wid}_00_{g}.json' for g in GRIPS)
        model = json.loads((ASSETS / f'models/{base_key(wid)}.json').read_bytes())
        paths.update(ASSETS / f'textures/{t.split(":", 1)[1]}.png'
                     for t in model['textures'].values() if t.startswith('destiny:'))
    return sorted(paths)


def generate():
    originals = {p: p.read_bytes() for p in source_paths()}
    inputs = {str(p.relative_to(ROOT)): sha(raw) for p, raw in originals.items()}
    source_set = sha(encode(inputs))
    assert source_set == IMMUTABLE_INPUT_SHA256, 'Original source/W91 drift: ' + source_set
    two_hand_display = runpy.run_path(str(ROOT / 'scripts/build_weapons_w30.py'))['two_hand_display']
    models, items, output, samples, rows = {}, {}, {}, [], []
    def read(path):
        return json.loads(originals[path])
    for wid, family in FAMILIES.items():
        for g in GRIPS:
            suffix = '_twohand' if g == 'twohand' else ''
            models[wid, g] = read(ASSETS / f'models/{base_key(wid)}{suffix}.json')
            assert read(ASSETS / f'models/weapon_aim_w70/{wid}_00_{g}.json')['display'] == models[wid, g]['display']
        assert 8 < len(models[wid, 'native']['elements']) <= 256
        assert models[wid, 'twohand']['parent'] == 'destiny:' + base_key(wid)
        assert two_hand_display(models[wid, 'native']['display'], family) == models[wid, 'twohand']['display']
        items[wid] = read(ASSETS / f'items/weapon/{wid}.json')
    for outgoing, incoming in PAIRS:
        pair = f'{outgoing}_to_{incoming}'
        entries = []
        for phase, start in (('stow', 0), ('ready', 2)):
            rendered = outgoing if phase == 'stow' else incoming
            for frame in range(21):
                progress = frame / 20
                rotation, translation = pose_delta(phase, progress)
                display = copy.deepcopy(models[rendered, 'native']['display'])
                for context in FP:
                    for field, delta in (('rotation', rotation), ('translation', translation)):
                        display[context][field] = [round(v + delta[i], 6)
                                                   for i, v in enumerate(display[context][field])]
                references, displays = {}, {}
                endpoint = phase == 'stow' and frame == 0 or phase == 'ready' and frame == 20
                for grip in GRIPS:
                    source_display = models[rendered, grip]['display']
                    d = copy.deepcopy(display if grip == 'native' else two_hand_display(display, FAMILIES[rendered]))
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
        fallback = items[incoming]['model']
        route = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                 'index': 5, 'entries': entries, 'fallback': copy.deepcopy(fallback)}
        assert len(entries) == 42
        assert [e['threshold'] for e in entries] == sorted(e['threshold'] for e in entries)
        for i, entry in enumerate(entries):
            for offset in (0, .0001, .0002, .0003, .000999):
                value = f32(entry['threshold'] + offset)
                assert max(j for j, e in enumerate(entries) if f32(e['threshold']) <= value) == i
        wrapper = copy.deepcopy(items[incoming])
        wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                            'cases': [{'when': list(FP), 'model': route}], 'fallback': copy.deepcopy(fallback)}
        output[ASSETS / f'items/{PREFIX}/{pair}.json'] = encode(wrapper)
        rows.append(dict(pair=pair, itemModel=f'destiny:{PREFIX}/{pair}', outgoing=outgoing, incoming=incoming,
                         samplesPerPhase=21, phases=['STOW', 'READY'], carriers=list(GRIPS)))
    output[ART / 'asset-samples.json'] = encode(dict(
        purpose='Authored approximation preview inputs; generated assets, not captured original-game frames.',
        samples=samples, suggestedContactFrames=[0, 4, 11, 16, 18, 20], previewContexts=list(FP),
        previewNotes='Resolve actual source parent/texture and current incoming carrier. Native verification pending.'))
    output[ART / 'authoring-notes.md'] = NOTES.encode()
    catalog = {e['id']: e for e in read(ROOT / 'art/weapons/w30/catalog.json')}
    manifest = dict(stage='W113', generator='scripts/generate_swap_presentation_w113.py',
        sourceSnapshotFiles=34980, sourceSnapshotSha256=SOURCE_SNAPSHOT,
        consumedOriginalSetSha256=source_set, originalSha256=inputs,
        generatorSha256=sha(Path(__file__).read_bytes()),
        selectorFloatIndex=5, carrierFlagIndex=0, phaseRanges={'STOW': [0, 1], 'READY': [2, 3]},
        samplesPerPhase=21, step=.05, helperOffset=0, pairs=rows, modelChildren=840, itemDefinitions=10,
        preservedW91Pairs=[f'{a}_to_{b}' for a, b in sorted(OLD_PAIRS)],
        sourceGeometry={wid: dict(cubes=len(models[wid, 'native']['elements']), model='destiny:' + base_key(wid),
                                 catalogSource=catalog[wid]['source']) for wid in FAMILIES},
        exactHipEndpoints=True, sourceGeometryUvTexturesUnchanged=True,
        currentCarrierCompensation=True, phaseTimingOwner='Existing WeaponHandling only',
        authoredDisplayPoses=True, approximation=True, measuredSourceFrames=False, handIK=False,
        nativeGameplayVerified=False, nativeCodecVerified=False, visualPreviewVerified=False,
        keyframes=W91['KEYS'], ownedPaths=sorted(owned_paths()),
        outputSha256={str(p.relative_to(ROOT)): sha(raw) for p, raw in sorted(output.items())},
        outputHashNote='Manifest excludes itself; all other generated outputs covered.')
    output[ART / 'manifest.json'] = encode(manifest)
    assert len(samples) == 840 and len(output) == 853
    assert {str(p.relative_to(ROOT)) for p in output} <= owned_paths()
    for p, raw in originals.items():
        assert p.read_bytes() == raw, f'Original changed during generation: {p}'
    return output


NOTES = """# W113 first-person swap authoring

Ten new directional pairs among Austringer, Beloved, Ammit AR2 and The Recluse;
the original Austringer <-> Beloved graphs, children and reports stay byte-identical
in weapon_swap_w91. All ten additions live in weapon_swap_w113.

This is an explicitly authored approximation of swap motion, reusing W91's audited
pure smoothstep and matrix helpers via runpy. It is not extracted or measured
original-game animation, hand motion, bones, frame interpolation or invented IK.
The current detailed W30 parent models, face UVs, textures, editable bbmodels,
default display transforms and item graphs remain immutable inputs. Their source
catalog archive provenance and byte hashes are recorded in manifest.json.

Every child has only parent and display. STOW renders actual outgoing geometry;
READY renders incoming geometry. Each phase has 21 samples at .05 spacing.
STOW 0 and READY 1 exactly match the rendered weapon's native/twohand HIP display.
Only first-person contexts animate. Non-first-person child contexts preserve the
actual rendered source carrier variant; the item wrapper sends all GUI, ground,
fixed, head and third-person contexts directly to the exact incoming item graph,
including ADS/inspect/default fallbacks and original metadata.

Float slot 5 selects STOW 0..1 or READY 2..3. Thresholds are sorted and audited in
float32 with the existing positive sub-.001 binding offsets. Values below 0 use the
incoming graph; 1..2 holds STOW's final sample; above 3 holds READY's exact HIP.
Flag 0 is the CURRENT incoming wire carrier, not the outgoing weapon default grip.
Both hands and both carrier branches are audited using actual crossbow correction
(-.641864 translation and 10-degree yaw). Vanilla performs left-hand reflection;
no extra mirror or hand IK is introduced. Scale and source geometry stay intact.

Runtime support is exactly the twelve distinct permutations of these four IDs.
Old two routes use W91, new ten use W113. Binding admission, owner/stack/level
identity, float restoration, cleanup and cache offsets are unchanged. Handling
alone owns phase durations, zero-duration transitions, firing and ammunition.

Generate: rtk proxy python3 -B scripts/generate_swap_presentation_w113.py
Read-only audit: append --verify. The 858-path worker allowlist is exact; this
generator writes only 853 asset/report files within it. Unknown output files are
rejected without deletion. Verification reconstructs bytes and checks immutable
source hashes and all output bytes without creating directories or writing files.

asset-samples.json lists all 840 children, current carrier flags, selectors,
actual parents and both first-person displays. Central native scenarios: all ten
new directions plus both W91 controls, both hands and carriers; STOW 0/.55/1 and
READY 0/.8/1; GUI/third-person/ADS/inspect fallbacks; interruptions, death, world
change, disconnect, donor handoff, stack copies and optional grip changes. Check
framing, occlusion and exact HIP continuity. No native/app/framebuffer acceptance
is claimed here; the master owns centralized compilation, JUnit and game testing.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Read-only reconstruction and audit')
    args = parser.parse_args()
    output = generate()
    existing = set()
    for directory in (ASSETS / f'items/{PREFIX}', ASSETS / f'models/item/{PREFIX}', ART):
        if directory.exists():
            existing.update(p for p in directory.rglob('*') if p.is_file())
    extra = existing - set(output)
    if extra:
        raise SystemExit('Unexpected W113 output (not deleted): ' + ', '.join(str(p.relative_to(ROOT)) for p in sorted(extra)))
    for path, raw in output.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != raw:
                raise SystemExit('W113 asset differs: ' + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f'{"Verified" if args.verify else "Generated"} {len(output)} W113 files; '
          '840 children, 10 pair items, 3 reports; immutable source and carrier audits passed')


if __name__ == '__main__':
    main()
