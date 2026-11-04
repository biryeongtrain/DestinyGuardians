#!/usr/bin/env python3
"""W149 Dimensional Hypotrochoid: semantic solids / authored opaque face UV.
Only inert FBX arrays are read. No Blender scripts, shaders or native clients.
"""
import argparse, base64, copy, hashlib, io, json, math, runpy, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='dimensional_hypotrochoid'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/heavy_grenade_launcher/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w149_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w149/{ID}-worker.md'
BATCH='docs/qa/2026-10-26/w149/batch.json'
REFS='art/weapons/w31/references.json'
HELPER='scripts/generate_surface_w123_beloved.py'
RAW=Path('/tmp/destiny-weapons-w30/raw/dimensional_hypotrochoid/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/dimensional_hypotrochoid.jpg')
H=runpy.run_path(str(ROOT/HELPER));FACES=H['FACES'];EDGE=1024
PALETTE=dict(cyan=[153,202,213],silver=[176,188,199],edge=[111,135,155],
    graphite=[39,46,59],navy=[25,51,85],rubber=[21,26,34],black=[12,17,24],
    violet=[69,36,106],magenta=[233,79,235],pink=[251,153,248],pin=[204,247,246])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w149:'+ID+':'+n))
def render_element(e):
 e=copy.deepcopy(e)
 if 'rotation' in e:
  r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return e
def vertices(e):return H['vertices'](render_element(e))
def model_triangles(m,tex):
 m=copy.deepcopy(m);m['elements']=[render_element(e) for e in m['elements']]
 return H['model_triangles']({'full':m},tex)

