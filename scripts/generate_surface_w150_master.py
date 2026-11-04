#!/usr/bin/env python3
"""W150 master: Retraced Path / Line in the Sand semantic solids and face UV.

Inert FBX arrays only. Source/photo geometry evidence, not original shader execution.
"""
import argparse,base64,copy,hashlib,io,json,math,runpy,uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ASSET='src/main/resources/assets/destiny/'
SCRIPT='scripts/generate_surface_w150_master.py'
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER));FACES=H['FACES'];EDGE=1024
IDS=('retraced_path','line_in_the_sand')
TITLES={'retraced_path':'Retraced Path','line_in_the_sand':'Line in the Sand'}
FAMILIES={'retraced_path':'trace_rifle','line_in_the_sand':'linear_fusion_rifle'}
PALETTES={
 'retraced_path':dict(blue=[83,103,151],lightblue=[138,162,194],purple=[100,71,150],black=[25,30,39],steel=[137,145,154],gold=[186,165,118],dark=[16,21,28],pin=[240,233,185]),
 'line_in_the_sand':dict(silver=[184,191,196],steel=[103,115,127],black=[31,38,45],dark=[14,22,29],gold=[181,138,75],glow=[171,161,244],pin=[234,227,194])}
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def paths(id):
 return dict(base=ASSET+f'models/weapon/{FAMILIES[id]}/{id}.json',source=f'art/blockbench/weapons/w30/{id}.bbmodel',art=f'art/weapons/w123/{id}/',model=ASSET+f'models/weapon_surface_w123/{id}.json',texture=ASSET+f'textures/item/weapon/w123/{id}.png')
def vertices(e):
 e=copy.deepcopy(e)
 if 'rotation' in e:
  r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return H['vertices'](e)
def model_triangles(model,texture):
 m=copy.deepcopy(model)
 for e in m['elements']:
  if 'rotation' in e:
   r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return H['model_triangles']({'full':m},texture)

