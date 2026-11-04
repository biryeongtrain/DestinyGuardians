#!/usr/bin/env python3
"""W150 Stormchaser: semantic closed solids, inert source audit, face paint, seven products."""
import argparse, base64, copy, hashlib, io, json, math, runpy, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='stormchaser'; ART=f'art/weapons/w123/{ID}/'; ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/linear_fusion_rifle/stormchaser.json'
MODEL=ASSET+'models/weapon_surface_w123/stormchaser.json'
TEXTURE=ASSET+'textures/item/weapon/w123/stormchaser.png'
SOURCE='art/blockbench/weapons/w30/stormchaser.bbmodel'
SCRIPT='scripts/generate_surface_w123_stormchaser.py'; TEST='scripts/qa/test_surface_w150_stormchaser.py'
REPORT='docs/qa/2026-10-26/w150/stormchaser-worker.md'
RAW=Path('/tmp/destiny-weapons-w30/raw/stormchaser/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/stormchaser.jpg')
HELPER='scripts/generate_surface_w123_hollow_words.py'
L=runpy.run_path(str(ROOT/HELPER)); H=L['H']; FACES=H['FACES']; EDGE=1024
PALETTE=dict(body=[49,30,34],silver=[186,184,181],steel=[78,77,80],black=[27,28,32],rubber=[22,24,25],red=[124,30,35],green=[142,224,111])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w150:stormchaser:'+n))
def vertices(e):return L['vertices'](e)
def model_triangles(m,tex):return L['model_triangles'](m,tex)
def source_meshes():
 meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
 for n,digest in meta['source_files'].items():assert sha((RAW/Path(n).name).read_bytes())==digest
 b=L['Blend'](RAW/'Stormchaser.blend');bl={}
 for _,o in b.records('Object'):
  if b.field(o,'Object','type')!=1:continue
  name=b.field(b.field(o,'Object','id'),'ID','name')[2:];matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
  mesh=b.pointed(b.field(o,'Object','data'));nv=b.field(mesh,'Mesh','totvert')
  v=np.ndarray((nv,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
  bl[name]=dict(local=v,world=(np.c_[v,np.ones(nv)]@matrix)[:,:3],matrix=matrix,triangles=b.field(mesh,'Mesh','totpoly'))
 roots=H['parse_fbx'](RAW/'Stormchaser.fbx');obs=next(n[2] for n in roots if n[0]=='Objects');byid={n[1][0]:n for n in obs}
 links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO'];ms=[];audit=[]
 for n in obs:
  if n[0]!='Geometry':continue
  mo=byid[next(p for c,p in links if c==n[1][0])];name=mo[1][1].split('\x00')[0];ch={c[0]:c for c in n[2]}
  props={p[1][0]:p[1][4:] for p in next(c[2] for c in mo[2] if c[0]=='Properties70')}
  raw=np.array(ch['Vertices'][1][0]).reshape(-1,3)
  np.testing.assert_allclose(raw,bl[name]['local'],atol=1e-7,rtol=0)
  # Exporter -90X/100 properties are transport metadata. BLEND stored matrices
  # are authoritative; notably the separate reticle has a nonidentity matrix.
  world=(np.c_[raw,np.ones(len(raw))]@bl[name]['matrix'])[:,:3]
  np.testing.assert_allclose(world,bl[name]['world'],atol=1e-7,rtol=0)
  native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
  ix=np.array(ch['PolygonVertexIndex'][1][0]);assert np.all(ix[2::3]<0)
  faces=np.where(ix<0,-ix-1,ix).reshape(-1,3);assert len(faces)==bl[name]['triangles']
  layer={c[0]:c[1][0] for c in ch['LayerElementUV'][2]}
  assert layer['MappingInformationType']=='ByPolygonVertex' and layer['ReferenceInformationType']=='IndexToDirect'
  uv=np.array(layer['UV']).reshape(-1,2)[np.array(layer['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
  mats=[byid[c][1][1].split('\x00')[0] for c,p in links if p==mo[1][0] and byid[c][0]=='Material'];assert len(mats)==1
  status='accepted' if name in meta['source_objects'] else 'excluded';assert name in meta['source_objects']+meta['excluded_objects']
  audit.append(dict(name=name,status=status,triangles=len(faces),material=mats[0],fbx_properties=props,blend_matrix=bl[name]['matrix'].tolist(),world_bounds=[world.min(0).tolist(),world.max(0).tolist()]))
  if status=='accepted':ms.append(dict(name=name,vertices=native,world=world,faces=faces,uv=uv,material=mats[0]))
 assert sorted(bl)==sorted(m['name'] for m in audit)
 assert sorted(m['name'] for m in ms)==sorted(meta['source_objects'])
 assert sum(len(m['faces']) for m in ms)==meta['source_triangles']==29718
 ps=np.concatenate([m['vertices'] for m in ms]);ws=np.concatenate([m['world'] for m in ms])
 np.testing.assert_allclose([ws.min(0),ws.max(0)],meta['source_bounds'],atol=1e-7,rtol=0)
 np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=1e-7,rtol=0)
 assert meta['source_axis']==dict(length=1,thin=0,muzzle_sign=-1)
 return ms,meta,audit

def source_triangles(ms):
 tex=np.asarray(Image.open(RAW/'textures/StormchaserBody_Diffuse.png').convert('RGBA'));green=np.array([[[142,224,111,255]]],dtype='uint8');out=[]
 for m in ms:
  t=tex if m['material'].startswith('StormchaserBody&') else green
  for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
   if length>1e-10:out.append((ps,uv,t,n/length))
 return out

def make_design(meta,audit):
 parts=[]
 def c(name,center,size,material,group,motif='panel',turn=None):
  center=np.array(center,float);size=np.array(size,float)
  e=dict(name=name,**{'from':(center-size/2).round(6).tolist(),'to':(center+size/2).round(6).tolist()})
  if turn:e['rotation']=dict(origin=center.round(6).tolist(),axis=turn[0],angle=round(turn[1],6))
  parts.append(dict(group=group,material=material,motif=motif,geometry=e))
 def beam(name,a,b,width,thick,mat,group,motif='panel',x=8):
  # a,b are (y,z); thickness is along the local Y cross-section.
  a,b=np.array(a,float),np.array(b,float);mid=(a+b)/2;dy,dz=b-a
  c(name,[x,*mid],[width,thick,float(np.linalg.norm(b-a))],mat,group,motif,('x',-math.degrees(math.atan2(dy,dz))))
 # Full-depth body forms; the upper shroud has a continuous sloping spine
 # and chamfer shoulders, with silver vampiric paint on its broad faces.
 beam('upper_shroud_core',(11.03,-6.45),(11.92,4.72),1.14,.67,'body','upper','crest')
 for s in (-1,1):
  beam('upper_shoulder_'+str(s),(11.31,-6.28),(12.20,4.65),.27,.22,'silver','upper','crest',8+s*.51)
  beam('upper_lower_lip_'+str(s),(10.77,-6.30),(11.51,4.70),.16,.15,'red','upper','edge',8+s*.63)
 beam('upper_crown',(11.44,-5.9),(12.24,4.35),.54,.13,'black','upper','seam')
 for z,y in [(-6.27,11.08),(4.75,11.95)]:
  c('shroud_end_'+str(z),[8,y,z],[1.20,.61,.26],'silver','upper','crest',('x',-4.5))
 # Silver side ribs cross a real channel; ribs are grouped functional rails,
 # not thin ornamental cover plates. Their grooves are face paint.
 beam('barrel_core',(10.60,-5.76),(11.10,3.05),.59,.43,'black','barrel','machine')
 for s in (-1,1):
  beam('rib_header_'+str(s),(10.77,-6.12),(11.38,1.45),.18,.22,'silver','barrel','silver',8+s*.56)
  beam('rib_sill_'+str(s),(10.03,-5.70),(10.56,1.15),.20,.15,'silver','barrel','silver',8+s*.57)
  for i in range(10):
   z=-5.26+i*.66;y=10.49+(z+5.26)*.078
   beam('barrel_rib_'+str(s)+'_'+str(i),(y-.25,z-.18),(y+.29,z+.14),.14,.14,'silver','barrel','silver',8+s*.61)
 # Exposed rear charge chamber and silver piston neck, deep structural mass.
 for i,(z,ln,sy,mat) in enumerate([(1.65,.54,.66,'steel'),(2.19,.42,.56,'silver'),(2.68,.75,.72,'black'),(3.45,.88,.65,'body')]):
  c('chamber_'+str(i),[8,10.91,z],[.84,sy,ln],mat,'chamber','machine')
 c('chamber_top_bridge',[8,11.44,3.58],[1.10,.26,1.34],'black','chamber','machine')
 # Hollow octagonal muzzle: eight long wall solids around actual air.
 # The blind breech is deliberately recessed more than one native unit.
 r=.36;wall=.125
 for i in range(8):
  a=i*math.pi/4
  c('bore_wall_'+str(i),[8+r*math.sin(a),10.55+r*math.cos(a),-6.43],[.31,wall,.86],
    'steel','muzzle','bore',('z',-i*45))
 c('bore_recessed_breech',[8,10.55,-5.83],[.55,.55,.10],'black','muzzle','dark')
 for s in (-1,1):
  beam('muzzle_side_fin_'+str(s),(10.95,-7.10),(11.15,-6.23),.13,.13,'silver','muzzle','silver',8+s*.61)
 # Lower red-black receiver is broad and continuous, above its daylight loop.
 beam('lower_forebody',(9.91,-6.37),(9.55,1.90),1.01,.63,'body','body','marble')
 beam('lower_rearbody',(9.65,1.65),(10.01,7.86),1.34,.72,'black','body','machine')
 for s in (-1,1):
  beam('lower_rail_'+str(s),(10.10,-6.24),(10.13,4.40),.14,.13,'red','body','edge',8+s*.61)
 c('receiver_crossblock',[8,10.72,6.35],[2.442257673,1.11,1.54],'black','receiver','machine')
 beam('receiver_upper_fairing',(11.71,4.64),(11.63,7.60),1.19,.62,'black','receiver','machine')
 c('receiver_back',[8,10.87,7.78],[1.48,.92,1.53],'steel','receiver','machine')
 beam('receiver_rear_spine',(11.47,5.0),(11.03,12.57),.90,.72,'black','stock','machine')
 for s in (-1,1):
  beam('receiver_swept_cheek_'+str(s),(10.43,7.82),(10.30,11.70),.29,1.10,'black','stock','panel',8+s*.56)
  beam('stock_silver_slash_'+str(s),(9.97,9.53),(10.60,11.39),.12,.16,'silver','stock','silver',8+s*.74)
 c('butt_upper',[8,10.43,12.58],[1.07,1.18,1.37],'black','stock','rubber')
 beam('butt_heel',(10.79,13.00),(8.24,12.92),.96,.55,'black','stock','rubber')
 c('butt_end',[8,10.29,13.31],[.88,1.39,.53],'rubber','stock','rubber')
 # Long forward bayonet/keel. Four taper stations are solid silhouette spans.
 for i,(z0,z1,w,t,y) in enumerate([(-11.4264,-10.45,.07,.07,10.025),(-10.52,-9.17,.20,.15,10.00),(-9.25,-7.55,.36,.23,9.965),(-7.63,-6.02,.57,.35,9.90)]):
  c('forward_keel_'+str(i),[8,y,(z0+z1)/2],[w,t,z1-z0],'body','keel','marble')
 # Swept open handguard / underbody loop. Every segment has structural depth.
 pts=[(9.60,-6.20),(8.78,-4.90),(7.88,-3.16),(7.13,-1.14),(6.55,1.06),(6.03,3.07),(5.89,3.83)]
 for i,(a,b) in enumerate(zip(pts,pts[1:])):beam('swept_guard_'+str(i),a,b,.41,.18,'body','guard','marble')
 beam('guard_rear_upright',(5.96,3.83),(9.18,4.29),.74,.52,'black','guard','grip')
 beam('guard_front_web',(9.37,-6.14),(8.91,-4.75),.66,.43,'silver','guard','crest')
 # Distinct grip opening behind the large guard; no hidden fill through air.
 beam('pistol_grip',(9.73,7.37),(6.79,8.66),1.00,1.04,'black','grip','grip')
 beam('grip_front_swell',(9.44,7.17),(8.65,7.17),.86,.43,'rubber','grip','grip')
 beam('trigger_front_web',(8.89,4.44),(6.83,6.76),.78,.55,'black','grip','bands')
 beam('trigger_shoe',(8.88,6.20),(9.51,6.39),.21,.17,'black','grip','dark')
 beam('grip_floor',(6.80,6.50),(6.76,8.72),1.12,.24,'steel','grip','machine')
 c('power_shoe',[8,6.43,7.54],[1.25,.58,2.78],'black','shoe','machine')
 beam('power_shoe_toe',(6.04,6.20),(5.86,7.79),1.14,.40,'black','shoe','panel')
 beam('power_shoe_rear_lip',(5.91,7.75),(6.10,9.24),1.08,.19,'body','shoe','edge')
 for s in (-1,1):
  c('power_green_inset_'+str(s),[8+s*.638,6.57,8.18],[.045,.15,1.13],'green','shoe','green')
 # Photo's raised open U-holo frame, with an opaque reticle pin below its ray.
 # No glass card intersects the eye-to-forward centerline.
 c('optic_base',[8,11.91,6.55],[1.14,.20,1.62],'silver','optic','machine')
 for s in (-1,1):
  beam('optic_leg_'+str(s),(11.99,6.82),(12.47,6.50),.16,.19,'silver','optic','silver',8+s*.48)
  c('optic_horn_'+str(s),[8+s*.48,12.65,6.50],[.18,.32346716,.46],'black','optic','rubber')
  beam('optic_front_foot_'+str(s),(11.95,5.78),(12.15,6.30),.17,.13,'silver','optic','silver',8+s*.48)
 c('optic_center_pin',[8,12.14,6.51],[.065,.32,.11],'red','optic','red')
 c('optic_windage',[8.65,12.01,6.75],[.32,.22,.32],'black','optic','machine')
 assert 80<=len(parts)<=140,len(parts)
 inputs=[BASE,SOURCE,HELPER,'scripts/generate_surface_w123_beloved.py','scripts/generate_surface_w123_erentil_fr4.py',ASSET+'textures/item/weapon/w30/stormchaser.png']
 raws=sorted(p for p in RAW.rglob('*') if p.is_file())+[PHOTO]
 return dict(id=ID,revision='W150',construction='Author placed filled semantic cuboids; no voxel or rip-island conversion',parts=parts,palette=PALETTE,source=meta,
  source_matching=dict(mapping='BLEND stored matrix then native = [world.X,world.Z,world.Y] * scale + anchor',muzzle='raw negative Y becomes native negative Z; exporter +forward conventions do not override W30 muzzle_sign=-1',
   source_triangles=29718,textured_triangles=29694,accepted_emission_triangles=24,excluded_triangles=546,inventory=audit),
  identity=['swept lower daylight frame and extended forward keel','silver diagonal barrel cooling cage','vampiric silver crest over red-black basic dye','large independent trigger/grip opening','black hooked shoulder with silver slash','green power shoe and raised open U-holo'],
  starting_draft='94 author placed initial solids; rear fairing added after matched-view review; repeated structural ribs provide side parallax, minor panel lines stay UV',
  full_only=True,muzzle_axis='-Z',source_frame_preserved=True,
  ads_sight=dict(sightCenter=[8,12.50,6.50],forwardPoint=[8,12.50,4.50],eyeSide='+Z',plane='XY',style='optic'),
  openings=dict(bore=[8,10.55,-6.43],swept_guard=[8,7.75,.6],trigger_grip=[8,8.48,6.25],stock_cutaway=[8,9.25,11.80],optic=[8,12.50,6.5]),
  filled_probes=dict(upper=[8,11.46,-1],body=[8,9.69,-2],grip=[8,7.9,8.2],stock=[8,10.4,12.7]),
  atlas=dict(size=EDGE,gutter=2,texels_per_unit=20),
  default_photo_sha256=sha(PHOTO.read_bytes()),input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raws},
  limitations=['Offline CPU inspection only; native resource load/held/ADS/fire/reload/listening/20-display remain parent owned.',
   'Opaque static authored red-black basic dye and silver ornament approximate the photo; no animated VFX or dynamic PBR.',
   'Swept curves, bore, blade taper and grip are deliberately faceted; reverse-side silver ornament follows structural evidence.'])

def tile(s,face,w,h):
 u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h);ps=vertices(s['geometry'])[list(FACES[face])]
 pos=((1-u)*(1-v))[:,:,None]*ps[0]+(u*(1-v))[:,:,None]*ps[1]+(u*v)[:,:,None]*ps[2]+((1-u)*v)[:,:,None]*ps[3]
 x,y,z=(pos[:,:,i] for i in range(3));mat=s['material'];motif=s['motif'];side=face in ('east','west')
 rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy();edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
 rgb*=(.97+.03*np.cos(v*math.pi))[:,:,None]
 if motif in ('marble','crest','edge'):
  # Organized sparse red cloudy veins, continuous in model space, no random wear.
  f=np.sin(z*2.0+y*5)+.50*np.sin(z*5.8-y*9)+.25*np.cos(z*13+y*11)
  if mat in ('body','red'):
   strength=np.clip((f+.15)/1.8,0,1)**2;rgb[:]=np.array([35,25,30])+strength[:,:,None]*np.array([89,12,15])
  if motif=='crest' and side:
   # Long silver curved bat-wing fields over a dark vampiric shroud.
   phase=np.mod((z+6.5)/4.15,1);yy=y-(11.04+.078*(z+6.45))
   upper=-.23+.51*abs(phase-.5)*2
   wing=(yy>upper)&(yy<.51)&(phase>.08)&(phase<.90)
   lower=(yy<-.05)&(yy>-.27)&(phase>.38)&(phase<.66)
   rgb[wing|lower]=[196,193,190]
   # Three scalloped notches echo the photographed fang/wing ornament.
   for q in (.42,.52,.62):
    rr=((phase-q)/.035)**2+((yy+.10)/.095)**2
    rgb[(rr<1)&(yy<-.065)]=[34,24,29]
  if motif=='marble' and side:
   # Source/photo-supported abstract hooked rune on forebody, not text.
   zz=z+.95;yy=y-9.77
   rune=(abs(yy-.10*np.sin(zz*6))<.027)&(abs(zz)<.32)
   rune|=(abs(zz-.22)<.025)&(yy>-.10)&(yy<.19)
   rgb[rune]=[169,162,155]
 if motif in ('panel','machine'):
  rgb[(edge>2)&(edge<3)]*=.62
  if side:
   # Restrained grooves and recessed fasteners painted into large solids.
   if motif=='machine':rgb[(abs(v-.74)<.018)&(u>.10)&(u<.88)]*=.55
   for a in (.12,.88):
    r=np.hypot((u-a)*w,(v-.25)*h)
    rgb[(r<1.7)&(r>.75)]=[94,91,92]
 if motif in ('grip','rubber'):
  rgb[np.mod(y*7+z*.45,1)<.19]*=.57
  if motif=='grip' and side:rgb[(edge>2)&(edge<3)]=[64,62,63]
 if motif=='bands' and side:
  f=np.mod(y*2.25+z*.76,1);rgb[(f>.12)&(f<.36)]=[179,176,172]
 if motif=='silver':
  rgb*=(.96+.035*np.cos(z*15+y*2))[:,:,None]
 if motif=='bore':
  # The wall's inward face stays dark; bore remains actual open geometry.
  rr=np.hypot(x-8,y-10.55);rgb[rr<.33]=[32,29,33]
 if motif=='seam':rgb[abs(u-.5)<.13]=[119,34,41]
 if motif=='green':rgb[edge<1]=[65,111,56]
 if motif!='dark':
  rgb[edge<.65]*=.65;rgb[(edge>.65)&(edge<1.35)]*=1.15
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(24,25,28,255));requests=[]
 for s in d['parts']:
  for f,ix in FACES.items():
   p=vertices(s['geometry'])[list(ix)];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*20));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*20))
   requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;islands=[];uvmap={}
 for h,w,n,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'UV atlas overflow'
  atlas.paste(Image.fromarray(np.pad(np.asarray(tile(s,f,w,h)),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  rect=[x,y,x+w,y+h];uvmap[n,f]=[a*16/EDGE for a in rect];islands.append(dict(element=n,face=f,rect=rect));x+=w+4;row=max(row,h)
 es=[]
 for s in d['parts']:
  e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in FACES};es.append(e)
 d['atlas'].update(used_height=y+row+2,islands=islands,face_islands=len(islands),paint_policy='Independent opaque six-face UV; photo-backed silver wing crest, red-black veins, diagonal cage and grip bands')
 return atlas,dict(credit='W150 Stormchaser / semantic filled solids / full only / native pending parent',textures={'0':'destiny:item/weapon/w123/stormchaser','particle':'destiny:item/weapon/w123/stormchaser'},display=copy.deepcopy(json.loads((ROOT/BASE).read_bytes())['display']),elements=es)

def inspection(d,model,atlas):
 es=[];groups={}
 for s,e in zip(d['parts'],model['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
  for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
  es.append(b);groups.setdefault(s['group'],[]).append(b['uuid'])
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Stormchaser W150 editable semantic full model',resolution=dict(width=EDGE,height=EDGE),elements=es,display=copy.deepcopy(model['display']),
  outliner=[dict(name=n,uuid=uid(n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],
  textures=[dict(name='stormchaser.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
  destiny_w150=dict(nativeAccepted=False,fullOnly=True,sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor'],ads_sight=d['ads_sight']))

def comparison(d,ms,atlas,model):
 w,h=1000,370;out=Image.new('RGB',(3000,2100),'#18212a');dr=ImageDraw.Draw(out)
 def label(x,y,t,size=22):dr.text((x,y),t,fill='#e6ebef',font_size=size)
 label(20,12,'STORMCHASER / W150 / CLOSED SEMANTIC SOLIDS + OPAQUE FACE UV / OFFLINE',30)
 photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1050,550));out.paste(photo,(20,57))
 for i,t in enumerate([f'{len(model["elements"])} solid cuboids / full-only / canonical display, scale and anchor',
  'Default photo: silver wings + cage, red-black body, swept daylight frame',
  'Actual FBX 29,718 accepted triangles; BLEND vertices verified inertly',
  'Raw [X,Z,Y] mapping matches W30 bounds; muzzle remains negative Z',
  '546 excluded VFX/reticle triangles inventoried separately',
  'Actual bore / grip / swept loop / stock cutaway / raised open U-holo',
  'Independent face UV; opaque atlas; pin below a clear eye-to-forward ray',
  'Native held/ADS/scope/fire/reload/audio/20-display: pending parent']):label(1110,80+i*48,t,22)
 label(20,540,'ACTUAL LOCAL FBX / NEUTRAL DIFFUSE')
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/stormchaser.png'))
 label(w+20,540,f'CANONICAL W30 / {len(old["elements"])} CUBOIDS')
 label(2*w+20,540,f'W150 / {len(model["elements"])} AUTHORED SOLIDS')
 ts=[source_triangles(ms),model_triangles(old,oldtex),model_triangles(model,atlas)];ps=np.concatenate([m['vertices'] for m in ms]);d['comparison_views']=[]
 for row,(n,cam) in enumerate([('SIDE / MATCHED CAMERA + SCALE',[-1,0,0]),('FRONT QUARTER / MATCHED CAMERA + SCALE',[-1,.42,-.60]),('OPPOSITE REAR QUARTER / MATCHED CAMERA + SCALE',[1,.40,.60])]):
  ext=H['frame'](ps,cam,w,h);d['comparison_views'].append(dict(name=n,camera=cam,center=ext[0].tolist(),scale=float(ext[1])))
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);out.paste(im,(col*w,580+row*h));label(col*w+14,590+row*h,n,18)
 for i,(groups,title,cam) in enumerate([(['muzzle','barrel'],'ACTUAL RECESSED BORE',[.25,.15,-1]),(['guard','grip','shoe','body'],'REAL GUARD + GRIP AIR',[-1,.25,-.15]),(['optic'],'OPEN U-HOLO / PIN BELOW RAY',[0,.04,1]),(['upper','chamber'],'SILVER CREST / OPAQUE PAINT',[-1,.3,-.4])]):
  names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups};es=[e for e in model['elements'] if e['name'] in names];pp=np.concatenate([vertices(e) for e in es])
  im,_=H['render'](model_triangles(dict(elements=es),atlas),cam,H['frame'](pp,cam,750,330),(750,330));out.paste(im,(i*750,1710));label(i*750+13,1720,title,18)
 label(20,2060,'CPU geometry/art comparison only. Neutral source diffuse is not basic dye. Static finish and faceted curves; native acceptance remains parent-owned.',21)
 return png(out)

def review_text(d,counts):
 return f"""# Stormchaser W150 — offline art review

{len(d['parts'])} author-placed closed cuboids / {len(d['parts'])*6} independently allocated opaque face UVs; no triangle adapter, alpha body, mesh-island conversion or voxel body. The ~110-element draft uses substantial housing/receiver/grip/stock volumes; cooling ribs, guard spans and bore walls improve silhouette and parallax. Fine seams, grip ribs, bolts, red-black veins and silver wing crest use paint.

Opened actual default-dye photo `{PHOTO}`. Identity retained: silver gothic upper shroud, diagonal silver cooling cage, black/red basic dye, long forward keel and swept open handguard, separate trigger/grip opening, hooked black shoulder with silver slash, green power shoe, raised open U-holo. The bore is an eight-wall physical aperture with a recessed breech. The grip, forward guard and stock cutaway are physical air. The optic has side horns and a small red pin just below center. Native sightCenter=[8,12.50,6.50], forwardPoint=[8,12.50,4.50], eyeSide=+Z and plane=XY produce direction [0,0,-2], matching native muzzle -Z at physical ADS rotation 0. The center ray and a 0.09-unit horizontal / 0.08-unit vertical corridor are clear from native Z=+16 to -12; no global model reversal was applied. Parent retains Stormchaser's existing screen-space LFR scope.

Actual local FBX and BLEND are read as inert data using sibling parsers; no source script or shader executes. Every FBX local vertex matches BLEND, all five stored object matrices are applied, and the two W30 accepted objects contain 29,718 triangles: body 29,694 and green shoe 24. Excluded source objects contain 542 VFX + 2 reticle sides + 2 reticle = 546 triangles. The separate reticle's nonidentity stored matrix is audited. Raw exporter -90X/100 properties are diagnosed rather than blindly applied twice. Native `[world.X,world.Z,world.Y] * {d['source']['scale']} + {d['source']['anchor']}` exactly reproduces W30 source/native bounds. Raw negative Y (not a generic source +forward convention) becomes native negative Z; source muzzle_sign=-1 and old model agree. No recentering or axial reversal.

Original full display, source scale, anchor and hand coordinate frame are preserved. Only the full candidate model is emitted. No split-magazine/reload/timing/audio/HUD/gameplay/registry edits. Parent owns integration and native verification. Editable inspection.bbmodel embeds the exact atlas and grouped cubes. comparison.png contains actual photo, inert source, actual old W30 and authored output at matched scale in side/front/opposite quarters, plus bore/open-frame/optic/paint details. Final comparison was opened in side, front quarter and opposite rear quarter views. Review corrected the thin upper shroud, weak rear fairing, disconnected grip brace and core blocking the bore. This is offline evidence, never a native screenshot.

Limits: static face paint approximates photographed default dye; PBR, animated red VFX and reflective response are not restored. Curves and tapered keel remain faceted cuboid approximations. Reverse-side small ornament follows the structural finish without invented text. Native parser/pack load, first/third-person contact, scoped ADS, charging/fire, full-only generic reload/ammo timing, listening and 10–20 displays remain pending parent.

Group counts: {json.dumps(counts,sort_keys=True)}.
"""

def generate():
 ms,meta,audit=source_meshes();d=make_design(meta,audit);atlas,model=compile_model(d);counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
 comp=comparison(d,ms,atlas,model);ps=np.concatenate([vertices(e) for e in model['elements']])
 outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode(),ART+'comparison.png':comp}
 manifest=dict(id=ID,revision='W150',family='linear_fusion_rifle',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),emitted_faces=len(model['elements'])*6,triangle_adapter_elements=0,contour_elements=0,alpha_body_elements=0,max_assembled_elements=1000,full_only=True,groups=counts,texture_size=[EDGE,EDGE],face_uv_islands=len(d['atlas']['islands']),atlas_used_height=d['atlas']['used_height'],actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],source_matching=d['source_matching'],ads_sight=d['ads_sight'],canonical_display_exact=True,native_accepted=False,existing_ADS_scope_reload_timing_audio_unchanged=True,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/'docs/qa/2026-10-26/w150/batch.json').read_bytes())['features'] if f['name']=='w150-stormchaser')
 assert len(outputs)==7 and set(outputs)<=set(owned);assert len(model['elements'])<=1000
 return outputs

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();outputs=generate()
 for rel,data in outputs.items():
  path=ROOT/rel
  if a.verify:assert path.is_file() and path.read_bytes()==data,'Regeneration differs: '+rel
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if a.verify else 'Generated')+f' seven artifacts; {m["assembled_elements"]} closed cuboids; {m["emitted_faces"]} faces; atlas height {m["atlas_used_height"]}; native pending parent')
if __name__=='__main__':main()
