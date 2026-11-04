#!/usr/bin/env python3
"""W144 Null Composure: authored semantic solids, full-only, inert source readers."""
import argparse, base64, collections, copy, hashlib, io, json, math, runpy, struct, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='null_composure'
ASSET='src/main/resources/assets/destiny/'
ART=f'art/weapons/w123/{ID}/'
BASE=ASSET+f'models/weapon/fusion_rifle/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w144/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/null_composure/extracted/Null Composure')
PHOTO=Path('/tmp/destiny-weapons-w31/references/null_composure.jpg')
H=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
E=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_erentil_fr4.py'))
L=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_long_arm.py'))
FACES=H['FACES'];EDGE=1024
PALETTE=dict(silver=[182,191,193],edge=[141,157,163],blue=[24,105,159],bluebright=[52,135,188],black=[27,30,32],rubber=[20,23,25],gold=[185,155,58],steel=[75,88,96],recess=[12,17,21])
def sha(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w144:null_composure:'+n))
def vertices(e):return H['vertices'](e)
def triangles(m,tex):return H['model_triangles']({'full':m},tex)

def source_meshes():
 meta=copy.deepcopy(json.loads((ROOT/SOURCE).read_bytes())['destiny_w30'])
 for name,pin in meta['source_files'].items():assert sha((RAW.parent/name).read_bytes())==pin,name
 roots=E['parse_fbx'](RAW/'Null Composure.fbx')
 objects=next(r[2] for r in roots if r[0]=='Objects')
 links=[c[1][1:] for r in roots if r[0]=='Connections' for c in r[2] if c[1][0]=='OO']
 models={o[1][0]:o for o in objects if o[0]=='Model'}
 b=L['Blend'](RAW/'Null Composure.blend');blend={}
 for _,o in b.records('Object'):
  name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
  if b.field(o,'Object','type')!=1:raise ValueError('Unexpected nonmesh '+name)
  matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
  mesh=b.pointed(b.field(o,'Object','data'));nv=b.field(mesh,'Mesh','totvert')
  vs=np.ndarray((nv,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
  world=(np.c_[vs,np.ones(nv)]@matrix)[:,:3]
  blend[name]=dict(matrix=matrix,world=world,triangles=b.field(mesh,'Mesh','totpoly'))
 assert set(blend)==set(meta['source_objects']+meta['excluded_objects'])
 meshes=[];audit=[]
 for o in objects:
  if o[0]!='Geometry':continue
  model=models[next(p for c,p in links if c==o[1][0])];name=model[1][1].split('\x00')[0]
  assert name in blend,name
  props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
  np.testing.assert_allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
  assert props['Lcl Scaling']==[100,100,100]
  cs={c[0]:c for c in o[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
  # FBX is centimeters, rotated -90 around X; convert world back to Blender basis.
  r=H['rotation'](dict(x=props['Lcl Rotation'][0],y=0,z=0))
  fbx_world=raw@r.T*100+props['Lcl Translation']
  world=np.c_[fbx_world[:,0],-fbx_world[:,2],fbx_world[:,1]]/100
  np.testing.assert_allclose(world,blend[name]['world'],atol=1.5e-7,rtol=0)
  ix=np.array(cs['PolygonVertexIndex'][1][0]);assert len(ix)%3==0 and np.all(ix[2::3]<0)
  faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
  assert len(faces)==blend[name]['triangles']
  status='retained' if name in meta['source_objects'] else 'excluded_reticle'
  audit.append(dict(name=name,status=status,vertices=len(raw),triangles=len(faces),fbx_properties=props,
   blend_matrix=blend[name]['matrix'].tolist(),world_bounds=[world.min(0).tolist(),world.max(0).tolist()]))
  if status!='retained':continue
  uv_layer=next(c for c in o[2] if c[0]=='LayerElementUV' and c[1][0]==0)
  uvdata={c[0]:c[1][0] for c in uv_layer[2]}
  assert uvdata['MappingInformationType']=='ByPolygonVertex' and uvdata['ReferenceInformationType']=='IndexToDirect'
  uv=np.array(uvdata['UV']).reshape(-1,2)[np.array(uvdata['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
  native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
  meshes.append(dict(name=name,vertices=native,world=world,faces=faces,uv=uv))
 assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
 assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==meta['textured_triangles']==15171
 points=np.concatenate([m['vertices'] for m in meshes]);world=np.concatenate([m['world'] for m in meshes])
 np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=5e-6,rtol=0)
 np.testing.assert_allclose([world.min(0),world.max(0)],meta['source_bounds'],atol=1.5e-7,rtol=0)
 meta.update(raw_fbx_triangles=sum(x['triangles'] for x in audit),object_audit=audit,
  mapping='FBX model scale/rotation/translation -> [world.X,-world.Z,world.Y]/100 -> Blender; native=[Blender.X,Blender.Z,Blender.Y]*scale+anchor',
  retained_textured_triangles=15171,excluded_reticle_triangles=244)
 ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
 assert sha(PHOTO.read_bytes())==ref['sha256']
 return meshes,meta,ref

def source_triangles(ms):
 tex=np.asarray(Image.open(RAW/'NCFrame_Diffuse.png').convert('RGBA'));ts=[]
 for m in ms:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
   if length>1e-12:ts.append((p,uv,tex,n/length))
 return ts

def make_design(meta,ref):
 parts=[]
 def box(group,name,c,size,mat,motif='',angles=(0,0,0)):
  c=np.array(c,float);s=np.array(size,float)
  parts.append(dict(group=group,material=mat,motif=motif,kind='filled_solid',geometry=dict(name=name,
   **{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()},
   rotation=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles))))))
 def beam(group,name,a,b,width,depth,mat,motif=''):
  a=np.array(a,float);b=np.array(b,float);v=b-a;assert abs(v[0])<1e-8
  box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,(round(math.degrees(math.atan2(v[2],v[1])),6),0,0))
 def cylinder(group,name,y,z0,z1,r,mat,motif='',x=8):
  # Four overlapping filled rectangles produce a convex solid octagonal section.
  for i in range(4):box(group,f'{name}_facet_{i}',[x,y,(z0+z1)/2],
   [2*r*math.cos(math.pi/8),2*r*math.sin(math.pi/8),z1-z0],mat,motif,(0,0,i*45))
 def tube(group,name,y,z0,z1,r,t,mat):
  for i in range(8):
   a=i*45;q=math.radians(a)
   box(group,f'{name}_wall_{i}',[8+(r-t/2)*math.cos(q),y+(r-t/2)*math.sin(q),(z0+z1)/2],
    [2*r*math.tan(math.pi/8)+.012,t,z1-z0],mat,'rim',(0,0,a-90))
 # The shroud is a solid vaulted top with thick structural sides, not alpha plates.
 box('receiver','Shroud_vault',[8,12.72,-5.44],[1.63,.70,9.98],'silver','shroud')
 for side in (-1,1):
  box('receiver',f'Shroud_upper_chamfer_{side}',[8+side*.82,12.72,-5.44],[.36,.36,9.98],'silver','shroud',(0,0,side*45))
  box('receiver',f'Shroud_rear_cheek_{side}',[8+side*.82,11.74,-2.08],[.36,1.45,2.50],'silver','crest')
  beam('receiver',f'Shroud_nose_drop_{side}',[8+side*.81,12.60,-10.29],[8+side*.81,11.15,-9.73],.37,.48,'silver','shroud')
  beam('receiver',f'Shroud_aft_drop_{side}',[8+side*.82,12.70,-1.0],[8+side*.82,10.60,-.30],.34,.66,'silver','crest')
 box('receiver','Shroud_lower_aft_core',[8,10.74,-1.30],[1.92,.43,2.55],'black','lower')
 box('receiver','Front_shroud_bridge',[8,12.08,-10.42],[1.90,1.90,.29],'silver','nose')
 cylinder('capacitor','Blue_capacitor',11.65,-9.88,-3.86,.56,'blue','capacitor')
 cylinder('capacitor','Capacitor_socket',11.65,-4.05,-3.67,.60,'recess','socket')
 box('capacitor','Capacitor_lower_gold_rail',[8,10.98,-6.72],[1.46,.13,5.64],'gold','trim')
 for side in (-1,1):
  box('receiver',f'Shroud_latch_{side}',[8+side*1.02,12.69,-9.86],[.13,.15,.66],'black','latch')
 # Deep lower forearm: continuous angled support, cheek thickness from source.
 beam('forearm','Underbarrel_core',[8,10.45,-10.65],[8,9.92,-4.46],1.64,.78,'black','forearm')
 box('forearm','Underbarrel_spine',[8,10.89,-7.55],[1.66,.21,6.38],'steel','rail')
 for side in (-1,1):
  beam('forearm',f'Forearm_lower_chamfer_{side}',[8+side*.68,10.06,-10.45],[8+side*.68,9.56,-4.55],.29,.31,'black','forearm')
 box('forearm','Underbarrel_front_hook',[8,10.10,-10.92],[1.37,.31,.56],'black','hook')
 box('frame','Receiver_lower_bridge',[8,10.48,-.31],[1.70,.61,7.06],'black','frame')
 box('frame','Battery_keel_solid',[8,7.48,.27],[1.47,6.75,3.24],'black','battery')
 box('frame','Battery_blue_spine',[8,7.29,-1.38],[1.56,6.24,.18],'blue','battery_edge')
 beam('frame','Keel_forward_diagonal_web',[8,10.10,-4.35],[8,8.30,-1.25],1.49,1.55,'black','battery_web')
 box('frame','Keel_upper_web_fill',[8,10.03,-2.11],[1.48,.96,3.34],'black','battery_web')
 box('frame','Battery_heel',[8,4.26,.27],[1.58,.30,3.31],'steel','heel')
 # Exposed rear breech, separated rail, source-matched rear buffer and butt.
 cylinder('breech','Blue_breech',11.64,-.69,1.78,.61,'blue','breech')
 cylinder('breech','Rear_buffer',11.94,1.75,11.42,.37,'silver','buffer')
 box('stock','Rear_lower_blue_rail',[8,10.61,6.50],[1.34,.47,9.73],'blue','stock_rail')
 box('stock','Rear_gold_web',[8,11.16,6.55],[.96,.70,9.62],'black','stock_web')
 box('stock','Breech_lower_mount',[8,10.80,2.29],[1.41,.77,1.27],'steel','rail')
 box('stock','Upper_blue_breech_rail',[8,12.69,1.68],[1.23,.34,4.78],'bluebright','rail')
 beam('stock','Upper_rail_taper',[8,12.82,2.23],[8,12.47,4.77],1.08,.21,'bluebright','rail')
 beam('stock','Rear_shoulder_diagonal',[8,10.95,10.44],[8,9.23,11.39],1.32,.46,'gold','trim')
 beam('stock','Butt_heel_pad',[8,12.24,11.64],[8,8.54,11.64],1.44,.42,'rubber','pad')
 box('stock','Butt_upper_cap',[8,12.20,11.52],[1.52,.31,.61],'steel','trim')
 # Grip remains in canonical hand region, with real trigger and thumb openings.
 box('grip','Grip_root',[8,10.24,4.78],[1.26,.76,1.33],'black','grip')
 beam('grip','Grip_main',[8,10.04,4.62],[8,7.12,6.02],1.22,1.24,'rubber','grip')
 beam('grip','Grip_front_strap',[8,9.99,4.06],[8,7.07,5.47],1.07,.22,'black','grip')
 beam('grip','Grip_backstrap',[8,10.01,5.24],[8,7.13,6.59],1.12,.20,'black','grip')
 beam('grip','Grip_heel',[8,7.13,5.24],[8,6.92,6.78],1.33,.25,'rubber','heel')
 beam('guard','Open_frame_lower_brace',[8,5.67,1.85],[8,6.97,6.76],1.18,.37,'black','brace')
 beam('guard','Trigger',[8,10.21,3.57],[8,9.22,3.48],.20,.19,'steel','trigger')
 box('grip','Grip_gold_heel_tag',[7.39,6.99,6.30],[.08,.15,.30],'gold','trim')
 # Real recessed bore; blue breech insert is surrounded by solid silver rails.
 tube('muzzle','Muzzle_bore',11.78,-13.097119,-12.54,.72,.17,'silver')
 cylinder('muzzle','Bore_backstop',11.78,-12.39,-12.20,.52,'recess')
 cylinder('muzzle','Blue_muzzle_insert',11.78,-12.20,-10.52,.43,'blue','muzzle_insert')
 for side in (-1,1):
  box('muzzle',f'Muzzle_upper_jaw_{side}',[8+side*.45,12.30,-11.49],[.43,.28,2.20],'silver','muzzle')
  box('muzzle',f'Muzzle_lower_jaw_{side}',[8+side*.45,11.25,-11.49],[.43,.25,2.20],'silver','muzzle')
 # Photo-specific open reflex hood: no opaque lens slab or alternate reticle stack.
 box('sight','Reflex_mount',[8,13.18,.38],[1.16,.30,2.91],'black','rail')
 for z in (-.63,1.36):box('sight',f'Reflex_gold_foot_{z}',[8,13.42,z],[1.32,.22,.48],'gold','trim')
 box('sight','Reflex_sill',[8,13.62,.48],[1.30,.18,2.09],'black','optic')
 for side in (-1,1):
  box('sight',f'Reflex_lower_hood_{side}',[8+side*.64,13.95,.48],[.19,.55,2.18],'black','optic')
  beam('sight',f'Reflex_arch_{side}',[8+side*.54,14.13,.61],[8+side*.54,14.67,.83],.20,.27,'silver','optic')
 box('sight','Reflex_roof',[8,14.72,.80],[1.16,.20,1.18],'silver','optic')
 box('sight','Reflex_rear_hood',[8,14.65,1.42],[1.22,.15,.15],'steel','optic')
 # The dial genuinely protrudes and defines the silhouette in the source photo.
 for i in range(4):
  box('sight',f'Reflex_dial_facet_{i}',[7.20,13.98,.32],[.31,2*.24*math.cos(math.pi/8),2*.24*math.sin(math.pi/8)],'steel','dial',(i*45,0,0))
 inputs=[BASE,SOURCE,REFS,'scripts/generate_surface_w123_beloved.py','scripts/generate_surface_w123_erentil_fr4.py','scripts/generate_surface_w123_long_arm.py',ASSET+'textures/item/weapon/w30/null_composure.png']
 inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT/BASE).parent.glob('null_composure_*.json'))]
 return dict(id=ID,stage='W144',family='fusion_rifle',revision='semantic-r1',source=meta,reference=ref,
  anchor=meta['anchor'],scale=meta['scale'],coordinate_mapping=meta['mapping'],palette=PALETTE,
  method='Hand-authored filled semantic solids and authored opaque per-face UV; no source islands, voxels, alpha body cards or arbitrary triangle fields.',
  starting_draft='80-120 element blockout, including octagonal solid sections, open muzzle and reflex hood.',
  full_only=True,frame_policy='Original source scale/anchor, grip frame and exact canonical display; ADS/twohand/charge/reload/timings/audio untouched.',
  parts=parts,groups=dict(collections.Counter(s['group'] for s in parts)),max_assembled_elements=1000,
  required_air_probes=dict(open_grip_frame=[8,7.8,3.1],trigger_space=[8,9.55,3.95],bore_entry=[8,11.78,-12.95],bore_depth=[8,11.78,-12.65],reflex_window=[8,14.40,.32],rear_stock_undercut=[8,9.5,8]),
  contact_probes=dict(grip=[8,8.40,5.40],battery=[8,6.3,.35],shroud=[8,12.75,-6],lower_brace=[8,6.3,4.3],buffer=[8,11.94,8]),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
  raw_input_sha256={str(p):sha(p.read_bytes()) for p in sorted(RAW.rglob('*')) if p.is_file()}|{str(PHOTO):sha(PHOTO.read_bytes())},
  limitations=['Static authored opaque materials, not recovered PBR/refraction.','Small reverse-side markings without photo evidence omitted.','Faceted circular sections; exact source triangulation deliberately redesigned.','Native resource loading/held views/ADS/reload/fusion charge/audio/10-20 displays pending master.'])

