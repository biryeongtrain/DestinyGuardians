#!/usr/bin/env python3
"""W151 isolated ADS bodies. Canonical artwork and animation graphs are inputs only.

Standard library only. --verify compares bytes without writing. No shared generator
is imported or executed; W148 shotgun_body supplies the structural pattern only.
"""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path('src/main/resources/assets/destiny')
NAMESPACE = 'weapon_sight_w151'
MANIFEST = Path('art/weapons/w151/rifles-sights.json')
SIGHT_TEXTURE = ASSETS / 'textures/item/weapon/w148/sights.png'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')
WEAPONS = {
    'halfdan_d': dict(family='auto_rifle', center=[8, 13.65, 7.57],
        style='hakke_iron', front=-4.68, seat=13.08, width=.24, depth=.34,
        donor='Sight_sill', removed=[],
        cues='Ivory HAKKE split ears on a raised rectangular foot, low sill and long toothed rail; retain the inward-canted ears, no added optic.'),
    'ammit_ar2': dict(family='auto_rifle', center=[8, 14.0, 7.54],
        style='omolon_peep', front=-8.7, seat=13.34, width=.16, depth=.22,
        donor='Peep_post_-1', removed=[],
        cues='Blue alloy OMOLON rear peep with narrow parallel uprights and short bridge; long smooth blue upper and small silver muzzle-top cue, no scope.'),
    'gnawing_hunger': dict(family='auto_rifle', center=[8, 12.95, 2.91],
        style='round_reflex', front=2.83, seat=12.56, width=.09, depth=.12,
        donor='optic/stalk', removed=[],
        cues='Short dark round reflex hood on a narrow stalk, rectangular adjuster behind it, white wrapped receiver; retain all eight rotated hood staves.'),
    'steelfeather_repeater': dict(family='auto_rifle', center=[8, 13.12, 5.07],
        style='sundial_open_u', front=-4.93, seat=12.57, width=.18, depth=.24,
        donor='sight_ear_-1', removed=[],
        cues='Silver open U cradle above the swept silver receiver; tall straight ears with no roof and a short angled saddle ahead, not a round reflex.'),
    'frontier_justice': dict(family='scout_rifle', center=[8, 13.36, 7.68],
        style='hakke_ga_post', front=-4.24, seat=12.71, width=.22, depth=.30,
        donor='post_cheek_-1', removed=[],
        cues='Pewter GA POST on a stepped HAKKE riser, chamfered upper cheeks and short cap; long toothed rail over chipped navy receiver, distinct from Halfdan.'),
    'distant_relation': dict(family='scout_rifle', center=[8, 11.88, 7.25],
        style='gambit_box_scope', front=4.30, seat=11.46, width=.085, depth=.10,
        donor='optic_mount_0',
        removed=['optic_housing_core', 'optic_housing_shoulder_l',
                 'objective_glass', 'ocular_glass'],
        cues='Dark teal box scope with circular objective, silver ocular rim, two feet and low side dials; retain the 16 rotated rim staves and replace only the filled housing/glass across the axis.'),
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_bytes())


def source_path(weapon):
    suffix = '_body' if weapon == 'ammit_ar2' else ''
    return ASSETS / f'models/weapon_surface_w123/{weapon}{suffix}.json'


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rotation_matrix(rotation):
    """Native element order Rz*Ry*Rx; also accept legacy axis/angle records."""
    angles = {a: rotation.get(a, 0) for a in 'xyz'}
    if 'axis' in rotation:
        angles[rotation['axis']] = rotation['angle']
    x, y, z = (math.radians(angles[a]) for a in 'xyz')
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return matmul(rz, matmul(ry, rx))


def inverse_point(element, point):
    """Transform a world point into a cuboid's local frame, including rescale."""
    r = element.get('rotation', {})
    origin = r.get('origin', [0, 0, 0])
    matrix = rotation_matrix(r)
    q = [point[i] - origin[i] for i in range(3)]
    # R is orthonormal, so inverse(R) = transpose(R).
    local = [sum(matrix[j][i] * q[j] for j in range(3)) for i in range(3)]
    if r.get('rescale'):
        if 'axis' not in r:
            raise ValueError('rescale requires a legacy axis/angle rotation')
        factor = abs(math.cos(math.radians(r['angle'])))
        local = [v if 'xyz'[i] == r['axis'] else v * factor for i, v in enumerate(local)]
    return [local[i] + origin[i] for i in range(3)]


