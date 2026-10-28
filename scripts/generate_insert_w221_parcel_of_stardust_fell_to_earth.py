#!/usr/bin/env python3
"""W221 Parcel: pure 61-pose initial/loop/return shell presentation.

Only generate() reads inputs; import and generation never materialize assets.
The master composes the original source weapon AND full arm chain together;
these leaves express the rigid canonical body and its relative cartridge path.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
WEAPON = 'parcel_of_stardust_fell_to_earth'
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w221')/WEAPON
KEY = 'weapon_insert_w221_'+WEAPON+'/'+WEAPON
SOURCE = A/'models/weapon_surface_w123'/f'{WEAPON}.json'
TWOHAND = A/'models/weapon/shotgun'/f'{WEAPON}_twohand.json'
ITEM = A/'items/weapon'/f'{WEAPON}.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
RIG = Path('art/weapons/w221/rigs/shotgun_2eb0529e.json')
# Repository-relative archival destinations; scratch overrides are temporary.
SOURCE_EVIDENCE = {'review': 'docs/qa/2026-10-28/w221/source-review.json', 'handling': 'docs/qa/2026-10-28/w221/source-handling-evidence.json', 'upperChainSheet': 'docs/qa/2026-10-28/w221/source-sheets/shotgun_2eb0529e-80A8A3F1-upper-chain.png'}
SURFACE_MANIFEST = Path('src/main/resources/weapon_surface_w123/manifest.json')
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
PARTS = ('body', 'shell')
GRIPS = ('native', 'twohand')
INTERVALS = 60
SAMPLES = 61
ARM_RESERVE = 448
GRIP = (8., 9., 9.18)
# Below the Parcel elevator's lower face Y10.08; its rear edge is Z4.10.
# A longitudinal .44-diameter case approaches the fixed .44-bore tube.
SHELL_ANCHOR = (8., 9.78, 4.18)
HOME = (-1.65, -2.05, 2.15)
ALIGN = (0., 0., 0.)
SEATED = (0., .62, -1.35)
# Authored normalized handling windows, not extracted per-shell events.
# Source .35/frame36 and its whole chain are held by the master shell opt-in.
SHELL_KEYS = {
    'initial': ((0., HOME), (.36, HOME), (.46, HOME),
                (.65, (-.45, -.65, .80)), (.76, ALIGN),
                (.86, SEATED), (.90, SEATED), (1., HOME)),
    'loop': ((0., HOME), (.12, HOME),
             (.37, (-.45, -.65, .80)), (.52, ALIGN),
             (.78, SEATED), (.84, SEATED), (1., HOME)),
    'return': ((0., HOME), (1., HOME)),
}
VISIBLE = {'initial': (.46, .90), 'loop': (.12, .84)}

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
    """Body has no independent sweep: shared source composition owns it."""
    if phase not in PHASES:
        raise ValueError(phase)
    return [0., 0., 0.], [0., 0., 0.], interpolate(SHELL_KEYS[phase], progress)


def shell_visible(phase, progress):
    return phase in VISIBLE and VISIBLE[phase][0] <= progress < VISIBLE[phase][1]


def pose_display(original, twohand, phase, progress, part, grip):
    if part not in PARTS or grip not in GRIPS:
        raise ValueError('Unknown part or grip')
    _, _, offset = sample(phase, progress)
    accepted = original if grip == 'native' else twohand
    display = copy.deepcopy(accepted)
    if part == 'body':
        return display
    for context in FP:
        idle = accepted[context]
        scale = idle['scale']
        if len(set(scale)) != 1 or min(scale) <= 0:
            raise ValueError('Ordinary uniform first-person scale required')
        delta = vec(xyz(idle['rotation']), [scale[0]*v for v in offset])
        display[context]['translation'] = [round(v+d, 9) for v, d in zip(idle['translation'], delta)]
    return display


def shell_geometry(source):
    """Twelve solids; full-size case/head/rim, existing Parcel material UVs.

    Retain nonzero face UV rectangles (tube wall / steel bolt / collar).
    This is an authored incoming cartridge, never a detached tube magazine.
    """
    by_name = {e['name']: e for e in source['elements']}
    elements = []
    for name, radius, z0, z1, donor in (
        ('case', .22, -.77, .49, 'magazine_wall_0'),
        ('head', .23, .46, .70, 'ejection_bolt'),
        ('rim', .255, .67, .77, 'magazine_front_collar_0'),
    ):
        for angle in (0, 45, -45, 90):
            center = list(SHELL_ANCHOR)
            center[2] += (z0+z1)/2
            widths = [2*radius*math.tan(math.pi/8), 2*radius]
            if angle == 90:
                widths.reverse()
            element = {
                'name': 'incoming_shell_'+name+'_'+str(angle),
                'from': [center[0]-widths[0]/2, center[1]-widths[1]/2, SHELL_ANCHOR[2]+z0],
                'to': [center[0]+widths[0]/2, center[1]+widths[1]/2, SHELL_ANCHOR[2]+z1],
                'faces': copy.deepcopy(by_name[donor]['faces']),
            }
            if angle in (45, -45):
                element['rotation'] = {'origin': center, 'axis': 'z', 'angle': angle}
            elements.append(element)
    return {'credit': 'W221 authored Parcel longitudinal shell; existing tube/bolt/collar UVs',
            'textures': copy.deepcopy(source['textures']), 'elements': elements}


def after_float32(value):
    bits = struct.unpack('!I', struct.pack('!f', value))[0]
    return struct.unpack('!f', struct.pack('!I', bits+1))[0]


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Read root-relative inputs, return absolute paths and bytes; no writes."""
    root = Path(root).resolve()
    def actual(override, default):
        path = Path(override) if override is not None else default
        return path if path.is_absolute() else root/path
    rig_file = actual(rig_path, RIG)
    profile_file = actual(profile_path, ART/'profile.json')
    raw_inputs = {p: (root/p).read_bytes() for p in (SOURCE, TWOHAND, ITEM, CONTACTS, SURFACE_MANIFEST)}
    rig_raw, profile_raw = rig_file.read_bytes(), profile_file.read_bytes()
    source = json.loads(raw_inputs[SOURCE])
    twohand = json.loads(raw_inputs[TWOHAND])['display']
    canonical = json.loads(raw_inputs[ITEM])
    profile = json.loads(profile_raw)
    rig = json.loads(rig_raw)
    rule = next(t for t in json.loads(raw_inputs[SURFACE_MANIFEST])['targets']
                if t['path'] == f'assets/destiny/models/weapon/shotgun/{WEAPON}.json')
    if rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/') or rule['replacementSha256'] != sha(raw_inputs[SOURCE]):
        raise ValueError('Effective Parcel surface drift')
    if profile.get('schemaVersion') != 1 or profile.get('stage') != 'W221' or profile.get('weapon') != WEAPON:
        raise ValueError('Invalid W221 Parcel profile')
    if profile['sourceRig'].get('path') != str(RIG) or profile.get('sourceEvidence') != SOURCE_EVIDENCE:
        raise ValueError('Expected durable repository-relative W221 provenance')
    reload = profile['contacts']['reload']
    if (tuple(reload['contact']) != SHELL_ANCHOR or reload['partHint'] != 'shell'
        or reload['policy'] != 'shell' or reload['rigAction'] != '80A8A3F1'
        or reload.get('hand') != 'left' or not reload.get('sourcePalmContactFit')
        or not reload.get('sourceShellPoseHold')):
        raise ValueError('Parcel shell contact/source contract drift')
    framing = profile['framing']
    if not framing.get('sourceFullChain') or not framing.get('keepMeshSupport') or framing.get('hideSupportAtRest'):
        raise ValueError('Full ordinary visible arm chain required')
    if WEAPON not in rig['weapons'] or rig['fallback'] or rig['group'] != 'shotgun_2eb0529e':
        raise ValueError('Expected original shotgun source rig')
    for field in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if profile['sourceRig'][field] != rig[field]:
            raise ValueError('Source provenance drift: '+field)
    if profile.get('sourceAction') != reload['rigAction'] or profile['sourceRig'].get('action') != reload['rigAction']:
        raise ValueError('Source action mismatch')
    action = rig['actions'][reload['rigAction']]
    if len(action['frames']) != SAMPLES or [action['start'], action['end']] != [1., 101.]:
        raise ValueError('Expected fresh original Blender61, frames1..101')
    for i, frame in enumerate(action['frames']):
        if abs(frame['progress']-i/INTERVALS) > 1e-9 or not all(side+joint in frame['joints'] for side in ('left','right') for joint in ('Shoulder','Elbow','Wrist')):
            raise ValueError('Missing original full source chain/sample')
    original_contacts = json.loads(raw_inputs[CONTACTS])['weapons'][WEAPON]
    for side in ('right', 'left'):
        if profile['contacts'][side] != original_contacts[side]:
            raise ValueError('Preserve accepted idle '+side+' contact')
    shell = shell_geometry(source)
    assembled = len(source['elements'])+len(shell['elements'])+ARM_RESERVE
    if assembled > 1000:
        raise ValueError('Assembled elements exceed budget')
    output = {}
    allowed = (A/('models/weapon_insert_w221_'+WEAPON), A/('items/weapon_insert_w221_'+WEAPON))
    def emit(path, value):
        if path != ART/'manifest.json' and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError('Output outside owned W221 namespace')
        output[root/path] = encode(value)
    emit(A/f'models/{KEY}_body.json', copy.deepcopy(source))
    emit(A/f'models/{KEY}_shell.json', shell)
    emit(A/f'models/{KEY}_shell_hidden.json', {
        'textures': {'particle': source['textures']['particle']}, 'elements': []})
    entries = []
    for phase_index, phase in enumerate(PHASES):
        for frame in range(SAMPLES):
            progress = frame/INTERVALS
            for part in PARTS:
                parent = f'destiny:{KEY}_{part}'
                if part == 'shell' and not shell_visible(phase, progress):
                    parent += '_hidden'
                for grip in GRIPS:
                    emit(A/f'models/{KEY}_{phase}_{frame:02}_{part}_{grip}.json', {
                        'parent': parent, 'display': pose_display(source['display'], twohand, phase, progress, part, grip)})
            def composite(grip):
                return {'type': 'minecraft:composite', 'models': [
                    {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{phase}_{frame:02}_{part}_{grip}'} for part in PARTS]}
            node = {'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
                    'on_true': composite('twohand'), 'on_false': composite('native')}
            # Preserve the entire canonical endpoint graph, including metadata.
            if (phase == 'initial' and frame == 0) or (phase == 'return' and frame == INTERVALS):
                node = copy.deepcopy(canonical['model'])
            entries.append({'threshold': threshold(phase_index, frame), 'model': node})
        if phase != 'return':
            # CMD4's inactive inter-bank gaps must not retain an active pose.
            entries.append({'threshold': after_float32(phase_index*2+1), 'model': copy.deepcopy(canonical['model'])})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data', 'index': 4,
                'entries': entries, 'fallback': copy.deepcopy(canonical['model'])}
    modes = {'type': 'minecraft:select', 'property': 'minecraft:custom_model_data', 'index': 0,
             'cases': [{'when': mode, 'model': copy.deepcopy(canonical['model'])} for mode in ('ads','inspect')],
             'fallback': dispatch}
    wrapper = copy.deepcopy(canonical)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': modes}], 'fallback': copy.deepcopy(canonical['model'])}
    emit(A/f'items/{KEY}.json', wrapper)
    input_hashes = {str(p): sha(raw) for p, raw in raw_inputs.items()}
    input_hashes.update({str(RIG): sha(rig_raw), str(ART/'profile.json'): sha(profile_raw)})
    emit(ART/'manifest.json', {
        'schemaVersion': 1, 'stage': 'W221', 'weapon': WEAPON,
        'generator': 'scripts/generate_insert_w221_'+WEAPON+'.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'itemModel': 'destiny:'+KEY, 'requiredParts': list(PARTS),
        'phases': list(PHASES), 'phaseRanges': [[0,1],[2,3],[4,5]],
        'framesPerPhase': SAMPLES, 'intervalsPerPhase': INTERVALS, 'totalPoseSamples': 183,
        'progressFloatIndex': 4, 'gripFlagIndex': 0, 'inactiveGapGuards': 2,
        'thresholdEncoding': 'float32(phase*2 + float32(frame/60))',
        'parents': 3, 'displayChildren': 732, 'packFiles': len(output), 'generatedFiles': len(output)+1,
        'bodyElements': len(source['elements']), 'shellElements': len(shell['elements']),
        'maxAssembledElements': assembled, 'ordinaryArmReserve': ARM_RESERVE, 'elementLimit': 1000,
        'bodyGeometryAndUVPreserved': True, 'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'newTextures': 0, 'gripPivot': GRIP, 'shellAnchor': SHELL_ANCHOR,
        'shellKeyframes': SHELL_KEYS, 'visibility': VISIBLE,
        'curve': 'PCHIP C1 weighted harmonic tangents; zero endpoints, holds and extrema',
        'hiddenShell': 'Empty geometry only; ordinary scale; hidden HOME recycle after seating; zero-speed phase seams',
        'heldSeams': [['initial',60],['loop',0],['loop',60],['return',0]],
        'canonicalEndpoints': [['initial',0],['return',60]],
        'rig': {'path': str(RIG), 'group': rig['group'], 'reload': reload['rigAction'],
                'action': action['action'], 'sourceFrameRange': [action['start'],action['end']],
                'evaluatedReloadSamples': len(action['frames']), 'cameraExported': rig.get('cameraExported',False)},
        'sourceEvidence': copy.deepcopy(SOURCE_EVIDENCE),
        'sourcePoseCalibration': 'Shared body and full chain initial .35*smooth(p/.36); loop .35/frame36; return same pose blended to rest. Authored calibration, not recovered shell-loop.',
        'sourceWeaponMotion': True, 'sourcePalmContactFit': True,
        'mechanicsOrAudioChanged': False, 'nativeGameplayVerified': False, 'fingerIK': False,
        'masterIntegration': 'Load W221 profile/rig; route CMD4 three-phase60 grid; enable Parcel shared sourceShellPoseHold and sourcePalmContactFit; compose original body and chain together; framing once. Preserve actual per-shell timing and W219 cancellable final-shell sound.',
        'limitations': ['No weapon mesh, camera or per-weapon selector in original armature file.',
                       'Authored shell path and material donors require FIRST feedback then SECOND Vision.',
                       '448 arms is a conservative reservation; master measures actual assembled skin geometry.',
                       '61 poses are discrete bank samples, not proof of continuous60fps.'],
        'inputSha256': input_hashes,
        'outputSha256': {str(p.relative_to(root)): sha(raw) for p, raw in output.items()},
    })
    return output
