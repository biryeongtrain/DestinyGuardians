"""Blender-only default-material albedo rebake. Never save/execute source scenes.

Run --background --disable-autoexec --python this.py -- --cache <W30 cache>
--out <staging directory> [--only ids]. Geometry stays fixed; UV repacking is opt-in.
"""
import argparse, base64, hashlib, importlib.util, json, math, pathlib, re, sys
import bpy
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('w30', ROOT/'scripts/art/reconstruct_weapons_w30.py')
w30 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w30)

def linear_to_srgb(v):
    v = np.maximum(v, 0)
    return np.where(v <= .0031308, v*12.92, 1.055*np.power(v, 1/2.4)-.055)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def pure_dye_socket(tree):
    """Locate the saved shader's dyed albedo before metallic/iridescent lighting.

    These legacy shaders convert albedo to a separate white specular lobe before
    Principled BSDF. Baking that socket alone washes dyed metal back to grey.
    Require one unambiguous color exit from the explicitly labelled dye frame,
    excluding branches that sample the view-dependent iridescence lookup.
    """
    author_bake = [s.links[0].from_socket for n in tree.nodes if n.type == 'GROUP_OUTPUT'
                   for s in n.inputs if s.name.lower().replace('_', ' ') == 'bake color' and s.is_linked and s.type == 'RGBA']
    if len(author_bake) == 1:
        return author_bake[0]
    frames = [n for n in tree.nodes if n.type == 'FRAME' and 'dye overlay' in (n.label+' '+n.name).lower()]
    if len(frames) != 1:
        return None
    frame = frames[0]
    def inside(node):
        while node:
            if node == frame:
                return True
            node = node.parent
        return False
    def has_iridescence(node, seen):
        if node.name in seen:
            return False
        seen.add(node.name)
        if node.type == 'TEX_IMAGE' and 'iridescence' in (node.label+' '+node.name+' '+(node.image.name if node.image else '')).lower():
            return True
        return any(has_iridescence(link.from_node, seen) for s in node.inputs for link in s.links)
    candidates = {}
    for link in tree.links:
        if link.from_socket.type != 'RGBA' or not inside(link.from_node) or inside(link.to_node):
            continue
        socket = link.from_socket
        while socket.node.type == 'REROUTE' and socket.node.inputs[0].is_linked:
            socket = socket.node.inputs[0].links[0].from_socket
        if not has_iridescence(socket.node, set()):
            candidates[(socket.node.name, socket.identifier)] = socket
    return next(iter(candidates.values())) if len(candidates) == 1 else None

def bake_existing(model, coords, tris, uvs, textures, bvh):
    """Use stored pixel rectangles; rounded cube extents must not repack UVs."""
    edge = model['textures'][0]['width']
    atlas = np.zeros((edge, edge, 4), dtype=np.uint8)
    tv = coords[tris]
    v0, v1 = tv[:, 1]-tv[:, 0], tv[:, 2]-tv[:, 0]
    d00, d01, d11 = (v0*v0).sum(1), (v0*v1).sum(1), (v1*v1).sum(1)
    den = d00*d11-d01*d01
    for element in model['elements']:
        for face, corners in w30.face_corners(element['from'], element['to']).items():
            x, y, X, Y = [round(v*edge/16) for v in element['faces'][face]['uv']]
            w, h = X-x, Y-y
            c = np.array(corners)
            tile = np.empty((h, w, 4), dtype=np.uint8)
            for j in range(h):
                for k in range(w):
                    p = c[0]+(c[1]-c[0])*((k+.5)/w)+(c[3]-c[0])*((j+.5)/h)
                    pos, normal, idx, distance = bvh.find_nearest(Vector(p))
                    color = np.array([.35, .37, .39, 1.])
                    if idx is not None and textures[idx] is not None and abs(den[idx]) > 1e-15:
                        v2 = np.array(pos)-tv[idx, 0]
                        d20, d21 = v2@v0[idx], v2@v1[idx]
                        bv, bw = (d11[idx]*d20-d01[idx]*d21)/den[idx], (d00[idx]*d21-d01[idx]*d20)/den[idx]
                        uv = (1-bv-bw)*uvs[idx][0]+bv*uvs[idx][1]+bw*uvs[idx][2]
                        img = textures[idx]
                        ix, iy = int((uv[0]%1)*img.shape[1])%img.shape[1], int((uv[1]%1)*img.shape[0])%img.shape[0]
                        color = img[iy, ix]
                    tile[j, k] = np.clip(color*255, 0, 255).astype(np.uint8)
            atlas[y-1:Y+1, x-1:X+1] = np.pad(tile, ((1, 1), (1, 1), (0, 0)), mode='edge')
    return w30.png(atlas)

