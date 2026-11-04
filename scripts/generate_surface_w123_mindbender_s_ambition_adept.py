#!/usr/bin/env python3
"""W147 Mindbender: hand-authored solid volumes, inert FBX, opaque face atlas.
Only exact batch-owned files are written. No source code/shader/DCC execution.
"""
import argparse, base64, collections, copy, hashlib, io, json, math, runpy, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='mindbender_s_ambition_adept'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/shotgun/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
BB=f'art/blockbench/weapons/w30/{ID}.bbmodel'
RAW=Path("/tmp/destiny-weapons-w30/raw/mindbender_s_ambition_adept/extracted/Mindbender's Ambition (Adept)")
PHOTO=Path('/tmp/destiny-weapons-w31/references/mindbender_s_ambition_adept.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER)); FACES=H['FACES']; EDGE=1024
PALETTE=dict(blue=[49,65,74],edge=[65,80,89],bone=[191,164,122],bone_edge=[207,184,145],silver=[190,193,185],steel=[85,92,94],black=[27,32,35],recess=[12,17,20])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w147:'+ID+':'+n))
def render_element(e):
 e=copy.deepcopy(e)
 if 'rotation' in e:
  r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return e
def vertices(e):return H['vertices'](render_element(e))
def model_triangles(m,atlas):
 m=copy.deepcopy(m);m['elements']=[render_element(e) for e in m['elements']]
 return H['model_triangles']({'full':m},atlas)
def source_meshes():
 meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
 for n,v in meta['source_files'].items():assert sha((RAW.parent/n).read_bytes())==v,n
 r=H['parse_fbx'](RAW/"Mindbender's Ambition (Adept).fbx")
 o=next(n[2] for n in r if n[0]=='Objects')
 links=[n[1][1:] for a in r if a[0]=='Connections' for n in a[2] if n[1][0]=='OO']
 models={n[1][0]:n for n in o if n[0]=='Model'}
 mats={n[1][0]:n[1][1].split('\x00')[0] for n in o if n[0]=='Material'}
 meshes=[]
 for n in o:
  if n[0]!='Geometry':continue
  mid=next(p for c,p in links if c==n[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
  assert name in meta['source_objects'],name
  props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
  assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
  assert props['Lcl Scaling']==[100,100,100]
  cs={c[0]:c for c in n[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
  # This weapon's raw exporter buffers already use source X,Y,Z; not Beloved axes.
  points=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
  ix=np.array(cs['PolygonVertexIndex'][1][0]);assert np.all(ix[2::3]<0)
  faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
  layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
  vals={c[0]:c[1][0] for c in layer[2]}
  assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
  uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
  mat=next(mats[c] for c,p in links if p==mid and c in mats)
  meshes.append(dict(name=name,vertices=points,faces=faces,uv=uv,material=mat))
 assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
 assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==meta['textured_triangles']==11516
 ps=np.concatenate([m['vertices'] for m in meshes])
 np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
 world=(ps-8)/meta['scale'];world=world[:,[0,2,1]]
 np.testing.assert_allclose([world.min(0),world.max(0)],meta['source_bounds'],atol=1e-7,rtol=0)
 ref=next(x for x in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if x['id']==ID)
 assert sha(PHOTO.read_bytes())==ref['sha256']
 return meshes,meta,ref

def source_triangles(meshes):
 names={"Mindbender's Bones":'72cbeb80_Diffuse.png',"Mindbender's Sights":'e0beea80_Diffuse.png',"Mindbender's Main Body + Barrel":'92dbeb80_Diffuse.png',"Mindbender's Stock":'92dbeb80_Diffuse.png'}
 tex={m:np.array(Image.open(RAW/f).convert('RGBA')) for m,f in names.items()}
 # Diffuse alpha is packed data, not an opacity instruction for solid source bodies.
 for t in tex.values():t[:,:,3]=255
 ts=[]
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
   if length>1e-12:ts.append((p,uv,tex[m['material']],n/length))
 return ts

def make_design(meta,ref):
 parts=[]
 def box(group,name,c,size,mat,motif='plain',turn=None):
  c=np.array(c,float);s=np.array(size,float)
  e=dict(name=name,**{'from':(c-s/2).round(7).tolist(),'to':(c+s/2).round(7).tolist()})
  if turn:e['rotation']=dict(origin=c.tolist(),axis=turn[0],angle=round(turn[1],7))
  parts.append(dict(group=group,material=mat,motif=motif,kind='filled_semantic_cuboid',geometry=e))
 def beam(group,name,a,b,width,depth,mat,motif='plain',x=8):
  z0,y0=a;z1,y1=b
  box(group,name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(z1-z0,y1-y0)],mat,motif,('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
 def ring(group,name,z,length,y,r,t,mat,motif='plain'):
  # Eight physical walls form an open octagonal bore, all with real thickness.
  for i in range(8):
   a=math.radians(i*45);q=r-t/2
   box(group,name+f'_{i}',[8+q*math.sin(a),y+q*math.cos(a),z],[2*r*math.tan(math.pi/8),t,length],mat,motif,('z',-i*45))
 # 101-part semantic draft; no connected-component or voxel-derived construction.
 ring('barrel','long_bore_wall',-3.75,12.008345576,11.835,.415,.095,'blue','runes')
 box('barrel','deep_bore_stop',[8,11.835,-8.90],[.59,.59,.08],'recess')
 ring('muzzle','muzzle_lip',-9.67,.168345576,11.835,.415,.105,'edge','runes')
 ring('tube','lower_tube',-6.73,6.00,10.97,.305,.09,'blue','runes')
 box('tube','lower_tube_stop',[8,10.97,-9.18],[.41,.41,.06],'recess')
 box('tube','pump_slide',[8,10.94,-1.70],[.56,.58,6.20],'steel','runes')
 box('receiver','action_solid',[8,11.49,5.30],[1.17,1.62,7.40],'blue','runes')
 for side in (-1,1):
  box('receiver',f'action_top_shoulder_{side}',[8+side*.47,12.15,5.25],[.29,.25,7.30],'edge','runes',('z',side*35))
  box('receiver',f'action_low_shoulder_{side}',[8+side*.47,10.84,5.25],[.29,.25,7.30],'blue','runes',('z',-side*35))
  box('receiver',f'action_inset_{side}',[8+side*.605,11.15,5.25],[.08,.72,3.34],'blue','runes')
 beam('receiver','action_tail',[8.80,11.40],[9.70,11.12],.94,1.18,'blue','runes')
 box('receiver','loading_tray',[8,10.59,5.42],[.82,.20,3.25],'black','runes')
 # Bone fore-end is a filled broad mass, with two long bevel planes and tapered ends.
 box('forebone','forebone_core',[8,10.48,-2.63],[1.70,1.02,5.72],'bone','bone')
 for side in (-1,1):
  box('forebone',f'bone_upper_bevel_{side}',[8+side*.82,10.90,-2.63],[.30,.36,5.72],'bone_edge','bone',('z',side*35))
  box('forebone',f'bone_lower_bevel_{side}',[8+side*.79,10.05,-2.67],[.32,.31,5.64],'bone','bone',('z',-side*32))
 beam('forebone','forebone_back_taper',[-.05,10.42],[.68,10.10],1.48,.87,'bone','bone')
 beam('forebone','forebone_front_lip',[-5.76,10.45],[-5.30,10.58],1.78,1.03,'bone_edge','bone')
 beam('forebone','hanging_bone_tooth',[.24,10.10],[.48,9.52],.56,.39,'bone','bone')
 # Thick hooked bone grip. Its front metal extension and open space are real geometry.
 beam('grip','grip_root',[7.21,10.38],[7.90,8.74],.87,1.31,'bone','bone')
 beam('grip','grip_palm',[7.90,8.90],[8.81,7.11],.89,1.35,'bone','bone')
 beam('grip','grip_hook_tip',[8.81,7.12],[8.25,6.71],.74,.48,'bone_edge','bone')
 for side in (-1,1):
  beam('grip',f'grip_edge_{side}',[7.73,9.03],[8.82,7.18],.21,1.25,'bone','bone',x=8+side*.44)
  beam('grip',f'grip_crown_{side}',[7.05,10.50],[7.63,9.54],.21,.73,'bone_edge','bone',x=8+side*.39)
 beam('guard','guard_front',[5.60,10.59],[5.78,9.35],.18,.18,'silver')
 beam('guard','guard_floor',[5.78,9.35],[6.70,9.05],.18,.18,'silver')
 beam('guard','guard_rear',[6.70,9.05],[7.10,9.60],.18,.18,'silver')
 beam('guard','trigger_upper',[6.40,10.55],[6.22,9.85],.17,.16,'steel')
 beam('guard','trigger_hook',[6.22,9.85],[6.50,9.69],.17,.15,'steel')
 beam('guard','grip_spur_front',[6.65,9.26],[7.47,6.65],.22,.20,'silver')
 beam('guard','grip_spur_heel',[7.47,6.65],[7.95,6.60],.22,.20,'silver')
 beam('guard','grip_spur_return',[7.95,6.60],[8.74,7.18],.22,.20,'silver')
 # Rear stock: metal tang and substantial ivory wedge, not a rectangular filled card.
 box('stock','stock_tang',[8,11.21,10.09],[.72,1.12,1.25],'black','runes')
 beam('stock','stock_bone_upper',[10.34,11.61],[14.55,11.44],.78,.85,'bone_edge','bone')
 beam('stock','stock_bone_lower',[10.48,10.91],[14.21,10.69],.78,.75,'bone','bone')
 beam('stock','stock_bone_blade',[14.45,11.52],[14.31,8.86],.73,.88,'bone','bone')
 beam('stock','stock_bone_point',[14.24,9.13],[14.12,8.57],.55,.45,'bone','bone')
 for side in (-1,1):
  beam('stock',f'cheek_edge_{side}',[10.42,11.92],[14.53,11.75],.16,.24,'bone_edge','bone',x=8+side*.35)
  beam('stock',f'stock_lower_edge_{side}',[10.55,10.55],[13.86,10.33],.16,.20,'bone','bone',x=8+side*.35)
 beam('stock','butt_pad',[14.92,11.51],[14.89,9.18],.70,.54,'steel','pad')
 beam('stock','butt_pad_top',[14.87,11.66],[15.12,11.58],.65,.25,'steel','pad')
 beam('stock','stock_rear_grip',[12.05,10.46],[12.36,9.88],.62,.71,'steel','pad')
 box('stock','stock_lower_catch',[8,10.39,11.97],[.77,.24,.84],'black')
 # Native iron sights preserve the upper source envelope, without a filled notch.
 box('sight','sight_rail',[8,12.37,5.18],[.59,.19,1.82],'silver','plain')
 box('sight','sight_ramp',[8,12.53,5.15],[.46,.20,1.43],'steel','plain',('x',8))
 for side in (-1,1):box('sight',f'notch_ear_{side}',[8+side*.22,12.64,5.93],[.14,.315439533,.32],'black')
 # Distinctive silver rune-covered collars use original source UV detail.
 ring('bands','barrel_silver_collar',-.39,.32,11.835,.47,.105,'silver','source_silver')
 ring('bands','front_silver_rune_sleeve',-8.35,2.22,10.97,.324,.075,'silver','source_silver')
 ring('bands','pump_silver_collar',-5.24,.22,10.97,.345,.075,'silver','source_silver')
 box('bands','side_rune_plaque_left',[8.64,11.20,4.30],[.12,.74,1.31],'silver','source_silver')
 box('bands','side_rune_plaque_right',[7.36,11.20,4.30],[.12,.74,1.31],'silver','source_silver')
 box('bands','bolt_handle_base',[8.66,10.80,6.65],[.18,.22,.40],'steel')
 box('bands','bolt_handle_knob',[8.76,10.69,6.65],[.20,.25,.20],'silver')
 return dict(id=ID,revision='W147',family='shotgun',method='Hand-authored filled semantic cuboids; source geometry only reference and paint evidence.',
  source=meta,reference=ref,source_mapping='raw FBX [X,Z,Y]*original_scale+anchor; buffers verified against original source and native bounds',
  scale=meta['scale'],anchor=meta['anchor'],palette=PALETTE,parts=parts,full_only=True,moving_element_names=[],
  starting_draft='Near 80-120 solids; long octagonal barrel and tube, three thick carved bones, trigger/grip air and open muzzle.',
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in (BASE,BB,HELPER,ASSET+f'textures/item/weapon/w30/{ID}.png')},
  raw_input_sha256={str(p):sha(p.read_bytes()) for p in sorted(RAW.rglob('*')) if p.is_file()}|{str(PHOTO):sha(PHOTO.read_bytes())},
  air_probes={'muzzle':[8,11.835,-9.67],'lower_tube_mouth':[8,10.97,-9.45],'trigger_guard':[8,9.78,5.98],'grip_loop':[8,7.71,7.55],'sight_notch':[8,12.70,5.93]},
  solid_probes={'receiver':[8,11.49,5.30],'forebone':[8,10.48,-2.63],'grip':[8,8.5,8.1],'stock':[8,11.5,12.5]},
  limitations=['Static matte default-dye interpretation; no original dynamic PBR/iridescence.',
   'Bone cavities and Hive inscriptions are source-relief paint on broad solid planes; organic curvature is deliberately faceted.',
   'Neutral source side projections retain actual source markings; top/end transitions use clean material fallback where source is absent.',
   'Native parser, pack, held/ADS/per-shell reload and 10-20 display acceptance remain master-owned.'])

MAP_CAMS={'east':[1,0,0],'west':[-1,0,0],'north':[.00001,0,-1],'south':[.00001,0,1],'up':[.00001,1,.00001],'down':[.00001,-1,.00001]}
def paint_maps(meshes):
 maps={}
 # Independent maps per material and view prevent unrelated parts contaminating bone paint.
 for kind in ('bone','metal'):
  ms=[m for m in meshes if (m['material']=="Mindbender's Bones")== (kind=='bone')]
  ps=np.concatenate([m['vertices'] for m in ms]);ts=source_triangles(ms)
  for face,cam in MAP_CAMS.items():
   cam=np.array(cam,float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
   ext=H['frame'](ps,cam,1200,440)
   im,mask=H['render'](ts,cam,ext,(1200,440),raw=True)
   maps[kind,face]=(np.asarray(im),mask,cam,right,up,ext)
 return maps

def tile(s,face,w,h,maps):
 base=np.array(PALETTE[s['material']],float);yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
 q=vertices(s['geometry'])[list(FACES[face])];p=q[0]+u[:,:,None]*(q[1]-q[0])+v[:,:,None]*(q[3]-q[0])
 a=np.empty((h,w,4),np.uint8);a[:,:,:3]=base*(.98+.02*np.sin(v*np.pi))[:,:,None];a[:,:,3]=255
 motif=s['motif'];material=s['material']
 if motif in ('bone','runes','source_silver'):
  im,mask,cam,right,up,ext=maps['bone' if motif=='bone' else 'metal',face];center,scale=ext
  px=np.clip(((p@right-center[0])*scale+600).astype(int),0,1199);py=np.clip((220-(p@up-center[1])*scale).astype(int),0,439)
  valid=mask[py,px];rgb=im[py,px,:3].astype(float);lum=rgb.mean(2)
  if motif=='bone':
   # Preserve large source cavities; suppress fine albedo dirt and restore warm default dye.
   contrast=np.clip(lum/100+.15,.52,1.18);paint=base*contrast[:,:,None]
  elif motif=='runes':
   # Neutral diffuse has dark actual Hive script. No new alphabet or random glyphs.
   ink=np.clip((lum-38)/67,.38,1.08);paint=base*ink[:,:,None]
  else:
   ink=np.clip((lum-29)/69,.22,1.04);paint=base*ink[:,:,None]
  a[valid,:3]=np.clip(paint[valid],0,255)
 if material in ('silver','steel','edge'):
  a[0,:,:3]=np.minimum(base+13,255);a[-1,:,:3]=base*.75
 if motif=='pad':
  a[np.mod(p[:,:,1],.14)<.027,:3]=base*.67
 return Image.fromarray(a)

def compile_model(d,maps):
 atlas=Image.new('RGBA',(EDGE,EDGE),(25,32,36,255));requests=[]
 for s in d['parts']:
  s['geometry']['faces']={}
  for f in FACES:
   p=vertices(s['geometry'])[list(FACES[f])];density=20
   w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
   requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;islands=[]
 for h,w,name,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'atlas overflow'
  im=tile(s,f,w,h,maps);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  s['geometry']['faces'][f]=dict(uv=[v*16/EDGE for v in (x,y,x+w,y+h)],texture='#0')
  islands.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
 d['atlas']=dict(size=EDGE,gutter=2,face_islands=len(islands),islands=islands,used_height=y+row+2)
 return atlas,dict(credit='Mindbender W147 / semantic solid volumes / actual source Hive and bone relief / opaque independent UV',
  textures={'0':f'destiny:item/weapon/w123/{ID}','particle':f'destiny:item/weapon/w123/{ID}'},elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])
def inspection(d,m,atlas):
 es=[];groups=collections.defaultdict(list)
 for s,e in zip(d['parts'],m['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation',None);rot=[0,0,0]
  if r:rot['xyz'.index(r['axis'])]=r['angle']
  b.update(type='cube',uuid=uid(b['name']),origin=r['origin'] if r else [8,8,8],rotation=rot,box_uv=False,autouv=0)
  for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
  es.append(b);groups[s['group']].append(b['uuid'])
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Mindbender W147 / editable offline inspection',resolution=dict(width=EDGE,height=EDGE),elements=es,
  outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=c,export=True) for g,c in groups.items()],
  textures=[dict(name=ID+'.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=m['display'],destiny_w147=dict(nativeAccepted=False,fullOnly=True,sourceScale=d['scale'],sourceAnchor=d['anchor']))
def comparison(d,meshes,atlas,m):
 w,h=900,310;sheet=Image.new('RGB',(w*3,1770),'#151c25');draw=ImageDraw.Draw(sheet)
 def label(x,y,t,size=21):draw.text((x,y),t,fill='#e2e7ed',font_size=size)
 label(20,14,"MINDBENDER'S AMBITION (ADEPT) / W147 / OFFLINE SOLID + FACE-UV INSPECTION",29)
 photo=Image.open(PHOTO).convert('RGB').crop((640,300,1880,770));photo.thumbnail((1700,390));sheet.paste(photo,(20,65))
 label(1770,100,'Actual default photo',24);label(1770,145,'Warm carved bone / blue-black Hive metal',20)
 label(1770,185,'Silver rune bands / hooked grip / open bore',20);label(1770,235,f"{len(m['elements'])} authored solid cuboids",24)
 label(1770,275,'Full-only / original generic per-shell reload',20)
 label(20,485,'RAW SOURCE / 11,516tri / neutral diffuse')
 label(w+20,485,'ORIGINAL CANONICAL / 250cuboids')
 label(w*2+20,485,f"W147 / {len(m['elements'])}solids / independent opaque UV")
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
 ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(m,atlas)]
 ps=np.concatenate([s['vertices'] for s in meshes]);metrics={}
 for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT THREE-QUARTER',[1,.48,-.65]),('REAR THREE-QUARTER',[-1,.40,.66])]):
  ext=H['frame'](ps,cam,w,h);masks=[]
  for col,tris in enumerate(ts):
   im,mask=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,525+row*h));label(col*w+15,535+row*h,name,18);masks.append(mask)
  metrics[name]=dict(raw_pixels=int(masks[0].sum()),new_pixels=int(masks[2].sum()),silhouette_iou=float(np.logical_and(masks[0],masks[2]).sum()/np.logical_or(masks[0],masks[2]).sum()))
 for i,g in enumerate(('muzzle','forebone','guard','stock')):
  names={s['geometry']['name'] for s in d['parts'] if s['group']==g};sub=[e for e in m['elements'] if e['name'] in names];ps=np.concatenate([vertices(e) for e in sub]);cam=[.45,.25,-1] if g=='muzzle' else [1,.3,-.4]
  im,_=H['render'](model_triangles(dict(elements=sub),atlas),cam,H['frame'](ps,cam,675,250),(675,250));sheet.paste(im,(i*675,1470));label(i*675+15,1480,g.upper(),18)
 label(20,1732,'Same native frame and camera per row. CPU evidence only; native held/ADS/reload/10-20 display QA pending master.',19)
 return png(sheet),metrics

def generate(include_comparison=True):
 meshes,meta,ref=source_meshes();d=make_design(meta,ref);maps=paint_maps(meshes);atlas,m=compile_model(d,maps)
 n=len(m['elements']);assert 80<=n<=120
 out={ART+'design.json':encode(d),MODEL:encode(m),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,m,atlas))}
 metrics={}
 if include_comparison:out[ART+'comparison.png'],metrics=comparison(d,meshes,atlas,m)
 ps=np.concatenate([vertices(e) for e in m['elements']]);counts=dict(collections.Counter(s['group'] for s in d['parts']))
 review=f"""# Mindbender's Ambition (Adept) W147

{n} authored opaque cuboids / {n*6} independent face UVs / 1024 atlas. Groups: {counts}. Full-only; zero detachable magazine, triangle adapters, alpha body cards or raw island/voxel construction. Long eight-wall bore, lower tube, filled action, broad fore-end bone planes, thick hooked grip, true open trigger/grip loop, tapered rear bone stock and iron sight notch preserve identity. Bone grooves and actual Hive inscriptions are selected original diffuse relief in their own native positions, cleaned and recolored to the actual default photo's warm bone / blue-black metal / silver bands. No invented alphabet, random texture dirt or unrelated weapon dye.

The actual default photo, original diffuse maps, five-object FBX and old canonical were inspected. Inert binary FBX arrays [X,Z,Y] times original scale {meta['scale']} plus anchor {meta['anchor']} reproduce both original source and native bounds within 1e-6. Exactly 11516 textured triangles across five accepted objects, no excluded or silently omitted geometry. Original blend/FBX, all raw inputs and original model/texture hashes are pinned; shared migration manifests are not art inputs. Original shader Python was read as text only; no raw code, shader or DCC execution. Existing repository CPU helper is a pinned read-only dependency.

comparison.png contains actual default photo and raw-neutral / original canonical / authored side, front and rear oblique at identical scale per row. Detail panels show muzzle, forebone, guard and stock. Inspection project embeds final atlas and semantic named editable groups; no live app state changed. Full-only display transforms are copied exactly. No grip/muzzle anchor, gameplay, timing, input, HUD, registration, audio or reload split edits. Source envelope is preserved as a frame, with small deliberate organic-to-faceted silhouette differences recorded as actual bounds and image IoU rather than hidden refitting.

Pixel review: bone planes stay continuous; dark script remains on the barrel/action and silver sleeves; front walls preserve bore depth, and guard/stock/grip retain transverse depth in oblique views. Organic bone tips, engraved cavities and curved tube sections remain faceted/static. Fine scripts can soften at game distance. No native acceptance or performance claim: resource loading, 26.3 rotations, first/third person, ADS, full/per-shell reload and10-20display QA remain with master.
"""
 out[ART+'review.md']=review.encode()
 manifest=dict(id=ID,revision='W147',assembled_elements=n,opaque_cuboids=n,triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=n*6,max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=n*6,groups=counts,
  actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],source_objects=5,source_triangles=11516,textured_triangles=11516,canonical_display_exact=True,full_only=True,native_accepted=False,
  generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],comparison_metrics=metrics,output_sha256={p:sha(v) for p,v in out.items()},limitations=d['limitations'])
 out[ART+'manifest.json']=encode(manifest);return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
 scope=next(f['owned_paths'] for f in json.loads((ROOT/'docs/qa/2026-10-26/w147/batch.json').read_bytes())['features'] if f['name']=='w147-'+ID)
 out=generate();assert set(out)<=set(scope)
 for rel,data in out.items():
  target=ROOT/rel
  if a.verify:assert target.is_file() and target.read_bytes()==data,'Regeneration differs: '+rel
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 m=json.loads(out[ART+'manifest.json']);print(('Verified' if a.verify else 'Generated')+f" {len(out)} artifacts / {m['assembled_elements']} solids / {m['emitted_faces']} faces / full-only")
if __name__=='__main__':main()
