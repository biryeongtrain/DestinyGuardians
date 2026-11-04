#!/usr/bin/env python3
"""W215 Duke Mk.44: evaluated source body and unchanged authored cylinder keys.

Pure stdlib. Import and generate(root=ROOT) do not write files or caches.
Master materializes the returned absolute Path -> bytes mapping, binds the fresh
61-sample full arm chain, and owns FIRST feedback and SECOND acceptance.
No recovered cylinder mesh, camera, finger IK or gameplay event is claimed.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w215/duke_mk_44')
KEY = 'weapon_reload_w215_duke_mk_44/duke_mk_44'
SOURCE = A/'models/weapon_surface_w123/duke_mk_44.json'
TWOHAND = A/'models/weapon/hand_cannon/duke_mk_44_twohand.json'
ITEM = A/'items/weapon/duke_mk_44.json'
TEXTURE = A/'textures/item/weapon/w123/duke_mk_44.png'
GENERATOR = Path('scripts/generate_reload_w215_duke_mk_44.py')
PROFILE = ART/'profile.json'
MANIFEST = ART/'manifest.json'
RIG = Path('art/weapons/w205/rigs/hand_cannon_cedb29ae.json')
RIG_ACTION = '80A8A53D'
SOURCE_GROUP = 'hand_cannon_cedb29ae'
SOURCE_BLEND_SHA256 = 'bde226ffa88f30cbcc60a3d1b4c36548f01fe3808e6e8c848cad36e43d93f04d'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'moving')
INTERVALS = 60
SAMPLES = INTERVALS + 1
# Existing W127 semantic-r3-blue-photo solids in the W123 namespace.
MOVING = tuple(range(78,147))
NAMES = tuple([f'Cylinder_shell_{i}' for i in range(12)] +
              [n for i in range(6) for n in ([f'Chamber_{i}_{j}' for j in range(8)]+[f'Cylinder_web_{i}'])] +
              ['Cylinder_spindle','Yoke_vertical','Yoke_arm'])
FIXED_FRAME = tuple(range(8,19))
FIXED_NAMES = ('Top_strap','Top_crown','Top_chamfer_-1','Slot_shadow_-1',
               'Top_chamfer_1','Slot_shadow_1','Breech_rear','Breech_crown',
               'Cylinder_bottom_rail','Breech_to_grip','Cylinder_front_mount')
GRIP = (8,9.525,7.875)
HINGE = (8,10.2,5.17)
SOURCE_SHA256 = '8ce48917d727b8bc444481e8e38b1477db4d4725e8e3621d122708cce0a4fb79'
BODY_BONE = '4A0810C4'
BASIS = [[0,-1,0],[0,0,1],[-1,0,0]]
MECHANICAL_KEYS = ((0.,0),(.10,0),(.24,80),(.34,80),(.49,80),
                   (.60,80),(.70,80),(.82,80),(.92,0),(1.,0))
GRIP_WINDOW = (.05, .20, .70, .82)  # Release across final open hold; clear before closure.


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

def quaternion(r):
    """Stable matrix -> unit wxyz, including the source's rotations past 180."""
    tr = sum(r[i][i] for i in range(3))
    if tr > 0:
        t = math.sqrt(tr+1)*2
        q = [t/4, (r[2][1]-r[1][2])/t, (r[0][2]-r[2][0])/t, (r[1][0]-r[0][1])/t]
    else:
        i = max(range(3), key=lambda k:r[k][k]); j=(i+1)%3; k=(i+2)%3
        t = math.sqrt(1+r[i][i]-r[j][j]-r[k][k])*2
        q = [(r[k][j]-r[j][k])/t, 0, 0, 0]
        q[i+1]=t/4; q[j+1]=(r[j][i]+r[i][j])/t; q[k+1]=(r[k][i]+r[i][k])/t
    n = math.sqrt(sum(v*v for v in q))
    return [v/n for v in q]

