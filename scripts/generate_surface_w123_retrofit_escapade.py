#!/usr/bin/env python3
"""W136 Retrofit Escapade: authored filled volumes and default-photo face UV.
W154 feed/longitudinal-round correction precedes UV compilation.
Bundled Python -B; inert source parsing and CPU images only. FULL candidate.
"""
import argparse
import base64
from collections import Counter
import copy
import json
import math
from pathlib import Path
import runpy
import uuid

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/retrofit_escapade/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/machine_gun/retrofit_escapade.json'
MODEL = ASSET+'models/weapon_surface_w123/retrofit_escapade.json'
TEXTURE = ASSET+'textures/item/weapon/w123/retrofit_escapade.png'
SOURCE = 'art/blockbench/weapons/w30/retrofit_escapade.bbmodel'
HELPER = 'scripts/generate_surface_w123_beloved.py'
REFS = 'art/weapons/w31/references.json'
CATALOG = 'art/weapons/w30/catalog.json'
TEST = 'scripts/qa/test_surface_w123_retrofit_escapade.py'
REPORT = 'docs/qa/2026-10-26/w136/retrofit_escapade-worker.md'
BATCH = 'docs/qa/2026-10-26/w136/batch.json'
RAW = Path('/tmp/destiny-weapons-w30/raw/retrofit_escapade/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/retrofit_escapade.jpg')
EDGE = 1024
H = runpy.run_path(str(ROOT/HELPER))
FACES = H['FACES']
vertices, rotation = H['vertices'], H['rotation']
sha, encode, png = H['sha'], H['encode'], H['png']
PALETTE = dict(teal=[53,89,88], teal_edge=[82,112,108], steel=[108,121,124],
               dark=[30,38,43], recess=[13,20,24], cloth=[118,116,109],
               stitch=[171,169,157], rubber=[28,31,33], copper=[184,106,61],
               brass=[204,149,91], link=[155,164,165], lens=[19,63,69], red=[184,27,19])
OWNED = {str(Path(__file__).relative_to(ROOT)), TEST, REPORT, MODEL, TEXTURE,
         *(ART+n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png'))}
ALBEDO = {'RetrofitEscapadeBody':'13d5fb80_Diffuse.png',
          'RetrofitEscapadeScope':'66d8fb80_Diffuse.png',
          'RetrofitEscapadeAmmo':'74d7fb80_Diffuse.png',
          'FireAndForgetScreen':'a4dafb80_Diffuse.png',
          'FireAndForgetLaser':'a4dafb80_Diffuse.png'}


def source_meshes():
    """Derive basis from this X-long/Y-thin source and test W30 bounds.
    Mesh arrays are reference-only; none are input to make_design's geometry.
    W30's ten selected names include an overlay absent from FBX geometry;
    the FBX contains nine selected objects and 26,031 of 26,147 triangles.
    """
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    for name,digest in meta['source_files'].items():
        assert sha((RAW/name).read_bytes())==digest, 'Source drift: '+name
    roots=H['parse_fbx'](RAW/'Retrofit Escapade.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(p for c,p in links if c==node[1][0]);model=models[mid]
        name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=2e-5)
        assert np.allclose(props['Lcl Scaling'],[100,100,100],atol=1e-6)
        cs={c[0]:c for c in node[2]}
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=raw[:,[1,2,0]]*[-1,1,-1]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0])
        assert np.all((ix<0).reshape(-1,3)==[False,False,True])
        ix=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex'
        assert vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        material=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=ix,uv=uv,material=material))
    ps=np.concatenate([m['vertices'] for m in meshes])
    np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=2e-6)
    assert meta['source_triangles']==26147
    assert sum(len(m['faces']) for m in meshes)==26031
    assert len(meshes)==9 and set(meta['source_objects'])-{m['name'] for m in meshes}=={'79D7FB80_Group7_Index34_17__lod_category_01'}
    return meshes,meta


