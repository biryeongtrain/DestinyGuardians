import bpy,json,pathlib,hashlib
from mathutils import Vector
root=pathlib.Path('/Users/qf/IdeaProjects/DestinyGuardians');meta=json.loads((root/'art/blockbench/weapons/w30/first_in_last_out.bbmodel').read_text())['destiny_w30']
meshes=[]
for name in meta['source_objects']:
 obj=bpy.data.objects.get(name)
 if obj is None:raise RuntimeError('Missing source object: '+name)
 m=obj.data;m.calc_loop_triangles();uv=m.uv_layers.active
 vs=[list(obj.matrix_world@v.co) for v in m.vertices]
 meshes.append(dict(name=name,vertices=vs,faces=[list(t.vertices) for t in m.loop_triangles],uv=[[[uv.data[i].uv.x,1-uv.data[i].uv.y] for i in t.loops] for t in m.loop_triangles],material=[obj.material_slots[t.material_index].name if t.material_index<len(obj.material_slots) else '' for t in m.loop_triangles]))
p=pathlib.Path('/private/tmp/destiny-w133-reference');p.mkdir(exist_ok=True);(p/'first_in_last_out-meshes.json').write_text(json.dumps(meshes,separators=(',',':'),allow_nan=False)+'\n')
print('OWNED_READONLY_EXTRACT',[(m['name'],len(m['faces'])) for m in meshes]);print('TOTAL',sum(len(m['faces']) for m in meshes))
