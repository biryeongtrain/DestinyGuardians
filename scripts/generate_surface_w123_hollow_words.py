#!/usr/bin/env python3
"""Hollow Words W144: semantic solid remodel with deterministic face UV and inspection.
Inert FBX decoding; no rip scripts, shader execution, or live DCC. Seven owned products.
"""
import argparse, base64, copy, hashlib, io, json, math, re, runpy, struct, subprocess, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='hollow_words'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/fusion_rifle/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w144/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
BATCH='docs/qa/2026-10-26/w144/batch.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/hollow_words/extracted/Hollow Words')
PHOTO=Path('/tmp/destiny-weapons-w31/references/hollow_words.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
FACES=H['FACES']; EDGE=1024
PALETTE=dict(steel=[52,61,64],silver=[177,192,193],bronze=[145,117,84],teal=[24,67,64],edge=[42,49,52],black=[27,30,36],glass=[41,68,68])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w144:hollow_words:'+n))
def render_element(e):
 e=copy.deepcopy(e)
 if 'rotation' in e:
  r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return e
def vertices(e):return H['vertices'](render_element(e))
def model_triangles(m,tex):
 m=copy.deepcopy(m);m['elements']=[render_element(e) for e in m['elements']]
 return H['model_triangles']({'full':m},tex)

class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 3.0/3.1 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12] in (b'BLENDER-v300',b'BLENDER-v301'),data[:12]
        self.blocks={};pos=12
        while pos+24<=len(data):
            code,size,addr,dna,count=struct.unpack_from('<4sIQII',data,pos);pos+=24
            raw=data[pos:pos+size];pos+=size
            self.blocks[addr]=(code,dna,count,raw)
            if code==b'DNA1': self.dna=raw
            if code==b'ENDB': break
        d=self.dna;pos=0
        def tag(s):
            nonlocal pos
            assert d[pos:pos+4]==s;(pos:=pos+4)
        def integer():
            nonlocal pos
            v=struct.unpack_from('<I',d,pos)[0];pos+=4;return v
        def strings(n):
            nonlocal pos
            a=[]
            for _ in range(n):
                end=d.index(0,pos);a.append(d[pos:end].decode());pos=end+1
            pos=(pos+3)//4*4;return a
        tag(b'SDNA');tag(b'NAME');names=strings(integer())
        tag(b'TYPE');types=strings(integer());tag(b'TLEN')
        sizes=struct.unpack_from('<'+str(len(types))+'H',d,pos);pos+=2*len(types);pos=(pos+3)//4*4
        tag(b'STRC');n=integer();self.structs=[];self.fields={};self.sizes=dict(zip(types,sizes))
        for _ in range(n):
            ti,nf=struct.unpack_from('<HH',d,pos);pos+=4;fields={};offset=0
            for _ in range(nf):
                ft,fn=struct.unpack_from('<HH',d,pos);pos+=4;name=names[fn]
                count=math.prod(int(x) for x in re.findall(r'\[(\d+)\]',name))
                size=(8 if '*' in name else sizes[ft])*count
                key=re.sub(r'\[.*','',name).lstrip('*')
                fields[key]=(offset,types[ft],count,'*' in name,size);offset+=size
            assert offset==sizes[ti],(types[ti],offset,sizes[ti])
            self.structs.append(types[ti]);self.fields[types[ti]]=fields
    def field(self,raw,kind,name):
        off,typ,count,ptr,size=self.fields[kind][name]
        if ptr:return struct.unpack_from('<Q',raw,off)[0]
        fmts={'int':'i','short':'h','float':'f','double':'d','char':'b','uchar':'B','uint':'I'}
        if typ=='char':return raw[off:off+size].split(b'\0')[0].decode(errors='replace')
        if typ not in fmts:return raw[off:off+size]
        v=struct.unpack_from('<'+str(count)+fmts[typ],raw,off);return v[0] if count==1 else v
    def records(self,kind):
        for addr,(code,dna,count,raw) in self.blocks.items():
            if self.structs[dna]==kind:
                size=self.sizes[kind]
                for i in range(count):yield addr+i*size,raw[i*size:(i+1)*size]
    def pointed(self,addr):return self.blocks[addr][3]

