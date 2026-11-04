#!/usr/bin/env python3
"""W218 Stormchaser: same-weapon W188 battery reload,61 poses/60 intervals.

Pure stdlib, inert import, read-only generate(root=ROOT)->absolute Path:bytes.
Master owns materialization, full-chain player-skin arms and FIRST/SECOND Vision.
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
ART = Path('art/weapons/w218/stormchaser')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w218_stormchaser.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w188_stormchaser.py')
AUTHORED_MANIFEST = Path('art/weapons/w188/stormchaser/manifest.json')
SOURCE = A / 'models/weapon_surface_w123/stormchaser.json'
NATIVE = A / 'models/weapon/linear_fusion_rifle/stormchaser.json'
TWOHAND = A / 'models/weapon/linear_fusion_rifle/stormchaser_twohand.json'
ITEM = A / 'items/weapon/stormchaser.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w218/rigs/linear_fusion_rifle_d9d0adf4.json')
SOURCE_REVIEW = Path('docs/qa/2026-10-28/w218/source/source-review.json')
KEY = 'weapon_reload_w218_stormchaser/stormchaser'
FP = ('firstperson_righthand','firstperson_lefthand')
PARTS = ('body','magazine')
GRIPS = ('native','twohand')
INTERVALS = 60
SAMPLES = 61
SOURCE_GROUP = 'linear_fusion_rifle_d9d0adf4'
SOURCE_ACTION = '80A8ADE1'
ACTION_NAME = 'Armature|fp_80A8ADE1_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.13,.22,.68,.75)
GRIP = (8.0, 8.26, 8.015)
MAGAZINE_ANCHOR = (8.0, 6.78, 7.61)
MAGAZINE_NAMES = ('grip_floor', 'power_shoe', 'power_shoe_toe', 'power_shoe_rear_lip', 'power_green_inset_-1', 'power_green_inset_1')
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.06, (-5, -1, -2), (-0.15, -0.18, -0.15), (0, 0, 0)), (0.13, (42, -5, -11), (-0.65, -0.55, -1.35), (0, 0, 0)), (0.22, (73, -10, -15), (-1.4, -1.2, -2.8), (0, 0, 0)), (0.29, (76, -11, -14), (-1.4, -1.2, -2.8), (0, -1.0, 0.439)), (0.39, (75, -11, -14), (-1.4, -1.2, -2.8), (-0.6, -4.8, 2.106)), (0.49, (73, -10, -13), (-1.4, -1.2, -2.8), (-0.9, -5.2, 2.282)), (0.58, (72, -9, -12), (-1.4, -1.2, -2.8), (-0.25, -3.1, 1.36)), (0.68, (70, -8, -12), (-1.4, -1.2, -2.8), (0, -1.4, 0.614)), (0.75, (68, -7, -11), (-1.4, -1.2, -2.8), (0, 0, 0)), (0.79, (59, -5, -13), (-1.3, -1.1, -2.6), (0, 0, 0)), (0.88, (25, -1, -8), (-0.6, -0.5, -1.25), (0, 0, 0)), (0.95, (3, 0, -1), (-0.08, -0.08, -0.17), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/stormchaser.json': '20d84ccbf4ceb5916023928f4c0f38ece8c97a2ae54f027cd4aed27005ac67ff', 'src/main/resources/assets/destiny/items/weapon/stormchaser.json': 'f2e90ea1eb2a05165057ab1d55bdbc31556ad4d88bbc07048cf363278a504fa4', 'src/main/resources/assets/destiny/textures/item/weapon/w123/stormchaser.png': '9df012783bc20706ac5659d5596d9bfa692417b79cd18f790cdfb13c80c13c0d', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_ads_twohand.json': 'a1e35e293fa9f54dfc66467cd67c666ec6da52e74cac1bf3213904eb99f1b97b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_ads.json': '15d97d6e712a891966a6fe6042d454cea12bb41b9473d917dc6e46ce29d9f269', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_twohand.json': '7d67e07e5565cebc402090735fe77fa2e110ffc0f26d3f8aade0528803a92fdb', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_inspect.json': '48cff067c4d7905b27aef02348cf00eb071d4a6be32ac0d20995390ec135689d', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser.json': 'dae7be8060d539e03da89a2008862b2e5bd1a68bd7a4441bca1c57f4fb4bba25', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_inspect_twohand.json': 'bd07fb49b65a955cdeb729fea62a06bfbd9503a016a5d8eaf6dacaa0e926426b', 'src/main/resources/assets/destiny/sounds/w63/reload/weapon_stormchaser_reload_49.ogg': 'a40924cac0896dd8930677618c9fa42d2c446c01b7d2d2a48718b7dacec9a62d', 'scripts/generate_reload_w188_stormchaser.py': 'ed7abe8aab16ffd2cecfd649126754852b0c537f6b4ac8e224667fa074c6058f', 'art/weapons/w188/stormchaser/manifest.json': '4320058a943624136d97e0e2eea1017285a30f9cca629ea1781afd61902838dc', 'art/weapons/w188/stormchaser/SOURCE.md': '2b429263203a9d7b13b8ebb1141c5b2d3d860cd1bfb94ccd3492c5f7bbbbbdb1', 'art/weapons/w188/stormchaser/comparison.png': 'dcfc2cf29d342864b0d40b0ab4b5773a646179d7c532e68fc323cc6b87c63261', 'art/weapons/w188/stormchaser/storyboard.png': '77c36e8c459c8a3a14bab9952687591ad7b2deaabdbfa4535bf99c63d83e4f94', 'art/weapons/w123/stormchaser/design.json': 'bab1860e4564087627bf953c73bee69e819a606684073a29c531b5229ca3e027'}
RIG_SHA256 = '718521c9996709031263f7680792d1bb8ab23987decfdc9d291a9f6704a1e955'
REVIEW_SHA256 = 'f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0'
EXPECTED_FRAMING = {'translation': [-0.65, 0.6, 0], 'rotation': [-1, 2, 0], 'scale': 0.98, 'rightWristRoll': 28, 'leftRotation': [15, 35, -35], 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_CONTACTS = {'right': {'position': [8.0, 8.25, 8.02], 'rotation': [-24.0, 0.0, 0.0]}, 'left': {'position': [7.8, 9.12, -2.3], 'rotation': [0.0, 90.0, -85.0]}, 'reload': {'contact': [7.25, 6.78, 7.61], 'rotation': [-24.0, 0.0, 0.0], 'partHint': 'magazine', 'policy': 'magazine'}}


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

def is_payload(e):return e['name'] in MAGAZINE_NAMES

def reload_shaft(source):
    # n26952..26968 resolve the incoming long stem above the broad battery foot.
    # Hidden stem dimensions are authored within original pistol_grip76 bounds.
    # This preserves the complete static silhouette and six original heel solids.
    stem=copy.deepcopy(source['elements'][76])
    stem.update(name='reload_battery_stem',**{'from':[7.73,8.02,6.55],'to':[8.27,8.50,9.62]})
    return [stem]

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
    # Full heel, green insets, crown plate and concealed stem share one rigid transform.
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
    """Read current pinned inputs only; never write or materialize returned assets."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([*(Path(p) for p in PINS), GENERATOR, PROFILE,
        RIG, SOURCE_REVIEW, CONTACTS, FRAMING, Path('scripts/first_person_framing_w205.py')]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError('Current Stormchaser geometry/UV/authored input drift: ' + path)
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != REVIEW_SHA256:
        raise ValueError('Fresh W218 original rig/report required at dedicated W218 paths')
    source, canonical = json.loads(raw[SOURCE]), json.loads(raw[NATIVE])
    twohand, item = json.loads(raw[TWOHAND])['display'], json.loads(raw[ITEM])
    old, profile = json.loads(raw[AUTHORED_MANIFEST]), json.loads(raw[PROFILE])
    rig, report = json.loads(raw[RIG]), json.loads(raw[SOURCE_REVIEW])
    # Treat old generator as inert syntax, never execute/import its dependencies.
    tree = ast.parse(raw[AUTHORED_SOURCE])
    names = {'KEYS', 'GRIP', 'MAGAZINE_ANCHOR', 'MAGAZINE_NAMES'}
    literals = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id in names}
    if literals != {'KEYS': KEYS, 'GRIP': GRIP, 'MAGAZINE_ANCHOR': MAGAZINE_ANCHOR,
                    'MAGAZINE_NAMES': MAGAZINE_NAMES}:
        raise ValueError('W188 authored knots/anchors/semantic part boundaries drift')
    elements = source['elements']
    indices = {part: [i for i, e in enumerate(elements)
                     if is_payload(e) == (part == 'magazine')] for part in PARTS}
    if (len(elements) != 95 or indices['magazine'] != list(range(80,86))
            or elements[76]['name'] != 'pistol_grip'
            or tuple(elements[i]['name'] for i in indices['magazine']) != MAGAZINE_NAMES
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['partitionIndices'] != indices
            or old['gripPivot'] != list(GRIP)
            or old['magazineAnchor'] != list(MAGAZINE_ANCHOR)
            or old['reloadOnlyGeometry']['elements'] != reload_shaft(source)):
        raise ValueError('Same-weapon W188 heel/stem geometry, UV or authored manifest drift')
    framing = json.loads(raw[FRAMING])
    effective = {**framing['families']['linear_fusion_rifle'],
                 **framing.get('weapons', {}).get('stormchaser', {}),
                 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
    if (effective != EXPECTED_FRAMING or profile.get('schemaVersion') != 1
            or profile.get('weapon') != 'stormchaser'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('framing') != EXPECTED_FRAMING
            or profile.get('contacts') != {'reload': {'rigAction': SOURCE_ACTION,
                'partHint': 'magazine', 'policy': 'magazine', 'gripWindow': list(GRIP_WINDOW)}}):
        raise ValueError('Explicit W218 full-chain/effective framing/contact policy drift')
    contacts = json.loads(raw[CONTACTS])['weapons']['stormchaser']
    if any(contacts[k] != v for k,v in EXPECTED_CONTACTS.items()):
        raise ValueError('Original Stormchaser mesh contacts changed')
    action = rig['actions'][SOURCE_ACTION]
    evidence = report['groups'][SOURCE_GROUP]
    marker = rig.get('w218Source61', {})
    joints = {'weapon','leftShoulder','leftElbow','leftWrist',
              'rightShoulder','rightElbow','rightWrist'}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or 'stormchaser' not in rig['weapons'] or rig.get('cameraExported') is not False
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('exporterSha256') != report['exporterSha256']
            or marker.get('blenderVersion') != report['blenderVersion']
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1.,96.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i/INTERVALS
                   or abs(f['frame']-(1+95*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys()
                   for i,f in enumerate(action['frames']))
            or evidence['actions'][SOURCE_ACTION]['action'] != ACTION_NAME
            or evidence['actions'][SOURCE_ACTION]['slot'] != 'OBSlot'
            or evidence['actions'][SOURCE_ACTION]['sourceFrameRange'] != [1.,96.]
            or evidence['actions'][SOURCE_ACTION]['samples'] != SAMPLES
            or evidence['actions'][SOURCE_ACTION]['maxExistingCacheJointAbsError'] != 0
            or evidence['objects'] != [{'name':'Armature','type':'ARMATURE'}]
            or report.get('allInputsUnchanged') is not True):
        raise ValueError('Expected original full-chain Blender action1..96,61 evaluated samples')
    for key in ('sourceBlendSha256','sourceMapSha256','boneMapSha256'):
        if (rig[key] != profile['sourceRig'][key]
                or rig[key] != evidence['inputSha256'][key.removesuffix('Sha256')]):
            raise ValueError('Original source provenance changed: ' + key)
    if (profile['sourceRig'].get('path') != str(RIG)
            or profile['sourceRig'].get('group') != SOURCE_GROUP
            or profile['sourceRig'].get('action') != SOURCE_ACTION):
        raise ValueError('Expected dedicated fresh W218 source rig profile')
    geometries = partition(source)
    counts = {part:len(model['elements']) for part,model in geometries.items()}
    canonical_count = len(canonical['elements'])
    estimate = max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE
    if counts != {'body':89,'magazine':7} or estimate > 1000:
        raise ValueError('Unexpected semantic partition or reserved arm budget overflow')
    output = {}
    allowed = expected_output_paths()
    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside owned Stormchaser namespace')
        output[root/path] = encode(value)
    for part, model in geometries.items():
        emit(A/f'models/{KEY}_{part}.json', model)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{frame:02}_{part}_{grip}.json', {
                    'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,progress,part,grip)})
        def composite(grip):
            # W188 always displayed both parts. No hold/hide/zero-scale phase.
            return {'type':'minecraft:composite','models':[
                {'type':'minecraft:model','model':f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in PARTS]}
        model = copy.deepcopy(item['model']) if frame in (0,INTERVALS) else {
            'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,
            'on_true':composite('twohand'),'on_false':composite('native')}
        entries.append({'threshold':float32(progress),'model':model})
    dispatch = {'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data',
                'index':1,'entries':entries,'fallback':copy.deepcopy(item['model'])}
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select'
            or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index',0) != 0
            or [case['when'] for case in guard['cases']] != ['ads','inspect']):
        raise ValueError('Canonical ADS/inspect precedence drift')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':list(FP),'model':guard}],'fallback':copy.deepcopy(item['model'])}
    emit(A/f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion':1,'stage':'W218','weapon':'stormchaser',
        'generator':str(GENERATOR),'generatorSha256':sha(raw[GENERATOR]),
        'itemModel':'destiny:'+KEY,'frames':SAMPLES,'intervals':INTERVALS,
        'progressFloatIndex':1,'gripFlagIndex':0,'firstPersonContexts':list(FP),
        'thresholdEncoding':'exact float32(i/60); master runtime grid60',
        'curve':'C1 weighted harmonic PCHIP, shared knot derivatives; zero endpoint/hold/extremum tangents',
        'keyframes':KEYS,'gripPivot':GRIP,'magazineAnchor':MAGAZINE_ANCHOR,
        'magazineExtractionAxis':old['magazineExtractionAxis'],
        'magazineSeatedProgress':.75,'gripWindow':list(GRIP_WINDOW),
        'normalizedPhases':old['normalizedPhases'],'reference':old['reference'],
        'referencePolicy':'Read inert W188 AST/SOURCE/manifest and viewed retained actual storyboard/comparison. Original video not reopened; current model base dye retained.',
        'authoredTimingSource':str(AUTHORED_SOURCE),
        'sourceGeometryPath':str(SOURCE),'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'sourceElements':len(elements),'partElements':counts,'bodyElements':89,
        'movingElements':7,'magazineElements':7,'weaponElements':sum(counts.values()),
        'canonicalWeaponElements':canonical_count,'addedElements':1,'newElementsRelativeToW188':0,
        'triangleAdapterElements':0,'ordinaryArmElementReserve':ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate':sum(counts.values())+ARM_ELEMENT_RESERVE,
        'candidateKnownCanonicalWithArmsEstimate':canonical_count+ARM_ELEMENT_RESERVE,
        'maxAssembledElements':estimate,'elementLimit':1000,
        'assembledBudgetVerified':False,'measuredAllRouteElements':None,
        'budgetBasis':'Reload96+448 reserve=544; raw canonical245+448=693. Alternatives not summed. Master must measure all actual routes including canonical/ADS/inspect.',
        'partitionIndices':indices,'movingNames':list(MAGAZINE_NAMES),
        'geometryPolicy':old['geometryPolicy'],'payloadPolicy':old['payloadPolicy'],
        'payloadVisibility':'Both original parts always dispatched; no inherited normalized omission/hide/zero-scale phase.',
        'reloadOnlyGeometry':old['reloadOnlyGeometry'],'sourceLimitation':old['sourceLimitation'],
        'semanticGroups':old['semanticGroups'],'ripProvenance':old['ripProvenance'],
        'sourceElementsAndUVSha256':sha(encode(elements)),
        'partElementsAndUVSha256':{part:sha(encode(m['elements'])) for part,m in geometries.items()},
        'canonicalGeometryAndUVPreserved':True,'reloadGeometryMatchesW188':True,
        'hipEndpoints':[0,INTERVALS],'endpointDisplayExact':True,'fallbackModelExact':True,
        'fallback':'Canonical graph at0/1, negative/inactive, overshoot and nonFP; ADS/inspect precede reload; both native/twohand flags preserved.',
        'rotationConvention':old['rotationConvention'],
        'rigAction':SOURCE_ACTION,'sourceAction':SOURCE_ACTION,'rigActionName':ACTION_NAME,
        'sourceGroup':SOURCE_GROUP,'sourceRigPath':str(RIG),'sourceReviewPath':str(SOURCE_REVIEW),
        'sourceActionSourceRange':[1.,96.],'sourceRigSamples':SAMPLES,'sourceFullChain':True,
        'sourceCameraRecovered':False,'partHint':'magazine','policy':'magazine',
        'sourceReviewEvidence':profile['evidence'],
        'motionAuthorship':'Exact14 W188 knots/holds, rigid native-to-twohand math, whole battery heel+stem and anchors. Only segment smoothstop becomes C1 PCHIP. Master attaches unattenuated original full arm chains to authored mesh contacts.',
        'gameplayTimingChanged':False,'mechanicsOrAudioChanged':False,'timingPolicy':old['timingPolicy'],
        'nativeGameplayVerified':False,'nativeVisibilityAccepted':False,
        'packFiles':len(output),'totalReturnedFiles':len(allowed),'staticParts':2,
        'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'limitations':[
            'Master evaluated original Blender5.4; worker read report/fresh rig and viewed bone-only sheet, not independent Blender evaluation.',
            'Shared-family ARMATURE source only; no weapon-exclusive mesh, camera or finger IK. Battery/body path, mesh contacts and concealed stem remain authored.',
            '61 poses/60 intervals do not prove continuous native60fps interpolation.',
            'Grip attachment fades.68..75 and is zero from neutral seat.75; wrist recovery must not drag the seated payload.',
            'No rest-contact edits, limb scaling, axis compensation, new framing fit, geometry/UV redesign or gameplay/audio changes.',
            'Master all-route budget measurement, FIRST actual image feedback, same-worker review and SECOND remain pending.'],
        'inputSha256':{str(path):sha(data) for path,data in raw.items()},
        'outputSha256':{str(path.relative_to(root)):sha(data) for path,data in output.items()}})
    if set(output) != {root/path for path in allowed}:
        raise ValueError('Incomplete61-pose Stormchaser output mapping')
    return output
