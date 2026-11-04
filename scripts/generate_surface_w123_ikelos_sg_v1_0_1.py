#!/usr/bin/env python3
"""W136 IKELOS_SG_v1.0.1: deterministic semantic solid-cuboid art; full export only.
Read-only reuse of W126 inert FBX and CPU raster helpers. No DCC/game actions.
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
import struct
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/ikelos_sg_v1_0_1/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/shotgun/ikelos_sg_v1_0_1.json'
MODEL = ASSET + 'models/weapon_surface_w123/ikelos_sg_v1_0_1.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/ikelos_sg_v1_0_1.png'
REPORT = 'docs/qa/2026-10-26/w136/ikelos_sg_v1_0_1-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/ikelos_sg_v1_0_1/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/ikelos_sg_v1_0_1.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(carbon=[140,127,140], darkcarbon=[68,59,67], silver=[166,166,160],
    edge=[194,191,179], steel=[86,86,82], graphite=[48,50,48], recess=[16,18,18],
    rubber=[37,33,29], copper=[182,127,104], ochre=[135,106,55], walnut=[118,75,43])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w136:ikelos_sg_v1_0_1:'+name))


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


def parse_fbx(path):
    """Binary FBX 7500 / 64-bit node reader; inert arrays only, no source execution."""
    data = path.read_bytes()
    assert data[:23] == b'Kaydara FBX Binary  \x00\x1a\x00'
    assert struct.unpack_from('<I', data, 23)[0] == 7500

    def node(pos):
        end, count, _, length = struct.unpack_from('<QQQB', data, pos)
        pos += 25
        if end == 0:
            return None, pos
        name = data[pos:pos + length].decode()
        pos += length
        properties = []
        for _ in range(count):
            kind = chr(data[pos]); pos += 1
            if kind in 'YCFDIL':
                fmt = {'Y': 'h', 'C': '?', 'I': 'i', 'F': 'f', 'D': 'd', 'L': 'q'}[kind]
                value = struct.unpack_from('<' + fmt, data, pos)[0]
                pos += struct.calcsize(fmt)
            elif kind in 'SR':
                length = struct.unpack_from('<I', data, pos)[0]; pos += 4
                value = data[pos:pos + length]; pos += length
                if kind == 'S':
                    value = value.decode(errors='replace')
            elif kind in 'fdlibc':
                length, compression, size = struct.unpack_from('<III', data, pos); pos += 12
                raw = data[pos:pos + size]; pos += size
                assert compression in (0, 1)
                if compression:
                    raw = zlib.decompress(raw)
                fmt = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': '?', 'c': 'b'}[kind]
                value = struct.unpack('<' + str(length) + fmt, raw)
            else:
                raise ValueError('Unsupported FBX type ' + kind)
            properties.append(value)
        children = []
        while pos < end - 25:
            child, pos = node(pos)
            assert child is not None
            children.append(child)
        return (name, properties, children), end

    roots = []; pos = 27
    while pos < len(data):
        value, pos = node(pos)
        if value is None:
            break
        roots.append(value)
    return roots


def source_meshes():
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/ikelos_sg_v1_0_1.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'IKELOS_SG_v1_0_1.fbx').read_bytes())==meta['source_files']['IKELOS_SG_v1_0_1.fbx']
    roots=parse_fbx(RAW/'IKELOS_SG_v1_0_1.fbx')
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
        # FBX 7500 contains identity model transforms and baked geometry.
        assert 'Lcl Rotation' not in props and 'Lcl Scaling' not in props
        cs={c[0]:c for c in node[2]}
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=np.c_[-raw[:,1],raw[:,2],-raw[:,0]]*meta['scale']+meta['anchor']
        faces=[]; face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3; faces.append(face); face=[]
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByVertice' and vals['ReferenceInformationType']=='Direct'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(faces)]
        uv[:,:,1]=1-uv[:,:,1]
        material=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=name.split('_')[0]))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5,rtol=0)
    assert sum(len(m['faces']) for m in meshes)==39273
    # W30 blend count 31852 differs from raw FBX's padded triangle arrays.
    # Keep both counts; never claim topology equivalence.
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    return meshes,meta


def make_design(meta):
    """Semantic filled volumes. All coordinates authored in W30's absolute hand frame."""
    parts=[]
    def box(name,lo,hi,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(pos,size)],[round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name,a,b,width,depth,mat,group,motif='plain'):
        dy=b[1]-a[1];dz=b[2]-a[2];angle=-math.degrees(math.atan2(dy,dz))
        if angle>90:angle-=180
        if angle<-90:angle+=180
        c(name,[(x+y)/2 for x,y in zip(a,b)],[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',angle))
    # Large continuous upper housing, with full cross-section, no alpha side plates.
    box('shroud_core',[7.29,11.68,-9.02],[8.71,13.05,3.28],'carbon','shroud','carbon')
    box('shroud_long_nose',[7.29,11.76,-9.53],[8.71,12.61,-8.93],'carbon','shroud','emblem')
    beam('nose_chamfer',[8,11.68,-9.04],[8,12.17,-9.64],1.42,.57,'carbon','shroud','carbon')
    box('shroud_top_rail',[7.40,13.04,-9.03],[8.60,13.124,3.26],'silver','shroud','rail')
    beam('shroud_rear_slope',[8,12.32,3.23],[8,11.83,4.75],1.42,1.15,'carbon','shroud','carbon')
    box('shroud_heel',[7.37,11.40,3.80],[8.63,12.11,4.971],'darkcarbon','shroud','carbon')
    box('lower_receiver',[7.32,10.48,-5.38],[8.68,11.68,5.27],'graphite','action','action')
    box('lower_receiver_rear',[7.31,10.48,4.85],[8.69,11.60,8.22],'graphite','action','action')
    box('long_barrel_rail',[7.43,10.60,-8.35],[8.57,11.48,-5.18],'graphite','action','action')
    beam('lower_action_chamfer',[8,10.22,3.44],[8,10.78,5.28],1.27,.60,'graphite','action','action')
    box('action_side_ledge',[7.24,10.38,-4.86],[8.76,10.58,4.75],'steel','action','rail')
    # Deep rectangular bore between independent upper/lower jaws.
    zmin=meta['model_bounds'][0][2]
    box('muzzle_roof',[7.36,11.50,zmin],[8.64,11.76,-8.46],'steel','muzzle','metal')
    box('muzzle_floor',[7.36,10.58,zmin],[8.64,10.80,-8.46],'steel','muzzle','metal')
    for side in (-1,1):
        box(f'muzzle_wall_{side}',[8+side*.55-.10,10.76,zmin],[8+side*.55+.10,11.54,-8.46],'silver','muzzle','metal')
    box('bore_depth_stop',[7.45,10.78,-8.48],[8.55,11.52,-8.35],'recess','muzzle')
    box('lower_nose_core',[7.31,9.47,-9.58],[8.69,10.39,-6.50],'darkcarbon','muzzle','carbon')
    beam('lower_nose_chamfer',[8,9.61,-9.58],[8,10.05,-9.87],1.38,.51,'darkcarbon','muzzle','carbon')
    beam('lower_nose_heel',[8,9.66,-6.72],[8,10.19,-7.10],1.38,.45,'darkcarbon','muzzle','carbon')
    # Ribbed foregrip: broad solid brown core, ribs authored on continuous face UV.
    box('foregrip_core',[7.35,9.237,-5.89],[8.65,10.48,-.42],'walnut','foregrip','ribs')
    for z in (-5.91,-.37):
        c('foregrip_collar_'+str(z),[8,9.93,z],[1.42,1.44,.24],'steel','foregrip','collar')
    box('foregrip_lower_edge',[7.42,9.25,-5.84],[8.58,9.44,-.45],'walnut','foregrip','ribs')
    # Four source-backed capacitor housings on each side; actual full solid blocks.
    for i,z in enumerate((-2.12,-.67,.78,2.23)):
        for side in (-1,1):
            x=8+side*1.28
            c(f'capacitor_{i}_{side}',[x,10.88,z],[1.05,.78,.85],'copper','capacitors','module')
            c(f'capacitor_socket_{i}_{side}',[8+side*.87,11.29,z-.04],[.31,.23,.73],'steel','capacitors','socket')
            c(f'shroud_strut_{i}_{side}',[8+side*.78,12.32,z-.29],[.17,1.67,.16],'steel','braces','strut')
            # Slanted surface cable is UV; the lower lifted elbows need depth/parallax.
            beam(f'cable_upper_{i}_{side}',[8+side*.91,11.86,z-.16],[8+side*.96,11.47,z+.11],.12,.12,'edge','braces')
            beam(f'cable_lower_{i}_{side}',[8+side*.96,11.47,z+.11],[8+side*1.03,11.17,z+.04],.12,.12,'ochre','braces')
        c(f'top_saddle_{i}',[8,13.14,z-.29],[1.32,.18,.23],'steel','braces','saddle')
    # Rear action bellows and two large solid disc hubs are recognizable stock landmarks.
    box('bellows_core',[7.58,11.32,4.86],[8.42,12.06,6.30],'steel','stock','bellows')
    box('stock_spine',[7.45,10.81,6.26],[8.55,11.54,14.58],'graphite','stock','stock')
    box('cheek_rest',[7.39,11.48,10.46],[8.61,11.99,13.19],'darkcarbon','stock','carbon')
    beam('cheek_rest_front',[8,11.52,9.94],[8,11.80,10.63],1.20,.42,'darkcarbon','stock','carbon')
    beam('butt_plate',[8,8.30,14.30],[8,11.16,14.71],1.32,.38,'graphite','stock','stock')
    beam('butt_upper_horn',[8,11.16,14.51],[8,11.91,14.79],1.22,.23,'steel','stock','metal')
    # Terminate precisely at original positive-Z endpoint, no global scale/anchor change.
    box('stock_tail',[7.43,10.62,14.54],[8.57,11.07,meta['model_bounds'][1][2]],'graphite','stock','stock')
    beam('stock_lower_strut',[8,10.63,10.61],[8,8.37,13.62],.92,.44,'steel','stock','stock')
    beam('stock_rubber_sleeve',[8,10.29,11.12],[8,8.68,13.28],1.09,.65,'rubber','stock','rubber')
    for name,y,z,r in (('front',11.52,7.32,.73),('rear',9.20,13.83,.70)):
        # Convex octagon: central cross plus four inward-overlapped corner diamonds.
        # Every diamond lies inside the polygon: no cog/star silhouette and no mesh adapter.
        aa=r*(math.sqrt(2)-1);ll=(r-aa)*math.sqrt(2)
        c(name+'_hub_cross_y',[8,y,z],[1.53,2*r,2*aa],'silver','hubs','hub')
        c(name+'_hub_cross_z',[8,y,z],[1.53,2*aa,2*r],'silver','hubs','hub')
        for j,(sy,sz) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):
            c(name+'_hub_corner_'+str(j),[8,y+sy*aa,z+sz*aa],[1.53,ll,ll],'silver','hubs','hub',('x',45))
        for side in (-1,1):
            c(name+'_hub_cap_'+str(side),[8+side*.81,y,z],[.16,r*.62,r*.62],'steel','hubs','hubcap',('x',45))
    # Skeletal grip with real openings, kept in the original rear hand neighborhood.
    beam('grip_front',[8,7.20,9.08],[8,10.10,7.83],.78,.22,'steel','grip','grip')
    beam('grip_back',[8,7.30,9.95],[8,9.96,8.79],.78,.24,'steel','grip','grip')
    beam('grip_heel',[8,7.13,9.12],[8,7.29,9.95],.81,.23,'steel','grip','grip')
    beam('grip_top',[8,9.87,7.84],[8,9.87,8.83],.81,.30,'graphite','grip','grip')
    beam('grip_diagonal_a',[8,7.35,9.25],[8,9.40,8.57],.39,.13,'steel','grip')
    beam('grip_diagonal_b',[8,8.40,8.67],[8,9.37,8.96],.40,.13,'steel','grip')
    beam('grip_midbrace',[8,8.38,8.68],[8,8.52,9.42],.42,.13,'steel','grip')
    # Open trigger guard and shallow fixed trigger; no new moving/runtime parts.
    box('trigger_guard_front',[7.73,9.03,6.47],[8.27,10.63,6.68],'steel','guard')
    beam('trigger_guard_floor',[8,9.12,6.55],[8,9.20,7.57],.54,.17,'steel','guard')
    beam('trigger_guard_rear',[8,9.20,7.54],[8,10.22,7.80],.54,.17,'steel','guard')
    beam('trigger',[8,10.54,7.01],[8,9.91,7.19],.20,.14,'graphite','guard')
    # Existing open sight brackets, within W30 maximum Y.
    for side in (-1,1):
        beam('sight_ear_'+str(side),[8+side*.30,12.94,3.67],[8+side*.30,13.48,3.87],.13,.15,'steel','sight')
        c('sight_tip_'+str(side),[8+side*.30,13.53,3.93],[.14,.11767597773345,.30],'edge','sight')
    box('sight_base',[7.60,12.76,3.48],[8.40,12.94,4.10],'graphite','sight')
    beam('rear_sight_left',[7.71,12.06,7.56],[7.71,12.65,7.32],.11,.10,'steel','sight')
    beam('rear_sight_right',[8.29,12.06,7.56],[8.29,12.65,7.32],.11,.10,'steel','sight')
    c('rear_sight_bridge',[8,12.65,7.32],[.67,.10,.11],'steel','sight')
    inputs=[BASE,'art/blockbench/weapons/w30/ikelos_sg_v1_0_1.bbmodel','art/weapons/w30/catalog.json',
            'art/weapons/w31/references.json',HELPER,ASSET+'textures/item/weapon/w30/ikelos_sg_v1_0_1.png']
    raw_inputs=[RAW/'IKELOS_SG_v1_0_1.fbx',RAW/'IKELOS_SG_v1.0.1.blend',PHOTO]+sorted((RAW/'Textures').glob('*_albedo.png'))
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='ikelos_sg_v1_0_1')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    catalogue=next(r for r in json.loads((ROOT/'art/weapons/w30/catalog.json').read_bytes()) if r['id']=='ikelos_sg_v1_0_1')
    assert catalogue['family']=='shotgun'
    assert sha((RAW/'IKELOS_SG_v1.0.1.blend').read_bytes())==meta['source_files']['IKELOS_SG_v1.0.1.blend']
    return dict(id='ikelos_sg_v1_0_1',revision='W136',method='authored filled semantic cuboids and proportional independent face UV',
        source=meta,reference=ref,catalogue=catalogue,palette=PALETTE,parts=parts,
        identity=['long mauve carbon shroud with white geometric nose mark','four paired copper modules / pale and ochre cable braces',
                  'ribbed brown foregrip / dark chassis / rectangular deep muzzle','skeletal grip and stock / two circular stock hubs'],
        coordinate_policy=dict(basis='native X=-FBX Y, Y=FBX Z, Z=-FBX X; identity model transforms; muzzle -Z',
            scale=meta['scale'],anchor=meta['anchor'],grip='skeletal grip near native Z8..10, Y7..10; no recenter',
            display='exact canonical dictionary',export='full only; existing generic reload / ADS / audio / timing unchanged'),
        source_alignment=dict(fbx_version=7500,fbx_triangles=39273,w30_blend_triangles=meta['source_triangles'],
            bounds_match_tolerance=1e-5,retained_objects=meta['source_objects'],
            topology_note='Raw FBX contains padded/degenerate faces; its 39273 records differ from W30 blend count 31852. Bounds and names match; topology equivalence not claimed.'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Offline CPU art only; native target parser, held/ADS/reload and 10-20 displays pending master.',
            'Photo-backed static matte colors and subtle carbon weave are not recovered PBR or exact default shader graphs.',
            'Hubs use six-cuboid filled octagonal approximations; curved cables use two broad elbow segments.',
            'Opposite-side photo unavailable; no invented reverse-side emblem. Raw FBX and W30 blend triangle counts differ.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];u,v,q=world_points(spec['geometry'],face,w,h)
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.98+.035*np.exp(-((v-.32)/.45)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    if motif!='hub':
        rgb[edge<.7]*=.73;rgb[(edge>=.7)&(edge<1.5)]*=1.08
    side=face in ('east','west');z=q[:,:,2];y=q[:,:,1]
    def line(yline,mask,width=.018):
        nonlocal rgb
        rgb[mask&(abs(y-yline)<width)]*=.55
        rgb[mask&(abs(y-yline-.033)<.012)]*=1.12
    def screw(zc,yc,r=.067):
        rr=np.hypot(z-zc,y-yc)
        rgb[rr<r]=PALETTE['graphite'];rgb[(rr>r*.72)&(rr<r)]=PALETTE['silver']
        rgb[(rr<r*.55)&(abs(z-zc)<.012)]=PALETTE['steel']
    if motif in ('carbon','emblem'):
        # Low-contrast ordered carbon twill, subordinate to broad quiet material planes.
        aa=(z+y)*6;bb=(z-y)*6
        weave=np.where((np.floor(aa)+np.floor(bb))%4<2,1.025,.975)
        rgb*=weave[:,:,None]
        if side:
            line(11.82,np.ones_like(u,dtype=bool),.015)
            if spec['geometry']['name']=='shroud_core':
                # Four pale diagonal cable runs and ochre edge, aligned across faces.
                for zz in (-2.12,-.67,.78,2.23):
                    cable_z=zz-.29+(13.08-y)*.43
                    run=(y>11.85)&(y<13.06)
                    rgb[run&(abs(z-cable_z)<.034)]=PALETTE['ochre']
                    rgb[run&(abs(z-cable_z+.07)<.035)]=PALETTE['edge']
                    for yy in (11.89,12.91):
                        bar=(abs(y-yy)<.036)&(abs(z-(zz-.29+(13.08-yy)*.43))<.18)
                        rgb[bar]=PALETTE['silver']
                # Actual photo's geometric diamond/wing mark, visible side only.
                if face=='west':
                    zz=(z+8.17)/.36;yy=(y-12.18)/.40
                    diamond=abs(zz)+abs(yy)
                    mark=((diamond<1)&(diamond>.54))|((yy>.70)&(yy<.96)&(abs(zz)<1.22))
                    rgb[mark]=PALETTE['edge']
    if side and motif in ('action','stock'):
        line(10.88,(z>-5)&(z<14),.018)
        for zc,yc in ((-4.9,10.67),(-.10,10.81),(3.7,10.77),(5.5,11.04),(10.3,11.0),(14.2,10.92)):screw(zc,yc)
        if motif=='action':
            slot=(z>.4)&(z<3.6)&(y>10.96)&(y<11.19);rgb[slot]=PALETTE['recess']
            rgb[slot&(y<11.01)]=PALETTE['steel']
    if motif in ('ribs','rubber','bellows'):
        phase=np.mod((z if motif!='rubber' else y)*6,1)
        rgb[phase<.16]*=.57;rgb[(phase>.16)&(phase<.29)]*=1.28
        if motif=='ribs':
            rgb[(phase>.29)&(phase<.40)]=PALETTE['silver']
            if side:rgb[(y<9.43)|(y>10.28)]*=.79
    if side and motif=='module':
        # Raised housings have dark recessed diamond motifs painted per side.
        zz=(u-.50)/.19;yy=(v-.52)/.23;diam=abs(zz)+abs(yy)
        rgb[(diam>.8)&(diam<1.02)]=PALETTE['steel']
        rgb[(v<.17)&(u>.2)&(u<.74)]*=1.18
    if motif=='rail':
        phase=np.mod(z*8,1);rgb[(face=='up')&(phase<.12)]*=.60
    if motif in ('hub','hubcap') and side:
        # Concentric machining, no source reprojected blotches.
        yc,zc=(11.52,7.32) if spec['geometry']['name'].startswith('front') else (9.20,13.83)
        rr=np.hypot(y-yc,z-zc)
        for r in (.20,.28,.47):rgb[abs(rr-r)<.016]*=.56
        if motif=='hubcap':rgb[rr<.07]=PALETTE['ochre']
    if motif in ('collar','socket','grip') and side:
        e=spec['geometry'];screw((e['to'][2]+e['from'][2])/2,(e['to'][1]+e['from'][1])/2,.055)
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=30 if spec['motif'] in ('carbon','action','ribs','module','stock','grip') else 20
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
    model=dict(credit='IKELOS_SG_v1.0.1 W136 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/ikelos_sg_v1_0_1','particle':'destiny:item/weapon/w123/ikelos_sg_v1_0_1'},
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
        name='IKELOS_SG_v1.0.1 W136 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='ikelos_sg_v1_0_1.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w136=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    result=[];textures={}
    for m in meshes:
        mat=m['material']
        if mat not in textures:
            f=RAW/'Textures'/(mat+'_albedo.png')
            textures[mat]=np.asarray(Image.open(f).convert('RGBA')) if f.exists() else np.full((4,4,4),[130,130,130,255],np.uint8)
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((t,uv,textures[mat],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=900,380;sheet=Image.new('RGB',(2700,2070),'#151d27');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'IKELOS_SG_v1.0.1 / W136 / FILLED SEMANTIC SOLIDS + AUTHORED FACE UV / CPU ART',28)
    photo=Image.open(PHOTO).convert('RGB').crop((620,225,1850,690));photo.thumbnail((1100,345));sheet.paste(photo,(15,65))
    label(20,418,'ACTUAL DEFAULT PHOTO / Bungie 1887808042 / mauve carbon + copper + dark frame',17)
    for i,fn in enumerate(('85DDEA80_albedo.png','1709EB80_albedo.png')):
        im=Image.open(RAW/'Textures'/fn).convert('RGB');im.thumbnail((230,310));sheet.paste(im,(1135+i*245,67));label(1135+i*245,395,'RAW NEUTRAL '+('BODY' if i==0 else 'FRAME'),15)
    for i,line in enumerate([f'{len(model["elements"])} opaque filled cuboids / full only',
          'Mauve carbon shroud / copper modules / brown ribs',
          'Continuous UV / cables / emblem / hub machining',
          'Deep rectangular bore / skeletal stock + grip',
          'Original axis / anchor / scale / canonical display',
          'CPU inspection only; native QA pending master']):label(1640,80+i*49,line,21)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/ikelos_sg_v1_0_1.png'))
    label(20,455,'ACTUAL FBX / 39,273 records incl. padding / NEUTRAL')
    label(w+20,455,f'CANONICAL / {len(old["elements"])} cuboids / NOT RAW FBX')
    label(2*w+20,455,f'W136 / {len(model["elements"])} authored solids / CPU ART')
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE / DEFAULT PHOTO SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.42,-.65]),('OPPOSITE REAR THREE-QUARTER',[1,.36,.65])]):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,490+row*h));label(col*w+15,498+row*h,name,17)
    for col,(groups,cam) in enumerate([(('muzzle',),[.18,.13,-1]),(('sight',),[-.1,.1,-1]),(('grip','guard'),[-1,.10,-.12]),(('stock','hubs'),[-1,.16,.3]),(('capacitors','braces'),[-1,.35,-.6])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names]);points=np.concatenate([vertices(e) for e in sub['elements']])
        im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](points,cam,540,335),(540,335))
        sheet.paste(im,(col*540,1660));label(col*540+14,1668,' + '.join(groups).upper(),17)
    label(20,2025,'Matched camera + scale per row. Native parser, held/ADS, generic reload/audio/timing and 10-20 displays pending master.',21)
    return png(sheet)


