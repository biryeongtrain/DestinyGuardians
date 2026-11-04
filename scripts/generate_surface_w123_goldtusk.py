#!/usr/bin/env python3
"""W141 Goldtusk: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/goldtusk/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sword/goldtusk.json'
MODEL = ASSET + 'models/weapon_surface_w123/goldtusk.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/goldtusk.png'
REPORT = 'docs/qa/2026-10-26/w141/goldtusk-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/goldtusk/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/goldtusk.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(dark=[33,36,36], steel=[178,180,172], edge=[226,225,210],
               gold=[165,139,68], gold_edge=[203,178,105], gold_shadow=[113,91,43],
               rubber=[22,25,26], recess=[13,17,18])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w141:goldtusk:'+name))


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
    """Inert source evidence only. Goldtusk thin=Y: canonical [-Y,Z,X]."""
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/goldtusk.bbmodel').read_bytes())['destiny_w30']
    for name,digest in meta['source_files'].items():
        assert sha((RAW/name).read_bytes())==digest,name
    roots=H['parse_fbx'](RAW/'Goldtusk.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(p for c,p in links if c==node[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=2e-5,rtol=0)
        assert props['Lcl Scaling']==[100,100,100] and props.get('Lcl Translation',[0,0,0])==[0,0,0]
        cs={c[0]:c for c in node[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=raw[:,[1,2,0]]*[-1,1,1]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]);assert np.all((ix<0).reshape(-1,3)==[False,False,True])
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0);vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        meshes.append(dict(name=name,vertices=v,faces=faces,uv=uv))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==3048
    catalogue=json.loads((ROOT/'src/main/resources/destiny/weapons/w30.json').read_bytes())
    assert next(w for w in catalogue if w['id']=='goldtusk')['family']=='sword'
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='goldtusk')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta

def make_design(meta):
    parts=[]
    def c(name,pos,size,mat,group,motif='metal',turn=None):
        lo=[round(a-b/2,7) for a,b in zip(pos,size)];hi=[round(a+b/2,7) for a,b in zip(pos,size)]
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def beam(name,y0,z0,y1,z1,thick,width,mat,group,motif='metal',x=8):
        angle=math.degrees(math.atan2(z1-z0,y1-y0))
        c(name,[x,(y0+y1)/2,(z0+z1)/2],[thick,math.hypot(y1-y0,z1-z0)+.035,width],mat,group,motif,('x',angle))
    def collar(name,y,z,length,rx,rz,mat,group):
        # Filled octagon, not a hollow uniform shell.
        c(name+'_core',[8,y,z],[rx*1.48,length,rz*1.48],mat,group,'gold')
        for i,(sx,sz) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
            c(name+'_facet_'+str(i),[8+sx*rx*.56,y,z+sz*rz*.56],[rx*.64,length,rz*.64],mat,group,'gold',('y',45))
    # Authored arc stations: long solid dark blade shoulder, narrower pale bevel,
    # genuinely thinner cutting strip. Cross-section changes are real geometry.
    stations=[(10.73,8.34,1.26),(14.0,8.43,1.24),(18.0,8.42,1.23),
              (21.5,8.36,1.23),(25.0,8.20,1.23),(28.72,7.91,1.23)]
    def blade_span(i,a,b,group):
        y0,z0,w0=a;y1,z1,w1=b;w=(w0+w1)/2
        for role,offset,width,thick,motif in (
            ('dark',-.18,.64,.202,'blade_dark'),('steel',.305,.33,.142,'blade_bevel'),
            ('edge',.485,.055,.048,'cutting'),('steel',-.493,.028,.065,'spine')):
            start_y,start_z=y0,z0+offset*w0
            if group=='blade' and i==0 and motif in ('blade_bevel','cutting'):
                # The pale edge begins again after the real heel bite.
                t=(12.12-y0)/(y1-y0);start_y=12.12
                start_z=(z0+offset*w0)*(1-t)+(z1+offset*w1)*t
            label={'blade_dark':'shoulder','blade_bevel':'bevel','cutting':'edge','spine':'spine'}[motif]
            beam(f'{group}_{label}_{i}',start_y,start_z,y1,z1+offset*w1,
                 thick if group=='blade' else thick*max(.28,min(1,w/1.2)),width*w,role,group,motif)
    for i,(a,b) in enumerate(zip(stations,stations[1:])):blade_span(i,a,b,'blade')
    tip=[stations[-1],(29.55,7.75,1.20),(30.25,7.39,1.02),(30.83,6.93,.70),(31.43,6.36,.025)]
    for i,(a,b) in enumerate(zip(tip,tip[1:])):blade_span(i,a,b,'point')
    # Heel has a genuine bite in the cutting side. Dark web stays continuous.
    c('heel_tang',[8,10.49,8.23],[.202,.96,1.04],'dark','heel','blade_dark')
    beam('heel_silver_root',10.37,8.74,11.27,8.85,.14,.24,'steel','heel','blade_bevel')
    beam('heel_silver_after_bite',11.76,8.83,12.14,8.86,.14,.28,'steel','heel','blade_bevel')
    # Back-spine serrations are silhouette features near the ricasso only.
    for i in range(5):
        c('ricasso_tooth_'+str(i),[8,11.17+i*.25,7.692+i*.007],[.17,.13,.16],'dark','heel','blade_dark',('x',-18))
    # Continuous filled palm section at the unmodified W30 hand origin.
    c('palm_core',[8,6.16,8.12],[.58,5.93,.82],'rubber','grip','grip')
    # Gold long frame rails border a true dark recessed side channel.
    beam('hilt_backbone',3.25,7.93,9.30,7.96,.64,.29,'gold','hilt','gold')
    beam('hilt_black_palm_pad',3.95,8.68,8.36,8.68,.66,.43,'rubber','hilt','grip')
    for sign in (-1,1):
        beam('side_channel_lip_'+str(sign),3.65,8.16,8.72,8.13,.11,.12,'gold_edge','hilt','gold',8+sign*.33)
        # Broad sculpted gold side mass is filled and chamfered, never an alpha decal.
        c('palm_gold_shoulder_'+str(sign),[8+sign*.28,5.75,8.26],[.20,3.82,.30],'gold','hilt','gold',('y',sign*25))
    # Faceted neck and small swept guard, heavier on the cutting side.
    collar('neck',9.34,8.29,.65,.39,.57,'gold','guard')
    beam('guard_swept_root',9.52,8.74,10.47,9.30,.48,.47,'gold','guard','gold')
    beam('guard_terminal',10.22,9.29,10.64,9.40,.34,.23,'gold_edge','guard','gold')
    beam('guard_back_hook',9.48,7.93,10.26,7.71,.43,.31,'gold','guard','gold')
    c('guard_block',[8,10.28,8.43],[.55,.74,1.10],'gold','guard','ferrule')
    for sign in (-1,1):
        c('guard_bevel_'+str(sign),[8+sign*.22,10.26,8.42],[.12,.76,.70],'gold_edge','guard','ferrule',('y',sign*25))
    # Lower grip flange and hooked pommel are distinct load bearing forms.
    collar('lower_ferrule',3.53,8.40,.48,.36,.57,'gold','pommel')
    c('pommel_core',[8,2.99,8.58],[.62,.72,1.10],'gold','pommel','pommel')
    beam('pommel_hook',2.98,8.45,2.63,9.22,.54,.30,'gold','pommel','pommel')
    beam('pommel_back',3.43,7.94,2.86,8.13,.51,.38,'gold','pommel','pommel')
    for sign in (-1,1):
        c('pommel_chamfer_'+str(sign),[8+sign*.28,3.0,8.56],[.12,.66,.80],'gold_shadow','pommel','pommel',('y',sign*15))
    files=[BASE,'art/blockbench/weapons/w30/goldtusk.bbmodel','art/weapons/w31/references.json',
           'src/main/resources/destiny/weapons/w30.json','src/main/resources/assets/destiny/items/weapon/goldtusk.json',
           'src/main/resources/assets/destiny/models/weapon/sword/goldtusk_twohand.json',
           'src/main/resources/destiny/animation/sword_w140.animation.json',
           HELPER,
           'scripts/generate_surface_w123_crown_splitter.py','scripts/generate_surface_w123_falling_guillotine.py']
    rawfiles=[PHOTO,RAW/'Goldtusk.fbx',RAW/'Goldtusk.blend',RAW/'Goldtusk_Diffuse.dds']
    return dict(id='goldtusk',stage='W141',family='sword',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='anchor + scale * [-raw.Y, raw.Z, raw.X]',
            fbx_translation_cm=[0,0,0],fbx_rotation_deg=[-90,0,0],fbx_scale=[100,100,100],length='+Y',display='canonical exact',
            validation='all8 objects /3048 triangles / all W30 bounds within2e-6'),
        construction='authored semantic filled cuboids; no source island/voxel conversion; no alpha silhouettes',
        identity=['slender curved dark blade','pale continuous cutting bevel with diagonal etching','swept gold guard and hooked pommel','gold framed black palm channel'],
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['curved blade and pommel use a few solid arc spans; smooth original curvature is approximated',
            'face paint is authored from default screenshot; static opaque colors do not reproduce original PBR',
            'CPU comparison is offline only; pack/held/swing/guard/native swordframe/10-20 display pending master'])

def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    e=spec['geometry'];u,v,q=world_points(e,face,w,h);role=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    y=q[:,:,1];z=q[:,:,2];x=q[:,:,0];side=face in ('east','west')
    # Deliberately painted quiet material fields, no DDS sampling or random noise.
    rgb*=(.99+.014*np.sin(y*.9+z*1.8))[:,:,None]
    if motif=='blade_dark':
        # Broad charcoal polished spine and restrained silver scuffs from reference.
        rgb*=(.88+.20*u)[:,:,None]
        rgb[(np.mod(y*1.7+z*2.2,1)<.028)&(u<.24)]*=1.48
    if motif=='blade_bevel' and side:
        # Repeating shallow diagonal cuts are paint, not cuboid saw teeth.
        # Both sides use model coordinates: never random mirror of an emblem/text.
        slash=(np.mod(y*1.26+z*2.50,1)<.055)&(u>.12)&(u<.88)&(y>12.1)&(y<28.7)
        rgb[slash]*=.42
        hi=(np.mod(y*1.26+z*2.50-.06,1)<.028)&(u>.12)&(u<.88)&(y>12.1)&(y<28.7)
        rgb[hi]*=1.12
    if motif=='cutting':rgb*=1.015
    if motif=='grip':
        # Fine regular leather/rubber cross weave, bordered by solid gold frame.
        weave=(np.mod(y*24+z*12,1)<.13)|(np.mod(y*24-z*12,1)<.13)
        rgb[weave]*=1.25
    if motif in ('gold','pommel','ferrule'):
        # Continuous hand-painted channel/inlay aligned to the hilt, mild wear only.
        rgb*=(.94+.08*u)[:,:,None]
        if side:
            channel=(abs(z-(8.24+.035*(y-6)))<.025)&(y>3.9)&(y<8.72)
            rgb[channel]=PALETTE['gold_shadow']
            trim=(abs(z-(8.28+.035*(y-6)))<.017)&(y>3.9)&(y<8.72)
            rgb[trim]=PALETTE['gold_edge']
            # Small sourced fastener/inlay marks painted at their hilt positions.
            for yy,zz in ((3.18,8.63),(3.53,8.22),(8.80,8.21),(10.22,8.45),(10.22,8.72)):
                rr=(y-yy)**2+(z-zz)**2
                rgb[rr<.055**2]=PALETTE['gold_shadow']
                rgb[(rr>.055**2)&(rr<.076**2)]=PALETTE['gold_edge']
            if motif=='ferrule':
                band=(abs(z-8.68)<.035)|(abs(z-8.96)<.035)
                rgb[band]=PALETTE['gold_shadow']
        border=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[border<.55]*=.92
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(28,36,44,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=40
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
    model=dict(credit='Goldtusk W141 semantic solid arc / default gold-charcoal-ivory paint / full only',
        textures={'0':'destiny:item/weapon/w123/goldtusk','particle':'destiny:item/weapon/w123/goldtusk'},
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
        name='Goldtusk W141 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='goldtusk.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w141=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    tex=np.asarray(Image.open(RAW/'Goldtusk_Diffuse.dds').convert('RGBA'));result=[]
    for m in meshes:
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
            if length>1e-10:result.append((t,uv,tex,n/length))
    return result


def comparison(d,meshes,atlas,model):
    w,h=600,730;sheet=Image.new('RGB',(1800,2470),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'GOLDTUSK / W141 / CURVED SOLID BLADE + GOLD HILT + DEFAULT FACE PAINT',25)
    photo=Image.open(PHOTO).convert('RGB').crop((360,280,1570,860));photo.thumbnail((1030,440));sheet.paste(photo,(0,49))
    for i,line in enumerate([f'{len(model["elements"])} filled opaque cuboids / 1024 face atlas',
        'Charcoal blade shoulder / ivory bevel / thin silver edge',
        'Gold swept guard + hooked pommel / black grip',
        'Goldtusk W30 basis: [-raw.Y, raw.Z, raw.X]',
        'Canonical +Y / exact hand frame and display',
        'CPU study only: native acceptance pending master']):label(1000,74+i*48,line,18)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/goldtusk.png'))
    triangles=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    labels=['RAW FBX / UNDYED ALBEDO','CANONICAL /151 CUBOIDS / READ ONLY',f'NEW /{len(model["elements"])} SOLID CUBOIDS']
    for row,cam in enumerate(([1,0,0],[.70,.13,.70])):
        yy=500+row*785
        for col,ts in enumerate(triangles):
            label(col*w+10,yy-28,labels[col],17)
            im,_=H['render'](ts,cam,H['frame'](points,cam,w,h),(w,h),raw=col==0);sheet.paste(im,(col*w,yy))
    # Close view resolves the guard/pommel section and the stepped cutting bevel.
    cam=[.8,.08,.60];extent=H['frame'](points[points[:,1]<11.1],cam,600,360)
    for col,ts in enumerate(triangles):
        im,_=H['render'](ts,cam,extent,(600,360),raw=col==0);sheet.paste(im,(col*w,2070))
    label(20,2440,'Matched cameras/scales. Offline geometry/paint evidence only; pack, first/third-person, swing, guard and10-20 display PENDING.',17)
    return png(sheet)

def review_text(d,counts):
    return f"""# Goldtusk W141

