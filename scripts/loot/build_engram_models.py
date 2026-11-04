#!/usr/bin/env python3
"""3D world-drop engram models from the Engram Megapack (Drive: Misc/Pick-Ups/Engram Megapack.7z,
file id 1PQndp7oIOqCjgMszuhWfdKdBn04R3Z6n, Charm export of C6B9A580).

Two halves:
  Blender -b "<extracted>/Engram Megapack.blend" --python build_engram_models.py -- render <work>
      un-excludes the tier collections, remaps G:/ texture paths to the extracted folder, renders each tier
      orthographically along the top face normal (EEVEE, film transparent) and dumps the dodecahedron faces.
  python3 build_engram_models.py bake <work>
      impostor bake: every one of the 12 pentagon faces samples the top-face render (the source look through
      the glass, including the inner core), split into native 26.3 right-triangle elements
      (scripts/mesh/native_triangle_elements_w115.py). Source is read-only; outputs go to the resource pack.
"""
import json, math, os, sys
from pathlib import Path

TIERS = {'common': 'Common Engram', 'uncommon': 'Uncommon Engram', 'rare': 'Rare Engram',
         'legendary': 'Legendary Engram', 'exotic': 'Exotic Engram | Group 0'}
SHELL = 'C6B9A580_Group4_Index12_12_GripStock0'   # 36-triangle regular dodecahedron, circumradius ~0.2535
ORTHO, RES = 0.56, 1024
ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
TILE, COLS = 32, 12
MODEL_RADIUS = 4.0   # model units (block = 16)


