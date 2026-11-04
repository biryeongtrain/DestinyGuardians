#!/usr/bin/env python3
"""W129 Antiope-D: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/antiope_d/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/submachine_gun/antiope_d.json'
MODEL = ASSET + 'models/weapon_surface_w123/antiope_d.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/antiope_d.png'
REPORT = 'docs/qa/2026-10-26/w129/antiope_d-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/antiope_d/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/antiope_d.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(ivory=[193,193,176], edge=[216,217,204], steel=[132,140,139],
               graphite=[43,43,38], recess=[23,26,26], rubber=[31,32,30],
               brown=[102,76,54], brown_edge=[125,94,64], orange=[216,88,50], lens=[53,69,67])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w129:antiope_d:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/antiope_d.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Antiope-D.fbx').read_bytes())==meta['source_files']['Antiope-D.fbx']
    roots=H['parse_fbx'](RAW/'Antiope-D.fbx')
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
        if turn:
            axis,angle=turn
            e['rotation']=dict(origin=[round((a+b)/2,6) for a,b in zip(lo,hi)],axis=axis,angle=angle)
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def center(name,c,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,6) for a,b in zip(c,size)],
            [round(a+b/2,6) for a,b in zip(c,size)],mat,group,motif,turn)
    def tube(name,x,y,z0,z1,r,t,mat,group):
        # Real open octagonal bore: eight solid tangent walls, never alpha.
        length=z1-z0; w=2*r*math.tan(math.pi/8)+.018
        for i in range(8):
            a=i*45; q=math.radians(a); cr=r-t/2
            c=[x-cr*math.sin(q),y+cr*math.cos(q),(z0+z1)/2]
            size=[w,t,length]; turn=None
            if a%90==0:
                if a%180: size=[t,w,length]
            else: turn=('z',45 if i%4==1 else -45)
            center(f'{name}_{i}',c,size,mat,group,'ring',turn)
    def octagon(name,c,w,h,length,mat,group,motif='plain'):
        # Filled solid octagon approximated with a center and four shoulders.
        center(name+'_core',c,[w*.70,h,length],mat,group,motif)
        center(name+'_cross',c,[w,h*.70,length],mat,group,motif)
        for s in (-1,1):
            for t in (-1,1):
                center(f'{name}_bevel_{s}_{t}',[c[0]+s*w*.345,c[1]+t*h*.345,c[2]],
                       [w*.29,h*.29,length],mat,group,motif,('z',45*s*t))
    # Broad load-bearing body. The upper ivory and lower dark parts are solids,
    # with color/decals on their actual faces, not body-shaped side cards.
    box('upper_receiver',[7.35,12.62,1.60],[8.65,13.91,12.48],'ivory','receiver','upper')
    box('lower_receiver',[7.34,11.13,1.52],[8.66,12.64,12.65],'graphite','receiver','lower')
    box('rear_action',[7.38,11.51,11.55],[8.62,13.29,13.06],'graphite','receiver','action')
    box('top_spine',[7.51,13.91,1.67],[8.49,14.15,12.24],'ivory','receiver','rail')
    for s in (-1,1):
        center(f'upper_shoulder_{s}',[8+s*.60,13.84,6.90],[.30,.30,10.62],'ivory','receiver','plain',('z',45*s))
    box('front_receiver_boss',[7.27,11.91,.72],[8.73,13.10,1.91],'ivory','fore_end','front')
    box('lower_fore_end',[7.33,10.47,.90],[8.67,11.93,3.18],'ivory','fore_end','fore_end')
    center('fore_end_chin',[8,10.40,1.65],[1.17,.38,1.70],'ivory','fore_end','plain',('x',-22.5))
    box('front_sling_mount',[7.73,10.32,.40],[8.27,11.03,1.04],'steel','fore_end','plain')
    # Physical muzzle and throat, recessed dark termination >1.5 units deep.
    tube('muzzle',8,12.33,-2.785893526985056,-1.0,.52,.15,'ivory','muzzle')
    tube('barrel_throat',8,12.33,-1.18,.83,.41,.18,'graphite','muzzle')
    box('bore_depth_stop',[7.76,12.09,.64],[8.24,12.57,.71],'recess','muzzle','bore')
    # Open front protection ears around actual post.
    box('front_sight_base',[7.39,13.16,.43],[8.61,13.79,1.66],'ivory','sights','front_sight')
    for s in (-1,1):
        center(f'front_sight_ear_{s}',[8+s*.51,14.18,.97],[.22,1.18,.49],'ivory','sights','plain')
    box('front_sight_post',[7.94,13.72,.84],[8.06,14.38,1.02],'steel','sights','plain')
    # Top Picatinny bars follow the long continuous rail; no side panel tiling.
    for i,z in enumerate(np.linspace(2.0,6.4,8)):
        center(f'rail_tooth_{i}',[8,14.24,float(z)],[1.03,.18,.25],'edge','rail','rail')
    box('rear_rail',[7.49,14.13,10.45],[8.51,14.27,12.08],'ivory','rail','rail')
    for i,z in enumerate((10.72,11.27,11.82)):
        center(f'rear_rail_tooth_{i}',[8,14.34,z],[1.06,.18,.25],'edge','rail','rail')
    # Rear peep is a true hole, no opaque lens across it.
    box('rear_sight_pedestal',[7.51,14.08,6.91],[8.49,14.52,8.03],'ivory','sights','plain')
    box('rear_sight_riser',[7.64,14.50,7.07],[8.36,14.83,7.91],'ivory','sights','plain')
    tube('rear_peep',8,15.22,7.27,7.70,.54,.115,'ivory','sights')
    center('rear_sight_adjuster',[8.55,14.65,7.50],[.28,.39,.47],'graphite','sights','dial')
    # The photo's orange rear cap is a structural top/rear block.
    box('orange_rear_cap',[7.31,13.09,10.46],[8.69,14.08,12.65],'orange','receiver','orange_cap')
    # Solid brown pistol grip enclosing the feed, full thickness across X.
    center('grip_core',[8,9.32,9.49],[1.26,4.00,1.98],'brown','pistol_grip','grip',('x',-6))
    center('grip_front_bevel',[8,9.20,8.57],[1.18,3.68,.37],'brown','pistol_grip','grip',('x',-11))
    center('grip_backstrap',[8,9.36,10.43],[1.29,3.84,.31],'brown','pistol_grip','grip',('x',-6))
    box('grip_heel',[7.27,7.11,8.48],[8.73,7.43,10.67],'brown','pistol_grip','heel')
    # Angled forward grip with black broad insert handled by UV.
    center('foregrip_body',[8,8.91,3.45],[1.24,3.40,1.65],'brown','foregrip','foregrip',('x',-27))
    center('foregrip_front_bevel',[8,9.18,2.72],[1.15,3.04,.36],'brown_edge','foregrip','plain',('x',-27))
    center('foregrip_heel',[8,7.43,4.18],[1.29,.41,1.91],'brown','foregrip','heel',('x',-27))
    # Guard surrounds open air; trigger hangs clear of its bow.
    center('guard_front',[8,10.33,5.73],[.63,1.36,.22],'graphite','trigger','plain',('x',-24))
    box('guard_floor',[7.685,9.47,6.00],[8.315,9.72,8.27],'graphite','trigger','plain')
    center('guard_rear',[8,10.13,8.34],[.63,1.11,.24],'graphite','trigger','plain',('x',19))
    center('trigger',[8,10.49,7.94],[.22,.97,.22],'steel','trigger','plain',('x',-22.5))
    # Original short stock, cheek pad, lower triangular air and rear pad.
    box('stock_comb',[7.39,12.07,12.61],[8.61,13.48,16.40],'ivory','stock','stock')
    center('stock_cheek_pad',[8,13.43,14.32],[1.39,.60,3.19],'rubber','stock','cheek',('x',-7))
    box('stock_butt_upper',[7.43,11.16,16.24],[8.57,13.38,16.83],'ivory','stock','stock')
    box('stock_butt_pad',[7.48,8.999,16.77],[8.52,12.61,17.214106473014944],'ivory','stock','butt')
    center('stock_lower_brace',[8,10.70,15.23],[.70,.28,3.53],'ivory','stock','plain',('x',35))
    for s in (-1,1):
        center(f'stock_lock_plate_{s}',[8+s*.79,11.74,14.58],[.35,.81,3.75],'ivory','stock','stock_plate')
    # Distinct side cylinder (right/native +X), its front ring and lens recess.
    octagon('side_cylinder',[9.18,13.18,3.62],1.16,1.16,2.44,'graphite','side_optic','knurl')
    for i,z in enumerate((2.64,3.47,4.27)):
        # Thin collars are actual solid transverse bands, not decorative screws.
        octagon(f'side_band_{i}',[9.18,13.18,z],1.24,1.24,.20,'ivory','side_optic','ring')
    tube('side_objective',9.18,13.18,1.98,2.38,.62,.13,'steel','side_optic')
    box('side_objective_lens',[8.82,12.82,2.31],[9.54,13.54,2.34],'lens','side_optic','lens')
    box('side_mount',[8.55,12.85,3.56],[9.15,13.52,4.69],'graphite','side_optic','plain')
    # Action charging handle and selector; shallow screws/markings remain UV.
    box('charging_rail',[8.64,12.31,7.61],[8.86,12.73,11.23],'steel','controls','charging')
    box('charging_handle',[8.81,12.22,7.61],[9.18,12.84,8.21],'steel','controls','dial')
    center('selector',[8.77,11.25,9.01],[.22,.71,.23],'graphite','controls','knurl',('x',-31))
    # Magazine in the original full assembly frame. No new split model emitted.
    box('magazine_core',[7.63,3.63,7.80],[8.37,8.16,9.55],'edge','magazine','magazine')
    box('magazine_front_spine',[7.61,3.61,7.73],[8.39,7.89,7.99],'steel','magazine','magazine')
    box('magazine_back_spine',[7.60,3.61,9.39],[8.40,7.90,9.62],'steel','magazine','magazine')
    box('magazine_floor',[7.52,3.46,7.73],[8.48,3.77,9.67],'graphite','magazine','heel')
    box('magazine_pull_front',[7.77,3.3626039679040387,8.36],[8.23,3.49,9.26],'graphite','magazine','plain')
    # Sling eye under the fore-end: thin bars surrounding real air.
    box('sling_left',[7.58,10.03,.42],[7.77,10.50,.65],'steel','sling','plain')
    box('sling_right',[8.23,10.03,.42],[8.42,10.50,.65],'steel','sling','plain')
    box('sling_floor',[7.65,9.94,.42],[8.35,10.11,.65],'steel','sling','plain')
    inputs=[BASE,'art/blockbench/weapons/w30/antiope_d.bbmodel',
            'art/weapons/w31/palette-overrides.json','art/weapons/w31/references.json',HELPER,
            ASSET+'textures/item/weapon/w30/antiope_d.png']
    raw_inputs=[RAW/'Antiope-D.fbx',RAW/'Antiope-DBarrel_Diffuse.dds',RAW/'Antiope-DStock_Diffuse.dds',PHOTO]
    return dict(id='antiope_d',revision='W129',method='authored semantic opaque cuboids / authored per-face UV',
        source=meta,palette=PALETTE,parts=parts,
        identity=['ivory upper / black lower receiver','orange rear cap / brown grips / silver magazine',
                  'side cylinder / two iron sights','compact stock with lower air / angled forward grip'],
        coordinate_policy=dict(basis='native X=raw X, Y=raw Z, Z=raw Y; muzzle -Z',scale=meta['scale'],
             anchor=meta['anchor'],grip='original pistol-grip frame; no global recenter or scale',
             display='exact canonical dictionary',export='full only; existing generic reload and ADS graph unchanged'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Offline CPU inspection only; native parser / pack / gameplay / performance pending master.',
                     'Photo-backed default paint with restrained static shading; no PBR reproduction.',
                     'Reverse-side photo not supplied; consistent structural materials, no invented reverse-side text.',
                     'Cuboid silhouette intentionally simplifies the original sculpted curves.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];e=spec['geometry'];u,v,q=world_points(e,face,w,h)
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.97+.055*np.exp(-((v-.28)/.33)**2))[:,:,None]
    # Crisp subtle edge light; large faces stay calm rather than random grime.
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    rgb[edge<.7]*=.76;rgb[(edge>=.7)&(edge<1.6)]*=1.07
    side=face in ('east','west')
    if side and motif=='upper':
        # Long dark action cut at lower edge, grounded in source/photo layout.
        z=q[:,:,2];y=q[:,:,1]
        rgb[(y<12.83)&(z>5.6)]=PALETTE['graphite']
        seam=(abs(y-13.68)<.025)&(z>2)&(z<10.5);rgb[seam]*=.65
    if side and motif=='lower':
        z=q[:,:,2];y=q[:,:,1]
        # Source H emblem (not an imported weapon logo) and recessed panel.
        mark=(abs(z-6.36)<.045)&(abs(y-11.78)<.32)
        mark|=(abs(z-6.72)<.045)&(abs(y-11.78)<.32)
        mark|=(abs(y-11.78)<.05)&(z>6.19)&(z<6.90)
        rgb[mark]=PALETTE['orange']
        panel=((z>3.0)&(z<4.73)&(y>11.33)&(y<12.33))
        border=panel&((z<3.06)|(z>4.67)|(y<11.39)|(y>12.27));rgb[border]=PALETTE['steel']
        for zc in (3.46,4.20):
            r=np.hypot(z-zc,y-11.82);rgb[(r>.16)&(r<.20)]=PALETTE['steel']
            rgb[(abs(z-zc)<.024)&(abs(y-11.82)<.14)]=PALETTE['edge']
        # Long shallow slots stay in UV instead of floating geometry strips.
        slot=(z>7.25)&(z<8.45)&(y>11.53)&(y<11.83);rgb[slot]*=.64
    if motif in ('grip','foregrip','cheek','butt'):
        if motif=='grip' and side:
            # Photo: tan/brown worn front and dark rear wrapping, calm texture.
            a=(u>.20)&(u<.80)&(v>.18)&(v<.83)
            rgb[a]*=.79
            rib=(np.mod(v*22,1)<.10)&a;rgb[rib]*=.91
        if motif=='foregrip' and side:
            mask=(u>.14)&(u<.86)&(v>.11)&(v<.83)
            rgb[mask]=np.array(PALETTE['rubber'])*(.97+.04*np.sin(v[mask]*100))[:,None]
        if motif=='cheek':rgb*=(.96+.025*np.cos(u*140)*np.cos(v*113))[:,:,None]
        if motif=='butt' and face=='south':rgb[np.mod(v*16,1)<.20]*=.73
    if motif=='magazine' and side:
        # Two long pressed flutes, sourced from photo and raw silhouette.
        for c in (.27,.70):
            rgb[(abs(u-c)<.035)&(v>.10)&(v<.94)]*=.64
            rgb[(abs(u-c-.035)<.012)&(v>.10)&(v<.94)]*=1.13
    if motif=='stock_plate' and side:
        slot=(u>.18)&(u<.83)&(v>.30)&(v<.61);rgb[slot]=PALETTE['graphite']
    if motif=='knurl':rgb[(np.mod(u*20,1)<.17)&(v>.05)&(v<.95)]*=.73
    if motif=='charging' and side:rgb[(np.mod(u*10,1)<.16)&(v>.10)&(v<.90)]*=.68
    if motif=='lens':
        rgb*= (.84+.20*np.exp(-((u-.32)**2+(v-.32)**2)/.06))[:,:,None]
    # Source-backed large fasteners: UV only, never arrays of screw cubes.
    if side and motif in ('orange_cap','stock_plate','front','fore_end'):
        for uc,vc in ((.15,.25),(.85,.70)) if motif=='stock_plate' else ((.72,.42),):
            radius=min(w,h)*.07;rr=np.hypot((u-uc)*w,(v-vc)*h)
            rgb[rr<radius]=PALETTE['graphite'];rgb[(rr>radius*.75)&(rr<radius)]=PALETTE['steel']
            rgb[(abs((u-uc)*w)<.65)&(rr<radius*.62)]=PALETTE['edge']
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=25 if spec['motif'] in ('lower','grip','foregrip','magazine') else 21
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
    model=dict(credit='Antiope-D W129 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/antiope_d','particle':'destiny:item/weapon/w123/antiope_d'},
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
        name='Antiope-D W129 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='antiope_d.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w129=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    result=[];textures={}
    for m in meshes:
        mat=m['material']
        if mat not in textures:
            textures[mat]=np.array([[[45,45,42,255]]],np.uint8) if 'Override' in mat else np.asarray(Image.open(RAW/(mat+'_Diffuse.dds')).convert('RGBA'))
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((t,uv,textures[mat],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=900,380;sheet=Image.new('RGB',(2700,2070),'#151d27');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'ANTIOPE-D / W129 / SEMANTIC SOLIDS + AUTHORED FACE UV / OFFLINE ART INSPECTION',28)
    photo=Image.open(PHOTO).convert('RGB').crop((760,235,1650,955));photo.thumbnail((760,370));sheet.paste(photo,(20,55))
    for i,fn in enumerate(('Antiope-DBarrel_Diffuse.dds','Antiope-DStock_Diffuse.dds')):
        im=Image.open(RAW/fn).convert('RGB');im.thumbnail((330,330));sheet.paste(im,(830+i*360,64));label(830+i*360,400,'RAW '+('BARREL' if i==0 else 'STOCK')+' / UNDYED',17)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    for i,line in enumerate([f'{len(model["elements"])} opaque solid cuboids / full only',
          '0 alpha shells / 0 triangle adapters',
          'Ivory / black / orange / brown / silver default paint',
          'True bore / peep / guard / stock air',
          'Canonical display + source anchor and scale',
          'CPU render only; native and live QA pending master']):label(1570,85+i*47,line,23)
    label(20,450,'RAW FBX / 17,248 triangles / NEUTRAL DIFFUSE')
    label(w+20,450,'CANONICAL / 230 cuboids / READ ONLY')
    label(2*w+20,450,f'W129 / {len(model["elements"])} opaque semantic solids')
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/antiope_d.png'))
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE / DEFAULT PHOTO SIDE',[1,0,0]),('FRONT THREE-QUARTER',[1,.42,-.65]),('REAR / OPPOSITE THREE-QUARTER',[-1,.36,.65])]):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,490+row*h));label(col*w+15,498+row*h,name,17)
    # Four close physical inspections from multiple directions.
    for col,(group,cam) in enumerate([('muzzle',[.26,.13,-1]),('sights',[.15,.10,-1]),('trigger',[1,.16,-.15]),('stock',[-1,.30,.4])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names])
        points=np.concatenate([vertices(e) for e in sub['elements']]);im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](points,cam,675,335),(675,335))
        sheet.paste(im,(col*675,1660));label(col*675+14,1668,group.upper()+' / REAL OPEN GEOMETRY',17)
    label(20,2025,'Matched full-model camera / scale. Native parser, held/ADS/reload and 10-20 display checks: pending master. No game acceptance implied.',21)
    return png(sheet)


def review_text(d,counts):
    return f"""# Antiope-D W129 offline art review

