import bpy,importlib.util,json,hashlib,shutil
from pathlib import Path
out=Path('/tmp/devils-source-alpha');bpy.ops.wm.open_mainfile(filepath='/tmp/devils-drive-marauder-dual/evaluated-qa.blend');scene=bpy.context.scene;scene.cycles.samples=1
obj=next(o for o in scene.objects if o.type=='MESH' and o.data.uv_layers.get('shader_bake'))
for o in bpy.context.selected_objects:o.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
spec=importlib.util.spec_from_file_location('coverage',Path.cwd()/'scripts/strikes/bake_shader_coverage.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
shutil.copy2(out/'dl_marauder.bbmodel',out/'before-add-dl_marauder.bbmodel');meta=mod.bake_coverage(obj,scene,out)
d=json.loads((out/'shader-bake.json').read_text());d.update(coverage_sha256=hashlib.sha256((out/'opacity.npz').read_bytes()).hexdigest(),coverage_method=meta['method']);(out/'shader-bake.json').write_text(json.dumps(d,indent=2))
