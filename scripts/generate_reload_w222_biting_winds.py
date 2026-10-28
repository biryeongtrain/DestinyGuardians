#!/usr/bin/env python3
"""Pure W222 Biting Winds RIGHT-hand nock carrier, not the W50 draw action.

Import/generate only read inputs and return absolute Path -> bytes. Master
replays the original weapon and both shoulder/elbow/wrist chains once, then
materializes the pack. No recovered arrow mesh or event track is available.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
WEAPON = 'biting_winds'
ART = Path('art/weapons/w222') / WEAPON
GENERATOR = Path('scripts/generate_reload_w222_biting_winds.py')
PROFILE = ART / 'profile.json'
MANIFEST = ART / 'manifest.json'
SOURCE = A / 'models/weapon_surface_w123/biting_winds.json'
NATIVE = A / 'models/weapon/bow/biting_winds.json'
TWOHAND = A / 'models/weapon/bow/biting_winds_twohand.json'
ITEM = A / 'items/weapon/biting_winds.json'
CONTACTS = Path('art/weapons/w201/contacts.json')
FRAMING = Path('art/weapons/w205/first-person-framing.json')
SURFACE_MAP = Path('src/main/resources/weapon_surface_w123/manifest.json')
DESIGN = Path('art/weapons/w123/biting_winds/design.json')
TIMING = Path('src/main/resources/destiny/weapons/w46-timing.json')
SOUND = Path('src/main/resources/destiny/sounds/w63-reload.json')
RIG = Path('art/weapons/w222/rigs/bow_6239be39.json')
KEY = 'weapon_reload_w222_biting_winds/biting_winds'
SOURCE_GROUP = 'bow_6239be39'
SOURCE_ACTION = '80A8A207'
ACTION_NAME = 'Armature|fp_80A8A207_reload_full|Base'
FP = ('firstperson_righthand', 'firstperson_lefthand')
GRIPS = ('native', 'twohand')
PARTS = ('body',)
SAMPLES, INTERVALS = 61, 60
ARM_ELEMENT_RESERVE = 448
SOURCE_SETTINGS = {
    'sourceFullChain': True, 'keepMeshSupport': True,
    'hideSupportAtRest': False, 'sourceViewRotation': [0, 0, 0],
    'sourceWeaponMotion': True,
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def expected_output_paths():
    return ({A / f'models/{KEY}_body.json'}
            | {A / f'models/{KEY}_{i:02}_body_{grip}.json'
               for i in range(SAMPLES) for grip in GRIPS}
            | {A / f'items/{KEY}.json', MANIFEST})


def generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[Path, bytes]:
    """Return bytes only; overrides may be absolute or relative to root."""
    root = Path(root).resolve()

    def location(override, default):
        path = Path(override) if override is not None else default
        return path if path.is_absolute() else root / path

    profile_raw = location(profile_path, PROFILE).read_bytes()
    rig_raw = location(rig_path, RIG).read_bytes()
    profile, rig = json.loads(profile_raw), json.loads(rig_raw)
    inputs = (SOURCE, NATIVE, TWOHAND, ITEM, CONTACTS, FRAMING,
              SURFACE_MAP, DESIGN, TIMING, SOUND)
    raw = {p: (root / p).read_bytes() for p in inputs}
    source, native, twohand, item, contacts, config, surface_map, design = (
        json.loads(raw[p]) for p in
        (SOURCE, NATIVE, TWOHAND, ITEM, CONTACTS, FRAMING, SURFACE_MAP, DESIGN))
    contacts = contacts['weapons'][WEAPON]
    if (profile.get('schemaVersion') != 1 or profile.get('stage') != 'W222'
            or profile.get('weapon') != WEAPON or profile.get('sourceAction') != SOURCE_ACTION):
        raise ValueError('Invalid W222 Biting Winds profile')
    # Keep calibrated contacts, including the bow-specific right nocking target.
    expected_contacts = {side: copy.deepcopy(contacts[side]) for side in ('right', 'left', 'reload')}
    expected_contacts['reload'].update(hand='right', policy='bow', rigAction=SOURCE_ACTION)
    if profile['contacts'] != expected_contacts:
        raise ValueError('Existing bow contacts or RIGHT-hand nock policy changed')
    effective = {**config['families'].get('bow', config['default']),
                 **config.get('weapons', {}).get(WEAPON, {}), **SOURCE_SETTINGS}
    if profile['framing'] != effective:
        raise ValueError('Existing bow framing plus full-source settings required')
    action = rig['actions'][SOURCE_ACTION]
    required = {'weapon', 'leftShoulder', 'leftElbow', 'leftWrist',
                'rightShoulder', 'rightElbow', 'rightWrist'}
    if (rig.get('group') != SOURCE_GROUP or rig.get('fallback') is not False
            or WEAPON not in rig['weapons'] or rig.get('cameraExported') is not False
            or rig.get('space') != 'armature_object'
            or rig.get('w222Source61', {}).get('reloadSamples') != SAMPLES
            or action['action'] != ACTION_NAME or (action['start'], action['end']) != (1., 29.)
            or len(action['frames']) != SAMPLES
            or any(abs(f['progress'] - i / INTERVALS) > 1e-12
                   or abs(f['frame'] - (1 + 28 * i / INTERVALS)) > 1e-10
                   or not required <= f['joints'].keys()
                   for i, f in enumerate(action['frames']))):
        raise ValueError('Fresh original 61-pose nock/full shoulder chains required')
    provenance = profile['sourceRig']
    if (provenance.get('path') != str(RIG) or provenance.get('group') != SOURCE_GROUP
            or provenance.get('action') != SOURCE_ACTION
            or provenance.get('cacheSha256') != sha(rig_raw)
            or provenance.get('sourceBlend') != rig.get('sourceBlend')
            or any(provenance.get(k) != rig.get(k)
                   for k in ('sourceBlendSha256', 'sourceMapSha256', 'boneMapSha256'))):
        raise ValueError('Authoritative source cache/provenance changed')
    rule = next(r for r in surface_map['targets']
                if r['path'] == str(NATIVE).removeprefix('src/main/resources/'))
    if (rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/')
            or rule['replacementSha256'] != sha(raw[SOURCE])):
        raise ValueError('Effective canonical bow surface changed')
    # This is a complete resting carrier: the 23 existing arrow/string pieces
    # remain byte-equivalent as element data. No new arrow event is invented.
    names = [e['name'] for e in source['elements']]
    if (len(names) != len(set(names))
            or set(names) != set(design['body_element_names'] + design['moving_element_names'])):
        raise ValueError('Complete semantic body/resting arrow-string contract changed')
    for ctx in FP:
        if source['display'][ctx] != native['display'][ctx]:
            raise ValueError('Canonical native hip calibration mismatch')

    # Read existing W50 alternatives only to bound their simultaneous elements.
    # They are neither emitted nor folded into the source nock carrier.
    w50_body = A / 'models/weapon_bow_w50/biting_winds_body_hip.json'
    w50_states = sorted((root / A / 'models/weapon_bow_w50').glob('biting_winds_*_hip.json'))
    if not w50_states:
        raise ValueError('Existing W50 draw/nock assets required')
    for path in w50_states:
        raw[path.relative_to(root)] = path.read_bytes()
    moving_count = max(len(json.loads(raw[p.relative_to(root)]).get('elements', []))
                       for p in w50_states if p.relative_to(root) != w50_body)
    w50_count = len(json.loads(raw[w50_body])['elements']) + moving_count
    weapon_count = len(source['elements'])
    estimate = max(weapon_count, len(native['elements']), w50_count) + ARM_ELEMENT_RESERVE
    if estimate > 1000:
        raise ValueError('Weapon plus four ordinary skin-arm surfaces exceeds 1000')

    output, allowed = {}, expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError('Output outside exclusive W222 Biting Winds namespace')
        output[root / path] = encode(value)

    emit(A / f'models/{KEY}_body.json', copy.deepcopy(source))
    entries = []
    canonical = item['model']
    for i in range(SAMPLES):
        for grip in GRIPS:
            # Neutral accepted display in BOTH FP contexts. Master applies
            # original source motion once; never bake a generic body sweep.
            display = source['display'] if grip == 'native' else twohand['display']
            emit(A / f'models/{KEY}_{i:02}_body_{grip}.json', {
                'parent': f'destiny:{KEY}_body', 'display': copy.deepcopy(display)})
        node = copy.deepcopy(canonical) if i in (0, INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_body_twohand'},
            'on_false': {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{i:02}_body_native'}}
        entries.append({'threshold': float32(i / INTERVALS), 'model': node})
    dispatch = {'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data',
                'index': 1, 'entries': entries, 'fallback': copy.deepcopy(canonical)}
    # Outer guards preserve the entire original ADS/inspect graphs regardless
    # of the canonical graph's internal selectors (W50 routes stay master-owned).
    modes = {'type': 'minecraft:select', 'property': 'minecraft:custom_model_data', 'index': 0,
             'cases': [{'when': mode, 'model': copy.deepcopy(canonical)} for mode in ('ads', 'inspect')],
             'fallback': dispatch}
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': list(FP), 'model': modes}], 'fallback': copy.deepcopy(canonical)}
    emit(A / f'items/{KEY}.json', wrapper)
    raw.update({PROFILE: profile_raw, RIG: rig_raw, GENERATOR: Path(__file__).read_bytes()})
    emit(MANIFEST, {
        'schemaVersion': 1, 'stage': 'W222', 'weapon': WEAPON, 'mode': 'reload',
        'generator': str(GENERATOR), 'generatorSha256': sha(raw[GENERATOR]),
        'itemModel': 'destiny:' + KEY, 'requiredParts': list(PARTS),
        'frames': SAMPLES, 'intervals': INTERVALS, 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'thresholdEncoding': 'exact float32(i/60)', 'firstPersonContexts': list(FP),
        'staticParts': 1, 'parentDisplayChildren': SAMPLES * len(GRIPS),
        'packFiles': len(output), 'totalReturnedFiles': len(allowed),
        'sourceGroup': SOURCE_GROUP, 'sourceAction': SOURCE_ACTION, 'rigAction': SOURCE_ACTION,
        'rigActionName': ACTION_NAME, 'sourceActionSourceRange': [1, 29],
        'sourceRigPath': str(RIG), 'sourceRigSamples': SAMPLES, 'sourceRig': provenance,
        'sourceReviewEvidence': profile['evidence'], 'sourceFullChain': True,
        'sourceActionWeaponExclusive': False, 'sourceCameraRecovered': False,
        'reloadHand': 'right', 'stabilizingHand': 'left', 'policy': 'bow', 'partHint': 'moving',
        'motionAuthorship': 'Neutral body carrier. Master replays original weapon and both shoulder/elbow/wrist chains once. Entire action is RIGHT-hand nocking; no draw or authored arrow events.',
        'sourceGeometryPath': str(SOURCE), 'sourceGeometryFileSha256': sha(raw[SOURCE]),
        'sourceElements': weapon_count, 'bodyElements': weapon_count, 'weaponElements': weapon_count,
        'partElements': {'body': weapon_count}, 'addedElements': 0, 'triangleAdapterElements': 0,
        'restArrowStringElements': len(design['moving_element_names']),
        'geometryAndUVPreserved': True, 'bodyElementsAndUVSha256': sha(encode(source['elements'])),
        'restArrowStringPreserved': True, 'w50DrawRouteChanged': False,
        'canonicalWeaponElements': len(native['elements']), 'existingW50MaxWeaponElements': w50_count,
        'ordinaryArmElementReserve': ARM_ELEMENT_RESERVE,
        'candidateReloadWithArmsEstimate': weapon_count + ARM_ELEMENT_RESERVE,
        'maxAssembledElements': estimate, 'elementLimit': 1000, 'assembledBudgetVerified': False,
        'budgetBasis': 'Maximum of complete semantic rest carrier, raw canonical full model, or raw W50 body plus one moving state; add448 for four ordinary skin-arm surfaces. Alternatives never summed.',
        'hipEndpoints': [0, INTERVALS], 'endpointDisplayExact': True, 'fallbackModelExact': True,
        'endpointPolicy': 'Exact canonical graph at0/1, negative fallback, overshoot and nonFP; original ADS/inspect graph guarded before dispatch.',
        'bodyCarrierNeutral': True, 'gameplayTimingChanged': False, 'mechanicsOrAudioChanged': False,
        'unchangedTimingSnapshot': next(t for t in json.loads(raw[TIMING]) if t['id'] == WEAPON),
        'unchangedReloadSoundSnapshot': next((t for t in json.loads(raw[SOUND])['entries'] if t['id'] == WEAPON), None),
        'reloadSoundSnapshotScope': 'Existing W63 per-ID entry only; null means absent. No audio assets or routing changed.',
        'nativeGameplayVerified': False, 'nativeVisibilityAccepted': False,
        'masterIntegration': 'Load W222 profile/cache and bind80A8A207/61poses to CMD1 reload. Preserve separate W50 draw route, RIGHT string displacement and lowered LEFT riser anchor after source_palm_translations. Materialize source motion once; FIRST feedback/same-worker review then SECOND Vision.',
        'limitations': profile['notes'],
        'inputSha256': {str(p): sha(b) for p, b in raw.items()},
        'outputSha256': {str(p.relative_to(root)): sha(b) for p, b in output.items()},
    })
    if set(output) != {root / p for p in allowed}:
        raise ValueError('Incomplete W222 output mapping')
    return output