def review_text(d,counts):
    return f"""# IKELOS_SG_v1.0.1 W136 offline art review

Default reference: `{PHOTO}`, Bungie 1887808042. SHA-256 `{d['reference']['sha256']}`. Visually inspected before authoring. Rapid-fire shotgun confirmed from W30 catalogue; no alternate version or shader mixed in. Observed identity: long mauve carbon upper slab, dark lower action, four copper capacitors on each side with pale/ochre diagonal cables, brown ribbed foregrip, skeletal pistol grip/stock and two circular stock hubs. White diamond/wing nose mark is authored on the photographed side; opposite side stays unmarked. Subtle ordered carbon twill, panel scribes, grip ribs and hub rings use authored face UV, not raw mesh transfer or noisy albedo projection.

{sum(counts.values())} emitted opaque filled cuboids; {sum(counts.values())*6} explicit face UVs; zero triangle adapter elements; zero alpha silhouette shells. Full assembly {sum(counts.values())}/1000. Group counts: {json.dumps(counts,sort_keys=True)}. Shroud, lower receiver, capacitor blocks and foregrip have broad solid interiors. Actual geometry leaves the rectangular muzzle bore with recessed depth stop, stock opening, grip lattice and guard aperture. Shallow surface cables are UV; lifted lower elbows are filled beams. Hubs deliberately approximate circular hardware with six filled cuboids forming a convex octagon; roundness and cable curvature are simplified. Editor groups are semantic selection aids, not runtime animation parts.

Every face has a proportional independent UV rectangle on the 1024 atlas with two-pixel extruded opaque gutters; {d['atlas']['face_islands']} islands, used height {d['atlas']['used_height']}. No transparency is sampled by any face. The inspection BBModel embeds the exact emitted atlas and preserves editable cuboids, rotations, groups, UVs and display dictionary. Static matte paint is not Bungie's recovered PBR/default shader graph.

Source alignment was derived rather than copied: FBX 7500 uses 64-bit node headers, identity model transforms, and Direct/ByVertice UV. Actual raw FBX has length +X toward muzzle, thin Y, height Z. Native basis is **[-FBX Y, FBX Z, -FBX X] × {d['source']['scale']} + {d['source']['anchor']}**, hence muzzle -Z. All ten retained object names and the union bounds match W30 within 1e-5 native units (maximum float-export residual about 0.000006302). Both source FBX and blend hashes match W30. The raw FBX contains 39,273 triangle records including padding/degenerate faces, whereas W30 records 31,852 blend triangles; those counts are intentionally distinct and topology equivalence is not claimed. The FBX is read as inert arrays; no embedded source code/shader execution occurs.

Original absolute length endpoints, source scale/anchor, skeletal grip neighborhood and exact canonical display transforms are preserved. Candidate resource `destiny:weapon_surface_w123/ikelos_sg_v1_0_1`, texture `destiny:item/weapon/w123/ikelos_sg_v1_0_1`. Full only; existing generic reload remains. No shared registry, manifest, HUD, runtime, canonical model, ADS, combat, audio or timing edits; no invented moving parts or split magazines.

comparison.png includes the actual default photo, two raw neutral albedo maps, actual raw FBX, 230-cuboid read-only canonical model and new art at matched side/front-quarter/opposite-rear-quarter camera scales. Lower row isolates bore, sights, grip/guard, stock/hubs and capacitor/cable geometry. Actual final image observations and test results are recorded in the worker report.

Offline targeted checks cover scope, filled depth, assembled budget, canonical display/hand frame, real openings, UV opacity/gutters, provenance/hashes, editable inspection parity and deterministic generation. Native 26.3 parser/pack load, representative first/third-person grip, ADS, generic reload/audio/timing and 10-20 displays are **pending master**. Offline rendering alone is not native acceptance or performance evidence. No Gradle, DCC, native/game/server or children used; unsaved DCC work untouched.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta)
    source_points=np.concatenate([m['vertices'] for m in meshes])
    source_bounds=np.array([source_points.min(0),source_points.max(0)])
    d['source_alignment'].update(fbx_native_bounds=source_bounds.tolist(),max_bounds_residual=float(np.abs(source_bounds-meta['model_bounds']).max()))
    atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='ikelos_sg_v1_0_1',revision='W136',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=39273,w30_blend_triangles=meta['source_triangles'],source_alignment=d['source_alignment'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        canonical_display_exact=True,full_only=True,generic_reload_ADS_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        default_photo_sha256=d['reference']['sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


OWNED=[
    'scripts/generate_surface_w123_ikelos_sg_v1_0_1.py',
    'scripts/qa/test_surface_w123_ikelos_sg_v1_0_1.py',
    ART+'design.json',ART+'manifest.json',ART+'review.md',ART+'inspection.bbmodel',ART+'comparison.png',
    REPORT,TEXTURE,MODEL]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();assert len(OWNED)==10 and set(outputs)<=set(OWNED)
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
