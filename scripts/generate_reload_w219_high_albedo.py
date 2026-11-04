#!/usr/bin/env python3
"""W219 High Albedo: W183 revision2 geometry/motion with 61 C1 PCHIP poses.

Pure stdlib. Import and generate perform no writes. Master owns original Blender
extraction, full source-chain skin arms, materialization and FIRST/SECOND Vision.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w219/high_albedo')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w219_high_albedo.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w183_high_albedo.py')
AUTHORED_MANIFEST = Path('art/weapons/w183/high_albedo/manifest.json')
AUTHORED_REVIEW = Path('art/weapons/w183/high_albedo/SOURCE.md')
SOURCE = A / 'models/weapon_surface_w123/high_albedo.json'
TWOHAND = A / 'models/weapon/sidearm/high_albedo_twohand.json'
ITEM = A / 'items/weapon/high_albedo.json'
TEXTURE = A / 'textures/item/weapon/w123/high_albedo.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w219/rigs/sidearm_80771a27.json')
KEY = 'weapon_reload_w219_high_albedo/high_albedo'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8ADE2'
ACTION_NAME = 'Armature|fp_80A8ADE2_reload_full|Base'
ARM_ELEMENT_RESERVE = 4 * 112
GRIP_WINDOW = (.18, .25, .50, .60)
GRIP = (8.0, 8.65, 7.85)
MAGAZINE_ANCHOR = (8.0, 5.97, 8.67)
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (18, 2, -3), (0.12, -0.12, 0), (0, 0, 0)), (0.2, (42, 10, -16), (0.35, 0.18, 0.12), (0, 0, 0)), (0.3, (46, 16, -29), (0.45, 0.25, 0.15), (0, -2.8, 0.856)), (0.4, (44, 17, -31), (0.45, 0.25, 0.15), (-0.5, -5.2, 1.59)), (0.5, (43, 17, -30), (0.45, 0.23, 0.15), (-0.16, -2.3, 0.703)), (0.6, (41, 18, -27), (0.45, 0.2, 0.15), (0, 0, 0)), (0.7, (33, 22, -33), (0.38, 0.1, 0.1), (0, 0, 0)), (0.8, (22, 25, -40), (0.3, 0, 0.1), (0, 0, 0)), (0.86, (26, 16, -24), (0.22, 0.06, 0.05), (0, 0, 0)), (0.92, (9, 5, -7), (0.1, -0.02, 0), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))

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
    # The only existing magazine geometry is the exposed baseplate, not a shaft.
    # Grip heel/backstrap, lower cylinder, selector, cage and sight remain fixed.
    return e['name'] == 'magazine_base'

def reload_shaft(source):
    """Authored shaft from frame1998: elongated rectangular core + ribbed broad sides.
    Whole assembly shares the original baseplate anchor and -17deg grip axis.
    Existing dark baseplate/steel atlas regions only. No texture file modification.
    """
    dark=copy.deepcopy(source['elements'][91]['faces']['up'])
    metal=copy.deepcopy(source['elements'][16]['faces']['up'])
    # Restrict metal UV to an interior patch of the existing steel barrel region;
    # avoid stretching a border or repeating its unrelated long barrel bands.
    metal['uv']=[.3125,.25,.4375,.375]
    def box(name,lo,hi,face):
        return dict(name='magazine_shaft_'+name,**{'from':lo,'to':hi},
            rotation=dict(origin=list(MAGAZINE_ANCHOR),axis='x',angle=-17),
            faces={f:copy.deepcopy(face) for f in ('north','south','east','west','up','down')})
    result=[box('core',[7.50,6.08,8.09],[8.50,10.12,9.25],dark)]
    # Source broad face has three longitudinal reinforcing bars and two cross bars.
    # Mirror its structural ribs on both broad faces; fine dimensions are authored.
    for side,x0,x1 in [('left',7.474,7.505),('right',8.495,8.526)]:
        for i,z in enumerate((8.18,8.67,9.16)):
            result.append(box(f'{side}_longrib_{i}',[x0,6.18,z-.022],[x1,10.02,z+.022],metal))
        for i,y in enumerate((7.18,9.12)):
            result.append(box(f'{side}_crossrib_{i}',[x0-.002,y-.025,8.11],[x1+.002,y+.025,9.23],metal))
    return result

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
    # Original baseplate and reference-backed reload-only shaft move as one rigid payload.
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


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return absolute output paths and bytes; never materialize any output.

    Optional read-only paths allow bounded preparation before master installs
    the fresh W219 rig/profile. Normal integration uses only root-owned paths.
    """
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE, AUTHORED_SOURCE,
              AUTHORED_MANIFEST, AUTHORED_REVIEW, CONTACTS, FRAMING,
              Path('src/main/resources/destiny/weapons/w46-timing.json'),
              Path('src/main/resources/destiny/sounds/w63-reload.json')]
    raw = {path: (root / path).read_bytes() for path in inputs}
    # Shared/canonical inputs are recorded as currently read, never pinned to
    # stale shared loader, routing, Java, timing or sound file hashes.
    raw[GENERATOR] = Path(__file__).read_bytes()
    raw[PROFILE] = Path(profile_path or root / PROFILE).read_bytes()
    raw[RIG] = Path(rig_path or root / RIG).read_bytes()
    source, twohand, item, profile, rig, old = (
        json.loads(raw[path]) for path in
        (SOURCE, TWOHAND, ITEM, PROFILE, RIG, AUTHORED_MANIFEST))
    twohand = twohand['display']
    if (len(source['elements']) != 100
            or source['elements'][91]['name'] != 'magazine_base'
            or old.get('revision') != 2
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP)
            or old['magazineAnchor'] != list(MAGAZINE_ANCHOR)
            or old['sourceGeometryFileSha256'] != sha(raw[SOURCE])
            or old['reloadOnlyGeometry']['elements'] != reload_shaft(source)):
        raise ValueError('W183 revision2 authored keys/baseplate/11 shaft ribs must remain exact')
    reload = profile.get('contacts', {}).get('reload', {})
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W219'
            or profile.get('weapon') != 'high_albedo'
            or profile.get('sourceAction') != SOURCE_ACTION
            or reload.get('rigAction') != SOURCE_ACTION
            or reload.get('hand') != 'left'
            or reload.get('partHint') != 'magazine'
            or reload.get('policy') != 'magazine'
            or reload.get('gripWindow') != list(GRIP_WINDOW)
            or any(profile['framing'].get(k) is not v for k,v in
                   {'sourceFullChain': True, 'keepMeshSupport': True,
                    'hideSupportAtRest': False}.items())):
        raise ValueError('Expected W219 original full-chain left magazine profile')
    current_contacts = json.loads(raw[CONTACTS])['weapons']['high_albedo']
    for side in ('right', 'left'):
        if profile['contacts'][side] != current_contacts[side]:
            raise ValueError('Existing authored mesh contact changed: ' + side)
    for name in ('contact', 'rotation'):
        if reload[name] != current_contacts['reload'][name]:
            raise ValueError('Existing authored reload contact changed: ' + name)
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'sidearm_80771a27' or rig.get('fallback') is not False
            or 'high_albedo' not in rig['weapons']
            or rig.get('cameraExported') is not False
            or rig.get('w219Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 67.)
            or len(action['frames']) != SAMPLES
            or any(frame['progress'] != i/INTERVALS
                   or abs(frame['frame']-(1+66*i/INTERVALS)) > 1e-10
                   or not joints <= frame['joints'].keys()
                   for i,frame in enumerate(action['frames']))):
        raise ValueError('Fresh original W21961 shoulder/elbow/wrist/weapon samples required')
    if any(rig[k] != profile['sourceRig'][k] for k in
           ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256')):
        raise ValueError('Original source provenance differs from reviewed profile')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part,model in geometries.items()}
    if counts != {'body': 99, 'magazine': 12}:
        raise ValueError('Expected unchanged body99 and complete magazine12')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W219 High Albedo namespace')
        output[root / path] = encode(value)

    # Count parent-resolved canonical item alternatives independently. A full
    # model and a composite are alternatives; only concurrent children sum.
    model_counts = {}

    def model_count(ref, visiting=()):
        if not ref.startswith('destiny:') or ref in visiting:
            raise ValueError('Unexpected canonical model reference: ' + ref)
        if ref in model_counts:
            return model_counts[ref]
        path = A / ('models/' + ref.split(':', 1)[1] + '.json')
        data = raw.setdefault(path, (root / path).read_bytes())
        model = json.loads(data)
        count = (len(model['elements']) if 'elements' in model else
                 model_count(model['parent'], (*visiting, ref)))
        model_counts[ref] = count
        return count

    def route_count(node):
        kind = node['type']
        if kind == 'minecraft:model':
            return model_count(node['model'])
        if kind == 'minecraft:composite':
            return sum(route_count(child) for child in node['models'])
        if kind == 'minecraft:condition':
            return max(route_count(node['on_true']), route_count(node['on_false']))
        if kind in ('minecraft:select', 'minecraft:range_dispatch'):
            children = node.get('cases', node.get('entries', []))
            return max([route_count(node['fallback']),
                        *(route_count(child['model']) for child in children)])
        raise ValueError('Unhandled canonical item route: ' + kind)

    canonical_count = route_count(item['model'])
    maximum = max(canonical_count, sum(counts.values())) + ARM_ELEMENT_RESERVE
    if maximum > 1000:
        raise ValueError('Weapon plus four classic arm surfaces exceeds1000')
    for part, model in geometries.items():
        emit(A / f'models/{KEY}_{part}.json', model)
    entries = []
    for i in range(SAMPLES):
        p = i/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f'models/{KEY}_{i:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'],twohand,p,part,grip)})

        def composite(grip):
            return {'type':'minecraft:composite', 'models':[
                {'type':'minecraft:model', 'model':f'destiny:{KEY}_{i:02}_{part}_{grip}'}
                for part in PARTS]}

        model = copy.deepcopy(item['model']) if i in (0,INTERVALS) else {
            'type':'minecraft:condition', 'property':'minecraft:custom_model_data',
            'index':0, 'on_true':composite('twohand'), 'on_false':composite('native')}
        entries.append({'threshold':float32(p), 'model':model})
    dispatch = {'type':'minecraft:range_dispatch', 'property':'minecraft:custom_model_data',
                'index':1, 'entries':entries, 'fallback':copy.deepcopy(item['model'])}
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select'
            or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index',0) != 0
            or [case['when'] for case in guard['cases']] != ['ads','inspect']):
        raise ValueError('Expected canonical High Albedo ADS/inspect guard')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type':'minecraft:select', 'property':'minecraft:display_context',
        'cases':[{'when':list(FP), 'model':guard}], 'fallback':copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion':1, 'stage':'W219', 'weapon':'high_albedo', 'revision':1,
        'generator':str(GENERATOR), 'generatorSha256':sha(raw[GENERATOR]),
        'itemModel':'destiny:'+KEY, 'frames':SAMPLES, 'intervals':INTERVALS,
        'progressFloatIndex':1, 'gripFlagIndex':0, 'firstPersonContexts':list(FP),
        'thresholdEncoding':'exact float32(i/60), matching master runtime60grid',
        'curve':'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes':KEYS, 'gripPivot':GRIP, 'magazineAnchor':MAGAZINE_ANCHOR,
        'magazineExtractionAxis':old['magazineExtractionAxis'],
        'magazineSeatedProgress':.60, 'gripWindow':list(GRIP_WINDOW),
        'authoredTimingSource':str(AUTHORED_SOURCE), 'normalizedPhases':old['normalizedPhases'],
        'reference':old['reference'], 'sourceReviewEvidence':profile['evidence'],
        'sourceGeometryPath':str(SOURCE), 'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'sourceElements':100, 'partElements':counts, 'bodyElements':99,
        'movingElements':12, 'magazineElements':12, 'weaponElements':111,
        'addedElements':11, 'newElementsRelativeToW183Revision2':0,
        'triangleAdapterElements':0, 'ordinaryArmElementReserve':ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate':111+ARM_ELEMENT_RESERVE,
        'canonicalWeaponElements':canonical_count,
        'candidateKnownCanonicalWithArmsEstimate':canonical_count+ARM_ELEMENT_RESERVE,
        'canonicalModelElements':model_counts,
        'maxAssembledElements':maximum, 'elementLimit':1000,
        'assembledBudgetVerified':False, 'measuredAllRouteElements':None,
        'budgetBasis':'Parent-resolved current canonical route maximum or active99+12, plus448 classic arm surfaces. Alternatives not summed. Master measures final materialized routes.',
        'partitionIndices':old['partitionIndices'], 'semanticGroups':old['semanticGroups'],
        'movingIndices':[91], 'movingNames':['magazine_base'] +
            [e['name'] for e in reload_shaft(source)],
        'reloadOnlyGeometry':old['reloadOnlyGeometry'],
        'sourceElementsAndUVSha256':sha(encode(source['elements'])),
        'partElementsAndUVSha256':{part:sha(encode(m['elements'])) for part,m in geometries.items()},
        'canonicalGeometryAndUVPreserved':True, 'reloadGeometryMatchesW183Revision2':True,
        'hipEndpoints':[0,INTERVALS], 'endpointDisplayExact':True, 'fallbackModelExact':True,
        'fallback':'Exact current canonical graph at0/1,overshoot,negative inactive and nonFP; ADS/inspect cases precede reload; native/twohand retained.',
        'rigAction':SOURCE_ACTION, 'sourceAction':SOURCE_ACTION, 'rigActionName':action['action'],
        'sourceGroup':rig['group'], 'sourceRigPath':str(RIG),
        'sourceActionSourceRange':[action['start'],action['end']],
        'sourceRigSamples':len(action['frames']), 'sourceFullChain':True,
        'sourceCameraRecovered':False, 'hand':'left', 'partHint':'magazine', 'policy':'magazine',
        'motionAuthorship':'Exact12 W183 revision2 knots, holds, baseplate+11 ribbed shaft geometry/UV, transform algebra and post-insertion upper/rear sweep. Only interpolation becomes C1 PCHIP61. Master attaches fresh W219 full original shoulder chains without retiming, length stretch, axis damping or support hiding.',
        'gameplayTimingChanged':False, 'mechanicsOrAudioChanged':False,
        'timingPolicy':old['timingPolicy'],
        'nativeGameplayVerified':False, 'nativeVisibilityAccepted':False,
        'packFiles':len(output), 'totalReturnedFiles':len(allowed),
        'staticParts':2, 'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'limitations':[
            'Worker read master original Blender evaluation and viewed actual bone sheet; no independent Blender opening claimed.',
            'ARMATURE only: no original weapon mesh, camera, finger IK or measured hidden shaft dimensions. Mesh contacts remain authored.',
            '61 poses/60 intervals do not establish continuous native60fps interpolation.',
            'Left grip attachment ramps.18..25, fades.50..60; zero after.60 seat, leaving upper/rear sweep independent. FIRST contact review pending.',
            'Current route element counts plus448 reserve are bounded; final materialized arms/routes require master verification.',
            'FIRST PNG review, same-worker correction or justified no-change, and master SECOND pending.'],
        'inputSha256':{str(path):sha(data) for path,data in raw.items()},
        'outputSha256':{str(path.relative_to(root)):sha(data) for path,data in output.items()}})
    if set(output) != {root/path for path in allowed}:
        raise ValueError('Incomplete W219 High Albedo output mapping')
    return output
