import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Matrix,Vector
cache=Path('/tmp/devils-drive-marauder-dual');out=Path('/tmp/devils-source-alpha');helper=Path.cwd()/'docs/qa/2026-11-03/devils-lair/models/surface-study/render-culled.py';ns={};s=helper.read_text();exec(s[:s.index('for name in sys.argv')],ns)
bpy.ops.wm.open_mainfile(filepath=str(cache/'evaluated-qa.blend'))
st=json.loads((cache/'marauder_stats.json').read_text());k=st['k']/16;offset=st['y0']/16
M=Matrix(((-k,0,0,0),(0,-k,0,0),(0,0,k,offset),(0,0,0,1)))
lights=set()
for obj in bpy.context.scene.objects:
 if obj.type in ('MESH','LIGHT'):
  obj.matrix_world=M@obj.matrix_world
  if obj.type=='LIGHT':lights.add(obj.name)
v=np.load(cache/'marauder_mesh.npz')['V'].reshape(-1,3);ref=v*k;ref[:,2]+=offset
cen,h,cam=ns['setup'](ref)
# Preserve the source bake's authored lights rather than adding the comparison renderer's lamps.
for obj in list(bpy.context.scene.objects):
 if obj.type=='LIGHT' and obj.name not in lights:bpy.data.objects.remove(obj,do_unlink=True)
bpy.context.scene.cycles.samples=32
for label,angle in [('front',0),('threequarter',35)]:
 a=math.radians(angle);cam.location=cen+Vector((math.sin(a)*h*2,math.cos(a)*h*2,h*.12));cam.rotation_euler=(Vector(cen)-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.render.filepath=str(out/('original-shader-'+label+'.png'));bpy.ops.render.render(write_still=True)
