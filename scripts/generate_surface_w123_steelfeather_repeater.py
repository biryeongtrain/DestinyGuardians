#!/usr/bin/env python3
"""W134 Steelfeather Repeater: deterministic semantic solid-cuboid art; full export only.
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

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/steelfeather_repeater/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/auto_rifle/steelfeather_repeater.json'
MODEL = ASSET + 'models/weapon_surface_w123/steelfeather_repeater.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/steelfeather_repeater.png'
REPORT = 'docs/qa/2026-10-26/w134/steelfeather_repeater-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/steelfeather_repeater/extracted/Steelfeather Repeater')
PHOTO = Path('/tmp/destiny-weapons-w31/references/steelfeather_repeater.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(silver=[181,183,184], edge=[201,203,202], steel=[104,109,112],
               graphite=[49,52,55], recess=[20,23,26], rubber=[28,30,33],
               gold=[159,139,84], palegold=[188,172,119])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w134:steelfeather_repeater:'+name))


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


def source_meshes():
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/steelfeather_repeater.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Steelfeather Repeater.fbx').read_bytes())==meta['source_files']['Steelfeather Repeater/Steelfeather Repeater.fbx']
    roots=H['parse_fbx'](RAW/'Steelfeather Repeater.fbx')
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
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    return meshes,meta


def make_design(meta):
    parts=[]
    def box(name,lo,hi,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:e['rotation']=dict(origin=[round((a+b)/2,6) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(pos,size)],[round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name,a,b,width,depth,mat,group,motif='plain'):
        dy=b[1]-a[1];dz=b[2]-a[2]
        c(name,[(x+y)/2 for x,y in zip(a,b)],[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',-math.degrees(math.atan2(dy,dz))))
    def tube(name,y,z0,z1,r,t,mat,group):
        for i in range(8):
            a=math.radians(i*45);rr=r-t/2
            c(f'{name}_{i}',[8-rr*math.sin(a),y+rr*math.cos(a),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.006,t,z1-z0],mat,group,'rim',('z',i*45))
    # Filled long silver body. Native frame: muzzle -Z; hand stays near Z8.
    box('upper_receiver',[7.33,10.91,-6.15],[8.67,12.28,1.90],'silver','receiver','upper')
    box('upper_crown',[7.49,12.25,-5.17],[8.51,12.47,1.92],'silver','receiver','crown')
    for side in (-1,1):
        c(f'front_shoulder_{side}',[8+side*.57,12.24,-1.85],[.28,.28,7.31],'silver','receiver','upper',('z',45*side))
    beam('receiver_sweep',[8,11.90,1.62],[8,12.42,4.02],1.33,.83,'silver','receiver','upper')
    box('receiver_action_roof',[7.35,11.65,3.83],[8.65,12.58,8.57],'silver','receiver','upper')
    box('stock_upper_solid',[7.36,11.62,8.53],[8.64,12.61,15.339255253591372],'silver','stock','stock')
    for side in (-1,1):
        c(f'rear_shoulder_{side}',[8+side*.56,12.55,9.62],[.24,.24,11.22],'silver','stock','stock',('z',45*side))
    box('receiver_lower_ledge',[7.29,10.72,-6.05],[8.71,10.96,1.96],'steel','receiver','ledge')
    beam('sweep_lower_ledge',[8,10.87,1.86],[8,11.51,4.34],1.42,.21,'steel','receiver','ledge')
    box('stock_ledge',[7.30,11.35,4.24],[8.70,11.65,15.23],'steel','stock','ledge')
    # Broad lower action, with the dark forward rail read as one assembly.
    box('lower_action',[7.30,9.77,2.20],[8.70,11.67,7.16],'steel','action','action')
    box('rear_action',[7.31,10.27,6.91],[8.69,11.45,11.92],'steel','action','action')
    box('forearm_action',[7.37,9.76,-4.63],[8.63,10.83,2.34],'graphite','forearm','forearm')
    box('forearm_rubber',[7.40,8.99,-3.90],[8.60,9.84,1.89],'rubber','forearm','rubber')
    c('forearm_nose',[8,9.46,-4.03],[1.20,.86,.49],'rubber','forearm','rubber',('x',-15))
    box('forearm_rear_sleeve',[7.21,9.06,1.70],[8.79,10.53,2.36],'silver','forearm','socket')
    # Thin source-backed keeper straps wrap around actual solid forearm.
    for i,z in enumerate((-4.00,1.89)):
        for side in (-1,1):c(f'keeper_{i}_{side}',[8+side*.69,9.89,z],[.19,1.61,.42],'steel','forearm','keeper')
    box('forearm_gold_line',[7.27,9.12,1.58],[8.73,10.29,1.70],'palegold','forearm','plain')
    # The muzzle's segmented side walls leave real lateral ports; six other
    # tangent walls are continuous. No alpha cutouts, no imported mesh islands.
    muzzle_min=meta['model_bounds'][0][2]
    for i in range(8):
        a=math.radians(i*45);rr=.52-.115/2
        spans=[(muzzle_min,-6.22)] if i not in (2,6) else [(muzzle_min,-9.17),(-8.44,-8.12),(-7.34,-6.22)]
        for j,(za,zb) in enumerate(spans):
            c(f'muzzle_wall_{i}_{j}',[8-rr*math.sin(a),11.30+rr*math.cos(a),(za+zb)/2],
              [2*.52*math.tan(math.pi/8)+.006,.115,zb-za],'steel','muzzle','rim',('z',i*45))
            if za==muzzle_min:parts[-1]['geometry']['from'][2]=muzzle_min
    box('bore_depth_stop',[7.70,11.0,-6.23],[8.30,11.60,-6.20],'recess','muzzle','plain')
    # Front collar: broad filled octagonal block; exposed barrel remains hollow.
    box('front_collar',[7.25,10.64,-6.22],[8.75,12.22,-5.58],'silver','receiver','collar')
    # Remove no source hand-frame material globally: bore only exists forward
    # of collar, with depth stop where the original chamber becomes solid.
    # Real gas cylinder and an open bracket under the barrel.
    box('gas_tube',[7.72,9.70,-6.51],[8.28,10.17,-4.17],'steel','gas','gas')
    box('gas_front_block',[7.45,9.32,-6.76],[8.55,10.28,-6.15],'silver','gas','gas_cap')
    for side in (-1,1):
        box(f'gas_bracket_post_{side}',[8+side*.65-.10,9.45,-6.14],[8+side*.65+.10,10.80,-5.92],'steel','gas','keeper')
    box('gas_bracket_floor',[7.27,9.32,-6.14],[8.73,9.52,-5.92],'steel','gas','plain')
    # A short faceted hooked blade, its thick spine curves toward the muzzle.
    beam('blade_root',[8,9.38,-6.49],[8,8.38,-6.40],.24,.39,'steel','blade','blade')
    beam('blade_sweep',[8,8.42,-6.40],[8,7.44,-6.68],.20,.31,'steel','blade','blade')
    beam('blade_tip',[8,7.51,-6.65],[8,6.91,-7.04],.12,.16,'edge','blade','blade')
    # Magazine is one assembled solid; its pressed flutes and fasteners are UV.
    box('magazine_core',[7.48,6.24,2.04],[8.52,9.72,4.63],'graphite','magazine','magazine')
    for side in (-1,1):
        c(f'magazine_side_bevel_{side}',[8+side*.50,7.96,2.14],[.20,3.41,.20],'graphite','magazine','magazine',('y',45*side))
    box('magazine_floor',[7.41445245,6.106844730685009,1.98092499],[8.58560152,6.30,4.67151929],'steel','magazine','magazine_floor')
    box('magwell',[7.23,9.32,1.88],[8.77,9.93,4.87],'steel','magazine','magwell')
    box('magwell_gold_trim',[7.22,9.48,2.02],[8.78,9.61,4.66],'palegold','magazine','plain')
    # Pistol grip and heel retain the actual raw/native contact position.
    beam('pistol_grip',[8,9.59,7.35],[8,7.03,9.04],1.29,1.04,'steel','grip','grip')
    beam('grip_rubber',[8,8.33,8.23],[8,6.99,9.05],1.32,.94,'rubber','grip','grip_rubber')
    beam('grip_backstrap',[8,9.51,7.91],[8,7.14,9.51],1.20,.24,'steel','grip','grip')
    c('grip_heel',[8,6.89,9.03],[1.42,.26,1.07],'steel','grip','heel',('x',32))
    # Trigger guard surrounds open space, the trigger is a separate solid.
    beam('guard_front',[8,9.78,5.50],[8,8.75,5.60],.35,.21,'silver','guard')
    beam('guard_floor',[8,8.75,5.60],[8,8.53,6.48],.35,.22,'silver','guard')
    beam('guard_rear',[8,8.53,6.48],[8,9.10,7.01],.35,.22,'silver','guard')
    beam('trigger',[8,9.79,6.49],[8,9.05,6.22],.19,.17,'graphite','guard')
    # Rear stock is open below the comb. Butt and low upper brace frame air.
    box('stock_lower_cheek',[7.37,10.17,10.67],[8.63,11.47,14.93],'steel','stock','stock_lower')
    beam('stock_inner_arch',[8,10.66,9.76],[8,10.37,11.12],1.21,.57,'steel','stock','stock_lower')
    beam('stock_butt',[8,8.83,14.91],[8,11.65,15.03],1.36,.50,'silver','stock','butt')
    beam('stock_butt_rubber',[8,8.87,15.22],[8,11.62,15.22],1.11,.21,'rubber','stock','butt_rubber')
    beam('stock_butt_inset',[8,9.04,14.89],[8,10.69,14.65],.72,.22,'graphite','stock','plain')
    # Open U sight in the original top position; rail slots are real gaps.
    box('sight_base',[7.63,12.53,4.58],[8.37,12.74,5.70],'steel','sight','sight')
    for side in (-1,1):
        box(f'sight_ear_{side}',[8+side*.285-.075,12.71,4.95],[8+side*.285+.075,13.427511201832907,5.19],'steel','sight','sight')
    box('sight_cradle',[7.70,12.70,4.91],[8.30,12.85,5.24],'steel','sight','sight')
    box('rear_top_rail',[7.72,12.60,5.68],[8.28,12.69,9.21],'graphite','rail','rail')
    for i,z in enumerate(np.linspace(5.93,8.95,9)):
        c(f'rear_rail_tooth_{i}',[8,12.77,float(z)],[.77,.18,.17],'steel','rail','rail')
    for i,z in enumerate(np.linspace(-4.93,-2.94,6)):
        c(f'front_cooling_tooth_{i}',[8,12.51,float(z)],[.65,.17,.19],'silver','rail','rail')
    # Photo's arcing top saddle: two substantial angled blocks, marking in UV.
    c('sight_front_saddle',[8,12.53,3.61],[1.14,.42,2.02],'silver','receiver','saddle',('x',-10))
    # Charging lever on native -X, source +X carried mirrored controls differ.
    box('charging_slide',[6.90,10.80,6.36],[7.31,11.07,7.39],'graphite','controls','control')
    c('charging_handle',[7.11,10.67,6.61],[.42,.29,.61],'steel','controls','control',('y',-18))
    box('ejection_port_rim',[8.69,10.25,2.44],[8.94,10.98,3.83],'silver','controls','port')
    box('side_pivot',[9.05,10.32,6.97],[9.28,10.72,7.50],'graphite','controls','control')
    inputs=[BASE,'art/blockbench/weapons/w30/steelfeather_repeater.bbmodel','art/weapons/w31/references.json',HELPER,
            ASSET+'textures/item/weapon/w30/steelfeather_repeater.png']
    raw_inputs=[RAW/'Steelfeather Repeater.fbx',RAW/'Steelfeather_Repeater_Diffuse.dds',RAW/'Steelfeather_Repeater_Sight_Diffuse.dds',PHOTO]
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='steelfeather_repeater')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return dict(id='steelfeather_repeater',revision='W134',method='authored filled semantic cuboids and proportional independent face UV',
        source=meta,reference=ref,palette=PALETTE,parts=parts,
        identity=['sweeping silver upper body and continuous dark action','dark box magazine / restrained gold trim',
                  'open stock, U sight and guard','ported bored barrel / hooked front blade / ribbed dark forearm'],
        coordinate_policy=dict(basis='native X=raw X, Y=raw Z, Z=raw Y; muzzle -Z',scale=meta['scale'],anchor=meta['anchor'],
             grip='raw source grip near Z7..9 and Y7..10, no global transform',display='exact canonical dictionary',export='full only; existing generic reload / ADS / audio / timing unchanged'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Offline CPU art only; native target parser, held/ADS/reload and 10-20 displays pending master.',
                     'Source neutral diffuse is not default dye; photo-backed static matte paint is not PBR.',
                     'Curved blade and flowing upper body simplified with broad solids; no source-poly equivalence.',
                     'Opposite-side photograph unavailable; no invented reverse-side insignia.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];u,v,q=world_points(spec['geometry'],face,w,h)
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.97+.045*np.exp(-((v-.30)/.45)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    rgb[edge<.75]*=.72;rgb[(edge>=.75)&(edge<1.7)]*=1.07
    side=face in ('east','west');z=q[:,:,2];y=q[:,:,1]
    def line(yline,mask,width=.018):
        nonlocal rgb
        rgb[mask&(abs(y-yline)<width)]*=.52
        rgb[mask&(abs(y-yline-.035)<.014)]*=1.12
    def screw(zc,yc,r=.085):
        nonlocal rgb
        rr=np.hypot(z-zc,y-yc)
        rgb[rr<r]=PALETTE['graphite'];rgb[(rr>r*.73)&(rr<r)]=PALETTE['edge']
        rgb[(rr<r*.57)&(abs(z-zc)<.013)]=PALETTE['steel']
    if side and motif in ('upper','stock','saddle','collar'):
        # Flowing lower panel scribe and a long quiet silver plane.
        curve=11.04+.59/(1+np.exp(-(z-2.55)*1.7))
        line(curve,np.ones_like(u,dtype=bool),.018)
        if motif in ('upper','collar'):
            line(12.28,(z>-.8)&(z<2.5),.012)
            for zc,yc in ((-5.75,11.77),(.85,11.26),(4.08,11.84),(7.35,12.02)):
                screw(zc,yc,.068)
            # Shallow crest at the front collar, drawn as a clean contour.
            r=np.hypot((z+5.64)*.9,y-11.90)
            rgb[(r>.23)&(r<.25)&(z<-5.1)]=PALETTE['graphite']
        if motif=='stock':
            for zc in (10.73,12.42):screw(zc,12.22,.065)
        if motif=='saddle':
            line(12.42,np.ones_like(u,dtype=bool),.016)
            screw(4.19,12.39,.060)
    if side and motif in ('action','forearm','stock_lower'):
        # Shallow panel paths and dark recesses have authored face UV.
        if motif=='action':
            boundary=10.25+.15*np.sin((z-2)*1.2)
            line(boundary,(z>2.6)&(z<11.5),.022)
            slot=(z>7.0)&(z<8.13)&(y>10.78)&(y<10.93);rgb[slot]=PALETTE['recess']
            for zc,yc in ((3.20,10.10),(4.15,10.72),(5.73,10.34),(7.73,10.65),(10.54,10.75)):
                screw(zc,yc,.09)
        if motif=='forearm':
            line(10.02,(z>-3.7)&(z<1.5),.016)
            # Two oval recessed caps observed on the photo's forward action.
            for zc in (-3.38,-2.25):
                rr=np.hypot((z-zc)*.75,y-10.38)
                rgb[rr<.16]=PALETTE['steel'];rgb[(rr>.105)&(rr<.14)]=PALETTE['recess']
                rgb[rr<.065]=PALETTE['graphite']
        if motif=='stock_lower':
            line(10.41,(z>10.3)&(z<14.5),.020)
            for zc in (12.10,14.32):screw(zc,10.71,.075)
    if motif in ('rubber','grip_rubber','butt_rubber'):
        # Directional ribbing, no grain/noise or separately bolted rib cubes.
        a=z if motif=='rubber' else y
        phase=np.mod(a*6,1)
        rgb[phase<.13]*=.66;rgb[(phase>.13)&(phase<.20)]*=1.13
        if side:rgb[(u<.07)|(u>.93)]*=.83
    if side and motif=='grip':
        line(8.95,(z>7.4)&(z<8.5),.018)
        screw(8.98,7.16,.075)
    if side and motif=='magazine':
        for zc in (2.46,3.37,4.22):
            rgb[(abs(z-zc)<.026)&(y>6.40)&(y<9.35)]*=.58
            rgb[(abs(z-zc-.045)<.015)&(y>6.40)&(y<9.35)]*=1.15
        # Source rectangular inspection indentation at the upper front.
        r=(z>2.19)&(z<2.57)&(y>8.72)&(y<9.28)
        rgb[r]=PALETTE['recess'];rgb[r&(y<8.80)]=PALETTE['steel']
        for zc,yc in ((2.48,7.99),(2.49,6.94),(4.12,8.32),(4.17,7.22)):screw(zc,yc,.065)
    if motif=='blade' and side:
        rgb[u<.25]*=1.16;rgb[(u>.25)&(u<.28)]*=.7
    if side and motif in ('keeper','socket','collar','port','gas_cap'):
        screw(float((spec['geometry']['from'][2]+spec['geometry']['to'][2])/2),
              float((spec['geometry']['from'][1]+spec['geometry']['to'][1])/2),min(.11,(spec['geometry']['to'][1]-spec['geometry']['from'][1])*.16))
        if motif=='port':
            a=(u>.18)&(u<.80)&(v>.27)&(v<.71);rgb[a]=PALETTE['recess']
            rgb[a&(v>.59)]=PALETTE['steel']
    im=Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))
    if motif=='saddle' and face=='west':
        # Small gold XXV is visible in supplied default photo; other side stays plain.
        dr=ImageDraw.Draw(im);fs=max(8,min(15,h//2));text='XXV';bb=dr.textbbox((0,0),text,font_size=fs)
        dr.text(((w-(bb[2]-bb[0]))/2,max(1,h*.20)),text,fill=tuple(PALETTE['gold'])+(255,),font_size=fs)
    return im

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=32 if spec['motif'] in ('upper','action','saddle','stock','grip','magazine') else 22
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
    model=dict(credit='Steelfeather Repeater W134 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/steelfeather_repeater','particle':'destiny:item/weapon/w123/steelfeather_repeater'},
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
        name='Steelfeather Repeater W134 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='steelfeather_repeater.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w134=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    result=[];textures={}
    for m in meshes:
        mat=m['material']
        if mat not in textures:
            name='Steelfeather_Repeater_Sight_Diffuse.dds' if mat=='Sight' else 'Steelfeather_Repeater_Diffuse.dds'
            textures[mat]=np.asarray(Image.open(RAW/name).convert('RGBA'))
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((t,uv,textures[mat],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=900,380;sheet=Image.new('RGB',(2700,2070),'#151d27');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'STEELFEATHER REPEATER / W134 / FILLED SEMANTIC SOLIDS + AUTHORED FACE UV / CPU ART',28)
    photo=Image.open(PHOTO).convert('RGB').crop((700,235,1910,835));photo.thumbnail((970,355));sheet.paste(photo,(15,65))
    label(20,418,'ACTUAL DEFAULT PHOTO / Bungie 1251729046 / silver + dark + restrained gold',17)
    for i,fn in enumerate(('Steelfeather_Repeater_Diffuse.dds','Steelfeather_Repeater_Sight_Diffuse.dds')):
        im=Image.open(RAW/fn).convert('RGB');im.thumbnail((285,310));sheet.paste(im,(1000+i*305,67));label(1000+i*305,395,'RAW NEUTRAL '+('BODY' if i==0 else 'SIGHT'),17)
    for i,line in enumerate([f'{len(model["elements"])} opaque filled cuboids / full only',
          'Silver broad upper / dark lower + magazine',
          'Authored seams / XXV / flutes / fasteners',
          'True bore + side ports / U sight / guard / stock air',
          'Original axis / anchor / scale / canonical display',
          'CPU inspection only; native QA pending master']):label(1640,80+i*49,line,23)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/steelfeather_repeater.png'))
    label(20,455,f'ACTUAL FBX / {d["source"]["source_triangles"]:,} triangles / NEUTRAL DIFFUSE')
    label(w+20,455,f'CANONICAL / {len(old["elements"])} cuboids / NOT RAW FBX')
    label(2*w+20,455,f'W134 / {len(model["elements"])} authored solids / CPU ART')
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE / DEFAULT PHOTO SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.42,-.65]),('OPPOSITE REAR THREE-QUARTER',[1,.36,.65])]):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,490+row*h));label(col*w+15,498+row*h,name,17)
    for col,(group,cam) in enumerate([('muzzle',[.18,.13,-1]),('sight',[-.1,.1,-1]),('guard',[-1,.10,-.12]),('stock',[-1,.16,.3]),('forearm',[-1,.35,-.6])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names]);points=np.concatenate([vertices(e) for e in sub['elements']])
        im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](points,cam,540,335),(540,335))
        sheet.paste(im,(col*540,1660));label(col*540+14,1668,group.upper()+' / SOLID DETAIL',17)
    label(20,2025,'Matched full-model camera + scale per row. Native parser, first/third person, ADS/reload, audio and 10-20 displays pending master.',21)
    return png(sheet)


def review_text(d,counts):
    return f'''# Steelfeather Repeater W134 offline art review

Actual supplied default photo: `{PHOTO}` (Bungie item 1251729046). SHA-256 `{d['reference']['sha256']}`. It was opened with the image tool before authoring. Silver swept upper body, dark lower frame/forearm/grip/magazine, restrained gold trim and small XXV, short hooked blade, ported barrel, open U sight and open stock are the observed identity. The neutral raw body/sight diffuse maps appear separately in the comparison; they are not claimed to be finished default dye. Materials are authored photo-backed static matte colors, not recovered PBR or shader channels.

**{sum(counts.values())} emitted opaque filled cuboids, {sum(counts.values())*6} explicit face UVs, zero triangle-adapter elements, zero alpha body shells; full assembled count {sum(counts.values())}/1000.** Groups: {json.dumps(counts,sort_keys=True)}. The design began as a roughly 100-element semantic plan. Long continuous receiver, action, forearm and stock blocks have meaningful volume in all axes. Geometry is authored from semantic proportions, not a transfer of source mesh islands/voxels/UV data. The blade curve and organic upper sweep are deliberately simplified. Shallow panel scribes, observed large screws, magazine pressings, grip/forearm ribs and the small gold marking are authored face paint.

Geometry has a 3.43-unit-deep muzzle opening terminating at a chamber stop, lateral barrel ports, an open U sight, a surrounded trigger aperture and empty air below the rear stock comb. Broad forearm and grip are filled solids. Every cube face has its own proportional UV rectangle on a 1024-square atlas, with opaque 2-pixel extruded gutters. Atlas islands {d['atlas']['face_islands']}, used height {d['atlas']['used_height']}. Inspection BBModel embeds exactly the final atlas and editable cubes/rotations/face UVs with semantic editor groups. These groups do not create runtime reload splits.

The actual original FBX SHA matches the W30 record. Retained objects are exactly {d['source']['source_objects']}; excluded reticle objects remain excluded. Parsing their FBX model links, local rotation approximately [-90,0,0] and scale [100,100,100], then using the established W30 native basis [raw X, raw Z, raw Y] × {d['source']['scale']} + {d['source']['anchor']}, reproduces the exact retained 19,011 triangles and W30 union bounds. This is source provenance and coordinate evidence, not shape equivalence of the new design. Native muzzle -Z, original magazine and grip locations and original absolute length endpoints remain; canonical display dictionary is copied exactly. No global scale/recenter or hand offset adjustment is used.

The full-only candidate is `destiny:weapon_surface_w123/steelfeather_repeater` with `destiny:item/weapon/w123/steelfeather_repeater`. Existing weapon registry, canonical auto-rifle model, ADS, generic reload, timing, combat, item and audio graph are untouched. No split resources are emitted.

comparison.png contains the actual photo, neutral source diffuse, actual 19,011-triangle FBX, read-only 239-cuboid canonical (explicitly not raw FBX), and new solids in matched side/front-quarter/opposite rear-quarter views. It also includes muzzle, sight, guard, stock and forearm details. Final image-tool observations are recorded in the worker report. CPU art rendering does not establish native parser, texture load, held appearance or performance acceptance.

Targeted unittest checks basic emitted schema/count, broad depth, original frame/display, real holes, alpha/UV/gutters, input/reference/output hashes, editable BB parity and deterministic regeneration. It is not an all-angle aesthetic gate. Native 26.3 parser/pack load, representative first/third-person grip, muzzle, ADS, generic full reload/audio/timing and 10-20 displays remain pending master. No GUI, DCC, native client, Gradle, server, lease, CU or Vision was used.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='steelfeather_repeater',revision='W134',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        canonical_display_exact=True,full_only=True,generic_reload_ADS_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        default_photo_sha256=d['reference']['sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


OWNED=[
    'scripts/generate_surface_w123_steelfeather_repeater.py',
    'scripts/qa/test_surface_w123_steelfeather_repeater.py',
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
