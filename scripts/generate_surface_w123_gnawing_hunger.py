#!/usr/bin/env python3
"""W128 Gnawing Hunger: independent semantic solid remodel; full only.
Bundled numpy/Pillow; inert FBX parsing and offline raster helpers are read-only.
"""
import argparse
import base64
import collections
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import uuid
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/gnawing_hunger/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/auto_rifle/gnawing_hunger.json'
BB = 'art/blockbench/weapons/w30/gnawing_hunger.bbmodel'
MODEL = ASSET+'models/weapon_surface_w123/gnawing_hunger.json'
TEXTURE = ASSET+'textures/item/weapon/w123/gnawing_hunger.png'
RAW = Path('/tmp/destiny-weapons-w30/raw/gnawing_hunger/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/gnawing_hunger.jpg')
EDGE = 1024
HELP = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
FACES, NORMALS = HELP['FACES'], HELP['NORMALS']
vertices, rotation = HELP['vertices'], HELP['rotation']
render, frame, model_triangles = HELP['render'], HELP['frame'], HELP['model_triangles']

def sha(b): return hashlib.sha256(b).hexdigest()
def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w128:gnawing_hunger:'+s))

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Gnawing Hunger.fbx').read_bytes())==meta['source_files']['Gnawing Hunger.fbx']
    roots=HELP['parse_fbx'](RAW/'Gnawing Hunger.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects');byid={n[1][0]:n for n in objects if n[1]}
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    meshes=[]
    for g in objects:
        if g[0]!='Geometry':continue
        mid=next(p for c,p in links if c==g[1][0] and byid[p][0]=='Model')
        model=byid[mid];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in g[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        faces=[];face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                for j in range(1,len(face)-1):faces.append([face[0],face[j],face[j+1]])
                face=[]
        ul=next(c for c in g[2] if c[0]=='LayerElementUV')
        vals={c[0]:c[1][0] for c in ul[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        mat=byid[next(c for c,p in links if p==mid and byid[c][0]=='Material')][1][1].split('\x00')[0]
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=mat))
    pts=np.concatenate([m['vertices'] for m in meshes]);assert np.allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-5)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    return meshes,meta

def source_triangles(meshes):
    textures={m:np.array(Image.open(RAW/({'rey':'Ret','Effect':'Effect'}.get(m,m)+('_Main' if m=='Effect' else '_Diffuse')+'.png')).convert('RGBA')) for m in {m['material'] for m in meshes}}
    ts=[]
    for m in meshes:
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:ts.append((ps,uv,textures[m['material']],n/length))
    return ts

# Quiet default paint, from W31 reference photograph and its unchanged dye entry.
# The raw diffuse supplies cloth and quatrefoil artwork, never geometry.
PALETTE = {'steel':[66,69,69], 'edge':[92,95,93], 'black':[29,32,32],
           'rubber':[24,26,26], 'brass':[135,102,60], 'brass_lip':[167,134,84],
           'recess':[13,17,18], 'cloth':[195,197,187], 'cyan':[107,163,158]}