def source_meshes(id):
 p=paths(id);meta=json.loads((ROOT/p['source']).read_bytes())['destiny_w30'];title=TITLES[id]
 raw=Path('/tmp/destiny-weapons-w30/raw')/id/'extracted';fbx=raw/title/(title+'.fbx')
 assert sha(fbx.read_bytes())==meta['source_files'][str(fbx.relative_to(raw))]
 roots=H['parse_fbx'](fbx);objects=next(n[2] for n in roots if n[0]=='Objects')
 links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
 models={n[1][0]:n for n in objects if n[0]=='Model'};meshes=[]
 for n in objects:
  if n[0]!='Geometry':continue
  mid=next(pa for ch,pa in links if ch==n[1][0]);model=models[mid];name=model[1][1].split('\0')[0]
  if name not in meta['source_objects']:continue
  props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
  np.testing.assert_allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001,rtol=0)
  np.testing.assert_allclose(props['Lcl Scaling'],[100]*3,atol=.0001,rtol=0)
  assert 'Lcl Translation' not in props or not any(props['Lcl Translation'])
  cs={c[0]:c for c in n[2]};world=np.array(cs['Vertices'][1][0],float).reshape(-1,3)
  # Source FBX arrays already match stored BLEND world coordinates (checked below).
  assert meta['source_axis']==dict(length=1,thin=0,muzzle_sign=-1)
  v=world[:,[0,2,1]]*meta['scale']+meta['anchor'];faces=[];face=[]
  for i in cs['PolygonVertexIndex'][1][0]:
   face.append(i if i>=0 else -i-1)
   if i<0:assert len(face)==3;faces.append(face);face=[]
  layer=next((c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0),None)
  if layer:
   vals={c[0]:c[1][0] for c in layer[2]};assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
   uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
  else:uv=np.zeros((len(faces),3,2))
  meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,worldBounds=[world.min(0).tolist(),world.max(0).tolist()]))
 assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
 assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
 pts=np.concatenate([m['vertices'] for m in meshes]);wb=np.array([m['worldBounds'] for m in meshes])
 np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
 np.testing.assert_allclose([wb[:,0].min(0),wb[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
 photo=Path('/tmp/destiny-weapons-w31/references')/(id+'.jpg');ref=next(x for x in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if x['id']==id)
 assert sha(photo.read_bytes())==ref['sha256']
 return meshes,meta,ref,fbx,photo

class Builder:
 def __init__(self):self.parts=[]
 def c(self,name,pos,size,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
  if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=turn[1])
  self.parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def beam(self,name,a,b,w,h,mat,group,motif='plain'):
  self.c(name,[(x+y)/2 for x,y in zip(a,b)],[w,h,math.dist(a,b)],mat,group,motif,('x',-math.degrees(math.atan2(b[1]-a[1],b[2]-a[2]))))
 def tube(self,name,pos,z0,z1,r,t,mat,group,motif='plain'):
  x,y=pos
  for i in range(8):
   a=i*45;q=math.radians(a);rr=r-t/2
   self.c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],[2*rr*math.tan(math.pi/8)+.008,t,z1-z0],mat,group,motif,('z',a))
 def disc(self,name,x0,x1,y,z,r,mat,group,motif='plain'):
  for i in range(4):self.c(f'{name}_{i}',[(x0+x1)/2,y,z],[x1-x0,2*r,2*r*math.tan(math.pi/8)],mat,group,motif,('x',i*45))
 def optic(self,x,y,z,w,h,mat):
  self.c('optic_floor',[x,y-h/2,z],[w,.14,.65],mat,'sight')
  self.c('optic_roof',[x,y+h/2,z],[w,.14,.65],mat,'sight')
  for side in (-1,1):self.c('optic_wall_'+str(side),[x+side*w/2,y,z],[.14,h,.65],mat,'sight')
  self.c('optic_pin',[x,y-.21,z-.25],[.06,.28,.08],'pin','sight')

def design(id,meta,ref,fbx,photo):
 b=Builder();c=b.c;beam=b.beam;tube=b.tube;disc=b.disc
 if id=='retraced_path':
  # Long separated Covenant-like rails, not a uniform extruded silhouette.
  tube('central_energy_barrel',(8,10.45),-9.64,.65,.42,.13,'gold','barrel','vent')
  tube('muzzle_bore',(8,10.45),-10.15,-9.63,.51,.13,'gold','barrel')
  c('bore_depth',[8,10.45,-9.58],[.67,.67,.06],'dark','barrel')
  for side in (-1,1):
   x=8+side*.68
   beam(f'upper_rail_{side}',[x,11.95,-10.13],[x,12.78,.75],.48,.68,'blue','rail','blue_panel')
   beam(f'upper_rail_bevel_{side}',[x+side*.20,12.12,-9.92],[x+side*.20,12.91,.80],.27,.34,'lightblue','rail','blue_panel')
   beam(f'lower_rail_{side}',[x,8.48,-10.10],[x,9.18,.84],.48,.64,'purple','rail','blue_panel')
   beam(f'lower_rail_bevel_{side}',[x+side*.20,8.66,-9.91],[x+side*.20,9.35,.78],.25,.30,'blue','rail')
   beam(f'upper_broad_casing_{side}',[x,11.55,-10.0],[x,12.03,.80],.48,1.20,'blue','shell','blue_panel')
   beam(f'lower_broad_casing_{side}',[x,8.90,-10.0],[x,9.60,.83],.48,1.00,'blue','shell','blue_panel')
   c(f'rail_front_tip_{side}',[x,12.03,-10.12],[.54,.43,.19],'gold','rail')
   c(f'lower_tip_{side}',[x,8.53,-10.12],[.53,.44,.19],'black','rail')
   beam(f'sweeping_receiver_{side}',[x,11.84,-.55],[x,13.10,2.70],.84,.69,'blue','shell','blue_panel')
   beam(f'sweeping_receiver_lower_{side}',[x,9.13,.40],[x,9.98,3.08],.83,.72,'blue','shell','blue_panel')
   c(f'silver_stock_panel_{side}',[8+side*.62,11.6,7.7],[.37,.73,7.15],'steel','stock','panel')
   beam(f'purple_stock_upper_{side}',[8+side*.68,13.14,4.9],[8+side*.68,13.20,14.54],.47,.34,'purple','stock','blue_panel')
   beam(f'blue_stock_upper_{side}',[8+side*.57,12.98,4.0],[8+side*.57,13.04,14.5],.67,.45,'blue','stock')
   beam(f'underslung_stock_curve_{side}',[8+side*.65,7.09,9.30],[8+side*.65,9.11,13.65],.43,.47,'purple','stock','blue_panel')
   beam(f'underslung_stock_return_{side}',[8+side*.65,9.11,13.65],[8+side*.65,12.65,14.51],.43,.47,'blue','stock','blue_panel')
   beam(f'stock_silver_inset_{side}',[8+side*.74,7.62,10.10],[8+side*.74,9.19,13.31],.17,.23,'steel','stock')
  c('receiver_solid',[8,11.21,2.58],[1.50,2.24,4.30],'black','receiver','panel')
  for side in (-1,1):
   outer=(8.85,9.02) if side>0 else (6.98,7.15)
   face=(9.02,9.12) if side>0 else (6.88,6.98)
   hub=(9.12,9.19) if side>0 else (6.81,6.88)
   disc(f'power_disc_outer_{side}',*outer,11.30,1.0,1.51,'gold','disc','disc')
   disc(f'power_disc_face_{side}',*face,11.30,1.0,1.31,'steel','disc','disc')
   disc(f'power_disc_hub_{side}',*hub,11.30,1.0,.45,'steel','disc')
  c('rear_action',[8,11.70,8.60],[1.35,1.81,11.68],'black','receiver','panel')
  c('upper_action_spine',[8,12.76,7.7],[1.24,.42,11.93],'blue','shell','blue_panel')
  beam('pistol_grip',[8,10.97,9.32],[8,7.32,9.9],1.03,1.16,'black','grip','grip')
  c('grip_heel',[8,7.11,10.02],[1.23,.34,1.46],'gold','grip')
  beam('magazine_well',[8,9.12,3.55],[8,5.34,4.42],1.16,1.62,'black','magazine','panel')
  c('magazine_foot',[8,5.11,4.51],[1.35,.35,1.83],'steel','magazine','panel')
  for side in (-1,1):c(f'magazine_blue_edge_{side}',[8+side*.57,7.11,4.02],[.10,3.7,.19],'lightblue','magazine')
  beam('trigger_guard_front',[8,10.66,6.85],[8,8.91,6.91],.23,.21,'black','guard')
  beam('trigger_guard_floor',[8,8.91,6.91],[8,8.91,9.15],.23,.21,'gold','guard')
  c('trigger',[8,10.08,8.0],[.17,.59,.22],'steel','guard',turn=('x',-18))
  c('rear_buttpad',[8,11.23,14.57],[1.62,4.03,.45],'black','stock','grip')
  for side in (-1,1):
   x=8+side*.55
   beam(f'arched_scope_front_{side}',[x,13.25,.50],[x,14.15,2.08],.42,.51,'blue','sight','blue_panel')
   beam(f'arched_scope_roof_{side}',[x,14.15,2.08],[x,14.14,3.96],.42,.51,'purple','sight','blue_panel')
   beam(f'arched_scope_rear_{side}',[x,14.14,3.96],[x,13.16,6.15],.42,.51,'blue','sight','blue_panel')
  c('scope_roof_bridge',[8,14.18,3.00],[1.50,.42,1.55],'purple','sight','blue_panel')
  c('optic_pedestal',[8,13.74,5.74],[.67,.78,.55],'black','sight','panel')
  b.optic(8,14.50,5.74,1.08,.85,'lightblue')
  sight=[8,14.50,5.74];openings=dict(bore=[8,10.45,-9.94],trigger_guard=[8,9.45,7.5],stock=[8,9.1,11.4])
  identity=['blue-purple sweeping split rails','long exposed gold energy channel','large silver/gold side power disc','open black rear stock and underslung magazine']
 else:
  # Upper/lower separated fork rails and exposed gold coil bank.
  c('upper_rail_core',[8,10.68,-4.7],[.89,.57,10.12],'silver','rail','silver_panel')
  c('lower_rail_core',[8,7.98,-4.75],[.91,.61,10.12],'silver','rail','silver_panel')
  for side in (-1,1):
   c(f'upper_rail_outer_{side}',[8+side*.39,10.61,-4.72],[.27,.45,10.15],'steel','rail','silver_panel')
   c(f'lower_rail_outer_{side}',[8+side*.39,8.00,-4.72],[.27,.46,10.15],'steel','rail','silver_panel')
   beam(f'upper_hook_{side}',[8+side*.3,10.64,-9.47],[8+side*.3,11.62,-9.72],.27,.35,'black','fork')
   beam(f'lower_hook_{side}',[8+side*.3,8.0,-9.47],[8+side*.3,7.32,-9.68],.27,.35,'black','fork')
   c(f'fork_glow_upper_{side}',[8+side*.44,10.57,-9.59],[.04,.12,.25],'glow','energy')
   c(f'fork_glow_lower_{side}',[8+side*.44,8.04,-9.59],[.04,.12,.25],'glow','energy')
  for i in range(7):
   z=-8.98+i*.69
   c(f'upper_serration_{i}',[8,10.20,z],[.82,.36,.25],'black','fork',turn=('x',-22))
   c(f'lower_serration_{i}',[8,8.48,z],[.82,.30,.25],'silver','fork',turn=('x',22))
  c('receiver_coil_spine',[8,9.50,2.50],[1.42,2.63,7.16],'black','receiver','panel')
  for side in (-1,1):
   c(f'gold_upper_coil_{side}',[8+side*.55,10.25,2.03],[.47,.53,7.21],'gold','coil','coil')
   c(f'gold_lower_coil_{side}',[8+side*.57,9.19,2.03],[.47,.72,7.21],'gold','coil','coil')
   c(f'gold_bank_rim_{side}',[8+side*.73,9.84,2.12],[.13,.17,7.46],'gold','coil','rail')
   beam(f'upper_silver_shell_{side}',[8+side*.41,11.33,-.57],[8+side*.41,11.84,4.92],.73,1.35,'silver','shell','silver_panel')
   beam(f'upper_shell_bevel_{side}',[8+side*.62,11.08,-.30],[8+side*.62,11.53,5.28],.25,.43,'steel','shell','silver_panel')
   beam(f'rear_silver_cheek_{side}',[8+side*.49,11.57,6.15],[8+side*.49,11.15,11.50],.67,1.25,'silver','shell','silver_panel')
   c(f'lower_black_vent_panel_{side}',[8+side*.57,8.45,3.18],[.26,.86,5.40],'black','receiver','vent')
   beam(f'lower_stock_arm_{side}',[8+side*.55,5.92,8.37],[8+side*.55,6.50,10.24],.43,.46,'silver','stock','silver_panel')
   c(f'lower_stock_energy_{side}',[8+side*.78,6.07,8.42],[.04,.11,1.28],'glow','energy')
   c(f'gold_rear_rail_{side}',[8+side*.32,10.57,12.63],[.29,.40,4.70],'gold','coil','coil')
   c(f'grip_silver_cheek_{side}',[8+side*.51,7.36,9.5],[.27,1.93,1.42],'silver','grip','silver_panel',('x',-18))
  c('rear_stock_beam',[8,11.04,12.60],[.85,.59,4.77],'black','stock','rail')
  c('rear_stock_upper',[8,11.65,12.68],[1.02,.43,4.75],'silver','stock','silver_panel')
  c('rear_buttpad',[8,10.36,14.93],[1.35,2.47,.44],'black','stock','grip')
  beam('pistol_grip',[8,9.78,7.19],[8,6.88,8.77],1.01,1.1,'black','grip','grip')
  c('grip_heel',[8,6.70,8.86],[1.26,.37,1.36],'steel','grip')
  c('lower_battery',[8,5.60,6.83],[1.35,.80,5.70],'black','battery','panel')
  c('battery_silver_floor',[8,5.08,6.83],[1.59,.28,5.64],'silver','battery','silver_panel')
  for side in (-1,1):
   beam(f'battery_rounded_front_{side}',[8+side*.62,5.17,4.11],[8+side*.62,5.78,3.88],.35,.40,'silver','battery','silver_panel')
   beam(f'battery_rounded_rear_{side}',[8+side*.62,5.17,9.50],[8+side*.62,5.78,9.73],.35,.40,'silver','battery','silver_panel')
  for side in (-1,1):c('battery_edge_'+str(side),[8+side*.70,5.45,6.80],[.14,.53,5.81],'steel','battery','rail')
  beam('foregrip',[8,7.90,-.95],[8,6.54,-.62],.72,.63,'black','grip','grip')
  c('foregrip_heel',[8,6.44,-.59],[.95,.35,.76],'steel','grip')
  beam('guard_front',[8,8.80,4.18],[8,7.07,4.22],.23,.23,'black','guard')
  beam('guard_floor',[8,7.07,4.22],[8,7.1,6.87],.23,.23,'steel','guard')
  c('trigger',[8,8.22,5.73],[.16,.65,.25],'black','guard',turn=('x',-15))
  c('xiv_plate',[8,11.28,6.0],[1.28,.43,.71],'silver','mark','xiv')
  c('scope_pedestal',[8,11.98,4.28],[.54,.69,1.84],'black','sight','panel')
  b.optic(8,12.65,5.47,1.28,.88,'black')
  c('scope_silver_cap',[8,13.16,4.47],[1.33,.22,2.14],'silver','sight','silver_panel')
  for side in (-1,1):c(f'scope_silver_cheek_{side}',[8+side*.62,12.75,4.51],[.14,.62,1.87],'steel','sight')
  sight=[8,12.65,5.47];openings=dict(fork=[8,9.4,-8.5],trigger_guard=[8,7.8,4.95],scope=[8,12.65,5.47])
  identity=['separated silver fork rails with curved black tips','exposed gold dual coil bank','white upper receiver cheeks','lower black battery and open optic']
 p=paths(id);inputs=[p['base'],p['source'],HELPER,'art/weapons/w31/references.json',ASSET+f'textures/item/weapon/w30/{id}.png']
 return dict(id=id,revision='W150',source=meta,reference=ref,parts=b.parts,palette=PALETTES[id],full_only=True,identity=identity,
  ads_sight=dict(sightCenter=sight,forwardPoint=[sight[0],sight[1],sight[2]-2],eyeSide='+Z',plane='XY',style='optic'),
  openings=openings,atlas=dict(size=EDGE,gutter=2,texels_per_unit=18),
  method='authored semantic filled solids and independent opaque face UV; source FBX only informs scale/silhouette',
  input_sha256={x:sha((ROOT/x).read_bytes()) for x in inputs},raw_input_sha256={str(x):sha(x.read_bytes()) for x in [fbx,photo]},
  limitations=['Authored static default-photo material, not original PBR, iridescence or source shader.','Original curves are faceted; neutral raw illustration is not source dye.','Generic reload retained; no new moving magazine or coil.','Existing LFR screen-space scope retained for Line in the Sand.','Native acceptance must be established separately by master.'])

def tile(d,s,face,w,h):
 u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h);pts=vertices(s['geometry'])[list(FACES[face])]
 p=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3];x,y,z=p[:,:,0],p[:,:,1],p[:,:,2]
 pal=d['palette'];rgb=np.broadcast_to(np.array(pal[s['material']],float),(h,w,3)).copy();edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb*=((.96+.04*np.cos(v*math.pi))[:,:,None]);rgb[edge<.7]*=.67;rgb[(edge>=.7)&(edge<1.5)]*=1.15
 motif=s['motif']
 if motif in ('panel','silver_panel','blue_panel'):
  rgb[(edge>2)&(edge<2.7)]*=.66
  if motif=='blue_panel':
   stripe=(y-.045*z)>12.24;rgb[stripe]*=np.array([1.08,.94,1.10]);rgb[(edge>1.5)&(edge<3)]=pal['lightblue']
  if motif=='silver_panel':rgb[(np.mod(z*1.2,1)<.024)&(edge>3)]*=.60
 elif motif=='coil':
  t=np.mod(z*3.8,1);rgb[t<.17]*=.42;rgb[(t>.22)&(t<.29)]*=1.24;rgb[(abs(v-.5)<.08) & (edge>3)]*=.70
 elif motif=='vent':rgb[(np.mod(z*3.9,1)<.35)&(v>.2)&(v<.78)]*=.31
 elif motif=='grip':rgb[(np.mod(y*4+z*.2,1)<.20)&(edge>2)]*=.48
 elif motif=='disc':
  rad=np.sqrt((y-11.30)**2+(z-1.0)**2);rgb[(rad>.95)&(rad<1.02)]*=.5;rgb[(rad>.48)&(rad<.56)]*=.55
  angle=np.arctan2(y-11.30,z-1);rgb[(np.mod(angle/(2*math.pi)*8,1)<.12)&(rad>1.02) & (rad<1.19)]*=.46
 elif motif=='xiv':
  # Small source-backed XIV plate, not invented serial numbers.
  out=Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]));dr=ImageDraw.Draw(out)
  if face in ('east','west'):dr.text((max(1,w//5),max(1,h//5)),'XIV',fill=(35,40,48,255),font_size=max(6,min(h-2,w//3)))
  return out
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(17,22,28,255));requests=[]
 for s in d['parts']:
  for f,ix in FACES.items():
   p=vertices(s['geometry'])[list(ix)];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*18));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*18));requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;uvs={};islands=[]
 for h,w,n,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'UV atlas overflow'
  atlas.paste(Image.fromarray(np.pad(np.asarray(tile(d,s,f,w,h)),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2));rect=[x,y,x+w,y+h];uvs[n,f]=[a*16/EDGE for a in rect];islands.append(dict(element=n,face=f,rect=rect));x+=w+4;row=max(row,h)
 es=[]
 for s in d['parts']:
  e=copy.deepcopy(s['geometry']);e['faces']={f:dict(texture='#0',uv=uvs[e['name'],f]) for f in FACES};es.append(e)
 d['atlas'].update(used_height=y+row+2,islands=islands)
 return atlas,dict(credit=TITLES[d['id']]+' W150 / semantic solids and independently painted face UV',textures={'0':'destiny:item/weapon/w123/'+d['id'],'particle':'destiny:item/weapon/w123/'+d['id']},display=copy.deepcopy(json.loads((ROOT/paths(d['id'])['base']).read_bytes())['display']),elements=es)

def inspection(d,model,atlas):
 uid=lambda x:str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w150:'+d['id']+':'+x));es=[];groups={}
 for s,e in zip(d['parts'],model['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
  for f in b['faces'].values():f['texture']=0;f['uv']=[x*EDGE/16 for x in f['uv']]
  es.append(b);groups.setdefault(s['group'],[]).append(b['uuid'])
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name=TITLES[d['id']]+' W150 semantic inspection',resolution=dict(width=EDGE,height=EDGE),elements=es,display=copy.deepcopy(model['display']),outliner=[dict(name=n,uuid=uid(n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],textures=[dict(name=d['id']+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())])

def raw_triangles(meshes):
 result=[];texture=np.array([[[127,139,149,255]]],np.uint8)
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20);result.append((p,uv,texture,n))
 return result
def comparison(d,meshes,model,atlas,photo):
 id=d['id'];w,h=500,260;im=Image.new('RGB',(1500,1150),'#171e26');dr=ImageDraw.Draw(im)
 dr.text((14,10),TITLES[id]+' W150 / actual raw + default photo / authored filled solids and face UV',fill='white',font_size=21)
 ref=Image.open(photo).convert('RGB');ref=ref.crop((400,150,1920,920));ref.thumbnail((790,285));im.paste(ref,(12,45))
 dr.text((810,74),str(len(model['elements']))+' opaque cuboids / full only\n'+ '\n'.join(d['identity'])+'\nNo native acceptance from CPU views',fill='white',font_size=21,spacing=12)
 old=json.loads((ROOT/paths(id)['base']).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{id}.png'));pts=np.concatenate([m['vertices'] for m in meshes]);tris=[raw_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
 for col,title in enumerate(['RAW NEUTRAL GEOMETRY','OLD CANONICAL','W150 SOLID + PHOTO PAINT']):dr.text((col*w+10,342),title,fill='white',font_size=18)
 for row,(label,cam) in enumerate([('SIDE',[-1,0,0]),('FRONT QUARTER',[-1,.35,-.65]),('OPPOSITE REAR',[1,.30,.65])]):
  extent=H['frame'](pts,cam,w,h)
  for col,t in enumerate(tris):
   frame,_=H['render'](t,cam,extent,(w,h),raw=col==0);im.paste(frame,(col*w,370+row*h));dr.text((col*w+10,375+row*h),label,fill='white',font_size=15)
 return png(im)

def generate(id,include_comparison=True):
 meshes,meta,ref,fbx,photo=source_meshes(id);d=design(id,meta,ref,fbx,photo);atlas,model=compile_model(d);p=paths(id);art=p['art'];groups=dict(sorted(Counter(x['group'] for x in d['parts']).items()));count=len(model['elements']);assert 0<count<=1000
 review=f'''# {TITLES[id]} — W150 semantic filled solids

Actual basic-dye photo `{photo}` and inert FBX `{fbx}` informed proportions, openings, palette and characteristic parts. {len(meshes)} retained source objects / {meta['source_triangles']} triangles. Source selection, bounds and native [world.X,world.Z,world.Y] scale/anchor verified against W30 metadata. No embedded scripts/material execution; raw comparison is neutral geometry, not shader/dye evaluation.

Identity: {', '.join(d['identity'])}. {count} substantial opaque cuboids / {count*6} independently mapped faces, no triangle adapters or alpha body cards; full-only <=1000. Meaningful long rails, closed solids, open barrel/fork/guard/stock/sight as appropriate, not source component/voxel conversion. Groups {json.dumps(groups)}. Face UV carries material boundaries, restrained panel edges, source-backed coil/vent lines and marking; silhouette-defining separation and discs are real geometry. Original curves are intentionally faceted and material is authored static paint, not original PBR/iridescence.

Original display transforms, axis, scale/anchor and generic reload retained. No new magazine/coil animation, combat/ammo/timing/audio changes. Functional open optic with clear optical ray and pin below it; Line in the Sand retains its existing LFR scope overlay. Inspection embeds final texture and geometry. Actual native parser/pack/held/ADS/reload/20display review remains master scope, not proven by offline comparison.
'''
 out={art+'design.json':encode(d),p['model']:encode(model),p['texture']:png(atlas),art+'inspection.bbmodel':encode(inspection(d,model,atlas)),art+'review.md':review.encode()}
 if include_comparison:out[art+'comparison.png']=comparison(d,meshes,model,atlas,photo)
 pts=np.concatenate([vertices(e) for e in model['elements']]);out[art+'manifest.json']=encode(dict(id=id,revision='W150',assembled_elements=count,opaque_cuboids=count,triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=count*6,full_only=True,groups=groups,actual_bounds=[pts.min(0).tolist(),pts.max(0).tolist()],source_scale=meta['scale'],source_anchor=meta['anchor'],source_triangles=meta['source_triangles'],canonical_display_exact=True,native_accepted=False,generator_sha256=sha((ROOT/SCRIPT).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(b) for p,b in out.items()},limitations=d['limitations']))
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('ids',nargs='*',choices=IDS);p.add_argument('--verify',action='store_true');p.add_argument('--no-comparison',action='store_true');a=p.parse_args()
 for id in a.ids or IDS:
  out=generate(id,not a.no_comparison)
  for n,b in out.items():
   path=ROOT/n
   if a.verify:assert path.read_bytes()==b,n
   else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
  print(id,len(out),'verified' if a.verify else 'generated',json.loads(out[paths(id)['art']+'manifest.json'])['assembled_elements'],'cuboids')
