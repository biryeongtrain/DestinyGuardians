#!/usr/bin/env python3
"""W118 BF R5: opaque primary cuboids and source-plane neck patches.

Design is the editable, pinned source-derived product: component/skin ledger,
source-triangle history, native cuboids and authored clean component materials.
Normal generation and --verify are pure Python, read-only on every reference;
no Blender, shaders, network, subprocesses or shared application interaction.
Only the preserved historical W115 shader bake used background Blender.
W118 reads that cache and original mesh; no new DCC process is used.
"""
import argparse,base64,copy,hashlib,importlib.util,io,itertools,json,math,runpy,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
ART=Path('art/weapons/w115/blast_furnace');DESIGN=ART/'design.json'
TEXTURE=Path('src/main/resources/assets/destiny/textures/item/weapon/w115/blast_furnace.png')
MODELS=Path('src/main/resources/assets/destiny/models/weapon_surface_w115')
BASE=Path('src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace.json')
FACES=('north','south','west','east','up','down')
FACE_CORNERS={'north':(6,2,0,4),'south':(3,7,5,1),'west':(2,3,1,0),'east':(7,6,4,5),'up':(2,6,7,3),'down':(1,5,4,0)}
NORMALS={'north':(0,0,-1),'south':(0,0,1),'west':(-1,0,0),'east':(1,0,0),'up':(0,1,0),'down':(0,-1,0)}
def sha(b):return hashlib.sha256(b).hexdigest()
def encode(j):return (json.dumps(j,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9);return b.getvalue()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w115/blast_furnace/r5/'+s))
def compiler(design):
 p=ROOT/'scripts/mesh/native_triangle_elements_w115.py'
 if not p.exists():p=Path('/Users/qf/IdeaProjects/DestinyGuardians/scripts/mesh/native_triangle_elements_w115.py')
 assert sha(p.read_bytes())==design['compilerSha256'],'Common compiler drift: '+str(p)
 spec=importlib.util.spec_from_file_location('w115_native_triangle',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def rotation_matrix(e):
 r=e.get('rotation',{});m=np.eye(3)
 angles={a:r.get(a,0) for a in 'xyz'}
 if 'axis' in r:angles[r['axis']]=r['angle']
 for axis in 'xyz':
  t=math.radians(angles[axis]);c,s=math.cos(t),math.sin(t)
  a={'x':[[1,0,0],[0,c,-s],[0,s,c]],'y':[[c,0,s],[0,1,0],[-s,0,c]],'z':[[c,-s,0],[s,c,0],[0,0,1]]}[axis]
  m=np.array(a)@m
 return m

def euler_rzryrx(matrix):
 """Native element Rz*Ry*Rx, with an explicit gimbal branch (not ItemTransform)."""
 r=np.array(matrix);y=math.asin(float(np.clip(-r[2,0],-1,1)))
 if abs(math.cos(y))<1e-7:x=0.;z=math.atan2(-r[0,1],r[1,1])
 else:x=math.atan2(r[2,1],r[2,2]);z=math.atan2(r[1,0],r[0,0])
 return np.degrees([x,y,z]).tolist()

def vertices(e):
 v=np.array(list(itertools.product(*zip(e['from'],e['to']))),dtype=float)
 if 'rotation' in e:
  o=np.array(e['rotation']['origin']);v=(v-o)@rotation_matrix(e).T+o
 return v

def geometry_vertices(e):
 # Transparent card corners are not source geometry. Effective support retains
 # source-union holes and disconnected patches; rendering still uses native quads.
 return np.array(e['support_triangles']).reshape(-1,3) if e.get('kind')=='alpha_patch' else vertices(e)

def bounds(elements):
 v=np.concatenate([geometry_vertices(e) for e in elements]);return [v.min(0).tolist(),v.max(0).tolist()]

def render(elements,texture,view,width=1000,height=390,scale=33,offset=None,return_mask=False):
 """Orthographic textured z-buffer triangles, identical lights/camera before/after."""
 right,up,depth=[np.array(v,dtype=float) for v in view]
 bg=np.zeros((height,width,3),dtype=np.uint8)
 for y in range(height):bg[y,:,:]=np.array([29,34,41])+int(y/height*9)
 zbuffer=np.full((height,width),-np.inf);tex=np.array(texture.convert('RGBA'))
 center=np.array([8.006,10.70,5.69445]);ox,oy=offset or (width/2,height*.47)
 light=np.array([-.45,.78,-.42]);light/=np.linalg.norm(light)
 for e in elements:
  verts=vertices(e);pts=verts-center
  screen=np.stack((pts@right*scale+ox,-pts@up*scale+oy,pts@depth),axis=1)
  rot=rotation_matrix(e)
  for face,ids in FACE_CORNERS.items():
   normal=rot@np.array(NORMALS[face]);f=e['faces'].get(face)
   if f is None:continue
   if normal@depth<=1e-7:continue
   u1,v1,u2,v2=f['uv'];uv=np.array([[u1,v1],[u2,v1],[u2,v2],[u1,v2]])/16
   q=screen[list(ids)];lighting=.60+.40*max(0,float(normal@light))
   for tri in ((0,1,2),(0,2,3)):
    p=q[list(tri)];t=uv[list(tri)]
    x0=max(0,int(np.floor(p[:,0].min())));x1=min(width-1,int(np.ceil(p[:,0].max())))
    y0=max(0,int(np.floor(p[:,1].min())));y1=min(height-1,int(np.ceil(p[:,1].max())))
    if x1<x0 or y1<y0:continue
    xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
    if abs(den)<1e-8:continue
    a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
    b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den;c=1-a-b
    zz=a*p[0,2]+b*p[1,2]+c*p[2,2]
    sl=np.s_[y0:y1+1,x0:x1+1];mask=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)&(zz>zbuffer[sl])
    tu=a*t[0,0]+b*t[1,0]+c*t[2,0];tv=a*t[0,1]+b*t[1,1]+c*t[2,1]
    tx=np.clip((tu*tex.shape[1]).astype(int),0,tex.shape[1]-1);ty=np.clip((tv*tex.shape[0]).astype(int),0,tex.shape[0]-1)
    colors=tex[ty,tx];mask &= colors[:,:,3]>127
    bg[sl][mask]=np.clip(colors[:,:,:3]*lighting,0,255).astype(np.uint8)[mask];zbuffer[sl][mask]=zz[mask]
 return (Image.fromarray(bg),np.isfinite(zbuffer)) if return_mask else Image.fromarray(bg)

def camera(yaw,elevation):
 # yaw zero is left profile, longitudinal axis horizontal, muzzle at left.
 a,b=math.radians(yaw),math.radians(elevation)
 depth=np.array([-math.cos(a)*math.cos(b),math.sin(b),math.sin(a)*math.cos(b)])
 right=np.array([math.sin(a),0,math.cos(a)]);up=np.cross(depth,right)
 return right,up,depth


def source_data():
 m=runpy.run_path(str(ROOT/'scripts/generate_reload_w114_blast_furnace.py'));return m['source_meshes']()

def source_mask(meshes,view,width,height,scale,offset=None):
 right,up,depth=[np.array(v) for v in view];center=np.array([8.006,10.70,5.69445]);ox,oy=offset or (width/2,height*.47);mask=np.zeros((height,width),dtype=bool)
 for m in meshes:
  p=np.array(m['vertices'])-center;screen=np.stack((p@right*scale+ox,-p@up*scale+oy),axis=1)
  for f in m['faces']:
   t=screen[list(f)];x0=max(0,int(np.floor(t[:,0].min())));x1=min(width-1,int(np.ceil(t[:,0].max())));y0=max(0,int(np.floor(t[:,1].min())));y1=min(height-1,int(np.ceil(t[:,1].max())))
   if x1<x0 or y1<y0:continue
   den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
   if abs(den)<1e-10:continue
   xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
   a=((t[1,1]-t[2,1])*(xx-t[2,0])+(t[2,0]-t[1,0])*(yy-t[2,1]))/den
   b=((t[2,1]-t[0,1])*(xx-t[2,0])+(t[0,0]-t[2,0])*(yy-t[2,1]))/den;c=1-a-b
   mask[y0:y1+1,x0:x1+1]|=(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)
 return mask

def contour_meshes(design):
 """Intended geometry before alpha rasterization, independent of atlas pixels."""
 meshes=[]
 for specs in design['parts'].values():
  for s in specs:
   if s['kind']=='alpha_patch':
    t=np.array(s['support_triangles']);meshes.append(dict(vertices=t.reshape(-1,3),faces=np.arange(t.size//3).reshape(-1,3)))
   else:
    fs=[]
    for ids in FACE_CORNERS.values():fs.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]])
    meshes.append(dict(vertices=vertices(s),faces=fs))
 return meshes

R2ROOT=Path('docs/qa/2026-10-25/w116/r2-inputs')
BATCH=Path('docs/qa/2026-10-25/w118/batch.json')
EDGE=1024

_CAPTURE=None
def capture():
 global _CAPTURE
 if _CAPTURE is None:
  a=np.load('/private/tmp/destiny-w115-blast_furnace-dyed-source.npz');_CAPTURE={k:a[k] for k in a.files}
 return _CAPTURE

def covered_rectangle(rect,others):
 a,b,c,d=rect;cuts=sorted(set([a,b]+[max(a,min(b,x)) for r in others for x in r[:2]]))
 for lo,hi in zip(cuts,cuts[1:]):
  if hi-lo<1e-9:continue
  x=(lo+hi)/2;spans=sorted((max(c,r[2]),min(d,r[3])) for r in others if r[0]<=x<=r[1] and r[3]>c and r[2]<d);end=c
  for y,z in spans:
   if y>end+1e-7:break
   end=max(end,z)
  if end<d-1e-7:return False
 return True

def hidden_faces(specs):
 result={};axes={'west':(0,-1),'east':(0,1),'down':(1,-1),'up':(1,1),'north':(2,-1),'south':(2,1)}
 for s in specs:
  key=s['source_mesh'],s['source_component'];lo,hi=np.array(s['local_bounds']);hidden=[]
  for face,(axis,sign) in axes.items():
   plane=(lo if sign<0 else hi)[axis]+sign*1e-6;uv=[i for i in range(3) if i!=axis];rect=[lo[uv[0]],hi[uv[0]],lo[uv[1]],hi[uv[1]]];others=[]
   for other in specs:
    if other is s or other['source_bone']!=s['source_bone'] or any(abs(other['rotation'][a]-s['rotation'][a])>1e-8 for a in 'xyz'):continue
    a,b=np.array(other['local_bounds'])
    if a[axis]<=plane<=b[axis]:others.append([a[uv[0]],b[uv[0]],a[uv[1]],b[uv[1]]])
   if others and covered_rectangle(rect,others):hidden.append(face)
  if len(hidden)==6:hidden.remove('west')  # preserve one editable original-component face
  result[s['name']]=hidden
 # A duplicate coplanar face is not an internal face: the outward epsilon test
 # correctly leaves it alive. Give complete same-material coincident rectangles
 # one deterministic emitted owner. Partial overlaps are NOT blindly deleted.
 for i,s in enumerate(specs):
  lo,hi=np.array(s['local_bounds'])
  for face,(axis,sign) in axes.items():
   if face in result[s['name']]:continue
   plane=(lo if sign<0 else hi)[axis];uv=[j for j in range(3) if j!=axis];covers=[]
   for other in specs[:i]:
    if face in result[other['name']] or other['source_bone']!=s['source_bone'] or other['material']!=s['material'] or any(abs(other['rotation'][a]-s['rotation'][a])>1e-8 for a in 'xyz'):continue
    a,b=np.array(other['local_bounds']);op=(a if sign<0 else b)[axis]
    if abs(op-plane)<=1e-8:covers.append([a[uv[0]],b[uv[0]],a[uv[1]],b[uv[1]]])
   if covers and covered_rectangle([lo[uv[0]],hi[uv[0]],lo[uv[1]],hi[uv[1]]],covers) and len(result[s['name']])<5:result[s['name']].append(face)
 return result

def atlas_and_models(d):
 edge=EDGE;im=Image.new('RGBA',(edge,edge),(0,0,0,0));draw=ImageDraw.Draw(im);tiles={};plain={};x=y=3;rh=0;atlas_rows=[]
 def place(w,h):
  nonlocal x,y,rh
  if x+w+3>edge:x=3;y+=rh+5;rh=0
  assert y+h+3<edge,'Atlas overflow'
  a,b=x,y;x+=w+5;rh=max(rh,h);return a,b
 for role,col in d['palette'].items():
  a,b=place(8,8);draw.rectangle([a-2,b-2,a+9,b+9],fill=tuple(col)+(255,));plain[role]=[a/64,b/64,(a+8)/64,(b+8)/64]
 for row in d['componentSpecs']:
  key=(row['source_mesh'],row['source_component']);ss=[s for es in d['parts'].values() for s in es if (s['source_mesh'],s['source_component'])==key];s=ss[0];axis=s['profile_axis'];u=2 if axis==0 else 0;v=1;lo,hi=np.array(s['profile_frame_bounds']);extent=hi-lo
  density=48 if key==(0,12) else 20 if key==(0,0) else 13;w=max(8,min(256,math.ceil(extent[u]*density)));h=max(8,min(192,math.ceil(extent[v]*density)));a,b=place(w,h);col=d['palette'][s['material']];tile=Image.new('RGBA',(w,h),tuple(col)+(255,));td=ImageDraw.Draw(tile)
  # Authored source panel lines only. No nearest-source texture transfer, noise,
  # speckles, transparency, per-section border or invented decorative greeble.
  def point(z,yy):return ((z-lo[u])/max(extent[u],1e-9)*(w-1),(hi[v]-yy)/max(extent[v],1e-9)*(h-1))
  dark=tuple(max(0,int(c*.78)) for c in col)+(255,);light=tuple(min(255,int(c*1.10)) for c in col)+(255,)
  if key==(0,0):
   for ya,z1,z2 in ((11.25,3.4,13.5),(12.05,3.4,6.1)):
    td.line([point(z1,ya),point(z2,ya)],fill=dark,width=1)
  if key in ((0,24),(0,34),(0,54)):
   td.line([(2,h-3),(w-3,h-3)],fill=dark,width=1);td.line([(2,2),(w-3,2)],fill=light,width=1)
  if key in ((0,0),(0,12)):
   # Backprojected original profile: large stock-side port at Z14.08/Y12.28
   # belongs to Frame12; adjacent receiver recess belongs to Frame0.
   # Existing cap materials only: no new silhouette, fake alpha hole or greeble.
   def box2(z1,y1,z2,y2):
    p,q=point(z1,y1),point(z2,y2);return [min(p[0],q[0]),min(p[1],q[1]),max(p[0],q[0]),max(p[1],q[1])]
   if key==(0,12):
    td.ellipse(box2(13.78,11.98,14.38,12.58),fill=(31,36,33,255),outline=(123,129,121,255),width=1)
    td.ellipse(box2(13.96,12.16,14.20,12.40),fill=(151,156,144,255),outline=(73,80,72,255),width=1)
   else:
    td.rectangle(box2(10.36,11.98,13.48,12.80),fill=(79,85,79,255),outline=(60,66,60,255),width=1)
    td.rectangle(box2(10.60,12.16,13.22,12.62),fill=(118,123,114,255))
    td.line([point(12.35,12.17),point(12.35,12.62)],fill=(68,74,67,255),width=1)
    # The fitted outer receiver occludes part of the raw stock-side cap. Restore
    # the same source-anchored port pigment on the visible outer material too.
    td.ellipse(box2(13.78,11.98,14.38,12.58),fill=(31,36,33,255),outline=(123,129,121,255),width=1)
    td.ellipse(box2(13.96,12.16,14.20,12.40),fill=(151,156,144,255),outline=(73,80,72,255),width=1)
  if key==(0,16):
   td.line([point(10.5,10.4),point(11.4,10.4),point(13.45,9.2)],fill=tuple(d['palette']['red'])+(255,),width=2)
  if key==(0,1):
   td.line([(w*.18,h*.26),(w*.70,h*.26)],fill=light,width=1);td.line([(w*.22,h*.7),(w*.78,h*.7)],fill=dark,width=1)
  if key in ((0,0),(0,2),(0,8),(0,12)):
   td.line([(2,2),(w-3,2)],fill=light,width=1)
  if key==(0,18):
   # Original magazine's straight longitudinal pressed channel; no fractured wear.
   td.line([(w*.53,3),(w*.53,h-4)],fill=dark,width=1)
  if key==(0,6):
   for yy in (h*.35,h*.51,h*.67):td.line([(w*.24,yy),(w*.72,yy)],fill=dark,width=1)
  im.paste(tile,(a,b));arr=np.array(tile);padded=np.pad(arr,((2,2),(2,2),(0,0)),mode='edge');im.paste(Image.fromarray(padded),(a-2,b-2));tiles[key]=(a,b,w,h,u,v,lo,hi)
  atlas_rows.append(dict(source_mesh=key[0],source_component=key[1],pixels=[a,b,w,h],gutter=2,material=s['material']))
 # Small planar circular/diagonal source patches get their own local union mask;
 # no nearest-source sampling, disconnected hull fill, or ripped texture transfer.
 patch_tiles={};patch_rows=[]
 for part,ss in d['parts'].items():
  for spec in ss:
   if spec['kind']!='alpha_patch':continue
   lo,hi=np.array(spec['local_bounds']);extent=hi-lo;w=max(4,math.ceil(extent[0]*spec.get('mask_density',d['neck_refinement']['maskDensity'])));h=max(4,math.ceil(extent[1]*spec.get('mask_density',d['neck_refinement']['maskDensity'])));a,b=place(w,h)
   R=rotation_matrix(spec);tri=(np.array(spec['support_triangles'])@R)[:,:,:2];px=(np.arange(w)+.5)/w*extent[0]+lo[0];py=(1-(np.arange(h)+.5)/h)*extent[1]+lo[1];xx,yy=np.meshgrid(px,py);points=np.stack((xx,yy),axis=2);mask=np.zeros((h,w),bool)
   # Conservative pixel-square support prevents artificial inter-patch cracks.
   # Its measured raster contour envelope is separate from exact source geometry.
   for t in tri:
    cross=(t[1,0]-t[0,0])*(t[2,1]-t[0,1])-(t[1,1]-t[0,1])*(t[2,0]-t[0,0]);sign=1 if cross>=0 else -1;inside=np.ones((h,w),bool)
    for x0,x1 in zip(t,np.roll(t,-1,axis=0)):
     ed=x1-x0;rel=points-x0;distance=sign*(ed[0]*rel[:,:,1]-ed[1]*rel[:,:,0]);radius=(abs(ed[0])*extent[1]/h+abs(ed[1])*extent[0]/w)*.500001
     inside &= distance>=-radius-1e-12
    # Triangle/texel SAT also needs the two rectangle axes. Omitting
    # these over-expanded acute source corners beyond one texel.
    inside &= (xx>=t[:,0].min()-extent[0]/w*.5-1e-12)&(xx<=t[:,0].max()+extent[0]/w*.5+1e-12)&(yy>=t[:,1].min()-extent[1]/h*.5-1e-12)&(yy<=t[:,1].max()+extent[1]/h*.5+1e-12)
    mask |= inside
   ys,xs=np.where(mask);world_corners=[]
   for du,dv in ((0,0),(1,0),(0,1),(1,1)):
    world_corners.append(np.c_[lo[0]+(xs+du)/w*extent[0],hi[1]-(ys+dv)/h*extent[1],np.full(len(xs),lo[2])]@R.T)
   raster_points=np.concatenate(world_corners);raster_bounds=[raster_points.min(0).tolist(),raster_points.max(0).tolist()]
   arr=np.zeros((h,w,4),np.uint8);arr[:,:,:3]=d['palette'][spec['material']];arr[:,:,3]=mask*255;im.paste(Image.fromarray(np.pad(arr,((2,2),(2,2),(0,0)),mode='edge')),(a-2,b-2));patch_tiles[spec['name']]=[a/64,b/64,(a+w)/64,(b+h)/64]
   patch_rows.append(dict(name=spec['name'],source_mesh=spec['source_mesh'],source_component=spec['source_component'],pixels=[a,b,w,h],gutter=2,material=spec['material'],supportTriangles=len(tri),rasterBounds=raster_bounds,maxTexelDiagonal=float(np.linalg.norm(extent[:2]/[w,h]))))
 models={};hidden=hidden_faces([s for s in sum(d['parts'].values(),[]) if s['kind']=='cuboid' and not s.get('opaque_source_plane')])
 for part,ss in d['parts'].items():
  es=[]
  for s in ss:
   e={k:copy.deepcopy(s[k]) for k in ('name','from','to','rotation')};e['faces']={}
   if s['kind']=='alpha_patch' or s.get('opaque_source_plane'):
    uv=patch_tiles[s['name']] if s['kind']=='alpha_patch' else plain[s['material']];e['faces']={'south':dict(uv=uv,texture='#0'),'north':dict(uv=[uv[2],uv[1],uv[0],uv[3]],texture='#0')};es.append(e);continue
   key=s['source_mesh'],s['source_component'];a,b,w,h,u,v,lo,hi=tiles[key];local=np.array(list(itertools.product(*zip(*s['local_bounds']))));axis=s['profile_axis'];caps=('west','east') if axis==0 else ('north','south')
   for face,ids in FACE_CORNERS.items():
    if face in hidden[s['name']]:continue
    uv=plain[s['material']]
    if not s.get('surface_panel') and face in caps and min((hi-lo)[[u,v]])>=.003:
     p,q=local[ids[0]],local[ids[2]]
     def U(k):return (a+.5+(k-lo[u])/max(hi[u]-lo[u],1e-12)*(w-1))/64
     def V(k):return (b+.5+(hi[v]-k)/max(hi[v]-lo[v],1e-12)*(h-1))/64
     uv=[U(p[u]),V(p[v]),U(q[u]),V(q[v])]
    e['faces'][face]=dict(uv=uv,texture='#0')
   es.append(e)
  models[part]=dict(credit='W118 R5 Blast Furnace | opaque primary cuboids + source-plane collar/sleeve patches',textures={'0':'destiny:item/weapon/w115/blast_furnace','particle':'destiny:item/weapon/w115/blast_furnace'},elements=es)
 return models,png(im),atlas_rows,patch_rows

def inspection(models,texture,d):
 es=[];groups=[]
 for part,m in models.items():
  children=[]
  for e in m['elements']:
   r=e['rotation'];b={k:copy.deepcopy(e[k]) for k in ('name','from','to')};b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],autouv=0,box_uv=False,rescale=False,locked=False,visibility=True,export=True,shade=True)
   b['faces']={f:(dict(uv=[v*64 for v in e['faces'][f]['uv']],texture=0) if f in e['faces'] else dict(uv=[0,0,0,0],texture=None)) for f in FACES};es.append(b);children.append(b['uuid'])
  groups.append(dict(name=part,uuid=uid(part),origin=[8,8,8],children=children,export=True,isOpen=True))
 return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W118 R5 Blast Furnace / cuboids and source-plane patches',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,textures=[dict(path='',name='blast_furnace.png',folder='',namespace='destiny',id='0',uuid=uid('atlas'),source='data:image/png;base64,'+base64.b64encode(texture).decode(),mode='bitmap',width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,particle=True)],destiny_w118=dict(revision=5,nativeAcceptance=False))

