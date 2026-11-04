#!/usr/bin/env python3
"""W218 Code Duello: unchanged W187 whole-canister assembly, 61-pose C1 bank.

Pure stdlib, inert import and generate(root=ROOT) -> absolute Path:bytes only.
Master owns original Blender evaluation, source installation, shared full-chain
arms, routing, asset materialization and FIRST/SECOND native review.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w218/code_duello')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w218_code_duello.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w187_code_duello.py')
AUTHORED_MANIFEST = Path('art/weapons/w187/code_duello/manifest.json')
SOURCE_DOC = Path('art/weapons/w187/code_duello/SOURCE.md')
SOURCE = A / 'models/weapon_surface_w123/code_duello.json'
NATIVE = A / 'models/weapon/rocket_launcher/code_duello.json'
TWOHAND = A / 'models/weapon/rocket_launcher/code_duello_twohand.json'
ITEM = A / 'items/weapon/code_duello.json'
TEXTURE = A / 'textures/item/weapon/w123/code_duello.png'
DESIGN = Path('art/weapons/w123/code_duello/design.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w218/rigs/rocket_launcher_ba250bec.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w218/source/source-review.json')
KEY = 'weapon_reload_w218_code_duello/code_duello'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8A1F5'
ACTION_NAME = 'Armature|fp_80A8A1F5_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
# Release by first neutral seat .68; original .74 overtravel/.80 settle remain
# authored body-relative motion, never a wrist-driven recovery displacement.
GRIP_WINDOW = (.08, .18, .60, .68)

# Same-weapon W187 literals inspected inertly through AST, never imported.
GRIP = [8.0, 7.4, 16.0]
MAGAZINE_ANCHOR = [8.0, 12.0, 10.9]
ORIGINAL_KEYS = [[0, [0, 0, 0], [0, 0, 0], [0, 0, 0]], [0.08, [12, -2, -5], [0.15, -0.35, 0.1], [0, 0, 0]], [0.18, [78, -8, -12], [0.9, -0.4, 0.6], [0, 0, 0]], [0.27, [82, -10, -12], [1.0, -0.6, 0.7], [0, 0, -0.45]], [0.36, [80, -10, -12], [1.1, -0.65, 0.7], [0.15, 0, -18.0]], [0.44, [78, -9, -11], [1.05, -0.6, 0.65], [3.4, 1.0, -25.0]], [0.53, [78, -9, -11], [1.05, -0.6, 0.65], [3.0, 1.0, -25.0]], [0.6, [80, -9, -11], [1.0, -0.6, 0.65], [0.1, 0, -5.0]], [0.68, [82, -9, -11], [0.95, -0.55, 0.6], [0, 0, 0]], [0.74, [82, -8, -10], [0.95, -0.5, 0.6], [0, 0, 0.08]], [0.8, [77, -7, -9], [0.8, -0.45, 0.5], [0, 0, 0]], [0.9, [38, -4, -7], [0.4, -0.3, 0.25], [0, 0, 0]], [0.97, [6, -1, -1], [0.04, -0.06, 0.03], [0, 0, 0]], [1, [0, 0, 0], [0, 0, 0], [0, 0, 0]]]
FRAMING_DELTA = [-2.0, -3.5, -6.5]
FRAMING_WEIGHTS = [0.0, 0.18, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.45, 0.05, 0.0]
KEYS = [[0, [0, 0, 0], [0.0, 0.0, 0.0], [0, 0, 0]], [0.08, [12, -2, -5], [-0.21, -0.98, -1.0699999999999998], [0, 0, 0]], [0.18, [78, -8, -12], [-1.1, -3.9, -5.9], [0, 0, 0]], [0.27, [82, -10, -12], [-1.0, -4.1, -5.8], [0, 0, -0.45]], [0.36, [80, -10, -12], [-0.8999999999999999, -4.15, -5.8], [0.15, 0, -18.0]], [0.44, [78, -9, -11], [-0.95, -4.1, -5.85], [3.4, 1.0, -25.0]], [0.53, [78, -9, -11], [-0.95, -4.1, -5.85], [3.0, 1.0, -25.0]], [0.6, [80, -9, -11], [-1.0, -4.1, -5.85], [0.1, 0, -5.0]], [0.68, [82, -9, -11], [-1.05, -4.05, -5.9], [0, 0, 0]], [0.74, [82, -8, -10], [-1.05, -4.0, -5.9], [0, 0, 0.08]], [0.8, [77, -7, -9], [-1.2, -3.95, -6.0], [0, 0, 0]], [0.9, [38, -4, -7], [-0.5, -1.875, -2.6750000000000003], [0, 0, 0]], [0.97, [6, -1, -1], [-0.060000000000000005, -0.23500000000000001, -0.29500000000000004], [0, 0, 0]], [1, [0, 0, 0], [0.0, 0.0, 0.0], [0, 0, 0]]]
CANISTER_INDICES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 71, 72, 73, 74, 75, 76, 77, 78)
EXPECTED_FRAMING = {'translation': [0, 0, 0], 'rotation': [0, 0, 0], 'scale': 1, 'rightWristRoll': 15, 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {'right': {'position': [8.0, 8.45, 8.15], 'rotation': [-17.0, 0.0, 0.0]}, 'left': {'position': [8.0, 9.15, 2.0], 'rotation': [0.0, 0.0, 0.0]}}
EXPECTED_RELOAD_CONTACT = {'contact': [7.0, 12.0, 7.5], 'rotation': [90.0, 0.0, 0.0]}
RIG_SHA256 = '78d7101c57cc3a3a3d88e0dc957cbdb4982160e21ec7e11a9630e3bee5958e3d'
REVIEW_SHA256 = 'f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0'
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/code_duello.json': '3976bf8a35213f5cf6978b1f325f9e2ab75b83cd9adf307d8abb00be2ce11781', 'src/main/resources/assets/destiny/items/weapon/code_duello.json': '57f2ed10aa31f67012981dee0786c71e53aadea317b198c5951ad75e76474c12', 'src/main/resources/assets/destiny/textures/item/weapon/w123/code_duello.png': '97fee43c3c6247f4b19c48e52835ef7b840bb5f26333684fafa9fd946cf5572a', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello.json': 'cb749df662d293747c44124ceb010554b4664a49d3d36bd9be9e3d16ddcae5ba', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_ads.json': '1612334d558b341fe9a49b565b9e1714e5d93232ef033039c5fcfad948ca7a02', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_ads_twohand.json': 'c28a0afe1c8108e8f465215a27bd9a4940e3e3e0b75b9efc3e1e4e41416041b7', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_inspect.json': '5dad0f5f508a938851d39fd110809b861481630bd1c48ab2dcf49eead3cffdff', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_inspect_twohand.json': '986615dd7b0605721621fc77a54a64c42b0e3fe3ed995f20f65140f541b0c641', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_twohand.json': '28086257edd779e6a264be610e06851120f4723ba3b86bd2183fcedbecad355b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'scripts/generate_reload_w187_code_duello.py': '567251c91eafb8c4d048468f72aa57cc0e68a56748552039ac31066f4c2c725b', 'art/weapons/w187/code_duello/manifest.json': '809c90caba5b0e2c248bcc412063fc0aa2286d3c1b27e57d03809060c3a13d11', 'art/weapons/w187/code_duello/SOURCE.md': 'd7964e10615c28af7968defee42fafd7aae3ce42375108fb3f357de5b892cd17', 'art/weapons/w123/code_duello/design.json': '2e00bfa4df177f6d3fb4e2dbf0ccb3d3bc24d2d00296474fa0efc4326479b3d5'}

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()

def sha(b):return hashlib.sha256(b).hexdigest()

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
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # All 56 canister solids and two connector prisms share one rigid transform.
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

def reload_shaft(source):
    # n802/826 show the brass connector at the detached long canister's rear.
    # Two intersecting prisms form one connected short octagonal connector.
    # Dimensions are authored; seated connector lies inside Rear_solid_heart.
    core=copy.deepcopy(source['elements'][71]);core.pop('rotation',None)
    core.update(name='reload_connector_core',**{'from':[7.68,11.68,11.10],'to':[8.32,12.32,12.40]})
    diagonal=copy.deepcopy(core);diagonal['name']='reload_connector_diagonal'
    diagonal['rotation']={'origin':[8.,12.,11.75],'axis':'z','angle':45}
    return [core,diagonal]

def partition(source):
    return {part: {
        **{k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'},
        'elements': [copy.deepcopy(e) for i, e in enumerate(source['elements'])
                     if (i in CANISTER_INDICES) == (part == 'magazine')]
                    + (reload_shaft(source) if part == 'magazine' else [])}
            for part in PARTS}


def payload_visible(progress):
    """W187 has no hide/zero-scale phase; offscreen exchange is rigid motion."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError(progress)
    return True


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read-only generation; no import, render or execution of legacy generators."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE,
        GENERATOR, PROFILE, RIG, SOURCE_REVIEW, AUTHORED_SOURCE, AUTHORED_MANIFEST,
        SOURCE_DOC, DESIGN, SURFACE_MAP, CONTACTS, FRAMING,
        Path('scripts/first_person_framing_w205.py'), *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Current canonical/authored Code Duello input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Fresh W218 original source61/report required; never replace W205 rig')
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile, rig, report = (json.loads(raw[p]) for p in (PROFILE, RIG, SOURCE_REVIEW))
    old = json.loads(raw[AUTHORED_MANIFEST])
    elements = source['elements']
    if (len(elements) != 217 or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP)
            or old['magazineAnchor'] != list(MAGAZINE_ANCHOR)
            or old['partitionIndices']['magazine'] != list(CANISTER_INDICES)
            or old['sourceLimitation']['canonicalMovingNames'] !=
               [elements[i]['name'] for i in CANISTER_INDICES]
            or old['reloadOnlyGeometry']['elements'] != reload_shaft(source)
            or old['framingCorrection']['originalKeys'] != json.loads(encode(ORIGINAL_KEYS))
            or old['framingCorrection']['weights'] != list(FRAMING_WEIGHTS)
            or old['framingCorrection']['commonDisplayDelta'] != list(FRAMING_DELTA)):
        raise ValueError('W187 whole-canister geometry/UV/anchors/keys/framing drift')
    rule = next(r for r in json.loads(raw[SURFACE_MAP])['targets']
                if r['path'] == 'assets/destiny/models/weapon/rocket_launcher/code_duello.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/code_duello.json'
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Selected Code Duello surface mapping changed')
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'code_duello'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or profile.get('contacts') != {'reload': {
                'rigAction': SOURCE_ACTION, 'partHint': 'magazine',
                'policy': 'magazine', 'hand': 'right', 'gripWindow': list(GRIP_WINDOW)}}):
        raise ValueError('Code Duello full-chain/framing/seat-release profile changed')
    config = json.loads(raw[FRAMING])
    effective = {**config['families'].get('rocket_launcher', config['default']),
                 **config.get('weapons', {}).get('code_duello', {})}
    for flag in ('sourceFullChain', 'keepMeshSupport', 'hideSupportAtRest'):
        effective[flag] = EXPECTED_FRAMING[flag]
    if effective != EXPECTED_FRAMING:
        raise ValueError('Current effective canonical framing changed')
    contacts = json.loads(raw[CONTACTS])['weapons']['code_duello']
    if (any(contacts[k] != v for k, v in EXPECTED_CONTACTS.items())
            or any(contacts['reload'][k] != v for k, v in EXPECTED_RELOAD_CONTACT.items())):
        raise ValueError('Code Duello mesh rest/reload contact changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups']['rocket_launcher_ba250bec']
    marker = rig.get('w218Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'rocket_launcher_ba250bec'
            or rig.get('fallback') is not False or 'code_duello' not in rig['weapons']
            or rig.get('cameraExported') is not False
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('exporterSha256') != report['exporterSha256']
            or marker.get('blenderVersion') != report['blenderVersion']
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 133.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i / INTERVALS
                   or abs(f['frame'] - (1 + 132*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys()
                   for i, f in enumerate(action['frames']))
            or evidence['actions'][SOURCE_ACTION]['action'] != ACTION_NAME
            or evidence['actions'][SOURCE_ACTION]['slot'] != 'OBSlot'
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1., 133.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['actions'][SOURCE_ACTION]['maxExistingCacheJointAbsError'] != 0
            or evidence['objects'] != [{'name': 'Armature', 'type': 'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Expected original W218 Blender full chain/action1..133')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if (rig.get(key) != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('group') != rig['group']
            or profile['sourceRig'].get('action') != SOURCE_ACTION):
        raise ValueError('Code Duello sourceRig mismatch')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(sum(counts.values()), len(elements), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body': 161, 'magazine': 58} or estimate > 1000:
        raise ValueError('Code Duello partition/weapon+arm reserve budget changed')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W218 Code Duello namespace')
        output[root / path] = encode(value)

    for part, model in geometries.items():
        emit(A / f'models/{KEY}_{part}.json', model)
    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f'models/{KEY}_{frame:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand, progress, part, grip)})

        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in PARTS if part == 'body' or payload_visible(progress)]}

        model = copy.deepcopy(item['model']) if frame in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': model})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select'
            or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index', 0) != 0
            or [case['when'] for case in guard['cases']] != ['ads', 'inspect']):
        raise ValueError('Canonical Code Duello ADS/inspect guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W218', 'weapon': 'code_duello',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; shared knot derivative; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'originalKeys': ORIGINAL_KEYS,
        'gripPivot': GRIP, 'magazineAnchor': MAGAZINE_ANCHOR,
        'magazineExtractionAxis': old['magazineExtractionAxis'],
        'magazineSeatedProgress': .68, 'magazineOvertravelProgress': .74,
        'magazineCompressionSettledProgress': .80, 'gripWindow': list(GRIP_WINDOW),
        'framingCorrection': {**old['framingCorrection'],
            'policy': 'Preserve W187 r2 corrected knots/delta/weights; interpolate final corrected keys with shared C1 PCHIP derivatives.'},
        'authoredTimingSource': str(AUTHORED_SOURCE),
        'normalizedPhases': old['normalizedPhases'], 'reference': old['reference'],
        'referencePolicy': 'Read W187 SOURCE.md/manifest and viewed retained actual-gameplay storyboard and offline comparison; original video not reopened. Same-weapon mechanism remains authored.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': 161,
        'movingElements': 58, 'magazineElements': 58, 'weaponElements': 219,
        'canonicalWeaponElements': canonical_count, 'selectedSurfaceElements': len(elements),
        'addedElements': 2, 'newElementsRelativeToW187': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': 219 + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'candidateSelectedSurfaceWithArmsEstimate': len(elements) + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': 'Reload219+448=667; selected W123 canonical217+448=665; raw canonical151+448=599. Alternatives not summed. Master measures every composed route, including ADS/inspect.',
        'movingIndices': list(CANISTER_INDICES),
        'movingNames': [elements[i]['name'] for i in CANISTER_INDICES],
        'partitionIndices': old['partitionIndices'], 'geometryPolicy': old['geometryPolicy'],
        'semanticGroups': old['semanticGroups'],
        'payloadPolicy': 'Same56-solid whole ribbed canister +2 connectors, one rigid outgoing/incoming assembly. W187 has no hide/zero-scale phase; always visible at normalized time, exchange goes offscreen by motion.',
        'reloadOnlyGeometry': old['reloadOnlyGeometry'], 'sourceLimitation': old['sourceLimitation'],
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements']))
                                    for part, model in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'reloadGeometryMatchesW187': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Complete canonical graph at0/1, overshoot, negative inactive and nonFP; original ADS/inspect cases precede reload; native/twohand flag preserved.',
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION,
        'rigActionName': action['action'], 'sourceGroup': rig['group'],
        'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigPath': str(RIG), 'sourceReviewPath': str(SOURCE_REVIEW),
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceBlend': rig['sourceBlend'],
        'originalSourceSha256': evidence['inputSha256'],
        'sourceCameraRecovered': False, 'fingerIKRecovered': False,
        'partHint': 'magazine', 'policy': 'magazine', 'reloadHand': 'right',
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'Exact14 W187 corrected knots, anchors, whole-canister geometry/UV and rigid native/twohand display math retained. Interpolation alone changes to C1 weighted harmonic PCHIP. Source full-chain ordinary arms are attached by master without axis/length compensation.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'timingPolicy': 'Preserve67tick reload,1rocket,15RPM,cadence80ticks,burst1,shellReloadfalse, ammo and audio.61 poses/60 intervals; no continuous60fps claim.',
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': 2,
        'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': [
            'Master evaluated original Blender5.4; worker read fresh report/matrices and viewed actual bone-only sheet, not an independent Blender evaluation.',
            'Shared-family ARMATURE only; no recovered Code Duello weapon mesh/camera/finger IK; rest/reload contacts remain authored.',
            'Occluded exchange/connector dimensions/open socket/hand clearance not recovered; canonical Rear_solid_heart remains filled.',
            'W187 r2 framing preserved; it was an authored native-defect response and still needs this batch native review.',
            'RIGHT handling hand attachment fades.60..68 and is zero from first neutral seat.68. Authored.74 overtravel/.80 relaxation remain body-relative, followed by wrist recovery.',
            '61 poses/60 intervals do not prove vanilla continuous60fps interpolation.',
            'FIRST actual PNG feedback reviewed: empty right hand in raw09 proved wrong shared LEFT attachment. Explicit reloadHand=right correction returned; master shared selected-hand fix and SECOND canister/contact acceptance remain pending.'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W218 Code Duello output mapping')
    return output