def source_meshes():
 """Read-only binary FBX 7400/7500; object labels/materials are diagnosed explicitly."""
 meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
 reader=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_erentil_fr4.py'))['parse_fbx']
 for filename,digest in meta['source_files'].items():assert sha((RAW/Path(filename).name).read_bytes())==digest
 roots=reader(RAW/'Hollow Words.fbx');obs=next(n[2] for n in roots if n[0]=='Objects');byid={n[1][0]:n for n in obs}
 links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
 blend=Blend(RAW/'Hollow Words.blend');blend_objects={}
 for _,o in blend.records('Object'):
  if blend.field(o,'Object','type')!=1:continue
  name=blend.field(blend.field(o,'Object','id'),'ID','name')[2:]
  matrix=np.array(blend.field(o,'Object','obmat')).reshape(4,4)
  mesh=blend.pointed(blend.field(o,'Object','data'));nv=blend.field(mesh,'Mesh','totvert')
  v=np.ndarray((nv,3),'<f4',blend.pointed(blend.field(mesh,'Mesh','mvert')),offset=blend.fields['MVert']['co'][0],strides=(blend.sizes['MVert'],4)).astype(float)
  world=(np.c_[v,np.ones(nv)]@matrix)[:,:3]
  blend_objects[name]=(world,blend.field(mesh,'Mesh','totpoly'))
 meshes=[];excluded=[]
 for n in obs:
  if n[0]!='Geometry':continue
  model=byid[next(parent for child,parent in links if child==n[1][0])]
  name=model[1][1].split('\x00')[0];ch={c[0]:c for c in n[2]}
  # FBX exporter records -90 X / 100 scale. Geometry buffers are already
  # in the BLEND authoring basis; verify every vertex instead of guessing axes.
  props={p[1][0]:p[1][4:] for p in next(c[2] for c in model[2] if c[0]=='Properties70')}
  np.testing.assert_allclose(props['Lcl Rotation'],[-90,0,0],atol=1e-4,rtol=0)
  assert props['Lcl Scaling']==[100,100,100] and 'Lcl Translation' not in props
  raw=np.array(ch['Vertices'][1][0]).reshape(-1,3)
  np.testing.assert_allclose(raw,blend_objects[name][0],atol=1e-7,rtol=0)
  native=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
  ix=np.array(ch['PolygonVertexIndex'][1][0]);assert np.all(ix[2::3]<0)
  faces=np.where(ix<0,-ix-1,ix).reshape(-1,3);assert len(faces)==blend_objects[name][1]
  uvch={c[0]:c[1][0] for c in ch['LayerElementUV'][2]}
  assert uvch['MappingInformationType']=='ByPolygonVertex' and uvch['ReferenceInformationType']=='IndexToDirect'
  uv=np.array(uvch['UV']).reshape(-1,2)[np.array(uvch['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
  mats=[byid[c][1][1].split('\x00')[0] for c,p in links if p==model[1][0] and byid[c][0]=='Material']
  assert len(mats)<=1;material=mats[0] if mats else 'UNASSIGNED'
  m=dict(name=name,vertices=native,faces=faces,uv=uv,material=material,raw_bounds=[raw.min(0).tolist(),raw.max(0).tolist()],textured=material in ('Barrel','Scope'))
  if name in meta['excluded_objects']:excluded.append(m)
  else:assert name in meta['source_objects'],name;meshes.append(m)
 assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
 assert sorted(m['name'] for m in excluded)==sorted(meta['excluded_objects'])
 assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==12620
 assert sum(len(m['faces']) for m in meshes if m['textured'])==meta['textured_triangles']==8886
 assert sum(len(m['faces']) for m in excluded)==372
 assert set(blend_objects)=={m['name'] for m in meshes+excluded}
 pts=np.concatenate([m['vertices'] for m in meshes]);world=np.array([m['raw_bounds'] for m in meshes])
 np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-7,rtol=0)
 np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-7,rtol=0)
 ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID);assert sha(PHOTO.read_bytes())==ref['sha256']
 return meshes,meta

def source_triangles(meshes,auxiliary=False):
 textures={m:np.asarray(Image.open(RAW/(m+'_Diffuse.png')).convert('RGBA')) for m in ('Barrel','Scope')};result=[]
 for m in meshes:
  if m['textured']==auxiliary:continue
  tex=np.full((2,2,4),[110,82,123,255],np.uint8) if auxiliary else textures[m['material']]
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20);result.append((p,uv,tex,n))
 return result