def slerp(a, b, t):
    dot = sum(x*y for x,y in zip(a,b))
    if dot < 0:
        b = [-v for v in b]; dot = -dot
    dot = max(-1, min(1, dot))
    if dot > .9995:
        q = [x+(y-x)*t for x,y in zip(a,b)]
    else:
        angle = math.acos(dot)
        q = [(math.sin((1-t)*angle)*x+math.sin(t*angle)*y)/math.sin(angle) for x,y in zip(a,b)]
    n = math.sqrt(sum(v*v for v in q))
    w,x,y,z = [v/n for v in q]
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]

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
    """Preserve all ten authored knots and the exact .24..82 open hold."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Reload progress must be finite and within 0..1')
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
    """Require master's fresh original61 cache, never evaluate/import old code."""
    rig = json.loads((Path(root)/RIG).read_bytes() if raw is None else raw)
    action = rig['actions'][RIG_ACTION]
    frames = action['frames']
    if (rig['group'] != SOURCE_GROUP or rig.get('cameraExported') is not False
            or rig.get('sourceBlendSha256') != SOURCE_BLEND_SHA256
            or rig.get('names',{}).get('weapon') != BODY_BONE
            or not rig.get('w215Source61')
            or rig['w215Source61'].get('reloadSamples') != SAMPLES
            or action['action'] != 'Armature|fp_80A8A53D_reload_full|Base.001'
            or [action['start'],action['end']] != [1,127]
            or len(frames) != SAMPLES):
        raise ValueError('Master W215 original61 Duke full-chain rig is required')
    required = {'weapon','leftShoulder','leftElbow','leftWrist',
                'rightShoulder','rightElbow','rightWrist'}
    for i,frame in enumerate(frames):
        if (frame['progress'] != i/INTERVALS
                or abs(frame['frame']-(1+126*i/INTERVALS)) > 1e-7
                or not required <= frame['joints'].keys()):
            raise ValueError('Incomplete W215 Duke source timeline/chain')
        for matrix in frame['joints'].values():
            rigid(matrix)
    return rig


def sample(p,motion=None):
    """Original weapon FK plus the W169 authored hinge, not source arm filtering.

    Keep W199's 32-unit/basis/grip calibration and terminal 5% body recovery.
    The master full-chain pass replaces this presentation body with its shared
    source weapon parent; the cylinder-local affine survives that replacement.
    Arms are neither generated nor smoothed/attenuated by this module.
    """
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError('Reload progress must be finite and within 0..1')
    motion = load_motion() if motion is None else motion
    frames = motion['actions'][RIG_ACTION]['frames']
    n = p*INTERVALS
    i = min(int(n),INTERVALS-1)
    t = n-i
    ra,pa = rigid(frames[i]['joints']['weapon'])
    rb,pb = rigid(frames[i+1]['joints']['weapon'])
    r0,p0 = rigid(frames[0]['joints']['weapon'])
    r = slerp(quaternion(ra),quaternion(rb),t)
    position = add(pa,[(b-a)*t for a,b in zip(pa,pb)])
    body = mul(BASIS,mul(mul(transpose(r0),r),transpose(BASIS)))
    shift = [32*v for v in vec(BASIS,vec(transpose(r0),sub(position,p0)))]
    if p > .95:
        blend = (p-.95)/.05
        blend = blend*blend*(3-2*blend)
        body = slerp(quaternion(body),[1,0,0,0],blend)
        shift = [v*(1-blend) for v in shift]
    if p in (0,1):
        body,shift = xyz((0,0,0)),[0,0,0]
    return body,shift,[0,0,cylinder_angle(p)]


