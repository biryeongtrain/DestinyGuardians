#!/usr/bin/env python3
"""W149 Deafening Whisper: deterministic authored solids, inert source evidence, full only."""
import argparse,base64,copy,gzip,hashlib,io,json,math,re,runpy,struct,uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='deafening_whisper'; REV='W149'
ART=f'art/weapons/w123/{ID}/'; ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/grenade_launcher/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w149_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w149/{ID}-worker.md'
REFS='art/weapons/w31/references.json'; BATCH='docs/qa/2026-10-26/w149/batch.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/deafening_whisper/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/deafening_whisper.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER)); FACES=H['FACES']; EDGE=1024
PALETTE=dict(silver=[154,158,156],light=[187,191,188],steel=[64,69,69],black=[25,30,30],recess=[13,19,20],wrap=[68,75,67],rim=[108,117,115],red=[198,32,24],violet=[137,135,213],screen=[23,47,42])
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

class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 3.1 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
        assert data[:12]==b'BLENDER-v293',data[:12]
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
    """Retained meshes only, stored matrices + SDNA strides, never bpy/shaders."""
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    path=RAW/"Deafening Whisper.blend"
    assert sha(path.read_bytes())==meta['source_files'][path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),
            offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        axes=meta['source_axis']; thin=axes['thin']; length=axes['length']; vertical=next(i for i in range(3) if i not in (thin,length))
        assert axes['muzzle_sign']==-1
        native=world[:,[thin,vertical,length]]*meta['scale']+meta['anchor']
        nl=b.field(mesh,'Mesh','totloop')
        loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(b.sizes['MLoop'],))
        uvs=np.ndarray((nl,2),'<f4',b.pointed(b.field(mesh,'Mesh','mloopuv')),strides=(b.sizes['MLoopUV'],4)).astype(float)
        uvs[:,1]=1-uvs[:,1];polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[]
        for i in range(b.field(mesh,'Mesh','totpoly')):
            start,count=struct.unpack_from('<ii',polys,b.sizes['MPoly']*i)
            assert count==3,count
            ix=[start,start+1,start+2];faces.append(loops[ix]);uv.append(uvs[ix])
        ptr=struct.unpack_from('<Q',b.pointed(b.field(mesh,'Mesh','mat')))[0]
        material=b.field(b.field(b.pointed(ptr),'Material','id'),'ID','name')[2:]
        meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material,
            world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
    pts=np.concatenate([m['vertices'] for m in meshes]);world=np.array([m['world_bounds'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==30564
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta


def make_design(meta,meshes):
 parts=[]
 def c(name,pos,size,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
  if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=turn[1])
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def beam(name,a,b,width,depth,mat,group,motif='plain'):
  dy=b[1]-a[1];dz=b[2]-a[2];angle=-math.degrees(math.atan2(dy,dz))
  if angle>90:angle-=180
  if angle< -90:angle+=180
  c(name,[(x+y)/2 for x,y in zip(a,b)],[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',angle))
 def tube(name,x,y,z0,z1,r,t,mat,group,motif='plain'):
  for i in range(8):
   a=i*45;q=math.radians(a);rr=r-t/2
   c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
    [2*r*math.tan(math.pi/8)+.012,t,z1-z0],mat,group,motif,('z',a))
 def octsolid(name,x,y,z0,z1,r,mat,group,motif='plain'):
  for i in range(4):c(f'{name}_{i}',[x,y,(z0+z1)/2],[2*r,2*r*math.tan(math.pi/8),z1-z0],mat,group,motif,('z',i*45))
 # Long hollow launcher tube: structural walls, deep bore, filled rear breech.
 tube('barrel',8,12.94,-9.27,10.48,1.48,.30,'silver','barrel','silver_tube')
 tube('muzzle_lip',8,12.94,-9.344,-8.97,1.53,.25,'light','muzzle','machined')
 octsolid('breech',8,12.94,8.95,10.55,1.43,'steel','receiver','breech')
 # Two broad woven sleeves and their structural divider; weave is face UV.
 tube('front_mesh_wrap',8,12.94,-6.28,-3.87,1.65,.22,'wrap','wrap','weave')
 tube('rear_mesh_wrap',8,12.94,-3.48,-.48,1.72,.29,'wrap','wrap','weave')
 tube('wrap_divider',8,12.94,-3.87,-3.48,1.75,.32,'silver','wrap','machined')
 # Continuous top structure and rear paired stock rails track the original frame.
 c('top_sight_rail',[8,14.63,-2.72],[1.22,.23,5.45],'black','receiver','rail')
 c('rear_top_plate',[8,14.65,4.25],[1.45,.21,4.02],'steel','receiver','rail')
 c('lower_receiver',[8,11.32,6.76],[1.43,.46,7.48],'black','receiver','receiver')
 c('rear_lower_lip',[8,11.13,9.36],[1.49,.22,2.40],'rim','receiver','rail')
 for side in (-1,1):
  c(f'stock_upper_rail_{side}',[8+side*.44,14.30,12.58],[.24,.40,5.893523114],'steel','stock','rail')
 beam('stock_butt',[8,14.26,15.263017095],[8,8.63,14.713017095],1.28,.53,'black','stock','butt')
 beam('stock_butt_inlay',[8,13.78,15.313017095],[8,8.85,14.853017095],.60,.20,'rim','stock','butt')
 c('stock_neck',[8,13.34,10.56],[1.38,2.19,.48],'steel','stock','stock_neck')
 # Broad solid grips preserve source hand frame and front vertical handhold.
 c('front_grip_socket',[8,11.25,-3.03],[1.24,.35,1.28],'black','foregrip','socket')
 c('front_grip',[8,9.69,-3.04],[1.07,2.94,1.36],'black','foregrip','grip')
 c('front_grip_heel',[8,8.27,-3.04],[1.11,.31,1.40],'steel','foregrip','grip')
 beam('pistol_grip',[8,11.14,6.67],[8,7.57,8.55],1.07,1.60,'black','grip','grip')
 c('pistol_grip_heel',[8,7.67344392,8.56],[1.12,.45,1.68],'black','grip','grip',('x',28))
 beam('trigger',[8,11.03,5.74],[8,9.72,5.52],.22,.23,'steel','trigger','plain')
 # Source has a hanging trigger, not a complete invented guard.
 c('trigger_socket',[8,11.10,5.66],[.55,.32,.61],'black','trigger','socket')
 # Real underbarrel red unit, solid body, inset matte red front; not animated.
 octsolid('laser_housing',8,10.71,-9.33,-6.94,.37,'steel','underbarrel','machined')
 octsolid('laser_tip',8,10.71,-9.473238443,-9.33,.25,'red','underbarrel','red')
 c('laser_mount',[8,11.20,-7.74],[.65,.32,1.77],'black','underbarrel','rail')
 beam('laser_cable_a',[8,10.73,-6.95],[8,10.73,-6.12],.13,.13,'black','underbarrel')
 beam('laser_cable_b',[8,10.73,-6.12],[8,11.35,-5.59],.13,.13,'black','underbarrel')
 # Source side display is a protruding rectangular module (not a body side card).
 c('counter_housing',[9.77,12.94,.86],[.68,1.75,3.12],'steel','counter','counter_housing')
 c('counter_recess',[10.14,12.94,.86],[.18,1.37,2.62],'screen','counter','counter')
 for s in (-1,1):
  c(f'counter_rail_{s}',[10.10,12.94+s*.79,.86],[.29,.15,3.13],'rim','counter','rail')
  c(f'wrap_side_rail_{s}',[8+s*1.76,12.78,-2.12],[.32,.30,3.70],'steel','wrap','rail')
 c('left_wrap_latch',[6.23,12.85,.02],[.35,.90,.65],'steel','wrap','latch')
 # Tall actual rectangular sight frame: no lens/reticle alpha plane.
 # Center ray y15.86 is above every body and stock volume.
 c('sight_plinth',[8,14.94,-1.83],[1.16,.33,2.32],'black','sight','rail')
 for s in (-1,1):
  c(f'sight_upright_{s}',[8+s*.49,16.26,-1.416],[.16,2.64,.23],'black','sight','sight')
 c('sight_top',[8,17.57,-1.416],[1.14,.1874744,.23],'steel','sight','sight')
 c('sight_bottom',[8,15.05,-1.416],[1.14,.18,.23],'steel','sight','sight')
 c('sight_pin',[8,15.46,-1.416],[.085,.64,.095],'light','sight','sight')
 c('sight_pin_tip',[8,15.80,-1.416],[.10,.07,.10],'violet','sight','sight')
 c('sight_wheel_base',[8,15.02,-2.83],[.94,.19,.76],'steel','sight','dial')
 c('sight_wheel',[8,15.17,-2.83],[.82,.17,.82],'rim','sight','dial',('y',45))
 c('rear_indicator',[8,14.39,9.58],[.37,.12,.43],'violet','receiver','plain')
 inputs=[BASE,SOURCE,REFS,HELPER,'scripts/generate_surface_w123_long_arm.py','scripts/generate_surface_w123_edge_transit.py',ASSET+'textures/item/weapon/w30/'+ID+'.png']
 raws=[RAW/'Deafening Whisper.blend',RAW/'Deafening Whisper Main_Diffuse.dds',RAW/'Deafening Whisper Scope_Diffuse.dds',RAW/'Ammo Counter_Diffuse.dds',PHOTO]
 reference=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
 return dict(id=ID,revision=REV,method='hand-authored semantic solid cuboids with opaque face-specific UV; no voxel, mesh-island or connected-component conversion',
  source=meta,reference=reference,palette=PALETTE,parts=parts,
  source_matching=dict(method='inert gzip Blender 2.93 SDNA; each stored object obmat applied; source_axis selects native basis',objects=len(meshes),triangles=sum(len(m['faces']) for m in meshes),object_transforms={m['name']:m['object_matrix'] for m in meshes},excluded_preserved=meta['excluded_objects']),
  identity=['long silver launcher tube / recessed open muzzle','two dark woven sleeves and narrow silver divider','vertical foregrip and swept pistol grip','paired rear rails and deep open butt frame','side counter / underbarrel red unit / tall open rectangular sight'],
  ads_sight=dict(sightCenter=[8,15.86,-1.416],forwardPoint=[8,15.86,-3.416],eyeSide='+Z',plane='XY',style='optic',
   aperture=dict(x=[7.59,8.41],y=[15.14,17.476],z=[-1.531,-1.301]),pinTop=[8,15.835,-1.416],
   notes='Source tall rectangular reflex frame; excluded source Ret cards stay excluded. No opaque glass. Small pale pin with violet tip immediately below open -Z eye ray; body and butt remain below y14.8.'),
  coordinate_policy=dict(basis='world[thin=0,vertical=2,length=1], native muzzle -Z; stored object matrices applied before scale/anchor',source_axis=meta['source_axis'],scale=meta['scale'],anchor=meta['anchor'],bore_axis=[8,12.94],
   grip_top=[8,11.14,6.67],grip_heel=[8,7.57,8.55],display='exact canonical dictionary including all hip transforms',export='full only; existing generic reload; no new split or animation'),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raws},
  limitations=['Offline CPU art review only; master owns pack/native parser, held/ADS/generic reload and 10-20 displays.',
   'Static authored matte default-photo colors; no PBR/refraction/emission reconstruction.',
   'Octagonal tube, simplified grip curves and weave; opposite markings omitted when unobserved.',
   'Retained source Ammo Counter/Glass/Map components guide static UV modules; excluded Ret planes are not restored.'])

def world_points(e,face,w,h):
 p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
 q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
 return u,v,q

def tile(spec,face,w,h):
 u,v,q=world_points(spec['geometry'],face,w,h);x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
 mat=spec['material'];motif=spec['motif'];rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
 r=spec['geometry'].get('rotation',{});normal=H['rotation']({r.get('axis','z'):r.get('angle',0)})@np.array(H['NORMALS'][face])
 side=abs(normal[0])>.55;end=abs(normal[2])>.8
 # Coherent quiet material, no random grime or projected rip noise.
 rgb*=(.98+.025*np.cos((y-12.9)*.8))[:,:,None]
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
 if motif not in ('breech','red'):
  rgb[edge<.65]*=.82;rgb[(edge>.65)&(edge<1.45)]*=1.06
 def seam(mask):rgb[mask]=np.array(PALETTE['steel'])*.87
 def screw(zc,yc,r=.085):
  rr=np.hypot(z-zc,y-yc);rgb[rr<r]=PALETTE['rim'];rgb[rr<r*.62]=PALETTE['black'];rgb[(rr<r*.42)&(abs(z-zc)<.015)]=PALETTE['silver']
 # Axis-based surface coordinates continue weave across each octagonal side.
 if motif=='weave':
  circum=np.arctan2(x-8,y-12.94)*1.64
  a=np.mod(circum*2.25+z*1.13,1);b=np.mod(circum*2.25-z*1.13,1)
  holes=(a>.19)&(a<.81)&(b>.19)&(b<.81)
  rgb[:]=PALETTE['black'];rgb[holes]=PALETTE['wrap'];rgb[((a<.10)|(b<.10))]=np.array(PALETTE['rim'])*.74
  rgb[(z< -6.14)|((z> -3.62)&(z< -3.48))|(z>-.62)]=PALETTE['steel']
 if motif=='silver_tube':
  # Source photo's rear ribbed collar and narrow machined boundary rings.
  rib=(z>6.48)&(z<7.38)
  rgb[rib]=PALETTE['black'];rgb[rib&(np.mod(z*17,1)<.30)]=PALETTE['rim']
  seam((abs(z+8.69)<.026)|(abs(z+8.39)<.026)|(abs(z-3.98)<.035)|(abs(z-9.08)<.027))
  rgb[(z>10.05)]=PALETTE['steel']
  if side:
   for zc,yc in [(-7.8,12.40),(2.95,13.2),(8.78,13.8)]:screw(zc,yc)
   # Photo-backed front moth-like crossed emblem; only on the observed left side.
   if normal[0]<-.55:
    dz=z+7.38;dy=y-13.18
    mark=(abs(dz)<.40)&(abs(dy)<.40)&((abs(dy-dz)<.045)|(abs(dy+dz)<.045)|(abs(dz)<.032))
    rgb[mark]=PALETTE['light']
    for j in range(3):rgb[(abs(z+7.55-j*.17)<.028)&(y>12.45)&(y<12.62)]=PALETTE['light']
    # Restrained rear observed vertical markings without invented text.
    for zc in (5.36,8.24):
     rgb[(abs(z-zc)<.045)&(abs(y-13.10)<.32)]=PALETTE['light']
     rgb[(abs(abs(z-zc)-.18)<.028)&(abs(y-12.91)<.11)]=PALETTE['light']
 if motif=='silver_tube' and face=='down':
  rgb[:]=PALETTE['black'];rgb[np.mod(np.arctan2(y-12.94,x-8)*9,1)<.13]=PALETTE['steel']
 if motif=='machined':
  rgb[np.mod(z*24,1)<.12]*=.73
  if end:rgb[np.mod(np.arctan2(y-12.94,x-8)*12,1)<.10]*=.76
 if motif=='grip' and side:
  rgb[(u>.10)&(u<.90)&(v>.08)&(v<.92)]*=.83
  rgb[((abs(u-.11)<.012)|(abs(u-.89)<.012))&(v>.08)&(v<.92)]=PALETTE['steel']
  for zc,yc in [(-3.04,10.53),(7.02,10.40),(8.30,7.98)]:screw(zc,yc,.10)
 if motif in ('rail','stock_neck'):
  rgb[(np.mod(z*7,1)<.18)&(v>.15)&(v<.85)]*=.63
 if motif=='butt' and side:
  rgb[(u>.38)&(u<.62)&(v>.14)&(v<.85)]=PALETTE['steel']
  rgb[(u>.44)&(u<.56)&(v>.45)&(v<.74)]=PALETTE['rim']
 if motif=='counter' and side:
  rgb[:]=PALETTE['screen'];rgb[(v<.1)|(v>.9)|(u<.06)|(u>.94)]=PALETTE['black']
  rgb[(np.mod(v*15,1)<.06)&(u>.1)&(u<.90)]*=1.23
  # Static observed zero on the source counter, not a runtime ammo display.
  rr=((u-.52)/.055)**2+((v-.50)/.14)**2
  rgb[(rr>.55)&(rr<1.0)]=PALETTE['light']
  for a in (.14,.72,.83):rgb[(abs(u-a)<.025)&(v>.15)&(v<.19)]=PALETTE['rim']
 if motif=='dial':
  rgb[(np.mod(np.arctan2(x-8,z+2.83)*12,1)<.24)]=PALETTE['black']
 if motif=='red':
  rgb[:]=PALETTE['red'];rgb*=((.76+.23*np.cos((x-8)*5)*np.cos((y-10.71)*5)))[:,:,None]
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(20,26,27,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=13 if spec['group'] in ('barrel','wrap') else 19
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
    model=dict(credit='Deafening Whisper W149 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/deafening_whisper','particle':'destiny:item/weapon/w123/deafening_whisper'},
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
        name='Deafening Whisper W149 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='deafening_whisper.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w149=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))



def source_triangles(meshes):
 textures={n:np.asarray(Image.open(RAW/(n+'_Diffuse.dds')).convert('RGBA')) for n in ('Deafening Whisper Main','Deafening Whisper Scope','Ammo Counter')}
 # Glass/Map are retained source modules; no side-channel shader execution.
 for n,c in dict(Glass=[22,45,40,255],Map=[22,45,40,255],Emi=[198,32,24,255]).items():textures[n]=np.array([[c]],np.uint8)
 out=[]
 for m in meshes:
  for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
   if length>1e-10:out.append((ps,uv,textures[m['material']],n/length))
 return out

def comparison(d,meshes,atlas,model):
 w,h=720,280;sheet=Image.new('RGB',(2160,1530),'#151d27');draw=ImageDraw.Draw(sheet)
 def label(x,y,t,size=19):draw.text((x,y),t,fill='#e4ebed',font_size=size)
 label(18,12,'DEAFENING WHISPER / W149 / authored solid volumes + face UV / OFFLINE CPU ART',27)
 photo=Image.open(PHOTO).convert('RGB').crop((1020,195,1900,740));photo.thumbnail((700,350));sheet.paste(photo,(12,52))
 for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / 1024 atlas / full only',
  'Silver tube / dark woven sleeves / side counter',
  'True bore / open rail stock / solid hand grips',
  'Tall open optic frame / pale pin / clear -Z eye ray',
  'Source transforms, anchor, scale and hip display retained',
  '11 retained objects / 30,564 source triangles',
  'Native held / ADS / generic reload: pending master']):label(745,65+38*i,line,23)
 label(18,385,'ACTUAL DEFAULT-DYE PHOTO',18)
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/'+ID+'.png'))
 tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
 for i,t in enumerate(('RAW BLEND / neutral diffuse + declared static tints',f'CANONICAL / {len(old["elements"])} cuboids',f'W149 / {len(model["elements"])} semantic solids')):label(i*w+16,419,t,18)
 points=np.concatenate([m['vertices'] for m in meshes]+[vertices(e) for e in model['elements']])
 for row,(name,cam) in enumerate([('PHOTO SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.36,-.65]),('OPPOSITE REAR THREE-QUARTER',[1,.32,.65])]):
  ext=H['frame'](points,cam,w,h)
  for col,ts in enumerate(tris):
   im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,452+row*h));label(col*w+12,460+row*h,name,15)
 for col,(group,cam) in enumerate([('muzzle',[.12,.14,-1]),('stock',[-1,.25,.45]),('sight',[.10,.08,1])]):
  names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
  sub=dict(elements=[e for e in model['elements'] if e['name'] in names]);pts=np.concatenate([vertices(e) for e in sub['elements']])
  im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](pts,cam,w,190),(w,190));sheet.paste(im,(col*w,1296));label(col*w+14,1303,group.upper()+' / REAL OPEN GEOMETRY',16)
 label(18,1500,'Matched camera + scale per row. Authored matte color is photo based; raw undyed diffuse is not the default dye. No native acceptance claimed.',17)
 return png(sheet)

