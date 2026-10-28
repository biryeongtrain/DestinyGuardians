#!/usr/bin/env python3
"""W208 First In, Last Out: 61-pose C1 initial/held insert/return banks.

Import and generate(root=ROOT) only read inputs and return absolute Path->bytes.
Master owns pack writes, runtime routing, skin-arm sampling and native review.
W178 visible timing/rigid pivot convention retained; no recovered camera claim.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w208/first_in_last_out')
KEY = 'weapon_insert_w208_first_in_last_out/first_in_last_out'
SOURCE = A/'models/weapon_surface_w123/first_in_last_out.json'
TWOHAND = A/'models/weapon/shotgun/first_in_last_out_twohand.json'
ITEM = A/'items/weapon/first_in_last_out.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
RIG = Path('art/weapons/w205/rigs/shotgun_2eb0529e.json')
SURFACE_MANIFEST = Path('src/main/resources/weapon_surface_w123/manifest.json')
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
PARTS = ('body', 'shell')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = INTERVALS+1
GRIP = (8., 8.88, 8.53)
SHELL_ANCHOR = (8., 9.96, 4.65)
HOLD = ((18., -8., -42.), (-.35, .55, .20))
# Original W178 authored times/values: preserve meaningful lift/held spans.
KEYS = {'initial': ((0.0, (0, 0, 0), (0, 0, 0), (-1.4, -2.1, 1.9)),
             (0.15, (8, -3, -19), (-0.12, 0.2, 0.08), (-1.4, -2.1, 1.9)),
             (0.3, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (-1.4, -2.1, 1.9)),
             (0.4, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (-1.4, -2.1, 1.9)),
             (0.58, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (-0.7, -1.05, 1.45)),
             (0.7, (18.4, -8.3, -42.8), (-0.34, 0.58, 0.21), (0, -0.12, 0.8)),
             (0.87, (18.9, -8.2, -42.4), (-0.35, 0.62, 0.18), (0, 0, -2.1)),
             (1.0, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (0, 0, -2.1))),
 'loop': ((0.0, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (-1.4, -2.1, 1.9)),
          (0.15, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (-1.4, -2.1, 1.9)),
          (0.38, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (-0.7, -1.05, 1.45)),
          (0.55, (18.4, -8.3, -42.8), (-0.34, 0.58, 0.21), (0, -0.12, 0.8)),
          (0.8, (18.9, -8.2, -42.4), (-0.35, 0.62, 0.18), (0, 0, -2.1)),
          (1.0, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (0, 0, -2.1))),
 'return': ((0.0, (18.0, -8.0, -42.0), (-0.35, 0.55, 0.2), (0, 0, -2.1)),
            (0.3, (13, -6, -31), (-0.25, 0.35, 0.12), (0, 0, -2.1)),
            (0.7, (4, -2, -9), (-0.07, 0.08, 0.03), (0, 0, -2.1)),
            (1.0, (0, 0, 0), (0, 0, 0), (0, 0, -2.1)))}
VISIBLE = {'initial': (0.4, 0.87), 'loop': (0.15, 0.8)}
# Recycle only AFTER the last visible seated sample. The hidden shell contact
# reaches HOME with zero speed at every held seam, instead of teleporting.
HOME = KEYS['initial'][0][3]
SEATED = KEYS['initial'][-1][3]
SHELL_KEYS = {
    'initial': tuple((k[0], k[3]) for k in KEYS['initial'][:-1]) + ((.90, SEATED), (1., HOME)),
    'loop': tuple((k[0], k[3]) for k in KEYS['loop'][:-1]) + ((.85, SEATED), (1., HOME)),
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
    """Exact W178 twelve-solid case/head/rim, using existing atlas texels."""
    elements = []
    for name, radius, z0, z1, uv_index in (
            ('case', .25, -.77, .49, 34), ('head', .26, .46, .70, 58),
            ('rim', .29, .67, .77, 58)):
        for angle in (0, 45, -45, 90):
            center = list(SHELL_ANCHOR)
            center[2] += (z0+z1)/2
            width = 2*radius*math.tan(math.pi/8)
            sizes = [width, 2*radius]
            if angle == 90:
                sizes.reverse()
            faces = copy.deepcopy(source['elements'][uv_index]['faces'])
            # Shared existing texel avoids inconsistent overlapping end paint.
            for face in faces.values():
                uv = source['elements'][uv_index]['faces']['east']['uv']
                u, v = (uv[0]+uv[2])/2, (uv[1]+uv[3])/2
                face['uv'] = [u, v, u, v]
            element = {'name': 'hidden_insert_'+name+'_'+str(angle),
                       'from': [center[0]-sizes[0]/2, center[1]-sizes[1]/2, SHELL_ANCHOR[2]+z0],
                       'to': [center[0]+sizes[0]/2, center[1]+sizes[1]/2, SHELL_ANCHOR[2]+z1],
                       'faces': faces}
            if angle in (45, -45):
                element['rotation'] = {'origin': center, 'axis': 'z', 'angle': angle}
            elements.append(element)
    return {'credit': 'W178 hidden cartridge only; existing graphite tube34 / steel sleeve58 atlas texels; no extracted shell',
            'textures': copy.deepcopy(source['textures']), 'elements': elements}


def generate(root=ROOT):
    """Return new W208 assets + owned manifest; never materialize files."""
    root = Path(root).resolve()
    source = json.loads((root/SOURCE).read_bytes())
    twohand = json.loads((root/TWOHAND).read_bytes())['display']
    canonical = json.loads((root/ITEM).read_bytes())
    profile = json.loads((root/ART/'profile.json').read_bytes())
    rig = json.loads((root/RIG).read_bytes())
    rules = json.loads((root/SURFACE_MANIFEST).read_bytes())['targets']
    rule = next(r for r in rules if r['path'] == 'assets/destiny/models/weapon/shotgun/first_in_last_out.json')
    if rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/') or rule['replacementSha256'] != sha((root/SOURCE).read_bytes()):
        raise ValueError('Effective First In, Last Out surface drift')
    if len(source['elements']) != 97:
        raise ValueError('Expected current 97-element canonical body')
    reload = profile['contacts']['reload']
    if tuple(reload['contact']) != SHELL_ANCHOR or reload['partHint'] != 'shell' or reload['rigAction'] != '80A8A3F1':
        raise ValueError('Moving shell/left-contact contract drift')
    if not profile['framing']['keepMeshSupport'] or 'first_in_last_out' not in rig['weapons'] or reload['rigAction'] not in rig['actions']:
        raise ValueError('Mesh support/source rig contract drift')
    output = {}
    allowed = (A/'models/weapon_insert_w208_first_in_last_out', A/'items/weapon_insert_w208_first_in_last_out')
    def emit(path, value):
        if path != ART/'manifest.json' and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError('Output outside exclusive W208 namespace')
        output[root/path] = encode(value)
    emit(A/f'models/{KEY}_body.json', copy.deepcopy(source))
    shell = shell_geometry(source)
    emit(A/f'models/{KEY}_shell.json', shell)
    emit(A/f'models/{KEY}_shell_hidden.json', {
        'textures': {'particle': source['textures']['particle']}, 'elements': []})
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
            entries.append({'threshold': threshold(phase_index, frame), 'model': {
                'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
                'on_true': composite('twohand'), 'on_false': composite('native')}})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 4, 'entries': entries, 'fallback': copy.deepcopy(canonical['model'])}
    modes = {'type': 'minecraft:select', 'property': 'minecraft:custom_model_data', 'index': 0,
             'cases': [{'when': mode, 'model': copy.deepcopy(canonical['model'])} for mode in ('ads', 'inspect')],
             'fallback': dispatch}
    wrapper = copy.deepcopy(canonical)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': modes}], 'fallback': copy.deepcopy(canonical['model'])}
    emit(A/f'items/{KEY}.json', wrapper)
    inputs = (SOURCE, TWOHAND, ITEM, CONTACTS, RIG, SURFACE_MANIFEST, ART/'profile.json',
              Path('scripts/generate_insert_w178_first_in_last_out.py'),
              Path('art/weapons/w123/first_in_last_out/manifest.json'))
    emit(ART/'manifest.json', {
        'schemaVersion': 1, 'stage': 'W208', 'weapon': 'first_in_last_out',
        'generator': 'scripts/generate_insert_w208_first_in_last_out.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': 'destiny:'+KEY, 'requiredParts': list(PARTS),
        'phases': list(PHASES), 'phaseRanges': [[0, 1], [2, 3], [4, 5]],
        'framesPerPhase': SAMPLES, 'intervalsPerPhase': INTERVALS,
        'progressFloatIndex': 4, 'gripFlagIndex': 0,
        'thresholdEncoding': 'float32(phase*2 + float32(frame/60)); Java float division then addition; existing collision offset owned by runtime',
        'parents': 3, 'displayChildren': 3*SAMPLES*2*2,
        'packFiles': len(output), 'generatedFiles': len(output)+1,
        'bodyElements': 97, 'shellElements': len(shell['elements']), 'maxAssembledElements': 97+len(shell['elements']),
        'bodyGeometryAndUVPreserved': True, 'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'newTextures': 0, 'elementLimit': 1000, 'gripPivot': GRIP, 'shellAnchor': SHELL_ANCHOR,
        'keyframes': KEYS, 'shellKeyframes': SHELL_KEYS, 'visibility': VISIBLE,
        'curve': 'W207 Ammit shape-preserving C1 PCHIP; weighted harmonic knot tangents, zero endpoints/holds/extrema; W178 visible event timing',
        'hiddenShell': 'Empty elements parent, ordinary accepted display scale. Invisible recycle after .87 initial/.80 loop; zero-velocity HOME anchor at all held seams.',
        'heldSeams': [['initial', 60], ['loop', 0], ['loop', 60], ['return', 0]],
        'bodyHipEndpoints': [['initial', 0], ['return', 60]],
        'rotationConvention': 'W178 rigid Rx Ry Rz source grip pivot; native presentation shift; rigid native->twohand carrier; no additive Euler',
        'returnTicks': 6, 'returnBlocksGameplay': False, 'mechanicsOrAudioChanged': False,
        'reference': {'url': 'https://www.youtube.com/watch?v=5IZfs2bjrYY',
                      'metadata': 'art/weapons/w178/first_in_last_out/motion-reference.json',
                      'recordedFrames': 12, 'identityFrames': 1, 'reloadFrames': 11,
                      'viewedCurrentPngs': ['reference-01.png', 'reference-06.png'],
                      'limitation': 'W178 authored timing. Source camera pans, flashes and hand occlusion prevent exact camera/cartridge extraction; return is authored, not a settled source full-mag return.'},
        'rig': {'path': str(RIG), 'fallback': rig['fallback'], 'idle': rig['idle'], 'ads': rig['ads'],
                'reload': reload['rigAction'], 'evaluatedReloadSamples': len(rig['actions'][reload['rigAction']]['frames']),
                'cameraExported': rig['cameraExported']},
        'nativeGameplayVerified': False, 'handIK': False,
        'masterIntegration': 'Load W208 profile; route model and 60 intervals in WeaponInsertPresentation; whitelist first_in_last_out 80A8A3F1 with initial/loop/return CMD4 handling; left hand follows shell display including hidden normal-scale states; keepMeshSupport=true. Apply shared framing once.',
        'limitations': ['61 poses reduce bank quantization; server pacing remains up to 20Hz, not proof of 60fps.',
                       'Native classic/slim arms, both hands/grips, contact clearance and shell occlusion require master review.',
                       'No common pipeline, gameplay durations, ammo, audio, source arm lengths or meshes edited.'],
        'inputSha256': {str(p): sha((root/p).read_bytes()) for p in inputs},
        'outputSha256': {str(p.relative_to(root)): sha(raw) for p, raw in output.items()}})
    return output