def raw_render(view,width,height,scale,removed=False,offset=None):
 # Original shader capture retained from W115; no Blender import/process needed.
 p=Path('/private/tmp/destiny-w115-blast_furnace-dyed-source.npz');a=capture();tris=a['coords'][a['tris']].copy()
 if removed:
  d=json.loads((ROOT/DESIGN).read_bytes());moving=[i for r in d['componentSpecs'] if r['source_bone']=='Magazine' for i in r['captured_triangle_ids']];tris[moving,:,1]-=3.4
 uvs=a['uvs'];tids=a['texture_ids'];textures=[a['texture_'+str(i)] for i in range(3)];right,up,depth=[np.array(v) for v in view];center=np.array([8.006,10.70,5.69445]);img=np.zeros((height,width,3),np.uint8)
 for y in range(height):img[y]=np.array([29,34,41])+int(y/height*9)
 ox,oy=offset or (width/2,height*.47);zbuf=np.full((height,width),-np.inf);p3=tris-center;screen=np.stack((p3@right*scale+ox,-p3@up*scale+oy,p3@depth),axis=2);light=np.array([-.45,.78,-.42]);light/=np.linalg.norm(light)
 for source,p,t,tid in zip(tris,screen,uvs,tids):
  normal=np.cross(source[1]-source[0],source[2]-source[0]);normal/=max(np.linalg.norm(normal),1e-12)
  # Original X/Z/Y conversion reverses handedness; raw source is double sided here.
  lighting=.60+.40*abs(float(normal@light));x0=max(0,int(np.floor(p[:,0].min())));x1=min(width-1,int(np.ceil(p[:,0].max())));y0=max(0,int(np.floor(p[:,1].min())));y1=min(height-1,int(np.ceil(p[:,1].max())))
  if x0>x1 or y0>y1:continue
  den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
  if abs(den)<1e-9:continue
  xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);wa=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den;wb=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den;wc=1-wa-wb;zz=wa*p[0,2]+wb*p[1,2]+wc*p[2,2];sl=np.s_[y0:y1+1,x0:x1+1];mask=(wa>=0)&(wb>=0)&(wc>=0)&(zz>zbuf[sl]);uv=wa[:,:,None]*t[0]+wb[:,:,None]*t[1]+wc[:,:,None]*t[2];tex=textures[int(tid)];tx=((uv[:,:,0]%1)*tex.shape[1]).astype(int)%tex.shape[1];ty=((uv[:,:,1]%1)*tex.shape[0]).astype(int)%tex.shape[0];col=tex[ty,tx,:3];img[sl][mask]=np.clip(col*lighting,0,255).astype(np.uint8)[mask];zbuf[sl][mask]=zz[mask]
 return Image.fromarray(img)

