#!/usr/bin/env python3
"""W141 Temptation's Hook: authored filled sword volumes and opaque face paint.
CPU-only. Never loads a DCC scene, evaluates a shader, or drives game tools.
"""
import argparse
import base64
from collections import Counter
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import runpy
import struct
import subprocess
import uuid
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
ID='temptation_s_hook'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/sword/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
ITEM=ASSET+f'items/weapon/{ID}.json'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w141/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
BATCH='docs/qa/2026-10-26/w141/batch.json'
RAW=Path(f'/tmp/destiny-weapons-w30/raw/{ID}/extracted')
PHOTO=Path(f'/tmp/destiny-weapons-w31/references/{ID}.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
FACES=H['FACES']
EDGE=1024
PALETTE=dict(blade=[81,85,102], bevel=[119,124,145], spine=[37,41,52],
    edge=[199,196,255], edge_tip=[228,224,255], bronze=[122,105,80],
    bronze_light=[166,145,110], teal=[51,99,101], black=[25,30,32],
    steel=[145,156,157], inset=[202,211,215], recess=[15,22,28])

def encode(value):return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(data):return hashlib.sha256(data).hexdigest()
def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w141:temptation_s_hook:'+name))
def render_element(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return e

def vertices(e):return H['vertices'](render_element(e))
def model_triangles(model,atlas):
    m=copy.deepcopy(model);m['elements']=[render_element(e) for e in m['elements']]
    return H['model_triangles']({'full':m},atlas)

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
    path=RAW/"Temptation's Hook.blend"
    assert sha(path.read_bytes())==meta['source_files'][path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        np.testing.assert_allclose(matrix,np.eye(4),atol=1e-8,rtol=0)
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
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==4278
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=2e-8,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-7,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta


def make_design(meta,meshes):
    parts=[]
    def box(name,lo,hi,material,group,motif='metal',turn=None):
        e=dict(name=name,**{'from':[round(x,7) for x in lo],'to':[round(x,7) for x in hi]})
        if turn:e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=material,group=group,motif=motif))
    def c(name,point,size,material,group,motif='metal',turn=None):
        box(name,[a-b/2 for a,b in zip(point,size)],[a+b/2 for a,b in zip(point,size)],material,group,motif,turn)
    def beam(name,a,b,thickness,width,material,group,motif='metal',x=8,overlap=0):
        # a,b are authored Y/Z stations. Rotation leaves true solid cross section.
        angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        c(name,[x,(a[0]+b[0])/2,(a[1]+b[1])/2],
            [thickness,math.dist(a,b)+overlap,width],material,group,motif,('x',angle))
    # Each station marks a change in the recognisable recurve, not a source island.
    # E is the inner metal/energy seam; S is the broad dark spine.
    stations=[(15.1,8.833,9.81),(18.2,8.835,10.065),(21.8,8.755,10.056),
              (23.4,8.36,9.31),(25.4,7.59,8.39),(27.6,6.45,7.23),(29.65,5.23,5.84),(30.28,5.02,5.20)]
    for i,(a,b) in enumerate(zip(stations,stations[1:])):
        y0,e0,s0=a;y1,e1,s1=b
        slope=((e1+s1)-(e0+s0))/(2*(y1-y0));normal=math.sqrt(1+slope*slope)
        width=((s0-e0)+(s1-e1))/2/normal
        beam(f'blade_web_{i}',(y0,(e0+s0)/2),(y1,(e1+s1)/2),.335,width,'blade','blade','blade',overlap=.12)
        # Thick shoulder -> narrower bevel -> rounded bright energy edge.
        beam(f'edge_bevel_{i}',(y0,e0+.075),(y1,e1+.075),.25,.24/normal,'bevel','bevel','blade',overlap=.14)
        energy_width=(.53 if i<3 else .48)/normal
        beam(f'arc_cutting_edge_{i}',(y0,e0-.245),(y1,e1-.245),.145,energy_width,'edge','energy','arc',overlap=.12)
        if i<6:beam(f'blade_back_{i}',(y0,s0-.055),(y1,s1-.055),.25,.13/normal,'spine','spine','back',overlap=.09)
    # Last filled hook point turns down to Z4.49 and closes at Y31.5.
    beam('hook_point_metal',(29.55,5.47),(30.65,4.97),.28,.37,'blade','tip','blade')
    beam('hook_point_edge',(29.74,4.77),(31.25,4.59),.13,.19,'edge_tip','tip','arc')
    beam('hook_point_return',(30.17,4.98),(31.36,4.57),.14,.21,'edge','tip','arc')
    c('hook_terminal',[8,31.39,4.535],[.105,.18,.085],'edge_tip','tip','arc',('x',-19))
    # Root energy strip is one real solid turning into the long blade.
    beam('root_edge',(10.93,6.35),(14.74,8.35),.145,.48,'edge','energy','arc',overlap=.05)
    beam('root_edge_transition',(14.60,8.31),(15.30,8.58),.145,.48,'edge','energy','arc',overlap=.08)
    beam('root_blade_bevel',(10.95,6.65),(15.23,8.81),.26,.27,'bevel','heel','blade',overlap=.05)
    beam('root_blade_web',(11.22,6.99),(15.29,9.08),.35,.50,'blade','heel','blade',overlap=.05)
    # Continuous raised two-row rivet rail on the spine; rivets are paint.
    beam('spine_rivet_rail',(15.55,9.91),(22.12,9.895),.405,.31,'spine','rail','rivets')
    beam('spine_rail_lip',(15.55,10.09),(22.12,10.075),.235,.075,'steel','rail','metal')
    # A filled stepped hilt, offset shoulder and diagonal bronze relief.
    box('hilt_root',[7.635,7.45,7.03],[8.365,10.85,8.88],'bronze','hilt','veil')
    box('hilt_forward_step',[7.67,10.65,7.62],[8.33,11.78,8.94],'bronze','hilt','veil')
    beam('hilt_swept_cheek',(10.60,7.35),(15.20,9.85),.62,.75,'bronze','hilt','veil',overlap=.12)
    beam('hilt_middle_swell',(10.70,8.08),(14.0,9.99),.64,.75,'bronze','hilt','veil',overlap=.12)
    beam('hilt_outer_swell',(10.70,8.66),(13.0,9.96),.64,.55,'bronze','hilt','veil',overlap=.12)
    box('hilt_crest',[7.73,12.0,9.55],[8.27,15.48,10.12],'bronze','hilt','veil')
    beam('hilt_crest_tip',(13.52,10.17),(14.75,10.17),.43,.30,'bronze','hilt','veil')
    # A recessed backing and pale inset actually change side depth.
    for sign in (-1,1):
        c(f'inset_bezel_{sign}',[8+sign*.373,8.72,7.70],[.055,1.53,.74],'black','inset','metal')
        c(f'pale_inset_{sign}',[8+sign*.403,8.72,7.70],[.043,1.27,.52],'inset','inset','stone')
        c(f'inset_endcap_{sign}',[8+sign*.402,8.12,7.70],[.047,.16,.42],'steel','inset','metal',('x',-25))
    # Bronze border is raised, with thinner geometry at the terminal knee.
    beam('hilt_outer_rim',(7.72,8.925),(10.67,8.925),.80,.16,'bronze_light','rim','flutes')
    beam('hilt_outer_knee',(10.66,8.925),(12.35,9.98),.70,.16,'bronze_light','rim','flutes',overlap=.06)
    beam('hilt_outer_diagonal',(12.25,10.00),(15.48,9.94),.60,.18,'bronze_light','rim','flutes',overlap=.06)
    # Signature diagonal bronze brace from root heel to spine, solid and raised.
    beam('hilt_diagonal_brace',(10.56,8.82),(15.58,9.69),.80,.32,'bronze_light','brace','flutes')
    beam('hilt_brace_shadow',(10.54,8.60),(15.57,9.47),.70,.11,'black','brace','metal')
    # Cut-back guard leaves real negative space between teeth and the crest.
    beam('finned_guard_root',(7.67,6.91),(11.08,6.91),.66,.42,'black','guard','guard')
    beam('guard_bronze_rail',(7.77,7.08),(11.02,7.08),.78,.20,'bronze','guard','rivets')
    for i in range(11):
        y=7.98+i*.279
        c(f'guard_fin_{i}',[8,y,6.55],[.50,.185,.48],'black','fins','fin',('x',-23))
    beam('guard_crest_cap',(12.25,10.13),(13.63,10.13),.64,.10,'black','guard','metal')
    # Original grip sits around Z7.714 (not recentered onto the blade at Z8).
    box('grip_core',[7.715,3.00,7.30],[8.285,7.60,8.13],'black','grip','grip')
    for sign in (-1,1):
        c(f'grip_side_bevel_{sign}',[8+sign*.275,5.31,7.715],[.10,4.56,.66],'black','grip','grip',('y',sign*24))
    c('grip_back',[8,5.31,8.12],[.50,4.56,.08],'steel','grip','grip')
    c('grip_front',[8,5.31,7.31],[.50,4.56,.08],'black','grip','grip')
    c('grip_upper_ferrule',[8,7.49,7.715],[.66,.23,.93],'black','ferrule','rivets')
    c('grip_lower_ferrule',[8,3.14,7.715],[.66,.25,.98],'steel','ferrule','metal')
    # Filled angular pommel section (center + corner bevels).
    c('pommel_core',[8,2.83,7.715],[.64,.62,.86],'steel','pommel','pommel')
    for sx in (-1,1):
        for sz in (-1,1):
            c(f'pommel_facet_{sx}_{sz}',[8+sx*.285,2.83,7.715+sz*.422],
              [.20,.62,.20],'black','pommel','pommel',('y',45))
    c('pommel_cap',[8,2.55,7.715],[.68,.10,1.05],'black','pommel','metal')
    files=[BASE,ITEM,SOURCE,REFS,'art/weapons/w30/manifest.json','src/main/resources/destiny/weapons/w30.json',
           HELPER,'scripts/generate_surface_w123_frontier_justice.py',
           'scripts/generate_surface_w123_crown_splitter.py','scripts/generate_surface_w123_falling_guillotine.py']
    rawfiles=[PHOTO,RAW/"Temptation's Hook.blend",RAW/"Temptation's Hook.png",RAW/"textures/Temptation's Hook_Diffuse.png"]
    return dict(id=ID,stage='W141',family='sword',source=meta,parts=parts,palette=PALETTE,
        construction='authored semantic filled cuboids; no source island conversion, voxels, alpha sheets, or rip texture sampling',
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='anchor + scale * [world.X, world.Z, world.Y]',
            length='+Y',thin='X',grip_center_z=7.715,display='canonical exact',native_swordframe='W140 unchanged'),
        source_matching=dict(method='inert Blender3.3 SDNA, stored object matrices, all6 W30 meshes/4278 triangles',
            bounds_tolerance=1e-7,objects=[dict(name=m['name'],triangles=len(m['faces']),material=m['material'],object_matrix=m['object_matrix']) for m in meshes]),
        identity=['swept hooked violet-white cutting edge','dark straight double-rivet spine rail',
            'bronze and desaturated teal contour hilt','black fin guard with air between teeth',
            'raised bronze brace and pale side inset','black patterned grip and silver angular pommel'],
        paint_policy='new deterministic face brushwork, contour lines and hardware marks; no raw UV/texture transplant; all pixels opaque',
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['Cuboid curvature approximates the source recurve and point; small source edge wear is face paint.',
            'Violet energy is static opaque color, not bloom, animated shader or original PBR reflection.',
            'CPU comparison and editable inspection are offline evidence only; native DCC/held/thirdperson/swing/guard/caster/10-20 display pending master.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    """Paint new face strokes in sword coordinates, never sample the rip atlas."""
    u,v,q=world_points(spec['geometry'],face,w,h);x,y,z=np.moveaxis(q,2,0)
    mat=spec['material'];motif=spec['motif'];side=face in ('east','west')
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb*=(.99+.015*np.sin(y*.51+z*.7))[:,:,None]
    if motif=='veil':
        # Authored flowing contour brushwork, deliberately broad and legible.
        flow=z*3.7+y*1.2+.65*np.sin(y*1.8+z*2)+.40*np.sin(y*3.8-z*2.3)
        for yy,zz in ((8.25,8.29),(10.23,7.51),(12.94,9.68),(14.42,10.08)):
            r=np.hypot((y-yy)*1.2,z-zz);angle=np.arctan2((y-yy)*1.2,z-zz)
            mix=np.clip(1-r/.62,0,1)**2
            flow=flow*(1-mix)+(r*6+.3*np.sin(angle*3))*mix
        phase=np.mod(flow,1)
        rgb[phase<.12]=[31,43,45]
        rgb[(phase>=.12)&(phase<.30)]=PALETTE['teal']
        rgb[(phase>.79)&(phase<.89)]=PALETTE['bronze_light']
        rgb[(phase>=.30)&(phase<.35)]=[68,125,122]
        # No bolt geometry for these two evidenced recessed round fasteners.
        if side:
            for yy,zz in ((8.02,8.5),(13.66,9.94)):
                r=np.hypot((y-yy),(z-zz))
                rgb[r<.11]=PALETTE['recess'];rgb[(r>.066)&(r<.096)]=PALETTE['steel']
    elif motif=='arc':
        # Long unbroken pale core and lilac side falloff on actual solid strips.
        rgb*=(.97+.03*np.cos(v*math.pi*2))[:,:,None]
        rgb[:,(np.arange(w)<max(1,w//12))]=PALETTE['edge_tip']
    elif motif=='blade':
        # Quiet steel scoring; chosen shallow paired sockets, no noisy projection.
        rgb*=(.985+.025*np.sin(z*3.3+y*.15))[:,:,None]
        if side:
            for yy,zz in ((16.6,9.03),(20.4,9.04),(24.6,8.02),(27.9,6.40)):
                r=np.hypot((y-yy)*.8,(z-zz))
                rgb[(r<.12)&(r>.07)]=[123,132,157]
                rgb[r<.065]=[38,43,62]
            score=(np.mod(y*4.9+z*37,1)<.045)&(np.mod(y*.72,1)<.28)
            rgb[score]*=.79
    elif motif=='rivets':
        # Rail repeats follow local along/across dimensions, independent back UV.
        period=np.mod(y*3.2,1);across=np.mod(z*5.7,1)
        if spec['group']=='rail':
            across=(z-9.72)/.31
            rows=np.minimum(abs(across-.26),abs(across-.72))
            rr=np.hypot((period-.5)*.33,rows*.31)
            rgb[rr<.056]=PALETTE['steel'];rgb[rr<.026]=PALETTE['recess']
        else:
            rr=np.hypot((period-.5)*.33,(across-.5)*.22)
            rgb[rr<.065]=PALETTE['bronze_light'];rgb[rr<.035]=PALETTE['recess']
    elif motif=='flutes':
        # Fine parallel bronze strokes are paint, not stacks of thin geometry.
        stripes=np.mod((z-y*.17)*29,1)
        rgb[stripes<.18]*=.61;rgb[stripes>.82]*=1.11
    elif motif=='grip':
        # Black wrap with pale linked diamond/eye marks from the reference.
        period=np.mod((y-3.23)*2.60,1);across=(z-7.715)/.83
        diamond=abs(period-.5)+abs(across)*1.15
        if side:
            rgb[(diamond>.32)&(diamond<.39)]=[105,113,112]
            rgb[(diamond>.16)&(diamond<.20)]=[67,76,75]
        rgb[np.mod(y*9.4,1)<.045]*=.72
    elif motif=='fin':
        if side:
            rr=np.hypot((u-.5)*.7,(v-.51))
            rgb[(rr>.12)&(rr<.17)]=PALETTE['bronze_light']
            rgb[(u>.42)&(u<.52)&(v>.22)&(v<.72)]=[70,91,92]
    elif motif=='stone':
        # Pale uneven silver insert, drawn broad facets rather than sampled image.
        facet=np.sin(y*11+z*16)*np.sin(z*25-y*3)
        rgb*=(.91+.14*facet)[:,:,None]
        rgb[abs(np.sin(y*5-z*9))<.12]*=.78
    elif motif=='pommel' and side:
        rgb[(u>.12)&(u<.17)]=PALETTE['recess']
        for yy in (2.75,2.98):
            rr=np.hypot(y-yy,z-7.91)
            rgb[(rr>.027)&(rr<.055)]=PALETTE['recess']
    if motif not in ('veil','arc','blade'):
        border=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        rgb[border<.65]*=.87
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(23,29,36,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=27 if spec['group'] in ('hilt','grip','rail','inset') else 22
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
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    model=dict(credit="Temptation's Hook W141 / authored solid recurve and default face paint / full only",
        textures={'0':f'destiny:item/weapon/w123/{ID}','particle':f'destiny:item/weapon/w123/{ID}'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])
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
        name="Temptation's Hook W141 / offline inspection",resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w141=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    diffuse=np.asarray(Image.open(RAW/"textures/Temptation's Hook_Diffuse.png").convert('RGBA'))
    # Glow objects are not part of the main diffuse map; identify as neutral here.
    neutral=np.array([[[192,191,222,255]]],np.uint8);result=[]
    for m in meshes:
        tex=diffuse if m['material']=="Temptation's Hook Main" else neutral
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:result.append((ps,uv,tex,n/length))
    return result


def comparison(d,meshes,atlas,model):
    w,h=600,690;sheet=Image.new('RGB',(1800,2500),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,"TEMPTATION'S HOOK / W141 / SOLID RECURVE + AUTHORED DEFAULT FACE PAINT",25)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((930,485));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} filled cuboids / opaque 1024 atlas',
        'Violet edge / dark rail / bronze-teal hilt / black fins',
        'Solid webs, bevels and thin cutting section',
        '6 raw objects / 4278 triangles / exact W30 frame',
        'New face brushwork; no rip texture samples',
        'CPU views only; native acceptance pending master']):label(940,92+i*54,line,20)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    triangles=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    labels=['RAW MESH / UNDYED ALBEDO + NEUTRAL GLOW','CANONICAL / 246 VOLUME CUBOIDS',f'NEW / {len(model["elements"])} SEMANTIC SOLIDS']
    for row,cam in enumerate(([1,0,0],[.67,.12,.73])):
        yy=560+row*745
        for col,ts in enumerate(triangles):
            label(col*w+8,yy-25,labels[col],16)
            im,_=H['render'](ts,cam,H['frame'](points,cam,w,h),(w,h),raw=col==0);sheet.paste(im,(col*w,yy))
    # Detail crop: an oblique hilt view shows relief, actual guard teeth and grip.
    cam=[.84,.10,-.53];detail=points[(points[:,1]>7.1)&(points[:,1]<15.9)]
    for col,ts in enumerate(triangles):
        im,_=H['render'](ts,cam,H['frame'](detail,cam,600,390),(600,390),raw=col==0);sheet.paste(im,(col*w,2072))
    label(20,2025,'HILT DETAIL / reverse oblique / physical fin spacing and raised brace / same framing',20)
    label(20,2470,'Offline CPU study. Pack, DCC, held, third person, swing, guard, caster,10-20 display: pending master.',18)
    return png(sheet)


def review_text(d,counts):
    return f"""# Temptation's Hook W141

{len(d['parts'])} authored filled cuboids ({len(d['parts'])*6} opaque faces), zero triangle-adapter elements. A continuous swept blade uses solid webs, shoulders, bevels and a thinner violet-white cutting edge. The recurve and hooked return are geometry, not an alpha silhouette. A dark double-rivet spine rail, bronze/teal contour hilt, raised diagonal bronze brace, pale side insert, black fin guard, patterned grip and angular silver pommel retain the default identity. The guard has real tooth gaps; the hilt's setback and insert have side relief. Shallow fasteners, parallel flutes, wrap eyes, steel scoring and broad flowing hilt contours are new face paint. Every face has its own rectangle with two-pixel extruded gutters in the fully opaque 1024 atlas.

Default appearance is grounded in the W31 Bungie screenshot (hash35794111, SHAa3b54621dcfa09b6ddc3021712cf66c412a45b064a38cd8d4649557a5eec4e6c) and local raw artist preview. The comparison labels raw main albedo undyed and energy objects neutral. Neither is claimed as recovered default PBR. The new atlas samples none of the source pixels or UV islands. The veil pattern is intentionally simplified, authored contour brushwork; native energy bloom, reflections and animated shader effects are not reproduced by this static RGBA texture.

The inert Blender3.3 reader decompresses the local source as data and decodes SDNA field sizes (MVert is16bytes here, unlike older20byte files). All six W30 retained objects and4278 triangles match. Stored matrices are applied before mapping `anchor + scale * [world.X, world.Z, world.Y]`; all source/native bounds agree within1e-7. The sword remains +Y, thinX; scale21.078860348466854, hand anchor[8,4.738785774747939,8]. The grip's actual center is nearZ7.715 and includes the canonical hand anchor. All canonical display transforms are copied exactly.

Full model only. Existing item selectors, W140 native swordframe carry, combat, audio, animation, ADS/inspect and ammo behavior remain outside this delta. The integration owner must route the shared surface registry/item inheritance when appropriate; this worker does not change it or add a reload split. Editable inspection.bbmodel and CPU side/oblique/reverse hilt comparisons are available, but are not native acceptance. Master still owns pack/DCC, first/third person, swing/guard/caster, audio/server and10-20 display checks. Cuboid station joins and point curvature are the primary visual simplifications to inspect.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
    counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
        ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    pts=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id=ID,revision='W141',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[pts.min(0).tolist(),pts.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        canonical_display_exact=True,full_only=True,native_swordframe='W140 unchanged',native_accepted=False,
        generator_sha256=sha((ROOT/SCRIPT).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();scope=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w141-'+ID)
    assert set(outputs)<=set(scope)
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
