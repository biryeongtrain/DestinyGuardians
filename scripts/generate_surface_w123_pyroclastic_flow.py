#!/usr/bin/env python3
"""W150 Pyroclastic Flow: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/pyroclastic_flow/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/rocket_launcher/pyroclastic_flow.json'
MODEL = ASSET + 'models/weapon_surface_w123/pyroclastic_flow.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/pyroclastic_flow.png'
REPORT = 'docs/qa/2026-10-26/w150/pyroclastic_flow-worker.md'
RAW = Path("/tmp/destiny-weapons-w30/raw/pyroclastic_flow/extracted/Pyroclastic Flow")
PHOTO = Path('/tmp/destiny-weapons-w31/references/pyroclastic_flow.jpg')
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
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w150:pyroclastic_flow:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/pyroclastic_flow.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/"Pyroclastic Flow.fbx").read_bytes())==meta['source_files']["Pyroclastic Flow/Pyroclastic Flow.fbx"]
    roots=H['parse_fbx'](RAW/"Pyroclastic Flow.fbx")
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
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3); v=raw[:,[0,2,1]]*np.array([1,1,-1])*meta['scale']+meta['anchor']
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
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==28675
    return meshes,meta


SOURCE="art/blockbench/weapons/w30/pyroclastic_flow.bbmodel"
REFS="art/weapons/w31/references.json"
ID="pyroclastic_flow"
SCRIPT="scripts/generate_surface_w123_pyroclastic_flow.py"
TEST="scripts/qa/test_surface_w150_pyroclastic_flow.py"
BATCH="docs/qa/2026-10-26/w150/batch.json"
# Trusted inert SDNA reader; never executes anything embedded in the source asset.
Blend=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_salvager_s_salvo.py'))['Blend']

def source_meshes():
    """Retained meshes only, stored matrices + SDNA strides, never bpy/shaders."""
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    path=RAW/"Pyroclastic Flow.blend"
    assert sha(path.read_bytes())==meta['source_files']["Pyroclastic Flow/"+path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),
            offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        native=world[:,[0,2,1]]*np.array([1,1,-1])*meta['scale']+meta['anchor']
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
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==28675
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta



PALETTE=dict(purple=[63,57,84],purple_light=[70,64,94],gold=[196,170,100],
 black=[31,34,38],steel=[65,69,73],edge=[133,139,141],rubber=[29,32,34],
 red=[105,27,36],pin=[235,184,118],bore=[20,23,25])


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
    [2*r*math.tan(math.pi/8)+.010,t,z1-z0],mat,group,motif,('z',a))
 # Full-depth launch tube and actual recessed bore. Muzzle is native -Z.
 tube('launch_tube',8,11.90,meta['model_bounds'][0][2],5.35,1.0,.22,'black','tube','barrel')
 tube('muzzle_crown',8,11.90,meta['model_bounds'][0][2],-6.14,1.55,.57,'purple','muzzle','crown')
 tube('forward_band',8,11.90,-4.22,-3.86,1.17,.20,'purple','bands','band')
 tube('receiver_band',8,11.90,4.71,5.20,1.20,.25,'purple','bands','band')
 box('bore_stop',[7.02,10.92,5.22],[8.98,12.88,5.44],'bore','breech')
 # Shaped fins at the tube shoulder, as in the retained rip.
 for side in (-1,1):
  c(f'barrel_fin_{side}',[8,11.90+side*1.24,-3.25],[.18,.62,1.30],'black','fins','fin',('x',side*27))
 # Filled receiver/action: broad transverse masses, not alpha cards or thin skins.
 box('receiver_core',[6.91,10.54,5.22],[9.09,13.05,16.44],'black','receiver','action')
 box('receiver_cradle',[6.77,9.67,5.15],[9.23,10.62,16.49],'purple','receiver','rail')
 box('upper_cowling',[6.72,13.02,5.50],[9.28,13.56,17.80],'black','cowling','cowling')
 box('cowling_high_crown',[6.80,13.52,10.6],[9.20,14.22,15.80],'purple','cowling','cowling')
 beam('cowling_front_ramp',[8,13.45,5.62],[8,13.91,10.74],2.38,.67,'purple','cowling','cowling')
 beam('cowling_rear_ramp',[8,13.91,15.70],[8,13.44,18.61],2.28,.66,'purple','cowling','cowling')
 for side in (-1,1):
  # Beveled solid shoulders and coherent long armor plates.
  for k,a,b in [('forward',[8+side*1.18,13.40,5.50],[8+side*1.18,14.04,10.80]),
                ('middle',[8+side*1.18,14.04,10.65],[8+side*1.18,14.04,15.82]),
                ('rear',[8+side*1.18,14.04,15.70],[8+side*1.18,13.48,18.60])]:
   beam(f'cowling_shoulder_{side}_{k}',a,b,.53,.46,'purple_light','cowling','cowling')
  # Broad gold-edged cheek armor fills the upper flank below its bevel crown.
  for k,a,b in [('forward',[8+side*1.31,13.05,5.80],[8+side*1.31,13.69,11.0]),
                ('middle',[8+side*1.31,13.69,10.80],[8+side*1.31,13.69,15.80]),
                ('rear',[8+side*1.31,13.69,15.60],[8+side*1.31,13.23,18.55])]:
   beam(f'upper_flank_{side}_{k}',a,b,.40,.94,'purple','cowling','cowling')
  c(f'legion_armor_{side}',[8+side*1.35,11.14,13.37],[.56,2.12,5.52],
    'purple','armor','legion')
  beam(f'legion_armor_crown_{side}',[8+side*1.35,11.76,10.50],[8+side*1.35,12.39,16.12],
       .56,.55,'purple','armor','legion')
  beam(f'armor_lower_edge_{side}',[8+side*1.28,10.10,10.26],[8+side*1.28,9.99,16.20],
       .48,.38,'purple','armor','legion')
  c(f'lower_frame_rail_{side}',[8+side*1.17,9.76,10.86],[.32,.31,11.32],'purple','receiver','rail')
 # Tapered rear top and bottom, leaving the recognizable rear carry socket open.
 beam('rear_roof',[8,13.58,16.13],[8,13.46,19.15],1.40,.87,'black','rear_frame','enamel')
 c('rear_roof_cap',[8,13.63,18.78],[1.21,.54,.86],'purple','rear_frame','enamel',('x',12))
 box('rear_socket_front',[7.12,10.44,16.08],[8.88,12.90,16.58],'purple','rear_frame','enamel')
 beam('rear_socket_floor',[8,10.37,16.30],[8,10.60,18.10],1.65,.65,'purple','rear_frame','enamel')
 beam('rear_socket_lip',[8,10.60,18.10],[8,10.97,18.57],1.65,.55,'purple','rear_frame','enamel')
 # Mechanism below the carry socket; large hinge and compact latch, no screw cubes.
 c('rear_hinge',[8,9.40,16.43],[1.92,1.03,1.10],'steel','controls','pivot',('x',-12))
 c('rear_latch',[8,9.55,17.34],[1.12,.86,.88],'black','controls','latch',('x',-14))
 # Source lower skeleton has two large windows, sloping brace and front hand bow.
 beam('stock_front_bow',[8,9.78,6.34],[8,7.27,7.54],.85,.72,'purple','stock','enamel')
 beam('stock_lower_front',[8,7.27,7.54],[8,7.08,10.18],.88,.76,'purple','stock','enamel')
 beam('stock_lower_rear',[8,7.08,10.18],[8,9.57,13.12],.91,.80,'purple','stock','enamel')
 beam('stock_divider',[8,10.12,10.68],[8,7.18,10.24],.70,.54,'black','stock','grip')
 box('stock_heel_pad',[7.52,6.64,8.82],[8.48,6.96,10.12],'black','stock','grip')
 beam('pistol_grip',[8,9.08,13.02],[8,6.25,16.09],.79,.85,'rubber','grip','grip')
 c('grip_heel',[8,6.13,16.20],[.83,.45,.51],'purple','grip','band',('x',-44))
 c('grip_root',[8,9.07,13.33],[.98,.64,.90],'black','grip','pivot',('x',-42))
 beam('trigger',[8,10.03,8.06],[8,9.25,8.34],.18,.18,'steel','stock','trigger')
 # Top carry ridge is a connected shallow arch, preserving source height.
 box('top_ridge',[7.25,14.18,11.04],[8.75,14.65,14.06],'black','ridge','action')
 beam('top_ridge_front',[8,13.87,9.83],[8,14.42,11.17],1.50,.43,'black','ridge','action')
 beam('top_ridge_rear',[8,14.42,13.94],[8,14.05,15.07],1.50,.43,'black','ridge','action')
 # Side mechanical bay and supported lugs with recognizable channel relief in UV.
 for side in (-1,1):
  c(f'mechanical_bay_{side}',[8+side*1.25,11.89,7.53],[.44,1.96,4.56],
    'steel','mechanics','action')
  c(f'bay_latch_{side}',[8+side*1.49,11.02,8.61],[.24,.58,.70],
    'black','mechanics','latch')
 # Offset optic matches retained Scope bounds; real unobstructed air tunnel.
 # No opaque glass disc spans the player ray. Amber pin terminates below center.
 sx,sy=10.132,12.69
 c('optic_mount',[9.30,12.21,9.65],[.84,.43,1.48],'black','optic','mount')
 c('optic_upper_bracket',[9.79,13.66,9.63],[.73,.32,2.02],'purple','optic','enamel')
 tube('optic_housing',sx,sy,8.40,10.88,.59,.19,'black','optic','optic')
 tube('optic_eye_rim',sx,sy,10.61,10.91,.65,.15,'purple','optic','optic_rim')
 c('optic_pin_stem',[sx,12.40,8.71],[.075,.33,.11],'black','optic','pin')
 c('optic_pin_tip',[sx,12.59,8.71],[.075,.065,.11],'pin','optic','pin')
 # Front structural shoulder gives the source's cheek silhouette real thickness.
 for side in (-1,1):
  beam(f'front_cheek_{side}',[8+side*1.17,13.31,5.50],[8+side*1.17,13.82,7.13],
    .45,.54,'purple','cowling','cowling')
 # Retained geometry is used only as evidence for painted logo silhouette.
 logos={}
 for side,face in [(-1,'west'),(1,'east')]:
  ts=[]
  for m in meshes:
   if not m['name'].startswith('Red Legion'):continue
   for tri in m['vertices'][m['faces']]:
    if (tri[:,0].mean()-8)*side>1.0:ts.append(tri[:,[2,1]].tolist())
  logos[face]=ts
 inputs=[BASE,SOURCE,REFS,HELPER,'scripts/generate_surface_w123_salvager_s_salvo.py',
  ASSET+'textures/item/weapon/w30/pyroclastic_flow.png',
  ASSET+'items/weapon/pyroclastic_flow.json',ASSET+'items/weapon_aim_w70/pyroclastic_flow.json']
 inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT/(ASSET+'models/weapon_aim_w70')).glob('pyroclastic_flow*.json'))]
 raw_inputs=sorted(p for p in RAW.rglob('*') if p.is_file())+[PHOTO]
 ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
 return dict(id=ID,revision='W150',method='hand-authored semantic closed solids + independent opaque face UV; no voxel/component conversion',
  source=meta,reference=ref,palette=PALETTE,parts=parts,logo_silhouettes=logos,
  identity=['purple armor / gold piping / black mechanism / worn red Legion stamp',
   'long black launch tube and faceted purple muzzle crown','rear carry socket and two lower stock windows',
   'angled black pistol grip / upper carry ridge / offset optic'],
  ads_sight=dict(sightCenter=[sx,sy,10.73],forwardPoint=[sx,sy,8.73],eyeSide='+Z',plane='XY',style='optic',
   pinTop=[sx,12.6225,8.71],notes='Real open octagonal right-side optic, amber pin 0.0675 below ray; no opaque lens/card.'),
  coordinate_policy=dict(basis='Stored BLEND world [X,Z,-Y] * W30 scale + anchor; source +Y becomes native -Z.',
   source_axis=meta['source_axis'],scale=meta['scale'],anchor=meta['anchor'],muzzle_axis='-Z',bore_axis=[8,11.90],
   grip_root=[8,9.08,13.02],grip_heel=[8,6.25,16.09],display='exact original full canonical dictionary',
   export='full only; generic reload, timing and audio unchanged'),
  source_matching=dict(method='inert FBX arrays + BLEND SDNA stored matrices; metadata bounds checked',
   objects=[dict(name=m['name'],material=m['material'],triangles=len(m['faces']),object_matrix=m['object_matrix'],world_bounds=m['world_bounds']) for m in meshes],
   excluded=meta['excluded_objects'],triangles=sum(len(m['faces']) for m in meshes)),
  open_probes=dict(bore=[8,11.9,-7.4],rear_carry=[8,11.84,17.50],front_stock=[8,8.7,8.70],rear_stock=[8,8.9,11.50],optic=[sx,sy,9.7]),
  filled_probes=dict(receiver=[8,11.6,12.0],armor_east=[9.4,11.3,13.2],armor_west=[6.6,11.3,13.2],grip=[8,7.665,14.555]),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
  limitations=['Offline CPU comparison only; native parser/pack/held/ADS/generic reload/audio/10-20 displays pending parent.',
   'Photo-backed matte default dye and source logo silhouette; does not recover original shader/PBR or glass/reflection.',
   'Rounded launch tube, muzzle and optic are deliberately faceted; armor tapers and small mechanical details are simplified; panel channels use UV.',
   'Photo clips forward muzzle; retained source supplies full muzzle and barrel. No invented reverse lettering.',
   'Open optic replaces opaque source Scope Glass on the aiming ray; pin is a functional adaptation.'])


def world_points(e,face,w,h):
 p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
 q=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0])
 return u,v,q


def tile(spec,face,w,h,design):
 e=spec['geometry'];u,v,q=world_points(e,face,w,h);x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
 mat=spec['material'];motif=spec['motif'];rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);side=face in ('east','west')
 r=e.get('rotation');normal=np.array(H['NORMALS'][face],float)
 if r:normal=H['rotation']({r['axis']:r['angle']})@normal
 world_side=abs(normal[0])>.67
 # Large clean color fields; small directional finish is deterministic and restrained.
 rgb*=(.99+.035*np.cos(y*1.3+z*.35))[:,:,None]
 if mat.startswith('purple'):
  if side and motif in ('enamel','rail'):
   rgb[edge<1.25]=PALETTE['black'];rgb[(edge>=1.25)&(edge<2.40)]=PALETTE['gold']
  if motif=='cowling' and world_side:
   # Shared world-space gold piping follows the continuous upper silhouette.
   top=np.interp(z,[5.8,11.0,15.6,18.55],[13.52,14.17,14.17,13.70])
   lower=13.18+.015*(z-10)
   dist=np.minimum(abs(y-top),abs(y-lower))
   rgb[dist<.040]=PALETTE['gold']
   rgb[(dist>.04)&(dist<.10)]*=.57
   # Large gold-edged bevel polygon supported by the photo's upper side inlay.
   diag=13.36+.23*(z-10.8)
   line=(abs(y-diag)<.036)&(z>10.8)&(z<14.6)
   rgb[line]=PALETTE['gold']
  if motif=='legion' and world_side:
   top=11.76+(z-10.50)*(.63/5.62)+.28
   lower=10.12-.018*(z-10.5)
   dist=np.minimum.reduce([abs(y-top),abs(y-lower),abs(z-10.61),abs(z-16.13)])
   rgb[dist<.045]=PALETTE['gold'];rgb[(dist>.045)&(dist<.095)]*=.58
 if motif in ('band','crown','optic_rim'):
  gold=(v<.065)|(v>.935) if face in ('up','down','east','west') else (edge<1.8)
  rgb[gold]=PALETTE['gold']
 if motif=='barrel':
  rgb[:]=[45,49,53]
  # The photograph's pale longitudinal inset and two vents are face relief.
  if world_side:
   slot=(abs(y-11.90)<.24)&(z> -2.2)&(z<2.55)
   rgb[slot]=[137,143,145];rgb[slot&(abs(y-11.90)>.20)]=PALETTE['steel']
   vents=(abs(y-11.90)<.65)&(((z>3.05)&(z<3.22))|((z>3.62)&(z<3.80)))
   rgb[vents]=[8,10,12]
 if motif=='action':
  rgb[edge<1.0]*=.65
  if side:
   rgb[(abs(y-11.95)<.12)&(z>5.6)&(z<9.2)]=PALETTE['black']
   for zz in (5.59,6.24,7.20,8.87):
    rgb[(abs(z-zz)<.045)&(y>11.7)&(y<12.45)]*=.45
 if motif in ('grip','latch'):
  diamond=np.sin(y*47+z*41)*np.sin(y*47-z*41)>.30
  rgb[diamond]*=1.14
  if motif=='latch':rgb[(edge>3)&(edge<4.5)]=PALETTE['steel']
 if motif=='pivot' and side:
  r=np.hypot(u-.5,v-.5);rgb[r<.30]=PALETTE['black'];rgb[(r>.20)&(r<.24)]=PALETTE['edge'];rgb[r<.15]=PALETTE['steel']
 if motif=='optic':
  rgb[(z>9.0)&(z<9.14)]=PALETTE['gold']
 if motif=='legion' and world_side:
  mask=np.zeros((h,w),bool)
  for tri in design['logo_silhouettes']['east' if normal[0]>0 else 'west']:
   a,b,c=np.array(tri);den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
   if abs(den)<1e-10:continue
   wa=((b[1]-c[1])*(z-c[0])+(c[0]-b[0])*(y-c[1]))/den
   wb=((c[1]-a[1])*(z-c[0])+(a[0]-c[0])*(y-c[1]))/den
   mask|=(wa>=0)&(wb>=0)&(wa+wb<=1)
  wear=np.asarray(Image.open(RAW/'6a6dee80.png').convert('L'))
  iy=np.mod((y*90).astype(int),wear.shape[0]);ix=np.mod((z*90).astype(int),wear.shape[1])
  mask&=wear[iy,ix]>66
  rgb[mask]=PALETTE['red']
  # Real photo fasteners are paint, placed only on broad armor faces.
  for zz,yy in [(13.37,10.42),(13.37,11.88)]:
   r=np.hypot(z-zz,y-yy);rgb[(r<.080)&(r>.041)]=PALETTE['edge'];rgb[r<.034]=PALETTE['black']
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(24,27,30,255));requests=[]
 for spec in d['parts']:
  e=spec['geometry']
  for face in FACES:
   p=vertices(e)[list(FACES[face])];density=20 if spec['group'] not in ('tube','muzzle','bands') else 14
   w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
   requests.append((h,w,e['name'],face,spec))
 requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[];uvmap={}
 for h,w,name,face,spec in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
  im=tile(spec,face,w,h,d);atlas.paste(Image.fromarray(np.pad(np.asarray(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  uvmap[(name,face)]=[a*16/EDGE for a in (x,y,x+w,y+h)]
  ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
 elements=[]
 for spec in d['parts']:
  e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
 model=dict(credit='Pyroclastic Flow W150 semantic closed volumes / photo default paint / full only',
  textures={'0':'destiny:item/weapon/w123/pyroclastic_flow','particle':'destiny:item/weapon/w123/pyroclastic_flow'},
  elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])
 d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
 return atlas,model


def inspection(d,model,atlas):
 es=[];groups=[]
 for group in sorted({s['group'] for s in d['parts']}):
  children=[];names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
  for e in model['elements']:
   if e['name'] not in names:continue
   b=copy.deepcopy(e);r=b.pop('rotation',None)
   b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
    rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
   for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
   es.append(b);children.append(b['uuid'])
  groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
 return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
  name='Pyroclastic Flow W150 / offline editable inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
  textures=[dict(name='pyroclastic_flow.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
   source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']),
  destiny_w150=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True,ads_sight=d['ads_sight']))


def source_triangles(meshes):
 textures={m:np.asarray(Image.open(RAW/f).convert('RGB').convert('RGBA')) for m,f in
  [('Main','46d3eb80_Diffuse.png'),('Main (Red Legion Logo w/ wear)','46d3eb80_Diffuse.png'),
   ('Internals','2decea80_Diffuse.png'),('Scope','fb9deb80_Diffuse.png')]}
 textures['Scope Glass']=np.array([[[51,51,53,255]]],np.uint8)
 result=[]
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20);result.append((p,uv,textures[m['material']],n))
 return result


def comparison(d,meshes,atlas,model):
 w,h=740,320;sheet=Image.new('RGB',(2220,1650),'#18212a');dr=ImageDraw.Draw(sheet)
 def label(x,y,s,size=17):dr.text((x,y),s,fill='#e5ece6',font_size=size)
 label(18,10,'PYROCLASTIC FLOW / W150 / SEMANTIC SOLIDS + OPAQUE FACE UV / OFFLINE CPU ART',27)
 photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((855,420));sheet.paste(photo,(12,52))
 for i,line in enumerate([f'{len(model["elements"])} closed solid cuboids / {len(model["elements"])*6} independent face UV islands',
  'Actual retained BLEND + FBX: 28,675 triangles / metadata bounds verified',
  'Purple + gold + black default photo / source-derived red Legion silhouette',
  'Actual bore, rear carry socket, twin stock windows, offset open optic',
  'Source +Y -> native -Z / original full display / scale and anchor retained',
  'Functional amber pin immediately below a clear -Z aiming ray',
  'Generic reload, timing and audio unchanged / no shared integration edits',
  'Native pack, held, ADS, reload and 10-20 displays: pending parent']):label(885,65+i*40,line,21)
 label(18,477,'ACTUAL DEFAULT PHOTO / photo clips forward muzzle; retained rip supplies the full tube',17)
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/pyroclastic_flow.png'))
 for i,line in enumerate(['ACTUAL RAW BLEND / NEUTRAL ALBEDO',f'CANONICAL W30 / {len(old["elements"])} CUBOIDS',f'W150 / {len(model["elements"])} AUTHORED CUBOIDS']):label(i*w+15,508,line)
 ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
 pts=np.concatenate([m['vertices'] for m in meshes]+[vertices(e) for e in model['elements']])
 for row,(name,cam) in enumerate([('SIDE / SAME NATIVE FRAME',[1,.03,0]),('FRONT THREE-QUARTER',[1,.35,-.70]),('OPPOSITE REAR THREE-QUARTER',[-1,.36,.65])]):
  extent=H['frame'](pts,cam,w,h)
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,540+row*h));label(col*w+10,548+row*h,name,14)
 names={s['geometry']['name'] for s in d['parts'] if s['group']=='optic'}
 es=[e for e in model['elements'] if e['name'] in names];pts=np.concatenate([vertices(e) for e in es])
 im,_=H['render'](model_triangles(dict(elements=es),atlas),[0,0,1],H['frame'](pts,[0,0,1],280,145),(280,145));sheet.paste(im,(17,1504))
 label(315,1519,'+Z EYE VIEW / open physical optic + amber pin 0.0675 below center',21)
 label(315,1555,'Real source and canonical comparison, matched frame. Source neutral albedo is not finished default dye.',18)
 label(315,1590,'CPU evidence only. Native integration and acceptance remain with parent. No DCC or source scripts executed.',18)
 return png(sheet)


def review_text(d,counts):
 return f"""# Pyroclastic Flow W150 — semantic remodel

