#!/usr/bin/env python3
"""Pure W222 Whispering Slab nock carrier; master replays the source chain.

Import/generate only read inputs and return absolute Path -> bytes. No source
weapon mesh/arrow events/camera were recovered. W50 owns draw displacement.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
WEAPON = 'whispering_slab'
ART = Path('art/weapons/w222') / WEAPON
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
GENERATOR = Path('scripts/generate_reload_w222_whispering_slab.py')
SOURCE = A / f'models/weapon_surface_w123/{WEAPON}.json'
NATIVE = A / f'models/weapon/bow/{WEAPON}.json'
TWOHAND = A / f'models/weapon/bow/{WEAPON}_twohand.json'
ITEM = A / f'items/weapon/{WEAPON}.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
RIG = Path('art/weapons/w222/rigs/bow_6239be39.json')
QA = Path('docs/qa/2026-10-28/w222')
KEY = 'weapon_reload_w222_whispering_slab/whispering_slab'
SOURCE_GROUP = 'bow_6239be39'
SOURCE_ACTION = '80A8A207'
ACTION_NAME = 'Armature|fp_80A8A207_reload_full|Base'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
PARTS = ('body',)
SAMPLES, INTERVALS = 61, 60
ARM_ELEMENT_RESERVE = 448
CHAIN_SETTINGS = {'sourceFullChain': True, 'keepMeshSupport': True,
                  'hideSupportAtRest': False, 'sourceViewRotation': [0, 0, 0],
                  'sourceWeaponMotion': True}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    """Match Java's normalized float progress, including non-dyadic thresholds."""
    return struct.unpack('!f', struct.pack('!f', value))[0]


def pose_display(original, twohand, progress, part, grip):
    """Accepted neutral display, with no second application of source motion."""
    if (not math.isfinite(progress) or not 0 <= progress <= 1
            or part not in PARTS or grip not in GRIPS):
        raise ValueError((progress, part, grip))
    return copy.deepcopy(original if grip == 'native' else twohand)


