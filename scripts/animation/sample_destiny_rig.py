"""Independent FBX evaluation in an isolated Blender process; never edits the source.

rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background \
  --factory-startup --disable-autoexec --python scripts/animation/sample_destiny_rig.py \
  -- --source <return-folder> --output <new-output-folder>

Output uses armature object space and retains the import matrix as metadata. It does
not silently bake FBX centimetre/axis metadata into Minecraft coordinates, retarget
to BetterModel, retime gameplay, or certify a 1P clip from a 3P rig.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def vector(value):
    result = [float(x) for x in value]
    if not all(math.isfinite(x) for x in result):
        raise ValueError('Non-finite evaluated FBX transform')
    return result


def matrix(value):
    return [vector(row) for row in value]


def sample(source, group, kind='hunter', tags=None):
    # Empty, isolated process only. This script must not run through live Blender MCP.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8-sig'))
    if kind == 'hunter':
        expected = {c['id']: c for c in manifest['clips'] if c.get('preferredGroup') == group}
        bone_map_path = source/'provenance/bone-map.json'
        paths = {c.get('files', {}).get('fbx') for c in expected.values()}
    else:
        declared_group = next(g for g in manifest['groups'] if g['id'] == group)
        expected = {c['tags']['clip']: c for c in manifest['clips'] if group in c.get('groupIds', [])}
        paths = {declared_group['firstPersonFbx']}
        bone_map_path = source/'clips'/group/'bone-map.json'
    if tags is not None:
        expected = {tag: c for tag,c in expected.items() if tag in tags}
    if not expected:
        raise ValueError('No manifest clips for ' + group)
    if len(paths) != 1 or None in paths:
        raise ValueError('Expected one explicitly mapped FBX for ' + group)
    path = (source / paths.pop()).resolve()
    if source not in path.parents or not path.is_file():
        raise ValueError('FBX reference escapes source or is missing')
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=True)
    rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    if len(rigs) != 1:
        raise ValueError('Ambiguous FBX armature count')
    rig = rigs[0]
    if rig.constraints or rig.animation_data and rig.animation_data.drivers:
        raise ValueError('Unexpected evaluated constraints/drivers')
    bone_map = json.loads(bone_map_path.read_text(encoding='utf-8-sig'))
    semantic = {b['name']: b for b in bone_map}
    bones = list(rig.data.bones)
    if len({b.name for b in bones}) != len(bones) or set(semantic) != {b.name for b in bones}:
        raise ValueError('Imported and provenance bone sets differ')
    # Bone-map Index order is not Blender's bone order. Match stable names, never zip lists.
    by_index = {b['Index']: b['name'] for b in bone_map}
    for bone in bones:
        parent_index = semantic[bone.name]['ParentNodeIndex']
        expected_parent = None if parent_index < 0 else by_index[parent_index]
        if (bone.parent.name if bone.parent else None) != expected_parent:
            raise ValueError('Bone parent mismatch: ' + bone.name)
    bone_names = [b.name for b in bones]
    bone_rows = [dict(name=b.name, semanticName=semantic[b.name]['semanticName'],
        parent=b.parent.name if b.parent else None, head=vector(b.head_local),
        tail=vector(b.tail_local), restMatrix=matrix(b.matrix_local),
        weaponBone=semantic[b.name].get('weaponBone',False),
        weaponBoneIndex=semantic[b.name].get('weaponBoneIndex')) for b in bones]
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    clips = []
    for tag, declared in expected.items():
        prefix = '|fp_' if kind == 'weapon' else '|'
        actions = [a for a in bpy.data.actions if (prefix + tag + '_') in a.name or (prefix + tag + '|') in a.name]
        if len(actions) != 1:
            raise ValueError('Missing/ambiguous action for ' + tag)
        action = actions[0]
        rig.animation_data_create()
        rig.animation_data.action = action
        if len(action.slots) != 1:
            raise ValueError('Ambiguous action slot for ' + tag)
        rig.animation_data.action_slot = action.slots[0]
        start, end = map(float, action.frame_range)
        if start != int(start) or end != int(end) or fps <= 0 or end <= start:
            raise ValueError('Unsupported frame/time domain')
        frames = []
        for frame in range(int(start), int(end) + 1):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            heads = [vector(rig.pose.bones[name].head) for name in bone_names]
            # Object-space matrices retain cumulative pose and root motion. Consumers must
            # derive local/rest deltas explicitly, rather than treating these as local Euler.
            poses = [matrix(rig.pose.bones[name].matrix) for name in bone_names]
            frames.append(dict(frame=frame, seconds=(frame-start)/fps, heads=heads, matrices=poses))
        max_motion = max(math.dist(frames[0]['heads'][i], f['heads'][i])
                         for f in frames for i in range(len(bones)))
        if max_motion <= 1e-7:
            raise ValueError('No actual evaluated motion for ' + tag)
        clips.append(dict(tag=tag, action=action.name, sourceNames=declared.get('sourceNames', []),
            perspective=declared.get('perspective', 'unknown'), startFrame=start, endFrame=end,
            sampleCount=len(frames), durationSeconds=(end-start)/fps, maxBoneHeadDisplacement=max_motion,
            events=declared.get('events', []), frames=frames))
    return dict(schemaVersion=1, group=group, sourceFbx=str(path.relative_to(source)),
        sourceFbxSHA256=digest(path), sourceManifestSHA256=digest(source/'manifest.json'),
        sourceBoneMapSHA256=digest(bone_map_path),
        blenderVersion=bpy.app.version_string, blenderBuild=bpy.app.build_hash.decode(),
        sampleSpace='armature_object', matrixConvention='row_major; column_vectors',
        rotationRepresentation='4x4 cumulative armature pose matrices; not local Euler channels',
        fps=fps, fpsBasis='FBX import scene render.fps/render.fps_base',
        importObjectMatrix=matrix(rig.matrix_world), importObjectScale=vector(rig.scale),
        coordinateStatus='Rest semantic head/foot confirm Z-height in armature space; forward sign and Minecraft retarget unverified',
        bones=bone_rows, clips=clips, minecraftApplied=False, nativeVerified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--groups', nargs='+', default=['hunter_arc_staff', 'hunter_shadowshot'])
    parser.add_argument('--kind', choices=['hunter','weapon'], default='hunter')
    parser.add_argument('--tags', nargs='+')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source = args.source.resolve()
    if args.output.resolve().is_relative_to(source):
        parser.error('Output must be outside the read-only delivery')
    args.output.mkdir(parents=True, exist_ok=False)
    for group in args.groups:
        if args.kind == 'hunter' and group not in {'hunter_arc_staff', 'hunter_shadowshot'}:
            raise ValueError('Only the explicitly verified Hunter groups are admitted')
        result = sample(source, group, args.kind, set(args.tags) if args.tags else None)
        path = args.output / (group + '.json')
        path.write_text(json.dumps(result, separators=(',', ':'), allow_nan=False)+'\n')
        print('W196_SAMPLE', group, 'bones', len(result['bones']), 'clips', len(result['clips']), str(path))


if __name__ == '__main__':
    main()
