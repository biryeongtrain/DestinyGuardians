"""W300 r7 — reusable "Dreg-Light" baker: source FBX -> BetterModel .bbmodel made of axis-aligned zero-thickness quads.

Reproduces the technique of the adopted Dreg-Light handoff (~/Downloads/Dreg-Light-Handoff/Dreg-Light, read-only):
  * a small display rig (Fallen: 19 bones, bind pose = the D2 bind pose of the mapped 77-bone skeleton bones);
  * every source triangle belongs to one display bone (dominant skin weight -> nearest mapped ancestor; weapons
    to their weapon bone via the hand socket bone);
  * per bone and per axis direction (north/south/east/west/up/down) the bone's triangles are rasterised on a
    fine grid (1/13 px, head and hands 1/17 px) keeping the nearest surface seen from that side; the hit depth
    is quantised to absolute planes every 0.29 px (head and hands 0.18 px). Each occupied plane becomes ONE
    zero-thickness quad (bounding rect of its texels) with one textured face, cut from a <=2048 atlas with
    binary alpha. No element rotations;
  * colours come from the decoded source albedo (/tmp/w300_src_tex/<model>/<texture>.png, PNG decodes of the
    TexturesDDS) and are re-dyed per source material (House of Dusk palette) keeping the albedo value detail;
  * D2 clips (Dreg_77bone.fbx, 13 actions, 30 fps; fire/hurt additive on idle frame 0) are retargeted to
    parent-relative Blockbench position/rotation keys; Shank/Walker keep authored clips re-keyed to the new rig.

Two halves in one file:
  Blender headless:  Blender -b --python bake_dreglight.py -- dump <spec> <out.npz>
                     Blender -b --python bake_dreglight.py -- anim <out.npz>
  Python (numpy+PIL): python bake_dreglight.py bake <spec> <out.bbmodel> [--evidence DIR]
                     (runs the Blender halves itself; BLENDER env var overrides the Blender path)
"""
import json, math, os, sys

SRC = '/Users/qf/Downloads/Rising-Guardian-2026-11-01/models'
TEX = '/tmp/w300_src_tex'
ANIM_FBX = '/Users/qf/Downloads/Dreg-Light-Handoff/Dreg-Light/animations/Dreg_77bone.fbx'
BLENDER = os.environ.get('BLENDER', '/Applications/Blender.app/Contents/MacOS/Blender')

# ------------------------------------------------------------------------------------------------ specs
FALLEN_BONES = {   # display bone -> D2 skeleton bone (identical hashes on Dreg / Vandal / Captain, handoff original-clips.json)
    'hips': 'C7C0BA6E', 'chest': 'A152A6A2', 'head': '0E4EBB10',
    'thigh_l': '695DAF09', 'shin_l': '35B14D1B', 'foot_l': '0F8B505D',
    'thigh_r': '9F0FD28C', 'shin_r': '8BD44A3F', 'foot_r': 'B9B9E05D',
    'arm_l': 'D1232BA2', 'forearm_l': '897A1504', 'hand_l': '8C83CB67',
    'lower_arm_l': '5B58FBAF', 'lower_forearm_l': 'E350F14F',
    'arm_r': '17025F50', 'forearm_r': 'A3781DCD', 'hand_r': 'DE9D6BEA',
    'lower_arm_r': 'C10E6B03', 'lower_forearm_r': '85F82F11'}
FALLEN_PARENT = {'hips': None, 'chest': 'hips', 'head': 'chest', 'thigh_l': 'hips', 'shin_l': 'thigh_l', 'foot_l': 'shin_l',
                 'thigh_r': 'hips', 'shin_r': 'thigh_r', 'foot_r': 'shin_r', 'arm_l': 'chest', 'forearm_l': 'arm_l',
                 'hand_l': 'forearm_l', 'lower_arm_l': 'chest', 'lower_forearm_l': 'lower_arm_l', 'arm_r': 'chest',
                 'forearm_r': 'arm_r', 'hand_r': 'forearm_r', 'lower_arm_r': 'chest', 'lower_forearm_r': 'lower_arm_r'}
FALLEN_FINE = ('head', 'hand_l', 'hand_r')
# Hand weapon sockets (unweighted children of the hand bones): upper right/left, lower right/left.
SOCKET = {'hand_r': '19AB4BEF', 'hand_l': 'C3BCA7CA', 'lower_r': '932F47C8', 'lower_l': 'E582BC40'}

# Weapon grip in the hand_r socket frame, fitted (ICP, 0.18 px mean error) to the pistol texels of the adopted
# Dreg-Light handoff (hand_r quads) so every hand_r weapon sits in the hand the way the handoff pistol does.
GRIP_HAND_R = [[0.82024, -0.37803, -0.4293, -0.162], [-0.15061, 0.5813, -0.79963, -0.04941], [0.55184, 0.72054, 0.41987, 0.01596], [0.0, 0.0, 0.0, 1.0]]

# D2 bones whose skin counts as hands/feet (mauve), including the lower (second pair) hands.
HAND_ROOTS = ('DE9D6BEA', '8C83CB67', '7CCDEFE5', '2A2B599C', '0F8B505D', 'B9B9E05D')

# Material roles shared by the three Fallen infantry bodies (same D2 material hashes on Dreg / Vandal / Captain).
FALLEN_ROLES = {'80E1D0A6': 'leather', '80E1D0AD': 'steel_hi', '80E1D1BF': 'steel', '80E1D357': 'hide',
                '80E1D1A7': 'foot', '80E1D621': 'bone', '80E1D61B': 'eye', '80E1D61D': 'eye', '80E1D619': 'additive'}

# Dreg reference: hitbox 1.9 blocks <-> 30 px total height (the handoff normalisation, k_dreg = 30 px / 2.37 m).
K_DREG = 12.65865780841959
HITBOX_DREG = 1.9

