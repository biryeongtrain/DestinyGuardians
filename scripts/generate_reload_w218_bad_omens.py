#!/usr/bin/env python3
"""W218 Bad Omens: unchanged W177 solids/UV/path, 61 poses / 60 intervals.

Pure stdlib import and generate(root=ROOT) -> absolute Path:bytes, no writes.
Master installs the freshly evaluated original W218 source, composes ordinary
full-chain skin arms, materializes outputs and owns FIRST/SECOND Vision.
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
ART = Path('art/weapons/w218/bad_omens')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w218_bad_omens.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w177_bad_omens.py')
AUTHORED_MANIFEST = Path('art/weapons/w177/bad_omens/manifest.json')
REFERENCE = Path('art/weapons/w177/bad_omens/motion-reference.json')
SOURCE = A / 'models/weapon_surface_w123/bad_omens.json'
NATIVE = A / 'models/weapon/rocket_launcher/bad_omens.json'
TWOHAND = A / 'models/weapon/rocket_launcher/bad_omens_twohand.json'
ITEM = A / 'items/weapon/bad_omens.json'
TEXTURE = A / 'textures/item/weapon/w123/bad_omens.png'
DESIGN = Path('art/weapons/w123/bad_omens/design.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w218/rigs/rocket_launcher_ba250bec.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w218/source/source-review.json')
KEY = 'weapon_reload_w218_bad_omens/bad_omens'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_GROUP = 'rocket_launcher_ba250bec'
SOURCE_ACTION = '80A8A1F5'
ACTION_NAME = 'Armature|fp_80A8A1F5_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.20, .25, .58, .64)
RELOAD_HAND = 'right'
EXPECTED_FRAMING = {'translation': [0, 0, 0], 'rotation': [0, 0, 0], 'scale': 1,
    'rightWristRoll': 15, 'sourceFullChain': True,
    'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {
    'right': {'position': [8., 8.3, 8.12], 'rotation': [-12., 0., 0.]},
    'left': {'position': [8., 8.9, 1.88], 'rotation': [0., 0., 0.]}}
EXPECTED_RELOAD_CONTACT = {'contact': [7.1, 12.2, 17.], 'rotation': [90., 0., 0.]}
VISIBILITY_KNOTS = ((0, 0), (.20, 0), (.25, 1), (.66, 1), (.72, 0), (1, 0))

# Literal same-weapon W177 constants; old module is never executed or imported.
GRIP = (8.0, 8.25, 8.13)
MAG_ANCHOR = (8.0, 12.2245, 17.0)
KEYS = ((0.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.06, (-8, 2, -3), (0, -0.6, 0), (0, 0, 0)), (0.18, (76, -5, -8), (0.2, -0.2, 0.2), (-3, -4, 13)), (0.3, (34, -13, -20), (0.1, -1.4, 0.2), (-3, -3, 12)), (0.4, (28, -15, -22), (0.1, -1.2, 0.2), (-1.5, -1.8, 10)), (0.48, (31, -13, -19), (0.1, -1.0, 0.1), (0, 0, 7)), (0.58, (48, -8, -12), (0.1, -0.7, 0.1), (0, 0, 2)), (0.64, (76, -5, -8), (0.2, -0.2, 0.2), (0, 0, 0)), (0.78, (72, -4, -7), (0.15, -0.2, 0.1), (0, 0, 0)), (0.9, (24, -1, -2), (0.05, -0.1, 0), (0, 0, 0)), (1.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
RIG_SHA256 = '78d7101c57cc3a3a3d88e0dc957cbdb4982160e21ec7e11a9630e3bee5958e3d'
REVIEW_SHA256 = 'f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0'
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/bad_omens.json': '437b9d20791bcd61c9a9923d17daa83cad3aaa6ac727c8b17ee8ba7357ad4ffe', 'src/main/resources/assets/destiny/items/weapon/bad_omens.json': '897aff69243a9b3f219a3d200a280d27f6b318134aa4f6890901febff20f0f2e', 'src/main/resources/assets/destiny/textures/item/weapon/w123/bad_omens.png': '2c322a42504792f2b84ada7c26bef1d4602085bb430e84f669382dd063b6af5e', 'scripts/generate_reload_w177_bad_omens.py': '5efcd84c8c4c00a717d1a31cbc38331dde32e83f8b8021c856c4979f9bcd43d6', 'art/weapons/w177/bad_omens/manifest.json': 'a7ec75d944468cad3508bc1279c656c89d4c67ee9b18f190acdad3e0b9a3f961', 'art/weapons/w177/bad_omens/motion-reference.json': 'f2005f0bbc69f59aca7f92e51296c546d1568b38fda4ccc694898cb11fc547c8', 'art/weapons/w123/bad_omens/design.json': '3b2ce7313db402fe2f8364e505bd4dae2949afe354601d34ceddf9c5357e8365', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_ads.json': '8c71dcc39c02126b375a0f5d2b21cb39e2bdf129b9df489c1a12439cbf1920e8', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_ads_twohand.json': 'bcac27a4e9423cddfc91bc16cc78ff87610685b1df623c2e6a837576d4293caf', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_twohand.json': '79486ccc0263306fb8e51cc1f2b2271402ea32c60b1237fcea88da8892fabaa8', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_inspect_twohand.json': 'd56817f3f2ea442116f6dbe3eb44f44d5401bcc70457e96d5893dfdf9c74c727', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens_inspect.json': '93b9c95a7eba25e4d6c359d9e2996646d716f56ecfb4592393b1c982d23ea3ed', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bad_omens.json': 'ef85cfffd28a597c5683ef9b6682d23ef151d46f3069c6c2ce18bfd9db97d40c', 'src/main/resources/assets/destiny/models/weapon_reload_w177_bad_omens/bad_omens_body.json': '819afa160231e333ab0c5c1c86498af2f6b243587aa9bf33b0c2e8b4380db0e1', 'src/main/resources/assets/destiny/models/weapon_reload_w177_bad_omens/bad_omens_magazine.json': 'e0b84181e4c5a7d9950af229d9ed8df88e1457fbcc8e62cc55492b671cb39b31'}

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

def payload_visibility(p):
    # A replacement round enters from below/right-of-rear opening; no empty magazine ejection.
    if p<=.20 or p>=.72:return 0.
    if p<.25:return (p-.20)/.05
    if p>.66:return (.72-p)/.06
    return 1.

def rocket_elements(source):
    """12 overlapping solid faceted-profile pieces; all hidden dimensions authored.
    Negative-Z nose, long body, connected tail band. Uses existing dark/steel face UV.
    Seated inside aft bore, omitted visually at rest rather than plugging canonical bore.
    """
    out=[]
    def segment(name,z0,z1,width,height,template):
        for i,angle in enumerate((0,45)):
            e=copy.deepcopy(source['elements'][template])
            e.update(name=f'authored_rocket_{name}_{i}',**{'from':[8-width/2,12.2245-height/2,z0],'to':[8+width/2,12.2245+height/2,z1]})
            e['rotation']={'origin':[8,12.2245,(z0+z1)/2],'axis':'z','angle':angle}
            out.append(e)
    segment('body',14,20,.92,.92,32)
    segment('shoulder',13.3,14.15,.86,.86,32)
    segment('nose',12.6,13.45,.62,.62,32)
    segment('tip',12.25,12.75,.30,.30,32)
    segment('tail_band',19.7,20.1,.96,.96,40)
    segment('tail_plug',20.0,20.35,.72,.72,32)
    return out

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS: raise ValueError((part,grip))
    if not math.isfinite(p) or not 0 <= p <= 1: raise ValueError(p)
    accepted=original if grip=='native' else twohand
    if p in (0,1):
        d=copy.deepcopy(accepted)
        if part=='magazine':
            for context in FP: d[context]['scale']=[0,0,0]
        return d
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
        if part=='magazine':
            visibility=payload_visibility(p)
            # Scale around payload anchor, not model center, to prevent shrink drift.
            position=add(position,vec(rotation,[s[0]*(1-visibility)*v for v in anchor]))
            display[context]['scale']=[round(v*visibility,9) for v in s]
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def authored_constants(raw):
    """Read only literal W177 AST assignments; no compile, exec, import or runpy."""
    wanted = {'KEYS', 'GRIP', 'MAG_ANCHOR'}
    return {node.targets[0].id: ast.literal_eval(node.value)
            for node in ast.parse(raw).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id in wanted}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return complete, deterministic W218-only blobs; never materialize files."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, GENERATOR,
        PROFILE, RIG, SOURCE_REVIEW, AUTHORED_SOURCE, AUTHORED_MANIFEST, REFERENCE,
        DESIGN, SURFACE_MAP, CONTACTS, FRAMING,
        Path('scripts/first_person_framing_w205.py'),
        Path('src/main/resources/destiny/weapons/w46-timing.json'),
        Path('src/main/resources/destiny/sounds/w63-reload.json'),
        *(Path(path) for path in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Current Bad Omens geometry/UV/authored input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Fresh W218 source61 rig/report required at W218 paths')
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile, rig, report = (json.loads(raw[path]) for path in (PROFILE, RIG, SOURCE_REVIEW))
    old = json.loads(raw[AUTHORED_MANIFEST])
    reference = json.loads(raw[REFERENCE])
    if (len(source['elements']) != 117
            or authored_constants(raw[AUTHORED_SOURCE]) != {'GRIP': GRIP, 'MAG_ANCHOR': MAG_ANCHOR, 'KEYS': KEYS}
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP) or old['magazineAnchor'] != list(MAG_ANCHOR)
            or old['payloadVisibilityKnots'] != json.loads(encode(VISIBILITY_KNOTS))):
        raise ValueError('W177 keys/anchors/visibility/canonical solids changed')
    for part in PARTS:
        prior = json.loads(raw[A / f'models/weapon_reload_w177_bad_omens/bad_omens_{part}.json'])
        expected = source['elements'] if part == 'body' else rocket_elements(source)
        if prior['elements'] != expected:
            raise ValueError('W177 retained part geometry/face UV changed: ' + part)
    if json.loads(raw[DESIGN])['revision'] != 'W130':
        raise ValueError('Expected current W130 semantic geometry provenance')
    rule = next(rule for rule in json.loads(raw[SURFACE_MAP])['targets']
                if rule['path'] == 'assets/destiny/models/weapon/rocket_launcher/bad_omens.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/bad_omens.json'
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Selected Bad Omens surface mapping changed')
    if reference['inspectedActualFrames'] is not True or len(reference['frames']) != 12:
        raise ValueError('Expected retained Bad Omens actual gameplay references')
    for frame in reference['frames']:
        path = Path(frame['path'])
        raw[path] = (root / path).read_bytes()
        if sha(raw[path]) != frame['sha256']:
            raise ValueError('Retained actual reference drift: ' + str(path))
    settings = json.loads(raw[FRAMING])
    effective = {**settings['families'].get('rocket_launcher', settings['default']),
                 **settings.get('weapons', {}).get('bad_omens', {})}
    # Preserve the current shared loader fallback. Rocket launcher has no family
    # entry: do not silently copy fusion-rifle camera offsets or left wrist roll.
    if effective != {k: v for k, v in EXPECTED_FRAMING.items()
                     if k not in {'sourceFullChain', 'keepMeshSupport', 'hideSupportAtRest'}}:
        raise ValueError('Current effective rocket framing changed')
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'bad_omens'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or profile.get('contacts') != {'reload': {'rigAction': SOURCE_ACTION,
                'partHint': 'magazine', 'policy': 'magazine', 'gripWindow': list(GRIP_WINDOW),
                'hand': RELOAD_HAND}}):
        raise ValueError('W218 Bad Omens full-chain/contact profile changed')
    contacts = json.loads(raw[CONTACTS])['weapons']['bad_omens']
    if (any(contacts[k] != v for k, v in EXPECTED_CONTACTS.items())
            or any(contacts['reload'][k] != v for k, v in EXPECTED_RELOAD_CONTACT.items())):
        raise ValueError('Bad Omens authored mesh rest/loading contact changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups'][SOURCE_GROUP]
    marker = rig.get('w218Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or 'bad_omens' not in rig['weapons'] or rig.get('cameraExported') is not False
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('exporterSha256') != report['exporterSha256']
            or marker.get('blenderVersion') != report['blenderVersion']
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 133.)
            or len(action['frames']) != SAMPLES
            or any(frame['progress'] != i / INTERVALS
                   or abs(frame['frame'] - (1 + 132*i/INTERVALS)) > 1e-10
                   or not joints <= frame['joints'].keys()
                   for i, frame in enumerate(action['frames']))
            or evidence['actions'][SOURCE_ACTION]['action'] != ACTION_NAME
            or evidence['actions'][SOURCE_ACTION]['slot'] != 'OBSlot'
            or 'reload_full' not in evidence['actions'][SOURCE_ACTION]['sourceNames']
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1., 133.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['actions'][SOURCE_ACTION]['maxExistingCacheJointAbsError'] != 0
            or evidence['objects'] != [{'name': 'Armature', 'type': 'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Expected original Blender action1..133 and full shoulder chains')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if (rig.get(key) != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('group') != SOURCE_GROUP
            or profile['sourceRig'].get('action') != SOURCE_ACTION
            or profile['sourceRig'].get('path') != str(RIG)
            or profile['sourceRig'].get('sha256') != RIG_SHA256):
        raise ValueError('Invalid fresh W218 sourceRig profile')
    geometries = {part: copy.deepcopy(source) for part in PARTS}
    geometries['magazine']['elements'] = rocket_elements(source)
    counts = {part: len(model['elements']) for part, model in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body': 117, 'magazine': 12} or estimate > 1000:
        raise ValueError('Unexpected Bad Omens weapon+reserved-arm budget')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W218 Bad Omens namespace')
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
        raise ValueError('Canonical Bad Omens ADS/inspect guard changed')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W218', 'weapon': 'bad_omens',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'exact float32(i/60), matching master runtime grid60',
        'curve': 'C1 weighted harmonic PCHIP; shared derivatives, zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'magazineAnchor': MAG_ANCHOR,
        'payloadVisibilityKnots': VISIBILITY_KNOTS, 'magazineNeutralSeatedProgress': .64,
        'gripWindow': list(GRIP_WINDOW), 'reloadGripWindow': list(GRIP_WINDOW),
        'reloadHand': RELOAD_HAND, 'stabilizingHand': 'left',
        'firstVisionFeedback': profile.get('firstVisionFeedback', {}),
        'authoredTimingSource': str(AUTHORED_SOURCE), 'normalizedPhases': old['normalizedPhases'],
        'reference': old['reference'], 'referenceConfidence': old['referenceConfidence'],
        'sourceObservedSeconds': old['sourceObservedSeconds'],
        'referencePolicy': 'Viewed retained W177 actual-frame storyboard and three-oblique comparison; read inert W177 AST, manifest and motion-reference. Original video not reopened.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceRevision': old['sourceRevision'], 'sourceElements': 117,
        'partElements': counts, 'bodyElements': 117, 'movingElements': 12,
        'magazineElements': 12, 'weaponElements': 129,
        'canonicalWeaponElements': canonical_count, 'addedElements': 12,
        'newElementsRelativeToW177': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': 129 + ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate': canonical_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000,
        'assembledBudgetVerified': False, 'measuredAllRouteElements': None,
        'budgetBasis': 'Reload129+448=577; raw canonical253+448=701. Alternatives are not summed; master measures all routes, including ADS/inspect.',
        'partitionRationale': old['partitionRationale'],
        'authoredHiddenDetails': old['authoredHiddenDetails'],
        'reloadOnlyGeometry': {'count': 12, 'elements': rocket_elements(source),
            'uvPolicy': 'Exact existing W177 dark/steel face UV from current canonical templates32/40'},
        'payloadPolicy': 'Keep normalized W177 scale envelope: zero through.20, linear reveal to.25, full through.66, linear hide to.72, then zero. Scale about MAG_ANCHOR; no frame-index remapping.',
        'payloadVisibleSampleIndices': [i for i in range(SAMPLES) if payload_visibility(i/INTERVALS) > 0],
        'sourceElementsAndUVSha256': sha(encode(source['elements'])),
        'partElementsAndUVSha256': {part: sha(encode(model['elements'])) for part, model in geometries.items()},
        'canonicalGeometryAndUVPreserved': True, 'geometryAndUVPreserved': True,
        'reloadGeometryMatchesW177': True, 'hipEndpoints': [0, INTERVALS],
        'endpointDisplayExact': True, 'fallbackModelExact': True,
        'endpointPolicy': old['endpointPolicy'],
        'fallback': 'Canonical graph at0/1, negative inactive and non-FP; ADS/inspect cases precede reload; native/twohand flags preserved. Range dispatch clamps overshoot to canonical final entry.',
        'rotationConvention': old['rotationConvention'],
        'rigAction': SOURCE_ACTION, 'sourceAction': SOURCE_ACTION, 'rigActionName': action['action'],
        'sourceGroup': SOURCE_GROUP, 'sourceActionWeaponExclusive': False,
        'sourceActionSourceRange': [action['start'], action['end']],
        'sourceRigPath': str(RIG), 'sourceRigSha256': sha(raw[RIG]),
        'sourceRigSamples': len(action['frames']), 'sourceFullChain': True,
        'sourceCameraRecovered': False, 'partHint': 'magazine', 'policy': 'magazine',
        'sourceReviewEvidence': profile.get('evidence', []), 'originalRip': {
            'sourceBlend': rig['sourceBlend'],
            **{key: rig[key] for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256')}},
        'motionAuthorship': 'Exact11 W177 same-weapon knots, anchors, holds, 117+12 geometry/UV, payload visibility and rigid math. Only interpolation changes to C1 PCHIP. Original shared-family shoulder/elbow/wrist source61 supplies ordinary fingerless arms; no camera fit or IK invented.',
        'timingPolicy': old['timingPolicy'], 'gameplayTimingChanged': False,
        'mechanicsOrAudioChanged': False, 'nativeGameplayVerified': False,
        'nativeVisibilityAccepted': False, 'thirdPersonReloadClaimed': False, 'handIK': False,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed),
        'staticParts': 2, 'parentDisplayChildren': SAMPLES * len(PARTS) * len(GRIPS),
        'limitations': [
            'Master evaluated original Blender5.4; worker read fresh report/rig and viewed actual bone sheet, not an independent Blender evaluation.',
            'ARMATURE only, shared rocket family; no recovered weapon mesh/camera/fingers/IK or concealed rocket internals. Contacts and weapon/payload motion remain authored.',
            '61 poses/60 intervals are a bank of discrete native item displays, not proof of continuous60fps interpolation.',
            'RIGHT-hand payload attachment fades.58..64, zero at authored neutral seat.64. Existing visibility remains full until.66 and hides through.72 without wrist recovery drag.',
            'Current effective default rocket framing and authored right/left/rest reload contact values preserved; no limb length/axis attenuation or new camera offsets.',
            'FIRST actual PNG feedback reviewed; wrong LEFT handling binding corrected to RIGHT in profile. Master reports native/runtime and maximum701 budget pass. SECOND must show actual rocket with right hand through handling/reseat; visual acceptance remains pending.',
            *reference['limitations']],
        'canonicalSha256': PINS,
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W218 Bad Omens output mapping')
    return output
