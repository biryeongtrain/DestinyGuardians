#!/usr/bin/env python3
"""W149 Salvager's Salvo: deterministic semantic solid-cuboid art; full export only.
Read-only reuse of trusted inert FBX/SDNA and CPU raster helpers. No DCC/game actions.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import uuid
import re, struct, subprocess
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/salvager_s_salvo/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/grenade_launcher/salvager_s_salvo.json'
MODEL = ASSET + 'models/weapon_surface_w123/salvager_s_salvo.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/salvager_s_salvo.png'
REPORT = 'docs/qa/2026-10-26/w149/salvager_s_salvo-worker.md'
RAW = Path("/tmp/destiny-weapons-w30/raw/salvager_s_salvo/extracted/Salvager's Salvo")
PHOTO = Path('/tmp/destiny-weapons-w31/references/salvager_s_salvo.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w149:salvager_s_salvo:'+name))


def render_element(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation']; e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return e


def vertices(e):
    return H['vertices'](render_element(e))


def model_triangles(model,atlas):
    m=copy.deepcopy(model); m['elements']=[render_element(e) for e in m['elements']]
    return H['model_triangles']({'full':m},atlas)


def source_fbx():
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/salvager_s_salvo.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/"Salvager's Salvo.fbx").read_bytes())==meta['source_files']["Salvager's Salvo/Salvager's Salvo.fbx"]
    roots=H['parse_fbx'](RAW/"Salvager's Salvo.fbx")
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry': continue
        mid=next(p for c,p in links if c==node[1][0]); model=models[mid]
        name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']: continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in node[2]}
        v=np.array(cs['Vertices'][1][0]).reshape(-1,3)[:,[0,2,1]]*meta['scale']+meta['anchor']
        faces=[]; face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3; faces.append(face); face=[]
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        material=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=material))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-6)
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==21314
    return meshes,meta



SOURCE="art/blockbench/weapons/w30/salvager_s_salvo.bbmodel"
REFS="art/weapons/w31/references.json"
ID="salvager_s_salvo"
SCRIPT="scripts/generate_surface_w123_salvager_s_salvo.py"
TEST="scripts/qa/test_surface_w149_salvager_s_salvo.py"
BATCH="docs/qa/2026-10-26/w149/batch.json"
class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 3.3 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12]==b'BLENDER-v303',data[:12]
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
    path=RAW/"Salvager's Salvo.blend"
    assert sha(path.read_bytes())==meta['source_files']["Salvager's Salvo/"+path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),
            offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
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
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==21314
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta


PALETTE=dict(olive=[91,105,42],lightolive=[127,141,63],darkolive=[53,64,28],
 steel=[66,69,59],edge=[137,143,117],black=[23,28,23],brown=[91,66,49],
 green=[75,95,53],sage=[151,173,135],wrap=[59,45,36],wood=[76,47,33],ivory=[209,215,169])

def make_design(meta,meshes):
 parts=[]
 def c(name,pos,size,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
  if turn:e['rotation']=dict(origin=list(pos),axis=turn[0],angle=turn[1])
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def box(name,lo,hi,mat,group,motif='plain'):
  c(name,[(a+b)/2 for a,b in zip(lo,hi)],[b-a for a,b in zip(lo,hi)],mat,group,motif)
 def beam(name,a,b,w,t,mat,group,motif='plain'):
  dy=b[1]-a[1];dz=b[2]-a[2];angle=-math.degrees(math.atan2(dy,dz))
  if angle>90:angle-=180
  if angle< -90:angle+=180
  c(name,[(x+y)/2 for x,y in zip(a,b)],[w,t,math.hypot(dy,dz)],mat,group,motif,('x',angle))
 def tube(name,x,y,z0,z1,r,t,mat,group,motif='plain'):
  for i in range(8):
   a=i*45;q=math.radians(a);rr=r-t/2
   c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
    [2*r*math.tan(math.pi/8)+.008,t,z1-z0],mat,group,motif,('z',a))
 def filled(name,x,y,z0,z1,r,mat,group,motif='plain'):
  for i in range(4):c(f'{name}_{i}',[x,y,(z0+z1)/2],[r*2,r*2*math.tan(math.pi/8),z1-z0],mat,group,motif,('z',45*i))
 # Broad full-depth octagonal barrel shell. The bore has real depth and an opaque stop only behind breech.
 tube('barrel_shell',8,12.27,-7.68,4.14,1.06,.20,'green','barrel','camo')
 tube('muzzle_lip',8,12.27,meta['model_bounds'][0][2],-7.56,1.09,.19,'brown','muzzle','rim')
 tube('front_band',8,12.27,-3.57,-3.27,1.13,.12,'olive','bands','band')
 tube('breech_band',8,12.27,3.55,4.05,1.15,.17,'lightolive','bands','band')
 filled('breech_plug',8,12.27,4.05,4.53,1.04,'black','barrel','breech')
 # Four long axial reinforcing seams on the source tube, shaded modestly in UV.
 for i in (1,3,5,7):
  a=i*45;q=math.radians(a)
  c(f'barrel_seam_{i}',[8-1.055*math.sin(q),12.27+1.055*math.cos(q),-1.69],[.09,.09,11.52],'darkolive','barrel','seam',('z',a))
 box('lower_barrel_cradle',[7.02,10.62,-7.30],[8.98,11.20,2.78],'darkolive','frame','cradle')
 box('cradle_keel',[7.20,10.41,-7.16],[8.80,10.69,-2.15],'olive','frame','cradle')
 box('cradle_rear_haunch',[7.13,10.61,1.58],[8.87,11.43,4.70],'olive','frame','cradle')
 # Left front sling/strap and clamp have real stand-off and an open short loop.
 beam('front_strap',[6.27,13.43,-5.55],[6.27,9.83,-5.18],.24,.23,'brown','controls','strap')
 beam('strap_foot',[6.27,9.83,-5.18],[6.27,9.73,-4.76],.24,.23,'brown','controls','strap')
 c('strap_upper_bridge',[6.94,13.35,-5.54],[1.59,.20,.24],'olive','controls','latch')
 c('strap_lower_bridge',[6.91,10.55,-5.27],[1.28,.24,.28],'olive','controls','latch')
 for side in (-1,1):
  c(f'band_latch_{side}',[8+side*1.13,11.82,-3.42],[.16,.83,.31],'lightolive','controls','latch')
 box('top_rail',[7.64,13.26,-5.24],[8.36,13.43,3.34],'black','rail','rail')
 for i in range(8):c(f'rail_tooth_{i}',[8,13.46,-4.90+i*.91],[.91,.16,.29],'olive','rail','rail')
 # Large receiver, front shoulders and X-braced green service panels; relief is UV, not fake moving pieces.
 box('receiver_core',[7.02,10.91,4.10],[8.98,13.12,9.66],'olive','receiver','receiver')
 box('receiver_crown',[7.20,13.09,4.55],[8.80,13.32,8.87],'lightolive','receiver','crown')
 box('receiver_lower',[7.10,10.73,4.57],[8.90,11.13,8.51],'black','receiver','lower')
 for side in (-1,1):
  c(f'receiver_shoulder_{side}',[8+side*.84,13.08,6.47],[.30,.30,4.50],'olive','receiver','receiver',('z',side*45))
  c(f'braced_panel_{side}',[8+side*1.005,12.09,6.70],[.13,1.76,3.20],'darkolive','receiver','xpanel')
 # Hand contact follows source top [8,10.75,6.8] to heel near [8,6.65,9.3].
 beam('grip_upper',[8,10.86,6.93],[8,9.10,7.60],1.26,1.32,'black','grip','wrap')
 beam('grip_main',[8,9.31,7.53],[8,7.00,8.97],1.35,1.52,'wrap','grip','wrap')
 c('grip_heel',[8,6.89,9.17],[1.55,.62,1.90],'black','grip','heel',('x',-9))
 # Rounded U guard is four structural beams around real air; trigger separate and static.
 box('guard_front',[7.80,9.32,5.12],[8.20,10.95,5.36],'darkolive','guard','plain')
 beam('guard_curve_front',[8,9.36,5.22],[8,9.02,5.62],.40,.22,'darkolive','guard')
 box('guard_floor',[7.80,8.92,5.57],[8.20,9.15,6.88],'olive','guard','plain')
 beam('guard_back',[8,9.04,6.82],[8,9.54,7.09],.40,.22,'olive','guard')
 c('trigger',[8,10.18,6.04],[.20,.70,.16],'steel','trigger','plain',('x',-20))
 # Black vertical foregrip; two crossed solid prisms form a filled octagonal cross section along Y.
 for i in (0,45):c(f'foregrip_{i}',[8,8.92,-2.14],[.98,3.00,.98],'black','foregrip','knurl',('y',i))
 box('foregrip_socket',[7.47,10.38,-2.68],[8.53,10.78,-1.60],'steel','foregrip','socket')
 # Source stock offset to +X, with its characteristic dog-leg connector and raised triangular wooden cheek.
 box('stock_socket',[7.65,11.56,9.55],[8.91,12.83,10.41],'darkolive','stock_frame','socket')
 beam('stock_connector_down',[8.50,12.65,10.08],[8.50,10.92,12.01],.43,.36,'brown','stock_frame','metal')
 beam('stock_connector_up',[8.50,10.92,12.01],[8.50,12.83,13.75],.43,.36,'brown','stock_frame','metal')
 box('stock_wood',[8.10,10.91,13.20],[8.90,13.20,16.53],'wood','stock','wood')
 beam('stock_cheek_slope',[8.50,11.19,12.18],[8.50,12.79,13.76],.80,.79,'wood','stock','wood')
 box('stock_cheek_cap',[8.06,13.15,13.72],[8.94,13.43,16.34],'darkolive','stock','cap')
 beam('stock_lower_tie',[8.50,10.98,15.49],[8.50,10.13,16.48],.37,.26,'olive','stock_frame','metal')
 box('butt_pad',[7.97,9.26,16.51],[9.03,13.60,meta['model_bounds'][1][2]],'black','stock','butt')
 box('butt_olive_edge',[7.94,9.45,16.42],[9.06,13.44,16.68],'darkolive','stock','butt')
 # Tall original ladder sight: native original top Y retained; center is physically empty, no reticle card.
 box('sight_pedestal',[7.27,13.35,-2.27],[8.73,13.66,-.52],'darkolive','sight','sight')
 for side in (-1,1):
  x=8+side*.59
  box(f'ladder_side_{side}',[x-.075,13.63,-2.19],[x+.075,meta['model_bounds'][1][1],-2.02],'olive','sight','ladder')
  for yy in (14.83,16.12):
   c(f'ladder_tick_{side}_{yy}',[8+side*.46,yy,-1.99],[.20,.055,.16],'ivory','sight','tick')
 box('ladder_top',[7.34,16.40,-2.19],[8.66,meta['model_bounds'][1][1],-2.02],'olive','sight','ladder')
 box('ladder_bottom',[7.34,13.62,-2.19],[8.66,13.78,-2.02],'steel','sight','ladder')
 box('sight_pin',[7.957,13.76,-2.22],[8.043,14.22,-2.06],'ivory','sight','pin')
 c('sight_hinge',[8.73,13.65,-1.71],[.28,.49,.51],'steel','sight','pivot',('x',45))
 box('sight_folding_foot',[7.43,13.43,-1.66],[8.57,13.78,.34],'darkolive','sight','sight')
 # Low front sight / bead retained at muzzle; tall ladder handles grenade range elevation.
 box('front_sight_base',[7.60,13.28,-7.22],[8.40,13.49,-6.30],'olive','front_sight','sight')
 box('front_bead',[7.94,13.45,-7.04],[8.06,13.68,-6.88],'ivory','front_sight','pin')
 for side in (-1,1):
  c(f'front_sight_ear_{side}',[8+side*.32,13.49,-6.96],[.12,.35,.71],'olive','front_sight','sight',('x',-10))
 inputs=[BASE,SOURCE,REFS,HELPER,'scripts/generate_surface_w123_long_arm.py',
  'scripts/generate_surface_w123_edge_transit.py',ASSET+'textures/item/weapon/w30/salvager_s_salvo.png']
 raw_inputs=[RAW/"Salvager's Salvo.blend",RAW/"Salvager's Salvo.fbx",RAW/'f4f6ea80_Diffuse.png',RAW/'5e09eb80_Diffuse.png',PHOTO]
 ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
 assert sha(PHOTO.read_bytes())==ref['sha256']
 return dict(id=ID,revision='W149',method='hand-authored semantic solid cuboids and opaque continuous face UV; no voxel or component conversion',
  source=meta,reference=ref,palette=PALETTE,parts=parts,
  identity=['long three-tone camouflaged tube and brown recessed muzzle','tall open olive ladder with ivory ticks',
   'olive receiver and twin X service panels','dark wrapped pistol grip / knurled vertical foregrip',
   'offset bent connector, wooden stock and black butt'],
  ads_sight=dict(sightCenter=[8,14.30,-2.105],forwardPoint=[8,14.30,-4.105],eyeSide='+Z',plane='XY',style='iron',
   pinTop=[8,14.22,-2.14],notes='Real open ladder. Ivory pin immediately 0.08 below center; clear full -Z ray above body/stock. Ladder range sight; original low muzzle bead retained.'),
  coordinate_policy=dict(basis='Stored Blender 3.3 object matrices, then metadata thin X / vertical Z / length Y => native [world.X,world.Z,world.Y]',
   source_axis=meta['source_axis'],scale=meta['scale'],anchor=meta['anchor'],muzzle_axis='-Z',bore_axis=[8,12.27],
   grip_top=[8,10.86,6.93],grip_heel=[8,6.89,9.17],display='exact canonical hip display dictionary',export='full only; existing generic reload'),
  source_matching=dict(method='inert SDNA stored matrices, checked against retained FBX and W30 metadata',
   objects=[dict(name=m['name'],material=m['material'],triangles=len(m['faces']),object_matrix=m['object_matrix'],world_bounds=m['world_bounds']) for m in meshes],
   excluded=meta['excluded_objects'],triangles=sum(len(m['faces']) for m in meshes)),
  open_probes=dict(bore=[8,12.27,-7.0],guard=[8,9.65,5.69],ladder=[8,15.5,-2.10],stock_dogleg=[8.5,12.3,11.75]),
  filled_probes=dict(receiver=[8,12,6],grip=[8,8.4,8.1],stock=[8.5,12.2,15],foregrip=[8,8.9,-2.14]),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
  limitations=['Offline CPU art only; native parsing/pack/held/ADS/generic reload/10-20 displays pending master.',
   'Matte default-photo reinterpretation, not recovered shader/PBR/reflection.',
   'Tube and grip curves are faceted; shallow wear, knurling, wraps and X braces use UV. No opposite-side photo; no invented reverse lettering.',
   'Photo clips stock at right; stored rip establishes full stock proportions. No new split or animation.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q



def tile(spec,face,w,h):
 e=spec['geometry'];u,v,q=world_points(e,face,w,h);x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
 mat=spec['material'];motif=spec['motif'];rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
 rgb*=(.98+.035*np.cos(y*.65))[:,:,None]
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);side=face in ('east','west')
 if motif=='camo':
  # Large source/photo-supported organic bands, not noisy voxel sampling. World space joins all eight facets.
  phase=z+.50*(y-12.27)+.28*np.sin(y*3.3)+.22*np.sin(z*1.4+x*2.0)
  p=np.mod(phase+1.3,5.0)
  rgb[:]=PALETTE['green'];rgb[p<1.45]=PALETTE['brown'];rgb[(p>2.9)&(p<3.88)]=PALETTE['sage']
  rgb*=(.98+.035*np.cos(z*1.2+y))[:,:,None]
  # One grounded longitudinal rolled seam, no wear noise.
  rgb[(abs(y-12.0)<.024)&(z> -6.9)&(z<3.2)]*=.64
 if motif not in ('camo','breech','wood','wrap','knurl'):
  rgb[edge<.65]*=.71;rgb[(edge>=.65)&(edge<1.45)]*=1.14
 if motif in ('band','rim'):
  rgb[(np.mod(z*24,1)<.16)]*=.87
 if motif=='knurl':
  a=np.mod(x*17,1);b=np.mod(z*17,1);rgb[(a<.15)|(b<.15)]*=.55
  rgb[(y>10.15)|(y<7.55)]=PALETTE['steel']
 if motif=='wrap':
  # Wide slanted leather bands run continuously around all transverse faces.
  t=np.mod(y*1.65+.70*z,1)
  rgb[:]=PALETTE['wrap'];rgb[t<.10]*=.48;rgb[(t>.10)&(t<.16)]*=1.48
  rgb*=(.96+.05*np.sin(x*10+y*14+z*4))[:,:,None]
 if motif=='wood':
  rgb*=(1+.07*np.sin(y*34+1.7*np.sin(z*.7))+.022*np.sin(y*90+z))[:,:,None]
  if side:
   rgb[(abs(y-13.05)<.035)&(z>13.5)]=PALETTE['brown']
 if motif=='butt':rgb[np.mod(y*11,1)<.22]*=.60
 if side and motif=='xpanel':
  # Two actual recessed X panels from photograph, relief by face UV only.
  for zz in (5.91,7.46):
   dz=z-zz;dy=y-12.10
   valid=(abs(dz)<.58)&(abs(dy)<.66)
   cross=(np.minimum(abs(dy-1.03*dz),abs(dy+1.03*dz))<.09)&valid
   rgb[cross]=PALETTE['black']
   rim=(np.minimum(abs(dy-1.03*dz-.12),abs(dy+1.03*dz-.12))<.024)&valid
   rgb[rim]=PALETTE['olive']
  rgb[(edge>2)&(edge<3.1)]=PALETTE['olive']
  for zz in (5.25,8.13):
   for yy in (11.36,12.84):
    rr=np.hypot(z-zz,y-yy);rgb[rr<.055]=PALETTE['edge'];rgb[rr<.028]=PALETTE['black']
 if side and motif in ('receiver','cradle','latch','socket'):
  rgb[(abs(y-11.16)<.025)&(z> -6.6)&(z<8.9)]*=.53
  for zz,yy in [(-6.30,10.83),(-3.42,11.84),(4.65,11.10),(8.88,12.72)]:
   rr=np.hypot(z-zz,y-yy);rgb[rr<.09]=PALETTE['edge'];rgb[rr<.045]=PALETTE['black']
 if motif=='pivot' and side:
  r=np.hypot(u-.5,v-.5);rgb[r<.34]=PALETTE['edge'];rgb[r<.22]=PALETTE['black'];rgb[r<.12]=PALETTE['steel']
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(22,28,24,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=15 if spec['group'] in ('drum','barrel') else 23
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
    model=dict(credit='Salvagers Salvo W149 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/salvager_s_salvo','particle':'destiny:item/weapon/w123/salvager_s_salvo'},
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
        name='Salvagers Salvo W149 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='salvager_s_salvo.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w149=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))




def source_triangles(meshes):
 textures={m:np.asarray(Image.open(RAW/f).convert('RGBA')) for m,f in [('Main','f4f6ea80_Diffuse.png'),('Sights','5e09eb80_Diffuse.png')]}
 result=[]
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
   result.append((p,uv,textures[m['material']],n))
 return result


def comparison(d,meshes,atlas,model):
 w,h=720,295;sheet=Image.new('RGB',(2160,1510),'#18212a');dr=ImageDraw.Draw(sheet)
 def label(x,y,s,size=17):dr.text((x,y),s,fill='#e5ece6',font_size=size)
 label(18,10,"SALVAGER'S SALVO / W149 / AUTHORED SOLIDS + FACE UV / OFFLINE CPU ART",26)
 im=Image.open(PHOTO).convert('RGB').crop((980,195,1920,790));im.thumbnail((780,340));sheet.paste(im,(18,53))
 for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / 0 triangle adapters / full only',
  'Actual rip: 21,314 triangles / Main + Barrel Camo + Sights',
  'Reticle excluded exactly as W30 / no source scripts executed',
  'Olive + three-tone tube camouflage / leather + wooden stock',
  'True recessed bore / open guard / open ladder + ivory aiming pin',
  'Source scale + anchor + native -Z muzzle / exact hip display',
  'Native parser, held, ADS, reload and 10-20 displays: pending master']):label(815,65+i*39,line,20)
 label(18,404,'DEFAULT BUNGIE PHOTO / right edge clips stock; rip supplies full stock',17)
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/salvager_s_salvo.png'))
 for i,line in enumerate(['ACTUAL RAW BLEND / NEUTRAL ALBEDO',f'CANONICAL W30 / {len(old["elements"])} CUBOIDS',f'W149 / {len(model["elements"])} AUTHORED CUBOIDS']):label(i*w+15,440,line)
 ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)];pts=np.concatenate([m['vertices'] for m in meshes])
 for row,(name,cam) in enumerate([('SIDE / MATCHED SCALE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.40,-.65]),('OPPOSITE REAR THREE-QUARTER',[1,.36,.65])]):
  extent=H['frame'](pts,cam,w,h)
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,470+row*h));label(col*w+10,477+row*h,name,14)
 # Small direct +Z eye-side view: physical window and pin, no opaque card.
 names={s['geometry']['name'] for s in d['parts'] if s['group']=='sight'};es=[e for e in model['elements'] if e['name'] in names]
 pts=np.concatenate([vertices(e) for e in es]);im,_=H['render'](model_triangles(dict(elements=es),atlas),[0,0,1],H['frame'](pts,[0,0,1],250,145),(250,145))
 sheet.paste(im,(17,1360));label(285,1376,'LADDER: open physical window / ivory pin / aim center 0.08 above pin tip',20)
 label(285,1411,'Large camo fields, X recesses, wraps, knurling and grain are independent opaque face UV.',19)
 label(285,1444,'Matched offline art views establish geometry only. No native or performance acceptance claimed.',18)
 return png(sheet)


def review_text(d,counts):
 return f"""# Salvager's Salvo W149 — offline product review

