"""W300 Guardian Rises — BetterModel cube models for the first mission.

Run headless (Blender 5.x ships numpy):

    Blender -b --python scripts/campaign/rising_models.py -- [--only rg_dreg,...] [--evidence DIR] [--no-render]

Pipeline per model
  1. Import the extracted FBX (READ-ONLY source), evaluate the bind pose, convert Destiny/Blender axes
     to Blockbench/Minecraft model space (+Y up, model front = -Z, 16 px = 1 block).
  2. Map every source bone to a small rig bone (nearest anchored ancestor). Child weapon models that the
     export left at the origin are re-mounted on a hand anchor (authored placement, documented).
  3. Surface-sample the triangles with their source DDS colour (palette grading per texture tag),
     voxelise per rig bone, close + fill, greedy-merge into axis-aligned cubes (no element rotation —
     always BetterModel/26.3 safe) and auto-coarsen until the element budget holds.
  4. Bake a per-face UV atlas from the sampled colours (k texels per voxel, convex-edge darkening).
  5. Add authored glow parts (eyes, cores, engines) and ORIGINAL authored animation clips
     (the extraction contains no animation clips) with the clip names of RisingServices.Models.
  6. Write src/main/resources/destiny/guardian_rises/models/NAME.bbmodel and review renders.

rg_ship is an ORIGINAL authored jumpship: the extraction has no player ship (see docs/design/guardian-rises/models.md).
"""
import bpy, json, math, os, sys, zlib, struct, uuid, base64, hashlib, time
import numpy as np
from mathutils import Vector, Matrix, kdtree

SRC = '/Users/qf/Downloads/Rising-Guardian-2026-11-01/models'
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(REPO, 'src/main/resources/destiny/guardian_rises/models')
EVIDENCE = os.path.join(os.path.dirname(REPO), 'w300-evidence/models')
GENERATOR = 'w300-rising-models-r4'

# ----------------------------------------------------------------------------------------------- rigs
# Source bone hash -> rig bone. Every other source bone inherits the rig bone of its nearest anchored
# ancestor. Order = hierarchy declaration (parent first); the rig parent is derived from the source tree.
FALLEN_ANCHORS = {
    '1A5C68E5': 'root', 'C7C0BA6E': 'hips',
    '695DAF09': 'thigh_l', '35B14D1B': 'shin_l', '9F0FD28C': 'thigh_r', '8BD44A3F': 'shin_r',
    'A152A6A2': 'torso', '0D4EBB10': 'head',
    '038E2D3A': 'uarm_ul', '897A1504': 'farm_ul', '259035C6': 'uarm_ll', 'E350F14F': 'farm_ll',
    'A9D76416': 'uarm_ur', 'A3781DCD': 'farm_ur', 'C32E4198': 'uarm_lr', '85F82F11': 'farm_lr',
}
# palm (weapon grip) = mean of the hand bone and its finger roots
FALLEN_HANDS = {'farm_ul': '8C83CB67', 'farm_ll': '2A2B599C', 'farm_ur': 'DE9D6BEA', 'farm_lr': '7CCDEFE5'}
# limb frame: rig bone -> source bone whose head marks the far end of the limb (leaf limbs)
FALLEN_ENDS = {'shin_l': '0F8B505D', 'shin_r': 'B9B9E05D', 'farm_ul': '8C83CB67', 'farm_ll': '2A2B599C',
               'farm_ur': 'DE9D6BEA', 'farm_lr': '7CCDEFE5'}
FALLEN_LIMBS = ['thigh_l', 'shin_l', 'thigh_r', 'shin_r', 'uarm_ul', 'farm_ul', 'uarm_ll', 'farm_ll',
                'uarm_ur', 'farm_ur', 'uarm_lr', 'farm_lr']
SHANK_ANCHORS = {'1A5C68E5': 'root', 'B5F0FE15': 'body', '47350C69': 'wing_ll', 'D0B3C0C1': 'wing_ul',
                 '81BE8747': 'wing_lr', 'B63D175F': 'wing_ur', '7682264D': 'gun'}
WALKER_ANCHORS = {'1A5C68E5': 'root', 'B5F0FE15': 'body', '7E92D640': 'head',
                  'C6049175': 'leg_fl', '1ABE862E': 'leg_fl_low', '9CBE38E0': 'leg_fr', '5434883E': 'leg_fr_low',
                  'BD39E38A': 'leg_ml', 'B325CFF2': 'leg_ml_low', '7B18A488': 'leg_mr', '95404CDA': 'leg_mr_low',
                  '130A3B7F': 'leg_bl', '3D749CA1': 'leg_bl_low', '9D76C139': 'leg_br', '138DAA1A': 'leg_br_low',
                  '913939BB': 'claw_l', '87BD44AC': 'claw_r', 'F7473E64': 'turret'}
SKIFF_ANCHORS = {'1A5C68E5': 'root', 'B5F0FE15': 'hull', '2D7B30DC': 'clamp_l', 'B787B2AE': 'clamp_r',
                 '828A3F9F': 'gun_l', 'F446DA9F': 'gun_r'}
GHOST_ANCHORS = {'1A5C68E5': 'root', '2FBED439': 'core',
                 '54703D26': 'shell_a_bottom', '5CC2CF05': 'shell_a_top', '1D04DE8C': 'shell_a_left', 'BBB26AC5': 'shell_a_right',
                 '5D17056F': 'shell_b_bottom', '9B1A9B66': 'shell_b_top', '28B4D4C7': 'shell_b_left', 'EAA747DF': 'shell_b_right'}

def limb_frame(axis):
    """Minimal rotation taking the local hanging axis (0,-1,0) onto `axis`. Returns (3x3, euler ZYX deg)."""
    a = np.asarray(axis, dtype=np.float64); a /= np.linalg.norm(a)
    d = np.array([0.0, -1.0, 0.0])
    v = np.cross(d, a); c = float(np.dot(d, a))
    if np.linalg.norm(v) < 1e-6:
        M = np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        M = np.eye(3) + vx + vx @ vx * (1 / (1 + c))
    return M, euler_zyx(M)

def rot_zyx(deg):
    a, b, c = [math.radians(x) for x in deg]
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def _signed_perms():
    import itertools
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            P = np.zeros((3, 3))
            for i, (j, sg) in enumerate(zip(perm, signs)):
                P[j, i] = sg
            if np.linalg.det(P) > 0:
                out.append(P)
    return out

def obb_frame(points):
    """Rotation M (columns = box axes) minimising the axis-aligned box volume of points @ M; the axis
    labelling closest to identity is kept so rest rotations stay small."""
    P = points - points.mean(0)
    if len(P) > 4000:
        P = P[np.linspace(0, len(P) - 1, 4000).astype(int)]
    def vol(M):
        q = P @ M
        return float(np.prod(q.max(0) - q.min(0) + 1e-3))
    w, V = np.linalg.eigh(np.cov(P.T))
    if np.linalg.det(V) < 0:
        V[:, 0] *= -1
    best = min([np.eye(3), V], key=vol)
    step = math.radians(8)
    while step > math.radians(0.25):
        improved = False
        for axis in range(3):
            for sg in (1, -1):
                a = [0, 0, 0]; a[axis] = sg * step
                M = best @ rot_zyx([math.degrees(x) for x in a])
                if vol(M) < vol(best) - 1e-9:
                    best, improved = M, True
        if not improved:
            step *= 0.5
    best = max((best @ Q for Q in _signed_perms()), key=lambda M: np.trace(M))
    return best

def euler_zyx(M):
    """M = Rz(c) Ry(b) Rx(a) (three.js 'ZYX' == JOML rotateZYX, the Blockbench/BetterModel convention)."""
    b = math.asin(max(-1.0, min(1.0, -M[2, 0])))
    a = math.atan2(M[2, 1], M[2, 2])
    c = math.atan2(M[1, 0], M[0, 0])
    return (math.degrees(a), math.degrees(b), math.degrees(c))

DEVILS = dict(cloth=(0.55, 0.12, 0.10), metal=(0.46, 0.45, 0.43), dark=(0.23, 0.22, 0.22), eye=(0.62, 0.86, 1.0))

# Dye/shader data were not extracted: gray detail maps get an authored, palette-matched dye (House of
# Devils-like maroon cloth, worn steel, dark leather). Unique colour albedos are sampled as-is.
FALLEN_PAINT = {   # r2 values (luma/255 in comments) — readable under Minecraft display shading
    '810895C7': ('mul', (0.72, 0.22, 0.19)),   # cloak / wraps, maroon ~94
    '80E157E8': ('mul', (0.74, 0.21, 0.19)),   # captain cloak ~94
    '80E15778': ('mul', (0.60, 0.57, 0.52)),   # captain fur mantle ~146
    '80E1578A': ('mul', (0.52, 0.43, 0.35)),   # under-suit leather ~114
    '80E12D44': ('mul', (0.64, 0.65, 0.66)),   # armour plates (steel) ~165
    '80E15785': ('mul', (0.80, 0.76, 0.68)),   # scratched trims / highlights ~195
    '80E12DF7': ('mul', (0.56, 0.55, 0.53)),   # ~140
    '80E157D8': ('mul', (0.42, 0.38, 0.34)),   # head crest ~99
}

SPECS = {
    'rg_dreg': dict(family_override='fallen_authored', paint=FALLEN_PAINT, grade=(1.0, 1.0), tex_values=(0.36, 0.64), src='fallen_dreg__80E1AFCF', include=['80E1AFCF'], anchors=FALLEN_ANCHORS, family='fallen',
                    ends=FALLEN_ENDS, limbs=FALLEN_LIMBS,
                    weapons=[dict(entity='80A6DB7C', name='weapon', bone='farm_ur', hand='DE9D6BEA', rot=(-90, 0, 0)),
                             dict(entity='80A6DD0B', name='blade', bone='farm_ll', hand='2A2B599C', rot=(180, 0, 0))],
                    px_per_m=16.0, voxel=1.0, budget=(150, 400), tex_max=512, style='dreg'),
    'rg_vandal': dict(family_override='fallen_authored', paint=FALLEN_PAINT, grade=(1.0, 1.0), tex_values=(0.36, 0.64), src='fallen_vandal__80E1AF6E', include=['80E1AF6E'], anchors=FALLEN_ANCHORS, family='fallen',
                      ends=FALLEN_ENDS, limbs=FALLEN_LIMBS,
                      weapons=[dict(entity='80A6DEFD', name='weapon', bone='farm_ur', hand='DE9D6BEA', rot=(-90, 0, 0))],
                      px_per_m=16.0, voxel=1.0, budget=(150, 400), tex_max=512, style='vandal'),
    'rg_captain': dict(family_override='fallen_authored', paint=FALLEN_PAINT, grade=(1.0, 1.0), tex_values=(0.36, 0.64), src='fallen_captain__80E15797', include=['80E15797'], anchors=FALLEN_ANCHORS, family='fallen',
                       ends=FALLEN_ENDS, limbs=FALLEN_LIMBS,
                       weapons=[dict(entity='80A6D809', name='weapon', bone='farm_ur', hand='DE9D6BEA', rot=(-90, 0, 0)),
                                dict(entity='80A6D802', name='blade', bone='farm_lr', hand='7CCDEFE5', rot=(180, 0, 0))],
                       px_per_m=16.0, voxel=1.0, budget=(150, 400), tex_max=512, style='captain'),
    'rg_shank': dict(family_override='shank_authored', base_tint=(0.56, 0.56, 0.58), grade=(1.0, 1.0), tex_values=(0.36, 0.66), src='Shank__80E29872', include=['80E29872'], anchors=SHANK_ANCHORS, family='shank',
                     px_per_m=16.0, voxel=1.0, budget=(120, 380), tex_max=512),
    'rg_walker': dict(family_override='walker_authored', base_tint=(0.54, 0.54, 0.56), grade=(1.0, 1.0), tex_values=(0.34, 0.68), src='Walker__80C60641', include=['80C60641', '80C3EA34', '80C3631C'], anchors=WALKER_ANCHORS,
                      family='walker', px_per_m=16.0 * 0.55, voxel=2.0, budget=(450, 900), tex_max=1024),
    'rg_skiff': dict(family_override='skiff_authored', base_tint=(0.60, 0.59, 0.57), grade=(1.0, 1.0), tex_values=(0.38, 0.70), src='Skiff__80C3EE92', include=['80C3EE92', '80C3EEB3'], anchors=SKIFF_ANCHORS, family='skiff',
                     px_per_m=16.0 * 0.35, voxel=2.0, budget=(250, 600), tex_max=512),
    'rg_ghost': dict(src='Ghost__80CFD3CB', include=['80CFD3CB'], anchors=GHOST_ANCHORS, family='ghost',
                     mesh_bones={'Index13': 'eye'}, obb=['shell_a_bottom', 'shell_a_top', 'shell_a_left', 'shell_a_right',
                     'shell_b_bottom', 'shell_b_top', 'shell_b_left', 'shell_b_right'],
                     paint={'80CF282B': ('tex',), '80CF282F': ('tex',), '80C3AA83': ('tex',)}, grade=(1.0, 1.0),
                     px_per_m=90.0, voxel=0.5, budget=(20, 300), tex_max=256),
    'rg_ship': dict(family='ship', budget=(50, 400), tex_max=512),
}

# ------------------------------------------------------------------------------------------- utilities
def png_bytes(rgba):
    """rgba: uint8 array (h, w, 4), row 0 = top."""
    h, w, _ = rgba.shape
    raw = b''.join(b'\x00' + rgba[y].tobytes() for y in range(h))
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'w300/' + '/'.join(str(p) for p in parts)))

def r4(x):
    return float(round(float(x), 4))

def to_mc(v, k):
    """Blender world (after the -90 X fix: Z up, front +X) -> Blockbench px (Y up, front -Z)."""
    return np.array([-v[1], v[2], -v[0]], dtype=np.float64) * k

def rot_mat(deg):
    """Rotation matrix (MC frame) for authored placement, applied X then Y then Z."""
    rx, ry, rz = [math.radians(a) for a in deg]
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Z @ Y @ X

def rgb_to_hsv_sat(c):
    mx = c.max(-1); mn = c.min(-1)
    return np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)

# ------------------------------------------------------------------------------------------ extraction
class Source:
    pass

def load_image(path, cache):
    if path in cache:
        return cache[path]
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    if max(w, h) > 512:
        f = 512 / max(w, h)
        img.scale(max(1, int(w * f)), max(1, int(h * f)))
        w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    arr = px.reshape(h, w, 4)[:, :, :3].copy()
    cache[path] = arr
    return arr

def material_texture(src_dir, mat_name):
    tag = mat_name.split('.')[0]
    p = f'{src_dir}/Materials/{tag}.slots.json'
    if not os.path.exists(p):
        return None
    for slot in json.load(open(p))['slots']:
        f = f"{src_dir}/TexturesDDS/{slot['texture']}.dds"
        if slot.get('srgb') and os.path.exists(f):
            return slot['texture']
    return None

def extract(name, spec):
    src_dir = f"{SRC}/{spec['src']}"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f"{src_dir}/{spec['src']}.fbx")
    R = Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(100, 4)
    for o in list(bpy.data.objects):
        if o.parent is None:
            o.matrix_world = R @ o.matrix_world
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    k = spec['px_per_m']
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    heads, parent = {}, {}
    for pb in arm.pose.bones:
        heads[pb.name] = to_mc(arm.matrix_world @ pb.head, k)
        parent[pb.name] = pb.parent.name if pb.parent else None
    anchors = spec['anchors']

    def rig_of(bone):
        b = bone
        while b is not None:
            if b in anchors:
                return anchors[b]
            b = parent.get(b)
        return anchors[next(iter(anchors))]

    order = []
    for sb, rb in anchors.items():
        if rb not in order:
            order.append(rb)
    pivots = {anchors[b]: heads[b] for b in anchors}
    rig_parent = {}
    for sb, rb in anchors.items():
        p = parent.get(sb)
        while p is not None and p not in anchors:
            p = parent.get(p)
        rig_parent[rb] = anchors[p] if p else None
    frames = {}
    for rb in spec.get('limbs', []):
        kids = [c for c in order if rig_parent.get(c) == rb]
        end = pivots[kids[0]] if kids else heads[spec['ends'][rb]]
        axis = end - pivots[rb]
        if np.degrees(np.arccos(np.clip(-axis[1] / np.linalg.norm(axis), -1, 1))) > 8:
            M, eul = limb_frame(axis)
            frames[rb] = (M, eul, pivots[rb])
    weapons = {w['entity']: w for w in spec.get('weapons', [])}
    obb_bones = spec.get('obb', [])
    img_cache, tex_ids, tex_arrays = {}, {}, []
    P, UV, TEX, BONE, AREA = [], [], [], [], []
    for o in bpy.data.objects:
        if o.type != 'MESH' or 'InternalGeom' in o.name:
            continue
        prefix = o.name.split('_')[0]
        if prefix not in spec['include'] and prefix not in weapons:
            continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        n = len(me.vertices)
        co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        M = np.array(o.matrix_world)
        wco = co @ M[:3, :3].T + M[:3, 3]
        mc = np.stack([-wco[:, 1], wco[:, 2], -wco[:, 0]], 1) * k
        nt = len(me.loop_triangles)
        tv = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', tv); tv = tv.reshape(-1, 3)
        tl = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('loops', tl); tl = tl.reshape(-1, 3)
        tm = np.empty(nt, dtype=np.int64); me.loop_triangles.foreach_get('material_index', tm)
        if me.uv_layers:
            luv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', luv); luv = luv.reshape(-1, 2)
        else:
            luv = np.zeros((len(me.loops), 2))
        # dominant deform bone per vertex (original data keeps the groups)
        gnames = {g.index: g.name for g in o.vertex_groups}
        vbone = []
        for v in o.data.vertices:
            if v.groups:
                g = max(v.groups, key=lambda g: g.weight)
                vbone.append(gnames.get(g.group))
            else:
                vbone.append(None)
        mesh_rig = None
        for sub, rb in spec.get('mesh_bones', {}).items():
            if sub in o.name:
                mesh_rig = rb
        if prefix in weapons:
            w = weapons[prefix]
            hand = w['hand']
            kids = [b for b, p in parent.items() if p == hand]
            palm = np.mean([heads[hand]] + [heads[c] for c in kids], 0)
            Rw = rot_mat(w['rot'])
            if w['bone'] in frames:
                Rw = frames[w['bone']][0] @ Rw
            mc = mc @ Rw.T + palm
            wb = w['name']
            if wb not in order:
                order.append(wb); pivots[wb] = palm; rig_parent[wb] = w['bone']
                frames[wb] = (Rw, euler_zyx(Rw), palm)
            rig_tri = np.full(nt, wb, dtype=object)
        elif mesh_rig:
            rig_tri = np.full(nt, mesh_rig, dtype=object)
        else:
            vrig = np.array([rig_of(b) if b else rig_of(next(iter(anchors))) for b in vbone], dtype=object)
            # majority over the three corners (first corner wins ties)
            a, b, c = vrig[tv[:, 0]], vrig[tv[:, 1]], vrig[tv[:, 2]]
            rig_tri = np.where(b == c, b, a)
        mats = [s.material.name if s.material else '' for s in o.material_slots]
        tex_per_slot = []
        for mn in mats:
            tag = spec.get('tex_override', {}).get(mn.split('.')[0]) or material_texture(src_dir, mn)
            if tag is None:
                tex_per_slot.append(-1)
                continue
            if tag not in tex_ids:
                tex_ids[tag] = len(tex_arrays)
                tex_arrays.append(load_image(f'{src_dir}/TexturesDDS/{tag}.dds', img_cache))
            tex_per_slot.append(tex_ids[tag])
        tri_tex = np.array([tex_per_slot[m] if m < len(tex_per_slot) else -1 for m in tm]) if tex_per_slot else np.full(nt, -1)
        p3 = mc[tv]                                         # (nt,3,3)
        area = 0.5 * np.linalg.norm(np.cross(p3[:, 1] - p3[:, 0], p3[:, 2] - p3[:, 0]), axis=1)
        P.append(p3); UV.append(luv[tl]); TEX.append(tri_tex); BONE.append(rig_tri); AREA.append(area)
    s = Source()
    s.tris = np.concatenate(P); s.uv = np.concatenate(UV); s.tex = np.concatenate(TEX)
    s.bone = np.concatenate(BONE); s.area = np.concatenate(AREA)
    s.textures = tex_arrays; s.tex_tags = {v: k_ for k_, v in tex_ids.items()}
    for sub, rb in spec.get('mesh_bones', {}).items():
        if rb not in order:
            order.append(rb)
            sel = s.tris[s.bone == rb]
            pivots[rb] = sel.reshape(-1, 3).mean(0) if len(sel) else np.zeros(3)
            rig_parent[rb] = order[1] if len(order) > 1 else order[0]
    s.order, s.pivots, s.rig_parent, s.heads, s.src_parent = order, pivots, rig_parent, heads, parent
    for rb in obb_bones:
        sel = s.tris[s.bone == rb].reshape(-1, 3)
        if len(sel) >= 4:
            M = obb_frame(sel)
            if np.degrees(np.arccos(np.clip((np.trace(M) - 1) / 2, -1, 1))) > 4:
                frames[rb] = (M, euler_zyx(M), pivots[rb])
    s.frames = frames
    return s

# -------------------------------------------------------------------------------------------- colour
def texture_modes(src, spec):
    """Per texture: sample it ('tex') when it is a unique colour albedo; otherwise it is a tiling detail /
    dye-driven gray map and we grade it with a palette tint ('mul')."""
    modes = {}
    paint = spec.get('paint', {})
    for tid, arr in enumerate(src.textures):
        tag = src.tex_tags[tid]
        flat = arr.reshape(-1, 3)
        sat = float(rgb_to_hsv_sat(flat).mean())
        mode = paint.get(tag) or (('tex',) if sat > 0.12 else ('mul', spec.get('base_tint', DEVILS['metal'])))
        modes[tid] = tuple(mode) + (flat.mean(0),)
    return modes

