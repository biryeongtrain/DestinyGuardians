#!/usr/bin/env python3
"""Shared strike briefing poses from the Crota's End landing cinematic (cin_728_rai).

Evaluate (read-only source):
  Blender --background --factory-startup --disable-autoexec --python THIS --
    --evaluate --source-root ~/Downloads/Destiny-Raid-Briefing-Poses-2026-11-04 --samples /tmp/.../evaluated.json
Convert: python3 -B THIS --root CHECKOUT --samples JSON [--output-root OUT] [--verify]

Retarget math is the W260 Trials-intro pipeline (same 72-bone guardian rig, verified rest).
Each clip lands, then HOLDS its final pose until HOLD_SECONDS so the briefing voice can finish.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROLES = (('pla03', '80B902FF'), ('pla01', '80B90307'), ('pla06', '80B9030A'))
# First source frame (1-based) each role becomes visible: just before its descent, where it transmats in mid-air.
# Earlier frames only hold an off-stage pose. Runtime delays each actor by (frame-1)/30 s so cross-role timing is kept.
REVEAL_FRAME = {'pla01': 1, 'pla06': 81, 'pla03': 141}
SOURCE_BLEND = 'Crota_Landing_Guardians.blend'
SOURCE_FILES = [SOURCE_BLEND, 'README.md', 'rig.json', 'manifest.csv', 'briefing/timeline.json',
                'poses/pla03.json', 'poses/pla01.json', 'poses/pla06.json']
FRAMES = 266
HOLD_SECONDS = 30.0
PACK = 'src/main/resources/destiny/animation/briefing_crota_landing.animation.json'
PROVENANCE = 'art/strikes/briefing/briefing-poses-provenance.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def evaluate(args):
    import bpy
    source = args.source_root.resolve(); output = args.samples.resolve()
    if output.is_relative_to(source): raise ValueError('Source is read-only')
    if not bpy.app.background or bpy.context.preferences.filepaths.use_scripts_auto_execute:
        raise RuntimeError('Require headless Blender --factory-startup --disable-autoexec')
    hashes = {p: sha(source / p) for p in SOURCE_FILES}
    bpy.ops.wm.open_mainfile(filepath=str(source / SOURCE_BLEND), use_scripts=False)
    rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']; assert len(rigs) == 1
    rig = rigs[0]; assert len(rig.data.bones) == 72
    scene = bpy.context.scene; assert scene.render.fps / scene.render.fps_base == 30
    group = {'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'head': list(b.head_local),
                        'tail': list(b.tail_local), 'matrix': [list(r) for r in b.matrix_local]} for b in rig.data.bones],
             'clips': []}
    rig.animation_data_create()
    for track in rig.animation_data.nla_tracks: track.mute = True
    for role, tag in ROLES:
        actions = [a for a in bpy.data.actions if a.name == role + '__' + tag]; assert len(actions) == 1, role
        action = actions[0]; rig.animation_data.action = action
        slots = [s for s in action.slots if s.target_id_type == 'OBJECT']; assert len(slots) <= 1
        if slots: rig.animation_data.action_slot = slots[0]
        assert tuple(action.frame_range) == (1.0, float(FRAMES)), action.frame_range
        frames = []
        for frame in range(1, FRAMES + 1):
            scene.frame_set(frame); bpy.context.view_layer.update()
            ev = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
            joints = {b.name: [list(r) for r in b.matrix] for b in ev.pose.bones}
            assert all(math.isfinite(v) for m in joints.values() for row in m for v in row)
            frames.append({'frame': frame, 'joints': joints})
        group['clips'].append({'role': role, 'tag': tag, 'action': action.name, 'firstFrame': 1.0,
                               'lastFrame': float(FRAMES), 'fps': 30, 'frames': frames})
        print('EVALUATED', role, tag, len(frames), flush=True)
    assert hashes == {p: sha(source / p) for p in SOURCE_FILES}, 'Source drift'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'schemaVersion': 1, 'sourceRoot': str(source), 'sourceHashes': hashes,
        'blenderVersion': bpy.app.version_string, 'sampleSpace': 'armature_object', 'autoexecDisabled': True,
        'groups': [group]}, separators=(',', ':'), allow_nan=False) + '\n')
    print('BRIEFING_SOURCE_COMPLETE', output, flush=True)

def convert(args):
    root = args.root.resolve(); output = (args.output_root or root).resolve()
    data = json.loads(args.samples.read_text()); source = Path(data['sourceRoot']).resolve()
    if output.is_relative_to(source): raise ValueError('Source is read-only')
    assert data['autoexecDisabled'] and data['sampleSpace'] == 'armature_object'
    assert data['sourceHashes'] == {p: sha(source / p) for p in data['sourceHashes']}, 'Source drift'
    sys.path[:0] = [str(root / 'scripts'), str(root / 'scripts/animation')]
    import build_hunter_animation_h15 as h15, build_hunter_animation_h19 as h19, build_hunter_source_w197 as w197
    import build_crucible_intro_w260 as base
    model_path = root / 'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
    model = json.loads(model_path.read_text()); groups = {g['name']: g for g in model['groups']}
    base.h15, base.h19, base.w197, base.C, base.model, base.GROUPS = h15, h19, w197, w197.C, model, groups
    g = data['groups'][0]; bones = {b['name']: b for b in g['bones']}
    reference = root / 'art/weapons/w197/hunter-source-motion.json'
    old = json.loads(reference.read_text())['bones']; assert old.keys() == bones.keys()
    rest = max(abs(old[n]['restMatrix'][i][j] - bones[n]['matrix'][i][j]) for n in bones for i in range(4) for j in range(4))
    assert rest < 1e-5, ('Source rig differs', rest)
    units = groups['phip_hip']['origin'][1] / bones['C7C0BA6E']['head'][2]
    clips, summaries = [], []
    for c in g['clips']:
        start = REVEAL_FRAME[c['role']]
        c = dict(c, frames=[f for f in c['frames'] if f['frame'] >= start])
        normals, repairs = {}, {}
        for chain in [['9F0FD28C', '8BD44A3F', 'B9B9E05D'], ['695DAF09', '35B14D1B', '0F8B505D'],
                      ['D1232BA2', '897A1504', '8C83CB67'], ['17025F50', 'A3781DCD', 'DE9D6BEA']]:
            normals[chain[0]], repairs[chain[0]] = base.stable_normals(c, chain)
        frames = [(round((f['frame'] - start) / 30, 9), base.pose(g, f, {n: vs[i] for n, vs in normals.items()}))
                  for i, f in enumerate(c['frames'])]
        base.unwrap(frames)
        name = 'h15_intro_brief_' + c['role']
        clip = h15.clip(model, name, frames, root_positions={}, linear_root=True)
        # Full pelvis trajectory relative to the final landed hip; runtime pins X/Z (inPlaceIntro).
        end_pose = frames[-1][1]
        end_hip = base.xyz(h19.fk(model, end_pose)['phip_hip']); end_hip[1] += h15.floor_y(model, end_pose)
        end_source = base.xyz(c['frames'][-1]['joints']['C7C0BA6E'])
        positions = []
        for (_, p), f in zip(frames, c['frames']):
            delta = h19.mul(base.convert(h19.sub(base.xyz(f['joints']['C7C0BA6E']), end_source)), units)
            positions.append(h19.sub(h19.add(end_hip, delta), base.xyz(h19.fk(model, p)['phip_hip'])))
        length = (FRAMES - start) / 30
        max_step = 0
        for animator in clip['animators'].values():
            previous = None; index = 0; last = {}
            for k in animator['keyframes']:
                k['interpolation'] = 'linear'
                if k['channel'] == 'position':
                    k['data_points'] = [dict(zip('xyz', positions[index]))]; index += 1
                else:
                    values = [k['data_points'][0][a] for a in 'xyz']
                    if previous is not None: max_step = max(max_step, max(abs(a - b) for a, b in zip(values, previous)))
                    previous = values
                k['data_points'][0] = {a: round(float(v), 7) for a, v in k['data_points'][0].items()}
                if abs(k['time'] - length) < 1e-8: k['time'] = length
                if k['time'] == length: last[k['channel']] = k
            # Hold: duplicate each channel's final key at HOLD_SECONDS (linear => exact still pose).
            for channel, k in last.items():
                hold = json.loads(json.dumps(k)); hold['time'] = HOLD_SECONDS
                hold['uuid'] = hashlib.md5((name + animator.get('name', '') + channel).encode()).hexdigest()
                hold['uuid'] = '-'.join([hold['uuid'][:8], hold['uuid'][8:12], hold['uuid'][12:16], hold['uuid'][16:20], hold['uuid'][20:]])
                animator['keyframes'].append(hold)
        # Face the briefing camera: bake the final chest heading out of the root (model forward = stage yaw).
        def final_pose():
            pose = h15.zero()
            for a in clip['animators'].values():
                n = a.get('name'); ks = [k for k in a['keyframes'] if k['channel'] == 'rotation']
                if not ks or n not in pose: continue
                k = max(ks, key=lambda k: k['time'])['data_points'][0]; pose[n] = [k['x'], k['y'], k['z']]
            return pose
        def heading():
            m = h19.fk(model, final_pose())['pc_chest']; return math.degrees(math.atan2(m[0][2], m[2][2]))
        facing = heading(); turn = h15.rot([0, -facing, 0])
        root_bone = next(a for a in clip['animators'].values() if a.get('name') == 'player_root')
        previous = None
        for k in sorted((k for k in root_bone['keyframes'] if k['channel'] == 'rotation'), key=lambda k: k['time']):
            d = k['data_points'][0]; e = h19.euler(h15.mm(turn, h15.rot([d['x'], d['y'], d['z']])))
            if previous: e = min(([v + 360 * round((o - v) / 360) for v, o in zip(f, previous)] for f in ([e[0], e[1], e[2]], [e[0] + 180, 180 - e[1], e[2] + 180])),
                                 key=lambda q: sum((a - b) ** 2 for a, b in zip(q, previous)))
            previous = e; k['data_points'][0] = {a: round(float(v), 7) for a, v in zip('xyz', e)}
        for k in root_bone['keyframes']:
            if k['channel'] == 'position':
                d = k['data_points'][0]; v = h19.vector(turn, [d['x'], d['y'], d['z']])
                k['data_points'][0] = {a: round(float(x), 7) for a, x in zip('xyz', v)}
        assert abs(heading()) < 1, ('Facing bake failed', c['role'], heading())
        clip['length'] = HOLD_SECONDS; clip['snapping'] = 30
        assert max_step < 90, ('Euler discontinuity', c['role'], max_step)
        assert all(math.isfinite(v) for a in clip['animators'].values() for k in a['keyframes'] for v in k['data_points'][0].values())
        clearance = [pos[1] - h15.floor_y(model, p) for (_, p), pos in zip(frames, positions)]
        clips.append(clip)
        summaries.append({'name': name, 'role': c['role'], 'sourceTag': c['tag'], 'action': c['action'],
                          'sourceFrames': FRAMES, 'revealSourceFrame': start, 'revealDelaySeconds': (start - 1) / 30,
                          'motionSeconds': length, 'bakedFacingCorrectionDegrees': -facing, 'holdUntilSeconds': HOLD_SECONDS,
                          'maxAdjacentEulerStepDegrees': max_step, 'targetLowestSkinRange': [min(clearance), max(clearance)],
                          'collinearRepairs': {n: len(r) for n, r in repairs.items() if r}})
        print('RETARGET', name, 'maxEulerStep', round(max_step, 3), 'clearance', round(min(clearance), 3), round(max(clearance), 3), flush=True)
    helpers = ['scripts/build_hunter_animation_h15.py', 'scripts/build_hunter_animation_h19.py', 'scripts/build_hunter_source_w197.py',
               'scripts/animation/build_crucible_intro_w260.py', str(model_path.relative_to(root)), str(reference.relative_to(root))]
    manifest = {'schemaVersion': 1, 'source': 'Crota\'s End raid landing cinematic cin_728_rai (user-selected roles pla03/pla01/pla06)',
                'sourceRoot': str(source), 'sourceHashes': data['sourceHashes'], 'samplesSha256': sha(args.samples),
                'generatorSha256': sha(Path(__file__)), 'helperHashes': {p: sha(root / p) for p in helpers},
                'blenderVersion': data['blenderVersion'], 'maxRestMatrixDifference': rest,
                'retarget': 'W260 pipeline: source torso/pelvis rotations, geometric legs, elbow IK, transported bend planes, Euler unwrap; '
                            'pelvis trajectory proportional to bind hip height and anchored at the final landing; runtime pins X/Z.',
                'hold': 'final pose duplicated at holdUntilSeconds; runtime ends the cast at phase exit',
                'clips': summaries,
                'limitations': ['rigid 16-group skin cannot reproduce fingers, wrists, ankles or cloth',
                                'formation, camera and voice sync are authored for the strike, not recovered from the raid',
                                'no frame-by-frame comparison against the original game']}
    for rel, obj, indent in [(PACK, {'animations': clips}, None), (PROVENANCE, manifest, 2)]:
        raw = (json.dumps(obj, indent=indent, separators=None if indent else (',', ':'), allow_nan=False) + '\n').encode()
        path = output / rel
        if args.verify: assert path.read_bytes() == raw, ('Reproduction differs', path)
        else: path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print('BRIEFING_RETARGET_COMPLETE', output, flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluate', action='store_true'); parser.add_argument('--source-root', type=Path)
    parser.add_argument('--samples', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root', type=Path); parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
    if args.evaluate: evaluate(args)
    else: convert(args)

if __name__ == '__main__': main()
