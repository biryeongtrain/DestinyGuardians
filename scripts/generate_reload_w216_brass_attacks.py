#!/usr/bin/env python3
"""W216 Brass Attacks: unchanged W176 parts/path, 61-pose C1 PCHIP bank.

Pure stdlib. Import is inert; generate(root=ROOT) reads inputs and returns
absolute Path -> bytes only. Master binds fresh original full-chain arms,
materializes assets, checks every route and owns FIRST/SECOND native review.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w216/brass_attacks')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w216_brass_attacks.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w176_brass_attacks.py')
AUTHORED_MANIFEST = Path('art/weapons/w176/brass_attacks/manifest.json')
REFERENCE = Path('art/weapons/w176/brass_attacks/motion-reference.json')
SOURCE = A / 'models/weapon_surface_w123/brass_attacks.json'
NATIVE = A / 'models/weapon/sidearm/brass_attacks.json'
TWOHAND = A / 'models/weapon/sidearm/brass_attacks_twohand.json'
ITEM = A / 'items/weapon/brass_attacks.json'
TEXTURE = A / 'textures/item/weapon/w123/brass_attacks.png'
DESIGN = Path('art/weapons/w123/brass_attacks/design.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w205/rigs/sidearm_80771a27.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w216/source/source-review.json')
KEY = 'weapon_reload_w216_brass_attacks/brass_attacks'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8ADE2'
ACTION_NAME = 'Armature|fp_80A8ADE2_reload_full|Base'
ARM_ELEMENT_RESERVE = 4 * 112
GRIP_WINDOW = (.05, .12, .36, .43)

# AST-read W176 constants; no import/runpy of the heavy original generator.
MOVING = (103,)
NAMES = ('magazine_base',)
FIXED_HOUSING = (45, 56, 63, 64, 95, 96, 97, 98, 99, 100, 101, 102)
FIXED_NAMES = ('rear_breech_core', 'rear_cap', 'receiver_core', 'rear_shoulder', 'grip_core', 'grip_wrist', 'grip_panel_-1', 'grip_panel_1', 'frontstrap', 'backstrap', 'upper_backstrap', 'heel')
GRIP = (8.0, 10.02, 8.4)
MAG_ANCHOR = (8.0, 6.62, 9.34)
SOURCE_SHA256 = '49d02c139b239ecff7814bbb579ec0958a80d7bba75e3575f15b760a7e5dec09'
CORE_NAME = 'authored_internal_magazine_core'
NECK_NAME = 'authored_internal_magazine_neck'
MAG_AXIS = (0.0, -0.9452341037968682, 0.3263931509994218)
KEYS = ((0.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.06, (27, -8, -12), (0.18, 0.08, 0.02), (0, 0, 0)), (0.12, (46, -14, -25), (0.35, 0.18, 0.08), (0.0, -0.4726170518984341, 0.1631965754997109)), (0.2, (40, -12, -23), (0.2, 0.1, 0.12), (0.0, -7.089255778476511, 2.447948632495663)), (0.28, (36, -10, -22), (0.12, 0.06, 0.1), (0.0, -7.089255778476511, 2.447948632495663)), (0.36, (33, -9, -20), (0.08, 0.02, 0.06), (-0.35, -2.25, 0.78)), (0.43, (27, -8, -16), (0.03, -0.04, 0.02), (0, 0, 0)), (0.5, (12, -7, -10), (0, -0.08, 0), (0, 0, 0)), (0.58, (16, -12, -16), (-0.08, -0.02, 0.05), (0, 0, 0)), (0.69, (25, -3, 4), (-0.1, -0.12, 0.1), (0, 0, 0)), (0.78, (-6, 4, 3), (-0.08, -0.38, 0.05), (0, 0, 0)), (0.9, (-4, 2, 1), (-0.02, -0.14, 0.01), (0, 0, 0)), (1.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
EXPECTED_FRAMING = {'translation': [-1.0, 0.25, 0], 'rotation': [-1, 0, 0], 'scale': 0.98, 'rightWristRoll': 27, 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {'right': {'position': [8.0, 10.1, 8.37], 'rotation': [-19.0, 0.0, 0.0]}, 'left': {'position': [7.05, 9.65, 8.72], 'rotation': [-19.0, 0.0, -20.0]}}
EXPECTED_RELOAD_CONTACT = {'contact': [7.1, 6.62, 9.34], 'rotation': [-19.0, 0.0, 0.0]}
RIG_SHA256 = '2fefe3ce5619d594e53a44ec573e1217c4e1b9e3ba2db6e40b31dfa39999a273'
REVIEW_SHA256 = '3b5ec3c27772222c14730457fd1d9ff431c39802ae4df10bb7f286440aaf61d6'
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/brass_attacks.json': '49d02c139b239ecff7814bbb579ec0958a80d7bba75e3575f15b760a7e5dec09', 'src/main/resources/assets/destiny/items/weapon/brass_attacks.json': '678051c7ff93f5171893a1234d7bd8b8c9d0a469fab7ccb65de0350f291f137b', 'src/main/resources/assets/destiny/textures/item/weapon/w123/brass_attacks.png': 'b5c08322401ae7b6c6511b3cfd58c087e93497ed75d93ec8752aedd87139682d', 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks.json': '225ab67eb09f06d81f4c962736f3a726974f8a9653e24d5907c96043efab145a', 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks_ads.json': '1fab7ff1b9cb34478b7a219a526bc1f4b198a3d2394b852056b2bc868659c5c5', 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks_ads_twohand.json': 'edebba15fdeaeec81c26e02439c0ca4e468a889c4eb141eaca4d58deb00a40e1', 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks_inspect.json': '52bf35b987f50281cc63a9d857d969e7e464b8161c1d7e7eee64282455abf8d2', 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks_inspect_twohand.json': 'f0584e67d551a438374dcda2f00e2f31607901628e051da1cde89863aba6c148', 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks_twohand.json': 'a9617a1be4aa3d30907c25af909d32e375c9974eb7c3d6215ed5ea95d1825494', 'scripts/generate_reload_w176_brass_attacks.py': '139cdca64b8d1d69a370e50de24031209871983609f0afd850dcaa4afd91fa21', 'art/weapons/w176/brass_attacks/manifest.json': 'c61a680aaacba8f6ffb9600e14dff3929fd5483488dd1aa38ad474d6e9017164', 'art/weapons/w123/brass_attacks/design.json': 'cd1cf376272f2de6a6a417cfe46547d54ae8136edc1f0052f34fb2e25b601d56'}

def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

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

def internal_core(source):
    """One reload-only solid, strictly within opaque W143 grip_core at rest.

    Frame812/60 shows a box magazine, not its hidden dimensions or texels.
    Extents and UV allocation are authored; all canonical elements stay intact.
    The unmodified baseplate and core share one parent and rigid child display.
    """
    core=copy.deepcopy(source['elements'][95])
    core.update(name=CORE_NAME, **{'from':[7.42,7.15,7.32], 'to':[8.58,12.75,9.35]})
    return core

def internal_neck(source):
    """One small dark bridge from base103 to the core, in base103's frame.

    Hidden attachment is authored, not measured from gameplay. At rest it is
    recessed into the grip/heel housing; it shares the rigid magazine parent.
    """
    neck=copy.deepcopy(source['elements'][103])
    neck.update(name=NECK_NAME, **{'from':[7.5,6.70,8.55], 'to':[8.5,7.45,10.25]})
    neck['faces']=copy.deepcopy(source['elements'][95]['faces'])
    return neck

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    anchor=sub(MAG_ANCHOR,(8,8,8))
    # Place the unchanged magazine anchor at its body-carried position plus
    # source-local withdrawal, then subtract its rotated child-space anchor.
    # This is translation only; no recentering or extra magazine spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
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


def partition(source):
    """Keep grip/heel fixed; move only base103 plus unchanged W176 core/neck."""
    parts = {}
    for part in PARTS:
        model = {k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'}
        model['elements'] = [copy.deepcopy(e) for i, e in enumerate(source['elements'])
                             if (i in MOVING) == (part == 'magazine')]
        if part == 'magazine':
            model['elements'].extend((internal_core(source), internal_neck(source)))
        parts[part] = model
    return parts


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read-only inputs under root; no directory creation, writes or imports."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, GENERATOR,
        PROFILE, RIG, SOURCE_REVIEW, AUTHORED_SOURCE, AUTHORED_MANIFEST, REFERENCE,
        DESIGN, SURFACE_MAP, CONTACTS, FRAMING,
        Path('scripts/first_person_framing_w205.py'),
        Path('src/main/resources/destiny/weapons/w46-timing.json'),
        Path('src/main/resources/destiny/sounds/w63-reload.json'),
        *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Reviewed geometry/UV/canonical/authored input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Master fresh normalized W216 source61/report required')
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    report = json.loads(raw[SOURCE_REVIEW])
    old = json.loads(raw[AUTHORED_MANIFEST])
    elements = source['elements']
    if (len(elements) != 111 or tuple(elements[i]['name'] for i in MOVING) != NAMES
            or tuple(elements[i]['name'] for i in FIXED_HOUSING) != FIXED_NAMES
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP) or old['magazineAnchor'] != list(MAG_ANCHOR)
            or old['authoredCore'] != internal_core(source)
            or old['authoredNeck'] != internal_neck(source)
            or old['sourceElementsAndUVSha256'] != sha(encode(elements))):
        raise ValueError('W176 authored knots or W143 fixed-grip/magazine partition drift')
    design = json.loads(raw[DESIGN])
    if (design['revision'] != 'W143' or
            [p['geometry']['name'] for p in design['parts'] if p['group'] == 'magazine'] != list(NAMES)):
        raise ValueError('Brass Attacks semantic magazine provenance drift')
    rule = next(r for r in json.loads(raw[SURFACE_MAP])['targets']
                if r['path'] == 'assets/destiny/models/weapon/sidearm/brass_attacks.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/brass_attacks.json'
            or rule['replacementSha256'] != SOURCE_SHA256):
        raise ValueError('Selected Brass Attacks surface mapping drift')
    reload = profile.get('contacts', {}).get('reload', {})
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'brass_attacks'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or set(profile.get('contacts', {})) != {'reload'}
            or reload != {'rigAction': SOURCE_ACTION, 'partHint': 'magazine',
                          'policy': 'magazine', 'gripWindow': list(GRIP_WINDOW)}):
        raise ValueError('W216 Brass effective framing/full-chain/contact profile drift')
    contacts = json.loads(raw[CONTACTS])['weapons']['brass_attacks']
    if (any(contacts[k] != v for k, v in EXPECTED_CONTACTS.items())
            or any(contacts['reload'][k] != v for k, v in EXPECTED_RELOAD_CONTACT.items())):
        raise ValueError('Brass Attacks authored rest mesh contacts changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups']['sidearm_80771a27']
    marker = rig.get('w216Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'sidearm_80771a27' or rig.get('fallback') is not False
            or 'brass_attacks' not in rig['weapons'] or rig.get('cameraExported') is not False
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('exporterSha256') != report['exporterSha256']
            or marker.get('blenderVersion') != report['blenderVersion']
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 67.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i / INTERVALS
                   or abs(f['frame'] - (1 + 66*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys()
                   for i, f in enumerate(action['frames']))
            or evidence['actions'][SOURCE_ACTION]['action'] != ACTION_NAME
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1., 67.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['objects'] != [{'name': 'Armature', 'type': 'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Expected actual W216 Blender action1..67 and ordinary full shoulder chains')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        report_key = key.removesuffix('Sha256')
        if (rig.get(key) != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][report_key]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('group') != rig['group']
            or profile['sourceRig'].get('action') != SOURCE_ACTION):
        raise ValueError('Invalid Brass sourceRig profile')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body': 110, 'magazine': 3} or estimate > 1000:
        raise ValueError('Unexpected Brass partition or candidate weapon+arm budget')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W216 Brass namespace')
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
                for part in PARTS]}

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
        raise ValueError('Canonical Brass ADS/inspect guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W216', 'weapon': 'brass_attacks',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'magazineAnchor': MAG_ANCHOR,
        'magazineExtractionAxis': MAG_AXIS, 'magazineSeatedProgress': .43,
        'gripWindow': list(GRIP_WINDOW), 'authoredTimingSource': str(AUTHORED_SOURCE),
        'normalizedPhases': old['normalizedPhases'],
        'reference': json.loads(raw[REFERENCE])['url'],
        'sourceObservedSeconds': old['sourceObservedSeconds'],
        'referencePolicy': 'W176 retained Ultraclocked evidence; worker read motion-reference/manifest, did not reopen video. W176 SOURCE.md absent.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': 110,
        'movingElements': 3, 'magazineElements': 3, 'weaponElements': sum(counts.values()),
        'canonicalWeaponElements': canonical_count, 'addedElements': 2,
        'newElementsRelativeToW176': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': sum(counts.values()) + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': '113 reload weapon+448 estimated classic arm surfaces=561; canonical244+448=692. Master measures every materialized route including ADS/inspect.',
        'movingIndices': list(MOVING), 'movingNames': list(NAMES),
        'fixedHousingIndices': list(FIXED_HOUSING), 'fixedHousingNames': list(FIXED_NAMES),
        'partitionIndices': {part: [i for i in range(len(elements))
                                   if (i in MOVING) == (part == 'magazine')] for part in PARTS},
        'partitionRationale': old['partitionRationale'],
        'authoredCore': internal_core(source), 'authoredNeck': internal_neck(source),
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements']))
                                    for part, model in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'reloadGeometryMatchesW176': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Canonical item graph at0/1, overshoot, negative inactive and non-FP; original ADS/inspect cases precede reload; native/twohand flags preserved.',
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': rig['group'], 'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceCameraRecovered': False, 'partHint': 'magazine', 'policy': 'magazine',
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'Exact13 W176 knots, holds, part split, UVs, hidden core/neck and transform algebra. Only interpolation changes to W215 PCHIP. Master attaches original ordinary-length sourceFullChain FK without attenuation or new camera offsets.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'timingPolicy': 'Retain catalog24 rounds,37tick reload,325rpm two-round burst, ammo lifecycle/perk speed/audio; source30fps1..67 does not retime gameplay.',
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': 2,
        'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': [
            'Master freshly evaluated original Blender; worker read current report/full61 matrices and viewed bone-only sheet, not independent Blender inspection.',
            'ARMATURE only; no recovered weapon mesh, camera, finger IK or hidden magazine dimensions. Mesh contacts/part path remain authored.',
            '61 poses/60 intervals do not prove native continuous60fps interpolation.',
            'Attachment fades.36..43 and is zero throughout.43..1, preventing later wrist motion dragging the seated magazine. FIRST contact review pending.',
            'No independent slide motion, arm length/axis compensation, damping, rest-contact change or camera fit added.',
            'All-route measured budget, master FIRST PNG feedback, worker correction/justified nochange and master SECOND remain pending.'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W216 Brass output mapping')
    return output