def semantic_geometry():
    specs=[]
    def box(group,name,c,size,mat,motif='',angles=(0,0,0)):
        c=np.array(c,float);sz=np.array(size,float)
        specs.append(dict(group=group,material=mat,motif=motif,geometry=dict(name=group+'/'+name,
            **{'from':(c-sz/2).round(6).tolist(),'to':(c+sz/2).round(6).tolist()},
            rotation=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles))))))
    def beam(group,name,a,b,width,depth,mat,motif=''):
        a=np.array(a,float);b=np.array(b,float);v=b-a;assert abs(v[0])<1e-8
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0))
    def ring(group,name,x,y,z,r,thick,depth,mat):
        # Adjacent tangent staves overlap at corners; the bore stays unfilled.
        for i in range(8):
            a=i*45;t=math.radians(a)
            box(group,f'{name}-{i}',[x+r*math.cos(t),y+r*math.sin(t),z],
                [2*r*math.tan(math.pi/8)+.02,thick,depth],mat,'tube',(0,0,a-90))

    # Long receiver volumes, not source fitted slices or thin side skins.
    box('receiver','core',[8,10.85,5.20],[1.46,1.70,6.34],'steel','receiver')
    box('receiver','upper',[8,11.82,5.25],[1.36,.49,5.60],'steel','receiver')
    beam('receiver','rear-slope',[8,11.73,8.02],[8,11.12,8.72],1.30,.46,'steel','receiver')
    box('receiver','front-seat',[8,11.0,2.02],[1.55,1.75,.44],'steel','receiver')
    box('receiver','lower-rear',[8,10.10,7.75],[1.23,.42,1.10],'black','receiver')
    box('receiver','well',[8,9.68,3.53],[1.43,1.00,2.30],'steel','well')
    box('receiver','well-lower',[8,8.92,3.64],[1.24,.62,1.88],'steel','well')
    beam('receiver','well-release',[8.72,9.43,2.08],[8.72,8.61,1.65],.17,.14,'edge')
    box('receiver','charge-handle',[9.04,11.05,7.56],[.65,.22,.92],'black','receiver')
    box('receiver','rear-button',[8.76,10.46,7.73],[.17,.40,.47],'edge')

    # Octagonal roundings of cloth-wrapped body are formed with four broad
    # shoulders over the solid receiver; the actual binding artwork lives in UV.
    box('bindings','receiver-crown',[8,12.08,4.26],[1.25,.30,4.10],'cloth','binding')
    for side in (-1,1):
        box('bindings',f'receiver-shoulder-{side}',[8+side*.66,11.82,4.26],[.39,.48,4.10],
            'cloth','binding',(0,0,side*35))
        box('bindings',f'receiver-flank-{side}',[8+side*.78,11.18,4.26],[.20,.97,4.10],'cloth','binding')
        beam('bindings',f'loose-overlap-{side}',[8+side*.70,10.80,4.1],[8+side*.70,9.36,5.37],.23,.72,'cloth','binding')
    # Two narrow steel straps interrupt the cloth, as in the default photo.
    for z in (4.25,5.9):
        box('bindings',f'strap-{z}',[8,12.28,z],[1.45,.13,.19],'black','strap')
        for side in (-1,1):
            box('bindings',f'strap-flank-{z}-{side}',[8+side*.89,11.33,z],[.13,1.70,.19],'black','strap')

    # Lateral protective tubular cage, offset from the receiver: air is real.
    for side in (-1,1):
        x=8+side*1.02
        beam('cage',f'lower-rail-{side}',[x,10.02,1.85],[x,10.57,8.77],.17,.18,'edge','tube')
        beam('cage',f'rear-return-{side}',[x,10.57,8.77],[x,11.65,8.77],.17,.18,'edge','tube')
        beam('cage',f'upper-rail-{side}',[x,11.70,2.20],[x,11.38,6.75],.17,.18,'edge','tube')
        beam('cage',f'upper-nose-{side}',[x,11.70,2.20],[x,11.60,1.42],.17,.18,'edge','tube')

    # Skeleton stock: two independently open windows separated by one stile.
    box('stock','comb',[8,11.05,11.91],[1.08,.55,6.45],'black','stock')
    beam('stock','lower-strut',[8,8.32,9.18],[8,7.72,15.02],1.08,.63,'black','stock')
    beam('stock','buttpad',[8,7.25,15.14],[8,11.27,15.14],1.19,.61,'rubber','stock')
    beam('stock','middle-stile',[8,7.74,12.20],[8,10.87,12.20],1.03,.45,'black','stock')
    box('stock','window-roof',[8,10.63,13.60],[1.06,.24,2.48],'black','stock')
    box('stock','rear-web',[8,8.44,13.63],[1.08,1.16,2.77],'black','stock')
    box('stock','window-rear-post',[8,9.88,14.84],[1.08,2.10,.48],'black','stock')
    box('stock','rear-heel',[8,7.35,14.84],[1.18,.27,.74],'rubber','stock')
    for z in (11.05,12.18):
        box('stock',f'steel-band-roof-{z}',[8,11.36,z],[1.14,.10,.15],'edge','strap')
    for side in (-1,1):
        box('stock',f'steel-band-stile-{side}',[8+side*.55,9.45,12.18],[.09,3.25,.18],'edge','strap')

    # Hand contact stays in the W30 grip region; spiral white binding has depth.
    beam('grip','core',[8,9.96,7.82],[8,7.23,8.76],1.08,1.18,'black','grip')
    beam('grip','backstrap',[8,9.85,8.35],[8,7.30,9.30],.99,.21,'rubber','grip')
    beam('grip','heel',[8,7.13,8.34],[8,7.32,9.28],1.14,.25,'black','grip')
    beam('grip','cloth-foundation',[8,9.42,8.02],[8,7.67,8.63],1.16,1.30,'cloth','binding')
    for i,(y,z) in enumerate(((9.13,8.10),(8.10,8.49))):
        box('grip',f'binding-turn-{i}',[8,y,z],[1.20,.36,1.36],'cloth','binding',(-18,0,0))
    beam('trigger','front',[8,9.81,5.56],[8,9.23,5.68],.25,.16,'brass')
    beam('trigger','hook',[8,9.23,5.68],[8,9.05,5.45],.25,.14,'brass')
    beam('trigger','guard-front',[8,9.95,5.05],[8,9.02,5.31],.48,.15,'black')
    beam('trigger','guard-bottom',[8,9.02,5.31],[8,9.02,7.42],.48,.16,'black')
    beam('trigger','guard-rear',[8,9.02,7.42],[8,9.88,7.67],.48,.15,'black')

    # Curved magazine: three broad continuous sections; no moving split invented.
    box('magazine','neck',[8,8.66,3.57],[1.10,.63,1.89],'black','magazine')
    beam('magazine','upper',[8,8.56,3.61],[8,7.33,3.51],1.04,1.94,'black','magazine')
    beam('magazine','middle',[8,7.33,3.51],[8,6.16,3.25],1.04,1.94,'black','magazine')
    beam('magazine','lower',[8,6.16,3.25],[8,5.30,2.93],1.04,1.94,'black','magazine')
    beam('magazine','floorplate',[8,5.12,3.91],[8,5.68,2.04],1.15,.19,'edge','magazine')

    # Fore-end: long solid spine and full depth side frames around inset grille
    # rows. These are actual recessed panels, not alpha silhouettes of a gun.
    box('foreend','barrel-core',[8,10.88,-1.55],[.80,.80,8.55],'black','tube')
    box('foreend','top-spine',[8,11.93,-1.04],[1.20,.22,5.62],'steel','tube')
    box('foreend','lower-spine',[8,10.03,-1.04],[1.26,.25,5.62],'steel','rail')
    for side in (-1,1):
        x=8+side*.79
        for y,h,name in ((11.82,.25,'upper'),(10.97,.40,'middle'),(10.18,.24,'lower')):
            box('foreend',f'brass-{name}-{side}',[x,y,-1.02],[.23,h,5.58],'brass','brass')
        for z in (-3.72,1.66):
            box('foreend',f'brass-end-{side}-{z}',[x,11.0,z],[.23,1.54,.28],'brass','brass')
        for row,y in enumerate((11.39,10.55)):
            box('foreend',f'inset-quatrefoils-{side}-{row}',[8+side*.54,y,-1.02],[.17,.49,5.12],'brass','filigree')
        beam('foreend',f'lower-tube-{side}',[8+side*.83,10.08,1.75],[8+side*.83,10.08,-3.88],.16,.19,'edge','tube')
    # Front collar is a full-section bracket, not a stack of tiny face patches.
    box('collar','main',[8,11.03,-4.03],[1.78,2.03,.71],'steel','collar')
    box('collar','front-band',[8,11.02,-4.47],[1.55,1.86,.18],'edge','collar')
    for side in (-1,1):
        box('collar',f'upper-shoulder-{side}',[8+side*.65,11.92,-4.04],[.45,.36,.68],'steel','collar',(0,0,side*32))
    # Real undercut beneath the tube, with a small long lug at the muzzle.
    beam('barrel','neck',[8,10.89,-4.58],[8,10.89,-6.31],.76,.76,'steel','tube')
    box('barrel','underside-lug',[8,10.30,-7.85],[.55,.31,2.02],'steel','lug')
    beam('barrel','lug-ramp',[8,10.46,-6.66],[8,10.13,-7.20],.55,.27,'steel','lug')
    ring('muzzle','tube',8,10.87,-7.96,.34,.16,3.15,'steel')
    box('muzzle','bore-backstop',[8,10.87,-6.35],[.56,.56,.08],'recess')
    # Actual rail teeth under the fore-end justify geometry by underside profile.
    for i in range(9):
        box('foreend',f'under-rail-tooth-{i}',[8,9.76,-3.35+i*.43],[1.07,.31,.18],'black','rail')

    # Round sight is an eight-stave open hood at the original optic station.
    # The source reticle plane is a reference, never emitted as an opaque cap.
    box('optic','base',[8,12.29,4.10],[.83,.22,2.12],'black','optic')
    box('optic','rear-adjuster',[8,12.53,4.90],[.90,.28,1.16],'steel','optic')
    ring('optic','hood',8,12.95,2.91,.43,.15,.24,'black')
    box('optic','stalk',[8,12.39,2.91],[.44,.39,.40],'black','optic')
    return specs


