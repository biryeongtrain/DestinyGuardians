#!/usr/bin/env python3
"""W220 Dimensional Hypotrochoid: authored latch and complete drum exchange.

Pure stdlib, no import/generate writes. The master owns fresh original Blender
extraction, source weapon/full arm replay, materialization and native review.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ID = 'dimensional_hypotrochoid'
GROUP = 'heavy_grenade_launcher_796e9ebf'
SOURCE_ACTION = '80A8A104'
ACTION_NAME = 'Armature|fp_80A8A104_reload_full|Base'
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w220') / ID
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w220_dimensional_hypotrochoid.py')
SOURCE = A / f'models/weapon_surface_w123/{ID}.json'
TWOHAND = A / f'models/weapon/heavy_grenade_launcher/{ID}_twohand.json'
ITEM = A / f'items/weapon/{ID}.json'
TEXTURE = A / f'textures/item/weapon/w123/{ID}.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w220/rigs') / (GROUP + '.json')
KEY = f'weapon_reload_w220_{ID}/{ID}'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
PARTS = ('body', 'magazine', 'latch')
INTERVALS = 60
SAMPLES = 61
ARM_ELEMENT_RESERVE = 4 * 112
MAGAZINE_ANCHOR = (8.026, 10.16, 2.6)
# Rear end of the real left latch, not the weapon midpoint or another GL pivot.
LATCH_PIVOT = (5.62, 10.16, 5.19)
GRIP_WINDOW = (.18, .24, .52, .64)
SEATED = .68
PARTITION_INDICES = {
    'body': tuple(range(43)) + tuple(range(62, 92)),
    'magazine': tuple(range(43, 55)),
    'latch': tuple(range(55, 62)),
}
# All offsets are model units. The body's display remains canonical throughout;
# the master replays source weapon motion once, over every part and source limb.
MAGAZINE_KEYS = (
    (0., (0, 0, 0), (0, 0, 0)),
    (.20, (0, 0, 0), (0, 0, 0)),
    (.28, (0, 0, -8), (-5.6, -.5, .5)),
    (.38, (8, 0, -14), (-7.4, -5.5, 3.5)),
    (.46, (8, 0, -14), (-7.4, -5.5, 3.5)),
    (.54, (4, 0, -8), (-5.5, -2.8, 1.5)),
    (.62, (0, 0, 0), (-2.8, -.4, .15)),
    (SEATED, (0, 0, 0), (0, 0, 0)),
    (1., (0, 0, 0), (0, 0, 0)),
)
LATCH_KEYS = (
    (0., (0, 0, 0), (0, 0, 0)),
    (.08, (0, 0, 0), (0, 0, 0)),
    (.20, (0, 70, 0), (0, 0, 0)),
    (.70, (0, 70, 0), (0, 0, 0)),
    (.80, (0, 0, 0), (0, 0, 0)),
    (1., (0, 0, 0), (0, 0, 0)),
)
PHASES = [
    {'range': [0, .08], 'action': 'source reach; drum and latch seated'},
    {'range': [.08, .20], 'action': 'left latch cage pivots outward about rear mount'},
    {'range': [.20, .38], 'action': 'entire 12-solid drum extracts to the left and down'},
    {'range': [.38, .46], 'action': 'authored exchange hold; source wrist continues unchanged'},
    {'range': [.46, .64], 'action': 'replacement approaches; left source attachment fades .52..64'},
    {'range': [.64, SEATED], 'action': 'released drum completes coaxial seating'},
    {'range': [SEATED, .80], 'action': 'seated drum stays fixed; latch closes .70..80'},
    {'range': [.80, 1], 'action': 'source recovery to the original foregrip'},
]


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def tangents(times, values):
    """C1 weighted harmonic PCHIP; zero endpoint, hold and extremum slopes."""
    steps = [b-a for a, b in zip(times, times[1:])]
    secants = [(b-a)/h for a, b, h in zip(values, values[1:], steps)]
    slopes = [0.] * len(times)
    for i in range(1, len(times)-1):
        before, after = secants[i-1], secants[i]
        if before * after > 0:
            w1, w2 = 2*steps[i]+steps[i-1], steps[i]+2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before+w2/after)
    return slopes


def sample(progress, part='magazine'):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Reload progress must be finite and within 0..1')
    if part not in PARTS:
        raise ValueError(part)
    if part == 'body':
        return [0., 0., 0.], [0., 0., 0.]
    keys = MAGAZINE_KEYS if part == 'magazine' else LATCH_KEYS
    for key in keys:
        if progress == key[0]:
            return tuple(list(v) for v in key[1:])
    times = [k[0] for k in keys]
    index = next(i for i in range(len(keys)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    basis = (2*t**3-3*t*t+1, t**3-2*t*t+t, -2*t**3+3*t*t, t**3-t*t)
    result = []
    for channel in (1, 2):
        vector = []
        for axis in range(3):
            values = [k[channel][axis] for k in keys]
            slopes = tangents(times, values)
            vector.append(values[index] if values[index] == values[index+1] else
                          basis[0]*values[index] + basis[1]*h*slopes[index]
                          + basis[2]*values[index+1] + basis[3]*h*slopes[index+1])
        result.append(vector)
    return tuple(result)


def add(a, b): return [x+y for x, y in zip(a, b)]
def sub(a, b): return [x-y for x, y in zip(a, b)]
def mul(a, b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m, v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c], [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(m):
    b = math.asin(max(-1., min(1., m[0][2])))
    a, c = ((math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0]))
            if abs(math.cos(b)) > 1e-8 else (math.atan2(m[2][1], m[1][1]), 0))
    return [round(math.degrees(v), 9) for v in (a, b, c)]


def partition(source):
    expected_names = ([f'drum_solid_{i}' for i in range(4)]
                      + [f'drum_jacket_{i}' for i in range(8)]
                      + ['latch_root', 'latch_handle', 'latch_return_0.84',
                         'latch_return_5.14', 'latch_top_slope', 'latch_upper_panel', 'latch_upper_rear'])
    if len(source['elements']) != 92 or [e['name'] for e in source['elements'][43:62]] != expected_names:
        raise ValueError('Expected canonical92 with complete drum43..54 and latch55..61')
    return {part: {**{k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'},
                   'elements': [copy.deepcopy(source['elements'][i]) for i in indices]}
            for part, indices in PARTITION_INDICES.items()}


def pose_display(original, twohand, p, part, grip):
    if part not in PARTS or grip not in GRIPS:
        raise ValueError((part, grip))
    angles, shift = sample(p, part)
    accepted = original if grip == 'native' else twohand
    if angles == [0, 0, 0] and shift == [0, 0, 0]:
        return copy.deepcopy(accepted)
    motion = xyz(angles)
    pivot = sub(MAGAZINE_ANCHOR if part == 'magazine' else LATCH_PIVOT, (8, 8, 8))
    local = add(sub(pivot, vec(motion, pivot)), shift)
    display = copy.deepcopy(accepted)
    for context in FP:
        idle = accepted[context]
        scale = idle['scale']
        if scale != original[context]['scale'] or len(set(scale)) != 1:
            raise ValueError('Expected equal uniform canonical grip scales')
        base = xyz(idle['rotation'])
        display[context]['rotation'] = euler(mul(base, motion))
        display[context]['translation'] = [round(v, 9) for v in
            add(idle['translation'], vec(base, [scale[0]*v for v in local]))]
    return display


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return only exclusive absolute output paths and bytes; never write."""
    root = Path(root).resolve()
    inputs = (SOURCE, TWOHAND, ITEM, TEXTURE, CONTACTS, FRAMING,
              Path('art/weapons/w123') / ID / 'design.json',
              Path('src/main/resources/destiny/weapons/w46-timing.json'),
              Path('src/main/resources/destiny/sounds/w63-reload.json'))
    raw = {path: (root/path).read_bytes() for path in inputs}
    raw[GENERATOR] = Path(__file__).read_bytes()
    raw[PROFILE] = Path(profile_path or root/PROFILE).read_bytes()
    raw[RIG] = Path(rig_path or root/RIG).read_bytes()
    source, twohand, item, profile, rig = (json.loads(raw[p]) for p in (SOURCE, TWOHAND, ITEM, PROFILE, RIG))
    reload = profile.get('contacts', {}).get('reload', {})
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W220'
            or profile.get('weapon') != ID or profile.get('sourceAction') != SOURCE_ACTION
            or reload.get('hand') != 'left' or reload.get('rigAction') != SOURCE_ACTION
            or reload.get('partHint') != 'magazine' or reload.get('policy') != 'magazine'
            or reload.get('gripWindow') != list(GRIP_WINDOW)
            or any(profile['framing'].get(k) is not v for k, v in
                   {'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}.items())):
        raise ValueError('Expected W220 left whole-drum full-chain profile')
    current = json.loads(raw[CONTACTS])['weapons'][ID]
    for side in ('right', 'left'):
        if profile['contacts'][side] != current[side]:
            raise ValueError('Existing idle grip changed: '+side)
    for key in ('contact', 'rotation'):
        if reload[key] != current['reload'][key]:
            raise ValueError('Existing drum flank contact changed: '+key)
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist', 'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != GROUP or rig.get('fallback') is not False or ID not in rig['weapons']
            or rig.get('cameraExported') is not False
            or rig.get('w220Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1., 142.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i/INTERVALS or abs(f['frame']-(1+141*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys() for i, f in enumerate(action['frames']))):
        raise ValueError('Fresh original heavy104 full-chain61 source samples required')
    if (profile['sourceRig']['group'] != GROUP or profile['sourceRig']['action'] != SOURCE_ACTION
            or any(rig[k] != profile['sourceRig'][k] for k in
                   ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'))):
        raise ValueError('Source provenance differs from reviewed original')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    if counts != {'body': 73, 'magazine': 12, 'latch': 7}:
        raise ValueError('Incomplete mechanical partition')
    model_counts = {}

    def model_count(ref, visiting=()):
        if not ref.startswith('destiny:') or ref in visiting:
            raise ValueError('Unexpected canonical model reference: '+ref)
        if ref not in model_counts:
            path = A / ('models/'+ref.split(':', 1)[1]+'.json')
            if path not in raw:
                raw[path] = (root/path).read_bytes()
            model = json.loads(raw[path])
            model_counts[ref] = len(model['elements']) if 'elements' in model else model_count(model['parent'], (*visiting, ref))
        return model_counts[ref]

    def route_count(node):
        kind = node['type']
        if kind == 'minecraft:model': return model_count(node['model'])
        if kind == 'minecraft:composite': return sum(route_count(c) for c in node['models'])
        if kind == 'minecraft:condition': return max(route_count(node['on_true']), route_count(node['on_false']))
        if kind in ('minecraft:select', 'minecraft:range_dispatch'):
            return max([route_count(node['fallback']), *(route_count(c['model']) for c in node.get('cases', node.get('entries', [])))])
        raise ValueError('Unhandled canonical route: '+kind)

    canonical_count = route_count(item['model'])
    maximum = max(canonical_count, sum(counts.values())) + ARM_ELEMENT_RESERVE
    if maximum > 1000:
        raise ValueError('Assembled output plus four ordinary arm surfaces exceeds1000')
    output, allowed = {}, expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W220 namespace')
        output[root/path] = encode(value)

    for part, model in geometries.items():
        emit(A / f'models/{KEY}_{part}.json', model)
    entries = []
    for i in range(SAMPLES):
        p = i/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f'models/{KEY}_{i:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand['display'], p, part, grip)})

        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_{part}_{grip}'} for part in PARTS]}

        node = copy.deepcopy(item['model']) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data',
            'index': 0, 'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(p), 'model': node})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select' or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index', 0) != 0 or [c['when'] for c in guard['cases']] != ['ads', 'inspect']):
        raise ValueError('Expected canonical ADS/inspect guard')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W220', 'weapon': ID, 'revision': 1,
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:'+KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60)',
        'curve': 'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes': {'magazine': MAGAZINE_KEYS, 'latch': LATCH_KEYS}, 'normalizedPhases': PHASES,
        'magazineAnchor': MAGAZINE_ANCHOR, 'latchPivot': LATCH_PIVOT,
        'magazineExtractionAxis': [-1, 0, 0], 'magazineSeatedProgress': SEATED,
        'latchClosedProgress': .80, 'gripWindow': GRIP_WINDOW,
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': 92, 'partElements': counts, 'weaponElements': 92,
        'bodyElements': 73, 'magazineElements': 12, 'latchElements': 7,
        'movingElements': 19, 'addedElements': 0, 'triangleAdapterElements': 0,
        'partitionIndices': PARTITION_INDICES,
        'movingIndices': list(range(43, 62)),
        'movingNames': [e['name'] for e in source['elements'][43:62]],
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': 92+ARM_ELEMENT_RESERVE,
        'canonicalModelElements': model_counts, 'canonicalWeaponElements': canonical_count,
        'maxAssembledElements': maximum, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': 'Resolved canonical alternative maximum or simultaneous73+12+7, plus448 arm reserve. Master measures materialized full-chain arms.',
        'sourceElementsAndUVSha256': sha(encode(source['elements'])),
        'partElementsAndUVSha256': {p: sha(encode(m['elements'])) for p, m in geometries.items()},
        'canonicalGeometryAndUVPreserved': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Current canonical graph at0/1,negative,overshoot,nonFP; ADS/inspect precede reload; native/twohand preserved.',
        'sourceAction': SOURCE_ACTION, 'rigAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': GROUP, 'sourceRigPath': str(RIG), 'sourceRigSamples': len(action['frames']),
        'sourceActionSourceRange': [action['start'], action['end']],
        'sourceFullChain': True, 'sourceCameraRecovered': False,
        'hand': 'left', 'partHint': 'magazine', 'policy': 'magazine',
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'New authored rear-hinged left latch55..61 and whole drum43..54 exchange. Fixed body has identity authored motion so master source weapon replay is applied once. One drum represents outgoing/incoming assemblies, with an exchange hold; no per-round or duplicate drum geometry. Shared class action104 is not a recovered per-weapon selector or mesh mechanism.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed),
        'staticParts': len(PARTS), 'parentDisplayChildren': SAMPLES*len(PARTS)*len(GRIPS),
        'limitations': [
            'Master evaluated original Blender5.4 Alpha and61 samples. Worker read those results and viewed the actual chosen bone sheet; no independent Blender evaluation.',
            'Original ARMATURE only; no recovered weapon mesh, camera, finger IK or latch event track. Pivot, clearances and replacement mechanics are authored for canonical92.',
            'Left source attachment fades.52..64, zero before.68 seat; source hand/shoulder chain is never damped, stretched, hidden or moved to match the drum.',
            '61 poses/60 intervals do not establish continuous native60fps interpolation.',
            'Full-chain visible arm budget, native contacts, latch clearance, FIRST feedback and SECOND Vision remain master verification.'],
        'inputSha256': {str(p): sha(data) for p, data in raw.items()},
        'outputSha256': {str(p.relative_to(root)): sha(data) for p, data in output.items()},
    })
    if set(output) != {root/p for p in allowed}:
        raise ValueError('Incomplete W220 output mapping')
    return output
