#!/usr/bin/env python3
"""W131 Lonesome: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/lonesome/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sidearm/lonesome.json'
MODEL = ASSET + 'models/weapon_surface_w123/lonesome.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/lonesome.png'
REPORT = 'docs/qa/2026-10-26/w131/lonesome-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/lonesome/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/lonesome.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(steel=[99,104,100], edge=[143,151,144], graphite=[50,55,53], recess=[19,26,25], rubber=[28,31,29], bronze=[111,99,78], bronze_edge=[146,129,96], copper=[108,66,44], brass=[153,119,65], core=[53,84,80])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w131:lonesome:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/lonesome.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Lonesome.fbx').read_bytes())==meta['source_files']['Lonesome.fbx']
    roots=H['parse_fbx'](RAW/'Lonesome.fbx')
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
        v=np.array(cs['Vertices'][1][0]).reshape(-1,3)[:,[1,2,0]]*meta['scale']; v[:,2]*=-1; v+=meta['anchor']
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
            axis,angle=turn; e['rotation']=dict(origin=[round((a+b)/2,6) for a,b in zip(lo,hi)],axis=axis,angle=angle)
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def center(name,c,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,6) for a,b in zip(c,size)],[round(a+b/2,6) for a,b in zip(c,size)],mat,group,motif,turn)
    def tube(name,x,y,z0,z1,r,t,mat,group):
        for i in range(8):
            a=i*45; q=math.radians(a);cr=r-t/2
            size=[2*r*math.tan(math.pi/8)+.015,t,z1-z0]
            turn=None
            if a%90==0:
                if a%180:size=[size[1],size[0],size[2]]
            else:turn=('z',45 if i%4==1 else -45)
            center(f'{name}_{i}',[x-cr*math.sin(q),y+cr*math.cos(q),(z0+z1)/2],size,mat,group,'ring',turn)
    def beam(name,x,y0,z0,y1,z1,w,mat,group,motif='plain'):
        length=math.hypot(y1-y0,z1-z0);angle=-math.degrees(math.atan2(y1-y0,z1-z0))
        if abs(angle)>90: angle=angle-180 if angle>0 else angle+180
        center(name,[x,(y0+y1)/2,(z0+z1)/2],[w,w,length],mat,group,motif,('x',angle))
    # Wide solid lower receiver, long load-bearing underlug and rear action.
    box('lower_receiver',[7.40,11.32,-1.43],[8.60,12.48,6.67],'steel','receiver','panel')
    box('underlug',[7.31,11.28,-1.30],[8.69,12.30,4.90],'graphite','receiver','panel')
    for sign in (-1,1):
        center(f'underlug_bevel_{sign}',[8+sign*.65,12.28,1.70],[.20,.20,6.35],'steel','receiver',turn=('z',45*sign))
    box('action_core',[7.28,12.06,6.25],[8.72,13.52,9.64],'graphite','action','breech')
    box('slide_lower',[7.32,12.35,6.0],[8.68,12.78,10.36],'steel','action','seam')
    box('breech_top',[7.41,14.37,7.15],[8.59,14.69,9.72],'steel','action','seam')
    # Open oval side windows: broad lower/top rims and angled end shoulders.
    for sign in (-1,1):
        x=8+sign*.83
        center(f'breech_lower_{sign}',[x,13.04,8.30],[.28,.30,2.44],'steel','action','seam')
        center(f'breech_upper_{sign}',[x,14.45,8.30],[.28,.28,1.84],'steel','action','seam')
        center(f'breech_front_{sign}',[x,13.68,7.10],[.28,.83,.26],'steel','action','seam')
        center(f'breech_rear_{sign}',[x,13.68,9.50],[.28,.83,.26],'steel','action','seam')
        beam(f'breech_front_arc_{sign}',x,14.08,7.10,14.45,7.45,.28,'steel','action')
        beam(f'breech_rear_arc_{sign}',x,14.45,9.18,14.08,9.50,.28,'steel','action')
    # Real dark breech opening under top bridge. Recessed back, no painted cap at rim.
    box('breech_back',[7.50,13.19,9.26],[8.50,14.38,9.40],'recess','action')
    box('breech_floor',[7.48,13.12,7.08],[8.52,13.36,9.11],'steel','action')
    # Long barrel with real front bore, shallow wear is face paint.
    tube('barrel',8,13.54,-4.28,-1.10,.58,.17,'bronze','muzzle')
    tube('muzzle_lip',8,13.54,-4.30,-4.10,.63,.19,'steel','muzzle')
    center('barrel_back',[8,13.54,-1.06],[.86,.86,.18],'recess','muzzle')
    tube('front_clamp',8,13.54,-1.92,-1.39,.88,.18,'steel','clamps')
    tube('rear_collar',8,13.68,5.98,6.52,.91,.18,'copper','clamps')
    for sign in (-1,1):
        x=8+sign*.83
        beam(f'front_clamp_sweep_{sign}',x,12.92,-1.78,11.99,-1.16,.24,'steel','clamps')
        beam(f'front_clamp_heel_{sign}',x,11.99,-1.16,11.97,-.40,.24,'steel','clamps')
    # Filled bronze heat-shield rails, with actual large slots between rails/core.
    # Tiny floral perforations are static dark recessed UV, not claimed through-bores.
    box('shield_roof',[7.49,14.42,-1.42],[8.51,14.62,5.98],'bronze','shield','flowers')
    box('shield_floor',[7.49,12.94,-1.42],[8.51,13.17,5.98],'bronze','shield','flowers')
    for sign in (-1,1):
        box(f'shield_upper_{sign}',[8+sign*.58-.085,14.06,-1.35],[8+sign*.58+.085,14.46,5.90],'bronze_edge','shield','flowers')
        box(f'shield_lower_{sign}',[8+sign*.58-.085,12.98,-1.35],[8+sign*.58+.085,13.37,5.90],'bronze_edge','shield','flowers')
    box('recessed_core',[7.72,13.28,-1.14],[8.28,14.23,5.87],'core','shield','core')
    box('shield_rear_post',[7.35,12.78,5.72],[8.65,14.64,6.13],'graphite','shield','seam')
    # Distinctive diagonal external brace is structural, thick and separate.
    for sign in (-1,1):
        x=8+sign*.91
        beam(f'brace_long_{sign}',x,12.62,-1.44,14.30,5.94,.27,'bronze','brace','scrape')
        beam(f'brace_rear_{sign}',x,14.30,5.94,12.02,6.75,.29,'bronze','brace','scrape')
        beam(f'brace_heel_{sign}',x,12.02,6.75,11.88,5.90,.32,'steel','brace','knurl')
    # Grip retains source/native hand frame, broad filled core + dark side panels.
    center('grip_core',[8,9.44,8.81],[1.25,6.15,1.66],'graphite','grip','rib',('x',-10))
    for sign in (-1,1):
        center(f'grip_panel_{sign}',[8+sign*.68,9.56,9.01],[.16,5.52,1.69],'rubber','grip','grain',('x',-10))
    center('grip_backstrap',[8,9.36,9.80],[1.30,5.85,.29],'steel','grip','seam',('x',-10))
    center('grip_frontstrap',[8,9.35,7.83],[1.14,5.86,.32],'graphite','grip','rib',('x',-10))
    center('heel',[8,6.48,9.25],[1.47,.51,2.35],'steel','grip','seam',('x',-10))
    center('heel_lower',[8,6.26,9.34],[1.25,.25,1.95],'graphite','grip',turn=('x',-10))
    # Open curved guard: several substantial sections rather than flat outline sheets.
    beam('guard_front',8,11.40,4.81,10.46,4.65,.25,'steel','guard')
    beam('guard_front_lower',8,10.46,4.65,9.82,5.08,.25,'steel','guard')
    beam('guard_bottom',8,9.82,5.08,9.64,5.95,.25,'steel','guard')
    beam('guard_rear_lower',8,9.64,5.95,10.03,6.69,.25,'steel','guard')
    beam('guard_rear',8,10.03,6.69,11.29,7.13,.25,'steel','guard')
    beam('trigger_upper',8,11.33,6.52,10.62,6.29,.15,'edge','trigger')
    beam('trigger_tip',8,10.62,6.29,10.35,5.98,.15,'edge','trigger')
    box('front_sight_base',[7.62,14.65,-1.34],[8.38,14.82,-.70],'steel','sight')
    box('front_sight_blade',[7.92,14.79,-1.18],[8.08,15.06,-.84],'graphite','sight','dot')
    box('rear_sight_base',[7.46,14.63,8.37],[8.54,14.82,9.04],'graphite','sight')
    for sign in (-1,1):
        box(f'rear_sight_wing_{sign}',[8+sign*.43-.13,14.78,8.44],[8+sign*.43+.13,15.08,8.98],'steel','sight')
    for sign in (-1,1):
        for i,(yc,zc) in enumerate(((13.78,5.58),(13.57,9.46))):
            center(f'bronze_pivot_{sign}_{i}',[8+sign*1.04,yc,zc],[.13,.37,.37],'brass','controls','bolt',('x',45))
    box('slide_stop',[8.72,12.13,7.14],[8.95,12.50,8.43],'graphite','controls','knurl')
    box('rear_latch',[7.57,12.52,9.67],[8.43,12.78,10.59],'copper','controls','seam')
    files=[BASE,'art/blockbench/weapons/w30/lonesome.bbmodel','art/weapons/w31/references.json']
    rawfiles=[PHOTO,RAW/'Lonesome.fbx',RAW/'Lonesome_Diffuse.dds',RAW/'LonesomeShell_Diffuse.dds']
    return dict(id='lonesome',stage='W131',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='[8+raw.Y*s,8+raw.Z*s,8-raw.X*s]',muzzle='-Z',display='canonical exact'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['tiny quatrefoil flowers are opaque recessed artwork, not individual through-holes','static matte interpretation, not PBR or emissive shader recovery','generic reload, native held/ADS and20 displays pending'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];e=spec['geometry'];u,v,q=world_points(e,face,w,h)
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.96+.05*np.exp(-((v-.30)/.35)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.65]*=.72;rgb[(edge>=.65)&(edge<1.3)]*=1.12
    side=face in ('east','west')
    if motif=='flowers' and side:
        # Same source quatrefoil band, resampled into clean long continuous UVs.
        raw=Image.open(RAW/'LonesomeShell_Diffuse.dds').convert('RGBA')
        band=np.asarray(raw.crop((45,51,329,89)).resize((w,h),Image.Resampling.LANCZOS))
        # Source black petals are recess paint; all exported face samples remain opaque.
        lum=band[:,:,:3].mean(2)/255;rgb*=np.clip(.45+lum*.86,.22,1.22)[:,:,None]
    if motif in ('grain','rib'):
        if motif=='grain':
            line=np.sin(q[:,:,1]*3+q[:,:,2]*27+np.sin(q[:,:,1]*9)*.55);rgb*=(.98+.045*line)[:,:,None]
        else:rgb[np.mod(q[:,:,1]*6,1)<.22]*=.65
    if motif in ('panel','breech','seam') and side:
        # Shallow seam and a few source-backed fasteners are texture, not dozens of bolts.
        rgb[(v>.14)&(v<.17)&(u>.10)&(u<.90)]*=.66
        for uc,vc in ((.12,.24),(.87,.77)):
            r=np.hypot((u-uc)*w,(v-vc)*h);radius=min(w,h)*.06
            rgb[r<radius]=PALETTE['graphite'];rgb[(r>radius*.66)&(r<radius)]=PALETTE['edge']
    if motif=='knurl':rgb[(np.mod(u*17,1)<.19)&(v>.1)&(v<.9)]*=.62
    if motif=='core':
        rgb*=(.84+.12*np.cos(q[:,:,2]*3))[:,:,None]
    if motif=='scrape':rgb[(v<.08)|(v>.93)]*=1.13
    if motif=='bolt' and side:
        r=np.hypot(u-.5,v-.5);rgb[r<.34]*=1.15;rgb[(r>.34)&(r<.42)]*=.60
    if motif=='dot' and face=='south':rgb[(abs(u-.5)<.16)&(abs(v-.5)<.16)]=[183,189,158]
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
    model=dict(credit='Lonesome W131 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/lonesome','particle':'destiny:item/weapon/w123/lonesome'},
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
        name='Lonesome W131 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='lonesome.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w131=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    result=[];textures={}
    for m in meshes:
        mat=m['material']
        if mat not in textures:
            textures[mat]=np.asarray(Image.open(RAW/(mat+'_Diffuse.dds')).convert('RGBA')) if (RAW/(mat+'_Diffuse.dds')).exists() else np.array([[[45,65,61,255]]],np.uint8)
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((t,uv,textures[mat],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=850,420;sheet=Image.new('RGB',(2550,1860),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,14,'LONESOME / W131 / SOLID SEMANTIC VOLUMES + AUTHORED FACE UV',29)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((900,470));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / full model only',
        'Muted steel + bronze shield + dark striated grip',
        'Real bore / large rail slots / breech / guard / sight',
        'Quatrefoil small petals = opaque source-backed recess paint',
        'Native display/ADS/generic reload unchanged',
        'Original frame: [8+raw.Y*s,8+raw.Z*s,8-raw.X*s]',
        'Offline CPU art comparison; native pending']):label(1000,100+i*48,line,24)
    label(20,550,'RAW FBX / UNDYED DIFFUSE / CORE NEUTRAL',22);label(w+20,550,'OLD CANONICAL / 236 CUBOIDS / READ ONLY',22);label(w*2+20,550,f'NEW SEMANTIC SOLIDS / {len(model["elements"])} CUBOIDS',22)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/lonesome.png'))
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT OBLIQUE',[1,.4,-.62]),('REAR OBLIQUE',[-1,.3,.6])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,590+row*h));label(col*w+15,598+row*h,name,18)
    return png(sheet)


def review_text(d,counts):
    return f"""# Lonesome W131 — master art

{len(d['parts'])} opaque semantic cuboids, filled broad receiver and grip, true bore, open guard and sight, real rail slots, thick separate diagonal brace. Quatrefoil tiny petals are source-backed opaque recess UV, not claimed through holes. Muted steel/bronze/dark grip from actual W31 default photo; raw diffuse neutral fields are not default dye. Hand-authored face UV on1024 atlas, no alpha body shells/triangles/source-island transplant.

Actual raw FBX22805 triangles parsed read-only in original source frame; canonical display/anchor/scale/generic reload/ADS/timing/audio unchanged. Static matte color interpretation; no original PBR/reflection/emissive recovery. Side/front/rear CPU comparisons are not native success. Master targeted tests and actual Blockbench review recorded separately. Native pack/client/held/ADS/reload/20display pending.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='lonesome',revision='W131',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
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
    outputs=generate();scope=json.loads((ROOT/'docs/qa/2026-10-26/w131/scope.json').read_bytes());assert set(outputs)<=set(scope['owned_paths'])
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
