#!/usr/bin/env python3
"""W136 Edge Transit: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/edge_transit/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/heavy_grenade_launcher/edge_transit.json'
MODEL = ASSET + 'models/weapon_surface_w123/edge_transit.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/edge_transit.png'
REPORT = 'docs/qa/2026-10-26/w136/edge_transit-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/edge_transit/extracted/Edge Transit')
PHOTO = Path('/tmp/destiny-weapons-w31/references/edge_transit.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(seafoam=[140,172,165], pale=[174,199,189], green=[79,105,91],
               darkgreen=[53,69,57], steel=[73,78,75], edge=[120,134,126],
               rubber=[30,34,32], recess=[15,23,21], violet=[127,111,166])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w136:edge_transit:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/edge_transit.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Edge Transit.fbx').read_bytes())==meta['source_files']['Edge Transit/Edge Transit.fbx']
    roots=H['parse_fbx'](RAW/'Edge Transit.fbx')
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
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==30450
    return meshes,meta



def make_design(meta):
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
        c(name,[(x+y)/2 for x,y in zip(a,b)],[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',angle))
    def tube(name,x,y,z0,z1,r,t,mat,group,motif='rim',facets=range(8)):
        for i in facets:
            a=i*45;q=math.radians(a);rr=r-t/2
            c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.012,t,z1-z0],mat,group,motif,('z',a))
    def filled_octagon(name,x,y,z0,z1,r,mat,group,motif):
        # Union of four crossing solid prisms is a FILLED regular octagon.
        # All end faces use world-space paint so the overlapping caps agree.
        for i in range(4):
            c(f'{name}_{i}',[x,y,(z0+z1)/2],[2*r,2*r*math.tan(math.pi/8),z1-z0],mat,group,motif,('z',i*45))
    # Source bore axis is [8.001,11.580], above and left of the large drum axis.
    tube('muzzle',8,11.58,meta['model_bounds'][0][2],-7.41,.79,.20,'seafoam','muzzle','bore')
    tube('barrel_shroud',8,11.58,-7.43,-.23,1.105,.47,'darkgreen','barrel','shroud')
    tube('barrel_breech',8,11.58,-.48,.13,1.135,.49,'steel','barrel','collar')
    c('bore_depth_stop',[8,11.58,.18],[1.17,1.17,.12],'recess','barrel')
    # Two axial shoulder rails shape the top ridge without decorating each seam.
    c('barrel_top_ridge',[8,12.63,-3.81],[.76,.25,5.61],'steel','barrel','ridge')
    for side in (-1,1):
        c(f'barrel_lower_bevel_{side}',[8+side*.63,10.82,-3.2],[.27,.29,5.4],'darkgreen','barrel','shroud',('z',side*45))
    # Large offset drum is a broad mass; no mesh-island or alpha-card conversion.
    dx,dy=8.53,10.22
    filled_octagon('drum_core',dx,dy,.18,6.04,2.48,'darkgreen','drum','drum_end')
    # Deep longitudinal green bays sit on a continuous solid octagonal core.
    for i in range(8):
        a=i*45;q=math.radians(a);r=2.47
        c(f'drum_bay_{i}',[dx-r*math.sin(q),dy+r*math.cos(q),2.91],
          [1.84,.35,5.12],'green','drum','drum_bay',('z',a))
    # Structural front and rear annular rim; the core fills the central end caps.
    tube('drum_front_rim',dx,dy,.05,.39,2.53,.18,'steel','drum','drum_rim')
    tube('drum_rear_rim',dx,dy,5.80,6.15,2.55,.20,'steel','drum','drum_rim')
    # Static latch and side support arms visible in the photo, never animated parts.
    for side in (-1,1):
        x=dx+side*2.52
        c(f'drum_latch_{side}',[x,9.35,4.69],[.30,.93,2.15],'steel','controls','latch')
        c(f'drum_pivot_{side}',[x,9.67,.85],[.38,.68,.72],'steel','controls','pivot',('x',45))
        beam(f'drum_cradle_{side}',[x,9.40,.87],[x,9.10,3.84],.32,.40,'steel','controls','latch')
    # Broad swept rear upper receiver and pale closed stock slab, true stock air.
    box('receiver_core',[7.12,10.72,6.12],[8.88,12.62,13.71],'green','receiver','receiver')
    c('receiver_crown',[8,12.56,10.44],[1.48,.44,7.61],'green','receiver','receiver')
    for side in (-1,1):
        c(f'receiver_shoulder_{side}',[8+side*.70,12.52,10.47],[.33,.33,7.66],'green','receiver','receiver',('z',side*45))
    box('receiver_underside',[7.14,10.50,6.18],[8.86,10.88,12.15],'rubber','receiver','receiver')
    box('stock_slab',[7.10,8.11,13.29],[8.90,12.55,16.11],'seafoam','stock','stock')
    box('stock_butt',[7.10,7.88,16.04],[8.90,12.40,meta['model_bounds'][1][2]],'seafoam','stock','butt')
    c('stock_top_cap',[8,12.52,14.94],[1.76,.34,2.50],'pale','stock','stock')
    beam('stock_lower_sweep',[8,5.76,10.79],[8,8.48,15.65],1.74,1.00,'seafoam','stock','stock')
    beam('stock_inner_sweep',[8,6.47,10.76],[8,9.15,13.75],1.49,.55,'seafoam','stock','stock')
    # Photo's long lower connector is full-width and continuous, not two skins.
    box('lower_frame_rail',[7.24,meta['model_bounds'][0][1],-1.56],[8.76,6.28,10.94],'seafoam','frame','rail')
    box('lower_rail_spine',[7.42,6.25,-1.63],[8.58,6.48,9.69],'steel','frame','rail_top')
    for side in (-1,1):
        c(f'rail_shoulder_{side}',[8+side*.67,6.21,4.62],[.25,.25,10.88],'pale','frame','rail',('z',side*45))
    # Source front auxiliary grip connects the shroud to the bottom rail.
    beam('front_grip_upper',[8,10.53,-3.14],[8,7.37,-1.89],1.02,.92,'rubber','front_grip','ribbed')
    beam('front_grip_lower',[8,7.48,-1.90],[8,6.05,-2.46],1.06,.84,'rubber','front_grip','ribbed')
    box('front_grip_foot',[7.31,5.20,-2.61],[8.69,6.30,-1.14],'seafoam','front_grip','grip_foot')
    c('front_grip_socket',[8,10.49,-3.14],[1.30,.42,1.09],'steel','front_grip','socket')
    # Hand grip preserves the original slanted source hand frame near Z8..10.
    box('hand_grip_neck',[7.40,9.54,7.38],[8.60,10.64,8.83],'steel','grip','socket')
    beam('pistol_grip',[8,9.82,7.98],[8,6.78,9.60],1.00,.97,'rubber','grip','grip')
    c('grip_heel',[8,6.63,9.68],[1.13,.52,1.14],'steel','grip','grip',('x',28))
    # Small original guard at front of hand grip, with real air in the aperture.
    box('guard_front',[7.75,8.94,6.35],[8.25,10.53,6.60],'steel','guard','plain')
    box('guard_bottom',[7.75,8.91,6.42],[8.25,9.14,7.66],'steel','guard','plain')
    c('trigger',[8,9.89,7.17],[.19,.58,.18],'steel','guard','plain',('x',-15))
    # Low top sight: protected flat window, matte violet reticle face from photo.
    box('sight_base',[7.46,12.72,7.54],[8.54,12.92,9.82],'steel','sight','sight')
    for side in (-1,1):
        box(f'sight_ear_{side}',[8+side*.43-.07,12.88,7.72],[8+side*.43+.07,meta['model_bounds'][1][1],9.26],'steel','sight','sight')
    box('sight_top',[7.50,13.25,7.68],[8.50,meta['model_bounds'][1][1],9.25],'edge','sight','sight_top')
    for z in (7.86,8.57,9.36):c(f'sight_recess_{z}',[8,12.94,z],[.61,.08,.18],'violet','sight','reticle')
    # Forward top latch and exposed charging lug follow source silhouette.
    for z in (6.75,7.24):c(f'top_lug_{z}',[8,12.91,z],[.44,.28,.28],'steel','controls','socket')
    c('charging_lug',[7.20,12.56,5.97],[.42,.35,.67],'steel','controls','latch')
    inputs=[BASE,'art/blockbench/weapons/w30/edge_transit.bbmodel','art/weapons/w31/references.json',HELPER,
            ASSET+'textures/item/weapon/w30/edge_transit.png','src/main/resources/destiny/weapons/w30.json']
    raw_inputs=[RAW/'Edge Transit.fbx',RAW/'Edge Transit.blend',RAW/'ETFrame_Diffuse.png',RAW/'ETSight_Diffuse.png',RAW/'ETBolts_Diffuse.png',PHOTO]
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='edge_transit')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    catalogue=next(r for r in json.loads((ROOT/'src/main/resources/destiny/weapons/w30.json').read_bytes()) if r['id']=='edge_transit')
    assert catalogue['family']=='heavy_grenade_launcher'
    return dict(id='edge_transit',revision='W136',method='authored filled semantic cuboids + independently authored continuous face UV',
        source=meta,reference=ref,catalogue=catalogue,palette=PALETTE,parts=parts,
        identity=['seafoam structural lower rail and swept stock','green offset drum with long raised bays / dark barrel jacket',
                  'two dark slanted grips / stock air / low protected sight / true recessed bore'],
        coordinate_policy=dict(basis='native X=raw X, Y=raw Z, Z=raw Y; muzzle -Z; verified selected FBX bounds',scale=meta['scale'],anchor=meta['anchor'],
           bore_axis=[8,11.58],drum_axis=[dx,dy],grip_top=[8,9.82,7.98],grip_heel=[8,6.78,9.60],
           display='exact canonical dictionary; no recenter or global scale',export='full only / existing generic reload; combat, ADS, audio and timing untouched'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Offline CPU art inspection only; native parser/pack/held/ADS/generic reload and 10-20 displays pending master.',
           'Authored static matte default-photo palette; no recovered PBR, dynamic reflection or runtime emission.',
           'Cylinder contours reduced to octagonal solids; tiny wear, source lettering and curved grip scallops simplified.',
           'Opposite photo unavailable: structural UV retained, reverse markings omitted. No new moving parts or reload split.'])

def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q



def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];u,v,q=world_points(spec['geometry'],face,w,h)
    x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    # World-space restrained material shading avoids noisy source-island seams.
    rgb*=(.97+.055*np.cos((y-10)*.4))[:,:,None]
    side=face in ('east','west');end=face in ('north','south')
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    # Crossed solids share identical end-cap paint, never tile-local borders.
    if motif!='drum_end':
        rgb[edge<.7]*=.77;rgb[(edge>=.7)&(edge<1.6)]*=1.10
    def seam(yline,mask,width=.025):
        rgb[mask&(abs(y-yline)<width)]*=.50
        rgb[mask&(abs(y-yline-.05)<.018)]*=1.13
    def screw(zc,yc,r=.09):
        rr=np.hypot(z-zc,y-yc)
        rgb[rr<r]=PALETTE['recess'];rgb[(rr>r*.73)&(rr<r)]=PALETTE['edge']
        rgb[(rr<r*.52)&(abs(z-zc)<.018)]=PALETTE['steel']
    if motif in ('shroud','ridge','collar'):
        # Default photo has a pale green belly and a broad dark charcoal crown.
        rgb[y<11.50]=np.array(PALETTE['green'])*(.93+.05*np.cos(z[y<11.50]))[:,None]
        if side:
            seam(12.12,(z>-6.5)&(z<-.65),.028)
            seam(10.96,(z>-5.7)&(z<-.8),.022)
            screw(-1.12,11.75,.15)
            # One observed shallow U-shaped front latch, as face paint.
            mark=(abs(z+1.45)<.20)&(abs(y-11.19)<.12)
            rgb[mark&(abs(y-11.19)>.075)]=PALETTE['edge']
    if motif in ('bore','collar'):
        # Axial machining is face UV; lumen stays geometry, not a black disk.
        rgb[(np.mod(z*18,1)<.16)]*=.83
    if motif=='drum_bay':
        # Local face coordinate around each long axial facet; radial at ends.
        r=spec['geometry'].get('rotation',{});o=np.array(r.get('origin',[8,8,8]))
        R=H['rotation']({r.get('axis','z'):r.get('angle',0)})
        local=(q-o)@R+o;across=local[:,:,0]-o[0]
        if face in ('up','down'):
            rim=(abs(across)>.73)|(z<.78)|(z>5.30)
            rgb[rim]=PALETTE['steel']
            # Each bay has a broad green panel, frame channels, a round latch.
            channel=(abs(abs(across)-.70)<.055)&(z<3.15)&(z>.85)
            rgb[channel]=PALETTE['recess']
            neck=.30+.38*np.clip((3.8-z),0,1)
            rgb[(abs(abs(across)-neck)<.045)&(z>2.85)&(z<5.25)]=PALETTE['recess']
            rr=np.hypot((z-4.30)*.85,across)
            rgb[rr<.30]=PALETTE['recess'];rgb[(rr>.24)&(rr<.29)]=PALETTE['edge']
            rgb[(rr<.18)&(across>-.05)]=PALETTE['steel']
    if motif=='drum_end' and end:
        rr=np.hypot(x-8.53,y-10.22)
        rgb[(rr>2.10)&(rr<2.23)]=PALETTE['steel']
        rgb[(rr>1.90)&(rr<1.95)]=PALETTE['green']
        rgb[rr<.48]=PALETTE['steel']
        rgb[(abs(x-8.53)<.10)&(y<9.65)]=PALETTE['steel']
    if motif in ('drum_rim','latch','pivot'):
        rgb[np.mod(z*14,1)<.15]*=.70
        if motif=='pivot' and side:
            rr=np.hypot(u-.5,v-.5);rgb[rr<.29]=PALETTE['recess'];rgb[(rr>.26)&(rr<.34)]=PALETTE['edge']
    if side and motif in ('stock','butt','receiver','rail','grip_foot'):
        if motif in ('stock','receiver'):
            seam(10.60,(z>9)&(z<15.6),.025)
            # Observed perforated region immediately under the rear receiver.
            vents=(z>12.30)&(z<14.03)&(y>10.46)&(y<11.35)
            rr=np.hypot(np.mod(z*.25/.065,1)-.5,np.mod(y*7,1)-.5)
            rgb[vents&(rr<.17)]=PALETTE['recess']
            for zc,yc in ((12.8,12.08),(15.8,11.73),(15.8,10.22),(15.1,8.50),(11.40,6.26)):screw(zc,yc,.12)
            seam(7.00+.51*(z-11.4),(z>11)&(z<15),.03)
        if motif=='rail':
            inset=(z>-.15)&(z<9.14)&(y>5.43)&(y<6.06)
            rgb[inset]=PALETTE['pale']
            rgb[inset&(y<5.51)]=PALETTE['steel']
            # The reference's large silver rail label is cleaned, not source grime.
            rgb[(abs(z-1.37)<.035)&inset]=PALETTE['steel']
            rgb[(abs(z-6.8)<.035)&inset]=PALETTE['steel']
        if motif=='grip_foot':
            for zc in (-2.14,-1.31):screw(zc,5.49,.08)
    if motif in ('ribbed','grip'):
        phase=np.mod(y*9,1);rgb[phase<.23]*=.56;rgb[(phase>=.23)&(phase<.34)]*=1.19
        if side:
            for zc,yc in ((-2.68,10.10),(-1.85,7.94),(8.11,9.56),(9.73,6.84)):screw(zc,yc,.13)
            if motif=='grip':
                # Small light lozenges seen on the source grip, kept as UV detail.
                band=(z>8.55)&(z<8.86)&(y>7.50)&(y<9.05)
                rgb[band]=PALETTE['recess'];rgb[band&(np.mod(y*5,1)<.45)]=PALETTE['edge']
    if motif=='reticle':
        rgb[:]=PALETTE['violet'];rgb[(abs(u-.5)<.06)|(abs(v-.5)<.10)]=[188,184,201]
    im=Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))
    # Legible small observed label on photo-facing barrel/drum panels only.
    if face=='up' and motif=='drum_bay' and spec['geometry']['name']=='drum_bay_2':
        dr=ImageDraw.Draw(im);dr.text((max(2,w*.25),max(2,h*.26)),'H382',fill=(183,193,181,255),font_size=8)
    if face=='west' and motif=='stock':
        dr=ImageDraw.Draw(im)
        if spec['geometry']['name']=='stock_slab':dr.text((w*.24,h*.56),'T84',fill=(80,109,103,255),font_size=9)
    return im

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
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
    model=dict(credit='Edge Transit W136 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/edge_transit','particle':'destiny:item/weapon/w123/edge_transit'},
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
        name='Edge Transit W136 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='edge_transit.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w136=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))



def source_triangles(meshes):
    # The rip has no independent decal albedo; omit 429 overlay triangles here.
    textures={n:np.asarray(Image.open(RAW/f).convert('RGBA')) for n,f in
              [('Frame','ETFrame_Diffuse.png'),('Sight','ETSight_Diffuse.png'),('Bolts','ETBolts_Diffuse.png')]}
    textures['Emission']=np.array([[[32,29,40,255]]],np.uint8)
    out=[]
    for m in meshes:
        if m['material']=='Decals':continue
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:out.append((ps,uv,textures[m['material']],n/length))
    return out


def comparison(d,meshes,atlas,model):
    w,h=900,360;sheet=Image.new('RGB',(2700,2100),'#151d27');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'EDGE TRANSIT / W136 / FILLED SEMANTIC VOLUMES + AUTHORED FACE UV / CPU ART ONLY',28)
    photo=Image.open(PHOTO).convert('RGB').crop((675,280,1750,910));photo.thumbnail((1000,450));sheet.paste(photo,(15,60))
    label(20,517,'ACTUAL DEFAULT PHOTO / seafoam frame, green drum, dark shroud',19)
    for i,fn in enumerate(('ETFrame_Diffuse.png','ETSight_Diffuse.png')):
        im=Image.open(RAW/fn).convert('RGB');im.thumbnail((280,310));sheet.paste(im,(1030+i*290,80));label(1030+i*290,414,'RAW NEUTRAL '+('FRAME' if i==0 else 'SIGHT'),17)
    for i,line in enumerate([f'{len(model["elements"])} filled opaque cuboids / FULL ONLY',
            'Solid offset drum + raised longitudinal bays',
            'True barrel bore / open stock + hand frame',
            'Seafoam lower rail / dark ribbed grips',
            'Original scale, anchor, axes and display',
            'No split or invented moving parts',
            'Native QA pending master']):label(1650,85+i*47,line,23)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/edge_transit.png'))
    label(20,563,'ACTUAL FBX / neutral diffuse / overlay decals omitted',19)
    label(w+20,563,f'CANONICAL / {len(old["elements"])} cuboids / NOT RAW FBX',19)
    label(2*w+20,563,f'W136 / {len(model["elements"])} authored solids / CPU ART',19)
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('PHOTO SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.40,-.65]),('OPPOSITE REAR THREE-QUARTER',[1,.36,.65])]):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,600+row*h));label(col*w+15,609+row*h,name,17)
    for col,(group,cam) in enumerate([('muzzle',[.18,.13,-1]),('drum',[-1,.25,-.65]),('grip',[-1,.1,-.15]),('stock',[-1,.16,.3]),('sight',[-.15,.18,-1])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names]);points=np.concatenate([vertices(e) for e in sub['elements']])
        im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](points,cam,540,330),(540,330))
        sheet.paste(im,(col*540,1710));label(col*540+14,1720,group.upper()+' / SOLID DETAIL',17)
    label(20,2050,'Matched camera + scale per row. Native parser, held frame, ADS, generic reload, audio/timing, 10-20 display QA pending master.',19)
    return png(sheet)


def review_text(d,counts):
    return f'''# Edge Transit W136 offline art review

Actual default photo: `{PHOTO}`, SHA-256 `{d['reference']['sha256']}`; visually inspected before authoring. Read-only W30 FBX, metadata and neutral Frame/Sight/Bolts albedos establish proportions and detail. Catalogue confirms `heavy_grenade_launcher`, Adaptive Frame. Identity: pale seafoam lower rail and swept stock, dark barrel jacket/pale muzzle lip, large offset green drum with broad longitudinal bays, dark front/pistol grips and low protected sight. Materials are authored photo-backed static matte paint; PBR, reflections and exact dye/wear are not reconstructed.

**{sum(counts.values())} emitted filled opaque cuboids; {sum(counts.values())*6} independently UV-authored faces; zero triangle adapters; assembled FULL {sum(counts.values())}/1000.** Groups: {json.dumps(counts,sort_keys=True)}. Four crossing solid prisms form a filled octagonal drum. Eight broad raised bays and two structural rims explain silhouette and parallax. End-cap paint is world aligned across intersecting solids. Thick shroud walls enclose a real bore terminating behind the barrel. Receiver, stock, rail and grips have substantial cross sections. Stock/hand/front-grip air is geometry, never alpha side shells. Semantic proportions are hand authored; no source mesh-island, voxel or polygon conversion.

Each face has an independent proportional rectangle on a 1024-square atlas with opaque extruded 2px gutters. Green bays use continuous paint for channels, end latches and H382; stock/receiver/rail use observed seams, vents, fasteners and T84; grip ribs/marks are UV details. No source albedo or UV is transplanted to the new atlas. No random dirt, invented labels or decorative screw cubes. Neutral source albedos are explicitly not default dye. Source illustration omits 429 untextured decal-overlay triangles, while all six source objects and 30,450 triangles are parsed and checked. Source Emission uses a declared static dark tint.

Actual FBX local rotation approximately [-90,0,0], scaling [100,100,100]; raw thin X, length Y, vertical Z. Native = raw [X,Z,Y] × {d['source']['scale']} + {d['source']['anchor']}. This reproduces the W30 union bounds and 30,450 triangles. Beloved's [-Y,Z,-X] basis would be incorrect. Bore [8,11.58] points -Z; drum axis [8.53,10.22]. Canonical muzzle/butt Z endpoints, lower Y and sight upper Y are retained. Hand frame runs [8,9.82,7.98] to [8,6.78,9.60]; no global scale/recenter/display alteration. Broad drum and curved source are intentionally not exact geometric equivalents.

Canonical display dictionary is copied exactly. Full candidate `destiny:weapon_surface_w123/edge_transit`, texture `destiny:item/weapon/w123/edge_transit`; no split resources or newly animated drum/latch. Existing generic reload, combat, audio, ADS and all timing remain unchanged. Shared registration, canonical model, runtime and HUD remain untouched. Inspection BBModel embeds final texture and semantic groups with absolute coordinates/rotations/UV. No DCC was opened.

comparison.png includes the actual photo, neutral raw textures, FBX/canonical/final in matched side/front-quarter/opposite rear-quarter views, plus bore/drum/grip/stock/sight details. Worker report records actual final image observations. CPU art views are not native held/ADS evidence. Fine scratches, sculpted grip scallops and cylindrical contours are simplified; opposite-side markings are omitted without a photo.

Targeted tests cover exclusive ownership, full-only budget/schema, filled interiors, UV/alpha/gutters, true openings, source object/triangle/bounds/basis provenance, exact display/hand frame, BB parity, hashes and deterministic generation. Native 26.3 parser/pack load, first/third-person holding, ADS, generic reload/audio/timing and 10-20 displays remain pending master. No Gradle, DCC, native/client/server or children used; no performance acceptance claimed.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    assert len(model['elements'])<=1000
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='edge_transit',revision='W136',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
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

OWNED=['scripts/generate_surface_w123_edge_transit.py','scripts/qa/test_surface_w123_edge_transit.py',
       ART+'design.json',ART+'manifest.json',ART+'review.md',ART+'inspection.bbmodel',ART+'comparison.png',REPORT,TEXTURE,MODEL]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    batch=json.loads((ROOT/'docs/qa/2026-10-26/w136/batch.json').read_bytes())
    owned=next(f['owned_paths'] for f in batch['features'] if f['name']=='w136-edge_transit')
    assert len(OWNED)==10 and set(OWNED)==set(owned)
    outputs=generate();assert set(outputs)<=set(owned)
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
