#!/usr/bin/env python3
"""W142 IKELOS_SMG_v1.0.1: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/ikelos_smg_v1_0_1/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/submachine_gun/ikelos_smg_v1_0_1.json'
MODEL = ASSET + 'models/weapon_surface_w123/ikelos_smg_v1_0_1.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/ikelos_smg_v1_0_1.png'
REPORT = 'docs/qa/2026-10-26/w142/ikelos_smg_v1_0_1-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/ikelos_smg_v1_0_1/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/ikelos_smg_v1_0_1.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(carbon=[140,127,140], darkcarbon=[68,59,67], silver=[166,166,160],
    edge=[194,191,179], steel=[86,86,82], graphite=[48,50,48], recess=[16,18,18],
    rubber=[37,33,29], copper=[182,127,104], ochre=[135,106,55], walnut=[118,75,43], bronze=[147,124,95])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w142:ikelos_smg_v1_0_1:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/ikelos_smg_v1_0_1.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'IKELOS_SMG_v1_0_1.fbx').read_bytes())==meta['source_files']['IKELOS_SMG_v1_0_1.fbx']
    roots=parse_fbx(RAW/'IKELOS_SMG_v1_0_1.fbx')
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
        v=np.c_[raw[:,1],raw[:,2],-raw[:,0]]*meta['scale']+meta['anchor']
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
    assert sum(len(m['faces']) for m in meshes)==38980
    # W30 blend count 31768 differs from raw FBX's padded triangle arrays.
    # Keep both counts; never claim topology equivalence.
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    return meshes,meta


def make_design(meta):
    """Hand-authored full solids in absolute W30 hand coordinates; no mesh reduction."""
    parts=[]
    def c(name,pos,size,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':[round(a-b/2,8) for a,b in zip(pos,size)],
                           'to':[round(a+b/2,8) for a,b in zip(pos,size)]})
        if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=(turn[1]+90)%180-90)
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def beam(name,a,b,width,depth,mat,group,motif='plain'):
        dy=b[1]-a[1];dz=b[2]-a[2]
        c(name,[(x+y)/2 for x,y in zip(a,b)],[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',-math.degrees(math.atan2(dy,dz))))
    def disc(name,y,z,r,thick,mat):
        # Six overlapping solids fill a convex octagon. No cog/star or hollow shells.
        aa=r*(math.sqrt(2)-1);ll=(r-aa)*math.sqrt(2)
        c(name+'_cross_y',[8,y,z],[thick,2*r,2*aa],mat,'hub','hub')
        c(name+'_cross_z',[8,y,z],[thick,2*aa,2*r],mat,'hub','hub')
        for j,(sy,sz) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):
            c(name+'_corner_'+str(j),[8,y+sy*aa,z+sz*aa],[thick,ll,ll],mat,'hub','hub',('x',45))
    # Long solid receiver and separate lower ledge. Copper cells remain proud of its sides.
    c('carbon_receiver',[8,12.16,1.98],[1.39,1.25,5.38],'carbon','receiver','carbon')
    c('nose_upper_jaw',[8,12.44,-1.28],[1.39,.45,.82],'carbon','receiver','emblem',('x',-28))
    c('nose_lower_jaw',[8,11.01,-1.30],[1.39,.40,.82],'carbon','receiver','carbon',('x',28))
    c('receiver_rear_cuff',[8,11.95,4.54],[1.58,1.81,.40],'graphite','receiver','action')
    c('receiver_top_deck',[8,12.90,1.54],[1.26,.23,5.45],'graphite','receiver','rail')
    c('upper_action',[8,12.02,7.30],[1.18,1.05,5.28],'graphite','action','action')
    c('upper_action_rail',[8,12.63,7.28],[1.00,.18,5.40],'steel','action','rail')
    c('lower_chassis',[8,10.77,7.46],[1.26,.67,6.02],'graphite','action','action')
    c('gas_piston',[8,11.20,7.39],[.66,.25,4.72],'silver','action','piston')
    c('gas_piston_clamp',[8,11.18,7.83],[.91,.43,.33],'silver','action','collar')
    c('rear_bellows',[8,12.02,10.20],[.92,.91,.73],'graphite','action','bellows')
    # Eight solid tangent walls form the source's circular bore approximation.
    # Receiver begins behind the recessed stop: the bore is actual air in the full model.
    for i in range(8):
        theta=i*math.pi/4;r=.38
        c('muzzle_wall_'+str(i),[8+math.sin(theta)*r,11.68+math.cos(theta)*r,-1.22],
          [2*r*math.tan(math.pi/8)+.025,.14,.80],'silver','muzzle','metal',('z',-i*45))
    c('bore_stop',[8,11.68,-.78],[.67,.67,.16],'recess','muzzle')
    # Four capacitor units on each side: their transverse housings and lifted leads.
    for i,z in enumerate((.52,1.58,2.64,3.70)):
        for side in (-1,1):
            x=8+side*1.08
            c(f'cell_{i}_{side}',[x,11.50,z],[.88,.80,.72],'copper','cells','cell')
            c(f'cell_socket_{i}_{side}',[x,11.99,z-.04],[.72,.20,.65],'steel','cells','socket')
            beam(f'cell_lead_{i}_{side}',[8+side*.77,12.69,z-.35],[8+side*1.07,11.99,z+.10],.11,.12,'silver','leads','lead')
        c('cell_saddle_'+str(i),[8,12.79,z-.35],[1.53,.13,.20],'steel','leads','saddle')
    # Two side frames create actual windows, with deep cross rails joining their ends.
    for side in (-1,1):
        x=8+side*.56
        beam('frame_floor_'+str(side),[x,10.19,-1.8984861904674793],[x,10.19,4.93],.23,.24,'bronze','foreframe','frame')
        beam('frame_nose_riser_'+str(side),[x,10.20,-.78],[x,10.85,-.25],.23,.23,'bronze','foreframe','frame')
        beam('frame_front_brace_'+str(side),[x,10.24,.32],[x,11.13,1.25],.23,.19,'bronze','foreframe','frame')
        beam('frame_central_brace_'+str(side),[x,10.25,1.63],[x,10.97,2.39],.23,.18,'bronze','foreframe','frame')
        beam('frame_rear_brace_'+str(side),[x,10.20,4.90],[x,10.98,4.90],.23,.21,'bronze','foreframe','frame')
        beam('frame_grip_diagonal_'+str(side),[x,10.22,2.15],[x,7.91,5.30],.23,.24,'bronze','foreframe','frame')
        beam('frame_grip_back_'+str(side),[x,7.93,5.30],[x,10.78,5.10],.23,.23,'bronze','foreframe','frame')
    c('frame_front_crossbar',[8,10.19,-1.8934861904674793],[1.35,.29,.25],'bronze','foreframe','frame')
    beam('ribbed_foregrip',[8,9.92,1.85],[8,7.96,4.97],1.10,.52,'bronze','foregrip','ribs')
    # Seven broad ribs affect the foregrip's underside silhouette, not surface tiling.
    for i in range(7):
        t=(i+.5)/7;y=9.92-1.96*t;z=1.85+3.12*t
        c('foregrip_rib_'+str(i),[8,y-.16,z-.10],[1.20,.22,.65],'bronze','foregrip','ribs',('x',-32.13))
    # Source-visible bent silver hose and dark terminal outside the right receiver.
    for i,(a,b) in enumerate(zip(((8.74,12.19,4.72),(8.74,12.15,5.18),(8.74,11.83,5.54),(8.74,11.28,5.67)),
                                ((8.74,12.15,5.18),(8.74,11.83,5.54),(8.74,11.28,5.67),(8.74,10.98,5.65)))):
        beam('front_hose_'+str(i),a,b,.49,.49,'silver' if i<3 else 'rubber','action','tube')
    c('front_hose_boss',[7.23,11.91,5.20],[.24,.75,.75],'steel','action','hubcap',('x',45))
    # Front straps are structural; screws and strap grooves are UV.
    for z in (-.52,4.15):
        c('front_strap_'+str(z),[8,11.66,z],[1.60,2.63,.22],'graphite','foreframe','strap')
    # Raised reflex ladder: two narrow rails, bridge and genuine open center.
    c('sight_base',[8,13.16,2.71],[1.30,.28,2.40],'graphite','sight','rail')
    for side in (-1,1):
        beam('sight_rail_'+str(side),[8+side*.46,13.32,4.02],[8+side*.46,14.90,2.30],.13,.13,'steel','sight','metal')
        c('sight_hinge_'+str(side),[8+side*.54,13.27,4.00],[.20,.40,.40],'steel','sight','hubcap')
    c('sight_top_bridge',[8,14.90,2.30],[1.05,.14,.20],'silver','sight','metal')
    for side in (-1,1):
        c('front_sight_ear_'+str(side),[8+side*.43,13.19,-.68],[.18,.73,.22],'steel','sight','metal')
    c('front_sight_bridge',[8,13.54,-.68],[1.02,.12,.23],'silver','sight','metal')
    c('charging_handle_stem',[8,12.98,7.95],[.16,.63,.16],'silver','action')
    c('charging_handle_knob',[8,13.45,7.95],[.29,.48,.29],'rubber','action','rubber')
    # A real convex transverse disc, with side bosses and an aft rectangular stock frame.
    disc('rear_disc',12.08,11.70,1.10,1.15,'silver')
    for side in (-1,1):
        c('disc_hub_'+str(side),[8+side*.65,12.08,11.70],[.21,.46,.46],'graphite','hub','hubcap',('x',45))
    c('disc_stanchion',[8,10.91,11.70],[1.15,.55,.47],'steel','stock','collar')
    c('stock_top_tube',[8,10.70,13.58],[.52,.49,7.23],'bronze','stock','tube')
    c('stock_rear_spine',[8,11.57,15.28],[.88,.42,4.45],'graphite','stock','action')
    c('stock_coil',[8,11.88,15.10],[.68,.29,3.44],'copper','stock','coil')
    for z in (13.7,15.3,16.65):
        c('coil_bridge_'+str(z),[8,11.71,z],[1.01,.48,.13],'steel','stock','collar')
    beam('stock_diagonal_tube',[8,7.05,8.79],[8,9.68,15.40],.68,.62,'silver','stock','tube')
    beam('stock_lower_elbow',[8,6.35,9.25],[8,6.70,10.56],.62,.62,'rubber','stock','rubber')
    beam('stock_elbow_rise',[8,6.70,10.56],[8,8.0,11.06],.62,.62,'rubber','stock','rubber')
    beam('stock_diagonal_sleeve',[8,7.79,10.20],[8,9.35,14.52],.77,.72,'rubber','stock','rubber')
    beam('stock_rear_elbow',[8,9.45,15.0],[8,10.68,16.25],.64,.63,'rubber','stock','rubber')
    for i,(y,z) in enumerate(((8.45,12.0),(9.15,13.95))):
        c('stock_band_'+str(i),[8,y,z],[.85,.17,.84],'silver','stock','collar',('x',-20))
    c('butt_main',[8,10.25,17.60],[1.21,4.34,.54],'graphite','stock','stock')
    c('butt_pad',[8,10.25,17.89],[1.20,4.30,.18302761906504],'rubber','stock','rubber')
    c('butt_inner_brace',[8,9.60,16.92],[.87,.38,.92],'steel','stock','collar',('x',-33))
    # Long existing grip/magazine neighborhood. Frame bars leave real triangular windows.
    c('grip_front_rail',[8,8.23,7.79],[.70,4.94,.20],'graphite','grip','grip')
    c('grip_rear_rail',[8,8.23,8.75],[.70,4.94,.18],'graphite','grip','grip')
    c('grip_top_web',[8,10.23,8.26],[.73,.92,1.15],'graphite','grip','grip')
    c('grip_heel_web',[8,6.07,8.26],[.76,.74,1.18],'graphite','grip','grip')
    beam('grip_diagonal_upper',[8,8.87,7.88],[8,9.55,8.65],.64,.17,'steel','grip','grip')
    beam('grip_diagonal_lower',[8,7.78,8.66],[8,8.59,7.88],.64,.17,'graphite','grip','grip')
    # Lower stock/hose swivel actually joins the grip well; convex and filled.
    disc('lower_swivel',6.22,9.24,.39,1.00,'steel')
    for side in (-1,1):
        c('lower_swivel_cap_'+str(side),[8+side*.55,6.22,9.24],[.14,.25,.25],'graphite','hub','hubcap',('x',45))
    c('magazine_well',[8,6.10,8.25],[1.03,.86,1.32],'bronze','grip','magwell')
    c('magazine',[8,4.57733137367,8.26],[.69,2.38533725266,1.12],'graphite','grip','magazine')
    # Trigger-guard loop under action, in front of the grip.
    c('guard_front',[8,9.95,6.67],[.39,1.14,.16],'steel','guard')
    beam('guard_floor',[8,9.42,6.67],[8,9.42,7.69],.39,.16,'steel','guard')
    c('trigger',[8,10.02,7.13],[.18,.52,.14],'graphite','guard',turn=('x',-16))
    files=[BASE,'art/blockbench/weapons/w30/ikelos_smg_v1_0_1.bbmodel','art/weapons/w31/references.json',
           'art/weapons/w30/catalog.json',HELPER,'scripts/generate_surface_w123_ikelos_sg_v1_0_1.py',
           ASSET+'textures/item/weapon/w30/ikelos_smg_v1_0_1.png',
           ASSET+'items/weapon/ikelos_smg_v1_0_1.json',ASSET+'items/weapon_aim_w70/ikelos_smg_v1_0_1.json']
    files+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/(ASSET+'models/weapon/submachine_gun')).glob('ikelos_smg_v1_0_1_*.json'))
    files+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/(ASSET+'models/weapon_aim_w70')).glob('ikelos_smg_v1_0_1_*.json'))
    rawfiles=[PHOTO,RAW/'IKELOS_SMG_v1_0_1.fbx',RAW/'IKELOS_SMG_v1.0.1.blend']+sorted((RAW/'Textures').glob('*_albedo.png'))
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='ikelos_smg_v1_0_1')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    cat=next(r for r in json.loads((ROOT/'art/weapons/w30/catalog.json').read_bytes()) if r['id']=='ikelos_smg_v1_0_1')
    return dict(id='ikelos_smg_v1_0_1',revision='W142',source=meta,reference=ref,catalogue=cat,parts=parts,palette=PALETTE,
        method='hand-authored filled semantic solids and detailed independent opaque face UV',
        identity=['four paired copper-magenta capacitor cells','mauve carbon nose with white Warmind geometric mark',
                  'skeletal bronze foreframe and diagonal ribbed grip','raised open ladder sight','transverse silver disc and tubular triangular stock'],
        coordinate_policy=dict(basis='native X=FBX Y, Y=FBX Z, Z=-FBX X; baked identity transforms; muzzle -Z',
            scale=meta['scale'],anchor=meta['anchor'],display='exact canonical dictionary',export='full only; no runtime changes'),
        source_alignment=dict(fbx_version=7500,fbx_triangles=38980,w30_blend_triangles=meta['source_triangles'],bounds_match_tolerance=1e-5,
            topology_note='FBX triangle records include padding; W30 blend count differs; topology equality not claimed.'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['Offline CPU rendering only; native parser/pack/held/ADS/reload/audio/10-20 displays pending master.',
            'Photo-authored static paint approximates iridescence and carbon; no recovered dynamic PBR.',
            'Disc is a filled convex octagon and hose bends are broad solid segments.',
            'Far-side cells and frame are corroborated by rip; unseen reverse emblem not invented.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];e=spec['geometry'];name=e['name']
    u,v,q=world_points(e,face,w,h);x=q[:,:,0];y=q[:,:,1];z=q[:,:,2]
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.97+.045*np.exp(-((v-.28)/.6)**2))[:,:,None]
    side=face in ('east','west')
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    if motif not in ('hub','tube'):
        rgb[edge<.65]*=.72;rgb[(edge>=.65)&(edge<1.45)]*=1.11
    def screw(zc,yc,r=.052):
        rr=np.hypot(z-zc,y-yc)
        rgb[rr<r]=PALETTE['graphite'];rgb[(rr>r*.7)&(rr<r)]=PALETTE['silver']
        rgb[(rr<r*.5)&(abs(z-zc)<.01)]=PALETTE['steel']
    if motif in ('carbon','emblem'):
        twill=((np.floor((z+y)*8)+np.floor((z-y)*8))%4)<2
        rgb*=np.where(twill,1.023,.977)[:,:,None]
        if side:
            line=(abs(y-12.04)<.018)&(z>-.3);rgb[line]*=.49
            line=(abs(y-12.09)<.014)&(z>-.3);rgb[line]*=1.14
            # Four diagonal channel runs are continuous across the receiver's broad face.
            for zz in (.52,1.58,2.64,3.70):
                cable=zz-.35+(12.69-y)*.64
                mask=(y>12.04)&(y<12.70)
                rgb[mask&(abs(z-cable)<.025)]=PALETTE['ochre']
                rgb[mask&(abs(z-cable+.055)<.024)]=PALETTE['silver']
            # Photo's geometric diamond/wing Warmind motif, on photographed side only.
            if face=='west':
                zz=(z+.83)/.30;yy=(y-12.36)/.27;diam=abs(zz)+abs(yy)
                emblem=((diam<1)&(diam>.58))|((yy>.71)&(yy<.94)&(abs(zz)<1.38))
                rgb[emblem]=PALETTE['edge']
    if motif=='cell':
        t=np.clip((y-11.10)/.80,0,1)[:,:,None]
        # Static color sweep based on actual photo; no emissive or dynamic iridescence claim.
        low=np.array([181,125,83]);mid=np.array([199,142,122]);high=np.array([157,62,119])
        rgb[:]=np.where(t<.57,low+(mid-low)*t/.57,mid+(high-mid)*(t-.57)/.43)
        rgb*=np.where(edge<1.1,.72,1)[:,:,None]
        if side:
            diamond=abs((u-.50)/.16)+abs((v-.66)/.18)
            rgb[(diamond>.74)&(diamond<1.02)]=PALETTE['steel']
    if motif=='socket':
        rgb[(u>.18)&(u<.82)&(v>.24)&(v<.77)]=PALETTE['graphite']
        rgb[(abs(u-.5)<.09)&(v>.22)&(v<.8)]=PALETTE['silver']
    if motif in ('action','stock','grip','magwell','magazine') and side:
        # Source-supported receiver scribes, slot and panel fasteners.
        for yy in (10.66,11.76,12.30):
            rgb[(abs(y-yy)<.015)&(z>4.8)&(z<9.7)]*=.49
        for zz,yy in ((5.5,12.04),(7.75,12.04),(9.35,12.04),(8.26,9.82),(8.27,6.11),(17.6,11.88)):
            screw(zz,yy)
        if name=='upper_action':
            slot=(z>5.55)&(z<8.83)&(y>12.16)&(y<12.40)
            rgb[slot]=PALETTE['recess'];rgb[slot&(y<12.20)]=PALETTE['steel']
        if motif=='magazine':
            rgb[(abs(z-7.88)<.035)|(abs(z-8.65)<.03)]*=1.32
            dimple=(np.mod(y*8.5+z*3,1)<.20)&(np.mod(z*10,1)<.22)&(y<5.4)&(y>3.8)
            rgb[dimple]*=.5
        if motif=='magwell':
            notch=(abs(z-8.25)<.23)&(y<6.18);rgb[notch]=PALETTE['graphite']
            rgb[notch&(abs(z-8.25)>.17)]=PALETTE['silver']
    if motif=='ribs':
        # Along diagonal foregrip centerline, seam wraps continuously around faces.
        t=(z-1.85)*.847-(y-9.92)*.532
        phase=np.mod(t*4.1,1)
        rgb[phase<.19]*=.42;rgb[(phase>.19)&(phase<.30)]=PALETTE['silver']
        rgb[(phase>.30)&(phase<.39)]*=1.13
    if motif in ('rubber','bellows','coil'):
        phase=np.mod((z*8 if motif!='rubber' else (z*.91+y*.36)*13),1)
        rgb[phase<.18]*=.53;rgb[(phase>.18)&(phase<.33)]*=1.23
        if motif=='coil':rgb[(phase>.34)&(phase<.46)]=[186,118,133]
    if motif in ('frame','strap','collar') and side:
        rgb[(u<.10)|(u>.90)]*=1.17
        if motif=='strap':
            for yy in (10.48,12.88):screw((e['from'][2]+e['to'][2])/2,yy,.07)
        if motif=='frame':
            # Long quiet bronze fields; no invented labels or random patina.
            rgb[(v>.32)&(v<.37)]*=.78
    if motif=='tube':
        rgb*=(.82+.24*np.sin(np.pi*u))[:,:,None]
        if side and name=='stock_top_tube':
            label=(z>9.2)&(z<10.2)&(y>10.69)&(y<10.85)
            rgb[label]=[187,178,135]
            rgb[label&(np.mod(z*29,1)<.15)&(y<10.79)]=PALETTE['steel']
    if motif=='hub' and side:
        yc,zc,scale=(6.22,9.24,.39/1.10) if name.startswith('lower_swivel') else (12.08,11.70,1)
        rr=np.hypot(y-yc,z-zc)/scale
        rgb*=(.94+.05*np.cos(rr*2))[:,:,None]
        for r in (.33,.83,1.02):rgb[abs(rr-r)<.018]*=.56
        rgb[rr<.24]=PALETTE['graphite']
    if motif=='hubcap' and side:
        rgb[(abs(u-.5)<.22)&(abs(v-.5)<.22)]=PALETTE['recess']
    if motif=='rail':
        rgb[(face=='up')&(np.mod(z*8,1)<.13)]*=.54
    if motif=='piston':
        rgb[(abs(z-6.3)<.04)|(abs(z-8.4)<.035)]*=.53
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=30 if spec['motif'] in ('carbon','action','ribs','cell','stock','grip','magazine') else 20
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
    model=dict(credit='IKELOS_SMG_v1.0.1 W142 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/ikelos_smg_v1_0_1','particle':'destiny:item/weapon/w123/ikelos_smg_v1_0_1'},
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
        name='IKELOS_SMG_v1.0.1 W142 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='ikelos_smg_v1_0_1.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w142=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


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
    w,h=900,470;sheet=Image.new('RGB',(2700,2470),'#151d27');draw=ImageDraw.Draw(sheet)
    def label(x,y,text,size=21):draw.text((x,y),text,fill='#e4ebed',font_size=size)
    label(20,12,'IKELOS_SMG_v1.0.1 / W142 / SEMANTIC FILLED SOLIDS + FACE UV / OFFLINE CPU ART',28)
    photo=Image.open(PHOTO).convert('RGB').crop((825,115,1855,920));photo.thumbnail((680,440));sheet.paste(photo,(20,60))
    label(20,505,'ACTUAL W31 DEFAULT PHOTO / Bungie + light.gg reference',17)
    for i,fn in enumerate(('E4D0EB80_albedo.png','59AFEB80_albedo.png')):
        im=Image.open(RAW/'Textures'/fn).convert('RGB');im.thumbnail((310,390));sheet.paste(im,(640+i*330,70))
        label(640+i*330,470,'RAW NEUTRAL '+('BODY' if i==0 else 'FRAME'),17)
    preview=atlas.copy();preview.thumbnail((370,370));sheet.paste(preview.convert('RGB'),(1330,75));label(1330,470,'AUTHORED 1024 ATLAS',17)
    for i,line in enumerate([f'{len(model["elements"])} opaque filled cuboids / full assembly',
        'Four copper-magenta cells per side / bronze skeleton',
        'Deep bore / open ladder sight / real stock + guard air',
        'Solid transverse receiver + filled octagonal rear disc',
        'Independent face UV / opaque extruded gutters',
        'Exact canonical display / absolute hand coordinates',
        'CPU evidence only; native QA remains with master']):label(1760,85+i*53,line,21)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/ikelos_smg_v1_0_1.png'))
    label(20,550,'ACTUAL FBX / 38,980 RECORDS / NEUTRAL ALBEDO')
    label(w+20,550,f'OLD CANONICAL / {len(old["elements"])} CUBOIDS')
    label(2*w+20,550,f'W142 / {len(model["elements"])} AUTHORED SOLIDS')
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    views=[('SIDE / -X',[-1,0,0]),('FRONT OBLIQUE',[-1,.42,-.65]),('OPPOSITE REAR OBLIQUE',[1,.36,.65])]
    for row,(name,cam) in enumerate(views):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,585+row*h));label(col*w+15,596+row*h,name,18)
    details=[(('muzzle',),[.18,.10,-1]),(('sight',),[-.15,.12,-1]),(('foreframe','foregrip'),[-1,.2,-.3]),
             (('stock','hub'),[-1,.35,.45]),(('grip','guard'),[-1,.1,-.3])]
    for col,(groups,cam) in enumerate(details):
        names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names]);p=np.concatenate([vertices(e) for e in sub['elements']])
        im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](p,cam,540,380),(540,380))
        sheet.paste(im,(col*540,2040));label(col*540+14,2050,' + '.join(groups).upper(),17)
    label(20,2430,'Matched source-frame camera + scale per row. Parser/pack, held/ADS/reload/audio and 10-20 native display QA pending master.',21)
    return png(sheet)


def review_text(d,counts):
    return f"""# IKELOS_SMG_v1.0.1 W142 art review