def review_text(d,counts):
 return f'''# Deafening Whisper W149 offline art review

Reinterprets the actual default-dye photo (`{PHOTO}`, SHA256 `{d['reference']['sha256']}`) and read-only W30 Blender source as clean large semantic solids. Source metadata and default dye provenance remain in design.json. Photo identity: long silver launcher tube, two dark woven sleeves with silver divider, side counter, two dark hand grips, open rail stock, underbarrel red unit, tall rectangular optic. No source blend scripts or shaders run. Inert gzip Blender 2.93 SDNA reading applies each stored object matrix, then metadata source_axis (thin X, vertical Z, length Y, muzzle sign -1), scale {d['source']['scale']} and anchor {d['source']['anchor']}. All 11 retained objects and 30,564 triangles reproduce W30 source/native bounds. Three excluded Ret planes stay excluded; retained Ammo Counter/Glass/Map modules inform static surface details rather than unapproved moving parts.

{sum(counts.values())} emitted cuboids; zero triangles or triangle adapters; {sum(counts.values())*6} independently allocated face UVs. Assembled full model {sum(counts.values())}/1000. Counts: {json.dumps(counts,sort_keys=True)}. Eight broad hollow tube walls carry the main volume, with a filled rear breech. Two broad wrapped sleeves, one divider and muzzle lip define the profile. Octagonal rings are a deliberate contour approximation, not mesh-island or voxel conversion. Solid receiver/grips/counter have meaningful thickness. Stock is rails + swept butt surrounding real air. No flat alpha body shells. The red unit is static, not a fabricated moving part. Existing generic reload only; full model only.

Face-specific authored UV uses an entirely opaque 1024x1024 atlas and two-pixel extruded gutters. Silver boundary rings, shallow fasteners, grip outlines, rear ribs and restrained white emblem are painted instead of screw/line cubes. Woven sleeve paint uses continuous circumferential and axial coordinates to keep the pattern coherent across facets; it is simplified fabric, not cut-through holes. The observed side counter zero is static texture, not runtime ammo integration. Opposite unobserved glyphs are omitted. No random noise or neutral-albedo projection is presented as restored dye. Colors are static matte approximations; source PBR, tiny wear, glass and active emission are not reconstructed.

ADS uses an actual open rectangular frame at source sight position. sightCenter [8,15.86,-1.416], forwardPoint [8,15.86,-3.416], eyeSide +Z, XY plane, optic style. The small pale pin with violet tip terminates at y15.835, immediately below the open -Z ray. Body/stock remain below the ray. Excluded Ret cards are not restored; no opaque lens crosses the opening. Ray and aperture tests accompany the model; native sight alignment belongs to master. Canonical hip/all display dictionary copied exactly; no global scale, recenter, gameplay/reload timing or split registration changes.

comparison.png includes actual photo, raw BLEND with neutral diffuse/declared tints, canonical and final in matched side and two three-quarter cameras, plus true bore, stock and optic details. inspection.bbmodel embeds final atlas with matching absolute geometry/rotations/UV and semantic groups. CPU art views establish offline appearance, not native acceptance. Curved grips, cylinder contour and small text/wear are simplified. The large open sight has no glass because the excluded cards must stay excluded.

Targeted regression covers schema/finite positive cube dimensions, budget, face UV/gutter/opaque alpha, real openings, unobstructed sight ray/pin, retained display/anchor/scale/grip, identity groups, raw source selection/transforms/bounds/hashes, inspection parity and deterministic generation. Master still owns native 26.3 parser/pack loading, representative first/third-person holding, ADS, generic reload/audio/timing and 10-20 displays. No native/client/DCC/Gradle or performance verification claimed.
'''

def generate(include_comparison=True):
 meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
 counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()));assert len(model['elements'])<=1000
 outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
 points=np.concatenate([vertices(e) for e in model['elements']])
 manifest=dict(id=ID,revision=REV,assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=len(model['elements'])*6,groups=counts,
  max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
  canonical_display_exact=True,full_only=True,generic_reload_unchanged=True,native_accepted=False,ads_sight=d['ads_sight'],
  generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],default_photo_sha256=d['reference']['sha256'],
  output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 return outputs

OWNED=[SCRIPT,TEST,ART+'design.json',ART+'manifest.json',ART+'review.md',ART+'inspection.bbmodel',ART+'comparison.png',REPORT,MODEL,TEXTURE]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w149-'+ID)
 assert len(owned)==10 and set(owned)==set(OWNED)
 outputs=generate();assert set(outputs)<=set(owned)
 for path,data in outputs.items():
  target=ROOT/path
  if a.verify:assert target.read_bytes()==data,'Regeneration differs: '+path
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if a.verify else 'Generated')+f' {len(outputs)} artifacts; {m["assembled_elements"]} solid cuboids; full only')
if __name__=='__main__':main()
