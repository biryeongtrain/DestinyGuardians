#!/usr/bin/env python3
"""W126 Beloved: authored solid semantic volumes and face UVs, offline only.

Bundled Python + Pillow/numpy. Reads inert FBX/DDS reference data, never opens a
DCC or a game. The only writes are this feature's generated owned artifacts.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import uuid
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/beloved/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sniper_rifle/beloved.json'
RELOAD = ASSET + 'models/weapon_reload_w47/beloved'
MODEL = ASSET + 'models/weapon_surface_w123/beloved'
TEXTURE = ASSET + 'textures/item/weapon/w123/beloved.png'
RAW = Path('/tmp/destiny-weapons-w30/raw/beloved/extracted')
W31 = Path('/tmp/destiny-weapons-w31')
EDGE = 1024
FACES = {'north': (3, 2, 0, 1), 'south': (6, 7, 5, 4),
         'west': (2, 6, 4, 0), 'east': (7, 3, 1, 5),
         'up': (2, 3, 7, 6), 'down': (4, 5, 1, 0)}
NORMALS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0),
           'east': (1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}
PALETTE = {'gold': [177, 145, 69], 'gold_edge': [211, 181, 104],
           'steel': [151, 159, 164], 'darksteel': [73, 79, 85],
           'receiver': [43, 47, 52], 'rubber': [29, 32, 37],
           'recess': [18, 22, 28], 'purple': [77, 34, 115],
           'lens': [23, 27, 38]}


def encode(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def png(im):
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w126:beloved:' + name))


def rotation(r):
    x, y, z = [math.radians(r.get(a, 0)) for a in 'xyz']
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @
            np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @
            np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def vertices(e):
    v = np.array([[e['to' if mask >> a & 1 else 'from'][a] for a in range(3)] for mask in range(8)], float)
    if 'rotation' in e:
        o = np.array(e['rotation']['origin'])
        v = (v - o) @ rotation(e['rotation']).T + o
    return v


def parse_fbx(path):
    """Binary FBX 7400 node reader; inert arrays only, no source execution."""
    data = path.read_bytes()
    assert data[:23] == b'Kaydara FBX Binary  \x00\x1a\x00'
    assert struct.unpack_from('<I', data, 23)[0] == 7400

    def node(pos):
        end, count, _, length = struct.unpack_from('<IIIB', data, pos)
        pos += 13
        if end == 0:
            return None, pos
        name = data[pos:pos + length].decode()
        pos += length
        properties = []
        for _ in range(count):
            kind = chr(data[pos]); pos += 1
            if kind in 'YCFDIL':
                fmt = {'Y': 'h', 'C': '?', 'I': 'i', 'F': 'f', 'D': 'd', 'L': 'q'}[kind]
                value = struct.unpack_from('<' + fmt, data, pos)[0]
                pos += struct.calcsize(fmt)
            elif kind in 'SR':
                length = struct.unpack_from('<I', data, pos)[0]; pos += 4
                value = data[pos:pos + length]; pos += length
                if kind == 'S':
                    value = value.decode(errors='replace')
            elif kind in 'fdlibc':
                length, compression, size = struct.unpack_from('<III', data, pos); pos += 12
                raw = data[pos:pos + size]; pos += size
                assert compression in (0, 1)
                if compression:
                    raw = zlib.decompress(raw)
                fmt = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': '?', 'c': 'b'}[kind]
                value = struct.unpack('<' + str(length) + fmt, raw)
            else:
                raise ValueError('Unsupported FBX type ' + kind)
            properties.append(value)
        children = []
        while pos < end - 13:
            child, pos = node(pos)
            assert child is not None
            children.append(child)
        return (name, properties, children), end

    roots = []; pos = 27
    while pos < len(data):
        value, pos = node(pos)
        if value is None:
            break
        roots.append(value)
    return roots


def source_meshes():
    meta = json.loads((ROOT / 'art/blockbench/weapons/w30/beloved.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW / 'Beloved.fbx').read_bytes()) == meta['source_files']['Beloved.fbx']
    roots = parse_fbx(RAW / 'Beloved.fbx')
    objects = next(n[2] for n in roots if n[0] == 'Objects')
    links = [n[1][1:] for r in roots if r[0] == 'Connections' for n in r[2] if n[1][0] == 'OO']
    models = {n[1][0]: n for n in objects if n[0] == 'Model'}
    meshes = []
    for node in objects:
        if node[0] != 'Geometry':
            continue
        mid = next(parent for child, parent in links if child == node[1][0])
        model = models[mid]; name = model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:
            continue
        props = {p[1][0]: p[1][4:] for c in model[2] if c[0] == 'Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'], [-90, 0, 0], atol=.0001)
        assert props['Lcl Scaling'] == [100, 100, 100]
        cs = {c[0]: c for c in node[2]}
        raw = np.array(cs['Vertices'][1][0]).reshape(-1, 3)
        # Beloved basis, verified against W30 bounds; muzzle is negative native Z.
        v = np.c_[-raw[:, 1], raw[:, 2], -raw[:, 0]] * meta['scale'] + meta['anchor']
        fs = []; face = []
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i >= 0 else -i - 1)
            if i < 0:
                assert len(face) == 3
                fs.append(face); face = []
        layer = next(c for c in node[2] if c[0] == 'LayerElementUV' and c[1][0] == 0)
        vals = {c[0]: c[1][0] for c in layer[2]}
        assert vals['MappingInformationType'] == 'ByPolygonVertex'
        assert vals['ReferenceInformationType'] == 'IndexToDirect'
        uv = np.array(vals['UV']).reshape(-1, 2)[np.array(vals['UVIndex'])].reshape(-1, 3, 2)
        uv[:, :, 1] = 1 - uv[:, :, 1]
        meshes.append(dict(name=name, vertices=v, faces=np.array(fs), uv=uv,
                           material='Scope' if int(name[5:9]) >= 9 else 'Barrel'))
    pts = np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([pts.min(0), pts.max(0)], meta['model_bounds'], atol=1e-5)
    assert sum(len(m['faces']) for m in meshes) == meta['source_triangles']
    return meshes, meta


def make_design(meta):
    """Authored semantic blockout: NOT source polygon/component conversion."""
    parts = {'body': [], 'magazine': []}

    def box(name, lo, hi, mat, group, motif='panel', turn=None, part='body'):
        e = dict(name=name, **{'from': lo, 'to': hi})
        if turn:
            axis, angle = turn
            e['rotation'] = dict(origin=[round((a+b)/2, 6) for a, b in zip(lo, hi)], x=0, y=0, z=0)
            e['rotation'][axis] = angle
        parts[part].append(dict(geometry=e, material=mat, group=group, motif=motif))

    def center(name, c, size, mat, group, motif='panel', turn=None, part='body'):
        box(name, [round(a-b/2, 6) for a, b in zip(c, size)],
            [round(a+b/2, 6) for a, b in zip(c, size)], mat, group, motif, turn, part)

    def tube(name, x, y, z0, z1, radius, thick, mat, group):
        # Eight opaque tangent walls. Gaps are real bores, with recessed lenses.
        width = 2 * radius * math.tan(math.pi/8) + .016
        for i in range(8):
            a = i*45; r = radius - thick/2
            center(f'{name}_{i}', [x-r*math.sin(math.radians(a)), y+r*math.cos(math.radians(a)), (z0+z1)/2],
                   [width, thick, z1-z0], mat, group, 'rim', ('z', a))

    # Long continuous barrel, visibly faceted under oblique light, not voxels.
    tube('barrel', 8, 10.015, -12.1, -3.05, .255, .16, 'steel', 'barrel')
    box('barrel_root', [7.63, 9.67, -3.7], [8.37, 10.36, -2.85], 'darksteel', 'barrel', 'barrel_root')
    # The muzzle has a physically open horizontal slot, deep throat and two jaws.
    box('muzzle_upper_jaw', [7.50, 10.24, -15.5], [8.5, 10.53, -12.12], 'steel', 'muzzle', 'muzzle')
    box('muzzle_lower_jaw', [7.50, 9.50, -15.5], [8.5, 9.79, -12.12], 'darksteel', 'muzzle', 'muzzle')
    for side in (-1, 1):
        x = 8 + side*.48
        center('muzzle_upper_bevel_'+str(side), [x, 10.23, -13.81], [.22, .22, 3.38], 'steel', 'muzzle', 'muzzle', ('z', 45*side))
        center('muzzle_lower_bevel_'+str(side), [x, 9.8, -13.81], [.22, .22, 3.38], 'darksteel', 'muzzle', 'muzzle', ('z', -45*side))
        center('muzzle_throat_'+str(side), [8+side*.35, 10.015, -12.25], [.30, .76, .60], 'steel', 'muzzle', 'panel')
    # Gold load-bearing rails, side ornament sits on a real open cage.
    box('forearm_upper_spine', [7.59, 10.43, -3.05], [8.41, 10.70, 4.10], 'gold_edge', 'forearm', 'gold_rail')
    box('forearm_lower_spine', [7.60, 9.22, -3.05], [8.40, 9.49, 4.05], 'gold', 'forearm', 'gold_rail')
    box('forearm_inner_barrel', [7.76, 9.73, -3.1], [8.24, 10.21, 4.43], 'recess', 'forearm', 'flute')
    for z, tag in [(-3.0, 'front'), (3.95, 'rear')]:
        box('forearm_'+tag+'_collar', [7.42, 9.39, z-.18], [8.58, 10.49, z+.18], 'gold', 'forearm', 'collar')
        for side in (-1, 1):
            center(f'forearm_{tag}_lug_{side}', [8+side*.61, 9.94, z], [.22, .62, .64], 'gold_edge', 'forearm', 'lug', ('x', 45))
    for i, z in enumerate([-1.78, .48, 2.74]):
        # Separate solid diamond crests + raised bevel and purple cabochon.
        # Filigree/pearls use actual source DDS relief, recolored to default gold.
        for side in (-1, 1):
            label = f'ornament_{i}_{side}'
            center(label+'_crest', [8+side*.63, 10.03, z], [.24, 1.43, 1.43], 'gold', 'ornaments', 'crest', ('x', 45))
            center(label+'_bezel', [8+side*.76, 9.99, z], [.16, .80, 1.82], 'gold_edge', 'ornaments', 'bezel')
            center(label+'_gem', [8+side*.858, 9.99, z], [.085, .57, 1.54], 'purple', 'ornaments', 'gem')
        # Structural top/bottom saddle gives true thickness to each crest.
        center(f'crest_top_saddle_{i}', [8, 10.59, z], [1.30, .24, .36], 'gold_edge', 'forearm', 'gold_rail')
        center(f'crest_bottom_saddle_{i}', [8, 9.46, z], [1.28, .25, .36], 'gold', 'forearm', 'gold_rail')
    # Receiver: continuous major volume with shoulder bevels, real bolt handle.
    box('receiver_core', [7.48, 9.48, 4.13], [8.52, 10.43, 8.95], 'receiver', 'receiver', 'receiver')
    box('receiver_top', [7.60, 10.43, 4.18], [8.40, 10.77, 8.82], 'receiver', 'receiver', 'rail')
    for side in (-1, 1):
        center(f'receiver_shoulder_{side}', [8+side*.47, 10.40, 6.51], [.28, .28, 4.66], 'darksteel', 'receiver', 'panel', ('z', 45*side))
        center(f'receiver_front_band_{side}', [8+side*.55, 9.98, 4.22], [.13, 1.18, .46], 'darksteel', 'receiver', 'receiver_band')
    box('action_lower', [7.55, 8.88, 4.24], [8.45, 9.53, 7.40], 'receiver', 'receiver', 'action')
    box('magazine_socket', [7.60, 8.50, 4.23], [8.55, 9.12, 6.55], 'receiver', 'receiver', 'action')
    box('bolt_port_recess', [8.522, 9.67, 5.11], [8.55, 10.06, 6.88], 'recess', 'receiver', 'port')
    center('bolt_handle_shaft', [8.80, 9.59, 5.07], [.91, .20, .23], 'darksteel', 'receiver', 'panel', ('y', -18))
    center('bolt_handle_knob', [9.24, 9.50, 5.20], [.34, .39, .38], 'rubber', 'receiver', 'knob', ('y', -18))
    # Skeleton stock: no filler/alpha between comb, wrist and bottom brace.
    box('stock_comb', [7.48, 9.49, 8.88], [8.52, 10.49, 13.35], 'receiver', 'stock', 'stock')
    box('stock_cheek_wrap', [7.39, 9.53, 9.26], [8.61, 10.62, 11.88], 'rubber', 'stock', 'wrap')
    box('stock_butt_pad', [7.46, 8.02, 13.05], [8.54, 10.59, 13.5], 'rubber', 'stock', 'butt')
    center('stock_lower_brace', [8, 7.85, 11.0], [.64, .33, 4.30], 'receiver', 'stock', 'stock', ('x', -9))
    center('stock_wrist', [8, 8.40, 8.32], [.72, 2.38, .58], 'receiver', 'stock', 'grip', ('x', -27))
    center('grip_heel', [8, 7.41, 8.88], [.76, .28, .70], 'rubber', 'stock', 'panel', ('x', -15))
    center('stock_rear_join', [8, 8.40, 12.83], [.65, .50, .90], 'receiver', 'stock', 'stock', ('x', -25))
    # Open trigger bow + an actual gold trigger, separate from the magazine.
    box('trigger_bow_front', [7.68, 8.33, 6.78], [8.32, 8.97, 7.00], 'darksteel', 'trigger', 'panel')
    box('trigger_bow_bottom', [7.68, 8.27, 6.91], [8.32, 8.46, 7.87], 'darksteel', 'trigger', 'panel')
    center('trigger_bow_rear', [8, 8.66, 7.99], [.64, .18, .63], 'darksteel', 'trigger', 'panel', ('x', -27))
    center('gold_trigger', [8, 8.75, 7.25], [.23, .16, .44], 'gold', 'trigger', 'rim', ('x', -24))
    # Raised optic, solid bevel body plus an actual recessed front lens.
    box('scope_rail', [7.45, 10.76, 4.73], [8.55, 10.95, 8.41], 'recess', 'scope', 'rail')
    for i, z in enumerate([5.38, 7.76]):
        box(f'scope_gold_foot_{i}', [7.55, 10.95, z-.28], [8.45, 11.34, z+.28], 'gold', 'scope', 'scope_mount')
    box('scope_body', [7.53, 11.55, 5.39], [8.47, 12.23, 8.45], 'receiver', 'scope', 'scope')
    box('scope_roof', [7.65, 12.23, 5.39], [8.35, 12.52, 8.45], 'darksteel', 'scope', 'scope_top')
    box('scope_keel', [7.62, 11.30, 5.48], [8.38, 11.55, 8.37], 'receiver', 'scope', 'scope')
    for side in (-1, 1):
        center(f'scope_roof_bevel_{side}', [8+side*.42, 12.24, 6.92], [.25, .25, 3.06], 'darksteel', 'scope', 'scope_top', ('z', 45*side))
    tube('scope_front_gold_rim', 8, 11.94, 4.93, 5.40, .62, .13, 'gold_edge', 'scope')
    # Opaque octagonal lens composed of central rectangle and bevel-side strips.
    box('scope_lens_center', [7.61, 11.47, 5.30], [8.39, 12.41, 5.33], 'lens', 'scope', 'lens')
    for side in (-1, 1):
        center(f'scope_lens_side_{side}', [8+side*.415, 11.94, 5.315], [.19, .66, .03], 'lens', 'scope', 'lens')
    box('scope_eyepiece', [7.51, 11.55, 8.40], [8.49, 12.33, 8.83], 'rubber', 'scope', 'eyepiece')
    center('scope_side_dial', [8.61, 11.96, 7.02], [.29, .48, .48], 'darksteel', 'scope', 'dial')
    center('scope_diopter_dial', [8.64, 11.96, 7.73], [.27, .39, .39], 'darksteel', 'scope', 'dial')
    # Magazine stays in exactly the old model coordinate space / external pivot.
    box('magazine_main', [7.72, 6.72, 4.12], [8.52, 8.60, 6.39], 'receiver', 'magazine', 'magazine', part='magazine')
    center('magazine_front_slope', [8.12, 7.62, 4.10], [.78, 1.68, .30], 'receiver', 'magazine', 'magazine', ('x', -7), 'magazine')
    box('magazine_rear_spine', [7.72, 6.75, 6.39], [8.52, 8.52, 6.64], 'darksteel', 'magazine', 'magazine_spine', part='magazine')
    box('magazine_base', [7.69, 6.430646, 4.0], [8.56, 6.73, 6.70], 'rubber', 'magazine', 'magazine_base', part='magazine')
    box('magazine_feed', [7.73, 8.52, 4.24], [8.50, 8.670895, 6.32], 'darksteel', 'magazine', 'panel', part='magazine')
    inputs = [BASE, RELOAD+'_body.json', RELOAD+'_magazine.json',
              'art/blockbench/weapons/w30/beloved.bbmodel', ASSET+'textures/item/weapon/w30/beloved.png']
    raw_inputs = [RAW/'Beloved.fbx', RAW/'BelovedBarrel_Diffuse.dds', RAW/'BelovedScope_Diffuse.dds',
                  W31/'references/beloved.jpg', W31/'renders/beloved-after.png']
    oldmag = json.loads((ROOT/(RELOAD+'_magazine.json')).read_bytes())
    mag_bounds = [[min(e['from'][a] for e in oldmag['elements']) for a in range(3)],
                  [max(e['to'][a] for e in oldmag['elements']) for a in range(3)]]
    return dict(id='beloved', revision='W126', method='authored semantic opaque cuboids; no rip component conversion',
                source=meta, palette=PALETTE, atlas=dict(size=EDGE, gutter=2, texels_per_unit=27), parts=parts,
                identity=['silver long barrel / open fork muzzle', 'gold open forearm / three purple jewels per side',
                          'source scrolls and pearl relief', 'black skeleton stock / black optic with gold objective rim'],
                magazine_reference_bounds=mag_bounds, magazine_anchor_policy='Unchanged coordinates; existing external reload pivot retained.',
                input_sha256={p: sha((ROOT/p).read_bytes()) for p in inputs},
                raw_input_sha256={str(p): sha(p.read_bytes()) for p in raw_inputs},
                limitations=['Offline Python rasterizer only; no native parser/pack/game validation.',
                             'Clean default-dye reinterpretation; source relief is static RGBA, not PBR.',
                             'Deliberately simplified bevels and sculpted curves; not an exact rip.'])


class Paint:
    def __init__(self):
        source = Image.open(RAW/'BelovedBarrel_Diffuse.dds').convert('RGB')
        # Actual rectangular cabochon and triangular scroll + three pearls.
        self.gem = np.asarray(source.crop((1570, 695, 2000, 870)).filter(ImageFilter.MedianFilter(3))) / 255.
        self.crest = np.asarray(source.crop((1598, 902, 2000, 1137)).filter(ImageFilter.MedianFilter(3))) / 255.

    def tile(self, spec, face, width, height):
        role = spec['material']; motif = spec['motif']
        u, v = np.meshgrid((np.arange(width)+.5)/width, (np.arange(height)+.5)/height)
        rgb = np.broadcast_to(np.array(PALETTE[role], float), (height, width, 3)).copy()
        # Broad satin highlight, deliberate recessed panel and fine border only.
        rgb *= (.94 + .09*np.exp(-((v-.28)/.30)**2))[:, :, None]
        edge = np.minimum.reduce([u*width, (1-u)*width, v*height, (1-v)*height])
        rgb[edge<1.1] *= .71
        rgb[(edge>=1.1)&(edge<2.1)] *= 1.12
        side = face in ('west', 'east')
        if role == 'gold' or role == 'gold_edge':
            rgb += (2*np.cos(u*math.pi))[:, :, None]
        if side and motif == 'gem':
            # Same original cabochon, independently UV'd for the two sides.
            tex = self.gem
            q = tex[np.minimum((v*tex.shape[0]).astype(int),tex.shape[0]-1),
                    np.minimum((u*tex.shape[1]).astype(int),tex.shape[1]-1)]
            # Keep original facets, purple bands and limited wear; reduce grime.
            rgb = np.clip(q * [1.16, .92, 1.35] * 255, 0, 255)
            rgb += np.array([12, 2, 16])
        if side and motif == 'crest':
            e = spec['geometry']; pts = vertices(e)[list(FACES[face])]
            pos = ((1-u)*(1-v))[:, :, None]*pts[0] + (u*(1-v))[:, :, None]*pts[1] + (u*v)[:, :, None]*pts[2] + ((1-u)*v)[:, :, None]*pts[3]
            cy = (e['from'][1]+e['to'][1])/2; cz = (e['from'][2]+e['to'][2])/2
            # World-aligned upper / lower triangle despite rotated cube UV frame.
            yy = abs(pos[:,:,1]-cy)
            a = np.clip((pos[:,:,2]-cz)/1.86+.5, 0, 1)
            b = np.clip((.96-yy)/.69, 0, 1)
            tex = self.crest
            q = tex[np.minimum((b*tex.shape[0]).astype(int),tex.shape[0]-1),
                    np.minimum((a*tex.shape[1]).astype(int),tex.shape[1]-1)]
            luma = q @ [.2126, .7152, .0722]
            detail = np.clip((luma-.43)*1.65+1.02, .60, 1.28)
            rgb *= detail[:,:,None]
            pearl = (q.min(2)>.62)&(luma>.69)&(b>.62)&(b<.94)
            rgb[pearl] = np.array([221, 218, 190]) * detail[pearl,None]
        if side and motif in ('receiver','action','stock','scope','magazine','magazine_spine'):
            # Continuous authored panel islands; no fake lettering or random noise.
            inside = (u>.10)&(u<.90)&(v>.16)&(v<.83)
            line = inside & ((abs(v-.20)<.018)|(abs(v-.79)<.018))
            rgb[line] *= .57
            if motif == 'receiver':
                port = (u>.17)&(u<.70)&(v>.35)&(v<.64)
                rgb[port] *= .53
                rgb[(abs(v-.35)<.03)&(u>.20)&(u<.68)] *= 1.45
            if motif == 'magazine':
                flutes = ((abs(u-.23)<.026)|(abs(u-.51)<.026)|(abs(u-.77)<.026))&(v>.26)&(v<.87)
                rgb[flutes] *= .63
                rgb[(v>.08)&(v<.12)&(u>.16)&(u<.84)] *= 1.34
            if motif == 'scope':
                # Scope dial housing outline observed on source/photo.
                rr = ((u-.58)/.13)**2 + ((v-.50)/.31)**2
                rgb[(rr>.85)&(rr<1.2)] *= 1.5
        if motif in ('wrap','butt','grip','eyepiece','knob'):
            stripes = (np.mod(u*9,1)<.09)&(v>.10)&(v<.90)
            rgb[stripes] *= .64
            rgb[(np.mod(u*9,1)>.09)&(np.mod(u*9,1)<.17)] *= 1.14
        if motif == 'muzzle' and side:
            for a in (.17,.23,.29):
                rgb[((u-a)**2/(.008**2)+(v-.40)**2/(.055**2))<1] *= .28
        if motif == 'dial' and side:
            r = np.sqrt(((u-.5)*2)**2+((v-.5)*2)**2)
            rgb[(r>.66)&(r<.84)] *= .5
            rgb[(r>.47)&(r<.55)] *= 1.5
        if motif == 'lens' and face in ('north','south'):
            # One coherent lens in world coordinates across its three solid tiles.
            pts = vertices(spec['geometry'])[list(FACES[face])]
            px = pts[0,0]*(1-u)+pts[1,0]*u
            py = pts[0,1]*(1-v)+pts[3,1]*v
            r = np.sqrt(((px-8)/.52)**2+((py-11.94)/.52)**2)
            glint = np.exp(-(((px-7.82)/.11)**2+((py-12.18)/.09)**2))
            rgb[:] = [15, 19, 29]
            rgb += np.clip(1-r,0,1)[:,:,None]*[10,13,25]
            rgb += glint[:,:,None]*[55,62,80]
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((height,width),255,dtype='uint8')]))


def compile_models(d):
    atlas = Image.new('RGBA', (EDGE, EDGE), (0, 0, 0, 0)); paint = Paint()
    tiles = []
    for part, specs in d['parts'].items():
        for spec in specs:
            e = spec['geometry']; v = vertices(e)
            for face, indices in FACES.items():
                p = v[list(indices)]; w = np.linalg.norm(p[1]-p[0]); h = np.linalg.norm(p[3]-p[0])
                width, height = max(6,min(256,math.ceil(w*27))), max(6,min(256,math.ceil(h*27)))
                if spec['motif'] == 'crest' and face in ('east','west'):
                    width = height = 104
                if spec['motif'] == 'gem' and face in ('east','west'):
                    width, height = 104, 40
                tiles.append((part, spec, face, width, height))
    # Shelf pack tall islands first, with extruded gutters; stable order on ties.
    tiles.sort(key=lambda t:(-t[4],-t[3],t[1]['geometry']['name'],t[2]))
    x = y = 2; row = 0; uvmap = {}; islands = []
    for part, spec, face, w, h in tiles:
        if x+w+2 > EDGE:
            x = 2; y += row+4; row = 0
        if y+h+2 > EDGE:
            raise ValueError('Face UV atlas overflow: simplify UV allocation')
        tile = paint.tile(spec, face, w, h)
        padded = Image.fromarray(np.pad(np.array(tile), ((2,2),(2,2),(0,0)), mode='edge'))
        atlas.paste(padded, (x-2, y-2))
        uvmap[(spec['geometry']['name'],face)] = [q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=spec['geometry']['name'],face=face,rect=[x,y,x+w,y+h]))
        x += w+4; row = max(row,h)
    models = {}
    for part, specs in d['parts'].items():
        es = []
        for spec in specs:
            e = copy.deepcopy(spec['geometry'])
            e['faces'] = {f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES}
            es.append(e)
        models[part] = dict(credit='W126 Beloved | semantic solid volumes + source-backed default-dye face UV',
                            textures={'0':'destiny:item/weapon/w123/beloved','particle':'destiny:item/weapon/w123/beloved'},elements=es)
    full = copy.deepcopy(models['body']); full['elements'] += copy.deepcopy(models['magazine']['elements'])
    full['display'] = json.loads((ROOT/BASE).read_bytes())['display']; models['full'] = full
    assert len(full['elements']) <= 1000
    d['atlas']['islands'] = islands
    d['atlas']['used_height'] = y+row+2
    return atlas, models


def inspection(d, models, atlas):
    es = []; groups = []
    for part in ('body','magazine'):
        children = []
        for e in models[part]['elements']:
            b = copy.deepcopy(e); r = b.pop('rotation', {})
            b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
                     origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
            for f in b['faces'].values():
                f['texture'] = 0; f['uv'] = [v*EDGE/16 for v in f['uv']]
            es.append(b); children.append(b['uuid'])
        groups.append(dict(name=part,uuid=uid(part),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
                name='Beloved W126 | offline inspection / semantic solids',resolution={'width':EDGE,'height':EDGE},
                elements=es,outliner=groups,textures=[dict(name='beloved.png',id='0',uuid=uid('texture'),
                width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
                display=models['full']['display'],destiny_w126=dict(nativeAccepted=False,rotationOrder='RzRyRx',
                sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],reloadPivotPolicy=d['magazine_anchor_policy']))


def model_triangles(models, texture):
    tex = np.asarray(texture.convert('RGBA')); result = []
    for m in models.values():
        for e in m['elements']:
            v = vertices(e); R = rotation(e.get('rotation',{}))
            for face, f in e['faces'].items():
                ps = v[list(FACES[face])]; n = R @ np.array(NORMALS[face]); a,b,c,d = f['uv']
                uv = np.array([[a,b],[c,b],[c,d],[a,d]]) / 16
                for ix in ((0,1,2),(0,2,3)):
                    result.append((ps[list(ix)],uv[list(ix)],tex,n))
    return result


def source_triangles(meshes):
    textures = {n:np.asarray(Image.open(RAW/('Beloved'+n+'_Diffuse.dds')).convert('RGBA')) for n in ('Scope','Barrel')}
    result = []
    for m in meshes:
        for ps, uv in zip(m['vertices'][m['faces']],m['uv']):
            n = np.cross(ps[1]-ps[0],ps[2]-ps[0]); length = np.linalg.norm(n)
            if length > 1e-10:
                result.append((ps,uv,textures[m['material']],n/length))
    return result


def render(triangles, camera, extent, viewport, raw=False):
    width,height = viewport; cam = np.array(camera,float); cam /= np.linalg.norm(cam)
    right = np.cross([0,1,0],cam); right /= np.linalg.norm(right); up = np.cross(cam,right)
    center,scale = extent
    bg = np.broadcast_to(np.array([32,39,48],float),(height,width,3)).copy()
    depth = np.full((height,width),-np.inf); light = np.array([.45,.85,-.35]); light /= np.linalg.norm(light)
    for ps,uv,texture,normal in triangles:
        facing = normal@cam
        if not raw and facing < -1e-8:
            continue
        n = normal if facing >= 0 else -normal
        screen = np.c_[(ps@right-center[0])*scale+width/2,height/2-(ps@up-center[1])*scale]
        z = ps@cam; a,b,c = screen
        x0 = max(0,int(math.floor(screen[:,0].min()))); x1 = min(width-1,int(math.ceil(screen[:,0].max())))
        y0 = max(0,int(math.floor(screen[:,1].min()))); y1 = min(height-1,int(math.ceil(screen[:,1].max())))
        if x1<x0 or y1<y0:
            continue
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-10:
            continue
        gx,gy = np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        wa = ((b[1]-c[1])*(gx-c[0])+(c[0]-b[0])*(gy-c[1]))/den
        wb = ((c[1]-a[1])*(gx-c[0])+(a[0]-c[0])*(gy-c[1]))/den; wc = 1-wa-wb
        zz = wa*z[0]+wb*z[1]+wc*z[2]; q = wa[:,:,None]*uv[0]+wb[:,:,None]*uv[1]+wc[:,:,None]*uv[2]
        th,tw = texture.shape[:2]
        tx = np.clip((q[:,:,0]*tw).astype(int),0,tw-1); ty = np.clip((q[:,:,1]*th).astype(int),0,th-1)
        sample = texture[ty,tx]
        visible = (wa>=-1e-7)&(wb>=-1e-7)&(wc>=-1e-7)&(zz>=depth[y0:y1+1,x0:x1+1])&(sample[:,:,3]>=128)
        shade = .64+.36*max(0,float(n@light))
        bg[y0:y1+1,x0:x1+1][visible] = (sample[:,:,:3]*shade)[visible]
        depth[y0:y1+1,x0:x1+1][visible] = zz[visible]
    return Image.fromarray(np.clip(bg,0,255).astype('uint8')), np.isfinite(depth)


def frame(points, camera, w, h):
    cam = np.array(camera,float); cam /= np.linalg.norm(cam); right = np.cross([0,1,0],cam)
    right /= np.linalg.norm(right); up = np.cross(cam,right)
    proj = np.c_[points@right,points@up]; lo,hi = proj.min(0),proj.max(0)
    return (lo+hi)/2,min((w-65)/max(hi[0]-lo[0],.1),(h-65)/max(hi[1]-lo[1],.1))


def comparison(d, meshes, atlas, models):
    w,h = 1000,340
    sheet = Image.new('RGB',(w*3,1760),'#151c25'); draw = ImageDraw.Draw(sheet)
    def label(x,y,s,size=22,color='#e3e7ed'):
        draw.text((x,y),s,fill=color,font_size=size)
    label(24,16,'BELOVED / W126 / authored volumes + clean face UV / OFFLINE ART INSPECTION',30)
    photo = Image.open(W31/'references/beloved.jpg').convert('RGB').crop((0,260,1880,820))
    photo.thumbnail((1650,360)); sheet.paste(photo,(20,65))
    old_render = Image.open(W31/'renders/beloved-after.png').convert('RGB'); old_render.thumbnail((600,320)); sheet.paste(old_render,(1720,65))
    label(24,405,'Default dye reference: black / silver barrel / gold cage / purple gems',20)
    label(1740,405,'W31 historical render',20)
    count = len(models['full']['elements'])
    label(24,445,'RAW SOURCE / 22,120 triangles / undyed DDS')
    label(w+24,445,'LOCAL CANONICAL / 253 cuboids')
    label(2*w+24,445,f'W126 / {count} solid cuboids / no alpha cards')
    old = json.loads((ROOT/BASE).read_bytes())
    oldtex = Image.open(ROOT/(ASSET+'textures/item/weapon/w30/beloved.png'))
    tris = [source_triangles(meshes),model_triangles({'old':old},oldtex),model_triangles({'full':models['full']},atlas)]
    points = np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT THREE-QUARTER',[1,.52,-.60]),('REAR THREE-QUARTER',[-1,.45,.60])]):
        extent = frame(points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_ = render(ts,cam,extent,(w,h),raw=col==0); sheet.paste(im,(col*w,485+row*h))
            label(col*w+20,495+row*h,name,18)
    # Close inspections of real geometry holes / jewelry rather than side-only QA.
    es = models['full']['elements']; groups = {}
    for group in ('ornaments','scope','muzzle','stock'):
        names = {s['geometry']['name'] for ss in d['parts'].values() for s in ss if s['group']==group}
        subset = [e for e in es if e['name'] in names]; ps = np.concatenate([vertices(e) for e in subset])
        cam = [1,.32,-.65] if group!='scope' else [.35,.15,-1]
        im,_ = render(model_triangles({'detail':dict(elements=subset)},atlas),cam,frame(ps,cam,750,210),(750,210))
        groups[group] = im
    for i,(name,im) in enumerate(groups.items()):
        sheet.paste(im,(i*750,1515)); label(i*750+15,1525,name.upper()+' / solid detail',18)
    label(24,1732,'Same camera/scale within each full-model row. Native rendering, first/third person, ADS, reload and 10-20 display QA: pending master.',17)
    return png(sheet)


def review_text(counts):
    return f'''# Beloved W126 — offline art review

Reference: `/tmp/destiny-weapons-w31/references/beloved.jpg` (default dye), W31 render and original Beloved FBX/DDS. The raw albedo is mostly undyed; it is deliberately labeled that way in the comparison.

The new design uses **{counts['full']} opaque cuboids**: body {counts['body']}, magazine {counts['magazine']}. These are semantic barrel walls, forked muzzle jaws, open gold frame, solid jewel settings, receiver, stock braces and optic. It does not convert all 22,120 source triangles/components or substitute two alpha side sheets for a body. Full and body+magazine are alternative representations; assembled count is {counts['full']}, below 1,000.

Identity retained: long silver barrel; open slotted muzzle; three purple jewels per side in gold settings; source scrollwork and pearl studs; dark skeleton stock and scope with gold objective rim. A continuous 1024² atlas allocates independent face islands at about 27 texels per model unit, with 2px extruded gutters. Purple cabochons and upper/lower scroll relief use selected original DDS crops, softly cleaned and recolored to the default-dye reference. Wide structural panels use restrained satin shading, panel seams, grip wraps and magazine flutes. There is no random texture noise or invented text. The static source relief is not runtime PBR.

The side + front/rear oblique comparison shows raw source, local 253-cube canonical, and the new design at the same scale per row. Detail panels show solid jewelry, recessed lens/rim, open muzzle and open stock. `inspection.bbmodel` embeds the atlas and separate body/magazine groups for user-opened inspection only; no GUI state is touched.

Preserved: canonical display transforms; native muzzle -Z axis; source scale {18.824982686476197}; source anchor [8,8,8.359254816030532]; existing magazine coordinate frame/external reload anchor. The magazine's lowest Y and feed height match the source split. Approximate curves, subtle sculpted lip transitions and physical metallic reflections remain simplified.

Offline Python checks cover regeneration, emitted-element budget, all-solid geometry, face UV/opaque gutters, independent mag partition and anchor envelope, structural voids, input provenance, display, and inspection-project parity. Master must still validate 26.3 native rotation/parser, resource-pack registration and texture loading, Polymer parts, first/third-person holding and ADS, split reload trajectory, and 10–20 simultaneously displayed weapons. No game, GUI, Gradle or performance acceptance is claimed.
'''


def generate(include_comparison=True):
    meshes,meta = source_meshes(); d = make_design(meta); atlas,models = compile_models(d)
    counts = {p:len(models[p]['elements']) for p in ('full','body','magazine')}
    points = np.concatenate([vertices(e) for e in models['full']['elements']])
    outputs = {ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL+'.json':encode(models['full']),
               MODEL+'_body.json':encode(models['body']),MODEL+'_magazine.json':encode(models['magazine']),
               ART+'inspection.bbmodel':encode(inspection(d,models,atlas)),ART+'review.md':review_text(counts).encode()}
    if include_comparison:
        outputs[ART+'comparison.png'] = comparison(d,meshes,atlas,models)
    manifest = dict(id='beloved',revision='W126',counts=counts,max_assembled_elements=1000,
                    assembled_elements=counts['body']+counts['magazine'],opaque_cuboids=counts['full'],
                    alpha_elements=0,emitted_faces=counts['full']*6,texture_size=[EDGE,EDGE],
                    actual_bounds=[points.min(0).round(7).tolist(),points.max(0).round(7).tolist()],
                    source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],
                    source_triangles=meta['source_triangles'],canonical_display_exact=True,part_display_absent=True,
                    magazine_coordinate_frame_preserved=True,full_is_body_plus_magazine=True,
                    native_accepted=False,generator_sha256=sha(Path(__file__).read_bytes()),
                    input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
                    output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json'] = encode(manifest)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--verify',action='store_true')
    args = parser.parse_args(); outputs = generate()
    batch = json.loads((ROOT/'docs/qa/2026-10-25/w126/batch.json').read_bytes())
    owned = set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w126-beloved'))
    assert set(outputs) <= owned
    for rel,data in outputs.items():
        p = ROOT/rel
        if args.verify:
            assert p.is_file() and p.read_bytes()==data, 'Regeneration differs: '+rel
        else:
            p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    m = json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; {m["counts"]}; solid faces {m["emitted_faces"]}')


if __name__ == '__main__':
    main()
