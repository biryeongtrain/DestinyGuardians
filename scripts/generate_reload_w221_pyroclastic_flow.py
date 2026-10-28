#!/usr/bin/env python3
"""Pure W221 Pyroclastic Flow reload candidate. Import/generate never writes.

Only mechanical parts are authored here; master replays source weapon/arms.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w221/pyroclastic_flow')
GENERATOR = Path('scripts/generate_reload_w221_pyroclastic_flow.py')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
SOURCE = A / 'models/weapon_surface_w123/pyroclastic_flow.json'
NATIVE = A / 'models/weapon/rocket_launcher/pyroclastic_flow.json'
TWOHAND = A / 'models/weapon/rocket_launcher/pyroclastic_flow_twohand.json'
ITEM = A / 'items/weapon/pyroclastic_flow.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
RIG = Path('art/weapons/w221/rigs/rocket_launcher_1a221f25.json')
KEY = 'weapon_reload_w221_pyroclastic_flow/pyroclastic_flow'
SOURCE_GROUP = 'rocket_launcher_1a221f25'
SOURCE_ACTION = '80A8A1A2'
ACTION_NAME = 'Armature|fp_80A8A1A2_reload_full|Base'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
PARTS = ('body', 'magazine', 'cradle', 'lever')
SAMPLES, INTERVALS = 61, 60
ARM_ELEMENT_RESERVE = 448
GRIP_WINDOW = (.18, .28, .56, .66)
MAGAZINE_ANCHOR = (8., 11.7, 14.8)
CRADLE_PIVOT = (8., 9.4, 16.43)
LEVER_PIVOT = (8., 9.55, 16.9)
CRADLE_NAMES = ('rear_socket_floor', 'rear_socket_lip')
LEVER_NAMES = ('rear_latch',)
# p, cradle-X, latch-X, projectile-X/Y/Z offset, projectile-X tilt, visibility.
# Local projectile axis is -Z, toward launch tube. No authored body sweep.
KEYS = (
    (0., 0., 0., (0., 0., 0.), 0., 0.),
    (.08, 0., -24., (0., 0., 0.), 0., 0.),
    (.18, 42., -24., (0., 0., 10.), -8., 0.),
    (.28, 42., -24., (0., 0., 10.), -8., 1.),
    (.46, 42., -24., (0., 0., 10.), -8., 1.),
    (.56, 42., -24., (0., 0., 7.), -4., 1.),
    (.66, 42., -24., (0., 0., 3.), 0., 1.),
    (.72, 42., -24., (0., 0., 0.), 0., 1.),
    (.76, 42., -24., (0., 0., 0.), 0., 0.),
    (.84, 0., -24., (0., 0., 0.), 0., 0.),
    (.89, 0., 0., (0., 0., 0.), 0., 0.),
    (1., 0., 0., (0., 0., 0.), 0., 0.),
)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def tangents(times, values):
    """C1 harmonic PCHIP with zero endpoints, holds and extrema."""
    steps = [b-a for a, b in zip(times, times[1:])]
    secants = [(b-a)/h for a, b, h in zip(values, values[1:], steps)]
    slopes = [0.] * len(times)
    for i in range(1, len(times)-1):
        before, after = secants[i-1], secants[i]
        if before*after > 0:
            w1, w2 = 2*steps[i]+steps[i-1], steps[i]+2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before+w2/after)
    return slopes


def curve(progress, values):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Progress must be finite in0..1')
    times = [k[0] for k in KEYS]
    if progress in times:
        return values[times.index(progress)]
    i = next(i for i in range(len(times)-1) if progress < times[i+1])
    if values[i] == values[i+1]:
        return values[i]
    h = times[i+1]-times[i]
    t = (progress-times[i])/h
    slopes = tangents(times, values)
    return ((2*t**3-3*t*t+1)*values[i] + (t**3-2*t*t+t)*h*slopes[i]
            + (-2*t**3+3*t*t)*values[i+1] + (t**3-t*t)*h*slopes[i+1])


def sample(progress):
    return {
        'cradle': curve(progress, [k[1] for k in KEYS]),
        'lever': curve(progress, [k[2] for k in KEYS]),
        'offset': [curve(progress, [k[3][a] for k in KEYS]) for a in range(3)],
        'tilt': curve(progress, [k[4] for k in KEYS]),
        'visibility': curve(progress, [k[5] for k in KEYS]),
    }


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def vec(m, v):
    return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c], [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(m):
    y = math.asin(max(-1., min(1., m[0][2])))
    x, z = ((math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0]))
            if abs(math.cos(y)) > 1e-8 else (math.atan2(m[2][1], m[1][1]), 0.))
    return [round(math.degrees(v), 9) for v in (x, y, z)]


def projectile_elements(source):
    """Eight connected reload-only solids; actual opaque existing face UVs.

    Long axis -Z matches launch_tube_0..7. The narrower nose leads the seat.
    No receiver, optic, tube or decorative shell is relabelled as ammunition.
    """
    templates = {e['name']: e for e in source['elements']}
    def solid(name, lo, hi, template, diagonal=False):
        e = copy.deepcopy(templates[template])
        e.pop('rotation', None)
        e.update(name=name, **{'from': lo, 'to': hi})
        if diagonal:
            e['rotation'] = {'origin': list(MAGAZINE_ANCHOR), 'axis': 'z', 'angle': 45}
        return e
    result = []
    for diagonal in (False, True):
        suffix = 'diagonal' if diagonal else 'core'
        result.append(solid('reload_rocket_'+suffix, [7.55,11.25,12.0], [8.45,12.15,17.5], 'launch_tube_0', diagonal))
        result.append(solid('reload_rocket_nose_'+suffix, [7.7,11.4,10.7], [8.3,12.0,12.1], 'optic_upper_bracket', diagonal))
        result.append(solid('reload_rocket_collar_'+suffix, [7.5,11.2,16.9], [8.5,12.2,17.5], 'receiver_band_0', diagonal))
    result.append(solid('reload_rocket_fin_vertical', [7.92,10.95,16.0], [8.08,12.45,17.3], 'barrel_fin_-1'))
    result.append(solid('reload_rocket_fin_horizontal', [7.25,11.62,16.0], [8.75,11.78,17.3], 'barrel_fin_1'))
    return result


def partition(source):
    result = {}
    for part in PARTS:
        model = {k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'}
        if part == 'magazine':
            elements = projectile_elements(source)
        else:
            names = CRADLE_NAMES if part == 'cradle' else LEVER_NAMES
            elements = [copy.deepcopy(e) for e in source['elements'] if
                        (e['name'] not in CRADLE_NAMES+LEVER_NAMES if part == 'body' else e['name'] in names)]
        model['elements'] = elements
        result[part] = model
    return result


def pose_display(original, twohand, progress, part, grip):
    if part not in PARTS or grip not in GRIPS:
        raise ValueError((part, grip))
    accepted = original if grip == 'native' else twohand
    out = copy.deepcopy(accepted)
    pose = sample(progress)
    pivot = MAGAZINE_ANCHOR if part == 'magazine' else CRADLE_PIVOT if part == 'cradle' else LEVER_PIVOT
    angle = pose['tilt'] if part == 'magazine' else pose.get(part, 0.)
    motion = xyz([angle, 0., 0.])
    visibility = pose['visibility'] if part == 'magazine' else 1.
    pivot = sub(pivot, [8., 8., 8.])
    local = sub(pivot, vec(motion, [visibility*v for v in pivot]))
    if part == 'magazine':
        local = add(local, pose['offset'])
    if part == 'body' or (part != 'magazine' and progress in (0., 1.)):
        return out
    for context in FP:
        idle = accepted[context]
        base = xyz(idle['rotation'])
        scale = idle['scale']
        if len(set(scale)) != 1:
            raise ValueError('Uniform canonical part scale required')
        out[context] = {
            'rotation': euler(mul(base, motion)),
            'translation': [round(v, 9) for v in add(idle['translation'], vec(base, [scale[0]*v for v in local]))],
            'scale': [round(v*visibility, 9) for v in scale],
        }
    return out


def expected_output_paths():
    result = {A / f'models/{KEY}_{part}.json' for part in PARTS}
    result.update(A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
                  for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return result | {A / f'items/{KEY}.json', MANIFEST}


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    root = Path(root).resolve()
    def input_path(override, default):
        path = Path(override) if override is not None else default
        return path if path.is_absolute() else root / path
    profile_raw = input_path(profile_path, PROFILE).read_bytes()
    profile = json.loads(profile_raw)
    rig_raw = input_path(rig_path, RIG).read_bytes()
    rig = json.loads(rig_raw)
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W221'
            or profile.get('weapon') != 'pyroclastic_flow' or profile.get('sourceAction') != SOURCE_ACTION):
        raise ValueError('Invalid W221 Pyroclastic Flow profile')
    raw = {Path(p): (root / p).read_bytes() for p in profile['canonicalSha256']}
    for path, data in raw.items():
        if sha(data) != profile['canonicalSha256'][str(path)]:
            raise ValueError('Canonical input drift: '+str(path))
    source, twohand, item = (json.loads(raw[p]) for p in (SOURCE, TWOHAND, ITEM))
    twohand = twohand['display']
    canonical = item['model']
    if (canonical.get('type') != 'minecraft:select'
            or canonical.get('property') != 'minecraft:custom_model_data'
            or canonical.get('index', 0) != 0
            or [c['when'] for c in canonical['cases']] != ['ads', 'inspect']):
        raise ValueError('Canonical ADS/inspect graph guard changed')
    joints = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist', 'rightShoulder', 'rightElbow', 'rightWrist'}
    action = rig['actions'][SOURCE_ACTION]
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or 'pyroclastic_flow' not in rig['weapons'] or rig.get('cameraExported') is not False
            or rig.get('w221Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1., 113.)
            or len(action['frames']) != SAMPLES
            or any(f['progress'] != i/INTERVALS or abs(f['frame']-(1+112*i/INTERVALS)) > 1e-10
                   or not joints <= f['joints'].keys() for i, f in enumerate(action['frames']))):
        raise ValueError('Fresh original Blender61 shoulder chains required')
    provenance = profile['sourceRig']
    if (provenance.get('path') != str(RIG) or provenance.get('group') != SOURCE_GROUP
            or provenance.get('action') != SOURCE_ACTION or provenance.get('sha256') != sha(rig_raw)
            or any(provenance.get(k) != rig.get(k) for k in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'))):
        raise ValueError('Source provenance drift')
    framing = profile['framing']
    if (framing != {'translation':[0,0,0], 'rotation':[0,0,0], 'scale':1, 'rightWristRoll':15,
                   'sourceFullChain':True, 'keepMeshSupport':True, 'hideSupportAtRest':False, 'sourceViewRotation':[0,0,0]}
            or profile['contacts'] != {'reload':{'rigAction':SOURCE_ACTION, 'hand':'left', 'policy':'magazine',
                'partHint':'magazine', 'contact':list(MAGAZINE_ANCHOR), 'rotation':[0,0,0], 'gripWindow':list(GRIP_WINDOW)}}):
        raise ValueError('Source-palm/seat-release contract changed')
    geometries = partition(source)
    counts = {part:len(model['elements']) for part, model in geometries.items()}
    original_partition = [e for part in ('body','cradle','lever') for e in geometries[part]['elements']]
    if (len(source['elements']) != 106 or counts != {'body':103,'magazine':8,'cradle':2,'lever':1}
            or sorted(map(encode, original_partition)) != sorted(map(encode, source['elements']))):
        raise ValueError('Canonical106-element/UV partition changed')
    canonical_count = len(json.loads(raw[NATIVE])['elements'])
    estimate = max(canonical_count, sum(counts.values())) + ARM_ELEMENT_RESERVE
    if estimate > 1000:
        raise ValueError('Assembled element reserve exceeded')
    allowed = expected_output_paths()
    output = {}
    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside owned W221 namespace')
        output[root/path] = encode(value)
    for part, model in geometries.items():
        emit(A/f'models/{KEY}_{part}.json', model)
    entries = []
    for i in range(SAMPLES):
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json', {
                    'parent':f'destiny:{KEY}_{part}',
                    'display':pose_display(source['display'],twohand,i/INTERVALS,part,grip)})
        def composite(grip):
            return {'type':'minecraft:composite','models':[
                {'type':'minecraft:model','model':f'destiny:{KEY}_{i:02}_{part}_{grip}'} for part in PARTS]}
        node = copy.deepcopy(canonical) if i in (0,INTERVALS) else {
            'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,
            'on_true':composite('twohand'),'on_false':composite('native')}
        entries.append({'threshold':float32(i/INTERVALS),'model':node})
    dispatch = {'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':1,
                'entries':entries,'fallback':copy.deepcopy(canonical)}
    guard = copy.deepcopy(canonical)
    guard['fallback'] = dispatch
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':list(FP),'model':guard}],'fallback':copy.deepcopy(canonical)}
    emit(A/f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion':1,'stage':'W221','weapon':'pyroclastic_flow','generator':str(GENERATOR),
        'generatorSha256':sha(Path(__file__).read_bytes()),'profileSha256':sha(profile_raw),
        'itemModel':'destiny:'+KEY,'frames':SAMPLES,'intervals':INTERVALS,'progressFloatIndex':1,
        'gripFlagIndex':0,'firstPersonContexts':list(FP),'thresholdEncoding':'exact float32(i/60)',
        'curve':'C1 harmonic PCHIP; shared zero endpoint/hold/extremum tangents', 'keyframes':KEYS,
        'sourceAction':SOURCE_ACTION,'rigAction':SOURCE_ACTION,'sourceGroup':SOURCE_GROUP,
        'sourceRigPath':str(RIG),'sourceRigSha256':sha(rig_raw),'sourceRigSamples':SAMPLES,
        'rigActionName':ACTION_NAME,'sourceActionSourceRange':[1,113],'sourceFullChain':True,
        'sourceActionWeaponExclusive':False,'sourceCameraRecovered':False,
        'sourceRig':provenance,'sourceReviewEvidence':profile['evidence'],
        'sourceGeometryPath':str(SOURCE),'sourceGeometryFileSha256':sha(raw[SOURCE]),
        'partElements':counts,'weaponElements':sum(counts.values()),'sourceElements':106,
        'addedElements':8,'triangleAdapterElements':0,'ordinaryArmElementReserve':ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate':sum(counts.values())+ARM_ELEMENT_RESERVE,
        'canonicalWeaponElements':canonical_count,'maxAssembledElements':estimate,'elementLimit':1000,
        'assembledBudgetVerified':False,'measuredAllRouteElements':None,
        'budgetBasis':'114 reload +448 reserve=562; raw canonical228+448=676. Master measures actual all routes.',
        'partitionNames':{part:[e['name'] for e in model['elements']] for part,model in geometries.items()},
        'partElementsAndUVSha256':{part:sha(encode(model['elements'])) for part,model in geometries.items()},
        'canonicalGeometryAndUVPreserved':True,'geometryAndUVPreserved':True,
        'reloadHand':'left','stabilizingHand':'right','policy':'magazine','partHint':'magazine',
        'reloadGripWindow':GRIP_WINDOW,'gripWindow':GRIP_WINDOW,'magazineAnchor':MAGAZINE_ANCHOR,
        'magazineNeutralSeatedProgress':.72,'cradlePivot':CRADLE_PIVOT,'leverPivot':LEVER_PIVOT,
        'payloadAxis':[0,0,-1],'payloadVisibilityKnots':[[k[0],k[5]] for k in KEYS],
        'payloadVisibleSampleIndices':[i for i in range(SAMPLES) if sample(i/INTERVALS)['visibility']>0],
        'partitionRationale':'Keep receiver/tube/cowling/sights intact. Existing socket floor/lip pivot on rear hinge; rear latch unlocks.8 added incoming-rocket solids use existing opaque UV templates.',
        'motionAuthorship':'Only geometry-based closure and projectile motion authored; body display stays canonical. Shared master replays original weapon bone and ordinary full-chain arms once. Source palm unchanged; attached projectile alone translates.',
        'hipEndpoints':[0,INTERVALS],'endpointDisplayExact':True,'fallbackModelExact':True,
        'endpointPolicy':'Canonical whole item graph at0/1; negative fallback/nonFP/ADS/inspect preserved.',
        'gameplayTimingChanged':False,'mechanicsOrAudioChanged':False,'handIK':False,
        'nativeGameplayVerified':False,'nativeVisibilityAccepted':False,'thirdPersonReloadClaimed':False,
        'staticParts':len(PARTS),'parentDisplayChildren':SAMPLES*len(PARTS)*len(GRIPS),
        'packFiles':len(output),'totalReturnedFiles':len(allowed),'canonicalSha256':profile['canonicalSha256'],
        'inputSha256':{str(p):sha(b) for p,b in raw.items()},
        'outputSha256':{str(p.relative_to(root)):sha(b) for p,b in output.items()},
        'limitations':profile['notes'],
    })
    if set(output) != {root/p for p in allowed}:
        raise ValueError('Incomplete W221 output mapping')
    return output