def make_design(meta,meshes):
 parts=[]
 def c(name,pos,size,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
  if turn:e['rotation']=dict(origin=list(pos),axis=turn[0],angle=round(turn[1],7))
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def beam(name,a,b,width,depth,mat,group,motif='plain',x=8):
  z0,y0=a;z1,y1=b;angle=-math.degrees(math.atan2(y1-y0,z1-z0))
  c(name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(y1-y0,z1-z0)],mat,group,motif,('x',angle))
 def rim(name,y):
  # Eight walls leave a deep axial port, with an inset dark backstop.
  r=.58;t=.16
  for i in range(8):
   a=i*45;q=math.radians(a)
   c(name+'_wall_'+str(i),[8-(r-t/2)*math.sin(q),y+(r-t/2)*math.cos(q),-9.48],
    [2*r*math.tan(math.pi/8)+.006,t,.66],'steel','muzzle','muzzle',('z',a))
  c(name+'_backstop',[8,y,-9.10],[.87,.87,.10],'black','muzzle')
 # Deep continuous upper housing, with long bevels rather than source islands.
 c('upper_housing',[8,12.48,-1.40],[1.46,1.38,15.30],'teal','upper','marble')
 for sx in (-1,1):
  c('upper_roof_bevel'+str(sx),[8+sx*.65,13.13,-1.40],[.22,.22,15.30],'teal','upper','marble',('z',sx*45))
 c('upper_roof_silver',[8,13.27,-1.57],[1.46,.16,15.72],'silver','trim','braid')
 beam('upper_tail_sweep',[5.99,12.47],[6.48,12.32],1.40,1.28,'teal','upper','marble')
 beam('upper_tail_round',[6.38,12.34],[6.75,12.04],1.29,.93,'teal','upper','marble')
 c('upper_lower_black_rail',[8,11.77,-2.1],[1.48,.12,14.6],'black','upper','edge')
 # Lower channel tapers continuously. Its upper face is separated from the upper housing.
 beam('lower_long_housing',[-8.97,10.72],[.10,9.51],1.42,1.55,'black','lower','stars')
 beam('lower_upper_fill',[-8.98,11.05],[.10,10.75],1.42,1.05,'black','lower','stars')
 beam('lower_top_land',[-9.0,11.58],[.12,11.28],1.49,.15,'silver','lower','steelgrain')
 c('lower_rear_vertical',[8,10.05,.37],[1.46,2.43,.40],'silver','lower','silverflow')
 c('lower_nose_shoulder',[8,10.83,-8.80],[1.53,1.29,.50],'teal','lower','grooves')
 c('upper_nose_shoulder',[8,12.42,-8.80],[1.55,1.21,.50],'teal','upper','grooves')
 rim('upper_port',12.46);rim('lower_port',10.83)
 # Visible internal bridge is set back; the forward channel remains real air.
 c('channel_rear_bridge',[8,11.38,-.48],[.82,.93,1.20],'black','receiver')
 c('receiver_core',[8,11.22,5.00],[1.43,1.12,8.94],'black','receiver','receiver')
 c('receiver_front_drop',[8,10.46,2.83],[1.36,.79,3.52],'black','receiver','ribs')
 c('silver_energy_inset',[8,11.11,2.09],[1.49,.88,3.03],'silver','receiver','silverflow')
 # Elbow border is a real, substantial step in silhouette; fine nested lines are UV.
 for sx in (-1,1):
  beam('bronze_front_return'+str(sx),[.52,9.04],[.52,11.62],.13,.22,'bronze','trim','bronzelines',x=8+sx*.735)
  beam('bronze_elbow'+str(sx),[.52,11.53],[.88,11.88],.13,.25,'bronze','trim','bronzelines',x=8+sx*.735)
  beam('bronze_long_return'+str(sx),[.85,11.88],[5.96,11.88],.13,.23,'bronze','trim','bronzelines',x=8+sx*.735)
  beam('bronze_rear_curve'+str(sx),[5.92,11.88],[6.53,12.18],.13,.23,'bronze','trim','bronzelines',x=8+sx*.71)
 # Source hand region: broad forward grip and triangular rear brace, filled across X.
 beam('grip_front_solid',[1.30,4.15],[3.80,10.19],1.25,2.55,'black','grip','ribs')
 beam('grip_front_bevel',[.20,4.02],[2.38,10.03],1.05,.24,'edge','grip','gripedge')
 beam('grip_inner_bevel',[2.80,4.89],[5.10,10.03],1.14,.23,'edge','grip','gripedge')
 beam('grip_heel',[.24,3.99],[2.18,4.16],1.24,.31,'black','grip','ribs')
 beam('grip_lower_brace',[2.18,5.05],[9.71,6.91],1.20,.62,'black','guard','brace')
 beam('grip_lower_inner_rail',[3.05,5.47],[8.98,7.02],1.04,.18,'teal','guard','gripedge')
 beam('rear_guard_strut',[7.20,10.39],[10.78,4.96],1.15,.82,'black','guard','ribs')
 beam('rear_guard_inner_edge',[7.00,9.76],[9.00,6.94],1.01,.22,'edge','guard','gripedge')
 c('trigger_root',[8,10.07,6.93],[.30,.75,.33],'steel','guard','plain')
 beam('trigger_hook',[6.88,9.90],[6.64,9.26],.26,.22,'steel','guard')
 c('under_grip_cell',[8,4.35,3.70],[1.07,.95,3.54],'black','grip','stars')
 # Substantial rear shoulder with actual cutaway; no alpha card or hollow stock shell.
 beam('stock_neck',[6.98,12.06],[9.67,11.73],1.33,1.22,'black','stock','receiver')
 c('stock_beam',[8,11.57,12.05],[1.31,1.42,5.22],'teal','stock','stockmarble')
 c('stock_lower_rail',[8,10.78,12.05],[1.26,.21,5.35],'black','stock','ribs')
 beam('stock_hook',[14.36,12.31],[14.68,8.24],1.31,1.10,'black','stock','ribs')
 beam('stock_hook_front_sweep',[13.62,10.78],[14.57,8.31],1.26,.58,'black','stock','ribs')
 c('stock_comb_lip',[8,12.47,14.66],[1.32,.70,.61],'teal','stock','stockmarble')
 beam('stock_butt_pad',[15.01,12.43],[15.01,8.30],1.27,.20,'edge','stock','ribs')
 beam('stock_hook_top',[14.12,12.12],[14.66,12.51],1.30,.41,'teal','stock','stockmarble')
 # Continuous long top rail plus spaced teeth that affect the side silhouette.
 c('top_rail_spine',[8,13.48,-1.63],[1.19,.17,15.94],'black','rail','rail')
 for i in range(24):c('rail_tooth_'+str(i),[8,13.62,-9.18+i*.64],[1.22,.16,.22],'edge','rail','rail')
 c('optic_base',[8,13.81,3.37],[1.03,.24,3.10],'black','optic','rail')
 # Thick rectangular tube with beveled longitudinal shoulders: see-through, no invented glass plate.
 for sx in (-1,1):c('optic_wall_'+str(sx),[8+sx*.66,14.46,3.34],[.25,1.14,4.44],'black','optic','optic')
 c('optic_roof',[8,15.04,3.34],[1.18,.25,4.44],'black','optic','optic')
 c('optic_floor',[8,13.95,3.34],[1.18,.20,4.44],'black','optic','optic')
 for sx in (-1,1):
  for sy in (-1,1):c('optic_bevel_'+str(sx)+str(sy),[8+sx*.57,14.48+sy*.51,3.34],[.25,.25,4.44],'black','optic','optic',('z',sx*sy*45))
 inputs=[BASE,SOURCE,HELPER,REFS,'scripts/generate_surface_w123_erentil_fr4.py','scripts/generate_surface_w123_long_arm.py',ASSET+'textures/item/weapon/w30/hollow_words.png']+[BASE.replace('.json',suffix+'.json') for suffix in ('_ads','_twohand','_ads_twohand')]
 # Hash every original extracted file without changing it. No shared migration manifest pin.
 raws=sorted(p for p in RAW.rglob('*') if p.is_file())+[PHOTO]
 inventory=[dict(name=m['name'],material=m['material'],triangles=len(m['faces']),textured=m['textured']) for m in meshes]
 return dict(id=ID,revision='W144',construction='Author-placed filled semantic solids; no source-island, voxel or alpha-body conversion',
  parts=parts,source=meta,palette=PALETTE,full_only=True,muzzle_axis='-Z',hand_frame='Canonical anchor [8,8,8]; original scale, no recentering',
  starting_draft='Approximately 110 elements, expanded only for real port walls, shaped grip, optic tube and rail silhouette',
  identity=['stacked deep muzzle channels and forward daylight','continuous teal/gold marbled upper and rear stock','silver braid, bronze elbow border, silver energy inset','large triangular grip opening and short hooked rear shoulder'],
  atlas=dict(size=EDGE,gutter=2,texels_per_unit=20),
  openings=dict(forward_channel=[8,11.62,-5.0],triangle=[8,7.70,5.15],stock_cutaway=[8,9.60,12.0],optic=[8,14.48,3.34],upper_bore=[8,12.46,-9.5],lower_bore=[8,10.83,-9.5]),
  filled_probes=dict(grip=[8,7.5,3.1],stock=[8,11.57,12.0],upper=[8,12.48,-4],lower=[8,10.5,-5],receiver=[8,11.2,5]),
  source_matching=dict(method='Inert FBX + compressed BLEND 3.0 SDNA; [raw.X,raw.Z,raw.Y], all FBX vertices checked against stored-matrix BLEND 3.0 then W30 bounds',objects=len(meshes),triangles=12620,textured=8886,
   auxiliary_triangles=3734,raw_all_triangles=12992,excluded_reticle_glass_triangles=372,inventory=inventory,
   excluded=[dict(name='Hollow-Words.01.003',triangles=264,reason='W30 excluded FalsePromisesReticle'),dict(name='Hollow-Words.01.004',triangles=72,reason='W30 excluded FalsePromisesReticle'),dict(name='Hollow-Words.01.005',triangles=36,reason='W30 excluded ReticleGlass')]),
  default_photo_sha256=sha(PHOTO.read_bytes()),input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raws},
  limitations=['Offline CPU art only; native pack/held/ADS/charging/reload/audio/multi-display pending master.',
   'Opaque static authored marble/silver patterns approximate default shader, not dynamic PBR or animated Taken effects.',
   'Curves use faceted solids; reverse-side ornament follows the structural finish without invented text.'])

