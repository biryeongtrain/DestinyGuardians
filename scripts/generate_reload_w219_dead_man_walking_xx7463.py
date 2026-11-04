#!/usr/bin/env python3
"""W219 Dead Man Walking: original-source body, authored whole heel magazine.

Pure stdlib; inert import. generate returns absolute Path -> bytes without writes.
Master owns original Blender evaluation, rig installation, full skin-arm assembly,
runtime routing, materialization and FIRST/SECOND native review.
"""
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
WEAPON = 'dead_man_walking_xx7463'
ART = Path('art/weapons/w219') / WEAPON
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w219_dead_man_walking_xx7463.py')
SOURCE = A / f'models/weapon_surface_w123/{WEAPON}.json'
NATIVE = A / f'models/weapon/sidearm/{WEAPON}.json'
TWOHAND = A / f'models/weapon/sidearm/{WEAPON}_twohand.json'
ITEM = A / f'items/weapon/{WEAPON}.json'
DESIGN = Path('art/weapons/w123') / WEAPON / 'design.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w219/rigs/sidearm_60848ee7.json')
KEY = f'weapon_reload_w219_{WEAPON}/{WEAPON}'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = 61
SOURCE_ACTION = '80A8A560'
ACTION_NAME = 'Armature|fp_80A8A560_reload_full|Base'
MOVING_NAMES = ('heel_core', 'heel_roundover_-1', 'heel_roundover_1')
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.08, .15, .46, .53)
C = ((0,-1,0),(0,0,1),(-1,0,0))
# Authored mesh-space fallback extraction; only this weapon's source timing.
# The original has no magazine bone/mesh. Master fits magazine translation to
# LEFT source palm during GRIP_WINDOW without altering ordinary arm lengths.
KEYS = ((0.,(0,0,0)),(.10,(0,0,0)),(.18,(0,-1.0,.42)),
        (.25,(0,-5.2,2.2)),(.32,(0,-9.5,4.0)),(.37,(0,-9.5,4.0)),
        (.45,(0,-5.2,2.2)),(.50,(0,-.7,.29)),(.53,(0,0,0)),(1.,(0,0,0)))

def encode(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()

def sha(v): return hashlib.sha256(v).hexdigest()

def float32(v): return struct.unpack('!f',struct.pack('!f',v))[0]

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

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def norm(a):return math.sqrt(dot(a,a))

def unit(a):
 n=norm(a)
 if n<1e-8:raise ValueError('Degenerate rig arm')
 return [x/n for x in a]

def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def pos(m):return [m[i][3] for i in range(3)]

def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)

def quaternion(m):
 # Largest-component extraction avoids the 180-degree trace singularity.
 v=[1+m[0][0]+m[1][1]+m[2][2],1+m[0][0]-m[1][1]-m[2][2],
    1-m[0][0]+m[1][1]-m[2][2],1-m[0][0]-m[1][1]+m[2][2]]
 i=max(range(4),key=v.__getitem__);a=math.sqrt(max(0,v[i]))/2;d=4*a
 if i==0:q=[a,(m[2][1]-m[1][2])/d,(m[0][2]-m[2][0])/d,(m[1][0]-m[0][1])/d]
 elif i==1:q=[(m[2][1]-m[1][2])/d,a,(m[0][1]+m[1][0])/d,(m[0][2]+m[2][0])/d]
 elif i==2:q=[(m[0][2]-m[2][0])/d,(m[0][1]+m[1][0])/d,a,(m[1][2]+m[2][1])/d]
 else:q=[(m[1][0]-m[0][1])/d,(m[0][2]+m[2][0])/d,(m[1][2]+m[2][1])/d,a]
 return unit(q)

def interpolate(a,b,t):
 """Linear evaluated joint position, shortest-arc quaternion rotation."""
 if t<=0:return [row[:] for row in a]
 if t>=1:return [row[:] for row in b]
 qa,qb=quaternion(a),quaternion(b);cosine=dot(qa,qb)
 if cosine<0:qb=[-x for x in qb];cosine=-cosine
 if cosine>.9995:q=unit([x+(y-x)*t for x,y in zip(qa,qb)])
 else:
  angle=math.acos(max(-1,min(1,cosine)));s=math.sin(angle)
  q=[(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/s for x,y in zip(qa,qb)]
 w,x,y,z=q;p=[a[i][3]+(b[i][3]-a[i][3])*t for i in range(3)]
 return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),p[0]],
         [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),p[1]],
         [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),p[2]],[0.,0.,0.,1.]]

def weapon_basis(joints):
 """Remove tiny exported scale/shear before inverting the weapon rotation."""
 m=joints['weapon'];x=unit([m[i][0] for i in range(3)])
 y=[m[i][1] for i in range(3)];y=unit([y[i]-x[i]*dot(y,x) for i in range(3)])
 z=unit(cross(x,y));y=cross(z,x)
 return transpose([x,y,z])