def render(work):
    import bpy
    from mathutils import Vector
    work = Path(work); work.mkdir(parents=True, exist_ok=True)
    base = Path(bpy.data.filepath).parent
    def unex(lc):
        lc.exclude = False
        for x in lc.children: unex(x)
    unex(bpy.context.view_layer.layer_collection)
    for im in bpy.data.images:
        if im.filepath.startswith('G:/') and '/Engrams/' in im.filepath:
            im.filepath = str(base / im.filepath.split('/Engrams/')[1]); im.reload()
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (.6, .6, .6, 1)
    cam = bpy.data.objects.new('engram_cam', bpy.data.cameras.new('engram_cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = ORTHO; cam.location = (0, 0, 3); cam.rotation_euler = (0, 0, 0)
    for key, col in TIERS.items():
        names = {o.name for o in bpy.data.collections[col].objects}
        for o in bpy.data.objects:
            if o.type == 'MESH': o.hide_render = o.name not in names
        sc.render.filepath = str(work / f'{key}_top.png'); bpy.ops.render.render(write_still=True)
    o = bpy.data.objects[SHELL]; me = o.data
    groups = {}
    for p in me.polygons:
        pts = [tuple(o.matrix_world @ me.vertices[i].co) for i in p.vertices]
        c = Vector([sum(x) / 3 for x in zip(*pts)]); n = (o.matrix_world.to_3x3() @ p.normal).normalized()
        if n.dot(c) < 0: n = -n
        k = tuple(round(x, 2) for x in n)
        groups.setdefault(k, []).extend(pts)
    faces = []
    for k, pts in groups.items():
        u = []
        for p in pts:
            if all(math.dist(p, q) > 1e-5 for q in u): u.append(p)
        faces.append({'normal': list(k), 'vertices': u})
    (work / 'faces.json').write_text(json.dumps(faces))


def bake(work):
    sys.path.insert(0, str(ROOT / 'scripts/mesh'))
    from native_triangle_elements_w115 import split_triangle, to_element, point_at
    from PIL import Image
    work = Path(work)
    faces = json.loads((work / 'faces.json').read_text())
    def sub(a, b): return [x - y for x, y in zip(a, b)]
    def dot(a, b): return sum(x * y for x, y in zip(a, b))
    def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    def unit(a): n = math.sqrt(dot(a, a)); return [x / n for x in a]
    def frame(f):
        c = [sum(x) / len(f['vertices']) for x in zip(*f['vertices'])]
        n = unit(c)
        e1 = unit(sub(f['vertices'][0], c)); e2 = cross(n, e1)
        ordered = sorted(f['vertices'], key=lambda v: math.atan2(dot(sub(v, c), e2), dot(sub(v, c), e1)))
        return c, n, e1, e2, ordered
    top = max(faces, key=lambda f: sum(v[2] for v in f['vertices']))
    tc, tn, te1, te2, _ = frame(top)
    def to_px(p3):   # top-view render: camera +Z looking down, right=+X, up=+Y
        return (RES / 2 + p3[0] / ORTHO * RES, RES / 2 - p3[1] / ORTHO * RES)
    scale = MODEL_RADIUS / max(math.sqrt(dot(v, v)) for f in faces for v in f['vertices'])
    def model(p):   # source Z-up -> Minecraft Y-up, centred at (8,8,8)
        return (8 + p[0] * scale, 8 + p[2] * scale, 8 - p[1] * scale)
    report = {}
    for tier in TIERS:
        src = Image.open(work / f'{tier}_top.png').convert('RGBA')
        parts = []
        for f in faces:
            c, n, e1, e2, ordered = frame(f)
            for i in range(5):   # fan from centroid: 5 triangles per pentagon
                tri = [c, ordered[i], ordered[(i + 1) % 5]]
                for part in split_triangle([model(v) for v in tri]):
                    parts.append((part, (c, e1, e2)))
        rows = math.ceil(len(parts) / COLS)
        atlas = Image.new('RGBA', (COLS * TILE, rows * TILE), (0, 0, 0, 0))
        elements = []
        inv = 1 / scale
        for idx, (part, (c, e1, e2)) in enumerate(parts):
            tx, ty = idx % COLS, idx // COLS
            for py in range(TILE):
                for px in range(TILE):
                    u, v = (px + .5) / TILE, (py + .5) / TILE
                    if u > v + 1.5 / TILE: continue
                    m = point_at(part, min(u, v), v)
                    p = (( m[0] - 8) * inv, -(m[2] - 8) * inv, (m[1] - 8) * inv)   # back to source space
                    d = sub(p, c); a, b = dot(d, e1), dot(d, e2)
                    q = [tc[k] + a * te1[k] + b * te2[k] for k in range(3)]
                    sx, sy = to_px(q)
                    r, g, bl, al = src.getpixel((min(RES - 1, max(0, int(sx))), min(RES - 1, max(0, int(sy)))))
                    if al: r, g, bl = (min(255, int(x * 255 / al)) for x in (r, g, bl))
                    atlas.putpixel((tx * TILE + px, ty * TILE + py), (r, g, bl, 255))
            W, H = atlas.size
            uv = [tx * TILE * 16 / W, ty * TILE * 16 / H, (tx + 1) * TILE * 16 / W, (ty + 1) * TILE * 16 / H]
            el = to_element(part, f'engram_{tier}', uv)
            el['shade'] = False; el['light_emission'] = 15
            elements.append(el)
        tex = ASSETS / f'textures/item/loot/engram_{tier}.png'; tex.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(tex, optimize=True)
        mdl = ASSETS / f'models/loot/engram_{tier}.json'; mdl.parent.mkdir(parents=True, exist_ok=True)
        mdl.write_text(json.dumps({'ambientocclusion': False,
            'textures': {'0': f'destiny:item/loot/engram_{tier}', 'particle': f'destiny:item/loot/engram_{tier}'},
            'elements': elements,
            'display': {'fixed': {'scale': [1, 1, 1]}}}, separators=(',', ':')))
        it = ASSETS / f'items/loot/engram_{tier}.json'; it.parent.mkdir(parents=True, exist_ok=True)
        it.write_text(json.dumps({'model': {'type': 'minecraft:model', 'model': f'destiny:loot/engram_{tier}'}}, indent=2) + '\n')
        report[tier] = {'elements': len(elements), 'texture': list(atlas.size)}
    (ROOT / 'src/main/resources/destiny/loot/engram-models.json').write_text(json.dumps({
        'source': {'drive_folder': '14Ry-piQtH3j6MlfoVLfFfu98c4pcTJUb', 'path': 'Misc/Pick-Ups/Engram Megapack.7z',
                   'drive_file_id': '1PQndp7oIOqCjgMszuhWfdKdBn04R3Z6n', 'blend_collections': TIERS, 'shell_mesh': SHELL},
        'method': 'EEVEE ortho top-face render per tier, impostor-mapped onto all 12 dodecahedron faces as native 26.3 right-triangle elements; fullbright, opaque.',
        'tiers': report}, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    {'render': render, 'bake': bake}[args[0]](args[1])
