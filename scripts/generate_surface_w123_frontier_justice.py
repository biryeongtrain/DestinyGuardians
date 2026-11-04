#!/usr/bin/env python3
"""W138 Frontier Justice: CPU-only semantic solids and authored opaque face UV."""
import argparse
import base64
from collections import Counter
import copy
import json
import math
from pathlib import Path
import re
import runpy
import struct
import uuid
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ART='art/weapons/w123/frontier_justice/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/scout_rifle/frontier_justice.json'
MODEL=ASSET+'models/weapon_surface_w123/frontier_justice.json'
TEXTURE=ASSET+'textures/item/weapon/w123/frontier_justice.png'
REPORT='docs/qa/2026-10-26/w138/frontier_justice-worker.md'
SOURCE='art/blockbench/weapons/w30/frontier_justice.bbmodel'
HELPER='scripts/generate_surface_w123_beloved.py'
REFS='art/weapons/w31/references.json'
TEST='scripts/qa/test_surface_w123_frontier_justice.py'
RAW=Path('/tmp/destiny-weapons-w30/raw/frontier_justice/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/frontier_justice.jpg')
EDGE=1024
H=runpy.run_path(str(ROOT/HELPER))
FACES,NORMALS=H['FACES'],H['NORMALS']
sha,encode,png=H['sha'],H['encode'],H['png']
OWNED={'scripts/generate_surface_w123_frontier_justice.py',TEST,REPORT,TEXTURE,MODEL,
       *(ART+n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png'))}

class Blend:
    """Minimal inert Blender 3.0 SDNA reader. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        assert data[:12]==b'BLENDER-v300',data[:12]
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
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    assert sha((RAW/'Frontier Justice.blend').read_bytes())==meta['source_files']['Frontier Justice.blend']
    b=Blend(RAW/'Frontier Justice.blend');meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        assert b.field(o,'Object','parent')==0
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        np.testing.assert_allclose(matrix,[[0,1,0,0],[-1,0,0,0],[0,0,1,0],[0,0,0,1]],atol=1e-7)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),strides=(20,4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        native=np.c_[-world[:,1],world[:,2],-world[:,0]]*meta['scale']+meta['anchor']
        nl=b.field(mesh,'Mesh','totloop');np_=b.field(mesh,'Mesh','totpoly')
        loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(8,))
        uvs=np.ndarray((nl,2),'<f4',b.pointed(b.field(mesh,'Mesh','mloopuv')),strides=(12,4)).astype(float);uvs[:,1]=1-uvs[:,1]
        polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[]
        for i in range(np_):
            start,count=struct.unpack_from('<ii',polys,12*i)
            assert count in (3,4),count
            for j in range(1,count-1):
                ix=[start,start+j,start+j+1];faces.append(loops[ix]);uv.append(uvs[ix])
        materialptr=struct.unpack_from('<Q',b.pointed(b.field(mesh,'Mesh','mat')))[0]
        material=b.field(b.field(b.pointed(materialptr),'Material','id'),'ID','name')[2:]
        matdata=b.pointed(materialptr);tree=b.pointed(b.field(matdata,'Material','nodetree'))
        node=b.field(b.field(tree,'bNodeTree','nodes'),'ListBase','first');diffuse=None
        while node:
            nd=b.pointed(node)
            if b.field(nd,'bNode','name')=='Diffuse Texture':
                image=b.pointed(b.field(nd,'bNode','id'));diffuse=b.field(image,'Image','name').replace('\\','/').split('/')[-1]
            node=b.field(nd,'bNode','next')
        assert diffuse==TEXMAP[material],(material,diffuse)

        meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material,
            world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
    pts=np.concatenate([m['vertices'] for m in meshes]);world=np.array([m['world_bounds'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-8,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-7,rtol=0)
    return meshes,meta

def native_element(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return e

def vertices(e):return H['vertices'](native_element(e))

def model_triangles(model,atlas):
    m=copy.deepcopy(model);m['elements']=[native_element(e) for e in m['elements']]
    return H['model_triangles']({'full':m},atlas)

def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w138:frontier_justice:'+name))

TEXMAP={'FrontierJusticeBody':'b875ad80_Diffuse.png','FrontierJusticeStock':'7a74ad80_Diffuse.png',
        'FrontierJusticeSights':'0e20ad80_Diffuse.png','FrontierJusticeDecals':'7a74ad80_Diffuse.png'}

def source_triangles(meshes):
    textures={m:np.asarray(Image.open(RAW/p).convert('RGBA')) for m,p in TEXMAP.items()};result=[]
    for m in meshes:
        for p,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((p,uv,textures[m['material']],n))
    return result

PALETTE=dict(navy=[38,52,73],steel=[153,153,145],edge=[174,174,161],black=[37,39,38],
             stock=[45,46,43],rubber=[23,25,25],recess=[15,18,20],barrel=[112,103,91])

def make_design(meta,meshes):
    parts=[]
    def box(name,lo,hi,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(pos,size)],
            [round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name,a,b,width,depth,mat,group,motif='plain'):
        dy=b[1]-a[1];dz=b[2]-a[2];angle=-math.degrees(math.atan2(dy,dz))
        if angle>90:angle-=180
        if angle< -90:angle+=180
        c(name,[(p+q)/2 for p,q in zip(a,b)],[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',angle))
    def tube(name,x,y,z0,z1,radius,thick,mat,group,motif='rim'):
        for i in range(8):
            a=i*45;q=math.radians(a);rr=radius-thick/2
            size=[2*radius*math.tan(math.pi/8)+.008,thick,z1-z0];turn=None
            if a%90==0:
                if a%180:size=[size[1],size[0],size[2]]
            else:turn=('z',45 if i%4==1 else -45)
            c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],size,mat,group,motif,turn)
    def solid_cylinder(name,x,y,z0,z1,r,mat,group,motif='plain'):
        # Six intersecting FILLED prisms form an exact octagonal section, not cards.
        a=2*r/(1+math.sqrt(2))
        c(name+'_core',[x,y,(z0+z1)/2],[a,2*r,z1-z0],mat,group,motif)
        c(name+'_cross',[x,y,(z0+z1)/2],[2*r,a,z1-z0],mat,group,motif)
        for sx in (-1,1):
            for sy in (-1,1):
                c(f'{name}_corner_{sx}_{sy}',[x+sx*a/2,y+sy*a/2,(z0+z1)/2],[a,a,z1-z0],mat,group,motif,('z',45))
    # Source-derived native endpoints and source muzzle center, no auto-fitting.
    pts=np.concatenate([m['vertices'] for m in meshes]);tip=meta['model_bounds'][0][2];butt=meta['model_bounds'][1][2]
    terminal=pts[np.isclose(pts[:,2],pts[:,2].min(),atol=1e-7,rtol=0)]
    mx,my=((terminal.min(0)+terminal.max(0))/2)[:2].tolist()
    tube('muzzle',mx,my,tip,-6.93,.425,.14,'steel','muzzle','muzzle')
    solid_cylinder('muzzle_rear_band',mx,my,-6.98,-6.72,.46,'edge','muzzle','band')
    solid_cylinder('exposed_barrel',mx,my,-6.76,-4.40,.285,'barrel','barrel','machined')
    solid_cylinder('knurled_collar',mx,my,-5.98,-5.60,.48,'steel','barrel','knurl')
    solid_cylinder('barrel_base',mx,my,-4.84,-4.34,.47,'barrel','barrel','band')
    c('bore_deep_back',[mx,my,-7.02],[.34,.34,.08],'recess','muzzle')
    # Lower forward cylinder: substantial body and a recessed open front bezel.
    tube('lower_bezel',8,10.26,-5.24,-4.88,.42,.14,'steel','lower_cylinder','knurl')
    solid_cylinder('lower_cylinder',8,10.26,-4.92,-3.18,.34,'barrel','lower_cylinder','knurl')
    c('lower_lens',[8,10.26,-4.95],[.37,.37,.08],'recess','lower_cylinder')
    # Filled navy receiver, actual vent gaps, a deeply inset barrel, no alpha shells.
    box('upper_lower_spine',[7.24,10.55,-4.44],[8.76,11.67,4.62],'navy','upper','navy')
    box('upper_roof',[7.31,12.22,-4.44],[8.69,12.48,4.62],'steel','upper','worn')
    box('small_vent_sill',[7.24,11.67,-4.44],[8.76,11.91,-.12],'navy','upper','navy')
    for i,(z0,z1) in enumerate([(-4.44,-4.12),(-3.53,-3.24),(-2.55,-2.26),(-1.57,-1.28),(-.59,-.12)]):
        box(f'vent_post_{i}',[7.24,11.91,z0],[8.76,12.23,z1],'navy','upper','navy')
    for i,z in enumerate([-.06,2.38,4.43]):
        c(f'window_post_{i}',[8,11.94,z],[1.52,.57,.23],'navy','upper','navy')
    solid_cylinder('window_barrel',8,my,-4.46,4.70,.33,'barrel','upper','machined')
    box('rear_receiver',[7.27,10.58,4.62],[8.73,12.43,7.86],'navy','receiver','receiver')
    box('silver_slide',[7.24,11.78,4.64],[8.76,12.47,7.35],'steel','receiver','worn')
    c('rear_slide_slope',[8,12.17,7.53],[1.43,.53,.70],'steel','receiver','worn',('x',-25))
    box('rear_action_spine',[7.38,10.26,7.72],[8.62,11.57,11.22],'black','receiver','receiver')
    # Continuous roof rail; teeth alter the real silhouette, shallow crosscuts are UV.
    box('top_rail_base',[7.56,12.47,-4.40],[8.44,12.58,7.57],'steel','rail','machined')
    for i,z in enumerate(np.linspace(-4.24,7.40,22)):
        c(f'rail_tooth_{i:02}',[8,12.66,float(z)],[1.02,.15,.28],'edge','rail','rail')
    # Default GA POST sight: genuine aperture, source height, no opaque reticle card.
    box('post_base',[7.55,12.58,7.18],[8.45,12.84,8.02],'steel','sight','worn')
    c('post_riser',[8,12.94,7.68],[.55,.29,.43],'steel','sight')
    for side in (-1,1):
        c(f'post_cheek_{side}',[8+side*.32,13.36,7.68],[.18,.61,.28],'steel','sight','worn')
        c(f'post_corner_{side}',[8+side*.25,13.54,7.68],[.23,.22,.28],'steel','sight','worn',('z',45*side))
    c('post_cap',[8,meta['model_bounds'][1][1]-.07,7.68],[.43,.14,.28],'steel','sight')
    # Black underbody and a beveled long forearm, all filled across weapon width.
    box('forearm_core',[7.27,9.83,-3.50],[8.73,10.57,2.56],'black','forearm','forearm')
    beam('forearm_belly',[8,9.94,-3.30],[8,9.35,2.55],1.38,.37,'stock','forearm','forearm')
    beam('forearm_nose',[8,9.16,-4.55],[8,10.54,-3.91],1.38,.43,'black','forearm')
    c('forearm_rear_ramp',[8,9.83,2.62],[1.42,1.02,.68],'black','forearm','forearm',('x',-28))
    box('lower_receiver',[7.25,9.86,2.59],[8.75,10.79,7.44],'black','action','receiver')
    beam('front_action_leg',[8,9.99,2.80],[8,6.19,4.33],1.31,1.60,'black','action','action')
    beam('front_action_haunch',[8,8.95,3.90],[8,6.31,5.20],1.31,1.50,'black','action','action')
    beam('front_leg_toe',[8,6.24,4.16],[8,5.98,4.48],1.29,.46,'black','action','action')
    beam('lower_frame',[8,5.94,4.31],[8,7.73,11.22],1.22,.44,'stock','action','frame')
    # Rounded lower left extent follows the original forward leg, not a re-anchor.
    # Pistol grip passes between trigger aperture and rear thumbhole at source hand frame.
    beam('grip_core',[8,9.56,7.12],[8,7.29,8.39],1.18,1.10,'black','grip','grip')
    beam('grip_backstrap',[8,9.49,7.69],[8,7.25,8.91],1.13,.23,'rubber','grip','grip')
    beam('grip_heel',[8,7.30,8.39],[8,7.64,9.70],1.18,.44,'stock','grip')
    # Separate shallow curved trigger and opaque bow form a real through opening.
    beam('guard_front',[8,9.98,5.03],[8,9.00,5.12],.75,.23,'stock','guard')
    beam('guard_floor',[8,8.98,5.12],[8,8.71,6.48],.75,.23,'stock','guard')
    beam('guard_rear',[8,8.71,6.48],[8,9.05,7.29],.75,.24,'stock','guard')
    beam('trigger_stem',[8,9.95,6.38],[8,9.41,6.28],.17,.16,'steel','trigger')
    beam('trigger_hook',[8,9.41,6.28],[8,9.17,6.05],.17,.16,'steel','trigger')
    # Deep rear stock and open thumbhole; solid cheekpiece, toe and butt across X.
    box('stock_bridge',[7.35,10.25,10.80],[8.65,11.94,16.68],'stock','stock','stock')
    box('stock_rear_mass',[7.36,8.04,12.03],[8.64,10.36,16.68],'stock','stock','stock')
    box('thumbhole_rear_wall',[7.37,8.00,10.92],[8.63,10.31,12.08],'stock','stock','stock')
    beam('thumbhole_roof',[8,10.49,8.65],[8,10.41,11.48],1.23,.45,'stock','stock','stock')
    beam('thumbhole_floor',[8,7.71,9.10],[8,8.03,11.35],1.20,.44,'stock','stock','stock')
    box('stock_comb',[7.29,11.93,10.87],[8.71,12.19,16.64],'rubber','stock','butt')
    box('buttpad',[7.33,7.46,16.65],[8.67,12.17,butt],'rubber','stock','butt')
    # Rear magazine stays assembled: existing full-only reload graph is preserved.
    box('magazine',[7.59,6.49,11.12],[8.41,8.66,13.71],'barrel','magazine','magazine')
    box('magazine_floor',[7.56,6.2682,11.04],[8.44,6.57,13.91],'steel','magazine','magazine')
    c('magazine_rear_bevel',[8,6.75,13.64],[.82,.54,.45],'barrel','magazine','magazine',('x',30))
    # Photo-supported right charging latch + selector; screws and logos stay in UV.
    c('charging_handle',[6.81,10.90,7.52],[.34,.19,.75],'steel','controls','machined')
    c('selector_hub',[7.19,10.24,7.01],[.25,.46,.46],'black','controls','selector',('x',45))
    c('selector_lever',[7.09,10.30,6.79],[.18,.17,.58],'black','controls','selector',('x',-16))
    for side in (-1,1):
        c(f'accessory_mount_{side}',[8+side*.82,10.90,-1.84],[.20,.50,2.45],'steel','accessory','machined')
        for i,z in enumerate(np.linspace(-2.71,-.97,5)):
            c(f'accessory_tooth_{side}_{i}',[8+side*.94,10.90,float(z)],[.20,.67,.20],'edge','accessory','rail')
    groups=dict(Counter(s['group'] for s in parts))
    raw_inputs=[PHOTO,RAW/'Frontier Justice.blend',*(RAW/p for p in sorted(set(TEXMAP.values())))]
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']=='frontier_justice')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return dict(id='frontier_justice',revision='W138',full_only=True,parts=parts,groups=groups,
        source=meta,reference=ref,default_photo_sha256=sha(PHOTO.read_bytes()),
        frame=dict(mapping='[8-world.Y*s,8+world.Z*s,8-world.X*s]',object_rotation_z_degrees=90,
            scale=meta['scale'],anchor=meta['anchor'],hand_origin=[8,8,8],muzzle_axis='-Z',
            muzzle_tip_z=tip,butt_tip_z=butt,muzzle_bore_center=[mx,my],grip_center=[8,8.425,7.755]),
        source_matching=dict(method='inert Blender 3.0 SDNA; obmat applied; retained objects only',
            source_objects=meta['source_objects'],triangles=meta['source_triangles'],bounds_tolerance=1e-7,
            material_diffuse=TEXMAP),
        input_sha256={r:sha((ROOT/r).read_bytes()) for r in (BASE,SOURCE,HELPER,REFS)},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        holes=[dict(name='muzzle bore',point=[mx,my,-7.4],ray_axis='z',range=[tip,-7.07]),
               dict(name='lower bezel',point=[8,10.26,-5.1],ray_axis='z',range=[-5.23,-5.00]),
               dict(name='trigger aperture',point=[8,9.42,5.7],ray_axis='x',range=[6.5,9.5]),
               dict(name='lower frame opening',point=[8,7.23,6.50],ray_axis='x',range=[6.5,9.5]),
               dict(name='rear thumbhole',point=[8,9.21,10.1],ray_axis='x',range=[6.5,9.5]),
               dict(name='upper long window',point=[8,12.02,1.3],ray_axis='x',range=[6.5,9.5]),
               dict(name='small vent',point=[8,12.07,-3.83],ray_axis='x',range=[6.5,9.5]),
               dict(name='post aperture',point=[8,13.36,7.68],ray_axis='z',range=[7.3,8.1])],
        limitations=['CPU art views are not native Minecraft acceptance.',
            'Faceted curves, shallow muzzle side ports and simplified patina; no dynamic metallic shader recovery.',
            'Native parser, pack registration, first/third person, ADS, generic reload and 10-20 display QA pending master.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=((1-u)*(1-v))[:,:,None]*p[0]+(u*(1-v))[:,:,None]*p[1]+(u*v)[:,:,None]*p[2]+((1-u)*v)[:,:,None]*p[3]
    return u,v,q

def value_noise(x,y,freq,seed):
    x=x*freq;y=y*freq;ix=np.floor(x);iy=np.floor(y);fx=x-ix;fy=y-iy
    fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    def cell(a,b):
        q=np.sin(a*127.1+b*311.7+seed*74.7)*43758.5453
        return q-np.floor(q)
    return ((1-fx)*(1-fy)*cell(ix,iy)+fx*(1-fy)*cell(ix+1,iy)+
            (1-fx)*fy*cell(ix,iy+1)+fx*fy*cell(ix+1,iy+1))

class Paint:
    def tile(self,spec,face,w,h):
        u,v,q=world_points(spec['geometry'],face,w,h);role=spec['material'];motif=spec['motif'];group=spec['group']
        rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);z=q[:,:,2];y=q[:,:,1]
        # Continuous world coordinates keep wear and grain coherent across new faces.
        grain=np.sin(z*93+y*77)*np.sin(z*41-y*103)
        rgb*=(.98+.025*grain+.035*np.exp(-((v-.22)/.42)**2))[:,:,None]
        rgb[edge<.65]*=.64;rgb[(edge>=.65)&(edge<1.4)]*=1.18
        side=face in ('east','west')
        if role=='navy':
            # Photo: navy paint chipped to pewter along upper/bottom boundaries.
            weather=.65*value_noise(z,y,8,13)+.35*value_noise(z,y,29,31)
            boundary=(y<11.07)|(y>12.27)|((y>11.58)&(y<11.72))
            chip=((weather>.57)&boundary)|(weather>.74)
            chip|=(y<10.98+.07*(value_noise(z,y,12,2)-.5))&(y>10.66+.08*(value_noise(z,y,9,3)-.5))&(weather>.38)
            rgb[chip]=[153,154,147];rgb[chip & (weather>.77)]=[185,183,169]
        if motif=='worn':
            shade=np.sin(z*53+y*87)*np.sin(z*17-y*31)
            rgb[shade>.73]*=.70
            rgb[(edge<2.2)&(shade>.1)]*=1.10
        if side and motif in ('navy','receiver','forearm','action','stock','magazine'):
            # Shallow panels have face paint, never duplicate coplanar geometry.
            panel=(u>.10)&(u<.90)&(v>.16)&(v<.84)
            border=panel&((u<.12)|(u>.88)|(v<.19)|(v>.81));rgb[border]*=.48
            rgb[panel & (v>.78)]*=1.19
            for zz,yy in [(-4.12,10.95),(-.22,10.97),(2.59,10.99),(4.33,10.95),
                          (3.47,9.85),(4.75,7.10),(8.97,7.05),(12.70,11.10),(15.86,11.13),(15.85,8.62)]:
                rr=np.hypot(z-zz,y-yy)
                rgb[rr<.12]=[16,19,20];rgb[(rr>.08)&(rr<.115)]=[111,112,105]
                rgb[(rr<.065)&(abs(y-yy)<.016)]*=.35
        if motif=='stock' and side:
            # Large characteristic triangular groove in stock cheek, seen in photo.
            line=(abs(y-(8.39+(z-12.4)*.48))<.037)&(z>12.4)&(z<15.8)
            line|=(abs(y-8.39)<.037)&(z>12.4)&(z<15.8)
            rgb[line]*=.42
        if motif=='grip':
            diamond=np.mod(z*20+y*17,1)<.22;diamond|=np.mod(z*20-y*17,1)<.22
            rgb[diamond]*=.65;rgb[~diamond]*=1.11
        if motif=='knurl':
            checks=(np.mod(y*26+z*25,1)<.24)|(np.mod(y*26-z*25,1)<.24)
            rgb[checks]*=.62
        if motif in ('machined','band','rail'):
            rgb[(np.mod(z*12,1)<.16)&(v>.12)&(v<.88)]*=.78
        if motif=='muzzle' and side:
            rr=np.hypot(z+7.40,y-11.40)
            rgb[rr<.14]=[18,21,23];rgb[(rr>.14)&(rr<.19)]=[104,105,101]
        if motif=='selector' and side:
            rr=np.hypot(u-.5,v-.5);rgb[(rr>.29)&(rr<.36)]*=1.4
        if motif=='action' and side:
            # Photo-supported twin-bar HAKKE emblem; no invented serial lettering.
            a=z-3.82;b=y-8.91
            mark=((abs(a-.10)<.038)|(abs(a+.10)<.038))&(abs(b)<.23)
            mark|=((abs(b-.08)<.04)|(abs(b+.08)<.04))&(abs(a)<.23)
            rgb[mark]=[180,183,177]
        if motif=='magazine' and side:
            rgb[(np.mod(z*4+y*2.5,1)<.11)&(u>.2)&(u<.8)]*=.68
        if motif=='butt':rgb[(np.mod(y*7,1)<.19)&(u>.12)&(u<.88)]*=.65
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    paint=Paint(); atlas=Image.new('RGBA',(EDGE,EDGE),(15,18,20,255));requests=[]
    for s in d['parts']:
        for f in FACES:
            p=vertices(s['geometry'])[list(FACES[f])];density=27 if s['motif'] in ('navy','receiver','stock','action') else 23
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,s['geometry']['name'],f,s))
    requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;islands=[];uvmap={}
    for h,w,name,f,s in requests:
        if x+w+2>EDGE: x=2;y+=row+4;row=0
        if y+h+2>EDGE: raise ValueError('Atlas overflow: '+name)
        tile=paint.tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvmap[(name,f)]=[a*16/EDGE for a in (x,y,x+w,y+h)]
        islands.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for s in d['parts']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(islands),islands=islands,
                    
                    paint_policy='Opaque per-face UV; authored default-photo navy paint, pewter chips, panels, knurling and grip stipple')
    return atlas,dict(credit='Frontier Justice W138 / semantic solids and authored default-photo face UV / full only',
        textures={'0':'destiny:item/weapon/w123/frontier_justice','particle':'destiny:item/weapon/w123/frontier_justice'},
        display=copy.deepcopy(json.loads((ROOT/BASE).read_bytes())['display']),elements=elements)


def inspection(d,model,atlas):
    elements=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group};children=[]
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None)
            b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
                rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            elements.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Frontier Justice W138 / editable offline inspection',
        resolution={'width':EDGE,'height':EDGE},elements=elements,outliner=groups,display=copy.deepcopy(model['display']),
        textures=[dict(name='frontier_justice.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
             source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        destiny_w138=dict(nativeAccepted=False,fullOnly=True,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale']))



def comparison(d,meshes,atlas,model):
    w,h=900,365;sheet=Image.new('RGB',(2700,2050),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'FRONTIER JUSTICE / W138 / SEMANTIC SOLIDS + AUTHORED FACE UV / CPU ART ONLY',28)
    photo=Image.open(PHOTO).convert('RGB').crop((580,300,1820,865));photo.thumbnail((1240,475));sheet.paste(photo,(20,62))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / 0 adapters / full only',
        'Default: chipped navy upper + pewter + black chassis',
        'Three frame openings / rear magazine / GA POST sight',
        'Deep muzzle bore, lower bezel and upper vent windows',
        'Inert raw .blend: 8 objects / 14,977 triangles',
        'Original source basis, scale, grip frame and display',
        'CPU comparison; native pack / ADS / reload pending']):label(1320,85+i*47,line,23)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/frontier_justice.png'))
    label(20,560,'RAW BLEND / NEUTRAL DIFFUSE / READ ONLY',20)
    label(w+20,560,f'CANONICAL W30 / {len(old["elements"])} CUBOIDS / READ ONLY',20)
    label(2*w+20,560,f'W138 / {len(model["elements"])} AUTHOR-PLACED FILLED CUBOIDS',20)
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE / SAME CAMERA AND SCALE',[-1,0,0]),
        ('FRONT OBLIQUE / SAME CAMERA AND SCALE',[-1,.42,-.63]),('REAR OBLIQUE / SAME CAMERA AND SCALE',[1,.32,.62])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,600+row*h));label(col*w+15,610+row*h,name,18)
    for i,(groups,title,cam) in enumerate([(['muzzle','barrel'],'MUZZLE / DEEP BORE',[.2,.15,-1]),
        (['action','grip','guard','trigger','stock'],'FILLED FRAME / THREE APERTURES',[-1,.15,-.13]),
        (['upper','rail','sight'],'VENTS / ROOF / OPEN SIGHT',[.24,.20,-1]),
        (['stock','magazine'],'STOCK / REAR MAGAZINE',[1,.35,.6])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups}
        es=[e for e in model['elements'] if e['name'] in names];pts=np.concatenate([vertices(e) for e in es])
        im,_=H['render'](model_triangles(dict(elements=es),atlas),cam,H['frame'](pts,cam,675,255),(675,255))
        sheet.paste(im,(i*675,1730));label(i*675+15,1738,title,18)
    label(20,2010,'Raw neutral diffuse is not default dye. CPU raster views do not prove native parser, lighting, holding, ADS, reload or performance.',20)
    return png(sheet)

def review_text(d,counts):
    return f"""# Frontier Justice W138 — CPU art review

{len(d['parts'])} opaque semantic cuboids, {len(d['parts'])*6} explicit face UVs, one authored 1024 atlas, full-only assembly. Zero triangle/contour adapters, alpha body cards, mesh-island conversions or voxel conversions. The initial 115-cube blockout was within the 80–120 starting range. Four filled corner prisms per cylinder section improve exposed octagonal sections; a stock floor closes the thumbhole boundary and an action haunch preserves the narrow lower-frame opening. These are section/silhouette volumes rather than surface clutter. It follows the Ace87/Izanagi79 study: long filled masses, rotated semantic parts, face artwork for shallow details. The 1000 assembled-element ceiling is not a target.

Identity: chipped navy/pewter upper, long toothed rail, ported silver muzzle with real recessed bore, lower cylinder, three open spaces around the grip/frame, black thumbhole buttstock, rear magazine and the default GA POST aperture sight. The reference photo was inspected locally; SHA-256 `{d['default_photo_sha256']}` matches the retained W31 reference record. Wear, panel seams, fasteners, knurling, grip stipple, stock grooves and the photo-supported twin-bar emblem are authored opaque face paint. The default dye is reconstructed from that photo; the raw neutral diffuse is not treated as a recovered default shader. Small side muzzle ports are painted relief, while axial bores, upper windows, sight and frame holes have actual depth/space.

Raw evidence: the read-only Blender 3.0 file matches its W30 SHA-256. A minimal inert SDNA reader applies the stored object matrices and recovers exactly eight retained objects and 14,977 triangles with original per-loop UVs. World and native bounds match W30 within 0.0000001. The stored +90-degree Z object rotation is applied before mapping `[-world Y, world Z, -world X]`; it is not assumed to share Beloved/Bygones FBX axes. Material diffuse associations are read from the source node-tree links. Alternate scopes, staging Plane/Cube and shader execution are excluded. Source faces are used only in CPU comparison, never as new construction units.

The exact original scale {d['source']['scale']}, anchor {d['source']['anchor']}, -Z weapon axis and unchanged hand frame are retained; the muzzle and butt longitudinal tips match the canonical frame. Grip is authored around the original slanted grip location, with no transform compensation. Canonical display is copied byte-value-exact. This worker emits only the full model and changes no registration, HUD, reload, gameplay, timing or audio files. Shared registry/HUD integration belongs to master.

Every face owns its UV rectangle with two-pixel extruded gutters. The complete atlas, including unused background, is opaque. inspection.bbmodel embeds this exact atlas and editable cube groups. comparison.png contains the source appearance plus side/front/rear views of raw source, canonical W30 and W138, with equal cameras/scales per row and additional geometry closeups. The source render uses original UV/diffuse; no native screenshot is implied.

Offline checks cover schema/budget, original basis/display/endpoints, actual empty ray channels and filled chassis depth, UV opacity/gutters/nonoverlap, source/input/output hashes, inspection parity, batch ownership, and deterministic regeneration. Curved source surfaces are faceted and patina is simplified. Source metallic reflections, PBR response, physical glass and runtime lighting are not recovered. No GUI, Blender, Blockbench, server, Gradle or other worker was called.

Native pack/parser/registration, first/third-person holding, ADS, generic reload and 10–20 simultaneous display remain pending master. No native or performance pass is claimed. Group counts: {json.dumps(counts,sort_keys=True)}.
"""

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
    counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()));points=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
        ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    manifest=dict(id='frontier_justice',revision='W138',family='scout_rifle',assembled_elements=len(model['elements']),
        opaque_cuboids=len(model['elements']),triangle_adapter_elements=0,contour_elements=0,alpha_body_elements=0,
        max_assembled_elements=1000,groups=counts,emitted_faces=len(model['elements'])*6,full_only=True,
        texture_size=[EDGE,EDGE],face_uv_islands=d['atlas']['face_islands'],atlas_used_height=d['atlas']['used_height'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        default_photo_sha256=d['default_photo_sha256'],source_matching=d['source_matching'],
        canonical_display_exact=True,generic_reload_ADS_combat_audio_timing_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    assert set(outputs)<=OWNED and len(outputs)==(7 if include_comparison else 6)
    assert manifest['assembled_elements']<=1000
    assert sum(len(b) for b in outputs.values())<25*1024*1024
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate()
    for rel,data in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; {m["assembled_elements"]} opaque cuboids; {m["emitted_faces"]} faces; 0 adapters; full only')
    print(f'1024 atlas, used height {m["atlas_used_height"]}; payload {sum(len(b) for b in outputs.values())} bytes; native pending')

if __name__=='__main__':main()
