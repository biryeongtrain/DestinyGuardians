"""Headless, read-only projection extractor for the W302 Khvostov 7G-02 source .blend (never saves the .blend).

Run by scripts/art/build_w302_khvostov_7g_02.py extract.  Renders calibrated orthographic emission passes from the six
axis directions with Cycles:
  <view>_albedo.png : D2 PlayerGear 'Bake_Color' (Body/Sights) / reticle diffuse, sRGB 'Standard', RGBA8, 16 spp box filter
  <view>_depth.png  : depth along the view direction, 16-bit greyscale, 0 = background,
                      v/65535 = 0.02 + 0.98*(dot(p,dir)-dmin)/(dmax-dmin), 1 spp point filter
Usage: Blender -b <blend> --python extract_projection_cache.py -- <outdir> <pixels_per_metre>
"""
import bpy, sys, json, math, os, mathutils
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; ppm = float(args[1])
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.use_denoising = False
sc.cycles.seed = 0
sc.cycles.max_bounces = 0
sc.cycles.device = 'CPU'
sc.render.film_transparent = True
sc.render.resolution_percentage = 100
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
glass = bpy.data.objects.get('Reticle Glass')
if glass: glass.hide_render = True
pts = [o.matrix_world @ mathutils.Vector(c) for o in meshes for c in o.bound_box]
lo = [min(p[i] for p in pts) - 0.01 for i in range(3)]
hi = [max(p[i] for p in pts) + 0.01 for i in range(3)]
ctr = [(lo[i] + hi[i]) / 2 for i in range(3)]
w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[1].default_value = 0.0

def rewire_albedo():
    for m in bpy.data.materials:
        if not m.node_tree or m.name.startswith('xx_'): continue
        nt = m.node_tree
        outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
        if not outn: continue
        e = nt.nodes.get('xx_em') or nt.nodes.new('ShaderNodeEmission'); e.name = 'xx_em'
        for l in list(e.inputs['Color'].links): nt.links.remove(l)
        grp = [n for n in nt.nodes if n.type == 'GROUP' and n.node_tree and 'PlayerGear' in n.node_tree.name]
        tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'Diffuse' in n.image.name]
        if grp: nt.links.new(grp[0].outputs['Bake_Color'], e.inputs['Color'])
        elif tex: nt.links.new(tex[0].outputs['Color'], e.inputs['Color'])
        else: e.inputs['Color'].default_value = (0, 0, 0, 1)
        for o in outn: nt.links.new(e.outputs[0], o.inputs['Surface'])

def depth_material(d, dmin, dmax):
    m = bpy.data.materials.new('xx_depth'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    g = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = d
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = dmin; mr.inputs['From Max'].default_value = dmax
    mr.inputs['To Min'].default_value = 0.02; mr.inputs['To Max'].default_value = 1.0
    nt.links.new(g.outputs['Position'], dot.inputs[0]); nt.links.new(dot.outputs['Value'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], e.inputs['Color']); nt.links.new(e.outputs[0], o.inputs['Surface'])
    return m

VIEWS = {'px': ((1, 0, 0), (0, 0, 1)), 'nx': ((-1, 0, 0), (0, 0, 1)), 'pz': ((0, 0, 1), (1, 0, 0)),
         'nz': ((0, 0, -1), (1, 0, 0)), 'ny': ((0, -1, 0), (0, 0, 1)), 'py': ((0, 1, 0), (0, 0, 1))}
cam = bpy.data.cameras.new('xx_cam'); cam.type = 'ORTHO'
co = bpy.data.objects.new('xx_cam', cam); sc.collection.objects.link(co); sc.camera = co
corners = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
manifest = {'lo': lo, 'hi': hi, 'ppm': ppm, 'depth_encoding': 'v/65535 = 0.02 + 0.98*(dot(p,dir)-dmin)/(dmax-dmin); 0 = background', 'views': {}}
for name, (d, up) in VIEWS.items():
    d = mathutils.Vector(d); up = mathutils.Vector(up); right = up.cross(d)
    ext = [hi[i] - lo[i] for i in range(3)]
    wr = abs(sum(ext[i] * abs(right[i]) for i in range(3))); hu = abs(sum(ext[i] * abs(up[i]) for i in range(3)))
    rx = int(math.ceil(wr * ppm)); ry = int(math.ceil(hu * ppm))
    sc.render.resolution_x = rx; sc.render.resolution_y = ry
    cam.ortho_scale = max(rx, ry) / ppm; cam.clip_start = 0.001; cam.clip_end = 10
    c = mathutils.Vector(ctr); co.location = c + d * 2.0
    co.rotation_euler = mathutils.Matrix((right, up, d)).transposed().to_euler()
    dots = [sum(cc[i] * d[i] for i in range(3)) for cc in corners]
    dmin, dmax = min(dots), max(dots)
    manifest['views'][name] = {'res': [rx, ry], 'centre': list(c), 'right': list(right), 'up': list(up), 'dir': list(d),
                               'dmin': dmin, 'dmax': dmax}
    # albedo
    sc.cycles.samples = 16; sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 1.0
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    rewire_albedo(); sc.view_layers[0].material_override = None
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '8'
    sc.render.filepath = os.path.join(out, f'{name}_albedo.png'); bpy.ops.render.render(write_still=True)
    # depth
    sc.cycles.samples = 1; sc.cycles.filter_width = 0.01
    sc.view_settings.view_transform = 'Raw'
    sc.view_layers[0].material_override = depth_material(d, dmin, dmax)
    sc.render.image_settings.color_mode = 'BW'; sc.render.image_settings.color_depth = '16'
    sc.render.filepath = os.path.join(out, f'{name}_depth.png'); bpy.ops.render.render(write_still=True)
json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1, sort_keys=True)
print('done', out)
