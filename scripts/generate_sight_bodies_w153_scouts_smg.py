#!/usr/bin/env python3
"""W153 ADS-only scout/SMG assemblies. Standard library; --verify never writes.

W151 supplies the manifest and wrapper contract, not the sight designs. Each
assembly retains its actual W123 full model, including its seated magazine once.
No shared generators, canonical assets, dependencies, or native apps are run.
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
MANIFEST = Path('art/weapons/w153/scouts-smg-sights.json')
REVIEW = Path('art/weapons/w153/scouts-smg-review.md')
SIGHT_TEXTURE = ASSETS / 'textures/item/weapon/w148/sights.png'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')
SPECS = {
    'patron_of_lost_causes': dict(center=[8, 12.8, 7.991], eye=.42,
        style='sundial_silver_open_tube', front=6.1, floor=12.425,
        donor='silver_scope_4', removed=['front_recessed_glass', 'rear_recessed_glass'],
        rim=['rear_eyecup_' + str(i) for i in range(8)],
        notes='Silver octagonal long scope and larger rear eyecup, twin feet and low side controls survive with their original UV. Open only the two opaque recessed glass slabs; preserve silver casing, gold tubes, XIV, hook and triangular stock.'),
    'aishas_embrace': dict(center=[8, 12.29, 7.585], eye=.38,
        style='trials_black_box_tube', front=6.8, floor=12.11,
        donor='optic_floor', removed=['front_recessed_lens', 'rear_recessed_lens'],
        rim=['rear_hood_side_-1', 'rear_hood_side_1',
             'rear_hood_cross_11.9', 'rear_hood_cross_12.69'],
        notes='Black rectangular optic with separate end hoods, bevels and right dials over the gold Trials rail. Only the two opaque lens slabs are absent in ADS. Retain the source black/gold furniture, sun and wings and curved stock.'),
    'long_arm': dict(center=[8, 11.33, 3.795], eye=.38,
        style='tex_wrapped_raised_peep', front=3.7, floor=11.195,
        donor='sight_aperture_floor', removed=[],
        rim=['sight_aperture_floor', 'sight_aperture_side-1',
             'sight_aperture_side1', 'sight_aperture_roof'],
        notes='Small raised rectangular peep immediately ahead of the gold braided sight cylinder; retain its four original aperture bars and wrap UV. Cut a shallow ADS-only top groove in the filled cylinder behind the peep, keeping its lower mass and side wrap. Walnut, cloth, barrel daylight and lever remain exact.'),
    'antiope_d': dict(center=[8, 15.22, 7.7], eye=.52,
        style='hakke_peep_and_front_post', front=.93, floor=14.38,
        selfOccluders=['rear_sight_riser'],
        donor='front_sight_post', removed=[],
        rim=['rear_peep_' + str(i) for i in range(8)],
        notes='Original ivory HAKKE eight-piece rear peep and front ears; keep side cylinder as side hardware, not the aiming optic. Extend the existing front post in ADS to the rear peep axis, with a small pale tip. Preserve rail teeth, orange cap, brown grip and silver magazine.'),
    'bug_out_bag': dict(center=[8, 13.85, 3.38], eye=.32,
        style='gambit_short_round_reflex', front=3.11, floor=13.52184,
        donor='optic_rim_4', removed=['optic_lens'],
        rim=['optic_rim_' + str(i) for i in range(8)],
        notes='Short black round reflex and swept rear ramp above the bronze floral shield. Open its opaque lens and lower the occluding ramp top by 0.185 local units, retaining the tilted lower ramp, all eight original rim staves and adjuster. Forward seating keeps the woven cloth saddle out of the optic foreground; cage and wire stock remain exact.'),
    'ikelos_smg_v1_0_1': dict(center=[8, 14.1, 3.8], eye=.32,
        style='warmind_open_ladder', front=2.4, floor=13.3,
        donor='sight_base', removed=[],
        rim=['sight_rail_-1', 'sight_rail_1', 'sight_top_bridge'],
        notes='Original inclined open ladder rails, hinges and top bridge, not a reflex tube. A low connected aiming pin sits inside the ladder. The 0.32m eye is ahead of the transverse silver disc so it cannot mask the real ladder. Copper-magenta cells, Warmind mark, hoses and tubular stock remain exact.'),
    'the_recluse': dict(center=[8, 13.85, 7.54], eye=.48,
        style='veist_tall_octagonal_reflex', front=7.4, floor=13.175,
        selfOccluders=['sight/foot-7.47', 'sight/foot-8.37', 'optic/crown'],
        donor='sight/hoop-6', removed=[],
        rim=['sight/hoop-' + str(i) for i in range(8)],
        notes='Tall white octagonal open hoop over the complete white VEIST hood and red charge window; add a narrow connected pin within the hoop. Preserve hood ramps, burgundy power rail and bird stock. Use the W123 full assembly so the four seated magazine pieces occur once.'),
}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def rotate(v, axis, degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    x, y, z = v
    if axis == 'x':
        return [x, c*y-s*z, s*y+c*z]
    if axis == 'y':
        return [c*x+s*z, y, -s*x+c*z]
    return [c*x-s*y, s*x+c*y, z]


def local_point(element, point):
    """Inverse native Rz Ry Rx, or legacy rotation followed by rescale."""
    r = element.get('rotation', {})
    origin = r.get('origin', [0, 0, 0])
    v = [a-b for a, b in zip(point, origin)]
    angles = {a: r.get(a, 0) for a in 'xyz'}
    if 'axis' in r:
        angles[r['axis']] = r['angle']
    for axis in 'zyx':
        v = rotate(v, axis, -angles[axis])
    if r.get('rescale'):
        factor = abs(math.cos(math.radians(r['angle'])))
        v = [n if a == r['axis'] else n*factor for a, n in zip('xyz', v)]
    return [a+b for a, b in zip(v, origin)]


def world_point(element, point):
    r = element.get('rotation', {})
    origin = r.get('origin', [0, 0, 0])
    v = [a-b for a, b in zip(point, origin)]
    if r.get('rescale'):
        factor = abs(math.cos(math.radians(r['angle'])))
        v = [n if a == r['axis'] else n/factor for a, n in zip('xyz', v)]
    angles = {a: r.get(a, 0) for a in 'xyz'}
    if 'axis' in r:
        angles[r['axis']] = r['angle']
    for axis in 'xyz':
        v = rotate(v, axis, angles[axis])
    return [a+b for a, b in zip(v, origin)]


def segment_entry(element, start, end):
    """Exact solid cuboid intersection, also counting opaque zero-depth cards."""
    start, end = local_point(element, start), local_point(element, end)
    t0, t1 = 0., 1.
    for lo, hi, a, b in zip(element['from'], element['to'], start, end):
        delta = b-a
        if abs(delta) < 1e-12:
            if a < lo-1e-9 or a > hi+1e-9:
                return None
        else:
            near, far = sorted(((lo-a)/delta, (hi-a)/delta))
            t0, t1 = max(t0, near), min(t1, far)
            if t0 > t1+1e-10:
                return None
    return t0


def eye(row):
    x, y, z = row['sightCenter']
    return [x, y, z + row['eyeToSightMeters']*16/row['scale']]


def aperture_rays(row):
    """A 0.20 x 0.16 model-unit window, not a tiny center-ray clearance.

    Cast from the actual eye, through the original optic to beyond the muzzle.
    Lower margin leaves room for the deliberately visible aiming pin.
    """
    x, y, z = row['sightCenter']
    start = eye(row)
    factor = (start[2]+40)/(start[2]-z)
    for dx, dy in itertools.product([i*.025 for i in range(-4, 5)],
                                   [-.06, -.04, -.02, 0, .025, .05, .075, .1]):
        yield start, [x+dx*factor, y+dy*factor, -40]


def blockers(model, row):
    return sorted({e['name'] for a, b in aperture_rays(row)
                   for e in model['elements'] if segment_entry(e, a, b) is not None})


def rim_visibility(model, row):
    """Prove the actual hardware can be seen, not merely its empty central ray.

    A rim piece may hide behind another piece of this SAME optic. Any non-optic
    foreground (stock, receiver, cloth, rear disc) fails the test. The target is
    the center of each named original rim bar (also valid for inclined rails).
    """
    original = {e['name']: e for e in read(row['source'])['elements']}
    result = {}
    for name in row['visibleSightNames']:
        e = original[name]
        target = world_point(e, [(a+b)/2 for a, b in zip(e['from'], e['to'])])
        hits = [(t, p['name']) for p in model['elements']
                if (t := segment_entry(p, eye(row), target)) is not None]
        first = min(hits, default=(math.inf, 'missing_rim'))[1]
        result[name] = first
    return result


def cropped_piece(donor, name, lo, hi):
    """Crop the donor faces in its local frame; preserve UV density/rotation."""
    e = copy.deepcopy(donor)
    e.update(name='w153_'+name, **{'from': lo, 'to': hi})
    axes = dict(north=(0, 1, True, True), south=(0, 1, False, True),
                east=(2, 1, True, True), west=(2, 1, False, True),
                up=(0, 2, False, False), down=(0, 2, False, True))
    for face, data in e['faces'].items():
        ua, va, fu, fv = axes[face]
        ranges = []
        for axis, flip in ((ua, fu), (va, fv)):
            length = donor['to'][axis]-donor['from'][axis]
            a, b = (lo[axis]-donor['from'][axis])/length, (hi[axis]-donor['from'][axis])/length
            ranges.append((1-b, 1-a) if flip else (a, b))
        u, v, u1, v1 = data['uv']
        data['uv'] = [round(u+(u1-u)*ranges[0][0], 9), round(v+(v1-v)*ranges[1][0], 9),
                      round(u+(u1-u)*ranges[0][1], 9), round(v+(v1-v)*ranges[1][1], 9)]
    return e


def groove(donor):
    """Subtract a small conservative local box around the raised peep channel.

    Long Arm's cylinders rotate only about Z. Inverse-map the 0.28-wide top
    groove, then bound it in that donor's XY frame. This slightly overcuts the
    hidden inner corner of rotated wrap solids, never alters exterior paint.
    """
    corners = [local_point(donor, [x, y, donor['from'][2]])
               for x, y in itertools.product((7.86, 8.14), (11.205, 11.7))]
    a, b = donor['from'], donor['to']
    lo = [max(a[i], min(p[i] for p in corners)) for i in range(2)]
    hi = [min(b[i], max(p[i] for p in corners)) for i in range(2)]
    if any(lo[i] >= hi[i]-1e-8 for i in range(2)):
        return None
    boxes = [([a[0], a[1], a[2]], [lo[0], b[1], b[2]]),
             ([hi[0], a[1], a[2]], [b[0], b[1], b[2]]),
             ([lo[0], a[1], a[2]], [hi[0], lo[1], b[2]]),
             ([lo[0], hi[1], a[2]], [hi[0], b[1], b[2]])]
    return [cropped_piece(donor, donor['name']+'_groove_'+str(i), low, high)
            for i, (low, high) in enumerate(boxes)
            if all(high[j]-low[j] > 1e-8 for j in range(3))]


def aiming_pin(cfg, by_name):
    x, y, z = cfg['center']
    front = cfg['front']
    # A consistent .08 apparent gap, adjusted for each actual eye relief and pin
    # depth. The real tip is visible below center and above the original sill.
    gap = .08*(1+(z-front)/(cfg['eye']*16/.9))
    top, split = round(y-gap, 7), round(y-gap-.035, 7)
    if split <= cfg['floor']:
        raise ValueError('Aiming pin must seat above the original optic floor')
    stem = dict(name='w153_aim_stem', **{'from': [7.972, cfg['floor'], front-.045],
                'to': [8.028, split, front+.045]},
                faces=copy.deepcopy(by_name[cfg['donor']]['faces']))
    tip = dict(name='w153_aim_tip', **{'from': [7.976, split, front-.047],
               'to': [8.024, top, front+.047]},
               faces={f: dict(texture='#sight', uv=[4.25, .25, 4.75, .75]) for f in FACES})
    return [stem, tip], [x, top, front]


def make_body(id, cfg):
    source = ASSETS / f'models/weapon_surface_w123/{id}.json'
    original = read(source)
    by_name = {e['name']: e for e in original['elements']}
    if len(by_name) != len(original['elements']):
        raise ValueError('Duplicate source element names: '+id)
    model = copy.deepcopy(original)
    model.pop('display', None)
    removed = list(cfg['removed'])
    replacements, mapping = [], {}
    if id == 'long_arm':
        for e in original['elements']:
            if e['name'].startswith(('wrapped_sight_', 'sight_front_')):
                pieces = groove(e)
                if pieces is not None:
                    removed.append(e['name'])
                    replacements.extend(pieces)
                    mapping[e['name']] = [p['name'] for p in pieces]
    if id == 'bug_out_bag':
        # The tilted ramp masks the lower field and the two sides of the rim.
        # Trim only its upper .185 in local Y; retain width, depth and tilt.
        ramp = by_name['optic_rear_ramp']
        a, b = ramp['from'], ramp['to']
        pieces = [cropped_piece(ramp, 'ramp_lower', a, [b[0], 13.60, b[2]])]
        removed.append(ramp['name'])
        replacements.extend(pieces)
        mapping[ramp['name']] = [p['name'] for p in pieces]
    if not set(removed) <= by_name.keys():
        raise ValueError('Unknown removal: '+id)
    model['elements'] = [e for e in model['elements'] if e['name'] not in removed]
    model['elements'].extend(replacements)
    pins, tip = aiming_pin(cfg, by_name)
    model['elements'].extend(pins)
    model['textures']['sight'] = 'destiny:item/weapon/w148/sights'
    x, y, z = cfg['center']
    row = dict(id=id, family='scout_rifle' if id in tuple(SPECS)[:3] else 'submachine_gun',
        body=f'weapon_sight_w153/{id}_body', sightCenter=list(cfg['center']),
        forwardPoint=[x, y, round(z-2, 6)], eyeSide='+Z', plane='XY', scale=.9,
        eyeToSightMeters=cfg['eye'], elementCount=len(model['elements']),
        source=source.as_posix(), sourceSha256=sha((ROOT/source).read_bytes()),
        sourceElementCount=len(original['elements']), removedSightNames=removed,
        addedSightNames=[e['name'] for e in model['elements'] if e['name'].startswith('w153_')],
        style=cfg['style'], aimingTip=tip, aimingTipName='w153_aim_tip',
        reticle=dict(kind='connected physical pale pin', apparentTipGap=.08,
                     exactOriginalReticle=False, texture='destiny:item/weapon/w148/sights'),
        clearApertureBounds=[[-.1, -.06], [.1, .1]],
        visibleSightNames=cfg['rim'], replacedSightPieces=mapping,
        assemblyElementCount=len(model['elements']), companionElementCount=0,
        assemblyWithSpareMagazineCount=len(model['elements']),
        assemblyPolicy='Full static ADS assembly includes its seated magazine once; no companion or extra seated magazine wrapper. Reload/HIP/third-person retain their existing resources.',
        sightTextureSha256=sha((ROOT/SIGHT_TEXTURE).read_bytes()), nativeChecks='pending master')
    if len(model['elements']) > 1000:
        raise ValueError('Assembled emitted element budget: '+id)
    blocked = blockers(model, row)
    if blocked:
        raise ValueError(f'{id}: usable aperture blocked by {blocked}')
    visible = rim_visibility(model, row)
    optic_names = set(cfg['rim']) | set(cfg.get('selfOccluders', [])) | {e['name'] for e in replacements}
    if any(hit not in optic_names for hit in visible.values()):
        raise ValueError(f'{id}: optic hidden by foreground {visible}')
    minimum_fraction = .6 if id in ('bug_out_bag', 'the_recluse') else .75
    if sum(hit in cfg['rim'] for hit in visible.values()) < len(cfg['rim'])*minimum_fraction:
        raise ValueError(f'{id}: insufficient original rim visible: {visible}')
    row['rimVisibility'] = visible
    row['allowedRimSelfOccluders'] = sorted(optic_names-set(cfg['rim']))
    row['reference'] = reference(id, cfg, original)
    return model, row


def reference(id, cfg, original):
    record = next(r for r in read('art/weapons/w31/references.json') if r['id'] == id)
    photo = Path(f'/tmp/destiny-weapons-w31/references/{id}.jpg')
    prior = Path(f'art/weapons/w123/{id}')
    manifest = read(prior/'manifest.json')
    raw = manifest.get('raw_input_sha256', {})
    photo_hash = raw.get(str(photo), manifest.get('source', {}).get('reference_sha256'))
    if photo_hash != record['sha256'] or sha(photo.read_bytes()) != photo_hash:
        raise ValueError('Default photo provenance mismatch: '+id)
    # Bind all original textures, plus the original canonical model and split
    # resources. They are read-only inputs; no texture or reload resource emitted.
    inputs = {ASSETS/f'textures/{v.split(":", 1)[1]}.png'
              for v in original['textures'].values() if not v.startswith('#')}
    inputs.update((ASSETS/'models/weapon_surface_w123').glob(id+'*.json'))
    family = 'scout_rifle' if id in tuple(SPECS)[:3] else 'submachine_gun'
    canonical = ASSETS/f'models/weapon/{family}/{id}.json'
    if (ROOT/canonical).is_file():
        inputs.add(canonical)
    inputs.update((ASSETS/'models').glob(f'weapon_reload_w*/{id}*.json'))
    return dict(photo=str(photo), photoSha256=photo_hash, url=record['screenshot'],
        bungieHash=record['bungie_hash'], notes=cfg['notes'],
        limitation='Actual default three-quarter photo opened with view_image. Hidden rear hardware follows W123 design/rip study. Pale pin is an ADS visibility adaptation, not a recovered Bungie reticle or shader.',
        provenance={str(prior/p): sha((ROOT/prior/p).read_bytes())
                    for p in ('design.json', 'manifest.json', 'review.md')},
        priorRipSha256={p: h for p, h in raw.items() if p.lower().endswith(('.blend', '.fbx'))}
            or manifest.get('source', {}).get('source_files', {}),
        preservedInputSha256={str(p): sha((ROOT/p).read_bytes()) for p in sorted(inputs)})


def review(rows):
    lines = ['# W153 scouts / SMG ADS-only physical sights', '',
        'Seven full static assemblies derived from the actual W123 JSON and its design, manifest and review provenance. All seven default reference photographs were opened with view_image. The Ace / Izanagi study informed real openings and retained face UV; no foreign optic was pasted onto the batch.', '',
        'Only W153 bodies, this manifest/review and the owned generator/test change. No canonical texture/model, HIP, third-person, reload, shared generator, Java, wrapper or dependency is written. Full W123 inputs already contain the seated magazine; there is no companion. In particular Recluse uses its 66-element full model, not its 62-element detached body plus a duplicated magazine.', '',
        '| Weapon | Source / ADS emitted cubes | Eye relief | Original optic / ADS change |',
        '|---|---:|---:|---|']
    for row in rows:
        lines.append(f"| {row['id']} | {row['sourceElementCount']} / {row['elementCount']} | {row['eyeToSightMeters']:.2f} m | {row['reference']['notes']} |")
    lines += ['',
        'Every retained original element record, including rotation and every face UV, is unchanged. Patron and Aisha lose only the two fully opaque glass slabs; Bug-Out Bag loses its opaque lens and replaces the tilted rear ramp with the same cuboid cropped 0.185 units lower in local Y. The ramp width, depth, position, tilt and UV density remain; its lower face still naturally masks three lower rim samples, while the top and both sides are visible. Their existing hollow shells, end rims and mounts remain. No transparency assumption excuses a solid glass slab.', '',
        'Long Arm retains its four original raised peep bars at [8,11.33,3.795]. The filled wrapped tube directly behind them originally masks the lower field. Only intersecting wrapped_sight / sight_front cuboids are replaced by a shallow top groove through x=7.86..8.14, y>=11.205. Each rotated donor is split in its own frame around a conservative bound of that groove; this can overcut an inner corner of the concealed channel. Donor rotations, face materials and planar UV density are retained by cropping. The lower braided cylinder and side wrap survive; no stock/receiver is cut and no optic is deleted for anchor convenience.', '',
        'Each sight gets one narrow connected pin using its own metal face material and an existing W148 pale texture patch at the tip. Antiope extends its actual front post to align with the higher rear peep; the others seat within their own aperture. The apparent tip top is 0.08 model units below aim center at the declared eye relief, adjusted for perspective and depth. This is a readable physical aiming guide, not a claim to recreate the original game shader/reticle.', '',
        'Anchors are on the actual source apertures with +Z eye side and -Z forward axis. Eye relief varies deliberately: IKELOS at 0.32m seats ahead of its large transverse disc; Bug-Out Bag at 0.32m avoids cloth foreground. No source stock is removed. Validation casts a 9x8 perspective ray bundle across a 0.20x0.16 aperture from the actual eye through and beyond the muzzle, plus direct sight lines to every original rim bar. A clear center ray alone cannot pass: any stock, receiver, cloth or disc hiding those rim samples fails. The lower peep floor on Long Arm, peep base on Antiope and lower hoop/feet on Recluse can hide behind their own optic mounting structure; these explicitly named self-occluders cannot excuse other foreground. At least three quarters of rim samples must directly show original rim hardware (five eighths for Bug-Out Bag and Recluse, whose lower rim is seated behind its own ramp/hood). These are geometric offline checks, not a native view or parser proof.', '',
        'All counts include every simultaneously emitted cuboid, including the seated magazine once; there are zero triangle adapters and every assembly is below 1,000. generate() returns only Path-to-bytes outputs deterministically, including this review; --verify compares bytes without writing. Targeted standard-library tests exercise schema, ownership, full assembly/magazine preservation, UV and source provenance, nonwriting verification, usable aperture, actual rim and aiming-tip visibility, and foreground-occlusion mutations.', '',
        'Offline visual inspection: a seven-panel CPU raycast used the actual W153 cuboids and source face textures, from each declared eye position, at a clearly labeled 24-degree inspection crop. The silver tube, black box, small peep over braided wrap, ivory HAKKE peep, short round reflex, inclined ladder and white VEIST hoop are visibly distinct; all show their pale aiming tip. Long Arm keeps its gold wrapped lower foreground, and Bug-Out Bag keeps the lower black ramp beneath its open upper field. No stock covers the actual optic. This in-memory review produced no extra worktree artifact and does not establish native FOV, clipping or resource parsing.', '',
        'Targeted test suite: 22 tests via `rtk proxy python3 -B scripts/qa/test_sight_bodies_w153_scouts_smg.py`. Generator verification: `rtk proxy python3 -B scripts/generate_sight_bodies_w153_scouts_smg.py --verify`.', '',
        'Master followups: shared 18 ADS21frame wrappers and Java admission; actual 26.3 native parser and resource load; all seven settled ADS views showing the recognizable real optic and visible aiming pin; verify native near clipping with the selected per-weapon eye relief; HIP/third/reload seating and transition checks (especially Recluse: do not add a second seated magazine); representative 10–20 displayed weapons. No Gradle, CU/Vision, DCC, game/server, native parser, audio or performance testing was run here. Integration into main was not performed.', '']
    return '\n'.join(lines).encode()


def generate():
    outputs, rows = {}, []
    for id, cfg in SPECS.items():
        model, row = make_body(id, cfg)
        outputs[ASSETS/f"models/{row['body']}.json"] = encode(model)
        rows.append(row)
    outputs[MANIFEST] = encode(dict(weapons=rows))
    outputs[REVIEW] = review(rows)
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    outputs = generate()
    for path, data in outputs.items():
        target = ROOT/path
        if args.verify:
            if not target.is_file() or target.read_bytes() != data:
                parser.exit(1, f'W153 differs: {path}\n')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print('W153 scouts/SMG: 7 weapons / 9 outputs '+('verified' if args.verify else 'generated'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
