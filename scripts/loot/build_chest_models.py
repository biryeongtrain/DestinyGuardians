#!/usr/bin/env python3
"""Activity reward chest + Glimmer pickup models.

Sources (Drive root 14Ry-piQtH3j6MlfoVLfFfu98c4pcTJUb, Misc, read-only):
  Interactable Items/Khvostov Golden Chest [BLENDER 4.X ONLY].7z  (file 179gmP5XR92Fw93-unKivGa94nCm1Hwjb)
  Pick-Ups/Glimmer.rar                                             (file 1XCtZbBy5LdAbTyaYG5MgmxNAHYX4u2z_)

  Blender -b "<extracted>/Khvostov Golden Chest.blend" --python build_chest_models.py -- <glimmer_diffuse.png>

The chest mesh is one skinned mesh: bone CFFAB20E is the body (and the Glimmer pile inside), bone 7BFE9BB6 is the
lid hinged at (x=-0.39, z=0.509). Rest pose is closed. Body and lid are split by dominant bone weight and baked as
orthographic projection impostors: six ortho renders per part, a stepped slab silhouette from the side/front
alpha, and every slab face sampling the render of its own direction. The lid model puts its hinge at the model
centre so the server rotates it open about the display origin. Blender axes: +x front, +y width, +z up.
MC model: x = blender y, y = blender z (base at 0), z = blender x (front = south).
"""
import json, math, sys
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
WORK = Path('/tmp/dg-chest/bake'); WORK.mkdir(parents=True, exist_ok=True)
PPM = 300                 # render pixels per metre (chest is ~1.1 m wide, seen up close)
ATLAS = 1024
BODY_BONE, LID_BONE = 'CFFAB20E', '7BFE9BB6'
HINGE = (-0.39, 0.509)    # blender x, z
Z0 = -0.048               # chest base

# outward normal (blender) -> (MC face, camera right, camera up)
VIEWS = {
    'south': (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
    'north': (Vector((-1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))),
    'east': (Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1))),
    'west': (Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))),
    'up': (Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((-1, 0, 0))),
    'down': (Vector((0, 0, -1)), Vector((0, 1, 0)), Vector((1, 0, 0))),
}


def split_parts():
    parts = {'body': [], 'lid': []}
    for o in list(bpy.data.objects):
        if o.type != 'MESH': continue
        for part, keep in (('body', BODY_BONE), ('lid', LID_BONE)):
            c = o.copy(); c.data = o.data.copy(); c.name = f'{part}_{o.name[-24:]}'
            bpy.context.scene.collection.objects.link(c)
            for m in list(c.modifiers): c.modifiers.remove(m)
            bm = bmesh.new(); bm.from_mesh(c.data)
            dl = bm.verts.layers.deform.active
            drop = []
            for v in bm.verts:
                w = v[dl] if dl else {}
                best = max(w.items(), key=lambda kv: kv[1])[0] if w else None
                if best is None or o.vertex_groups[best].name != keep: drop.append(v)
            bmesh.ops.delete(bm, geom=drop, context='VERTS')
            bm.to_mesh(c.data); bm.free()
            c.matrix_world = o.matrix_world.copy()
            if len(c.data.polygons): parts[part].append(c)
            else: bpy.data.objects.remove(c)
        o.hide_render = True
    glow = bpy.data.materials.new('chest_glow'); glow.use_nodes = True
    nt = glow.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (.32, 1, .42, 1); em.inputs[1].default_value = 2.2
    out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs[0])
    for objs in parts.values():   # Index20 = the green status lights; their D2 shader group does not evaluate here
        for c in objs:
            if 'Index20' in c.name: c.data.materials.clear(); c.data.materials.append(glow)
    return parts


