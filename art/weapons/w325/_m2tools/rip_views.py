"""Headless read-only reference renders of a rip .blend (never saves). blender -b X.blend --python rip_views.py -- OUTPREFIX"""
import bpy, sys, math, mathutils, os
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
_root = os.path.dirname(bpy.data.filepath); _files = {}
for _d, _, _fs in os.walk(os.path.dirname(_root)):
    for _f in _fs: _files.setdefault(_f.lower(), os.path.join(_d, _f))
for _im in bpy.data.images:
    if _im.source == 'FILE' and not os.path.exists(bpy.path.abspath(_im.filepath)):
        _hit = _files.get(os.path.basename(_im.filepath.replace('\\', '/')).lower())
        if _hit: _im.filepath = _hit; _im.reload()
for m in bpy.data.materials:
    if not m.node_tree: continue
    nt = m.node_tree; outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    if not outn: continue
    e = nt.nodes.new('ShaderNodeEmission')
    grp = [n for n in nt.nodes if n.type == 'GROUP' and n.node_tree and 'PlayerGear' in n.node_tree.name]
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'Diffuse' in n.image.name]
    if grp: nt.links.new(grp[0].outputs['Bake_Color'], e.inputs['Color'])
    elif tex: nt.links.new(tex[0].outputs['Color'], e.inputs['Color'])
    for o in outn: nt.links.new(e.outputs[0], o.inputs['Surface'])
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and o.visible_get()]
for o in meshes:
    if any(k in o.name.lower() for k in ('glass', 'lens')): o.hide_render = True
pts = [o.matrix_world @ mathutils.Vector(c) for o in meshes for c in o.bound_box]
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
c = mathutils.Vector([(lo[i] + hi[i]) / 2 for i in range(3)]); ext = max(hi[i] - lo[i] for i in range(3)) * 1.1
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.device = 'CPU'; sc.render.film_transparent = False
w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (.45, .5, .6, 1)
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
sc.render.resolution_x, sc.render.resolution_y = 1100, 600
for k, d in {'q1': (0.6, -0.55, -0.45), 'q2': (-0.6, -0.55, -0.45), 'rear': (0.05, 1, -0.12), 'front': (0.05, -1, -0.1)}.items():
    d_ = mathutils.Vector(d).normalized(); co.location = c - d_ * 3
    co.rotation_euler = d_.to_track_quat('-Z', 'Y').to_euler(); cam.ortho_scale = ext if k.startswith('q') else ext * 0.5
    sc.render.filepath = f'{out}_{k}.png'; bpy.ops.render.render(write_still=True)