def expected_output_paths():
    return ({A / f'models/{KEY}_body.json', A / f'items/{KEY}.json', MANIFEST}
            | {A / f'models/{KEY}_{i:02}_body_{grip}.json'
               for i in range(SAMPLES) for grip in GRIPS})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Read root-relative inputs; overrides may be absolute or root-relative.

    Return bytes only in this weapon's exclusive namespaces. Materialization,
    source weapon/shoulder replay, hands, routing and native QA belong to master.
    """
    root = Path(root).resolve()
    inputs = (SOURCE, NATIVE, TWOHAND, ITEM, CONTACTS, FRAMING, SURFACE_MAP,
              RIG, PROFILE, GENERATOR, QA / 'source-review.json',
              QA / 'source-handling-evidence.json', QA / 'selection.json')
    locations = {path: root / path for path in inputs}
    if rig_path is not None:
        locations[RIG] = root / Path(rig_path)
    if profile_path is not None:
        locations[PROFILE] = root / Path(profile_path)
    locations[GENERATOR] = Path(__file__).resolve()
    raw = {path: location.read_bytes() for path, location in locations.items()}
    source, native, twohand, item, contacts, config, surface, rig, profile = (
        json.loads(raw[path]) for path in
        (SOURCE, NATIVE, TWOHAND, ITEM, CONTACTS, FRAMING, SURFACE_MAP, RIG, PROFILE))
    contacts = contacts['weapons'][WEAPON]
    review = json.loads(raw[QA / 'source-review.json'])['groups'][SOURCE_GROUP]
    handling = next(row for row in json.loads(raw[QA / 'source-handling-evidence.json'])['rows']
                    if row['group'] == SOURCE_GROUP)
    selection = json.loads(raw[QA / 'selection.json'])
    rule = next(row for row in surface['targets']
                if row['path'] == str(NATIVE).removeprefix('src/main/resources/'))
    if (rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/')
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Effective canonical bow surface drift')
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W222'
            or profile.get('weapon') != WEAPON or profile.get('sourceAction') != SOURCE_ACTION
            or selection['actions'][WEAPON] != SOURCE_ACTION
            or WEAPON not in selection['groups'][SOURCE_GROUP]):
        raise ValueError('Invalid W222 bow selection/profile')
    reload = profile['contacts']['reload']
    expected_reload = {**contacts['reload'], 'hand': 'right', 'policy': 'bow',
                       'partHint': 'body', 'rigAction': SOURCE_ACTION}
    if (profile['contacts']['right'] != contacts['right']
            or profile['contacts']['left'] != contacts['left']
            or reload != expected_reload or contacts['left']['position'][0] != 6.38):
        raise ValueError('Preserve calibrated contacts and RIGHT nock / LEFT offset riser')
    effective = {**config['families'].get('bow', config['default']),
                 **config.get('weapons', {}).get(WEAPON, {}), **CHAIN_SETTINGS}
    if profile['framing'] != effective:
        raise ValueError('Preserve effective framing; source motion/chain applied once')
    action = rig['actions'][SOURCE_ACTION]
    required = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
                'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or WEAPON not in rig['weapons'] or rig.get('cameraExported') is not False
            or rig.get('space') != 'armature_object'
            or rig.get('w222Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1., 29.)
            or len(action['frames']) != SAMPLES
            or any(abs(frame['progress'] - i / INTERVALS) > 1e-12
                   or abs(frame['frame'] - (1 + 28 * i / INTERVALS)) > 1e-10
                   or not required <= frame['joints'].keys()
                   for i, frame in enumerate(action['frames']))):
        raise ValueError('Original 61-sample bow weapon/shoulder/elbow/wrist chain required')
    for frame in action['frames']:
        for name in required:
            matrix = frame['joints'][name]
            if (len(matrix) != 4 or any(len(row) != 4 for row in matrix)
                    or not all(math.isfinite(v) for row in matrix for v in row)):
                raise ValueError('Invalid original chain matrix: ' + name)
    provenance = profile['sourceRig']
    if (provenance.get('path') != str(RIG) or provenance.get('group') != SOURCE_GROUP
            or provenance.get('action') != SOURCE_ACTION
            or provenance.get('sourceAction') != SOURCE_ACTION
            or provenance.get('sha256') != sha(raw[RIG])
            or provenance.get('cacheSha256') != sha(raw[RIG])
            or handling['sourceCacheSha256'] != sha(raw[RIG])):
        raise ValueError('Original cache/action provenance drift')
    for field in ('sourceBlend', 'sourceMap', 'boneMap'):
        if (provenance.get(field) != review['paths'][field]
                or provenance.get(field + 'Sha256') != rig[field + 'Sha256']
                or provenance[field + 'Sha256'] != review['inputSha256'][field]):
            raise ValueError('Original source provenance drift: ' + field)
    canonical = item['model']
    if (canonical.get('type') != 'minecraft:select'
            or canonical.get('property') != 'minecraft:custom_model_data'
            or canonical.get('index', 0) != 0
            or not {'ads', 'inspect'} <= {c['when'] for c in canonical['cases']}):
        raise ValueError('Canonical ADS/inspect guard required')
    count = len(source['elements'])
    canonical_count = len(native['elements'])
    estimate = max(count, canonical_count) + ARM_ELEMENT_RESERVE
    if estimate > 1000:
        raise ValueError('Weapon plus four ordinary arm surfaces exceeds budget')
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W222 Whispering Slab namespace')
        output[root / path] = encode(value)

    # Entire current rest model, including its existing string and arrow.
    emit(A / f'models/{KEY}_body.json', copy.deepcopy(source))
    entries = []
    for i in range(SAMPLES):
        for grip in GRIPS:
            emit(A / f'models/{KEY}_{i:02}_body_{grip}.json', {
                'parent': 'destiny:' + KEY + '_body',
                'display': pose_display(source['display'], twohand['display'],
                                        i / INTERVALS, 'body', grip)})

        def body(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_body_{grip}'}]}

        node = copy.deepcopy(canonical) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': body('twohand'), 'on_false': body('native')}
        entries.append({'threshold': float32(i / INTERVALS), 'model': node})
    guard = copy.deepcopy(canonical)
    guard['fallback'] = {
        'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data', 'index': 1,
        'entries': entries, 'fallback': copy.deepcopy(canonical)}
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': guard}],
                        'fallback': copy.deepcopy(canonical)}
    emit(A / f'items/{KEY}.json', wrapper)
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W222', 'weapon': WEAPON,
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'frames': SAMPLES, 'intervals': INTERVALS,
        'progressFloatIndex': 1, 'gripFlagIndex': 0, 'thresholdEncoding': 'exact float32(i/60)',
        'firstPersonContexts': list(FP), 'requiredParts': list(PARTS),
        'staticParts': 1, 'parentDisplayChildren': SAMPLES * len(GRIPS),
        'packFiles': len(output), 'totalReturnedFiles': len(allowed),
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'geometryAndUVPreserved': True, 'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'partElements': {'body': count}, 'bodyElements': count, 'weaponElements': count,
        'movingElements': 0, 'addedElements': 0, 'triangleAdapterElements': 0, 'newTextures': 0,
        'canonicalWeaponElements': canonical_count, 'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000, 'assembledBudgetVerified': False,
        'budgetBasis': 'Current full rest surface or raw canonical alternative plus448 reserved ordinary skin-arm elements; master measures integrated routes.',
        'sourceRig': provenance, 'sourceRigPath': str(RIG), 'sourceGroup': SOURCE_GROUP,
        'sourceAction': SOURCE_ACTION, 'rigAction': SOURCE_ACTION, 'rigActionName': ACTION_NAME,
        'sourceActionSourceRange': [1, 29], 'sourceRigSamples': len(action['frames']),
        'sourceFullChain': True, 'sourceWeaponMotion': True, 'sourceCameraRecovered': False,
        'sourceActionWeaponExclusive': False, 'sourceReviewEvidence': profile['evidence'],
        'sourceHandlingEvidence': handling, 'reloadHand': 'right', 'stabilizingHand': 'left',
        'policy': 'bow', 'partHint': 'body', 'leftRiserContactX': 6.38,
        'bodyCarrier': 'Neutral accepted native/twohand displays at every sample.',
        'motionAuthorship': 'Master replays original weapon and both complete shoulder/elbow/wrist chains once. Entire source action is nock; no authored recovered arrow event, source draw or camera claim.',
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'endpointPolicy': 'Exact canonical graph at0/1, negative fallback, overshoot and nonFP; original ADS/inspect cases precede CMD1 dispatch.',
        'restArrowAndStringPreserved': True, 'w50DrawRoutingChanged': False,
        'masterIntegration': 'Bind exact ID/action61 at CMD1; retain W50 draw hand displacement and lowered LEFT riser anchor. Materialize neutral body plus source weapon/full chain once. FIRST images to same worker, then SECOND.',
        'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'limitations': profile['notes'],
        'inputSha256': {str(path): sha(data) for path, data in raw.items()},
        'outputSha256': {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root / path for path in allowed}:
        raise ValueError('Incomplete W222 output mapping')
    return output
