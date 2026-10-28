#!/usr/bin/env python3
"""W221 Officer pure61 hinged-cylinder poses; master owns source body and arms.
Import and generate write nothing. Python standard library only.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
WEAPON = 'seventh_seraph_officer_revolver'
ART = Path('art/weapons/w221')/WEAPON
KEY = f'weapon_reload_w221_{WEAPON}/{WEAPON}'
SOURCE = A/f'models/weapon_surface_w123/{WEAPON}.json'
TWOHAND = A/f'models/weapon/hand_cannon/{WEAPON}_twohand.json'
ITEM = A/f'items/weapon/{WEAPON}.json'
TEXTURE = A/f'textures/item/weapon/w123/{WEAPON}.png'
GENERATOR = Path('scripts/generate_reload_w221_seventh_seraph_officer_revolver.py')
PROFILE = ART/'profile.json'
MANIFEST = ART/'manifest.json'
RIG = Path('art/weapons/w221/rigs/hand_cannon_5b24a8d7.json')
QA = Path('docs/qa/2026-10-28/w221')
SOURCE_GROUP = 'hand_cannon_5b24a8d7'
RIG_ACTION = '80A8A53D'
SOURCE_BLEND_SHA256 = 'caa2af7aaf5a6219f1044a585da1dfe47f18c7559757cf8d2f4cd6dd77b8b81a'
SOURCE_SHA256 = '089fd5426ba2c2047c386391c1f38031193a3c71c71e60187291cea687a348bb'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'cylinder')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = 61
MOVING = tuple(range(72,82))
CYLINDER_NAMES = ('rear_chamber','chamber_bevel_-1','chamber_bevel_1',
    'chamber_underside','chamber_brass_side_-1','chamber_brass_bevel_-1',
    'chamber_brass_side_1','chamber_brass_bevel_1','chamber_brass_top',
    'chamber_brass_bottom')
GRIP = (8.,8.09,8.765)
HINGE = (7.25,10.56,4.32)
# All eleven W181 cylinder knots; no duplicate authored wholebody sweep.
MECHANICAL_KEYS = ((0.,0),(1/11,0),(2/11,82),(4/11,82),(5/11,82),
    (6/11,82),(7/11,82),(8/11,82),(9/11,0),(10/11,0),(1.,0))
GRIP_WINDOW = (.05,.20,6/11,7/11)
CLOSE_START = 8/11
SEATED = 9/11
ARMS_RESERVE = 448

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

def rigid(matrix):
    """Remove only evaluated FBX float drift; reject scale/shear/nonfinite input."""
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise ValueError("Expected cumulative 4x4 pose")
    if not all(math.isfinite(v) for row in matrix for v in row):
        raise ValueError("Nonfinite source pose")
    if any(abs(a-b) > 1e-7 for a,b in zip(matrix[3], (0,0,0,1))):
        raise ValueError("Invalid homogeneous source pose")
    r = [row[:3] for row in matrix[:3]]
    gram = mul(transpose(r), r)
    if max(abs(gram[i][j] - (i == j)) for i in range(3) for j in range(3)) > 1e-4:
        raise ValueError("Source pose is not rigid")
    def norm(v):
        n = math.sqrt(sum(x*x for x in v))
        return [x/n for x in v]
    x, y = [row[0] for row in r], [row[1] for row in r]
    x = norm(x)
    dot = sum(a*b for a,b in zip(x,y))
    y = norm(sub(y, [dot*v for v in x]))
    z = [x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]]
    if sum(z[i]*r[i][2] for i in range(3)) < .999:
        raise ValueError("Reflected source pose")
    return transpose([x,y,z]), [row[3] for row in matrix[:3]]

def float32(value):
    """Match Java progress division and Minecraft's float range threshold codec."""
    return struct.unpack('!f',struct.pack('!f',value))[0]

