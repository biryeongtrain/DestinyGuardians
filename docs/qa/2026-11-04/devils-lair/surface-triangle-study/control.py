"""Compare unchanged source and reduced geometry with textured/solid materials."""
import bpy, numpy as np, json, math
from pathlib import Path
from mathutils import Vector
root=Path.cwd();cache=Path('/tmp/devils-drive-marauder-dual');out=Path('/tmp/devils-surface-controls');out.mkdir(exist_ok=True)
helper=root/'docs/qa/2026-11-03/devils-lair/models/surface-study/render-culled.py'
ns={};code=helper.read_text();exec(code[:code.index('for name in sys.argv')],ns)
stats=json.loads((cache/'marauder_stats.json').read_text())
def coords(v):
 v=v.reshape(-1,3);return np.stack([v[:,0]*stats['k'],v[:,1]*stats['k'],v[:,2]*stats['k']+stats['y0']],axis=1)/16
ref=coords(np.load(cache/'marauder_mesh.npz')['V'])
for label,path in [('source',cache/'marauder_mesh.npz'),('reduced',Path('/tmp/devils-triangle-study/surface.npz'))]:
 d=np.load(path)
 for mode in ['textured','solid']:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  mat=ns['material'](cache/'combined.png')
  if mode=='solid':
   nodes=mat.node_tree.nodes;nodes.clear();bs=nodes.new('ShaderNodeBsdfDiffuse');bs.inputs['Color'].default_value=(.6,.6,.6,1);o=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],o.inputs[0])
  ns['mesh'](coords(d['V']),d['UV'],np.zeros(len(d['V']),int),[mat])
  cen,h,cam=ns['setup'](ref);a=math.radians(35);cam.location=cen+Vector((math.sin(a)*h*2,math.cos(a)*h*2,h*.12));cam.rotation_euler=(Vector(cen)-cam.location).to_track_quat('-Z','Y').to_euler()
  bpy.context.scene.render.filepath=str(out/(label+'-'+mode+'.png'));bpy.ops.render.render(write_still=True)