Actual default photo: `{PHOTO}`; hash `{d['reference']['sha256']}`; viewed before authoring. Local W30 FBX, blend metadata and neutral albedos establish proportions, absolute hand frame and unseen structural details. No raw Python or shader scripts executed. No ornament/version mixing. The photo motivates mauve carbon, copper-to-magenta cell paint, bronze frame, silver hardware and black hoses. Authoring follows the Ace87/Izanagi79 semantic-solids and face-UV study; their geometry or motifs are not copied.

Assembly: {sum(counts.values())} filled opaque cuboids, {sum(counts.values())*6} explicit faces, zero triangle adapters, zero alpha silhouette shells; hard cap 1000, not a target. Group counts: {json.dumps(counts,sort_keys=True)}. The lower element count comes from continuous receiver/action volumes and structural beams rather than source-island, voxel or fragment conversion. Each cell is a solid transverse housing. The octagonal disc uses six filled intersecting cuboids; hoses use broad filled spans. Foreframe, magazine/grip and stock remain distinct 3D structures. Broad receiver panels carry subtle twill, aligned channel runs, the photographed geometric nose mark, panel scribes and source-supported fasteners. Raised leads, frame struts and stock tubes stay geometric for parallax. Small grip ribs, coil windings, machining rings and dimples use face UV.

