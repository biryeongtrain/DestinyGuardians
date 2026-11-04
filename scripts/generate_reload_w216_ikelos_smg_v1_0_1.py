#!/usr/bin/env python3
"""W216 IKELOS v1.0.1: unchanged W182 part path, 61-pose C1 PCHIP.

Pure stdlib; import and generate(root=ROOT) never write. Master owns source FK,
materialization, arm integration, all-route budget, FIRST feedback and SECOND.
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
ART = Path('art/weapons/w216/ikelos_smg_v1_0_1')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w216_ikelos_smg_v1_0_1.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w182_ikelos_smg_v1_0_1.py')
OLD_ART = Path('art/weapons/w182/ikelos_smg_v1_0_1')
SOURCE = A / 'models/weapon_surface_w123/ikelos_smg_v1_0_1.json'
NATIVE = A / 'models/weapon/submachine_gun/ikelos_smg_v1_0_1.json'
TWOHAND = A / 'models/weapon/submachine_gun/ikelos_smg_v1_0_1_twohand.json'
ITEM = A / 'items/weapon/ikelos_smg_v1_0_1.json'
TEXTURE = A / 'textures/item/weapon/w123/ikelos_smg_v1_0_1.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w205/rigs/submachine_gun_cdf8185c.json')
KEY = 'weapon_reload_w216_ikelos_smg_v1_0_1/ikelos_smg_v1_0_1'
WEAPON = 'ikelos_smg_v1_0_1'
GROUP = 'submachine_gun_cdf8185c'
RIG_ACTION = '80A8A170'
ACTION_NAME = 'Armature|fp_80A8A170_reload_full|Base'
EXPORTER_SHA256 = '54b2f8673aaf75b97a388077ecad683eef2441a73f313194e52ce9b6cd514a38'
FRESH_RIG_SHA256 = '8f381506a064afb16da2480a2458e997405d5840972cc7afa83a257616c275c4'
AUTHORED_SHA256 = 'e4b6cdca770c37904e9e44995fcc0cd084ee6003abe581c1c67176af3a2842eb'
OLD_SOURCE_SHA256 = '4c190016188aec73faf2edc2cb2542ef95755da403c1ef60a0c4045f764ce77a'
OLD_MANIFEST_SHA256 = '3848497de47f995cecb8c232cdee08b088a1f0357f32acd23a74515024f2360b'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = 61
ARM_ELEMENT_RESERVE = 4 * 112
EXPECTED_FRAMING = {
    'translation': [-.65, .6, 0], 'rotation': [-1, 2, 0], 'scale': .98,
    'rightWristRoll': 28, 'keepMeshSupport': True, 'meshArmDirections': True,
    'hideSupportAtRest': False, 'reloadCameraLower': 0,
    'sourceWeaponRelative': True, 'sourceFullChain': True,
}

GRIP = (8.0, 8.4, 8.25)
MAGAZINE_ANCHOR = (8.0, 4.577331375, 8.26)
KEYS = ((0.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.06, (4, -2, -3), (0.05, -0.05, 0), (0, 0, 0)), (0.22, (58, -9, -17), (0.2, 0.2, 0.1), (0, -2.8, 0.15)), (0.34, (62, -9, -17), (0.2, 0.2, 0.1), (0, -4.8, 0.3)), (0.46, (48, -7, -19), (0.2, 0.1, 0.1), (0, -4.8, 0.3)), (0.62, (43, -7, -20), (0.2, 0.1, 0.1), (0, -1.4, 0.1)), (0.7, (43, -7, -20), (0.2, 0.1, 0.1), (0, 0, 0)), (0.76, (47, -7, -21), (0.2, 0.16, 0.1), (0, 0, 0)), (0.8, (42, -7, -20), (0.2, 0.06, 0.1), (0, 0, 0)), (0.88, (38, -5, -16), (0.1, 0, 0.05), (0, 0, 0)), (1.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/ikelos_smg_v1_0_1.json': '953456dfd97404185ccb13dedb7d70a0f4110915ca405c4d0a6843a7578a791c', 'src/main/resources/assets/destiny/textures/item/weapon/w123/ikelos_smg_v1_0_1.png': '67169c7e0a97481c77de13b4a08fd9b63188359bdfef8075fd0e35dfb72e0690', 'src/main/resources/assets/destiny/items/weapon/ikelos_smg_v1_0_1.json': '4c6ccbcda6f81cb75eb8fe89fecf71aa78ba7f0b42ec8245247866cddcbb5e08', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_inspect_twohand.json': 'ed76502a03723011e81e7e9b0b98ad2262e55ff149e1d9563327211da9dc8d49', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_twohand.json': 'fd54f41d53da0dbfb74d500e93ab4416a0eed7bea54986ac8a08f2b78e30b8e4', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_ads_twohand.json': '8f19751f7b00ab71784027a0d4ce034dfb90977b73822a190be11b069880795c', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1.json': 'd0b5f0be06846af78d9c207889e33226694343f896e1bd4028776754df28bec8', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_ads.json': '888d2860e55eec215ca2ac9bffc9f70abd5c587bb1e1b4d6ebbf1706f854af89', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_inspect.json': 'aa7578f2da14189c1670289f8b78ce2df03b5274e7d6a6430f86a9928c16050d'}

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

def is_payload(e):
    # Side cells, their leads, lower swivel and well are fixed to the receiver/grip.
    return e['name'] == 'magazine'

def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements']
                              if is_payload(e)==(part=='magazine')]}
            for part in PARTS}

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Complete existing grip-fed magazine is one rigid payload; fixed cells are body.
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
    """Read reviewed inputs under root; return absolute Path -> bytes only."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, PROFILE,
        GENERATOR, AUTHORED_SOURCE, OLD_ART/'SOURCE.md', OLD_ART/'manifest.json',
        CONTACTS, FRAMING, RIG, *(Path(p) for p in PINS)]))
    raw = {path: (root/path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Canonical geometry/UV/ADS/gameplay/audio drift: ' + path)
    for path, digest in ((AUTHORED_SOURCE, AUTHORED_SHA256),
                         (OLD_ART/'SOURCE.md', OLD_SOURCE_SHA256),
                         (OLD_ART/'manifest.json', OLD_MANIFEST_SHA256)):
        if sha(raw[path]) != digest:
            raise ValueError('W182 authored provenance drift: ' + str(path))
    # Literal AST only: never import or execute the heavy numpy/Pillow generator.
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {'KEYS', 'GRIP', 'MAGAZINE_ANCHOR', 'PINS'}):
            authored[node.targets[0].id] = ast.literal_eval(node.value)
    if authored != {'KEYS': KEYS, 'GRIP': GRIP,
                    'MAGAZINE_ANCHOR': MAGAZINE_ANCHOR, 'PINS': PINS}:
        raise ValueError('W182 authored knots/anchors changed')
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    contacts = json.loads(raw[CONTACTS])['weapons'][WEAPON]
    old_manifest = json.loads(raw[OLD_ART/'manifest.json'])
    elements = source['elements']
    indices = {part: [i for i,e in enumerate(elements)
                      if is_payload(e) == (part == 'magazine')] for part in PARTS}
    if (len(elements) != 133 or indices['magazine'] != [129]
            or indices != old_manifest['partitionIndices']
            or old_manifest['keyframes'] != json.loads(encode(KEYS))
            or elements[129]['name'] != 'magazine'):
        raise ValueError('W182 complete magazine/fixed grip partition drift')
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != WEAPON
            or profile.get('sourceAction') != RIG_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or set(profile.get('contacts', {})) != {'reload'}):
        raise ValueError('Preserved framing/full-chain profile drift')
    overrides = profile['contacts']['reload']
    if set(overrides) != {'rigAction', 'partHint', 'policy', 'gripWindow'}:
        raise ValueError('Only action/payload/attachment override is permitted')
    reload = {**contacts['reload'], **overrides}
    if (reload.get('rigAction') != RIG_ACTION or reload.get('partHint') != 'magazine'
            or reload.get('policy') != 'magazine'
            or contacts['right']['position'] != [8.,8.4,8.25]
            or contacts['right']['rotation'] != [0.,0.,0.]
            or contacts['left']['position'] != [7.8,9.,3.6]
            or contacts['left']['rotation'] != [-54.,0.,-20.]
            or reload.get('contact') != [7.5,4.55,8.26]
            or reload.get('rotation') != [0.,0.,0.]):
        raise ValueError('Original mesh rest/reload contact drift')
    window = reload['gripWindow']
    if not (isinstance(window, list) and len(window) == 4
            and all(isinstance(v, (int,float)) and math.isfinite(v) for v in window)
            and 0 <= window[0] < window[1] <= window[2] < window[3] <= .70):
        raise ValueError('Magazine attachment must release by authored .70 seat')
    action = rig['actions'][RIG_ACTION]
    fresh = rig.get('w216Source61', {})
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (sha(raw[RIG]) != FRESH_RIG_SHA256 or rig.get('group') != GROUP
            or WEAPON not in rig.get('weapons', []) or rig.get('fallback') is not False
            or rig.get('cameraExported') is not False
            or fresh.get('exporterSha256') != EXPORTER_SHA256
            or fresh.get('reloadSamples') != SAMPLES
            or action.get('action') != ACTION_NAME
            or (action['start'], action['end']) != (1.,91.)
            or len(action['frames']) != SAMPLES):
        raise ValueError('Master fresh W216 source61 actual action frames1..91 required')
    if (profile['sourceRig'].get('group') != GROUP
            or profile['sourceRig'].get('action') != RIG_ACTION
            or profile['sourceRig'].get('evaluatedJsonSha256') != FRESH_RIG_SHA256):
        raise ValueError('Reviewed fresh source profile drift')
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if rig.get(key) != profile['sourceRig'][key]:
            raise ValueError('Original source hash drift: ' + key)
    for i, frame in enumerate(action['frames']):
        if (frame['progress'] != i/INTERVALS or abs(frame['frame']-(1+90*i/INTERVALS)) > 1e-10
                or not joints <= frame['joints'].keys()):
            raise ValueError('Uniform original full-chain sampling required')
        for joint in joints:
            matrix = frame['joints'][joint]
            if len(matrix) != 4 or any(len(row) != 4 or not all(math.isfinite(v) for v in row)
                                       for row in matrix):
                raise ValueError('Invalid source matrix: ' + joint)
    parts = partition(source)
    counts = {part: len(model['elements']) for part,model in parts.items()}
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    if counts != {'body':132, 'magazine':1} or max(sum(counts.values()),canonical_count)+ARM_ELEMENT_RESERVE > 1000:
        raise ValueError('Partition or ordinary full-chain arm budget exceeded')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside W216 IKELOS namespace')
        output[root/path] = encode(value)

    for part,model in parts.items():
        emit(A/f'models/{KEY}_{part}.json', model)
    entries = []
    for i in range(SAMPLES):
        progress = i/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'],twohand,progress,part,grip)})

        def composite(grip):
            return {'type':'minecraft:composite', 'models':[
                {'type':'minecraft:model', 'model':f'destiny:{KEY}_{i:02}_{part}_{grip}'}
                for part in PARTS]}

        model = copy.deepcopy(item['model']) if i in (0,INTERVALS) else {
            'type':'minecraft:condition', 'property':'minecraft:custom_model_data', 'index':0,
            'on_true':composite('twohand'), 'on_false':composite('native')}
        entries.append({'threshold':float32(progress), 'model':model})
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {
        'type':'minecraft:select', 'property':'minecraft:display_context',
        'cases':[{'when':list(FP), 'model':{
            'type':'minecraft:select', 'property':'minecraft:custom_model_data', 'index':0,
            'cases':[{'when':['ads','inspect'], 'model':copy.deepcopy(item['model'])}],
            'fallback':{'type':'minecraft:range_dispatch', 'property':'minecraft:custom_model_data',
                        'index':1, 'entries':entries, 'fallback':copy.deepcopy(item['model'])}}}],
        'fallback':copy.deepcopy(item['model'])}
    emit(A/f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion':1, 'stage':'W216', 'weapon':WEAPON,
        'generator':str(GENERATOR), 'generatorSha256':sha(raw[GENERATOR]),
        'itemModel':'destiny:'+KEY, 'frames':SAMPLES, 'intervals':INTERVALS,
        'progressFloatIndex':1, 'gripFlagIndex':0, 'firstPersonContexts':list(FP),
        'thresholdEncoding':'exact float32(i/60)',
        'curve':'C1 weighted harmonic PCHIP; zero endpoints, holds and extrema',
        'keyframes':KEYS, 'gripPivot':GRIP, 'magazineAnchor':MAGAZINE_ANCHOR,
        'authoredTimingSource':str(AUTHORED_SOURCE),
        'normalizedPhases':old_manifest['normalizedPhases'],
        'magazineSeatedProgress':.70, 'reloadGripWindow':window,
        'sourceGeometryPath':str(SOURCE), 'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'sourceElements':len(elements), 'partElements':counts,
        'bodyElements':counts['body'], 'movingElements':counts['magazine'],
        'weaponElements':sum(counts.values()), 'canonicalWeaponElements':canonical_count,
        'partitionIndices':indices, 'movingNames':['magazine'],
        'partitionRationale':'Existing complete grip-fed magazine129 alone moves. Grip well, lower swivel, cells/wires, foregrip, sight, rear disc and charging handle stay fixed.',
        'geometryAndUVPreserved':True, 'addedElements':0, 'triangleAdapterElements':0,
        'sourceElementsAndUVSha256':sha(encode(elements)),
        'partElementsAndUVSha256':{part:sha(encode(model['elements'])) for part,model in parts.items()},
        'elementLimit':1000, 'ordinaryArmElementReserve':ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate':sum(counts.values())+ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate':canonical_count+ARM_ELEMENT_RESERVE,
        'integratedAllRouteMaximumMeasured':False,
        'budgetBasis':'133 reload+448 ordinary arm surfaces=581; canonical220+448=668 estimate. Master measures every composed ADS/inspect/native/twohand route.',
        'hipEndpoints':[0,INTERVALS], 'endpointDisplayExact':True, 'fallbackModelExact':True,
        'fallback':'Exact canonical item graph at negative/inactive progress, endpoints, overshoot and non-FP. ADS/inspect precede dispatch; native/twohand boolean0 retained.',
        'sourceGroup':GROUP, 'sourceAction':RIG_ACTION, 'rigAction':RIG_ACTION,
        'rigActionName':ACTION_NAME, 'sourceActionSourceRange':[action['start'],action['end']],
        'sourceRigSamples':SAMPLES, 'sourceFullChain':True, 'sourceCameraRecovered':False,
        'sourceEvidence':profile.get('evidence',[]),
        'firstReview':profile.get('firstReview',{}),
        'reference':old_manifest['reference'],
        'motionAuthorship':'Exact W182 authored eleven knots, pivot, rigid split, holds and offset path. Only segment smoothstops become W215 weighted harmonic PCHIP. Master binds original unattenuated normal-length shoulder/elbow/wrist FK and supported magazine attachment release.',
        'gameplayTimingChanged':False, 'mechanicsOrAudioChanged':False,
        'timingPolicy':old_manifest['timingPolicy'],
        'nativeGameplayVerified':False, 'nativeVisibilityAccepted':False,
        'staticParts':len(PARTS), 'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'packFiles':len(output), 'totalReturnedFiles':len(output)+1,
        'inputSha256':{str(path):sha(data) for path,data in raw.items()},
        'outputSha256':{str(path.relative_to(root)):sha(data) for path,data in output.items()},
        'limitations':[
            'Worker read fresh master Blender5.4 evaluation and viewed bone-only sheet; no independent worker Blender inspection.',
            'Original contains armature only, no weapon mesh/camera/finger IK. Part path and mesh contacts remain authored.',
            '61 poses do not establish continuous native60fps interpolation.',
            'Attachment fades .62..70 and ends at authored seat before wrist recovery; FIRST must inspect exact contact/clearance.',
            'FIRST feedback correction removes legacy reloadCameraLower2.5 via explicit0 only; hip/ADS/rest and relative full-chain transforms unchanged. sourceFullChain takes priority over meshArmDirections in master pipeline.',
            'Master FIRST native12/12 reported; worker reviewed exact PNG feedback and returned reload-only lowering correction. Corrected materialization/all-route checks and SECOND visibility/contact review remain master-owned and pending.']})
    if set(output) != {root/path for path in allowed}:
        raise ValueError('Incomplete W216 IKELOS output mapping')
    return output