def paint_tile(spec,face,w,h):
    mat=spec['material'];base=np.array(PALETTE[mat],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    field=.97+.04*np.cos(v*np.pi)
    col=np.broadcast_to(base,(h,w,3)).copy()*field[:,:,None]
    # Deterministic, subdued material grain. No unseeded noise.
    grain=((xx*17+yy*29)%23-11)*.12
    col+=grain[:,:,None]
    edge=(xx==0)|(yy==0)|(xx==w-1)|(yy==h-1)
    if mat not in ('recess','rubber') and spec['motif']!='magazine':col[edge]=base+10
    tile=Image.fromarray(np.dstack((np.clip(col,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))
    dr=ImageDraw.Draw(tile);motif=spec['motif'];side=face in ('east','west')
    q=vertices(spec['geometry'])[list(FACES[face])]
    p=q[0]+u[:,:,None]*(q[1]-q[0])+v[:,:,None]*(q[3]-q[0])
    wy,wz=p[:,:,1],p[:,:,2]
    def paint(mask,color):
        nonlocal tile,dr
        a=np.array(tile);a[mask,:3]=color;tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
    if motif=='binding':
        # A real cloth artwork crop from Body_Diffuse (viewed before design),
        # repainted to the photo's warm white/charcoal; no UV-island geometry.
        raw=np.asarray(Image.open(RAW/'Body_Diffuse.png').convert('RGB').crop((540,128,1000,196)))
        # Choose two independent axes for every face, including shoulders and
        # end grain; a Y/Z-only projection would stretch top and end faces.
        a,b=(wz,wy) if side else (wz,p[:,:,0]) if face in ('up','down') else (p[:,:,0],wy)
        tx=np.mod(((a*1.17+b*.55)*150).astype(int),raw.shape[1])
        ty=np.mod(((b*.91-a*.19)*105).astype(int),raw.shape[0])
        s=raw[ty,tx].mean(2);s=np.clip((s-27)/183,0,1)
        rgb=np.array([36,40,39])+(np.array([213,215,202])-[36,40,39])*s[:,:,None]
        a=np.array(tile);a[:,:,:3]=rgb.astype('uint8');tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
        # Overlapping selvage is paint on the rounded volume, not many strips.
        paint(np.mod(wy+.21*wz,.44)<.014,[155,158,150])
    if motif=='filigree' and side:
        # Use the ACTUAL Barrel_Diffuse quatrefoil silhouette as a stencil.
        # Recess is physical .25 model units; tiny floral holes are UV only.
        raw=np.asarray(Image.open(RAW/'Barrel_Diffuse.png').convert('RGB'))
        z0,z1=-3.58,1.54
        t=np.clip((wz-z0)/(z1-z0),0,1)
        # Source has 13 linked quatrefoils; preserve full strip without mirroring
        # the drawing into an unrelated material or inventing text/screws.
        rx=(20+t*690).astype(int);ry=(8+np.clip((wy-(spec['geometry']['from'][1]))/.49,0,1)*84).astype(int)
        flower=raw[ry,rx].max(2)<35
        paint(flower,[10,16,16])
        # Pale end flowers establish the photo's oxidized blue-white accents.
        paint(flower&((t<.08)|(t>.92)),[139,171,157])
        paint((v<.035)|(v>.965),[174,137,84])
    if motif in ('receiver','well','collar','lug','optic') and side:
        dr.line([(2,h-3),(w-3,h-3),(w-3,2)],fill='#282c2b',width=1)
        dr.line([(2,2),(w-3,2)],fill='#686e6b',width=1)
        # Sparse reference panel screws, painted rather than emitted boxes.
        if motif in ('collar','lug','optic'):
            for px,py in ((.18,.20),(.82,.80)):
                cx,cy=int(px*w),int(py*h);r=max(1,min(w,h)//13)
                dr.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#313635',outline='#8f9690')
                dr.line((cx-r+1,cy,cx+r-1,cy),fill='#272c2b')
    if motif=='collar' and side:
        for y in (10.42,11.55):
            mask=((wy-y)**2+(wz+4.05)**2<.018)
            paint(mask,[173,146,98])
    if motif=='magazine' and side:
        # Long pressed channels run down the physical curved sections in world
        # coordinates, so their paint continues at each deliberate bend.
        for z in (2.20,2.56,3.77,4.06):
            mask=abs(wz-(z+.13*(wy-8)))<.025
            paint(mask,[15,20,21]);paint(abs(wz-(z+.13*(wy-8))-.035)<.014,[64,70,68])
    if motif=='stock':
        paint(np.mod(wy*30+np.sin(wz*12)*.4,1)<.12,[38,40,39])
    if motif in ('grip','rail'):
        paint(np.mod(wy*15+wz*5,1)<.14,[17,21,21])
    if motif in ('tube','strap'):
        paint((u>.13)&(u<.16),np.minimum(base+14,255).astype(int).tolist())
    return tile


def compile_model(specs,canonical):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[];elements=[]
    for s in specs:
        e=copy.deepcopy(s['geometry']);e['faces']={};elements.append(e)
        for face,ids in FACES.items():
            q=vertices(e)[list(ids)];density=34 if s['motif'] in ('binding','filigree') and face in ('west','east') else 22
            w=max(5,math.ceil(np.linalg.norm(q[1]-q[0])*density));h=max(5,math.ceil(np.linalg.norm(q[3]-q[0])*density))
            requests.append((e,s,face,w,h))
    x=y=2;row=0;ledger=[]
    for e,s,face,w,h in sorted(requests,key=lambda r:(-r[4],-r[3],r[0]['name'],r[2])):
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError(f'Atlas overflow at {e["name"]}: {y+h}')
        tile=paint_tile(s,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        e['faces'][face]=dict(uv=[a*16/EDGE for a in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=e['name'],face=face,pixels=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    model=dict(credit='W128 Gnawing Hunger / authored solid volumes and face UV / full only',ambientocclusion=False,
        textures={'0':'destiny:item/weapon/w123/gnawing_hunger','particle':'destiny:item/weapon/w123/gnawing_hunger'},
        display=copy.deepcopy(canonical['display']),elements=elements)
    assert len(elements)<=1000
    return atlas,model,dict(size=[EDGE,EDGE],padding=2,used_height=y+row+2,islands=ledger)


def inspection(specs,model,atlas,meta):
    es=[];groups=collections.defaultdict(list)
    for s,e in zip(specs,model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation');b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
            origin=r['origin'],rotation=[r[a] for a in 'xyz'])
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Gnawing Hunger W128 / OFFLINE inspection',
        resolution={'width':EDGE,'height':EDGE},elements=es,
        outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],children=ids,export=True) for g,ids in groups.items()],
        textures=[dict(name='gnawing_hunger.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=model['display'],
        destiny_w128=dict(nativeAccepted=False,rotationOrder='RzRyRx',sourceAnchor=meta['anchor'],sourceScale=meta['scale'],fullOnly=True))


def comparison(meshes,model,atlas):
    w,h=880,330;sheet=Image.new('RGB',(w*3,1840),'#161d25');dr=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):dr.text((x,y),s,fill='#e3e7ed',font_size=size)
    label(20,15,'GNAWING HUNGER / W128 / semantic solids + authored face atlas / OFFLINE',28)
    photo=Image.open(PHOTO).convert('RGB').crop((660,235,1890,835));photo.thumbnail((1240,390));sheet.paste(photo,(20,60))
    label(1310,85,'DEFAULT PAINT / W31 photo',24)
    for i,t in enumerate(('Charcoal skeleton stock / curved magazine','White patterned wraps / brass quatrefoil recesses',
        'Physical stock + trigger + sight openings / deep muzzle',
        'Raw FBX column = undyed diffuse, not finished paint',
        f"New = {len(model['elements'])} opaque cuboids / one FULL model",'Generic graphs and ADS inherit full; no invented split')):
        label(1310,140+i*37,t)
    label(20,465,'RAW FBX / 27,436 triangles / undyed diffuse')
    label(w+20,465,'CANONICAL W30/W31 / 246 cuboids')
    label(w*2+20,465,f"W128 / {len(model['elements'])} authored cuboids")
    old=json.loads((ROOT/BASE).read_bytes());ot=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/gnawing_hunger.png'))
    tris=[source_triangles(meshes),model_triangles({'old':old},ot),model_triangles({'full':model},atlas)]
    ps=np.concatenate([m['vertices'] for m in meshes]+[vertices(e) for e in model['elements']])
    for row,(name,cam) in enumerate((('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.40,-.52]),('OPPOSITE REAR OBLIQUE',[-1,.36,.55]))):
        ext=frame(ps,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=render(ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,505+row*h));label(col*w+14,512+row*h,name,18)
    for i,group in enumerate(('muzzle','optic','stock','foreend')):
        es=[e for e in model['elements'] if e['name'].startswith(group+'/')]
        ps=np.concatenate([vertices(e) for e in es]);cam=[.24,.13,-1] if group in ('muzzle','optic') else [1,.28,-.40]
        im,_=render(model_triangles({'part':dict(elements=es)},atlas),cam,frame(ps,cam,660,270),(660,270));sheet.paste(im,(i*660,1510))
        label(i*660+12,1518,group.upper()+' / depth inspection',18)
    label(20,1805,'Matched camera and scale within rows. Python raster only. Native parsing / held / ADS / reload / 10-20 displays pending master.',19)
    return png(sheet)


def protected_inputs():
    return [BASE,BB,ASSET+'textures/item/weapon/w30/gnawing_hunger.png','art/weapons/w31/references.json',
        'art/weapons/w31/palette-overrides.json','scripts/generate_surface_w123_hammerhead.py',
        'scripts/generate_surface_pack_w123.py','art/weapons/w123/manifest.json']


def generate(include_comparison=True):
    meshes,meta=source_meshes();canonical=json.loads((ROOT/BASE).read_bytes());specs=semantic_geometry()
    atlas,model,uvplan=compile_model(specs,canonical);counts=dict(collections.Counter(s['group'] for s in specs))
    limits=['Faceted solid reinterpretation; rounded cloth folds and compound bends simplified.',
        'Quatrefoil microperforations are opaque artwork on physically recessed panels; not individual through holes.',
        'White binding uses actual diffuse cloth crop; shader reflections and exact folds are not recreated.',
        'Single supplied default photo establishes paint; opposite side conservatively follows source diffuse.',
        'Offline Python inspection only; native pack/parser, first/third person, ADS, generic reload and 10-20 displays pending master.']
    probes={'stock_large':[8,9.65,10.65],'stock_rear':[8,9.50,13.65],
        'trigger_guard':[8,9.43,6.60],'optic_aperture':[8,12.95,2.91],
        'muzzle_entry':[8,10.87,-9.50],'muzzle_depth':[8,10.87,-8.5],
        'cage_clearance':[8.98,10.7,7.0]}
    pins={p:sha((ROOT/p).read_bytes()) for p in protected_inputs() if (ROOT/p).is_file()}
    rawpins={str(p):sha(p.read_bytes()) for p in [RAW/'Gnawing Hunger.fbx',RAW/'Body_Diffuse.png',RAW/'Barrel_Diffuse.png',
        RAW/'Scope_Diffuse.png',RAW/'Ret_Diffuse.png',RAW/'Effect_Main.png',PHOTO]}
    points=np.concatenate([vertices(e) for e in model['elements']])
    design=dict(schema='destiny.weapon-surface.w128.v1',id='gnawing_hunger',family='auto_rifle',stage='W128',
        generator='scripts/generate_surface_w123_gnawing_hunger.py',method='Authored broad semantic cuboids, rotated beams, physical apertures; source meshes remain references only.',
        frame=dict(mapping=['8+source_x*scale','8+source_z*scale','8+source_y*scale'],anchor=meta['anchor'],scale=meta['scale'],muzzle='-Z',
            source_bounds=meta['model_bounds'],authored_bounds=[points.min(0).tolist(),points.max(0).tolist()],grip='Unrebased W30 contact region; grip core top [8,9.96,7.82], heel [8,7.23,8.76]'),
        identity=['white patterned receiver and spiral grip bindings','brass twin recessed quatrefoil grille rows','dark two-window skeleton stock',
            'curved dark magazine','lateral steel protective cage','short open round reflex hood and long bored muzzle'],
        paint_sources=dict(cloth_crop=[540,128,1000,196],cloth_source_size=[2048,2048],quatrefoil='Barrel_Diffuse actual top strip'),
        palette=PALETTE,palette_evidence='W31 reference gnawing_hunger entry, no W31 palette override; photo 821154603 default dyes. Raw diffuse is not finished paint.',
        partition='FULL ONLY. Magazine is an authored visual group inside full; no separate output, pivot or moving reload split. Existing generic graphs / ADS inherit full.',
        geometry=specs,groups=counts,parts={'full':len(specs)},max_assembled_elements=1000,
        alpha_shells=0,source_component_tessellation=False,uv=uvplan,required_air_probes=probes,
        input_sha256=pins,raw_input_sha256=rawpins,limitations=limits)
    outputs={MODEL:encode(model),TEXTURE:png(atlas),ART+'design.json':encode(design),ART+'inspection.bbmodel':encode(inspection(specs,model,atlas,meta))}
    if include_comparison:outputs[ART+'comparison.png']=comparison(meshes,model,atlas)
    review=f"""# Gnawing Hunger W128 art review

{len(specs)} emitted opaque cuboids / {len(specs)*6} faces; FULL ONLY, no reload split.
Semantic groups: {json.dumps(counts,sort_keys=True)}. Maximum assembled 1000.

Long receiver, true solid curved magazine and grip, skeleton stock with two air
windows, offset protective cage and round sight are authored from broad volumes.
The long muzzle is eight continuous tangent staves surrounding a deep bore with a
recessed backstop. There are real gaps in the stock, trigger guard and sight, and
clearance under the lateral cage. Per-face UV uses independent aspect-proportional
islands and two-pixel bleed. No source mesh conversion, connected-island fitting,
alpha body plates, opaque silhouette box, or source triangles are emitted.

Default paint comes from the supplied W31 photo / reference 821154603: charcoal
steel and stock, warm-white mottled binding and brown brass twin fore-end rows.
W31 has no palette override for this weapon. Body_Diffuse provides an actual
cloth-pattern crop; Barrel_Diffuse supplies the actual quatrefoil stencil. These
are repainted/repacked on deliberate face islands, not treated as finished dyes.
Tiny floral perforations are opaque painted ornament on panels set .25 units
behind the broad brass frame. The recess is physical; individual petals are not
through holes. No invented lettering, alternate shader palette or decorative
screw geometry. Small fasteners and pressed channels are face artwork.

The original [8,8,8] carrier, scale {meta['scale']}, (X,Z,Y) source mapping,
-Z muzzle, hand-contact region and all canonical display transforms are preserved.
No canonical JSON, historical W30/W31, gameplay, sounds, timing, shared manifest,
Java, graphs or ADS are changed. Generic graphs / ADS can inherit this full
replacement through master's integration. The magazine group has no invented
moving split; inspection groups organize art only.

comparison.png contains actual raw FBX (undyed), unchanged canonical W31 paint,
and new output at a matched side camera and two oblique cameras, plus independent
muzzle/sight/stock/fore-end depth close-ups. It embeds the actual default photo.
The generated PNG must be inspected via view_image; offline raster does not prove
native acceptance. inspection.bbmodel embeds the complete new opaque atlas.

Limitations: {' '.join(limits)}
"""
    outputs[ART+'review.md']=review.encode()
    manifest=dict(stage='W128',id='gnawing_hunger',family='auto_rifle',counts={'full':len(specs)},parts={'full':len(specs)},groups=counts,
        elements=len(specs),emitted_faces=6*len(specs),maximum_assembled_elements=1000,opaque_cuboids=len(specs),triangle_adapter_elements=0,
        alpha_body_plates=0,source_triangles=sum(len(m['faces']) for m in meshes),canonical_elements=len(canonical['elements']),full_only=True,
        canonical_display_exact=True,canonical_anchor_preserved=True,source_scale=meta['scale'],source_anchor=meta['anchor'],
        texture_size=[EDGE,EDGE],uv_islands=len(uvplan['islands']),atlas_used_height=uvplan['used_height'],
        native_accepted=False,validation=dict(targeted_python='scripts/qa/test_surface_w123_gnawing_hunger.py',native='pending master',performance='not measured'),
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=pins,raw_input_sha256=rawpins,
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=limits)
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w128/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w128-gnawing_hunger'))
    assert len(owned)==10 and set(outputs)<=owned
    for p,data in outputs.items():
        dst=ROOT/p
        if args.verify:assert dst.is_file() and dst.read_bytes()==data,'Regeneration drift: '+p
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f" {len(outputs)} artifacts / {m['counts']} / {m['uv_islands']} face UV islands")

if __name__=='__main__':main()
