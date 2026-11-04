import bpy,numpy as np,json,importlib.util,hashlib
from pathlib import Path
root=Path.cwd();base=Path('/tmp/devils-drive-models');out=Path('/tmp/devils-coverage-audit');out.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('coverage',root/'scripts/strikes/bake_shader_coverage.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
rows=[]
for name in ['acolyte','knight','wizard','servitor','brig','sepiks']:
 p=base/name;target=out/name;target.mkdir(exist_ok=True)
 try:
  bpy.ops.wm.open_mainfile(filepath=str(p/'evaluated-qa.blend'));scene=bpy.context.scene;scene.cycles.samples=1
  objects=[o for o in scene.objects if o.type=='MESH' and o.data.uv_layers.get('shader_bake')];assert len(objects)==1,(name,len(objects));obj=objects[0]
  for o in bpy.context.selected_objects:o.select_set(False)
  obj.select_set(True);bpy.context.view_layer.objects.active=obj
  meta=mod.bake_coverage(obj,scene,target)
  d=np.load(p/'shader_mesh.npz');uv=d['UV'].mean(1);mask=np.load(target/'opacity.npz')['coverage'];h,w=mask.shape
  x=np.clip((uv[:,0]*w).astype(int),0,w-1);y=np.clip(((1-uv[:,1])*h).astype(int),0,h-1);values=mask[y,x]
  source=json.loads((p/'shader-bake.json').read_text());pure=np.isin(d['MAT'],[i for i,m in enumerate(d['mats']) if m in source.get('pure_emission_materials',[])])
  row=dict(name=name,triangles=len(values),transparentCentres=int((values<.5).sum()),ordinaryTransparentCentres=int(((values<.5)&~pure).sum()),maskSha256=hashlib.sha256((target/'opacity.npz').read_bytes()).hexdigest(),materials=meta['materials'])
 except Exception as e:
  row=dict(name=name,error=repr(e))
 rows.append(row);(out/'audit.json').write_text(json.dumps(rows,indent=2));print('AUDIT',json.dumps(row),flush=True)