def ray_hit(element, start, end):
    """Exact finite segment / rotated solid-box slab test; no Z sampling/AABB proxy.

    Treat every source face as opaque: an opaque lens cannot be waved through by
    calling its material glass. Both native XYZ and legacy rotations are inverted.
    """
    a, b = inverse_point(element, start), inverse_point(element, end)
    entry, exit_ = 0.0, 1.0
    for axis in range(3):
        direction = b[axis] - a[axis]
        lo, hi = element['from'][axis], element['to'][axis]
        if abs(direction) < 1e-12:
            if a[axis] < lo - 1e-9 or a[axis] > hi + 1e-9:
                return False
        else:
            t0, t1 = (lo - a[axis]) / direction, (hi - a[axis]) / direction
            entry, exit_ = max(entry, min(t0, t1)), min(exit_, max(t0, t1))
            if entry > exit_ + 1e-10:
                return False
    return True


def sight_rays(row):
    """7x7 parallel and perspective bundles through a genuinely empty square.

    Model units are 1/16 metre before the .9 item scale. Include everything from
    the actual eye plane to Z=-40, rather than testing only the new frame's depth.
    """
    x, y, z = row['sightCenter']
    eye_z = z + row['eyeToSightMeters'] * 16 / row['scale']
    half = row['clearApertureHalfSize']
    for dx, dy in itertools.product([half * i / 3 for i in range(-3, 4)], repeat=2):
        yield [x + dx, y + dy, eye_z], [x + dx, y + dy, -40]
        factor = (eye_z + 40) / (eye_z - z)
        yield [x, y, eye_z], [x + dx * factor, y + dy * factor, -40]


def blockers(model, row):
    hits = set()
    for start, end in sight_rays(row):
        hits.update(e['name'] for e in model['elements'] if ray_hit(e, start, end))
    return sorted(hits)


def box(name, lo, hi, donor=None, uv=None):
    if donor is None:
        faces = {f: dict(texture='#sight', uv=list(uv)) for f in FACES}
    else:
        faces = copy.deepcopy(donor['faces'])
        # A small center patch of the source sight metal; no invented body paint.
        for face in faces.values():
            u, v, u1, v1 = face['uv']
            face['uv'] = [round(u + (u1-u)*.35, 7), round(v + (v1-v)*.35, 7),
                          round(u + (u1-u)*.65, 7), round(v + (v1-v)*.65, 7)]
    return dict(name='w151_' + name, **{'from': lo, 'to': hi}, faces=faces)


def scope_slice(donor, name, lo, hi):
    """Hollow the old optic using its existing atlas/material and planar UV scale."""
    element = dict(name='w151_' + name, **{'from': lo, 'to': hi}, faces=copy.deepcopy(donor['faces']))
    axes = dict(north=(0, 1, True, True), south=(0, 1, False, True),
                east=(2, 1, True, True), west=(2, 1, False, True),
                up=(0, 2, False, False), down=(0, 2, False, True))
    for face, data in element['faces'].items():
        uaxis, vaxis, flipu, flipv = axes[face]
        bounds = []
        for axis, flip in [(uaxis, flipu), (vaxis, flipv)]:
            length = donor['to'][axis] - donor['from'][axis]
            a, b = (lo[axis]-donor['from'][axis])/length, (hi[axis]-donor['from'][axis])/length
            bounds.append((1-b, 1-a) if flip else (a, b))
        u, v, u1, v1 = data['uv']
        data['uv'] = [round(u+(u1-u)*bounds[0][0], 7), round(v+(v1-v)*bounds[1][0], 7),
                      round(u+(u1-u)*bounds[0][1], 7), round(v+(v1-v)*bounds[1][1], 7)]
    return element


