"""Headless diagnostic: reduce the read-only evaluated Marauder shader surface, no product output."""
import bpy, numpy as np, sys, json
from pathlib import Path
source=Path('/tmp/devils-drive-marauder-dual/marauder_mesh.npz')
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
d=np.load(source);bpy.ops.wm.read_factory_settings(use_empty=True)
# Weld only coincident coordinates; UV remains per loop. One mesh per source bone
# prevents reduction across articulated parts (static diagnostic, no new rig).
Vs=[];UVs=[];Bs=[];audit=[]
for bone in np.unique(d['BONE']):
 mask=d['BONE']==bone;verts=d['V'][mask];uvs=d['UV'][mask]
 key=verts.reshape(-1,3)
 if '--uv-seams' in sys.argv:key=np.concatenate([key,uvs.reshape(-1,2)],axis=1)
 unique,indices=np.unique(np.round(key,8),axis=0,return_inverse=True)
 unique=unique[:,:3]
 mesh=bpy.data.meshes.new(str(bone));mesh.from_pydata(unique.tolist(),[],indices.reshape(-1,3).tolist());mesh.update()
 uv=mesh.uv_layers.new();uv.data.foreach_set('uv',uvs.reshape(-1))
 obj=bpy.data.objects.new(str(bone),mesh);bpy.context.collection.objects.link(obj)
 mod=obj.modifiers.new('diagnostic reduction','DECIMATE');mod.ratio=.075;mod.use_collapse_triangulate=True
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 for tri in me.loop_triangles:
  Vs.append([list(me.vertices[i].co) for i in tri.vertices]);UVs.append([list(me.uv_layers.active.data[i].uv) for i in tri.loops]);Bs.append(str(bone))
 audit.append(dict(bone=str(bone),source=int(mask.sum()),reduced=len(me.loop_triangles)))
 ev.to_mesh_clear();bpy.data.objects.remove(obj,do_unlink=True)
np.savez(out/'surface.npz',V=np.array(Vs),UV=np.array(UVs),BONE=np.array(Bs))
(out/'reduction.json').write_text(json.dumps(audit,indent=2)+'\n')
print('Source',len(d['V']),'reduced',len(Vs))
