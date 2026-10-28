#!/usr/bin/env python3
"""Shared presentation-space calibration for weapon leaves and skin-arm contacts.

Values are authored from gameplay references, not recovered Bungie camera data.
Gun full ADS is identity. Bows can share an explicit camera-depth dolly while
keeping the centered sight's X/Y alignment.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'art/weapons/w205/first-person-framing.json'
PROFILES = ROOT / 'art/weapons/w206'
PREFIX = 'first_person_framing_w205/'


def load():
    data = json.loads(CONFIG.read_bytes())
    assert data['schemaVersion'] == 1
    data['profileInputs'] = {}
    data['contactOverrides'] = {}
    for path in sorted([*PROFILES.glob('*/profile.json'), *(ROOT/'art/weapons/w208').glob('*/profile.json'), *(ROOT/'art/weapons/w210').glob('*/profile.json'), *(ROOT/'art/weapons/w212').glob('*/profile.json'), *(ROOT/'art/weapons/w213').glob('*/profile.json'), *(ROOT/'art/weapons/w214').glob('*/profile.json'), *(ROOT/'art/weapons/w215').glob('*/profile.json'), *(ROOT/'art/weapons/w216').glob('*/profile.json'), *(ROOT/'art/weapons/w217').glob('*/profile.json'), *(ROOT/'art/weapons/w218').glob('*/profile.json'), *(ROOT/'art/weapons/w219').glob('*/profile.json'), *(ROOT/'art/weapons/w220').glob('*/profile.json'), *(ROOT/'art/weapons/w221').glob('*/profile.json')]):
        raw = path.read_bytes()
        entry = json.loads(raw)
        weapon = path.parent.name
        if entry.get('schemaVersion') != 1 or entry.get('weapon') != weapon:
            raise ValueError('Invalid weapon presentation profile: ' + str(path))
        if weapon in data.get('weapons', {}):
            raise ValueError('Duplicate weapon presentation: ' + weapon)
        data.setdefault('weapons', {})[weapon] = entry['framing']
        overrides = entry.get('contacts', {})
        if set(overrides) - {'right', 'left', 'reload'}:
            raise ValueError('Invalid contact override: ' + weapon)
        data['contactOverrides'][weapon] = overrides
        data['profileInputs'][str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return data


def contacts(data, weapon, original):
    result = copy.deepcopy(original)
    for key, values in data.get('contactOverrides', {}).get(weapon, {}).items():
        result[key] = {**result[key], **copy.deepcopy(values)}
    return result


def profile(data, weapon, family):
    return {**data['families'].get(family, data['default']),
            **data.get('weapons', {}).get(weapon, {})}


def weight(state, key):
    mode = state.get('mode', 'hip')
    if mode in ('inspect', 'scope', 'ads'):
        return 0.0
    if 3 in state:
        t = max(0.0, min(1.0, state[3]))
        return 1.0 - t*t*(3-2*t)
    name = key.rsplit('/', 1)[-1]
    if '_ads' in name or '_scope' in name or '_inspect' in name:
        return 0.0
    return 1.0


def reload_camera_lift(settings, progress, insert_phase):
    """Keep shell handling visible without resetting at every insert boundary."""
    lift = settings.get('reloadCameraLift', 0)
    if not lift or progress is None or not 0 <= progress <= 1:
        return 0.0
    def smooth(t):
        t = max(0.0, min(1.0, t))
        return t*t*(3-2*t)
    if insert_phase == 'initial':
        envelope = smooth(progress/.36)
    elif insert_phase == 'loop':
        envelope = 1.0
    elif insert_phase == 'return':
        envelope = 1-smooth(progress)
    else:
        envelope = smooth((progress-.02)/.12)*(1-smooth((progress-.80)/.18))
    return lift*envelope


def display(original, settings, amount, xyz, mul, euler, vec):
    result = copy.deepcopy(original)
    for context in ('firstperson_righthand', 'firstperson_lefthand'):
        d = result.get(context, {})
        side = -1 if context.endswith('lefthand') else 1
        rotation = [v * amount for v in settings.get('rotation', [0, 0, 0])]
        rotation[1] *= side
        rotation[2] *= side
        q = xyz(rotation)
        scale = 1 + (settings.get('scale', 1) - 1)*amount
        shift = list(settings.get('translation', [0, 0, 0]))
        shift[0] *= side
        t = vec(q, [v*scale for v in d.get('translation', [0, 0, 0])])
        result[context] = {
            'rotation': euler(mul(q, xyz(d.get('rotation', [0, 0, 0])))),
            'translation': [round(t[i]+shift[i]*amount, 8) for i in range(3)],
            'scale': [round(v*scale, 8) for v in d.get('scale', [1, 1, 1])]
        }
        # Keep gun full-ADS matrices byte-exact before the optional bow dolly.
        if amount == 0:
            result[context] = copy.deepcopy(d)
        # Shared bow camera-space dolly applies to the weapon, all moving
        # parts, and hand contact frames. It changes distance, not arm length.
        # Centered full-ADS sight X/Y stays centered under a pure depth move.
        depth = settings.get('cameraDepth', 0)
        if depth:
            result[context]['translation'][2] += depth
    return result


def weapon_node(ref, calibrated, outputs, assets):
    record = {'parent': ref['model'], 'display': {k:calibrated[k] for k in
                ('firstperson_righthand', 'firstperson_lefthand')}}
    raw = (json.dumps(record, sort_keys=True, separators=(',', ':'))+'\n').encode()
    key = PREFIX + hashlib.sha256(raw).hexdigest()[:24]
    outputs[assets/'models'/(key+'.json')] = raw
    return {**copy.deepcopy(ref), 'model': 'destiny:'+key}


def contact(config, side):
    result = copy.deepcopy(config[side])
    settings = config.get('framing', {})
    # A fingerless block palm needs clearance below the source wrist/nock
    # landmark; its solid top otherwise hides the sight after the bow dolly.
    result['position'][1] -= settings.get(side+'PalmLower', 0)
    # Contact point stays attached to its authored grip. Only the forearm's
    # approach vector changes; Minecraft block hands remain fingerless.
    if side == 'right':
        r = result.get('rotation', [0,0,0]); result['rotation'] = [r[0],r[1],r[2]+settings.get('rightWristRoll', 0)]
    elif 'leftRotation' in settings:
        result['rotation'] = settings['leftRotation']
    return result