{len(d['parts'])} authored solid cuboids / {len(d['parts'])*6} opaque faces / zero triangle adapter elements. Full-only candidate. Groups: {counts}. No source mesh-island conversion, voxel cover, alpha side skins or count-padding surface screws. The new blade is an authored arc made from long filled dark shoulders, narrower pale bevels and physically thin cutting edges; tip spans taper and turn toward the characteristic curved point. Five small heel serrations affect silhouette; diagonal blade etchings stay in UV. The gold hilt has a continuous solid palm, substantial chamfered side masses, recessed black channel, swept guard and hooked pommel.

Default appearance evidence: `/tmp/destiny-weapons-w31/references/goldtusk.jpg`, Bungie item3371413057, SHA408bd019f7dceffeeb4e067e509cf0aa76dcd43e64bcbf92aa5dc53944dd5524. Palette follows its charcoal blade, warm pale cutting bevel, gold frame and black grip. The 1024 RGBA atlas is entirely opaque and independently painted per face, with two-pixel extruded gutters. No ripped diffuse sampling occurs in the candidate paint. Reference-matched shallow diagonal etchings, paired guard bands, hilt channels, limited fastener marks and fine grip weave are paint rather than geometry. There are no invented runes or gun parts. The source diffuse is used only in the explicitly undyed raw comparison column.