Real openings: eight muzzle walls surround an octagonal open bore ending at a recessed opaque stop; ladder sight rails leave an open center; skeletal foreframe, triangular grip windows, trigger guard and large triangular stock opening contain actual air across transverse thickness. No alpha-based body or uniformly extruded silhouette plates. Carbon receiver X thickness 1.39, action 1.18, cells .88 each, diagonal foregrip 1.10. Front and back/edge faces have independent UV, not copied side projections.

1024 atlas, two-pixel opaque edge extrusion, {d['atlas']['face_islands']} independently packed face islands. Quiet ordered materials and source-derived markings replace noisy reprojected blotches. Copper/magenta sweep is a fixed photo interpretation, not original dynamic iridescence/PBR. Reverse-side structural symmetry is supported by the rip; reverse emblem is intentionally absent because the photo does not establish it.

Canonical scale {d['source']['scale']}, anchor {d['source']['anchor']}; native basis [FBX Y, FBX Z, -FBX X], muzzle -Z. The baked FBX has identity transforms; all ten retained objects and source bounds match W30 within 1e-5. 38,980 FBX records include padding; W30 records 31,768 blend triangles. Counts are reported separately; topology equality is not claimed. Both raw FBX and blend hashes match W30 metadata. No downstream aggregate manifest hash is an art input. Candidate retains original muzzle/stock length endpoints and grip/magazine neighborhood; exact original display dictionary is copied without recentering or rescaling.

