#!/usr/bin/env python3
"""W220 Deafening Whisper: authored break-open mechanism, source136 arm replay.

Pure stdlib; import/generate never write. Master installs the rig and outputs,
binds the new route and performs FIRST/correction/SECOND native review.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w220/deafening_whisper')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w220_deafening_whisper.py')
SOURCE = A / 'models/weapon_surface_w123/deafening_whisper.json'
TWOHAND = A / 'models/weapon/grenade_launcher/deafening_whisper_twohand.json'
ITEM = A / 'items/weapon/deafening_whisper.json'
TEXTURE = A / 'textures/item/weapon/w123/deafening_whisper.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w220/rigs/grenade_launcher_83c75a3c.json')
GROUP = 'grenade_launcher_83c75a3c'
SOURCE_ACTION = '80A8A136'
ACTION_NAME = 'Armature|fp_80A8A136_reload_full|Base'
KEY = 'weapon_reload_w220_deafening_whisper/deafening_whisper'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
PARTS = ('body', 'barrel', 'round')
INTERVALS = 60
SAMPLES = 61
ARM_ELEMENT_RESERVE = 4 * 112
# Lower front corner of the fixed breech, derived from this weapon's receiver
# y11.09..11.55 and breech z8.95..10.55. This is not Salvo's hinge.
HINGE = (8.0, 11.34, 8.95)
ROUND_CENTER = (8.0, 12.94, 8.18)
# W204 palm origin is inside its fingerless box, not on its exterior. This
# virtual palm anchor places the case against the outer source-driven hand;
# the old x7.25 case-surface anchor embedded the payload in the forearm.
# Only the bounded round attachment uses it; zero-weight seat is unchanged.
ROUND_CONTACT = (5.5, 13.5, 8.5)
GRIP_WINDOW = (.27, .30, .38, .46)
ROUND_VISIBLE = tuple(range(17, 29))
BARREL = tuple([*range(0, 16), *range(20, 46), *range(53, 56), *range(60, 87)])
SEMANTIC_GROUPS = {
    'barrel_and_muzzle': list(range(16)), 'fixed_breech': list(range(16, 20)),
    'sleeves_divider_and_rails': list(range(20, 46)),
    'fixed_receiver_and_stock': list(range(46, 53)),
    'hinged_foregrip': list(range(53, 56)),
    'fixed_pistol_grip_and_trigger': list(range(56, 60)),
    'hinged_laser_and_cables': list(range(60, 71)),
    'hinged_counter_and_wrap_latch': list(range(71, 78)),
    'hinged_open_sight': list(range(78, 87)), 'fixed_rear_indicator': [87]}
# progress, hinge angle in degrees, incoming round offset in the open bore frame.
# No authored body cant/translation: master replays the original weapon bone.
KEYS = (
    (0., 0., (0., 0., 5.2)), (.10, 0., (0., 0., 5.2)),
    (.25, -52., (0., 0., 5.2)), (.28, -52., (-1.2, .6, 4.8)),
    (.34, -52., (-.7, .35, 3.6)), (.40, -52., (-.15, .1, 1.8)),
    (.46, -52., (0., 0., 0.)), (.50, -52., (0., 0., 0.)),
    (.68, 0., (0., 0., 0.)), (.84, 0., (0., 0., 0.)),
    (1., 0., (0., 0., 0.)))


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def tangents(times, values):
    """C1 weighted harmonic PCHIP, zero at endpoints, holds and extrema."""
    h = [b-a for a, b in zip(times, times[1:])]
    d = [(b-a)/step for a, b, step in zip(values, values[1:], h)]
    slopes = [0.] * len(times)
    for i in range(1, len(times)-1):
        if d[i-1]*d[i] > 0:
            w1, w2 = 2*h[i]+h[i-1], h[i]+2*h[i-1]
            slopes[i] = (w1+w2)/(w1/d[i-1]+w2/d[i])
    return slopes


def sample(progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Progress must be finite within 0..1')
    for p, angle, offset in KEYS:
        if p == progress:
            return angle, list(offset)
    times = [k[0] for k in KEYS]
    i = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[i+1]-times[i]
    t = (progress-times[i])/h
    def channel(values):
        if values[i] == values[i+1]:
            return values[i]
        m = tangents(times, values)
        return ((2*t**3-3*t*t+1)*values[i] + (t**3-2*t*t+t)*h*m[i]
                + (-2*t**3+3*t*t)*values[i+1] + (t**3-t*t)*h*m[i+1])
    return channel([k[1] for k in KEYS]), [channel([k[2][a] for k in KEYS]) for a in range(3)]


def add(a, b): return [x+y for x, y in zip(a, b)]
def sub(a, b): return [x-y for x, y in zip(a, b)]
def mul(a, b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m, v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c], [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(m):
    y = math.asin(max(-1., min(1., m[0][2])))
    x, z = ((math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0]))
            if abs(math.cos(y)) > 1e-8 else (math.atan2(m[2][1], m[1][1]), 0.))
    return [round(math.degrees(v), 9) for v in (x, y, z)]


def round_elements(source):
    """A short hex case plus shallow rim; no breech geometry used as a round.

    Reuse neutral socket steel faces. It is a cosmetic authored payload, not
    a recovered ammunition mesh or gameplay ammo event.
    """
    faces = source['elements'][53]['faces']
    result = []
    for name, radius, z0, z1 in (('case', .72, 6.8, 9.4), ('rim', .79, 9.4, 9.56)):
        for angle in (0, 60, 120):
            result.append({'name': f'cosmetic_round_{name}_{angle}',
                           'from': [8-radius, 12.94-radius/math.sqrt(3), z0],
                           'to': [8+radius, 12.94+radius/math.sqrt(3), z1],
                           'rotation': {'origin': list(ROUND_CENTER), 'axis': 'z', 'angle': angle},
                           'faces': copy.deepcopy(faces)})
    return result


def partition(source):
    result = {}
    for part in PARTS:
        result[part] = {k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'}
        result[part]['elements'] = (round_elements(source) if part == 'round' else
            [copy.deepcopy(e) for i, e in enumerate(source['elements']) if (i in BARREL) == (part == 'barrel')])
    return result


def pose_display(original, twohand, progress, part, grip):
    if part not in PARTS or grip not in GRIPS:
        raise ValueError((part, grip))
    accepted = original if grip == 'native' else twohand
    display = copy.deepcopy(accepted)
    if progress in (0, 1) or part == 'body':
        return display
    angle, offset = sample(progress)
    motion = xyz([angle, 0, 0])
    pivot = sub(HINGE, (8, 8, 8))
    local = sub(pivot, vec(motion, pivot))
    if part == 'round':
        local = add(local, vec(motion, offset))
    for context in FP:
        # Use the selected carrier frame directly; scale exactly once.
        idle = accepted[context]
        if len(set(idle['scale'])) != 1 or idle['scale'] != original[context]['scale']:
            raise ValueError('Uniform, equal canonical native/twohand scales required')
        base = xyz(idle['rotation'])
        display[context]['rotation'] = euler(mul(base, motion))
        display[context]['translation'] = [round(v, 9) for v in add(
            idle['translation'], vec(base, [idle['scale'][0]*v for v in local]))]
    return display


def expected_output_paths():
    return ({A / f'models/{KEY}_{part}.json' for part in PARTS}
            | {A / f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(SAMPLES) for part in PARTS for grip in GRIPS}
            | {A / f'items/{KEY}.json', MANIFEST})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return absolute paths and bytes without materializing files."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE, CONTACTS, FRAMING,
              Path('art/weapons/w123/deafening_whisper/design.json'),
              Path('scripts/first_person_framing_w205.py'), Path('scripts/reload_hand_w218.py'),
              Path('scripts/rig_arms_w205.py'), Path('scripts/build_first_person_hands_w201.py'),
              Path('scripts/skin_arm_models_w204.py'),
              Path('src/main/resources/destiny/weapons/w46-timing.json'),
              Path('src/main/resources/destiny/sounds/w63-reload.json')]
    raw = {p: (root/p).read_bytes() for p in inputs}
    raw[GENERATOR] = Path(__file__).read_bytes()
    raw[PROFILE] = Path(profile_path or root/PROFILE).read_bytes()
    raw[RIG] = Path(rig_path or root/RIG).read_bytes()
    source, twohand, item, profile, rig = (json.loads(raw[p]) for p in (SOURCE, TWOHAND, ITEM, PROFILE, RIG))
    if len(source['elements']) != 88 or len(set(BARREL)) != 72:
        raise ValueError('Expected canonical88 / fixed16 / hinged72')
    design = json.loads(raw[Path('art/weapons/w123/deafening_whisper/design.json')])
    if [p['geometry']['name'] for p in design['parts']] != [e['name'] for e in source['elements']]:
        raise ValueError('Canonical semantic part order changed')
    reload = profile.get('contacts', {}).get('reload', {})
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W220'
            or profile.get('weapon') != 'deafening_whisper' or profile.get('sourceAction') != SOURCE_ACTION
            or reload.get('rigAction') != SOURCE_ACTION or reload.get('hand') != 'left'
            or reload.get('partHint') != 'round' or reload.get('policy') != 'magazine'
            or reload.get('contact') != list(ROUND_CONTACT) or reload.get('gripWindow') != list(GRIP_WINDOW)
            or any(profile['framing'].get(k) is not v for k, v in
                   {'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}.items())):
        raise ValueError('Expected W220 full-chain profile with bounded round-only attachment')
    current = json.loads(raw[CONTACTS])['weapons']['deafening_whisper']
    if any(profile['contacts'][side] != current[side] for side in ('right', 'left')):
        raise ValueError('Preserve existing idle grip contacts')
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist', 'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != GROUP or rig.get('fallback') is not False
            or 'deafening_whisper' not in rig['weapons'] or rig.get('cameraExported') is not False
            or rig.get('w220Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1., 89.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i/INTERVALS or abs(f['frame']-(1+88*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys() for i, f in enumerate(action['frames']))):
        raise ValueError('Fresh W220 source136 full upper chains required')
    if profile['sourceRig']['group'] != GROUP or profile['sourceRig']['action'] != SOURCE_ACTION or any(
            rig[k] != profile['sourceRig'][k] for k in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256')):
        raise ValueError('Source provenance differs from profile')
    geometries = partition(source)
    counts = {p: len(g['elements']) for p, g in geometries.items()}
    if counts != {'body': 16, 'barrel': 72, 'round': 6}:
        raise ValueError('Unexpected part count')
    output = {}
    allowed = expected_output_paths()
    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive weapon namespace')
        output[root/path] = encode(value)
    # Resolve current canonical alternatives. Composite counts add, selection
    # counts take max; full and split alternatives must never be double counted.
    model_counts = {}
    def model_count(key, trail=()):
        if key in trail: raise ValueError('Model parent cycle')
        p = A/'models'/(key.split(':', 1)[-1]+'.json')
        if p not in raw: raw[p] = (root/p).read_bytes()
        m = json.loads(raw[p])
        n = len(m['elements']) if 'elements' in m else model_count(m['parent'], trail+(key,))
        model_counts[key] = n
        return n
    def graph_count(n):
        if isinstance(n, list): return max([graph_count(v) for v in n] or [0])
        if not isinstance(n, dict): return 0
        if n.get('type') == 'minecraft:model': return model_count(n['model'])
        if n.get('type') == 'minecraft:composite': return sum(graph_count(v) for v in n['models'])
        return max([graph_count(v) for v in n.values()] or [0])
    canonical_count = graph_count(item['model'])
    maximum = max(sum(counts.values()), canonical_count)+ARM_ELEMENT_RESERVE
    if maximum > 1000: raise ValueError('Conservative assembled budget exceeded')
    for part, geo in geometries.items(): emit(A/f'models/{KEY}_{part}.json', geo)
    entries = []
    for i in range(SAMPLES):
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand['display'], i/INTERVALS, part, grip)})
        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_{part}_{grip}'}
                for part in PARTS if part != 'round' or i in ROUND_VISIBLE]}
        node = (copy.deepcopy(item['model']) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data',
            'index': 0, 'on_true': composite('twohand'), 'on_false': composite('native')})
        entries.append({'threshold': float32(i/INTERVALS), 'model': node})
    # Last threshold1 is itself canonical, so overshoot clamps to that exact
    # graph; negative inactive values use fallback. Runtime owns nonfinite input.
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select' or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index', 0) != 0 or [c['when'] for c in guard['cases']] != ['ads', 'inspect']):
        raise ValueError('Expected canonical ADS/inspect selector')
    guard['fallback'] = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                         'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A/f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W220', 'weapon': 'deafening_whisper', 'revision': 2,
        'generator': str(GENERATOR), 'itemModel': 'destiny:'+KEY,
        'frames': SAMPLES, 'intervals': INTERVALS, 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'firstPersonContexts': list(FP), 'thresholdEncoding': 'exact float32(i/60)',
        'curve': 'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'hingePivot': HINGE, 'roundCenter': ROUND_CENTER,
        'gripWindow': GRIP_WINDOW, 'roundSeatedProgress': .46, 'roundVisibleSamples': ROUND_VISIBLE,
        'roundContact': ROUND_CONTACT,
        'roundContactCalibration': 'Virtual palm anchor accounts for W204 classic box width/depth2.4 and Y9 hand cap beyond internal Y8 palm origin. FIRST exposed case/forearm embedding. Cosmetic round only shifts outward while attached; source arms and zero-weight seat unchanged.',
        'normalizedPhases': {'unlock': [0, .10], 'open': [.10, .25], 'openDwell': [.25, .50],
                             'roundApproachAndInsert': [.28, .46], 'handClear': [.46, .50],
                             'close': [.50, .68], 'recover': [.68, 1]},
        'partitionIndices': {'body': [i for i in range(88) if i not in BARREL], 'barrel': list(BARREL)},
        'semanticGroups': SEMANTIC_GROUPS,
        'movingIndices': list(BARREL), 'movingNames': [source['elements'][i]['name'] for i in BARREL],
        'fixedNames': [e['name'] for i, e in enumerate(source['elements']) if i not in BARREL],
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': 88, 'partElements': counts, 'bodyElements': 16, 'barrelElements': 72,
        'roundElements': 6, 'weaponElements': 94, 'addedElements': 6, 'triangleAdapterElements': 0,
        'canonicalModelElements': model_counts, 'canonicalWeaponElements': canonical_count,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE, 'candidateReloadWithArmsEstimate': 94+ARM_ELEMENT_RESERVE,
        'maxAssembledElements': maximum, 'elementLimit': 1000, 'assembledBudgetVerified': False,
        'budgetBasis': 'Maximum parent-resolved canonical alternative or active16+72+6, plus448 ordinary arm elements; master measures materialized routes.',
        'sourceElementsAndUVSha256': sha(encode(source['elements'])),
        'partElementsAndUVSha256': {p: sha(encode(g['elements'])) for p, g in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'newTexture': False,
        'reloadOnlyGeometry': {'elements': geometries['round']['elements'], 'UVSource': 'Canonical front_grip_socket53 faces'},
        'hipEndpoints': [0, 60], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Exact canonical graph at0/1,negative inactive,overshoot and nonFP; canonical ADS/inspect precedence.',
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': GROUP, 'sourceRigPath': str(RIG), 'sourceActionSourceRange': [1, 89],
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True, 'sourceCameraRecovered': False,
        'hand': 'left', 'partHint': 'round', 'policy': 'magazine',
        'motionAuthorship': 'New weapon-specific lower-front-breech hinge and52deg break, open dwell and short incoming case path. Fixed receiver/breech/stock. Barrel is gun-attached throughout; only six-solid cosmetic round may follow left palm during bounded insertion. No authored body transform duplicates source weapon replay.',
        'sourceReviewEvidence': profile['evidence'], 'gameplayTimingChanged': False,
        'mechanicsOrAudioChanged': False, 'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': 3,
        'parentDisplayChildren': SAMPLES*len(PARTS)*len(GRIPS),
        'limitations': profile['notes'],
        'inputSha256': {str(p): sha(b) for p, b in raw.items()},
        'outputSha256': {str(p.relative_to(root)): sha(b) for p, b in output.items()}})
    if set(output) != {root/p for p in allowed}:
        raise ValueError('Incomplete exclusive output mapping')
    return output
