import bpy,json,numpy as np
from pathlib import Path
rig=max((o for o in bpy.data.objects if o.type=='ARMATURE'),key=lambda o:len(o.data.bones))
native=np.load('/tmp/devils-models-evidence/marauder_mesh.npz');basis=np.diag([-1.,-1.,1.,1.]);rows=[];used=set()
for obj in bpy.data.objects:
 if obj.type!='MESH' or not obj.data.materials or not obj.vertex_groups or obj.hide_render or not obj.visible_get():continue
 print('VISIBLE',obj.name,[m.name for m in obj.data.materials],obj.parent.name if obj.parent else None)
 for v in obj.data.vertices:
  if v.groups:used.add(obj.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name)
for name in sorted(used):
 if name not in rig.pose.bones:rows.append({'name':name,'missing_in_main_rig':True});continue
 matrix=basis@np.array(rig.matrix_world@rig.pose.bones[name].matrix);dist=np.linalg.norm(native['rest'][:,:3,3]-matrix[:3,3],axis=1);order=np.argsort(dist)[:3]
 rows.append({'name':name,'parent':rig.data.bones[name].parent.name if rig.data.bones[name].parent else None,'candidates':[{'hash':str(native['names'][j]),'error':float(dist[j])} for j in order]})
Path('/tmp/devils-marauder-rig-audit.json').write_text(json.dumps(rows,indent=2));print('USED',len(used))