def comparison(d,models,texture):
 r2models={p:json.loads((ROOT/R2ROOT/MODELS/f'blast_furnace_{p}.json').read_bytes()) for p in models};r2d=json.loads((ROOT/R2ROOT/DESIGN).read_bytes());r2tex=Image.open(io.BytesIO(base64.b64decode(r2d['atlas']['png_base64'])));r1tex=Image.open(io.BytesIO(base64.b64decode(d['rejected_r1']['texture_base64'])));r1=d['rejected_r1']['models'];r3=d['previous_r3']['models'];r3tex=Image.open(io.BytesIO(base64.b64decode(d['previous_r3']['texture_base64'])));r4=d['previous_r4']['models'];r4tex=Image.open(io.BytesIO(base64.b64decode(d['previous_r4']['texture_base64'])));im=Image.open(io.BytesIO(texture))
 out=Image.new('RGB',(4200,3020),'#171c23');draw=ImageDraw.Draw(out);draw.text((18,10),'BLAST FURNACE / RAW - R1 - R2 - FROZEN R3 - FROZEN R4 - R5 / OFFLINE, NOT IN-GAME',fill='white',font=ImageFont.load_default(size=23))
 rows=[('PROFILE',camera(0,0)),('MUZZLE OBLIQUE',camera(-28,18)),('REAR / STOCK',camera(152,16)),('HIGH TOP / ADS SURFACES',camera(-10,72)),('REAR ADS AXIS',camera(90,15)),('MAGAZINE REMOVED',camera(-18,8)),('RECEIVER HIP DETAIL',camera(-28,18)),('RECEIVER HIGH DETAIL',camera(-12,38))]
 titles=('RAW / 29124 original triangles','R1 REJECTED / 71 cubes','R2 REJECTED / 1504 elements','FROZEN R3 / 1073 cubes','FROZEN R4 / 1135 cubes',f'R5 / {sum(len(m["elements"]) for m in models.values())} native elements')
 for row,(label,view) in enumerate(rows):
  yy=50+row*370;scale=24 if row<6 else 135;offset=None
  if row>=6:
   center=np.array([8.006,10.70,5.69445]);target=np.array([8,13.00,9.4]);delta=target-center;offset=(350-delta@view[0]*scale,170+delta@view[1]*scale)
  raw=raw_render(view,700,340,scale,removed=row==5,offset=offset);out.paste(raw,(0,yy))
  for col,(ms,tex) in enumerate(zip((r1,r2models,r3,r4,models),(r1tex,r2tex,r3tex,r4tex,im)),1):
   es=copy.deepcopy(sum([m['elements'] for m in ms.values()],[]))
   if row==5:
    for e in es[len(ms['body']['elements']):]:
     for k in ('from','to'):e[k][1]-=3.4
     e.get('rotation',{}).get('origin',[0,0,0])[1]-=3.4
   out.paste(render(es,tex,view,700,340,scale,offset=offset),(col*700,yy))
  for col,title in enumerate(titles):
   draw.text((col*700+12,yy+4),title,fill=('#98d6b6' if col==5 else '#c9b7b0'),font=ImageFont.load_default(size=17));draw.text((col*700+12,yy+27),label,fill='#b0bfce',font=ImageFont.load_default(size=14))
 return png(out)

