#!/usr/bin/env python3
"""W221 Mindbender: pure 61-pose initial/held-shell/return candidate.

W179 canonical geometry, shell, contact axis and event times are retained.
Master owns original Blender evaluation, shared source-chain integration,
materialization, gameplay clocks and FIRST -> feedback -> SECOND Vision.
Import and generate only read inputs; output is absolute Path -> bytes.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
WEAPON = 'mindbender_s_ambition_adept'
ART = Path('art/weapons/w221') / WEAPON
KEY = 'weapon_insert_w221_' + WEAPON + '/' + WEAPON
SOURCE = A / 'models/weapon_surface_w123' / (WEAPON + '.json')
TWOHAND = A / 'models/weapon/shotgun' / (WEAPON + '_twohand.json')
ITEM = A / 'items/weapon' / (WEAPON + '.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
RIG = Path('art/weapons/w221/rigs/shotgun_2eb0529e.json')
PROFILE = ART / 'profile.json'
SURFACE_MANIFEST = Path('src/main/resources/weapon_surface_w123/manifest.json')
ACTION = '80A8A3F1'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
PARTS = ('body', 'shell')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS + 1
ARM_RESERVE = 448

GRIP = (8., 8.70, 8.18)

SHELL_ANCHOR = (8., 10.04, 4.45)

HOLD = ((22., -11., -36.), (-.24, .44, .16))

APPROACH = (1.10, -1.65, .45)

CONTACT = (0., -.05, 0.)

SEATED = (0., .96, -1.90)

KEYS = {
 'initial': (
  (0., (0,0,0), (0,0,0), APPROACH),
  (.14, (9,-4,-17), (-.10,.19,.06), APPROACH),
  (.30, *HOLD, APPROACH),
  (.38, *HOLD, APPROACH),
  (.59, *HOLD, (.40,-.72,.20)),
  (.72, (22.45,-11.2,-36.65), (-.23,.47,.15), CONTACT),
  (.90, (22.70,-11.3,-36.4), (-.24,.49,.14), SEATED),
  (1., *HOLD, SEATED)),
 'loop': (
  (0., *HOLD, APPROACH),
  (.10, *HOLD, APPROACH),
  (.38, *HOLD, (.40,-.72,.20)),
  (.57, (22.45,-11.2,-36.65), (-.23,.47,.15), CONTACT),
  (.84, (22.70,-11.3,-36.4), (-.24,.49,.14), SEATED),
  (1., *HOLD, SEATED)),
 'return': (
  (0., *HOLD, SEATED),
  (.28, (17,-8,-28), (-.19,.34,.12), SEATED),
  (.72, (4,-2,-7), (-.04,.06,.02), SEATED),
  (1., (0,0,0), (0,0,0), SEATED))
}

VISIBLE = {'initial': (.38,.90), 'loop': (.10,.84)}

# Keep every visible W179 key, then recycle only while geometry is empty.
# Shared zero-speed HOME at all held boundaries prevents a wrist teleport.
HOME = APPROACH
SHELL_KEYS = {
    'initial': tuple((k[0], k[3]) for k in KEYS['initial'][:-1]) + ((.94, SEATED), (1., HOME)),
    'loop': tuple((k[0], k[3]) for k in KEYS['loop'][:-1]) + ((.90, SEATED), (1., HOME)),
    'return': ((0., HOME), (1., HOME)),
}

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
    return (interpolate(tuple((k[0], k[1]) for k in KEYS[phase]), progress),
            interpolate(tuple((k[0], k[2]) for k in KEYS[phase]), progress),
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
        # W178 authored shift is display-space, outside source scale/rotation.
        position = add(add(idle['translation'], shift), vec(base, [scale[0]*v for v in local]))
        if grip == 'twohand':
            carrier = mul(xyz(twohand[context]['rotation']), transpose(base))
            position = add(vec(carrier, position), sub(twohand[context]['translation'], vec(carrier, idle['translation'])))
            rotation = mul(carrier, rotation)
        display[context]['rotation'] = euler(rotation)
        display[context]['translation'] = [round(v, 9) for v in position]
    return display

def shell_geometry(source):
    """One octagonal cartridge, twelve connected solids, no new atlas.

    Longitudinal Z case; head/rim at the rear (+Z), crimp end toward muzzle.
    Four intersecting rectangular solids per section fill the octagonal section.
    Reuse clean existing graphite tray and silver collar texels, no rune decals.
    """
    elements = []
    for name, radius, z0, z1, paint in (
        ('case', .25, -.77, .49, 'loading_tray'),
        ('head', .26, .46, .70, 'barrel_silver_collar_0'),
        ('rim', .29, .67, .77, 'barrel_silver_collar_0')):
        donor = next(e for e in source['elements'] if e['name'] == paint)
        uv = donor['faces']['east']['uv']
        u, v = (uv[0]+uv[2])/2, (uv[1]+uv[3])/2
        for angle in (0,45,-45,90):
            width = 2*radius*math.tan(math.pi/8)
            sizes = [width, 2*radius]
            if angle == 90:
                sizes.reverse()
            center = list(SHELL_ANCHOR)
            center[2] += (z0+z1)/2
            faces = copy.deepcopy(donor['faces'])
            for face in faces.values():
                face['uv'] = [u,v,u,v]
            element = dict(name=f'insert_{name}_{angle}', **{
                'from': [center[0]-sizes[0]/2,center[1]-sizes[1]/2,SHELL_ANCHOR[2]+z0],
                'to': [center[0]+sizes[0]/2,center[1]+sizes[1]/2,SHELL_ANCHOR[2]+z1]}, faces=faces)
            if angle in (45,-45):
                element['rotation'] = dict(origin=center,axis='z',angle=angle)
            elements.append(element)
    return dict(credit='W179 authored model-only cartridge; longitudinal -Z crimp / +Z head. Canonical graphite tray / silver collar texels.',
                textures=copy.deepcopy(source['textures']), elements=elements)

def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Read ROOT-relative inputs and return exclusive W221 assets; no writes.

    Absolute scratch overrides are accepted for master original61 inspection.
    Relative overrides are resolved against root, never the caller's cwd.
    """
    root = Path(root).resolve()
    def input_path(value, default):
        path = Path(default if value is None else value)
        return path if path.is_absolute() else root / path
    rig_file = input_path(rig_path, RIG)
    profile_file = input_path(profile_path, PROFILE)
    source = json.loads((root / SOURCE).read_bytes())
    twohand = json.loads((root / TWOHAND).read_bytes())['display']
    canonical = json.loads((root / ITEM).read_bytes())
    profile = json.loads(profile_file.read_bytes())
    rig = json.loads(rig_file.read_bytes())
    rules = json.loads((root / SURFACE_MANIFEST).read_bytes())['targets']
    rule = next(r for r in rules if r['path'] == 'assets/destiny/models/weapon/shotgun/' + WEAPON + '.json')
    if rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/') or rule['replacementSha256'] != sha((root / SOURCE).read_bytes()):
        raise ValueError('Effective Mindbender canonical surface drift')
    if len(source['elements']) != 104:
        raise ValueError('Expected current 104-solid Mindbender body')
    if (profile.get('schemaVersion'), profile.get('stage'), profile.get('weapon'), profile.get('sourceAction')) != (1, 'W221', WEAPON, ACTION):
        raise ValueError('W221 Mindbender profile identity drift')
    reload = profile['contacts']['reload']
    if (tuple(reload['contact']) != SHELL_ANCHOR or reload['partHint'] != 'shell'
            or reload['policy'] != 'shell' or reload['rigAction'] != ACTION
            or reload.get('hand', 'left') != 'left'
            or not reload.get('sourcePalmContactFit') or not reload.get('sourceShellPoseHold')):
        raise ValueError('Moving shell/LEFT contact/held source contract drift')
    framing = profile['framing']
    if not framing['sourceFullChain'] or not framing['keepMeshSupport'] or framing['hideSupportAtRest'] or framing['sourceViewRotation'] != [0, 0, 0]:
        raise ValueError('Ordinary visible full-chain contract drift')
    original_contacts = json.loads((root / CONTACTS).read_bytes())['weapons'][WEAPON]
    for side in ('right', 'left'):
        override = profile['contacts'].get(side, {})
        if {**original_contacts[side], **override} != original_contacts[side]:
            raise ValueError('Accepted idle mesh grip changed: ' + side)
    if rig['group'] != 'shotgun_2eb0529e' or rig['fallback'] or WEAPON not in rig['weapons'] or rig['cameraExported']:
        raise ValueError('Audited source rig binding drift')
    provenance = profile['sourceRig']
    for key in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if provenance[key] != rig[key]:
            raise ValueError('Original source hash drift: ' + key)
    if provenance['group'] != rig['group'] or provenance['action'] != ACTION:
        raise ValueError('Source action/group provenance drift')
    action = rig['actions'][ACTION]
    if (action['start'], action['end'], len(action['frames'])) != (1, 101, SAMPLES):
        raise ValueError('Expected original source frames1..101 evaluated at61 samples')
    required = ('weapon', 'leftShoulder', 'leftElbow', 'leftWrist', 'rightShoulder', 'rightElbow', 'rightWrist')
    for i, frame in enumerate(action['frames']):
        if abs(frame['progress'] - i / INTERVALS) > 1e-7:
            raise ValueError('Nonuniform original61 sample grid')
        for name in required:
            matrix = frame['joints'][name]
            if len(matrix) != 4 or any(len(row) != 4 or not all(math.isfinite(v) for v in row) for row in matrix):
                raise ValueError('Invalid evaluated full-chain matrix')
    output = {}
    allowed = (A / ('models/weapon_insert_w221_' + WEAPON), A / ('items/weapon_insert_w221_' + WEAPON))
    def emit(path, value):
        if path != ART / 'manifest.json' and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError('Output outside exclusive Mindbender W221 namespace')
        output[root / path] = encode(value)
    emit(A / f'models/{KEY}_body.json', copy.deepcopy(source))
    shell = shell_geometry(source)
    if len(shell['elements']) != 12:
        raise ValueError('Expected W179 twelve-solid longitudinal shell')
    assembled = len(source['elements']) + len(shell['elements']) + ARM_RESERVE
    if assembled > 1000:
        raise ValueError('Conservative assembled element budget exceeded')
    emit(A / f'models/{KEY}_shell.json', shell)
    emit(A / f'models/{KEY}_shell_hidden.json', {'elements': []})
    entries = []
    for phase_index, phase in enumerate(PHASES):
        for frame in range(SAMPLES):
            p = frame / INTERVALS
            for part in PARTS:
                parent = f'destiny:{KEY}_{part}'
                if part == 'shell' and not shell_visible(phase, p):
                    parent += '_hidden'
                for grip in GRIPS:
                    emit(A / f'models/{KEY}_{phase}_{frame:02}_{part}_{grip}.json', {
                        'parent': parent,
                        'display': pose_display(source['display'], twohand, phase, p, part, grip)})
            def composite(grip):
                return {'type': 'minecraft:composite', 'models': [
                    {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{phase}_{frame:02}_{part}_{grip}'} for part in PARTS]}
            endpoint = (phase == 'initial' and frame == 0) or (phase == 'return' and frame == INTERVALS)
            model = copy.deepcopy(canonical['model']) if endpoint else {
                'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
                'on_true': composite('twohand'), 'on_false': composite('native')}
            entries.append({'threshold': threshold(phase_index, frame), 'model': model})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 4, 'entries': entries, 'fallback': copy.deepcopy(canonical['model'])}
    modes = {'type': 'minecraft:select', 'property': 'minecraft:custom_model_data', 'index': 0,
             'cases': [{'when': mode, 'model': copy.deepcopy(canonical['model'])} for mode in ('ads', 'inspect')],
             'fallback': dispatch}
    wrapper = copy.deepcopy(canonical)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': modes}], 'fallback': copy.deepcopy(canonical['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    inputs = (SOURCE, TWOHAND, ITEM, CONTACTS, SURFACE_MANIFEST,
              Path('scripts/generate_insert_w179_mindbender_s_ambition_adept.py'))
    input_hashes = {str(p): sha((root / p).read_bytes()) for p in inputs}
    input_hashes[str(RIG)] = sha(rig_file.read_bytes())
    input_hashes[str(PROFILE)] = sha(profile_file.read_bytes())
    emit(ART / 'manifest.json', {
        'schemaVersion': 1, 'stage': 'W221', 'weapon': WEAPON,
        'generator': 'scripts/generate_insert_w221_' + WEAPON + '.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': 'destiny:' + KEY, 'requiredParts': list(PARTS),
        'phases': list(PHASES), 'phaseRanges': [[0, 1], [2, 3], [4, 5]],
        'framesPerPhase': SAMPLES, 'intervalsPerPhase': INTERVALS, 'samples': 3 * SAMPLES,
        'progressFloatIndex': 4, 'gripFlagIndex': 0, 'firstPersonContexts': list(FP),
        'thresholdEncoding': 'float32(phase*2 + float32(frame/60)); Java division then addition',
        'parents': 3, 'displayChildren': 3 * SAMPLES * 2 * 2,
        'packFiles': len(output), 'generatedFiles': len(output) + 1,
        'bodyElements': 104, 'shellElements': 12, 'weaponElements': 116,
        'conservativeArmElements': ARM_RESERVE, 'maxAssembledElements': assembled,
        'assembledCountStatus': '116 actual emitted weapon elements plus448 conservative ordinary skin-arm reserve; master measures final assembly',
        'triangleAdapterElements': 0, 'elementLimit': 1000,
        'bodyGeometryAndUVPreserved': True, 'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'newTextures': 0, 'gripPivot': GRIP, 'shellAnchor': SHELL_ANCHOR,
        'shellAxis': {'longitudinal': 'Z', 'crimpDirection': [0, 0, -1], 'rimDirection': [0, 0, 1],
                      'chamberContact': add(SHELL_ANCHOR, CONTACT), 'occludedSeat': add(SHELL_ANCHOR, SEATED)},
        'keyframes': KEYS, 'shellKeyframes': SHELL_KEYS, 'visibility': VISIBLE,
        'curve': 'Shape-preserving C1 PCHIP, weighted harmonic knot derivatives; zero endpoints/extrema/holds; W179 visible keys retained',
        'hiddenShell': 'Empty geometry outside initial[.38,.90) / loop[.10,.84); ordinary display scale; continuous invisible recycle to HOME with zero seam speed',
        'heldSeams': [['initial', 60], ['loop', 0], ['loop', 60], ['return', 0]],
        'canonicalGraphEndpoints': [['initial', 0], ['return', 60]],
        'fallback': 'Exact canonical item graph for nonFP, ADS, inspect, inactive negative CMD4 and bank endpoints',
        'rotationConvention': 'W179 rigid RxRyRz source grip pivot; native display-space shift; rigid native-to-twohand carrier',
        'sourceAction': ACTION, 'sourceRig': provenance,
        'rig': {'path': str(RIG), 'idle': rig['idle'], 'ads': rig['ads'], 'reload': ACTION,
                'sourceFrameRange': [action['start'], action['end']], 'evaluatedReloadSamples': SAMPLES, 'cameraExported': False},
        'sourceCalibration': 'Master opt-in: source body AND limbs share .35/frame36; initial reaches hold by .36, loop holds, return blends hold to rest. Generic source pose calibration, not recovered shell events or full-action replay.',
        'returnTicks': 6, 'returnBlocksGameplay': False, 'mechanicsOrAudioChanged': False,
        'nativeGameplayVerified': False, 'fingerIK': False,
        'masterIntegration': 'Install fresh W221 rig/profile; add exact weapon ID to three-phase CMD4 parser and rig-action/held-shell opt-in; route W221 item with60grid. Fit LEFT palm to shell; keep body and full limbs on common source sample. Preserve actual per-shell insertion timing and W219 cancellable last-shell sound.',
        'limitations': ['Master original Blender evaluation reviewed; this worker did not independently evaluate Blender.',
                       'No source mesh, camera, finger IK or per-weapon selector recovery.',
                       '61 sampled poses do not establish continuous native60fps interpolation.',
                       'FIRST Vision, same-worker feedback and SECOND Vision remain required; no full-hands, Gradle or game generation run here.'],
        'inputSha256': input_hashes,
        'outputSha256': {str(p.relative_to(root)): sha(raw) for p, raw in output.items()}})
    return output
