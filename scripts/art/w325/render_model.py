"""Blender (headless, empty scene) review renders of a W325 skin json in model px space. Never saves a .blend.
blender -b --python render_model.py -- OUT_PREFIX skin.json atlas.png views(csv of west,east,top,q,front,rear)"""
import bpy, sys, math, json, mathutils
a = sys.argv[sys.argv.index('--') + 1:]
OUT, SKIN, TEX = a[0], a[1], a[2]; want = a[3].split(',') if len(a) > 3 else ['west', 'q']
FACES = {'north': (3, 2, 0, 1), 'south': (6, 7, 5, 4), 'west': (2, 6, 4, 0), 'east': (7, 3, 1, 5), 'up': (2, 3, 7, 6), 'down': (4, 5, 1, 0)}
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
d = json.load(open(SKIN)); els = [e for v in d['parts'].values() for e in v]
mb = lambda p: ((8 - p[0]) / 16, p[2] / 16, p[1] / 16)          # model px -> Blender metres (z up)
def rot(r):
    m = mathutils.Matrix.Identity(3)
    if r:
        ang = [r['angle'] if k == r['axis'] else 0 for k in 'xyz'] if 'axis' in r else [r.get(k, 0) for k in 'xyz']
        m = (mathutils.Matrix.Rotation(math.radians(ang[2]), 3, 'Z') @ mathutils.Matrix.Rotation(math.radians(ang[1]), 3, 'Y')
             @ mathutils.Matrix.Rotation(math.radians(ang[0]), 3, 'X'))
    return m
img = bpy.data.images.load(TEX); W, H = d['texture_size']
mat = bpy.data.materials.new('m'); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img; ti.interpolation = 'Closest'
nt.links.new(ti.outputs[0], bs.inputs['Base Color']); nt.links.new(ti.outputs[1], bs.inputs['Alpha']); bs.inputs['Roughness'].default_value = .85
verts, polys, uvs = [], [], []
for e in els:
    lo, hi = e['from'], e['to']; r = e.get('rotation'); M = rot(r); o = mathutils.Vector(r['origin']) if r else mathutils.Vector((0, 0, 0))
    cs = [M @ (mathutils.Vector([hi[i] if m >> i & 1 else lo[i] for i in range(3)]) - o) + o for m in range(8)]
    for f, fc in e['faces'].items():
        u1, v1, u2, v2 = fc['uv']; b = len(verts)
        for k, (uu, vv) in zip(FACES[f], ((u1, v1), (u2, v1), (u2, v2), (u1, v2))):
            verts.append(mb(cs[k])); uvs.append((uu / 16, 1 - vv / 16))
        polys.append((b, b + 1, b + 2, b + 3))
me = bpy.data.meshes.new('w'); me.from_pydata(verts, [], polys); uvl = me.uv_layers.new()
for li, loop in enumerate(me.loops): uvl.data[li].uv = uvs[loop.vertex_index]
me.materials.append(mat); ob = bpy.data.objects.new('w', me); bpy.context.scene.collection.objects.link(ob)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = False
w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.45, .47, .5, 1); bg.inputs[1].default_value = .7
for ang, en in [((0.9, 0.2, 0.5), 2.2), ((-0.5, -0.4, 0.3), 0.8), ((2.6, 0.3, -2.5), 0.6)]:
    l = bpy.data.lights.new('s', 'SUN'); l.energy = en; lo_ = bpy.data.objects.new('s', l); sc.collection.objects.link(lo_); lo_.rotation_euler = ang
pts = [v for v in verts]; lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
c = mathutils.Vector([(lo[i] + hi[i]) / 2 for i in range(3)]); ext = max(hi[i] - lo[i] for i in range(3)) * 1.1
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
dirs = {'west': (1, 0, 0), 'east': (-1, 0, 0), 'top': (0, 0, -1), 'front': (0, 1, 0), 'rear': (0, -1, 0), 'q': (-0.7, 0.45, -0.45)}
sc.render.resolution_x, sc.render.resolution_y = 1200, 700
for k in want:
    d_ = mathutils.Vector(dirs[k]).normalized(); co.location = c - d_ * 3
    co.rotation_euler = d_.to_track_quat('-Z', 'Z' if k not in ('top',) else 'Y').to_euler(); cam.ortho_scale = ext
    sc.render.filepath = f'{OUT}_{k}.png'; bpy.ops.render.render(write_still=True)
