"""Offline static skiff projection preview; not Minecraft validation.
Usage: Blender --background --factory-startup --python-exit-code 1 --python script -- CANDIDATE_DIR BAKE_DIR
"""
import bpy, json, math, sys, base64, io, os
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(sys.argv[sys.argv.index('--')+1]); P.mkdir(parents=True,exist_ok=True)
MODELROOT=Path(os.environ.get('DEVILS_RENDER_MODELS',str(P)))
PREFIX=os.environ.get('DEVILS_RENDER_PREFIX','')
CLIP=os.environ.get('DEVILS_RENDER_CLIP','')
TIME=float(os.environ.get('DEVILS_RENDER_TIME','0'))
FAC={'north':(2,0,1,-1,-1),'south':(2,0,1,1,-1),'east':(0,2,1,-1,-1),'west':(0,2,1,1,-1),'up':(1,0,2,1,1),'down':(1,0,2,1,-1)}

def material(path):
 m=bpy.data.materials.new(str(path));m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial'); tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True) if str(path) else bpy.data.images.new('unmapped',1,1);tex.interpolation='Closest'
 bs=n.new('ShaderNodeEmission');tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
 m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Color']);m.node_tree.links.new(tex.outputs['Alpha'],mix.inputs[0]);m.node_tree.links.new(tr.outputs[0],mix.inputs[1]);m.node_tree.links.new(bs.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],out.inputs[0]);return m

def mesh(V,UV,M,mats):
 me=bpy.data.meshes.new('geometry');me.from_pydata(V,[],[list(range(i*3,i*3+3)) for i in range(len(M))]);me.update();o=bpy.data.objects.new('model',me);bpy.context.collection.objects.link(o)
 for m in mats:me.materials.append(m)
 uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.asarray(UV).reshape(-1))
 for p,mi in zip(me.polygons,M):p.material_index=int(mi)
 return o

def setup(vertices):
 lo,hi=vertices.min(0),vertices.max(0); cen=(lo+hi)/2; height=max(hi-lo)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.transparent_max_bounces=128
 scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('studio');scene.world.color=(.16,.16,.16);scene.view_settings.view_transform='Standard'
 scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
 for loc,power,size in [((4,-6,8),900,5),((-4,-2,5),600,4),((2,5,7),1000,3)]:
  bpy.ops.object.light_add(type='AREA',location=cen+np.array(loc)*height/4);l=bpy.context.object;l.data.energy=power*(height/4)**2;l.data.shape='DISK';l.data.size=size*height/4;l.rotation_euler=(Vector(cen)-l.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=height*1.22
 return cen,height,cam


bpy.ops.wm.read_factory_settings(use_empty=True)
model=json.loads((P/'dl_skiff_candidate.bbmodel').read_text());scale=1/16
transforms={}
if CLIP:
 sys.path.insert(0,str(Path(__file__).resolve().parent))
 from retarget_skiff_motion import euler_matrix
 animation=next(a for a in model['animations'] if a['name']==CLIP)
 def channel(animator,name,default):
  keys=sorted([k for k in animator.get('keyframes',[]) if k['channel']==name],key=lambda k:k['time'])
  if not keys:return np.array(default,float)
  def value(k):return np.array([float(k['data_points'][0][axis]) for axis in 'xyz'])
  if TIME<=keys[0]['time']:return value(keys[0])
  for a,b in zip(keys,keys[1:]):
   if a['time']<=TIME<=b['time']:
    if a['interpolation']!='linear':raise ValueError('Preview supports only linear keys')
    t=(TIME-a['time'])/(b['time']-a['time']);return value(a)*(1-t)+value(b)*t
  return value(keys[-1])
 def posed(nodes,parent_origin=np.zeros(3),parent_position=np.zeros(3),parent_rotation=np.eye(3)):
  for node in nodes:
   if isinstance(node,str):
    transforms[node]=(parent_origin,parent_position,parent_rotation);continue
   origin=np.array(node['origin'],float)
   animator=animation['animators'].get(node['uuid'],{})
   if np.max(abs(channel(animator,'scale',[1,1,1])-1))>1e-8:raise ValueError('Scaled animation unsupported')
   position=parent_position+parent_rotation@(origin-parent_origin+channel(animator,'position',[0,0,0]))
   rotation=parent_rotation@euler_matrix(np.deg2rad(channel(animator,'rotation',[0,0,0]))[None])[0]
   posed(node['children'],origin,position,rotation)
 posed(model['outliner'])
texture_width=model['resolution']['width'];texture_height=model['resolution']['height']
if any(any(float(v)!=0 for v in e.get('rotation',[0,0,0])) for e in model['elements']):
 raise ValueError('Renderer requires axis-aligned elements')
materials=[]
for index,texture in enumerate(model['textures']):
 atlas=P/f'render-atlas-{index}.png';atlas.write_bytes(base64.b64decode(texture['source'].split(',')[1]));materials.append(material(atlas))
vs=[];us=[];m=[]
for e in model['elements']:
 for face,f in e['faces'].items():
  if f['texture'] is None:continue
  texture=model['textures'][int(f['texture'])]
  texture_width=texture.get('uv_width',texture['width']);texture_height=texture.get('uv_height',texture['height'])
  da,ua,va,sgnu,sgnv=FAC[face];low,high=np.array(e['from']),np.array(e['to']);p=[]
  for u,v in [(0,0),(1,0),(1,1),(0,1)]:
   q=low.copy();q[ua]=(high if u else low)[ua];q[va]=(high if v else low)[va];p.append(q)
  if CLIP:
   origin,position,rotation=transforms[e['uuid']];p=[position+rotation@(q-origin) for q in p]
  x0,y1,x1,y0uv=f['uv'];u0,u1=x0/texture_width,x1/texture_width;v0,v1=1-y1/texture_height,1-y0uv/texture_height
  uvp=[[(u0 if u==0 else u1) if sgnu>0 else (u1 if u==0 else u0),(v1 if v==0 else v0) if sgnv<0 else (v0 if v==0 else v1)] for u,v in [(0,0),(1,0),(1,1),(0,1)]]
  for ids in [(0,1,2),(0,2,3)]:
   vs.extend([p[i] for i in ids]);us.extend([uvp[i] for i in ids]);m.append(int(f['texture']))
v=np.array(vs);V=np.stack([v[:,0],-v[:,2],v[:,1]],1)*scale;uv=np.array(us)
mesh(V,uv,m,materials)
ref=np.load(Path(sys.argv[sys.argv.index('--')+2])/'shader_mesh.npz')['V'].reshape(-1,3)
cen,h,cam=setup(ref)
bpy.context.scene.render.resolution_x=1200;bpy.context.scene.render.resolution_y=900
cam.data.ortho_scale=h*1.15
for label,offset in [('threequarter',(-.9,1.3,.65)),('side',(-1,0,.1)),('below',(-.9,1.3,-.65))]:
 cam.location=Vector(cen)+Vector(offset)*h;cam.rotation_euler=(Vector(cen)-cam.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.scene.render.filepath=str(P/(PREFIX+'candidate-'+label+'.png'));bpy.ops.render.render(write_still=True)