{len(d['parts'])} authored opaque cuboids / {len(d['parts'])*6} independent face UV rectangles / zero triangle adapters / full-only model. Assembled ceiling 1000. Semantic groups: {json.dumps(counts,sort_keys=True)}. The Ace87/Izanagi79 study guided large volumes and face UV, without copying their weapon motifs. No connected-component or voxel conversion, alpha-card side shells, arbitrary mesh JSON, new reload split or invented animated part.

Identity comes from the actual default-dye photo (Bungie item 2060863616; {d['reference']['screenshot']}; SHA256 {d['reference']['sha256']}) and retained local rip. Broad olive/green/brown/sage barrel camouflage, brown muzzle lip, two clamps, tall olive ladder with pale ticks, green receiver and two recessed X panels, leather-wrapped pistol grip, knurled vertical foregrip, bent offset stock connector, wooden cheek and black butt are retained. Photo is clipped at right; full stock proportion follows raw geometry. Photo, raw Main albedo, raw source and final comparison were inspected using the image tool. Opposite-side markings are not invented.

Thick octagonal barrel walls enclose a true recessed bore, stopped at the breech. The filled receiver, stock, grip and foregrip have transverse volume. Trigger guard, dog-leg and ladder sight openings contain real air. Long main tube remains continuous rather than source-island fragments. Source rounds become deliberately faceted solids. Fasteners, X panel relief, shallow seams, camouflage, wrap edges, knurling and wood grain are authored opaque face paint. All 1024 atlas pixels have alpha 255, including extruded 2px gutters. Static diffuse approximation does not recover original PBR, shader camouflage distribution or reflections.