def face_points(e,face):return vertices(e)[list(FACES[face])]
def tile(spec,face,w,h):
 base=np.array(PALETTE[spec['material']],float);yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
 a=np.zeros((h,w,4),np.uint8);a[:,:,3]=255
 a[:,:,:3]=np.clip(base[None,None,:]*(.97+.03*np.sin(v*np.pi))[:,:,None],0,255)
 p=face_points(spec['geometry'],face);world=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0]);X,Y,Z=(world[:,:,i] for i in range(3))
 motif=spec['motif'];side=face in ('west','east');cyl='_facet_' in spec['geometry']['name']
 if cyl and face in ('north','south'):a[:,:,:3]=base
 elif spec['material'] not in ('recess','rubber'):
  a[0,:,:3]=np.minimum(base+18,255);a[-1,:,:3]=base*.78
 if side and motif in ('shroud','crest','forearm','battery','battery_web','stock_rail','stock_web','grip'):
  edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);a[(edge>1)&(edge<2),:3]=base*.65
 # Restrained, supported material lines instead of stochastic grunge.
 if motif=='shroud' and side:
  a[abs(Y-12.60)<.018,:3]=[101,118,127]
 if motif=='crest' and side:
  diamond=abs((Z+1.56)/.46)+abs((Y-12.10)/.49)
  a[abs(diamond-1)<.065,:3]=PALETTE['gold']
  for z,y in ((-1.73,12.19),(-1.41,12.19),(-1.57,11.94)):
   q=((Z-z)/.065)**2+((Y-y)/.12)**2
   a[(q>.56)&(q<1.1),:3]=PALETTE['gold']
  vents=(Z>-.85)&(Z<-.05)&(Y>11.48)&(Y<11.71)&(np.mod(Z,.105)<.043)
  a[vents,:3]=PALETTE['recess']
 if motif=='nose' and side:
  a[(Z<-10.30)&(Y>11.56)&(Y<11.76),:3]=PALETTE['gold']
  a[(Z<-10.30)&(Y>11.58)&(Y<11.74)&(np.mod(Z,.06)<.026),:3]=[80,83,72]
 if motif in ('capacitor','breech','muzzle_insert','buffer'):
  if motif=='capacitor':
   # Actual repeated gold cartridge outlines in the blue side cylinder.
   for z in (-8.58,-6.69,-4.79):
    q=((Z-z)/.24)**2+((Y-11.64)/.115)**2
    a[(q>.72)&(q<1.20)&(abs(X-8)>.28),:3]=[163,137,53]
    a[(abs(Z-z-.13)<.022)&(abs(Y-11.64)<.105)&(abs(X-8)>.28),:3]=[164,139,56]
  for z in ((-.40,.68,1.58) if motif=='breech' else (-12.15,-11.93,-10.81,2.01,10.98)):
   a[abs(Z-z)<.034,:3]=base*.43
   a[(Z-z>.039)&(Z-z<.067),:3]=np.minimum(base+23,255)
 if side and motif in ('battery','battery_web','forearm'):
  # Photo's circular perforation field is UV only; large battery stays solid.
  dots=(np.mod(Z+.10,.245)-.1225)**2+(np.mod(Y,.245)-.1225)**2
  mask=(dots<.004)&(Y>6.4)&(Y<8.38)&(Z>-.16)&(Z<1.41)
  if motif=='battery':a[mask,:3]=[79,86,87]
  if motif in ('forearm','battery_web'):a[(dots>.004)&(dots<.005)&(Y>9.7)&(Y<10.6),:3]=[43,48,49]
  if motif=='battery':
   stripe=(Y>4.95)&(Y<6.78)&(Z>.92)&(Z<1.45)&(Y>5.10+(Z-1.02)*1.7)
   a[stripe,:3]=PALETTE['gold']
 if motif=='battery_edge':a[(abs(X-8)>.63),:3]=[48,126,171]
 if motif=='stock_rail' and side:
  a[abs(Y-10.65)<.041,:3]=[105,162,192];a[abs(Y-10.46)<.025,:3]=[10,40,58]
 if motif=='latch' and face=='up':a[:,:,:3]=PALETTE['gold']
 if motif=='stock_web' and side:
  a[(Z>8.10+(Y-10.8)*1.15),:3]=PALETTE['gold']
  holes=(np.mod(Z,.32)-.16)**2+(np.mod(Y,.24)-.12)**2
  a[(Z>9)&(Y>11.05)&(holes<.003),:3]=[36,37,29]
 if motif in ('grip','pad'):
  # Fine regular grip ribs only, no random surface noise.
  a[(np.mod(Y+.25*Z,.16)<.022),:3]=[36,40,42]
 if motif=='brace' and side:a[abs(Y-(5.67+(Z-1.85)*1.30/4.91))<.035,:3]=[58,64,66]
 if motif=='optic':
  a[0,:,:3]=[147,160,166]
  if side and face=='west':
   q=np.hypot(Z-.30,Y-13.99);a[(q>.12)&(q<.18),:3]=[114,127,133]
 if motif=='dial':
  a[(np.mod(Z,.09)<.025),:3]=base*.55
 return Image.fromarray(a)

