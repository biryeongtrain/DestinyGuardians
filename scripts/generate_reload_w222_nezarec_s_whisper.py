#!/usr/bin/env python3
"""Pure W222 Nezarec's Whisper carrier for master-owned source-chain replay.

Import/generate only read inputs and return bytes. The intact body has no local
animation: master applies the actual source weapon bone and both full arms once.
No detachable cell, source mesh, camera or finger animation is claimed.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
WEAPON = 'nezarec_s_whisper'
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w222') / WEAPON
GENERATOR = Path('scripts/generate_reload_w222_nezarec_s_whisper.py')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
SOURCE = A / f'models/weapon_surface_w123/{WEAPON}.json'
NATIVE = A / f'models/weapon/glaive/{WEAPON}.json'
TWOHAND = A / f'models/weapon/glaive/{WEAPON}_twohand.json'
ITEM = A / f'items/weapon/{WEAPON}.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
TIMING = Path('src/main/resources/destiny/weapons/w46-timing.json')
SOUND = Path('src/main/resources/destiny/sounds/w63-reload.json')
RIG = Path('art/weapons/w222/rigs/glaive_f9784d8f.json')
KEY = f'weapon_reload_w222_{WEAPON}/{WEAPON}'
SOURCE_GROUP = 'glaive_f9784d8f'
SOURCE_ACTION = '80A8A440'
ACTION_NAME = 'Armature|fp_80A8A440_reload_full|Base'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
PARTS = ('body',)
SAMPLES, INTERVALS = 61, 60
ARM_ELEMENT_RESERVE = 448
# Existing global X-forward/Z-up calibration. The glaive's remodeled shaft is
# +Y, so its weapon-local replay additionally needs the derived rigid Q below.
SOURCE_TO_CANONICAL = ((0, -1, 0), (0, 0, 1), (-1, 0, 0))


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def source_mesh_basis(rig, contacts):
    """Shortest arc from source idle grip direction to accepted mesh direction.

    This fixes weapon-local axes, not screen framing. It adds no arbitrary
    twist about the shaft, scale ratio, source-pose attenuation or camera fit.
    Master must use Q coherently for weapon, wrist and whole forearm chains.
    """
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    def unit(v):
        length = math.sqrt(dot(v, v))
        if length < 1e-8:
            raise ValueError('Cannot derive mesh basis from a degenerate grip/bone')
        return [x / length for x in v]

    def cross(a, b):
        return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]

    def vec(m, v):
        return [dot(row, v) for row in m]

    rest = rig['actions'][rig['idle']]['frames'][0]['joints']
    weapon = rest['weapon']
    # Match shared weapon_basis: remove tiny exported scale/shear before inverse.
    x = unit([weapon[i][0] for i in range(3)])
    y = [weapon[i][1] for i in range(3)]
    projection = dot(y, x)
    y = unit([y[i] - projection * x[i] for i in range(3)])
    z = unit(cross(x, y))
    y = cross(z, x)
    separation = [rest['leftWrist'][i][3] - rest['rightWrist'][i][3] for i in range(3)]
    source = unit(vec(SOURCE_TO_CANONICAL, vec([x, y, z], separation)))
    target = unit([contacts['left']['position'][i] - contacts['right']['position'][i]
                   for i in range(3)])
    v = cross(source, target)
    cosine = dot(source, target)
    if 1 + cosine < 1e-8:
        raise ValueError('Antiparallel grip directions leave the shortest-arc axis ambiguous')
    skew = [[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]
    squared = [[sum(skew[i][k] * skew[k][j] for k in range(3))
                for j in range(3)] for i in range(3)]
    return [[(1 if i == j else 0) + skew[i][j] + squared[i][j] / (1 + cosine)
             for j in range(3)] for i in range(3)]


def pose_display(original, twohand, progress, part, grip):
    """Accepted carrier unchanged at every pose, in both FP handed contexts."""
    if (part not in PARTS or grip not in GRIPS
            or not math.isfinite(progress) or not 0 <= progress <= 1):
        raise ValueError('Expected body/native-or-twohand and normalized progress')
    return copy.deepcopy(original if grip == 'native' else twohand)


def expected_output_paths():
    return ({A / f'models/{KEY}_body.json'}
            | {A / f'models/{KEY}_{i:02}_body_{grip}.json'
               for i in range(SAMPLES) for grip in GRIPS}
            | {A / f'items/{KEY}.json', MANIFEST})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Read only; overrides change input locations, never output namespaces."""
    root = Path(root).resolve()

    def location(override, default):
        path = Path(override) if override is not None else default
        return path if path.is_absolute() else root / path

    paths = (SOURCE, NATIVE, TWOHAND, ITEM, CONTACTS, FRAMING, SURFACE_MAP,
             TIMING, SOUND, PROFILE, RIG)
    locations = {p: root / p for p in paths}
    locations[PROFILE] = location(profile_path, PROFILE)
    locations[RIG] = location(rig_path, RIG)
    raw = {p: path.read_bytes() for p, path in locations.items()}
    raw[GENERATOR] = Path(__file__).read_bytes()
    source, native, twohand, item, profile, rig = (
        json.loads(raw[p]) for p in (SOURCE, NATIVE, TWOHAND, ITEM, PROFILE, RIG))
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W222'
            or profile.get('weapon') != WEAPON or profile.get('sourceAction') != SOURCE_ACTION):
        raise ValueError('Expected W222 Nezarec source profile')

    contacts = json.loads(raw[CONTACTS])['weapons'][WEAPON]
    reload = profile['contacts']['reload']
    if (any(profile['contacts'][side] != contacts[side] for side in ('right', 'left'))
            or reload.get('hand') != 'right' or reload.get('policy') != 'fixed'
            or reload.get('partHint') != 'loading_port' or reload.get('rigAction') != SOURCE_ACTION
            or any(reload.get(k) != contacts['reload'][k] for k in ('contact', 'rotation'))):
        raise ValueError('Preserve calibrated shaft contacts and estimated fixed port; RIGHT reload')
    config = json.loads(raw[FRAMING])
    effective = {**config['families'].get(contacts['family'], config['default']),
                 **config.get('weapons', {}).get(WEAPON, {})}
    required_framing = dict(sourceFullChain=True, keepMeshSupport=True,
                            hideSupportAtRest=False, sourceViewRotation=[0, 0, 0],
                            sourceWeaponMotion=True, sourceMeshPivot=True)
    basis = profile['framing'].get('sourceMeshBasis')
    derived_basis = source_mesh_basis(rig, contacts)
    if (not isinstance(basis, list) or len(basis) != 3
            or any(not isinstance(row, list) or len(row) != 3 for row in basis)
            or any(not math.isfinite(basis[i][j]) or abs(basis[i][j] - derived_basis[i][j]) > 1e-12
                   for i in range(3) for j in range(3))):
        raise ValueError('sourceMeshBasis must be derived from actual idle source/mesh grip directions')
    if {k: v for k, v in profile['framing'].items() if k != 'sourceMeshBasis'} != {**effective, **required_framing}:
        raise ValueError('Keep current framing; opt in to coherent source basis and pivot registration only')

    provenance = profile['sourceRig']
    if (provenance.get('path') != str(RIG) or provenance.get('group') != SOURCE_GROUP
            or provenance.get('action') != SOURCE_ACTION
            or provenance.get('sourceAction') != SOURCE_ACTION
            or provenance.get('cacheSha256') != sha(raw[RIG])
            or provenance.get('sha256') != sha(raw[RIG])
            or provenance.get('sourceBlend') != rig.get('sourceBlend')
            or any(provenance.get(k) != rig.get(k) for k in
                   ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'))):
        raise ValueError('Original source/cache provenance mismatch')
    action = rig['actions'][SOURCE_ACTION]
    joints = {'weapon'} | {side + joint for side in ('left', 'right')
                          for joint in ('Shoulder', 'Elbow', 'Wrist')}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or WEAPON not in rig['weapons'] or rig.get('space') != 'armature_object'
            or rig.get('cameraExported') is not False
            or rig.get('w222Source61', {}).get('reloadSamples') != SAMPLES
            or action.get('action') != ACTION_NAME
            or (action.get('start'), action.get('end')) != (1., 123.)
            or len(action['frames']) != SAMPLES):
        raise ValueError('Expected master-evaluated original 61-pose glaive action')
    for i, frame in enumerate(action['frames']):
        if (abs(frame['progress'] - i / INTERVALS) > 1e-12
                or abs(frame['frame'] - (1 + 122 * i / INTERVALS)) > 1e-10
                or not joints <= frame['joints'].keys()):
            raise ValueError('Source sample grid or full arm-chain missing')
        for joint in joints:
            matrix = frame['joints'][joint]
            if len(matrix) != 4 or any(len(row) != 4 or not all(map(math.isfinite, row)) for row in matrix):
                raise ValueError('Expected finite original 4x4 joint matrices')

    rule = next(r for r in json.loads(raw[SURFACE_MAP])['targets']
                if r['path'] == str(NATIVE.relative_to(Path('src/main/resources'))))
    if (rule['replacement'] != str(SOURCE.relative_to(Path('src/main/resources')))
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Current surface mapping does not select this preserved geometry')
    canonical = item['model']
    if (canonical.get('type') != 'minecraft:select'
            or canonical.get('property') != 'minecraft:custom_model_data'
            or canonical.get('index', 0) != 0
            or not {'ads', 'inspect'} <= {mode for case in canonical['cases']
                 for mode in (case['when'] if isinstance(case['when'], list) else [case['when']])}):
        raise ValueError('Expected canonical ADS/inspect selector')
    count = len(source['elements'])
    estimate = max(count, len(native['elements'])) + ARM_ELEMENT_RESERVE
    if estimate > 1000:
        raise ValueError('Weapon plus four ordinary arm surfaces exceeds element reserve')
    allowed = expected_output_paths()
    output = {}

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W222 Nezarec namespace')
        output[root / path] = encode(value)

    emit(A / f'models/{KEY}_body.json', copy.deepcopy(source))
    entries = []
    for i in range(SAMPLES):
        for grip in GRIPS:
            emit(A / f'models/{KEY}_{i:02}_body_{grip}.json', {
                'parent': f'destiny:{KEY}_body',
                'display': pose_display(source['display'], twohand['display'], i / INTERVALS, 'body', grip)})

        def carrier(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_body_{grip}'}]}

        node = copy.deepcopy(canonical) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': carrier('twohand'), 'on_false': carrier('native')}
        entries.append({'threshold': float32(i / INTERVALS), 'model': node})
    guard = copy.deepcopy(canonical)
    guard['fallback'] = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                         'index': 1, 'entries': entries, 'fallback': copy.deepcopy(canonical)}
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': guard}], 'fallback': copy.deepcopy(canonical)}
    emit(A / f'items/{KEY}.json', wrapper)
    timing = next(t for t in json.loads(raw[TIMING]) if t['id'] == WEAPON)
    sound = next(t for t in json.loads(raw[SOUND])['entries'] if t['id'] == WEAPON)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W222', 'weapon': WEAPON, 'generator': str(GENERATOR),
        'generatorSha256': sha(raw[GENERATOR]), 'profileSha256': sha(raw[PROFILE]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'thresholdEncoding': 'exact float32(i/60)', 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'firstPersonContexts': list(FP), 'requiredParts': list(PARTS), 'staticParts': 1,
        'parentDisplayChildren': SAMPLES * len(GRIPS), 'packFiles': len(output),
        'totalReturnedFiles': len(allowed), 'sourceRig': provenance,
        'sourceGroup': SOURCE_GROUP, 'sourceAction': SOURCE_ACTION, 'rigAction': SOURCE_ACTION,
        'sourceRigPath': str(RIG), 'sourceRigSha256': sha(raw[RIG]), 'rigActionName': ACTION_NAME,
        'sourceActionSourceRange': [1, 123], 'sourceRigSamples': SAMPLES, 'sourceFullChain': True,
        'sourceWeaponMotion': True, 'sourceCameraRecovered': False, 'sourceMeshRecovered': False,
        'sourceMeshBasis': basis, 'sourceMeshPivot': True,
        'sourceMeshBasisDerivation': 'Shortest arc: normalized C*idleWeaponBasis^T*(leftWrist-rightWrist) to normalized calibrated mesh(leftGrip-rightGrip); no extra shaft twist or length rescale.',
        'sourceMeshPivotDerivation': 'O=(rightGrip-8)-32*Q*C*idleWeaponBasis^T*(idleRightWrist-idleWeapon); local body translation32*Q*shift+(I-Q*A*Q^T)*O before accepted scale/rotation.',
        'sourceReviewEvidence': profile['evidence'], 'sourceGeometryPath': str(SOURCE),
        'sourceGeometryFileSha256': sha(raw[SOURCE]), 'sourceElements': count,
        'partElements': {'body': count}, 'bodyElements': count, 'weaponElements': count,
        'movingElements': 0, 'addedElements': 0, 'triangleAdapterElements': 0,
        'canonicalWeaponElements': len(native['elements']), 'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000, 'assembledBudgetVerified': False,
        'measuredAllRouteElements': None,
        'budgetBasis': 'Whole surface body or canonical model plus448 reserve for four ordinary skin-arm surfaces; alternatives not summed. Master measures integrated routes.',
        'geometryAndUVPreserved': True, 'canonicalGeometryAndUVPreserved': True,
        'partElementsAndUVSha256': {'body': sha(encode(source['elements']))},
        'reloadHand': 'right', 'stabilizingHand': 'left', 'policy': 'fixed', 'partHint': 'loading_port',
        'reloadContact': reload['contact'], 'sourceMaximumWeaponRelativeWristExcursion': profile['sourceHandling'],
        'motionAuthorship': 'Neutral whole-body carrier; master replays original weapon bone and both complete shoulder/elbow/wrist chains once with coherent derived sourceMeshBasis and sourceMeshPivot registration. No invented cell, part event, authored weapon sweep or source-camera fit.',
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'endpointPolicy': 'Exact canonical graph at0/1, negative fallback, overshoot and nonFP; original ADS/inspect cases precede CMD1 dispatch.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'unchangedTimingSnapshot': timing, 'unchangedReloadSoundSnapshot': sound,
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'limitations': profile['notes'],
        'inputSha256': {str(p): sha(data) for p, data in raw.items()},
        'outputSha256': {str(p.relative_to(root)): sha(data) for p, data in output.items()}})
    if set(output) != {root / p for p in allowed}:
        raise ValueError('Incomplete owned output mapping')
    return output
