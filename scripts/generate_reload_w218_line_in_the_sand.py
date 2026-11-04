#!/usr/bin/env python3
"""W218 Line in the Sand: unchanged W188 battery geometry/path, 61-pose C1 bank.

Pure stdlib. Import is inert; generate(root=ROOT) reads only and returns absolute
Path->bytes. Master owns materialization, shared routing/arms and native review.
Legacy generator is parsed as inert AST only; no render dependencies are loaded.
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
ART = Path('art/weapons/w218/line_in_the_sand')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w218_line_in_the_sand.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w188_line_in_the_sand.py')
AUTHORED_MANIFEST = Path('art/weapons/w188/line_in_the_sand/manifest.json')
SOURCE_DOC = Path('art/weapons/w188/line_in_the_sand/SOURCE.md')
SOURCE = A / 'models/weapon_surface_w123/line_in_the_sand.json'
NATIVE = A / 'models/weapon/linear_fusion_rifle/line_in_the_sand.json'
TWOHAND = A / 'models/weapon/linear_fusion_rifle/line_in_the_sand_twohand.json'
ITEM = A / 'items/weapon/line_in_the_sand.json'
TEXTURE = A / 'textures/item/weapon/w123/line_in_the_sand.png'
DESIGN = Path('art/weapons/w123/line_in_the_sand/design.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w218/rigs/fusion_rifle_04669cdb.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w218/source/source-review.json')
KEY = 'weapon_reload_w218_line_in_the_sand/line_in_the_sand'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8ADD3'
ACTION_NAME = 'Armature|fp_80A8ADD3_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.10, .20, .80, .84)
BATTERY_INDICES = tuple(range(56, 64))
GRIP = (8.0, 8.2, 8.2)
MAGAZINE_ANCHOR = (8.0, 5.6, 6.83)
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (50, -5, -10), (-1.1, -1.0, -2.1), (0, 0, 0)), (0.2, (70, -9, -15), (-1.8, -2.7, -3.8), (0, -0.35, 0)), (0.3, (74, -10, -16), (-1.9, -3.1, -4.3), (0, -2.0, 0)), (0.38, (73, -9, -16), (-1.9, -3.1, -4.3), (-0.45, -4.6, 0.1)), (0.48, (73, -9, -15), (-1.9, -3.1, -4.3), (-1.0, -6.4, 0.2)), (0.6, (70, -8, -15), (-1.8, -3.0, -4.1), (-2.1, -4.8, 0.3)), (0.68, (66, -7, -14), (-1.6, -2.8, -3.8), (-0.5, -2.6, 0)), (0.76, (65, -7, -13), (-1.5, -2.6, -3.7), (0, -0.25, 0)), (0.8, (63, -6, -12), (-1.5, -2.5, -3.5), (0, 0.1, 0)), (0.84, (58, -5, -10), (-1.3, -2.2, -3.2), (0, 0, 0)), (0.92, (24, -2, -4), (-0.5, -0.8, -1.2), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
EXPECTED_FRAMING = {'translation': [-0.65, 0.6, 0], 'rotation': [-1, 2, 0], 'scale': 0.98, 'rightWristRoll': 28, 'leftRotation': [15, 35, -35], 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {'right': {'position': [8.0, 8.28, 8.0], 'rotation': [-29.0, 0.0, 0.0]}, 'left': {'position': [8.0, 7.25, -0.79], 'rotation': [-14.0, 0.0, 0.0]}}
EXPECTED_RELOAD_CONTACT = {'contact': [7.2, 5.6, 6.8], 'rotation': [0.0, 0.0, 0.0]}
RIG_SHA256 = 'f2ecda5b6b4595443f313fda97f2536856bd85d7cbb47fa3544f0e5ab5d35929'
REVIEW_SHA256 = 'f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0'
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/line_in_the_sand.json': 'b5a5319fdacf4f759fb5b682c8d4c6ffbb83cc7e5c992fee6f5a70345f385eff', 'src/main/resources/assets/destiny/textures/item/weapon/w123/line_in_the_sand.png': '3d23d635215fbb69c8ddd4ce1b27f58a36869013932bcc85f40d958bcece81f3', 'src/main/resources/assets/destiny/items/weapon/line_in_the_sand.json': '554a5be4af5bd63e0c31e2b7784ce33225c62ff59cf7ba550cc172653731550f', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand.json': 'b77783d88d521fa77e58269f38c86a073fd7953c00b55425cb133750c3bcf09b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_twohand.json': '7697a6a142002b2b8a33e4bf419393a708f513be8daa7f6bbaf981bbfbf09a62', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_inspect_twohand.json': 'c6d824bb4218e3a92b489801bb50ccefbfd2f01992c53fa78be9590a5cab52ac', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_ads.json': '6a461b6a4bfe86234504b23b392234cebefa840a9663c079fdd442744312de9d', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_inspect.json': '8da76eca201833d6cb31b0f67191a1628b89502d052ba782a02f251b1301223f', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_ads_twohand.json': 'cbfec2400ef8f7385608f9f57daf59f42952468f9d047d65c7f2d53cceb5cad9', 'scripts/generate_reload_w188_line_in_the_sand.py': 'cffc0564667f38372a635d654213008d263978d82897f40594938774063fa2de', 'art/weapons/w188/line_in_the_sand/manifest.json': 'bc782eb56dd73cd1febacef67ead66f171830c72a4e9ff4e5464bfd30519bebf', 'art/weapons/w188/line_in_the_sand/SOURCE.md': '2343eae06d11efa03e0aa434090e31e8edea866dd40d01093adbd180c30e8d98', 'art/weapons/w188/line_in_the_sand/storyboard.png': '862b59c9c176fdcc752d59f8fe0ea1c3e019c0cba807cb8ed25fcda3c4ad9142', 'art/weapons/w188/line_in_the_sand/comparison.png': 'c8bdad369c7b17e8f64ecfb913ad5e60bf44c76109826b71e9e4cc1cb43f4033', 'art/weapons/w123/line_in_the_sand/design.json': 'f138bc6243aaa4eb0e37fdbdca2b9feed07363012b233d825a57c381a0ea9a43'}


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

def contacts(source):
    # Source Battery maxY6.194; contact profile/hidden seating are authored.
    result=[]
    for side,x in enumerate((7.65,8.14)):
        e=copy.deepcopy(source['elements'][57]);e.update(name=f'Reload_battery_contact_{side}',**{'from':[x,5.88,4.18],'to':[x+.21,6.17,4.50]});e.pop('rotation',None);result.append(e)
    return result

def partition(source):
    models={part:copy.deepcopy(source) for part in PARTS}
    models['body']['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if i not in BATTERY_INDICES]
    models['magazine']['elements']=[copy.deepcopy(source['elements'][i]) for i in BATTERY_INDICES]+contacts(source)
    return models

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


def payload_visible(progress):
    """W188 dispatch hid old poses8..11: preserve normalized [.40,.60)."""
    return progress < .40 or progress >= .60


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}



def generate(root=ROOT) -> dict[Path, bytes]:
    """Return the dense bank without materializing files or importing old code."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE,
        GENERATOR, PROFILE, RIG, SOURCE_REVIEW, AUTHORED_SOURCE, AUTHORED_MANIFEST,
        SOURCE_DOC, DESIGN, CONTACTS, FRAMING,
        Path('scripts/first_person_framing_w205.py'), *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Current canonical/authored Line in the Sand input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Fresh W218 original rig/report required at dedicated W218 paths')
    # Parse only literal constants. Never execute/import/run the W188 generator.
    legacy = ast.parse(raw[AUTHORED_SOURCE])
    literals = {node.targets[0].id: ast.literal_eval(node.value)
                for node in legacy.body if isinstance(node, ast.Assign)
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ('KEYS', 'GRIP', 'MAGAZINE_ANCHOR')}
    if literals != {'KEYS': KEYS, 'GRIP': GRIP, 'MAGAZINE_ANCHOR': MAGAZINE_ANCHOR}:
        raise ValueError('W188 authored knots/pivots/anchor changed')
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile, rig, report = (json.loads(raw[p]) for p in (PROFILE, RIG, SOURCE_REVIEW))
    old = json.loads(raw[AUTHORED_MANIFEST])
    elements = source['elements']
    expected_names = ['lower_battery', 'battery_silver_floor', 'battery_rounded_front_-1',
        'battery_rounded_rear_-1', 'battery_rounded_front_1', 'battery_rounded_rear_1',
        'battery_edge_-1', 'battery_edge_1']
    if (len(elements) != 79 or [elements[i]['name'] for i in BATTERY_INDICES] != expected_names
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP)
            or old['magazineAnchor'] != list(MAGAZINE_ANCHOR)
            or old['partitionIndices']['magazine'] != list(BATTERY_INDICES)
            or old['reloadOnlyGeometry']['elements'] != contacts(source)):
        raise ValueError('W188 semantic battery/contacts/UV/keys/anchors changed')
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'line_in_the_sand'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or profile.get('contacts') != {'reload': {'rigAction': SOURCE_ACTION,
                'partHint': 'magazine', 'policy': 'magazine', 'gripWindow': list(GRIP_WINDOW)}}):
        raise ValueError('W218 full-chain framing/reload-release profile changed')
    framing = json.loads(raw[FRAMING])
    effective = {**framing['families']['linear_fusion_rifle'],
                 **framing.get('weapons', {}).get('line_in_the_sand', {})}
    if any(effective.get(k) != v for k, v in EXPECTED_FRAMING.items()
           if k not in ('sourceFullChain', 'keepMeshSupport', 'hideSupportAtRest')):
        raise ValueError('Effective canonical family framing changed')
    mesh_contacts = json.loads(raw[CONTACTS])['weapons']['line_in_the_sand']
    if (any(mesh_contacts[k] != v for k, v in EXPECTED_CONTACTS.items())
            or any(mesh_contacts['reload'][k] != v for k, v in EXPECTED_RELOAD_CONTACT.items())):
        raise ValueError('Authored rest/reload mesh contacts changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups']['fusion_rifle_04669cdb']
    marker = rig.get('w218Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'fusion_rifle_04669cdb' or rig.get('fallback') is not False
            or 'line_in_the_sand' not in rig['weapons'] or rig.get('cameraExported') is not False
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
        raise ValueError('Expected fresh original Blender action/full shoulder chains')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if (rig.get(key) != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('path') != str(RIG)
            or profile['sourceRig'].get('group') != rig['group']
            or profile['sourceRig'].get('action') != SOURCE_ACTION):
        raise ValueError('Invalid W218 sourceRig profile')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body': 71, 'magazine': 10} or estimate > 1000:
        raise ValueError('Battery partition or candidate weapon+arm budget exceeded')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W218 Line in the Sand namespace')
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
        'schemaVersion': 1, 'stage': 'W218', 'weapon': 'line_in_the_sand',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; shared knot derivatives; zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'magazineAnchor': MAGAZINE_ANCHOR,
        'magazineExtractionAxis': [0, -1, 0], 'magazineSeatedProgress': .84,
        'magazineCompressionProgress': .80, 'gripWindow': list(GRIP_WINDOW),
        'authoredTimingSource': str(AUTHORED_SOURCE), 'normalizedPhases': old['normalizedPhases'],
        'reference': old['reference'],
        'referencePolicy': 'Read W188 SOURCE.md/manifest; viewed retained actual storyboard/comparison. Original video was not reopened. Same-weapon battery mechanism remains authored; shared family rig is not exclusive weapon motion recovery.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': 71,
        'movingElements': 10, 'magazineElements': 10, 'weaponElements': sum(counts.values()),
        'canonicalWeaponElements': canonical_count, 'addedElements': 2,
        'newElementsRelativeToW188': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': sum(counts.values()) + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': 'Reload81+448=529; canonical253+448=701. Alternatives are not summed. Master measures every composed route including ADS/inspect.',
        'movingIndices': list(BATTERY_INDICES),
        'movingNames': expected_names,
        'partitionIndices': old['partitionIndices'], 'geometryPolicy': old['geometryPolicy'],
        'payloadPolicy': 'Whole canonical8-element lower battery plus unchanged2 metallic contacts. Constant rigid scale; normalized dispatch omission [.40,.60), dense poses24..35; no shrinking.',
        'payloadHiddenInterval': [.40, .60], 'payloadHiddenEndExclusive': True,
        'reloadOnlyGeometry': {'elements': contacts(source), 'count': 2,
            'visibleSampleIndices': [i for i in range(SAMPLES) if payload_visible(i / INTERVALS)],
            'uvPolicy': old['reloadOnlyGeometry']['uvPolicy']},
        'sourceLimitation': old['sourceLimitation'],
        'originalRip': {'path': '/tmp/destiny-weapons-w30/raw/line_in_the_sand/extracted/Line in the Sand/Line in the Sand.fbx',
            'sha256': '82041f575f104715b2c4c5a688d3d25ff19df1b3a09c18f756fd61ca8830f899',
            'policy': 'Historical inert W188 mesh provenance; not reopened or rehashed in W218.'},
        'sourceElementsAndUVSha256': sha(encode(elements)),
        'partElementsAndUVSha256': {part: sha(encode(model['elements']))
                                    for part, model in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'reloadGeometryMatchesW188': True,
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Canonical graph at0/1, overshoot, negative inactive and non-FP; original ADS/inspect cases precede reload; native/twohand flags preserved.',
        'rigPath': str(RIG), 'sourceReviewPath': str(SOURCE_REVIEW),
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': rig['group'], 'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceCameraRecovered': False, 'partHint': 'magazine', 'policy': 'magazine',
        'originalBlend': evidence['paths']['sourceBlend'],
        'originalBlendSha256': rig['sourceBlendSha256'],
        'sourceReviewEvidence': profile.get('evidence', []),
        'motionAuthorship': 'Exact13 W188 keys, holds, anchors, UV/part partition, normalized visibility and rigid transform algebra. Only interpolation changes to W215/216 C1 PCHIP. Master attaches original ordinary shoulder/elbow/wrist chains without attenuation or new framing offsets.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'timingPolicy': 'Existing capacity5/reload49ticks/charge11ticks/cadence19ticks/burst1/sharedBurstAmmo preserved;61 normalized samples across60 intervals. Source perk capacity9 not copied.',
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed), 'staticParts': 2,
        'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': profile['limitations'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W218 Line in the Sand output mapping')
    return output
