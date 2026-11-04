import bpy,importlib.util,json,hashlib,numpy as np
from pathlib import Path
out=Path('/tmp/devils-source-alpha');bpy.ops.wm.open_mainfile(filepath='/tmp/devils-drive-marauder-dual/evaluated-qa.blend');scene=bpy.context.scene;scene.cycles.samples=1
obj=next(o for o in scene.objects if o.type=='MESH' and o.data.uv_layers.get('shader_bake'))
for o in bpy.context.selected_objects:o.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
spec=importlib.util.spec_from_file_location('coverage',Path.cwd()/'scripts/strikes/bake_shader_coverage.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def graphs():
 return [(t.name,tuple(sorted(n.name for n in t.nodes)),tuple(sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links))) for t in list(bpy.data.node_groups)+[m.node_tree for m in bpy.data.materials if m.use_nodes]]
before=graphs();mod.bake_coverage(obj,scene,out);assert before==graphs(),'Shader graph was not restored'
a=np.load(out/'opacity.npz')['coverage'];b=np.load(out/'opacity.npy');assert np.array_equal(a,b),'Reusable helper differs from independent prototype'
meta=json.loads((out/'shader-bake.json').read_text());meta.update(pipeline_version=5,coverage_file='opacity.npz',coverage_sha256=hashlib.sha256((out/'opacity.npz').read_bytes()).hexdigest());(out/'shader-bake.json').write_text(json.dumps(meta,indent=2));(out/'helper-check.json').write_text(json.dumps(dict(graphRestored=True,prototypePixelsIdentical=True)))
print('HELPER CHECK PASSED')