def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(19,25,29,255));requests=[]
 for s in d['parts']:
  s['geometry']['faces']={}
  for f in FACES:
   p=face_points(s['geometry'],f);density=23 if s['motif'] in ('crest','capacitor','battery') else 16
   w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
   requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[]
 for h,w,name,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  if y+h+2>EDGE:raise ValueError('UV atlas overflow')
  im=tile(s,f,w,h);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  s['geometry']['faces'][f]=dict(uv=[v*16/EDGE for v in (x,y,x+w,y+h)],texture='#0')
  ledger.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
 d['atlas']=dict(size=EDGE,gutter=2,islands=ledger,used_height=y+row+2)
 model=dict(credit='W144 Null Composure / authored semantic solid volumes + default-photo face UV / offline candidate',
  textures={'0':'destiny:item/weapon/w123/null_composure','particle':'destiny:item/weapon/w123/null_composure'},
  elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])
 assert len(model['elements'])<=1000
 return atlas,model

def inspection(d,atlas,model):
 es=[];groups=collections.defaultdict(list)
 for s,e in zip(d['parts'],model['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation');b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
  for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
  es.append(b);groups[s['group']].append(b['uuid'])
 return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Null Composure W144 / editable offline solids',
  resolution={'width':EDGE,'height':EDGE},elements=es,
  outliner=[dict(name=n,uuid=uid('group:'+n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],
  textures=[dict(name='null_composure.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
  display=model['display'],destiny_w144=dict(nativeAccepted=False,sourceAnchor=d['anchor'],sourceScale=d['scale'],fullOnly=True))

def comparison(d,ms,atlas,model):
 w,h=800,355;out=Image.new('RGB',(2400,2000),'#151e27');draw=ImageDraw.Draw(out)
 def label(x,y,s,size=21):draw.text((x,y),s,fill='#e2eaf0',font_size=size)
 label(20,14,'NULL COMPOSURE / W144 / SILVER SHROUD + BLUE CAPACITOR + OPEN FRAME',29)
 photo=Image.open(PHOTO).convert('RGB').crop((565,180,1870,880));photo.thumbnail((1260,470));out.paste(photo,(20,55))
 label(1270,85,'ACTUAL DEFAULT-DYE PHOTO',25)
 label(1270,130,'Raw FBX + compressed BLEND match W30: 15,171 retained triangles')
 label(1270,166,'244 alternate reticle triangles separately excluded by W30')
 label(1270,214,f'NEW: {len(model["elements"])} solid cubes / 0 emitted triangles / opaque face UV')
 label(1270,255,'Source scale, anchor, held frame and full display preserved')
 label(1270,296,'OFFLINE CPU views; native acceptance remains pending master')
 label(20,540,'ORIGINAL RIP / original UV + neutral diffuse')
 label(w+20,540,'CANONICAL W30 / 211 cubes / read only')
 label(2*w+20,540,f'W144 / {len(model["elements"])} AUTHORED SOLIDS / default paint')
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/null_composure.png'))
 ts=[source_triangles(ms),triangles(old,oldtex),triangles(model,atlas)]
 points=np.concatenate([m['vertices'] for m in ms]+[vertices(e) for e in model['elements']]);d['comparison_views']=[]
 for row,(name,cam) in enumerate([('SIDE',[-1,0,0]),('FRONT OBLIQUE',[-1,.47,-.55]),('REAR / HOLDING AXIS',[1,.28,.85])]):
  extent=H['frame'](points,cam,w,h);d['comparison_views'].append(dict(name=name,camera=cam,center=extent[0].tolist(),scale=extent[1],viewport=[w,h]))
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,extent,(w,h),raw=col==0);out.paste(im,(col*w,580+row*h));label(col*w+14,590+row*h,name,17)
 for col,(title,groups,cam) in enumerate([('MUZZLE / RECESSED BORE',('muzzle',),[-.45,.2,-1]),('REFLEX / OPEN WINDOW',('sight',),[-.30,.12,-1]),('GRIP / BATTERY / REAL AIR',('grip','guard','frame'),[-1,.24,.24])]):
  names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups};es=[e for e in model['elements'] if e['name'] in names]
  ps=np.concatenate([vertices(e) for e in es]);im,_=H['render'](triangles(dict(elements=es),atlas),cam,H['frame'](ps,cam,w,285),(w,285));out.paste(im,(col*w,1670));label(col*w+14,1680,title,18)
 label(20,1970,'Same camera/scale per full row. Static authored opaque finish, no native game screenshot or recovered PBR claim.',18)
 return png(out)

def review_text(d,model):
 n=len(model['elements'])
 return f"""# Null Composure W144 — offline art review

Actual default-dye photograph `{PHOTO}` was opened and used alongside the original rip under `{RAW}`. Photo SHA-256 `{d['reference']['sha256']}`. Bungie weapon hash 1644680957. Identity retained: silver vaulted forward shroud, blue capacitors and breech, black hanging battery keel, gold cartridge/emblem trim, exposed rear buffer, diagonal lower open grip frame and one open reflex hood. No unrelated weapon identity is copied.

{n} filled semantic cuboids, zero triangle adapter elements, {n*6} explicit opaque face UVs on a 1024 atlas. Draft began in the 80–120 range. Four filled intersecting rectangular prisms per cylinder give an octagonal solid cross section; eight structural muzzle walls preserve the actual bore. Receiver, forearm, keel and grip have real width. Shroud sides are structural blocks around a solid capacitor, not alpha plates. Perforation dots, small vents, cartridge outlines, gold crest and shallow seams are authored UV, without random noise or tiny decal cubes. Open grip frame, trigger space, reflex window, muzzle depth and rear stock undercut remain real air.

Source audit: inert binary FBX 7400/7500 reader from Erentil and compressed Blender 3.1 SDNA reader from Long Arm, read only. All 3 named mesh objects are accounted for: 1,746 Decal + 13,425 Frame = 15,171 retained/textured; 244 alternate reticle triangles excluded exactly as W30 metadata. FBX model rotation/scale/translation is applied, then converted from centimeters to Blender frame. Corresponding FBX and BLEND vertices agree within 1.5e-7 source units; source/native bounds agree within export precision. The longitudinal Blender translation is -0.08916319906711578; mapping is independently verified, not copied from Erentil. Original rip files (including inert shaders/scripts) are hash pinned and never executed or changed. Original UV + neutral diffuse appears in the first comparison column; it is not the default shader/PBR finish.

Source scale `{d['scale']}`, anchor `{d['anchor']}`, negative native Z muzzle and grip frame retained. Canonical full display is copied exactly. The only candidate resource is `{MODEL}`. Full-only output needs no custom reload split. ADS, twohand, charging, generic reload, timings, sounds and shared registries/HUD are outside this worker's mutation scope. Shared migration manifest is not pinned.

`comparison.png` shows actual photo, original textured rip, unchanged W30 and new solids in side/front/rear views with common cameras; detail panels inspect muzzle/reflex/grip depth. `inspection.bbmodel` embeds the final editable solids, face UVs, group names and atlas. These are offline CPU inspection images, not game screenshots. Deterministic `--verify` reproduces all seven generated artifacts, including comparison and BB. Targeted tests and export status are in the worker report.

Caveats: circular parts are intentionally faceted. The static authored palette simplifies the default reflective finish; no dynamic reflection, transparency/refraction or recovered PBR. Small unobserved reverse-side markings are omitted. Native parser/pack loading, first/third-person hand contact, ADS and twohand sight visibility, charge/fire, generic reload return/ammo/timing, sound and 10–20 simultaneous displays remain pending master.
"""

def generate():
 ms,meta,ref=source_meshes();d=make_design(meta,ref);atlas,model=compile_model(d)
 comp=comparison(d,ms,atlas,model);bb=inspection(d,atlas,model)
 products={MODEL:encode(model),TEXTURE:png(atlas),ART+'design.json':encode(d),ART+'inspection.bbmodel':encode(bb),ART+'comparison.png':comp,ART+'review.md':review_text(d,model).encode()}
 n=len(model['elements']);pts=np.concatenate([vertices(e) for e in model['elements']])
 manifest=dict(id=ID,stage='W144',family='fusion_rifle',model='destiny:weapon_surface_w123/null_composure',
  counts=dict(full=n,cubes=n,triangle_adapter_elements=0,assembled_emitted=n,faces=n*6),groups=d['groups'],
  bounds=[pts.min(0).round(6).tolist(),pts.max(0).round(6).tolist()],atlas=dict(width=EDGE,height=EDGE,opaque=True,explicit_face_islands=n*6),
  full_only=True,native_accepted=False,source_reference=ref,source_triangle_accounting=dict(raw=15415,retained=15171,textured=15171,excluded_reticle=244),
  input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],outputs={p:sha(b) for p,b in products.items()},
  native_pending=['resource parser/pack load','first/third person hand contact','ADS/twohand sight visibility','fusion charging/fire/muzzle','generic reload return/ammo/timings','weapon audio','10-20 simultaneous displays'])
 products[ART+'manifest.json']=encode(manifest)
 return products

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();outputs=generate()
 if a.verify:
  bad=[p for p,b in outputs.items() if not (ROOT/p).is_file() or (ROOT/p).read_bytes()!=b]
  if bad:raise SystemExit('Deterministic mismatch: '+', '.join(bad))
  print(f'PASS deterministic --verify: {len(outputs)} products including BB/comparison')
 else:
  for p,b in outputs.items():q=ROOT/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
  print(json.dumps(json.loads(outputs[ART+'manifest.json'])['counts'],sort_keys=True));print(f'Wrote {len(outputs)} owned products')
if __name__=='__main__':main()
