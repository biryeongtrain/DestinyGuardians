#!/usr/bin/env python3
"""W144 Dream Breaker: authored filled volumes and clean opaque face UV.

Binary FBX is inert reference only. Never executes embedded Blender scripts,
node graphs or shaders. Canonical native frame/display and gameplay untouched.
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

ROOT=Path(__file__).resolve().parents[1]
ID='dream_breaker'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/fusion_rifle/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
BB=f'art/blockbench/weapons/w30/{ID}.bbmodel'
RAW=Path('/tmp/destiny-weapons-w30/raw/dream_breaker/extracted/Dream Breaker')
PHOTO=Path('/tmp/destiny-weapons-w31/references/dream_breaker.jpg')
H=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
FACES=H['FACES'];EDGE=1024
PALETTE=dict(ivory=[196,199,184],edge=[224,224,207],steel=[56,61,61],black=[24,28,29],
             grip=[48,48,38],blue=[31,64,80],blue_edge=[47,83,98],brass=[145,122,68],
             copper=[137,74,40],silver=[184,190,184],recess=[11,15,17])

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w144:dream_breaker:'+n))
def vertices(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        q=e['rotation'];e['rotation']=dict(origin=q['origin'],**{q['axis']:q['angle']})
    return H['vertices'](e)
def model_triangles(model,atlas):
    model=copy.deepcopy(model)
    for e in model['elements']:
        if 'rotation' in e:
            q=e['rotation'];e['rotation']=dict(origin=q['origin'],**{q['axis']:q['angle']})
    return H['model_triangles']({'full':model},atlas)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    for name,expected in meta['source_files'].items():
        assert sha((RAW.parent/name).read_bytes())==expected
    roots=H['parse_fbx'](RAW/'Dream Breaker.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[];excluded=[]
    for n in objects:
        if n[0]!='Geometry':continue
        mid=next(p for c,p in links if c==n[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
        if name in meta['excluded_objects']:excluded.append(name);continue
        assert name in meta['source_objects'],name
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in n[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        # Dream's own baked FBX frame. Erentil's different basis is not reused.
        points=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]);assert np.all(ix[2::3]<0)
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        values={c[0]:c[1][0] for c in layer[2]}
        uv=np.array(values['UV']).reshape(-1,2)[np.array(values['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        mat=next((materials[c] for c,p in links if p==mid and c in materials),None)
        meshes.append(dict(name=name,vertices=points,faces=faces,uv=uv,material=mat))
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sorted(excluded)==sorted(meta['excluded_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==27052
    assert sum(len(m['faces']) for m in meshes if m['material'])==meta['textured_triangles']==26377
    points=np.concatenate([m['vertices'] for m in meshes])
    np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5,rtol=0)
    ref=next(x for x in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if x['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta,ref

def source_triangles(meshes):
    textures={m:np.array(Image.open(RAW/f'{f}_Diffuse.dds').convert('RGBA')) for m,f in [('Barrel','Dream'),('Icon','Icon')]}
    result=[]
    for m in meshes:
        if m['material'] not in textures:continue
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((ps,uv,textures[m['material']],n))
    return result

def make_design(meta,ref):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);s=np.array(size,float)
        e=dict(name=name,**{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()})
        if turn:e['rotation']=dict(origin=c.round(6).tolist(),axis=turn[0],angle=round(turn[1],6))
        parts.append(dict(group=group,material=mat,motif=motif,kind='filled_semantic_cuboid',geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='plain',x=8):
        z0,y0=a;z1,y1=b
        box(group,name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(z1-z0,y1-y0)],mat,motif,('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
    def strap(group,name,z,y0,y1,width,thick,mat='blue'):
        # Four opaque filled runs wrap a solid part; no alpha belt texture shell.
        for side in (-1,1):box(group,name+f'_side_{side}',[8+side*(width/2+thick/2),(y0+y1)/2,z],[thick,y1-y0,thick],mat,'cord')
        for y in (y0,y1):box(group,name+f'_end_{y}',[8,y,z],[width+2*thick,thick,thick],mat,'cord')
    # Continuous ivory forward housing. Broad bevel shoulders, not voxel stairs.
    box('forebody','forward_filled_core',[8,11.72,-3.90],[1.60,2.64,10.34],'ivory','receiver')
    for side in (-1,1):
        beam('forebody',f'upper_chamfer_{side}',[-8.99,13.04],[1.2,13.04],.28,.33,'edge','edge',x=8+side*.66)
        beam('forebody',f'lower_chamfer_{side}',[-8.99,10.39],[1.2,10.39],.28,.26,'ivory','edge',x=8+side*.66)
        box('forebody',f'upper_power_channel_{side}',[8+side*.812,12.02,-3.9],[.045,.72,10.18],'steel','flutes')
        box('forebody',f'lower_panel_{side}',[8+side*.82,10.80,-3.90],[.06,.73,10.05],'ivory','panels')
    box('receiver','receiver_full',[8,11.65,4.50],[1.67,2.65,6.72],'ivory','receiver')
    beam('receiver','rear_receiver_rise',[6.28,12.95],[7.31,11.95],1.67,.62,'steel','edge')
    box('receiver','rear_mount',[8,11.10,7.66],[1.40,1.25,1.55],'steel','receiver')
    box('receiver','rear_copper_spine',[8,11.75,10.81],[1.06,.30,7.36],'copper','rail')
    # Rectangular deep upper port with physically open beveled mouth.
    for side in (-1,1):
        box('muzzle',f'upper_port_wall_{side}',[8+side*.60,12.35,-9.18],[.19,1.13,.46],'edge','muzzle')
        box('muzzle',f'upper_port_chamfer_{side}',[8+side*.50,12.88,-9.18],[.30,.20,.46],'ivory','muzzle',('z',side*35))
        box('muzzle',f'upper_port_lower_chamfer_{side}',[8+side*.50,11.81,-9.18],[.30,.20,.46],'ivory','muzzle',('z',-side*35))
    for y in (11.73,12.97):box('muzzle',f'upper_port_rim_{y}',[8,y,-9.18],[.89,.16,.46],'ivory','muzzle')
    box('muzzle','upper_port_recess',[8,12.35,-9.11],[1.00,1.04,.05],'recess')
    for x in (7.45,8.55):box('muzzle',f'lower_port_wall_{x}',[x,10.64,-9.18],[.18,1.20,.43],'ivory','muzzle')
    for y in (10.02,11.26):box('muzzle',f'lower_port_rim_{y}',[8,y,-9.18],[1.28,.16,.43],'ivory','muzzle')
    box('muzzle','lower_port_recess',[8,10.64,-9.11],[.95,1.04,.05],'recess','vents')
    # The front hand contact is a substantial vertical power pack, not a card.
    box('powerpack','powerpack_full',[8,7.75,3.57],[1.42,6.54,3.45],'ivory','powerpack')
    box('powerpack','pack_heel',[8,4.64,3.57],[1.57,.42,3.60],'edge','panels')
    for side in (-1,1):box('powerpack',f'pack_ribbed_side_{side}',[8+side*.73,6.48,3.57],[.09,1.15,3.33],'steel','flutes')
    box('powerpack','upper_pack_cuff',[8,9.45,3.57],[1.66,.32,3.56],'black','pack_cuff')
    box('powerpack','lower_pack_cuff',[8,6.67,3.57],[1.66,.28,3.56],'black','pack_cuff')
    # Rear grip is a real slanted grid. Its broad-through openings are geometric.
    beam('grip','upper_grip_root',[8.12,10.40],[8.70,9.16],1.20,1.67,'grip','grip')
    for j in range(4):
        offset=(j/3-.5)*1.42
        beam('grip',f'lattice_stile_{j}',[8.64+offset,9.22],[10.07+offset,6.29],1.12,.13,'grip','grip')
    for j in range(6):
        t=j/5;z=8.64+1.43*t;y=9.22-2.93*t
        beam('grip',f'lattice_rung_{j}',[z-.77,y],[z+.77,y],1.12,.14,'grip','grip')
    beam('grip','grip_heel',[9.22,6.18],[10.90,6.18],1.26,.26,'grip','grip')
    # Guard and trigger are separate from the lattice's physical holes.
    beam('guard','trigger_spine',[7.02,10.38],[7.22,9.36],.19,.17,'steel')
    beam('guard','trigger_hook',[7.22,9.36],[6.94,9.10],.19,.17,'steel')
    beam('guard','guard_front',[6.34,10.20],[6.44,9.08],.20,.18,'grip')
    beam('guard','guard_base',[6.44,9.08],[7.79,9.22],.20,.18,'grip')
    # Long spare stock rails, stepped receiver neck and tall ivory shoulder pad.
    for side in (-1,1):
        beam('stock',f'stock_side_rail_{side}',[8.65,11.11],[15.15,11.11],.22,.24,'steel','rail',x=8+side*.46)
    beam('stock','upper_stock_rail',[8.0,12.03],[15.1,12.03],1.04,.40,'steel','rail')
    box('stock','stock_connector',[8,11.56,12.45],[1.05,1.14,3.87],'ivory','stock')
    box('stock','butt_pad',[8,10.90,15.15],[1.26,4.28,.73],'ivory','stock')
    box('stock','butt_end',[8,10.90,15.50],[1.15,4.11,.14],'steel','pad')
    for side in (-1,1):beam('stock',f'butt_bevel_{side}',[15.12,12.92],[15.12,8.96],.23,.55,'edge','edge',x=8+side*.54)
    # Dark blue rope wraps and side lashings keep the lunar identity. No screws.
    for i,z in enumerate((-8.51,-7.78,-2.22,1.25,1.94,2.73)):
        strap('cords',f'fore_wrap_{i}',z,10.22,13.27,1.70,.22)
    for i,z in enumerate((10.02,11.12,14.70)):
        strap('cords',f'stock_wrap_{i}',z,10.82,12.32,1.12,.18)
    for side in (-1,1):
        x=8+side*.97
        beam('cords',f'front_long_rope_{side}',[-8.41,10.87],[1.65,11.05],.24,.24,'blue','cord',x=x)
        beam('cords',f'rear_long_rope_{side}',[6.12,11.08],[15.10,11.10],.21,.21,'blue','cord',x=8+side*.72)
        for j,(a,b) in enumerate([([2.55,13.23],[5.79,9.56]),([6.63,12.70],[2.82,9.22]),([8.98,12.13],[10.23,10.38])]):
            beam('cords',f'receiver_diagonal_{side}_{j}',a,b,.25,.25,'blue','cord',x=x)
        for j in range(3):
            beam('cords',f'pack_rope_{side}_{j}',[1.72,8.80+j*.28],[5.39,9.02+j*.28],.24,.24,'blue','cord',x=x)
        for z in (1.82,5.24):
            beam('knots',f'knot_tie_{side}_{z}',[z-.23,10.15],[z+.16,10.51],.24,.20,'blue_edge','cord',x=x)
            beam('knots',f'knot_tail_{side}_{z}',[z-.12,10.25],[z+.12,9.98],.17,.15,'blue','cord',x=x)
    # Small engraved plaques are meaningful protruding relief; the actual icon is UV.
    plaques=[(-8.15,12.39),(-8.56,10.50),(2.51,12.58),(6.12,11.48),(9.48,11.46),(10.30,11.76)]
    for side in (-1,1):
        for i,(z,y) in enumerate(plaques):box('plaques',f'bronze_charm_{side}_{i}',[8+side*1.035,y,z],[.13,.74,.70],'brass','source_plaque')
    # Selected silver link silhouettes; fine chain relief is face texture.
    for side in (-1,1):
        for z,y0,y1 in [(-7.83,10.33,13.33),(5.72,10.06,13.27)]:
            beam('links',f'chain_back_{side}_{z}',[z,y0],[z-.30,y1],.13,.10,'steel','chain',x=8+side*.94)
            for i in range(7):
                t=i/6;box('links',f'silver_link_{side}_{z}_{i}',[8+side*1.00,y0+(y1-y0)*t,z-.30*t],[.20,.19,.19],'silver','chain',('x',35 if i%2 else -35))
    # Large hanging power hose is a real open U in front of the solid pack.
    arc=[]
    for i in range(13):
        a=math.radians(150+i*20);arc.append([3.72+1.66*math.cos(a),8.48+1.62*math.sin(a)])
    for i,(a,b) in enumerate(zip(arc,arc[1:])):
        beam('hose',f'power_hose_{i}',a,b,.32,.32,'black','hose',x=9.23)
        if i in (1,3,5,7,9):
            c=(np.array(a)+np.array(b))/2;v=np.array(b)-a;v=v/np.linalg.norm(v)*.22
            beam('couplings',f'brass_hose_collar_{i}',c-v,c+v,.51,.51,'brass','coupling',x=9.23)
    beam('hose','upper_hose_feed',[2.28,9.22],[2.53,10.12],.33,.33,'black','hose',x=9.23)
    beam('hose','upper_hose_return',[5.16,9.24],[4.95,10.20],.33,.33,'black','hose',x=9.23)
    for name,z,y in [('feed',2.53,10.12),('return',4.95,10.2)]:
        box('couplings',f'upper_brass_{name}',[9.23,y,z],[.57,.47,.57],'brass','coupling',('x',25))
    # Low physical sight channel follows the accepted source, not a new glass card.
    box('sight','sight_base',[8,13.33,3.29],[.92,.20,1.75],'steel','sight')
    for side in (-1,1):box('sight',f'rear_sight_fork_{side}',[8+side*.29,13.52,3.65],[.16,.25,.28],'steel','sight')
    box('sight','front_sight_post',[8,13.48,-7.55],[.09,.24,.18],'steel','sight')
    return dict(id=ID,revision='W144',family='fusion_rifle',source=meta,reference=ref,
        source_mapping='baked FBX [X,Z,Y]*scale+anchor; muzzle negative native Z',
        scale=meta['scale'],anchor=meta['anchor'],palette=PALETTE,parts=parts,
        method='Hand-authored solid volumes, per-face UV. No rip islands, voxel skin, alpha body or arbitrary mesh fields.',
        starting_draft='Body/stock/grip near80-120; extra cord runs, 28 selected silver links, U hose and plaque relief justify the larger final count.',
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in (BASE,BB,'art/weapons/w31/references.json','scripts/generate_surface_w123_beloved.py')},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in [RAW/'Dream Breaker.fbx',RAW/'Dream Breaker.blend',RAW/'Dream_Diffuse.dds',RAW/'Icon_Diffuse.dds',PHOTO]},
        required_air_probes={'upper_muzzle':[8,12.35,-9.24],'lower_muzzle':[8,10.64,-9.24],'trigger_guard':[8,9.65,7.42],'lattice_grip':[8,7.91,9.72],'sight_notch':[8,13.52,3.65]},
        solid_probes={'forebody':[8,11.72,-4.0],'receiver':[8,11.65,4.5],'powerpack':[8,7.75,3.57],'stock_connector':[8,11.56,12.45]},
        limitations=['Opaque static matte approximation, not recovered PBR or animated iridescence.','Sculpted cloth/rope and links are selectively faceted, not source fragment transplantation.','Fine plaque relief comes from actual source icon; reverse-side symmetry is a documented approximation.','Full-only generic reload retained. Actual held/ADS/charge/reload/20display QA is master-owned.'])

def plaque_image(meshes):
    m=next(m for m in meshes if m['name']=='Dream-Breaker.01.001')
    ts=source_triangles([m]);points=m['vertices'];cam=[-1,0,0]
    im,mask=H['render'](ts,cam,H['frame'](points,cam,180,180),(180,180),raw=True)
    yy,xx=np.where(mask);assert len(xx)
    return im.crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1))

def tile(spec,face,w,h,plaque):
    base=np.array(PALETTE[spec['material']],float);yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    a=np.zeros((h,w,4),np.uint8);a[:,:,3]=255
    a[:,:,:3]=np.clip(base[None,None,:]*(.97+.03*np.sin(v*np.pi))[:,:,None],0,255)
    ps=vertices(spec['geometry'])[list(FACES[face])];p=ps[0]+u[:,:,None]*(ps[1]-ps[0])+v[:,:,None]*(ps[3]-ps[0])
    X,Y,Z=(p[:,:,i] for i in range(3));motif=spec['motif'];side=face in ('east','west')
    if spec['material'] in ('ivory','edge','steel','brass','copper'):
        a[0,:,:3]=np.minimum(base+14,255);a[-1,:,:3]=base*.75
    if motif in ('receiver','panels','powerpack','stock') and side:
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        a[(edge>1.0)&(edge<2.2),:3]=base*.65
        a[(edge>2.2)&(edge<3.1),:3]=np.minimum(base+12,255)
        # Sparse supported wear at panel edges, not diffuse noise across the body.
        wear=(edge<2.5)&(np.sin(Z*11+Y*23)>.76);a[wear,:3]=[89,98,91]
        if motif in ('receiver','panels'):
            for z in (-6.8,-3.9,-.55,3.5,6.3):
                a[(abs(Z-z)<.018)&(Y<11.50),:3]=[72,80,75]
        if motif=='powerpack':
            a[(abs(Z-3.0)<.035)&(Y<6.0),:3]=[71,80,75]
            a[(abs(Z-3.74)<.035)&(Y<6.0),:3]=[71,80,75]
    if motif in ('flutes','rail','vents'):
        ribs=np.mod(Y,.14)<.034;a[ribs,:3]=base*.57
        a[(np.mod(Y,.14)>.045)&(np.mod(Y,.14)<.063),:3]=np.minimum(base+18,255)
    if motif in ('cord','hose','pack_cuff'):
        weave=np.sin(Y*55+Z*63+X*9)*np.sin(Y*37-Z*43)
        a[weave>.64,:3]=base*.80;a[weave<-.78,:3]=np.minimum(base+14,255)
        if motif=='hose':a[np.mod(Y+Z,.10)<.018,:3]=base*.62
    if motif=='coupling':
        a[np.mod(Y+Z,.15)<.025,:3]=base*.58
        a[np.mod(Y+Z,.15)>.125,:3]=np.minimum(base+24,255)
    if motif=='grip':
        a[np.mod(Y+.2*Z,.14)<.025,:3]=base*.62
    if motif=='chain':
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);a[edge<1.3,:3]=base*.72
        a[(abs(u-v)<.12)&(edge>1.3),:3]=np.minimum(base+24,255)
    im=Image.fromarray(a)
    if motif=='source_plaque' and side:
        # Source-relief crop is opaque, with independent per-face orientation.
        relief=np.asarray(plaque.resize((w,h),Image.Resampling.LANCZOS).convert('RGB')).astype(float)
        luminance=relief.mean(2);luminance=np.clip((luminance-25)*1.35+48,35,185)
        colors=np.clip(luminance[:,:,None]*np.array([1.15,.97,.56]),0,255).astype('uint8')
        im=Image.fromarray(np.dstack([colors,np.full((h,w),255,np.uint8)]))
    return im

def compile_model(d,meshes):
    atlas=Image.new('RGBA',(EDGE,EDGE),(20,26,29,255));requests=[];plaque=plaque_image(meshes)
    for s in d['parts']:
        s['geometry']['faces']={}
        for face in FACES:
            p=vertices(s['geometry'])[list(FACES[face])];density=25 if s['motif']=='source_plaque' else 16
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,s['geometry']['name'],face,s))
    requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;ledger=[]
    for h,w,name,face,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,'Atlas overflow'
        im=tile(s,face,w,h,plaque)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][face]=dict(uv=[q*16/EDGE for q in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,islands=ledger)
    return atlas,dict(credit='Dream Breaker W144 / authored semantic solids and source-relief face UV',
        textures={'0':f'destiny:item/weapon/w123/{ID}','particle':f'destiny:item/weapon/w123/{ID}'},
        elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])

def inspection(d,model,atlas):
    es=[];groups=collections.defaultdict(list)
    for s,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);q=b.pop('rotation',None);rot=[0,0,0]
        if q:rot['xyz'.index(q['axis'])]=q['angle']
        b.update(type='cube',uuid=uid(b['name']),origin=q['origin'] if q else [8,8,8],rotation=rot,box_uv=False,autouv=0)
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Dream Breaker W144 owned inspection',resolution={'width':EDGE,'height':EDGE},elements=es,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=names,export=True) for g,names in groups.items()],
        textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']))

def comparison(d,meshes,atlas,model):
    w,h=820,350;sheet=Image.new('RGB',(2460,1640),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'DREAM BREAKER W144 / AUTHORED SOLID VOLUMES + CLEAN DEFAULT DYE UV',27)
    photo=Image.open(PHOTO).convert('RGB').crop((655,175,1860,805));photo.thumbnail((1040,450));sheet.paste(photo,(5,52))
    for i,line in enumerate([f'{len(model["elements"])} opaque semantic cuboids / full only / no alpha body shells',
            'Ivory housing / dark blue lashings / copper rails / engraved brass plaques',
            'Physical deep ports, open lattice grip, hanging U hose, selected silver links',
            'Continuous filled receiver and power pack; long clean face UV',
            'Actual FBX 27052tri (26377 textured); original native frame/display retained',
            'Offline CPU art only; native pack/ADS/charge/reload/20displays pending']):label(1075,82+i*54,line,20)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    ps=np.concatenate([m['vertices'] for m in meshes])
    for i,t in enumerate(['RAW / UNDYED DIFFUSE /26377 TEXTURED TRI','CANONICAL / READ ONLY',f'NEW / {len(model["elements"])} SEMANTIC CUBOIDS']):label(i*w+15,480,t,18)
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.4,-.6]),('STOCK OBLIQUE',[-1,.35,.55])]):
        ext=H['frame'](ps,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,520+row*h));label(col*w+12,528+row*h,name,17)
    label(15,1602,'Actual photo and inert source read. Static matte UV, not PBR. Handedness/display/charge timings/audio preserved, not certified by this render.',18)
    return png(sheet)

def generate(include_comparison=True):
    meshes,meta,ref=source_meshes();d=make_design(meta,ref);atlas,model=compile_model(d,meshes)
    n=len(model['elements']);assert 0<n<=1000
    review=f'''# Dream Breaker W144\n\n**{n} opaque cuboids / {n*6} independent face UVs**, 1024 atlas, full-only. Filled ivory forward housing/receiver/powerpack, dark blue lashings, copper stock rails, brass source-relief plaques, selected physical silver links, hanging open U hose and actual lattice grip holes retain the lunar identity. Not a source island/voxel shell and not flat alpha side cards.\n\nActual default-photo `{PHOTO}` opened; source `Dream Breaker.fbx` read inertly, all19 accepted records27052triangles/26377textured, two120tri reticle alternatives excluded by original W30 labels. Exact rawFBX[X,Z,Y]*scale+anchor bound check. An initial attempt with Erentil's different frame failed to match bounds; corrected from evidence rather than recentering the product. A read-only BLEND helper probe rejected compressed Blender291 before output; no scene scripts/shaders executed. Both original hashes are pinned.\n\nScale {meta['scale']}, anchor {meta['anchor']}, native muzzle -Z and canonical display retained. Existing ADS/twohand/charge/generic reload/timing/gameplay/sounds untouched; no fake split resources. Surface motifs use face UV; actual original Icon material supplies plaque relief instead of invented glyphs. Reverse-side plaque symmetry and selected rope/link faceting are documented approximations. Source diffuse is neutral and not treated as complete default dye/PBR.\n\ncomparison includes actual photo, raw textured geometry (undyed), historical canonical and authored model at matching side/front/rear cameras. inspection.bbmodel embeds the final opaque texture and editable named solids. Native parser/pack/held/ADS/charge-fire/reload and10-20display verification is master-owned; CPU image is not native or performance proof.\n'''
    out={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review.encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    ps=np.concatenate([vertices(e) for e in model['elements']])
    m=dict(id=ID,revision='W144',assembled_elements=n,opaque_cuboids=n,triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=n*6,texture_size=[EDGE,EDGE],max_assembled_elements=1000,groups=dict(collections.Counter(s['group'] for s in d['parts'])),actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],source_bounds=meta['model_bounds'],source_triangles=27052,textured_triangles=26377,untextured_source_triangles=675,canonical_display_exact=True,full_only=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(v) for p,v in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(m);return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if args.verify:assert target.is_file() and target.read_bytes()==data,path
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print('Dream Breaker W144','verified' if args.verify else 'generated')
if __name__=='__main__':main()
