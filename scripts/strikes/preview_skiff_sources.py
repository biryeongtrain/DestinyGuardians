"""Headless albedo-only source preview; shader/dye/alpha fidelity is explicitly unverified.

blender -b --factory-startup --python this.py -- SOURCE_MODELS OUTPUT
Does not save or modify the FBX, DDS, or any user's Blender scene.
"""
import json
import math
import sys
import os
import re
from pathlib import Path
import bpy
from mathutils import Matrix, Vector


def preview(folder, output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(folder / (folder.name + '.fbx')))
    conversion = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(100, 4)
    for obj in list(bpy.data.objects):
        if obj.parent is None:
            obj.matrix_world = conversion @ obj.matrix_world
    bpy.context.view_layer.update()
    exclusion = os.environ.get('SKIFF_PREVIEW_EXCLUDE', '')
    excluded = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and exclusion and re.search(exclusion, obj.name):
            obj.hide_render = True
            excluded.append(obj.name)
    mapping = []
    for mat in bpy.data.materials:
        tag = mat.name.split('.')[0]
        path = folder / 'Materials' / (tag + '.slots.json')
        slots = json.loads(path.read_text())['slots'] if path.exists() else []
        # Slot selection is a diagnostic hypothesis, never a recovered Bungie material.
        candidates = [s for s in slots if s.get('srgb') and (folder / 'TexturesDDS' / (s['texture'] + '.dds')).is_file()]
        chosen = next((s for s in candidates if s.get('slot') == 0), candidates[0] if candidates else None)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        shader = nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Roughness'].default_value = .65
        output_node = nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(shader.outputs['BSDF'], output_node.inputs['Surface'])
        if chosen:
            image = bpy.data.images.load(str(folder / 'TexturesDDS' / (chosen['texture'] + '.dds')), check_existing=True)
            image.colorspace_settings.name = 'sRGB'
            node = nodes.new('ShaderNodeTexImage'); node.image = image
            mat.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
        else:
            # Magenta flags unresolved source material instead of silently certifying gray.
            shader.inputs['Base Color'].default_value = (.55, .015, .3, 1)
        mapping.append(dict(material=mat.name, diagnosticTexture=chosen, unresolved=chosen is None))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
    points = [o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    center = (low + high) / 2
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 960; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new('DiagnosticWorld'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.16, .18, .22, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
    scene.view_settings.view_transform = 'Standard'
    camera_data = bpy.data.cameras.new('DiagnosticCamera')
    camera = bpy.data.objects.new('DiagnosticCamera', camera_data); scene.collection.objects.link(camera)
    camera.location = center + Vector((38, -45, 28))
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.type = 'ORTHO'; camera_data.ortho_scale = max(high-low) * 1.12
    scene.camera = camera
    for name, offset, energy, size in [('Key', (10,-18,30), 17000, 25), ('Fill', (-25,5,15), 11000, 20)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
        obj.location=center+Vector(offset);obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
    output.mkdir(parents=True,exist_ok=True)
    suffix = '-excluded-surface-diagnostic' if exclusion else '-albedo-diagnostic'
    scene.render.filepath=str(output/(folder.name+suffix+'.png'))
    bpy.ops.render.render(write_still=True)
    (output/(folder.name+suffix+'-materials.json')).write_text(json.dumps(dict(
        warning='Albedo-only diagnostic. Dye, normal, emission, alpha and attachment alignment unverified.',
        excludedMeshPattern=exclusion, excludedMeshes=excluded, materials=mapping),indent=2)+'\n')


if __name__ == '__main__':
    source, output = map(Path, sys.argv[sys.argv.index('--')+1:])
    for tag in ('80C3EE92','80CC0740'):
        preview(source/('skiff__'+tag),output)
