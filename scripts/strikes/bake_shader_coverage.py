"""Explicit source shader coverage bake for Dreg-Light caches (Blender only).

Combined RGB radiance is not opacity. Preserve original colour/emission files and
write linear scalar coverage separately. Unsupported shader closures fail visibly.
All mutation is limited to the caller's temporary evaluated scene and restored.
"""
from pathlib import Path
import json


def bake_coverage(obj, scene, out, size=4096):
 import bpy
 import numpy as np
 out=Path(out)
 im=bpy.data.images.new('source_coverage',width=size,height=size,alpha=False,float_buffer=True)
 im.colorspace_settings.name='Non-Color'
 originals=[]
 report=[];memo={};group_ports={};trees={};ports=[]
 def remember(t):
  if t.as_pointer() not in trees:trees[t.as_pointer()]=(t,set(n.as_pointer() for n in t.nodes))
 def const(t,v):
  remember(t);n=t.nodes.new('ShaderNodeValue');n.outputs[0].default_value=v;return n.outputs[0]
 def mathop(t,op,*sockets):
  remember(t);n=t.nodes.new('ShaderNodeMath');n.operation=op
  for i,s in enumerate(sockets):t.links.new(s,n.inputs[i])
  return n.outputs[0]
 def value(t,s):return s.links[0].from_socket if s.is_linked else const(t,s.default_value)
 def coverage(t,s):
  if not s.is_linked:return const(t,0)
  source=s.links[0].from_socket;n=source.node;key=(t.as_pointer(),n.as_pointer(),source.identifier)
  if key in memo:return memo[key]
  # Blender converts numeric/colour Surface links to opaque emission closures.
  if source.type in ('RGBA','VALUE','VECTOR'):r=const(t,1)
  elif n.type=='BSDF_TRANSPARENT':r=const(t,0)
  elif n.type=='BSDF_PRINCIPLED':r=value(t,n.inputs['Alpha'])
  elif n.type=='EMISSION' or n.type.startswith('BSDF_'):r=const(t,1)
  elif n.type=='MIX_SHADER':
   fac=value(t,n.inputs[0]);left=coverage(t,n.inputs[1]);right=coverage(t,n.inputs[2])
   r=mathop(t,'ADD',mathop(t,'MULTIPLY',mathop(t,'SUBTRACT',const(t,1),fac),left),mathop(t,'MULTIPLY',fac,right))
  elif n.type=='ADD_SHADER':
   # Closures add transmittance. A transparent + emission overlay stays transparent.
   total=mathop(t,'ADD',coverage(t,n.inputs[0]),coverage(t,n.inputs[1]))
   r=mathop(t,'MAXIMUM',const(t,0),mathop(t,'SUBTRACT',total,const(t,1)))
  elif n.type=='GROUP':
   inner=n.node_tree;gkey=(inner.as_pointer(),source.identifier)
   if gkey not in group_ports:
    output=next(o for o in inner.nodes if o.type=='GROUP_OUTPUT' and o.is_active_output)
    original=next(i for i in output.inputs if i.identifier==source.identifier)
    scalar=coverage(inner,original)
    port=inner.interface.new_socket(name='QA opacity '+source.identifier,in_out='OUTPUT',socket_type='NodeSocketFloat')
    ports.append((inner,port))
    inner.links.new(scalar,next(i for i in output.inputs if i.identifier==port.identifier));group_ports[gkey]=port.identifier
   r=next(o for o in n.outputs if o.identifier==group_ports[gkey])
  else:raise ValueError('Unsupported surface closure '+t.name+' '+n.type)
  memo[key]=r;return r
 try:
  for mat in obj.data.materials:
   tree=mat.node_tree;remember(tree)
   output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
   originals.append((tree,output,output.inputs['Surface'].links[0].from_socket if output.inputs['Surface'].is_linked else None,tree.nodes.active))
   opacity=coverage(tree,output.inputs['Surface']);emit=tree.nodes.new('ShaderNodeEmission');tree.links.new(opacity,emit.inputs['Color']);tree.links.new(emit.outputs[0],output.inputs['Surface'])
   target=tree.nodes.new('ShaderNodeTexImage');target.image=im;tree.nodes.active=target
   report.append(dict(material=mat.name))
  scene.render.bake.use_clear=True;scene.render.bake.margin=3
  bpy.ops.object.bake(type='EMIT',uv_layer='shader_bake')
  pix=np.empty(size*size*4,dtype=np.float32);im.pixels.foreach_get(pix)
  alpha=pix.reshape(size,size,4)[::-1,:,0].copy();np.savez_compressed(out/'opacity.npz',coverage=alpha)
  result=dict(materials=report,minimum=float(alpha.min()),maximum=float(alpha.max()),underHalf=int((alpha<.5).sum()),method='shader closure coverage; Mix Shader interpolation, Principled alpha, transparent zero, opaque and emission one, Add Shader clamped additive transmittance; pure emission cutout remains separate')
  (out/'opacity-bake.json').write_text(json.dumps(result,indent=2))
  return result
 finally:
  for tree,output,socket,active in originals:
   if socket:tree.links.new(socket,output.inputs['Surface'])
   else:
    for link in list(output.inputs['Surface'].links):tree.links.remove(link)
   tree.nodes.active=active
  for tree,existing in trees.values():
   for node in list(tree.nodes):
    if node.as_pointer() not in existing:tree.nodes.remove(node)
  for tree,port in reversed(ports):tree.interface.remove(port)
  bpy.data.images.remove(im)
