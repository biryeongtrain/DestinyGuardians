"""Bake evaluated source shader coverage into the existing UV atlas. Isolated diagnostic."""
import bpy,numpy as np,json
from pathlib import Path
out=Path('/tmp/devils-source-alpha');out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath='/tmp/devils-drive-marauder-dual/evaluated-qa.blend')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
objects=[o for o in scene.objects if o.type=='MESH' and o.data.uv_layers.get('shader_bake')]
assert len(objects)==1,len(objects)
obj=objects[0]
for o in bpy.context.selected_objects:o.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
im=bpy.data.images.new('diagnostic_opacity',width=4096,height=4096,alpha=False,float_buffer=True);im.colorspace_settings.name='Non-Color'
report=[];memo={};group_ports={}
def const(t,v):
 n=t.nodes.new('ShaderNodeValue');n.outputs[0].default_value=v;return n.outputs[0]
def mathop(t,op,*sockets):
 n=t.nodes.new('ShaderNodeMath');n.operation=op
 for i,s in enumerate(sockets):t.links.new(s,n.inputs[i])
 return n.outputs[0]
def value(t,s):return s.links[0].from_socket if s.is_linked else const(t,s.default_value)
def coverage(t,s):
 if not s.is_linked:return const(t,0)
 source=s.links[0].from_socket;n=source.node;key=(t.as_pointer(),n.as_pointer(),source.identifier)
 if key in memo:return memo[key]
 if n.type=='BSDF_TRANSPARENT':r=const(t,0)
 elif n.type=='BSDF_PRINCIPLED':r=value(t,n.inputs['Alpha'])
 elif n.type=='EMISSION' or n.type.startswith('BSDF_'):r=const(t,1)
 elif n.type=='MIX_SHADER':
  fac=value(t,n.inputs[0]);left=coverage(t,n.inputs[1]);right=coverage(t,n.inputs[2])
  r=mathop(t,'ADD',mathop(t,'MULTIPLY',mathop(t,'SUBTRACT',const(t,1),fac),left),mathop(t,'MULTIPLY',fac,right))
 elif n.type=='ADD_SHADER':r=mathop(t,'MAXIMUM',coverage(t,n.inputs[0]),coverage(t,n.inputs[1]))
 elif n.type=='GROUP':
  inner=n.node_tree;gkey=(inner.as_pointer(),source.identifier)
  if gkey not in group_ports:
   output=next(o for o in inner.nodes if o.type=='GROUP_OUTPUT' and o.is_active_output)
   original=next(i for i in output.inputs if i.identifier==source.identifier)
   scalar=coverage(inner,original)
   port=inner.interface.new_socket(name='QA opacity '+source.identifier,in_out='OUTPUT',socket_type='NodeSocketFloat')
   inner.links.new(scalar,next(i for i in output.inputs if i.identifier==port.identifier));group_ports[gkey]=port.identifier
  r=next(o for o in n.outputs if o.identifier==group_ports[gkey])
 else:raise ValueError('Unsupported surface closure '+t.name+' '+n.type)
 memo[key]=r;return r
for mat in obj.data.materials:
 tree=mat.node_tree
 output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
 opacity=coverage(tree,output.inputs['Surface']);emit=tree.nodes.new('ShaderNodeEmission');tree.links.new(opacity,emit.inputs['Color']);tree.links.new(emit.outputs[0],output.inputs['Surface'])
 target=tree.nodes.new('ShaderNodeTexImage');target.image=im;tree.nodes.active=target
 report.append(dict(material=mat.name))
scene.render.bake.use_clear=True;scene.render.bake.margin=3
bpy.ops.object.bake(type='EMIT',uv_layer='shader_bake')
pix=np.empty(4096*4096*4,dtype=np.float32);im.pixels.foreach_get(pix)
alpha=pix.reshape(4096,4096,4)[::-1,:,0].copy();np.save(out/'opacity.npy',alpha)
(out/'opacity-bake.json').write_text(json.dumps(dict(materials=report,minimum=float(alpha.min()),maximum=float(alpha.max()),underHalf=int((alpha<.5).sum()),method='shader closure coverage evaluated through emission; linear float pixels; unchanged source UV atlas'),indent=2))
print('OPACITY BAKED',float(alpha.min()),float(alpha.max()),flush=True)