SPECS = {
    'rg_dreg': dict(kind='fallen', src='fallen_dreg__80E1AFCF', include=['80E1AFCF'], height_px=30.0,
                    weapons=[dict(prefix='80A6DB7C', bone='hand_r', socket='hand_r')],
                    roles={**FALLEN_ROLES, '80E12DD0': 'cloth', '80E12F18': 'cloth', '80E12DBD': 'crest'}),
    'rg_vandal': dict(kind='fallen', src='fallen_vandal__80E1AF6E', include=['80E1AF6E'], hitbox=2.3,
                      weapons=[dict(prefix='80A6DEFD', bone='weapon', parent='hand_r', socket='hand_r')],
                      roles={**FALLEN_ROLES, '80E12DA9': 'cloth', '80E12FFE': 'cloth',
                             '80E1D621': 'paint', '80A6DBE3': 'fxbolt:weapon_glow', '80CEA8D2': 'drop'}),
    'rg_captain': dict(kind='fallen', src='fallen_captain__80E15797', include=['80E15797'], hitbox=2.6,
                       weapons=[dict(prefix='80A6D809', bone='weapon', parent='hand_r', socket='hand_r'),
                                dict(prefix='80A6D802', bone='blade', parent='lower_forearm_l', socket='lower_l')],
                       roles={**FALLEN_ROLES, '80E130A4': 'cloth', '80E12FFE': 'cloth', '80E13056': 'steel',
                              '80E1303F': 'steel', '80E13047': 'steel_hi', '80E1304D': 'fur',
                              '80CEA8B8': 'glow:weapon_glow', '80CEA450': 'glow:blade_glow'},
                       fine=FALLEN_FINE, gold=True, pack=True),
    # Shank: same size as the r4b Shank (about 21 px wide, 15 px tall); own 15-bone D2 rig -> contract bones.
    'rg_shank': dict(kind='shank', src='Shank__80E29872', include=['80E29872'], weapons=[], k=11.6, root='body',
                     bones={'body': 'B5F0FE15', 'wing_ul': 'D0B3C0C1', 'wing_ur': 'B63D175F', 'wing_ll': '47350C69',
                            'wing_lr': '81BE8747', 'gun': '7682264D'},
                     parents={'body': None, 'eye_glow': 'body', 'wing_ul': 'body', 'wing_ur': 'body', 'wing_ll': 'body',
                              'wing_lr': 'body', 'gun': 'body'},
                     fine=(), density=0.55, spacing_scale=1.0, max_quads=1500,
                     roles={'80E1D04F': 'shell', '80E13302': 'steel_hi', '80E13278': 'steel_hi', '80E131A7': 'steel',
                            '80E132D1': 'steel', '80E13372': 'steel', '80E13368': 'steel', '80E132E0': 'steel', '80E132D0': 'steel',
                            '80E131A8': 'violet', '80E1D066': 'violet', '80E132CB': 'steel_dk', '80E1D61F': 'steel_dk',
                            '80E1E2FE': 'steel_dk', '80E13293': 'steel_dk', '80E132CE': 'steel_dk', '80E131A6': 'steel_dk',
                            '80E132D3': 'steel_dk', '80E13300': 'keep', '80E132CC': 'drop', '80E13505': 'drop', '80E13280': 'drop'},
                     role_rules=[('80E131A8', 2, '>', 1.1, 'keep')]),        # the rifle on top keeps its wood/brass
    # Walker: D2 six-leg Walker posed onto WalkerBoss.LAYOUT (legs IK-posed so the feet stand in the LEG boxes).
    'rg_walker': dict(kind='walker', src='Walker__80C60641', include=['80C60641'], weapons=[], k=14.0, y0=21.0, root='body',
                      bones={'body': 'B5F0FE15', 'head': ['7E92D640', '38127F50'],
                             'leg_fl': 'C6049175', 'leg_fl_low': '1ABE862E', 'leg_fr': '9CBE38E0', 'leg_fr_low': '5434883E',
                             'leg_ml': 'BD39E38A', 'leg_ml_low': 'B325CFF2', 'leg_mr': '7B18A488', 'leg_mr_low': '95404CDA',
                             'leg_bl': '130A3B7F', 'leg_bl_low': '3D749CA1', 'leg_br': '9D76C139', 'leg_br_low': '138DAA1A'},
                      parents={'body': None, 'head': 'body', 'eye_glow': 'head', 'weakpoint': 'body', 'weakpoint_glow': 'weakpoint',
                               'plate_l': 'body', 'plate_r': 'body',
                               'leg_fl': None, 'leg_fl_low': 'leg_fl', 'leg_fl_glow': 'leg_fl',
                               'leg_fr': None, 'leg_fr_low': 'leg_fr', 'leg_fr_glow': 'leg_fr',
                               'leg_ml': None, 'leg_ml_low': 'leg_ml', 'leg_mr': None, 'leg_mr_low': 'leg_mr',
                               'leg_bl': None, 'leg_bl_low': 'leg_bl', 'leg_bl_glow': 'leg_bl',
                               'leg_br': None, 'leg_br_low': 'leg_br', 'leg_br_glow': 'leg_br'},
                      legs={'fl': ('C6049175', '1ABE862E', 'F7CC5802'), 'fr': ('9CBE38E0', '5434883E', 'B17C0102'),
                            'ml': ('BD39E38A', 'B325CFF2', '3EB20C8C'), 'mr': ('7B18A488', '95404CDA', 'A8D0A4F8'),
                            'bl': ('130A3B7F', '3D749CA1', '6067FD1F'), 'br': ('9D76C139', '138DAA1A', '9E1D6CB1')},
                      fine=(), glow_fine=False, density=0.21, spacing_scale=3.0, max_quads=3000, walls=3, split=True,
                      roles={'80A5AFF2': 'split:plate/frame', '80A5A39C': 'armour', '80A5A386': 'violetpaint', '80A5A384': 'steel_hi',
                             '80A5ABA7': 'steel_dk', '80A5A398': 'steel_dk', '80A5A394': 'steel_dk', '80A5A393': 'steel_dk',
                             '80A5A39D': 'legglow', '80A5A331': 'drop'}),
}
# WalkerBoss.LAYOUT (campaign/fallen, anchor-local blocks: x right, y up, z forward) -> model px (16x, 16y, -16z).
WALKER_FOOT_X = 2.3                  # foot centre |x| (blocks) = LAYOUT LEG box centre
WALKER_FOOT_Z = 2.0                  # front/back foot centre (blocks forward/back)
WALKER_WEAKPOINT_PX = (0.0, 52.8, -25.6)

# ================================================================================================ Blender half
def _blender_main(argv):
    import bpy
    import numpy as np
    from mathutils import Matrix
    mode = argv[0]

    def load(path):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=path)
        R = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(100, 4)
        for o in list(bpy.data.objects):
            if o.parent is None: o.matrix_world = R @ o.matrix_world
        bpy.context.view_layer.update()
        return [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

    def bone_mats(arm, rest=False):
        names = [pb.name for pb in arm.pose.bones]
        if rest:   # bind pose (an imported FBX may arrive with an action already assigned)
            M = np.array([np.array(arm.matrix_world @ arm.data.bones[n].matrix_local) for n in names])
        else:
            M = np.array([np.array(arm.matrix_world @ pb.matrix) for pb in arm.pose.bones])
        return names, M

    if mode == 'anim':
        out = argv[1]
        arm = load(ANIM_FBX)
        names, rest = bone_mats(arm, rest=True)
        acts = sorted(bpy.data.actions, key=lambda a: a.name)
        idle = next(a for a in acts if '80E115E0' in a.name)
        def frames(a):
            f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1]))
            return list(range(f0, f1 + 1))
        def basis_at(a, f):
            arm.animation_data.action = a; bpy.context.scene.frame_set(f)
            return [pb.matrix_basis.copy() for pb in arm.pose.bones]
        arm.animation_data_create()
        base0 = basis_at(idle, frames(idle)[0])
        res = {'names': np.array(names), 'rest': rest}
        meta = []
        for a in acts:
            tag = a.name.split('|')[1].split('_')[0]
            additive = a.name.endswith('|Additive')
            mats = []
            for f in frames(a):
                if additive:
                    add = basis_at(a, f)
                    arm.animation_data.action = None
                    for pb, b0, ad in zip(arm.pose.bones, base0, add): pb.matrix_basis = b0 @ ad
                    bpy.context.view_layer.update()
                else:
                    arm.animation_data.action = a; bpy.context.scene.frame_set(f)
                mats.append(bone_mats(arm)[1])
            res['clip_' + tag] = np.array(mats)
            meta.append(dict(tag=tag, action=a.name, additive=additive, frames=len(mats)))
        res['meta'] = json.dumps(meta)
        np.savez_compressed(out, **res)
        print('ANIM', [(m['tag'], m['frames'], m['additive']) for m in meta])
        return

    if mode == 'dump':
        spec = SPECS[argv[1]]; out = argv[2]
        root = f"{SRC}/{spec['src']}"
        arm = load(f"{root}/{spec['src']}.fbx")
        names, rest = bone_mats(arm, rest=True)
        parents = [pb.parent.name if pb.parent else '' for pb in arm.pose.bones]
        slots = {}
        mdir = root + '/Materials'
        for f in os.listdir(mdir):
            if f.endswith('.slots.json'):
                d = json.load(open(os.path.join(mdir, f))); slots[d['tag']] = d['slots']
        def tex_of(tag):
            for x in slots.get(tag, []):
                p = f"{TEX}/{spec['src']}/{x['texture']}.png"
                if x.get('srgb') and os.path.exists(p): return p
            return ''
        weapons = {w['prefix']: w for w in spec.get('weapons', [])}
        bidx = {n: i for i, n in enumerate(names)}
        Aw = np.array(arm.matrix_world); Ainv = np.linalg.inv(Aw)
        dg = bpy.context.evaluated_depsgraph_get()
        V, UV, MAT, BONE, VB = [], [], [], [], []
        mats = []
        for o in bpy.data.objects:
            if o.type != 'MESH' or 'InternalGeom' in o.name: continue
            pre = o.name.split('_')[0]
            if pre not in spec['include'] and pre not in weapons and spec['include'] != ['*']: continue
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
            n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
            W = np.array(o.matrix_world); co = co @ W[:3, :3].T + W[:3, 3]
            nt = len(me.loop_triangles)
            tv = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get('vertices', tv); tv = tv.reshape(-1, 3)
            tl = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get('loops', tl); tl = tl.reshape(-1, 3)
            tm = np.empty(nt, np.int64); me.loop_triangles.foreach_get('material_index', tm)
            luv = np.zeros((len(me.loops), 2))
            if me.uv_layers:
                buf = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', buf); luv = buf.reshape(-1, 2)
            slot_tags = [s.material.name.split('.')[0] if s.material else '' for s in o.material_slots] or ['']
            for t in slot_tags:
                if t not in mats: mats.append(t)
            if pre in weapons:
                w = weapons[pre]
                S = rest[bidx[SOCKET[w['socket']]]]
                # weapon meshes sit at the armature origin in socket space: world = A @ socket(armature) @ A^-1 @ v
                G = np.array(GRIP_HAND_R) if w['socket'] == 'hand_r' else np.eye(4)
                # socket offsets follow the skeleton size (hips->head length relative to the Dreg, 0.74621 m)
                hh = np.linalg.norm(rest[bidx[FALLEN_BONES['head']]][:3, 3] - rest[bidx[FALLEN_BONES['hips']]][:3, 3])
                G[:3, 3] *= hh / 0.74621
                M = S @ G @ Ainv
                co = co @ M[:3, :3].T + M[:3, 3]
                tb = np.full(nt, 'WPN:' + w['bone'], dtype=object)
                tvb = np.full((nt, 3), 'WPN:' + w['bone'], dtype=object)
            else:
                gn = {g.index: g.name for g in o.vertex_groups}
                vb = np.array([gn.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in o.data.vertices], dtype=object)
                a, b, c = vb[tv[:, 0]], vb[tv[:, 1]], vb[tv[:, 2]]
                tb = np.where(b == c, b, a)
                tvb = vb[tv]
            VB.append(tvb.astype(str))
            V.append(co[tv]); UV.append(luv[tl]); MAT.append(np.array([mats.index(slot_tags[min(i, len(slot_tags) - 1)]) for i in tm]))
            BONE.append(tb.astype(str))
        np.savez_compressed(out, V=np.concatenate(V), UV=np.concatenate(UV), MAT=np.concatenate(MAT), BONE=np.concatenate(BONE),
                            VBONE=np.concatenate(VB),
                            mats=np.array(mats), mat_tex=np.array([tex_of(t) for t in mats]),
                            names=np.array(names), parents=np.array(parents), rest=rest)
        print('DUMP', argv[1], 'tris', sum(len(v) for v in V), 'mats', mats)
        return


