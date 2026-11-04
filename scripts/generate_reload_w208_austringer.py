#!/usr/bin/env python3
"""W208 Austringer: C1 W168 cylinder reload and unchanged W123 solids/UV.

Import and generate(root=ROOT) only read; the master owns pack materialization.
Authored reference-informed motion; no recovered camera or finger IK claim.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
SOURCE = ASSET / "models/weapon_surface_w123/austringer.json"
TWOHAND = ASSET / "models/weapon/hand_cannon/austringer_twohand.json"
ITEM = ASSET / "items/weapon/austringer.json"
TEXTURE = ASSET / "textures/item/weapon/w123/austringer.png"
KEY = "weapon_reload_w208_austringer/austringer"
MANIFEST = Path("art/weapons/w208/austringer/manifest.json")
PROFILE = Path("art/weapons/w208/austringer/profile.json")
RIG = Path("art/weapons/w205/rigs/hand_cannon_e762ed5f.json")
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = INTERVALS + 1
# Current W168 authored normalized phases, not new gameplay duration values.
MOVING = tuple(range(32,44))

NAMES = tuple([f'Cylinder_{i}' for i in range(4)] +
              [f'Cylinder_{end}_band_{i}' for end in ('front','rear') for i in range(4)])

FIXED_FRAME = (44,45,46,47)

GRIP = (8,9.38,7.515)  # Current Grip_palm rotation origin.

HINGE = (7.3,11.06,4.34)  # Authored left-lower cylinder crane approximation.

KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.09,(8,-6,-12),(-.05,-.10,0),(0,0,68)),
 (.20,(48,-8,-16),(.15,-.10,-.15),(0,0,78)),
 (.29,(70,-5,-10),(.25,-.20,-.25),(0,0,78)),
 (.50,(65,-6,-12),(.25,-.20,-.25),(0,0,78)),
 (.62,(18,-10,18),(.10,-.35,-.10),(0,0,78)),
 (.76,(3,-8,23),(0,-.45,0),(0,0,78)),
 (.84,(0,-3,-12),(0,-.20,0),(0,0,12)),
 (.90,(6,2,-6),(0,-.05,0),(0,0,0)),
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
            vector.append(h00*values[index] + h10*h*slopes[index]
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

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,cylinder=sample(p)
    body=xyz(angles);component=xyz(cylinder if part=='moving' else (0,0,0))
    h=sub(GRIP,(8,8,8));c=sub(HINGE,(8,8,8))
    # Independent cylinder rotation around its crane, then whole gun around grip.
    local=add(sub(h,vec(body,h)),vec(body,sub(c,vec(component,c))))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if len(set(scale))!=1: raise ValueError('Rigid motion requires uniform FP scale')
        if twohand[context]['scale']!=scale: raise ValueError('Grip scale mismatch')
        rotation=mul(mul(base,body),component)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display


def generate(root=ROOT):
    """Return absolute Path -> bytes; never materialize pack or art outputs."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE, PROFILE, RIG,
              Path('scripts/generate_reload_w168_austringer.py'),
              Path('art/weapons/w168/austringer/motion-reference.json')]
    raw = {p: (root/p).read_bytes() for p in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])['display']
    item = json.loads(raw[ITEM])
    reference = json.loads(raw[inputs[-1]])
    elements = source['elements']
    if (len(elements) != 126 or
            [elements[i]['name'] for i in MOVING] != list(NAMES) or
            [elements[i]['name'] for i in FIXED_FRAME] !=
            ['Cylinder_lower_frame', 'Breech', 'Top_frame', 'Top_gold_rod']):
        raise ValueError('Current Austringer cylinder/frame partition requires re-audit')
    rig = json.loads(raw[RIG])
    if (rig['fallback'] or 'austringer' not in rig['weapons'] or
            '80A8A53D' not in rig['actions']):
        raise ValueError('Expected Austringer evaluated reload rig is missing')
    output = {}

    def emit(path, value):
        allowed = (ASSET/'models/weapon_reload_w208_austringer',
                   ASSET/'items/weapon_reload_w208_austringer')
        if path != MANIFEST and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError('Output outside owned W208 Austringer namespace')
        output[root/path] = encode(value)

    counts = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items()
               if k not in ('elements', 'display')}
        geo['elements'] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == 'moving')]
        counts[part] = len(geo['elements'])
        emit(ASSET/f'models/{KEY}_{part}.json', geo)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ('native', 'twohand'):
                emit(ASSET/f'models/{KEY}_{frame:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand, progress, part, grip)})

        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in PARTS]}

        # Canonical endpoints restore ADS/inspect/idle selections exactly.
        model = copy.deepcopy(item['model']) if frame in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': model})
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {
        'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': {
            'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
            'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}}],
        'fallback': copy.deepcopy(item['model'])}
    emit(ASSET/f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W208', 'weapon': 'austringer',
        'generator': 'scripts/generate_reload_w208_austringer.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': f'destiny:{KEY}', 'frames': SAMPLES, 'intervals': INTERVALS,
        'packFiles': 247, 'generatedFiles': 248, 'staticParts': 2,
        'parentDisplayChildren': 244, 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'thresholdEncoding': 'float32(i/60), matching runtime float quantization',
        'curve': 'C1 shape-preserving PCHIP, harmonic moving-knot tangents, zero endpoint/hold/extremum tangents',
        'keyframes': KEYS, 'gripPivot': GRIP, 'cylinderHinge': HINGE,
        'sourceCubes': len(elements), 'sourceFaces': sum(len(e['faces']) for e in elements),
        'partCubes': counts, 'maxAssembledElements': len(elements), 'elementLimit': 1000,
        'movingIndices': MOVING, 'movingNames': NAMES, 'fixedFrameIndices': FIXED_FRAME,
        'geometryAndUVUnchanged': True, 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'rotationConvention': 'Rx Ry Rz; R_idle * R_body * R_cylinder; hinge affine then grip affine; static twohand carrier compensation',
        'normalizedPhases': {'rollOpen': [0, .09], 'raiseEjectionGesture': [.09, .29],
            'openHold': [.29, .50], 'lowerLoaderContact': [.50, .76],
            'closeFlick': [.76, .90], 'recover': [.90, 1]},
        'evidence': {'url': reference['url'], 'sourceObservedSeconds': reference['selectedSeconds'],
            'sourceFrameCount': len(reference['frames']), 'rig': str(RIG),
            'rigAction': '80A8A53D', 'rigActionFrames': len(rig['actions']['80A8A53D']['frames']),
            'cameraExported': rig['cameraExported']},
        'gameplayTimingChanged': False, 'ammoOrAudioChanged': False,
        'nativeGameplayVerified': False, 'recoveredCamera': False, 'fingerIK': False,
        'limitations': [
            'W168 angles, hinge and normalized phase timing remain authored approximations.',
            'The 12 gameplay frames use a dark/silver appearance; W123 default gold/purple UV is retained.',
            'Shared-family evaluated rig supplies arm directions; moving mesh contacts remain authoritative.',
            'No case, cartridge, speedloader or crane linkage geometry is added.',
            '61 bank poses remove /20 quantization; server-paced updates are not proof of 60fps.',
            'Shared profile loader, runtime routing, rig whitelist and native QA belong to master.'],
        'inputSha256': {str(p): sha(b) for p, b in raw.items()},
        'outputSha256': {str(p.relative_to(root)): sha(b) for p, b in output.items()}})
    if len(output) != 248:
        raise ValueError('Unexpected W208 output count')
    return output
