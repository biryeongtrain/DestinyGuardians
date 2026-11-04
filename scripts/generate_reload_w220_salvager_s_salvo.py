#!/usr/bin/env python3
"""W220 Salvo: preserve W173 break-open mechanism, add 61 C1 poses.

Pure stdlib; import and generate never write. Master owns source Blender
sampling, full shoulder-chain replay, materialization and FIRST/SECOND Vision.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w220/salvager_s_salvo')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w220_salvager_s_salvo.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w173_salvager_s_salvo.py')
AUTHORED_MANIFEST = Path('art/weapons/w173/salvager_s_salvo/manifest.json')
STORYBOARD = Path('art/weapons/w173/salvager_s_salvo/storyboard.png')
REFERENCE = Path('art/weapons/w173/salvager_s_salvo/motion-reference.json')
SOURCE = A / 'models/weapon_surface_w123/salvager_s_salvo.json'
TWOHAND = A / 'models/weapon/grenade_launcher/salvager_s_salvo_twohand.json'
ITEM = A / 'items/weapon/salvager_s_salvo.json'
TEXTURE = A / 'textures/item/weapon/w123/salvager_s_salvo.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w220/rigs/grenade_launcher_83c75a3c.json')
KEY = 'weapon_reload_w220_salvager_s_salvo/salvager_s_salvo'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'barrel', 'round')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = 61
SOURCE_ACTION = '80A8A136'
ACTION_NAME = 'Armature|fp_80A8A136_reload_full|Base'
ARM_ELEMENT_RESERVE = 4 * 112
GRIP_WINDOW = (.45, .48, .56, .65)
# Palm-origin anchor, offset from the case surface to clear the actual W204
# fingerless hand (classic +/-1.2 width/depth, hand end Y+1 before source scaling).
# Only attachment translation changes; geometry and the .65 seated pose do not.
ROUND_CONTACT = (6.1, 12.27, 3.6)
ROUND_VISIBLE = tuple(range(27, 40))


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]

BARREL = tuple(range(32))+tuple(range(36,58))+tuple(range(73,76))+tuple(range(85,101))

GRIP = (8.,8.155,8.25)

HINGE = (8.,10.91,4.14)

ROUND_CENTER = (8.,12.27,2.85)

KEYS = (
 (0., (0,0,0), (0,0,0), 0., (0,0,0)),
 (.10,(3,-3,-5),(.05,-.08,-.04),0.,(0,0,0)),
 (.20,(10,-7,-11),(.12,-.15,-.10),-24.,(0,0,0)),
 (.30,(17,-10,-16),(.18,-.20,-.15),-48.,(0,0,0)),
 (.40,(15,-10,-15),(.18,-.20,-.15),-48.,(-3.2,.6,3.5)),
 (.45,(14,-10,-15),(.18,-.20,-.15),-48.,(-2.4,.4,3.0)),
 (.53,(14,-10,-15),(.18,-.20,-.15),-48.,(0.,0.,2.8)),
 (.65,(14,-10,-15),(.18,-.20,-.15),-48.,(0.,0.,0.)),
 (.69,(14,-10,-15),(.18,-.20,-.15),-48.,(0,0,0)),
 (.76,(10,-7,-10),(.12,-.12,-.10),0.,(0,0,0)),
 (.86,(3,-2,-3),(.04,-.04,-.03),0.,(0,0,0)),
 (1., (0,0,0), (0,0,0), 0., (0,0,0)),
)

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

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,hinge,approach=sample(p)
    b=xyz(angles); h=sub(GRIP,(8,8,8)); q=sub(HINGE,(8,8,8))
    child=xyz((hinge,0,0)) if part!='body' else xyz((0,0,0))
    local=sub(h,vec(b,h))
    if part!='body':
        # B around grip, then child H around hinge. Round follows same H and
        # moves along its local bore axis only after lateral support-side entry.
        local=add(local,vec(b,sub(q,vec(child,q))))
        if part=='round': local=add(local,vec(mul(b,child),approach))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context]; base=xyz(idle['rotation']);s=idle['scale']
        if s!=twohand[context]['scale'] or len(set(s))!=1: raise ValueError('Uniform matching FP scale required')
        rotation=mul(base,mul(b,child))
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(comp,position),sub(twohand[context]['translation'],vec(comp,idle['translation'])))
            rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def round_elements(source):
    # Six authored volumes form a short hex cartridge and its shallow rim.
    # Reuse the existing neutral metal face UV; no new atlas or paint changes.
    faces=source['elements'][75]['faces']
    elements=[]
    for name,r,z0,z1 in (('case',.61,1.65,4.05),('rim',.68,4.05,4.22)):
        for angle in (0,60,120):
            elements.append(dict(name=f'cosmetic_round_{name}_{angle}',
                **{'from':[8-r,12.27-r/math.sqrt(3),z0], 'to':[8+r,12.27+r/math.sqrt(3),z1]},
                rotation=dict(origin=[8,12.27,2.85],axis='z',angle=angle),faces=copy.deepcopy(faces)))
    return elements

def tangents(times, values):
    """Weighted harmonic PCHIP: zero endpoint, hold and extremum slopes."""
    steps = [b-a for a,b in zip(times,times[1:])]
    secants = [(b-a)/h for a,b,h in zip(values,values[1:],steps)]
    slopes = [0.] * len(times)
    for i in range(1,len(times)-1):
        before,after = secants[i-1],secants[i]
        if before*after > 0:
            w1,w2 = 2*steps[i]+steps[i-1],steps[i]+2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before+w2/after)
    return slopes


def sample(p):
    """All12 W173 knots/holds, including hinge and round approach, unchanged."""
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError(p)
    for key in KEYS:
        if p == key[0]:
            return tuple(key[k] if k==3 else list(key[k]) for k in (1,2,3,4))
    times = [key[0] for key in KEYS]
    index = next(i for i in range(len(KEYS)-1) if p < times[i+1])
    h = times[index+1]-times[index]
    t = (p-times[index])/h
    h00,h10,h01,h11 = 2*t**3-3*t*t+1,t**3-2*t*t+t,-2*t**3+3*t*t,t**3-t*t
    def component(values):
        if values[index] == values[index+1]:
            return values[index]
        slopes = tangents(times,values)
        return h00*values[index]+h10*h*slopes[index]+h01*values[index+1]+h11*h*slopes[index+1]
    return tuple(component([key[k] for key in KEYS]) if k==3 else
                 [component([key[k][axis] for key in KEYS]) for axis in range(3)]
                 for k in (1,2,3,4))


def partition(source):
    """Fixed receiver28, gun-attached hinged fore-end73, cosmetic cartridge6."""
    result = {}
    for part in PARTS:
        model = {k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements'] = round_elements(source) if part=='round' else [
            copy.deepcopy(e) for i,e in enumerate(source['elements'])
            if (i in BARREL)==(part=='barrel')]
        result[part] = model
    return result


def expected_output_paths():
    paths = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return absolute path/bytes mapping without writing, including on import."""
    root = Path(root).resolve()
    inputs = [SOURCE,TWOHAND,ITEM,TEXTURE,CONTACTS,FRAMING,AUTHORED_SOURCE,
              AUTHORED_MANIFEST,STORYBOARD,REFERENCE,
              Path('src/main/resources/destiny/weapons/w46-timing.json'),
              Path('src/main/resources/destiny/sounds/w63-reload.json'),
              Path('scripts/skin_arm_models_w204.py'),
              Path('scripts/build_first_person_hands_w201.py'),
              Path('scripts/rig_arms_w205.py'),Path('scripts/reload_hand_w218.py')]
    raw = {p:(root/p).read_bytes() for p in inputs}
    raw[GENERATOR] = Path(__file__).read_bytes()
    raw[PROFILE] = Path(profile_path or root/PROFILE).read_bytes()
    raw[RIG] = Path(rig_path or root/RIG).read_bytes()
    source,twohand,item,profile,rig,old = (json.loads(raw[p]) for p in
        (SOURCE,TWOHAND,ITEM,PROFILE,RIG,AUTHORED_MANIFEST))
    twohand = twohand['display']
    if (len(source['elements'])!=101 or old['keyframes']!=json.loads(encode(KEYS))
            or old['barrelIndices']!=list(BARREL)
            or old['gripPivot']!=list(GRIP) or old['hingePivot']!=list(HINGE)
            or old['roundCenter']!=list(ROUND_CENTER)
            or old['sourceGeometryFileSha256']!=sha(raw[SOURCE])
            or any(not source['elements'][i]['name'].startswith('breech_plug_')
                   or i in BARREL for i in range(32,36))):
        raise ValueError('W17312 knots, partition, pivots or canonical geometry drift')
    # Compare the actual prior emitted round: six volumes and every face UV.
    prior_round = A / 'models/weapon_reload_w173_salvager_s_salvo/salvager_s_salvo_round.json'
    raw[prior_round] = (root/prior_round).read_bytes()
    if json.loads(raw[prior_round])['elements'] != round_elements(source):
        raise ValueError('Existing W173 cartridge geometry/UV drift')
    reload = profile.get('contacts',{}).get('reload',{})
    if (profile.get('schemaVersion')!=1 or profile.get('stage')!='W220'
            or profile.get('weapon')!='salvager_s_salvo'
            or profile.get('sourceAction')!=SOURCE_ACTION
            or profile.get('sourceRig',{}).get('group')!='grenade_launcher_83c75a3c'
            or profile['sourceRig'].get('action')!=SOURCE_ACTION
            or reload.get('rigAction')!=SOURCE_ACTION or reload.get('hand')!='left'
            or reload.get('partHint')!='round' or reload.get('policy')!='magazine'
            or reload.get('contact')!=list(ROUND_CONTACT)
            or reload.get('gripWindow')!=list(GRIP_WINDOW)
            or any(profile['framing'].get(k) is not v for k,v in
                {'sourceFullChain':True,'keepMeshSupport':True,'hideSupportAtRest':False}.items())):
        raise ValueError('Expected W220 full-chain LEFT round-only bounded attachment')
    current_contacts = json.loads(raw[CONTACTS])['weapons']['salvager_s_salvo']
    for side in ('right','left'):
        if profile['contacts'][side]!=current_contacts[side]:
            raise ValueError('Existing idle grip changed: '+side)
    if reload['rotation']!=current_contacts['reload']['rotation']:
        raise ValueError('Existing reload rotation changed')
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon','leftShoulder','leftElbow','leftWrist',
              'rightShoulder','rightElbow','rightWrist'}
    if (rig.get('group')!='grenade_launcher_83c75a3c' or rig.get('fallback') is not False
            or 'salvager_s_salvo' not in rig['weapons']
            or rig.get('cameraExported') is not False
            or rig.get('w220Source61',{}).get('reloadSamples')!=SAMPLES
            or action['action']!=ACTION_NAME
            or (action['start'],action['end'])!=(1.,89.)
            or len(action['frames'])!=SAMPLES
            or any(frame['progress']!=i/INTERVALS
                   or abs(frame['frame']-(1+88*i/INTERVALS))>1e-10
                   or not joints<=frame['joints'].keys()
                   for i,frame in enumerate(action['frames']))):
        raise ValueError('Fresh original W22061 full source-chain samples required')
    if any(rig[k]!=profile['sourceRig'][k] for k in
           ('sourceBlendSha256','sourceMapSha256','boneMapSha256')):
        raise ValueError('Reviewed original source provenance differs')
    geometries = partition(source)
    counts = {part:len(model['elements']) for part,model in geometries.items()}
    if counts!={'body':28,'barrel':73,'round':6}:
        raise ValueError('Expected fixed28 + hinged73 + cosmetic6')
    output = {}
    allowed = expected_output_paths()
    def emit(path,value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W220 Salvo namespace')
        output[root/path] = encode(value)
    model_counts = {}
    def model_count(ref,visiting=()):
        if not ref.startswith('destiny:') or ref in visiting:
            raise ValueError('Unexpected canonical model reference: '+ref)
        if ref in model_counts:return model_counts[ref]
        path = A / ('models/'+ref.split(':',1)[1]+'.json')
        if path not in raw:raw[path] = (root/path).read_bytes()
        model = json.loads(raw[path])
        count = len(model['elements']) if 'elements' in model else model_count(model['parent'],(*visiting,ref))
        model_counts[ref] = count
        return count
    def route_count(node):
        kind = node['type']
        if kind=='minecraft:model':return model_count(node['model'])
        if kind=='minecraft:composite':return sum(route_count(c) for c in node['models'])
        if kind=='minecraft:condition':return max(route_count(node['on_true']),route_count(node['on_false']))
        if kind in ('minecraft:select','minecraft:range_dispatch'):
            children = node.get('cases',node.get('entries',[]))
            return max([route_count(node['fallback']),*(route_count(c['model']) for c in children)])
        raise ValueError('Unhandled canonical item route: '+kind)
    canonical_count = route_count(item['model'])
    maximum = max(canonical_count,sum(counts.values()))+ARM_ELEMENT_RESERVE
    if maximum>1000:raise ValueError('Weapon plus448 classic arm surfaces exceeds1000')
    for part,model in geometries.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries = []
    for i in range(SAMPLES):
        p = i/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',{
                    'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,p,part,grip)})
        def composite(grip):
            return {'type':'minecraft:composite','models':[
                {'type':'minecraft:model','model':f'destiny:{KEY}_{i:02}_{part}_{grip}'}
                for part in PARTS if part!='round' or i in ROUND_VISIBLE]}
        node = copy.deepcopy(item['model']) if i in (0,INTERVALS) else {
            'type':'minecraft:condition','property':'minecraft:custom_model_data',
            'index':0,'on_true':composite('twohand'),'on_false':composite('native')}
        entries.append({'threshold':float32(p),'model':node})
    dispatch = {'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data',
                'index':1,'entries':entries,'fallback':copy.deepcopy(item['model'])}
    guard = copy.deepcopy(item['model'])
    if (guard.get('type')!='minecraft:select' or guard.get('property')!='minecraft:custom_model_data'
            or guard.get('index',0)!=0 or [c['when'] for c in guard['cases']]!=['ads','inspect']):
        raise ValueError('Expected canonical ADS/inspect precedence')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':list(FP),'model':guard}],'fallback':copy.deepcopy(item['model'])}
    emit(A/f'items/{KEY}.json',wrapper)
    emit(MANIFEST,{
        'schemaVersion':1,'stage':'W220','weapon':'salvager_s_salvo','revision':2,
        'generator':str(GENERATOR),'generatorSha256':sha(raw[GENERATOR]),
        'itemModel':'destiny:'+KEY,'frames':SAMPLES,'intervals':INTERVALS,
        'progressFloatIndex':1,'gripFlagIndex':0,'firstPersonContexts':list(FP),
        'thresholdEncoding':'exact float32(i/60), matching master runtime60grid',
        'curve':'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum slopes',
        'keyframes':KEYS,'gripPivot':GRIP,'hingePivot':HINGE,'roundCenter':ROUND_CENTER,
        'authoredTimingSource':str(AUTHORED_SOURCE),'normalizedPhases':old['normalizedPhases'],
        'barrelIndices':list(BARREL),'barrelNames':old['barrelNames'],'fixedNames':old['fixedNames'],
        'partitionRationale':old['partitionRationale'],
        'roundVisibleSamples':list(ROUND_VISIBLE),'roundVisibleProgress':[.45,.65],
        'roundHiddenFromSample':40,'roundSeatedProgress':.65,'gripWindow':list(GRIP_WINDOW),
        'roundPalmOriginContact':ROUND_CONTACT,
        'barrelGunAttached':True,'barrelPolicyMagazine':False,'breechPlugFixedIndices':list(range(32,36)),
        'reference':old['reference'],'storyboard':str(STORYBOARD),
        'sourceReviewEvidence':profile['evidence'],
        'sourceGeometryPath':str(SOURCE),'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'sourceElements':101,'partElements':counts,'bodyElements':28,'barrelElements':73,
        'roundElements':6,'weaponElements':107,'addedElements':6,'newElementsRelativeToW173':0,
        'triangleAdapterElements':0,'ordinaryArmElementReserve':ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate':107+ARM_ELEMENT_RESERVE,
        'canonicalWeaponElements':canonical_count,'canonicalModelElements':model_counts,
        'maxAssembledElements':maximum,'elementLimit':1000,'assembledBudgetVerified':False,
        'measuredAllRouteElements':None,
        'budgetBasis':'Parent-resolved current canonical route maximum or active28+73+6, plus448 classic arm surfaces; master measures final materialized routes.',
        'geometryAndUVPreserved':True,'reloadGeometryMatchesW173':True,'newTexture':False,
        'roundUVSource':old['roundUVSource'],
        'sourceElementsAndUVSha256':sha(encode(source['elements'])),
        'partElementsAndUVSha256':{p:sha(encode(m['elements'])) for p,m in geometries.items()},
        'hipEndpoints':[0,60],'endpointDisplayExact':True,'fallbackModelExact':True,
        'fallback':'Exact current canonical graph at0/1, overshoot, inactive and nonFP; ADS/inspect precede reload; both grips preserved.',
        'rigAction':SOURCE_ACTION,'sourceAction':SOURCE_ACTION,'rigActionName':action['action'],
        'sourceGroup':rig['group'],'sourceRigPath':str(RIG),
        'sourceRig':profile['sourceRig'],'sourceActionSourceRange':[action['start'],action['end']],
        'sourceRigSamples':len(action['frames']),'sourceFullChain':True,'sourceCameraRecovered':False,
        'hand':'left','partHint':'round','policy':'magazine',
        'motionAuthorship':'Exact12 W173 knots, holds, pivots, partition and six cartridge volumes/UV retained; only interpolation becomes C1 PCHIP61. Master source_weapon_display replaces authored body carrier motion while preserving body-relative hinge/round transforms, preventing double body motion. Full source chains remain undamped. Only round translation attaches to source LEFT during bounded insertion; barrel remains hinged to gun.',
        'contactAuthorship':profile['contactAuthorship'],
        'gameplayTimingChanged':False,'mechanicsOrAudioChanged':False,'remoteDetonationChanged':False,
        'timingPolicy':old['timingPolicy'],'nativeGameplayVerified':False,'nativeVisibilityAccepted':False,
        'packFiles':len(output),'totalReturnedFiles':len(allowed),'staticParts':3,
        'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'limitations':profile['limitations'],
        'inputSha256':{str(p):sha(b) for p,b in raw.items()},
        'outputSha256':{str(p.relative_to(root)):sha(b) for p,b in output.items()}})
    if set(output)!={root/p for p in allowed}:raise ValueError('Incomplete W220 Salvo mapping')
    return output