def make_design(meta):
    parts=[]
    def box(name,lo,hi,mat,group,motif='panel',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:
            e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],x=0,y=0,z=0)
            e['rotation'][turn[0]]=turn[1]
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='panel',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(pos,size)],
            [round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
    def tube(name,x,y,z0,z1,r,t,mat,group,motif='ring',facets=range(8)):
        for i in facets:
            a=i*45;q=math.radians(a);rr=r-t/2
            c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.012,t,z1-z0],mat,group,motif,('z',a))
    # Broad load-bearing receiver; the quilted wrap is a full-depth shoulder.
    box('receiver_core',[7.15,10.16,-.1],[8.85,11.86,8.95],'teal','receiver','receiver')
    box('receiver_upper_rail',[7.15,12.40,-.1],[8.85,12.67,8.95],'teal','receiver','receiver')
    box('receiver_forward_shoulder',[7.15,11.84,-.1],[8.85,12.44,2.57],'teal','receiver','receiver')
    box('receiver_rear_shoulder',[7.15,11.84,4.95],[8.85,12.44,8.95],'teal','receiver','receiver')
    box('lower_chassis',[7.35,9.98,-2.7],[8.65,10.67,9.62],'dark','receiver','chassis')
    box('receiver_wrap',[7.02,11.82,-2.75],[8.98,13.06,1.65],'cloth','wrap','quilt')
    c('wrap_front_slope',[8,12.39,-3.00],[1.92,1.15,.70],'cloth','wrap','quilt',('x',-32))
    c('wrap_rear_band',[8,12.45,1.60],[2.06,1.41,.44],'cloth','wrap','seam')
    # Front sleeve has an actual horizontal slot, not black painted alpha.
    box('forebody_upper',[7.24,12.03,-7.83],[8.76,13.03,-2.65],'teal','forebody','forebody')
    box('forebody_lower',[7.24,11.03,-7.83],[8.76,11.40,-2.65],'teal','forebody','forebody')
    box('forebody_slot_rear',[7.24,11.15,-4.18],[8.76,12.08,-2.65],'teal','forebody','forebody')
    c('forebody_nose_upper',[8,12.43,-7.90],[1.56,.48,.64],'teal_edge','forebody',turn=('x',-18))
    c('forebody_nose_lower',[8,10.96,-7.89],[1.56,.36,.64],'teal_edge','forebody',turn=('x',18))
    # Iconic open fork: two long solids and their side lips, separated by air.
    box('upper_fork',[7.40,13.03,-12.526633583091776],[8.60,13.18,-3.13],'steel','fork','fork')
    for side in (-1,1):
        c(f'upper_fork_lip_{side}',[8+side*.58,13.21,-7.72],[.12,.18,9.32],'dark','fork','fork_edge')
    box('lower_fork',[7.32,10.16,-12.48],[8.68,10.40,-4.02],'steel','fork','fork')
    for side in (-1,1):
        c(f'lower_fork_lip_{side}',[8+side*.64,10.58,-8.25],[.12,.46,8.45],'dark','fork','fork_edge')
    box('fork_heel',[7.31,10.31,-4.20],[8.69,10.76,-2.72],'dark','fork','chassis')
    # Slim barrel sits on the lower channel and is open at the muzzle.
    tube('barrel',8,10.74,-12.12,-3.85,.21,.11,'dark','barrel','barrel')
    tube('muzzle_collar',8,10.74,-12.31,-11.93,.28,.12,'steel','barrel')
    for z in (-9.92,-5.02,-.75):
        c('rod_clamp_'+str(z),[7.10,10.65,z],[.60,.80,.24],'dark','foregrip','chassis')
    c('side_guide_rod',[6.89,10.78,-4.83],[.13,.13,11.40],'teal_edge','foregrip','barrel')
    # Lower support, broad palm surface and right-hand grip in native frame.
    box('foregrip_body',[7.10,9.10,-3.00],[8.90,10.19,.23],'dark','foregrip','grip')
    box('foregrip_insert',[7.02,9.25,-2.77],[8.98,9.91,.02],'teal','foregrip','palm')
    c('foregrip_rear_sweep',[8,9.35,.53],[1.67,1.05,1.0],'teal','foregrip',turn=('x',-40))
    c('grip_neck',[8,9.72,8.16],[.82,.71,1.03],'dark','grip','grip')
    c('pistol_grip',[8,8.54,8.49],[.62,2.34,.74],'rubber','grip','grip',('x',-24))
    c('grip_heel',[8,7.49,8.98],[.73,.23,.81],'dark','grip','grip',('x',-12))
    box('guard_front',[7.67,7.51,6.65],[8.33,10.01,6.93],'teal','guard','panel')
    c('guard_floor',[8,7.48,7.78],[.66,.23,2.12],'teal','guard',turn=('x',-3))
    c('trigger',[8,9.64,7.50],[.15,.98,.18],'steel','guard',turn=('x',-21))
    # Rear stock: upper/lower rails frame a real through-cutout.
    box('stock_neck',[7.42,10.21,8.77],[8.58,12.24,10.05],'dark','stock','chassis')
    box('stock_upper',[7.53,11.78,9.85],[8.47,12.36,14.14],'cloth','stock','seam')
    box('stock_lower',[7.48,10.38,9.79],[8.52,10.98,14.16],'dark','stock','stock')
    box('stock_heel',[7.42,10.10,13.62],[8.58,12.19,14.20],'teal','stock','stock')
    box('stock_butt',[7.36,9.90,14.13],[8.64,12.26,14.473366416908222],'rubber','stock','butt')
    c('stock_inner_sweep',[8,11.32,13.29],[.94,.23,1.04],'teal','stock',turn=('x',-38))
    # Off-center drum with filled center and eight circumference facets.
    # Its axis is X, not the rifle bore. Every face is opaque; no side discs.
    c('drum_solid_core',[6.52,8.47,3.92],[3.55,2.44,2.44],'dark','drum','drum')
    for i in range(8):
        a=i*45;q=math.radians(a);rr=1.41
        c(f'drum_outer_{i}',[6.52,8.47+rr*math.cos(q),3.92+rr*math.sin(q)],
          [3.55,.62,1.46],'steel','drum','drum',('x',a))
    c('drum_feed_neck',[6.43,10.03,3.92],[2.26,1.12,1.75],'dark','drum','chassis')
    # W154: linked muzzleward rounds are authored by correct_parts below.
    # Sighting assembly: saddle, filled hood walls, recessed opaque lenses.
    c('optic_saddle',[8,12.82,4.48],[1.35,.44,4.74],'cloth','optic','seam')
    tube('optic_hood',8,13.52,2.90,6.49,.65,.20,'cloth','optic','optic')
    c('objective_lens',[8,13.52,3.16],[.77,.77,.10],'lens','optic','lens')
    c('ocular_lens',[8,13.52,6.24],[.70,.70,.09],'lens','optic','lens')
    tube('ocular_rim',8,13.52,6.42,6.70,.61,.17,'teal','optic','ring')
    # Small top loop: real open air, rather than an alpha decal.
    for side in (-1,1):
        c(f'optic_loop_ear_{side}',[8+side*.31,14.34,5.66],[.13,.64,.18],'teal','sight')
    c('optic_loop_top',[8,14.61,5.66],[.64,.12,.18],'teal','sight')
    c('front_sight_base',[8,10.94,-11.52],[.62,.22,.40],'dark','sight')
    c('front_sight_post',[8,11.27,-11.52],[.13,.56,.17],'steel','sight','sight')
    # Charging handle and photographed laser module, both static full-model.
    c('charging_handle',[9.05,11.95,3.73],[.86,.26,1.53],'steel','receiver','chassis')
    c('laser_module',[6.73,12.54,7.25],[.88,.57,1.24],'dark','laser','module')
    c('laser_aperture',[6.73,12.54,6.59],[.24,.24,.10],'red','laser','laser')
    # No floating alpha laser beam: omit source effect plane honestly.
    from fix_belt_feed_w154 import correct_parts
    feed_w154=correct_parts('retrofit_escapade',{'full':parts})
    inputs=[BASE,SOURCE,HELPER,REFS,CATALOG,ASSET+'textures/item/weapon/w30/retrofit_escapade.png',TEST]
    rawfiles=[PHOTO,RAW/'Retrofit Escapade.fbx',RAW/'Retrofit Escapade.blend',
              *[RAW/'Textures'/f for f in sorted(set(ALBEDO.values()))]]
    ref=next(x for x in json.loads((ROOT/REFS).read_bytes()) if x['id']=='retrofit_escapade')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    cat=next(x for x in json.loads((ROOT/CATALOG).read_bytes()) if x['id']=='retrofit_escapade')
    assert cat['family']=='machine_gun' and cat['frame']=='rapid_fire'
    return dict(id='retrofit_escapade',revision='W154',belt_feed_w154=feed_w154,family=cat['family'],frame=cat['frame'],
        method='authored semantic opaque cuboids, no source-island/voxel conversion',source=meta,
        coordinate_policy=dict(mapping='[8-raw.Y*s,8+raw.Z*s,8-raw.X*s]',muzzle='-Z',
                               anchor=meta['anchor'],scale=meta['scale'],display='canonical exact'),
        default_photo=ref,palette=PALETTE,parts={'full':parts},
        atlas=dict(size=EDGE,gutter=2,texels_per_unit=21),
        source_object_note='W30 lists 10 objects; overlay 79D7FB80_Group7_Index34_17__lod_category_01 is absent from FBX. Nine retained FBX meshes contain 26031 triangles (116 fewer than W30) and match all six bounds.',
        identity=['long open fork and lower bore','teal chassis with quilted gray wrap',
                  'hooded optic / open stock and guard','side drum and copper feed belt'],
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['Native 26.3 parser/pack/held/third-person/ADS/reload and 10-20 displays pending master.',
                     'Static authored default-photo colors; not original PBR, dye, cloth simulation or dynamic laser emission.',
                     'Complex sculpted curvature and very small markings simplified; optic lenses are opaque recessed color.',
                     'Source laser beam/glow effect planes are omitted; the red module aperture is opaque static color.',
                     'FBX is one overlay object short of W30 names, with 116 fewer triangles than W30; all six bounds match.'])