LUMA = np.array([0.299, 0.587, 0.114])

def remap_value(c, target):
    """W300 r2 value pass: Minecraft display shading darkens textures further, so map the texture's own
    8..92 percentile luma range onto `target` (0..1), keeping hue and relative detail."""
    L = c @ LUMA
    lo, hi = np.percentile(L, 8), np.percentile(L, 92)
    f = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    newL = target[0] + f * (target[1] - target[0])
    out = c * (newL / np.maximum(L, 1e-3))[:, None]
    dark = L < 1e-3
    out[dark] = newL[dark, None]
    over = out.max(1)
    out /= np.maximum(over, 1.0)[:, None]           # keep hue when a channel would clip
    return out

def sample_surface(src, spec, spacing, rng):
    dens = 1.0 / (spacing * spacing)
    cnt = np.floor(src.area * dens + rng.random(len(src.area))).astype(np.int64)
    cnt = np.maximum(cnt, (src.area > 0).astype(np.int64))      # every triangle contributes once
    idx = np.repeat(np.arange(len(cnt)), cnt)
    r1 = np.sqrt(rng.random(len(idx))); r2 = rng.random(len(idx))
    w = np.stack([1 - r1, r1 * (1 - r2), r1 * r2], 1)
    pts = np.einsum('nk,nkd->nd', w, src.tris[idx])
    uvs = np.einsum('nk,nkd->nd', w, src.uv[idx])
    nrm = np.cross(src.tris[idx, 1] - src.tris[idx, 0], src.tris[idx, 2] - src.tris[idx, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    col = np.full((len(idx), 3), 0.4)
    modes = texture_modes(src, spec)
    tex = src.tex[idx]
    for tid, arr in enumerate(src.textures):
        m = tex == tid
        if not m.any():
            continue
        h, wd, _ = arr.shape
        u = np.mod(uvs[m, 0], 1.0); v = np.mod(uvs[m, 1], 1.0)
        c = arr[np.minimum((v * h).astype(int), h - 1), np.minimum((u * wd).astype(int), wd - 1)]
        mode = modes[tid]
        if mode[0] == 'mul':
            # palette colour sets the value; source detail only modulates it (+-20%)
            lum = c.mean(1, keepdims=True) / max(float(np.mean(mode[-1])), 0.05)
            c = np.array(mode[1])[None, :] * np.clip(0.8 + 0.4 * (lum - 0.5), 0.8, 1.2)
        elif mode[0] == 'flat':
            c = np.repeat(np.array(mode[1])[None, :], m.sum(), 0)
        else:
            c = remap_value(c, spec.get('tex_values', (0.33, 0.62)))
        col[m] = c
    col[tex < 0] = np.array(spec.get('base_tint', DEVILS['metal']))
    g = spec.get('grade', (1.18, 0.9))
    col = np.clip(np.power(np.clip(col, 0, 1), g[1]) * g[0], 0, 1)
    return pts, col, src.bone[idx], nrm

# ------------------------------------------------------------------------------------------ voxelise
def dilate(a):
    b = a.copy()
    b[1:] |= a[:-1]; b[:-1] |= a[1:]
    b[:, 1:] |= a[:, :-1]; b[:, :-1] |= a[:, 1:]
    b[:, :, 1:] |= a[:, :, :-1]; b[:, :, :-1] |= a[:, :, 1:]
    return b

def erode(a):
    return ~dilate(~a)

def solidify(surface):
    """Morphological closing + exterior flood fill -> solid occupancy (keeps thin surface features)."""
    pad = np.pad(surface, 2)
    closed = dilate(pad)
    ext = np.zeros_like(closed)
    ext[0, :, :] = ext[-1, :, :] = ext[:, 0, :] = ext[:, -1, :] = ext[:, :, 0] = ext[:, :, -1] = True
    ext &= ~closed
    while True:
        nxt = dilate(ext) & ~closed
        if (nxt == ext).all():
            break
        ext = nxt
    solid = erode(~ext) | pad
    return solid[2:-2, 2:-2, 2:-2]

def greedy_boxes(solid):
    best = None
    for perm in [(0, 1, 2), (2, 1, 0), (1, 0, 2), (0, 2, 1), (1, 2, 0), (2, 0, 1)]:
        g = np.transpose(solid, perm)
        used = np.zeros_like(g)
        boxes = []
        A, B, C = g.shape
        for a in range(A):
            for b in range(B):
                for c in range(C):
                    if not g[a, b, c] or used[a, b, c]:
                        continue
                    c2 = c + 1
                    while c2 < C and g[a, b, c2] and not used[a, b, c2]:
                        c2 += 1
                    b2 = b + 1
                    while b2 < B and g[a, b2, c:c2].all() and not used[a, b2, c:c2].any():
                        b2 += 1
                    a2 = a + 1
                    while a2 < A and g[a2, b:b2, c:c2].all() and not used[a2, b:b2, c:c2].any():
                        a2 += 1
                    used[a:a2, b:b2, c:c2] = True
                    lo = [a, b, c]; hi = [a2, b2, c2]
                    inv = np.argsort(perm)
                    boxes.append(([lo[i] for i in inv], [hi[i] for i in inv]))
        if best is None or len(boxes) < len(best):
            best = boxes
    return best

class BoneVox:
    pass

def voxelise(pts, col, bone, order, voxel, frames=None, min_pts=2):
    out = {}
    frames = frames or {}
    for rb in order:
        m = bone == rb
        if m.sum() == 0:
            continue
        P = pts[m]
        if rb in frames:
            M, _, o = frames[rb]
            P = (P - o) @ M + o
        c = np.floor(P / voxel).astype(np.int64)
        # occupancy only where the surface passes near the voxel centre -> ~1 voxel thick shells
        near = np.linalg.norm(P / voxel - (c + 0.5), axis=1) < 0.62
        if near.sum() >= 4:
            c_occ = c[near]
        else:
            c_occ = c
        lo = c.min(0) - 1
        hi = c.max(0) + 2
        shape = tuple(hi - lo)
        lin = np.ravel_multi_index((c_occ - lo).T, shape)
        u, n = np.unique(lin, return_counts=True)
        keep = u[n >= min_pts] if (n >= min_pts).sum() >= max(4, 0.25 * len(u)) else u
        surf = np.zeros(int(np.prod(shape)), dtype=bool); surf[keep] = True
        surf = surf.reshape(shape)
        if surf.sum() == 0:
            continue
        bv = BoneVox()
        bv.lo, bv.solid = lo, solidify(surf)
        bv.boxes = greedy_boxes(bv.solid)
        tree = kdtree.KDTree(len(P))
        for i, p in enumerate(P):
            tree.insert(p, i)
        tree.balance()
        bv.tree, bv.col = tree, col[m]
        bv.frame = frames.get(rb)
        out[rb] = bv
    return out

# --------------------------------------------------------------------------------------- atlas + faces
# name: (normal axis, on high side, u axis, u descending, v axis, v descending) — vanilla UV conventions
FACES = {'north': (2, False, 0, True, 1, True), 'south': (2, True, 0, False, 1, True),
         'east': (0, True, 2, True, 1, True), 'west': (0, False, 2, False, 1, True),
         'up': (1, True, 0, False, 2, False), 'down': (1, False, 0, False, 2, True)}

def shelf_pack(rects, size):
    """rects: list of (w, h). Returns positions or None. Tallest first, left-to-right shelves."""
    order = sorted(range(len(rects)), key=lambda i: (-rects[i][1], -rects[i][0]))
    pos = [None] * len(rects)
    x = y = shelf = 0
    for i in order:
        w, h = rects[i]
        if w > size:
            return None
        if x + w > size:
            y += shelf; x = 0; shelf = 0
        if y + h > size:
            return None
        pos[i] = (x, y); x += w; shelf = max(shelf, h)
    return pos

class Part:
    """One cube element: bone, from/to (px), faces {name: (cells_u, cells_v, painter) or None}."""
    def __init__(self, bone, frm, to, faces, glow=False, name='cube', rot=(0, 0, 0), origin=None):
        self.bone, self.frm, self.to, self.faces, self.glow, self.name = bone, frm, to, faces, glow, name
        self.rot = rot
        self.origin = np.asarray(origin if origin is not None else frm, dtype=np.float64)

EDGE_HIGHLIGHT = 1.24   # plate rims catch light (r2: was a darkening 0.80)
EDGE_CREASE = 0.80
VALUE_FLOOR = 0.24      # no baked texel below ~61/255

def vox_parts(rb, bv, voxel):
    parts = []
    S = bv.solid
    sh = np.array(S.shape)

    def solid_at(ix):
        if (ix < 0).any() or (ix >= sh).any():
            return False
        return bool(S[tuple(ix)])

    for lo, hi in bv.boxes:
        lo = np.array(lo); hi = np.array(hi)
        faces = {}
        for fname, (na, high, ua, udesc, va, vdesc) in FACES.items():
            nu, nv = hi[ua] - lo[ua], hi[va] - lo[va]
            layer = hi[na] - 1 if high else lo[na]
            out = hi[na] if high else lo[na] - 1
            visible = False
            cells = {}
            for cu in range(nu):
                for cv in range(nv):
                    vu = hi[ua] - 1 - cu if udesc else lo[ua] + cu
                    vv = hi[va] - 1 - cv if vdesc else lo[va] + cv
                    ix = np.zeros(3, dtype=np.int64); ix[na] = out; ix[ua] = vu; ix[va] = vv
                    hidden = solid_at(ix)
                    visible |= not hidden
                    # convex/concave edge flags for (u-, u+, v-, v+) in texture direction
                    flags = []
                    for axis, d in ((ua, -1 if not udesc else 1), (ua, 1 if not udesc else -1),
                                    (va, -1 if not vdesc else 1), (va, 1 if not vdesc else -1)):
                        nb = np.zeros(3, dtype=np.int64); nb[na] = layer; nb[ua] = vu; nb[va] = vv; nb[axis] += d
                        if not solid_at(nb):
                            flags.append(EDGE_HIGHLIGHT)
                        else:
                            nb[na] = out
                            flags.append(EDGE_CREASE if solid_at(nb) else 1.0)
                    cells[(cu, cv)] = flags
            if not visible:
                faces[fname] = None
                continue
            faces[fname] = (nu, nv, ('vox', rb, lo, hi, fname, cells))
        g_lo = (bv.lo + lo) * voxel
        g_hi = (bv.lo + hi) * voxel
        if bv.frame is not None:
            parts.append(Part(rb, g_lo, g_hi, faces, rot=bv.frame[1], origin=bv.frame[2]))
        else:
            parts.append(Part(rb, g_lo, g_hi, faces))
    return parts

SMOOTH_N = 6

def paint_plate(img, x0, y0, painter):
    """r3 authored plate: bevel highlight (top/left rim bright, bottom/right dark), panel seams on large
    faces, corner rivets, low grime toward the bottom and deterministic per-face noise."""
    _, rgb, seed, w, h, seams = painter
    rng = np.random.default_rng(seed)
    base = np.array(rgb, float)
    tile = np.ones((h, w))
    tile *= 1 + rng.normal(0, 0.045, (h, w))
    tile *= np.linspace(1.04, 0.90, h)[:, None]              # grime toward the bottom
    if seams:
        for x in range(9, w - 4, 10):
            tile[:, x] *= 0.74
        for y in range(9, h - 4, 10):
            tile[y, :] *= 0.74
    tile[0, :] *= 1.30; tile[:, 0] *= 1.14                   # lit rim
    tile[-1, :] *= 0.70; tile[:, -1] *= 0.84                 # shadow rim
    if w >= 8 and h >= 8:
        for (x, y) in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
            tile[y, x] *= 1.38
    if w >= 10 and h >= 10:                                  # scratches
        for _ in range(max(1, (w * h) // 220)):
            x, y = rng.integers(1, w - 1), rng.integers(1, h - 1)
            tile[y, x:min(w - 1, x + rng.integers(2, 5))] *= 1.22
    img[y0:y0 + h, x0:x0 + w, :3] = np.clip(base[None, None, :] * tile[:, :, None], 0, 1) * 255
    img[y0:y0 + h, x0:x0 + w, 3] = 255

def paint_face(img, x0, y0, k, painter, vox, voxel):
    kind = painter[0]
    if kind == 'paint':
        paint_cell(img, x0, y0, painter)
        return
    if kind == 'plate':
        paint_plate(img, x0, y0, painter)
        return
    if kind == 'panel':
        _, rgb, edge, w, h = painter
        base = np.array(rgb)
        img[y0:y0 + h, x0:x0 + w, :3] = base * edge * 255
        img[y0 + 1:y0 + h - 1, x0 + 1:x0 + w - 1, :3] = base * 255
        img[y0:y0 + h, x0:x0 + w, 3] = 255
        return
    if kind == 'flat':
        _, rgb, w, h = painter
        img[y0:y0 + h, x0:x0 + w, :3] = np.array(rgb) * 255
        img[y0:y0 + h, x0:x0 + w, 3] = 255
        return
    _, rb, lo, hi, fname, cells = painter
    bv = vox[rb]
    na, high, ua, udesc, va, vdesc = FACES[fname]
    glo = bv.lo + lo; ghi = bv.lo + hi
    nu, nv = hi[ua] - lo[ua], hi[va] - lo[va]
    nval = (ghi[na] if high else glo[na]) * voxel + (0.25 if high else -0.25) * voxel
    for cu in range(nu):
        for cv in range(nv):
            flags = cells[(cu, cv)]
            for si in range(k):
                for sj in range(k):
                    fu = (cu * k + si + 0.5) / k
                    fv = (cv * k + sj + 0.5) / k
                    p = np.zeros(3)
                    p[na] = nval
                    p[ua] = (ghi[ua] - fu) * voxel if udesc else (glo[ua] + fu) * voxel
                    p[va] = (ghi[va] - fv) * voxel if vdesc else (glo[va] + fv) * voxel
                    near = bv.tree.find_n(p, SMOOTH_N)
                    ws = np.array([1.0 / (0.15 * voxel + d) for _, _, d in near])
                    c = (bv.col[[i for _, i, _ in near]] * ws[:, None]).sum(0) / ws.sum()
                    shade = 1.0
                    if k >= 2:
                        if si == 0: shade *= flags[0]
                        if si == k - 1: shade *= flags[1]
                        if sj == 0: shade *= flags[2]
                        if sj == k - 1: shade *= flags[3]
                    c = c * shade
                    L = float(c @ LUMA)
                    if L < VALUE_FLOOR:
                        c = c + (VALUE_FLOOR - L)
                    img[y0 + cv * k + sj, x0 + cu * k + si, :3] = np.clip(c, 0, 1) * 255
                    img[y0 + cv * k + sj, x0 + cu * k + si, 3] = 255

def bake_atlas(parts, vox, voxel, tex_max, kmax=4):
    faces = [(pi, fn, f) for pi, p in enumerate(parts) for fn, f in p.faces.items() if f is not None]
    for k in range(kmax, 0, -1):
        rects = []
        for pi, fn, (nu, nv, painter) in faces:
            if painter[0] == 'flat':
                rects.append((2, 2))
            elif painter[0] == 'panel':
                rects.append((4, 4))
            elif painter[0] in ('plate', 'paint'):
                rects.append((painter[3], painter[4]))
            else:
                rects.append((nu * k, nv * k))
        area = sum(w * h for w, h in rects)
        size = 16
        while size * size < area * 1.08:
            size *= 2
        pos = None
        while size <= tex_max:
            pos = shelf_pack(rects, size)
            if pos:
                break
            size *= 2
        if pos:
            break
    if not pos:
        raise RuntimeError('atlas does not fit; raise voxel size')
    img = np.zeros((size, size, 4), dtype=np.float64)
    uvs = {}
    for (pi, fn, (nu, nv, painter)), (x, y), (w, h) in zip(faces, pos, rects):
        if painter[0] == 'flat':
            paint_face(img, x, y, k, ('flat', painter[1], w, h), vox, voxel)
            uvs[(pi, fn)] = [x + 0.5, y + 0.5, x + 1.5, y + 1.5]
        elif painter[0] == 'panel':
            paint_face(img, x, y, k, ('panel', painter[1], painter[2], w, h), vox, voxel)
            uvs[(pi, fn)] = [x, y, x + w, y + h]
        elif painter[0] in ('plate', 'paint'):
            paint_face(img, x, y, k, painter, vox, voxel)
            uvs[(pi, fn)] = [x, y, x + w, y + h]
        else:
            paint_face(img, x, y, k, painter, vox, voxel)
            uvs[(pi, fn)] = [x, y, x + w, y + h]
    return np.clip(img, 0, 255).astype(np.uint8), uvs, k, size

# ------------------------------------------------------------------------------------------ bbmodel
class Clip:
    def __init__(self, name, length, loop):
        self.name, self.length, self.loop = name, float(length), loop
        self.tracks = {}

    def key(self, bone, channel, t, v, interp='catmullrom'):
        self.tracks.setdefault(bone, {}).setdefault(channel, []).append((float(t), tuple(float(x) for x in v), interp))
        return self

    def curve(self, bone, channel, fn, n=8, interp='catmullrom'):
        """Sample fn(phase 0..1) -> xyz at n+1 keys (loop safe: last == first when fn is periodic)."""
        for i in range(n + 1):
            f = i / n
            self.key(bone, channel, f * self.length, fn(f), interp)
        return self

def write_bbmodel(name, bones, parts, img, uvs, size, clips, meta):
    g_uuid = {b['name']: uid(name, 'group', b['name']) for b in bones}
    elements = []
    children = {b['name']: [] for b in bones}
    for pi, p in enumerate(parts):
        e_uuid = uid(name, 'el', pi)
        faces = {}
        for fn in FACES:
            f = p.faces.get(fn)
            if f is None:
                faces[fn] = {'uv': [0, 0, 0, 0], 'texture': None}
            else:
                faces[fn] = {'uv': [r4(x) for x in uvs[(pi, fn)]], 'texture': 0}
        el = {'name': p.name, 'box_uv': False, 'rescale': False, 'locked': False, 'render_order': 'default',
              'allow_mirror_modeling': True, 'from': [r4(x) for x in p.frm], 'to': [r4(x) for x in p.to],
              'autouv': 0, 'color': pi % 8, 'origin': [r4(x) for x in p.origin], 'rotation': [r4(x) for x in p.rot],
              'faces': faces, 'type': 'cube', 'uuid': e_uuid}
        if p.glow:
            el['light_emission'] = 15
        elements.append(el)
        children[p.bone].append(e_uuid)
    groups = []
    for b in bones:
        g = {'name': b['name'], 'origin': [r4(x) for x in b['origin']], 'rotation': [0, 0, 0], 'color': 0,
             'uuid': g_uuid[b['name']], 'export': True, 'mirror_uv': False, 'isOpen': False, 'locked': False,
             'visibility': True, 'autouv': 0, 'selected': False, 'children': []}
        if b.get('glow'):
            g['light_emission'] = 15
        groups.append(g)

    def outline(bname):
        return {'uuid': g_uuid[bname], 'isOpen': False,
                'children': children[bname] + [outline(c['name']) for c in bones if c.get('parent') == bname]}
    outliner = [outline(b['name']) for b in bones if not b.get('parent')]
    animations = []
    for clip in clips:
        animators = {}
        for bone, chans in clip.tracks.items():
            kfs = []
            for ch, keys in chans.items():
                for t, v, interp in sorted(keys, key=lambda k: k[0]):
                    kfs.append({'channel': ch, 'data_points': [{'x': r4(v[0]), 'y': r4(v[1]), 'z': r4(v[2])}],
                                'uuid': uid(name, clip.name, bone, ch, t), 'time': r4(t), 'color': -1,
                                'interpolation': interp})
            animators[g_uuid[bone]] = {'name': bone, 'type': 'bone', 'rotation_global': False,
                                       'quaternion_interpolation': False, 'keyframes': kfs}
        animations.append({'uuid': uid(name, 'anim', clip.name), 'name': clip.name, 'loop': clip.loop,
                           'override': False, 'length': r4(clip.length), 'snapping': 20, 'selected': False,
                           'anim_time_update': '', 'blend_weight': '', 'start_delay': '', 'loop_delay': '',
                           'animators': animators})
    model = {
        'meta': {'format_version': '5.0', 'model_format': 'free', 'box_uv': False},
        'name': name, 'model_identifier': name,
        'credit': meta.get('credit', ''),
        'visible_box': [1, 1, 0], 'variable_placeholders': '', 'variable_placeholder_buttons': [],
        'timeline_setups': [], 'unhandled_root_fields': {},
        'w300': meta,
        'resolution': {'width': size, 'height': size},
        'elements': elements, 'groups': groups, 'outliner': outliner,
        'textures': [{'path': '', 'name': name + '.png', 'folder': '', 'namespace': '', 'id': '0', 'group': '',
                      'width': size, 'height': size, 'uv_width': size, 'uv_height': size, 'particle': False,
                      'use_as_default': False, 'layers_enabled': False, 'sync_to_project': '',
                      'render_mode': 'default', 'render_sides': 'auto', 'frame_time': 1,
                      'frame_order_type': 'loop', 'frame_order': '', 'frame_interpolate': False,
                      'visible': True, 'internal': True, 'saved': False, 'uuid': uid(name, 'texture'),
                      'source': 'data:image/png;base64,' + base64.b64encode(png_bytes(img)).decode()}],
        'animations': animations,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name + '.bbmodel')
    with open(path, 'w') as f:
        json.dump(model, f, separators=(',', ':'))
    return path, model

# ------------------------------------------------------------------------------------------ review
VIEWS = {'front': (0, 1, 0.12), 'q34': (0.75, 0.8, 0.45), 'side': (1, 0, 0.08), 'back': (-0.5, -1, 0.3)}

def setup_render(res=480):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'TEXTURE'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = res
    cam = bpy.data.cameras.new('review'); cam.type = 'ORTHO'
    co = bpy.data.objects.new('review', cam); sc.collection.objects.link(co); sc.camera = co
    return sc, cam, co

def render_views(prefix, objs, views=VIEWS, res=480, bounds=None):
    sc, cam, co = setup_render(res)
    if bounds is None:
        pts = []
        for o in objs:
            if o.type == 'MESH':
                pts += [o.matrix_world @ v.co for v in o.data.vertices]
        lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    else:
        lo, hi = bounds
    ctr = (lo + hi) / 2; size = max(hi - lo) * 1.12
    cam.ortho_scale = size; cam.clip_start = size * 0.01; cam.clip_end = size * 30
    out = []
    for tag, d in views.items():
        dv = Vector(d).normalized()
        co.location = ctr + dv * size * 4
        co.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{prefix}_{tag}.png'
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
    return out, (lo, hi)

def assign_source_textures(src_dir):
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            mat = slot.material
            if not mat or not mat.node_tree:
                continue
            tag = material_texture(src_dir, mat.name)
            if not tag:
                continue
            img = bpy.data.images.load(f'{src_dir}/TexturesDDS/{tag}.dds', check_existing=True)
            img.alpha_mode = 'NONE'
            n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img
            bsdf = [x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED']
            if bsdf:
                mat.node_tree.links.new(n.outputs[0], bsdf[0].inputs['Base Color'])

def render_source(name, spec, ev):
    """Source review in the same frame as the cube review (front -> +Y blender)."""
    src_dir = f"{SRC}/{spec['src']}"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f"{src_dir}/{spec['src']}.fbx")
    R = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(100 * spec['px_per_m'] / 16, 4)
    for o in list(bpy.data.objects):
        if o.parent is None:
            o.matrix_world = R @ o.matrix_world
    bpy.context.view_layer.update()
    keep = set(spec['include'])
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o.name.split('_')[0] not in keep or 'InternalGeom' in o.name
    assign_source_textures(src_dir)
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.hide_render:
            m = o.evaluated_get(dg).to_mesh()
            pts += [o.matrix_world @ v.co for v in m.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return render_views(f'{ev}/{name}_source', [], bounds=(lo, hi))

def mc_to_bl(p):
    return Vector((p[0] / 16, -p[2] / 16, p[1] / 16))

def build_preview_objects(name, parts, uvs, size, png_path, bones):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    img = bpy.data.images.load(png_path)
    img.alpha_mode = 'NONE'
    mat = bpy.data.materials.new('atlas'); mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Closest'
    bsdf = [x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'][0]
    mat.node_tree.links.new(tex.outputs[0], bsdf.inputs['Base Color'])
    objs = {}
    for b in bones:
        verts, polys, puv = [], [], []
        for pi, p in enumerate(parts):
            if p.bone != b['name']:
                continue
            f, t = p.frm, p.to
            corners = {}
            for fn, (na, high, ua, udesc, va, vdesc) in FACES.items():
                if (pi, fn) not in uvs:
                    continue
                u0, v0, u1, v1 = uvs[(pi, fn)]
                # quad corners in texture order: (u0,v0) (u1,v0) (u1,v1) (u0,v1)
                quad = []
                for (uu, vv) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    q = np.zeros(3)
                    q[na] = t[na] if high else f[na]
                    q[ua] = (t[ua] if not udesc else f[ua]) if uu else (f[ua] if not udesc else t[ua])
                    q[va] = (t[va] if not vdesc else f[va]) if vv else (f[va] if not vdesc else t[va])
                    quad.append(q)
                base = len(verts)
                Mp = rot_zyx(p.rot)
                quad = [Mp @ (q - p.origin) + p.origin for q in quad]
                verts += [mc_to_bl(q) for q in quad]
                face = [base, base + 1, base + 2, base + 3]
                # keep outward winding: test normal
                nrm = np.cross(quad[1] - quad[0], quad[3] - quad[0])
                want = np.zeros(3); want[na] = 1 if high else -1
                want = Mp @ want
                nb = np.array([nrm[0], -nrm[2], nrm[1]])
                wb = np.array([want[0], -want[2], want[1]])
                if np.dot(nb, wb) < 0:
                    face = face[::-1]
                    tuv = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
                else:
                    tuv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
                polys.append(face)
                puv += [(u / size, 1 - v / size) for (u, v) in tuv]
        if not verts:
            continue
        me = bpy.data.meshes.new(b['name']); me.from_pydata([tuple(v) for v in verts], [], polys)
        uvl = me.uv_layers.new()
        for li, uvv in enumerate(puv):
            uvl.data[li].uv = uvv
        me.materials.append(mat)
        o = bpy.data.objects.new(b['name'], me); bpy.context.scene.collection.objects.link(o)
        objs[b['name']] = o
    return objs

# ------------------------------------------------------------------------------------------ build
def build_source_model(name, spec, ev, log):
    t0 = time.time()
    src = extract(name, spec)
    rng = np.random.default_rng(int(hashlib.sha1(name.encode()).hexdigest()[:8], 16))
    voxel = spec['voxel']
    lo_b, hi_b = spec['budget']
    decor_count = spec.get('decor_estimate', 16)
    for attempt in range(10):
        pts, col, bone, nrm = sample_surface(src, spec, voxel / 2.4, rng)
        vox = voxelise(pts, col, bone, src.order, voxel, src.frames)
        parts = []
        for rb in src.order:
            if rb in vox:
                parts += vox_parts(rb, vox[rb], voxel)
        total = len(parts) + decor_count
        log(f'{name}: voxel {voxel:.3f}px -> {total} elements')
        if total > hi_b:
            voxel *= 1.1 if total < hi_b * 1.3 else 1.22
        elif total < lo_b and voxel > spec['voxel'] * 0.55:
            voxel /= 1.12
        else:
            break
    bones = [{'name': rb, 'parent': src.rig_parent.get(rb), 'origin': src.pivots[rb]} for rb in src.order]
    decor_parts, decor_bones = family_decor(name, spec, src, vox, voxel)
    bones += decor_bones
    parts += decor_parts
    img, uvs, k, size = bake_atlas(parts, vox, voxel, spec['tex_max'])
    clips = family_clips(name, spec, src, bones)
    meta = {'generator': GENERATOR, 'source': spec['src'], 'source_entities': spec['include'],
            'weapons': [w['entity'] for w in spec.get('weapons', [])],
            'voxel_px': round(voxel, 4), 'texels_per_voxel': k, 'px_per_meter': spec['px_per_m'],
            'animations': 'original authored (extraction contains no clips)',
            'credit': 'Geometry/colour derived from extracted Destiny asset ' + spec['src'] + '; cube redesign + animations authored for W300'}
    path, model = write_bbmodel(name, bones, parts, img, uvs, size, clips, meta)
    png = f'{ev}/{name}_atlas.png'
    open(png, 'wb').write(png_bytes(img))
    stats = dict(name=name, elements=len(parts), bones=len(bones), voxel=round(voxel, 3), k=k, texture=size,
                 seconds=round(time.time() - t0, 1), clips=[c.name for c in clips])
    log(json.dumps(stats))
    return path, parts, uvs, size, png, bones, clips, stats


# ------------------------------------------------------------------------------------------ authored
PLATE_TEXELS_PER_PX = 0.5

def box(bone, center, size, colors, M=None, glow=False, edge=0.78, name='cube', style='panel'):
    """Authored cube centred at `center` (px), optional rotation matrix M about its centre.
    colors: rgb or {face: rgb}. style 'panel' = bevelled 4x4 texture; 'plate' = size-proportional
    detailed plate texture (r3 walker)."""
    c = np.asarray(center, dtype=np.float64); h = np.asarray(size, dtype=np.float64) / 2
    faces = {}
    for fn in FACES:
        rgb = colors[fn] if isinstance(colors, dict) else colors
        if rgb is None:
            faces[fn] = None
        elif style == 'plate' and not glow:
            na, high, ua, udesc, va, vdesc = FACES[fn]
            tw = int(np.clip(round(size[ua] * PLATE_TEXELS_PER_PX), 3, 36))
            th = int(np.clip(round(size[va] * PLATE_TEXELS_PER_PX), 3, 36))
            seed = int(hashlib.sha1(f'{bone}{center}{size}{fn}'.encode()).hexdigest()[:8], 16)
            faces[fn] = (1, 1, ('plate', tuple(rgb), seed, tw, th, min(tw, th) >= 14))
        else:
            faces[fn] = (1, 1, ('panel', tuple(rgb), edge))
    rot = euler_zyx(M) if M is not None else (0, 0, 0)
    return Part(bone, c - h, c + h, faces, glow=glow, name=name, rot=rot, origin=c)

def axes_matrix(ex, ey, ez):
    M = np.stack([np.asarray(ex, float), np.asarray(ey, float), np.asarray(ez, float)], 1)
    M /= np.linalg.norm(M, axis=0, keepdims=True)
    if np.linalg.det(M) < 0:
        M[:, 2] *= -1
    return M

def finish_authored(name, spec, ev, log, bones, parts, clips, meta):
    img, uvs, k, size = bake_atlas(parts, {}, 1.0, spec['tex_max'], kmax=1)
    path, model = write_bbmodel(name, bones, parts, img, uvs, size, clips, meta)
    png = f'{ev}/{name}_atlas.png'
    open(png, 'wb').write(png_bytes(img))
    stats = dict(name=name, elements=len(parts), bones=len(bones), texture=size, clips=[c.name for c in clips])
    log(json.dumps(stats))
    return path, parts, uvs, size, png, bones, clips, stats

GHOST_PETALS = {}

GHOST_PAL = dict(dark=(0.24, 0.25, 0.27), mid=(0.42, 0.43, 0.45), light=(0.76, 0.77, 0.78),
                 orange=(0.88, 0.47, 0.13), white=(0.93, 0.96, 1.0), socket=(0.07, 0.07, 0.08),
                 iris=(0.55, 0.86, 1.0))

def build_ghost(name, spec, ev, log):
    """Generalist Shell rebuilt from rotated plates (voxelising its pyramid petals stair-steps badly).
    Proportions measured from Ghost__80CFD3CB (8 petal bones, core, eye mesh); colours from its albedo."""
    P = GHOST_PAL
    bones = [dict(name='root', parent=None, origin=(0, 0, 0)),
             dict(name='body', parent='root', origin=(0, 0, 0)),
             dict(name='core', parent='body', origin=(0, 0, 0)),
             dict(name='eye', parent='core', origin=(0, 0, -2.6)),
             dict(name='eye_glow', parent='eye', origin=(0, 0, -2.6), glow=True),
             dict(name='shell', parent='body', origin=(0, 0, 0))]
    parts = []
    C = np.array([0.0, 0.0, 0.0])
    # core: rounded dark sphere
    parts += [box('core', C, (4.2, 4.2, 4.2), P['dark']),
              box('core', C, (5.0, 3.0, 3.0), P['mid']), box('core', C, (3.0, 5.0, 3.0), P['mid']),
              box('core', C, (3.0, 3.0, 4.8), P['dark']),
              box('core', C + (0, 0, 0), (5.6, 0.5, 5.6), P['socket'])]            # equator seam
    # eye (front = -Z): socket, white, iris glow
    parts += [box('core', C + (0, 0, -2.45), (3.8, 3.8, 0.6), P['socket']),
              box('eye_glow', C + (0, 0, -2.75), (2.8, 1.8, 0.5), P['white'], glow=True),
              box('eye_glow', C + (0, 0, -2.75), (1.8, 2.8, 0.5), P['white'], glow=True),
              box('eye_glow', C + (0, 0, -3.05), (1.2, 1.2, 0.3), P['iris'], glow=True)]
    a, t, dist = 4.3, 1.5, 3.5
    for side, sz in (('a', -1.0), ('b', 1.0)):                 # a = eye side (front)
        for pname, d in (('top', (0, 1)), ('bottom', (0, -1)), ('left', (-1, 0)), ('right', (1, 0))):
            bone = f'shell_{side}_{pname}'
            r3 = np.array([d[0], d[1], 0.0]); dz = np.array([0.0, 0.0, sz])
            g = (r3 + dz) / math.sqrt(2)                       # tip direction
            n = (r3 - dz) / math.sqrt(2)                       # plate normal (+Y local): outer/back face
            e = np.cross(g, n)
            GHOST_PETALS[bone] = (g, n, e, r3)
            bones.append(dict(name=bone, parent='shell', origin=tuple(C + g * 1.2)))   # hinge near the core
            u1 = (g + e) / math.sqrt(2); u2 = (g - e) / math.sqrt(2)
            M = axes_matrix(u1, n, u2)
            centre = C + g * dist
            # -n face looks along the eye axis (front petals) -> shell colour; +n face -> lighter facet
            cols = {'down': P['dark'], 'up': P['light'], 'north': P['mid'], 'south': P['mid'],
                    'east': P['mid'], 'west': P['mid']}
            parts.append(box(bone, centre, (a, t, a), cols, M=M))
            parts.append(box(bone, centre - n * (t / 2 + 0.1) - g * 0.4, (a * 0.58, 0.22, a * 0.58),
                             {f: P['mid'] for f in FACES}, M=M))
            parts.append(box(bone, C + g * (dist + a / math.sqrt(2) - 0.55), (0.9, t * 1.06, 0.9), P['orange'], M=M))
    clips = ghost_clips(bones)
    meta = {'generator': GENERATOR, 'source': spec['src'], 'geometry': 'authored plates from source proportions',
            'animations': 'original authored (extraction contains no clips)',
            'credit': 'Generalist Shell proportions/colours from extracted Ghost__80CFD3CB; cube rebuild + animations authored for W300'}
    return finish_authored(name, spec, ev, log, bones, parts, clips, meta)

SHIP_PAL = dict(hull=(0.84, 0.84, 0.82), panel=(0.66, 0.67, 0.67), dark=(0.30, 0.31, 0.33), glass=(0.16, 0.26, 0.34),
                stripe=(0.80, 0.30, 0.12), metal=(0.42, 0.43, 0.45), glow=(0.62, 0.88, 1.0), lamp=(1.0, 0.55, 0.25))

def build_ship(name, spec, ev, log):
    """ORIGINAL authored jumpship: the extraction contains no player ship (Dock 13 placements are Fallen
    and Shanks; 'sq_ship' labels refer to the Fallen skiff). Length ~10 blocks, front = -Z."""
    P = SHIP_PAL
    bones = [dict(name='root', parent=None, origin=(0, 0, 0)),
             dict(name='body', parent='root', origin=(0, 40, 0)),
             dict(name='canopy', parent='body', origin=(0, 50, -40)),
             dict(name='wing_l', parent='body', origin=(-14, 38, 4)),
             dict(name='wing_r', parent='body', origin=(14, 38, 4)),
             dict(name='engine_l', parent='body', origin=(-12, 40, 48)),
             dict(name='engine_r', parent='body', origin=(12, 40, 48)),
             dict(name='engine_l_glow', parent='engine_l', origin=(-12, 40, 66), glow=True),
             dict(name='engine_r_glow', parent='engine_r', origin=(12, 40, 66), glow=True),
             dict(name='lights_glow', parent='body', origin=(0, 40, 0), glow=True),
             dict(name='gear_f', parent='body', origin=(0, 30, -42)),
             dict(name='gear_l', parent='body', origin=(-12, 30, 30)),
             dict(name='gear_r', parent='body', origin=(12, 30, 30))]
    parts = []
    B = lambda *a, **k: parts.append(box(*a, **k))
    # fuselage: stepped nose -> body -> tail block (z from -78 nose to +56 tail)
    for i, (z0, z1, w, h, yc) in enumerate([(-78, -66, 6, 5, 40), (-66, -52, 10, 8, 40.5), (-52, -36, 14, 11, 41),
                                            (-36, -10, 18, 13, 41.5), (-10, 24, 22, 14, 41.5), (24, 46, 20, 13, 41)]):
        zc = (z0 + z1) / 2
        B('body', (0, yc, zc), (w, h, z1 - z0), {'up': P['hull'], 'down': P['dark'], 'north': P['panel'],
                                                 'south': P['panel'], 'east': P['hull'], 'west': P['hull']})
        B('body', (0, yc + h / 2 + 0.6, zc), (w * 0.55, 1.2, (z1 - z0) - 2), P['panel'])
    B('body', (0, 41, 54), (16, 12, 16), P['metal'])                                   # aft block
    B('body', (0, 49.5, 30), (3, 9, 22), P['hull'])                                    # dorsal fin
    B('body', (0, 55, 38), (2.2, 4, 10), P['stripe'])
    for x in (-1, 1):                                                                  # side stripes
        B('body', (x * 11.1, 41, 4), (0.4, 2, 34), P['stripe'])
        B('body', (x * 9.2, 41, -23), (0.4, 1.6, 24), P['stripe'])
    B('body', (0, 34, -4), (12, 2, 44), P['dark'])                                     # belly keel
    # canopy
    B('canopy', (0, 48.5, -40), (9, 4, 18), {'up': P['glass'], 'north': P['glass'], 'east': P['glass'],
                                              'west': P['glass'], 'south': P['dark'], 'down': P['dark']})
    B('canopy', (0, 47.5, -51), (6, 2.5, 6), P['glass'])
    B('canopy', (0, 50.8, -38), (9.4, 0.6, 2), P['metal'])
    # swept wings (stepped trailing sweep) + wingtip pods
    for side, x in (('l', -1), ('r', 1)):
        wb = f'wing_{side}'
        for j, (x0, x1, z0, z1) in enumerate([(11, 22, -14, 26), (22, 33, -4, 30), (33, 44, 6, 34), (44, 52, 16, 36)]):
            B(wb, (x * (x0 + x1) / 2, 38 - j * 0.6, (z0 + z1) / 2), (x1 - x0, 2.4 - j * 0.3, z1 - z0),
              {'up': P['hull'], 'down': P['panel'], 'north': P['metal'], 'south': P['metal'], 'east': P['panel'], 'west': P['panel']})
        B(wb, (x * 30, 39.6, 14), (14, 0.6, 3), P['stripe'])
        B(wb, (x * 53, 37, 22), (3, 4, 20), P['metal'])                                # tip pod
        B(wb, (x * 53, 37, 10.5), (2, 2.4, 3), P['dark'])
        parts.append(box('lights_glow', (x * 54.6, 37, 13), (0.8, 1.2, 1.2), P['lamp'], glow=True))
        # engine nacelle
        eb = f'engine_{side}'
        B(eb, (x * 12, 40, 40), (10, 10, 28), {'up': P['hull'], 'down': P['dark'], 'north': P['metal'],
                                                'south': P['dark'], 'east': P['panel'], 'west': P['panel']})
        B(eb, (x * 12, 40, 56), (12, 12, 8), P['metal'])
        B(eb, (x * 12, 40, 61), (9, 9, 2), P['dark'])
        B(eb, (x * 12, 46, 36), (6, 2, 18), P['stripe'])
        parts.append(box(f'engine_{side}_glow', (x * 12, 40, 62.4), (7, 7, 1.2), P['glow'], glow=True))
        parts.append(box(f'engine_{side}_glow', (x * 12, 40, 63.4), (4, 4, 1.0), (0.9, 0.97, 1.0), glow=True))
        # gear
        gb = f'gear_{side}'
        B(gb, (x * 12, 30, 30), (2, 8, 2), P['metal'])
        B(gb, (x * 12, 26.5, 30), (4, 1.6, 6), P['dark'])
    B('gear_f', (0, 30.5, -42), (2, 7, 2), P['metal'])
    B('gear_f', (0, 27, -42), (3.2, 1.6, 5), P['dark'])
    parts.append(box('lights_glow', (0, 42, -79), (2.2, 1.6, 1.0), P['lamp'], glow=True))
    clips = ship_clips(bones)
    meta = {'generator': GENERATOR, 'source': 'none (original authored jumpship)',
            'animations': 'original authored', 'credit': 'Original jumpship design authored for W300 (no player ship in extraction)'}
    return finish_authored(name, spec, ev, log, bones, parts, clips, meta)

# ------------------------------------------------------------------------------------------ families
def local_R(v):
    """Blockbench animation rotation (bedrock convention: x/y negated) -> matrix."""
    return rot_zyx((-v[0], -v[1], v[2]))

def anim_of(R):
    ex, ey, ez = euler_zyx(R)
    return (-ex, -ey, ez)

def rot_between(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    a /= np.linalg.norm(a); b /= np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-8:
        return np.eye(3) if c > 0 else rot_zyx((180, 0, 0))
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))

def nrm(*v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)

def mir(v):
    return np.array([-v[0], v[1], v[2]])

class Rig:
    def __init__(self, bones, rest_axes):
        self.parent = {b['name']: b.get('parent') for b in bones}
        self.order = [b['name'] for b in bones]
        self.rest = rest_axes

    def world_R(self, pose, bone):
        R = np.eye(3); chain = []
        b = bone
        while b is not None:
            chain.append(b); b = self.parent.get(b)
        for b in reversed(chain):
            R = R @ local_R(pose.get(b, (0, 0, 0)))
        return R

    def aim(self, pose, bone, target):
        p = self.parent.get(bone)
        Rp = self.world_R(pose, p) if p else np.eye(3)
        R = rot_between(self.rest.get(bone, (0, -1, 0)), Rp.T @ np.asarray(target, float))
        pose[bone] = anim_of(R)

def keyframe_pose(clip, t, pose, pos=None, scale=None, bones=None, interp='catmullrom'):
    for b, v in pose.items():
        if bones is None or b in bones:
            clip.key(b, 'rotation', t, v, interp)
    for b, v in (pos or {}).items():
        clip.key(b, 'position', t, v, interp)
    for b, v in (scale or {}).items():
        clip.key(b, 'scale', t, v, interp)

# ----------------------------------------------------------------------------------- fallen infantry
FALLEN_STYLE = {
    # lean deg, crouch px, walk period s, stride deg, bob px, run period, two-handed weapon
    'dreg': dict(lean=14, crouch=0.6, walk=0.8, stride=26, bob=0.7, run=0.5, two=False, blade='farm_ul', jitter=1.0),
    'vandal': dict(lean=22, crouch=1.2, walk=1.0, stride=24, bob=0.6, run=0.6, two=True, blade='farm_lr', jitter=0.4),
    'captain': dict(lean=9, crouch=0.8, walk=1.15, stride=22, bob=1.0, run=0.7, two=False, blade='farm_lr', jitter=0.2),
}

def fallen_pose(rig, st, lean=None, gait=None, stride=0.0, weapon='low', head=(0, 0), crouch=None, twist=0.0,
                free=0.0, blade=None, recoil=0.0, extra=None):
    """Compose one Fallen pose. gait = phase 0..1 (None = stand). Directions in model space (front -Z)."""
    lean = st['lean'] if lean is None else lean
    crouch = st['crouch'] if crouch is None else crouch
    pose, pos = {}, {}
    ph = 2 * math.pi * (gait or 0.0)
    swing = math.cos(ph) * stride if gait is not None else 0.0
    pose['hips'] = (0, (4 * math.cos(ph) if gait is not None else 0) + twist * 0.3, 0)
    bob = -crouch - (st['bob'] * (0.5 + 0.5 * math.cos(2 * ph)) if gait is not None else 0)
    pos['hips'] = (0, bob, 0)
    for side, sg, off in (('l', 1, 0.0), ('r', -1, math.pi)):
        a = math.cos(ph + off) * stride if gait is not None else 0.0
        lift = max(0.0, -math.sin(ph + off)) * (stride * 1.5) if gait is not None else 0.0
        pose[f'thigh_{side}'] = (-a - 6 - crouch * 4, 0, 0)
        pose[f'shin_{side}'] = (10 + crouch * 6 + lift, 0, 0)
    pose['torso'] = (lean, -twist - (3 * math.cos(ph) if gait is not None else 0), 0)
    pose['head'] = (head[0] - lean * 0.6, head[1], 0)
    # weapon arm (upper right pair)
    if weapon == 'aim' or weapon == 'recoil':
        rk = recoil
        rig.aim(pose, 'uarm_ur', nrm(0.18, -0.30 + 0.15 * rk, -1.0))
        rig.aim(pose, 'farm_ur', nrm(-0.06, 0.02 + 0.35 * rk, -1.0))
    elif weapon == 'run':
        rig.aim(pose, 'uarm_ur', nrm(0.30, -0.95, -0.15))
        rig.aim(pose, 'farm_ur', nrm(0.1, 0.25, -1.0))
    else:
        rig.aim(pose, 'uarm_ur', nrm(0.28, -0.95, -0.05 - 0.15 * free))
        rig.aim(pose, 'farm_ur', nrm(0.0, -0.45, -1.0))
    if st['two'] and weapon != 'run':
        if weapon in ('aim', 'recoil'):
            rig.aim(pose, 'uarm_ul', nrm(-0.25, -0.55, -0.85))
            rig.aim(pose, 'farm_ul', nrm(0.55, 0.05 + 0.3 * recoil, -1.0))
        else:
            rig.aim(pose, 'uarm_ul', nrm(-0.22, -0.95, -0.15))
            rig.aim(pose, 'farm_ul', nrm(0.55, -0.35, -1.0))
    else:
        rig.aim(pose, 'uarm_ul', nrm(-0.42, -0.9, -0.05 + 0.25 * free))
        rig.aim(pose, 'farm_ul', nrm(-0.25, -0.55 + 0.1 * free, -1.0))
    for side, sg in (('ll', 1), ('lr', -1)):
        sw = -swing * 0.6 * sg if gait is not None else 0.0
        rig.aim(pose, f'uarm_{side}', nrm(-0.45 * sg, -0.9, 0.1 + math.sin(math.radians(sw)) - 0.2 * free))
        rig.aim(pose, f'farm_{side}', nrm(-0.2 * sg, -0.75, -0.6 - 0.3 * free))
    if blade:
        bb = st['blade']; side = bb.split('_')[1]; sg = 1 if side.endswith('l') else -1
        up, fa = blade
        rig.aim(pose, 'uarm_' + side, up)
        rig.aim(pose, bb, fa)
    if extra:
        pose.update(extra)
    return pose, pos

def fallen_eyes(name, src, vox, voxel):
    """Authored glowing eyes (4, two pairs) on the head front, located from the head geometry."""
    sel = src.tris[src.bone == 'head'].reshape(-1, 3)
    if not len(sel):
        return [], []
    hy0, hy1 = sel[:, 1].min(), sel[:, 1].max()
    band = sel[(sel[:, 1] > hy0 + 0.25 * (hy1 - hy0)) & (sel[:, 1] < hy0 + 0.55 * (hy1 - hy0)) & (np.abs(sel[:, 0]) < 1.6)]
    if not len(band):
        band = sel
    yc = float(np.median(band[:, 1]))
    zf = np.percentile(band[:, 2], 3)
    if vox and 'head' in vox:
        # r2: sit on the voxelised face (the cube hull reaches past the triangle band; eyes were buried)
        bv = vox['head']
        ix = np.argwhere(bv.solid)
        wy = (bv.lo[1] + ix[:, 1] + 0.5) * voxel
        near = ix[np.abs(wy - yc) <= 1.5 * voxel]
        zf = (bv.lo[2] + (near if len(near) else ix)[:, 2].min()) * voxel
    col = (0.55, 0.85, 1.0)
    parts = []
    col = (0.78, 0.94, 1.0)   # blue-white
    for (dx, dy, s) in ((-0.95, 0.55, 0.7), (0.95, 0.55, 0.7), (-0.6, -0.35, 0.55), (0.6, -0.35, 0.55)):
        parts.append(box('eyes_glow', (dx, yc + dy, zf - 0.25), (s * 1.3, s * 1.05, 0.5), col, glow=True, edge=1.0))
    bones = [dict(name='eyes_glow', parent='head', origin=tuple(src.pivots['head']), glow=True)]
    arc_parts, arc_bones = fallen_arc(name, src)
    return parts + arc_parts, bones + arc_bones

ARC = (0.62, 0.86, 1.0)
ARC_HOT = (0.92, 0.98, 1.0)

def _bone_box(src, bone):
    sel = src.tris[src.bone == bone].reshape(-1, 3)
    if bone in src.frames:
        M, _, o = src.frames[bone]
        sel = (sel - o) @ M + o
    return sel.min(0), sel.max(0)

def fallen_arc(name, src):
    """Authored Arc/shock accents (not extracted VFX): weapon power cell for every Fallen, shock-blade
    edge for Dreg/Captain, Captain back coils. Placed in each owner bone's local (unrotated) frame."""
    parts, bones = [], []
    def part(bone, glow_bone, rel_c, size, col):
        lo, hi = _bone_box(src, bone)
        c = lo + (hi - lo) * np.array(rel_c)
        M = src.frames[bone][0] if bone in src.frames else None
        o = src.frames[bone][2] if bone in src.frames else None
        if M is not None:
            c = M @ (c - o) + o
        parts.append(box(glow_bone, c, size, col, M=M, glow=True, edge=1.0))
        if not any(b['name'] == glow_bone for b in bones):
            bones.append(dict(name=glow_bone, parent=bone, origin=tuple(src.pivots[bone]), glow=True))
    if 'weapon' in src.order:
        # weapon local frame: hand-hanging axis is local -Y (barrel). A cell on the receiver + muzzle ring.
        part('weapon', 'weapon_glow', (0.5, 0.62, 0.5), (1.2, 2.2, 1.2), ARC)
        part('weapon', 'weapon_glow', (0.5, 0.06, 0.5), (1.0, 0.6, 1.0), ARC_HOT)
    if 'blade' in src.order:
        for f in (0.15, 0.35, 0.55):
            part('blade', 'blade_glow', (0.5, f, 0.5), (0.5, 1.8, 0.5), ARC)
    if name == 'rg_captain':
        for dx in (0.3, 0.7):
            part('torso', 'pack_glow', (dx, 0.72, 0.92), (1.2, 2.6, 0.8), ARC)
        part('torso', 'pack_glow', (0.5, 0.80, 0.94), (2.6, 0.6, 0.7), ARC_HOT)
    return parts, bones

def fallen_clips(name, spec, src, bones):
    st = FALLEN_STYLE[spec['style']]
    rest = {rb: (M @ np.array([0, -1, 0])) for rb, (M, _, _) in src.frames.items()}
    rig = Rig(bones, rest)
    clips = []
    # idle -------------------------------------------------------------------------------------------
    c = Clip('idle', 2.4, 'loop')
    for i in range(9):
        f = i / 8; w = math.sin(2 * math.pi * f)
        pose, pos = fallen_pose(rig, st, lean=st['lean'] + 2 * w, head=(3 * w, 8 * math.sin(2 * math.pi * f + 1.2) * st['jitter']),
                                free=0.15 + 0.15 * w)
        pos['hips'] = (0, pos['hips'][1] - 0.25 * (1 + w), 0)
        keyframe_pose(c, f * c.length, pose, pos)
    clips.append(c)
    # walk / run -------------------------------------------------------------------------------------
    for cname, period, stride, lean_add, weap in (('walk', st['walk'], st['stride'], 4, 'low'), ('run', st['run'], st['stride'] * 1.5, 16, 'run')):
        c = Clip(cname, period, 'loop')
        for i in range(9):
            f = i / 8
            pose, pos = fallen_pose(rig, st, lean=st['lean'] + lean_add, gait=f, stride=stride, weapon=weap,
                                    head=(-4 if cname == 'run' else 0, 0), free=0.3)
            keyframe_pose(c, f * period, pose, pos)
        clips.append(c)
    # shoot -----------------------------------------------------------------------------------------
    c = Clip('shoot', 0.5, 'once')
    for t, w, rk, lean in ((0.0, 'low', 0, st['lean']), (0.07, 'aim', 0, st['lean'] + 2), (0.11, 'recoil', 1.0, st['lean'] - 4),
                           (0.2, 'aim', 0.25, st['lean']), (0.34, 'aim', 0, st['lean'] + 1), (0.5, 'low', 0, st['lean'])):
        pose, pos = fallen_pose(rig, st, lean=lean, weapon=w, recoil=rk, head=(4 if w != 'low' else 0, 0))
        keyframe_pose(c, t, pose, pos, interp='linear' if 0.05 < t < 0.13 else 'catmullrom')
    clips.append(c)
    # melee -----------------------------------------------------------------------------------------
    c = Clip('melee', 0.75, 'once')
    bb = st['blade']; sg = 1 if bb.endswith('l') else -1
    keys = ((0.0, None, 0, st['lean']), (0.22, (nrm(-0.6 * sg, 0.55, 0.6), nrm(-0.3 * sg, 0.9, 0.2)), -18 * sg, st['lean'] - 6),
            (0.34, (nrm(0.15 * sg, -0.2, -1.0), nrm(0.75 * sg, -0.35, -0.8)), 22 * sg, st['lean'] + 14),
            (0.48, (nrm(0.4 * sg, -0.7, -0.6), nrm(0.8 * sg, -0.6, -0.2)), 14 * sg, st['lean'] + 10),
            (0.75, None, 0, st['lean']))
    for t, bl, tw, lean in keys:
        pose, pos = fallen_pose(rig, st, lean=lean, blade=bl, twist=tw)
        if bl is not None and t == 0.34:
            pos['hips'] = (0, pos['hips'][1] - 0.8, -2.5)
        keyframe_pose(c, t, pose, pos, interp='linear' if 0.2 < t < 0.4 else 'catmullrom')
    clips.append(c)
    # hit ---------------------------------------------------------------------------------------------
    c = Clip('hit', 0.35, 'once')
    for t, lean, hd, fr in ((0, st['lean'], 0, 0.1), (0.06, st['lean'] - 16, -14, 0.6), (0.18, st['lean'] - 6, -5, 0.3), (0.35, st['lean'], 0, 0.1)):
        pose, pos = fallen_pose(rig, st, lean=lean, head=(hd, 6 if t else 0), free=fr)
        keyframe_pose(c, t, pose, pos)
    clips.append(c)
    # stagger ---------------------------------------------------------------------------------------
    c = Clip('stagger', 1.1, 'once')
    for t, lean, hz, cr, fr, g in ((0, st['lean'], 0, None, 0.1, None), (0.1, st['lean'] - 28, 1.5, 0.5, 1.0, None),
                                   (0.3, st['lean'] - 18, 3.5, 2.5, 0.9, 0.55), (0.55, st['lean'] - 6, 5.0, 3.0, 0.6, 0.05),
                                   (0.8, st['lean'] + 6, 5.0, 2.0, 0.3, None), (1.1, st['lean'], 0, None, 0.1, None)):
        pose, pos = fallen_pose(rig, st, lean=lean, crouch=cr, free=fr, gait=g, stride=10 if g is not None else 0,
                                head=(-10 if 0 < t < 0.6 else 0, 0))
        pos['hips'] = (0, pos['hips'][1], hz)
        keyframe_pose(c, t, pose, pos)
    clips.append(c)
    # death (hold on last pose) -----------------------------------------------------------------------
    c = Clip('death', 1.6, 'hold')
    seq = ((0.0, st['lean'], 0, 0, 0, 0.1, 0), (0.12, st['lean'] - 25, 0, 0.5, 0, 1.0, -12),
           (0.45, st['lean'] + 10, -6, 2.0, 40, 0.7, 10), (0.8, st['lean'] + 45, -14, 3.0, 70, 0.4, 20),
           (1.15, st['lean'] + 70, -21, 4.0, 85, 0.2, 30), (1.6, st['lean'] + 72, -22, 4.0, 86, 0.2, 32))
    for t, lean, hy, hz, knee, fr, hx in seq:
        pose, pos = fallen_pose(rig, st, lean=lean, free=fr, head=(hx, 0))
        pose['hips'] = (hx * 0.6, 0, 0)
        for sd in ('l', 'r'):
            pose[f'thigh_{sd}'] = (-knee * 0.9 - 6, 0, 0)
            pose[f'shin_{sd}'] = (10 + knee * 1.6, 0, 0)
        pos['hips'] = (0, -st['crouch'] + hy, hz)
        keyframe_pose(c, t, pose, pos)
    clips.append(c)
    # spawn (drop in, land, rise and roar) -------------------------------------------------------------
    c = Clip('spawn', 1.3, 'once')
    seq = ((0.0, 30.0, 0.0, 0, 0.2), (0.28, 0.0, 0.0, 0, 0.2), (0.36, -4.5, 3.5, 30, 0.6), (0.62, -3.0, 2.0, 20, 0.8),
           (0.95, 0.0, 0.0, -14, 1.0), (1.3, 0.0, 0.0, 0, 0.2))
    for t, y, cr, lean_d, fr in seq:
        pose, pos = fallen_pose(rig, st, lean=st['lean'] + lean_d, crouch=st['crouch'] + cr, free=fr,
                                head=(-22 if 0.8 < t < 1.1 else 0, 0))
        pos['hips'] = (0, pos['hips'][1] + y, 0)
        keyframe_pose(c, t, pose, pos, interp='linear' if t <= 0.36 else 'catmullrom')
    clips.append(c)
    # eye flicker overlay on every clip: none (eyes are static glow)
    return clips

# ------------------------------------------------------------------------------------------- shank
def shank_decor(src):
    body = src.tris[src.bone == 'body'].reshape(-1, 3)
    zf = np.percentile(body[:, 2], 2); cy = float(np.median(body[:, 1]))
    parts = [box('eye_glow', (0, cy + 0.5, zf - 0.2), (2.6, 2.6, 0.6), (1.0, 0.45, 0.14), glow=True, edge=1.0),
             box('eye_glow', (0, cy + 0.5, zf - 0.55), (1.2, 1.2, 0.3), (1.0, 0.88, 0.55), glow=True, edge=1.0)]
    return parts, [dict(name='eye_glow', parent='body', origin=(0, cy, zf), glow=True)]

def shank_clips(bones):
    clips = []
    c = Clip('idle', 2.0, 'loop')
    c.curve('body', 'position', lambda f: (0, 1.2 * math.sin(2 * math.pi * f), 0))
    c.curve('body', 'rotation', lambda f: (3 * math.sin(2 * math.pi * f + 0.6), 6 * math.sin(2 * math.pi * f * 1), 2 * math.sin(4 * math.pi * f)))
    for w, sg in (('wing_ul', 1), ('wing_ur', -1), ('wing_ll', 1), ('wing_lr', -1)):
        c.curve(w, 'rotation', lambda f, sg=sg: (6 * math.sin(4 * math.pi * f), 0, sg * 5 * math.sin(4 * math.pi * f + 1)))
    clips.append(c)
    c = Clip('fly', 1.0, 'loop')
    c.curve('body', 'rotation', lambda f: (14 + 2 * math.sin(2 * math.pi * f), 0, 3 * math.sin(2 * math.pi * f)))
    c.curve('body', 'position', lambda f: (0, 0.8 * math.sin(2 * math.pi * f), 0))
    for w, sg in (('wing_ul', 1), ('wing_ur', -1), ('wing_ll', 1), ('wing_lr', -1)):
        c.curve(w, 'rotation', lambda f, sg=sg: (18 + 8 * math.sin(4 * math.pi * f), 0, sg * -6))
    clips.append(c)
    c = Clip('shoot', 0.4, 'once')
    for t, gx, bx, bz in ((0, 0, 0, 0), (0.05, -10, -6, 1.5), (0.15, -4, -2, 0.5), (0.4, 0, 0, 0)):
        c.key('gun', 'rotation', t, (gx, 0, 0)); c.key('body', 'rotation', t, (bx, 0, 0)); c.key('body', 'position', t, (0, 0, bz))
    c.key('eye_glow', 'scale', 0, (1, 1, 1)); c.key('eye_glow', 'scale', 0.05, (1.4, 1.4, 1.4)); c.key('eye_glow', 'scale', 0.4, (1, 1, 1))
    clips.append(c)
    c = Clip('hit', 0.4, 'once')
    for t, r in ((0, (0, 0, 0)), (0.06, (-14, 18, 12)), (0.2, (5, -6, -4)), (0.4, (0, 0, 0))):
        c.key('body', 'rotation', t, r)
    clips.append(c)
    c = Clip('death', 1.4, 'hold')
    for t, r, y, sc in ((0, (0, 0, 0), 0, 1), (0.3, (25, 180, 40), -4, 1), (0.8, (60, 420, 90), -16, 0.95), (1.4, (80, 600, 120), -34, 0.85)):
        c.key('body', 'rotation', t, r, 'linear'); c.key('body', 'position', t, (0, y, 0)); c.key('body', 'scale', t, (sc, sc, sc))
    c.key('eye_glow', 'scale', 0, (1, 1, 1)); c.key('eye_glow', 'scale', 0.25, (1.6, 1.6, 1.6)); c.key('eye_glow', 'scale', 0.6, (0.01, 0.01, 0.01))
    c.key('eye_glow', 'scale', 1.4, (0.01, 0.01, 0.01))
    clips.append(c)
    return clips

# ------------------------------------------------------------------------------------------- walker
WALKER_LEGS = [('fl', 'A', -1), ('mr', 'A', 1), ('bl', 'A', -1), ('fr', 'B', 1), ('ml', 'B', -1), ('br', 'B', 1)]

def walker_decor(src):
    body = src.tris[src.bone == 'body'].reshape(-1, 3)
    head = src.tris[src.bone == 'head'].reshape(-1, 3)
    hz = float(np.percentile(head[:, 2], 6)); hy0 = float(head[:, 1].min())
    core_c = np.array([0.0, hy0 - 2.5, hz + 3.0])
    hot, rim = (1.0, 0.62, 0.22), (0.95, 0.30, 0.10)
    parts = [box('weakpoint', core_c + (0, 0, 1.0), (10, 10, 6), (0.40, 0.40, 0.42), edge=1.2),   # housing
             box('weakpoint_glow', core_c, (7, 7, 7), hot, glow=True, edge=1.0),
             box('weakpoint_glow', core_c, (9, 4, 4), rim, glow=True), box('weakpoint_glow', core_c, (4, 9, 4), rim, glow=True),
             box('weakpoint_glow', core_c + (0, 0, -3.8), (3, 3, 1), (1.0, 0.95, 0.75), glow=True)]
    plate = (0.46, 0.46, 0.48)
    for sd, sg in (('l', -1), ('r', 1)):
        parts.append(box(f'plate_{sd}', core_c + (sg * 3.2, 0, -4.8), (6.4, 11, 1.6), plate, edge=0.7))
        parts.append(box(f'plate_{sd}', core_c + (sg * 3.2, 0, -5.8), (4.8, 8, 0.6), (0.62, 0.61, 0.60)))
    eye_c = (0.0, float(np.median(head[:, 1])) + 1.0, float(np.percentile(head[:, 2], 2)) - 0.3)
    parts += [box('eye_glow', eye_c, (4, 2.6, 0.8), (0.70, 0.92, 1.0), glow=True, edge=1.0)]
    bones = [dict(name='weakpoint', parent='body', origin=tuple(core_c)),
             dict(name='weakpoint_glow', parent='weakpoint', origin=tuple(core_c), glow=True),
             dict(name='plate_l', parent='body', origin=tuple(core_c + (-6.4, 0, -4.8))),
             dict(name='plate_r', parent='body', origin=tuple(core_c + (6.4, 0, -4.8))),
             dict(name='eye_glow', parent='head', origin=eye_c, glow=True)]
    return parts, bones

def walker_leg_pose(leg, sg, swing, lift, knee=0.0):
    """swing>0 = foot forward, lift>0 = foot up. Left legs extend to -X, right legs to +X; with the Blockbench
    animation convention a +Y value turns toward +X, a +Z value rolls -Y toward +X (see models.md)."""
    if sg < 0:
        return {f'leg_{leg}': (0, swing, -lift), f'leg_{leg}_low': (0, 0, -knee)}
    return {f'leg_{leg}': (0, -swing, lift), f'leg_{leg}_low': (0, 0, knee)}

def walker_clips(bones):
    clips = []
    names = [b['name'] for b in bones]
    c = Clip('idle', 4.0, 'loop')
    c.curve('body', 'position', lambda f: (0, 0.8 * math.sin(2 * math.pi * f), 0))
    c.curve('body', 'rotation', lambda f: (1.0 * math.sin(2 * math.pi * f), 2.0 * math.sin(2 * math.pi * f + 0.8), 0.8 * math.sin(4 * math.pi * f)))
    c.curve('head', 'rotation', lambda f: (2 * math.sin(2 * math.pi * f + 2), 6 * math.sin(2 * math.pi * f), 0))
    c.curve('weakpoint', 'scale', lambda f: (1 + 0.04 * math.sin(4 * math.pi * f),) * 3)
    clips.append(c)
    c = Clip('walk', 2.4, 'loop')
    n = 12
    for i in range(n + 1):
        f = i / n; ph = 2 * math.pi * f
        pose = {}
        for leg, grp, sg in WALKER_LEGS:
            p = ph + (0 if grp == 'A' else math.pi)
            swing = 14 * math.sin(p)
            lift = 16 * max(0.0, math.cos(p))
            pose.update(walker_leg_pose(leg, sg, swing, lift, knee=lift * 0.6))
        pose['body'] = (0.8 * math.sin(2 * ph), 0, 1.6 * math.sin(ph))
        pose['head'] = (0, 3 * math.sin(ph), 0)
        keyframe_pose(c, f * c.length, pose, {'body': (0, -1.4 * abs(math.sin(ph)), 0)})
    clips.append(c)
    c = Clip('fire', 0.9, 'once')
    for t, hx, by, bz in ((0, 0, 0, 0), (0.08, -9, -1.5, 3), (0.25, -3, -0.5, 1), (0.9, 0, 0, 0)):
        c.key('head', 'rotation', t, (hx, 0, 0)); c.key('body', 'position', t, (0, by, bz)); c.key('body', 'rotation', t, (hx * 0.25, 0, 0))
    c.key('eye_glow', 'scale', 0, (1, 1, 1)); c.key('eye_glow', 'scale', 0.08, (1.6, 1.6, 1.6)); c.key('eye_glow', 'scale', 0.9, (1, 1, 1))
    clips.append(c)
    c = Clip('leg_break', 1.6, 'hold')
    for t, lift, knee, bx, bz, by in ((0, 0, 0, 0, 0, 0), (0.12, 30, 20, -3, -4, -2), (0.45, -18, 55, 7, -9, -10),
                                      (0.9, -22, 60, 9, -10, -13), (1.6, -20, 58, 8, -9, -12)):
        pose = walker_leg_pose('fl', -1, 6, lift, knee)
        pose['body'] = (bx, 0, bz)
        keyframe_pose(c, t, pose, {'body': (0, by, 0)})
    clips.append(c)
    c = Clip('stagger', 1.2, 'once')
    for t, bx, bz, by in ((0, 0, 0, 0), (0.1, -6, 4, -3), (0.35, 4, -3, -5), (0.7, -2, 1, -1), (1.2, 0, 0, 0)):
        pose = {'body': (bx, 0, bz), 'head': (-bx * 1.5, 0, 0)}
        for leg, grp, sg in WALKER_LEGS:
            pose.update(walker_leg_pose(leg, sg, 0, -abs(by) * 0.8, abs(by)))
        keyframe_pose(c, t, pose, {'body': (0, by, 0)})
    clips.append(c)
    c = Clip('weakpoint_open', 1.4, 'hold')
    for t, ang, sc, by, bx in ((0, 0, 1.0, 0, 0), (0.3, 20, 1.05, -4, 4), (0.7, 70, 1.25, -9, 8), (1.0, 82, 1.15, -10, 9), (1.4, 80, 1.2, -10, 9)):
        c.key('plate_l', 'rotation', t, (0, ang, 0)); c.key('plate_r', 'rotation', t, (0, -ang, 0))
        c.key('weakpoint', 'scale', t, (sc, sc, sc)); c.key('body', 'position', t, (0, by, 0)); c.key('body', 'rotation', t, (bx, 0, 0))
        for leg, grp, sg in WALKER_LEGS:
            for b, v in walker_leg_pose(leg, sg, 0, -abs(by) * 1.2, abs(by) * 2).items():
                c.key(b, 'rotation', t, v)
    clips.append(c)
    c = Clip('recover', 1.6, 'once')
    for t, ang, sc, by, bx in ((0, 80, 1.2, -10, 9), (0.5, 60, 1.1, -7, 5), (1.1, 8, 1.0, 1.5, -2), (1.6, 0, 1.0, 0, 0)):
        c.key('plate_l', 'rotation', t, (0, ang, 0)); c.key('plate_r', 'rotation', t, (0, -ang, 0))
        c.key('weakpoint', 'scale', t, (sc, sc, sc)); c.key('body', 'position', t, (0, by, 0)); c.key('body', 'rotation', t, (bx, 0, 0))
        for leg, grp, sg in WALKER_LEGS:
            for b, v in walker_leg_pose(leg, sg, 0, -max(0.0, -by) * 1.2, max(0.0, -by) * 2).items():
                c.key(b, 'rotation', t, v)
    clips.append(c)
    c = Clip('death', 2.6, 'hold')
    for t, by, bx, bz, splay in ((0, 0, 0, 0, 0), (0.25, -3, -5, 3, 5), (0.9, -14, 6, -6, 25), (1.6, -26, 10, -9, 40), (2.6, -28, 11, -10, 42)):
        pose = {'body': (bx, 0, bz), 'head': (bx * 1.4, 8 if t > 0.5 else 0, 0)}
        for leg, grp, sg in WALKER_LEGS:
            pose.update(walker_leg_pose(leg, sg, 0, -splay, splay * 0.4))
        keyframe_pose(c, t, pose, {'body': (0, by, 0)}, scale={'weakpoint': (1 - min(1, t / 2.0) * 0.99,) * 3})
    clips.append(c)
    return clips


# ------------------------------------------------------------------------------------- walker r3
# Hit regions of WalkerBoss.LAYOUT (main checkout, campaign/fallen/WalkerBoss.java; anchor-local blocks,
# x = right, y = up from the anchor feet, z = forward). BetterModel turns model -Z (north) to the entity's
# facing, so model px = (x * 16, y * 16, -z * 16) with model +X = right.
WALKER_LAYOUT = {   # region: (x, y_bottom, z, width, height)
    'leg_fl': (-2.3, 0.0, 2.0, 1.25, 4.0), 'leg_fr': (2.3, 0.0, 2.0, 1.25, 4.0),
    'leg_bl': (-2.3, 0.0, -2.0, 1.25, 4.0), 'leg_br': (2.3, 0.0, -2.0, 1.25, 4.0),
    'hull': (0.0, 3.7, -0.2, 4.0, 2.1), 'weakpoint': (0.0, 2.75, 1.6, 1.1, 1.1),
}
WALKER_MUZZLE = (0.0, 4.3, 2.4)       # WalkerBoss.muzzle — shots start here (model barrel tip is further out)

def layout_px(region):
    x, y, z, w, h = WALKER_LAYOUT[region]
    return np.array([x * 16, (y + h / 2) * 16, -z * 16]), np.array([w * 16, h * 16, w * 16])

WK = dict(  # r3 keys; r4 maps them to the HOD palette in build_walker
          steel=(0.74, 0.75, 0.76), steel_mid=(0.56, 0.57, 0.59), steel_dark=(0.34, 0.35, 0.37),
          maroon=(0.68, 0.19, 0.16), maroon_dark=(0.46, 0.12, 0.10), ochre=(0.90, 0.64, 0.22),
          joint=(0.22, 0.21, 0.21), hose=(0.28, 0.24, 0.22),
          core=(1.0, 0.62, 0.20), core_rim=(1.0, 0.42, 0.10), core_hot=(1.0, 0.92, 0.70),
          eye=(0.72, 0.93, 1.0), eye_hot=(0.95, 1.0, 1.0))
WALKER_HIP_Y = 74.0
WALKER_LEGS4 = [('fl', -1, -1), ('fr', 1, -1), ('bl', -1, 1), ('br', 1, 1)]   # name, side x, z (model)

def seg_matrix(a, b, up=(0, 1, 0)):
    """Box frame whose local -Y runs from a to b (limb segments)."""
    d = np.asarray(b, float) - np.asarray(a, float); d /= np.linalg.norm(d)
    ey = -d
    ref = np.array([0.0, 0.0, 1.0]) if abs(ey[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    ex = np.cross(ey, ref); ex /= np.linalg.norm(ex)
    ez = np.cross(ex, ey)
    return np.stack([ex, ey, ez], 1)

def build_walker(name, spec, ev, log):
    """r3: ORIGINAL authored four-legged Walker cube model laid out on WalkerBoss hit regions. Source
    Walker__80C60641 informs the domed hull, forward head cannon and segmented legs; the extraction's six
    legs are reduced to four because the boss has four leg hit regions."""
    P = WK
    parts = []
    PAINT['density'] = 1.0; PAINT['clip'] = 40
    # r4 repaint: Devil Walker palette (sand armour, red markings, dark mechanical joints) with the
    # hand-painted per-face painter; geometry unchanged from r3.
    remap = {P['steel']: ('sandarmor', HOD['sand_lt'], ('mark',)), P['steel_mid']: ('sandarmor', HOD['sand'], ()),
             P['steel_dark']: ('gun', HOD['gun'], ()), P['maroon']: ('sandarmor', HOD['red'], ()),
             P['maroon_dark']: ('gun', HOD['crimson_dk'], ()), P['ochre']: ('armor', HOD['ivory_dk'], ()),
             P['joint']: ('joint', HOD['joint'], ()), P['hose']: ('leather', HOD['leather'], ())}
    def add(bone, c, sz, col, glow=False, style=None, edge=None, M=None):
        if glow:
            parts.append(box(bone, c, sz, col, M=M, glow=True, edge=1.0)); return
        if isinstance(col, dict):
            col = col['north']
        mat, rgb, opts = remap[tuple(col)]
        big = min(sorted(sz)[1:]) >= 12
        parts.append(pbox(bone, c, sz, mat, color=rgb, M=M, opts=opts if big or mat != 'sandarmor' else ()))
    hull_c, hull_s = layout_px('hull')             # centre y 76, 64 wide
    wp_c, wp_s = layout_px('weakpoint')
    hz = hull_c[2]
    bones = [dict(name='root', parent=None, origin=(0, 0, 0)),
             dict(name='body', parent='root', origin=(0, 72, hz)),
             dict(name='head', parent='body', origin=(0, 74, -38)),
             dict(name='eye_glow', parent='head', origin=(0, 80, -56), glow=True),
             dict(name='weakpoint', parent='body', origin=tuple(wp_c)),
             dict(name='weakpoint_glow', parent='weakpoint', origin=tuple(wp_c), glow=True),
             dict(name='plate_l', parent='body', origin=(-12, wp_c[1], wp_c[2] - 8)),
             dict(name='plate_r', parent='body', origin=(12, wp_c[1], wp_c[2] - 8))]
    # ---- hull: wide armoured dome, maroon side armour, ochre trims
    top = {'up': P['steel'], 'down': P['steel_dark'], 'north': P['steel_mid'], 'south': P['steel_mid'],
           'east': P['steel_mid'], 'west': P['steel_mid']}
    add('body', (0, 63, hz), (54, 8, 70), P['steel_dark'])
    add('body', (0, 76, hz), (72, 18, 82), top)
    add('body', (0, 89, hz + 2), (60, 8, 70), top)
    add('body', (0, 96, hz + 6), (38, 6, 44), top)
    add('body', (0, 100.5, hz + 8), (20, 3, 24), P['steel_mid'])
    for sx in (-1, 1):
        for zc in (-18, 6, 30):
            add('body', (sx * 37.5, 77, hz + zc), (3, 16, 22), P['maroon'])           # side armour slabs
            add('body', (sx * 38.6, 84.5, hz + zc), (2, 2, 20), P['ochre'])
        add('body', (sx * 22, 93.5, hz - 4), (14, 3, 44), P['maroon'])                # roof plates
        add('body', (sx * 22, 95.3, hz - 4), (14, 0.6, 3), P['ochre'])
        add('body', (sx * 30, 87.5, hz), (8, 3, 72), P['steel_mid'])                  # shoulder rail
        for zc in (-26, 26):                                                          # hip sockets
            add('body', (sx * 33, WALKER_HIP_Y, hz + zc * 1.15), (10, 14, 16), P['joint'])
        add('body', (sx * 30, 97, hz + 34), (2, 14, 2), P['steel_dark'])              # antennae
        add('body', (sx * 30, 104.5, hz + 34), (3, 2, 3), P['ochre'])
    add('body', (0, 72, -37), (62, 12, 6), P['maroon_dark'])                          # front lip
    add('body', (0, 79, -38.5), (48, 3, 4), P['ochre'])
    add('body', (0, 78, hz + 44), (44, 18, 8), P['steel_dark'])                        # rear engine block
    for sx in (-1, 0, 1):
        add('body', (sx * 13, 78, hz + 48.5), (9, 10, 1.5), P['joint'])
    add('body', (0, 59, -20), (12, 6, 12), P['steel_dark'])                            # weakpoint strut
    # ---- head + cannon
    add('head', (0, 77, -47), (32, 18, 18), {'up': P['steel'], 'down': P['steel_dark'], 'north': P['steel_mid'],
                                             'south': P['steel_mid'], 'east': P['steel_mid'], 'west': P['steel_mid']})
    for sx in (-1, 1):
        add('head', (sx * 17.5, 77, -47), (3, 16, 15), P['maroon'])
    add('head', (0, 87.5, -48), (26, 3, 14), P['ochre'])                               # brow
    add('head', (0, 80, -56.5), (14, 9, 1), P['joint'])                                # eye socket
    add('head', (0, 69, -59), (14, 12, 8), P['steel_dark'])                            # cannon housing
    add('head', (0, 69, -69), (7, 7, 14), P['steel'])                                  # barrel
    add('head', (0, 69, -77.5), (10, 10, 3), P['ochre'])                               # muzzle ring
    add('head', (0, 69, -79.4), (5, 5, 0.8), P['joint'])
    for sx in (-1, 1):
        add('head', (sx * 6.5, 72, -66), (2, 3, 12), P['steel_dark'])                  # coolant fins
    # eye: 1.5x the r2 eye (4 x 2.6) -> 6 x 3.9, plus hot core
    add('eye_glow', (0, 80, -57.4), (6.0, 3.9, 1.2), P['eye'], glow=True, style='panel', edge=1.0)
    add('eye_glow', (0, 80, -58.1), (3.0, 2.0, 0.6), P['eye_hot'], glow=True, style='panel', edge=1.0)
    # ---- weakpoint: housing + 1.5x glow core (r2 core 7, rims 9x4x4, cap 3x3x1)
    add('weakpoint', wp_c + (0, 3.5, 4), (22, 14, 14), P['steel_dark'])
    add('weakpoint', wp_c + (0, 10, 3), (16, 2, 12), P['ochre'])
    add('weakpoint_glow', wp_c, (10.5, 10.5, 10.5), P['core'], glow=True, style='panel', edge=1.0)
    add('weakpoint_glow', wp_c, (13.5, 6, 6), P['core_rim'], glow=True, style='panel', edge=1.0)
    add('weakpoint_glow', wp_c, (6, 13.5, 6), P['core_rim'], glow=True, style='panel', edge=1.0)
    add('weakpoint_glow', wp_c + (0, 0, -5.7), (4.5, 4.5, 1.5), P['core_hot'], glow=True, style='panel', edge=1.0)
    for sx, bn in ((-1, 'plate_l'), (1, 'plate_r')):
        # r3: narrow armour shutters leave the orange core rim visible while ARMORED (readable target)
        add(bn, (sx * 3.2, wp_c[1], wp_c[2] - 8), (6.4, 9, 2.5), P['maroon'])
        add(bn, (sx * 3.2, wp_c[1] + 3.6, wp_c[2] - 9.5), (5.6, 1.2, 1), P['ochre'])
    # ---- legs: hip socket -> thick armoured thigh -> knee -> long shin -> clawed foot
    for leg, sx, sz in WALKER_LEGS4:
        lc, ls = layout_px(f'leg_{leg}')
        H = np.array([sx * 33.0, WALKER_HIP_Y, hz + sz * 30.0])
        K = np.array([sx * 54.0, 99.0, sz * 38.0])
        F = np.array([lc[0], 0.0, lc[2]])
        hb, kb = f'leg_{leg}', f'leg_{leg}_low'
        bones.append(dict(name=hb, parent='root', origin=tuple(H)))
        bones.append(dict(name=kb, parent=hb, origin=tuple(K)))
        Mt = seg_matrix(H, K)
        tl = float(np.linalg.norm(K - H))
        add(hb, (H + K) / 2, (15, tl + 6, 15), P['steel_mid'], M=Mt)
        out = np.array([sx, 0.0, 0.0])
        add(hb, (H + K) / 2 + Mt @ np.array([0, 0, 0]) + out * 7.6, (2.4, tl, 13), P['maroon'], M=Mt)
        add(hb, H + (K - H) * 0.25, (17, 3, 17), P['ochre'], M=Mt)
        add(hb, (H + K) / 2 + np.array([0, -7.5, 0]), (5, 4, tl * 0.7), P['hose'], M=Mt)
        # knee
        add(kb, K, (20, 20, 20), P['joint'])
        add(kb, K + out * 10.6, (2, 13, 13), P['ochre'])
        add(kb, K + np.array([0, 10.6, 0]), (13, 2, 13), P['steel'])
        # shin: armoured upper, steel lower, ankle
        Ms = seg_matrix(K, F)
        sl = float(np.linalg.norm(F - K))
        d = (F - K) / sl
        def at(f):
            return K + d * sl * f
        add(kb, at(0.30), (17, sl * 0.42, 17), P['maroon'], M=Ms)
        add(kb, at(0.30) + Ms @ np.array([0, 0, sz * -9.2]), (11, sl * 0.36, 1.6), P['maroon_dark'], M=Ms)
        add(kb, at(0.53), (19, 3, 19), P['ochre'], M=Ms)
        add(kb, at(0.74), (12, sl * 0.38, 12), P['steel'], M=Ms)
        add(kb, at(0.62) + Ms @ np.array([-sx * 8, 0, 0]), (3, sl * 0.5, 3), P['hose'], M=Ms)    # piston
        add(kb, at(0.95), (15, 6, 15), P['joint'], M=Ms)
        gb = f'leg_{leg}_glow'                                     # r4 orange running lights on each shin
        bones.append(dict(name=gb, parent=kb, origin=tuple(at(0.53)), glow=True))
        for fz in (-1, 1):
            add(gb, at(0.40) + Ms @ np.array([0, 0, fz * 8.8]), (3.0, 2.2, 0.8), P['core'], M=Ms, glow=True)
        # foot pad + toes (axis aligned)
        add(kb, F + (0, 3, 0), (24, 6, 26), P['steel_mid'])
        add(kb, F + (0, 6.6, 0), (16, 1.2, 18), P['steel'])
        for tx, tz in ((-8, -15), (0, -16), (8, -15), (sx * 13, 6)):
            add(kb, F + (tx, 2, tz), (5, 4, 8), P['joint'])
            add(kb, F + (tx, 1, tz - 5 if tz < 0 else tz), (4, 2, 3), P['ochre'])
    PAINT['density'] = 3.0; PAINT['clip'] = 64
    clips = walker4_clips(bones)
    meta = {'generator': GENERATOR, 'source': spec['src'], 'geometry': 'authored r3 four-leg walker on WalkerBoss.LAYOUT',
            'layout': {k: list(v) for k, v in WALKER_LAYOUT.items()}, 'muzzle_tip_blocks': [0, 69 / 16, 79.8 / 16],
            'animations': 'original authored (extraction contains no clips)',
            'credit': 'Walker silhouette informed by extracted Walker__80C60641; four-leg cube design + animations authored for W300'}
    return finish_authored(name, spec, ev, log, bones, parts, clips, meta)

def walker4_leg(leg, swing=0.0, lift=0.0, knee=0.0, drop=0.0):
    """Rotations for one leg. swing>0 foot forward, lift>0 foot up/out, knee>0 folds the shin under."""
    sx = -1 if leg.endswith('l') else 1
    hip = (0, swing if sx < 0 else -swing, -lift if sx < 0 else lift)
    low = (0, 0, knee if sx < 0 else -knee)
    return {f'leg_{leg}': hip, f'leg_{leg}_low': low}, {f'leg_{leg}': (0, -drop, 0)}

# Downed pose solved numerically (hip/knee z rotations per leg keep the three healthy feet planted on y=0
# while the hull pitches nose-down and rolls onto the broken front-left corner; that foot splays outward).
WALKER_DOWNED = {   # leg: (hip z, knee z, hip drop px)
    'fl': (-18.0, -26.0, 21.6), 'fr': (37.0, -26.0, 6.7), 'bl': (-39.0, 27.0, 13.4), 'br': (-4.0, 3.0, -1.4)}
WALKER_DOWNED_BODY = ((8.0, 0.0, 13.0), 10.0)

def walker_downed(k):
    """Shared posture of leg_break end / stagger / weakpoint_open / recover start."""
    (bx, by, bz), drop = WALKER_DOWNED_BODY
    rot = {'body': (bx * k, by * k, bz * k), 'head': (-12 * k, 0, -6 * k)}
    pos = {'body': (0, -drop * k, 0)}
    for leg, (hz_, kz, d) in WALKER_DOWNED.items():
        rot[f'leg_{leg}'] = (0, 0, hz_ * k)
        rot[f'leg_{leg}_low'] = (0, 0, kz * k)
        pos[f'leg_{leg}'] = (0, -d * k, 0)
    return rot, pos

def mix(a, b, f):
    out = {}
    for k in set(a) | set(b):
        va = np.array(a.get(k, (0, 0, 0)), float); vb = np.array(b.get(k, (0, 0, 0)), float)
        out[k] = tuple(va * (1 - f) + vb * f)
    return out

def walker4_clips(bones):
    clips = []
    c = Clip('idle', 4.0, 'loop')
    c.curve('body', 'position', lambda f: (0, 0.9 * math.sin(2 * math.pi * f), 0))
    c.curve('body', 'rotation', lambda f: (1.0 * math.sin(2 * math.pi * f), 2.0 * math.sin(2 * math.pi * f + 0.8), 0.8 * math.sin(4 * math.pi * f)))
    c.curve('head', 'rotation', lambda f: (2 * math.sin(2 * math.pi * f + 2), 7 * math.sin(2 * math.pi * f), 0))
    c.curve('weakpoint_glow', 'scale', lambda f: (1 + 0.06 * math.sin(4 * math.pi * f),) * 3)
    clips.append(c)
    # walk: diagonal pairs (fl+br, fr+bl), heavy stomp: feet plant fast, hull dips on contact
    c = Clip('walk', 2.4, 'loop')
    n = 16
    for i in range(n + 1):
        f = i / n; ph = 2 * math.pi * f
        rot, pos = {}, {}
        for leg, sx, sz in WALKER_LEGS4:
            p = ph + (0 if leg in ('fl', 'br') else math.pi)
            r, q = walker4_leg(leg, swing=13 * math.sin(p), lift=14 * max(0.0, math.cos(p)) ** 1.5,
                               knee=10 * max(0.0, math.cos(p)))
            rot.update(r); pos.update(q)
        stomp = abs(math.sin(ph)) ** 4
        rot['body'] = (1.2 * math.sin(2 * ph), 2.5 * math.sin(ph), 2.2 * math.sin(ph))
        rot['head'] = (1.5 * stomp, -2.5 * math.sin(ph), 0)
        pos['body'] = (0, -2.2 * stomp, 0)
        keyframe_pose(c, f * c.length, rot, pos)
    clips.append(c)
    c = Clip('fire', 0.9, 'once')
    for t, hx, bz, es in ((0, 0, 0, 1), (0.06, -12, 4, 1.8), (0.2, -4, 1.5, 1.3), (0.9, 0, 0, 1)):
        c.key('head', 'rotation', t, (hx, 0, 0)); c.key('head', 'position', t, (0, 0, bz))
        c.key('body', 'rotation', t, (hx * 0.25, 0, 0)); c.key('eye_glow', 'scale', t, (es, es, es))
    clips.append(c)
    # leg_break: impact jolt on the front-left leg, knee buckles, hull slams onto that corner, hold downed
    c = Clip('leg_break', 1.6, 'hold')
    seq = [(0.0, 0.0, None), (0.08, -0.15, dict(body=(-4, 0, -5))), (0.22, 0.55, None), (0.34, 1.12, None),
           (0.48, 0.92, None), (0.62, 1.04, None), (0.85, 0.98, None), (1.6, 1.0, None)]
    for t, k, extra in seq:
        rot, pos = walker_downed(max(k, 0.0))
        if extra:
            rot.update(extra)
        if k > 1:   # overshoot on the slam
            rot['body'] = tuple(np.array(rot['body']) * 1.0); pos['body'] = (0, -9 * k - 2, 0)
        if t == 0.08:
            pos['body'] = (0, 2.5, 0)
        keyframe_pose(c, t, rot, pos, interp='linear' if t <= 0.34 else 'catmullrom')
    c.key('weakpoint_glow', 'scale', 0, (1, 1, 1)); c.key('weakpoint_glow', 'scale', 0.34, (1.3, 1.3, 1.3))
    c.key('weakpoint_glow', 'scale', 1.6, (1.1, 1.1, 1.1))
    clips.append(c)
    # stagger: from downed, violent shudder side to side, healthy legs scrabble, head thrashes, back to downed
    c = Clip('stagger', 1.2, 'once')
    base_r, base_p = walker_downed(1.0)
    for i, t in enumerate((0, 0.1, 0.22, 0.34, 0.46, 0.6, 0.76, 0.95, 1.2)):
        a = (1 - t / 1.2) * (1 if i % 2 else -1)
        rot = dict(base_r); pos = dict(base_p)
        rot['body'] = (base_r['body'][0] + 4 * abs(a), 5 * a, base_r['body'][2] + 7 * a)
        rot['head'] = (-18 * abs(a) + base_r['head'][0], 16 * a, -8 * a)
        pos['body'] = (2 * a, base_p['body'][1] - 2 * abs(a), 0)
        for leg, ph in (('fr', 0), ('bl', 1), ('br', 2)):   # healthy legs scrabble around the planted pose
            hz_, kz, _ = WALKER_DOWNED[leg]
            w = a * (1 if ph % 2 == 0 else -1)
            rot[f'leg_{leg}'] = (0, 9 * w, hz_ + 5 * abs(a) * (1 if leg.endswith('r') else -1))
            rot[f'leg_{leg}_low'] = (0, 0, kz)
        rot['leg_fl_low'] = (0, 0, WALKER_DOWNED['fl'][1] - 8 * abs(a))   # broken leg twitches
        keyframe_pose(c, t, rot, pos, interp='linear')
    c.key('eye_glow', 'scale', 0, (1, 1, 1)); c.key('eye_glow', 'scale', 0.3, (0.4, 0.4, 0.4))
    c.key('eye_glow', 'scale', 0.6, (1.2, 1.2, 1.2)); c.key('eye_glow', 'scale', 1.2, (1, 1, 1))
    clips.append(c)
    # weakpoint_open: from downed, armour plates swing open, core swells and holds
    c = Clip('weakpoint_open', 1.4, 'hold')
    for t, ang, sc, extra in ((0, 0, 1.1, 0), (0.25, 25, 1.2, 1), (0.6, 80, 1.45, 2), (0.9, 95, 1.3, 2), (1.4, 92, 1.35, 2)):
        rot, pos = walker_downed(1.0)
        pos['body'] = (0, pos['body'][1] - extra, 0)
        keyframe_pose(c, t, rot, pos)
        c.key('plate_l', 'rotation', t, (0, ang, 0)); c.key('plate_r', 'rotation', t, (0, -ang, 0))
        c.key('weakpoint_glow', 'scale', t, (sc, sc, sc))
    clips.append(c)
    c = Clip('recover', 1.6, 'once')
    for t, k, ang, sc in ((0, 1.0, 92, 1.35), (0.4, 0.95, 70, 1.2), (0.9, 0.35, 10, 1.05), (1.2, -0.08, 0, 1.0), (1.6, 0, 0, 1.0)):
        rot, pos = walker_downed(max(k, 0)) if k >= 0 else (dict(body=(-2, 0, -1)), dict(body=(0, 1.5, 0)))
        if k < 0:
            for leg, *_ in WALKER_LEGS4:
                r, q = walker4_leg(leg); rot.update(r); pos.update(q)
        keyframe_pose(c, t, rot, pos)
        c.key('plate_l', 'rotation', t, (0, ang, 0)); c.key('plate_r', 'rotation', t, (0, -ang, 0))
        c.key('weakpoint_glow', 'scale', t, (sc, sc, sc))
    clips.append(c)
    # death: every leg splays like the broken one (mirrored solution keeps feet on the ground), hull slams
    # down and rolls, eye and core burn out
    c = Clip('death', 2.6, 'hold')
    hz_, kz, d = WALKER_DOWNED['fl']
    for t, k, roll, extra in ((0, 0, 0, 0), (0.2, 0.15, -3, -2), (0.7, 0.75, 6, 0), (1.05, 1.08, 11, 3), (1.35, 0.98, 9, 1), (2.6, 1.0, 10, 1.5)):
        rot = {'body': (5 * k, 3 * k, roll), 'head': (22 * k, 12 * k, 4 * k)}
        pos = {'body': (0, -(d + extra) * k, 0)}
        for leg, *_ in WALKER_LEGS4:
            sgn = 1 if leg.endswith('l') else -1
            rot[f'leg_{leg}'] = (0, 0, sgn * hz_ * k)
            rot[f'leg_{leg}_low'] = (0, 0, sgn * kz * k)
            pos[f'leg_{leg}'] = (0, -(d + extra) * k, 0)
        keyframe_pose(c, t, rot, pos, interp='linear' if t <= 1.05 else 'catmullrom',
                      scale={'weakpoint_glow': (max(0.01, 1 - t / 2.2),) * 3, 'eye_glow': (max(0.01, 1 - t / 1.2),) * 3})
    clips.append(c)
    return clips


# =========================================================================================== r4
# r4 (user feedback "materials/shaders look missing"): every enemy is an ORIGINAL authored cube model with
# hand-painted per-face pixel textures in the House of Devils palette (measured from the reference images in
# w300-evidence/models/r4/refs, see models.md). Nothing is voxelised and no source texture is sampled.
HOD = dict(   # hex values in models.md
    ivory=(0.843, 0.765, 0.671), ivory_dk=(0.733, 0.647, 0.557), bone=(0.80, 0.74, 0.62),
    rust=(0.565, 0.200, 0.150), crimson=(0.604, 0.188, 0.149), crimson_dk=(0.40, 0.125, 0.10),
    skin=(0.40, 0.349, 0.447), suit=(0.341, 0.365, 0.400), leather=(0.553, 0.416, 0.298),
    metal=(0.30, 0.314, 0.345), joint=(0.165, 0.157, 0.188), claw=(0.86, 0.80, 0.68),
    arc=(0.60, 0.88, 1.0), arc_hot=(0.93, 0.99, 1.0), eye=(0.55, 0.92, 1.0), eye_hot=(0.88, 1.0, 1.0),
    sand=(0.773, 0.639, 0.525), sand_lt=(0.851, 0.714, 0.557), sand_dk=(0.686, 0.565, 0.486),
    red=(0.663, 0.271, 0.294), gun=(0.227, 0.239, 0.275), orange=(1.0, 0.62, 0.24), orange_hot=(1.0, 0.86, 0.55))
CHIP = np.array([0.42, 0.31, 0.24]); DIRT = np.array([0.45, 0.36, 0.28]); SEAM = np.array([0.32, 0.24, 0.20])
PAINT = dict(density=3.0, clip=64)

def paint_tex(mat, rgb, w, h, seed, fn, opts):
    """Hand-painted pixel material (float rgb (h, w, 3)). Structured, low-noise: gradient, rims, seams,
    rivets, chips, dirt, folds, hems and markings, chosen per material."""
    rng = np.random.default_rng(seed)
    base = np.array(rgb, float)
    side = fn not in ('up', 'down')
    f = np.ones((h, w))
    if side:
        f *= np.linspace(1.10, 0.86, h)[:, None]
    else:
        f *= 1.05 if fn == 'up' else 0.92
    f *= 1 + rng.normal(0, 0.018, (h, w))
    col = base[None, None, :] * f[:, :, None]
    ys, xs = np.mgrid[0:h, 0:w]
    if mat in ('armor', 'sandarmor'):
        col[0, :] *= 1.20; col[:, 0] *= 1.08; col[-1, :] *= 0.70; col[:, -1] *= 0.86
        for (yy, xx) in [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]:
            if rng.random() < 0.10:
                col[yy, xx] = CHIP * (0.9 + 0.2 * rng.random())
        if side and h >= 4:
            t = np.clip((ys - h * 0.6) / max(h * 0.4, 1), 0, 1)[:, :, None] * 0.22
            col = col * (1 - t) + DIRT * t
        if 'mark' in opts and side and w >= 3 and h >= 4:
            red = np.array(HOD['red'] if mat == 'sandarmor' else HOD['rust'])
            y0 = max(1, int(h * 0.25)); band = max(1, h // 6)
            col[y0:y0 + band, 1:w - 1] = red * (0.95 + 0.1 * rng.random())
            if w >= 8 and h >= 8:   # chevron under the band
                for x in range(1, w - 1):
                    y = y0 + band + 1 + abs(x - w // 2) // 2
                    if y < h - 1 and abs(x - w // 2) < w // 3:
                        col[y, x] = red * 0.9
        if w >= 10 and h >= 8:
            col[1:-1, w // 2] = SEAM * 0.9 + col[1:-1, w // 2] * 0.1
            for (x, y) in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
                col[y, x] = base * 0.55; col[y - 1, x] = base * 1.22
    elif mat == 'cloth':
        period = 5 + (seed % 3)
        fold = 1 + 0.14 * np.sin(2 * np.pi * xs / period + seed % 7)
        col *= fold[:, :, None]
        if side:
            col[0, :] *= 0.72
            if 'hem' in opts:
                for x in range(w):
                    L = int(rng.integers(1, 2 + max(1, h // 5)))
                    col[h - L:, x] = np.array(HOD['crimson_dk']) * 0.7
                    if h - L - 1 >= 0:
                        col[h - L - 1, x] *= 0.82
    elif mat == 'suit':
        col[::4, :] *= 0.80
        col[0, :] *= 1.15; col[-1, :] *= 0.78
    elif mat == 'leather':
        col[(xs + ys) % 4 == 0] *= 0.76
        col[(xs + ys) % 4 == 1] *= 1.10
        col[0, :] *= 1.12; col[-1, :] *= 0.75
    elif mat == 'skin':
        col[2::3, :] *= 0.82
        col[1::3, :] *= 1.06
    elif mat in ('metal', 'gun'):
        col[0, :] *= 1.30; col[:, 0] *= 1.12; col[-1, :] *= 0.68
        if h >= 6:
            col[h // 2, 1:-1] *= 0.72
        if w >= 8:
            col[1:-1, 2] *= 1.18
    elif mat == 'joint':
        col[0, :] *= 1.45; col[:, 0] *= 1.15
    elif mat == 'claw':
        if side:
            col *= np.linspace(0.78, 1.15, h)[:, None, None]
    return np.clip(col, 0, 1)

def paint_cell(img, x0, y0, painter):
    _, mat, rgb, w, h, seed, fn, opts = painter
    img[y0:y0 + h, x0:x0 + w, :3] = paint_tex(mat, rgb, w, h, seed, fn, opts) * 255
    img[y0:y0 + h, x0:x0 + w, 3] = 255

def pbox(bone, center, size, mat, color=None, M=None, glow=False, opts=(), faces=None):
    """Designed cube with a per-face hand-painted texture (glow parts use a flat bevel panel)."""
    rgb = color if color is not None else {'armor': HOD['ivory'], 'cloth': HOD['crimson'], 'suit': HOD['suit'],
            'leather': HOD['leather'], 'skin': HOD['skin'], 'metal': HOD['metal'], 'gun': HOD['gun'],
            'joint': HOD['joint'], 'claw': HOD['claw'], 'sandarmor': HOD['sand']}[mat]
    if glow:
        return box(bone, center, size, rgb, M=M, glow=True, edge=1.0)
    c = np.asarray(center, float); sz = np.asarray(size, float)
    fs = {}
    for fn, (na, high, ua, udesc, va, vdesc) in FACES.items():
        if faces is not None and fn not in faces:
            fs[fn] = None; continue
        tw = int(np.clip(round(sz[ua] * PAINT['density']), 2, PAINT['clip']))
        th = int(np.clip(round(sz[va] * PAINT['density']), 2, PAINT['clip']))
        seed = int(hashlib.sha1(f'{bone}{np.round(c, 3)}{np.round(sz, 3)}{fn}'.encode()).hexdigest()[:8], 16)
        fs[fn] = (1, 1, ('paint', mat, tuple(rgb), tw, th, seed, fn, tuple(opts)))
    rot = euler_zyx(M) if M is not None else (0, 0, 0)
    return Part(bone, c - sz / 2, c + sz / 2, fs, rot=rot, origin=c)

def pseg(bone, a, b, thick, mat, extend=0.0, **kw):
    """Cube spanning segment a->b (local -Y along the segment)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    M = seg_matrix(a, b)
    if np.allclose(M, np.eye(3), atol=1e-6):
        M = None
    return pbox(bone, (a + b) / 2, (thick[0], L + extend, thick[1]), mat, M=M, **kw)

class AuthoredRig:
    """Minimal stand-in for Source so the existing fallen/shank clip authors can be reused."""
    def __init__(self, pivots):
        self.frames = {}
        self.pivots = pivots

# ---------------------------------------------------------------------------------------- Fallen
FALLEN_KINDS = {
    #            width k, height k, cloak bottom y (dreg units), hood, eyes, stump lower-left, captain extras
    'rg_dreg': dict(kw=1.0, kh=1.0, cloak_low=9.0, hood=True, eyes=4, stump=True, heavy=False, rifle=False),
    'rg_vandal': dict(kw=0.95, kh=1.19, cloak_low=2.8, hood=False, eyes=4, stump=False, heavy=False, rifle=True),
    'rg_captain': dict(kw=1.32, kh=1.34, cloak_low=3.4, hood=False, eyes=6, stump=False, heavy=True, rifle=False),
}

def build_fallen(name, spec, ev, log):
    """House of Devils Fallen designed in Dreg units (1 unit = 1 px for the Dreg; 1.9-block hitbox) and
    scaled per kind: Vandal taller/slimmer (2.3 blocks), Captain bulkier (2.6 blocks)."""
    K = FALLEN_KINDS[name]
    kw, kh = K['kw'], K['kh']
    S = np.array([kw, kh, kw])
    P = lambda *v: np.array(v, float) * S
    Z = lambda *v: np.array(v, float) * S        # sizes
    T2 = lambda a, b: np.array([a * kw, b * kw])  # limb cross-section
    parts, bones = [], []
    def add(p):
        parts.append(p)
    def bone(nm, parent, origin, glow=False):
        bones.append(dict(name=nm, parent=parent, origin=tuple(np.round(origin, 4)), glow=glow))
    heavy = K['heavy']
    bone('root', None, (0, 0, 0))
    bone('hips', 'root', P(0, 14, 0.2))
    # ---- legs (digitigrade: thigh forward-down, shin back-down, metatarsal forward-down)
    for sd, sx in (('l', -1), ('r', 1)):
        H = P(sx * 2.0, 14, 0.2); Kn = P(sx * 2.3, 9.0, -1.6); A = P(sx * 2.3, 3.6, 1.5); T = P(sx * 2.3, 0.35, -0.5)
        bone(f'thigh_{sd}', 'hips', H)
        bone(f'shin_{sd}', f'thigh_{sd}', Kn)
        add(pseg(f'thigh_{sd}', H, Kn, T2(2.1, 2.1), 'suit', extend=0.6))
        add(pseg(f'thigh_{sd}', H + P(0, -0.6, -0.9), Kn + P(0, 0.6, -0.9), T2(1.9, 0.6), 'armor', opts=('mark',)))
        add(pbox(f'shin_{sd}', Kn + P(0, 0, -0.3), Z(2.4, 2.2, 2.4) * (1.15 if heavy else 1), 'armor'))
        add(pseg(f'shin_{sd}', Kn, A, T2(1.6, 1.6), 'skin'))
        add(pseg(f'shin_{sd}', Kn + P(0, -0.5, -0.8), A + P(0, 1.2, -0.7), T2(1.7, 0.5), 'armor'))
        add(pseg(f'shin_{sd}', (Kn + A) / 2 + P(0, -0.4, 0), (Kn + A) / 2 + P(0, -1.6, 0.3), T2(1.9, 1.9), 'leather'))
        add(pbox(f'shin_{sd}', A, Z(1.7, 1.5, 1.7), 'joint'))
        add(pseg(f'shin_{sd}', A, T, T2(1.3, 1.3), 'skin'))
        add(pbox(f'shin_{sd}', T + P(0, 0.1, 0.3), Z(1.8, 0.8, 2.2), 'leather'))
        for dx in (-0.6, 0.0, 0.6):
            add(pbox(f'shin_{sd}', T + P(dx, -0.1, -1.4), Z(0.45, 0.5, 1.5), 'claw'))
        add(pbox(f'shin_{sd}', T + P(0, 0.2, 1.4), Z(0.45, 0.5, 1.2), 'claw'))
    # ---- hips: pelvis, belt, loincloth
    add(pbox('hips', P(0, 14.6, 0.2), Z(4.4, 2.4, 3.0), 'suit'))
    add(pbox('hips', P(0, 15.9, 0.2), Z(4.8, 1.0, 3.4), 'leather'))
    add(pbox('hips', P(0, 16.0, -1.65), Z(1.4, 1.2, 0.5), 'metal'))
    add(pbox('hips', P(0, 12.3, -1.6), Z(2.6, 4.6, 0.5), 'cloth', opts=('hem',)))
    if heavy:
        for sx in (-1, 1):
            add(pbox('hips', P(sx * 2.0, 13.6, -0.2), Z(1.4, 3.0, 3.2), 'armor', opts=('mark',)))
    # ---- torso
    bone('torso', 'hips', P(0, 16.2, 0.2))
    add(pbox('torso', P(0, 17.8, 0.3), Z(3.2, 3.2, 2.4), 'skin'))
    add(pbox('torso', P(0, 21.6, 0.2), Z(5.4, 5.0, 3.6), 'suit'))
    add(pbox('torso', P(0, 21.9, -1.85), Z(4.8, 4.0, 0.7) * (1.12 if heavy else 1), 'armor', opts=('mark',)))
    add(pbox('torso', P(0, 18.9, -1.4), Z(3.4, 1.6, 0.6), 'armor'))
    add(pbox('torso', P(0, 24.6, 0.2), Z(6.2, 1.2, 3.8), 'armor'))
    add(pbox('torso', P(0, 21.0, 2.0), Z(1.0, 6.5, 0.6), 'leather'))
    if heavy:   # back pack with arc coils
        add(pbox('torso', P(0, 22.0, 2.6), Z(4.0, 4.6, 1.6), 'metal'))
        add(pbox('torso', P(0, 24.6, 2.6), Z(4.4, 0.8, 1.9), 'armor'))
        bone('pack_glow', 'torso', P(0, 22, 3.5), glow=True)
        for sx in (-1, 1):
            add(pbox('pack_glow', P(sx * 1.1, 22.0, 3.5), Z(0.8, 3.2, 0.5), 'metal', color=HOD['arc'], glow=True))
        add(pbox('pack_glow', P(0, 23.4, 3.55), Z(2.6, 0.5, 0.5), 'metal', color=HOD['arc_hot'], glow=True))
    # ---- cape (sways in walk/run)
    bone('cape', 'torso', P(0, 24.6, 2.0))
    top_y, low_y = 24.6, K['cloak_low']
    Lc = top_y - low_y
    tilt = rot_zyx((-7, 0, 0))
    add(pbox('cape', P(0, 25.1, 0.6), Z(6.8, 2.0, 4.4), 'cloth'))                         # mantle
    add(pbox('cape', P(0, top_y - Lc / 2, 2.4 + Lc * 0.06), Z(6.2, Lc, 0.6), 'cloth', M=tilt, opts=('hem',)))
    for sx in (-1, 1):
        add(pbox('cape', P(sx * 3.2, top_y - Lc * 0.42, 1.5), Z(0.6, Lc * 0.8, 2.4), 'cloth', opts=('hem',)))
        add(pbox('cape', P(sx * 1.9, low_y - 1.0, 2.6 + Lc * 0.12), Z(1.3, 2.4, 0.5), 'cloth', M=tilt, opts=('hem',)))
    add(pbox('cape', P(0.4, low_y - 1.6, 2.7 + Lc * 0.12), Z(1.0, 2.0, 0.5), 'cloth', M=tilt, opts=('hem',)))
    if heavy:   # captain fur-trimmed mantle
        add(pbox('cape', P(0, 25.9, 0.9), Z(7.6, 1.4, 4.6), 'leather'))
    # ---- head
    bone('head', 'torso', P(0, 25.5, -0.1))
    add(pbox('head', P(0, 25.9, -0.3), Z(1.4, 1.6, 1.4), 'skin'))
    add(pbox('head', P(0, 27.6, -0.4), Z(3.0, 2.6, 3.2), 'skin'))
    add(pbox('head', P(0, 27.4, -2.15), Z(3.2, 2.2, 0.7), 'armor', opts=('mark',)))
    add(pbox('head', P(0, 26.2, -1.8), Z(2.0, 1.0, 1.2), 'joint'))
    add(pbox('head', P(0, 29.2, -0.4), Z(3.4, 1.0, 3.6), 'armor'))
    if K['hood']:
        add(pbox('head', P(0, 28.1, 1.1), Z(3.9, 3.4, 2.4), 'cloth', opts=('hem',)))
        add(pbox('head', P(0, 29.9, 0.3), Z(3.6, 0.7, 2.6), 'cloth'))
    add(pbox('head', P(0, 30.1, 0.0), Z(0.5, 1.4, 3.0), 'armor'))
    horn = 1.6 if heavy else 1.0
    for sx in (-1, 1):
        a = P(sx * 1.1, 29.4, 0.2); b = a + P(sx * 0.7, 1.6 * horn, 2.4 * horn)
        add(pseg('head', a, b, T2(0.6, 0.6) * (1.3 if heavy else 1), 'armor'))
        if heavy:
            c2 = b + P(sx * 0.8, 2.2, -0.2)
            add(pseg('head', b, c2, T2(0.5, 0.5), 'claw'))
            add(pseg('head', P(sx * 1.6, 28.4, -0.6), P(sx * 2.8, 29.8, -0.2), T2(0.5, 0.5), 'armor'))
    bone('eyes_glow', 'head', P(0, 27.5, -2.5), glow=True)
    eyes = [(-0.75, 27.9, 0.75, 0.55), (0.75, 27.9, 0.75, 0.55), (-0.55, 27.05, 0.55, 0.45), (0.55, 27.05, 0.55, 0.45)]
    if K['eyes'] == 6:
        eyes += [(-1.25, 28.45, 0.45, 0.4), (1.25, 28.45, 0.45, 0.4)]
    for ex, ey, ew, eh in eyes:
        add(pbox('eyes_glow', P(ex, ey, -2.62), Z(ew, eh, 0.35), 'metal', color=HOD['eye'], glow=True))
    # ---- arms
    def arm(pair, sx, sh, length=5.0, stump=False, small=False):
        up, fa = f'uarm_{pair}', f'farm_{pair}'
        sh = np.asarray(sh, float)
        el = sh + P(0, -length * (0.5 if stump else 1) * (0.85 if small else 1), 0)
        bone(up, 'torso', sh); bone(fa, up, el)
        t = 0.85 if small else 1.0
        add(pseg(up, sh, el, T2(1.5, 1.5) * t, 'suit'))
        if stump:
            add(pbox(up, el + P(0, 0.2, 0), Z(1.7, 1.0, 1.7), 'leather'))
            add(pbox(fa, el + P(0, -0.3, 0), Z(0.9, 0.6, 0.9), 'leather'))
            return el
        if pair.startswith('u'):
            add(pbox(up, sh + P(sx * 0.35, -0.3, 0), Z(2.5, 1.7, 2.5) * (1.35 if heavy else 1), 'armor', opts=('mark',)))
            if heavy:
                add(pseg(up, sh + P(sx * 1.6, 0.6, 0), sh + P(sx * 2.6, 2.2, 0.6), T2(0.5, 0.5), 'claw'))
        add(pbox(up, sh + P(0, -length * 0.62, 0), Z(1.8, 0.9, 1.8) * t, 'leather'))
        hand = el + P(0, -4.6 * t, 0)
        add(pseg(fa, el, hand, T2(1.3, 1.3) * t, 'skin'))
        add(pbox(fa, el + P(0, -2.1 * t, 0), Z(1.65, 2.4, 1.65) * t * (1.15 if heavy else 1), 'armor'))
        add(pbox(fa, hand + P(0, -0.3, 0), Z(1.45, 1.0, 1.2) * t, 'leather'))
        for dx in (-0.45, 0.45):
            add(pbox(fa, hand + P(dx, -1.4, -0.15), Z(0.4, 1.4, 0.4), 'claw'))
        add(pbox(fa, hand + P(0, -1.1, 0.5), Z(0.4, 1.0, 0.4), 'claw'))
        return hand + P(0, -0.6, 0)
    palms = {}
    for sx, s in ((-1, 'l'), (1, 'r')):
        palms['u' + s] = arm('u' + s, sx, P(sx * 3.4, 23.8, 0.2))
        palms['l' + s] = arm('l' + s, sx, P(sx * 2.9, 21.0, 0.4),
                             stump=K['stump'] and s == 'l', small=K['stump'] and s == 'r')
    # ---- weapon (right upper hand; barrel along the forearm axis, aimed by the shoot pose)
    pw = palms['ur']
    bone('weapon', 'farm_ur', pw)
    bone('weapon_glow', 'weapon', pw, glow=True)
    if K['rifle']:    # Vandal wire rifle
        add(pbox('weapon', pw + P(0, -0.2, 0.2), Z(1.0, 1.6, 1.2), 'leather'))
        add(pbox('weapon', pw + P(0, -3.5, 0.0), Z(1.3, 6.0, 1.8), 'gun'))
        add(pbox('weapon', pw + P(0, -3.0, -1.2), Z(1.1, 4.0, 0.6), 'armor', opts=('mark',)))
        add(pbox('weapon', pw + P(0, -9.5, 0.0), Z(0.6, 6.0, 0.6), 'metal'))
        add(pbox('weapon', pw + P(0, -2.2, 1.35), Z(0.7, 2.6, 0.9), 'metal'))
        add(pbox('weapon', pw + P(0, 1.8, 0.4), Z(0.9, 2.6, 1.0), 'armor'))
        for dy in (-2.0, -4.6):
            add(pbox('weapon_glow', pw + P(0, dy, 1.0), Z(0.7, 1.2, 0.5), 'metal', color=HOD['arc'], glow=True))
        add(pbox('weapon_glow', pw + P(0, -12.6, 0), Z(0.8, 0.4, 0.8), 'metal', color=HOD['arc_hot'], glow=True))
    else:             # Dreg shock pistol / Captain shock rifle
        L = 1.5 if heavy else 1.0
        add(pbox('weapon', pw + P(0, -1.8 * L, 0.3), Z(1.2, 3.4 * L, 1.8), 'gun'))
        add(pbox('weapon', pw + P(0, -1.6 * L, -0.85), Z(1.0, 2.2 * L, 0.6), 'armor', opts=('mark',)))
        add(pbox('weapon', pw + P(0, -4.2 * L, 0), Z(0.7, 2.4 * L, 0.7), 'metal'))
        add(pbox('weapon_glow', pw + P(0, -1.4 * L, 1.35), Z(0.8, 1.4 * L, 0.45), 'metal', color=HOD['arc'], glow=True))
        add(pbox('weapon_glow', pw + P(0, -5.5 * L, 0), Z(0.9, 0.4, 0.9), 'metal', color=HOD['arc_hot'], glow=True))
    # ---- shock blade
    if name in ('rg_dreg', 'rg_captain'):
        hand = 'ul' if name == 'rg_dreg' else 'lr'
        pb = palms[hand]
        bone('blade', 'farm_' + hand, pb)
        bone('blade_glow', 'blade', pb, glow=True)
        L = 1.3 if heavy else 1.0
        add(pbox('blade', pb + P(0, -0.4, 0), Z(0.6, 1.4, 0.6), 'leather'))
        add(pbox('blade', pb + P(0, -1.25, 0), Z(1.5, 0.4, 0.9), 'metal'))
        add(pbox('blade', pb + P(0, -1.45 - 2.4 * L, 0.1), Z(0.4, 4.8 * L, 1.2), 'metal'))
        add(pbox('blade_glow', pb + P(0, -1.6 - 2.3 * L, -0.65), Z(0.3, 4.2 * L, 0.3), 'metal', color=HOD['arc'], glow=True))
    clip_src = AuthoredRig({b['name']: np.asarray(b['origin']) for b in bones})
    clips = fallen_clips(name, spec, clip_src, bones)
    add_cape_sway(clips)
    meta = {'generator': GENERATOR, 'source': 'original authored (House of Devils references, see models.md)',
            'geometry': 'designed cubes r4', 'texture': 'hand-painted per face (procedural pixel painter)',
            'animations': 'original authored', 'credit': 'W300 r4 authored Fallen; reference: Bungie/Destiny concept art (palette only)'}
    return finish_authored(name, spec, ev, log, bones, parts, clips, meta)

def add_cape_sway(clips):
    for c in clips:
        if c.name in ('walk', 'run'):
            amp = 10 if c.name == 'walk' else 22
            c.curve('cape', 'rotation', lambda f, a=amp: (a * (0.6 + 0.4 * math.sin(4 * math.pi * f)), 0, 2 * math.sin(2 * math.pi * f)))
        elif c.name == 'idle':
            c.curve('cape', 'rotation', lambda f: (3 + 2 * math.sin(2 * math.pi * f), 0, 1.5 * math.sin(2 * math.pi * f + 1)))
        elif c.name in ('hit', 'stagger'):
            c.key('cape', 'rotation', 0, (0, 0, 0)); c.key('cape', 'rotation', c.length * 0.3, (14, 0, 4)); c.key('cape', 'rotation', c.length, (0, 0, 0))

# ----------------------------------------------------------------------------------------- Shank
def build_shank(name, spec, ev, log):
    """House of Devils Shank: ivory dome with red band, blue eye, under-slung arc gun, thruster pods
    (wing_u*) and four dangling spider legs (wing_l* hold the front/back pairs). ~0.9 block hitbox."""
    parts, bones = [], []
    add = parts.append
    def bone(nm, parent, origin, glow=False):
        bones.append(dict(name=nm, parent=parent, origin=tuple(np.round(origin, 4)), glow=glow))
    C = np.array([0.0, 7.5, 0.0])
    bone('root', None, (0, 0, 0)); bone('body', 'root', C)
    add(pbox('body', C, (9, 7, 9), 'armor', opts=('mark',)))
    add(pbox('body', C + (0, 4.2, 0.3), (7, 1.6, 7), 'armor'))
    add(pbox('body', C + (0, 5.4, 0.5), (4, 1.0, 4), 'armor'))
    add(pbox('body', C + (0, -4.0, 0), (7.4, 1.4, 7.4), 'suit'))
    add(pbox('body', C + (0, 1.6, 0), (9.4, 1.0, 9.4), 'cloth', color=HOD['red']))
    add(pbox('body', C + (0, 0, -4.7), (5.4, 5.4, 0.6), 'metal'))                       # eye socket plate
    add(pbox('body', C + (0, 3.2, 4.6), (3.0, 2.0, 1.2), 'metal'))                      # rear vent
    for sx in (-1, 1):
        add(pbox('body', C + (sx * 2.4, 5.9, 1.2), (0.4, 2.4, 0.4), 'joint'))           # antennae
    bone('eye_glow', 'body', C + (0, 0, -5.2), glow=True)
    add(pbox('eye_glow', C + (0, 0, -5.1), (3.2, 3.2, 0.5), 'metal', color=HOD['eye'], glow=True))
    add(pbox('eye_glow', C + (0, 0, -5.45), (1.4, 1.4, 0.3), 'metal', color=HOD['eye_hot'], glow=True))
    bone('gun', 'body', C + (0, -4.0, -2.0))
    add(pbox('gun', C + (0, -4.8, -2.4), (3.0, 2.0, 3.4), 'gun'))
    for dx, dy in ((-0.7, -4.4), (0.7, -4.4), (0, -5.3)):
        add(pbox('gun', C + (dx, dy, -6.0), (0.7, 0.7, 4.2), 'metal'))
    add(pbox('gun', C + (0, -4.8, -8.3), (2.6, 2.4, 0.6), 'gun'))
    for nm, sx in (('wing_ul', -1), ('wing_ur', 1)):                                     # thruster pods
        piv = C + (sx * 4.5, 1.0, 0.5)
        bone(nm, 'body', piv)
        add(pbox(nm, piv + (sx * 1.4, 0, 0), (2.6, 3.4, 3.8), 'metal'))
        add(pbox(nm, piv + (sx * 1.5, 0, 2.2), (2.0, 2.4, 0.6), 'joint'))
        add(pbox(nm, piv + (sx * 1.6, 2.0, 0), (2.2, 0.6, 3.0), 'armor', opts=('mark',)))
    for nm, sx in (('wing_ll', -1), ('wing_lr', 1)):                                    # leg pairs
        piv = C + (sx * 3.2, -3.6, 0)
        bone(nm, 'body', piv)
        for dz in (-2.4, 2.4):
            a = piv + (0, 0, dz); kn = a + (sx * 2.6, -1.2, dz * 0.4); ft = kn + (sx * 0.6, -3.6, dz * 0.15)
            add(pseg(nm, a, kn, (0.8, 0.8), 'suit'))
            add(pbox(nm, kn, (1.1, 1.1, 1.1), 'joint'))
            add(pseg(nm, kn, ft, (0.6, 0.6), 'metal'))
            add(pbox(nm, ft + (0, -0.4, 0), (0.5, 0.9, 0.5), 'claw'))
    clips = shank_clips(bones) + [shank_spawn()]
    meta = {'generator': GENERATOR, 'source': 'original authored (House of Devils references)', 'geometry': 'designed cubes r4',
            'animations': 'original authored', 'credit': 'W300 r4 authored Shank'}
    return finish_authored(name, spec, ev, log, bones, parts, clips, meta)

def shank_spawn():
    c = Clip('spawn', 1.2, 'once')
    for t, y, sc, leg, sp in ((0, 24, 0.2, 60, 0), (0.45, 6, 0.9, 50, 300), (0.7, -1.5, 1.05, 10, 360), (0.9, 0.6, 1.0, -4, 360), (1.2, 0, 1.0, 0, 360)):
        c.key('body', 'position', t, (0, y, 0)); c.key('body', 'scale', t, (sc, sc, sc))
        c.key('body', 'rotation', t, (0, sp, 0))
        c.key('wing_ll', 'rotation', t, (0, 0, -leg)); c.key('wing_lr', 'rotation', t, (0, 0, leg))
    c.key('eye_glow', 'scale', 0, (0.01, 0.01, 0.01)); c.key('eye_glow', 'scale', 0.7, (1.5, 1.5, 1.5)); c.key('eye_glow', 'scale', 1.2, (1, 1, 1))
    return c

# ----------------------------------------------------------------------------------------- Skiff
def build_skiff(name, spec, ev, log):
    """House of Devils skiff (dropship), ~15 blocks long: sand/ivory hull with red bands, dark keel and
    cockpit slits, side gun pods, under-slung drop clamps and twin aft engines. Front = -Z."""
    parts, bones = [], []
    add = parts.append
    def bone(nm, parent, origin, glow=False):
        bones.append(dict(name=nm, parent=parent, origin=tuple(np.round(origin, 4)), glow=glow))
    PAINT['density'] = 0.5; PAINT['clip'] = 48
    bone('root', None, (0, 0, 0)); bone('hull', 'root', (0, 0, 0))
    secs = [(-120, -96, 22, 18, 2), (-96, -60, 40, 30, 1), (-60, -10, 56, 40, 0), (-10, 50, 60, 42, 0), (50, 96, 50, 36, 0), (96, 120, 36, 28, 1)]
    for z0, z1, w, h, taper in secs:
        add(pbox('hull', (0, 0, (z0 + z1) / 2), (w, h, z1 - z0), 'sandarmor', opts=('mark',)))
        add(pbox('hull', (0, h / 2 + 2, (z0 + z1) / 2), (w * 0.66, 4, (z1 - z0) - 4), 'sandarmor'))
        add(pbox('hull', (0, -h / 2 - 2.5, (z0 + z1) / 2), (w * 0.7, 5, (z1 - z0) - 2), 'gun'))
    for sx in (-1, 1):
        add(pbox('hull', (sx * 30.5, 4, 20), (2, 10, 100), 'cloth', color=HOD['red']))
        add(pbox('hull', (sx * 21, 9, -70), (2, 4, 30), 'joint'))                      # cockpit slits
        for z in (-30, 0, 30, 60):
            add(pbox('hull', (sx * 30.8, -6, z), (2, 6, 10), 'joint'))                 # vents
    add(pbox('hull', (0, 24, 30), (6, 10, 50), 'sandarmor', opts=('mark',)))          # dorsal spine
    add(pbox('hull', (0, 30, 40), (2, 6, 20), 'cloth', color=HOD['red']))
    for sx in (-1, 1):                                                                 # aft engines
        add(pbox('hull', (sx * 15, 0, 124), (18, 18, 12), 'metal'))
    bone('engines_glow', 'hull', (0, 0, 131), glow=True)
    for sx in (-1, 1):
        add(pbox('engines_glow', (sx * 15, 0, 130.6), (13, 13, 1.2), 'metal', color=(0.6, 0.9, 1.0), glow=True))
        add(pbox('engines_glow', (sx * 15, 0, 131.4), (7, 7, 0.8), 'metal', color=(0.95, 1.0, 1.0), glow=True))
    for nm, sx in (('gun_l', -1), ('gun_r', 1)):
        piv = (sx * 32, 0, -40)
        bone(nm, 'hull', piv)
        add(pbox(nm, (sx * 36, 0, -40), (8, 8, 24), 'gun'))
        add(pbox(nm, (sx * 36, 0, -60), (3, 3, 18), 'metal'))
        add(pbox(nm, (sx * 36, 5, -40), (8, 2, 20), 'sandarmor', opts=('mark',)))
    for nm, sx in (('clamp_l', -1), ('clamp_r', 1)):
        piv = (sx * 14, -24, 10)
        bone(nm, 'hull', piv)
        add(pbox(nm, (sx * 14, -30, 10), (5, 12, 50), 'gun'))
        add(pbox(nm, (sx * 12, -38, 10), (9, 4, 46), 'metal'))
        for z in (-12, 10, 32):
            add(pbox(nm, (sx * 9, -42, z), (3, 5, 4), 'joint'))
    PAINT['density'] = 3.0; PAINT['clip'] = 64
    clips = skiff_clips(bones)
    meta = {'generator': GENERATOR, 'source': 'original authored (House of Devils skiff)', 'geometry': 'designed cubes r4',
            'animations': 'original authored', 'credit': 'W300 r4 authored Fallen skiff'}
    return finish_authored(name, spec, ev, log, bones, parts, clips, meta)

# ------------------------------------------------------------------------------- Minecraft-like review
MC_SHADE = {'up': 1.0, 'down': 0.5, 'north': 0.8, 'south': 0.8, 'east': 0.6, 'west': 0.6}

def load_bbmodel_parts(path, tmpdir):
    d = json.load(open(path)); size = d['resolution']['width']
    png = os.path.join(tmpdir, os.path.basename(path) + '.png')
    open(png, 'wb').write(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))
    gid = {g['uuid']: g for g in d['groups']}; eb = {}; par = {}
    def w(n, p):
        g = gid[n['uuid']]; par[g['name']] = p
        for c in n['children']:
            if isinstance(c, str): eb[c] = g['name']
            else: w(c, g['name'])
    for r in d['outliner']: w(r, None)
    parts, uvs = [], {}
    for i, e in enumerate(d['elements']):
        faces = {fn: (None if f['texture'] is None else (1, 1, None)) for fn, f in e['faces'].items()}
        for fn, f in e['faces'].items():
            if f['texture'] is not None: uvs[(i, fn)] = f['uv']
        parts.append(Part(eb[e['uuid']], np.array(e['from']), np.array(e['to']), faces, glow=e.get('light_emission', 0) > 0,
                          rot=e.get('rotation', [0, 0, 0]), origin=e.get('origin', [0, 0, 0])))
    bones = [dict(name=g['name'], parent=par[g['name']], origin=g['origin']) for g in d['groups']]
    clips = {}
    for a in d.get('animations', []):
        c = Clip(a['name'], a['length'], a['loop'])
        for an in a['animators'].values():
            for k in an['keyframes']:
                p = k['data_points'][0]
                c.key(an['name'], k['channel'], k['time'], (float(p['x']), float(p['y']), float(p['z'])), k['interpolation'])
        clips[c.name] = c
    return parts, uvs, size, png, bones, clips

def render_mc(path, out_prefix, dists=(10, 3), clip='idle', t=0.3, sky=True, target_h=None):
    """Approximate in-game look: unlit texture x Minecraft face shade (up 1, N/S .8, E/W .6, down .5),
    glow faces at 1.0, sky-blue background, dirt ground, 70 deg vertical FOV, eye height 1.62 blocks."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tmp = os.path.dirname(out_prefix)
    parts, uvs, size, png, bones, clips = load_bbmodel_parts(path, tmp)
    img = bpy.data.images.load(png)
    mats = {}
    for key, f in list(MC_SHADE.items()) + [('glow', 1.0)]:
        m = bpy.data.materials.new('mc_' + key); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Closest'
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = f
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        # r4b: alpha-cutout cloth fringe (texture alpha 0 -> transparent), like an item model with a cutout texture
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(tx.outputs['Color'], em.inputs['Color']); nt.links.new(tx.outputs['Alpha'], mx.inputs['Fac'])
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
        for attr, val in (('surface_render_method', 'DITHERED'), ('blend_method', 'CLIP')):
            try: setattr(m, attr, val)
            except (AttributeError, TypeError): pass
        mats[key] = m
    order = list(mats)
    W = bone_world(bones, clips.get(clip), t if clip in clips else 0)
    Cm = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float) @ np.diag([1 / 16] * 3 + [1])
    verts, polys, puv, pmat = [], [], [], []
    for pi, p in enumerate(parts):
        Mp = rot_zyx(p.rot); Wb = W[p.bone]
        f, tt = p.frm, p.to
        for fn, (na, high, ua, udesc, va, vdesc) in FACES.items():
            if (pi, fn) not in uvs:
                continue
            u0, v0, u1, v1 = uvs[(pi, fn)]
            quad = []
            for (uu, vv) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                q = np.zeros(3)
                q[na] = tt[na] if high else f[na]
                q[ua] = (tt[ua] if not udesc else f[ua]) if uu else (f[ua] if not udesc else tt[ua])
                q[va] = (tt[va] if not vdesc else f[va]) if vv else (f[va] if not vdesc else tt[va])
                q = Mp @ (q - p.origin) + p.origin
                quad.append((Cm @ Wb @ np.append(q, 1))[:3])
            base = len(verts); verts += quad
            polys.append([base, base + 1, base + 2, base + 3])
            puv += [(u0 / size, 1 - v0 / size), (u1 / size, 1 - v0 / size), (u1 / size, 1 - v1 / size), (u0 / size, 1 - v1 / size)]
            # face shade by its world normal (Minecraft shades by the rendered face direction)
            nrm = np.cross(quad[1] - quad[0], quad[3] - quad[0]); nrm /= max(np.linalg.norm(nrm), 1e-9)
            want = np.zeros(3); want[na] = 1 if high else -1
            wn = (Cm[:3, :3] @ Wb[:3, :3] @ Mp @ want); wn /= np.linalg.norm(wn)
            if np.dot(nrm, wn) < 0:
                polys[-1] = polys[-1][::-1]
            if p.glow:
                pmat.append(order.index('glow'))
            else:
                ax = int(np.argmax(np.abs(wn))); sgn = wn[ax] > 0
                key = {(2, True): 'up', (2, False): 'down', (1, True): 'north', (1, False): 'south', (0, True): 'east', (0, False): 'west'}[(ax, sgn)]
                pmat.append(order.index(key))
    me = bpy.data.meshes.new('m'); me.from_pydata([tuple(v) for v in verts], [], polys)
    uvl = me.uv_layers.new()
    for li, uv in enumerate(puv): uvl.data[li].uv = uv
    for m in mats.values(): me.materials.append(m)
    me.polygons.foreach_set('material_index', pmat)
    ob = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(ob)
    gm = bpy.data.materials.new('ground'); gm.use_nodes = True
    gn = gm.node_tree; gn.nodes.clear(); ge = gn.nodes.new('ShaderNodeEmission'); ge.inputs['Color'].default_value = (0.20, 0.15, 0.12, 1)
    go = gn.nodes.new('ShaderNodeOutputMaterial'); gn.links.new(ge.outputs[0], go.inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.data.materials.append(gm)
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new('sky'); sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (0.47, 0.65, 1.0, 1); bg.inputs['Strength'].default_value = 1.0
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    cam = bpy.data.cameras.new('c'); cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(70); cam.clip_end = 500; cam.clip_start = 0.05
    co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
    pts = np.array(verts); h = float(pts[:, 2].max()) if target_h is None else target_h
    files = []
    for dname in dists:
        for vname, (dx, dy) in (('front', (0, 1)), ('q34', (0.7, 0.7))):
            d = Vector((dx, dy, 0)).normalized()
            co.location = Vector((0, 0, 1.62)) + d * dname
            look = Vector((0, 0, min(h * 0.55, 1.62 + 0.8) if dname <= 4 else h * 0.5))
            co.rotation_euler = (look - co.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f'{out_prefix}_{dname}m_{vname}.png'
            bpy.ops.render.render(write_still=True)
            files.append(sc.render.filepath)
    return files

# -------------------------------------------------------------------------------------------- skiff
def skiff_decor(src):
    hull = src.tris[src.bone == 'hull'].reshape(-1, 3)
    zb = float(hull[:, 2].max()); yc = float(np.median(hull[:, 1]))
    parts = []
    for x in (-1, 1):
        parts.append(box('engines_glow', (x * 4.5, yc, zb + 0.6), (4.5, 4.5, 1.2), (0.6, 0.9, 1.0), glow=True))
        parts.append(box('engines_glow', (x * 4.5, yc, zb + 1.3), (2.4, 2.4, 0.8), (0.95, 1.0, 1.0), glow=True))
    return parts, [dict(name='engines_glow', parent='hull', origin=(0, yc, zb), glow=True)]

def skiff_clips(bones):
    clips = []
    c = Clip('idle', 3.0, 'loop')
    c.curve('hull', 'position', lambda f: (0, 3 * math.sin(2 * math.pi * f), 0))
    c.curve('hull', 'rotation', lambda f: (1.2 * math.sin(2 * math.pi * f + 0.7), 0, 1.5 * math.sin(2 * math.pi * f)))
    c.curve('engines_glow', 'scale', lambda f: (1 + 0.08 * math.sin(6 * math.pi * f),) * 3)
    clips.append(c)
    c = Clip('arrive', 4.0, 'once')
    for t, y, z, rx in ((0, 260, 1400, -8), (1.6, 120, 420, -10), (2.8, 30, 60, 6), (3.5, 4, 8, 3), (4.0, 0, 0, 0)):
        c.key('hull', 'position', t, (0, y, z)); c.key('hull', 'rotation', t, (rx, 0, 0))
    clips.append(c)
    c = Clip('drop', 2.6, 'once')
    for t, a, y in ((0, 0, 0), (0.35, 40, -3), (0.6, 55, -6), (1.9, 55, -5), (2.6, 0, 0)):
        c.key('clamp_l', 'rotation', t, (0, 0, -a)); c.key('clamp_r', 'rotation', t, (0, 0, a))
        c.key('hull', 'position', t, (0, y, 0))
    clips.append(c)
    c = Clip('depart', 4.0, 'once')
    for t, y, z, rx in ((0, 0, 0, 0), (0.8, 40, 10, 8), (1.8, 140, -260, 4), (4.0, 420, -1800, -4)):
        c.key('hull', 'position', t, (0, y, z)); c.key('hull', 'rotation', t, (rx, 0, 0))
    c.key('engines_glow', 'scale', 0, (1, 1, 1)); c.key('engines_glow', 'scale', 0.8, (1.6, 1.6, 1.6)); c.key('engines_glow', 'scale', 4.0, (1.8, 1.8, 1.8))
    clips.append(c)
    return clips

# -------------------------------------------------------------------------------------------- ghost
SHELL = ['shell_a_top', 'shell_a_bottom', 'shell_a_left', 'shell_a_right',
         'shell_b_top', 'shell_b_bottom', 'shell_b_left', 'shell_b_right']

def axis_angle(axis, deg):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K

def shell_open_pose(k):
    """k 0..1: every petal flares its tip outward (rotation about its hinge edge) and slides radially."""
    rot, pos = {}, {}
    for b, (g, n, e, r3) in GHOST_PETALS.items():
        rot[b] = anim_of(axis_angle(e, 16 * k))
        d = r3 * 1.4 * k + g * 0.5 * k
        pos[b] = (-d[0], d[1], d[2])                 # animation position: x negated (Blockbench)
    return rot, pos

def key_shell(c, t, k, interp='catmullrom'):
    rot, pos = shell_open_pose(k)
    for b in rot:
        c.key(b, 'rotation', t, rot[b], interp)
        c.key(b, 'position', t, pos[b], interp)

def ghost_clips(bones):
    clips = []
    c = Clip('idle', 3.2, 'loop')
    c.curve('body', 'position', lambda f: (0, 0.9 * math.sin(2 * math.pi * f), 0))
    c.curve('body', 'rotation', lambda f: (3 * math.sin(2 * math.pi * f + 1), 7 * math.sin(2 * math.pi * f), 4 * math.sin(2 * math.pi * f + 2)))
    c.curve('shell', 'rotation', lambda f: (0, 0, 6 * math.sin(2 * math.pi * f)))
    for i in range(9):
        key_shell(c, i / 8 * c.length, 0.08 + 0.08 * math.sin(2 * math.pi * i / 8))
    clips.append(c)
    c = Clip('scan', 2.4, 'loop')
    n = 12
    for i in range(n + 1):
        f = i / n
        c.key('shell', 'rotation', f * c.length, (0, 0, 360 * f), 'linear')
        key_shell(c, f * c.length, 0.75 + 0.15 * math.sin(4 * math.pi * f))
        c.key('eye', 'scale', f * c.length, (1 + 0.25 * abs(math.sin(4 * math.pi * f)),) * 3)
    c.curve('body', 'position', lambda f: (0, 0.5 * math.sin(4 * math.pi * f), 0))
    clips.append(c)
    c = Clip('speak', 1.6, 'loop')
    c.curve('eye', 'scale', lambda f: (1 + 0.18 * max(0.0, math.sin(6 * math.pi * f)) + 0.06 * math.sin(14 * math.pi * f),) * 3, n=16)
    c.curve('body', 'rotation', lambda f: (4 * math.sin(4 * math.pi * f), 5 * math.sin(2 * math.pi * f), 0))
    c.curve('body', 'position', lambda f: (0, 0.5 * math.sin(2 * math.pi * f), 0))
    for i in range(17):
        f = i / 16
        key_shell(c, f * c.length, 0.15 + 0.25 * max(0.0, math.sin(6 * math.pi * f)))
    clips.append(c)
    c = Clip('shell_open', 0.6, 'hold')
    for t, k in ((0, 0), (0.18, 1.15), (0.35, 0.95), (0.6, 1.0)):
        key_shell(c, t, k)
        c.key('shell', 'rotation', t, (0, 0, 45 * min(1, t / 0.35)))
    clips.append(c)
    c = Clip('shell_close', 0.6, 'once')
    for t, k in ((0, 1.0), (0.3, 0.1), (0.42, -0.08), (0.6, 0)):
        key_shell(c, t, k)
        c.key('shell', 'rotation', t, (0, 0, 45 * (1 - min(1, t / 0.3))))
    clips.append(c)
    c = Clip('transmat', 0.9, 'hold')
    for t, sc, sp, es in ((0, 1, 0, 1), (0.15, 1.12, 90, 1.8), (0.55, 0.6, 540, 2.4), (0.9, 0.01, 900, 0.01)):
        c.key('body', 'scale', t, (sc, sc, sc)); c.key('shell', 'rotation', t, (0, 0, sp), 'linear')
        c.key('eye', 'scale', t, (es, es, es))
        key_shell(c, t, min(1.0, t * 3))
    clips.append(c)
    c = Clip('look', 2.0, 'once')
    for t, r in ((0, (0, 0, 0)), (0.35, (-4, -38, 4)), (0.85, (-6, -38, 4)), (1.2, (10, 30, -4)), (1.6, (8, 30, -4)), (2.0, (0, 0, 0))):
        c.key('body', 'rotation', t, r)
    for t, s in ((0, 1), (0.3, 1.15), (0.5, 1), (1.15, 1.15), (1.35, 1), (2.0, 1)):
        c.key('eye', 'scale', t, (s, s, s))
    clips.append(c)
    return clips

# --------------------------------------------------------------------------------------------- ship
def ship_clips(bones):
    clips = []
    c = Clip('idle', 4.0, 'loop')
    c.curve('engine_l_glow', 'scale', lambda f: (0.15 + 0.03 * math.sin(2 * math.pi * f),) * 3)
    c.curve('engine_r_glow', 'scale', lambda f: (0.15 + 0.03 * math.sin(2 * math.pi * f + 1),) * 3)
    c.curve('lights_glow', 'scale', lambda f: (1.0 if math.sin(2 * math.pi * f) > -0.2 else 0.4,) * 3, n=8)
    clips.append(c)
    c = Clip('power_up', 3.0, 'hold')
    for t, g, shake, gear in ((0, 0.15, 0, 0), (0.4, 0.5, 0.6, 0), (0.55, 0.25, -0.5, 0), (0.9, 0.8, 0.5, -1.5), (1.3, 0.6, -0.4, -1.5),
                              (2.0, 1.0, 0.3, -2.0), (3.0, 1.05, 0, -2.0)):
        for gb in ('engine_l_glow', 'engine_r_glow'):
            c.key(gb, 'scale', t, (g, g, g))
        c.key('body', 'rotation', t, (shake * 0.6, 0, shake))
        c.key('body', 'position', t, (0, gear, 0))
    clips.append(c)
    c = Clip('takeoff', 4.5, 'hold')
    for t, y, z, rx, gear, g in ((0, -2, 0, 0, 0, 1.05), (0.6, 8, 0, 2, 20, 1.2), (1.4, 48, 0, -4, 85, 1.35), (2.2, 80, -40, -8, 90, 1.5),
                                 (3.2, 140, -480, -10, 90, 1.9), (4.5, 300, -2400, -6, 90, 2.2)):
        # W301: the flight path (lift, hover, boost) and pitch are driven by Departure.fly() through the tracker
        # location so particles, camera and model share one trajectory; the clip only settles the gear squat.
        c.key('body', 'position', t, (0, -2 if t == 0 else 0, 0)); c.key('body', 'rotation', t, (0, 0, 0))
        for gb in ('gear_f', 'gear_l', 'gear_r'):
            c.key(gb, 'rotation', t, (-gear if gb == 'gear_f' else gear, 0, 0))
        for gb in ('engine_l_glow', 'engine_r_glow'):
            c.key(gb, 'scale', t, (g, g, g * 1.6))
    clips.append(c)
    return clips

def family_decor(name, spec, src, vox, voxel):
    fam = spec['family']
    if fam == 'fallen':
        return fallen_eyes(name, src, vox, voxel)
    if fam == 'shank':
        return shank_decor(src)
    if fam == 'walker':
        return walker_decor(src)
    if fam == 'skiff':
        return skiff_decor(src)
    return [], []

def family_clips(name, spec, src, bones):
    fam = spec['family']
    if fam == 'fallen':
        return fallen_clips(name, spec, src, bones)
    if fam == 'shank':
        return shank_clips(bones)
    if fam == 'walker':
        return walker_clips(bones)
    if fam == 'skiff':
        return skiff_clips(bones)
    return []

# ------------------------------------------------------------------------------------------ main
def render_model_review(name, parts, uvs, size, png, bones, ev, bounds=None):
    objs = build_preview_objects(name, parts, uvs, size, png, bones)
    return render_views(f'{ev}/{name}_cubes', list(objs.values()), bounds=bounds)

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = None; ev = EVIDENCE; render = True
    i = 0
    while i < len(argv):
        if argv[i] == '--only': only = argv[i + 1].split(','); i += 2
        elif argv[i] == '--evidence': ev = argv[i + 1]; i += 2
        elif argv[i] == '--no-render': render = False; i += 1
        else: raise SystemExit('unknown arg ' + argv[i])
    os.makedirs(ev, exist_ok=True)
    logf = open(os.path.join(ev, 'build.log'), 'a')
    def log(msg):
        print('[rising_models]', msg); logf.write(msg + '\n'); logf.flush()
    summary = {}
    for name, spec in SPECS.items():
        if only and name not in only:
            continue
        if spec.get('family_override'):
            spec = dict(spec, family=spec['family_override'])
        if spec['family'] == 'ship':
            res = build_ship(name, spec, ev, log)
        elif spec['family'] == 'ghost':
            res = build_ghost(name, spec, ev, log)
        elif spec['family'] == 'walker_authored':
            res = build_walker(name, spec, ev, log)
        elif spec['family'] == 'fallen_authored':
            res = build_fallen(name, spec, ev, log)
        elif spec['family'] == 'shank_authored':
            res = build_shank(name, spec, ev, log)
        elif spec['family'] == 'skiff_authored':
            res = build_skiff(name, spec, ev, log)
        else:
            res = build_source_model(name, spec, ev, log)
        path, parts, uvs, size, png, bones, clips, stats = res
        summary[name] = stats
        if render:
            if spec['family'] not in ('ship', 'walker_authored', 'fallen_authored', 'shank_authored', 'skiff_authored'):
                _, bounds = render_source(name, spec, ev)
            else:
                bounds = None
            render_model_review(name, parts, uvs, size, png, bones, ev, bounds)
            render_clip_frames(name, parts, uvs, size, png, bones, clips, ev)
    json.dump(summary, open(os.path.join(ev, 'summary.json'), 'w'), indent=1)


def sample_channel(keys, t, default):
    keys = sorted(keys, key=lambda k: k[0])
    if not keys:
        return np.array(default, float)
    if t <= keys[0][0]:
        return np.array(keys[0][1])
    for (t0, v0, _), (t1, v1, _) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return np.array(v0) * (1 - f) + np.array(v1) * f
    return np.array(keys[-1][1])

def bone_world(bones, clip, t):
    """Blockbench semantics: rotation (bedrock x/y negation) about the pivot, position with x negated (px)."""
    by = {b['name']: b for b in bones}
    out = {}
    def T(v):
        m = np.eye(4); m[:3, 3] = v; return m
    def get(name):
        if name in out:
            return out[name]
        b = by[name]
        tr = (clip.tracks.get(name, {}) if clip else {})
        r = sample_channel(tr.get('rotation', []), t, (0, 0, 0))
        p = sample_channel(tr.get('position', []), t, (0, 0, 0))
        sc = sample_channel(tr.get('scale', []), t, (1, 1, 1))
        R = np.eye(4); R[:3, :3] = local_R(r)
        S = np.diag([sc[0], sc[1], sc[2], 1.0])
        piv = np.asarray(b['origin'], float)
        L = T(np.array([-p[0], p[1], p[2]])) @ T(piv) @ R @ S @ T(-piv)
        W = get(b['parent']) @ L if b.get('parent') else L
        out[name] = W
        return W
    for b in bones:
        get(b['name'])
    return out

def render_clip_frames(name, parts, uvs, size, png, bones, clips, ev, frames=5):
    if not clips:
        return
    objs = build_preview_objects(name, parts, uvs, size, png, bones)
    C = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float) @ np.diag([1 / 16] * 3 + [1])
    Ci = np.linalg.inv(C)
    rows = []
    # common framing: rest + all clip extents would be ideal; use rest bounds scaled
    pts = [o.matrix_world @ v.co for o in objs.values() for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    pad = (hi - lo) * 0.08
    bounds = (lo - pad, hi + pad)
    for clip in clips:
        row = []
        for i in range(frames):
            t = clip.length * i / (frames - 1)
            W = bone_world(bones, clip, t)
            for bname, o in objs.items():
                o.matrix_world = Matrix((C @ W[bname] @ Ci).tolist())
            files, _ = render_views(f'{ev}/frames/{name}_{clip.name}_{i}', list(objs.values()),
                                    views={'q34': (0.75, 0.8, 0.45)}, res=240, bounds=bounds)
            row.append(files[0])
        rows.append(row)
    # contact sheet (rows = clips) using Blender image io
    tiles = []
    for row in rows:
        imgs = []
        for f in row:
            im = bpy.data.images.load(f)
            w, h = im.size
            px = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(px)
            a = px.reshape(h, w, 4)[::-1]
            bg = np.array([0.27, 0.29, 0.33])
            a = a[:, :, :3] * a[:, :, 3:4] + bg * (1 - a[:, :, 3:4])
            imgs.append(a)
        tiles.append(np.concatenate(imgs, 1))
    sheet = np.concatenate(tiles, 0)
    rgba = np.concatenate([np.clip(sheet, 0, 1) * 255, np.full(sheet.shape[:2] + (1,), 255)], 2).astype(np.uint8)
    open(f'{ev}/{name}_clips.png', 'wb').write(png_bytes(rgba))
    with open(f'{ev}/{name}_clips.txt', 'w') as f:
        f.write('rows top->bottom: ' + ', '.join(f'{c.name}({c.length}s,{c.loop})' for c in clips) + '\n')

if __name__ == '__main__':
    main()