The actual supplied Bungie default photo (`/tmp/destiny-weapons-w31/references/antiope_d.jpg`, item 566976653) was opened with view_image. Both raw Barrel and Stock diffuse maps were converted into the owned comparison path and opened with view_image: they are neutral gray, not finished default dye. W31 reference hashes and the absent Antiope palette override were checked. Default identity is ivory upper metal, dark lower receiver, orange rear cap, brown grips, silver magazine, compact stock and native +X side cylinder. No alternate shader palette was invented.

{sum(counts.values())} emitted opaque solid cuboids / {sum(counts.values())*6} explicitly UV-authored faces. The 80-120 draft guideline was a starting point; the actual count follows meaningful parts and open holes, with a hard ceiling of 1,000. Group counts: {json.dumps(counts,sort_keys=True)}. Full only: no split body/magazine outputs. The generic existing reload/ADS graph is untouched.

Long receiver panels are solid broad cuboids; grip and forward grip have full thickness. Stock braces, guard bars, open eight-wall muzzle and peep remain air-filled geometry from multiple directions. The muzzle has a recessed throat and dark stop; the side optic has an inset opaque lens; its lens does not replace the peep gap. Large smooth faces use independent proportional UV rectangles. Shallow seams, flutes, knurling, existing H emblem and observed fasteners are restrained authored texture; source islands were not transplanted. No body-shell alpha cards, triangle adapters or invented native triangles fields are used.

