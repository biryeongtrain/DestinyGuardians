#!/usr/bin/env python3
"""Dust Rock Blues: held, one-shell insert presentation; no disk writes.

Master calls generate() and writes its absolute Path -> bytes mapping. Import
and generation are inert with respect to the filesystem. No third-party deps.
The W123 97-solid body/UV and accepted native/twohand displays remain the inputs;
W206 framing and source-rig skin arms are applied once by the shared pipeline.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w207/dust_rock_blues'
KEY = 'weapon_insert_w207_dust_rock_blues/dust_rock_blues'
SOURCE = A / 'models/weapon_surface_w123/dust_rock_blues.json'
TWOHAND = A / 'models/weapon/shotgun/dust_rock_blues_twohand.json'
ITEM = A / 'items/weapon/dust_rock_blues.json'
CONTACTS = ROOT / 'art/weapons/w201/contacts.json'
DESIGN = ROOT / 'art/weapons/w123/dust_rock_blues/design.json'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
GRIPS = ('native', 'twohand')
PARTS = ('body', 'shell')
STEPS = 60
GRIP = (8.0, 7.9, 11.42)
SHELL_ANCHOR = (7.3, 9.15, 7.1)
HOLD_ROTATION = (22.0, -6.0, -32.0)
HOLD_SHIFT = (-0.2, 0.65, 0.15)  # source model units, scaled exactly once
PREPARE_END = 0.30
HOME = (-1.1, -2.4, 1.35)
SEATED = (0.7, 0.45, -0.55)
# Cubic Hermite path. Interior bring/approach knots carry nonzero velocity;
# intentional rests only at the pickup, seated hold, and hidden recycle ends.
SHELL_KEYS = ((0.0, HOME), (0.15, HOME),
              (0.36, (-0.3, -1.35, 0.7)),
              (0.58, (0.7, -0.52, 0.0)),
              (0.76, SEATED), (0.82, SEATED), (1.0, HOME))
REST_KNOTS = {0, 1, 4, 5, 6}
VISIBLE = (0.16, 0.80)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def vec(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(m):
    y = math.asin(max(-1.0, min(1.0, m[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0])
    else:
        x, z = math.atan2(m[2][1], m[1][1]), 0
    return [round(math.degrees(v), 9) for v in (x, y, z)]


def smoother(t):
    t = max(0.0, min(1.0, t))
    return t*t*t*(10 + t*(-15 + 6*t))


def tangent(index):
    if index in REST_KNOTS:
        return [0.0]*3
    before, after = SHELL_KEYS[index-1], SHELL_KEYS[index+1]
    return [(b-a)/(after[0]-before[0]) for a, b in zip(before[1], after[1])]


def shell_offset(t):
    if not math.isfinite(t) or not 0 <= t <= 1:
        raise ValueError(t)
    for index, (a, b) in enumerate(zip(SHELL_KEYS, SHELL_KEYS[1:])):
        if t <= b[0]:
            dt = b[0]-a[0]
            u = (t-a[0])/dt
            h = (2*u**3-3*u*u+1, u**3-2*u*u+u, -2*u**3+3*u*u, u**3-u*u)
            ma, mb = tangent(index), tangent(index+1)
            return [h[0]*a[1][i]+h[1]*dt*ma[i]+h[2]*b[1][i]+h[3]*dt*mb[i] for i in range(3)]
    raise ValueError(t)


def sample(phase, p):
    """Body rotation/shift, shell offset, and visibility; C1 at all pose joins."""
    if phase not in PHASES or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError((phase, p))
    if phase == 'return':
        a = 1-smoother(p)
        return [v*a for v in HOLD_ROTATION], [v*a for v in HOLD_SHIFT], list(HOME), False
    q = p if phase == 'loop' else max(0.0, (p-PREPARE_END)/(1-PREPARE_END))
    a = smoother(p/PREPARE_END) if phase == 'initial' else 1.0
    # One smooth periodic held response, not stop-start easing at every sample.
    response = math.sin(math.pi*q)**2 if 0 < q < 1 else 0.0
    angles = add([v*a for v in HOLD_ROTATION], [0.6*response, -0.15*response, -0.4*response])
    shift = add([v*a for v in HOLD_SHIFT], [0.0, 0.045*response, 0.0])
    return angles, shift, shell_offset(q), VISIBLE[0] <= q < VISIBLE[1]


def pose_display(native, twohand, phase, p, part, grip):
    """Rigid source-local grip pivot, then the accepted context transform.

    The shell geometry is centered at SHELL_ANCHOR. Therefore applying this
    display to that same W201 contact gives the moving shell center exactly.
    Empty hidden geometry retains ordinary display scale for the skin hand.
    """
    accepted = native if grip == 'native' else twohand
    result = copy.deepcopy(accepted)
    if part == 'body' and ((phase == 'initial' and p == 0) or (phase == 'return' and p == 1)):
        return result
    angles, shift, offset, _ = sample(phase, p)
    rotation = xyz(angles)
    pivot, anchor = sub(GRIP, (8, 8, 8)), sub(SHELL_ANCHOR, (8, 8, 8))
    local = sub(pivot, vec(rotation, pivot))
    if part == 'shell':
        desired = add(pivot, vec(rotation, add(sub(anchor, pivot), offset)))
        local = sub(desired, vec(rotation, anchor))
    for context in FP:
        d = accepted[context]
        s = d['scale']
        if max(s)-min(s) > 1e-8:
            raise ValueError('Uniform accepted first-person scale required')
        base = xyz(d['rotation'])
        result[context]['rotation'] = euler(mul(base, rotation))
        result[context]['translation'] = [round(v, 9) for v in add(d['translation'], vec(base, [s[0]*x for x in add(local, shift)]))]
    return result


def shell_geometry(source):
    """12 connected solids, own red/steel atlas swatches; longitudinal Z case."""
    by_name = {e.get('name'): e for e in source['elements']}
    elements = []
    for name, radius, z0, z1, swatch in (
            ('case', 0.22, -0.68, 0.42, 'Long_red_shroud'),
            ('head', 0.23, 0.40, 0.60, 'Pump_rib_0_side_-1'),
            ('rim', 0.26, 0.58, 0.68, 'Pump_rib_0_side_-1')):
        uv = by_name[swatch]['faces']['east']['uv']
        u, v = (uv[0]+uv[2])/2, (uv[1]+uv[3])/2
        faces = {face: {'texture': '#0', 'uv': [u, v, u, v]} for face in ('north', 'south', 'east', 'west', 'up', 'down')}
        for angle in (0, 45, -45, 90):
            width = 2*radius*math.tan(math.pi/8)
            size = [width, 2*radius]
            if angle == 90:
                size.reverse()
            e = {'name': 'insert_'+name+'_'+str(angle),
                 'from': [SHELL_ANCHOR[0]-size[0]/2, SHELL_ANCHOR[1]-size[1]/2, SHELL_ANCHOR[2]+z0],
                 'to': [SHELL_ANCHOR[0]+size[0]/2, SHELL_ANCHOR[1]+size[1]/2, SHELL_ANCHOR[2]+z1],
                 'faces': copy.deepcopy(faces)}
            if angle in (45, -45):
                e['rotation'] = {'origin': list(SHELL_ANCHOR), 'axis': 'z', 'angle': angle}
            elements.append(e)
    return {'credit': 'W207 authored shell; own red shroud / silver pump swatches, not extracted ammunition.',
            'textures': copy.deepcopy(source['textures']), 'elements': elements}


def generate():
    """Return only NEW namespace pack assets and one manifest, without writing."""
    source = json.loads(SOURCE.read_bytes())
    twohand = json.loads(TWOHAND.read_bytes())['display']
    canonical = json.loads(ITEM.read_bytes())
    contact = json.loads(CONTACTS.read_bytes())['weapons']['dust_rock_blues']
    if len(source['elements']) != 97 or tuple(contact['reload']['contact']) != SHELL_ANCHOR:
        raise ValueError('Dust geometry/contact contract drift')
    if contact['reload']['partHint'] != 'loading_port' or contact['reload']['policy'] != 'shell':
        raise ValueError('Expected fixed-port per-shell policy')
    output = {}
    def emit(path, value):
        output[path] = encode(value)
    emit(A / f'models/{KEY}_body.json', copy.deepcopy(source))
    shell = shell_geometry(source)
    emit(A / f'models/{KEY}_shell.json', shell)
    emit(A / f'models/{KEY}_shell_hidden.json', {
        'textures': {'particle': source['textures']['particle']}, 'elements': []})
    entries = []
    for phase_index, phase in enumerate(PHASES):
        for i in range(STEPS+1):
            p = i/STEPS
            for part in PARTS:
                visible = sample(phase, p)[3] if part == 'shell' else True
                parent = f'destiny:{KEY}_{part}' + ('' if visible else '_hidden')
                for grip in GRIPS:
                    emit(A / f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json', {
                        'parent': parent,
                        'display': pose_display(source['display'], twohand, phase, p, part, grip)})
            def composite(grip):
                return {'type': 'minecraft:composite', 'models': [
                    {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{phase}_{i:02}_{part}_{grip}'} for part in PARTS]}
            entries.append({'threshold': phase_index*2+i/STEPS, 'model': {
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
    emit(A / f'items/{KEY}.json', wrapper)
    emit(ART / 'manifest.json', {
        'schemaVersion': 1, 'stage': 'W207', 'weapon': 'dust_rock_blues', 'itemModel': 'destiny:'+KEY,
        'framesPerPhase': STEPS+1, 'intervalsPerPhase': STEPS, 'phases': list(PHASES),
        'progressFloatIndex': 4, 'phaseRanges': [[0, 1], [2, 3], [4, 5]], 'gripFlagIndex': 0,
        'displayChildren': 3*(STEPS+1)*2*2, 'generatedFiles': len(output)+1,
        'bodyElements': 97, 'shellElements': len(shell['elements']), 'maxAssembledElements': 97+len(shell['elements']),
        'bothClassicArmFaceElements': 224, 'maxWithBothClassicArms': 97+len(shell['elements'])+224,
        'elementLimit': 1000, 'newTextures': 0, 'bodyGeometryAndUVPreserved': True,
        'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'gripPivot': GRIP, 'shellAnchor': SHELL_ANCHOR, 'shellPath': SHELL_KEYS,
        'holdRotation': HOLD_ROTATION, 'holdShiftModelUnits': HOLD_SHIFT,
        'prepareEnd': PREPARE_END, 'visibilityInNormalizedInsert': VISIBLE,
        'hiddenShell': 'Empty parent with ordinary display scale; hand contact must not inherit a visibility shrink.',
        'continuity': 'C1 cubic Hermite shell path with shared nonzero tangents at bring/approach knots; quintic prepare/return; periodic held response. All held body and shell seams coincide with zero boundary velocity.',
        'shellClearance': 'Approach center [8,8.63,7.1] stays below floor Y9.18; seated center [8,9.6,6.55] and the entire cartridge lie inside Loading_housing. No port cut; hide at seat, recycle while empty.',
        'returnTicks': 6, 'returnBlocksGameplay': False, 'mechanicsOrAudioChanged': False,
        'masterIntegration': 'Add Java support/model route with 60 intervals for Dust only. Shared skin arms: initial idle->shell, loop follows normal-scale shell display, return shell->idle. Apply W206 framing once. No arm geometry/length changes.',
        'fallback': 'Exact current canonical graph for non-firstperson and ADS/inspect; inactive negative float4 selects canonical fallback.',
        'reference': {'url': 'https://www.youtube.com/watch?v=5IZfs2bjrYY',
                      'actualPng': 'art/weapons/w178/first_in_last_out/reference-06.png',
                      'limitation': 'Related First In, Last Out shotgun only. Gesture and occluded Dust cartridge path are authored, not extracted animation or recovered camera.'},
        'nativeGameplayVerified': False,
        'sourceSha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (SOURCE, TWOHAND, ITEM, CONTACTS, DESIGN)},
        'outputSha256': {str(p.relative_to(ROOT)): sha(raw) for p, raw in output.items()}})
    allowed = (A/'models'/KEY).parent
    for path in output:
        if not path.is_absolute() or not (path == ART/'manifest.json' or
                (path.parent == allowed and path.name.startswith('dust_rock_blues')) or
                path == A/f'items/{KEY}.json'):
            raise ValueError('Output outside new namespace: '+str(path))
    return output