def make_body(weapon, cfg):
    source = source_path(weapon)
    model = read(source)
    by_name = {e['name']: e for e in model['elements']}
    if len(by_name) != len(model['elements']):
        raise ValueError(f'{weapon}: duplicate source names')
    for name in cfg['removed']:
        if name not in by_name:
            raise ValueError(f'{weapon}: absent removal {name}')
    model = {k: copy.deepcopy(v) for k, v in model.items() if k != 'display'}
    model['elements'] = [e for e in model['elements'] if e['name'] not in cfg['removed']]
    if weapon == 'distant_relation':
        # Only these two filled sight volumes are split; all chassis and old rim
        # elements, including their UVs/rotations, survive byte-value-exact.
        core = by_name['optic_housing_core']
        shoulder = by_name['optic_housing_shoulder_l']
        pieces = [
            (core, 'scope_floor', [7.6112, 11.23, 4.21], [8.3888, 11.49, 7.09]),
            (core, 'scope_ceiling', [7.6112, 12.27, 4.21], [8.3888, 12.53, 7.09]),
            (core, 'scope_inner_left', [7.6112, 11.49, 4.21], [7.72, 12.27, 7.09]),
            (core, 'scope_inner_right', [8.28, 11.49, 4.21], [8.3888, 12.27, 7.09]),
            (shoulder, 'scope_outer_left', [7.46, 11.425, 4.21], [7.6112, 12.335, 7.09]),
            (shoulder, 'scope_outer_right', [8.3888, 11.425, 4.21], [8.54, 12.335, 7.09]),
        ]
        model['elements'].extend(scope_slice(*piece) for piece in pieces)
    x, y, z = cfg['center']
    front, width, depth = cfg['front'], cfg['width'], cfg['depth']
    # Tip is physically .085 below sight center, leaving air even in perspective.
    # These are simplified physical guides, not a floating card or a D2 reticle rip.
    tip_top, tip_bottom = round(y-.085, 6), round(y-.245, 6)
    model['elements'].append(box('aim_stem',
        [round(x-width/2, 6), cfg['seat'], round(front-depth/2, 6)],
        [round(x+width/2, 6), tip_bottom, round(front+depth/2, 6)], donor=by_name[cfg['donor']]))
    model['elements'].append(box('aim_tip',
        [7.96, tip_bottom, round(front-.05, 6)],
        [8.04, tip_top, round(front+.05, 6)], uv=(4.25, .25, 4.75, .75)))
    model['textures']['sight'] = 'destiny:item/weapon/w148/sights'
    magazine = ASSETS / 'models/weapon_surface_w123/ammit_ar2_magazine.json'
    companion_count = len(read(magazine)['elements']) if weapon == 'ammit_ar2' else 0
    row = dict(id=weapon, family=cfg['family'], body=f'{NAMESPACE}/{weapon}_body',
        sightCenter=list(cfg['center']), forwardPoint=[x, y, round(z-2, 6)],
        style=cfg['style'], eyeSide='+Z', plane='XY', scale=.9, eyeToSightMeters=.65,
        removedSightNames=list(cfg['removed']), elementCount=len(model['elements']),
        source=source.as_posix(), sourceSha256=sha((ROOT/source).read_bytes()),
        clearApertureHalfSize=.03, aimingTip=[8, tip_top, front], aimingTipName='w151_aim_tip',
        addedSightNames=[e['name'] for e in model['elements'] if e['name'].startswith('w151_')],
        companionElementCount=companion_count,
        assemblyElementCount=len(model['elements'])+companion_count,
        assemblyWithSpareMagazineCount=len(model['elements'])+2*companion_count)
    if companion_count:
        row['companionModel'] = magazine.as_posix()
        row['companionSha256'] = sha((ROOT/magazine).read_bytes())
    if row['assemblyWithSpareMagazineCount'] > 1000:
        raise ValueError(f'{weapon}: assembly exceeds 1000 emitted elements')
    blocked = blockers(model, row)
    if blocked:
        raise ValueError(f'{weapon}: blocked sight channel: {blocked}')
    # Every removed part must actually obstruct the selected ADS channel.
    for name in cfg['removed']:
        if not any(ray_hit(by_name[name], a, b) for a, b in sight_rays(row)):
            raise ValueError(f'{weapon}: unjustified removal {name}')
    return model, row


def generate():
    references = {r['id']: r for r in read('art/weapons/w31/references.json')}
    outputs, rows = {}, []
    for weapon, cfg in WEAPONS.items():
        model, row = make_body(weapon, cfg)
        photo = Path(f'/tmp/destiny-weapons-w31/references/{weapon}.jpg')
        record = references[weapon]
        if sha(photo.read_bytes()) != record['sha256']:
            raise ValueError(f'{weapon}: default photo differs from W31 provenance')
        prior = Path('art/weapons/w123') / weapon
        manifest = read(prior / 'manifest.json')
        row['reference'] = dict(photo=str(photo), photoSha256=record['sha256'],
            screenshot=record['screenshot'], bungieHash=record['bungie_hash'],
            notes=cfg['cues'], limitation='Single default three-quarter photo; hidden rear details follow prior source study. Physical pale aiming tip is an ADS visibility adaptation, not extracted shader/reticle.',
            provenance={str(prior/p): sha((ROOT/prior/p).read_bytes()) for p in ('review.md', 'design.json', 'manifest.json')},
            priorRipSha256={p: h for p, h in manifest['raw_input_sha256'].items() if p.lower().endswith(('.fbx', '.blend'))})
        row['sightTextureSha256'] = sha((ROOT/SIGHT_TEXTURE).read_bytes())
        outputs[ASSETS / f"models/{row['body']}.json"] = encode(model)
        rows.append(row)
    outputs[MANIFEST] = encode(dict(weapons=rows))
    return outputs


def mismatches(outputs):
    return [str(path) for path, data in outputs.items()
            if not (ROOT/path).is_file() or (ROOT/path).read_bytes() != data]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    outputs = generate()
    if args.verify:
        bad = mismatches(outputs)
        if bad:
            parser.exit(1, 'W151 output mismatch: ' + ', '.join(bad) + '\n')
    else:
        for path, data in outputs.items():
            (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/path).write_bytes(data)
    print(f"W151 rifles: 6 weapons, {len(outputs)} generated outputs " + ('verified' if args.verify else 'written'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