1024-square RGBA atlas: {d['atlas']['face_islands']} independent islands with 2px extruded opaque gutters. Native elements use ordinary cuboid faces and single-axis rotation records. Inspection BBModel embeds this exact atlas and the same geometry organized by semantic group. Static material shading is not PBR. Reverse-side original photo is unavailable; unobserved text is not invented.

The canonical model is read-only. Source basis X=raw X, Y=raw Z, Z=raw Y, muzzle -Z; scale {d['source']['scale']} and anchor {d['source']['anchor']} are retained without global recentering. Exact canonical display dictionary and original grip/magazine assembly frame remain. Cuboid shape simplification is intentional; source-poly equivalence is not claimed.

comparison.png includes the actual default photo, neutral raw diffuse atlases, unchanged FBX geometry, read-only canonical and new authored solids in matched side, front-quarter and opposite rear-quarter views; muzzle/sight/guard/stock detail views show physical air. Final comparison must be opened with view_image; worker report records the observed result.

Offline targeted tests cover deterministic outputs, schema, full-only ownership, opacity/UV gutters, display/provenance, real bore/peep/guard/stock voids, coordinate scale and inspection parity. Master owns registration/integration and live QA: native 26.3 parsing and resource loading, first/third-person holding, ADS and generic reload, plus 10-20 display observations. No Gradle/server/GUI/native/CU or live performance test was run.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='antiope_d',revision='W129',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        canonical_display_exact=True,full_only=True,generic_reload_ADS_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w129/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w129-antiope_d'))
    assert len(owned)==10 and set(outputs)<=owned
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