def face_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    """Continuous world-space motifs across faces; six distinct UV rectangles.
    No source image reprojection, stochastic noise or alpha silhouette paint.
    """
    e=spec['geometry'];u,v,q=face_points(e,face,w,h);mat=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb*=(.97+.055*np.exp(-((v-.28)/.40)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    if motif not in ('optic','ring','barrel'):
        rgb[edge<.8]*=.71;rgb[(edge>=.8)&(edge<1.6)]*=1.16
    side=face in ('east','west');yy=q[:,:,1];zz=q[:,:,2];xx=q[:,:,0]
    world_side=abs((rotation(e.get('rotation',{}))@np.asarray(H['NORMALS'][face]))[0])>.55
    if motif=='quilt':
        # Photo's broad diagonal diamonds, running continuously over shoulder.
        a=(zz+yy)*1.22;b=(zz-yy)*1.22
        da=abs(np.mod(a+.5,1)-.5);db=abs(np.mod(b+.5,1)-.5)
        seam=np.minimum(da,db)
        rgb*=(.72+.30*np.minimum(seam/.13,1))[:,:,None]
        stitch=(seam<.018)&(np.mod((a+b)*6,1)<.65)
        rgb[stitch]=PALETTE['stitch']
        rgb[(edge<3)&(edge>1.8)]*=1.20
    if motif in ('seam','optic'):
        if motif=='seam':rgb[(edge>2)&(edge<3.2)]*=.70
        if motif=='optic' and world_side:
            # Observed tally crosses on rear hood; no invented lettering.
            for z in (5.12,5.40,5.68,5.96):
                for y in (13.22,13.49,13.76):
                    line=((abs(zz-z)<.021)&(abs(yy-y)<.105))|((abs(yy-y)<.021)&(abs(zz-z)<.092))
                    rgb[line]=PALETTE['stitch']
    if motif in ('forebody','receiver') and side:
        rgb[(abs(yy-11.55)<.024)&(zz>-.05)]*=.60
        if face=='west':
            # restrained warm edge tint from the default teal paint/photo.
            tint=np.clip((12.2-yy)/2,0,.35)
            rgb[:,:,0]+=tint*40
        if motif=='receiver':
            for z in (6.25,6.58,6.91,7.24):
                rgb[(abs(zz-z)<.072)&(yy>10.5)&(yy<11.15)]=PALETTE['recess']
    if motif=='fork':
        rgb*=(.95+.04*np.sin(zz*1.4))[:,:,None]
        if face in ('up','down'):
            # Photo's large hooked geometric cut-in marks, painted not holes.
            for z in (-6.1,-5.2,-4.3):
                hook=(abs((zz-z)-.7*(xx-8))<.075)&(abs(xx-8)<.44)
                hook|=(abs(zz-z-.30)<.055)&(xx>7.8)&(xx<8.4)
                rgb[hook]=PALETTE['dark']
            rgb[abs(xx-8)>.48]*=.62
    if motif in ('chassis','grip','palm','butt','stock'):
        if motif in ('grip','palm','butt'):
            ribs=np.mod((yy*6 if motif=='grip' else zz*3.2),1)<.20
            rgb[ribs]*=.62
        if motif=='palm' and side:
            rgb[(np.mod(zz*1.8,1)<.20)&(yy<9.65)]*=.55
        if motif=='stock' and side:
            rgb[(yy<10.68)&(np.mod(zz*2.2,1)<.25)]*=.48
    if motif=='drum':
        # Circumference bands use source-axis X; broad end faces remain filled.
        band=(abs(xx-4.86)<.13)|(abs(xx-8.18)<.13)
        rgb[band]=PALETTE['dark']
        if face=='west':
            r=np.hypot(yy-8.47,zz-3.92)
            rgb[r<1.14]=PALETTE['dark'];rgb[(r>1.13)&(r<1.20)]=PALETTE['teal_edge']
        if face in ('up','north','south'):
            rgb[(abs(xx-6.5)<.75)&(edge>4)]*=.83
    if motif in ('round','bullet'):
        rgb*=(.83+.25*np.exp(-((v-.32)/.21)**2))[:,:,None]
        if motif=='round':
            rgb[(zz>4.29)&(zz<4.51)]=PALETTE['link']
            rgb[(zz>4.70)&(zz<4.78)]=PALETTE['brass']
    if motif=='links':rgb[np.mod(yy*2.1,1)<.25]*=.60
    if motif=='lens':
        r=np.hypot(u-.5,v-.5);rgb*=(.62+.50*np.clip(r*2,0,1))[:,:,None]
        rgb[(r>.39)&(r<.46)]=PALETTE['teal_edge']
    if motif=='laser':
        r=np.hypot(u-.5,v-.5);rgb[r>.38]=PALETTE['dark'];rgb[r<.15]=[241,69,34]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_models(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,255));tiles=[]
    for spec in d['parts']['full']:
        e=spec['geometry'];v=vertices(e)
        for f,ix in FACES.items():
            p=v[list(ix)];w=max(5,math.ceil(np.linalg.norm(p[1]-p[0])*21));h=max(5,math.ceil(np.linalg.norm(p[3]-p[0])*21))
            tiles.append((spec,f,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2;row=0;uvmap={};islands=[]
    for s,f,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('UV atlas overflow')
        im=tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.asarray(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvmap[(s['geometry']['name'],f)]=[q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=s['geometry']['name'],face=f,rect=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    es=[]
    for s in d['parts']['full']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES};es.append(e)
    model=dict(credit='W136 Retrofit Escapade / authored filled semantic volumes / default-photo face paint',
               textures={'0':'destiny:item/weapon/w123/retrofit_escapade','particle':'destiny:item/weapon/w123/retrofit_escapade'},
               elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    d['atlas'].update(islands=islands,used_height=y+row+2)
    return atlas,model


def inspection(d,model,atlas):
    def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w136:retrofit_escapade:'+n))
    es=[];out={};groups={s['geometry']['name']:s['group'] for s in d['parts']['full']}
    for e in model['elements']:
        b=copy.deepcopy(e);r=b.pop('rotation',{})
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():f['texture']=0;f['uv']=[q*EDGE/16 for q in f['uv']]
        es.append(b);out.setdefault(groups[e['name']],[]).append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Retrofit Escapade W136 / offline inspection',
        resolution={'width':EDGE,'height':EDGE},elements=es,
        outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=ids,export=True) for g,ids in out.items()],
        textures=[dict(name='retrofit_escapade.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=model['display'],destiny_w136=dict(nativeAccepted=False,fullOnly=True,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],rotationOrder='RzRyRx'))


def source_triangles(meshes):
    textures={m:np.asarray(Image.open(RAW/'Textures'/f).convert('RGBA')) for m,f in ALBEDO.items()}
    neutral=np.array([[[83,106,110,255]]],np.uint8)
    out=[]
    for m in meshes:
        tex=textures.get(m['material'],neutral)
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:out.append((ps,uv,tex,n/length))
    return out


def comparison(d,meshes,atlas,model):
    w,h=900,315;sheet=Image.new('RGB',(2700,1720),'#161e28');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill='#e4e8eb',font_size=size)
    label(22,12,'RETROFIT ESCAPADE / W136 / AUTHORED FILLED VOLUMES + FACE UV / CPU ART ONLY',28)
    photo=Image.open(PHOTO).convert('RGB').crop((260,175,1900,910));photo.thumbnail((1560,360));sheet.paste(photo,(20,53))
    for i,line in enumerate(['DEFAULT PHOTO / teal / gray quilt / black fork / copper belt',
        f'New: {len(model["elements"])} opaque cuboids / FULL candidate',
        'Canonical display + source scale/anchor retained',
        'Native parser / held / ADS / reload / 10-20 displays pending']):label(1490,95+i*62,line,20)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/retrofit_escapade.png'))
    tris=[source_triangles(meshes),H['model_triangles']({'old':old},oldtex),H['model_triangles']({'new':model},atlas)]
    ps=np.concatenate([m['vertices'] for m in meshes])
    for col,title in enumerate(['RAW FBX / neutral albedo + labeled neutral effect materials',f'CANONICAL / {len(old["elements"])} cubes / read only',f'W136 / {len(model["elements"])} filled cuboids / photo paint']):label(col*w+12,420,title,18)
    for row,(title,cam) in enumerate([('SIDE',[-1,0,0]),('FRONT OBLIQUE',[-1,.48,-.60]),('REAR / OPPOSITE',[1,.38,.60])]):
        extent=H['frame'](ps,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,450+row*h));label(col*w+12,458+row*h,title,17)
    for i,(groups,cam,title) in enumerate([({'fork','barrel'},[-.4,.30,-1],'FORK / OPEN BORE'),({'guard','grip','stock'},[-1,.2,.3],'HAND FRAME / THROUGH CUTOUTS'),({'drum','belt'},[-1,.3,-.4],'FILLED DRUM / COPPER BELT'),({'optic','sight'},[-.5,.2,-1],'HOOD / RECESSED LENS')]):
        names={s['geometry']['name'] for s in d['parts']['full'] if s['group'] in groups};es=[e for e in model['elements'] if e['name'] in names]
        points=np.concatenate([vertices(e) for e in es]);im,_=H['render'](H['model_triangles']({'detail':dict(elements=es)},atlas),cam,H['frame'](points,cam,675,230),(675,230))
        sheet.paste(im,(i*675,1400));label(i*675+10,1408,title,17)
    label(22,1640,'Same camera and scale in every full row. Raw FBX only supplies reference; new geometry is authored independently.',19)
    label(22,1673,'Opaque static art: no recovered PBR, shader dye, laser beam or dynamic glow. Native QA pending master; no GUI/DCC touched.',19)
    return png(sheet)


def review_text(d,counts):
    return f'''# Retrofit Escapade W136 — authored art candidate

Default photo visually inspected: `{PHOTO}`; SHA-256 `{d['default_photo']['sha256']}`. Catalogue: machine_gun / rapid_fire, Bungie 3103325054. The default identity is teal chassis, charcoal fork, gray quilted cloth, copper rounds and a large side drum. No alternate ornament paint was mixed in.

{counts['full']} opaque filled cuboids, zero triangle adapters, {counts['combined']} assembled elements (hard cap 1000). Large receiver/forearm/palm/grip and drum core are filled volumes. Long upper and lower fork guards surround real air; the small lower barrel has eight opaque walls and a genuine bore. Stock and trigger guard have physical through-openings. The hood has depth and recessed opaque lenses, and its top loop remains open. Seven static exposed rounds retain outward side depth and copper/brass/silver distinctions. There is no body/magazine split or new moving part: FULL candidate uses the existing generic reload.

1024-square fully opaque atlas; six unique face rectangles per cuboid and two-pixel extruded gutters. Broad world-space diamond quilting, rear optic tally marks, hooked fork motifs, thin vent/stock grooves, feed links, grips and shallow seams are authored UV paint. Material color is interpreted from the actual supplied photo; it is not a source dye/PBR reconstruction. Source laser beam/glow planes are deliberately omitted rather than exported as alpha shells; red aperture is static opaque color.

Source alignment is derived from this weapon: native = [8-raw.Y*s,8+raw.Z*s,8-raw.X*s], s={d['source']['scale']}, anchor [8,8,8]. Raw X is length, Y is width, Z is height; +raw X muzzle maps to native -Z. FBX model properties are -90 degrees X / 100 scale, with vertices in exported coordinates. This mapping independently reproduces all six W30 native bounds. The nine selected FBX meshes contain 26,031 triangles versus 26,147 in W30. W30 lists ten retained object names but FBX has nine: `79D7FB80_Group7_Index34_17__lod_category_01` is missing. The FBX is 116 triangles short of W30; the missing name and count discrepancy are recorded rather than silently invented. Original .blend/FBX hashes match metadata; no source script or DCC was executed. The exact canonical display values, native muzzle and stock length endpoints, scale and grip frame are retained. Sculpted curves are simplified, not vertex-identical.

Comparison includes the actual photo, raw FBX (body 13d5fb80, scope/belt 66d8fb80, ammo 74d7fb80, screen/laser a4dafb80 neutral albedo; unsupported effect materials have explicit neutral tint), original 229-cube canonical and authored candidate at shared camera/scale. Raw undyed albedo does not claim default-paint recovery. Side/front/opposite-rear and detail panels are CPU art evidence. The editable inspection BB embeds exactly the exported atlas and all semantic cubes; no unsaved user project was touched.

Targeted Python tests cover count/schema, filled sections and real openings, UV opacity/gutters, display/hand frame, source mapping/hashes, catalogue family, BB parity and exact deterministic outputs. Native 26.3 parser/pack, first/third person, ADS, generic reload, combat/audio timing and 10-20 displays remain pending master. Shared registries/manifests/HUD/runtime and the canonical model are unchanged.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_models(d)
    groups=dict(sorted(Counter(s['group'] for s in d['parts']['full']).items()))
    counts=dict(full=len(model['elements']),triangles=0,combined=len(model['elements']),by_semantic_group=groups)
    assert counts['combined']<=1000
    points=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    manifest=dict(id=d['id'],revision='W136',family=d['family'],frame=d['frame'],counts=counts,
        assembled_elements=counts['combined'],max_assembled_elements=1000,opaque_cuboids=counts['full'],
        triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=6*counts['full'],texture_size=[EDGE,EDGE],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_scale=meta['scale'],source_anchor=meta['anchor'],source_axis=meta['source_axis'],source_triangles=meta['source_triangles'],
        fbx_selected_triangles=sum(len(m['faces']) for m in meshes),fbx_missing_triangles=116,
        source_object_note=d['source_object_note'],canonical_display_exact=True,full_only=True,
        generic_reload_ADS_unchanged=True,native_accepted=False,candidate='FULL ONLY',
        default_photo_sha256=d['default_photo']['sha256'],generator_sha256=sha(Path(__file__).read_bytes()),
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    assert set(outputs)<=OWNED
    from fix_belt_feed_w154 import finish_outputs
    return finish_outputs('retrofit_escapade',outputs,include_comparison)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    feature=next(f for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w136-retrofit_escapade')
    assert set(feature['owned_paths'])==OWNED and len(OWNED)==10
    assert Path(feature['destination']).resolve()==ROOT
    outputs=generate()
    for rel,data in outputs.items():
        dest=ROOT/rel
        if args.verify:assert dest.is_file() and dest.read_bytes()==data,'Regeneration differs: '+rel
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' 7 artifacts; {m["assembled_elements"]} opaque cuboids / {m["emitted_faces"]} faces / FULL only; native pending')


if __name__=='__main__':main()
