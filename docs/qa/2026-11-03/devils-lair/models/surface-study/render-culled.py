import bpy, json, math, sys, base64, io, os
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path('/tmp/devils-drive-marauder-dual')
MODELROOT=Path(os.environ.get('DEVILS_RENDER_MODELS',str(P)))
PREFIX=os.environ.get('DEVILS_RENDER_PREFIX','')
FAC={'north':(2,0,1,-1,-1),'south':(2,0,1,1,-1),'east':(0,2,1,-1,-1),'west':(0,2,1,1,-1),'up':(1,0,2,1,1),'down':(1,0,2,1,-1)}

def material(path):
 m=bpy.data.materials.new(str(path));m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial'); tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True) if str(path) else bpy.data.images.new('unmapped',1,1);tex.interpolation='Closest'
 bs=n.new('ShaderNodeEmission');tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
 m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Color']);m.node_tree.links.new(tex.outputs['Alpha'],mix.inputs[0]);m.node_tree.links.new(tr.outputs[0],mix.inputs[1]);m.node_tree.links.new(bs.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],out.inputs[0]);
 if 'render_atlas' in str(path):
  geo=n.new('ShaderNodeNewGeometry');cull=n.new('ShaderNodeMixShader');m.node_tree.links.new(geo.outputs['Backfacing'],cull.inputs[0]);m.node_tree.links.new(mix.outputs[0],cull.inputs[1]);m.node_tree.links.new(tr.outputs[0],cull.inputs[2]);m.node_tree.links.new(cull.outputs[0],out.inputs[0])
 return m

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

def render(name,mode):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 model=json.loads((MODELROOT/('dl_'+name+'.bbmodel')).read_text()); stats=json.loads((P/(name+'_stats.json')).read_text());k=stats['k'];y0=stats['y0'];scale=1/16
 if mode=='source':
  d=np.load(P/(name+'_mesh.npz')); v=d['V'].reshape(-1,3);V=np.stack([v[:,0]*k,v[:,1]*k,v[:,2]*k+y0],1)*scale
  uv=d['UV'];m=d['MAT']; materials=[material(p) for p in d['mat_tex']]
 else:
  atlas=P/(PREFIX+name+'_render_atlas.png');atlas.write_bytes(base64.b64decode(model['textures'][0]['source'].split(',')[1]));materials=[material(atlas)];vs=[];us=[];m=[]
  for e in model['elements']:
   for face,f in e['faces'].items():
    if f['texture'] is None:continue
    da,ua,va,sgnu,sgnv=FAC[face];low,high=np.array(e['from']),np.array(e['to']);p=[]
    for u,v in [(0,0),(1,0),(1,1),(0,1)]:
     q=low.copy();q[ua]=(high if u else low)[ua];q[va]=(high if v else low)[va];p.append(q)
    x0,y1,x1,y0uv=f['uv'];u0,u1=x0/2048,x1/2048;v0,v1=1-y1/2048,1-y0uv/2048
    uvp=[[(u0 if u==0 else u1) if sgnu>0 else (u1 if u==0 else u0),(v1 if v==0 else v0) if sgnv<0 else (v0 if v==0 else v1)] for u,v in [(0,0),(1,0),(1,1),(0,1)]]
    normal=np.cross(p[1]-p[0],p[2]-p[0]);sign=-1 if face in ('north','west','down') else 1
    indices=[(0,1,2),(0,2,3)] if normal[da]*sign>0 else [(0,2,1),(0,3,2)]
    for ids in indices:
     vs.extend([p[i] for i in ids]);us.extend([uvp[i] for i in ids]);m.append(0)
  v=np.array(vs);V=np.stack([v[:,0],-v[:,2],v[:,1]],1)*scale;uv=np.array(us)
 mesh(V,uv,m,materials)
 ref=np.load(P/(name+'_mesh.npz'))['V'].reshape(-1,3);ref=np.stack([ref[:,0]*k,ref[:,1]*k,ref[:,2]*k+y0],1)*scale;cen,h,cam=setup(ref)
 for label,angle in [('front',0),('side',90),('threequarter',35)]:
  a=math.radians(angle);cam.location=cen+Vector((math.sin(a)*h*2,math.cos(a)*h*2,h*.12));cam.rotation_euler=(Vector(cen)-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.render.filepath=str(P/(PREFIX+name+'_'+mode+'_'+label+'.png'));bpy.ops.render.render(write_still=True)
for name in sys.argv[sys.argv.index('--')+1:]:
 for mode in ['baked']:render(name,mode)
