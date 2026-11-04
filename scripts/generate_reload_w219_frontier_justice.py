#!/usr/bin/env python3
"""W219 Frontier Justice: pure split-magazine input for original-chain replay.

Import and generate() never write. The master framing/hands builder replaces
the neutral body carrier with the selected original weapon bone and replays
both complete shoulder chains. Only the mesh-local magazine path is authored.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w219/frontier_justice')
GENERATOR = Path('scripts/generate_reload_w219_frontier_justice.py')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
SOURCE = A / 'models/weapon_surface_w123/frontier_justice.json'
NATIVE = A / 'models/weapon/scout_rifle/frontier_justice.json'
TWOHAND = A / 'models/weapon/scout_rifle/frontier_justice_twohand.json'
ITEM = A / 'items/weapon/frontier_justice.json'
TEXTURE = A / 'textures/item/weapon/w123/frontier_justice.png'
DESIGN = Path('art/weapons/w123/frontier_justice/design.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
RIG = Path('art/weapons/w219/rigs/scout_rifle_a3826f40.json')
TIMING = Path('src/main/resources/destiny/weapons/w46-timing.json')
SOUND = Path('src/main/resources/destiny/sounds/w63-reload.json')
KEY = 'weapon_reload_w219_frontier_justice/frontier_justice'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
GRIPS = ('native', 'twohand')
SAMPLES, INTERVALS = 61, 60
SOURCE_GROUP = 'scout_rifle_a3826f40'
SOURCE_ACTION = '80A8A345'
ACTION_NAME = 'Armature|fp_80A8A345_reload_full|Base'
MOVING = (123, 124, 125)
MOVING_NAMES = ('magazine', 'magazine_floor', 'magazine_rear_bevel')
RELOAD_HAND = 'left'
GRIP_WINDOW = (.04, .10, .40, .48)
MAGAZINE_ANCHOR = (8., 7.45, 12.4)
ARM_ELEMENT_RESERVE = 4 * 112
# Authored rigid withdrawal, not an extracted mesh/event track. The long left
# source excursion is early; reseat/release precedes its later receiver motion.
# Retain the actual three solids/UVs without a shaft, fade, or scale animation.
MAGAZINE_KEYS = (
    (0., (0., 0., 0.)),
    (.10, (0., 0., 0.)),
    (.20, (0., -3.8, .25)),
    (.32, (0., -3.8, .25)),
    (.40, (0., -1.5, .10)),
    (.48, (0., 0., 0.)),
    (1., (0., 0., 0.)),
)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def tangents(times, values):
    steps = [b-a for a, b in zip(times, times[1:])]
    secants = [(b-a)/h for a, b, h in zip(values, values[1:], steps)]
    result = [0.] * len(times)
    for i in range(1, len(times)-1):
        before, after = secants[i-1], secants[i]
        if before * after > 0:
            w1, w2 = 2*steps[i]+steps[i-1], steps[i]+2*steps[i-1]
            result[i] = (w1+w2)/(w1/before+w2/after)
    return result


def magazine_offset(progress):
    """C1 weighted PCHIP: zero velocity at holds, endpoints and extrema."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError('Expected finite normalized progress')
    for time, value in MAGAZINE_KEYS:
        if progress == time:
            return list(value)
    times = [k[0] for k in MAGAZINE_KEYS]
    i = next(i for i in range(len(times)-1) if progress < times[i+1])
    h = times[i+1]-times[i]
    t = (progress-times[i])/h
    result = []
    for axis in range(3):
        values = [k[1][axis] for k in MAGAZINE_KEYS]
        slopes = tangents(times, values)
        result.append((2*t**3-3*t*t+1)*values[i] + (t**3-2*t*t+t)*h*slopes[i]
                      + (-2*t**3+3*t*t)*values[i+1] + (t**3-t*t)*h*slopes[i+1])
    return result


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]


def vec(matrix, vector):
    return [sum(matrix[i][k]*vector[k] for k in range(3)) for i in range(3)]


def pose_display(original, twohand, progress, part, grip):
    """Neutral carrier; sourceFullChain replaces body in the shared builder.

    Use each accepted grip/context frame directly, so native/twohand and left
    hand carry the same local displacement. No source motion is double-baked.
    """
    if part not in PARTS or grip not in GRIPS:
        raise ValueError((part, grip))
    accepted = original if grip == 'native' else twohand
    result = copy.deepcopy(accepted)
    if progress in (0, 1) or part == 'body':
        return result
    offset = magazine_offset(progress)
    for context in FP:
        pose = result[context]
        scale = pose['scale']
        if len(set(scale)) != 1:
            raise ValueError('Rigid magazine requires uniform FP scale')
        shift = vec(xyz(pose['rotation']), [scale[0]*v for v in offset])
        pose['translation'] = [round(v+s, 9) for v, s in zip(pose['translation'], shift)]
    return result


