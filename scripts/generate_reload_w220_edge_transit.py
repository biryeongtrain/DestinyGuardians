#!/usr/bin/env python3
"""W220 Edge Transit: exact W180 mechanisms, resampled to61 C1 PCHIP poses.

Pure stdlib; import/generate never write. Master owns source Blender evaluation,
full source-chain replay, materialization, runtime and FIRST/SECOND Vision.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w220/edge_transit')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w220_edge_transit.py')
AUTHORED_SOURCE = Path('scripts/generate_reload_w180_edge_transit.py')
AUTHORED_MANIFEST = Path('art/weapons/w180/edge_transit/manifest.json')
AUTHORED_REVIEW = Path('art/weapons/w180/edge_transit/SOURCE.md')
AUTHORED_STORYBOARD = Path('art/weapons/w180/edge_transit/storyboard.png')
SOURCE = A / 'models/weapon_surface_w123/edge_transit.json'
TWOHAND = A / 'models/weapon/heavy_grenade_launcher/edge_transit_twohand.json'
ITEM = A / 'items/weapon/edge_transit.json'
TEXTURE = A / 'textures/item/weapon/w123/edge_transit.png'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w220/rigs/heavy_grenade_launcher_796e9ebf.json')
KEY = 'weapon_reload_w220_edge_transit/edge_transit'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = '80A8A104'
ACTION_NAME = 'Armature|fp_80A8A104_reload_full|Base'
ARM_ELEMENT_RESERVE = 4 * 112
# Reach before .20 extraction; release during insertion, zero before .74 seat.
GRIP_WINDOW = (.12, .20, .64, .72)
GRIP = (8.0, 8.8, 8.5)
DRUM_ANCHOR = (8.53, 10.22, 3.11)
HINGE = (8.53, 9.67, 0.85)
CRADLE_NAMES = ('drum_latch_-1', 'drum_latch_1', 'drum_cradle_-1', 'drum_cradle_1')
BOLT_NAMES = ('charging_lug',)
KEYS = ((0.0, (0, 0, 0), (0, 0, 0), (0, 0, 0), 0, 0), (0.1, (12, -8, -10), (0.15, -0.25, 0), (0, 0, 0), 0, 0), (0.2, (40, -14, -17), (0.25, -0.55, 0.15), (0, 0, 0), 38, 0), (0.3, (64, -14, -19), (0.35, -0.65, 0.2), (-6.4, 0, 0), 38, 0), (0.42, (68, -14, -19), (0.35, -0.65, 0.2), (-6.4, -5.0, 0.2), 38, 0), (0.52, (68, -14, -19), (0.35, -0.65, 0.2), (-6.4, -5.0, 0.2), 38, 0), (0.64, (64, -14, -19), (0.35, -0.65, 0.2), (-6.4, 0, 0), 38, 0), (0.74, (60, -13, -18), (0.3, -0.55, 0.15), (0, 0, 0), 38, 0), (0.81, (55, -12, -16), (0.25, -0.45, 0.1), (0, 0, 0), 0, 0), (0.89, (39, -9, -12), (0.2, -0.3, 0.05), (0, 0, 0), 0, 0.85), (0.94, (27, -6, -7), (0.1, -0.2, 0), (0, 0, 0), 0, 0), (1.0, (0, 0, 0), (0, 0, 0), (0, 0, 0), 0, 0))

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
    """Preserve all12 authored vector/scalar knots, holds and zero extrema."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Reload progress must be finite and within0..1')
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) if isinstance(v, tuple) else v for v in key[1:])
    times = [key[0] for key in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    def channel(values):
        if values[index] == values[index+1]:
            return values[index]
        slopes = tangents(times, values)
        return (h00*values[index] + h10*h*slopes[index]
                + h01*values[index+1] + h11*h*slopes[index+1])
    return tuple([channel([key[k][axis] for key in KEYS]) for axis in range(3)]
                 if k <= 3 else channel([key[k] for key in KEYS])
                 for k in range(1,6))

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
    return e['name'].startswith(('drum_core_','drum_bay_','drum_front_rim_','drum_rear_rim_'))

def partition(source):
    parts={}
    for part in PARTS:
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if is_payload(e)==(part=='magazine')]
        parts[part]=model
    return parts

