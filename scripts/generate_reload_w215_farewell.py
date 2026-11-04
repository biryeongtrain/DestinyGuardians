#!/usr/bin/env python3
"""W215 Farewell: 61 poses preserving W184 authored carrier/payload knots.

Pure stdlib; import and generate(root=ROOT) never write files or caches.
Master materializes the returned absolute Path->bytes map, binds evaluated61
source arms/action, measures assembled routes, and owns FIRST/SECOND Vision.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w215/farewell')
KEY = 'weapon_reload_w215_farewell/farewell'
SOURCE = A / 'models/weapon_surface_w123/farewell.json'
TWOHAND = A / 'models/weapon/sidearm/farewell_twohand.json'
ITEM = A / 'items/weapon/farewell.json'
TEXTURE = A / 'textures/item/weapon/w123/farewell.png'
GENERATOR = Path('scripts/generate_reload_w215_farewell.py')
MANIFEST = ART / 'manifest.json'
RIG = Path('art/weapons/w205/rigs/sidearm_4cbe9231.json')
SOURCE_ACTION = '80A8ADE2'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_SHA256 = 'bd92efd7fe5f77e6571a5c526039cde59d0f619e7d5e3f9ffa4af53da3be37b1'
TEXTURE_SHA256 = '7cabfcb0ef9a88311fb7508f736d29812cfcc9dd363ed8c86e3c7783d8f77645'
SOURCE_BLEND_SHA256 = '164514cfdbb9d7a6f3c5ba7276204ccd2a3d5f64d0ceaf216a467d2b6556d796'
# Exact W184 authored values. These are not recovered mesh/camera trajectories.

GRIP=(8.,9.305,8.175)

MAGAZINE_ANCHOR=(8.,7.05,8.83)

KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (12, -4, -6), (0.1, -0.08, 0.03), (0, 0, 0)), (0.2, (31, -6, -24), (0.28, 0.2, 0.1), (0, 0, 0)), (0.3, (37, -5, -27), (0.32, 0.27, 0.15), (-0.1, -1.7, 0.424)), (0.4, (38, -7, -25), (0.34, 0.26, 0.12), (-0.6, -4.6, 1.147)), (0.5, (36, -8, -24), (0.34, 0.21, 0.1), (-0.8, -5.4, 1.346)), (0.6, (35, -8, -23), (0.32, 0.15, 0.08), (-0.3, -3.4, 0.848)), (0.72, (29, -6, -20), (0.28, 0.04, 0.05), (0, 0, 0)), (0.8, (11, 3, -43), (0.18, -0.12, 0.04), (0, 0, 0)), (0.86, (5, 9, -55), (0.1, -0.18, 0.02), (0, 0, 0)), (0.93, (13, 5, -22), (0.06, -0.05, 0.01), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()

def sha(b):return hashlib.sha256(b).hexdigest()

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
            vector.append(h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)

def is_payload(e):
    # Actual canonical heel and open heel loop; NOT grip_shoulder77 or grip_core78.
    return e['name']=='heel' or e['name'].startswith('open_heel_loop_')

def reload_shaft(source):
    """Three reload-only solids: shaft and two narrow broad-face seam strips.
    Visible rectangular magazine backed by n1472; exact hidden proportions authored.
    Shaft extends .070443 below grip78 local Y to overlap original heel81.
    Existing heel face UV only; canonical endpoints bypass reload geometry.
    """
    faces=copy.deepcopy(source['elements'][81]['faces'])
    rot=copy.deepcopy(source['elements'][78]['rotation'])
    def box(name,lo,hi):
        return dict(name='magazine_shaft_'+name,**{'from':lo,'to':hi},rotation=copy.deepcopy(rot),faces=copy.deepcopy(faces))
    return [box('core',[7.58,7.23,7.57],[8.42,10.95,8.85]),
            box('left_seam',[7.56,7.36,7.72],[7.585,10.87,7.78]),
            box('right_seam',[8.415,7.36,7.72],[8.44,10.87,7.78])]

def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements']
                              if is_payload(e)==(part=='magazine')]+(reload_shaft(source) if part=='magazine' else [])}
            for part in PARTS}

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Original baseplate and reference-backed reload-only shaft move as one rigid payload.
    local=add(sub(pivot,vec(motion,pivot)),vec(motion,offset) if part=='magazine' else [0,0,0])
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if twohand[context]['scale']!=scale or len(set(scale))!=1:raise ValueError('Expected equal uniform canonical grip scales')
        rotation=mul(base,motion)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read inputs once; return absolute output paths and bytes without writing."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE, GENERATOR, ART / 'profile.json', RIG,
              Path('scripts/generate_reload_w184_farewell.py'),
              Path('art/weapons/w184/farewell/SOURCE.md'),
              Path('art/weapons/w184/farewell/manifest.json'),
              Path('art/weapons/w123/farewell/design.json'),
              Path('art/weapons/w123/farewell/manifest.json'),
              Path('art/weapons/w201/contacts.json'),
              Path('art/weapons/w205/first-person-framing.json'),
              Path('src/main/resources/destiny/weapons/w46-timing.json'),
              Path('src/main/resources/destiny/sounds/w63-reload.json')]
    raw = {path: (root / path).read_bytes() for path in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[ART / 'profile.json'])
    rig = json.loads(raw[RIG])
    if sha(raw[SOURCE]) != SOURCE_SHA256 or sha(raw[TEXTURE]) != TEXTURE_SHA256:
        raise ValueError('Accepted Farewell geometry/UV/atlas changed; re-audit')
    elements = source['elements']
    moving_indices = [i for i, element in enumerate(elements) if is_payload(element)]
    moving_names = ['heel'] + ['open_heel_loop_' + str(i) for i in range(8)]
    if (len(elements) != 115 or moving_indices != list(range(81, 90))
            or [elements[i]['name'] for i in moving_indices] != moving_names
            or elements[77]['name'] != 'grip_shoulder'
            or elements[78]['name'] != 'grip_core'):
        raise ValueError('W184 Farewell fixed grip/heel partition changed')
    framing = profile['framing']
    reload = profile['contacts']['reload']
    if (profile['schemaVersion'] != 1 or profile['weapon'] != 'farewell'
            or profile.get('sourceAction') != SOURCE_ACTION
            or framing.get('sourceFullChain') is not True
            or framing.get('keepMeshSupport') is not True
            or framing.get('hideSupportAtRest') is not False
            or reload.get('rigAction') != SOURCE_ACTION
            or reload.get('partHint') != 'magazine' or reload.get('policy') != 'magazine'):
        raise ValueError('W215 Farewell full-chain/contact profile changed')
    start, attached, release, end = reload['gripWindow']
    if not 0 <= start < attached <= release < end <= .72:
        raise ValueError('Farewell attachment must release by authored magazine seat')
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig['group'] != 'sidearm_4cbe9231' or rig.get('cameraExported') is not False
            or rig.get('sourceBlendSha256') != SOURCE_BLEND_SHA256
            or not rig.get('w215Source61') or len(action['frames']) != SAMPLES
            or action['action'] != 'Armature|fp_80A8ADE2_reload_full|Base'
            or (action['start'], action['end']) != (1., 67.)
            or any(frame['progress'] != i / INTERVALS or not joints <= frame['joints'].keys()
                   for i, frame in enumerate(action['frames']))):
        raise ValueError('Master fresh W215 original61 shoulder rig is required')
    parts = partition(source)
    counts = {part: len(model['elements']) for part, model in parts.items()}
    if counts != {'body': 106, 'magazine': 12}:
        raise ValueError('Expected 106 fixed + 9 heel/loop + 3 reload-only shaft elements')
    # Worst-case classic skin:112 surfaces per limb segment, two sides/two segments.
    assembled_estimate = sum(counts.values()) + 448
    if assembled_estimate > 1000:
        raise ValueError('Farewell candidate exceeds assembled element cap')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside owned W215 Farewell namespace')
        output[root / path] = encode(value)

    for part, model in parts.items():
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

        model = copy.deepcopy(item['model']) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': model})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}
    # Keep the actual canonical ADS/inspect cases and change only its hip fallback.
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select'
            or guard.get('property') != 'minecraft:custom_model_data' or guard.get('index', 0) != 0):
        raise ValueError('Farewell canonical mode guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': guard}],
                        'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W215', 'weapon': 'farewell',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'float32(i/60), matching runtime float quantization',
        'curve': 'C1 shape-preserving Hermite; weighted harmonic knot tangents, zero at endpoints/holds/extrema',
        'keyframes': KEYS, 'gripPivot': GRIP, 'magazineAnchor': MAGAZINE_ANCHOR,
        'magazineExtractionAxis': [0, -.970289, .241949],
        'authoredTimingSource': 'scripts/generate_reload_w184_farewell.py',
        'normalizedPhases': {'raiseCant': [0, .2], 'heelRelease': [.2, .3],
                             'downLeftWithdraw': [.3, .5], 'incomingInsert': [.5, .72],
                             'wristRoll': [.72, .86], 'recover': [.86, 1]},
        'magazineSeatedProgress': .72, 'gripWindow': reload['gripWindow'],
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': 115, 'partElements': counts, 'weaponElements': 118,
        'endpointAssembledWeaponElements': 115, 'addedElements': 3, 'triangleAdapterElements': 0,
        'bothClassicForearmElements': 224, 'bothClassicUpperArmElements': 224,
        'maxAssembledElements': assembled_estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'assembledBudgetBasis': 'Candidate566=106body+12magazine+448classic arm surfaces; master must measure every composed route including canonical endpoints/ADS/inspect.',
        'partitionIndices': {part: [i for i, element in enumerate(elements)
                                   if is_payload(element) == (part == 'magazine')] for part in PARTS},
        'movingNames': moving_names,
        'partitionRationale': 'Fixed grip77/78, receiver, cables, blade, panels and backstrap retained. Heel81/loop82..89 plus three unchanged W184 reload-only shaft solids move rigidly; no independent bolt stroke.',
        'reloadOnlyGeometry': {'elements': reload_shaft(source), 'count': 3,
                               'sourceFrameIndex': 1472, 'sourceTimestampSeconds': 1472*1001/60000,
                               'uvPolicy': 'Exact canonical heel81 face UV; no atlas changes.',
                               'exactOriginalShaftFidelityVerified': False},
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements'])) for part, model in parts.items()},
        'canonicalGeometryAndUVPreserved': True, 'reloadGeometryMatchesW184': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Canonical graphs at0/1 and beyond1, negative/inactive progress, non-FP and ADS/inspect; both grip flags preserved.',
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': rig['group'], 'sourceFullChain': True, 'sourceCameraRecovered': False,
        'partHint': reload['partHint'], 'policy': reload['policy'],
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'Exact12 W184 knots and shaft/display algebra; only scalar interpolation becomes W214 weighted-harmonic PCHIP. Master binds fresh61 original weapon/shoulder/elbow/wrist FK.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'assets': len(output), 'packFiles': len(output), 'generatedFiles': len(allowed),
        'staticParts': 2, 'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': [
            'Original blend contains armature only: no recovered weapon/hand mesh, camera, fingers or IK.',
            '61 poses/60 intervals do not establish continuous60fps client interpolation.',
            'Authored magazine path/hidden shaft dimensions and attachment release need native contact review.',
            'Ordinary source limb lengths/FK must remain; no stretch, length smoothing, hidden arms or camera compensation.',
            'Master FIRST feedback, worker image-backed review/correction and master SECOND remain pending.'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W215 Farewell output mapping')
    return output