{len(d['parts'])} closed opaque cuboids / {len(d['parts'])*6} independent face UV rectangles / zero triangle adapters, full-only. Assembled ceiling 1000 is a limit, not a target. Groups: {json.dumps(counts,sort_keys=True)}. Ace87/Izanagi79 study informed broad continuous volumes and face detail. No rip-island conversion, voxel remeshing, alpha body cards, noise cubes, or unsupported triangles.

Actual references: default Bungie photo 1289324202 ({d['reference']['screenshot']}; SHA256 {d['reference']['sha256']}) and local nested Pyroclastic Flow FBX/BLEND. Photo and source neutral Main albedo were opened. Default identity is dark purple armor, gold piping, black action/tube, worn red Legion stamp, long launch tube with large faceted crown, rear carry socket, two lower stock windows, angled pistol grip, carry ridge and offset scope. Photo clips forward muzzle; retained rip establishes the complete tube. Opposite-side logo silhouettes come from actual source logo objects, not a mirrored invented mark.

Model uses substantial filled receiver, armor and cradle solids. Tube, muzzle and optic have eight thick opaque walls; bore is real air down to an opaque breech stop. Rear socket and stock windows contain actual air. Open optic replaces the source glass disc to make a functional in-model sight: center {d['ads_sight']['sightCenter']}, forward {d['ads_sight']['forwardPoint']}, eye +Z, plane XY, amber pin 0.0675 below center. Right-side position follows Scope bounds and keeps the body clear of the aiming ray. Parent owns runtime alignment.

