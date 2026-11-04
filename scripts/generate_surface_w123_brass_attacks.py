#!/usr/bin/env python3
"""W143 Brass Attacks: authored semantic solids and opaque, independent face UVs.

Only this weapon's owned products are written. FBX is inert reference data; the
read-only W123 Beloved parser/rasterizer never launches a DCC or executes source.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import uuid

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/brass_attacks/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sidearm/brass_attacks.json'
MODEL = ASSET + 'models/weapon_surface_w123/brass_attacks.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/brass_attacks.png'
BB = 'art/blockbench/weapons/w30/brass_attacks.bbmodel'
REFS = 'art/weapons/w31/references.json'
RAW = Path('/tmp/destiny-weapons-w30/raw/brass_attacks/extracted/Brass Attacks')
PHOTO = Path('/tmp/destiny-weapons-w31/references/brass_attacks.jpg')
EDGE = 1024
H = runpy.run_path(str(ROOT / 'scripts/generate_surface_w123_beloved.py'))
FACES = H['FACES']
PALETTE = dict(ivory=[224,214,173], brass=[158,132,72], brass_light=[193,166,99],
               blue=[43,94,104], copper=[159,80,43], steel=[68,74,73],
               black=[42,46,45], rubber=[36,39,36], recess=[12,18,19])
BARREL_Y = 15.47


def encode(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    b = io.BytesIO()
    im.save(b, format='PNG')
    return b.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w143:brass_attacks:' + name))


def render_element(e):
    e = copy.deepcopy(e)
    if 'rotation' in e:
        r = e['rotation']
        e['rotation'] = dict(origin=r['origin'], **{r['axis']: r['angle']})
    return e


def vertices(e):
    return H['vertices'](render_element(e))


def source_meshes():
    """FBX local vertex coordinates match the W30 accepted meter-space bounds.

    Exporter's -90deg/100 object records describe FBX units, not an additional
    native weapon transform. Validate the accepted frame before using arrays.
    """
    meta = json.loads((ROOT / BB).read_bytes())['destiny_w30']
    path = RAW / 'Brass Attacks.fbx'
    assert sha(path.read_bytes()) == meta['source_files']['Brass Attacks/Brass Attacks.fbx']
    roots = H['parse_fbx'](path)
    objects = next(n[2] for n in roots if n[0] == 'Objects')
    meshes = []
    for node in objects:
        name = node[1][1].split('\0')[0] if len(node[1]) > 1 else ''
        if node[0] != 'Geometry' or name not in meta['source_objects']:
            continue
        cs = {c[0]: c for c in node[2]}
        raw = np.array(cs['Vertices'][1][0]).reshape(-1, 3)
        fs = []; face = []
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i >= 0 else -i - 1)
            if i < 0:
                assert len(face) == 3, 'Accepted FBX must be triangulated'
                fs.append(face); face = []
        layer = next(c for c in node[2] if c[0] == 'LayerElementUV' and c[1][0] == 0)
        vals = {c[0]: c[1][0] for c in layer[2]}
        assert vals['MappingInformationType'] == 'ByPolygonVertex'
        assert vals['ReferenceInformationType'] == 'IndexToDirect'
        uv = np.array(vals['UV']).reshape(-1, 2)[np.array(vals['UVIndex'])].reshape(-1, 3, 2)
        uv[:, :, 1] = 1 - uv[:, :, 1]
        meshes.append(dict(name=name, raw=raw,
                           vertices=raw[:, [0, 2, 1]] * meta['scale'] + meta['anchor'],
                           faces=np.array(fs), uv=uv,
                           material='Frame' if '.00.' in name else 'Mag'))
    assert sorted(m['name'] for m in meshes) == sorted(meta['source_objects'])
    p = np.concatenate([m['vertices'] for m in meshes])
    r = np.concatenate([m['raw'] for m in meshes])
    np.testing.assert_allclose([r.min(0), r.max(0)], meta['source_bounds'], atol=1e-7, rtol=0)
    np.testing.assert_allclose([p.min(0), p.max(0)], meta['model_bounds'], atol=3e-6, rtol=0)
    ref = next(r for r in json.loads((ROOT / REFS).read_bytes()) if r['id'] == 'brass_attacks')
    assert sha(PHOTO.read_bytes()) == ref['sha256']
    return meshes, meta


def make_design(meta, meshes):
    parts = []

    def box(group, name, c, size, mat, motif='plain', turn=None):
        c = np.array(c, float); s = np.array(size, float)
        e = dict(name=name, **{'from': (c-s/2).round(6).tolist(), 'to': (c+s/2).round(6).tolist()})
        if turn:
            e['rotation'] = dict(origin=c.round(6).tolist(), axis=turn[0], angle=turn[1])
        parts.append(dict(group=group, material=mat, motif=motif,
                          kind='opaque_solid_cuboid', geometry=e))

    def beam(group, name, a, b, width, depth, mat, motif='plain'):
        a = np.array(a, float); b = np.array(b, float); v = b-a
        box(group, name, (a+b)/2, [width, np.linalg.norm(v), depth], mat, motif,
            ('x', round(math.degrees(math.atan2(v[2], v[1])), 6)))

    def ring(group, name, z0, z1, radius, thickness, mat, motif='plain'):
        # Eight thick tangent solids form a real octagonal aperture. Adjacent
        # corners overlap inside the wall; the central hole remains unobstructed.
        rc = radius-thickness/2
        for i in range(8):
            angle = i*45; rad = math.radians(angle)
            box(group, f'{name}_{i}', [8-rc*math.sin(rad), BARREL_Y+rc*math.cos(rad), (z0+z1)/2],
                [2*radius*math.tan(math.pi/8)+.008, thickness, z1-z0], mat, motif, ('z', angle))

    # Hollow only where a barrel is physically hollow; the action below is filled.
    ring('barrel', 'deep_bore_wall', -3.98, -2.15, .59, .22, 'black', 'bore')
    box('barrel', 'bore_backstop', [8, BARREL_Y, -2.10], [.78, .78, .12], 'recess')
    box('barrel', 'barrel_core', [8, BARREL_Y, 2.35], [1.00, 1.00, 8.90], 'black', 'spiral')
    for side in (-1, 1):
        box('barrel', f'barrel_chamfer_{side}', [8+side*.47, BARREL_Y, 2.35], [.25, .75, 8.90],
            'black', 'spiral', ('z', side*45))
    ring('muzzle', 'copper_muzzle', -4.123815, -3.84, .71, .22, 'copper', 'rim')
    ring('shroud', 'ivory_front_collar', -3.78, -3.33, 1.00, .29, 'ivory', 'enamel')
    # Long continuous upper/lower shroud volumes leave an actual longitudinal
    # channel exposing the dark, UV-fluted barrel rather than alpha-cut side plates.
    box('shroud', 'ivory_upper', [8, 15.97, 1.71], [1.64, .57, 10.16], 'ivory', 'enamel')
    box('shroud', 'ivory_lower', [8, 14.77, 1.71], [1.55, .32, 10.16], 'ivory', 'enamel')
    for side in (-1, 1):
        box('shroud', f'upper_shoulder_{side}', [8+side*.80, 15.83, 1.71], [.32, .43, 10.16],
            'ivory', 'enamel', ('z', side*35))
        box('shroud', f'lower_shoulder_{side}', [8+side*.75, 14.87, 1.71], [.30, .28, 10.16],
            'ivory', 'enamel', ('z', -side*35))
    box('shroud', 'slot_rear_bridge', [8, 15.34, 6.46], [1.84, 1.06, .66], 'ivory', 'enamel')
    for side in (-1, 1):
        box('shroud', f'slot_rear_chamfer_{side}', [8+side*.79, 15.32, 6.10], [.23,.62,.30],
            'ivory', 'enamel', ('x', -25))
    # Rear shroud rounds into a substantial action rather than a thin casing.
    ring('breech', 'rear_brass_collar', 6.79, 7.13, 1.00, .25, 'brass', 'grooves')
    box('breech', 'rear_breech_core', [8, 15.43, 8.19], [1.49, 1.43, 2.14], 'black', 'breech')
    for side in (-1, 1):
        box('breech', f'breech_shoulder_{side}', [8+side*.63, 15.86, 8.19], [.46, .46, 2.14],
            'steel', 'grooves', ('z', side*45))
    ring('breech', 'rear_band', 8.87, 9.22, .98, .27, 'brass_light', 'grooves')
    box('breech', 'rear_cap', [8, 15.45, 9.32], [1.41, 1.44, .20], 'steel', 'rear')
    # The tall double ledge is a characteristic stepped rail, not a modern optic.
    box('rail', 'front_rail_web', [8, 16.50, -1.76], [.70, .56, 4.55], 'brass', 'rail')
    box('rail', 'rear_rail_web', [8, 16.54, 4.89], [.70, .65, 8.77], 'brass', 'rail')
    for y, name, z, length in ((16.78, 'front', -1.76, 4.55), (16.90, 'rear', 4.89, 8.77)):
        box('rail', name+'_crown', [8, y, z], [.96, .17, length], 'brass_light', 'rail_edge')
        box('rail', name+'_foot', [8, 16.24, z], [.96, .14, length], 'brass_light', 'rail_edge')
    # Wide continuous receiver and rear shoulder, with silhouette-changing bevels.
    box('receiver', 'receiver_core', [8, 13.79, 5.19], [1.60, 1.69, 6.55], 'black', 'receiver')
    box('receiver', 'rear_shoulder', [8, 13.95, 8.15], [1.53, 1.38, 2.47], 'black', 'receiver')
    for side in (-1, 1):
        box('receiver', f'receiver_bevel_{side}', [8+side*.68, 14.51, 5.22], [.34, .34, 6.51],
            'steel', 'receiver', ('z', side*45))
    # Three true keyhole scallops in the brass underlug. Broad upper slab plus
    # four solid webs and six feet: the voids pass through the entire weapon width.
    box('underlug', 'underlug_upper', [8, 14.13, -1.06], [1.80, .81, 6.05], 'brass_light', 'patina')
    holes = [-2.63, -1.08, .47]
    intervals = [(-4.02, holes[0]-.37), (holes[0]+.37, holes[1]-.37),
                 (holes[1]+.37, holes[2]-.37), (holes[2]+.37, 1.98)]
    for i, (a, b) in enumerate(intervals):
        bottom = 12.86 - (a+4.02)*.085
        box('underlug', f'underlug_web_{i}', [8, (bottom+13.75)/2, (a+b)/2],
            [1.80, 13.75-bottom, b-a], 'brass_light', 'patina')
    for i, z in enumerate(holes):
        bottom = 12.86-(z+4.02)*.085
        for side in (-1, 1):
            # Angled shoulders round the upper edge of each aperture.
            box('underlug', f'keyhole_arch_{i}_{side}', [8, 13.62, z+side*.28],
                [1.80, .23, .34], 'brass_light', 'patina', ('x', side*45))
            box('underlug', f'keyhole_lower_round_{i}_{side}', [8, 13.04, z+side*.30],
                [1.80, .16, .25], 'brass_light', 'patina', ('x', -side*45))
            box('underlug', f'keyhole_foot_{i}_{side}', [8, (bottom+13.02)/2, z+side*.27],
                [1.80, 13.02-bottom, .21], 'brass_light', 'patina')
    for side in (-1, 1):
        box('underlug', f'blue_upper_trim_{side}', [8+side*.91, 14.60, -1.06], [.14, .13, 6.05], 'blue', 'trim')
        box('underlug', f'brass_ledge_{side}', [8+side*.88, 14.41, -1.06], [.20, .15, 6.05], 'brass', 'trim')
    box('underlug', 'front_nose', [8, 13.74, -4.015], [1.55, 1.35, .16], 'blue', 'nose')
    # Original swept black grip: one filled main core and joined shoulder/heel.
    # Side panels are raised over the core, never used as the body silhouette.
    beam('grip', 'grip_core', [8, 7.24, 9.36], [8, 12.80, 7.44], 1.45, 2.60, 'black', 'grip_edge')
    beam('grip', 'grip_wrist', [8, 12.40, 7.58], [8, 13.77, 7.85], 1.48, 2.19, 'black', 'grip_edge')
    for side in (-1, 1):
        beam('grip', f'grip_panel_{side}', [8+side*.735, 7.33, 9.35], [8+side*.735, 12.70, 7.49],
             .12, 2.14, 'rubber', 'checkering')
    beam('grip', 'frontstrap', [8, 7.20, 8.09], [8, 12.35, 6.32], 1.30, .26, 'black', 'frontstrap')
    beam('grip', 'backstrap', [8, 7.50, 10.57], [8, 12.19, 8.95], 1.32, .30, 'black', 'grip_edge')
    beam('grip', 'upper_backstrap', [8, 12.18, 8.95], [8, 13.96, 9.22], 1.31, .41, 'black', 'grip_edge')
    box('grip', 'heel', [8, 6.89, 9.43], [1.61, .41, 2.72], 'black', 'heel', ('x', -19.05))
    box('magazine', 'magazine_base', [8, 6.62, 9.34], [1.50, .29, 2.63], 'black', 'heel', ('x', -19.05))
    # Brass Attacks has an exposed trigger, not a closed hoop. Keep this bay
    # physically empty; inventing an enclosing guard would change its identity.
    beam('trigger', 'trigger_root', [8, 13.00, 4.43], [8, 12.06, 4.53], .30, .35, 'steel')
    beam('trigger', 'trigger_curve', [8, 12.06, 4.53], [8, 11.40, 4.18], .30, .35, 'black')
    beam('trigger', 'trigger_tip', [8, 11.40, 4.18], [8, 11.28, 3.96], .30, .34, 'steel')
    for side in (-1, 1):
        box('controls', f'slide_lever_{side}', [8+side*.84, 14.05, 4.82], [.14, .16, 1.74], 'steel', 'lever', ('x', 8))
        box('controls', f'copper_control_{side}', [8+side*.86, 13.27, 6.55], [.14, .44, .44], 'copper', 'bolt', ('x', 45))
    inputs = [BASE, BB, REFS, ASSET+'textures/item/weapon/w30/brass_attacks.png',
              'scripts/generate_surface_w123_brass_attacks.py',
              'scripts/generate_surface_w123_beloved.py']
    raw = [PHOTO, RAW/'Brass Attacks.fbx', RAW/'BAFrame_Diffuse.png', RAW/'BAMag_Diffuse.png']
    counts = {m['name']: len(m['faces']) for m in meshes}
    return dict(id='brass_attacks', revision='W143', source=meta, parts=parts,
                source_counts=dict(accepted_fbx_triangles=counts, actual_total=sum(counts.values()),
                                   recorded_w30_total=meta['source_triangles'], difference=sum(counts.values())-meta['source_triangles']),
                coordinate_policy=dict(mapping='[raw.X, raw.Z, raw.Y]*scale+anchor', anchor=meta['anchor'],
                                       scale=meta['scale'], muzzle='-Z', display='canonical exact', full_only=True),
                identity=['pale cylindrical cutaway shroud and dark spiral barrel', 'copper open muzzle',
                          'blue-edged brass underlug with three physical keyholes', 'stepped brass rail',
                          'swept full black checkered grip and exposed trigger bay'],
                geometry_rationale=dict(rings='real bore and rounded collar cross-sections',
                                        shroud='continuous thick solids around exposed barrel channel',
                                        underlug='arch shoulders, webs and feet preserve three through scallops',
                                        grip='filled swept core and raised rubber panels',
                                        uv='patina, checkering, screws, seams and barrel spiral stay on faces'),
                limitations=['Octagonal collars and segmented grip approximate the original smooth contours.',
                             'Spiral barrel flutes, fine screws and worn brass are opaque face artwork; no helical machining geometry.',
                             'The exposed trigger bay has no invented closed guard; the three underlug keyholes are through geometry.',
                             'Default-photo material reconstruction is matte RGBA, not recovered PBR or native acceptance.',
                             'Full-only asset: existing ADS, twohand and generic reload require central native review.'],
                input_sha256={p: sha((ROOT/p).read_bytes()) for p in inputs},
                raw_input_sha256={str(p): sha(p.read_bytes()) for p in raw})


def world_points(e, face, w, h):
    p = vertices(e)[list(FACES[face])]
    u, v = np.meshgrid((np.arange(w)+.5)/w, (np.arange(h)+.5)/h)
    q = ((1-u)[:, :, None]*(1-v)[:, :, None]*p[0] + u[:, :, None]*(1-v)[:, :, None]*p[1]
         + u[:, :, None]*v[:, :, None]*p[2] + (1-u)[:, :, None]*v[:, :, None]*p[3])
    return u, v, q


def surface_noise(a, b):
    """Continuous deterministic value noise for irregular metal wear, not geometry."""
    ia=np.floor(a).astype(np.int64);ib=np.floor(b).astype(np.int64)
    u=a-ia;v=b-ib;u=u*u*(3-2*u);v=v*v*(3-2*v)
    def lattice(x,y):
        h=(x*374761393+y*668265263)&0xffffffff
        h=((h^(h>>13))*1274126177)&0xffffffff
        return ((h^(h>>16))&0xffffffff)/4294967295.
    return ((1-u)*(1-v)*lattice(ia,ib)+u*(1-v)*lattice(ia+1,ib)
            +(1-u)*v*lattice(ia,ib+1)+u*v*lattice(ia+1,ib+1))


def tile(spec, face, w, h):
    u, v, q = world_points(spec['geometry'], face, w, h)
    x, y, z = [q[:, :, i] for i in range(3)]
    mat, motif = spec['material'], spec['motif']
    rgb = np.broadcast_to(np.array(PALETTE[mat], float), (h, w, 3)).copy()
    # World-space continuous fields prevent random source-island discoloration.
    field = np.sin(z*4.3+np.sin(y*5.1)*1.6) * np.sin(y*7.2+x*4.1)
    fine = np.sin(z*47+y*31+np.sin(z*13)*2)*np.sin(y*63-x*17)
    rgb *= (1 + .018*field + .009*fine)[:, :, None]
    if mat in ('brass', 'brass_light'):
        weather = np.clip((field+.38*fine-.15)*.33, 0, .30)
        rgb = rgb*(1-weather[:, :, None])+np.array([64,70,49])*weather[:, :, None]
    if mat == 'ivory':
        wear = np.clip((field+.3*fine-.48)*.23, 0, .14)
        rgb = rgb*(1-wear[:, :, None])+np.array(PALETTE['brass'])*wear[:, :, None]
    edge = np.minimum.reduce([u*w, (1-u)*w, v*h, (1-v)*h])
    # Surface joins inside one semantic volume must not acquire false seams.
    if motif not in ('patina', 'enamel', 'receiver', 'spiral', 'grip_edge'):
        rgb[edge < .7] *= .75
        rgb[(edge >= .7) & (edge < 1.5)] *= 1.10
    if motif == 'patina':
        wear=(surface_noise(y*4,z*3)*.55+surface_noise(y*11,z*8)*.30
              +surface_noise(y*29,z*20)*.15)
        patina = np.clip((wear-.42)*2.1, 0, .68)
        rgb = rgb*(1-patina[:, :, None])+np.array([43,52,39])*patina[:, :, None]
    side = face in ('east', 'west')
    if motif == 'spiral':
        a = np.arctan2(x-8, y-BARREL_Y)
        wave = np.mod(z*.94+a*.83, 1)
        rgb[wave < .13] = [13,24,25]
        rgb[(wave >= .13) & (wave < .23)] = [66,82,79]
        rgb[(wave >= .23) & (wave < .28)] = [91,103,92]
    if motif in ('rim', 'grooves'):
        if motif == 'rim' and face == 'north':
            rgb *= (1+.10*np.cos(np.arctan2(x-8,y-BARREL_Y)*8))[:, :, None]
        if motif == 'grooves':
            rgb[np.mod(z*14, 1)<.17] *= .56
    if motif in ('rail', 'rail_edge'):
        if side:
            rgb[(y > 16.32) & (y < 16.39)] = PALETTE['blue']
            rgb[(y > 16.70) & (y < 16.74)] *= .6
        if motif == 'rail_edge':
            rgb[edge < 1.4] = PALETTE['blue']
    if motif == 'enamel' and side:
        rgb[(y < 14.84) | ((y > 15.67) & (y < 15.73))] = PALETTE['blue']
    if motif == 'receiver' and side:
        # The source's inset lever recess and grounded pivots, without invented text.
        recess = (z > 3.40) & (z < 6.40) & (y > 13.80) & (y < 14.48)
        rgb[recess] = [20,25,25]
        rgb[(z > 3.45) & (z < 6.35) & (y > 13.80) & (y < 13.86)] = [80,85,78]
    if motif == 'checkering' and side:
        # Use grip-local coordinates for aligned diamonds and correct screw layout.
        e = spec['geometry']; r = e['rotation']; o = np.array(r['origin'])
        local = (q-o) @ H['rotation']({r['axis']:r['angle']}) + o
        gy = local[:, :, 1]; gz = local[:, :, 2]
        a = np.mod((gy+gz)*8.2, 1); b = np.mod((gy-gz)*8.2, 1)
        rgb[(a<.17)|(b<.17)] *= .47
        rgb[((a>.20)&(a<.27))|((b>.20)&(b<.27))] *= 1.35
        for sy in (o[1]-2.10, o[1]+.25, o[1]+2.14):
            rr = np.hypot(gy-sy, gz-o[2])
            rgb[(rr>.115)&(rr<.17)] = PALETTE['black']
            rgb[rr<.115] = PALETTE['copper']
            rgb[(rr<.10)&(abs((gy-sy)*.30+(gz-o[2]))<.018)] = [52,35,25]
    if motif == 'frontstrap':
        rgb[(np.mod(y*8,1)<.23)&(y<10.1)] *= .57
    if motif == 'heel':
        rgb[np.mod(y*18,1)<.14] *= .6
    if motif in ('patina', 'rail') and side:
        # Only photographed fastener locations: two underlug and two rail pivots.
        points = [(-3.62,14.03), (1.47,14.04)] if motif == 'patina' else [(-.9,16.52),(7.54,16.60)]
        for zz, yy in points:
            rr = np.hypot(z-zz, y-yy)
            rgb[(rr>.10)&(rr<.16)] = [70,51,30]
            rgb[rr<.10] = PALETTE['copper']
    if motif == 'bolt' and side:
        rr = np.hypot(u-.5,v-.5)
        rgb[rr>.41] *= .65
        rgb[(abs(u-v)<.055)&(rr<.35)] = [59,35,24]
    if motif == 'nose' and face == 'north':
        rr = np.hypot((x-8)*.85, y-13.86)
        rgb[rr<.18] = PALETTE['copper']
        rgb[(abs(x-8)<.045)&(abs(y-13.86)<.13)] = [50,39,23]
    if motif == 'rear' and face == 'south':
        rgb[(abs(x-8)<.38)&(abs(y-BARREL_Y)<.49)] *= .55
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255).astype('uint8'), np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas = Image.new('RGBA', (EDGE, EDGE), (0,0,0,0)); requests = []
    for s in d['parts']:
        for f in FACES:
            p = vertices(s['geometry'])[list(FACES[f])]
            w = max(4, math.ceil(np.linalg.norm(p[1]-p[0])*24))
            h = max(4, math.ceil(np.linalg.norm(p[3]-p[0])*24))
            requests.append((h,w,s['geometry']['name'],f,s))
    requests.sort(key=lambda r: (-r[0],-r[1],r[2],r[3]))
    x = y = 2; row = 0; ledger = []; uvs = {}
    for h,w,name,f,s in requests:
        if x+w+2 > EDGE:
            x = 2; y += row+4; row = 0
        if y+h+2 > EDGE:
            raise ValueError('Atlas overflow: '+name)
        im = tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im), ((2,2),(2,2),(0,0)), mode='edge')), (x-2,y-2))
        uvs[(name,f)] = [v*16/EDGE for v in [x,y,x+w,y+h]]
        ledger.append(dict(element=name, face=f, pixels=[x,y,x+w,y+h]))
        x += w+4; row = max(row,h)
    es = []
    for s in d['parts']:
        e = copy.deepcopy(s['geometry'])
        e['faces'] = {f: dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES}
        es.append(e)
    d['atlas'] = dict(size=EDGE, gutter=2, texels_per_unit=24, used_height=y+row+2,
                      face_islands=len(ledger), islands=ledger)
    return atlas, dict(credit='W143 Brass Attacks / semantic solids / clean default-photo face UV',
                       textures={'0':'destiny:item/weapon/w123/brass_attacks',
                                 'particle':'destiny:item/weapon/w123/brass_attacks'},
                       elements=es, display=json.loads((ROOT/BASE).read_bytes())['display'])


def model_triangles(model, atlas):
    m = copy.deepcopy(model)
    m['elements'] = [render_element(e) for e in m['elements']]
    return H['model_triangles']({'full':m}, atlas)


def source_triangles(meshes):
    textures = {k: np.array(Image.open(RAW/('BA'+k+'_Diffuse.png')).convert('RGBA')) for k in ('Frame','Mag')}
    ts = []
    for m in meshes:
        for p,uv in zip(m['vertices'][m['faces']],m['uv']):
            n = np.cross(p[1]-p[0],p[2]-p[0]); n /= max(np.linalg.norm(n),1e-20)
            ts.append((p,uv,textures[m['material']],n))
    return ts


def inspection(d, model, atlas):
    es = []; groups = []
    for group in sorted({s['group'] for s in d['parts']}):
        names = {s['geometry']['name'] for s in d['parts'] if s['group']==group}; children=[]
        for e in model['elements']:
            if e['name'] not in names:
                continue
            b = copy.deepcopy(e); r = b.pop('rotation',None)
            b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
                     rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():
                f['texture']=0; f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b); children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid('group:'+group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),
                name='Brass Attacks W143 / editable semantic solids',resolution=dict(width=EDGE,height=EDGE),
                elements=es,outliner=groups,display=copy.deepcopy(model['display']),
                textures=[dict(name='brass_attacks.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,
                               uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())])


def comparison(d, meshes, atlas, model):
    w,h = 740,415
    sheet = Image.new('RGB',(2220,2225),'#202730'); draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):
        draw.text((x,y),s,fill='#e8ece7',font_size=size)
    label(20,12,'BRASS ATTACKS W143 / SEMANTIC SOLIDS + OPAQUE FACE UV',29)
    photo = Image.open(PHOTO).convert('RGB').crop((1080,205,1730,850))
    photo.thumbnail((650,470)); sheet.paste(photo,(20,60))
    lines=[f'{len(model["elements"])} opaque cubes / 0 triangle adapters / full-only',
           'Ivory cutaway shroud / dark spiral barrel / copper muzzle',
           'Blue-edged brass underlug / three true through keyholes',
           'Filled receiver and swept grip / open exposed-trigger bay',
           'Source frame, scale, anchor and canonical display retained',
           'Raw FBX: 20,296 triangles = W30 recorded count (difference 0)',
           'Matte default-photo paint; fine relief uses authored face UV',
           'CPU art comparison only / native and PBR acceptance pending']
    for i,s in enumerate(lines):label(720,80+i*47,s,23)
    raw=source_triangles(meshes); old=json.loads((ROOT/BASE).read_bytes())
    oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/brass_attacks.png'))
    ts=[raw,model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for col,s in enumerate(['ACCEPTED RIP / NEUTRAL DIFFUSE','DIRTY BASELINE / 244 CUBES',f'W143 / {len(model["elements"])} AUTHORED SOLIDS']):label(col*w+15,545,s)
    for row,(title,cam) in enumerate([('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.32,-.68]),('REAR OBLIQUE',[-1,.26,.62])]):
        extent=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,extent,(w,h),raw=col==0)
            sheet.paste(im,(col*w,580+row*h));label(col*w+15,590+row*h,title,17)
    new=ts[2]
    details=[('MUZZLE / REAL BORE',[.23,.10,-1],[[6.85,14.3,-4.2],[9.15,16.6,-2.7]]),
             ('UNDERLUG / THROUGH KEYHOLES',[1,.18,-.20],[[6.85,12.2,-4.2],[9.15,14.9,2.1]]),
             ('GRIP / FILLED VOLUME + CHECKERING',[-1,.12,.50],[[6.9,5.7,6.1],[9.1,14.0,10.95]])]
    for col,(title,cam,bounds) in enumerate(details):
        ps=np.array([[bounds[(mask>>a)&1][a] for a in range(3)] for mask in range(8)])
        im,_=H['render'](new,cam,H['frame'](ps,cam,w,355),(w,355))
        sheet.paste(im,(col*w,1855));label(col*w+15,1832,title,18)
    return png(sheet)


def review_text(d, counts):
    return f'''# Brass Attacks W143

{len(d['parts'])} authored opaque cuboids, zero triangle adapters, one assembled full model. Groups: {json.dumps(counts,sort_keys=True)}. The 1,000-element ceiling is a cap, not a target. Construction starts from continuous barrel/shroud, receiver and swept grip volumes, with geometry spent on collar cross-sections, three underlug keyholes, shoulder transitions and exposed trigger. No source-island transplant, voxel envelope or alpha silhouette body.

Reference: actual W31 Bungie/light.gg default photo (2121785039), opened before modeling. Preserve the pale cylindrical cutaway shroud, black spiral insert, copper bore lip, stepped brass rail, blue-edged brass underlug, three keyhole scallops, black swept checkered handle and exposed trigger bay. Brass Attacks has an exposed trigger rather than a closed hoop; its finger space remains physically empty. Copper screws, grip diamonds, panel seams, light enamel wear and aged brass use independent face UV, continuous material-space patterns and 2px extruded opaque gutters. No invented logo or text.

Accepted inert FBX meshes: Brass-Attacks.00.000 = 19,864 triangles, Brass-Attacks.01.000 = 432 triangles; total 20,296, equal to W30's recorded 20,296 (difference 0). Excluded reticle .02 remains excluded. Local XYZ arrays map to native [X,Z,Y] with the exact W30 scale {d['source']['scale']} and anchor {d['source']['anchor']}; bounds validate within 0.000003 native units. Source scripts, shader files and DCC sessions are never executed. Read-only helper APIs: Beloved binary FBX parser, cube projection and CPU rasterizer. Raw diffuse preview is neutral and has no default-dye/PBR claim.

Native item JSON retains canonical display verbatim. No registration, migration, ADS, twohand, reload, gameplay or audio files are edited; full-only model preserves the existing generic reload contract, with no new split-magazine requirement. Master owns downstream activation and central native review.

comparison.png contains the actual default-photo crop and equal-frame rows of accepted raw source, dirty-seeded 244-cube baseline and new solids in side/front/rear oblique views, plus bore/keyhole/grip closeups. inspection.bbmodel embeds the exact PNG and editable cubes in semantic groups for master review; generating it does not imply a Blockbench session was opened.

Limitations: {' '.join(d['limitations'])} Focused checks establish basic schema/positive dimensions, source frame/bounds, physical aperture rays, solid core occupancy, face UV opacity and determinism. They are practical regression checks, not exhaustive certification. Resource-pack/native parsing, lighting, representative first/third-person holding, ADS/twohand, generic reload and 10–20 simultaneous displays remain unverified here. No live DCC, ComputerUse, Vision, QA fixture, Gradle or dependency build was run. Native and PBR acceptance are not claimed.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes(); d=make_design(meta,meshes); atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    out={ART+'design.json':encode(d), MODEL:encode(model), TEXTURE:png(atlas),
         ART+'inspection.bbmodel':encode(inspection(d,model,atlas)), ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:
        out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    ps=np.concatenate([vertices(e) for e in model['elements']])
    assert 0 < len(model['elements']) <= 1000
    manifest=dict(id='brass_attacks',revision='W143',assembled_elements=len(model['elements']),
                  opaque_cuboids=len(model['elements']),triangle_adapter_elements=0,alpha_body_elements=0,
                  emitted_faces=len(model['elements'])*6,groups=counts,max_assembled_elements=1000,
                  texture_size=[EDGE,EDGE],actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],
                  source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],
                  source_counts=d['source_counts'],baseline_cube_count=len(json.loads((ROOT/BASE).read_bytes())['elements']),
                  canonical_display_exact=True,full_only=True,native_accepted=False,pbr_accepted=False,
                  input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
                  output_sha256={p:sha(b) for p,b in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    out=generate()
    for path,data in out.items():
        target=ROOT/path
        if args.verify:
            assert target.is_file() and target.read_bytes()==data,path
        else:
            target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    m=json.loads(out[ART+'manifest.json'])
    print('Brass Attacks W143', 'verified' if args.verify else 'generated',
          m['assembled_elements'],'opaque cuboids;',m['source_counts'])


if __name__=='__main__':
    main()