Source provenance: all8 objects /3048 triangles from the inert Goldtusk FBX, with every W30 input hash checked. Source thin axis is Y; correct mapping is `anchor + scale * [-raw.Y, raw.Z, raw.X]`, unlike the other sword examples. FBX local rotation[-90,0,0], scale100, no local translation. All six transformed bounds agree with W30 within2e-6. Canonical hand anchor[8,5.213769490183353,8], scale26.632478432940058, +Y blade and exact display are retained. Canonical item select/condition variants, W140 swordframe carry, animation/audio/gameplay and shared W123 manifest remain untouched. Master owns registration/integration; no new split reload assets.

`comparison.png` includes the actual default screenshot plus same-scale side, oblique and hilt-close views of raw source, canonical151 and new candidate. `inspection.bbmodel` embeds the exact atlas with editable semantic groups, face UVs and canonical display; it was created as a file without opening shared DCC tools. Curve/faceted pommel and static reflectance remain approximations. Offline CPU images do not prove native rendering, hand placement during movement, animation or performance.

Pending master: pack integration/load, DCC visual review, representative first/third-person ready/carry/attack/guard/inspect, unchanged native swordframe pose and grip, native audio/animation/server behavior and short10-20 item display observation. No DCC, Vision, CU, Minecraft or server tool was used by this worker.
"""

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    assert len(model['elements'])<=1000
    assert len({e['name'] for e in model['elements']})==len(model['elements'])
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='goldtusk',revision='W141',family='sword',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],coordinate_policy=d['coordinate_policy'],
        canonical_display_exact=True,full_only=True,existing_generic_handling_unchanged=True,existing_native_swordframe_unchanged=True,combat_audio_timing_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w141/batch.json').read_bytes())
    scope=next(f['owned_paths'] for f in batch['features'] if f['name']=='w141-goldtusk')
    assert len(scope)==10 and set(outputs)<=set(scope)
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