def point_box_distance(points,e):
 p=np.array(points);lo,hi=np.array(e['from']),np.array(e['to']);o=np.array(e['rotation']['origin']);q=(p-o)@rotation_matrix(e)+o
 return np.linalg.norm(np.maximum(lo-q,np.maximum(q-hi,0)),axis=1)

def point_triangle_distance(points,triangles):
 t=np.array(triangles);aa=t[:,0];ab=t[:,1]-aa;ac=t[:,2]-aa;nn=np.cross(ab,ac);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-20);out=[]
 d00=(ab*ab).sum(1);d01=(ab*ac).sum(1);d11=(ac*ac).sum(1);den=d00*d11-d01*d01;den=np.where(abs(den)>1e-20,den,1e20)
 for start in range(0,len(points),32):
  p=np.array(points[start:start+32]);delta=p[:,None]-aa;nd=(delta*nn).sum(2);proj=delta-nd[:,:,None]*nn;d20=(proj*ab).sum(2);d21=(proj*ac).sum(2);u=(d11*d20-d01*d21)/den;v=(d00*d21-d01*d20)/den;dist=np.where((u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8),abs(nd),np.inf)
  for a,b in ((t[:,0],t[:,1]),(t[:,1],t[:,2]),(t[:,2],t[:,0])):
   e=b-a;q=((p[:,None]-a)*e).sum(2)/np.maximum((e*e).sum(1),1e-20);foot=a+np.clip(q,0,1)[:,:,None]*e;dist=np.minimum(dist,np.linalg.norm(p[:,None]-foot,axis=2))
  out.extend(dist.min(1).tolist())
 return np.array(out)