Candidate full-only resource: `destiny:weapon_surface_w123/ikelos_smg_v1_0_1`; texture `destiny:item/weapon/w123/ikelos_smg_v1_0_1`. No split reload or new gameplay requirement. The first blockout used 109 elements; source-visible hose elbows, the lower swivel, seven silhouette ribs and an octagonal bore brought the final assembly to 133. These additions preserve identity and physical continuity rather than filling a budget. Existing canonical models, item routing, 42 ADS/twohand aim variants, audio, animation and gameplay remain untouched. Semantic groups in inspection.bbmodel are editor selection groups only. Embedded atlas and all editable cuboids/rotations/face UV/display match native JSON.

comparison.png contains the actual default photo, raw neutral albedos, new atlas, actual FBX / old canonical / new geometry at shared source-frame scale in side, front-oblique and opposite-rear-oblique views, plus five aperture/detail views. This is offline CPU rendering, not a Blockbench screenshot or native acceptance. No DCC, client, server, Gradle or dependencies invoked. Native parser/pack loading, first/third-person hand fit, ADS, existing reload/audio and 10-20 simultaneous display observation remain master's checks. Targeted test and final viewed observations are in the worker report.
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
    manifest=dict(id='ikelos_smg_v1_0_1',revision='W142',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=38980,w30_blend_triangles=meta['source_triangles'],source_alignment=d['source_alignment'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        canonical_display_exact=True,full_only=True,generic_reload_ADS_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        default_photo_sha256=d['reference']['sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


OWNED=[
    'scripts/generate_surface_w123_ikelos_smg_v1_0_1.py',
    'scripts/qa/test_surface_w123_ikelos_smg_v1_0_1.py',
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
