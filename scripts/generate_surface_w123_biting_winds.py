#!/usr/bin/env python3
"""W147 Biting Winds: authored semantic solids, independent opaque UV, exact W50 rest."""
import argparse,base64,collections,copy,hashlib,io,json,math,re,runpy,struct,subprocess,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='biting_winds'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/bow/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w147/{ID}-worker.md'
BATCH='docs/qa/2026-10-26/w147/batch.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/biting_winds/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/biting_winds.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
W50=runpy.run_path(str(ROOT/'scripts/generate_bow_models_w50.py'))
FACES=H['FACES'];EDGE=1024
PALETTE=dict(red=[194,37,32],blue=[92,160,192],ice=[168,205,218],steel=[164,174,178],dark=[42,48,52],black=[22,26,29],yellow=[215,184,66])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w147:biting_winds:'+n))
def native_rotation(e):
 r=e.get('rotation',{})
 if 'axis' in r:return dict(origin=r['origin'],**{a:r['angle'] if a==r['axis'] else 0 for a in 'xyz'})
 return r

def vertices(e):
 b=copy.deepcopy(e)
 if 'rotation' in b:b['rotation']=native_rotation(e)
 return H['vertices'](b)

class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 2.91 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12]==b'BLENDER-v291',data[:12]
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
 meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30'];path=RAW/'Biting Winds.blend'
 assert sha(path.read_bytes())==meta['source_files'][path.name]=='ae0c8100b1fc6616f4bc4ef55ca3467d137742aaca3001e20d638c9fc655ddbe'
 b=Blend(path);meshes=[];audit=[]
 for _,o in b.records('Object'):
  if b.field(o,'Object','type')!=1:continue
  name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
  mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert');matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
  v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
  world=(np.c_[v,np.ones(n)]@matrix)[:,:3];native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
  nl=b.field(mesh,'Mesh','totloop');loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(b.sizes['MLoop'],))
  uvs=np.ndarray((nl,2),'<f4',b.pointed(b.field(mesh,'Mesh','mloopuv')),strides=(b.sizes['MLoopUV'],4)).astype(float);uvs[:,1]=1-uvs[:,1]
  polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[]
  for i in range(b.field(mesh,'Mesh','totpoly')):
   start,count=struct.unpack_from('<ii',polys,b.sizes['MPoly']*i);assert count==3
   ix=[start,start+1,start+2];faces.append(loops[ix]);uv.append(uvs[ix])
  ptr=struct.unpack_from('<Q',b.pointed(b.field(mesh,'Mesh','mat')))[0];material=b.field(b.field(b.pointed(ptr),'Material','id'),'ID','name')[2:]
  retained=name in meta['source_objects'];assert retained or name in meta['excluded_objects']
  audit.append(dict(name=name,material=material,triangles=len(faces),retained=retained,reason='retained geometry' if retained else 'excluded reticle alternative'))
  if retained:meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material))
 pts=np.concatenate([m['vertices'] for m in meshes]);np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
 assert len(meshes)==8 and sum(len(m['faces']) for m in meshes)==meta['textured_triangles']==23528
 assert len(audit)==11
 return meshes,meta,audit

def source_triangles(meshes):
 textures={m:np.asarray(Image.open(RAW/(m+'_Diffuse.dds')).convert('RGBA')) for m in {s['material'] for s in meshes}};result=[]
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20);result.append((p,uv,textures[m['material']],n))
 return result