def projection_distance(points,triangles):
 # Exact distance to union of original source projected triangles (no raster grid).
 t=np.array(triangles);a=t[:,0];b=t[:,1];c=t[:,2];ab=b-a;ac=c-a;den=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0];out=[]
 for start in range(0,len(points),32):
  p=np.array(points[start:start+32]);q=p[:,None]-a;safe=np.where(abs(den)>1e-12,den,1);u=(q[:,:,0]*ac[:,1]-q[:,:,1]*ac[:,0])/safe;v=(ab[:,0]*q[:,:,1]-ab[:,1]*q[:,:,0])/safe;inside=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(abs(den)>1e-12);best=np.full((len(p),len(t)),np.inf)
  for x,y in ((a,b),(b,c),(c,a)):
   d=y-x;dot=((p[:,None]-x)*d).sum(2)/np.maximum((d*d).sum(1),1e-24);foot=x+np.clip(dot,0,1)[:,:,None]*d;best=np.minimum(best,np.linalg.norm(p[:,None]-foot,axis=2))
  best[inside]=0;out.extend(best.min(1).tolist())
 return np.array(out)

def spatial_fidelity(d,models):
 sources=source_data();r2=json.loads((ROOT/R2ROOT/DESIGN).read_bytes());rows=[];element_by_name={e['name']:e for m in models.values() for e in m['elements']}
 for row in d['componentSpecs']:
  mi,ci=row['source_mesh'],row['source_component'];src=sources[mi];t=np.array(src['vertices'])[np.array(src['faces'])[src['components'][ci]['sourcePolygonIndices']]];points=np.unique(np.round(t.reshape(-1,3),8),axis=0);ss=[s for es in d['parts'].values() for s in es if (s['source_mesh'],s['source_component'])==(mi,ci)];es=[element_by_name[s['name']] for s in ss];distance=np.min(np.stack([point_triangle_distance(points,s['support_triangles']) if s['kind']=='alpha_patch' else point_box_distance(points,e) for s,e in zip(ss,es)]),axis=0);vv=np.concatenate([geometry_vertices(s) for s in ss]);b=np.array([vv.min(0),vv.max(0)]);original=np.array([points.min(0),points.max(0)]);R=rotation_matrix({'rotation':{'x':row['profile_angle_x']}});axis='xyz'.index(row['profile_normal']);uv=[i for i in range(3) if i!=axis];testpoints=[]
  for s,e in zip(ss,es):
   v=geometry_vertices(s);testpoints.extend(v)
   if s['kind']=='alpha_patch':testpoints.extend(np.array(s['support_triangles']).mean(1))
   else:testpoints.extend((v[i]+v[j])/2 for i,j in ((0,1),(0,2),(0,4),(7,6),(7,5),(7,3)))
  projection=projection_distance((np.array(testpoints)@R)[:,uv],(t@R)[:,:,uv]);old=[s for ps in r2['parts'].values() for s in ps if (s['source_mesh'],s['source_component'])==(mi,ci)];oldpts=np.concatenate([np.array(s['support_triangles']).reshape(-1,3) if s['kind']=='alpha_patch' else vertices(s) for s in old]);oldbounds=np.array([oldpts.min(0),oldpts.max(0)])
  rows.append(dict(source_mesh=mi,source_component=ci,sourceBounds=original.tolist(),productBounds=b.tolist(),extentDeviationMax=float(abs(b-original).max()),sourceCoverageMax=float(distance.max()),sourceCoverageP95=float(np.quantile(distance,.95)),profileOverreachMax=float(projection.max()),r2ExtentDeviationMax=float(abs(oldbounds-original).max())))
 return rows

