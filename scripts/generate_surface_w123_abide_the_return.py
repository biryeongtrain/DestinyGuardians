#!/usr/bin/env python3
"""W141 Abide the Return: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/abide_the_return/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sword/abide_the_return.json'
MODEL = ASSET + 'models/weapon_surface_w123/abide_the_return.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/abide_the_return.png'
REPORT = 'docs/qa/2026-10-26/w141/abide_the_return-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/abide_the_return/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/abide_the_return.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(gold=[192,160,83], gold_edge=[232,207,139], gold_shadow=[145,111,52],
    silver=[194,196,187], silver_edge=[226,228,217], dark=[29,36,40],
    blue=[52,88,111], binding=[24,35,43], engraving=[96,75,39])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w141:abide_the_return:'+name))


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
    """Read inert FBX arrays; W30 Blend contains coincident .001 duplicates."""
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/abide_the_return.bbmodel').read_bytes())['destiny_w30']
    for name,digest in meta['source_files'].items():
        assert sha((RAW/name).read_bytes())==digest,name
    roots=H['parse_fbx'](RAW/'Abide the Return.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(p for c,p in links if c==node[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=2e-5,rtol=0)
        assert props['Lcl Scaling']==[100,100,100] and props.get('Lcl Translation',[0,0,0])==[0,0,0]
        cs={c[0]:c for c in node[2]}
        v=np.array(cs['Vertices'][1][0]).reshape(-1,3)[:,[0,2,1]]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]);assert np.all((ix<0).reshape(-1,3)==[False,False,True])
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0);vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        mat=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=faces,uv=uv,material=mat))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==['Abide-the-Return.00.000','Abide-the-Return.01.000']
    assert sorted(meta['source_objects'])==sorted([m['name'] for m in meshes]+[m['name'][:-3]+'001' for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
    assert sum(len(m['faces']) for m in meshes)==19304 and meta['source_triangles']==38608
    return meshes,meta


def make_design(meta):
    parts=[]
    def c(name,pos,size,mat,group,motif='metal',turn=None):
        e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
        if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def beam(name,p,q,thick,width,mat,group,motif='metal',x=8,overlap=.035):
        y,z=p;Y,Z=q;angle=math.degrees(math.atan2(Z-z,Y-y))
        c(name,[x,(y+Y)/2,(z+Z)/2],[thick,math.hypot(Y-y,Z-z)+overlap,width],mat,group,motif,('x',angle))
    def collar(name,y,length,r,mat):
        c(name+'_core',[8,y,7.70],[r*1.54,length,r*1.54],mat,'ferrules','ferrule')
        for i,(sx,sz) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
            c(name+'_facet_'+str(i),[8+sx*r*.59,y,7.70+sz*r*.59],[r*.64,length,r*.64],mat,'ferrules','ferrule',('y',45))
    # Authored centerline and width stations, guided by the rip outline and photo.
    # Filled structural cores with thinner cutting margins and thick central spine.
    stations=[(10.65,6.85,8.22),(12.5,6.73,8.18),(15,6.65,8.11),
        (18,6.47,8.00),(20.5,6.24,7.77),(23,6.05,7.54),(25,6.025,7.45),
        (26.7,6.18,7.50),(28,6.43,7.71),(29,6.78,8.02),(30,7.24,8.42),
        (30.7,7.91,8.89),(31.15,8.57,9.28),(31.46,9.30,9.48)]
    for i,(a,b) in enumerate(zip(stations,stations[1:])):
        y,lo,hi=a;Y,LO,HI=b;p=(y,(lo+hi)/2);q=(Y,(LO+HI)/2)
        angle=math.atan2(q[1]-p[1],Y-y)
        width=((hi-lo)+(HI-LO))/2*math.cos(angle)
        thick=.28 if y<20 else (.20 if y<29 else .14)
        beam(f'blade_solid_{i:02}',p,q,thick,width,'gold','blade','blade')
        # Central shoulder is a filled thicker mass, far inside the cutting edge.
        beam(f'blade_shoulder_{i:02}',(y,p[1]+.12),(Y,q[1]+.12),thick+.08,width*.67,'gold','blade','blade')
        beam(f'cutting_margin_{i:02}',(y,lo+.04),(Y,LO+.04),.075,.10,'gold_edge','cutting_edge','edge')
    # Silver back rail grows out of the guard and ends in a separate hooked crest.
    rail=[(9.45,7.75),(10.45,8.14),(11.7,8.42),(13,8.38),(15.6,8.17),(17.5,8.06),(18.8,8.15),(19.65,8.50),(20.02,8.86)]
    for i,(p,q) in enumerate(zip(rail,rail[1:])):
        beam(f'silver_backrail_{i}',p,q,.52 if i<3 else .38,.38 if i<6 else .23,'silver','backrail','silver')
    # Broad silver root and curved opposed quillons; empty hooked throats are real air.
    c('guard_heart',[8,10.14,7.73],[.89,.94,1.10],'silver','guard','guard')
    for name,pts,width in [('lower',[(10.48,7.49),(10.42,6.82),(10.77,6.28),(11.20,6.03)],.28),
                           ('upper',[(9.75,8.01),(10.11,8.47),(10.73,8.62)],.25)]:
        for i,(p,q) in enumerate(zip(pts,pts[1:])):
            beam(f'guard_{name}_{i}',p,q,.53 if i==0 else .38,width,'silver','guard','silver')
    # Hollow eye at rail root: four rim beams, actual open center, never alpha.
    cy,cz=9.80,8.43
    for i,(p,q) in enumerate(zip([(cy-.23,cz-.20),(cy+.23,cz-.20),(cy+.23,cz+.20),(cy-.23,cz+.20)],
                              [(cy+.23,cz-.20),(cy+.23,cz+.20),(cy-.23,cz+.20),(cy-.23,cz-.20)])):
        beam(f'guard_eye_rim_{i}',p,q,.63,.095,'silver','guard','silver')
    # Solid dark blue oval grip: continuous core and four substantial section facets.
    c('grip_core',[8,6.08,7.70],[.72,5.15,.72],'blue','grip','wrap')
    for i,(sx,sz) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
        c(f'grip_facet_{i}',[8+sx*.27,6.08,7.70+sz*.27],[.28,5.15,.28],'blue','grip','wrap',('y',45))
    collar('upper_black_binding',8.63,.36,.49,'dark')
    collar('silver_ferrule',9.08,.51,.57,'silver')
    collar('lower_black_binding',3.52,.30,.43,'dark')
    # Hooked pommel has actual curvature and metal thickness in front/oblique view.
    for i,(p,q,width) in enumerate([((3.42,7.70),(3.02,7.56),.73),((3.02,7.56),(2.77,7.15),.61),
        ((2.77,7.15),(2.70,6.77),.43),((2.70,6.77),(2.86,6.48),.21)]):
        beam(f'pommel_hook_{i}',p,q,.62 if i<2 else .40,width,'silver','pommel','silver')
    # Two real cloth tabs seen at the lower blue binding, no decorative rivet quota.
    beam('binding_tab_a',(4.03,7.65),(3.94,8.29),.12,.15,'binding','grip','wrap',x=8.49)
    beam('binding_tab_b',(4.03,7.63),(4.23,8.08),.11,.16,'binding','grip','wrap',x=8.59)
    files=[BASE,'art/blockbench/weapons/w30/abide_the_return.bbmodel','art/weapons/w31/references.json',
        'src/main/resources/assets/destiny/items/weapon/abide_the_return.json','src/main/resources/destiny/weapons/w30.json','scripts/art/reconstruct_weapons_w30.py',
        'src/main/resources/destiny/animation/sword_w140.animation.json',HELPER]
    rawfiles=[PHOTO]+[RAW/n for n in ('Abide the Return.fbx','Abide the Return.blend','Blade_Diffuse.png','Hilt_Diffuse.png')]
    return dict(id='abide_the_return',stage='W141',family='sword',source=meta,parts=parts,
        palette=PALETTE,blade_stations=stations,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='anchor + scale * [raw.X, raw.Z, raw.Y]',
            fbx_translation_cm=[0,0,0],fbx_rotation_deg=[-90,0,0],fbx_scale=[100,100,100],length='+Y',display='canonical exact',
            validation='two FBX objects /19304 triangles match W30 bounds; W30 Blend records four objects /38608 triangles including .001 duplicates'),
        identity=['curved gold blade','silver hooked guard and shorter backrail','blue cross-bound grip','hooked silver pommel','small heel crest'],
        construction='authored semantic filled cuboids; no source island/voxel conversion; no alpha silhouettes',
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['segmented cuboid curve approximates the smooth original; small surface details are hand-authored face paint',
            'static opaque palette approximates default gold/silver/blue without PBR reflections',
            'offline CPU/BB inspection only; native pack/held/thirdperson/swing/guard/10-20display pending master'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    u,v,q=world_points(spec['geometry'],face,w,h)
    role=spec['material'];motif=spec['motif'];y=q[:,:,1];z=q[:,:,2];x=q[:,:,0]
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    # Hand-authored paint in model coordinates: coherent continuous metal fields.
    rgb*=(.985+.016*np.sin(y*.9+z*1.7))[:,:,None]
    side=face in ('east','west')
    if motif=='blade' and side:
        # Quiet warm polish and a few selected irregular wear strokes, not rip baking.
        rgb*=(.96+.07*np.clip((z-6)/3,0,1))[:,:,None]
        for yy,zz,ll in [(12.8,7.45,.21),(16.2,7.15,.36),(22.3,6.48,.25),(27.6,6.92,.29)]:
            rgb[(abs(y-yy)<ll)&(abs(z-zz-.12*(y-yy))<.018)]*=.68
        # Heel cartouche, stylized small fan-and-diamond crest visible in default photo.
        border=(((abs(y-12.2)<.030)&(abs(z-7.23)<.43))|((abs(y-13.45)<.030)&(abs(z-7.23)<.43))|
                ((abs(z-6.81)<.025)&(y>12.2)&(y<13.45))|((abs(z-7.65)<.025)&(y>12.2)&(y<13.45)))
        rgb[border]=PALETTE['engraving']
        for slope in (-.7,-.35,0,.35,.7):
            fan=(y>12.27)&(y<13.37)&(abs(z-7.23-slope*(y-12.35))<.022)
            rgb[fan]=PALETTE['engraving']
        diamond=(abs(abs(y-13.03)*.8+abs(z-7.22)-.27)<.025)
        rgb[diamond]=PALETTE['gold_edge']
        # Existing three dark half-round fastener seats beneath silver backrail.
        for yy,zz in ((13.8,8.12),(15.55,7.99),(17.35,7.91)):
            r=np.sqrt(((y-yy)*.72)**2+(z-zz)**2)
            rgb[(r<.16)&(z<zz)]=PALETTE['dark']
            rgb[(r<.055)&(z<zz)]=PALETTE['gold_edge']
    if motif=='wrap':
        # Broad crossing blue cloth strands, dark gaps and restrained bright selvedge.
        a=np.mod(y*1.38+(x-8)*.88+(z-7.7)*.88,1)
        b=np.mod(y*1.38-(x-8)*.88-(z-7.7)*.88,1)
        rgb[(a<.16)|(b<.16)]=PALETTE['binding']
        rgb[((a>.17)&(a<.23))|((b>.17)&(b<.23))]=[102,139,160]
        rgb[(a>.24)&(a<.29)]=[72,111,137]
    if motif=='ferrule':
        band=np.mod(y*15,1)
        rgb[band<.22]*=.58
        if role=='silver':rgb[(band>.27)&(band<.34)]*=1.10
    if motif in ('silver','guard') and side:
        # Minimal chased edge and restrained inset guard pivot; no invented lettering.
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<1.0]*=1.08
        if motif=='guard':
            rr=np.sqrt((y-10.22)**2+(z-7.68)**2)
            rgb[(rr>.09)&(rr<.13)]=PALETTE['gold_shadow'];rgb[rr<.075]=PALETTE['dark']
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(28,36,44,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=28
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
    model=dict(credit='Abide the Return W141 authored solid curved blade / default gold silver blue / full only',
        textures={'0':'destiny:item/weapon/w123/abide_the_return','particle':'destiny:item/weapon/w123/abide_the_return'},
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
        name='Abide the Return W141 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='abide_the_return.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w141=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    textures={n:np.asarray(Image.open(RAW/(n+'_Diffuse.png')).convert('RGBA')) for n in ('Blade','Hilt')}
    result=[]
    for m in meshes:
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
            if length>1e-10:result.append((t,uv,textures[m['material']],n/length))
    return result


def comparison(d,meshes,atlas,model):
    w,h=600,710;sheet=Image.new('RGB',(1800,2500),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'ABIDE THE RETURN / W141 / GOLD CURVE + SILVER HOOKS + BLUE BINDINGS',24)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1000,480));sheet.paste(photo,(0,49))
    for i,line in enumerate([f'{len(model["elements"])} filled cuboids / opaque 1024 atlas',
        'Authored continuous blade sections with solid shoulder',
        'Silver backrail / opposed hooks / blue cross binding',
        'FBX: 2 objects,19304 triangles; W30 duplicate total38608',
        'Canonical +Y / hand anchor and display retained',
        'CPU evidence only; native W140 checks pending master']):label(1000,94+i*52,line,17)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/abide_the_return.png'))
    triangles=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    labels=['RAW FBX / UNDYED DIFFUSE','CANONICAL /204 CUBOIDS / READ ONLY',f'NEW /{len(model["elements"])} SOLID CUBOIDS']
    for row,cam in enumerate(([1,0,0],[.73,.10,.68])):
        yy=540+row*750
        for col,ts in enumerate(triangles):
            label(col*w+10,yy-26,labels[col],17)
            im,_=H['render'](ts,cam,H['frame'](points,cam,w,h),(w,h),raw=col==0);sheet.paste(im,(col*w,yy))
    # Third view: opposite-side close-up and edge section, with atlas to inspect paint.
    for col,cam in enumerate(([-1,.08,.45],[.25,.12,1])):
        im,_=H['render'](triangles[2],cam,H['frame'](points,cam,580,410),(580,410))
        sheet.paste(im,(col*600,2060));label(col*600+10,2035,'NEW / OPPOSITE' if col==0 else 'NEW / EDGE SECTION',17)
    thumb=atlas.convert('RGB').resize((410,410));sheet.paste(thumb,(1320,2060));label(1320,2035,'OPAQUE FACE ATLAS',17)
    label(20,2480,'Same camera/scale per main row. Offline inspection only; native pack/held/swing/guard/load pending.',16)
    return png(sheet)


def review_text(d,counts):
    return f"""# Abide the Return W141