def bounds(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def render_views(part, objs):
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o not in objs
    lo, hi = bounds(objs)
    centre = (lo + hi) / 2
    out = {}
    for face, (n, right, up) in VIEWS.items():
        corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        rs = [c.dot(right) for c in corners]; us = [c.dot(up) for c in corners]
        w, h = max(rs) - min(rs) + .02, max(us) - min(us) + .02
        rx, ry = max(8, math.ceil(w * PPM)), max(8, math.ceil(h * PPM))
        w, h = rx / PPM, ry / PPM
        cam = sc.camera
        cam.data.ortho_scale = max(w, h)
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        mr, mu = (min(rs) + max(rs)) / 2, (min(us) + max(us)) / 2
        depth = 3.0
        pos = right * mr + up * mu + n * (centre.dot(n) + depth)
        cam.matrix_world = Matrix((
            (right.x, up.x, n.x, pos.x), (right.y, up.y, n.y, pos.y), (right.z, up.z, n.z, pos.z), (0, 0, 0, 1)))
        cam.data.clip_end = 10
        path = WORK / f'{part}_{face}.png'
        sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
        out[face] = {'file': str(path), 'w': rx, 'h': ry, 'left': mr - w / 2, 'top': mu + h / 2,
                     'right': list(right), 'up': list(up)}
    return out, lo, hi


def load(path):
    im = bpy.data.images.load(path)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1].copy()  # top row first
    bpy.data.images.remove(im)
    return a


def fill(a):
    """Dilate colour into transparent pixels and make the image opaque (no see-through slivers on faces)."""
    rgb, al = a[..., :3].copy(), a[..., 3] > .45
    filled = al.copy()
    for _ in range(64):
        if filled.all(): break
        acc = np.zeros_like(rgb); cnt = np.zeros(al.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            sh = np.roll(np.roll(filled, dy, 0), dx, 1); c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += c * sh[..., None]; cnt += sh
        grow = (~filled) & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]; filled |= grow
    grey = rgb.mean(-1, keepdims=True)
    rgb = np.clip((grey + (rgb - grey) * 1.18 - .5) * 1.08 + .52, 0, 1)
    a = a.copy(); a[..., :3] = rgb; a[..., 3] = 1
    return a


def extents(alpha_img, axis_cols):
    """Per row: (first, last) opaque column index, or None."""
    rows = []
    for r in alpha_img:
        idx = np.nonzero(r > .5)[0]
        rows.append((idx[0], idx[-1] + 1) if len(idx) else None)
    return rows


def slabs(views, max_slabs, tol):
    """Stepped silhouette along z: per z band the x extent (east view) and y extent (south view)."""
    e, s = views['east'], views['south']
    ea, sa = load(e['file'])[..., 3], load(s['file'])[..., 3]
    erows, srows = extents(ea, None), extents(sa, None)
    # rows are aligned: both views have up=+z, same PPM, same top (bounds of the same part)
    rows = []
    for i in range(min(len(erows), len(srows))):
        if erows[i] is None or srows[i] is None: continue
        z = e['top'] - (i + .5) / PPM
        # east view: right = -x, so column c -> x = -(left + c/PPM)
        x0, x1 = -(e['left'] + erows[i][1] / PPM), -(e['left'] + erows[i][0] / PPM)
        y0, y1 = s['left'] + srows[i][0] / PPM, s['left'] + srows[i][1] / PPM
        rows.append([z, x0, x1, y0, y1])
    rows.sort(key=lambda r: r[0])
    bands, cur = [], None
    for r in rows:
        if cur and all(abs(r[k] - np.median([q[k] for q in cur])) < tol for k in (1, 2, 3, 4)): cur.append(r)
        else:
            if cur: bands.append(cur)
            cur = [r]
    bands.append(cur)
    while len(bands) > max_slabs:  # merge the thinnest band into its most similar neighbour
        i = min(range(len(bands)), key=lambda k: len(bands[k]))
        j = i - 1 if i == len(bands) - 1 or (i > 0 and diff(bands[i - 1], bands[i]) < diff(bands[i], bands[i + 1])) else i + 1
        a, b = sorted((i, j)); bands[a:b + 1] = [bands[a] + bands[b]]
    out = []
    for b in bands:
        z0, z1 = b[0][0] - .5 / PPM, b[-1][0] + .5 / PPM
        if z1 - z0 < .03: continue   # rim slivers (hinge housing) read as noise; the render already shows them
        med = [float(np.median([q[k] for q in b])) for k in (1, 2, 3, 4)]
        out.append([med[0], med[2], z0, med[1], med[3], z1])   # x0 y0 z0 x1 y1 z1 (blender)
    return out