def source_meshes():
 meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
 assert meta['source_axis']==dict(length=0,thin=1,muzzle_sign=1)
 for name,digest in meta['source_files'].items():assert sha((RAW/name).read_bytes())==digest
 roots=H['parse_fbx'](RAW/'Dimensional Hypotrochoid.fbx')
 objects=next(n[2] for n in roots if n[0]=='Objects')
 links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
 models={n[1][0]:n for n in objects if n[0]=='Model'}
 materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
 meshes=[]
 for node in objects:
  if node[0]!='Geometry':continue
  mid=next(p for c,p in links if c==node[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
  if name not in meta['source_objects']:continue
  assert next(p for c,p in links if c==mid)==0,'Unexpected FBX parent'
  props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
  cs={c[0]:c for c in node[2]};local=np.array(cs['Vertices'][1][0]).reshape(-1,3)
  # FBX XYZ local rotation and centimeters -> Blender raw Z-up meters.
  R=H['rotation'](dict(zip('xyz',props.get('Lcl Rotation',[0,0,0]))))
  fbx=(local*np.array(props.get('Lcl Scaling',[1,1,1])))@R.T+props.get('Lcl Translation',[0,0,0])
  world=fbx[:,[0,2,1]]*[1,-1,1]/100
  # Metadata length=X, thin=Y, positive source muzzle -> native -Z.
  v=world[:,[1,2,0]]*[-1,1,-1]*meta['scale']+meta['anchor']
  faces=[];face=[]
  for i in cs['PolygonVertexIndex'][1][0]:
   face.append(i if i>=0 else -i-1)
   if i<0:
    assert len(face)==3;faces.append(face);face=[]
  layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
  vals={c[0]:c[1][0] for c in layer[2]}
  assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
  uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
  mat=next(materials[c] for c,p in links if p==mid and c in materials)
  meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=mat,
    object_transform=props,world_bounds=[world.min(0).tolist(),world.max(0).tolist()]))
 points=np.concatenate([m['vertices'] for m in meshes]);bounds=np.array([m['world_bounds'] for m in meshes])
 assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
 assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==15434
 np.testing.assert_allclose([bounds[:,0].min(0),bounds[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
 np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=3e-6,rtol=0)
 return meshes,meta

def source_triangles(meshes):
 textures={m['material']:np.asarray(Image.open(RAW/(m['material']+'_Diffuse.png')).convert('RGBA')) for m in meshes};out=[]
 for m in meshes:
  for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
   if length>1e-10:out.append((ps,uv,textures[m['material']],n/length))
 return out

def make_design(meta,meshes):
 parts=[]
 def box(name,lo,hi,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':lo,'to':hi})
  if turn:e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def c(name,pos,size,mat,group,motif='plain',turn=None):
  box(name,[round(a-b/2,7) for a,b in zip(pos,size)],[round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
 def beam(name,a,b,width,depth,mat,group,motif='plain'):
  angle=-math.degrees(math.atan2(b[1]-a[1],b[2]-a[2]))
  if angle>90:angle-=180
  if angle< -90:angle+=180
  c(name,[(x+y)/2 for x,y in zip(a,b)],[width,depth,math.hypot(b[1]-a[1],b[2]-a[2])],mat,group,motif,('x',angle))
 def tube(name,x,y,z0,z1,r,t,mat,group,motif='rim'):
  for i in range(8):
   a=i*45;q=math.radians(a);rr=r-t/2
   c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
     [2*r*math.tan(math.pi/8)+.006,t,z1-z0],mat,group,motif,('z',a))
 zmin=meta['model_bounds'][0][2];zmax=meta['model_bounds'][1][2]
 # Deep fore casing around an actual axial bore, not alpha skins.
 box('fore_crown',[7.21,12.08,zmin],[8.79,13.30,.46],'cyan','fore','flow')
 box('fore_keel',[7.24,10.28,zmin+.12],[8.76,10.69,.48],'graphite','fore','vent')
 for side in (-1,1):
  x=8+side*.65
  c(f'fore_wall_{side}',[x,11.37,-4.36],[.30,1.48,9.16],'graphite','fore','flow')
  c(f'fore_shoulder_{side}',[8+side*.69,12.07,-4.31],[.27,.27,9.19],'cyan','fore','flow',('z',side*45))
 tube('bore',8,11.35,zmin+.04,-.15,.68,.16,'graphite','muzzle','bore')
 tube('muzzle_lip',8,11.35,zmin,zmin+.18,.75,.14,'silver','muzzle','bore')
 c('bore_stop',[8,11.35,-.06],[1.08,1.08,.12],'black','muzzle')
 # Lower mounting hardware and the narrow crown slots are real depth changes.
 box('front_underrail',[7.31,9.82,-7.49],[8.69,10.40,-.08],'navy','lower','hardware')
 c('front_rail_seat',[8,10.17,-3.90],[1.67,.25,7.65],'edge','lower','hardware')
 for z in (-7.9,-4.45,-.80):c(f'fore_crown_segment_{z}',[8,13.33,z],[1.40,.16,2.66],'silver','fore','crown')
 # Continuous rear spine and photo's open lower stock frame.
 box('central_crown',[7.19,12.16,.44],[8.81,13.30,5.49],'cyan','receiver','flow')
 c('central_crown_cap',[8,13.33,3.0],[1.42,.15,3.13],'silver','receiver','crown')
 box('rear_crown',[7.18,12.13,5.45],[8.82,13.30,15.58],'cyan','receiver','flow')
 box('rear_dark_spine',[7.19,11.17,5.65],[8.81,12.13,15.54],'graphite','receiver','electronics')
 box('rear_lower_spine',[7.28,10.12,5.62],[8.72,10.65,11.35],'navy','receiver','hardware')
 for z in (7.0,10.1,13.2):c(f'rear_crown_segment_{z}',[8,13.32,z],[1.43,.15,2.64],'silver','receiver','crown')
 box('butt_vertical',[7.15,8.15,15.48],[8.85,13.29,zmax],'silver','stock','butt')
 box('butt_rubber',[7.21,8.10,15.79],[8.79,13.21,zmax],'violet','stock','butt')
 box('stock_lower_bridge',[7.28,8.62,11.25],[8.72,9.04,15.54],'silver','stock','hardware')
 box('stock_front_post',[7.29,8.75,11.12],[8.71,11.22,11.52],'graphite','stock','hardware')
 # Photo has a real inset silver equipment plate suspended in the stock frame.
 box('stock_equipment',[7.34,9.08,12.00],[8.66,10.75,15.22],'silver','stock','equipment')
 for side in (-1,1):
  c(f'stock_inset_{side}',[8+side*.69,9.89,13.62],[.15,1.72,3.68],'graphite','stock','equipment')
 # Large lateral magazine: four intersecting filled octagonal prisms.
 cy,cz=10.16,2.60;r=2.10
 for i in range(4):c(f'drum_solid_{i}',[8.026,cy,cz],[4.24,2*r,2*r*math.tan(math.pi/8)],'graphite','drum','drum_end',('x',i*45))
 # Structural facets around that solid core; no per-source island copying.
 for i in range(8):
  a=i*45;q=math.radians(a)
  c(f'drum_jacket_{i}',[8.026,cy+(r-.04)*math.cos(q),cz+(r-.04)*math.sin(q)],
    [4.30,.17,1.72],'silver' if i in (0,1,7) else 'graphite','drum','drum_jacket',('x',a))
 # The prominent static silver side latch belongs to the retained body object.
 box('latch_root',[4.52,9.30,.57],[6.12,10.25,5.47],'graphite','latch','latch')
 box('latch_handle',[meta['model_bounds'][0][0],9.62,.79],[4.62,10.27,5.27],'silver','latch','handle')
 for z in (.84,5.14):c(f'latch_return_{z}',[5.02,9.94,z],[1.42,.65,.48],'silver','latch','handle')
 beam('latch_top_slope',[5.62,10.31,.95],[5.62,12.21,1.42],.46,.42,'silver','latch','latch')
 box('latch_upper_panel',[5.02,10.34,1.36],[6.12,12.03,5.07],'silver','latch','latch')
 c('latch_upper_rear',[5.59,11.45,5.19],[.49,1.10,.43],'edge','latch','latch',('x',-20))
 c('right_latch',[10.34,10.25,2.63],[.70,.77,2.74],'edge','latch','handle')
 # Fore grip is solid, below the observed mounting frame.
 box('foregrip_socket',[7.30,9.32,-4.25],[8.70,10.10,-2.70],'navy','foregrip','hardware')
 beam('foregrip',[8,9.35,-3.40],[8,6.48,-2.01],1.02,.94,'rubber','foregrip','maze')
 c('foregrip_heel',[8,6.25,-1.94],[1.10,.46,1.01],'navy','foregrip','maze',('x',17.6))
 # Skeletal rear grip: a substantial open frame with genuine lattice air.
 box('pistol_socket',[7.34,9.52,8.12],[8.66,10.30,10.40],'navy','grip','hardware')
 beam('grip_front',[8,9.55,8.78],[8,6.90,7.94],.79,.24,'navy','grip','gripframe')
 beam('grip_back',[8,9.42,10.15],[8,7.04,9.48],.79,.26,'navy','grip','gripframe')
 beam('grip_heel',[8,6.90,7.94],[8,7.04,9.48],.83,.28,'navy','grip','gripframe')
 for i in range(4):
  y=7.23+i*.49;z=8.04+i*.155
  beam(f'grip_crossbar_{i}',[8,y,z],[8,y+.06,z+1.37],.63,.11,'edge','grip','gripframe')
 beam('grip_lattice_diagonal',[8,7.12,8.10],[8,9.18,9.86],.55,.10,'edge','grip','gripframe')
 # Small trigger guard ahead of pistol socket.
 box('guard_front',[7.84,9.18,6.29],[8.16,10.27,6.49],'edge','guard')
 box('guard_bottom',[7.84,9.11,6.34],[8.16,9.30,7.62],'edge','guard')
 c('trigger',[8,9.90,6.99],[.17,.53,.19],'silver','guard','plain',('x',-18))
 # Tall open optic housing: no glass/card on the native eye ray.
 box('sight_mount',[7.53,13.31,4.45],[8.85,13.54,6.11],'graphite','sight','sight')
 box('sight_foot',[7.63,13.53,4.87],[8.75,13.70,5.65],'silver','sight','sight')
 for side in (-1,1):
  c(f'optic_upright_{side}',[8.19+side*.47,14.34,5.28],[.13,1.46,.31],'violet','sight','sight')
  c(f'optic_outer_edge_{side}',[8.19+side*.55,14.34,5.28],[.07,1.44,.39],'silver','sight','sight')
  c(f'optic_shoulder_{side}',[8.19+side*.36,15.17,5.28],[.14,.40,.32],'silver','sight','sight',('z',side*32))
 c('optic_roof',[8.19,15.37,5.28],[.57,.1341552,.34],'violet','sight','sight')
 c('optic_floor',[8.19,13.66,5.28],[1.01,.12,.33],'violet','sight','sight')
 c('aiming_pin',[8.19,14.015,5.24],[.065,.39,.08],'pin','sight','pin')
 c('pin_pedestal',[8.19,13.77,5.24],[.25,.13,.16],'graphite','sight')
 # Retained sight base brace follows the source rearward foot.
 c('sight_rear_brace',[8.19,13.43,7.08],[.47,.17,1.55],'edge','controls','hardware')
 c('receiver_top_catch',[8,13.36,1.05],[1.57,.24,.52],'edge','controls','hardware')
 ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
 assert sha(PHOTO.read_bytes())==ref['sha256']
 inputs=[BASE,SOURCE,REFS,HELPER,BATCH,ASSET+f'textures/item/weapon/w30/{ID}.png']
 raw_inputs=[RAW/name for name in meta['source_files']]+[RAW/(m+'_Diffuse.png') for m in sorted({m['material'] for m in meshes})]+[RAW/'DimensionalHypotrochoidBody_Dyemap.png',PHOTO]
 return dict(id=ID,revision='W149',method='hand-authored semantic solid cuboids and per-face opaque paint',source=meta,reference=ref,
  source_transforms={m['name']:m['object_transform'] for m in meshes},palette=PALETTE,parts=parts,
  identity=['long cyan/silver upper beam with sweeping magenta default-dye ribbons','wide lateral drum and prominent silver static latch',
   'navy lower mounts, black maze foregrip, open lattice pistol grip','open tall violet optic and open stock equipment frame'],
  ads_sight=dict(sightCenter=[8.19,14.25,5.28],forwardPoint=[8.19,14.25,3.28],eyeSide='+Z',plane='XY',style='optic',
   pin_top=[8.19,14.21,5.24],aperture=[.79,1.31],notes='Open air instead of excluded reticle planes. Small pale pin immediately below center; no lens/card. Body and stock below eye ray.'),
  coordinate_policy=dict(basis='FBX stored RzRyRx/scaling -> Z-up meters; raw [-Y,Z,-X] -> native; source length X positive muzzle',
   scale=meta['scale'],anchor=meta['anchor'],bore_axis=[8,11.35],grip_top=[8,9.55,8.78],grip_heel=[8,6.90,7.94],
   foregrip_top=[8,9.35,-3.40],foregrip_heel=[8,6.48,-2.01],display='exact canonical dictionary / no recenter / no global scale',
   export='full only; existing generic reload; no split or new animation'),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
  limitations=['Offline CPU art inspection only. Native parser/pack, held views, ADS, generic reload and 10-20 displays pending master.',
   'Authored static matte photo palette; magenta is paint, not dynamic emission/PBR.',
   'Octagonal drum/bore and simplified grip lattice; tiny wear and fine equipment lettering omitted.',
   'Excluded source reticle cards remain excluded; open housing uses a small new aiming pin for sight alignment.',
   'Reverse photo unavailable; reverse structural paint only, no invented text.'])

def world_points(e,face,w,h):
 p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
 q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
 return u,v,q

def tile(spec,face,w,h):
 role=spec['material'];motif=spec['motif'];u,v,q=world_points(spec['geometry'],face,w,h);x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
 rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy();side=face in ('east','west')
 rgb*=((.98+.035*np.cos(y*.7))[:,:,None])
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
 if motif!='drum_end':rgb[edge<.75]*=.75;rgb[(edge>=.75)&(edge<1.55)]*=1.13
 def seam(yy,z0,z1,width=.025):
  m=(z>z0)&(z<z1);rgb[m&(abs(y-yy)<width)]*=.43;rgb[m&(abs(y-yy-.05)<.018)]*=1.16
 def fastener(zc,yc,r=.07):
  rr=np.hypot(z-zc,y-yc);rgb[rr<r]=PALETTE['black'];rgb[(rr>r*.64)&(rr<r)]=PALETTE['edge']
  rgb[(rr<r*.5)&(abs(z-zc)<.013)]=PALETTE['silver']
 if motif=='flow':
  # Long photo-backed cyan/graphite fields, flowing pink arcs and restrained violet bands.
  # World coordinates keep adjacent solid faces continuous; never raw re-projection.
  rgb[y<11.78]=PALETTE['graphite'];rgb[(y>12.70)]=PALETTE['cyan']
  stripe=(np.sin(z*.43+y*.8)>.90)&(y>12.2);rgb[stripe]=PALETTE['violet']
  if side:
   if face=='west':
    for zc,yc,rz,ry in [(-5.55,10.10,2.15,2.38),(-8.9,12.94,3.0,.90),(3.75,11.33,4.15,1.54),(12.55,13.32,2.21,1.38)]:
     dist=np.sqrt(((z-zc)/rz)**2+((y-yc)/ry)**2)
     rgb[(abs(dist-1)<.045)]=PALETTE['magenta'];rgb[(abs(dist-1)<.016)]=PALETTE['pink']
   else:
    # Structural reverse paint only; exact reverse graphic unavailable.
    rgb[(y>12.63)&(y<12.73)]=PALETTE['violet']
   for yy in (12.11,12.23,12.35):seam(yy,-8.6,15.3,.016)
   for zz in (-7.8,-1.1,6.45,14.60):fastener(zz,12.18,.065)
   # Source front vent is a shallow recess rather than drilled cube clutter.
   vent=(z< -7.45)&(z> -8.65)&(y>11.04)&(y<11.39)
   rgb[vent]=PALETTE['black'];dots=vent&(np.mod(z*15,1)<.25)&(np.mod(y*18,1)<.3);rgb[dots]=PALETTE['edge']
 if motif=='crown':
  rgb[np.mod(z+1.2,3.1)<.10]=PALETTE['graphite']
  rgb[(u>.86)&(u<.90)]=PALETTE['edge']
 if motif=='electronics' and side:
  for yy in (11.28,11.42,11.59,11.94):seam(yy,5.9,15.4,.014)
  panel=(y>11.60)&(y<11.91)&(z>7.1)&(z<14.9);rgb[panel]=PALETTE['edge']
  rgb[panel&(np.mod(z*.8,1)<.65)]=PALETTE['silver']
  holes=(y>11.24)&(y<11.36)&(np.mod(z*3,1)<.38);rgb[holes]=PALETTE['black']
 if motif in ('hardware','vent') and side:
  seam((spec['geometry']['from'][1]+spec['geometry']['to'][1])/2,-8,16,.032)
  for zz in (-6.5,-2,7.3,10.8,14.5):fastener(zz,float(q[:,:,1].mean()),.10)
 if motif=='equipment' and side:
  rgb[(y>9.18)&(y<10.64)&(z>12.62)&(z<14.7)]=PALETTE['silver']
  for zz in (12.39,14.90):
   for yy in (9.45,10.31):fastener(zz,yy,.17)
  seam(9.16,11.8,15.4);seam(10.64,11.8,15.4)
 if motif=='butt':
  rgb[z>15.75]=PALETTE['violet'];rgb[y<8.6]=PALETTE['graphite']
  if side:
   for yy in (8.8,10.5,12.6):fastener(15.64,yy,.075)
 if motif=='drum_end':
  rr=np.hypot(y-10.16,z-2.60);rgb[(rr>1.71)&(rr<1.78)]=PALETTE['edge']
  rgb[rr<.39]=PALETTE['black'];rgb[(rr>.31)&(rr<.40)]=PALETTE['silver']
 if motif=='drum_jacket':
  if face in ('east','west'):
   rr=np.hypot(y-10.16,z-2.60);rgb[rr<1.85]=PALETTE['graphite']
  else:
   channel=(u>.19)&(u<.80)&(v>.38)&(v<.57);rgb[channel]=PALETTE['black']
   rgb[(u>.20)&(u<.78)&(v>.35)&(v<.39)]=PALETTE['edge']
 if motif in ('handle','latch'):
  inset=(u>.14)&(u<.87)&(v>.34)&(v<.67);rgb[inset]=PALETTE['graphite']
  rgb[(u>.16)&(u<.85)&(v>.36)&(v<.39)]=PALETTE['edge']
 if motif=='maze':
  # Source grip has nested machining paths; ordered UV lines, no noise.
  rr=np.maximum(abs(u-.5),abs(v-.5))
  line=(np.mod(rr*36,1)<.22)&(rr<.45);rgb[line]=PALETTE['edge']
  rgb[(abs(u-.5)<.09)&(v>.15)&(v<.86)]=PALETTE['rubber']
 if motif=='bore':rgb[np.mod(z*15,1)<.18]*=.64
 if motif=='sight':
  rgb[(u>.25)&(u<.73)&(v>.12)&(v<.18)]=PALETTE['magenta']
 if motif=='pin':rgb[:]=PALETTE['pin']
 return Image.fromarray(np.concatenate([np.clip(rgb,0,255).astype(np.uint8),np.full((h,w,1),255,np.uint8)],2))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(12,17,24,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=17 if spec['group'] in ('drum','muzzle') else 22
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]))
    x=y=2;row=0;ledger=[];uvmap={}
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
        im=tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.asarray(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvmap[(name,face)]=[a*16/EDGE for a in (x,y,x+w,y+h)]
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    model=dict(credit='Dimensional Hypotrochoid W149 semantic solids / full only',
        textures={'0':'destiny:item/weapon/w123/dimensional_hypotrochoid','particle':'destiny:item/weapon/w123/dimensional_hypotrochoid'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,model


def inspection(d,model,atlas):
    es=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        children=[]
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None)
            b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
                     rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
        name='Dimensional Hypotrochoid W149 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='dimensional_hypotrochoid.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w149=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))




def comparison(d,meshes,atlas,model):
 w,h=720,290;sheet=Image.new('RGB',(2160,1450),'#151d27');draw=ImageDraw.Draw(sheet)
 def label(x,y,s,size=19):draw.text((x,y),s,fill='#e4ebed',font_size=size)
 label(20,12,'DIMENSIONAL HYPOTROCHOID / W149 / SEMANTIC SOLIDS + FACE UV / OFFLINE CPU ART',26)
 photo=Image.open(PHOTO).convert('RGB').crop((700,200,1780,850));photo.thumbnail((720,410));sheet.paste(photo,(15,52))
 label(20,435,'ACTUAL DEFAULT-DYE PHOTO / Bungie 1311684613',18)
 for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / {len(model["elements"])*6} unique UV faces / full only',
  'Cyan-silver beam / sweeping magenta paint / navy hardware',
  'Wide lateral drum + static silver latch / solid maze foregrip',
  'Open stock frame / lattice grip / actual bore and open optic',
  'Metadata X-length basis / original scale, anchor and display',
  'ADS center [8.19,14.25,5.28] / pin immediately below',
  'Native held / ADS / generic reload / 10-20 displays: master pending']):label(780,65+i*48,line,21)
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
 label(15,472,'ACTUAL FBX / neutral diffuse / 15,434 triangles')
 label(w+15,472,f'CANONICAL / {len(old["elements"])} cuboids / not raw')
 label(2*w+15,472,f'W149 / {len(model["elements"])} authored cuboids')
 tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
 points=np.concatenate([m['vertices'] for m in meshes])
 for row,(name,cam) in enumerate([('PHOTO SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.38,-.65]),('OPPOSITE REAR THREE-QUARTER',[1,.36,.65])]):
  extent=H['frame'](points,cam,w,h)
  for col,ts in enumerate(tris):
   im,_=H['render'](ts,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,505+row*h));label(col*w+12,510+row*h,name,16)
 label(20,1402,'Matched camera/scale per row. Source reticle cards excluded; sight housing is open. No native or performance acceptance claimed.',18)
 return png(sheet)

def review_text(d,counts):
 return f"""# Dimensional Hypotrochoid W149 offline art review

Actual default dye photo: `{PHOTO}`; SHA256 `{d['reference']['sha256']}`; source URL {d['reference']['screenshot']}. Raw FBX and inert source metadata establish proportions, sight, lateral drum, hand frame and excluded objects. Neutral body/sight diffuse is geometry detail evidence, not the final dye. The actual photo was opened before authoring. No source blend scripts or shaders were executed.

{sum(counts.values())} emitted opaque cuboids / {sum(counts.values())*6} independently authored face UVs / zero triangle adapters / full assembly {sum(counts.values())}/1000. Group counts: {json.dumps(counts,sort_keys=True)}. Started from large semantic fore casing, upper rear beam, lateral octagonal solid drum, static latch, lower hardware, two grips, stock and optic. Four intersecting filled prisms make the drum; substantial walls around the barrel preserve the actual lumen. No voxel/connected-component conversion, source triangle transplant, alpha side shells, fake moving parts or arbitrary triangle JSON.

Identity is the long cyan-silver casing with magenta curved ribbons, graphite panels and navy hardware, wide lateral drum and silver latch, black maze front grip and blue lattice pistol grip, inset stock equipment and tall optic. Main long faces use continuous world-aligned authored UV fields, magenta curves and grooves. The atlas is fully opaque 1024 square, with independent face islands and 2px extruded gutters. Plate seams, electronics, vent perforations and machining paths are UV. Deep drum/latch/casing steps, lattice voids, trigger air, stock frame and bore are geometry. Opposite-side exact ornament is unknown; only structural paint is authored there. Ribbons are static paint, not emission; no PBR/reflection recovery is claimed.

Transform was derived from stored FBX rotations (approximately [-90,90,0]) and scaling [100,100,100], converted from FBX Y-up centimeters to raw Z-up meters, then raw [-Y,Z,-X] times metadata scale {d['source']['scale']} plus original anchor {d['source']['anchor']}. Metadata source_axis is length X, thin Y, muzzle positive X, unlike Edge Transit's basis. All three retained objects, all 15,434 triangles and original native bounds are checked; excluded .02 reticle planes and Plane.001 are never imported. The unchanged canonical display dictionary preserves hip framing. Native muzzle is -Z. Both grip roots/heels follow actual source coordinates; no model-wide recenter or scale adjustment.

ADS sight: open XY optic housing, eye +Z looking -Z through [8.19,14.25,5.28], forward [8.19,14.25,3.28]. Pale pin top [8.19,14.21,5.24] is just below center. No opaque lens/card and no body or stock across the eye ray. Violet upright, silver outer trim and clipped shoulders follow the photo/source housing. The source reticle cards remain excluded; the small pin is an intentional functional reinterpretation. Master must align ADS to design.json ads_sight rather than bounds. The model display itself remains exact.

Full candidate only: destiny:weapon_surface_w123/{ID}; existing generic reload; no split/animation/runtime/shared registration edits. BBModel embeds exactly the final atlas and geometry. Comparison contains actual photo and matched raw/canonical/new side and two three-quarter views. Offline CPU renders do not establish pack or client acceptance. Curved contours are octagonal, grip lattice coarser than source, tiny wear and equipment lettering omitted. Native 26.3 parser/pack load, first/third-person holding, ADS, generic reload/audio/timing and 10-20 display observations remain master work.

Targeted regression checks finite cube/schema/budget, opaque UV islands and gutters, metadata/raw hashes and transforms, retained/excluded selection, empty bore/stock/grip/sight rays, exact display, BB parity, identity, output hashes and deterministic regeneration. Worker note records the final inspected image and actual test results. No Gradle, downloads, DCC, game/server/fixtures or child agents used.
"""

def generate(include_comparison=True):
 meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
 counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()));assert len(model['elements'])<=1000
 outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
 points=np.concatenate([vertices(e) for e in model['elements']])
 manifest=dict(id=ID,revision='W149',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),groups=counts,
  alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=6*len(model['elements']),max_assembled_elements=1000,
  texture_size=[1024,1024],atlas_face_islands=d['atlas']['face_islands'],actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],
  source_bounds=meta['model_bounds'],source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
  canonical_display_exact=True,full_only=True,existing_generic_reload=True,ads_sight=d['ads_sight'],native_accepted=False,
  generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
  default_photo_sha256=d['reference']['sha256'],output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest);return outputs

OWNED=[SCRIPT,TEST,ART+'design.json',ART+'manifest.json',ART+'review.md',ART+'inspection.bbmodel',ART+'comparison.png',REPORT,MODEL,TEXTURE]
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w149-'+ID)
 assert len(OWNED)==10 and set(OWNED)==set(owned)
 outputs=generate();assert len(outputs)==7 and set(outputs)<=set(owned)
 for path,data in outputs.items():
  p=ROOT/path
  if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json'])
 print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} cuboids / {m["emitted_faces"]} faces / full only')
if __name__=='__main__':main()
