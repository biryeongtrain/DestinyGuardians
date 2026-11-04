import bpy,sys,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path.cwd();sys.path.insert(0,str(root/'scripts/mesh'))
from native_triangle_elements_w115 import rotate
helper=root/'docs/qa/2026-11-03/devils-lair/models/surface-study/render-culled.py'
ns={};code=helper.read_text();exec(code[:code.index('for name in sys.argv')],ns)
out=Path(os.environ.get('DEVILS_TRIANGLE_DIR','/tmp/devils-triangle-study'));cache=Path('/tmp/devils-drive-marauder-dual')
bpy.ops.wm.read_factory_settings(use_empty=True)
model=json.loads((out/'native-model.json').read_text());vs=[];uvs=[];mats=[]
for e in model['elements']:
 lo=np.array(e['from']);hi=np.array(e['to']);rotation=e['rotation'];origin=np.array(rotation['origin']);angles=[rotation[k] for k in ['x','y','z']]
 points=[]
 for x,y in [(0,0),(1,0),(1,1),(0,1)]:
  p=np.array([hi[0] if x else lo[0],hi[1] if y else lo[1],lo[2]])
  p=origin+np.array(rotate(p-origin,angles));p=(p-8)/.5
  points.append([p[0]/16,-p[2]/16,p[1]/16])
 a,b,c,d=np.array(e['faces']['south']['uv'])/16
 tex=[(a,1-d),(c,1-d),(c,1-b),(a,1-b)]
 for inds in [(0,1,2),(0,2,3)]:
  vs.extend(points[i] for i in inds);uvs.extend(tex[i] for i in inds);mats.append(0)
if '--reduced' in sys.argv:
 d=np.load(out/'surface.npz');stats=json.loads((cache/'marauder_stats.json').read_text());v=d['V'].reshape(-1,3)
 vs=np.stack([v[:,0]*stats['k'],v[:,1]*stats['k'],v[:,2]*stats['k']+stats['y0']],axis=1)/16
 ns['mesh'](vs,d['UV'],np.zeros(len(d['V']),int),[ns['material'](cache/'combined.png')])
else:ns['mesh'](vs,uvs,mats,[ns['material'](out/'atlas.png')])
stats=json.loads((cache/'marauder_stats.json').read_text());v=np.load(cache/'marauder_mesh.npz')['V'].reshape(-1,3)
ref=np.stack([v[:,0]*stats['k'],v[:,1]*stats['k'],v[:,2]*stats['k']+stats['y0']],axis=1)/16
cen,height,cam=ns['setup'](ref)
for label,angle in [('front',0),('side',90),('threequarter',35)]:
 a=math.radians(angle);cam.location=cen+Vector((math.sin(a)*height*2,math.cos(a)*height*2,height*.12));cam.rotation_euler=(Vector(cen)-cam.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.scene.render.filepath=str(out/((('reduced-' if '--reduced' in sys.argv else '')+label)+'.png'));bpy.ops.render.render(write_still=True)