def repack_uv(model, density):
    edge = model['textures'][0]['width']
    faces = []
    for i, element in enumerate(model['elements']):
        for face, corners in w30.face_corners(element['from'], element['to']).items():
            c = np.array(corners)
            faces.append((i, face, max(2, math.ceil(np.linalg.norm(c[1]-c[0])*density)), max(2, math.ceil(np.linalg.norm(c[3]-c[0])*density))))
    x = y = 1
    row_height = 0
    for i, face, width, height in sorted(faces, key=lambda f: (-f[3], -f[2], f[0], f[1])):
        if x+width+2 > edge:
            x = 1
            y += row_height
            row_height = 0
        assert y+height+1 < edge, 'Detailed atlas budget exceeded'
        model['elements'][i]['faces'][face]['uv'] = [x*16/edge, y*16/edge, (x+width)*16/edge, (y+height)*16/edge]
        x += width+2
        row_height = max(row_height, height+2)

def retexture(row, cache, out, models, density):
    mats, arrays = {}, {}
    def target(mat, files, unused):
        if mat is None:
            return None
        if mat.name not in arrays:
            mats[mat.name] = mat
            arrays[mat.name] = np.zeros((1024, 1024, 4), dtype=np.float32)
        return arrays[mat.name]
    original = w30.material_image
    w30.material_image = target
    try:
        coords, tris, uvs, textures, bvh, info = w30.read_source(row, cache/'raw'/row['id']/'extracted')
    finally:
        w30.material_image = original
    folder = cache/'raw'/row['id']/'extracted'
    files = {p.name.lower(): p for p in folder.rglob('*') if p.is_file()}
    missing, resolved, shared = [], [], []
    for image in list(bpy.data.images):
        if image.type != 'IMAGE':
            continue
        key = re.sub(r'\.\d{3}$', '', image.name).lower()
        path = files.get(key) or files.get(pathlib.PureWindowsPath(image.filepath).name.lower())
        # This lookup is a shared shader library asset, not weapon-specific art.
        # Only reuse an exact-content unanimous match; never guess a diffuse.
        if path is None and re.sub(r'[^a-z]', '', key) == 'iridescencelookupdds':
            candidates = [p for p in cache.rglob('*.dds') if re.sub(r'[^a-z]', '', p.name.lower()) == 'iridescencelookupdds']
            hashes = {sha(p.read_bytes()) for p in candidates}
            if len(hashes) == 1:
                path = sorted(candidates)[0]
                shared.append(dict(image=image.name, path=str(path.relative_to(cache)), sha256=next(iter(hashes))))
        if not image.packed_file and path:
            image.filepath = str(path)
            image.reload()
            resolved.append(key)
        elif not image.packed_file and image.source == 'FILE':
            missing.append(image.name)
    overrides = json.loads((ROOT/'art/weapons/w31/palette-overrides.json').read_text()).get(row['id'], [])
    for override in overrides:
        if override.get('kind') == 'dye_channel':
            tree = bpy.data.node_groups[override['group']]
            nodes = [n for n in tree.nodes if n.type == 'RGB' and n.label == 'Dye Color' and n.parent and n.parent.label == override['channel']]
            assert len(nodes) == 1, (row['id'], override, 'ambiguous dye channel')
            nodes[0].outputs[0].default_value = override['linear_rgba']
            continue
        mat = mats[override['material']]
        node = mat.node_tree.nodes[override['node']]
        socket = node.inputs[override['input']]
        assert not socket.is_linked, 'Do not silently replace linked dye masks'
        socket.default_value = override['linear_rgba']
    # Preserve dye, wear, detail maps and vertex/UV slot selection. Bake only
    # material color, not studio illumination or metallic reflections.
    trees = [m.node_tree for m in bpy.data.materials if m.node_tree]+list(bpy.data.node_groups)
    replacements, pure_dye_outputs = 0, []
    for tree in trees:
        pure = pure_dye_socket(tree)
        if pure is not None:
            pure_dye_outputs.append(dict(tree=tree.name, node=pure.node.name, socket=pure.name))
            emission = tree.nodes.new('ShaderNodeEmission')
            tree.links.new(pure, emission.inputs[0])
            for output in list(tree.nodes):
                if output.type == 'GROUP_OUTPUT':
                    for socket in output.inputs:
                        if socket.type == 'SHADER':
                            tree.links.new(emission.outputs[0], socket)
            continue
        for n in list(tree.nodes):
            if n.type not in ('BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_GLOSSY', 'BSDF_ANISOTROPIC'):
                continue
            inp = n.inputs.get('Base Color') or n.inputs.get('Color')
            if inp is None:
                continue
            e = tree.nodes.new('ShaderNodeEmission')
            e.inputs[0].default_value = inp.default_value
            if inp.is_linked:
                tree.links.new(inp.links[0].from_socket, e.inputs[0])
            for link in list(n.outputs[0].links):
                tree.links.new(e.outputs[0], link.to_socket)
            replacements += 1
    source_scene = bpy.context.scene
    objects = [o for o in source_scene.objects if o.type == 'MESH' and o.name in info['source_objects']]
    # Some artists excluded physical parts from their presentation view layer.
    # Link the same data into an isolated, unhidden bake scene, not their stage.
    scene = bpy.data.scenes.new('W31 isolated albedo bake')
    bpy.context.window.scene = scene
    for o in objects:
        scene.collection.objects.link(o)
        o.hide_render = False
        o.hide_viewport = False
        o.hide_select = False
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 1
    scene.cycles.device = 'CPU'
    scene.render.bake.use_clear = False
    scene.render.bake.margin = 8
    for o in scene.objects:
        o.select_set(False)
    # Legacy meshes retain unused material slots; Cycles still requires a bake
    # target for every slot. They do not contribute triangles to the atlas.
    for o in objects:
        for mat in o.data.materials:
            if mat:
                mats.setdefault(mat.name, mat)
    targets = {}
    for name, mat in mats.items():
        mat.use_nodes = True
        if not mat.node_tree:
            raise ValueError('No material graph: '+name)
        im = bpy.data.images.new('W31_bake_'+name, width=1024, height=1024, alpha=True)
        targets[name] = im
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = im
        mat.node_tree.nodes.active = node
    for o in objects:
        o.select_set(bool(o.data.materials) and all(o.data.materials))
        if o.data.uv_layers.active:
            o.data.uv_layers.active.active_render = True
    bpy.context.view_layer.objects.active = next(o for o in objects if o.select_get())
    try:
        bpy.ops.object.bake(type='EMIT')
    except RuntimeError:
        print('W31 BAKE DIAGNOSTIC', [(o.name, [(m.name, m.use_nodes, m.node_tree.nodes.active.name if m.node_tree and m.node_tree.nodes.active else None) if m else None for m in o.data.materials]) for o in bpy.context.selected_objects if o.type == 'MESH'], flush=True)
        raise
    stats = {}
    for name, im in targets.items():
        px = np.empty(1024*1024*4, dtype=np.float32)
        im.pixels.foreach_get(px)
        px = px.reshape(1024, 1024, 4)
        if name not in arrays:
            continue
        arrays[name][:, :, :3] = np.clip(linear_to_srgb(px[:, :, :3]), 0, 1)
        arrays[name][:, :, 3] = 1
        used = px[:, :, 3] > .5
        stats[name] = dict(coverage=float(used.mean()), mean_rgb=arrays[name][used, :3].mean(axis=0).tolist() if used.any() else [0, 0, 0])
    path = models/(row['id']+'.bbmodel')
    before = path.read_bytes()
    model = json.loads(before)
    if density:
        repack_uv(model, density)
    tex = bake_existing(model, coords, tris, uvs, textures, bvh)
    model['textures'][0]['source'] = 'data:image/png;base64,'+base64.b64encode(tex).decode()
    model['destiny_w30']['texture_sha256'] = sha(tex)
    baseline = next(r for r in json.loads((ROOT/'art/weapons/w31/baseline.json').read_text()) if r['id'] == row['id'])
    model['destiny_w31'] = dict(method='saved_default_shader_graph_pure_dye_albedo_v2', color_space='sRGB', bake_resolution=1024, pixels_per_model_unit=density or 5, display_bounds=baseline['model_bounds'],
        source_bbmodel_sha256=sha(before), source_texture_sha256=json.loads(before)['destiny_w30']['texture_sha256'],
        material_stats=stats, missing_images=missing, resolved_images=resolved, shared_images=shared, palette_overrides=overrides, pure_dye_outputs=pure_dye_outputs, bsdf_basecolor_replacements=replacements, source_files=info['source_files'])
    out.mkdir(parents=True, exist_ok=True)
    (out/(row['id']+'.bbmodel')).write_text(json.dumps(model, separators=(',', ':'), ensure_ascii=False)+'\n')
    (out/(row['id']+'.png')).write_bytes(tex)
    (out/(row['id']+'.json')).write_text(json.dumps(model['destiny_w31'], indent=2))
    print('W31 STAGED', row['id'], stats, 'missing', missing, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=pathlib.Path, required=True)
    parser.add_argument('--out', type=pathlib.Path, required=True)
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--models', type=pathlib.Path, default=ROOT/'art/blockbench/weapons/w30')
    parser.add_argument('--pixels-per-unit', type=int, choices=(0, 5, 12, 14), default=0)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    errors = []
    for row in json.loads((ROOT/'art/weapons/w30/catalog.json').read_text()):
        if not args.only or row['id'] in args.only:
            try:
                retexture(row, args.cache, args.out, args.models, args.pixels_per_unit)
            except Exception as error:
                import traceback
                traceback.print_exc()
                errors.append(dict(id=row['id'], error=str(error)))
    if errors:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out/'errors.json').write_text(json.dumps(errors, indent=2))
        raise RuntimeError(errors)