def model_triangles(model,textures):
 tex={k:np.asarray(v.convert('RGBA')) for k,v in textures.items()};result=[]
 for e in model['elements']:
  v=vertices(e);R=H['rotation'](native_rotation(e))
  for face,f in e['faces'].items():
   ps=v[list(FACES[face])];n=R@np.array(H['NORMALS'][face]);a,b,c,d=f['uv'];uv=np.array([[a,b],[c,b],[c,d],[a,d]])/16
   if f.get('rotation'):uv=np.roll(uv,-f['rotation']//90,axis=0)
   for ix in ((0,1,2),(0,2,3)):result.append((ps[list(ix)],uv[list(ix)],tex[f['texture'].lstrip('#')],n))
 return result

def make_design(meta,audit):
 parts=[]
 def c(name,pos,size,mat,group,motif='panel',turn=None):
  e=dict(name=name,**{'from':[a-b/2 for a,b in zip(pos,size)],'to':[a+b/2 for a,b in zip(pos,size)]})
  if turn:e['rotation']=dict(origin=list(pos),axis=turn[0],angle=turn[1],rescale=False)
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif,classification='rigid_body'))
 def beam(name,a,b,width,thick,mat,group,motif='panel',x=8):
  z0,y0=a;z1,y1=b
  c(name,[x,(y0+y1)/2,(z0+z1)/2],[width,thick,math.hypot(y1-y0,z1-z0)],mat,group,motif,('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
 def disc(name,y,z,r,width,mat,group,motif='cam',x=8):
  # Four filled crossing cuboids form a solid octagonal section, axial X.
  r=r/math.cos(math.pi/8)  # input radius is the exact Y/Z envelope half-span
  for i in range(4):c(name+f'_section_{i}',[x,y,z],[width,2*r*math.cos(math.pi/8),2*r*math.sin(math.pi/8)],mat,group,motif,('x',i*45))
 # Each limb is six long, fully filled broad segments. Color/inset is face paint.
 upper=[(2.12,18.08),(3.40,19.12),(5.20,20.08),(7.30,20.90),(9.55,21.42),(11.68,21.53)]
 lower=[(2.12,1.30),(3.40,.26),(5.20,-.65),(7.30,-1.40),(9.55,-1.85),(11.68,-1.94)]
 for tag,path in [('upper',upper),('lower',lower)]:
  for i,(a,b) in enumerate(zip(path,path[1:])):beam(f'{tag}_limb_span_{i}',a,b,.86,.40,'blue','limbs','limb')
  for i,(z,y) in enumerate([path[0],path[2]]):c(f'{tag}_limb_bridge_{i}',[8,y,z],[.92,.25,.22],'blue','limb_mounts','fastener')
 # Front limb hinges and their fork: true holes between structural members.
 for tag,yy,sgn in [('upper',18.08,-1),('lower',1.30,1)]:
  disc(tag+'_front_hinge',yy,2.25,.34,.94,'blue','limb_mounts','fastener')
  beam(tag+'_fork_loadbar',(2.35,yy),(5.70,yy+sgn*1.80),.78,.32,'blue','forks')
  beam(tag+'_fork_rearbar',(5.70,yy+sgn*1.80),(7.38,yy+sgn*2.72),.92,.60,'steel','forks')
  beam(tag+'_fork_bottom',(5.0,yy+sgn*3.08),(7.38,yy+sgn*2.72),.66,.28,'dark','forks')
  beam(tag+'_fork_short',(5.0,yy+sgn*3.08),(5.60,yy+sgn*1.87),.66,.24,'steel','forks')
 # Four physical cams, with hubs and axle caps. Solid width and octagonal side profile.
 for tag,y,z,r in [('upper_tip',21.40,11.65083090770372,1.19541688272511),('lower_tip',-2.22,11.65,1.1845831172748855),('upper_inner',15.48,10.18,.80),('lower_inner',4.11,10.18,.80)]:
  disc(tag+'_wheel',y,z,r,.55,'dark','cams')
  disc(tag+'_hub',y,z,r*.62,.73,'steel','cams')
  c(tag+'_axle',[8,y,z],[.93,.20,.20],'black','cams','fastener')
  if 'tip' in tag:beam(tag+'_limb_socket',(11.0,y),(12.35,y+.03),.82,.23,'blue','limb_mounts')
 # Central upper/lower tension arms; the long rail is structural, not a string.
 beam('upper_cam_support',(6.25,17.0),(10.20,15.55),.82,.48,'steel','cam_supports','slot')
 beam('upper_cam_lower_support',(6.10,14.83),(10.20,15.05),.68,.30,'dark','cam_supports')
 beam('lower_cam_support',(6.25,2.66),(10.20,4.10),.82,.48,'steel','cam_supports','slot')
 beam('lower_cam_upper_support',(6.10,4.64),(10.20,4.45),.68,.30,'dark','cam_supports')
 beam('upper_cam_front_knee',(6.25,17.0),(6.28,16.22),1.10,.50,'steel','cam_supports')
 beam('lower_cam_front_knee',(6.25,2.66),(6.12,3.40),1.10,.50,'steel','cam_supports')
 # Red forged riser: three large real windows, solid transversely through X.
 beam('upper_riser_shoulder',(6.28,16.22),(7.84,15.50),1.10,.70,'steel','upper_riser','warning')
 beam('upper_riser_red_back',(7.60,15.72),(7.65,14.20),1.08,.68,'red','upper_riser')
 beam('upper_riser_red_front',(6.12,15.04),(6.46,14.18),1.02,.57,'red','upper_riser')
 beam('upper_riser_red_heel',(6.46,14.18),(7.65,14.20),1.08,.43,'red','upper_riser')
 beam('upper_grip_back',(7.64,14.22),(7.64,10.21),.66,.40,'black','grip','grip')
 beam('upper_grip_front',(6.45,13.72),(6.45,10.85),.62,.35,'black','grip','grip')
 beam('grip_head',(6.45,13.72),(7.64,14.05),.78,.35,'red','grip')
 beam('grip_heel',(6.45,10.85),(7.64,10.21),.78,.38,'red','grip')
 beam('arrow_shelf',(6.32,10.02),(8.35,10.02),.97,.29,'steel','arrow_rest')
 beam('lower_riser_head',(6.65,9.65),(8.30,9.95),1.02,.43,'red','lower_riser')
 beam('lower_riser_back',(8.04,9.76),(7.90,7.54),.93,.40,'red','lower_riser')
 beam('lower_riser_front',(6.81,9.60),(6.63,7.50),.89,.37,'red','lower_riser')
 beam('lower_riser_midbridge',(6.63,7.50),(7.90,7.54),.94,.34,'red','lower_riser')
 beam('lower_riser_back_slope',(7.90,7.54),(7.28,5.61),.92,.42,'red','lower_riser')
 beam('lower_riser_front_slope',(6.63,7.50),(5.73,5.95),.89,.38,'red','lower_riser')
 beam('lower_riser_base',(5.73,5.95),(7.28,5.61),1.04,.45,'red','lower_riser','warning')
 beam('lower_riser_diagonal',(6.32,6.94),(7.65,6.40),.88,.29,'red','lower_riser')
 c('lower_riser_saddle',[8,5.12,6.25],[1.15,.74,1.60],'red','lower_riser','warning')
 c('lower_forward_counterweight',[8,5.43,5.10],[1.38,.45,1.16],'steel','counterweights','flute')
 # Lateral sight projects to the original thin-axis minimum. Open bracket, no reticle cards.
 c('sight_mount',[7.36,12.26,7.20],[.68,.30,2.60],'blue','sight','label')
 c('sight_vertical',[7.12,11.85,5.46],[.30,1.96,.22],'dark','sight')
 c('sight_crown',[7.10,12.80,5.58],[.44,.19,.68],'blue','sight')
 c('sight_heel',[7.10,10.92,5.58],[.44,.19,.68],'blue','sight')
 c('sight_front_post',[7.10,11.85,5.26],[.30,1.82,.14],'steel','sight')
 c('sight_adjustment_drum',[6.984509126303771,12.26,6.16],[.50,.36,.48],'steel','sight','fastener')
 c('draw_counter',[7.08,11.32,7.97],[.20,.68,.29],'dark','sight','counter')
 # Hand-contact pad and hinge yokes provide readable full-width thickness.
 c('hand_pad',[8.10,12.13,7.53],[.72,2.37,.48],'black','grip','grip')
 for tag,y,z in [('upper',16.18,6.12),('lower',4.72,6.12)]:
  c(tag+'_hinge_yoke',[8,y,z],[1.474722498237362,.48,.76],'steel','forks','fastener')
 original=json.loads((ROOT/BASE).read_bytes());moving=moving_rest(original)
 inputs=[BASE,SOURCE,ASSET+'textures/item/weapon/w30/biting_winds.png','scripts/generate_bow_models_w50.py',HELPER,'art/weapons/w31/references.json']
 inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT/(ASSET+'models/weapon_bow_w50')).glob('biting_winds_*_hip.json'))]
 raw=[RAW/'Biting Winds.blend',PHOTO]+[RAW/(m+'_Diffuse.dds') for m in ('Biting Winds Main','Biting Winds Scope','Draw Counter')]
 return dict(id=ID,revision='W147',family='bow',method='Authored semantic SOLID cuboids; no voxel/rip-island conversion or alpha body cards',source=meta,source_audit=audit,
  identity=['pale blue long compound limbs / silver inset','red openwork riser with actual windows','four dark cams with full solid axial depth','raised lateral sight and native arrow/string frame'],
  parts=parts,moving_element_names=[e['name'] for e in moving],moving_classification='Exact W50 parts(original, CONFIG[id])[1]; name added, #0 remapped to #original only',
  body_element_names=[s['geometry']['name'] for s in parts],body_classification='Rigid semantic body only; no baked string or arrow. Master filters moving_element_names for new W50 replacement2 body.',
  palette=PALETTE,atlas=dict(size=EDGE,gutter=2,texels_per_unit=23),input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
  original_texture=original['textures']['0'],default_photo_sha256=sha(PHOTO.read_bytes()),
  limitations=['Offline CPU art inspection only; native pack, first/third person, ADS, sequence and 10-20 displays pending master.','Clean default dye reconstruction, not original PBR.','Faceted cam/limb contours; exact W50 moving pieces retain historical voxel thickness and neutral atlas colors.','Static auxiliary source cables omitted from clean rigid body; exact W50 active string and arrow retained.'])