def magazine_offset(progress):
    """C1 shape-preserving Hermite; exact holds and seated recovery."""
    times = [k[0] for k in KEYS]
    if progress <= 0 or progress >= 1: return [0.,0.,0.]
    i = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[i+1]-times[i]; t = (progress-times[i])/h
    out=[]
    for axis in range(3):
        values=[k[1][axis] for k in KEYS]; slopes=tangents(times,values)
        out.append((2*t**3-3*t*t+1)*values[i]+(t**3-2*t*t+t)*h*slopes[i]
                   +(-2*t**3+3*t*t)*values[i+1]+(t**3-t*t)*h*slopes[i+1])
    return out


def source_motion(rig, frame):
    """Same original weapon-parent basis and endpoint blend as shared W205.

    This bakes source body motion into the standalone candidate. The shared
    source_weapon_display replaces this body's transform from ready, rather
    than multiplying it again, retaining only child-relative part movement.
    """
    progress=frame/INTERVALS
    rest=rig['actions'][rig['idle']]['frames'][0]['joints']
    active=rig['actions'][SOURCE_ACTION]['frames'][frame]['joints']
    weight=smooth(progress/.1)*smooth((1-progress)/.1)
    current={'weapon':interpolate(rest['weapon'],active['weapon'],weight)}
    wr=weapon_basis(rest); wt=weapon_basis(current)
    rotation=mul(mul(C,mul(transpose(wr),wt)),transpose(C))
    shift=vec(C,vec(transpose(wr),sub(pos(current['weapon']),pos(rest['weapon']))))
    return rotation,shift


def pose_display(original,twohand,rig,frame,part,grip):
    if part not in PARTS or grip not in GRIPS: raise ValueError((part,grip))
    ready=original if grip=='native' else twohand
    if frame in (0,INTERVALS): return copy.deepcopy(ready)
    rotation,shift=source_motion(rig,frame)
    offset=magazine_offset(frame/INTERVALS) if part=='magazine' else [0,0,0]
    display=copy.deepcopy(ready)
    for context in FP:
        base=xyz(ready[context]['rotation']); scale=ready[context]['scale']
        if len(set(scale))!=1 or scale!=original[context]['scale']:
            raise ValueError('Expected equal uniform native/twohand scale')
        active=mul(base,rotation)
        displacement=add(vec(base,[32*scale[0]*v for v in shift]),
                         vec(active,[scale[0]*v for v in offset]))
        display[context]['rotation']=euler(active)
        display[context]['translation']=[round(v,9) for v in add(ready[context]['translation'],displacement)]
    return display


def internal_shaft(source):
    """One dark shaft recessed inside filled_grip in its existing local frame.

    Canonical grip remains fixed. This narrow cuboid meets heel_core at its
    bottom and provides the detached magazine body, with existing dark UVs.
    Dimensions/material allocation are authored; no hidden mesh was recovered.
    """
    by_name={e['name']:e for e in source['elements']}
    shaft=copy.deepcopy(by_name['filled_grip'])
    shaft.update(name='authored_internal_magazine_shaft',
                 **{'from':[7.45,7.0,6.35],'to':[8.55,11.2,7.55]})
    shaft['faces']=copy.deepcopy(by_name['rear_grip_bevel_-1']['faces'])
    return shaft


def partition(source):
    by_name={e['name']:e for e in source['elements']}
    if any(name not in by_name for name in MOVING_NAMES):
        raise ValueError('Whole heel/baseplate semantic parts missing')
    result={}
    for part in PARTS:
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements']
                           if (e['name'] in MOVING_NAMES)==(part=='magazine')]
        if part=='magazine': model['elements'].append(internal_shaft(source))
        result[part]=model
    return result