def tangents(times, values):
    """W214 C1 weighted harmonic PCHIP; zero endpoints, holds and extrema."""
    steps = [b-a for a,b in zip(times,times[1:])]
    secants = [(b-a)/h for a,b,h in zip(values,values[1:],steps)]
    slopes = [0.0]*len(times)
    for i in range(1,len(times)-1):
        before,after = secants[i-1],secants[i]
        if before*after > 0:
            w1,w2 = 2*steps[i]+steps[i-1],steps[i]+2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before+w2/after)
    return slopes


def cylinder_angle(progress):
    """C1 weighted-harmonic PCHIP, zero endpoint/hold/extremum derivatives."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Reload progress must be finite in0..1')
    for time,value in MECHANICAL_KEYS:
        if progress == time:
            return value
    times,values = zip(*MECHANICAL_KEYS)
    slopes = tangents(times,values)
    i = next(i for i in range(len(times)-1) if progress < times[i+1])
    h = times[i+1]-times[i]
    t = (progress-times[i])/h
    return ((2*t**3-3*t**2+1)*values[i]+(t**3-2*t**2+t)*h*slopes[i]
            +(-2*t**3+3*t**2)*values[i+1]+(t**3-t**2)*h*slopes[i+1])


def load_motion(root=ROOT, raw=None):
    """Validate fresh original61, correct group/action and both whole chains."""
    rig = json.loads((Path(root)/RIG).read_bytes() if raw is None else raw)
    action = rig['actions'][RIG_ACTION]
    frames = action['frames']
    if (rig.get('schemaVersion') != 1 or rig.get('group') != SOURCE_GROUP
            or rig.get('sourceBlendSha256') != SOURCE_BLEND_SHA256
            or rig.get('cameraExported') is not False
            or rig.get('names',{}).get('weapon') != '4A0810C4'
            or rig.get('w221Source61',{}).get('reloadSamples') != SAMPLES
            or action.get('action') != 'Armature|fp_80A8A53D_reload_full|Base'
            or [action['start'],action['end']] != [1,127]
            or len(frames) != SAMPLES):
        raise ValueError('Fresh original61 Officer5b24 rig required, not Duke cedb')
    required = {'weapon','leftShoulder','leftElbow','leftWrist',
                'rightShoulder','rightElbow','rightWrist'}
    for i,frame in enumerate(frames):
        if (frame['progress'] != i/INTERVALS
                or abs(frame['frame']-(1+126*i/INTERVALS)) > 1e-7
                or not required <= frame['joints'].keys()):
            raise ValueError('Incomplete Officer61 source timeline/full chain')
        for matrix in frame['joints'].values():
            rigid(matrix)
    return rig


def partition(source):
    """Every meaningful canonical solid/face UV occurs once; cylinder stays whole."""
    elements = source['elements']
    if (len(elements) != 121
            or tuple(elements[i]['name'] for i in MOVING) != CYLINDER_NAMES
            or [elements[i]['name'] for i in range(82,86)] !=
               ['rear_frame','rear_frame_slope','rear_dark_wrist','chamber_bottom_rail']):
        raise ValueError('Officer full cylinder or fixed frame partition drift')
    result = {}
    for part in PARTS:
        result[part] = {k:copy.deepcopy(v) for k,v in source.items()
                        if k not in ('elements','display')}
        result[part]['elements'] = [copy.deepcopy(e) for i,e in enumerate(elements)
                                    if (i in MOVING) == (part == 'cylinder')]
    return result


def pose_display(original, twohand, progress, part, grip):
    """Only hinge-local motion. Master replays source weaponbone exactly once.

    No grip-pivot/body sweep is authored here. Native and twohand carriers
    transport the same cylinder affine; nonFP display fields remain exact.
    """
    if part not in PARTS or grip not in GRIPS:
        raise ValueError('Unknown Officer part or grip')
    angle = cylinder_angle(progress)
    accepted = original if grip == 'native' else twohand
    display = copy.deepcopy(accepted)
    if part == 'body' or progress in (0,1) or angle == 0:
        return display
    component = xyz((0,0,angle))
    c = sub(HINGE,(8,8,8))
    local = sub(c,vec(component,c))
    for context in FP:
        idle = accepted[context]
        scale = idle['scale']
        if len(set(scale)) != 1 or twohand[context]['scale'] != original[context]['scale']:
            raise ValueError('Officer hinge requires matching uniform carrier scales')
        base = xyz(idle['rotation'])
        display[context]['rotation'] = euler(mul(base,component))
        display[context]['translation'] = [round(v,9) for v in
            add(idle['translation'],vec(base,[scale[0]*v for v in local]))]
    return display


def expected_output_paths():
    paths = {A/f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A/f'items/{KEY}.json',MANIFEST}


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return deterministic absolute Path->bytes. Never materialize or mutate.

    Relative overrides resolve below root; absolute scratch rig/profile overrides
    support draft checks while master is still preparing the independent slot.
    """
    root = Path(root).resolve()
    raw = {}
    input_labels = {}
    def read(path, *, identity=None):
        path = Path(path)
        full = path if path.is_absolute() else root/path
        full = full.resolve()
        if identity is not None:
            input_labels[full] = str(identity)
        if full not in raw:
            raw[full] = full.read_bytes()
        return raw[full]
    source_raw = read(SOURCE)
    source = json.loads(source_raw)
    twohand = json.loads(read(TWOHAND))['display']
    item = json.loads(read(ITEM))
    read(TEXTURE)
    generator_raw = Path(__file__).resolve().read_bytes()
    profile_raw = read(PROFILE if profile_path is None else profile_path, identity=PROFILE)
    profile = json.loads(profile_raw)
    rig_raw = read(RIG if rig_path is None else rig_path, identity=RIG)
    motion = load_motion(root,rig_raw)
    action = motion['actions'][RIG_ACTION]
    if sha(source_raw) != SOURCE_SHA256:
        raise ValueError('Canonical Officer geometry/UV changed; re-audit partition')
    geometries = partition(source)
    reload = profile['contacts']['reload']
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W221'
            or profile.get('weapon') != WEAPON or profile.get('sourceAction') != RIG_ACTION
            or reload.get('rigAction') != RIG_ACTION or reload.get('hand') != 'left'
            or reload.get('partHint') != 'cylinder' or reload.get('policy') != 'cylinder'
            or reload.get('gripWindow') != list(GRIP_WINDOW)
            or not GRIP_WINDOW[-1] < CLOSE_START < SEATED
            or profile['framing'].get('sourceFullChain') is not True
            or profile['framing'].get('keepMeshSupport') is not True
            or profile['framing'].get('hideSupportAtRest') is not False
            or profile['framing'].get('sourceViewRotation') != [0,0,0]):
        raise ValueError('Officer source-chain/LEFT cylinder release profile changed')
    durable_evidence = {
        'reviewPath':str(QA/'source-review.json'),
        'handlingEvidencePath':str(QA/'source-handling-evidence.json'),
        'evaluatedRigPath':str(RIG),
        'chainSheetPath':str(QA/'source-sheets'/f'{SOURCE_GROUP}-{RIG_ACTION}-upper-chain.png')}
    if any(profile['sourceProvenance'].get(key) != path
           for key,path in durable_evidence.items()):
        raise ValueError('Officer provenance must name durable repository evidence paths')
    for key in ('group','sourceBlendSha256','sourceMapSha256','boneMapSha256'):
        if profile['sourceRig'].get(key) != motion[key]:
            raise ValueError('Officer profile/source rig identity mismatch: '+key)
    if (profile['sourceRig'].get('action') != RIG_ACTION
            or profile['sourceProvenance']['evaluatedRigSha256'] != sha(rig_raw)):
        raise ValueError('Officer fresh61 source provenance changed')
    contacts = json.loads(read('art/weapons/w201/contacts.json'))['weapons'][WEAPON]
    if any(profile['contacts'][side] != contacts[side] for side in ('right','left')):
        raise ValueError('Officer canonical idle grip changed without geometry reason')
    # Canonical item fallback leaves remain unchanged, including ADS/inspect.
    # Count their inherited geometry too rather than assuming reload is largest.
    def resolve(key, ancestors=()):
        if not key.startswith('destiny:') or key in ancestors:
            raise ValueError('Unsupported/cyclic canonical parent: '+key)
        model = json.loads(read(A/'models'/(key.split(':',1)[1]+'.json')))
        parent = model.get('parent','')
        base = resolve(parent,ancestors+(key,)) if parent.startswith('destiny:') else {}
        return {**base,**model}
    fallback_counts = {}
    def collect(node):
        if isinstance(node,dict):
            if node.get('type') == 'minecraft:model':
                key = node['model']
                fallback_counts[key] = len(resolve(key).get('elements',[]))
            for value in node.values():
                collect(value)
        elif isinstance(node,list):
            for value in node:
                collect(value)
    collect(item['model'])
    counts = {part:len(geometry['elements']) for part,geometry in geometries.items()}
    weapon_count = sum(counts.values())
    budget = max(weapon_count,max(fallback_counts.values(),default=0))+ARMS_RESERVE
    if budget > 1000:
        raise ValueError('Officer geometry plus ordinary four-arm surfaces exceeds1000')
    output = {}
    allowed = expected_output_paths()
    def emit(path,value):
        if path not in allowed:
            raise ValueError('Output outside W221 Officer namespace')
        output[root/path] = encode(value)
    for part in PARTS:
        emit(A/f'models/{KEY}_{part}.json',geometries[part])
    entries = []
    for frame in range(SAMPLES):
        p = frame/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{frame:02}_{part}_{grip}.json',{
                    'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,p,part,grip)})
        def composite(grip):
            return {'type':'minecraft:composite','models':[
                {'type':'minecraft:model','model':f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in PARTS]}
        model = copy.deepcopy(item['model']) if frame in (0,INTERVALS) else {
            'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,
            'on_true':composite('twohand'),'on_false':composite('native')}
        entries.append({'threshold':float32(p),'model':model})
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {
        'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':list(FP),'model':{
            'type':'minecraft:select','property':'minecraft:custom_model_data','index':0,
            'cases':[{'when':['ads','inspect'],'model':copy.deepcopy(item['model'])}],
            'fallback':{'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data',
                'index':1,'entries':entries,'fallback':copy.deepcopy(item['model'])}}}],
        'fallback':copy.deepcopy(item['model'])}
    emit(A/f'items/{KEY}.json',wrapper)
    def label(path):
        # Scratch overrides change where bytes are read, never durable identity.
        return input_labels.get(path, str(path.relative_to(root))
                                if path.is_relative_to(root) else str(path))
    emit(MANIFEST,{
        'schemaVersion':1,'stage':'W221','weapon':WEAPON,
        'generator':str(GENERATOR),'generatorSha256':sha(generator_raw),
        'profileSha256':sha(profile_raw),'itemModel':'destiny:'+KEY,
        'frames':SAMPLES,'intervals':INTERVALS,'banks':['reload'],
        'progressFloatIndex':1,'gripFlagIndex':0,'firstPersonContexts':list(FP),
        'thresholdEncoding':'IEEE754 float32(i/60), matching Java runtime progress',
        'staticParts':len(PARTS),'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'generatedFiles':len(allowed),'packFiles':len(allowed)-1,
        'curve':'C1 weighted harmonic PCHIP; zero endpoints, extrema and holds',
        'mechanicalKeyframes':MECHANICAL_KEYS,'gripPivot':GRIP,'cylinderHinge':HINGE,
        'authoredMechanicalPhases':{'closed':[0,1/11],'swingOpen':[1/11,2/11],
            'openHold':[2/11,8/11],'loaderContactHold':[7/11,8/11],
            'closeReseat':[8/11,9/11],'closedRecovery':[9/11,1]},
        'wholeBodyAuthoredSweep':False,
        'sourceWeaponParentOwner':'Master shared source_weapon_display; replay exactly once',
        'gripWindow':list(GRIP_WINDOW),'contactReleasedBeforeClose':True,
        'partHint':'cylinder','policy':'cylinder','handlingHand':'left',
        'sourceGeometryPath':str(SOURCE),'sourceGeometryFileSha256':sha(source_raw),
        'sourceElements':len(source['elements']),'partElements':counts,
        'bodyElements':counts['body'],'movingElements':counts['cylinder'],
        'weaponElements':weapon_count,'triangleAdapterElements':0,'addedElements':0,
        'sourceElementsAndUVSha256':sha(encode(source['elements'])),
        'partElementsAndUVSha256':{part:sha(encode(model['elements']))
                                    for part,model in geometries.items()},
        'partitionIndices':{part:[i for i in range(len(source['elements']))
                                    if (i in MOVING)==(part=='cylinder')] for part in PARTS},
        'cylinderNames':list(CYLINDER_NAMES),'geometryAndUVPreserved':True,
        'geometryAndUVUnchanged':True,'hipEndpoints':[0,INTERVALS],
        'endpointDisplayExact':True,'fallbackModelExact':True,
        'fallback':'Exact canonical item graph for nonFP, ADS/inspect before reload, negative progress and both endpoints; both native/twohand preserved',
        'rawCanonicalFallbackElements':fallback_counts,
        'ordinaryArmReserveElements':ARMS_RESERVE,
        'reloadAssembledElements':weapon_count+ARMS_RESERVE,
        'maxAssembledElements':budget,'elementLimit':1000,
        'assembledBudgetVerified':False,'measuredAllRouteElements':None,
        'assembledBudgetBasis':'Conservative actual source and canonical leaf element counts plus448 ordinary arms; master measures materialized routes',
        'sourceMotionDataset':str(RIG),'sourceGroup':SOURCE_GROUP,
        'sourceRig':profile['sourceRig'],'sourceAction':RIG_ACTION,'rigAction':RIG_ACTION,
        'rigActionName':action['action'],'sourceActionSourceRange':[action['start'],action['end']],
        'sourceRigSamples':len(action['frames']),'sourceFullChain':True,
        'sourceCameraRecovered':False,'sourceActionWeaponExclusive':False,
        'sourceProvenance':profile['sourceProvenance'],
        'motionAuthorship':'Only W181 cylinder knots/hold/hinge are authored locally with C1 interpolation; source weapon/ordinary shoulder-elbow-wrist chains are replayed by master, not duplicated here',
        'gameplayTimingChanged':False,'mechanicsOrAudioChanged':False,
        'nativeGameplayVerified':False,'nativeVisibilityAccepted':False,
        'limitations':[
            'Master evaluated actual original Blender; worker reviewed report, fresh61 matrices and bone-only sheet. No source mesh, camera, fingerIK or perweapon selector recovery.',
            'Read-only W181 canonical121 solids have no separate cartridges/ejector. Full10-solid cylinder preserved; no invented floating/severed cartridges.',
            'Cylinder remains on its longitudinal hinge. LEFT gripWindow releases before close; sourceFullChain still replays actual source palms rather than claiming hand-to-cylinder IK.',
            'Inherited effective reloadCameraLower1.5 retained; no added camera fitting, source damping, limb stretch or support hiding.',
            '61 discrete poses do not establish continuous60fps interpolation, runtime visibility, sound listening or performance acceptance.',
            'Master FIRST feedback with sameworker review/correction and SECOND acceptance remain pending.'],
        'inputSha256':{label(path):sha(data) for path,data in raw.items()},
        'outputSha256':{str(path.relative_to(root)):sha(data) for path,data in output.items()}})
    if set(output) != {root/path for path in allowed}:
        raise ValueError('Incomplete W221 Officer output mapping')
    return output