def partition(source):
    return {part: {
        **{k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'},
        'elements': [copy.deepcopy(e) for i, e in enumerate(source['elements'])
                     if (i in MOVING) == (part == 'magazine')]}
        for part in PARTS}


def expected_output_paths():
    return ({A / f'models/{KEY}_{part}.json' for part in PARTS}
            | {A / f'models/{KEY}_{i:02}_{part}_{grip}.json'
               for i in range(SAMPLES) for part in PARTS for grip in GRIPS}
            | {A / f'items/{KEY}.json', MANIFEST})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return absolute Path -> bytes; optional read-only scratch inputs for prep.

    Default inputs always come from root. No old hashes of master shared files
    are pinned. Output namespaces remain rooted at root even with prep inputs.
    """
    root = Path(root).resolve()
    inputs = [SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, DESIGN, SURFACE_MAP,
              CONTACTS, FRAMING, TIMING, SOUND, PROFILE, RIG, GENERATOR]
    locations = {path: root / path for path in inputs}
    if rig_path is not None:
        locations[RIG] = Path(rig_path).resolve()
    if profile_path is not None:
        locations[PROFILE] = Path(profile_path).resolve()
    # During no-write preparation, generator bytes come from this owned file.
    locations[GENERATOR] = Path(__file__).resolve()
    raw = {path: location.read_bytes() for path, location in locations.items()}
    source, native, twohand, item, design, profile, rig = (
        json.loads(raw[path]) for path in (SOURCE, NATIVE, TWOHAND, ITEM, DESIGN, PROFILE, RIG))
    elements = source['elements']
    if (len(elements) != 141 or tuple(elements[i]['name'] for i in MOVING) != MOVING_NAMES
            or elements[126]['name'] != 'charging_handle'
            or tuple(p['geometry']['name'] for p in design['parts'] if p['group'] == 'magazine') != MOVING_NAMES):
        raise ValueError('Frontier Justice semantic magazine/fixed controls changed')
    rule = next(r for r in json.loads(raw[SURFACE_MAP])['targets']
                if r['path'] == 'assets/destiny/models/weapon/scout_rifle/frontier_justice.json')
    if (rule['replacement'] != 'assets/destiny/models/weapon_surface_w123/frontier_justice.json'
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Selected Frontier Justice surface mapping changed')
    contacts = json.loads(raw[CONTACTS])['weapons']['frontier_justice']
    reload = profile['contacts']['reload']
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W219'
            or profile.get('weapon') != 'frontier_justice'
            or profile.get('sourceAction') != SOURCE_ACTION
            or reload.get('rigAction') != SOURCE_ACTION
            or reload.get('hand') != RELOAD_HAND or reload.get('partHint') != 'magazine'
            or reload.get('policy') != 'magazine' or reload.get('gripWindow') != list(GRIP_WINDOW)
            or reload.get('contact') != contacts['reload']['contact']
            or reload.get('rotation') != contacts['reload']['rotation']
            or profile['contacts']['right'] != contacts['right']
            or profile['contacts']['left'] != contacts['left']):
        raise ValueError('Original rest/reload contacts or W219 profile changed')
    config = json.loads(raw[FRAMING])
    effective = {**config['families'].get('scout_rifle', config['default']),
                 **config.get('weapons', {}).get('frontier_justice', {})}
    for field, value in effective.items():
        if profile['framing'].get(field) != value:
            raise ValueError('Effective current framing changed: ' + field)
    if any(profile['framing'].get(field) is not value for field, value in (
            ('sourceFullChain', True), ('keepMeshSupport', True), ('hideSupportAtRest', False))):
        raise ValueError('Expected ordinary visible full source arm chains')
    action = rig['actions'][SOURCE_ACTION]
    marker = rig.get('w219Source61', {})
    required = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
                'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or 'frontier_justice' not in rig['weapons'] or rig.get('cameraExported') is not False
            or rig.get('space') != 'armature_object'
            or marker.get('reloadSamples') != SAMPLES
            or marker.get('cameraExported') is not False
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1., 105.)
            or len(action['frames']) != SAMPLES
            or any(abs(f['progress']-i/INTERVALS) > 1e-12
                   or abs(f['frame']-(1+104*i/INTERVALS)) > 1e-10
                   or not required <= f['joints'].keys()
                   for i, f in enumerate(action['frames']))):
        raise ValueError('Expected fresh original W219 61-pose full shoulder rig')
    for field in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'):
        if rig[field] != profile['sourceRig'][field]:
            raise ValueError('Original source provenance changed: ' + field)
    if (profile['sourceRig']['group'] != SOURCE_GROUP
            or profile['sourceRig']['action'] != SOURCE_ACTION
            or profile['sourceRig']['path'] != str(RIG)):
        raise ValueError('Invalid sourceRig selection')
    geometries = partition(source)
    counts = {part: len(geo['elements']) for part, geo in geometries.items()}
    estimate = max(sum(counts.values()), len(native['elements'])) + ARM_ELEMENT_RESERVE
    if counts != {'body': 138, 'magazine': 3} or estimate > 1000:
        raise ValueError('Weapon plus four classic arm surfaces exceeds budget')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside own W219 Frontier Justice namespace')
        output[root / path] = encode(value)

    for part, geometry in geometries.items():
        emit(A / f'models/{KEY}_{part}.json', geometry)
    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f'models/{KEY}_{frame:02}_{part}_{grip}.json', {
                    'parent': f'destiny:{KEY}_{part}',
                    'display': pose_display(source['display'], twohand['display'], progress, part, grip)})

        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in PARTS]}

        node = copy.deepcopy(item['model']) if frame in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': node})
    guard = copy.deepcopy(item['model'])
    if (guard.get('type') != 'minecraft:select' or guard.get('property') != 'minecraft:custom_model_data'
            or guard.get('index', 0) != 0 or [case['when'] for case in guard['cases']] != ['ads', 'inspect']):
        raise ValueError('Canonical ADS/inspect guard changed')
    guard['fallback'] = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                         'index': 1, 'entries': entries, 'fallback': copy.deepcopy(item['model'])}
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': guard}],
                        'fallback': copy.deepcopy(item['model'])}
    emit(A / f'items/{KEY}.json', wrapper)
    timing = next(t for t in json.loads(raw[TIMING]) if t['id'] == 'frontier_justice')
    sound = next(t for t in json.loads(raw[SOUND])['entries'] if t['id'] == 'frontier_justice')
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W219', 'weapon': 'frontier_justice',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'thresholdEncoding': 'exact float32(i/60)', 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'firstPersonContexts': list(FP), 'staticParts': 2, 'parentDisplayChildren': 244,
        'packFiles': len(output), 'totalReturnedFiles': len(allowed),
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': len(elements), 'partElements': counts, 'bodyElements': counts['body'],
        'movingElements': counts['magazine'], 'weaponElements': sum(counts.values()),
        'canonicalWeaponElements': len(native['elements']), 'addedElements': 0, 'triangleAdapterElements': 0,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': sum(counts.values()) + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000, 'assembledBudgetVerified': False,
        'budgetBasis': '141 split surface or current canonical geometry plus448 full classic arm surfaces; alternatives not summed. Master measures all integrated routes.',
        'partitionIndices': {part: [i for i in range(len(elements)) if (i in MOVING) == (part == 'magazine')]
                             for part in PARTS},
        'movingIndices': list(MOVING), 'movingNames': list(MOVING_NAMES), 'fixedChargingHandleIndex': 126,
        'magazineAnchor': list(MAGAZINE_ANCHOR), 'magazineKeyframes': MAGAZINE_KEYS,
        'magazineSeatedProgress': .48, 'gripWindow': list(GRIP_WINDOW), 'reloadHand': RELOAD_HAND,
        'curve': 'C1 weighted harmonic PCHIP, exact holds and zero endpoint/extremum tangents',
        'normalizedPhases': {'reach': [0, .10], 'withdrawAuthored': [.10, .20],
                             'exchangeHoldAuthored': [.20, .32], 'reseatAuthored': [.32, .48],
                             'sourceReceiverAndRecovery': [.48, 1]},
        'geometryAndUVPreserved': True,
        'partElementsAndUVSha256': {part: sha(encode(g['elements'])) for part, g in geometries.items()},
        'hipEndpoints': [0, 60], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'fallback': 'Exact canonical graph at0/1, negative inactive, overshoot and nonFP; original ADS/inspect cases precede dispatch.',
        'sourceGroup': SOURCE_GROUP, 'sourceAction': SOURCE_ACTION, 'rigAction': SOURCE_ACTION,
        'rigActionName': action['action'], 'sourceRigPath': str(RIG),
        'sourceActionSourceRange': [action['start'], action['end']], 'sourceRigSamples': len(action['frames']),
        'sourceFullChain': True, 'sourceActionWeaponExclusive': False, 'sourceCameraRecovered': False,
        'sourceReviewEvidence': profile.get('evidence', []), 'partHint': 'magazine', 'policy': 'magazine',
        'motionAuthorship': 'Neutral authored body; master sourceFullChain builder replays original weapon/shoulder chains once. Only three-element magazine local path/contact and gripWindow are authored. Shared master attaches magazine to LEFT source palm during handling, fading to body-relative seat by .48.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'unchangedTimingSnapshot': timing, 'unchangedReloadSoundSnapshot': sound,
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'limitations': [
            'Master evaluated original Blender5.4; worker viewed actual source sheet/report, not independent Blender evaluation.',
            'Shared scout has three ambiguous reload_full variants;80A8A345 is the master reviewed choice, not a unique Frontier Justice selector.',
            'ARMATURE ONLY: no weapon mesh, camera or finger IK; no recovered magazine trajectory or charging-handle actuation.',
            'Ordinary full fingerless player-skin arms: source shoulder/elbow/wrist chains; no length stretch, axis damping or hiding.',
            '61 poses/60 intervals do not establish native continuous60fps interpolation.',
            'FIRST Vision, same-worker actual-image review/correction, integration and SECOND Vision remain pending.'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete own output mapping')
    return output
