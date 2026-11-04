"""Blender (headless) review renders in MODEL px registration; never saves .blend.

blender -b [source.blend] --python render_review.py -- OUT PX MODE [model.json tex.png]
MODE=source renders the opened rip with its D2 shader; MODE=model imports native
elements (Rz*Ry*Rx) with nearest-filtered texture into an empty scene.
Model->Blender (contract v2 frame: rip z-3.15, y+0.88): xb=(8-x)/S, yb=(z+8.74)/S-0.7107, zb=(y-11.84)/S+0.1235.
"""
import bpy, sys, math, json, mathutils

a = sys.argv[sys.argv.index('--') + 1:]
OUT, PX, MODE = a[0], float(a[1]), a[2]
S = 24.77 / (0.317 + 0.7107)
Z0, Z1, Y0, Y1 = -11.0, 17.5, 5.0, 15.0
FACES = {'north': (3, 2, 0, 1), 'south': (6, 7, 5, 4), 'west': (2, 6, 4, 0),
         'east': (7, 3, 1, 5), 'up': (2, 3, 7, 6), 'down': (4, 5, 1, 0)}


def mb(p):
    return ((8 - p[0]) / S, (p[2] + 8.74) / S - 0.7107, (p[1] - 11.84) / S + 0.1235)


def rot(r):
    m = mathutils.Matrix.Identity(3)
    if r:
        if 'axis' in r:
            ang = [r['angle'] if k == r['axis'] else 0 for k in 'xyz']
        else:
            ang = [r.get(k, 0) for k in 'xyz']
        m = (mathutils.Matrix.Rotation(math.radians(ang[2]), 3, 'Z') @
             mathutils.Matrix.Rotation(math.radians(ang[1]), 3, 'Y') @
             mathutils.Matrix.Rotation(math.radians(ang[0]), 3, 'X'))
    return m


def import_model(path, tex):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    d = json.load(open(path))
    els = d['elements'] if 'elements' in d else [e for v in d['parts'].values() for e in v]
    img = bpy.data.images.load(tex)
    W = img.size[0]
    mat = bpy.data.materials.new('m'); mat.use_nodes = True
    nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
    ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img; ti.interpolation = 'Closest'
    nt.links.new(ti.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.85
    verts, polys, uvs = [], [], []
    for e in els:
        lo, hi = e['from'], e['to']
        r = e.get('rotation')
        M = rot(r); o = mathutils.Vector(r['origin']) if r else mathutils.Vector((0, 0, 0))
        cs = []
        for m in range(8):
            v = mathutils.Vector([hi[i] if m >> i & 1 else lo[i] for i in range(3)])
            cs.append(M @ (v - o) + o)
        for f, fc in e['faces'].items():
            u1, v1, u2, v2 = fc['uv']
            base = len(verts)
            for k, (uu, vv) in zip(FACES[f], ((u1, v1), (u2, v1), (u2, v2), (u1, v2))):
                verts.append(mb(cs[k])); uvs.append((uu / 16, 1 - vv / 16))
            polys.append((base, base + 1, base + 2, base + 3))
    me = bpy.data.meshes.new('w302'); me.from_pydata(verts, [], polys)
    uvl = me.uv_layers.new()
    for li, loop in enumerate(me.loops):
        uvl.data[li].uv = uvs[loop.vertex_index]
    me.materials.append(mat)
    ob = bpy.data.objects.new('w302', me); bpy.context.scene.collection.objects.link(ob)


if MODE == 'model':
    import_model(a[3], a[4])
if MODE == 'flat':
    import_model(a[3], a[4])
    for m in bpy.data.materials:
        if m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
            n = m.node_tree.nodes['Principled BSDF']
            for l in list(n.inputs['Base Color'].links): m.node_tree.links.remove(l)
            n.inputs['Base Color'].default_value = (0.8, 0.1, 0.6, 1)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.5, 0.5, 0.5, 1); bg.inputs[1].default_value = 0.6
for ang, e in [((0.9, 0.2, 0.5), 2.0), ((-0.5, -0.4, 0.3), 0.8), ((2.6, 0.3, -2.5), 0.6)]:
    l = bpy.data.lights.new('s', 'SUN'); l.energy = e
    lo_ = bpy.data.objects.new('s', l); sc.collection.objects.link(lo_); lo_.rotation_euler = ang
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'
co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
V = mathutils.Vector
views = {
    'west': ((0, 1, 0), (0, 0, 1), (Z0, Z1, Y0, Y1), (6.0, 9.5)),
    'east': ((0, -1, 0), (0, 0, 1), (Z0, Z1, Y0, Y1), (6.0, 9.5)),
    'top': ((0, 1, 0), (-1, 0, 0), (Z0, Z1, 5.0, 11.0), None),
    'rear': ((0, 1, 0), (0, 0, 1), (1.0, 10.0, 6.0, 13.5), None),
    'q': (None, None, (Z0, Z1, Y0, Y1), None),
    'front': ((1, 0, 0), (0, 0, 1), (4.0, 12.0, 6.0, 14.0), None),
}
want = a[5].split(',') if len(a) > 5 else list(views)
for k in want:
    r, u, (za, zb, ya, yb), _ = views[k]
    sc.render.resolution_x = int((zb - za) * PX); sc.render.resolution_y = int((yb - ya) * PX)
    cam.ortho_scale = max(zb - za, yb - ya) / S
    if k == 'top':
        c = V(mb(((ya + yb) / 2, 10.0, (za + zb) / 2)))
    elif k == 'front':
        c = V(mb(((za + zb) / 2, (ya + yb) / 2, 0)))
        c.y = -2.0
    else:
        c = V(mb((8.0, (ya + yb) / 2, (za + zb) / 2)))
    if k == 'q':
        d = V((0.75, -0.42, 0.5)).normalized()
        co.location = c + d * 2.0
        co.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cam.ortho_scale = 29.0 / S
    else:
        r, u = V(r), V(u)
        M = mathutils.Matrix((r, u, r.cross(u))).transposed()
        co.rotation_euler = M.to_euler()
        co.location = c + r.cross(u) * 2.0
    sc.render.filepath = f'{OUT}_{k}.png'
    bpy.ops.render.render(write_still=True)
