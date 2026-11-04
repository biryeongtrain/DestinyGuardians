#!/usr/bin/env python3
"""W219 Retraced Path: exact W170 pack, 61-pose C1 weighted harmonic PCHIP.

Pure stdlib. Import and generate are read-only; generate(root=ROOT) returns
absolute Path->bytes. Master materializes outputs and attaches source full arms.
Original source was evaluated by master; this worker reviewed its evidence.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w219/retraced_path')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w219_retraced_path.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w170_retraced_path.py')
AUTHORED_MANIFEST = Path('art/weapons/w170/retraced_path/manifest.json')
REFERENCE = Path('art/weapons/w170/retraced_path/motion-reference.json')
SOURCE = A / 'models/weapon_surface_w123/retraced_path.json'
NATIVE = A / 'models/weapon/trace_rifle/retraced_path.json'
TWOHAND = A / 'models/weapon/trace_rifle/retraced_path_twohand.json'
ITEM = A / 'items/weapon/retraced_path.json'
TEXTURE = A / 'textures/item/weapon/w123/retraced_path.png'
DESIGN = Path('art/weapons/w123/retraced_path/design.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w219/rigs/trace_rifle_1c48cd94.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w219/source/source-review.json')
SOURCE_SCRATCH = Path('/private/tmp/destiny-w219-source')
KEY = 'weapon_reload_w219_retraced_path/retraced_path'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'moving')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8A43C'
ACTION_NAME = 'Armature|fp_80A8A43C_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.09, .23, .62, .70)

MOVING = (78,79,80,81)
NAMES = ('magazine_well','magazine_foot','magazine_blue_edge_-1','magazine_blue_edge_1')
FIXED_HOUSING = (17,19,21,22,25,26,33,35,37,38,41,42,49,74,75)
FIXED_NAMES = ('upper_rail_-1','lower_rail_-1','upper_broad_casing_-1','lower_broad_casing_-1',
 'sweeping_receiver_-1','sweeping_receiver_lower_-1','upper_rail_1','lower_rail_1',
 'upper_broad_casing_1','lower_broad_casing_1','sweeping_receiver_1','sweeping_receiver_lower_1',
 'receiver_solid','rear_action','upper_action_spine')
GRIP = (8,9.145,9.61)
PACK_INSERTION_ANCHOR = (8,9.12,3.55)
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.09,(-7,-3,4),(-.08,-.12,0),(0,0,0)),
 (.23,(39,-10,23),(-.18,.12,-.20),(0,-.35,.080555556)),
 (.35,(40,-10,24),(-.18,.12,-.20),(0,-4.5,1.035714286)),
 (.51,(39,-10,24),(-.18,.10,-.20),(0,-4.5,1.035714286)),
 (.62,(37,-10,23),(-.17,.10,-.20),(0,-2.5,.575396825)),
 (.70,(39,-10,24),(-.18,.15,-.20),(0,0,0)),
 (.76,(43,-10,25),(-.18,.25,-.20),(0,0,0)),
 (.84,(34,-8,20),(-.12,.08,-.14),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()

def sha(b): return hashlib.sha256(b).hexdigest()

def add(a,b): return [x+y for x,y in zip(a,b)]

def sub(a,b): return [x-y for x,y in zip(a,b)]

def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]

def transpose(m): return list(map(list,zip(*m)))

def xyz(angles):
    x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]

def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
    return [round(math.degrees(v),9) for v in (a,b,c)]

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    local=add(sub(h,vec(body,h)),vec(body,offset if part=='moving' else (0,0,0)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale'] != s: raise ValueError('Grip scale mismatch')
        if len(set(s))!=1: raise ValueError('Rigid part motion requires uniform first-person scale')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]

def tangents(times, values):
    """Shared C1 weighted harmonic slopes; zero at endpoints, holds, extrema."""
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
    """Evaluate the unchanged authored knots with shape-preserving Hermite."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) for v in key[1:])
    times = [key[0] for key in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    result = []
    for channel in range(1, 4):
        vector = []
        for axis in range(3):
            values = [key[channel][axis] for key in KEYS]
            slopes = tangents(times, values)
            vector.append(values[index] if values[index] == values[index+1] else
                          h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read current inputs and return only own bank; never materialize output.

    During the authorized preparation phase, own source/profile and master's
    freshly evaluated rig/report may live in scratch. Installed root inputs
    always take precedence. Shared file hashes are observations, never pins.
    """
    root = Path(root).resolve()
    raw = {}

    def read(path, fallback=None):
        target = root / path
        if not target.is_file() and fallback is not None:
            target = fallback
        data = target.read_bytes()
        raw[path] = data
        return data

    for path in (SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, AUTHORED_SOURCE,
                 AUTHORED_MANIFEST, REFERENCE, DESIGN, CONTACTS, FRAMING):
        read(path)
    read(GENERATOR, Path(__file__))
    read(PROFILE, ROOT / PROFILE)
    read(RIG, SOURCE_SCRATCH / RIG.name)
    read(SOURCE_REVIEW, SOURCE_SCRATCH / 'source-review.json')
    source, twohand, item, old, reference, design, contacts, framing, profile, rig, report = (
        json.loads(raw[path]) for path in (SOURCE, TWOHAND, ITEM, AUTHORED_MANIFEST,
        REFERENCE, DESIGN, CONTACTS, FRAMING, PROFILE, RIG, SOURCE_REVIEW))
    twohand = twohand['display']
    literals = {node.targets[0].id: ast.literal_eval(node.value)
                for node in ast.parse(raw[AUTHORED_SOURCE]).body
                if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ('KEYS', 'GRIP', 'PACK_INSERTION_ANCHOR',
                                           'MOVING', 'NAMES', 'FIXED_HOUSING', 'FIXED_NAMES')}
    expected = dict(KEYS=KEYS, GRIP=GRIP, PACK_INSERTION_ANCHOR=PACK_INSERTION_ANCHOR,
                    MOVING=MOVING, NAMES=NAMES, FIXED_HOUSING=FIXED_HOUSING,
                    FIXED_NAMES=FIXED_NAMES)
    if literals != expected or old['keyframes'] != json.loads(encode(KEYS)):
        raise ValueError('W170 exact authored keys/holds/pivots/partition changed')
    elements = source['elements']
    if (len(elements) != 99 or [elements[i]['name'] for i in MOVING] != list(NAMES)
            or [elements[i]['name'] for i in FIXED_HOUSING] != list(FIXED_NAMES)
            or old['gripPivot'] != list(GRIP)
            or old['packInsertionAnchor'] != list(PACK_INSERTION_ANCHOR)
            or old['movingIndices'] != list(MOVING)
            or [p['geometry']['name'] for p in design['parts']
                if p['group'] == 'magazine'] != list(NAMES)):
        raise ValueError('Whole existing pack/housing/anchor semantics changed')
    base_contacts = contacts['weapons']['retraced_path']
    effective = {**framing['families']['trace_rifle'],
                 **framing.get('weapons', {}).get('retraced_path', {})}
    for flag, value in (('sourceFullChain', True), ('keepMeshSupport', True),
                        ('hideSupportAtRest', False)):
        effective.setdefault(flag, value)
    expected_reload = {**base_contacts['reload'], 'rigAction': SOURCE_ACTION,
        'hand': 'left', 'partHint': 'moving', 'policy': 'magazine',
        'gripWindow': list(GRIP_WINDOW)}
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W219'
            or profile.get('weapon') != 'retraced_path'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile['framing'] != effective
            or profile['contacts'] != {'right': base_contacts['right'],
                'left': base_contacts['left'], 'reload': expected_reload}):
        raise ValueError('Existing effective framing/contacts or W219 reload role changed')
    evidence = report['groups']['trace_rifle_1c48cd94']
    action = rig['actions'][SOURCE_ACTION]
    marker = rig.get('w219Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'trace_rifle_1c48cd94' or rig.get('fallback') is not False
            or 'retraced_path' not in rig['weapons'] or rig.get('cameraExported') is not False
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('exporterSha256') != report['exporterSha256']
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 106.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i / INTERVALS
                   or abs(f['frame'] - (1 + 105*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys()
                   for i, f in enumerate(action['frames']))
            or evidence['actions'][SOURCE_ACTION]['action'] != ACTION_NAME
            or evidence['actions'][SOURCE_ACTION]['slot'] != 'OBSlot'
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1., 106.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['actions'][SOURCE_ACTION]['maxExistingCacheJointAbsError'] != 0
            or evidence['objects'] != [{'name': 'Armature', 'type': 'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Fresh evaluated original trace-rifle full chain required')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if (rig[key] != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance mismatch: ' + key)
    if (profile['sourceRig']['path'] != str(RIG)
            or profile['sourceRig']['group'] != rig['group']
            or profile['sourceRig']['action'] != SOURCE_ACTION):
        raise ValueError('Invalid W219 sourceRig profile')
    geometries = {}
    for part in PARTS:
        model = copy.deepcopy(source)
        model['elements'] = [copy.deepcopy(e) for i, e in enumerate(elements)
                             if (i in MOVING) == (part == 'moving')]
        geometries[part] = model
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    if counts != {'body': 95, 'moving': 4}:
        raise ValueError('Expected exact95 fixed plus4 whole-pack elements')

    # Count actual weapon elements in every current canonical alternative.
    # Model-parent inheritance is resolved; alternatives are never summed.
    def model_count(key, stack=()):
        if key in stack:
            raise ValueError('Cyclic canonical model: ' + key)
        if not key.startswith('destiny:'):
            raise ValueError('Unresolved external canonical model: ' + key)
        path = A / ('models/' + key.split(':', 1)[1] + '.json')
        model = json.loads(raw[path] if path in raw else read(path))
        if 'elements' in model:
            return len(model['elements'])
        return model_count(model['parent'], (*stack, key))

    def route_count(node):
        kind = node['type'].removeprefix('minecraft:')
        if kind == 'model':
            return model_count(node['model'])
        if kind == 'empty':
            return 0
        if kind == 'composite':
            return sum(route_count(m) for m in node['models'])
        if kind == 'condition':
            return max(route_count(node['on_true']), route_count(node['on_false']))
        if kind in ('select', 'range_dispatch'):
            branches = node['cases'] if kind == 'select' else node['entries']
            return max([route_count(node['fallback']),
                        *(route_count(b['model']) for b in branches)])
        raise ValueError('Unresolved canonical graph type: ' + kind)

    canonical_count = route_count(item['model'])
    max_weapon = max(sum(counts.values()), canonical_count)
    max_assembly = max_weapon + ARM_ELEMENT_RESERVE
    if max_assembly > 1000:
        raise ValueError('Actual weapon alternative plus4 classic arm surfaces exceeds1000')
    allowed = expected_output_paths()
    output = {}

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W219 Retraced Path namespace')
        output[root / path] = encode(value)

    for part, model in geometries.items():
        emit(A / f'models/{KEY}_{part}.json', model)
    entries = []
    for i in range(SAMPLES):
        progress = i / INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f'models/{KEY}_{i:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand, progress, part, grip)})

        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_{part}_{grip}'}
                for part in PARTS]}

        node = copy.deepcopy(item['model']) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': node})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select'
            or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index', 0) != 0
            or [c['when'] for c in guard['cases']] != ['ads', 'inspect']):
        raise ValueError('Canonical ADS/inspect guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W219', 'weapon': 'retraced_path',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; shared knot derivatives; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'packInsertionAnchor': PACK_INSERTION_ANCHOR,
        'gripWindow': list(GRIP_WINDOW), 'hand': 'left',
        'authoredTimingSource': str(AUTHORED_SOURCE), 'normalizedPhases': old['normalizedPhases'],
        'reference': reference['url'], 'referenceConfidence': reference['referenceConfidence'],
        'referencePolicy': 'Worker viewed retained W170 actual gameplay storyboard/comparison; master evaluated original blend and worker viewed fresh source-chain PNG. Original video was not reopened.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': counts['body'],
        'movingElements': counts['moving'], 'weaponElements': sum(counts.values()),
        'canonicalWeaponElements': canonical_count, 'maxWeaponRouteElements': max_weapon,
        'addedElements': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': sum(counts.values()) + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': max_assembly, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'weaponRouteBudgetMeasured': True,
        'budgetBasis': 'Maximum current canonical graph or reload assembly plus448 for4 classic player-skin arm surfaces; full and split alternatives are not summed. Master must check final composed routes.',
        'movingIndices': list(MOVING), 'movingNames': list(NAMES),
        'fixedHousingIndices': list(FIXED_HOUSING), 'fixedHousingNames': list(FIXED_NAMES),
        'partitionRationale': old['partitionRationale'],
        'payloadPolicy': 'Unchanged complete4-element tilted underslung pack, constant scale, visible in every reload pose. Fixed rails/receiver/discs remain body. No fusion geometry or motion borrowed.',
        'payloadHiddenInterval': None,
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements']))
                                    for part, model in geometries.items()},
        'geometryAndUVPreserved': True, 'canonicalGeometryAndUVPreserved': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Exact canonical graph at0/1, overshoot, negative inactive and non-FP; canonical ADS/inspect precede reload; native/twohand flags retained.',
        'rigPath': str(RIG), 'sourceReviewPath': str(SOURCE_REVIEW),
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION,
        'rigActionName': action['action'], 'sourceGroup': rig['group'],
        'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceCameraRecovered': False, 'sourceWeaponMeshRecovered': False,
        'sourceFingerIKRecovered': False, 'partHint': 'moving', 'policy': 'magazine',
        'originalBlend': evidence['paths']['sourceBlend'],
        'originalBlendSha256': rig['sourceBlendSha256'],
        'sourceReviewEvidence': profile['evidence'],
        'motionAuthorship': 'Exact10 W170 Retraced Path keys/holds/anchors/rigid transforms and complete pack. Only dense C1 interpolation changes. Master loads original trace-rifle action and ordinary shoulder/elbow/wrist full chain without length stretch or axis damping.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'timingPolicy': 'Normalized presentation only; existing ammo, cadence, reload clocks, speed effects and sounds untouched. Source frame span is not a gameplay reload duration override.',
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'firstVisionReviewed': False, 'secondVisionVerified': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': len(PARTS),
        'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': profile['limitations'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W219 Retraced Path output mapping')
    return output