Native frame is [world.X,world.Z,-world.Y] ×{d['source']['scale']} +{d['source']['anchor']}. Source axis length1/thin0/muzzle_sign+1 is adapted to native negative Z and reproduces original bounds {d['source']['model_bounds']}. Inert BLEND SDNA matrices and independently parsed FBX vertex arrays agree; selected source objects total 28,675 triangles. Reticle and Reticle Back excluded exactly as metadata. No embedded shader/source scripts executed. Canonical rocket_launcher/pyroclastic_flow.json supplies the exact full display dictionary. Original scale/anchor and source grip frame retained. No new reload split, registration, timing, audio or shared helper edits.

Each face has its own UV island, 2px extruded gutters and alpha255. Purple/gold panels, tube inset, vents, fasteners, grip finish and wear use authored paint. The red stamp uses projected source logo triangles and the retained wear texture as face paint only. All emitted geometry is closed cuboids, including rotated braces; source triangles are evidence only. No static texture claims original PBR, gold reflections or lens refraction. Deliberate faceting and simplified fine mechanical detail remain visible limitations.

inspection.bbmodel embeds exact final atlas, solids, rotations, UVs, groups and display. comparison.png includes actual photo plus matched actual raw/canonical/final side and two quarter views, with an eye-side optic detail. This is CPU art evidence, not a native screenshot. Targeted checks cover budget/schema, UV/opacity/gutters, openings and filled mass, clear sight/pin, source hashes/transforms/bounds, original display, BB parity, ownership and deterministic generation. Parent still verifies native parser/pack, first/third person, ADS alignment, generic reload, audio and 10–20 simultaneous displays.
"""


def generate(include_comparison=True):
 meshes,meta=source_meshes();fbx,fmeta=source_fbx()
 assert meta['source_axis']==dict(length=1,thin=0,muzzle_sign=1)
 assert {m['name']:len(m['faces']) for m in meshes}=={m['name']:len(m['faces']) for m in fbx}
 for m in meshes:
  f=next(x for x in fbx if x['name']==m['name']);np.testing.assert_allclose(m['vertices'],f['vertices'],atol=1e-6,rtol=0)
 d=make_design(meta,meshes);atlas,model=compile_model(d);counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
 assert len(model['elements'])<=1000
 outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
 points=np.concatenate([vertices(e) for e in model['elements']])
 manifest=dict(id=ID,revision='W150',family='rocket_launcher',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
  emitted_faces=len(model['elements'])*6,triangle_adapter_elements=0,alpha_body_elements=0,max_assembled_elements=1000,full_only=True,
  groups=counts,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],atlas_used_height=d['atlas']['used_height'],
  source_scale=meta['scale'],source_anchor=meta['anchor'],source_bounds=meta['model_bounds'],source_matching=d['source_matching'],
  actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],ads_sight=d['ads_sight'],canonical_display_exact=True,native_accepted=False,
  generic_reload_preserved=True,default_photo_sha256=d['reference']['sha256'],input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
  generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),
  output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w150-pyroclastic_flow')
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
