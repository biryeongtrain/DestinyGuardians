#!/usr/bin/env python3
"""Pure W222 Long Arm pair-insert bank; only generate() reads inputs.

The generic scout reload is NOT a recovered Long Arm two-cartridge loop.
Master composes the same held source .35 calibration on weapon and full arms
once. These neutral body leaves author only a paired cartridge/contact path.
Import/generate never write, materialize, invoke subprocesses or create dirs.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
WEAPON = 'long_arm'
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w222') / WEAPON
GENERATOR = Path('scripts/generate_insert_w222_long_arm.py')
KEY = 'weapon_insert_w222_long_arm/long_arm'
SOURCE = A / 'models/weapon_surface_w123/long_arm.json'
NATIVE = A / 'models/weapon/scout_rifle/long_arm.json'
TWOHAND = A / 'models/weapon/scout_rifle/long_arm_twohand.json'
ITEM = A / 'items/weapon/long_arm.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
SURFACE_MANIFEST = Path('src/main/resources/weapon_surface_w123/manifest.json')
DESIGN = Path('art/weapons/w123/long_arm/design.json')
RIG = Path('art/weapons/w222/rigs/scout_rifle_e4c9ea6c.json')
GROUP, ACTION = 'scout_rifle_e4c9ea6c', '80A8A345'
ACTION_NAME = 'Armature|fp_80A8A345_reload_full|Base'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
PARTS, GRIPS = ('body', 'shell'), ('native', 'twohand')
SAMPLES, INTERVALS, ARM_RESERVE = 61, 60, 448
SOURCE_EVIDENCE = {
    'review': 'docs/qa/2026-10-28/w222/source-review.json',
    'handling': 'docs/qa/2026-10-28/w222/source-handling-evidence.json',
    'selection': 'docs/qa/2026-10-28/w222/selection.json',
    'upperChainSheet': 'docs/qa/2026-10-28/w222/source-sheets/scout_rifle_e4c9ea6c-80A8A345-upper-chain.png',
}
# receiver_main east face +.085; Y midpoint; front Z+2.48, behind bolt.
# Authored solid-receiver side-port approximation, not a recovered cavity.
SHELL_ANCHOR = (8.55, 9.4, 6.35)
PAIR_CENTERS_Y = (-.18, .18)
HOME, ALIGN, SEATED = (1.75, -1.65, 1.45), (0., 0., 0.), (-.58, 0., -.35)
# One rigid pair/contact carrier; -Z noses align before an inward -X push.
# End holds make the HOME seam exact and C1; only hidden geometry recycles.
SHELL_KEYS = {
    'initial': ((0., HOME), (.36, HOME), (.46, HOME),
                (.65, (.70, -.35, .35)), (.76, ALIGN),
                (.86, SEATED), (.90, SEATED), (1., HOME)),
    'loop': ((0., HOME), (.12, HOME),
             (.37, (.70, -.35, .35)), (.52, ALIGN),
             (.78, SEATED), (.84, SEATED), (1., HOME)),
    'return': ((0., HOME), (1., HOME)),
}
VISIBLE = {'initial': (.46, .90), 'loop': (.12, .84)}
UV_DONORS = {'case': 'lever_upper', 'head': 'lever_toe',
             'rim': 'lever_toe', 'nose': 'receiver_upper_action'}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def threshold(phase_index, frame):
    """Match Java float division BEFORE the phase-offset float addition."""
    return float32(phase_index * 2 + float32(frame / INTERVALS))


def after_float32(value):
    bits = struct.unpack('!I', struct.pack('!f', value))[0]
    return struct.unpack('!f', struct.pack('!I', bits + 1))[0]


def tangents(times, values):
    """Weighted PCHIP: shared C1 slopes, zero at endpoints/holds/extrema."""
    steps = [b - a for a, b in zip(times, times[1:])]
    secants = [(b - a) / h for a, b, h in zip(values, values[1:], steps)]
    slopes = [0.] * len(times)
    for i in range(1, len(times) - 1):
        before, after = secants[i - 1], secants[i]
        if before * after > 0:
            w1, w2 = 2 * steps[i] + steps[i - 1], steps[i] + 2 * steps[i - 1]
            slopes[i] = (w1 + w2) / (w1 / before + w2 / after)
    return slopes


def interpolate(keys, progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Expected finite normalized progress')
    for time, value in keys:
        if progress == time:
            return list(value)
    times = [k[0] for k in keys]
    i = next(i for i in range(len(keys) - 1) if progress < times[i + 1])
    h = times[i + 1] - times[i]
    t = (progress - times[i]) / h
    result = []
    for axis in range(3):
        values = [k[1][axis] for k in keys]
        slopes = tangents(times, values)
        result.append((2*t**3 - 3*t*t + 1)*values[i] + (t**3 - 2*t*t + t)*h*slopes[i]
                      + (-2*t**3 + 3*t*t)*values[i + 1] + (t**3 - t*t)*h*slopes[i + 1])
    return result


def sample(phase, progress):
    """Neutral body; source body/shoulder chains are applied by master once."""
    if phase not in PHASES:
        raise ValueError(phase)
    return [0., 0., 0.], [0., 0., 0.], interpolate(SHELL_KEYS[phase], progress)


def shell_visible(phase, progress):
    return phase in VISIBLE and VISIBLE[phase][0] <= progress < VISIBLE[phase][1]


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]


def vec(matrix, value):
    return [sum(matrix[i][k] * value[k] for k in range(3)) for i in range(3)]


def pose_display(original, twohand, phase, progress, part, grip):
    if part not in PARTS or grip not in GRIPS:
        raise ValueError((part, grip))
    _, _, offset = sample(phase, progress)
    accepted = original if grip == 'native' else twohand
    display = copy.deepcopy(accepted)
    if part == 'body':
        return display
    for context in FP:
        pose = display[context]
        scale = pose['scale']
        if len(set(scale)) != 1 or min(scale) <= 0:
            raise ValueError('Ordinary uniform first-person scale required')
        shift = vec(xyz(pose['rotation']), [scale[0] * v for v in offset])
        pose['translation'] = [round(v + s, 9) for v, s in zip(pose['translation'], shift)]
    return display


def shell_geometry(source):
    """Two small cartridges, 16 filled solids each; existing gold/steel UVs.

    Four crossing rectangles per section form a filled octagonal cross-section.
    Separate case/head/rim/nose volumes read as rounds, not a tube magazine.
    Both belong to one rigid shell leaf so the contact carrier cannot diverge.
    """
    by_name = {e['name']: e for e in source['elements']}
    elements = []
    for pair_index, dy in enumerate(PAIR_CENTERS_Y):
        for name, radius, z0, z1 in (
                ('case', .15, -.36, .40), ('head', .154, .38, .50),
                ('rim', .17, .49, .58), ('nose', .09, -.60, -.34)):
            donor_face = by_name[UV_DONORS[name]]['faces']['east']
            u0, v0, u1, v1 = donor_face['uv']
            uv = [u0 + (u1-u0)*.20, v0 + (v1-v0)*.20,
                  u0 + (u1-u0)*.80, v0 + (v1-v0)*.80]
            for angle in (0, 45, -45, 90):
                center = [SHELL_ANCHOR[0], SHELL_ANCHOR[1] + dy,
                          SHELL_ANCHOR[2] + (z0+z1)/2]
                widths = [2*radius*math.tan(math.pi/8), 2*radius]
                if angle == 90:
                    widths.reverse()
                element = {
                    'name': f'authored_pair_{pair_index}_{name}_{angle}',
                    'from': [center[0]-widths[0]/2, center[1]-widths[1]/2, SHELL_ANCHOR[2]+z0],
                    'to': [center[0]+widths[0]/2, center[1]+widths[1]/2, SHELL_ANCHOR[2]+z1],
                    'faces': {side: {'texture': donor_face['texture'], 'uv': list(uv)}
                              for side in ('north', 'south', 'east', 'west', 'up', 'down')},
                }
                if angle in (45, -45):
                    element['rotation'] = {'origin': center, 'axis': 'z', 'angle': angle}
                elements.append(element)
    return {'credit': 'W222 authored Long Arm small cartridge pair; existing gold/steel UV donors; no recovered payload mesh',
            'textures': copy.deepcopy(source['textures']), 'elements': elements}


def expected_output_paths():
    return ({A / f'models/{KEY}_{part}.json' for part in (*PARTS, 'shell_hidden')}
            | {A / f'models/{KEY}_{phase}_{frame:02}_{part}_{grip}.json'
               for phase in PHASES for frame in range(SAMPLES) for part in PARTS for grip in GRIPS}
            | {A / f'items/{KEY}.json', ART / 'manifest.json'})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Read inputs only and return absolute Path -> bytes, including manifest."""
    root = Path(root).resolve()
    def actual(override, default):
        path = Path(override) if override is not None else default
        return path if path.is_absolute() else root / path
    raw_inputs = {p: (root / p).read_bytes() for p in
                  (SOURCE, NATIVE, TWOHAND, ITEM, CONTACTS, FRAMING, SURFACE_MANIFEST, DESIGN)}
    rig_raw = actual(rig_path, RIG).read_bytes()
    profile_raw = actual(profile_path, ART / 'profile.json').read_bytes()
    source, native, twohand, canonical, profile, rig = (
        json.loads(raw) for raw in (raw_inputs[SOURCE], raw_inputs[NATIVE], raw_inputs[TWOHAND],
                                   raw_inputs[ITEM], profile_raw, rig_raw))
    rule = next(t for t in json.loads(raw_inputs[SURFACE_MANIFEST])['targets']
                if t['path'] == f'assets/destiny/models/weapon/scout_rifle/{WEAPON}.json')
    if (rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/')
            or rule['replacementSha256'] != sha(raw_inputs[SOURCE])):
        raise ValueError('Effective Long Arm surface mapping changed')
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W222'
            or profile.get('weapon') != WEAPON):
        raise ValueError('Invalid W222 Long Arm profile')
    contacts = json.loads(raw_inputs[CONTACTS])['weapons'][WEAPON]
    for side in ('right', 'left'):
        if profile['contacts'][side] != contacts[side]:
            raise ValueError('Accepted idle contact changed: ' + side)
    reload = profile['contacts']['reload']
    if (reload.get('contact') != list(SHELL_ANCHOR) or reload.get('partHint') != 'shell'
            or reload.get('policy') != 'shell' or reload.get('hand') != 'left'
            or reload.get('rigAction') != ACTION
            or reload.get('rotation') != contacts['reload']['rotation']
            or reload.get('sourcePalmContactFit') is not True
            or reload.get('sourceShellPoseHold') is not True):
        raise ValueError('Authored pair carrier / left contact contract changed')
    config = json.loads(raw_inputs[FRAMING])
    effective = {**config['families'].get('scout_rifle', config['default']),
                 **config.get('weapons', {}).get(WEAPON, {})}
    effective.update(sourceFullChain=True, keepMeshSupport=True, hideSupportAtRest=False,
                     sourceViewRotation=[0, 0, 0], sourceWeaponMotion=True)
    if profile['framing'] != effective:
        raise ValueError('Preserve current framing; only source full-chain flags may change')
    provenance = profile['sourceRig']
    action = rig['actions'].get(ACTION, {})
    if (rig.get('group') != GROUP or rig.get('fallback') is not False
            or WEAPON not in rig['weapons'] or rig.get('space') != 'armature_object'
            or rig.get('cameraExported') is not False
            or action.get('action') != ACTION_NAME
            or [action.get('start'), action.get('end')] != [1., 105.]
            or len(action.get('frames', [])) != SAMPLES):
        raise ValueError('Expected fresh original 61-pose scout source, frames1..105')
    required = {'weapon'} | {side + joint for side in ('left', 'right')
                            for joint in ('Shoulder', 'Elbow', 'Wrist')}
    for i, frame in enumerate(action['frames']):
        if (abs(frame['progress'] - i / INTERVALS) > 1e-12
                or abs(frame['frame'] - (1 + 104*i/INTERVALS)) > 1e-10
                or not required <= frame['joints'].keys()):
            raise ValueError('Original evaluated full chain/sample missing')
    for field in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if provenance[field] != rig[field]:
            raise ValueError('Source provenance drift: ' + field)
    if (provenance.get('cacheSha256') != sha(rig_raw) or provenance.get('sourceAction') != ACTION
            or provenance.get('action') != ACTION_NAME or provenance.get('group') != GROUP
            or provenance.get('path') != str(RIG) or provenance.get('sourceBlend') != rig['sourceBlend']
            or provenance.get('sourceFrameRange') != [1, 105]
            or provenance.get('evaluatedSamples') != SAMPLES):
        raise ValueError('Source cache/action binding changed')
    port = next(e for e in source['elements'] if e['name'] == 'receiver_main')
    derived = [port['to'][0] + .085, (port['from'][1]+port['to'][1])/2, port['from'][2] + 2.48]
    if any(abs(a-b) > 1e-8 for a, b in zip(derived, SHELL_ANCHOR)):
        raise ValueError('Receiver side-port derivation changed')
    shell = shell_geometry(source)
    weapon_count = len(source['elements']) + len(shell['elements'])
    canonical_count = max(len(native.get('elements', [])), len(twohand.get('elements', [])))
    budget = max(weapon_count, canonical_count) + ARM_RESERVE
    if budget > 1000:
        raise ValueError('Weapon plus four ordinary arm surfaces exceeds1000')
    output, allowed = {}, expected_output_paths()
    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W222 Long Arm namespace')
        output[root / path] = encode(value)
    emit(A / f'models/{KEY}_body.json', copy.deepcopy(source))
    emit(A / f'models/{KEY}_shell.json', shell)
    # Empty geometry still needs a particle reference for every inheriting leaf.
    emit(A / f'models/{KEY}_shell_hidden.json', {
        'textures': {'particle': source['textures']['particle']}, 'elements': []})
    entries = []
    for phase_index, phase in enumerate(PHASES):
        for frame in range(SAMPLES):
            progress = frame / INTERVALS
            for part in PARTS:
                parent = f'destiny:{KEY}_{part}'
                if part == 'shell' and not shell_visible(phase, progress):
                    parent += '_hidden'
                for grip in GRIPS:
                    emit(A / f'models/{KEY}_{phase}_{frame:02}_{part}_{grip}.json', {
                        'parent': parent,
                        'display': pose_display(source['display'], twohand['display'], phase, progress, part, grip)})
            def composite(grip):
                return {'type': 'minecraft:composite', 'models': [
                    {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{phase}_{frame:02}_{part}_{grip}'}
                    for part in PARTS]}
            endpoint = (phase == 'initial' and frame == 0) or (phase == 'return' and frame == INTERVALS)
            node = copy.deepcopy(canonical['model']) if endpoint else {
                'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
                'on_true': composite('twohand'), 'on_false': composite('native')}
            entries.append({'threshold': threshold(phase_index, frame), 'model': node})
        if phase != 'return':
            entries.append({'threshold': after_float32(phase_index*2 + 1),
                            'model': copy.deepcopy(canonical['model'])})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 4, 'entries': entries, 'fallback': copy.deepcopy(canonical['model'])}
    # Retain the original ADS/inspect cases verbatim, without selector assertions.
    modes = copy.deepcopy(canonical['model'])
    modes['fallback'] = dispatch
    wrapper = copy.deepcopy(canonical)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': modes}],
                        'fallback': copy.deepcopy(canonical['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    hashes = {str(p): sha(raw) for p, raw in raw_inputs.items()}
    hashes.update({str(RIG): sha(rig_raw), str(ART / 'profile.json'): sha(profile_raw)})
    emit(ART / 'manifest.json', {
        'schemaVersion': 1, 'stage': 'W222', 'weapon': WEAPON,
        'generator': str(GENERATOR), 'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': 'destiny:' + KEY, 'requiredParts': list(PARTS),
        'phases': list(PHASES), 'phaseRanges': [[0, 1], [2, 3], [4, 5]],
        'framesPerPhase': SAMPLES, 'intervalsPerPhase': INTERVALS, 'totalPoseSamples': 183,
        'progressFloatIndex': 4, 'gripFlagIndex': 0, 'inactiveGapGuards': 2,
        'thresholdEncoding': 'float32(phase*2 + float32(frame/60))',
        'parents': 3, 'displayChildren': 732, 'packFiles': len(output), 'generatedFiles': len(allowed),
        'bodyElements': len(source['elements']), 'shellElements': len(shell['elements']),
        'cartridgeCount': 2, 'cartridgeElementsEach': len(shell['elements']) // 2,
        'maxWeaponElements': weapon_count, 'canonicalWeaponElements': canonical_count,
        'candidateReloadWithArmsEstimate': weapon_count + ARM_RESERVE,
        'ordinaryArmReserve': ARM_RESERVE, 'maxAssembledElements': budget, 'elementLimit': 1000,
        'actualArmAssemblyMeasured': False, 'bodyGeometryAndUVPreserved': True,
        'bodyElementsAndUVSha256': sha(encode(source['elements'])), 'newTextures': 0,
        'shellAnchor': SHELL_ANCHOR, 'pairCentersY': PAIR_CENTERS_Y,
        'portDerivation': 'receiver_main east X+.085; midpoint Y; front Z+2.48, behind bolt_handle',
        'shellKeyframes': SHELL_KEYS, 'visibility': VISIBLE, 'uvDonors': UV_DONORS,
        'curve': 'C1 weighted harmonic PCHIP; zero endpoint, hold and extremum slopes',
        'seatedProgress': {'initial': .86, 'loop': .78},
        'hiddenShell': 'Empty geometry, ordinary scale; hidden HOME recycle only after seating',
        'heldSeams': [['initial', 60], ['loop', 0], ['loop', 60], ['return', 0]],
        'canonicalGraphEndpoints': [['initial', 0], ['return', 60]],
        'canonicalFallbackNonFPAndADSInspectPreserved': True,
        'rig': copy.deepcopy(provenance), 'sourceEvidence': copy.deepcopy(SOURCE_EVIDENCE),
        'sourceHeldProgress': .35, 'sourceHeldFrame': 37.4,
        'bodyCarrierNeutral': True, 'sourceWeaponMotion': True, 'sourcePalmContactFit': True,
        'sourcePoseCalibration': 'Master uses same source .35 sample for weapon AND full arm chains. Initial .35*smooth(p/.36); LOOP .35; RETURN same pose blended to rest. Authored calibration.',
        'motionAuthorship': 'Generic full-magazine scout action is not recovered Long Arm pair reload. Only cartridge geometry, material donor choice, contact target and normalized pair path are authored here.',
        'mechanicsOrAudioChanged': False, 'roundsPerInsert': 2, 'cosmeticReturnTicks': 6,
        'returnBlocksGameplay': False, 'nativeGameplayVerified': False, 'fingerIK': False,
        'masterIntegration': 'Load W222 profile/rig, bind long_arm to80A8A345 with sourceShellPoseHold and61 CMD4 bindings in each bank; compose source weapon/shoulder/elbow/wrist once; framing once. Preserve authoritative two-round insert timing, audio/ammo/inputs and6-tick cosmetic recovery. FIRST actual-image feedback, same worker review/correction, then SECOND.',
        'limitations': ['Original source contains only Armature: no weapon mesh, camera, finger IK or recovered pair events.',
                        'Receiver remains solid, with an authored side-port handling approximation; no cavity or mechanism edits.',
                        '448 is a conservative four ordinary skin-arm reserve; master measures actual integrated assembly.',
                        '61 poses are discrete samples per bank, not proof of continuous60fps interpolation.',
                        'FIRST feedback and SECOND Vision remain pending.'],
        'inputSha256': hashes,
        'outputSha256': {str(p.relative_to(root)): sha(raw) for p, raw in output.items()},
    })
    if set(output) != {root / p for p in allowed}:
        raise ValueError('Incomplete W222 output mapping')
    return output