def moving_rest(original):
 moving=W50['parts'](original,W50['CONFIG'][ID])[1]
 for i,e in enumerate(moving):
  e['name']=f'moving_rest_{i:03}'
  for f in e['faces'].values():
   assert f['texture']=='#0';f['texture']='#original'
 return moving

def tile(s,face,w,h):
 u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h);p=vertices(s['geometry'])[list(FACES[face])]
 pos=((1-u)*(1-v))[:,:,None]*p[0]+(u*(1-v))[:,:,None]*p[1]+(u*v)[:,:,None]*p[2]+((1-u)*v)[:,:,None]*p[3]
 x,y,z=pos[:,:,0],pos[:,:,1],pos[:,:,2];rgb=np.broadcast_to(np.array(PALETTE[s['material']],float),(h,w,3)).copy()
 rgb*=(.98+.025*np.cos(v*math.pi))[:,:,None];edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.6]*=.78
 motif=s['motif'];side=face in ('east','west')
 if motif=='limb':
  if face in ('up','down'):
   inset=abs(x-8)<.25;rgb[inset]=PALETTE['steel'];rgb[abs(x-8)<.08]=PALETTE['dark']
  elif side:
   stripe=(v>.25)&(v<.69);rgb[stripe]=PALETTE['ice'];rgb[(v>.42)&(v<.53)]=PALETTE['steel']
 if motif=='cam' and side:
  p0=(np.array(s['geometry']['from'])+s['geometry']['to'])/2;r=np.hypot(y-p0[1],z-p0[2]);rr=np.max(r)
  rgb[(r>rr*.66)&(r<rr*.72)]*=.45;rgb[(r>rr*.77)&(r<rr*.83)]*=1.30
 if motif=='grip':rgb[(np.mod(y*6+z*.7,1)<.12)&(edge>1)]*=.67
 if motif=='flute':rgb[(np.mod(z*4,1)<.16)&(edge>2)]*=.55
 if motif=='slot' and side:rgb[(u>.15)&(u<.85)&(abs(v-.50)<.14)]=PALETTE['black']
 if motif=='warning' and side:
  stripe=(v>.30)&(v<.53)&(u>.12)&(u<.60);rgb[stripe]=PALETTE['yellow'];rgb[stripe&(np.mod(u*17,1)<.17)]*=.65
 if motif=='label' and side:
  rgb[(u>.24)&(u<.68)&(v>.39)&(v<.60)]=[193,202,204]
 if motif=='counter' and side:
  rgb[(v>.23)&(v<.74)&(u>.15)&(u<.85)]=[30,79,91]
 if motif=='fastener' and side:
  rr=np.sqrt(((u-.5)*2)**2+((v-.5)*2)**2);rgb[(rr>.33)&(rr<.57)]=PALETTE['black'];rgb[(rr>.42)&(rr<.48)]=PALETTE['steel']
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(26,32,37,255));requests=[]
 for s in d['parts']:
  for f,ix in FACES.items():
   p=vertices(s['geometry'])[list(ix)];w=max(5,math.ceil(np.linalg.norm(p[1]-p[0])*23));h=max(5,math.ceil(np.linalg.norm(p[3]-p[0])*23));requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;uvmap={};islands=[]
 for h,w,name,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'UV atlas overflow'
  atlas.paste(Image.fromarray(np.pad(np.asarray(tile(s,f,w,h)),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  rect=[x,y,x+w,y+h];uvmap[name,f]=[v*16/EDGE for v in rect];islands.append(dict(element=name,face=f,rect=rect));x+=w+4;row=max(row,h)
 es=[]
 for s in d['parts']:
  e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in FACES};es.append(e)
 original=json.loads((ROOT/BASE).read_bytes());es+=moving_rest(original)
 d['atlas'].update(used_height=y+row+2,islands=islands,face_islands=len(islands),policy='Independent opaque face islands, two pixel extrusion; body only. W50 moving copies use untouched original texture.')
 return atlas,dict(credit='W147 Biting Winds semantic body + exact W50 resting moving elements / offline',textures={'0':'destiny:item/weapon/w123/biting_winds','original':d['original_texture'],'particle':'destiny:item/weapon/w123/biting_winds'},display=copy.deepcopy(original['display']),elements=es)


def inspection(d,model,atlas):
 es=[];groups={};oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/biting_winds.png')).convert('RGBA');sizes=[(EDGE,EDGE),oldtex.size]
 specs={s['geometry']['name']:s for s in d['parts']}
 for e in model['elements']:
  b=copy.deepcopy(e);r=native_rotation(e);b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
  for f in b['faces'].values():
   ix=1 if f['texture']=='#original' else 0;f['texture']=ix;w,h=sizes[ix];f['uv']=[q*(w if i%2==0 else h)/16 for i,q in enumerate(f['uv'])]
  es.append(b);group=specs[e['name']]['group'] if e['name'] in specs else 'W50_exact_rest_moving';groups.setdefault(group,[]).append(b['uuid'])
 tex=[]
 for ix,im in enumerate([atlas,oldtex]):
  w,h=im.size;tex.append(dict(name='biting_winds_body.png' if ix==0 else 'biting_winds_w30_original.png',id=str(ix),uuid=uid('texture'+str(ix)),width=w,height=h,uv_width=w,uv_height=h,source='data:image/png;base64,'+base64.b64encode(png(im)).decode()))
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='W147 Biting Winds / editable semantic body + exact W50 rest',resolution=dict(width=EDGE,height=EDGE),elements=es,textures=tex,display=copy.deepcopy(model['display']),outliner=[dict(name=k,uuid=uid(k),origin=[8,8,8],rotation=[0,0,0],children=v,export=True) for k,v in groups.items()],destiny_w147=dict(nativeAccepted=False,movingElementNames=d['moving_element_names'],sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor']))


def comparison(d,ms,atlas,model):
 w,h=850,720;out=Image.new('RGB',(2550,2890),'#18212a');draw=ImageDraw.Draw(out)
 def label(x,y,s,size=22):draw.text((x,y),s,fill='#e8ebeb',font_size=size)
 label(20,12,'BITING WINDS / W147 / SEMANTIC SOLID BODY + EXACT W50 REST / OFFLINE ART',30)
 photo=Image.open(PHOTO).convert('RGB').crop((480,70,1370,980));photo.thumbnail((620,510));out.paste(photo,(20,55))
 texts=[f'{len(d["parts"])} rigid body + {len(d["moving_element_names"])} exact moving copies',
 'Default dye: red openwork / blue limbs / steel cams',
 'Actual BLEND: 8 retained, 3 reticles excluded, 23,528 triangles',
 'Source scale 22.000896462875446 / anchor [8,8,8]',
 'Body: 1024 opaque face atlas / moving: original w30 atlas',
 'Exact W50 string endpoints / arrow coordinates and UV',
 'Native parsing, holding, ADS, animation, 10-20: pending master']
 for i,t in enumerate(texts):label(690,85+i*55,t,24)
 label(20,590,'RAW BLEND / ORIGINAL UV / NEUTRAL DDS');label(w+20,590,'OLD CANONICAL / 250 CUBOIDS');label(2*w+20,590,'W147 BODY + W50 REST / 2 TEXTURES')
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/biting_winds.png'))
 tris=[source_triangles(ms),model_triangles(old,{'0':oldtex}),model_triangles(model,{'0':atlas,'original':oldtex})];pts=np.concatenate([m['vertices'] for m in ms])
 for row,(name,cam) in enumerate([('SIDE / EQUAL SCALE',[-1,0,0]),('FRONT OBLIQUE / EQUAL SCALE',[-1,.15,-.65]),('REAR OBLIQUE / EQUAL SCALE',[1,.15,.65])]):
  ext=H['frame'](pts,cam,w,h)
  for col,ts in enumerate(tris):
   im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);out.paste(im,(col*w,635+row*h));label(col*w+14,645+row*h,name,18)
 label(20,2820,'Pixel inspection: true riser/fork voids, filled transverse depth, separate exact W50 moving texture.',22)
 label(20,2853,'CPU views do not establish native load, lighting, gameplay, animation or 10-20-display performance.',22)
 return png(out)


def review_text(d,counts):
 return f"""# Biting Winds W147 — offline art review

{len(d['parts'])} rigid semantic cuboids plus 23 exact W50 resting moving copies. No triangle/contour adapters, rip islands, voxels or alpha body cards. The canonical assembly and largest existing W50 moving state remain below 1000. The source photo was opened as an actual image before authoring. Default identity: red openwork forged riser with real windows, pale blue long compound limbs with silver insets, four dark steel cams and raised lateral sight. Major rails and limbs are broad filled volumes; axial cam sections are solid octagons. Face paint carries insets, grip texture, recessed slots, restrained fasteners and warning strips. Independent opaque face islands with two pixel gutters avoid sharing the opposite-face markings. This applies the Ace87/Izanagi79 volume/UV study without borrowing motifs.

W50 contract: moving_rest_000 through moving_rest_022 are exactly parts(original, CONFIG['biting_winds'])[1], with names added and texture #0 remapped to #original. Coords, UVs, rotations, bridge and arrow rest stay unchanged. Native JSON and embedded BB project use two textures; #original points at the original w30 PNG. design.json explicitly lists body_element_names and moving_element_names. Master must filter the moving names to create NEW replacement2 W50 body_hip resources, then use unchanged historical W50 moving state resources. No historical W50 generator, model or item graph was edited. No static string was added to the rigid body; auxiliary raw static cables are omitted, not duplicated as a resting string.

Frame: original scale {d['source']['scale']}, anchor {d['source']['anchor']}, thin X, vertical Y and arrow -Z. Canonical display values are copied exactly. Rigid geometry is authored within the native source envelope; exact W50 endpoint/arrow coordinates constrain the rest assembly. No grip, muzzle, timing, input, third-person, audio, HUD or shared registry files changed.

Provenance: inert Blender2.91 SDNA arrays and stored object matrices, not bpy or source scripts/shaders. Eight retained and three excluded reticle alternatives; 23,528 textured triangles and native bounds rechecked. Original BLEND, DDS, photo, original JSON/BB/PNG and historical W50 hip states are pinned directly; no shared migration manifest is a provenance input. Raw neutral DDS is not claimed to reproduce the default shader.

comparison.png shows actual photo, raw BLEND/UV/DDS, old canonical, and new two-texture assembly in equal-scale side/front/rear oblique rows. inspection.bbmodel has editable cubes, semantic groups and both embedded textures with per-texture pixel UVs. No app/DCC was mutated. Faceted limb curves and cam profiles simplify sculpted contours. Historical W50 moving cuboids remain visibly thicker and more neutral than the photo. Their original lower string endpoint is Y=-0.560833 and upper Y=22.595417; these do not symmetrically meet the raw tip-cam centers. They are deliberately not extended, slimmed or recolored: changing them would violate the exact W50 rest contract. Native parser/pack, actual holding, ADS, draw/nock, audio and 10–20 simultaneous displays remain pending master. Offline renders are art evidence only.

Group counts: {json.dumps(counts,sort_keys=True)}.
"""


def generate():
 ms,meta,audit=source_meshes();d=make_design(meta,audit);atlas,model=compile_model(d);counts=dict(sorted(collections.Counter(s['group'] for s in d['parts']).items()))
 largest=max(len(json.loads(p.read_bytes())['elements']) for p in (ROOT/(ASSET+'models/weapon_bow_w50')).glob('biting_winds_*_hip.json') if '_body_' not in p.name)
 d['largest_existing_W50_moving_state']=largest;d['max_assembled_elements']=len(d['parts'])+largest;assert d['max_assembled_elements']<=1000
 pts=np.concatenate([vertices(e) for e in model['elements']]);outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode(),ART+'comparison.png':comparison(d,ms,atlas,model)}
 manifest=dict(id=ID,revision='W147',family='bow',body_elements=len(d['parts']),moving_elements=len(d['moving_element_names']),canonical_assembled_elements=len(model['elements']),largest_existing_W50_moving_state=largest,max_assembled_elements=d['max_assembled_elements'],max_allowed_elements=1000,triangle_adapter_elements=0,alpha_body_elements=0,body_faces=len(d['parts'])*6,groups=counts,texture_count=2,atlas_used_height=d['atlas']['used_height'],actual_bounds=[pts.min(0).tolist(),pts.max(0).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],canonical_display_exact=True,moving_exact_except_name_and_texture_slot=True,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),output_sha256={p:sha(v) for p,v in sorted(outputs.items())},native_accepted=False,limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w147-biting_winds');assert set(outputs)<=set(owned) and len(owned)==10
 return outputs


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args();outputs=generate()
 for rel,data in outputs.items():
  path=ROOT/rel
  if args.verify:assert path.is_file() and path.read_bytes()==data,'Regeneration differs: '+rel
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} assets; body {m["body_elements"]} + moving {m["moving_elements"]} = {m["canonical_assembled_elements"]}; largest assembled {m["max_assembled_elements"]}; 2 textures; native pending master')
if __name__=='__main__':main()