def diff(a, b):
    ma = [np.median([q[k] for q in a]) for k in (1, 2, 3, 4)]; mb = [np.median([q[k] for q in b]) for k in (1, 2, 3, 4)]
    return sum(abs(x - y) for x, y in zip(ma, mb))


class Atlas:
    def __init__(self, size):
        self.size = size; self.img = np.zeros((size, size, 4), np.float32); self.x = self.y = self.row = 0; self.at = {}

    def put(self, key, a):
        h, w = a.shape[:2]
        if self.x + w > self.size: self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > self.size: raise RuntimeError(f'atlas full at {key}')
        self.img[self.y:self.y + h, self.x:self.x + w] = a
        self.at[key] = (self.x, self.y); self.x += w; self.row = max(self.row, h)

    def height(self): return int(math.ceil((self.y + self.row) / 16) * 16)

    def save(self, path):
        img = self.img[:self.height()]
        im = bpy.data.images.new(path.stem, self.size, img.shape[0], alpha=True)
        im.pixels[:] = img[::-1].ravel(); im.filepath_raw = str(path); im.file_format = 'PNG'; im.save()


def mc(p, hinge):
    """Blender point -> MC model units."""
    if hinge: return [8 + p[1] * 16, 8 + (p[2] - HINGE[1]) * 16, 8 + (p[0] - HINGE[0]) * 16]
    return [8 + p[1] * 16, (p[2] - Z0) * 16, 8 + p[0] * 16]