def raster_fidelity(d,patch_rows):
 rows=[];old={(r['source_mesh'],r['source_component']):r for r in d['previous_r4']['spatialFidelity']}
 for ci in (3,10):
  boxes=[r['rasterBounds'] for r in patch_rows if r['source_component']==ci]
  for s in d['parts']['body']:
   if s.get('opaque_source_plane') and s['source_component']==ci:
    v=vertices(s);boxes.append([v.min(0),v.max(0)])
  b=np.array(boxes);bounds=np.array([b[:,0].min(0),b[:,1].max(0)]);original=np.array(old[0,ci]['sourceBounds']);dev=float(abs(bounds-original).max());limit=old[0,ci]['extentDeviationMax']
  assert dev<=limit+1e-6,('Raster source-envelope worsened R4',ci,dev,limit)
  rows.append(dict(source_mesh=0,source_component=ci,sourceBounds=original.tolist(),occupiedTexelBounds=bounds.tolist(),extentDeviationMax=dev,r4ExtentDeviationMax=limit))
 return rows

def generate():
 d=json.loads((ROOT/DESIGN).read_bytes());assert d['revision']==5;compiler(d)
 for rel,pin in d['input_pins'].items():
  p=Path(rel) if Path(rel).is_absolute() else ROOT/rel;assert sha(p.read_bytes())==pin,'Input drift '+rel
 models,texture,atlas,patch_atlas=atlas_and_models(d);spatial=spatial_fidelity(d,models);out={TEXTURE:texture,ART/'inspection.bbmodel':encode(inspection(models,texture,d)),ART/'comparison.png':comparison(d,models,texture)}
 for p,m in models.items():out[MODELS/f'blast_furnace_{p}.json']=encode(m)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w118-blast_furnace');es=sum([m['elements'] for m in models.values()],[])
 manifest=dict(stage='W118',revision=5,weapon='blast_furnace',generator='scripts/generate_surface_w115_blast_furnace.py',sourceTriangleCount=29124,sourceComponentCount=270,sourceMagazineTriangles=681,partCounts={p:len(m['elements']) for p,m in models.items()},cubeCount=len(es),elementCount=len(es),solidCuboidCount=sum(s['kind']=='cuboid' and not s.get('opaque_source_plane') for ss in d['parts'].values() for s in ss),opaquePlaneCount=sum(bool(s.get('opaque_source_plane')) for ss in d['parts'].values() for s in ss),alphaPatchCount=sum(s['kind']=='alpha_patch' for ss in d['parts'].values() for s in ss),primitiveTypes={'cuboid':sum(s['kind']=='cuboid' and not s.get('opaque_source_plane') for ss in d['parts'].values() for s in ss),'opaque_plane':sum(bool(s.get('opaque_source_plane')) for ss in d['parts'].values() for s in ss),'alpha_patch':sum(s['kind']=='alpha_patch' for ss in d['parts'].values() for s in ss)},quadCount=sum(len(e['faces']) for e in es),textureSize=[EDGE,EDGE],rotationOrder='Rz*Ry*Rx',bounds=bounds(sum(d['parts'].values(),[])),partBounds={p:bounds(ss) for p,ss in d['parts'].items()},partPivots={p:[8,8,8] for p in models},compilerSha256=d['compilerSha256'],inputPins=d['input_pins'],componentLedger=d['componentSpecs'],refinement=d['neck_refinement'],previousRefinement=d['surface_refinement'],spatialFidelity=spatial,atlasComponents=atlas,atlasPatches=patch_atlas,rasterFidelity=raster_fidelity(d,patch_atlas),ownedPaths=owned,changedPaths=owned,nativeAcceptance=False,limitations=['R5 replaces only collar/sleeve horizontal slab anatomy with source-plane patches. Alpha-card raster contour is separate from ideal support geometry; native temporal acceptance is pending.','Same 0.1 component bounds/coverage and 0.5 projected-contour limits retained; R3 and R4 per-component metrics also must not deteriorate.','Receiver extrusion can occlude original stock-side cap; port material is repeated on visible outer cap at original Y/Z.','Authored source-profile cuboid approximation; not original triangles or pixel-perfect source surfacing.','Native shading/performance and all acceptance are master-only. No live client/DCC used.'],sha256={str(p):sha(b) for p,b in out.items()})
 hashes={str(p):sha(b) for p,b in out.items()}
 for rel in owned:
  if rel!=str(ART/'manifest.json') and rel not in hashes and (ROOT/rel).is_file():hashes[rel]=sha((ROOT/rel).read_bytes())
 manifest['deliverySha256']=hashes;out[ART/'manifest.json']=encode(manifest);assert set(map(str,out))<=set(owned);return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();out=generate()
 for rel,b in out.items():
  path=ROOT/rel
  if a.verify:assert path.is_file() and path.read_bytes()==b,'Output drift '+str(rel)
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
 print(('Verified' if a.verify else 'Generated')+f' {len(out)} deterministic W118 R5 products; source-fitted cuboids and circular/diagonal source-union planes; offline only')
if __name__=='__main__':main()
