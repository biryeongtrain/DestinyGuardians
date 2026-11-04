#!/usr/bin/env python3
"""W217 Erentil FR4: unchanged W189 grip-cell geometry/path,61-pose C1 bank.

Pure stdlib: import is inert and generate(root=ROOT) returns absolute Path->bytes.
No files/directories are written. Master owns fresh source installation, full-chain
skin arms, shared binding/materialization/runtime and FIRST/SECOND native review.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w217/erentil_fr4')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w217_erentil_fr4.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w189_erentil_fr4.py')
AUTHORED_MANIFEST = Path('art/weapons/w189/erentil_fr4/manifest.json')
SOURCE_DOC = Path('art/weapons/w189/erentil_fr4/SOURCE.md')
SOURCE = A / 'models/weapon_surface_w123/erentil_fr4.json'
NATIVE = A / 'models/weapon/fusion_rifle/erentil_fr4.json'
TWOHAND = A / 'models/weapon/fusion_rifle/erentil_fr4_twohand.json'
ITEM = A / 'items/weapon/erentil_fr4.json'
TEXTURE = A / 'textures/item/weapon/w123/erentil_fr4.png'
DESIGN = Path('art/weapons/w123/erentil_fr4/design.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w205/rigs/fusion_rifle_04669cdb.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w217/source/source-review.json')
KEY = 'weapon_reload_w217_erentil_fr4/erentil_fr4'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8ADD3'
ACTION_NAME = 'Armature|fp_80A8ADD3_reload_full|Base'
ARM_ELEMENT_RESERVE = 4 * 112
GRIP_WINDOW = (.12, .20, .69, .74)

# Literal same-weapon W189 constants, read inertly; no old generator import.
GRIP = (8.0, 8.15, 2.88)
MAGAZINE_ANCHOR = (8.0, 4.37, 3.115)
BATTERY_INDICES = (16,)
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.12, (48, -7, -9), (-0.8, 1.7, -0.45), (0, 0, 0)), (0.2, (69, -13, -15), (-1.5, 3.0, -0.9), (0, -0.38, -0.116)), (0.28, (73, -15, -17), (-1.7, 3.4, -1.1), (0, -2.1, -0.64)), (0.36, (72, -14, -17), (-1.8, 3.6, -1.2), (-1.2, -3.9, 1.6)), (0.44, (70, -13, -16), (-1.9, 3.7, -1.2), (-2.6, -4.6, 3.5)), (0.54, (63, -11, -15), (-1.8, 3.7, -1.1), (-2.8, -4.0, 2.7)), (0.62, (65, -12, -15), (-1.65, 3.5, -1.05), (-0.65, -2.65, -0.81)), (0.69, (70, -13, -16), (-1.6, 3.3, -1.0), (0, -0.55, -0.168)), (0.74, (72, -13, -15), (-1.6, 3.2, -0.95), (0, 0.09, 0.027)), (0.8, (68, -11, -13), (-1.4, 2.9, -0.8), (0, 0, 0)), (0.88, (46, -6, -8), (-0.9, 1.9, -0.5), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
MAG_AXIS = (0, -.95646, -.29189)
EXPECTED_FRAMING = {'translation': [-0.65, 0.6, 0], 'rotation': [-1, 2, 0], 'scale': 0.98, 'rightWristRoll': 28, 'leftRotation': [15, 35, -35], 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {'right': {'position': [8.0, 8.1, 2.86], 'rotation': [17.0, 0.0, 0.0]}, 'left': {'position': [7.8, 10.05, -4.6], 'rotation': [0.0, 90.0, -85.0]}}
EXPECTED_RELOAD_CONTACT = {'contact': [7.35, 4.35, 3.12], 'rotation': [-14.0, 0.0, 0.0]}
RIG_SHA256 = '747749cea16ee1bec34df57fbb7fb8b6c7bb32e6dd1dfef6188991a0d2e4d76a'
REVIEW_SHA256 = 'd8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a'
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/erentil_fr4.json': '13f46cf7d380bfa2d9b1e7adcd365e5a6e6dca8818f857d0148860fa7041ccfa', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_twohand.json': 'b0b7689f38f608cc51b49e60977c4bfdef7e40c9ebaabc640264babc02dade78', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4.json': '10649eb8b62d80ad7837f7bfa3595e7be1dc338db60bcd333a7c289a130642e2', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_inspect_twohand.json': '2f56ff08e92a303e681a33d038343f1cd89a5e11ed692fb8c19b03150dbbde11', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_ads.json': '5020950f7dfca5df6baa82493cb10c7cceeba017993515b1753c24764ade370a', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_ads_twohand.json': '58eed4e067722d3c3b27e320161e359601e8769b08d89d56076b621a1cbdc369', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_inspect.json': 'b2784931617bc42abf9578e291cab7dc2cbc41b3feb8c74916d62902ffca93c0', 'src/main/resources/assets/destiny/textures/item/weapon/w123/erentil_fr4.png': '03f0cc1d18ecf3eb92e83938404951ccca40a149e934b15c55d7ba6d0919536c', 'src/main/resources/assets/destiny/items/weapon/erentil_fr4.json': '106baf4e03246a040ee619b2bd053daee4008b5765b6994fb4adc72485cf1a74', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'scripts/generate_reload_w189_erentil_fr4.py': '75b13b62293b5eea9fff00b03531b7d02b0849b86e74933533156fd8a59f72da', 'art/weapons/w189/erentil_fr4/manifest.json': '3fabd36f4aedb59582cee455be5be2cb8c5aa39ae4e594640c5ffd2ef3b6976e', 'art/weapons/w189/erentil_fr4/SOURCE.md': '411df29f0486a3e999e042e8384494a5e9493c32ccddce551cd2b9844a6690f0', 'art/weapons/w123/erentil_fr4/design.json': '97be12b4fa09ec000aa186032eff9c43881f3bd73ef6e72a8972eea7cdb79323'}

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
    # Both grips transport identical rigid weapon-space battery offsets.
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

def cell_core(source):
    # Independently authored inserted sleeve. Canonical heel remains exact.
    # Extends from the heel into the grip; dimensions are not recovered source animation.
    e=copy.deepcopy(source['elements'][16])
    e.update(name='Reload_cell_inner_sleeve',**{'from':[7.62,4.45,2.02],'to':[8.38,7.55,2.66]})
    e['rotation']={'origin':[8.,6.,2.34],'x':16.970743,'y':0,'z':0}
    return [e]

def partition(source):
    models={part:copy.deepcopy(source) for part in PARTS}
    models['body']['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if i not in BATTERY_INDICES]
    models['magazine']['elements']=[copy.deepcopy(source['elements'][16])]+cell_core(source)
    return models

def payload_visible(frame):
    """Preserve old dispatch omission at [.40,.55), not a new shrink/fade."""
    return frame < 24 or frame >= 33


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read inputs only. Master materializes the returned immutable byte blobs."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, GENERATOR,
        PROFILE, RIG, SOURCE_REVIEW, AUTHORED_SOURCE, AUTHORED_MANIFEST, SOURCE_DOC,
        DESIGN, SURFACE_MAP, CONTACTS, FRAMING,
        Path('scripts/first_person_framing_w205.py'), *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Canonical/authored Erentil input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Fresh original W217 source61/report required; master installs shared inputs')
    source, twohand, item = json.loads(raw[SOURCE]), json.loads(raw[TWOHAND])['display'], json.loads(raw[ITEM])
    profile, rig, report = json.loads(raw[PROFILE]), json.loads(raw[RIG]), json.loads(raw[SOURCE_REVIEW])
    old = json.loads(raw[AUTHORED_MANIFEST])
    elements = source['elements']
    if (len(elements) != 135 or elements[16]['name'] != 'Cartridge_base'
            or [elements[i]['name'] for i in (0, 9, 10, 11, 12, 13, 14, 15)] !=
               ['Omolon_receiver', 'Grip_root', 'Grip_main', 'Grip_front_bevel',
                'Rear_thumbhole_web', 'Triangle_lower_brace', 'Grip_heel', 'Trigger']
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP)
            or old['magazineAnchor'] != list(MAGAZINE_ANCHOR)
            or old['reloadOnlyGeometry']['elements'] != cell_core(source)
            or old['partitionIndices']['magazine'] != list(BATTERY_INDICES)):
        raise ValueError('W189 same-weapon geometry/UV/keys/anchors/sleeve drift')
    design = json.loads(raw[DESIGN])
    if (design['revision'] != 'semantic-r1'
            or [p['geometry']['name'] for p in design['parts'] if p['group'] == 'cartridge'] != ['Cartridge_base']):
        raise ValueError('Erentil semantic cell provenance drift')
    rule = next(r for r in json.loads(raw[SURFACE_MAP])['targets']
                if r['path'] == 'assets/destiny/models/weapon/fusion_rifle/erentil_fr4.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/erentil_fr4.json'
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Selected Erentil surface mapping drift')
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'erentil_fr4'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or profile.get('contacts') != {'reload': {
                'rigAction': SOURCE_ACTION, 'partHint': 'magazine',
                'policy': 'magazine', 'gripWindow': list(GRIP_WINDOW)}}):
        raise ValueError('W217 Erentil full-chain/effective framing/seat contact profile drift')
    contacts = json.loads(raw[CONTACTS])['weapons']['erentil_fr4']
    if (any(contacts[k] != v for k, v in EXPECTED_CONTACTS.items())
            or any(contacts['reload'][k] != v for k, v in EXPECTED_RELOAD_CONTACT.items())):
        raise ValueError('Erentil authored mesh rest/reload contacts changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups']['fusion_rifle_04669cdb']
    marker = rig.get('w217Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'fusion_rifle_04669cdb' or rig.get('fallback') is not False
            or 'erentil_fr4' not in rig['weapons'] or rig.get('cameraExported') is not False
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('exporterSha256') != report['exporterSha256']
            or marker.get('blenderVersion') != report['blenderVersion']
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 100.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i / INTERVALS
                   or abs(f['frame'] - (1 + 99*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys()
                   for i, f in enumerate(action['frames']))
            or evidence['actions'][SOURCE_ACTION]['action'] != ACTION_NAME
            or evidence['actions'][SOURCE_ACTION]['slot'] != 'OBSlot'
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1., 100.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['actions'][SOURCE_ACTION]['maxExistingCacheJointAbsError'] != 0
            or evidence['objects'] != [{'name': 'Armature', 'type': 'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Expected original W217 Blender action1..100 and full shoulder chains')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if (rig.get(key) != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('group') != rig['group']
            or profile['sourceRig'].get('action') != SOURCE_ACTION):
        raise ValueError('Invalid Erentil sourceRig profile')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body': 134, 'magazine': 2} or estimate > 1000:
        raise ValueError('Unexpected Erentil partition or candidate weapon+arm budget')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W217 Erentil namespace')
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
                for part in PARTS if part == 'body' or payload_visible(frame)]}

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
        raise ValueError('Canonical Erentil ADS/inspect guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W217', 'weapon': 'erentil_fr4',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'magazineAnchor': MAGAZINE_ANCHOR,
        'magazineExtractionAxis': MAG_AXIS, 'magazineSeatedProgress': .74,
        'magazineCompressionSettledProgress': .80, 'gripWindow': list(GRIP_WINDOW),
        'authoredTimingSource': str(AUTHORED_SOURCE), 'normalizedPhases': old['normalizedPhases'],
        'reference': old['reference'],
        'referencePolicy': 'Read W189 SOURCE.md/manifest and viewed actual retained storyboard/comparison; original video was not reopened. Same-weapon Erentil lower-grip exchange, not recovered mesh animation.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': 134,
        'movingElements': 2, 'magazineElements': 2, 'weaponElements': sum(counts.values()),
        'canonicalWeaponElements': canonical_count, 'addedElements': 1,
        'newElementsRelativeToW189': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': sum(counts.values()) + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': 'Reload136+448 arm reserve=584; raw canonical222+448=670. Master measures every composed route, including ADS/inspect.',
        'movingIndices': list(BATTERY_INDICES), 'movingNames': ['Cartridge_base'],
        'partitionIndices': old['partitionIndices'], 'geometryPolicy': old['geometryPolicy'],
        'payloadPolicy': 'Same canonical heel+one unchanged rigid sleeve. Omit poses24..32 at [.40,.55), exactly preserving W189 dispatch visibility; no shrinking or new part spin.',
        'reloadOnlyGeometry': {'elements': cell_core(source), 'count': 1,
            'visibleSampleIndices': [i for i in range(SAMPLES) if payload_visible(i)],
            'uvPolicy': old['reloadOnlyGeometry']['uvPolicy']},
        'sourceLimitation': old['sourceLimitation'], 'originalRip': old['originalRip'],
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements']))
                                    for part, model in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'reloadGeometryMatchesW189': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Canonical graph at0/1, overshoot, negative inactive and non-FP; original ADS/inspect cases precede reload; native/twohand flags preserved.',
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': rig['group'], 'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceCameraRecovered': False, 'partHint': 'magazine', 'policy': 'magazine',
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'Exact13 W189 keys, anchors, UV/part partition, visibility hold and rigid transform algebra. Only interpolation changes to W215/216 C1 PCHIP. Master attaches ordinary original shoulder/elbow/wrist chains without attenuation or new framing offsets.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'timingPolicy': old['timingPolicy'],
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': 2,
        'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': [
            'Master evaluated original Blender5.4; worker read fresh matrices/report and viewed actual bone-only sheet, not independent Blender evaluation.',
            'ARMATURE only; no recovered weapon mesh/camera/finger IK or concealed cell dimensions. Mesh contacts and body/cell path remain authored.',
            '61 poses/60 intervals do not prove native continuous60fps interpolation.',
            'Attachment fades.69..74 and stays zero from.74. Original compression relaxation.74..80 remains authored, then payload is exactly body-fixed.',
            'No rest-contact, arm length/axis compensation, receiver/grip/guard movement or new camera fit.',
            'All-route measured budget, master FIRST actual PNG feedback, worker correction/justified nochange and master SECOND pending.'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W217 Erentil output mapping')
    return output
