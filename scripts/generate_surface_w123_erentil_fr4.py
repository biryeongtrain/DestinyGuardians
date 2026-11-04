#!/usr/bin/env python3
"""Erentil FR4 W130: semantic solid remodel, default-photo paint, full only.
Read-only CPU camera/raster helpers from Beloved; inert FBX 7500 reader adapted
from its parser. Never executes source scripts embedded in the rip.
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
import struct
import uuid
import zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
ART='art/weapons/w123/erentil_fr4/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/fusion_rifle/erentil_fr4.json'
MODEL=ASSET+'models/weapon_surface_w123/erentil_fr4.json'
TEXTURE=ASSET+'textures/item/weapon/w123/erentil_fr4.png'
BB='art/blockbench/weapons/w30/erentil_fr4.bbmodel'
GENERATOR='scripts/generate_surface_w123_erentil_fr4.py'
TEST='scripts/qa/test_surface_w123_erentil_fr4.py'
REPORT='docs/qa/2026-10-26/w130/erentil_fr4-worker.md'
RAW=Path('/tmp/destiny-weapons-w30/raw/erentil_fr4/extracted/Erentil FR4')
PHOTO=Path('/tmp/destiny-weapons-w31/references/erentil_fr4.jpg')
REFS=Path('/tmp/destiny-weapons-w31/references.json')
EDGE=1024
FACES={'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),
       'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
PALETTE={'blue':[43,65,81],'blue_edge':[67,94,109],'silver':[171,183,187],
         'steel':[113,128,136],'rubber':[23,29,32],'black':[17,22,26],
         'white':[199,208,208],'optic':[49,84,101]}
_HELPER=None

def helper():
    global _HELPER
    if _HELPER is None:_HELPER=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
    return _HELPER

def sha(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w130:erentil_fr4:'+s))
def vertices(e):return helper()['vertices'](e)

def parse_fbx(path):
    data=path.read_bytes()
    assert data[:23]==b'Kaydara FBX Binary  \x00\x1a\x00'
    version=struct.unpack_from('<I',data,23)[0];assert version in (7400,7500)
    header,size=('<QQQB',25) if version>=7500 else ('<IIIB',13)
    def node(pos):
        end,count,_,length=struct.unpack_from(header,data,pos);pos+=size
        if end==0:return None,pos
        name=data[pos:pos+length].decode();pos+=length;properties=[]
        for _ in range(count):
            kind=chr(data[pos]);pos+=1
            if kind in 'YCFDIL':
                fmt={'Y':'h','C':'?','I':'i','F':'f','D':'d','L':'q'}[kind]
                value=struct.unpack_from('<'+fmt,data,pos)[0];pos+=struct.calcsize(fmt)
            elif kind in 'SR':
                length=struct.unpack_from('<I',data,pos)[0];pos+=4
                value=data[pos:pos+length];pos+=length
                if kind=='S':value=value.decode(errors='replace')
            elif kind in 'fdlibc':
                length,compression,n=struct.unpack_from('<III',data,pos);pos+=12
                raw=data[pos:pos+n];pos+=n;assert compression in (0,1)
                if compression:raw=zlib.decompress(raw)
                fmt={'f':'f','d':'d','l':'q','i':'i','b':'?','c':'b'}[kind]
                value=struct.unpack('<'+str(length)+fmt,raw)
            else:raise ValueError('Unsupported FBX kind '+kind)
            properties.append(value)
        children=[]
        while pos<end-size:
            child,pos=node(pos);assert child is not None;children.append(child)
        return (name,properties,children),end
    roots=[];pos=27
    while pos<len(data):
        n,pos=node(pos)
        if n is None:break
        roots.append(n)
    return roots

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Erentil FR4.fbx').read_bytes())==meta['source_files']['Erentil FR4/Erentil FR4.fbx']
    roots=parse_fbx(RAW/'Erentil FR4.fbx');objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'};meshes=[]
    for n in objects:
        if n[0]!='Geometry':continue
        model=models[next(p for c,p in links if c==n[1][0])];name=model[1][1].split('\x00')[0]
        ch={c[0]:c for c in n[2]};raw=np.array(ch['Vertices'][1][0]).reshape(-1,3)
        points=raw[:,[1,2,0]]*np.array([1,1,-1])*meta['scale']+meta['anchor']
        indices=np.array(ch['PolygonVertexIndex'][1][0]);assert np.all(indices[2::3]<0)
        faces=np.where(indices<0,-indices-1,indices).reshape(-1,3)
        meshes.append(dict(name=name,vertices=points,faces=faces))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    # Original FBX retains alternate reticles omitted by the processed W30 blend.
    meta=copy.deepcopy(meta);meta['raw_fbx_triangles']=sum(len(m['faces']) for m in meshes)
    # Open neutral albedo read-only as material evidence, not the finished dye.
    diffuse=RAW/'Textures/2A76EB80_albedo.png'
    with Image.open(diffuse) as im:im.convert('RGB').resize((8,8)).load()
    reference=next(r for r in json.loads(REFS.read_bytes()) if r['id']=='erentil_fr4')
    assert sha(PHOTO.read_bytes())==reference['sha256']
    return meshes,meta,reference

def make_design(meta,reference):
    parts=[]
    def box(group,name,c,size,material,angles=(0,0,0),motif=''):
        c=np.array(c,float);size=np.array(size,float)
        parts.append(dict(group=group,material=material,motif=motif,kind='filled_solid',geometry={
            'name':name,'from':(c-size/2).round(6).tolist(),'to':(c+size/2).round(6).tolist(),
            'rotation':dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles)))}))
    def beam(group,name,a,b,width,depth,material,motif=''):
        a=np.array(a,float);b=np.array(b,float);v=b-a;assert abs(v[0])<1e-8
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],material,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0),motif)
    def cylinder(group,name,x,y,z,r,length,material,motif='bands'):
        # Four overlapping rectangles tile the SAME convex filled octagon.
        for i in range(4):
            box(group,f'{name}_facet_{i}',[x,y,z],
                [2*r*math.cos(math.pi/8),2*r*math.sin(math.pi/8),length],
                material,(0,0,45*i),motif)
    def ring(name,x,y,z,r,t,length):
        for i in range(8):
            a=i*45;q=math.radians(a)
            box('muzzle',f'{name}_rim_{i}',[x+r*math.cos(q),y+r*math.sin(q),z],
                [2*r*math.tan(math.pi/8)+.014,t,length],'silver',(0,0,a-90),'rim')
        box('muzzle',name+'_bore_backstop',[x,y,z+length/2+.04],[r*1.55,r*1.55,.10],'black')
    box('frame','Omolon_receiver',[8,11.50,6.15],[1.48,1.42,4.40],'blue',motif='omolon')
    box('stock','Stock_upper',[8,11.75,11.65],[1.35,1.08,6.86],'blue',motif='stock')
    box('stock','Stock_top_spine',[8,12.36,10.26],[1.18,.19,9.48],'steel',motif='stock_rail')
    beam('stock','Shoulder_hook',[8,12.30,15.15],[8,9.15,15.10],1.29,.65,'blue','stock')
    beam('stock','Shoulder_pad',[8,12.22,15.48],[8,9.22,15.43],1.23,.21,'rubber','pad')
    cylinder('stock','Rear_silver_buffer',8,12.42,14.15,.38,1.87,'silver')
    # Grip follows source native hand contact; the full model is never recentered.
    box('grip','Grip_root',[8,10.73,3.62],[1.32,.76,1.42],'blue',motif='grip')
    beam('grip','Grip_main',[8,10.58,3.62],[8,4.78,1.85],1.30,1.26,'blue','grip')
    beam('grip','Grip_front_bevel',[8,10.15,2.95],[8,4.70,1.30],1.02,.22,'blue_edge','grip_edge')
    beam('guard','Rear_thumbhole_web',[8,10.92,7.03],[8,7.02,8.80],1.25,1.09,'blue','web')
    beam('guard','Triangle_lower_brace',[8,4.67,1.88],[8,6.87,8.84],1.31,.65,'blue_edge','brace')
    beam('grip','Grip_heel',[8,4.31,1.22],[8,4.94,3.68],1.39,.35,'rubber','heel')
    beam('guard','Trigger',[8,10.80,6.20],[8,9.54,5.98],.24,.24,'black')
    beam('cartridge','Cartridge_base',[8,3.99,1.58],[8,4.75,4.65],1.04,.52,'black','cartridge')
    tubes=[('Upper',8,12.72,.44),('Lower_near',7.48,11.18,.35),('Lower_far',8.52,11.18,.35)]
    for name,x,y,r in tubes:
        cylinder('rails',name+'_rail',x,y,-4.95,r,7.10,'silver')
        cylinder('rails',name+'_tube_rear_collar',x,y,-1.48,r+.10,.39,'steel')
        ring(name,x,y,-9.10,r+.045,.17,.63)
    cylinder('chamber','Upper_chamber',8,12.72,1.83,.70,6.10,'silver','chamber')
    cylinder('chamber','Upper_rear_collar',8,12.72,5.00,.76,.61,'silver','collar')
    cylinder('chamber','Upper_front_collar',8,12.72,-1.14,.75,.51,'steel','collar')
    cylinder('capacitor','Lower_capacitor',8,11.14,1.40,.82,3.95,'silver','capacitor')
    cylinder('capacitor','Lower_rear_collar',8,11.14,3.50,.87,.45,'steel','collar')
    cylinder('reservoir','Underbody_reservoir',8,9.92,1.14,.46,2.75,'silver','reservoir')
    cylinder('reservoir','Reservoir_front_socket',8,9.92,-.32,.51,.33,'black')
    for x in (7.40,8.60):
        beam('cleats',f'Front_yoke_{x}',[x,12.47,-8.92],[x,11.35,-8.54],.17,.31,'steel')
        beam('cleats',f'Capacitor_clamp_{x}',[x,12.02,.44],[x,10.12,1.10],.19,.29,'steel')
    box('rails','Lower_support_rail',[8,10.47,-4.87],[1.12,.31,6.62],'steel',motif='support')
    # Real hoses cross silver chambers and run along exposed forward rails.
    for x in (7.10,8.90):
        paths=[[(12.75,-.93),(11.94,.45),(12.85,1.60)],
               [(12.84,1.70),(11.98,3.12),(12.76,4.37)],
               [(12.06,-8.80),(11.57,-7.30),(11.74,-4.45),(12.10,-1.18)],
               [(10.95,-7.90),(10.70,-5.65),(10.87,-2.93),(10.10,-.02)]]
        for k,path in enumerate(paths):
            for j,(a,b) in enumerate(zip(path,path[1:])):
                beam('hoses',f'Hose_{x}_{k}_{j}',[x,*a],[x,*b],.125,.14,'rubber','hose')
    box('sight','Optic_rail_base',[8,13.57,1.78],[.89,.21,5.10],'steel',motif='rail')
    for i in range(7):
        box('sight',f'Rail_tooth_{i}',[8,13.73,-.34+i*.63],[1.03,.18,.30],'silver')
    box('sight','Reflex_foot',[8,13.94,2.64],[1.03,.25,1.09],'black')
    for x in (7.46,8.54):
        beam('sight',f'Reflex_upright_{x}',[x,14.02,2.44],[x,15.10,2.67],.18,.26,'optic','optic')
    box('sight','Reflex_roof',[8,15.11,2.67],[1.20,.18,.29],'optic',motif='optic')
    box('sight','Reflex_sill',[8,14.12,2.46],[1.16,.15,.37],'optic',motif='optic')
    box('sight','Reflex_adjustment',[7.21,14.52,2.76],[.34,.58,.58],'black',motif='dial')
    inputs=[BASE,BB,'art/weapons/w31/references.json','scripts/generate_surface_w123_beloved.py']
    return dict(stage='W130',id='erentil_fr4',family='fusion_rifle',revision='semantic-r1',source=meta,
        reference=reference,anchor=meta['anchor'],scale=meta['scale'],
        coordinate_mapping='[8+raw.Y*scale,8+raw.Z*scale,8-raw.X*scale]; negative native Z muzzle',
        method='Hand-authored filled semantic cuboids. No connected-island transplant, voxel geometry, alpha shell, triangle adapter, or split resources.',
        starting_draft='Approximately 110 structural parts planned; actual count includes filled octagonal cylinder facets, open muzzle rims, and hose paths.',
        palette=PALETTE,paint_evidence='Actual default photo: dark muted blue frame/stock, separated silver rails/chambers, black hoses, blue open reflex, OMOLON side mark. Raw diffuse is neutral material evidence only.',
        frame_policy='Source anchor/scale and native full display retained; grip center follows source. Existing ADS/generic reload/timing/audio and registration untouched.',
        parts=parts,groups=dict(collections.Counter(s['group'] for s in parts)),max_assembled_elements=1000,
        required_air_probes={'triangular_stock':[8,7.35,5.50],'trigger_guard':[8,9.65,5.10],
            'rail_gap':[8,11.88,-5.0],'lower_rail_separation':[8,11.18,-5.0],
            'reflex_window':[8,14.60,2.55],'upper_bore_entry':[8,12.72,-9.39],
            'upper_bore_depth':[8,12.72,-9.0],'near_bore':[7.48,11.18,-9.1]},
        contact_probes={'grip':[8,8.15,2.88],'stock_lower_brace':[8,5.80,5.35],
            'upper_rail':[8,12.72,-5.0],'near_rail':[7.48,11.18,-5.0]},
        input_sha256={s:sha((ROOT/s).read_bytes()) for s in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in [RAW/'Erentil FR4.fbx',RAW/'Erentil FR4.py',RAW/'Textures/2A76EB80_albedo.png',PHOTO,REFS]},
        limitations=['Static opaque authored finish, not recovered PBR or refraction.',
            'Reverse-side construction follows shared Omolon structure; small unobserved markings are omitted.',
            'One actual-photo reflex replaces source bundle alternative optic stack.',
            'Native resource parser, held views, ADS, generic reload/audio and multi-display QA pending master.'])

def face_points(e,face):return vertices(e)[list(FACES[face])]

def tile(spec,face,w,h):
    base=np.array(PALETTE[spec['material']],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    a=np.zeros((h,w,4),np.uint8);a[:,:,3]=255
    a[:,:,:3]=np.clip(base[None,None,:]*(.965+.035*np.sin(v*np.pi))[:,:,None],0,255)
    ps=face_points(spec['geometry'],face)
    world=ps[0]+u[:,:,None]*(ps[1]-ps[0])+v[:,:,None]*(ps[3]-ps[0])
    X,Y,Z=(world[:,:,i] for i in range(3));motif=spec['motif'];side=face in ('east','west')
    # End faces of intersecting filled cylinder facets share identical paint;
    # this prevents coplanar cap overlaps from producing a visible cross seam.
    cylindrical=('_facet_' in spec['geometry']['name'])
    if cylindrical and face in ('north','south'):a[:,:,:3]=base
    if spec['material'] in ('silver','steel','blue','blue_edge','optic') and not (cylindrical and face in ('north','south')):
        a[0,:,:3]=np.minimum(base+17,255);a[-1,:,:3]=base*.78
        if spec['material']=='silver':a[:,:,:3]=np.clip(a[:,:,:3]+1.5*np.sin(Y[:,:,None]*55),0,255)
    if motif in ('bands','chamber','capacitor','collar','reservoir'):
        for z in (-8.3,-7.87,-6.15,-5.94,-3.15,-2.94,-1.15,-.60,.05,3.01,3.19,4.48,4.64,5.05,13.45,14.45):
            mask=abs(Z-z)<.022;a[mask,:3]=base*.54
            a[(Z-z>.026)&(Z-z<.044),:3]=np.minimum(base+20,255)
        if motif in ('chamber','capacitor') and side:
            for z in (.35,2.90):
                for y in (12.60,11.20):
                    rr=np.hypot(Z-z,Y-y);a[rr<.047,:3]=[60,72,78]
    if motif=='capacitor':
        ribs=(Z>.10)&(Z<.72)&(np.mod(Z,.12)<.04);a[ribs,:3]=base*.58
    if motif in ('stock','omolon','web','grip','brace','stock_rail') and side:
        # Continuous inset edge, short supported scuffs, restrained blue grain.
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        a[(edge>1)&(edge<2.1),:3]=base*.62
        a[(edge>2.1)&(edge<3.2),:3]=np.minimum(base+15,255)
        if motif in ('stock','grip','omolon'):
            grain=(np.sin(Y*147+Z*71)*np.sin(Y*59-Z*129)> .93)
            a[grain,:3]=base*.80
            wear=(edge<3.5)&(np.sin(Z*14+Y*29)>.75)
            a[wear,:3]=np.minimum(base+35,255)
        if motif=='grip':
            line=Z-(1.85+(Y-4.78)*1.77/5.8)
            a[abs(line-.38)<.024,:3]=[15,28,36]
            a[abs(line+.36)<.02,:3]=[65,84,93]
        if motif in ('stock','omolon'):
            a[abs(Y-11.16)<.023,:3]=base*.6
            r=np.hypot(Z-(6.45 if motif=='omolon' else 13.90),Y-11.94)
            a[(r<.067)&(r>.038),:3]=[117,132,138];a[r<.033,:3]=[14,22,28]
        if motif=='web':a[np.mod(Y+.45*Z,.21)<.018,:3]=base*.82
        if motif=='brace':a[abs(Y-(4.67+(Z-1.88)*2.20/6.96))<.03,:3]=[36,60,73]
    if motif=='stock_rail' and face=='up':
        a[(abs(X-8)<.35)&(np.mod(Z-.23,1.10)<.18),:3]=[36,50,59]
    if motif=='support' and side:
        a[np.mod(Z+.27,1.30)<.055,:3]=[42,55,61]
        a[abs(Y-10.46)<.04,:3]=[147,159,164]
    if motif in ('pad','heel','cartridge') and side:
        a[np.mod(Y+.20*Z,.22)<.026,:3]=[44,52,58]
    if motif=='dial' and side:
        r=np.hypot(u-.5,v-.5);a[(r<.44)&(r>.32),:3]=[107,125,134]
        a[(r<.28)&(r>.23),:3]=[49,67,76];a[(abs(v-.5)<.035)&(r<.18),:3]=[146,157,162]
    im=Image.fromarray(a);dr=ImageDraw.Draw(im)
    if motif=='omolon' and side:
        size=max(8,min(23,int(h*.27)))
        font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',size=size)
        label='OMOLON';bounds=dr.textbbox((0,0),label,font=font);tw=bounds[2]-bounds[0]
        dr.text(((w-tw)/2,h*.49-bounds[1]),label,font=font,fill=tuple(PALETTE['white']))
        dr.rounded_rectangle((w*.17,h*.17,w*.57,h*.29),radius=2,fill='#71828a',outline='#a6b5bc',width=1)
    return im

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(18,25,31,255));requests=[]
    for spec in d['parts']:
        spec['geometry']['faces']={}
        for face in FACES:
            p=face_points(spec['geometry'],face);density=25 if spec['motif']=='omolon' else 17
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,spec['geometry']['name'],face,spec))
    requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;ledger=[]
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow')
        im=tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        spec['geometry']['faces'][face]=dict(uv=[q*16/EDGE for q in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,islands=ledger,used_texels=sum((q['pixels'][2]-q['pixels'][0])*(q['pixels'][3]-q['pixels'][1]) for q in ledger))
    model=dict(credit='W130 Erentil FR4 / semantic filled solids and authored per-face UV / offline candidate',
        textures={'0':'destiny:item/weapon/w123/erentil_fr4','particle':'destiny:item/weapon/w123/erentil_fr4'},
        elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])
    assert len(model['elements'])<=1000
    return atlas,model

def inspection(d,atlas,model):
    elements=[];groups=collections.defaultdict(list)
    for spec,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation')
        b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        elements.append(b);groups[spec['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Erentil FR4 W130 default-photo solids',
        resolution={'width':EDGE,'height':EDGE},elements=elements,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=v,export=True) for g,v in groups.items()],
        textures=[dict(name='erentil_fr4.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=model['display'],
        destiny_w130={'nativeAccepted':False,'anchor':d['anchor'],'scale':d['scale'],'fullOnly':True})

def comparison(d,meshes,atlas,model):
    w,h=1000,370;sheet=Image.new('RGB',(2000,2030),'#151e27');dr=ImageDraw.Draw(sheet)
    dr.text((22,13),'ERENTIL FR4 / W130 / DEFAULT PHOTO + AUTHORED SOLID VOLUMES',fill='#e7edf0',font_size=26)
    photo=Image.open(PHOTO).convert('RGB').crop((650,235,1810,895));photo.thumbnail((840,410));sheet.paste(photo,(20,52))
    count=len(model['elements'])
    lines=[f'{count} emitted solid cuboids / {count*6} explicit opaque UV faces',
        'Full-only candidate: weapon_surface_w123/erentil_fr4',
        'Dark muted blue frame / silver cylinders / black hoses',
        'Real triangle, rail separation, deep ports, open reflex',
        'Original FBX read: 38,969 triangles including alternatives',
        'LEFT BELOW: canonical W30, 222 cubes, alternate optic stack',
        'Canonical neutral texture is NOT the default-photo finish',
        'CPU art inspection only; native integration pending master']
    for i,line in enumerate(lines):dr.text((886,79+i*41),line,fill='#d1dee6',font_size=19)
    dr.text((22,475),'LOCAL CANONICAL / W30 / neutral historical texture',fill='#c0cfdb',font_size=21)
    dr.text((1022,475),f'NEW SEMANTIC SOLIDS / {count} CUBOIDS / actual-photo finish',fill='#e0eaf0',font_size=21)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/erentil_fr4.png'))
    arrays=[helper()['model_triangles']({'canonical':old},oldtex),helper()['model_triangles']({'full':model},atlas)]
    points=np.concatenate([*[vertices(e) for e in old['elements']],*[vertices(e) for e in model['elements']]])
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.38,-.65]),('REAR THREE-QUARTER',[1,.30,.62])]
    d['comparison_views']=[]
    for row,(label,cam) in enumerate(views):
        extent=helper()['frame'](points,cam,w,h)
        d['comparison_views'].append(dict(name=label,camera=cam,center=extent[0].tolist(),scale=float(extent[1]),viewport=[w,h]))
        for col,tris in enumerate(arrays):
            im,_=helper()['render'](tris,cam,extent,(w,h));sheet.paste(im,(col*w,512+row*h))
            dr.text((col*w+20,523+row*h),label,fill='#e1eaf0',font_size=19)
    for col,(label,groups,cam) in enumerate([
        ('THROUGH-PORTS / exposed rails',('muzzle','rails'),[-.35,.15,-1]),
        ('OPEN REFLEX / no alpha window',('sight',),[-.30,.10,-1]),
        ('TRIANGLE + GUARD / solid frame',('grip','guard','frame','stock'),[-1,.25,-.30])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups}
        subset={'elements':[e for e in model['elements'] if e['name'] in names and not (col==0 and 'rear_collar' in e['name'])]}
        ps=np.concatenate([vertices(e) for e in subset['elements']]);tris=helper()['model_triangles']({'detail':subset},atlas)
        im,_=helper()['render'](tris,cam,helper()['frame'](ps,cam,666,315),(666,315));sheet.paste(im,(col*666,1650))
        dr.text((col*666+14,1663),label,fill='#e0e9ef',font_size=18)
    dr.text((22,1992),'Same frame per comparison row. No native acceptance claim. Held/ADS/generic reload/audio/10-20 displays remain master QA.',fill='#ccd9e2',font_size=18)
    return png(sheet)

def review_text(d,model):
    n=len(model['elements'])
    return f'''# Erentil FR4 W130 — offline solid remodel

Actual default evidence: `{PHOTO}` and the Erentil entry in `{REFS}`; Bungie screenshot hash `{d['reference']['sha256']}`. The photograph was opened for inspection. Dark muted blue structural stock, silver multi-cylinder rails, crossing black chamber hoses, blue open reflex and readable OMOLON side mark are retained. Neutral raw albedo is not the finished dye.

This is a hand-authored reconstruction of functional solids, not a conversion of source connected islands or the W30 voxel model. **{n} filled cuboids, 0 triangle adapter elements, {n*6} opaque explicit face UVs**, one 1024 atlas. The four overlapping cuboids used per long cylinder tile a solid octagonal section; seams/collars, panel edging and supported markings are face paint. Open triangular frame, trigger area, separated forward rails, recessed muzzle ports and open reflex window are real air. No screws or tiny coplanar decal cubes were used to pad the count.

Source frame remains anchor `{d['anchor']}`, scale `{d['scale']}`. Native full display is copied exactly; the grip follows source position. Full-only candidate `{MODEL}`. Registration, Java, ADS resources, generic reload, timing and audio are unchanged. No invented body/magazine resource or custom graph. W30 contains an alternative optic stack; the authored model follows the actual photo's one open reflex.

`comparison.png` includes the actual-photo crop, clearly labeled canonical W30 with its neutral historical texture, new side/front/rear obliques on shared cameras, and port/reflex/triangle depth details. Original binary FBX 7500 was parsed read-only ({d['source']['raw_fbx_triangles']:,} original triangles including alternatives); transformed aggregate bounds match W30. The canonical column is not presented as original textured FBX or as a native render. `inspection.bbmodel` embeds the final editable solids, named groups, per-face UV and complete atlas.

Validation: generator `--verify` reproduces seven generated outputs including comparison and inspection; targeted unittest checks schema, emitted budget, UV bounds/gutters/opacity, reference pins, source frame/display, real openings and embedded inspection. See the worker report for executed results. Native resource loading and game behavior are pending master. CPU images do not certify native parsing, PBR, hand clipping, performance, audio or animations.

Limitations: opaque static finish; circular parts intentionally faceted. Reverse-side minor markings are omitted where the supplied photo gives no evidence. Glass/refraction and recovered PBR are not claimed.
'''

def generate():
    meshes,meta,reference=source_meshes();d=make_design(meta,reference);atlas,model=compile_model(d)
    comp=comparison(d,meshes,atlas,model);bb=inspection(d,atlas,model)
    products={MODEL:encode(model),TEXTURE:png(atlas),ART+'design.json':encode(d),
        ART+'inspection.bbmodel':encode(bb),ART+'comparison.png':comp,ART+'review.md':review_text(d,model).encode()}
    n=len(model['elements']);points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='erentil_fr4',stage='W130',family='fusion_rifle',model='destiny:weapon_surface_w123/erentil_fr4',
        counts={'full':n,'cubes':n,'triangle_adapter_elements':0,'assembled_emitted':n,'faces':n*6},
        groups=d['groups'],bounds=[points.min(0).round(6).tolist(),points.max(0).round(6).tolist()],
        atlas={'width':EDGE,'height':EDGE,'opaque':True,'explicit_face_islands':n*6},
        full_only=True,native_accepted=False,native_pending=['resource parser/pack load','first/third person hand contact',
            'ADS sight visibility','generic reload return/ammo timing','fusion charge/fire/muzzle/audio','10-20 simultaneous displays'],
        source_reference=reference,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        outputs={p:sha(b) for p,b in products.items()})
    products[ART+'manifest.json']=encode(manifest)
    return products

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate()
    if args.verify:
        bad=[p for p,b in outputs.items() if not (ROOT/p).is_file() or (ROOT/p).read_bytes()!=b]
        if bad:raise SystemExit('Deterministic verification mismatch: '+', '.join(bad))
        print(f'PASS deterministic --verify: {len(outputs)} products')
    else:
        for p,b in outputs.items():
            q=ROOT/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        m=json.loads(outputs[ART+'manifest.json']);print(json.dumps(m['counts'],sort_keys=True));print(f'Wrote {len(outputs)} owned products')

if __name__=='__main__':main()
