#!/usr/bin/env python3
"""W221 IKelos: pure stdlib 61-pose INITIAL/LOOP/RETURN shell banks.

Import and generate only read inputs and return absolute Path -> bytes.
Shared source body/limb calibration and materialization belong to master.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
WEAPON = 'ikelos_sg_v1_0_1'
ART = Path('art/weapons/w221')/WEAPON
KEY = 'weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1'
SOURCE = A/'models/weapon_surface_w123/ikelos_sg_v1_0_1.json'
TWOHAND = A/'models/weapon/shotgun/ikelos_sg_v1_0_1_twohand.json'
ITEM = A/'items/weapon/ikelos_sg_v1_0_1.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
RIG = Path('art/weapons/w221/rigs/shotgun_2eb0529e.json')
SURFACE_MANIFEST = Path('src/main/resources/weapon_surface_w123/manifest.json')
ACTION = '80A8A3F1'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
PARTS = ('body', 'shell')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = 61
ARM_RESERVE = 448
# Preserve W201 carrier grip. Port derives from lower_receiver_rear:
# X midpoint, Y underside -.32 clearance, Z front +.95 shell half-length.
GRIP = (8., 8.65, 8.88)
SHELL_ANCHOR = (8., 10.16, 5.80)
HOLD = ((12., -4., -28.), (-.18, .30, .10))
# Authored port presentation, not source camera or recovered shell events.
BODY_KEYS = {
    'initial': ((0., (0,0,0), (0,0,0)),
                (.16, (5,-1.5,-11), (-.06,.10,.03)),
                (.36, *HOLD), (1., *HOLD)),
    'loop': ((0., *HOLD), (1., *HOLD)),
    'return': ((0., *HOLD), (.30, (9,-3,-21), (-.13,.22,.07)),
               (.72, (2,-.7,-4), (-.025,.04,.01)),
               (1., (0,0,0), (0,0,0))),
}
HOME = (-1.25, -2.0, 1.70)
SEATED = (0., .52, -1.35)
SHELL_KEYS = {
    'initial': ((0., HOME), (.36, HOME), (.43, HOME),
                (.60, (-.45,-.95,1.05)), (.72, (0.,-.10,.60)),
                (.84, SEATED), (.90, SEATED), (1., HOME)),
    'loop': ((0., HOME), (.15, HOME), (.20, HOME),
             (.43, (-.45,-.95,1.05)), (.59, (0.,-.10,.60)),
             (.78, SEATED), (.85, SEATED), (1., HOME)),
    'return': ((0., HOME), (1., HOME)),
}
VISIBLE = {'initial': (.43, .84), 'loop': (.20, .78)}
UV_DONORS = {'case': 'lower_receiver_rear', 'head': 'capacitor_0_-1',
             'rim': 'capacitor_0_-1', 'crimp': 'muzzle_roof'}

def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vec(matrix, value):
    return [sum(matrix[i][k]*value[k] for k in range(3)) for i in range(3)]


def transpose(matrix):
    return list(map(list, zip(*matrix)))


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(matrix):
    y = math.asin(max(-1., min(1., matrix[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(-matrix[1][2], matrix[2][2]), math.atan2(-matrix[0][1], matrix[0][0])
    else:
        x, z = math.atan2(matrix[2][1], matrix[1][1]), 0
    return [round(math.degrees(v), 9) for v in (x, y, z)]


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

def threshold(phase_index, frame):
    # Java phase*2+(float)frame/intervals: round division BEFORE addition.
    return float32(phase_index*2 + float32(frame/INTERVALS))


def interpolate(keys, progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Progress must be finite within 0..1')
    for time, value in keys:
        if progress == time:
            return list(value)
    times = [k[0] for k in keys]
    index = next(i for i in range(len(keys)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    result = []
    for axis in range(3):
        values = [k[1][axis] for k in keys]
        slopes = tangents(times, values)
        if values[index] == values[index+1]:
            result.append(values[index])
            continue
        result.append(h00*values[index] + h10*h*slopes[index]
                      + h01*values[index+1] + h11*h*slopes[index+1])
    return result


def sample(phase, progress):
    if phase not in PHASES:
        raise ValueError(phase)
    return (interpolate(tuple((k[0], k[1]) for k in BODY_KEYS[phase]), progress),
            interpolate(tuple((k[0], k[2]) for k in BODY_KEYS[phase]), progress),
            interpolate(SHELL_KEYS[phase], progress))


def shell_visible(phase, progress):
    return phase in VISIBLE and VISIBLE[phase][0] <= progress < VISIBLE[phase][1]


def pose_display(original, twohand, phase, progress, part, grip):
    accepted = original if grip == 'native' else twohand
    display = copy.deepcopy(accepted)
    if part == 'body' and ((phase == 'initial' and progress == 0) or (phase == 'return' and progress == 1)):
        return display
    angles, shift, offset = sample(phase, progress)
    body = xyz(angles)
    pivot, anchor = sub(GRIP, (8, 8, 8)), sub(SHELL_ANCHOR, (8, 8, 8))
    # Visibility belongs to empty geometry, never to contact/display scale.
    desired = add(pivot, vec(body, add(sub(anchor, pivot), offset)))
    local = sub(pivot, vec(body, pivot)) if part == 'body' else sub(desired, vec(body, anchor))
    for context in FP:
        idle = original[context]
        base, scale = xyz(idle['rotation']), idle['scale']
        if twohand[context]['scale'] != scale or len(set(scale)) != 1:
            raise ValueError('Uniform equal first-person grip scale required')
        rotation = mul(base, body)
        # Authored shift is display-space, outside source scale/rotation.
        position = add(add(idle['translation'], shift), vec(base, [scale[0]*v for v in local]))
        if grip == 'twohand':
            carrier = mul(xyz(twohand[context]['rotation']), transpose(base))
            position = add(vec(carrier, position), sub(twohand[context]['translation'], vec(carrier, idle['translation'])))
            rotation = mul(carrier, rotation)
        display[context]['rotation'] = euler(rotation)
        display[context]['translation'] = [round(v, 9) for v in position]
    return display


def shell_geometry(source):
    """Sixteen filled octagonal solids; full-size longitudinal case/head/rim/crimp.

    Named IKelos material donors retain finite interior UV rectangles; copper
    top-face donor avoids its side diamond. No texture edits or scale hiding.
    """
    by_name = {element['name']: element for element in source['elements']}
    elements = []
    for name, radius, z0, z1 in (('case', .28, -.70, .54),
                                ('head', .29, .51, .76),
                                ('rim', .32, .74, .86),
                                ('crimp', .26, -.86, -.69)):
        donor = by_name[UV_DONORS[name]]
        donor_face = donor['faces']['up' if name in ('head', 'rim') else 'east']
        u0, v0, u1, v1 = donor_face['uv']
        uv = [u0+(u1-u0)*.20, v0+(v1-v0)*.20,
              u0+(u1-u0)*.80, v0+(v1-v0)*.80]
        for angle in (0, 45, -45, 90):
            center = list(SHELL_ANCHOR)
            center[2] += (z0+z1)/2
            sizes = [2*radius*math.tan(math.pi/8), 2*radius]
            if angle == 90:
                sizes.reverse()
            faces = {side: {'texture': donor_face['texture'], 'uv': list(uv)}
                     for side in ('north', 'south', 'east', 'west', 'up', 'down')}
            element = {'name': 'insert_'+name+'_'+str(angle),
                       'from': [center[0]-sizes[0]/2, center[1]-sizes[1]/2, SHELL_ANCHOR[2]+z0],
                       'to': [center[0]+sizes[0]/2, center[1]+sizes[1]/2, SHELL_ANCHOR[2]+z1],
                       'faces': faces}
            if angle in (45, -45):
                element['rotation'] = {'origin': center, 'axis': 'z', 'angle': angle}
            elements.append(element)
    return {'credit': 'W221 IKelos authored longitudinal shell; existing graphite/copper/steel UV donors; no extracted shell',
            'textures': copy.deepcopy(source['textures']), 'elements': elements}


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Read ROOT-relative inputs; optional absolute or ROOT-relative overrides.

    No mkdir/write/export/subprocess, including import. Master installs outputs.
    """
    root = Path(root).resolve()
    rig_path = root/Path(rig_path if rig_path is not None else RIG)
    profile_path = root/Path(profile_path if profile_path is not None else ART/'profile.json')
    source_raw = (root/SOURCE).read_bytes()
    source = json.loads(source_raw)
    twohand = json.loads((root/TWOHAND).read_bytes())['display']
    canonical = json.loads((root/ITEM).read_bytes())
    profile = json.loads(profile_path.read_bytes())
    rig_raw = rig_path.read_bytes()
    rig = json.loads(rig_raw)
    rule = next(r for r in json.loads((root/SURFACE_MANIFEST).read_bytes())['targets']
                if r['path'] == 'assets/destiny/models/weapon/shotgun/'+WEAPON+'.json')
    if rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/') or rule['replacementSha256'] != sha(source_raw):
        raise ValueError('Effective IKelos canonical surface drift')
    if len(source['elements']) != 111:
        raise ValueError('Expected current 111-element canonical body')
    by_name = {e['name']: e for e in source['elements']}
    port = by_name['lower_receiver_rear']
    derived = ((port['from'][0]+port['to'][0])/2, port['from'][1]-.32, port['from'][2]+.95)
    if any(abs(a-b)>1e-8 for a,b in zip(derived, SHELL_ANCHOR)):
        raise ValueError('IKelos underside port geometry drift')
    if profile.get('schemaVersion') != 1 or profile.get('stage') != 'W221' or profile.get('weapon') != WEAPON:
        raise ValueError('Invalid W221 IKelos profile')
    reload = profile['contacts']['reload']
    if tuple(reload['contact']) != SHELL_ANCHOR or reload['partHint'] != 'shell' or reload['policy'] != 'shell' or reload['rigAction'] != ACTION:
        raise ValueError('Moving shell/left-contact contract drift')
    if not all(reload.get(k) is True for k in ('sourcePalmContactFit','sourceShellPoseHold')):
        raise ValueError('Shared body/limb held pose and palm fit required')
    settings = profile['framing']
    if not settings.get('sourceFullChain') or not settings.get('keepMeshSupport') or settings.get('hideSupportAtRest') is not False:
        raise ValueError('Full ordinary mesh-support chain required')
    if settings.get('sourceViewRotation') != [0,0,0] or settings.get('sourceWeaponMotion',True) is not True:
        raise ValueError('Source body and full chain must share motion')
    action = rig['actions'].get(ACTION, {})
    if rig['group'] != 'shotgun_2eb0529e' or rig['fallback'] or WEAPON not in rig['weapons']:
        raise ValueError('Nonfallback audited shotgun binding required')
    if len(action.get('frames',[])) != SAMPLES or (action.get('start'),action.get('end')) != (1.,101.):
        raise ValueError('Fresh original 61-sample source range required')
    required = {side+joint for side in ('left','right') for joint in ('Shoulder','Elbow','Wrist')} | {'weapon'}
    if not all(required <= set(frame['joints']) for frame in action['frames']):
        raise ValueError('Original shoulder/elbow/wrist/weapon chains required')
    provenance = profile['sourceRig']
    for field in ('sourceBlendSha256','sourceMapSha256','boneMapSha256'):
        if provenance[field] != rig[field]:
            raise ValueError('Source provenance drift: '+field)
    if provenance['cacheSha256'] != sha(rig_raw) or provenance['sourceAction'] != ACTION:
        raise ValueError('Fresh source cache/action drift')
    contacts = json.loads((root/CONTACTS).read_bytes())['weapons'][WEAPON]
    if tuple(contacts['right']['position']) != GRIP:
        raise ValueError('Existing carrier grip drift')
    output = {}
    allowed = (A/'models'/KEY.split('/')[0], A/'items'/KEY.split('/')[0])
    def emit(path, value):
        if path != ART/'manifest.json' and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError('Output outside exclusive W221 namespace')
        output[root/path] = encode(value)
    emit(A/f'models/{KEY}_body.json', copy.deepcopy(source))
    shell = shell_geometry(source)
    budget = len(source['elements'])+len(shell['elements'])+ARM_RESERVE
    if budget > 1000:
        raise ValueError('Assembled element budget exceeded')
    emit(A/f'models/{KEY}_shell.json', shell)
    emit(A/f'models/{KEY}_shell_hidden.json', {'elements': []})
    entries = []
    for phase_index, phase in enumerate(PHASES):
        for frame in range(SAMPLES):
            p = frame/INTERVALS
            for part in PARTS:
                parent = f'destiny:{KEY}_{part}'
                if part == 'shell' and not shell_visible(phase, p):
                    parent += '_hidden'
                for grip in GRIPS:
                    emit(A/f'models/{KEY}_{phase}_{frame:02}_{part}_{grip}.json', {
                        'parent': parent,
                        'display': pose_display(source['display'], twohand, phase, p, part, grip)})
            def composite(grip):
                return {'type': 'minecraft:composite', 'models': [
                    {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{phase}_{frame:02}_{part}_{grip}'} for part in PARTS]}
            endpoint = (phase == 'initial' and frame == 0) or (phase == 'return' and frame == INTERVALS)
            node = copy.deepcopy(canonical['model']) if endpoint else {
                'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
                'on_true': composite('twohand'), 'on_false': composite('native')}
            entries.append({'threshold': threshold(phase_index, frame), 'model': node})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 4, 'entries': entries, 'fallback': copy.deepcopy(canonical['model'])}
    modes = {'type': 'minecraft:select', 'property': 'minecraft:custom_model_data', 'index': 0,
             'cases': [{'when': mode, 'model': copy.deepcopy(canonical['model'])} for mode in ('ads', 'inspect')],
             'fallback': dispatch}
    wrapper = copy.deepcopy(canonical)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': modes}], 'fallback': copy.deepcopy(canonical['model'])}
    emit(A/f'items/{KEY}.json', wrapper)
    inputs = (SOURCE, TWOHAND, ITEM, CONTACTS, SURFACE_MANIFEST,
              Path('art/weapons/w123')/WEAPON/'design.json')
    hashes = {str(p): sha((root/p).read_bytes()) for p in inputs}
    # Override addresses are validation-only. Provenance names the durable
    # install locations; content identity is checked against the profile above.
    hashes[str(RIG)] = sha(rig_raw)
    hashes[str(ART/'profile.json')] = sha(profile_path.read_bytes())
    emit(ART/'manifest.json', {
        'schemaVersion': 1, 'stage': 'W221', 'weapon': WEAPON,
        'generator': 'scripts/generate_insert_w221_ikelos_sg_v1_0_1.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': 'destiny:'+KEY, 'requiredParts': list(PARTS),
        'phases': list(PHASES), 'phaseRanges': [[0,1],[2,3],[4,5]],
        'framesPerPhase': SAMPLES, 'intervalsPerPhase': INTERVALS,
        'totalSamples': 3*SAMPLES, 'progressFloatIndex': 4, 'gripFlagIndex': 0,
        'thresholdEncoding': 'float32(phase*2 + float32(frame/60))',
        'parents': 3, 'displayChildren': 3*SAMPLES*2*2,
        'packFiles': len(output), 'generatedFiles': len(output)+1,
        'bodyElements': len(source['elements']), 'shellElements': len(shell['elements']),
        'maxWeaponElements': budget-ARM_RESERVE, 'armElementReserve': ARM_RESERVE,
        'maxAssembledElements': budget, 'elementLimit': 1000,
        'actualArmAssemblyMeasured': False,
        'bodyGeometryAndUVPreserved': True, 'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'newTextures': 0, 'gripPivot': GRIP, 'shellAnchor': SHELL_ANCHOR,
        'portDerivation': 'lower_receiver_rear: X midpoint; underside Y-.32; front Z+.95',
        'bodyKeyframes': BODY_KEYS, 'shellKeyframes': SHELL_KEYS, 'visibility': VISIBLE,
        'uvDonors': UV_DONORS, 'curve': 'Shape-preserving C1 PCHIP, zero endpoint/hold/extremum slopes',
        'heldSeams': [['initial',60],['loop',0],['loop',60],['return',0]],
        'canonicalGraphEndpoints': [['initial',0],['return',60]],
        'hiddenShell': 'Empty geometry only; continuous hidden HOME recycle, ordinary display scale',
        'rotationConvention': 'Rigid Rx Ry Rz carrier grip pivot and native-to-twohand transport',
        'rig': {'path': str(RIG), 'sourceAction': ACTION, 'sourceFrameRange': [1,101],
                'evaluatedReloadSamples': len(action['frames']), 'heldProgress': .35, 'heldFrame': 36,
                'cameraExported': rig['cameraExported'], 'fallback': rig['fallback']},
        'sourcePoseCalibration': 'Shared body and shoulder/elbow/wrist held source .35 across insert banks; blend to rest on return. Authored calibration, not extracted shell-loop events.',
        'mechanicsOrAudioChanged': False, 'nativeGameplayVerified': False,
        'masterIntegration': 'Load W221 profile/cache; register exact ID for three CMD4 phases/60-grid and shared shell pose hold; materialize hands with framing applied once; FIRST feedback then SECOND Vision.',
        'limitations': ['Armature only, no source weapon mesh/camera/finger IK or per-weapon action selector recovery.',
                       'Canonical receiver is solid: underside port is a geometry-derived handling approximation; no cavity carved.',
                       '61 poses are bank samples, not proof of continuous 60fps; runtime owns authoritative shell timing and W219 cancellable audio.',
                       '448 conservative ordinary-arm reserve; master must measure actual assembled skin arms and review clearance/contact/ADS.'],
        'inputSha256': hashes,
        'outputSha256': {str(p.relative_to(root)): sha(raw) for p,raw in output.items()}})
    return output