{len(d['parts'])} authored filled cuboids / {len(d['parts'])*6} opaque faces, full-only assembly. The gold blade uses meaningful curved structural segments with narrower thicker shoulders and thin cutting margins. Silver guard hooks, shorter hooked backrail and hooked pommel carry real cross-section and parallax. The oval blue grip is solid through the canonical hand frame. No rip connected-component transplant, voxel conversion, alpha silhouette shell, triangle adapter or split reload.

Default evidence: `/tmp/destiny-weapons-w31/references/abide_the_return.jpg`, Bungie item1644160541, SHA e6fb97a1063621ae85bce9f1037be9b76d731d2dd3e2caef73b6b486924dd5c7. Gold blade / pale silver rail, guard and pommel / blue crossing cloth are photo-driven. Each face has an authored continuous UV rectangle with two-pixel extruded gutters in an opaque1024 atlas. Heel crest, dark fastener seats, cloth crossings, ferrule grooves and limited wear are painted by deterministic brush/mask recipes; no source texture pixels are transplanted. The small crest is a simplified fan-and-diamond interpretation, not a claim of exact original engraving recovery.

Local FBX and Blend hashes are verified against W30 metadata. Inert FBX has two objects and19304 triangles; W30 records four objects including .001 duplicates and38608 triangles. Do not mistake the doubled W30 count for four distinct FBX objects. Mapping `anchor + scale * [raw.X,raw.Z,raw.Y]` with zero local translation matches all six W30 bounds within2e-6. Scale{d['source']['scale']}, anchor{d['source']['anchor']}, +Y blade and all eight canonical display contexts are retained. This weapon must not inherit Crown-Splitter's +10cm translation.

Comparison includes the actual default screenshot, matched source/canonical/new side and oblique renders, opposite side, edge view and atlas. The filled curve is deliberately faceted; fine smooth curvature, photographic roughness and dynamic metal reflections remain approximate. Offline views establish authored geometry and paint only. Pack loading, native first/third-person W140 swordframe grip/carry, ADS/inspect, light/heavy swing, guard, audio, server combat and10-20 simultaneous displays remain pending master. The shared manifest/item routing is intentionally untouched and must be integrated by master. W140 native swordframe/gameplay/audio/animation remain unchanged by this delta.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    assert len(model['elements'])<=1000
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='abide_the_return',revision='W141',family='sword',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],coordinate_policy=d['coordinate_policy'],
        canonical_display_exact=True,full_only=True,existing_generic_handling_unchanged=True,combat_audio_timing_unchanged=True,native_accepted=False,fbx_source_triangles=19304,provenance_duplicate_factor=2,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w141/batch.json').read_bytes())
    scope=next(f['owned_paths'] for f in batch['features'] if f['name']=='w141-abide_the_return')
    assert len(scope)==10 and set(outputs)<=set(scope)
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