def articulated_elements(elements,p):
    """Rigid authored cradle release and action of existing solids only.
    The front pivot remains on body; the four original bracket solids open together.
    This mechanism is an adaptation of occluded handling, not extracted animation.
    """
    _,_,_,opening,bolt=sample(p)
    result=copy.deepcopy(elements)
    for e in result:
        if e['name'] in CRADLE_NAMES and opening:
            turn=xyz((opening,0,0));center=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
            old=e.get('rotation',{});origin=old.get('origin',center)
            old_angles=[old.get(axis,0) if 'axis' not in old else (old['angle'] if old['axis']==axis else 0) for axis in 'xyz']
            old_r=transpose(xyz([-v for v in old_angles]))
            actual_center=add(origin,vec(old_r,sub(center,origin)))
            new_center=add(HINGE,vec(turn,sub(actual_center,HINGE)))
            delta=sub(new_center,center)
            e['from']=add(e['from'],delta);e['to']=add(e['to'],delta)
            angles=[-v for v in euler(transpose(mul(turn,old_r)))]
            e['rotation']=dict(origin=new_center,**dict(zip('xyz',angles)))
        if e['name'] in BOLT_NAMES and bolt:
            e['from'][2]+=bolt;e['to'][2]+=bolt
            if 'rotation' in e:e['rotation']['origin'][2]+=bolt
    return result

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset,_,_=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Complete drum, both rims and all bays share exactly one rigid local transform.
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
    the fresh W220 rig/profile. Normal integration uses only root-owned paths.
    """
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE, AUTHORED_SOURCE,
              AUTHORED_MANIFEST, AUTHORED_REVIEW, AUTHORED_STORYBOARD, CONTACTS, FRAMING,
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
    payload_indices = [i for i,e in enumerate(source['elements']) if is_payload(e)]
    cradle_indices = [i for i,e in enumerate(source['elements']) if e['name'] in CRADLE_NAMES]
    bolt_indices = [i for i,e in enumerate(source['elements']) if e['name'] in BOLT_NAMES]
    if (len(source['elements']) != 96 or payload_indices != list(range(28,56))
            or len(cradle_indices) != 4 or bolt_indices != [95]
            or old.get('revision') != 1
            or old['keyframes'] != json.loads(encode(KEYS))
            or old['gripPivot'] != list(GRIP)
            or old['drumAnchor'] != list(DRUM_ANCHOR)
            or old['cradleHinge'] != list(HINGE)
            or old['cradleNames'] != list(CRADLE_NAMES)
            or old['chargingHandleNames'] != list(BOLT_NAMES)
            or old['sourceGeometryFileSha256'] != sha(raw[SOURCE])):
        raise ValueError('W18096 canonical solids,12 keys, holds, pivots and mechanisms must remain exact')
    reload = profile.get('contacts', {}).get('reload', {})
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W220'
            or profile.get('weapon') != 'edge_transit'
            or profile.get('sourceAction') != SOURCE_ACTION
            or profile.get('sourceRig', {}).get('group') != 'heavy_grenade_launcher_796e9ebf'
            or profile['sourceRig'].get('action') != SOURCE_ACTION
            or reload.get('rigAction') != SOURCE_ACTION
            or reload.get('hand') != 'left'
            or reload.get('partHint') != 'magazine'
            or reload.get('policy') != 'magazine'
            or reload.get('gripWindow') != list(GRIP_WINDOW)
            or any(profile['framing'].get(k) is not v for k,v in
                   {'sourceFullChain': True, 'keepMeshSupport': True,
                    'hideSupportAtRest': False}.items())):
        raise ValueError('Expected W220 original full-chain left magazine profile')
    current_contacts = json.loads(raw[CONTACTS])['weapons']['edge_transit']
    for side in ('right', 'left'):
        if profile['contacts'][side] != current_contacts[side]:
            raise ValueError('Existing authored mesh contact changed: ' + side)
    for name in ('contact', 'rotation'):
        if reload[name] != current_contacts['reload'][name]:
            raise ValueError('Existing authored reload contact changed: ' + name)
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
              'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != 'heavy_grenade_launcher_796e9ebf' or rig.get('fallback') is not False
            or 'edge_transit' not in rig['weapons']
            or rig.get('cameraExported') is not False
            or rig.get('w220Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME
            or (action['start'], action['end']) != (1., 142.)
            or len(action['frames']) != SAMPLES
            or any(frame['progress'] != i/INTERVALS
                   or abs(frame['frame']-(1+141*i/INTERVALS)) > 1e-10
                   or not joints <= frame['joints'].keys()
                   for i,frame in enumerate(action['frames']))):
        raise ValueError('Fresh original W22061 shoulder/elbow/wrist/weapon samples required')
    if any(rig[k] != profile['sourceRig'][k] for k in
           ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256')):
        raise ValueError('Original source provenance differs from reviewed profile')
    geometries = partition(source)
    counts = {part: len(model['elements']) for part,model in geometries.items()}
    if counts != {'body': 68, 'magazine': 28}:
        raise ValueError('Expected unchanged body68 and complete whole drum28')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W220 Edge Transit namespace')
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
                child = {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'],twohand,p,part,grip)}
                elements = articulated_elements(geometries[part]['elements'],p)
                if elements != geometries[part]['elements']:
                    child['elements'] = elements
                emit(A / f'models/{KEY}_{i:02}_{part}_{grip}.json',child)

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
        raise ValueError('Expected canonical Edge Transit ADS/inspect guard')
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type':'minecraft:select', 'property':'minecraft:display_context',
        'cases':[{'when':list(FP), 'model':guard}], 'fallback':copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion':1, 'stage':'W220', 'weapon':'edge_transit', 'revision':1,
        'generator':str(GENERATOR), 'generatorSha256':sha(raw[GENERATOR]),
        'itemModel':'destiny:'+KEY, 'frames':SAMPLES, 'intervals':INTERVALS,
        'progressFloatIndex':1, 'gripFlagIndex':0, 'firstPersonContexts':list(FP),
        'thresholdEncoding':'exact float32(i/60), matching master runtime60grid',
        'curve':'C1 weighted harmonic PCHIP; zero endpoint/hold/extremum tangents',
        'keyframes':KEYS, 'gripPivot':GRIP, 'drumAnchor':DRUM_ANCHOR,
        'cradleHinge':HINGE, 'cradleNames':CRADLE_NAMES, 'chargingHandleNames':BOLT_NAMES,
        'drumSeatedProgress':.74, 'cradleClosedProgress':.81,
        'chargingLugPeakProgress':.89, 'chargingLugReturnedProgress':.94,
        'gripWindow':list(GRIP_WINDOW),
        'authoredTimingSource':str(AUTHORED_SOURCE), 'normalizedPhases':old['normalizedPhases'],
        'reference':old['reference'], 'sourceReviewEvidence':profile['evidence'],
        'sourceGeometryPath':str(SOURCE), 'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'sourceElements':96, 'partElements':counts, 'bodyElements':68,
        'movingElements':28, 'magazineElements':28, 'weaponElements':96,
        'cradleElements':4, 'chargingHandleElements':1,
        'addedElements':0, 'triangleAdapterElements':0,
        'ordinaryArmElementReserve':ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate':96+ARM_ELEMENT_RESERVE,
        'canonicalWeaponElements':canonical_count,
        'candidateKnownCanonicalWithArmsEstimate':canonical_count+ARM_ELEMENT_RESERVE,
        'canonicalModelElements':model_counts,
        'maxAssembledElements':maximum, 'elementLimit':1000,
        'assembledBudgetVerified':False, 'measuredAllRouteElements':None,
        'budgetBasis':'Parent-resolved current canonical route maximum or active68+28, plus448 classic arm surfaces. Alternatives not summed. Master measures final materialized routes.',
        'partitionIndices':{'body':[i for i in range(96) if i not in payload_indices],
                            'magazine':payload_indices},
        'cradleIndices':cradle_indices, 'chargingHandleIndices':bolt_indices,
        'movingIndices':payload_indices,
        'movingNames':[source['elements'][i]['name'] for i in payload_indices],
        'geometryPolicy':old['geometryPolicy'], 'payloadPolicy':old['payloadPolicy'],
        'authoredHiddenDetails':old['authoredHiddenDetails'],
        'sourceElementsAndUVSha256':sha(encode(source['elements'])),
        'partElementsAndUVSha256':{part:sha(encode(m['elements'])) for part,m in geometries.items()},
        'canonicalGeometryAndUVPreserved':True, 'reloadGeometryMatchesW180':True,
        'hipEndpoints':[0,INTERVALS], 'endpointDisplayExact':True, 'fallbackModelExact':True,
        'fallback':'Exact current canonical graph at0/1,overshoot,negative inactive and nonFP; ADS/inspect cases precede reload; native/twohand retained.',
        'rigAction':SOURCE_ACTION, 'sourceAction':SOURCE_ACTION, 'rigActionName':action['action'],
        'sourceGroup':rig['group'], 'sourceRigPath':str(RIG),
        'sourceActionSourceRange':[action['start'],action['end']],
        'sourceRigSamples':len(action['frames']), 'sourceFullChain':True,
        'sourceCameraRecovered':False, 'hand':'left', 'partHint':'magazine', 'policy':'magazine',
        'motionAuthorship':'Exact12 W180 knots, empty-frame hold, complete28-solid drum, four articulated body cradle/latch solids, charging lug and transform algebra. Only interpolation becomes C1 PCHIP61. Master source_weapon_display replaces the authored carrier with the source weapon matrix and retains relative mechanism transforms, avoiding a second body replay. No source retiming, stretch, damping or support hiding.',
        'gameplayTimingChanged':False, 'mechanicsOrAudioChanged':False,
        'timingPolicy':old['timingPolicy'],
        'nativeGameplayVerified':False, 'nativeVisibilityAccepted':False,
        'packFiles':len(output), 'totalReturnedFiles':len(allowed),
        'staticParts':2, 'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'limitations':[
            'Worker read master original Blender evaluation and viewed actual bone sheet; no independent Blender opening claimed.',
            'ARMATURE only: no original weapon mesh, camera, finger IK or measured hidden drum path. Mesh contacts remain authored.',
            '61 poses/60 intervals do not establish continuous native60fps interpolation.',
            'Left grip attachment ramps.12..20, fades.64..72; zero before.74 seat, .81 cradle closure and .89..94 lug action. FIRST contact review pending.',
            'Current route element counts plus448 reserve are bounded; final materialized arms/routes require master verification.',
            'FIRST PNG review, same-worker correction or justified no-change, and master SECOND pending.'],
        'inputSha256':{str(path):sha(data) for path,data in raw.items()},
        'outputSha256':{str(path.relative_to(root)):sha(data) for path,data in output.items()}})
    if set(output) != {root/path for path in allowed}:
        raise ValueError('Incomplete W220 Edge Transit output mapping')
    return output
