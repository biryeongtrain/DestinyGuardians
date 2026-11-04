"""Read-only FBX rig/material audit, run in a separate factory-startup Blender process.

Usage: blender -b --factory-startup --python this.py -- SOURCE_MODELS OUTPUT
Output is diagnostic evidence, not a final shader bake or runtime model.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix
import math


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(folder, output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = folder / (folder.name + '.fbx')
    bpy.ops.import_scene.fbx(filepath=str(source))
    # Match the existing Dreg-Light source conversion; preserve the native matrices below.
    native_roots = {o.name: [list(row) for row in o.matrix_world]
                    for o in bpy.data.objects if o.parent is None}
    conversion = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(100, 4)
    for obj in list(bpy.data.objects):
        if obj.parent is None:
            obj.matrix_world = conversion @ obj.matrix_world
    bpy.context.view_layer.update()
    meshes = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        obj.data.calc_loop_triangles()
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        groups = {g.index: g.name for g in obj.vertex_groups}
        weights = {}
        for vertex in obj.data.vertices:
            for group in vertex.groups:
                if group.weight > 0:
                    name = groups[group.group]
                    weights[name] = weights.get(name, 0) + 1
        meshes.append(dict(name=obj.name, parent=obj.parent.name if obj.parent else None,
                           parentBone=obj.parent_bone, vertices=len(vertices),
                           triangles=len(obj.data.loop_triangles),
                           boundsMin=[min(v[i] for v in vertices) for i in range(3)] if vertices else [],
                           boundsMax=[max(v[i] for v in vertices) for i in range(3)] if vertices else [],
                           uvLayers=[layer.name for layer in obj.data.uv_layers],
                           materials=[s.material.name if s.material else None for s in obj.material_slots],
                           weightedVertexCounts=weights,
                           modifiers=[dict(type=m.type, target=getattr(getattr(m, 'object', None), 'name', None))
                                      for m in obj.modifiers]))
    rigs = []
    for obj in bpy.data.objects:
        if obj.type != 'ARMATURE':
            continue
        rigs.append(dict(name=obj.name, bones=[dict(name=b.name, parent=b.parent.name if b.parent else None,
                        head=list(obj.matrix_world @ b.head_local), tail=list(obj.matrix_world @ b.tail_local),
                        matrix=[list(row) for row in obj.matrix_world @ b.matrix_local]) for b in obj.data.bones]))
    materials = []
    for mat in bpy.data.materials:
        tag = mat.name.split('.')[0]
        slots_path = folder / 'Materials' / (tag + '.slots.json')
        slots = json.loads(slots_path.read_text())['slots'] if slots_path.exists() else []
        materials.append(dict(name=mat.name, useNodes=mat.use_nodes,
                              diffuseColor=list(mat.diffuse_color), slots=slots,
                              images=[dict(node=n.name, path=n.image.filepath, size=list(n.image.size))
                                      for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
                              if mat.node_tree else []))
    textures = []
    for path in sorted((folder / 'TexturesDDS').glob('*.dds')):
        try:
            image = bpy.data.images.load(str(path), check_existing=False)
            textures.append(dict(name=path.name, bytes=path.stat().st_size, sha256=sha(path),
                                 size=list(image.size), channels=image.channels, loaded=bool(image.size[0])))
            bpy.data.images.remove(image)
        except Exception as error:
            textures.append(dict(name=path.name, sha256=sha(path), error=str(error)))
    result = dict(source=str(source), sourceSha256=sha(source), blender=bpy.app.version_string,
                  coordinates='Dreg-Light normalized source, Z up; scale is not yet a Minecraft ship-size decision',
                  nativeRootMatrices=native_roots, meshes=meshes, armatures=rigs, materials=materials,
                  actions=[dict(name=a.name, frameRange=list(a.frame_range)) for a in bpy.data.actions],
                  textures=textures)
    output.mkdir(parents=True, exist_ok=True)
    (output / (folder.name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('SKIFF_SOURCE_AUDIT', folder.name, len(meshes), 'meshes',
          sum(m['triangles'] for m in meshes), 'triangles',
          [len(r['bones']) for r in rigs], 'bones', len(result['actions']), 'actions')


def inspect_motions(folder, output):
    import numpy as np
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = folder / 'native' / ('rig_' + folder.name + '.fbx')
    bpy.context.scene.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=str(source))
    conversion = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(100, 4)
    for obj in list(bpy.data.objects):
        if obj.parent is None:
            obj.matrix_world = conversion @ obj.matrix_world
    bpy.context.view_layer.update()
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if len(arms) != 1:
        raise ValueError('Expected one source motion rig: ' + str(source))
    arm = arms[0]; arm.animation_data_create()
    names = [b.name for b in arm.data.bones]
    data = {'names': np.array(names), 'rest': np.array([np.array(arm.matrix_world @ b.matrix_local) for b in arm.data.bones])}
    clips = []
    expected = json.loads((folder/'original-clips.json').read_text())['clips']
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        matches = [c for c in expected if c['source_clip'] in action.name]
        if len(matches) != 1:
            raise ValueError('Unmapped source action: ' + action.name)
        tag = matches[0]['source_clip']
        arm.animation_data.action = action
        if len(action.slots) != 1:
            raise ValueError('Ambiguous source action slots: ' + action.name)
        arm.animation_data.action_slot = action.slots[0]
        start, end = (int(round(t)) for t in action.frame_range)
        matrices = []
        for frame in range(start, end+1):
            bpy.context.scene.frame_set(frame)
            matrices.append(np.array([np.array(arm.matrix_world @ arm.pose.bones[n].matrix) for n in names]))
        values = np.array(matrices)
        if not np.isfinite(values).all():
            raise ValueError('Non-finite imported source motion: ' + tag)
        data['clip_'+tag] = values
        movement = np.linalg.norm(values[:, :, :3, 3] - values[0, :, :3, 3], axis=2)
        curves = []
        for layer in action.layers:
            for strip in layer.strips:
                bag = strip.channelbag(action.slots[0])
                if bag is None:
                    continue
                for curve in bag.fcurves:
                    key_values = [float(k.co.y) for k in curve.keyframe_points]
                    curves.append(dict(path=curve.data_path, component=curve.array_index,
                                       keys=len(key_values), valueMin=min(key_values), valueMax=max(key_values)))
        clips.append(dict(tag=tag, action=action.name, frames=len(values), firstFrame=start, lastFrame=end,
                          manifestFrames=matches[0]['frames'], frameCountMatchesManifest=len(values)==matches[0]['frames'],
                          importedFrameRange=list(action.frame_range),
                          maxMatrixComponentDelta=float(np.max(np.abs(values-values[0]))), curves=curves,
                          maxWorldTranslationFromFirstByBone=dict(zip(names, movement.max(axis=0).tolist()))))
    if {c['tag'] for c in clips} != {c['source_clip'] for c in expected}:
        raise ValueError('Missing extracted source clips')
    metadata=dict(source=str(source), sha256=sha(source), names=names, clips=clips,
                  importedSceneFps=bpy.context.scene.render.fps / bpy.context.scene.render.fps_base,
                  coordinates='Dreg-Light normalized source, Z up; bone world matrices; roles not inferred from hashes')
    data['metadata'] = json.dumps(metadata)
    np.savez_compressed(output/(folder.name+'-motion.npz'), **data)
    (output/(folder.name+'-motion.json')).write_text(json.dumps(metadata,indent=2)+'\n')
    print('SKIFF_MOTION_AUDIT', folder.name, len(names), 'bones', [(c['tag'],c['frames']) for c in clips])


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    source, output = map(Path, args)
    for tag in ('80C3EE92', '80CC0740'):
        inspect(source / ('skiff__' + tag), output)
        inspect_motions(source.parent / 'motions' / tag, output)