def tile(s,face,w,h):
 u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h);pts=vertices(s['geometry'])[list(FACES[face])]
 pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
 x,y,z=(pos[:,:,i] for i in range(3));mat=s['material'];motif=s['motif'];side=face in ('east','west')
 rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy();rgb*=(.98+.025*np.cos(v*math.pi))[:,:,None]
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
 if motif!='stars':rgb[edge<.70]*=.72;rgb[(edge>=.70)&(edge<1.5)]*=1.16
 if motif in ('marble','stockmarble'):
  # Flowing nested contours: deliberate material motif, never stochastic noise.
  flow=y*17+2.6*np.sin(z*1.5+y*3.4)+1.15*np.sin(z*3.1-y*4.7)
  q=np.mod(flow,2*np.pi)/(2*np.pi)
  rgb[:]=[16,45,43];rgb[(q>.12)&(q<.43)]=[31,76,70];rgb[(q>.47)&(q<.61)]=[62,82,57]
  rgb[(q>.65)&(q<.72)]=[123,110,68];rgb[(q>.74)&(q<.80)]=[46,81,72];rgb[(q>.86)&(q<.92)]=[10,28,31]
  if side:
   # Long inset silver gothic repeated filigree, photo-supported placement.
   zz=z if motif=='marble' else z-6.5
   mask=(zz>-.30)&(zz<5.65)&(y>12.34)&(y<12.88) if motif=='marble' else (z>10.25)&(z<13.9)&(y>11.50)&(y<11.99)
   yy=y-12.61 if motif=='marble' else y-11.75
   f=np.mod(zz*.98,1)-.5
   contour=abs(abs(yy)-(.065+.12*np.cos(f*6.28)))<.022
   rgb[mask&contour]=[171,187,182];rgb[mask&(abs(f)<.025)]=[113,143,139]
 if motif in ('ribs','brace','gripedge'):
  rgb[np.mod(y*6.7+z*.17,1)<.18]*=.59
  if motif=='gripedge':rgb[abs(u-.5)<.11]=[43,83,83]
  if side and s['geometry']['name']=='grip_front_solid':
   delta=z-(1.30+(y-4.15)*2.50/6.04)
   rib=(y>5.5)&(y<8.8)&(np.mod(y*1.15+z*.35,1)<.20)&(delta<.15)&(delta>-.95)
   rgb[rib]=[48,88,88]
  if motif=='brace' and side:rgb[(edge>2)&(edge<3.5)]=[54,93,92]
 if motif=='stars' and side:
  # The lower shroud has an engraved constellation/arc construction, not noise.
  for z0,y0,r in [(-7.2,10.15,.55),(-4.2,10.1,.65),(-1.6,9.68,.54),(3.9,4.35,.40)]:
   rr=np.hypot(z-z0,y-y0);rgb[abs(rr-r)<.015]=[99,115,113]
  line=(abs(y-(9.45+.24*(z+4.2)))<.016)|(abs(y-(10.75-.29*(z+4.2)))<.016)
  rgb[line]=[94,107,107]
  stars=(np.mod(z*.92+y*.33,1)<.045)&(np.mod(y*3.3-z*.05,1)<.12);rgb[stars]=[114,128,124]
 if motif=='braid':
  rgb*=(.84+.16*np.cos(z*16+y*4+x*6)**2)[:,:,None]
  rgb[np.sin(z*16+x*6+y*4)>.65]=[217,224,224]
 if motif=='silverflow':
  phase=np.sin(z*7+y*10)+.6*np.sin(z*15-y*7)+.4*np.cos(z*23+y*13)
  rgb*=(.82+.20*np.cos(phase*2.3))[:,:,None]
  rgb[abs(phase)<.11]=[218,225,220]
 if motif=='bronzelines':rgb[np.mod(y*25+z*25,1)<.26]*=.56
 if motif in ('receiver','optic','muzzle') and side:
  rgb[(edge>2)&(edge<3)]*=.55
  if motif=='receiver':
   slot=(z>5.2)&(z<6.7)&(y>11.13)&(y<11.30);rgb[slot]=[130,104,71]
  for zz,yy in [(5.8,11.1),(7.35,11.65),(1.72,14.5),(4.7,14.46)]:
   rr=np.hypot(z-zz,y-yy);rgb[(rr<.080)&(rr>.057)]=[77,89,87]
 if motif in ('grooves','rail'):rgb[np.mod(z*9+y*2,1)<.16]*=.48
 if motif=='steelgrain':rgb*=(.97+.025*np.sin(z*27+y*3))[:,:,None]
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(18,23,24,255));requests=[]
 for s in d['parts']:
  for f,ix in FACES.items():
   p=vertices(s['geometry'])[list(ix)];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*20));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*20))
   requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;islands=[];uvmap={}
 for h,w,name,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'UV atlas overflow'
  atlas.paste(Image.fromarray(np.pad(np.asarray(tile(s,f,w,h)),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  rect=[x,y,x+w,y+h];uvmap[name,f]=[a*16/EDGE for a in rect];islands.append(dict(element=name,face=f,rect=rect));x+=w+4;row=max(row,h)
 es=[]
 for s in d['parts']:
  e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in FACES};es.append(e)
 d['atlas'].update(used_height=y+row+2,islands=islands,face_islands=len(islands),paint_policy='Opaque independent faceUV, continuous teal marble, silver braid, constellation etching and bronze border')
 return atlas,dict(credit='Hollow Words W144 / semantic filled solids and default-photo face UV / full only',
  textures={'0':'destiny:item/weapon/w123/hollow_words','particle':'destiny:item/weapon/w123/hollow_words'},
  display=copy.deepcopy(json.loads((ROOT/BASE).read_bytes())['display']),elements=es)


def inspection(d,model,atlas):
 es=[];groups={}
 for s,e in zip(d['parts'],model['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
   origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
  for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
  es.append(b);groups.setdefault(s['group'],[]).append(b['uuid'])
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Hollow Words W144 / editable full solid inspection',
  resolution=dict(width=EDGE,height=EDGE),elements=es,display=copy.deepcopy(model['display']),
  outliner=[dict(name=n,uuid=uid(n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],
  textures=[dict(name='hollow_words.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
   source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
  destiny_w144=dict(nativeAccepted=False,fullOnly=True,sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor']))


def comparison(d,ms,atlas,model):
 w,h=1000,370;out=Image.new('RGB',(3000,2170),'#18212a');draw=ImageDraw.Draw(out)
 def label(x,y,text,size=22):draw.text((x,y),text,fill='#e8ebeb',font_size=size)
 label(20,12,'HOLLOW WORDS / W144 / SEMANTIC SOLIDS + OPAQUE FACE UV / OFFLINE ART',30)
 photo=Image.open(PHOTO).convert('RGB').crop((700,135,1880,850));photo.thumbnail((1040,505));out.paste(photo,(20,57))
 lines=[f'{len(model["elements"])} filled cuboids / full-only canonical frame / 0 adapters',
  'Actual photo: teal/gold marble, silver braid, bronze return, black ribs',
  'FBX: 12,620 retained = 8,886 textured + 3,734 FX/unassigned',
  '372 W30-excluded reticle/glass triangles separately diagnosed',
  '[X,Z,Y] mapping verified against exact W30 source/native bounds',
  'Forward slot, triangle, stock cutaway, bores, optic are physical air',
  '1024 opaque atlas / independent face UV / two-pixel gutters',
  'Pack load, held views, ADS, charge/fire, reload, sound, 10-20: pending']
 for i,text in enumerate(lines):label(1110,76+i*48,text,22)
 # Explicit auxiliary render accounts for all nontextured retained geometry.
 aux=source_triangles(ms,auxiliary=True);pts=np.concatenate([m['vertices'] for m in ms]);cam=[-1,.1,-.2]
 im,_=H['render'](aux,cam,H['frame'](pts,cam,700,175),(700,175),raw=True);out.paste(im,(2250,382));label(2258,390,'3734 FX / UNASSIGNED (diagnostic purple)',16)
 label(20,578,'ACTUAL FBX / 8886 TEXTURED TRIANGLES / NEUTRAL DIFFUSE')
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/hollow_words.png'))
 label(w+20,578,f'CANONICAL W30 / {len(old["elements"])} VOXEL CUBOIDS / READ ONLY')
 label(2*w+20,578,f'W144 / {len(model["elements"])} AUTHORED FILLED CUBOIDS')
 ts=[source_triangles(ms),model_triangles(old,oldtex),model_triangles(model,atlas)]
 d['comparison_views']=[]
 for row,(name,cam) in enumerate([('SIDE / EQUAL CAMERA AND SCALE',[-1,0,0]),('FRONT OBLIQUE / EQUAL CAMERA AND SCALE',[-1,.42,-.60]),('REAR OBLIQUE / EQUAL CAMERA AND SCALE',[1,.40,.60])]):
  ext=H['frame'](pts,cam,w,h);d['comparison_views'].append(dict(name=name,camera=cam,center=ext[0].tolist(),scale=float(ext[1])))
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);out.paste(im,(col*w,615+row*h));label(col*w+14,625+row*h,name,18)
 for i,(groups,title,cam) in enumerate([(['muzzle','lower','upper'],'TWIN RECESSED PORTS',[.25,.17,-1]),
  (['receiver','grip','guard'],'REAL TRIANGLE + FILLED GRIP',[-1,.20,-.15]),
  (['optic','rail'],'OPEN OPTIC + SOLID WALLS',[.3,.2,-1]),
  (['upper','stock','trim'],'FACE UV / MARBLE + SILVER TRIM',[-1,.30,-.35])]):
  names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups};es=[e for e in model['elements'] if e['name'] in names];pp=np.concatenate([vertices(e) for e in es])
  im,_=H['render'](model_triangles(dict(elements=es),atlas),cam,H['frame'](pp,cam,750,350),(750,350));out.paste(im,(i*750,1760));label(i*750+13,1770,title,18)
 label(20,2130,'Actual raw neutral diffuse is not the default shader. CPU art inspection only; no native, gameplay, audio or performance acceptance claimed.',21)
 return png(out)

def review_text(d,counts):
 return f"""# Hollow Words W144 — offline product art review

{len(d['parts'])} author-placed filled cuboids; {len(d['parts'])*6} explicit opaque face UVs; zero triangle adapters, alpha silhouette plates or split resources. Initial ~110-part blockout was kept near that range: twin real octagonal port rims, shaped structural grip/brace, hollow optic and rail teeth justify their separate elements. No rip connected components or voxel shells are used as design units. The 1000 ceiling is a cap, not a target.

Actual default-dye photo `{PHOTO}` was opened. Identity: stacked upper/lower channels with long daylight, continuous teal/gold marbled top and shoulder, silver twisted trim, bronze stepped elbow, bright silver inset, dark ribbed triangular grip frame, raised rectangular optic and short hooked butt. Contour marble, repeated metallic filigree, panel etching and grip ribs use face paint. Large housings/grips/stock remain full-depth solids. Muzzle bores, forward slot, triangular guard, rear stock cutaway and optic sight tunnel are real air. Ace87/Izanagi79 construction guidance was applied without importing their weapon identity.

Source: inert binary FBX reader, no embedded code or shader execution and no live DCC. All 15 retained W30 objects / 12,620 triangles match; 8,886 textured triangles use original Barrel/Scope UVs and neutral diffuse. 3,240 TakenEffect triangles + 494 unassigned optic/dot triangles = 3,734 auxiliary triangles, shown separately in diagnostic purple. All 3 W30-excluded reticle/glass objects total 372, making 12,992 raw FBX triangles. Nothing silently disappears from the inventory. Compressed BLEND 3.0 was decoded inertly using an adapted Long Arm SDNA reader. Every FBX geometry vertex matches the corresponding stored-matrix BLEND vertex within 1e-7, and per-object triangle counts match. FBX exporter model records (-90 X, scale 100) were diagnosed explicitly; the raw buffers already share the BLEND authoring basis, whose object matrices are identity. No exporter transform was blindly reapplied. The weapon-specific [raw.X,raw.Z,raw.Y] mapping matches W30 source/native bounds, unlike Erentil's mapping. All extracted originals are hash-pinned and untouched.

Exact source scale {d['source']['scale']}, anchor {d['source']['anchor']}, canonical display and hand coordinate frame remain. Native -Z muzzle direction is retained. Only the full `weapon_surface_w123/hollow_words` candidate is emitted; master owns canonical fusion_rifle/hollow_words integration, registries and shared systems. ADS, twohand, charging, generic reload, timing and sounds are unchanged. No shared migration manifest is pinned.

comparison.png includes actual-photo crop, original textured FBX, canonical W30, new solids at equal camera/scale in side/front/rear rows, auxiliary accounting and depth closeups. inspection.bbmodel embeds the exact atlas, editable cubes and semantic groups. Final comparison was opened for offline inspection; this is not a game screenshot.

Finish limits: structured static teal/bronze/silver face paint approximates the default shader; animated Taken/PBR/refraction are not recovered. Tiny reverse-side relief is simplified; circles/curves are faceted. Native pack/parser, first/third-person contact, ADS/optic visibility, charging/fire, generic reload/ammo return, sounds and 10–20 simultaneous displays remain pending master. No Gradle, native client, CU, Vision or live DCC was run. Test results and export evidence are in the worker report.

Group counts: {json.dumps(counts,sort_keys=True)}.
"""


def generate():
 ms,meta=source_meshes();d=make_design(meta,ms);atlas,model=compile_model(d);counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
 comp=comparison(d,ms,atlas,model)
 points=np.concatenate([vertices(e) for e in model['elements']]);outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
  ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 outputs[ART+'comparison.png']=comp
 manifest=dict(id=ID,revision='W144',family='fusion_rifle',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
  emitted_faces=len(model['elements'])*6,triangle_adapter_elements=0,contour_elements=0,alpha_body_elements=0,max_assembled_elements=1000,
  full_only=True,groups=counts,texture_size=[EDGE,EDGE],face_uv_islands=len(d['atlas']['islands']),atlas_used_height=d['atlas']['used_height'],
  actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],
  source_matching=d['source_matching'],native_pending=['resource parser/pack load','first/third person hand contact','ADS sight tunnel visibility','fusion charging/fire/muzzle','generic reload/ammo timing','sounds/listening','10-20 simultaneous displays'],default_photo_sha256=d['default_photo_sha256'],canonical_display_exact=True,
  existing_ADS_twohand_reload_audio_gameplay_unchanged=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
  generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),
  output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w144-hollow_words')
 assert set(outputs)<=set(owned) and len(outputs)==7
 assert len(model['elements'])<=1000
 return outputs


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args();outputs=generate()
 for rel,data in outputs.items():
  path=ROOT/rel
  if args.verify:assert path.is_file() and path.read_bytes()==data,'Regeneration differs: '+rel
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; {m["assembled_elements"]} filled cuboids / {m["emitted_faces"]} faces; full only; 0 adapters')
 print(f'1024 atlas used height {m["atlas_used_height"]}; payload {sum(len(v) for v in outputs.values())} bytes; native pending master')
if __name__=='__main__':main()
