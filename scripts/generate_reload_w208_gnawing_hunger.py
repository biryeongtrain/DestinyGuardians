#!/usr/bin/env python3
"""W208 Gnawing Hunger: C1 motion over the unchanged W164 authored timeline.

Import and generate(root=ROOT) never write; master materializes returned assets.
Source-rig directions are calibration only; no recovered weapon camera/hand IK.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
SOURCE = ASSET / "models/weapon_surface_w123/gnawing_hunger.json"
TWOHAND = ASSET / "models/weapon/auto_rifle/gnawing_hunger_twohand.json"
ITEM = ASSET / "items/weapon/gnawing_hunger.json"
KEY = "weapon_reload_w208_gnawing_hunger/gnawing_hunger"
MANIFEST = Path("art/weapons/w208/gnawing_hunger/manifest.json")
PROFILE = MANIFEST.with_name("profile.json")
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
MOVING = (54, 55, 56, 57, 58)
NAMES = ("neck", "upper", "middle", "lower", "floorplate")
GRIP = (8, 9.2, 8.1)
INTERVALS = 60
SAMPLES = INTERVALS + 1
# W164 reference-informed timing, including the complete .38..50 handling hold.
KEYS = (
    (0., (0,0,0), (0,0,0), (0,0,0)),
    (.12, (25,-8,-15), (-.3,.6,-.4), (0,0,0)),
    (.24, (43,-14,-24), (-.5,1.0,-.8), (-.3,-1.8,.1)),
    (.38, (40,-14,-25), (-.5,.9,-.8), (-1.2,-6.0,.5)),
    (.50, (40,-14,-25), (-.5,.9,-.8), (-1.2,-6.0,.5)),
    (.64, (42,-13,-24), (-.5,1.0,-.8), (-.4,-2.4,.2)),
    (.74, (47,-12,-22), (-.4,1.2,-.9), (0,0,0)),
    (.82, (38,-9,-18), (-.2,.7,-.7), (0,0,0)),
    (1., (0,0,0), (0,0,0), (0,0,0)),
)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]

def tangents(times, values):
    """Shape-preserving PCHIP: shared derivative at knots; zero at holds/extrema.

    Weighted harmonic means preserve monotone spans without overshoot. Endpoint
    slopes are explicitly zero to settle into and out of the accepted idle pose.
    """
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
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) for v in key[1:])
    times = [k[0] for k in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    result = []
    for channel in range(1, 4):
        vector = []
        for axis in range(3):
            values = [k[channel][axis] for k in KEYS]
            slopes = tangents(times, values)
            # Equal neighbors are a deliberate hold; avoid cancellation drift.
            if values[index] == values[index+1]:
                vector.append(values[index])
            else:
                vector.append(h00*values[index] + h10*h*slopes[index]
                              + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)

def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def vec(m, v):
    return [sum(m[i][j]*v[j] for j in range(3)) for i in range(3)]

def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]

def euler(m):
    y = math.asin(max(-1, min(1, m[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0])
    else:
        x, z = math.atan2(m[2][1], m[1][1]), 0
    return [round(math.degrees(v), 9) for v in (x, y, z)]

def add(a,b): return [x+y for x,y in zip(a,b)]

def sub(a,b): return [x-y for x,y in zip(a,b)]

def transpose(m): return list(map(list,zip(*m)))

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    local=add(sub(h,vec(body,h)),vec(body,offset if part=='moving' else (0,0,0)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if len(set(s))!=1: raise ValueError('Rigid part motion requires uniform first-person scale')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def generate(root=ROOT):
    """Return absolute Path -> bytes only; do not materialize generated assets."""
    root = Path(root).resolve()
    source = json.loads((root/SOURCE).read_bytes())
    twohand = json.loads((root/TWOHAND).read_bytes())['display']
    item = json.loads((root/ITEM).read_bytes())
    expected_names = ['magazine/'+name for name in NAMES]
    if len(source['elements']) != 114 or [source['elements'][i]['name'] for i in MOVING] != expected_names:
        raise ValueError('Current W123 Gnawing Hunger partition drift: expected 109 body + 5 magazine')
    output = {}
    allowed = (ASSET/'models/weapon_reload_w208_gnawing_hunger',
               ASSET/'items/weapon_reload_w208_gnawing_hunger')
    def emit(path, value):
        if path != MANIFEST and not any(path.is_relative_to(prefix) for prefix in allowed):
            raise ValueError('Output outside owned W208 Gnawing Hunger namespace')
        output[root/path] = encode(value)
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k,v in source.items() if k not in ('elements','display')}
        geo['elements'] = [copy.deepcopy(e) for i,e in enumerate(source['elements'])
                           if (i in MOVING) == (part == 'moving')]
        emit(ASSET/f'models/{KEY}_{part}.json', geo)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ('native','twohand'):
                emit(ASSET/f'models/{KEY}_{frame:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand, progress, part, grip)})
        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type':'minecraft:model', 'model':f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in PARTS]}
        model = copy.deepcopy(item['model']) if frame in (0,INTERVALS) else {
            'type':'minecraft:condition', 'property':'minecraft:custom_model_data', 'index':0,
            'on_true':composite('twohand'), 'on_false':composite('native')}
        entries.append({'threshold':float32(progress), 'model':model})
    dispatch = {'type':'minecraft:range_dispatch', 'property':'minecraft:custom_model_data',
                'index':1, 'entries':entries, 'fallback':copy.deepcopy(item['model'])}
    # Preserve explicit canonical modes even if stale reload progress is present.
    # Individual string cases also preserve the shared hand builder's mode state.
    modes = {'type':'minecraft:select', 'property':'minecraft:custom_model_data', 'index':0,
             'cases':[{'when':mode, 'model':copy.deepcopy(item['model'])} for mode in ('ads','inspect')],
             'fallback':dispatch}
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type':'minecraft:select', 'property':'minecraft:display_context',
        'cases':[{'when':list(FP), 'model':modes}], 'fallback':copy.deepcopy(item['model'])}
    emit(ASSET/f'items/{KEY}.json',wrapper)
    inputs = [SOURCE,TWOHAND,ITEM,PROFILE,Path('scripts/generate_reload_w164_gnawing_hunger.py'),
              Path('art/weapons/w205/rigs/auto_rifle_943c13a2.json')]
    emit(MANIFEST, {
        'schemaVersion':1, 'stage':'W208', 'weapon':'gnawing_hunger',
        'generator':'scripts/generate_reload_w208_gnawing_hunger.py',
        'generatorSha256':sha(Path(__file__).read_bytes()), 'itemModel':f'destiny:{KEY}',
        'frames':SAMPLES, 'intervals':INTERVALS, 'packFiles':247, 'generatedOutputs':248,
        'staticParts':2, 'parentDisplayChildren':244, 'progressFloatIndex':1, 'gripFlagIndex':0,
        'thresholdEncoding':'float32(i/60), matching runtime float encoding',
        'curve':'C1 shape-preserving cubic Hermite; weighted harmonic moving tangents; zero endpoint/hold/extremum velocities',
        'keyframes':KEYS, 'gripPivot':GRIP, 'movingIndices':list(MOVING), 'movingNames':expected_names,
        'sourceElements':114, 'bodyElements':109, 'movingElements':5, 'partCubes':{'body':109,'moving':5},
        'maxAssembledElements':114, 'elementLimit':1000, 'geometryAndUVUnchanged':True,
        'endpointDisplayExact':True, 'fallbackModelExact':True,
        'rotationConvention':'W164 JOML Rx Ry Rz; R_idle * R_body; fixed grip pivot; local magazine displacement rotated and scaled once, then twohand carrier compensation',
        'sourceRig':'auto_rifle_943c13a2', 'rigAction':'80A8A395',
        'sourceCameraRecovered':False, 'nativeGameplayVerified':False,
        'gameplayTimingChanged':False, 'mechanicsOrAudioChanged':False,
        'evidence':['https://www.youtube.com/watch?v=3XU0AygDiKI',
                    'art/weapons/w164/gnawing_hunger/motion-reference.json',
                    'art/weapons/w164/gnawing_hunger/storyboard.png'],
        'limitations':['W164 authored normalized timing retained; source hand occlusion prevents exact magazine trajectory claims.',
                       'Shared 395/38C/38A source actions are ambiguous; 395 is direction calibration only.',
                       '61 poses do not establish 60fps; server updates remain runtime paced.',
                       'Shared loader, runtime routing, rig whitelist and native skin-arm QA belong to master.'],
        'inputSha256':{str(p):sha((root/p).read_bytes()) for p in inputs},
        'outputSha256':{str(p.relative_to(root)):sha(raw) for p,raw in output.items()}})
    return output