def expected_output_paths():
    return ({A/f'models/{KEY}_{part}.json' for part in PARTS}
            | {A/f'models/{KEY}_{i:02}_{part}_{grip}.json'
               for i in range(SAMPLES) for part in PARTS for grip in GRIPS}
            | {A/f'items/{KEY}.json', MANIFEST})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path,bytes]:
    """Read current inputs; return bytes only. Explicit paths permit scratch prep.

    Installed default always reads the master-owned W219 rig under root.
    No import/run of shared or legacy generators and no pinned shared hashes.
    """
    root=Path(root).resolve()
    inputs=[SOURCE,NATIVE,TWOHAND,ITEM,DESIGN,CONTACTS,FRAMING,
            A/f'textures/item/weapon/w123/{WEAPON}.png',
            Path('src/main/resources/destiny/weapons/w46-timing.json'),
            Path('src/main/resources/destiny/sounds/w63-reload.json')]
    raw={path:(root/path).read_bytes() for path in inputs}
    raw[PROFILE]=Path(profile_path or root/PROFILE).read_bytes()
    raw[RIG]=Path(rig_path or root/RIG).read_bytes()
    raw[GENERATOR]=Path(__file__).read_bytes()
    source=json.loads(raw[SOURCE]); twohand=json.loads(raw[TWOHAND])['display']
    item=json.loads(raw[ITEM]); profile=json.loads(raw[PROFILE]); rig=json.loads(raw[RIG])
    design=json.loads(raw[DESIGN]); contacts=json.loads(raw[CONTACTS])['weapons'][WEAPON]
    if (profile.get('schemaVersion')!=1 or profile.get('stage')!='W219'
            or profile.get('weapon')!=WEAPON or profile.get('sourceAction')!=SOURCE_ACTION):
        raise ValueError('W219 weapon profile required')
    reload=profile['contacts']['reload']
    if any(reload.get(k)!=v for k,v in {'rigAction':SOURCE_ACTION,'hand':'left',
            'partHint':'magazine','policy':'magazine','gripWindow':list(GRIP_WINDOW)}.items()):
        raise ValueError('Explicit source LEFT magazine contact/window required')
    if any(profile['contacts'][side]!=contacts[side] for side in ('right','left')):
        raise ValueError('Preserve current mesh rest contacts')
    if any(reload[k]!=contacts['reload'][k] for k in ('contact','rotation')):
        raise ValueError('Preserve existing authored magazine contact')
    cfg=json.loads(raw[FRAMING])
    effective={**cfg['families'].get('sidearm',cfg['default']),
               **cfg.get('weapons',{}).get(WEAPON,{})}
    effective.update(sourceFullChain=True,keepMeshSupport=True,hideSupportAtRest=False)
    if profile['framing']!=effective: raise ValueError('Current effective framing changed')
    action=rig['actions'][SOURCE_ACTION]
    joints={'weapon','leftShoulder','leftElbow','leftWrist','rightShoulder','rightElbow','rightWrist'}
    if (rig.get('group')!='sidearm_60848ee7' or rig.get('fallback') is not False
            or WEAPON not in rig['weapons'] or rig.get('cameraExported') is not False
            or action['action']!=ACTION_NAME or (action['start'],action['end'])!=(1.,67.)
            or len(action['frames'])!=SAMPLES
            or any(f['progress']!=i/INTERVALS or abs(f['frame']-(1+66*i/INTERVALS))>1e-9
                   or not joints<=f['joints'].keys() for i,f in enumerate(action['frames']))):
        raise ValueError('Original W219 source61 full shoulder chains required')
    for key in ('sourceBlendSha256','sourceMapSha256','boneMapSha256'):
        if rig[key]!=profile['sourceRig'][key]: raise ValueError('Original source provenance changed: '+key)
    semantic={p['geometry']['name']:p for p in design['parts']}
    if any(semantic[n]['motif']!='heel' for n in MOVING_NAMES):
        raise ValueError('Whole heel/baseplate semantic evidence changed')
    geometries=partition(source)
    counts={part:len(model['elements']) for part,model in geometries.items()}
    canonical_count=len(json.loads(raw[NATIVE])['elements'])
    estimate=max(sum(counts.values()),canonical_count)+ARM_ELEMENT_RESERVE
    if estimate>1000: raise ValueError('Actual alternative weapon+448 arms budget exceeds1000')
    output={};allowed=expected_output_paths()
    def emit(path,value):
        if path not in allowed: raise ValueError('Output outside exclusive W219 weapon namespace')
        output[root/path]=encode(value)
    for part,model in geometries.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for frame in range(SAMPLES):
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{frame:02}_{part}_{grip}.json',{
                    'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,rig,frame,part,grip)})
        def composite(grip):
            return {'type':'minecraft:composite','models':[
                {'type':'minecraft:model','model':f'destiny:{KEY}_{frame:02}_{part}_{grip}'} for part in PARTS]}
        model=copy.deepcopy(item['model']) if frame in (0,INTERVALS) else {
            'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,
            'on_true':composite('twohand'),'on_false':composite('native')}
        entries.append({'threshold':float32(frame/INTERVALS),'model':model})
    canonical=copy.deepcopy(item['model'])
    if (canonical.get('type')!='minecraft:select'
            or canonical.get('property')!='minecraft:custom_model_data'
            or canonical.get('index',0)!=0
            or [c['when'] for c in canonical['cases']]!=['ads','inspect']):
        raise ValueError('Expected canonical ADS/inspect guards')
    # The exact1 canonical entry also handles every positive overshoot.
    dispatch={'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data',
              'index':1,'entries':entries,'fallback':copy.deepcopy(canonical)}
    guard=copy.deepcopy(canonical);guard['fallback']=dispatch
    wrapper=copy.deepcopy(item)
    wrapper['model']={'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':list(FP),'model':guard}],'fallback':copy.deepcopy(canonical)}
    emit(A/f'items/{KEY}.json',wrapper)
    emit(MANIFEST,{
        'schemaVersion':1,'stage':'W219','weapon':WEAPON,'generator':str(GENERATOR),
        'generatorSha256':sha(raw[GENERATOR]),'itemModel':'destiny:'+KEY,
        'frames':SAMPLES,'intervals':INTERVALS,'progressFloatIndex':1,'gripFlagIndex':0,
        'thresholdEncoding':'exact float32(i/60); exact1 canonical entry also handles overshoot',
        'firstPersonContexts':list(FP),'hipEndpoints':[0,60],
        'endpointDisplayExact':True,'fallbackModelExact':True,
        'sourceGeometryPath':str(SOURCE),'sourceElements':len(source['elements']),
        'partElements':counts,'bodyElements':counts['body'],'movingElements':counts['magazine'],
        'magazineElements':counts['magazine'],'weaponElements':sum(counts.values()),
        'canonicalWeaponElements':canonical_count,'selectedSurfaceElements':len(source['elements']),
        'addedElements':1,'triangleAdapterElements':0,'ordinaryArmElementReserve':448,
        'maxAssembledElements':estimate,'elementLimit':1000,
        'assembledBudgetVerified':False,'measuredAllRouteElements':None,
        'budgetBasis':'Simultaneous body+whole magazine+448 classic arm surfaces; raw canonical and reload are alternatives, never summed. Master measures final composed ADS/inspect routes.',
        'movingNames':list(MOVING_NAMES),'movingIndices':[i for i,e in enumerate(source['elements']) if e['name'] in MOVING_NAMES],
        'geometryPolicy':'Keep all canonical solids/UVs intact; fixed grip, straps, panels, latch and haunch. Move all three heel/baseplate solids plus one authored recessed shaft.',
        'reloadOnlyGeometry':{'elements':[internal_shaft(source)],'authored':True},
        'magazineAnchor':[8.,6.96,7.75],'keyframes':KEYS,'gripWindow':list(GRIP_WINDOW),
        'magazineSeatedProgress':.53,'partHint':'magazine','policy':'magazine','reloadHand':'left',
        'sourceAction':SOURCE_ACTION,'rigAction':SOURCE_ACTION,'rigActionName':ACTION_NAME,
        'sourceGroup':rig['group'],'sourceRigPath':str(RIG),'sourceRigSamples':SAMPLES,
        'sourceActionSourceRange':[1.,67.],'sourceBlend':rig['sourceBlend'],
        'sourceFullChain':True,'sourceCameraRecovered':False,'fingerIKRecovered':False,
        'originalSourceSha256':{k:rig[k] for k in ('sourceBlendSha256','sourceMapSha256','boneMapSha256')},
        'motionAuthorship':'Original own weapon-bone replay with shared source-parent basis/32 scale and .1 endpoint rest crossfade. Authored C1 withdrawal/reseat in source-timed envelope; shared builder attaches magazine to LEFT source palm and releases by.53. No other-weapon trajectory.',
        'sharedIntegration':'Master W219 rig/action/profile loading required. source_weapon_display replaces baked body from ready and retains child-relative offsets; never multiply source body twice. Preserve source shoulders/elbows/wrists, ordinary fingerless full arms and no axis/length/visibility compensation.',
        'sourceReviewEvidence':profile.get('evidence',[]),
        'canonicalGeometryAndUVPreserved':True,'gameplayTimingChanged':False,
        'mechanicsOrAudioChanged':False,'nativeGameplayVerified':False,'nativeVisibilityAccepted':False,
        'staticParts':2,'parentDisplayChildren':244,'packFiles':len(output),
        'totalReturnedFiles':len(allowed),
        'limitations':['Master evaluated original Blender; worker reviewed report, fresh61 matrices and actual bone-only sheet, not independent Blender evaluation.',
            'ARMATURE only; magazine construction, contacts, exchange and.53 seat/release are authored. No recovered weapon mesh/camera/finger IK.',
            'FIRST actual native PNG feedback and same-worker review/correction or justified nochange pending; SECOND native acceptance pending.',
            '61 poses/60 intervals do not establish vanilla continuous60fps interpolation.'],
        'inputSha256':{str(k):sha(v) for k,v in raw.items()},
        'outputSha256':{str(k.relative_to(root)):sha(v) for k,v in output.items()}})
    if set(output)!={root/p for p in allowed}: raise ValueError('Incomplete W219 output mapping')
    return output