Source: read-only Blender 3.3 SDNA, stored Object matrices applied, then metadata source_axis length1/thin0/muzzle_sign-1 maps [world.X,world.Z,world.Y] to native ×{d['source']['scale']} +{d['source']['anchor']}. Retained objects Main 15970, Barrel Camo 3916, Sights 1428 = 21314 triangles. Reticle excluded. FBX selected objects, triangles and bounds are independently checked against the same metadata; FBX export rotations/scales are verified instead of assuming Beloved axes. Stored BLEND matrices are identity in this rip. No rip scripts/shaders are executed. Original source muzzle/butt endpoints and sight top are retained; hand contact follows source frame; canonical hip display copied exactly. No shared HUD, runtime, registration or helper changed.

ads_sight: iron, center [8,14.30,-2.105], forward [8,14.30,-4.105], eye +Z, plane XY. Source ladder is physically open; ivory pin top [8,14.22,-2.14] is 0.08 below center. Body/stock sit below the eye ray. Low muzzle bead remains as the source secondary feature. Master aligns ADS to this supplied center. A tall grenade range ladder and low muzzle bead do not claim precision ballistic calibration.

inspection.bbmodel embeds the final atlas, exact final cuboids, rotations, UVs and semantic groups. comparison.png includes actual photo and raw/canonical/final matched side + two oblique rows, plus eye-side ladder view. This is CPU art evidence, not a native screenshot. Default source diffuse is neutral and not claimed as default-dye shader output.

