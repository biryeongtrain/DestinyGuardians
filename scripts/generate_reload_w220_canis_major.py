#!/usr/bin/env python3
"""Pure W220 Canis Major candidate; master materializes and owns native QA.

Original full-chain action104 supplies carrier and arms. Drum/cradle/latch
motion is authored calibration from Canis geometry, not recovered mesh motion.
Import and generate never write. Only Python stdlib is used.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w220/canis_major')
PROFILE, MANIFEST = ART/'profile.json', ART/'manifest.json'
GENERATOR = Path('scripts/generate_reload_w220_canis_major.py')
SOURCE = A/'models/weapon_surface_w123/canis_major.json'
TWOHAND = A/'models/weapon/heavy_grenade_launcher/canis_major_twohand.json'
ITEM = A/'items/weapon/canis_major.json'
TEXTURE = A/'textures/item/weapon/w123/canis_major.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w220/rigs/heavy_grenade_launcher_796e9ebf.json')
KEY = 'weapon_reload_w220_canis_major/canis_major'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine', 'cradle', 'latch')
GRIPS = ('native', 'twohand')
INTERVALS, SAMPLES = 60, 61
SOURCE_ACTION = '80A8A104'
ACTION_NAME = 'Armature|fp_80A8A104_reload_full|Base'
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.20, .25, .50, .58)
SEATED = .62
GRIP = (8., 8.66, 7.8)  # own pistol_grip rotation origin, not a body animation
MAGAZINE_ANCHOR = (8.84, 10.15, 1.815)  # own drum_core origin
CRADLE_PIVOT = (8.84, 9.42, -1.34)  # midpoint of fixed pivots65/67
LATCH_PIVOT = (8., 13.68, 13.53)  # fixed rear_latch_root100 center
PART_INDICES = {
    'magazine': tuple(range(36, 64)),
    'cradle': (64, 66, 68, 69, 70, 71),
    'latch': (99,),
}
PART_INDICES['body'] = tuple(i for i in range(101)
                            if all(i not in v for v in PART_INDICES.values()))

# p, drum translation, drum XYZ rotation, cradle X angle, latch X angle.
# Body stays canonical: master applies original source weapon motion once.
# Unlatch/open precede extraction; a held open cradle permits lateral exchange;
# palm attachment releases before seat, then cradle and latch close separately.
KEYS = (
    (0., (0,0,0), (0,0,0), 0, 0),
    (.06, (0,0,0), (0,0,0), 0, -32),
    (.10, (0,0,0), (0,0,0), 18, -32),
    (.16, (0,0,0), (0,0,0), 85, -32),
    (.19, (0,-2.9,0), (0,0,0), 85, -32),
    (.23, (0,-2.9,.9), (0,0,0), 85, -32),
    (.30, (-8,-2.9,.9), (0,0,12), 85, -32),
    (.40, (-8,-2.9,.9), (0,0,12), 85, -32),
    (.50, (-5.2,-2.9,.9), (0,0,6), 85, -32),
    (.58, (0,-2.9,.9), (0,0,0), 85, -32),
    (.60, (0,-2.9,0), (0,0,0), 85, -32),
    (.62, (0,0,0), (0,0,0), 85, -32),
    (.66, (0,0,0), (0,0,0), 85, -32),
    (.75, (0,0,0), (0,0,0), 0, -32),
    (.79, (0,0,0), (0,0,0), 0, -32),
    (.84, (0,0,0), (0,0,0), 0, 0),
    (1., (0,0,0), (0,0,0), 0, 0),
)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(raw): return hashlib.sha256(raw).hexdigest()


def float32(value): return struct.unpack('!f', struct.pack('!f', value))[0]


def tangents(times, values):
    """C1 PCHIP with zero endpoint, hold and extremum derivatives."""
    steps = [b-a for a,b in zip(times,times[1:])]
    secants = [(b-a)/h for a,b,h in zip(values,values[1:],steps)]
    slopes = [0.] * len(times)
    for i in range(1,len(times)-1):
        before, after = secants[i-1], secants[i]
        if before*after > 0:
            w1, w2 = 2*steps[i]+steps[i-1], steps[i]+2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before+w2/after)
    return slopes


def sample(progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Reload progress must be finite and within0..1')
    times = [key[0] for key in KEYS]
    def channel(values):
        if progress in times:
            return values[times.index(progress)]
        i = next(i for i in range(len(times)-1) if progress < times[i+1])
        if values[i] == values[i+1]: return values[i]
        slopes = tangents(times,values)
        h = times[i+1]-times[i]; t = (progress-times[i])/h
        return ((2*t**3-3*t*t+1)*values[i] + (t**3-2*t*t+t)*h*slopes[i]
                + (-2*t**3+3*t*t)*values[i+1] + (t**3-t*t)*h*slopes[i+1])
    return ([channel([k[1][a] for k in KEYS]) for a in range(3)],
            [channel([k[2][a] for k in KEYS]) for a in range(3)],
            channel([k[3] for k in KEYS]), channel([k[4] for k in KEYS]))


def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m): return list(map(list,zip(*m)))


def xyz(angles):
    x,y,z=map(math.radians,angles)
    a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]


def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=((math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0]))
         if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0))
    return [round(math.degrees(v),9) for v in (a,b,c)]


def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(source['elements'][i]) for i in PART_INDICES[part]]}
            for part in PARTS}


def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS: raise ValueError((part,grip))
    accepted = original if grip=='native' else twohand
    if p in (0,1) or part=='body': return copy.deepcopy(accepted)
    shift,angles,opening,latch=sample(p)
    if part=='magazine': pivot=MAGAZINE_ANCHOR
    elif part=='cradle': pivot=CRADLE_PIVOT; angles=[opening,0,0]; shift=[0,0,0]
    else: pivot=LATCH_PIVOT; angles=[latch,0,0]; shift=[0,0,0]
    motion=xyz(angles); pivot=sub(pivot,(8,8,8))
    local=add(sub(pivot,vec(motion,pivot)),shift)
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=accepted[context]; base=xyz(idle['rotation']); scale=idle['scale']
        if len(set(scale))!=1: raise ValueError('Expected uniform canonical scale')
        display[context]['rotation']=euler(mul(base,motion))
        display[context]['translation']=[round(v,9) for v in
            add(idle['translation'],vec(base,[scale[0]*v for v in local]))]
    return display


def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A/f'items/{KEY}.json',MANIFEST}


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return absolute paths and bytes only, with a scratch rig override."""
    root=Path(root).resolve()
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,CONTACTS,FRAMING,ART/'review.md',
            Path('scripts/generate_surface_w123_canis_major.py'),
            Path('art/weapons/w123/canis_major/design.json'),
            Path('src/main/resources/destiny/weapons/w46-timing.json'),
            Path('src/main/resources/destiny/sounds/w63-reload.json')]
    raw={path:(root/path).read_bytes() for path in inputs}
    raw[GENERATOR]=Path(__file__).read_bytes()
    raw[PROFILE]=Path(profile_path or root/PROFILE).read_bytes()
    raw[RIG]=Path(rig_path or root/RIG).read_bytes()
    source,twohand,item,profile,rig=(json.loads(raw[p]) for p in (SOURCE,TWOHAND,ITEM,PROFILE,RIG))
    twohand=twohand['display']
    expected_names={36:'drum_core_0',39:'drum_core_3',40:'drum_lobe_0',47:'drum_lobe_7',
        48:'etched_drum_belt_0',55:'etched_drum_belt_7',56:'rear_gold_belt_0',63:'rear_gold_belt_7',
        64:'drum_cradle_-1',65:'cradle_pivot_-1',66:'drum_cradle_1',67:'cradle_pivot_1',
        68:'lower_crossbar_0',71:'lower_crossbar_3',72:'rear_silver_tube_0',75:'rear_silver_tube_3',
        82:'pistol_grip',84:'front_grip',99:'rear_latch_blade',100:'rear_latch_root'}
    if len(source['elements'])!=101 or any(source['elements'][i]['name']!=n for i,n in expected_names.items()):
        raise ValueError('Expected complete canonical Canis101 geometry')
    def center(i):
        e=source['elements'][i]; return [(a+b)/2 for a,b in zip(e['from'],e['to'])]
    if (source['elements'][36]['rotation']['origin']!=list(MAGAZINE_ANCHOR)
            or any(abs(a-b)>1e-8 for a,b in zip(center(100),LATCH_PIVOT))
            or any(abs(a-b)>1e-8 for a,b in zip([(a+b)/2 for a,b in zip(center(65),center(67))],CRADLE_PIVOT))):
        raise ValueError('Canis own geometry anchors changed')
    reload=profile.get('contacts',{}).get('reload',{})
    if (profile.get('schemaVersion')!=1 or profile.get('stage')!='W220'
            or profile.get('weapon')!='canis_major' or profile.get('sourceAction')!=SOURCE_ACTION
            or profile.get('sourceRig',{}).get('action')!=SOURCE_ACTION
            or reload.get('rigAction')!=SOURCE_ACTION or reload.get('hand')!='left'
            or reload.get('partHint')!='magazine' or reload.get('policy')!='magazine'
            or reload.get('gripWindow')!=list(GRIP_WINDOW)
            or any(profile['framing'].get(k) is not v for k,v in
                {'sourceFullChain':True,'keepMeshSupport':True,'hideSupportAtRest':False}.items())):
        raise ValueError('Expected W220 original-chain left whole-drum profile')
    contacts=json.loads(raw[CONTACTS])['weapons']['canis_major']
    if any(profile['contacts'][s]!=contacts[s] for s in ('right','left')):
        raise ValueError('Existing Canis idle grips must remain exact')
    if any(reload[k]!=contacts['reload'][k] for k in ('contact','rotation')):
        raise ValueError('Existing Canis left drum contact must remain exact')
    action=rig['actions'][SOURCE_ACTION]
    joints={'weapon','leftShoulder','leftElbow','leftWrist','rightShoulder','rightElbow','rightWrist'}
    if (rig.get('group')!='heavy_grenade_launcher_796e9ebf' or rig.get('fallback') is not False
            or 'canis_major' not in rig['weapons'] or rig.get('cameraExported') is not False
            or rig.get('w220Source61',{}).get('reloadSamples')!=SAMPLES
            or action['action']!=ACTION_NAME or (action['start'],action['end'])!=(1.,142.)
            or len(action['frames'])!=SAMPLES
            or any(f['progress']!=i/INTERVALS or abs(f['frame']-(1+141*i/INTERVALS))>1e-10
                   or not joints<=f['joints'].keys() for i,f in enumerate(action['frames']))):
        raise ValueError('Fresh W220 original61 full-chain samples required')
    if any(rig[k]!=profile['sourceRig'][k] for k in ('group','sourceBlendSha256','sourceMapSha256','boneMapSha256')):
        raise ValueError('Source provenance mismatch')
    geometries=partition(source)
    counts={part:len(m['elements']) for part,m in geometries.items()}
    if counts!={'body':66,'magazine':28,'cradle':6,'latch':1}: raise ValueError(counts)
    # Resolve canonical alternatives separately; concurrent composites sum.
    model_counts={}
    def model_count(ref,visiting=()):
        if not ref.startswith('destiny:') or ref in visiting: raise ValueError(ref)
        if ref in model_counts: return model_counts[ref]
        path=A/('models/'+ref.split(':',1)[1]+'.json')
        if path not in raw: raw[path]=(root/path).read_bytes()
        m=json.loads(raw[path]);count=(len(m['elements']) if 'elements' in m else model_count(m['parent'],(*visiting,ref)))
        model_counts[ref]=count;return count
    def route_count(node):
        kind=node['type']
        if kind=='minecraft:model': return model_count(node['model'])
        if kind=='minecraft:composite': return sum(route_count(n) for n in node['models'])
        if kind=='minecraft:condition': return max(route_count(node['on_true']),route_count(node['on_false']))
        if kind in ('minecraft:select','minecraft:range_dispatch'):
            return max([route_count(node['fallback']),*(route_count(n['model']) for n in node.get('cases',node.get('entries',[])))])
        raise ValueError(kind)
    canonical_count=route_count(item['model'])
    maximum=max(canonical_count,sum(counts.values()))+ARM_ELEMENT_RESERVE
    if maximum>1000: raise ValueError('Assembled reserve exceeds1000')
    output={};allowed=expected_output_paths()
    def emit(path,value):
        if path not in allowed: raise ValueError('Outside owned Canis output namespace')
        output[root/path]=encode(value)
    for part,m in geometries.items(): emit(A/f'models/{KEY}_{part}.json',m)
    entries=[]
    for i in range(SAMPLES):
        p=i/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',{'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,p,part,grip)})
        def composite(grip):
            return {'type':'minecraft:composite','models':[{'type':'minecraft:model',
                'model':f'destiny:{KEY}_{i:02}_{part}_{grip}'} for part in PARTS]}
        model=(copy.deepcopy(item['model']) if i in (0,INTERVALS) else
            {'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,
             'on_true':composite('twohand'),'on_false':composite('native')})
        entries.append({'threshold':float32(p),'model':model})
    dispatch={'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':1,
              'entries':entries,'fallback':copy.deepcopy(item['model'])}
    guard=copy.deepcopy(item['model'])
    if (guard.get('type')!='minecraft:select' or guard.get('property')!='minecraft:custom_model_data'
            or guard.get('index',0)!=0 or [c['when'] for c in guard['cases']]!=['ads','inspect']):
        raise ValueError('Expected canonical Canis ADS/inspect guard')
    guard['fallback']=dispatch
    wrapper=copy.deepcopy(item)
    wrapper['model']={'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':list(FP),'model':guard}],'fallback':copy.deepcopy(item['model'])}
    emit(A/f'items/{KEY}.json',wrapper)
    emit(MANIFEST,dict(schemaVersion=1,stage='W220',weapon='canis_major',revision=1,
        generator=str(GENERATOR),generatorSha256=sha(raw[GENERATOR]),itemModel='destiny:'+KEY,
        frames=SAMPLES,intervals=INTERVALS,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        thresholdEncoding='exact float32(i/60)',curve='C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,cradlePivot=CRADLE_PIVOT,latchPivot=LATCH_PIVOT,
        bodyMotion='Identity authored body; original weapon bone replay applied once by master.',
        gripWindow=GRIP_WINDOW,magazineSeatedProgress=SEATED,
        normalizedPhases={'unlatch':[0,.06],'cradleOpen':[.06,.16],'unseat':[.16,.23],
            'lateralExchange':[.23,.58],'align':[.58,.60],'seat':[.60,.62],
            'seatHold':[.62,.66],'cradleClose':[.66,.75],'latchClose':[.79,.84],'recover':[.84,1.]},
        partitionIndices=PART_INDICES,partElements=counts,bodyElements=66,magazineElements=28,
        movingElements=35,weaponElements=101,sourceElements=101,addedElements=0,triangleAdapterElements=0,
        movingIndices=[i for part in PARTS if part!='body' for i in PART_INDICES[part]],
        movingNames={p:[e['name'] for e in geometries[p]['elements']] for p in PARTS if p!='body'},
        semanticGroups={'magazine':'whole drum core4+lobe8+etched belt8+rear gold belt8',
            'cradle':'two arms64/66 and crossbar68..71; fixed pivot bosses65/67 remain body',
            'latch':'blade99 rotates at fixed root100; rear tubes72..75 remain body'},
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha(raw[SOURCE]),
        sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={p:sha(encode(m['elements'])) for p,m in geometries.items()},
        canonicalGeometryAndUVPreserved=True,ordinaryArmElementReserve=ARM_ELEMENT_RESERVE,
        canonicalWeaponElements=canonical_count,canonicalModelElements=model_counts,maxAssembledElements=maximum,
        candidateReloadWithArmsEstimate=101+ARM_ELEMENT_RESERVE,elementLimit=1000,assembledBudgetVerified=False,
        budgetBasis='Parent-resolved canonical alternative maximum or active101, plus448 four arm surfaces; master measures integrated output.',
        hipEndpoints=[0,INTERVALS],endpointDisplayExact=True,fallbackModelExact=True,
        fallback='Exact current canonical graph at0/1, overshoot, negative inactive, nonFP and ADS/inspect.',
        sourceAction=SOURCE_ACTION,rigAction=SOURCE_ACTION,rigActionName=action['action'],sourceGroup=rig['group'],
        sourceRigPath=str(RIG),sourceActionSourceRange=[action['start'],action['end']],sourceRigSamples=SAMPLES,
        sourceFullChain=True,sourceCameraRecovered=False,hand='left',partHint='magazine',policy='magazine',
        sourceReviewEvidence=profile['evidence'],
        motionAuthorship='Canis own geometry-derived cradle opening85deg, lateral whole-drum exchange and seating, independent rear latch. Class104 supplies original carrier/arms only. Source-left attachment changes drum translation while handling, releases by.58 before.62 seat; no source retiming/damping/stretch/hiding.',
        gameplayTimingChanged=False,mechanicsOrAudioChanged=False,nativeGameplayVerified=False,nativeVisibilityAccepted=False,
        packFiles=len(output),totalReturnedFiles=len(allowed),staticParts=len(PARTS),parentDisplayChildren=SAMPLES*len(PARTS)*len(GRIPS),
        limitations=['Worker used master original Blender evaluation and actual source sheet, not independent Blender evaluation.',
            'ARMATURE only: no original Canis mesh motion, camera, finger IK or recovered cradle/latch events.',
            'Whole drum follows substantial original source-left travel during attachment; native contact and clearance require FIRST review.',
            '61 discrete poses do not establish continuous native60fps interpolation.',
            'Budget includes four112 arm reserves; final assembled routes must be measured by master.',
            'FIRST Vision, same-worker correction or justified no-change, and SECOND Vision pending.'],
        inputSha256={str(p):sha(data) for p,data in raw.items()},
        outputSha256={str(p.relative_to(root)):sha(data) for p,data in output.items()}))
    if set(output)!={root/p for p in allowed}: raise ValueError('Incomplete Canis output mapping')
    return output
