import bpy,json,importlib.util,numpy as np
from pathlib import Path
out=Path('/tmp/devils-add-alpha');out.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('coverage',Path.cwd()/'scripts/strikes/bake_shader_coverage.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
checks=[]
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.film_transparent=True;scene.render.resolution_x=32;scene.render.resolution_y=32;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
bpy.ops.mesh.primitive_plane_add(size=2);obj=bpy.context.object;obj.data.uv_layers.active.name='shader_bake'
bpy.ops.object.camera_add(location=(0,0,3));scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=2
m=bpy.data.materials.new('control');m.use_nodes=True;obj.data.materials.append(m)
for case in ['add_transparent_emission','mix_half','add_two_halves','add_two_opaque']:
 t=m.node_tree;t.nodes.clear();output=t.nodes.new('ShaderNodeOutputMaterial');trans=t.nodes.new('ShaderNodeBsdfTransparent');emit=t.nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(1,1,1,1)
 half=t.nodes.new('ShaderNodeMixShader');half.inputs[0].default_value=.5;t.links.new(trans.outputs[0],half.inputs[1]);t.links.new(emit.outputs[0],half.inputs[2])
 if case=='mix_half':result=half.outputs[0]
 else:
  add=t.nodes.new('ShaderNodeAddShader');left,right=(trans.outputs[0],emit.outputs[0]) if case=='add_transparent_emission' else (half.outputs[0],half.outputs[0]) if case=='add_two_halves' else (emit.outputs[0],emit.outputs[0]);t.links.new(left,add.inputs[0]);t.links.new(right,add.inputs[1]);result=add.outputs[0]
 t.links.new(result,output.inputs['Surface']);scene.render.filepath=str(out/(case+'.png'));bpy.ops.render.render(write_still=True)

 for o in bpy.context.selected_objects:o.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj
 target=out/case;target.mkdir(exist_ok=True);mod.bake_coverage(obj,scene,target,size=32)
 reference=bpy.data.images.load(scene.render.filepath,check_existing=False);alpha=reference.pixels[(16*32+16)*4+3];coverage=float(np.load(target/'opacity.npz')['coverage'][16,16]);bpy.data.images.remove(reference)
 assert abs(alpha-coverage)<1/255+1e-6,(case,alpha,coverage)
 checks.append(dict(case=case,renderedAlpha=alpha,bakedCoverage=coverage))
(out/'control-check.json').write_text(json.dumps(checks,indent=2));print('COVERAGE CONTROL PASSED',flush=True)