def pose_display(original,twohand,p,part,grip,motion=None):
    if part not in PARTS or grip not in ('native','twohand'):
        raise ValueError('Unknown Duke part or grip')
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    body,shift,cylinder=sample(p,motion)
    component=xyz(cylinder if part=='moving' else (0,0,0))
    h=sub(GRIP,(8,8,8));c=sub(HINGE,(8,8,8))
    # Independent cylinder rotation around its crane, then whole gun around grip.
    local=add(sub(h,vec(body,h)),vec(body,sub(c,vec(component,c))))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if len(set(scale))!=1: raise ValueError('Rigid motion requires uniform FP scale')
        if twohand[context]['scale']!=scale: raise ValueError('Grip scale mismatch')
        rotation=mul(mul(base,body),component)
        position=add(idle['translation'],vec(base,[scale[0]*v for v in add(local,shift)]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths = {A/f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in ('native','twohand'))
    return paths | {A/f'items/{KEY}.json',MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read inputs once; return deterministic absolute paths without any writes."""
    root = Path(root).resolve()
    inputs = [SOURCE,TWOHAND,ITEM,TEXTURE,GENERATOR,PROFILE,RIG,
              Path('art/weapons/w123/duke_mk_44/design.json'),
              Path('art/weapons/w123/duke_mk_44/manifest.json'),
              Path('src/main/resources/weapon_surface_w123/manifest.json'),
              Path('scripts/generate_reload_w169_duke_mk_44.py'),
              Path('art/weapons/w169/duke_mk_44/motion-reference.json'),
              Path('art/weapons/w201/contacts.json'),
              Path('art/weapons/w205/first-person-framing.json')]
    raw = {p:(root/p).read_bytes() for p in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    motion = load_motion(root,raw[RIG])
    action = motion['actions'][RIG_ACTION]
    elements = source['elements']
    if sha(raw[SOURCE]) != SOURCE_SHA256:
        raise ValueError('Canonical W127 Duke geometry/UV changed; re-audit')
    if (len(elements) != 147 or [elements[i]['name'] for i in MOVING] != list(NAMES)
            or [elements[i]['name'] for i in FIXED_FRAME] != list(FIXED_NAMES)):
        raise ValueError('Duke cylinder/yoke or fixed-frame partition changed')
    design = json.loads(raw[Path('art/weapons/w123/duke_mk_44/design.json')])
    if [p['geometry'] for p in design['parts']['body']+design['parts']['cylinder']] != elements:
        raise ValueError('Duke semantic solids/UV drift')
    rules = json.loads(raw[Path('src/main/resources/weapon_surface_w123/manifest.json')])['targets']
    rule = next(r for r in rules if r['path'] == 'assets/destiny/models/weapon/hand_cannon/duke_mk_44.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/duke_mk_44.json'
            or rule['replacementSha256'] != SOURCE_SHA256):
        raise ValueError('Selected canonical Duke source mapping changed')
    reload = profile['contacts']['reload']
    if (profile.get('schemaVersion') != 1 or profile.get('weapon') != 'duke_mk_44'
            or profile.get('sourceAction') != RIG_ACTION
            or reload.get('rigAction') != RIG_ACTION
            or reload.get('partHint') != 'moving' or reload.get('policy') != 'cylinder'
            or reload.get('gripWindow') != list(GRIP_WINDOW)
            or profile['framing'].get('sourceFullChain') is not True
            or profile['framing'].get('keepMeshSupport') is not True
            or profile['framing'].get('hideSupportAtRest') is not False):
        raise ValueError('W215 Duke source-chain/cylinder profile changed')
    if profile['sourceProvenance']['evaluatedRigSha256'] != sha(raw[RIG]):
        raise ValueError('Fresh original61 rig differs from reviewed W215 source')
    # Resolve raw canonical fallback geometry as a conservative budget bound.
    # Effective W123 replacement is 147; the unchanged raw leaves are 232.
    def resolve(key, ancestors=()):
        if not key.startswith('destiny:') or key in ancestors:
            raise ValueError('Unsupported canonical model parent: '+key)
        path = A/'models'/(key.split(':',1)[1]+'.json')
        if path not in raw:
            raw[path] = (root/path).read_bytes()
        model = json.loads(raw[path])
        parent = model.get('parent','')
        base = resolve(parent,ancestors+(key,)) if parent.startswith('destiny:') else {}
        return {**base,**model}
    counts_fallback = {}
    def collect(node):
        if isinstance(node,dict):
            if node.get('type') == 'minecraft:model':
                key = node['model']
                counts_fallback[key] = len(resolve(key).get('elements',[]))
            for value in node.values():
                collect(value)
        elif isinstance(node,list):
            for value in node:
                collect(value)
    collect(item['model'])
    budget = max(len(elements),max(counts_fallback.values(),default=0))+448
    if budget > 1000:
        raise ValueError('Duke weapon + four ordinary classic arm surfaces exceed 1000')
    geometries = {}
    for part in PARTS:
        geo = {k:copy.deepcopy(v) for k,v in source.items() if k not in ('elements','display')}
        geo['elements'] = [copy.deepcopy(e) for i,e in enumerate(elements)
                           if (i in MOVING) == (part == 'moving')]
        geometries[part] = geo
    output = {}
    allowed = expected_output_paths()
    def emit(path,value):
        if path not in allowed:
            raise ValueError('Output outside W215 Duke namespace')
        output[root/path] = encode(value)
    for part in PARTS:
        emit(A/f'models/{KEY}_{part}.json',geometries[part])
    entries = []
    for frame in range(SAMPLES):
        p = frame/INTERVALS
        for part in PARTS:
            for grip in ('native','twohand'):
                emit(A/f'models/{KEY}_{frame:02}_{part}_{grip}.json',{
                    'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,p,part,grip,motion)})
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
    counts = {part:len(geo['elements']) for part,geo in geometries.items()}
    reference = json.loads(raw[Path('art/weapons/w169/duke_mk_44/motion-reference.json')])
    emit(MANIFEST,{
        'schemaVersion':1,'stage':'W215','weapon':'duke_mk_44',
        'generator':str(GENERATOR),'generatorSha256':sha(raw[GENERATOR]),
        'itemModel':'destiny:'+KEY,'frames':SAMPLES,'intervals':INTERVALS,
        'progressFloatIndex':1,'gripFlagIndex':0,
        'thresholdEncoding':'IEEE754 float32(i/60), matching Java float runtime progress',
        'firstPersonContexts':list(FP),'staticParts':2,'parentDisplayChildren':244,
        'generatedFiles':len(allowed),'packFiles':len(allowed)-1,
        'curve':'C1 weighted harmonic PCHIP on authored cylinder knots; zero endpoints/holds/extrema',
        'mechanicalKeyframes':MECHANICAL_KEYS,'gripPivot':GRIP,'cylinderHinge':HINGE,
        'authoredMechanicalPhases':{'closed':[0,.10],'openBesideFrame':[.10,.24],
            'openHold':[.24,.82],'loaderContactHold':[.70,.82],
            'closeReseat':[.82,.92],'recover':[.92,1]},
        'gripWindow':list(GRIP_WINDOW),'cylinderClosedProgress':.92,
        'partitionRationale':'Exact W127 semantic split: body0..77 fixed; shell, six chamber bores/webs, spindle and two yoke links78..146 move as one attached hinge assembly. No extra loader, cases or cartridges.',
        'movingIndices':list(MOVING),'movingNames':list(NAMES),
        'fixedFrameIndices':list(FIXED_FRAME),'fixedFrameNames':list(FIXED_NAMES),
        'sourceGeometryPath':str(SOURCE),'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'sourceElements':len(elements),'partElements':counts,'weaponElements':sum(counts.values()),
        'sourceElementsAndUVSha256':sha(encode(elements)),
        'partElementsAndUVSha256':{part:sha(encode(geo['elements'])) for part,geo in geometries.items()},
        'geometryAndUVPreserved':True,'geometryAndUVUnchanged':True,
        'hipEndpoints':[0,INTERVALS],'endpointDisplayExact':True,'fallbackModelExact':True,
        'fallback':'Exact canonical graph for negative progress, non-FP, ADS/inspect and both endpoints; native/twohand selector preserved.',
        'rawCanonicalFallbackElements':counts_fallback,
        'bothClassicForearmElements':224,'bothClassicUpperArmElements':224,
        'maxAssembledElements':budget,'reloadAssembledElements':len(elements)+448,
        'elementLimit':1000,'assembledBudgetVerified':False,'measuredAllRouteElements':None,
        'assembledBudgetBasis':'Conservative static raw canonical leaf maximum plus four112-surface classic arms. Master must measure all materialized routes; no native route certification.',
        'sourceMotionDataset':str(RIG),'sourceGroup':SOURCE_GROUP,
        'sourceAction':RIG_ACTION,'rigAction':RIG_ACTION,'rigActionName':action['action'],
        'sourceActionSourceRange':[action['start'],action['end']],
        'sourceRigSamples':len(action['frames']),'sourceFullChain':True,
        'sourceActionWeaponExclusive':False,'sourceCameraRecovered':False,
        'sourceProvenance':profile['sourceProvenance'],
        'sourceReviewEvidence':profile.get('evidence',[]),
        'partHint':'moving','policy':'cylinder',
        'sourceBodyCalibration':{'sourceRootToModelBasis':BASIS,'neutralSourceFrame':1,
            'modelUnitsPerSourceUnit':32,'targetAnchor':GRIP,'terminalBodyRecovery':[.95,1]},
        'motionAuthorship':'W169 cylinder knots/holds and affine unchanged; W214 PCHIP replaces per-key easing. Body uses fresh original61 samples with prior W199 calibration. Master replaces this body with the shared source weapon parent and preserves its cylinder-local affine; ordinary source-length arms are master-owned.',
        'sourceObservedSeconds':reference['selectedSeconds'],'reference':reference['url'],
        'timingPolicy':'Original source1..127 at30fps maps to normalized runtime progress; source4.2s and partial-reload footage2.4s do not override gameplay duration, ammo credit or audio.',
        'gameplayTimingChanged':False,'mechanicsOrAudioChanged':False,
        'nativeGameplayVerified':False,'nativeVisibilityAccepted':False,
        'limitations':[
            'Master evaluated original Blender armature; worker read fresh report/61 matrices and viewed the bone-only sheet. No source mesh/camera/IK recovered.',
            'Cylinder/yoke motion is authored; fresh shoulder/elbow/wrist evidence is not a recovered cylinder trajectory or loader event.',
            'Contact release.70..82 is an authored legacy-envelope candidate. Full-chain palms replay source travel; cylinder policy never hand-translates the attached part.',
            'Inherited effective framing includes existing reloadCameraLower1.5; no new depth/lift, arm stretch, limb-length smoothing or support hiding is added.',
            '61 poses do not establish continuous60fps interpolation or native visual/performance acceptance.',
            'FIRST Vision feedback and worker review/correction, then SECOND acceptance remain pending.'],
        'inputSha256':{str(p):sha(b) for p,b in raw.items()},
        'outputSha256':{str(p.relative_to(root)):sha(b) for p,b in output.items()}})
    if set(output) != {root/p for p in allowed}:
        raise ValueError('Incomplete W215 Duke output mapping')
    return output
