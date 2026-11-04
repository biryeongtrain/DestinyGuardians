#!/usr/bin/env python3
"""W218 Bellowing Giant: exact W187 solids/UV/knots, 61-pose C1 reload bank.

Pure stdlib. Import is inert; generate(root=ROOT) reads only and returns absolute
Path -> bytes. Master owns installation, ordinary full-chain skin arms, shared
binding/routing/materialization and FIRST -> same-worker feedback -> SECOND.
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
ART = Path('art/weapons/w218/bellowing_giant')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w218_bellowing_giant.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w187_bellowing_giant.py')
AUTHORED_MANIFEST = Path('art/weapons/w187/bellowing_giant/manifest.json')
SOURCE_DOC = Path('art/weapons/w187/bellowing_giant/SOURCE.md')
SOURCE = A / 'models/weapon_surface_w123/bellowing_giant.json'
NATIVE = A / 'models/weapon/rocket_launcher/bellowing_giant.json'
TWOHAND = A / 'models/weapon/rocket_launcher/bellowing_giant_twohand.json'
ITEM = A / 'items/weapon/bellowing_giant.json'
TEXTURE = A / 'textures/item/weapon/w123/bellowing_giant.png'
DESIGN = Path('art/weapons/w123/bellowing_giant/design.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w218/rigs/rocket_launcher_ba250bec.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w218/source/source-review.json')
KEY = 'weapon_reload_w218_bellowing_giant/bellowing_giant'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_GROUP = 'rocket_launcher_ba250bec'
SOURCE_ACTION = '80A8A1F5'
ACTION_NAME = 'Armature|fp_80A8A1F5_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
# Approach before first visible rocket; fully attach at appearance, release at seat.
RELOAD_HAND = 'right'
# Original handling wrist is already carrying at first visible payload pose .35.
GRIP_WINDOW = (.30, .35, .60, .65)
EXPECTED_FRAMING = {'translation': [0, 0, 0], 'rotation': [0, 0, 0],
    'scale': 1, 'rightWristRoll': 15, 'sourceFullChain': True,
    'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {
    'right': {'position': [8.0, 8.35, 7.83], 'rotation': [-25.0, 0.0, 0.0]},
    'left': {'position': [8.0, 8.95, 2.17], 'rotation': [0.0, 0.0, 0.0]}}
EXPECTED_RELOAD_CONTACT = {'contact': [7.0, 12.05, 0.4], 'rotation': [90.0, 0.0, 0.0]}
RIG_SHA256 = '78d7101c57cc3a3a3d88e0dc957cbdb4982160e21ec7e11a9630e3bee5958e3d'
REVIEW_SHA256 = 'f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0'

# Literal constants read inertly via AST; no legacy module execution/import.
GRIP = (8.0, 8.65, 7.8)
MAGAZINE_ANCHOR = (8.0, 12.05, 0.4)
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (14, 2, -6), (0.1, -0.12, 0.06), (0, 0, 0)), (0.2, (64, -6, -16), (0.32, -0.45, 0.22), (0, 0, 0)), (0.3, (104, -12, -22), (0.55, -0.68, 0.4), (4, -1.5, -10.5)), (0.35, (108, -12, -22), (0.57, -0.7, 0.42), (3, -0.8, -10.3)), (0.43, (110, -10, -20), (0.55, -0.65, 0.4), (1.4, -0.2, -9.4)), (0.5, (109, -9, -19), (0.54, -0.6, 0.4), (0, 0, -8.9)), (0.55, (107, -8, -18), (0.52, -0.57, 0.38), (0, 0, -5.7)), (0.6, (104, -7, -16), (0.48, -0.51, 0.35), (0, 0, -2.8)), (0.65, (100, -6, -15), (0.43, -0.44, 0.3), (0, 0, 0)), (0.72, (90, -3, -13), (0.36, -0.35, 0.23), (0, 0, 0)), (0.82, (42, 4, -6), (0.16, -0.2, 0.1), (0, 0, 0)), (0.9, (-3, 2, 2), (0.03, -0.06, 0.02), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/bellowing_giant.json': 'c5bc85213c3daec0d188f396429a2f4c314888fb5d28d63e24233ac358de4e13', 'src/main/resources/assets/destiny/textures/item/weapon/w123/bellowing_giant.png': 'dba7cd9234e29158b6d7ce6d68dad6950b7802ee9f1aa94a9944083114d6e457', 'src/main/resources/assets/destiny/items/weapon/bellowing_giant.json': '6549576c026f913148d0e2bd6753d91f931fc4632597e08916d1be8c604b5eb5', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_twohand.json': '1c4a1cc6ffc83ed87698d5dc5a87c75a9c2852e4e7384451fdf78d14a7944fa3', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_ads_twohand.json': '86852d66c497dc5b8364f8b1c28fbcb2b87a4fe1f24f0c33eab05f9bd549222f', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant.json': 'e7a12634a512901893865bc41d5e23218741d03c2b0e3b8455a567358fb37a8b', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_ads.json': 'd00d5396cde90b8dab6d56e072af30a33c1cfc6cc539d2ff9e8f6b569052a43e', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_inspect.json': '8abbd6154b4486ac191ba8388910b37a7fd3ddf5ae9b71959c0125cddcebb99c', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_inspect_twohand.json': '0e6575324c7483f1c139f9288284a8abfb111816a29cd8d12904d777300b9236', 'scripts/generate_reload_w187_bellowing_giant.py': '1d87d69cb940a195d8b9309ed6c67ac7a539b5e78be2a735a21360381a3f8aed', 'art/weapons/w187/bellowing_giant/manifest.json': '58b8f6e7ae53f721bb3264a06dc8801bf91e86a7888d9fc44966ae79d65a4897', 'art/weapons/w187/bellowing_giant/SOURCE.md': '78e22e8c4ae4b9bcbb77bb26252501f4eaa0996e2b68a278f48de87b26157b3a', 'art/weapons/w123/bellowing_giant/design.json': '5061eff64ba3f899a7e90edfeb5956881a22227012481156cc1e1b58642c133f'}

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

def reload_rocket(source):
    # Observed front-loaded incoming dark cylinder and tail silhouette n3020..3060.
    # Exact hidden payload dimensions/UV are authored; source arm bones are separate.
    # One connected solid assembly fits entirely within original chamber when seated.
    template=source['elements'][64]  # graphite material; NOT movable stock geometry
    elements=[]
    def cube(name,lo,hi,rotation=None):
        el=copy.deepcopy(template);el.update(name=name,**{'from':lo,'to':hi});el.pop('rotation',None)
        if rotation:el['rotation']=rotation
        elements.append(el)
    cube('Reload_rocket_core',[7.65,11.70,-1.8],[8.35,12.40,2.25])
    for i in range(8):
        angle=i*45
        # Eight continuous jacket faces overlap the core, producing one long octagonal payload.
        cube(f'Reload_rocket_jacket_{i}',[7.80,12.35,-1.8],[8.20,12.51,2.25],
             {'origin':[8,12.05,.4],'z':angle})
    cube('Reload_rocket_nose',[7.72,11.77,2.15],[8.28,12.33,2.85])
    cube('Reload_rocket_nose_tip',[7.84,11.89,2.8],[8.16,12.21,3.2])
    cube('Reload_rocket_tail_neck',[7.73,11.78,-2.4],[8.27,12.32,-1.65])
    # Four shallow connected stabilizers; silhouettes source-backed, occluded profile authored.
    cube('Reload_rocket_fin_left',[7.46,11.99,-2.3],[7.8,12.11,-1.6])
    cube('Reload_rocket_fin_right',[8.2,11.99,-2.3],[8.54,12.11,-1.6])
    cube('Reload_rocket_fin_top',[7.94,12.25,-2.3],[8.06,12.59,-1.6])
    cube('Reload_rocket_fin_bottom',[7.94,11.51,-2.3],[8.06,11.85,-1.6])
    return elements

def partition(source):
    models={part:copy.deepcopy(source) for part in PARTS}
    models['magazine']['elements']=reload_rocket(source)
    return models

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Original body/floor and reference-backed reload-only upper neck move as one rigid payload.
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

def payload_visible(progress):
    """W187 range-dispatch hold: old poses7..13 occupy [.35,.70)."""
    return .35 <= progress < .70


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read only; master materializes exactly this mapping of immutable bytes."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, GENERATOR,
        PROFILE, RIG, SOURCE_REVIEW, AUTHORED_SOURCE, AUTHORED_MANIFEST, SOURCE_DOC,
        DESIGN, SURFACE_MAP, CONTACTS, FRAMING,
        Path('scripts/first_person_framing_w205.py'), *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Canonical/authored Bellowing Giant input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Fresh original W218 source61/report required; master installs shared inputs')
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile, rig, report = (json.loads(raw[p]) for p in (PROFILE, RIG, SOURCE_REVIEW))
    old = json.loads(raw[AUTHORED_MANIFEST])
    # Inspect literal assignments only. Never execute/import the old generator.
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {'KEYS', 'GRIP', 'MAGAZINE_ANCHOR'}:
                    authored[target.id] = ast.literal_eval(node.value)
    elements = source['elements']
    if (authored != {'KEYS': KEYS, 'GRIP': GRIP, 'MAGAZINE_ANCHOR': MAGAZINE_ANCHOR}
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP)
            or old['magazineAnchor'] != list(MAGAZINE_ANCHOR)
            or old['reloadOnlyGeometry']['elements'] != reload_rocket(source)
            or old['partitionIndices'] != {'body': list(range(114)), 'magazine': []}
            or len(elements) != 114
            or elements[8]['name'] != 'Launch_chamber_heart'
            or elements[64]['name'] != 'Stock_filled_heart'):
        raise ValueError('W187 same-weapon geometry/UV/keys/anchors/whole-rocket drift')
    rule = next(r for r in json.loads(raw[SURFACE_MAP])['targets']
                if r['path'] == 'assets/destiny/models/weapon/rocket_launcher/bellowing_giant.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/bellowing_giant.json'
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Selected Bellowing Giant surface mapping drift')
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'bellowing_giant'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or profile.get('contacts') != {'reload': {
                'rigAction': SOURCE_ACTION, 'partHint': 'magazine',
                'policy': 'magazine', 'hand': RELOAD_HAND,
                'gripWindow': list(GRIP_WINDOW)}}):
        raise ValueError('W218 full-chain/effective framing/seat release profile drift')
    config = json.loads(raw[FRAMING])
    # Shared loader merges family-or-default, then weapon/profile overrides.
    effective = {**config['families'].get('rocket_launcher', config['default']),
                 **config.get('weapons', {}).get('bellowing_giant', {})}
    for field in ('translation', 'rotation', 'scale', 'rightWristRoll', 'leftRotation'):
        if effective.get(field) != EXPECTED_FRAMING.get(field):
            raise ValueError('Existing effective launcher framing changed: ' + field)
    contacts = json.loads(raw[CONTACTS])['weapons']['bellowing_giant']
    if (any(contacts[k] != v for k, v in EXPECTED_CONTACTS.items())
            or any(contacts['reload'][k] != v for k, v in EXPECTED_RELOAD_CONTACT.items())):
        raise ValueError('Authored mesh rest/reload contacts changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups'][SOURCE_GROUP]
    marker = rig.get('w218Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or 'bellowing_giant' not in rig['weapons'] or rig.get('cameraExported') is not False
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
            or 'reload_full' not in evidence['actions'][SOURCE_ACTION]['sourceNames']
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1., 133.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['actions'][SOURCE_ACTION]['maxExistingCacheJointAbsError'] != 0
            or evidence['objects'] != [{'name': 'Armature', 'type': 'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Expected original W218 Blender action1..133 and full shoulder chains')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if (rig.get(key) != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('group') != rig['group']
            or profile['sourceRig'].get('action') != SOURCE_ACTION
            or profile['sourceRig'].get('path') != str(RIG)):
        raise ValueError('Invalid W218 shared-family sourceRig profile')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body': 114, 'magazine': 16} or estimate > 1000:
        raise ValueError('Unexpected Bellowing Giant partition or weapon+arm budget')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W218 Bellowing Giant namespace')
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
        raise ValueError('Canonical ADS/inspect guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W218', 'weapon': 'bellowing_giant',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'magazineAnchor': MAGAZINE_ANCHOR,
        'magazineInsertionAxis': [0, 0, 1], 'magazineSeatedProgress': .65,
        'gripWindow': list(GRIP_WINDOW), 'reloadHand': RELOAD_HAND,
        'authoredTimingSource': str(AUTHORED_SOURCE),
        'normalizedPhases': old['normalizedPhases'], 'reference': old['reference'],
        'referencePolicy': 'Read W187 source inertly via AST, manifest and SOURCE.md; viewed retained actual gameplay storyboard and comparison. Same-weapon front-loaded rocket motion; no old generator or render imports.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': 114,
        'movingElements': 16, 'magazineElements': 16, 'weaponElements': sum(counts.values()),
        'canonicalWeaponElements': canonical_count, 'addedElements': 16,
        'newElementsRelativeToW187': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': sum(counts.values()) + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': 'Reload130+448=578; raw canonical217+448=665. Alternatives are not summed. Master measures all composed routes, including ADS/inspect.',
        'partitionIndices': old['partitionIndices'], 'semanticGroups': old['semanticGroups'],
        'geometryPolicy': old['geometryPolicy'],
        'payloadPolicy': 'One identical rigid16-element whole rocket; never a breech/stock band. Visible on normalized [.35,.70), dense poses21..41; old21-pose dispatch held pose13 through .70. No scale fade or false extraction.',
        'reloadOnlyGeometry': {**old['reloadOnlyGeometry'],
            'visibleSampleIndices': [i for i in range(SAMPLES) if payload_visible(i / INTERVALS)]},
        'sourceLimitation': old['sourceLimitation'],
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements']))
                                    for part, model in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'reloadGeometryMatchesW187': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Canonical graph at0/1, overshoot, negative inactive and nonFP; original ADS/inspect cases precede reload; both native/twohand flags preserved.',
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': rig['group'], 'sourceRigPath': str(RIG),
        'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceCameraRecovered': False, 'partHint': 'magazine', 'policy': 'magazine',
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'Exact14 W187 knots, anchors, solids/UV, normalized visibility holds, native/twohand rigid display math. Only interpolation changes to C1 weighted harmonic PCHIP. Shared-family original chain supplies ordinary fingerless skin arms, without attenuation/new camera fit.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'timingPolicy': 'Unchanged capacity1, reload64ticks, cadence60ticks, burst1/sharedBurstAmmo=false, existing ammo/audio.61 normalized poses/60 intervals; footage clock does not set gameplay.',
        'rotationConvention': old['rotationConvention'],
        'originalBlendProvenance': {'sourceBlend': rig['sourceBlend'],
            'sourceBlendSha256': rig['sourceBlendSha256'],
            'sourceMapSha256': rig['sourceMapSha256'], 'boneMapSha256': rig['boneMapSha256'],
            'blenderVersion': report['blenderVersion'], 'slot': 'OBSlot',
            'fps': evidence['fps'], 'objects': evidence['objects'],
            'priorCacheMaxJointAbsError': 0, 'allInputsUnchanged': True},
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': 2,
        'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': [
            'Master evaluated original Blender5.4; worker read fresh matrices/report and viewed bone-only chain sheet, not independent Blender evaluation.',
            'Shared-family ARMATURE only, includes Bellowing Giant; no exclusive weapon mesh/camera/finger IK or recovered concealed rocket dimensions/UV. Authored mesh contacts and body/rocket path retained.',
            '61 poses/60 intervals do not prove native continuous60fps interpolation.',
            'RIGHT attachment reaches full weight by first visible pose .35 (approach .30..35), fades .60..65 and is zero from authored seat .65. Original payload hold extends to .70, then rocket stays body-relative during wrist recovery.',
            'Existing loader/default launcher framing and mesh rest contacts retained. No arm length/axis compensation or new geometry/camera fit.',
            'Worker viewed FIRST native sheets and10 raw frames; corrected original RIGHT handling hand selection. Master shared hand routing and SECOND must show an actual held rocket through handling/reseat before visual acceptance.'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W218 Bellowing Giant output mapping')
    return output