Targeted regression covers finite schema/bounds, aggregate budget, UV/alpha/gutters/nonoverlap, real openings and filled probes, clear ADS ray with immediate pin, source/photo hashes and selected objects, display/scale/anchor, identity proportions, BB parity and deterministic regeneration. Remaining master checks: native 26.3 parsing/pack loading, first/third person held alignment, ADS readability, existing generic reload, and 10–20 simultaneous displays. No native/client/server/DCC/Gradle run or performance claim.
"""


def generate(include_comparison=True):
 meshes,meta=source_meshes();fbx,fmeta=source_fbx()
 assert meta['source_axis']==dict(length=1,thin=0,muzzle_sign=-1)
 assert {m['name']:len(m['faces']) for m in meshes}=={m['name']:len(m['faces']) for m in fbx}
 for m in meshes:
  f=next(x for x in fbx if x['name']==m['name']);np.testing.assert_allclose(m['vertices'],f['vertices'],atol=1e-6,rtol=0)
 d=make_design(meta,meshes);atlas,model=compile_model(d);counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
 assert len(model['elements'])<=1000
 outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
 points=np.concatenate([vertices(e) for e in model['elements']])
 manifest=dict(id=ID,revision='W149',family='grenade_launcher',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
  emitted_faces=len(model['elements'])*6,triangle_adapter_elements=0,alpha_body_elements=0,max_assembled_elements=1000,full_only=True,
  groups=counts,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],atlas_used_height=d['atlas']['used_height'],
  source_scale=meta['scale'],source_anchor=meta['anchor'],source_bounds=meta['model_bounds'],source_matching=d['source_matching'],
  actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],ads_sight=d['ads_sight'],canonical_display_exact=True,native_accepted=False,
  generic_reload_preserved=True,default_photo_sha256=d['reference']['sha256'],input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
  generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),
  output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w149-salvager_s_salvo')
 assert len(owned)==10 and set(outputs)<=set(owned) and len(outputs)==(7 if include_comparison else 6)
 return outputs


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();outputs=generate()
 for rel,data in outputs.items():
  p=ROOT/rel
  if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts; {m["assembled_elements"]} cuboids / {m["emitted_faces"]} faces; full only; opaque 1024 atlas height {m["atlas_used_height"]}')
if __name__=='__main__':main()