def elements(part, views, boxes, atlas, hinge):
    els = []
    for k, (x0, y0, z0, x1, y1, z1) in enumerate(boxes):
        a, b = mc((x0, y0, z0), hinge), mc((x1, y1, z1), hinge)
        faces = {}
        for face, (n, right, up) in VIEWS.items():
            v = views[face]
            corners = [Vector((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
            # keep only the face plane's corners
            axis = [i for i in range(3) if n[i] != 0][0]
            plane = (x0, y0, z0)[axis] if n[axis] < 0 else (x1, y1, z1)[axis]
            corners = [c for c in corners if abs(c[axis] - plane) < 1e-5]
            px = [(c.dot(right) - v['left']) * PPM for c in corners]
            py = [(v['top'] - c.dot(up)) * PPM for c in corners]
            ox, oy = atlas.at[f'{part}_{face}']
            u0, u1 = (ox + min(px)) * 16 / ATLAS, (ox + max(px)) * 16 / ATLAS
            v0, v1 = (oy + min(py)) * 16 / atlas.height(), (oy + max(py)) * 16 / atlas.height()
            faces[face] = {'uv': [round(u0, 4), round(v0, 4), round(u1, 4), round(v1, 4)], 'texture': '#0'}
        els.append({'name': f'{part}_{k}', 'from': [round(min(a[i], b[i]), 4) for i in range(3)],
                    'to': [round(max(a[i], b[i]), 4) for i in range(3)], 'faces': faces})
    return els


def write_model(name, els, texture):
    model = {'textures': {'0': texture, 'particle': texture}, 'elements': els,
             'display': {'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [1, 1, 1]}}}
    (ASSETS / 'models/loot').mkdir(parents=True, exist_ok=True)
    (ASSETS / f'models/loot/{name}.json').write_text(json.dumps(model, separators=(',', ':')))
    (ASSETS / 'items/loot').mkdir(parents=True, exist_ok=True)
    (ASSETS / f'items/loot/{name}.json').write_text(json.dumps(
        {'model': {'type': 'minecraft:model', 'model': f'destiny:loot/{name}'}}, indent=2) + '\n')


def glimmer(diffuse):
    """Glimmer pickup: the source shard is a cluster of bevelled cubes (Pick-Ups/Glimmer); five cubes, marble tile."""
    src = load(diffuse)
    h, w = src.shape[:2]
    f = min(h, w) // 64
    lum = src[:f * 64, :f * 64, :3].mean(-1).reshape(64, f, 64, f).mean((1, 3))   # box filter, no aliasing
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
    # The source diffuse is a grey marble mask; the game tints it with the Glimmer shader: deep cyan to white veins.
    lo, hi = np.array([.16, .52, .80]), np.array([.80, .98, 1.0])
    t = lum[..., None] ** 1.3
    tile = np.ones((64, 64, 4), np.float32); tile[..., :3] = lo + (hi - lo) * t
    im = bpy.data.images.new('glimmer', 64, 64, alpha=True); im.pixels[:] = tile[::-1].ravel()
    path = ASSETS / 'textures/item/loot/glimmer.png'; im.filepath_raw = str(path); im.file_format = 'PNG'; im.save()
    cubes = [((5, 5, 5), (10, 10, 10)), ((9, 6, 6), (12.5, 9.5, 9.5)), ((5.5, 9, 6.5), (8.5, 12, 9.5)),
             ((6.5, 4, 8.5), (9, 6.5, 11)), ((4, 6.5, 4.5), (6.5, 9, 7))]
    els = []
    for i, (a, b) in enumerate(cubes):
        faces = {}
        for f in ('north', 'south', 'east', 'west', 'up', 'down'):
            o = (i * 3) % 8
            faces[f] = {'uv': [o, o, o + 8, o + 8], 'texture': '#0'}
        els.append({'name': f'shard_{i}', 'from': list(a), 'to': list(b), 'faces': faces,
                    'rotation': {'angle': [0, 22.5, -22.5, 0, 22.5][i], 'axis': 'y', 'origin': [8, 8, 8]}})
    write_model('glimmer', els, 'destiny:item/loot/glimmer')


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = .9
    cam = bpy.data.objects.new('bake_cam', bpy.data.cameras.new('bake_cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT': o.hide_render = True
    sun = bpy.data.objects.new('bake_sun', bpy.data.lights.new('bake_sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 1.2; sun.rotation_euler = (math.radians(35), 0, math.radians(60))

    parts = split_parts()
    atlas = Atlas(ATLAS)
    meta = {}
    pending = []
    for part, (max_slabs, tol) in (('body', (3, .04)), ('lid', (4, .025))):
        views, lo, hi = render_views(part, parts[part])
        for face, v in views.items(): pending.append((f'{part}_{face}', fill(load(v['file']))))
        meta[part] = {'views': views, 'boxes': slabs(views, max_slabs, tol)}
    # the lid's front lip closes the notch in the body's front wall: keep it just proud of the body face
    bx1, btop = meta['body']['boxes'][0][3], meta['body']['boxes'][0][5]
    for box in meta['lid']['boxes']:
        if box[2] < btop - .01: box[3] = max(box[3], bx1 + .004)
    for key, img in sorted(pending, key=lambda kv: -kv[1].shape[0]): atlas.put(key, img)
    atlas.save(ASSETS / 'textures/item/loot/reward_chest.png')
    for part in ('body', 'lid'):
        els = elements(part, meta[part]['views'], meta[part]['boxes'], atlas, part == 'lid')
        write_model(f'reward_chest_{part}', els, 'destiny:item/loot/reward_chest')
        print('MODEL', part, len(els), meta[part]['boxes'])
    if args: glimmer(args[0])
    (WORK / 'meta.json').write_text(json.dumps(meta, indent=1))


main()