if __name__ == '__main__' and 'bpy' in sys.modules:
    _blender_main(sys.argv[sys.argv.index('--') + 1:])


# ================================================================================================ Python half
NAMESPACE = 'b2a6f2a4-5d0e-4c55-9c1e-7f3b1a6e7700'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')
# per face: (depth axis, nearest = min or max, plane axes (u_axis, v_axis), u sign, v sign); sign -1 = u grows as coord decreases
FACE_DEF = {
    'north': (2, 'min', (0, 1), -1, -1),
    'south': (2, 'max', (0, 1), +1, -1),
    'east':  (0, 'max', (2, 1), -1, -1),
    'west':  (0, 'min', (2, 1), +1, -1),
    'up':    (1, 'max', (0, 2), +1, +1),
    'down':  (1, 'min', (0, 2), +1, -1),
}


def _uid(*parts):
    import uuid
    return str(uuid.uuid5(uuid.UUID(NAMESPACE), '/'.join(str(p) for p in parts)))


def run_blender(*args):
    import subprocess
    cmd = [BLENDER, '-b', '--python', os.path.abspath(__file__), '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or 'Traceback' in r.stderr + r.stdout:
        raise RuntimeError('blender failed: ' + (r.stdout + r.stderr)[-3000:])
    return r.stdout


HANDOFF = '/Users/qf/Downloads/Dreg-Light-Handoff/Dreg-Light/dreg_combat.bbmodel'
Y0_DREG = 0.1803441758049431
# House of Dusk (Bungie Dusk Dreg render; same targets as import_dreg_handoff.PAL for rg_dreg).
DUSK = {'cloth': (0.38, 0.26, 0.45), 'leather': (0.40, 0.28, 0.21), 'steel_hi': (0.58, 0.56, 0.55),
        'steel': (0.46, 0.44, 0.44), 'hide': (0.27, 0.25, 0.27), 'hand': (0.46, 0.33, 0.42), 'foot': (0.48, 0.35, 0.43),
        'crest': (0.33, 0.21, 0.40), 'bone': (0.84, 0.78, 0.62), 'fur': (0.42, 0.37, 0.45), 'gold': (0.86, 0.68, 0.24),
        'paint': (0.60, 0.50, 0.68), 'shell': (0.52, 0.49, 0.54), 'steel_dk': (0.33, 0.31, 0.36), 'violet': (0.40, 0.27, 0.48),
        'armour': (0.34, 0.30, 0.39), 'plate': (0.58, 0.56, 0.57), 'frame': (0.31, 0.29, 0.34), 'violetpaint': (0.50, 0.34, 0.62), 'violetglass': (0.42, 0.33, 0.70)}   # white decal material 80E1D621 -> pale Dusk violet on Vandal (gold on Captain)
GLOW_RGB = {'eyes_glow': (120, 228, 255), 'eye_glow': (120, 228, 255), 'weakpoint_glow': (150, 240, 255),
            'leg_fl_glow': (150, 110, 255), 'leg_fr_glow': (150, 110, 255), 'leg_bl_glow': (150, 110, 255), 'leg_br_glow': (150, 110, 255)}
GLOW_DEFAULT = (110, 205, 255)
EXTRA_PARENT = {'eyes_glow': 'head', 'weapon': 'hand_r', 'weapon_glow': 'weapon', 'blade': 'lower_forearm_l',
                'blade_glow': 'blade', 'pack_glow': 'chest'}
FACE_ORDER = {f: i for i, f in enumerate(FACES)}


class Bake:
    """Geometry/texture half. Model px: x right, y up, z = -forward (BB north = model front)."""

    def __init__(self, name, opts=None):
        import numpy as np
        self.np = np
        self.name = name
        self.spec = SPECS[name]
        self.o = dict(pitch=1 / 13, fine=1 / 17, spacing=0.29, fine_spacing=0.18, density=1.0, min_texels=4,
                      dilate=1, walls=4, atlas=2048, luma_floor=86.0, spacing_scale=1.0)
        self.o.update(opts or {})
        path = f'/tmp/r7_dump_{name}.npz'
        if not os.path.exists(path):
            run_blender('dump', name, path)
        d = np.load(path, allow_pickle=True)
        self.d = d
        self.V = d['V']; self.UV = d['UV']; self.MAT = d['MAT']
        self.mats = [str(m) for m in d['mats']]; self.mat_tex = [str(t) for t in d['mat_tex']]
        self.names = [str(n) for n in d['names']]
        self.par = dict(zip(self.names, [str(p) for p in d['parents']]))
        self.rest = {n: d['rest'][i] for i, n in enumerate(self.names)}
        self.handoff = json.load(open(HANDOFF))
        self.VB = d['VBONE'] if 'VBONE' in d.files else None
        self.bone_raw = d['BONE'].astype(str)
        self.extra_roles = {}
        self.origin_px = dict(self.spec.get('origins_px', {}))
        self._tex = {}
        self.stats = {}
        for key in ('density', 'spacing_scale', 'walls'):
            if key in self.spec and (opts or {}).get(key) is None: self.o[key] = self.spec[key]
        if self.spec.get('pack'): self._ether_pack()
        self._scale()
        if self.spec['kind'] == 'walker': self._pose_walker(); self._walker_parts()
        if self.spec['kind'] == 'shank': self._shank_eye()
        self._bones()

    def _ether_pack(self):
        """Captain pack_glow: two Ether canisters + yoke on the upper back, seated on the fur mantle.
        Authored (the D2 Captain mesh has no pack); kept from the r4b contract design (RisingModelAssetsTest.GLOW_BONES)."""
        np = self.np
        V = self.V.reshape(-1, 3)
        fur = self.MAT == self.mats.index('80E1304D')
        F = self.V[fur].reshape(-1, 3)
        band = F[(np.abs(F[:, 0]) < 0.22) & (F[:, 2] > 2.05) & (F[:, 2] < 2.4)]
        yb = float(band[:, 1].min()); r = 0.036
        tris = []
        def prism(c, h, axis, n=8):
            ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
            ring = np.stack([np.cos(ang) * r, np.sin(ang) * r], 1)
            def pt(a, b, t):
                q = np.array(c, float)
                if axis == 2: q += [a, b, t]
                else: q += [t, a, b]
                return q
            for i in range(n):
                a0, b0 = ring[i]; a1, b1 = ring[(i + 1) % n]
                p00, p01, p10, p11 = pt(a0, b0, -h / 2), pt(a0, b0, h / 2), pt(a1, b1, -h / 2), pt(a1, b1, h / 2)
                tris.extend([[p00, p10, p11], [p00, p11, p01]])
                tris.extend([[pt(0, 0, -h / 2), p10, p00], [pt(0, 0, h / 2), p01, p11]])
        for sx in (-1, 1): prism((sx * 0.085, yb + 0.5 * r, 2.30), 0.20, 2)
        self._add(tris, 'pack_glow', 'PACK', 'glow:pack_glow')

    # ------------------------------------------------------------------ synthetic contract parts (documented, untextured)
    def m_of(self, x, y, z):
        """model px -> source metres (inverse of to_px)."""
        return self.np.array([x / self.k, -z / self.k, (y - self.y0) / self.k])

    def _add(self, T, bone, mat, role):
        np = self.np
        T = np.asarray(T, float)
        self.mats.append(mat); self.mat_tex.append('')
        self.V = np.concatenate([self.V, T]); self.UV = np.concatenate([self.UV, np.zeros((len(T), 3, 2))])
        self.MAT = np.concatenate([self.MAT, np.full(len(T), len(self.mats) - 1)])
        self.bone_raw = np.concatenate([self.bone_raw, np.full(len(T), 'WPN:' + bone)])
        if self.VB is not None: self.VB = np.concatenate([self.VB, np.full((len(T), 3), 'WPN:' + bone)])
        self.extra_roles[mat] = role

    def _cyl(self, c, r, h, axis, n=10, caps=True, r2=None):
        """Closed (or open) n-gon cylinder in metres; axis 0/1/2 = x/y/z of the source frame."""
        np = self.np
        r2 = r if r2 is None else r2
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
        ax = [i for i in range(3) if i != axis]
        def pt(a, rr, t):
            q = np.array(c, float); q[ax[0]] += np.cos(a) * rr; q[ax[1]] += np.sin(a) * rr; q[axis] += t
            return q
        out = []
        for i in range(n):
            a0, a1 = ang[i], ang[(i + 1) % n]
            p00, p01, p10, p11 = pt(a0, r, -h / 2), pt(a0, r2, h / 2), pt(a1, r, -h / 2), pt(a1, r2, h / 2)
            out += [[p00, p10, p11], [p00, p11, p01]]
            if caps:
                c0 = np.array(c, float); c0[axis] -= h / 2; c1 = np.array(c, float); c1[axis] += h / 2
                out += [[c0, p10, p00], [c1, p01, p11]]
        return out

    def _sphere(self, c, r, nlat=6, nlon=10):
        np = self.np
        out = []
        th = np.linspace(0, np.pi, nlat + 1); ph = np.linspace(0, 2 * np.pi, nlon + 1)
        P = lambda t, f: np.array(c, float) + r * np.array([np.sin(t) * np.cos(f), np.sin(t) * np.sin(f), np.cos(t)])
        for i in range(nlat):
            for j in range(nlon):
                a, b, cc, dd = P(th[i], ph[j]), P(th[i + 1], ph[j]), P(th[i + 1], ph[j + 1]), P(th[i], ph[j + 1])
                out += [[a, b, cc], [a, cc, dd]]
        return out

    def _box(self, lo, hi):
        np = self.np
        lo, hi = np.array(lo, float), np.array(hi, float)
        C = [np.array([(hi if (i >> a) & 1 else lo)[a] for a in range(3)]) for i in range(8)]
        quads = [(0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (0, 1, 3, 2), (4, 6, 7, 5)]
        out = []
        for a, b, c, d in quads: out += [[C[a], C[b], C[c]], [C[a], C[c], C[d]]]
        return out

    def _shank_eye(self):
        """Shank eye_glow: lens on the front of the shell (the D2 Shank lens has no emissive material)."""
        np = self.np
        shell = self.MAT == self.mats.index('80E1D04F')
        P = self.V[shell].reshape(-1, 3)
        zc = 0.80
        band = P[(np.abs(P[:, 0]) < 0.08) & (np.abs(P[:, 2] - zc) < 0.06)]
        yf = float(band[:, 1].max())
        self._add(self._cyl((0.0, yf + 0.012, zc), 0.06, 0.05, 1, n=12), 'eye_glow', 'EYE', 'glow:eye_glow')
        self.origin_px['eye_glow'] = [0.0, round(zc * self.k + self.y0, 4), round(-(yf + 0.012) * self.k, 4)]

    def _walker_parts(self):
        """WalkerBoss contract parts the D2 Walker mesh lacks, placed on LAYOUT: weakpoint core (+ housing), armour
        plates that swing open in weakpoint_open, and the head eye lens."""
        np = self.np
        k = self.k
        cx, cy, cz = WALKER_WEAKPOINT_PX
        c = self.m_of(cx, cy, cz)
        self._add(self._sphere(c, 8.8 / k, 6, 12), 'weakpoint_glow', 'WPCORE', 'glow:weakpoint_glow')
        self._add(self._cyl(c + [0, -1.5 / k, 0], 10.0 / k, 7.0 / k, 1, n=12, caps=False), 'weakpoint', 'WPRING', 'steel_dk')
        self._add(self._cyl(c + [0, -5.0 / k, 0], 10.0 / k, 1.0 / k, 1, n=12), 'weakpoint', 'WPBACK', 'frame')
        for side, sx in (('plate_l', -1), ('plate_r', 1)):
            lo = self.m_of(min(0.0, 12.0 * sx), cy - 9.5, cz - 9.5); hi = self.m_of(max(0.0, 12.0 * sx), cy + 9.5, cz - 7.5)
            self._add(self._box(np.minimum(lo, hi), np.maximum(lo, hi)), side, 'PLATE_' + side, 'armour')
            self.origin_px[side] = [12.0 * sx, cy, cz - 8.0]
        self.origin_px['weakpoint'] = list(WALKER_WEAKPOINT_PX); self.origin_px['weakpoint_glow'] = list(WALKER_WEAKPOINT_PX)
        # eye lens on the head front (D2 head has no emissive eye material)
        head = np.isin(self.bone_raw, ['7E92D640', '38127F50'])
        H = self.V[head].reshape(-1, 3)
        zc = 4.15
        band = H[(np.abs(H[:, 0]) < 0.3) & (np.abs(H[:, 2] - zc) < 0.25)]
        yf = float(band[:, 1].max())
        self._add(self._cyl((0.0, yf + 0.03, zc), 0.22, 0.08, 1, n=12), 'eye_glow', 'EYE', 'glow:eye_glow')
        self.origin_px['eye_glow'] = [0.0, round(zc * k + self.y0, 4), round(-(yf + 0.03) * k, 4)]

    def _pose_walker(self):
        """IK-pose the six D2 legs (thigh, shin, rigid foot) so each sole stands flat on the ground at its
        WalkerBoss.LAYOUT foot (front/back) or level with its hip (middle). Per-vertex rigid segment transforms."""
        np = self.np
        k, y0 = self.k, self.y0
        zg = -y0 / k + 1e-4                                # ground plane (source metres), soles a hair above y = 0
        par = self.par
        def desc(h):
            out = {h}; ch = True
            while ch:
                ch = False
                for n, p in par.items():
                    if p in out and n not in out: out.add(n); ch = True
            return out
        def rot_between(a, b):
            a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
            v = np.cross(a, b); c = float(a @ b)
            if np.linalg.norm(v) < 1e-9: return np.eye(3)
            K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
            return np.eye(3) + K + K @ K * (1 / (1 + c))
        V = self.V.copy()
        VB = self.VB
        knees = {}
        for leg, (hip_b, shin_b, foot_b) in self.spec['legs'].items():
            sx = -1 if leg.endswith('l') else 1
            hip = self.rest[hip_b][:3, 3]; knee = self.rest[shin_b][:3, 3]; ankle = self.rest[foot_b][:3, 3]
            foot_set = desc(foot_b); shin_set = desc(shin_b) - foot_set; thigh_set = desc(hip_b) - foot_set - shin_set
            fm = np.isin(VB, list(foot_set))
            FP = V[fm]
            sole = FP[FP[:, 2] < FP[:, 2].min() + 0.06]
            contact = np.array([(sole[:, 0].min() + sole[:, 0].max()) / 2, (sole[:, 1].min() + sole[:, 1].max()) / 2, FP[:, 2].min()])
            if leg[0] == 'm':
                tgt_y = hip[1]
            else:
                tgt_y = (WALKER_FOOT_Z if leg[0] == 'f' else -WALKER_FOOT_Z) * 16 / k
            target = np.array([sx * WALKER_FOOT_X * 16 / k, tgt_y, zg])
            ankle_t = target + (ankle - contact)
            a = np.linalg.norm(knee - hip); b = np.linalg.norm(ankle - knee)
            dvec = ankle_t - hip; d = np.linalg.norm(dvec)
            d = min(d, (a + b) * 0.999)
            u = dvec / np.linalg.norm(dvec)
            pole = np.array([sx * 0.55, 0.0, 1.0]); w = pole - (pole @ u) * u; w /= np.linalg.norm(w)
            ca = (a * a + d * d - b * b) / (2 * a * d); sa = np.sqrt(max(0.0, 1 - ca * ca))
            knee_n = hip + a * (ca * u + sa * w)
            ankle_n = hip + u * d
            R1 = rot_between(knee - hip, knee_n - hip)
            R2 = rot_between(ankle - knee, ankle_n - knee_n)
            m = np.isin(VB, list(thigh_set)); V[m] = (V[m] - hip) @ R1.T + hip
            m = np.isin(VB, list(shin_set)); V[m] = (V[m] - knee) @ R2.T + knee_n
            V[fm] = V[fm] + (ankle_n - ankle)
            knees[leg] = knee_n
            self.stats.setdefault('walker_legs', {})[leg] = dict(
                foot_target_px=[round(float(v), 2) for v in self.to_px(target)], reach_m=round(float(d), 3),
                max_reach_m=round(float(a + b), 3), knee_px=[round(float(v), 2) for v in self.to_px(knee_n)])
        self.V = V
        for leg, kn in knees.items():
            self.origin_px[f'leg_{leg}_low'] = [round(float(v), 5) for v in self.to_px(kn)]

    # ------------------------------------------------------------------ scale / rig
    def _scale(self):
        np = self.np
        z = self.V[..., 2]
        zmin, zmax = float(z.min()), float(z.max())
        if self.spec['kind'] != 'fallen':
            k = self.spec['k']; y0 = self.spec.get('y0', -zmin * k)
            self.k, self.y0, self.skel, self.fpos = k, y0, 1.0, 1.0
            self.stats.update(k=k, y0=y0, zmin_m=zmin, zmax_m=zmax, height_px=(zmax - zmin) * k, skeleton_scale_vs_dreg=1.0,
                              skeleton_residual_m=0.0, position_key_scale=1.0)
            return
        # D2 skeleton size relative to the Dreg (least squares over the 19 display bones, about the hips)
        hb = {g['name']: g for g in self._handoff_groups()}
        D = np.array([[(hb[b]['origin'][0]) / K_DREG, -(hb[b]['origin'][2]) / K_DREG, (hb[b]['origin'][1] - Y0_DREG) / K_DREG]
                      for b in FALLEN_BONES])
        T = np.array([self.rest[h][:3, 3] for h in FALLEN_BONES.values()])
        D0, T0 = D - D[0], T - T[0]
        s = float((D0 * T0).sum() / (D0 * D0).sum())
        resid = float(np.abs(T0 - s * D0).max())
        if 'height_px' in self.spec:
            k = self.spec['height_px'] / (zmax - zmin)
        else:
            k = K_DREG * self.spec['hitbox'] / HITBOX_DREG / s
        self.k, self.y0, self.skel = k, -zmin * k, s
        self.fpos = s * k / K_DREG          # handoff position keys -> this model
        self.stats.update(k=k, y0=self.y0, zmin_m=zmin, zmax_m=zmax, height_px=(zmax - zmin) * k,
                          skeleton_scale_vs_dreg=s, skeleton_residual_m=resid, position_key_scale=self.fpos)

    def _handoff_groups(self):
        out = []
        def walk(g):
            out.append(g)
            for c in g['children']:
                if isinstance(c, dict): walk(c)
        for g in self.handoff['outliner']: walk(g)
        return out

    def to_px(self, P):
        np = self.np
        return np.stack([P[..., 0] * self.k, P[..., 2] * self.k + self.y0, -P[..., 1] * self.k], -1)

    def _bones(self):
        np = self.np
        bm = self.spec.get('bones', FALLEN_BONES)
        inv = {}
        for b, hs in bm.items():
            for h in ([hs] if isinstance(hs, str) else hs): inv[h] = b
        rootb = self.spec.get('root', 'hips')
        fallen = self.spec['kind'] == 'fallen'
        cache = {}
        def info(h):
            if h in cache: return cache[h]
            if h.startswith('WPN:'):
                r = (h[4:], False)
            else:
                x, hand = h, False
                while x and x not in inv:
                    x = self.par.get(x, '')
                y = h
                while fallen and y:
                    if y in HAND_ROOTS: hand = True
                    y = self.par.get(y, '')
                r = (inv.get(x, rootb), hand)
            cache[h] = r
            return r
        roles = {**self.spec['roles'], **self.extra_roles}
        bone, hand = zip(*[info(str(b)) for b in self.bone_raw])
        bone = np.array(bone, dtype=object); hand = np.array(hand)
        role = np.array([roles.get(m, 'keep') for m in self.mats], dtype=object)[self.MAT]
        C = self.V.mean(1)
        for mat, axis, op, val, r in self.spec.get('role_rules', []):
            if mat not in self.mats: continue
            sel = (self.MAT == self.mats.index(mat)) & ((C[:, axis] > val) if op == '>' else (C[:, axis] < val))
            role[sel] = r
        bone[role == 'eye'] = self.spec.get('eye_bone', 'eyes_glow')
        for r in set(role):
            if r.startswith(('glow:', 'fxbolt:')): bone[role == r] = r.split(':', 1)[1]
        # Walker: the blue leg-joint material glows on the four contract legs' thighs; elsewhere it stays unlit glass
        lg = role == 'legglow'
        if lg.any():
            parents = self.spec.get('parents', {})
            for b in set(bone[lg]):
                m = lg & (bone == b)
                if b + '_glow' in parents and parents[b + '_glow'] == b: bone[m] = b + '_glow'; role[m] = 'glow'
                else: role[m] = 'violetglass'
        self.tri_bone, self.tri_hand, self.tri_role = bone, hand, role
        # rig: display bones present + parents
        present = set(bone)
        parentmap = self.spec.get('parents', FALLEN_PARENT)
        parent = dict(parentmap)
        for w in self.spec.get('weapons', []):
            if w['bone'] not in parent: parent[w['bone']] = w['parent']
        if fallen:
            for b, p in EXTRA_PARENT.items():
                if b in present or b == 'pack_glow' and self.spec.get('pack'): parent.setdefault(b, p)
        wb = {w['bone'] for w in self.spec.get('weapons', [])}
        self.parent = {b: p for b, p in parent.items() if (b in parentmap and not b.endswith('_glow')) or b in present or b in wb}
        missing = [b for b in present if b not in self.parent]
        assert not missing, f'bones without a parent entry: {missing}'
        origin = {}
        for b, hs in bm.items():
            h = hs if isinstance(hs, str) else hs[0]
            origin[b] = self.to_px(self.rest[h][:3, 3])
        for w in self.spec.get('weapons', []):
            if w['bone'] not in origin: origin[w['bone']] = self.to_px(self.rest[SOCKET[w['socket']]][:3, 3])
        for b, o in self.origin_px.items(): origin[b] = np.array(o, float)
        for b in self.parent:
            if b not in origin:
                p = self.parent[b]
                while p not in origin: p = self.parent[p]
                origin[b] = origin[p]
        self.origin = {b: [round(float(v), 5) for v in o] for b, o in origin.items() if b in self.parent}

    # ------------------------------------------------------------------ sampling
    def texture(self, mi):
        np = self.np
        if mi not in self._tex:
            p = self.mat_tex[mi]
            if p and os.path.exists(p):
                from PIL import Image
                self._tex[mi] = np.asarray(Image.open(p).convert('RGB'))
            else:
                self._tex[mi] = None
        return self._tex[mi]

    def pitch_of(self, bone):
        f = self.k / K_DREG / self.o['density']      # density < 1 -> coarser texels
        fine = bone in self.spec.get('fine', FALLEN_FINE + ('weapon', 'blade')) or (bone.endswith('_glow') and self.spec.get('glow_fine', True))
        sp = (self.o['fine_spacing'] if fine else self.o['spacing']) * self.k / K_DREG * self.o['spacing_scale']
        return (self.o['fine'] if fine else self.o['pitch']) * f, sp

    def samples(self):
        np = self.np
        T = self.to_px(self.V); UVt = self.UV
        e = np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                      np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], 1).max(1)
        step = np.array([self.pitch_of(b)[0] for b in self.tri_bone]) * 0.55
        msub = np.clip(np.ceil(e / step).astype(int), 1, 300)
        P, C, TI = [], [], []
        for m in np.unique(msub):
            idx = np.nonzero(msub == m)[0]
            ii, jj = np.meshgrid(np.arange(m + 1), np.arange(m + 1), indexing='ij')
            ok = ii + jj <= m
            a = ii[ok] / m; b = jj[ok] / m
            W = np.stack([1 - a - b, a, b], 1)
            P.append(np.einsum('lk,tkd->tld', W, T[idx]).reshape(-1, 3))
            C.append(np.einsum('lk,tkd->tld', W, UVt[idx]).reshape(-1, 2))
            TI.append(np.repeat(idx, len(W)))
        P = np.concatenate(P); UV = np.concatenate(C); TI = np.concatenate(TI)
        MM = self.MAT[TI]
        rgb = np.full((len(P), 3), 128, np.uint8)
        # untextured (synthetic / FX) triangles: simple key-light shading so the form reads after the recolour
        T0 = self.V[TI]
        nrm = np.cross(T0[:, 1] - T0[:, 0], T0[:, 2] - T0[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        Lk = np.array([0.35, 0.55, 0.76]); Lk /= np.linalg.norm(Lk)
        shade = (0.55 + 0.45 * np.abs(nrm @ Lk)) * 200
        for mi in np.unique(MM):
            t = self.texture(mi); s = MM == mi
            if t is None:
                rgb[s] = np.clip(shade[s], 0, 255).astype(np.uint8)[:, None]
                continue
            h, w = t.shape[:2]
            x = (np.mod(UV[s, 0], 1.0) * w).astype(int) % w
            y = ((1.0 - np.mod(UV[s, 1], 1.0)) * h).astype(int) % h
            rgb[s] = t[y, x]
        keep = np.ones(len(P), bool)
        trole = self.tri_role[TI]
        keep &= trole != 'drop'
        # FX arc cards (no albedo): keep a thin zig-zag bolt across the card instead of an opaque rectangle
        fx = np.array([str(r).startswith('fxbolt:') for r in trole])
        if fx.any():
            u, v = np.mod(UV[:, 0], 1.0), np.mod(UV[:, 1], 1.0)
            zz = np.abs(np.mod(u * 4.0, 2.0) - 1.0)          # triangle wave 0..1
            keep &= ~fx | (np.abs(v - (0.35 + 0.3 * zz)) < 0.045)
        add = trole == 'additive'
        if add.any():
            lum = rgb[:, :3] @ np.array([.299, .587, .114])
            keep &= ~(add & (lum < 60))
        self.S = dict(P=P[keep], rgb=rgb[keep], tri=TI[keep])
        self.stats['samples'] = int(keep.sum())

    # ------------------------------------------------------------------ depth slices
    def extract(self):
        """Per bone x face: nearest surface per texel cell, quantised to absolute depth planes -> texel records."""
        np = self.np
        S = self.S
        sb = self.tri_bone[S['tri']]
        recs = []
        for bone in sorted(set(sb)):
            sel = np.nonzero(sb == bone)[0]
            pitch, spacing = self.pitch_of(bone)
            P = S['P'][sel]
            for face in FACES:
                da, near, (ua, va), us, vs = FACE_DEF[face]
                gi = np.floor(P[:, ua] / pitch).astype(np.int64); gj = np.floor(P[:, va] / pitch).astype(np.int64)
                dsg = P[:, da] if near == 'min' else -P[:, da]
                cell = (gi - gi.min()) * (gj.max() - gj.min() + 1) + (gj - gj.min())
                order = np.lexsort((dsg, cell))
                cs = cell[order]
                start = np.ones(len(order), bool); start[1:] = cs[1:] != cs[:-1]
                gid = np.cumsum(start) - 1
                first = np.nonzero(start)[0]
                dmin = dsg[order][first][gid]
                near_ok = dsg[order] - dmin <= 0.5 * spacing
                n = len(first)
                cnt = np.bincount(gid[near_ok], minlength=n).astype(float)
                rgb = np.stack([np.bincount(gid[near_ok], S['rgb'][sel][order][near_ok][:, c].astype(float), minlength=n)
                                for c in range(3)], 1) / cnt[:, None]
                win = sel[order[first]]
                L = np.round(S['P'][win, da] / spacing).astype(np.int64)
                recs.append(dict(bone=bone, face=face, pitch=pitch, spacing=spacing, gi=gi[order[first]], gj=gj[order[first]],
                                 L=L, rgb=rgb, win=win))
        self.recs = recs

    def merge_small(self):
        """Fold planes with fewer than min_texels texels into the nearest populated plane within 2 steps."""
        np = self.np
        mt = self.o['min_texels']
        for r in self.recs:
            L = r['L']
            for _ in range(2):
                ls, c = np.unique(L, return_counts=True)
                big = ls[c >= mt]
                if not len(big): break
                small = ls[c < mt]
                for l in small:
                    j = big[np.argmin(np.abs(big - l))]
                    if abs(j - l) <= 2: L[L == l] = j
            r['L'] = L

    # ------------------------------------------------------------------ colour
    def recolour(self):
        np = self.np
        allrgb = np.concatenate([r['rgb'] for r in self.recs]) / 255.0
        win = np.concatenate([r['win'] for r in self.recs])
        bones = np.concatenate([np.full(len(r['L']), r['bone'], dtype=object) for r in self.recs])
        tri = self.S['tri'][win]
        role = self.tri_role[tri].copy()
        role[(role == 'hide') & self.tri_hand[tri]] = 'hand'
        self.stats['texel_roles_raw'] = sorted(set(map(str, role)))
        lum = allrgb @ np.array([.299, .587, .114])
        P = self.S['P'][win]
        if self.spec.get('gold'):
            # Captain: Dusk gold-yellow paint streaks. Armour: the light paint marks of the source steel albedo.
            for r in ('steel', 'steel_hi'):
                m = role == r
                if m.any():
                    med = np.median(lum[m])
                    role[m & (lum > med * 1.55) & (lum > 0.32)] = 'gold'
            # Cloak (cape material): two vertical streaks and a hem band, laid out in model space.
            cape = (role == 'cloth') & (self.MAT[tri] == self.mats.index('80E130A4')) if '80E130A4' in self.mats else role == ''
            if cape.any():
                x, y = P[:, 0], P[:, 1]
                ylo = np.percentile(y[cape], 2)
                w = np.percentile(np.abs(x[cape]), 98)
                streak = (np.abs(np.abs(x) - 0.42 * w) < 0.075 * w) | (y < ylo + 0.9 * self.k / K_DREG)
                role[cape & streak] = 'gold'
        for r in [x for x in set(role) if str(x).startswith('split:')]:
            hi, lo = r[6:].split('/')
            m = role == r
            med = np.median(lum[m])
            role[m & (lum > med * 1.15)] = hi; role[m & (lum <= med * 1.15)] = lo
        out = allrgb.copy()
        for name, col in DUSK.items():
            m = role == name
            if not m.any(): continue
            rr = np.clip(lum[m] / max(np.median(lum[m]), 0.04), 0.2, 1.9)[:, None]
            out[m] = np.clip(np.array(col) * rr, 0, 1) * 0.9 + allrgb[m] * 0.1
        glow = np.array([b.endswith('_glow') for b in bones])
        for b in set(bones[glow]):
            m = bones == b
            shade = np.clip(0.85 + 0.3 * (lum[m] - lum[m].mean()), 0.8, 1.0)
            if np.ptp(lum[m]) < 1e-3:                     # synthetic (untextured) glow geometry
                y = P[m, 1]; t = (y - y.min()) / max(np.ptp(y), 1e-6)
                shade = 0.55 + 0.45 * np.clip(1.0 - np.abs(t - 0.5) * 2.2, 0, 1) ** 0.5
            out[m] = np.array(GLOW_RGB.get(b, GLOW_DEFAULT)) / 255.0 * shade[:, None]
        # readable mid-tone floor (RisingModelAssetsTest mean luma >= 80): lift dark values, keep hue
        mean = float((out @ np.array([.299, .587, .114])).mean() * 255)
        self.stats['mean_luma_before_floor'] = mean
        if mean < self.o['luma_floor']:
            g = 1.0
            for _ in range(30):
                t = out[~glow] ** g
                if (np.concatenate([t, out[glow]]) @ np.array([.299, .587, .114])).mean() * 255 >= self.o['luma_floor']: break
                g *= 0.97
            out[~glow] = out[~glow] ** g
            self.stats['luma_gamma'] = g
        out = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
        i = 0
        for r in self.recs:
            n = len(r['L']); r['col'] = out[i:i + n]; i += n
        self.stats['role_texels'] = {k: int((role == k).sum()) for k in sorted(set(role))}

    # ------------------------------------------------------------------ planes -> images
    def planes(self):
        np = self.np
        out = []
        for r in self.recs:
            da, near, (ua, va), us, vs = FACE_DEF[r['face']]
            gi, gj, L, col = r['gi'], r['gj'], r['L'], r['col']
            sgn = 1 if near == 'min' else -1          # signed depth: smaller = nearer the viewer
            occ = {(a, b): (l, c) for a, b, l, c in zip(gi.tolist(), gj.tolist(), L.tolist(), col)}
            box = {}
            for l in np.unique(L):
                s = L == l
                box[int(l)] = (gi[s].min() - 1, gi[s].max() + 1, gj[s].min() - 1, gj[s].max() + 1)
            def inside(l, q):
                b = box.get(l)
                return b is not None and b[0] <= q[0] <= b[1] and b[2] <= q[1] <= b[3]
            layer = {int(l): {} for l in box}
            for (a, b), (l, c) in occ.items():
                layer[l][(a, b)] = c
            for (a, b), (l, c) in occ.items():
                # step walls: repeat the texel on the deeper existing planes down to its deepest 4-neighbour so
                # oblique views see stacked slices instead of a crack (kept inside each plane's own rect)
                s0 = sgn * l; deep = s0
                for q in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    o = occ.get(q)
                    if o is not None: deep = max(deep, sgn * o[0])
                for sd in range(s0 + 1, min(deep, s0 + self.o['walls']) + 1):
                    ll = sgn * sd
                    if inside(ll, (a, b)): layer[ll].setdefault((a, b), c)
            for l in sorted(layer):
                cells = layer[l]
                if self.o['dilate']:
                    add = {}
                    for (a, b) in list(cells):
                        for q in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                            if q in cells or q in add or not inside(l, q): continue
                            o = occ.get(q)
                            if o is not None and sgn * o[0] > sgn * l: add[q] = o[1]
                    cells.update(add)
                A = np.array(list(cells)); C = np.array(list(cells.values()))
                out.append(dict(bone=r['bone'], face=r['face'], L=int(l), A=A, C=C, us=us, vs=vs, ua=ua, va=va, da=da,
                                pitch=r['pitch'], d=l * r['spacing'], part=0))
        cap = self.spec.get('max_quads', 2200)
        self.stats['planes_before_split'] = len(out)
        if self.spec.get('split') and len(out) < cap:
            out = self.split(out, cap)
        self.plist = [self.image(p) for p in out]

    def image(self, p):
        np = self.np
        A, C = p['A'], p['C']
        i0, j0 = A.min(0); i1, j1 = A.max(0)
        w, h = int(i1 - i0 + 1), int(j1 - j0 + 1)
        img = np.zeros((h, w, 4), np.uint8)
        cc = (A[:, 0] - i0) if p['us'] > 0 else (i1 - A[:, 0])
        rr = (A[:, 1] - j0) if p['vs'] > 0 else (j1 - A[:, 1])
        img[rr, cc, :3] = C; img[rr, cc, 3] = 255
        q = dict(p, img=img, u=(i0 * p['pitch'], (i1 + 1) * p['pitch']), v=(j0 * p['pitch'], (j1 + 1) * p['pitch']), n=len(A))
        del q['A'], q['C']
        return q

    def split(self, planes, cap):
        """Greedy guillotine split of sparse planes: each extra quad buys the largest bbox-area saving (texels) until
        the quad cap; keeps the atlas texel density up on big, hollow models (Walker)."""
        import heapq
        np = self.np
        def best(A):
            n = len(A)
            if n < 16: return 0, None
            area0 = int(np.ptp(A[:, 0]) + 1) * int(np.ptp(A[:, 1]) + 1)
            bestv, bestm = 0, None
            for ax in (0, 1):
                o = 1 - ax
                idx = np.argsort(A[:, ax], kind='stable'); s = A[idx]
                cut = np.nonzero(s[1:, ax] != s[:-1, ax])[0]          # split after position cut
                if not len(cut): continue
                pmin = np.minimum.accumulate(s[:, o]); pmax = np.maximum.accumulate(s[:, o])
                smin = np.minimum.accumulate(s[::-1, o])[::-1]; smax = np.maximum.accumulate(s[::-1, o])[::-1]
                aL = (s[cut, ax] - s[0, ax] + 1) * (pmax[cut] - pmin[cut] + 1)
                aR = (s[-1, ax] - s[cut + 1, ax] + 1) * (smax[cut + 1] - smin[cut + 1] + 1)
                sav = area0 - (aL + aR)
                j = int(np.argmax(sav))
                if sav[j] > bestv:
                    m = np.zeros(n, bool); m[idx[:cut[j] + 1]] = True
                    bestv, bestm = int(sav[j]), m
            return bestv, bestm
        heap = []
        items = {}
        for i, p in enumerate(planes):
            v, m = best(p['A']); items[i] = (p, m)
            if m is not None: heapq.heappush(heap, (-v, i))
        nid = len(planes); count = len(planes); gained = 0
        min_gain = self.spec.get('split_min_gain', 48)
        while heap and count < cap:
            v, i = heapq.heappop(heap)
            if -v < min_gain: break
            p, m = items.pop(i)
            for part in (m, ~m):
                q = dict(p, A=p['A'][part], C=p['C'][part], part=nid)
                bv, bm = best(q['A']); items[nid] = (q, bm)
                if bm is not None: heapq.heappush(heap, (-bv, nid))
                nid += 1
            count += 1; gained += -v
        self.stats['split_quads_added'] = count - len(planes); self.stats['split_texels_saved'] = int(gained)
        return [p for p, _ in items.values()]


    def pack(self):
        """Skyline bottom-left packing, tallest first, 1 px gutters."""
        np = self.np
        size = self.o['atlas']
        sky = np.zeros(size + 1, np.int64)
        order = sorted(range(len(self.plist)), key=lambda i: (-self.plist[i]['img'].shape[0], -self.plist[i]['img'].shape[1]))
        top = 0
        for i in order:
            h, w = self.plist[i]['img'].shape[:2]
            win = np.lib.stride_tricks.sliding_window_view(sky[:size], w).max(1)
            x = int(np.argmin(win)); y = int(win[x])
            if y + h > size: return False
            self.plist[i]['at'] = (x, y)
            sky[x:x + w + 1] = y + h + 1
            top = max(top, y + h)
        self.stats['atlas_rows_used'] = top
        return True

    def build(self):
        import time
        t0 = time.time()
        def log(*a): print(f'  [{self.name} {time.time() - t0:6.1f}s]', *a, flush=True)
        self.samples(); log('samples', self.stats['samples'])
        self.o['spacing_scale'] = self.spec.get('spacing_scale', self.o['spacing_scale'])
        grow, best = 0, None
        for _ in range(16):
            self.extract(); log('extract density', round(self.o['density'], 3), sum(len(r['L']) for r in self.recs))
            self.merge_small(); self.recolour(); log('recolour')
            self.planes(); log('planes', len(self.plist))
            area = sum((p['img'].shape[0] + 1) * (p['img'].shape[1] + 1) for p in self.plist)
            self.stats['rect_area_frac'] = area / self.o['atlas'] ** 2
            ok = area < 0.97 * self.o['atlas'] ** 2 and self.pack(); log('pack', round(area / self.o['atlas'] ** 2, 3), ok)
            cap = self.spec.get('max_quads', 2200)
            base = self.stats.get('planes_before_split', len(self.plist))
            if ok and (len(self.plist) > cap or (self.spec.get('split') and base > 0.62 * cap)):
                over = max(len(self.plist) / (0.96 * cap), base / (0.58 * cap) if self.spec.get('split') else 0)
                self.o['spacing_scale'] *= min(1.35, max(1.04, over ** 1.3)); log('too many quads -> spacing x', round(self.o['spacing_scale'], 3))
                continue
            if ok and self.stats['rect_area_frac'] < 0.78 and self.o['density'] < 0.99 and grow < 2:
                # spacing grew after the density was cut: give the texels back while the atlas still fits
                grow += 1; best = (list(self.plist), dict(self.stats), self.o['density'])
                self.o['density'] = min(1.0, self.o['density'] * (0.86 / self.stats['rect_area_frac']) ** 0.5)
                log('atlas has room -> density', round(self.o['density'], 3))
                continue
            if ok: break
            if best:
                self.plist, self.stats, self.o['density'] = best; self.pack(); log('kept previous fit'); break
            self.o['density'] *= min(0.97, (0.9 * self.o['atlas'] ** 2 / area) ** 0.5)
        else:
            raise RuntimeError('atlas overflow')
        self.stats['density'] = self.o['density']; self.stats['spacing_scale'] = self.o['spacing_scale']
        return self

    # ------------------------------------------------------------------ writer
    def model(self, provenance):
        import base64, io
        np = self.np
        from PIL import Image
        size = self.o['atlas']
        atlas = np.zeros((size, size, 4), np.uint8)
        elements, kids = [], {b: [] for b in self.parent}
        for p in sorted(self.plist, key=lambda p: (p['bone'], FACE_ORDER[p['face']], p['L'], p.get('part', 0))):
            h, w = p['img'].shape[:2]; x, y = p['at']
            atlas[y:y + h, x:x + w] = p['img']
            f = [0.0] * 3; t = [0.0] * 3
            f[p['ua']], t[p['ua']] = p['u']; f[p['va']], t[p['va']] = p['v']; f[p['da']] = t[p['da']] = p['d']
            name = f"{p['bone']}_{p['face']}_{p['L']}" + (f"_{p['part']}" if p.get('part') else '')
            e = {'type': 'cube', 'name': name, 'uuid': _uid(self.name, name), 'origin': self.origin[p['bone']],
                 'rotation': [0, 0, 0], 'from': [round(v, 5) for v in f], 'to': [round(v, 5) for v in t], 'box_uv': False,
                 'faces': {k: ({'uv': [x, y, x + w, y + h], 'texture': 0} if k == p['face'] else {'uv': [0, 0, 0, 0], 'texture': None})
                           for k in ('north', 'south', 'west', 'east', 'up', 'down')}}
            if p['bone'].endswith('_glow'): e['light_emission'] = 15
            elements.append(e); kids[p['bone']].append(e['uuid'])
        self.atlas = atlas
        groups = {}
        for b in self.parent:
            groups[b] = {'uuid': _uid(self.name, 'bone', b), 'name': b, 'origin': self.origin[b], 'export': True,
                         'visibility': True, 'children': list(kids[b])}
        roots = []
        for b in self.parent:
            p = self.parent[b]
            (groups[p]['children'] if p else roots).append(groups[b])
        buf = io.BytesIO(); Image.fromarray(atlas, 'RGBA').save(buf, 'PNG', optimize=True)
        tex = {'name': f'{self.name}.png', 'id': '0', 'uuid': _uid(self.name, 'texture'), 'width': size, 'height': size,
               'uv_width': size, 'uv_height': size, 'internal': True, 'saved': True,
               'source': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()}
        m = {'meta': {'format_version': '4.10', 'model_format': 'free', 'box_uv': False}, 'name': self.name,
             'resolution': {'width': size, 'height': size}, 'elements': elements, 'outliner': roots, 'textures': [tex],
             'animations': self.animations(groups) if self.spec['kind'] == 'fallen' else self.authored_animations(groups),
             'w300': provenance}
        self.stats['quads'] = len(elements)
        self.stats['quads_per_bone'] = {b: len(kids[b]) for b in kids}
        opaque = atlas[..., 3] > 0
        self.stats['atlas_opaque'] = int(opaque.sum())
        self.stats['mean_luma'] = float((atlas[opaque][:, :3] @ np.array([.299, .587, .114])).mean())
        return m

    def authored_animations(self, groups):
        """Shank/Walker: the r4b authored clips (data/<name>_authored_clips.json, from main) re-keyed onto the new rig by
        bone name. Walker middle legs (no contract bone in r4b) reuse the same-side back leg keys; in walk they run half a
        cycle out of phase with it."""
        import copy
        doc = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', f'{self.name}_authored_clips.json')))
        clips = []
        for a in doc['clips']:
            c = {k: v for k, v in a.items() if k != 'animators'}
            c['uuid'] = _uid(self.name, 'clip', a['name'])
            an = dict(a['animators'])
            if self.spec['kind'] == 'walker':
                for mid, src in (('leg_ml', 'leg_bl'), ('leg_mr', 'leg_br')):
                    for suf in ('', '_low'):
                        if src + suf not in an: continue
                        kfs = copy.deepcopy(an[src + suf])
                        if a['name'] == 'walk':
                            L = a['length']
                            for kf in kfs: kf['time'] = round((kf['time'] + L / 2) % L, 4)
                            kfs.sort(key=lambda kf: (kf['channel'], kf['time']))
                            # keep the loop closed: duplicate the t=0 key at t=L for every channel
                            for ch in {kf['channel'] for kf in kfs}:
                                first = min((kf for kf in kfs if kf['channel'] == ch), key=lambda kf: kf['time'])
                                if first['time'] == 0 and not any(kf['channel'] == ch and abs(kf['time'] - L) < 1e-6 for kf in kfs):
                                    e = copy.deepcopy(first); e['time'] = L; kfs.append(e)
                        an[mid + suf] = kfs
            c['animators'] = {}
            for b, kfs in an.items():
                if b not in groups: continue
                c['animators'][groups[b]['uuid']] = {'name': b, 'type': 'bone',
                                                     'keyframes': [dict(kf, uuid=_uid(self.name, a['name'], b, i)) for i, kf in enumerate(kfs)]}
            clips.append(c)
        return clips

    def animations(self, groups):
        """Handoff Dreg clips on the shared 19-bone Fallen rig: rotations unchanged, positions x fpos; + contract aliases."""
        import copy
        bone_of = {}
        for g in self._handoff_groups(): bone_of[g['uuid']] = g['name']
        clips = []
        for a in self.handoff['animations']:
            c = {k: v for k, v in a.items() if k != 'animators'}
            c['uuid'] = _uid(self.name, 'clip', a['name'])
            c['animators'] = {}
            for au, an in a['animators'].items():
                b = bone_of.get(au, an.get('name'))
                if b not in groups: continue
                kfs = []
                for i, kf in enumerate(an.get('keyframes', [])):
                    k = copy.deepcopy(kf); k['uuid'] = _uid(self.name, a['name'], b, i)
                    if k['channel'] == 'position':
                        k['data_points'] = [{ax: f'{float(dp[ax]) * self.fpos:.5f}'.rstrip('0').rstrip('.') for ax in ('x', 'y', 'z')}
                                            for dp in k['data_points']]
                    kfs.append(k)
                c['animators'][groups[b]['uuid']] = {'name': b, 'type': 'bone', 'keyframes': kfs}
            clips.append(c)
        by = {c['name']: c for c in clips}
        def alias(new, old, scale=1.0, loop=None):
            c = copy.deepcopy(by[old]); c['name'] = new; c['uuid'] = _uid(self.name, 'clip', new)
            c['length'] = round(c['length'] * scale, 6)
            if loop: c['loop'] = loop
            for an in c['animators'].values():
                for k in an['keyframes']:
                    k['time'] = round(k['time'] * scale, 6); k['uuid'] = _uid(self.name, new, k['uuid'])
            clips.append(c)
        if 'damage' not in by: alias('damage', 'hurt')
        alias('shoot', 'fire'); alias('hit', 'hurt'); alias('stagger', 'hurt'); alias('spawn', 'surprise_front')
        alias('run', 'walk', 0.72, 'loop')
        return clips


def write_bake(name, out, evidence=None, opts=None):
    import hashlib
    b = Bake(name, opts).build()
    prov = {'generator': 'scripts/campaign/bake_dreglight.py', 'technique': 'Dreg-Light depth-slice quads (W300 r7)',
            'source': b.spec['src'], 'weapons': [w['prefix'] for w in b.spec.get('weapons', [])],
            'clips': ('Dreg-Light handoff dreg_combat.bbmodel (13 D2 clips + damage) on the shared Fallen rig + aliases'
                      if b.spec['kind'] == 'fallen' else 'r4b authored clips re-keyed by bone name (data/%s_authored_clips.json)' % name),
            'handoff_sha256': hashlib.sha256(open(HANDOFF, 'rb').read()).hexdigest(),
            'scale': {k: round(v, 6) for k, v in b.stats.items() if k in ('k', 'y0', 'skeleton_scale_vs_dreg', 'position_key_scale')},
            'palette': 'House of Dusk'}
    m = b.model(prov)
    data = json.dumps(m, separators=(',', ':')).encode()
    open(out, 'wb').write(data)
    b.stats['sha256'] = hashlib.sha256(data).hexdigest(); b.stats['bytes'] = len(data)
    if evidence:
        from PIL import Image
        os.makedirs(evidence, exist_ok=True)
        Image.fromarray(b.atlas, 'RGBA').save(f'{evidence}/{name}_atlas.png')
        json.dump(b.stats, open(f'{evidence}/{name}_stats.json', 'w'), indent=1, default=float)
    print(name, 'quads', b.stats['quads'], 'luma', round(b.stats['mean_luma'], 1), 'density', round(b.stats['density'], 3),
          'k', round(b.k, 4), 'skel', round(b.skel, 4), 'resid_m', round(b.stats['skeleton_residual_m'], 4))
    return b


if __name__ == '__main__' and 'bpy' not in sys.modules:
    a = sys.argv[1:]
    if a and a[0] == 'bake':
        ev = a[a.index('--evidence') + 1] if '--evidence' in a else None
        write_bake(a[1], a[2], ev)
    else:
        print(__doc__)
