#!/usr/bin/env python3
"""W133 First In, Last Out: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/first_in_last_out/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/shotgun/first_in_last_out.json'
MODEL = ASSET + 'models/weapon_surface_w123/first_in_last_out.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/first_in_last_out.png'
REPORT = 'docs/qa/2026-10-26/w133/first_in_last_out-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/first_in_last_out/extracted/First In, Last Out')
PHOTO = Path('/tmp/destiny-weapons-w31/references/first_in_last_out.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(teal=[41,119,129], white=[198,205,201], steel=[116,125,128], edge=[153,163,165], graphite=[45,50,52], recess=[14,22,25], rubber=[29,33,35])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w133:first_in_last_out:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/first_in_last_out.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'First In, Last Out.blend').read_bytes())=='04aecd1d21839391e1528e8ceddda78cdc73b74b49788cfeff39b04875639377'
    data=json.loads((ROOT/(ART+'source-meshes.json')).read_bytes());meshes=[]
    assert {m['name'] for m in data}==set(meta['source_objects'])
    for m in data:
        v=np.array(m['vertices'])[:,[0,2,1]]*meta['scale']+meta['anchor']
        faces=np.array(m['faces']);uv=np.array(m['uv']);materials=np.array(m['material'])
        for mat in sorted(set(materials)):
            keep=materials==mat
            meshes.append(dict(name=m['name']+':'+mat,vertices=v,faces=faces[keep],uv=uv[keep],material=mat))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-6)
    assert sum(len(m['faces']) for m in meshes)==8040
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
    def tube(name,x,y,z0,z1,r,t,mat,group,motif='ring'):
        for i in range(8):
            a=i*45; q=math.radians(a);cr=r-t/2
            size=[2*r*math.tan(math.pi/8)+.015,t,z1-z0]
            turn=None
            if a%90==0:
                if a%180:size=[size[1],size[0],size[2]]
            else:turn=('z',45 if i%4==1 else -45)
            center(f'{name}_{i}',[x-cr*math.sin(q),y+cr*math.cos(q),(z0+z1)/2],size,mat,group,motif,turn)
    def beam(name,x,y0,z0,y1,z1,w,mat,group,motif='plain'):
        length=math.hypot(y1-y0,z1-z0);angle=-math.degrees(math.atan2(y1-y0,z1-z0))
        if abs(angle)>90: angle=angle-180 if angle>0 else angle+180
        center(name,[x,(y0+y1)/2,(z0+z1)/2],[w,w,length],mat,group,motif,('x',angle))
    # Filled SUROS body and broad bevel shoulders, not alpha side shells.
    box('shroud_main',[7.30,10.46,-5.75],[8.70,12.17,4.84],'teal','shroud','shroud')
    box('front_roof',[7.44,11.94,-8.03],[8.56,12.17,-5.73],'teal','shroud','shroud')
    for sign in (-1,1):
        box(f'front_wall_{sign}',[8+sign*.62-.08,10.46,-8.03],[8+sign*.62+.08,12.02,-5.73],'teal','shroud','shroud')
    box('action_roof',[7.30,11.60,4.82],[8.70,12.17,7.54],'teal','shroud','shroud')
    box('action_rear',[7.30,10.46,7.19],[8.70,11.62,7.54],'teal','shroud','shroud')
    box('shroud_roof',[7.58,12.13,-7.98],[8.42,12.44,7.37],'teal','shroud','shroud')
    for sign in (-1,1):
        center(f'shoulder_{sign}',[8+sign*.60,12.17,-.26],[.34,.34,15.42],'teal','shroud','shroud',('z',45*sign))
        box(f'shroud_skirt_{sign}',[8+sign*.62-.08,10.15,-7.94],[8+sign*.62+.08,10.49,4.28],'teal','shroud','shroud')
    # Recessed action under short upper bridge.
    box('rear_bridge',[7.30,10.46,7.52],[8.70,12.20,8.45],'teal','action','shroud')
    box('receiver_core',[7.39,10.42,3.9],[8.61,10.61,9.38],'graphite','receiver','seam')
    box('action_inner',[7.55,10.60,5.30],[8.45,11.57,7.20],'recess','action')
    box('bolt',[7.51,10.72,5.26],[8.49,10.89,7.18],'steel','action')
    for sign in (-1,1):
        center(f'action_rail_{sign}',[8+sign*.64,10.63,6.26],[.18,.16,2.20],'steel','action')
    # True upper and lower bores; back walls are set back from front lip.
    tube('barrel',8,11.40,-8.28,-5.85,.54,.14,'graphite','muzzle')
    tube('upper_lip',8,11.40,-8.37,-8.12,.64,.16,'steel','muzzle')
    center('barrel_depth',[8,11.40,-5.81],[.78,.78,.12],'recess','muzzle')
    tube('magazine_tube',8,9.96,-8.25,3.96,.48,.15,'graphite','foreend')
    tube('lower_lip',8,9.96,-8.36,-8.05,.55,.18,'steel','muzzle')
    center('magazine_recess',[8,9.96,-7.81],[.60,.60,.12],'recess','muzzle')
    for sign in (-1,1):
        center(f'front_cheek_{sign}',[8+sign*.68,10.73,-8.22],[.23,1.62,.28],'steel','muzzle','cap')
    center('cap_bridge',[8,10.64,-8.25],[1.01,.22,.25],'steel','muzzle')
    center('cap_bottom',[8,9.37,-8.22],[.76,.23,.28],'steel','muzzle')
    # Perforated fore-end dimples are UV; broad surrounding material is solid.
    box('foreend_belly',[7.64,9.45,-6.85],[8.36,9.85,1.13],'graphite','foreend','vents')
    for sign in (-1,1):
        center(f'foreend_side_{sign}',[8+sign*.47,9.93,-2.93],[.16,.72,7.88],'graphite','foreend','vents')
    tube('silver_sleeve',8,10.01,1.08,3.38,.58,.16,'steel','foreend','sleeve')
    box('rear_receiver',[7.39,10.04,7.30],[8.61,11.69,9.36],'graphite','receiver','seam')
    center('rear_shoulder',[8,11.34,8.79],[1.17,1.54,1.48],'steel','receiver',turn=('x',-22))
    center('grip_core',[8,8.88,8.53],[1.03,3.96,1.04],'graphite','grip','grip',('x',-18))
    for sign in (-1,1):
        center(f'grip_panel_{sign}',[8+sign*.55,8.63,8.64],[.13,3.35,1.04],'rubber','grip','rib',('x',-18))
    center('grip_heel',[8,7.02,9.17],[1.13,.34,1.25],'steel','grip',turn=('x',-18))
    beam('guard_front',8,10.43,6.54,9.62,6.43,.20,'steel','guard')
    beam('guard_bottom',8,9.62,6.43,9.56,7.53,.20,'steel','guard')
    beam('guard_rear',8,9.56,7.53,10.26,7.88,.20,'steel','guard')
    beam('trigger',8,10.37,7.29,9.89,7.17,.13,'graphite','guard')
    # Actual open stock window, substantial diagonal neck below.
    beam('stock_neck',8,10.56,9.27,9.44,12.88,.93,'steel','stock','seam')
    beam('stock_heel',8,9.42,12.54,8.92,15.93,1.05,'graphite','stock','seam')
    center('buttpad',[8,10.08,16.25],[1.32,3.33,.62],'rubber','stock','rib',('x',-5))
    center('cheek_roof',[8,12.06,14.59],[1.53,.50,3.24],'white','cheek','cheek')
    for sign in (-1,1):
        x=8+sign*.68
        center(f'cheek_topside_{sign}',[x,11.72,14.61],[.22,.53,3.21],'teal','cheek','cheek')
        center(f'cheek_front_{sign}',[x,11.50,13.07],[.22,.58,.27],'teal','cheek')
        center(f'cheek_rear_{sign}',[x,10.90,15.88],[.22,1.77,.61],'teal','cheek','cheek')
        center(f'cheek_rear_panel_{sign}',[x,10.98,15.33],[.24,1.96,1.52],'teal','cheek','cheek')
        center(f'cheek_bevel_{sign}',[x,11.74,14.75],[.24,.39,.65],'white','cheek',turn=('x',-22))
        beam(f'cheek_sweep_{sign}',x,11.46,14.73,10.19,15.65,.23,'teal','cheek')
    box('sight_rail',[7.64,12.43,3.32],[8.36,12.53,5.82],'steel','sight','rail')
    box('sight_blade',[7.82,12.52,4.91],[8.18,12.66,5.39],'graphite','sight')
    center('bolt_handle',[8.72,10.96,7.54],[.27,.61,.25],'steel','controls',turn=('x',8))
    for sign in (-1,1):
        center(f'cap_screw_{sign}',[8+sign*.79,10.66,-8.10],[.08,.19,.22],'edge','controls','bolt')
    files=[BASE,'art/blockbench/weapons/w30/first_in_last_out.bbmodel','art/weapons/w31/references.json',ART+'source-meshes.json',ART+'readonly-extract.py']
    rawfiles=[PHOTO,RAW/'First In, Last Out.blend',RAW/'Barrel_Diffuse.dds',RAW/'Stock_Diffuse.dds']
    return dict(id='first_in_last_out',stage='W133',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='[8+world.X*s,8+world.Z*s,8+world.Y*s]',muzzle='-Z',display='canonical exact'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['small fore-end dimples are opaque UV, not physical perforations','photo-sampled SUROS and phoenix on evidenced east side only; no invented reverse decal','static matte paint, no PBR reconstruction','generic reload/native held/ADS and20 displays pending'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def decal(q,rgb,pathbox,z0,z1,y0,y1,quad=None):
    im=Image.open(PHOTO).convert('RGB')
    if quad: im=im.transform((200,90),Image.Transform.QUAD,quad,Image.Resampling.BICUBIC)
    else: im=im.crop(pathbox)
    px=np.asarray(im);mask=(px.min(2)>125)&((px.max(2)-px.min(2))<40)
    xx=((z1-q[:,:,2])/(z1-z0)*mask.shape[1]).astype(int);yy=((y1-q[:,:,1])/(y1-y0)*mask.shape[0]).astype(int)
    keep=(xx>=0)&(xx<mask.shape[1])&(yy>=0)&(yy<mask.shape[0]);sample=mask[np.clip(yy,0,mask.shape[0]-1),np.clip(xx,0,mask.shape[1]-1)]
    rgb[keep&sample]=PALETTE['white']


def tile(spec,face,w,h):
    role=spec['material'];motif=spec['motif'];e=spec['geometry'];u,v,q=world_points(e,face,w,h)
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.97+.045*np.exp(-((v-.30)/.35)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.65]*=.76;rgb[(edge>=.65)&(edge<1.3)]*=1.09
    side=face in ('east','west')
    if motif=='shroud':
        if side:
            rgb[q[:,:,1]<10.45]=PALETTE['white']
            if face=='east':
                decal(q,rgb,None,-.3,2.2,10.53,11.12,quad=(1155,504,1155,527,1241,508,1241,486))
                decal(q,rgb,(1466,351,1539,475),7.25,8.38,10.56,12.24)
            for zz,yy in [(-7.36,11.72),(-6.98,11.72),(-7.18,11.40),(-6.79,11.40)]:
                dist=np.hypot(q[:,:,2]-zz,q[:,:,1]-yy);rgb[dist<.045]=PALETTE['recess'];rgb[(dist>=.045)&(dist<.067)]=PALETTE['edge']
    if motif=='vents':
        for yy in (9.69,9.94,10.19):
            for zz in np.arange(-6.40,.95,.48):
                rr=np.hypot(q[:,:,2]-zz,q[:,:,1]-yy)
                rgb[rr<.045]=PALETTE['recess'];rgb[(rr>=.045)&(rr<.068)]=PALETTE['steel']
    if motif in ('rib','grip'):
        if motif=='rib':rgb[np.mod(q[:,:,1]*4,1)<.22]*=.62
        else:rgb[(u>.12)&(u<.88)&(v>.13)&(v<.90)]*=.80
    if motif in ('seam','sleeve') and side:rgb[(v>.10)&(v<.135)&(u>.07)&(u<.93)]*=.65
    if motif=='cheek' and side:
        rgb[(q[:,:,1]>11.75)|((q[:,:,2]>15.12)&(q[:,:,1]>11.25))]=PALETTE['white']
        rgb[(q[:,:,2]>15.22)&(q[:,:,2]<16.08)&(q[:,:,1]>11.1)&(q[:,:,1]<11.25)]=PALETTE['recess']
    if motif=='rail':rgb[np.mod(q[:,:,2]*6,1)<.30]*=.56
    if motif=='bolt':
        rr=np.hypot(u-.5,v-.5);rgb[rr<.30]=PALETTE['graphite']
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
    model=dict(credit='First In, Last Out W133 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/first_in_last_out','particle':'destiny:item/weapon/w123/first_in_last_out'},
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
        name='First In, Last Out W133 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='first_in_last_out.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w133=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


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
    label(20,14,'FIRST IN, LAST OUT / W133 / SOLID SEMANTIC VOLUMES + AUTHORED FACE UV',29)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((900,470));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / full model only',
        'Teal-white SUROS shroud / silver cap / black fore-end',
        'Two real bores / recessed action / guard / open stock',
        'SUROS and phoenix sampled from actual default photo',
        'Native display/ADS/generic reload unchanged',
        'Original frame: [8+world.X*s,8+world.Z*s,8+world.Y*s]',
        'Offline CPU art comparison; native pending']):label(1000,100+i*48,line,24)
    label(20,550,'RAW BLEND / UNDYED DIFFUSE / AMMO NEUTRAL',22);label(w+20,550,'OLD CANONICAL / 226 CUBOIDS / READ ONLY',22);label(w*2+20,550,f'NEW SEMANTIC SOLIDS / {len(model["elements"])} CUBOIDS',22)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/first_in_last_out.png'))
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT OBLIQUE',[1,.4,-.62]),('REAR OBLIQUE',[-1,.3,.6])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,590+row*h));label(col*w+15,598+row*h,name,18)
    return png(sheet)


def review_text(d,counts):
    return f"""# First In, Last Out W133 — master art

{len(d['parts'])} opaque semantic cuboids. Long filled SUROS teal shroud with bevel shoulders, real upper/lower front bore depth, recessed bolt/action, open trigger guard and open raised cheek stock. Tiny fore-end dimples are authored opaque recess UV, not through holes. Default teal/white/black/silver from actual W31 photo; white SUROS wordmark and phoenix sampled from that photo on evidenced side only. No invented reverse decal, alpha body shells, triangle adapters or raw island transplant.

Original .blend opened in separate headless factory-startup Blender with autoexec disabled, read only. Retained9 source objects/8040 triangles exported to inert JSON; original unchanged, user GUI scene untouched. Barrel/Stock undyed diffuse is comparison evidence only; BattlerAmmo uses labeled neutral fallback. Generator uses inert extraction for comparison, not procedural remeshing.

Canonical full display/anchor/scale/muzzle, generic reload, ADS, combat, timing and audio unchanged. Static matte interpretation, not original PBR. CPU comparison and editable BB are not live rendering evidence. Native held/ADS/reload/download and20display pending.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='first_in_last_out',revision='W133',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
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
    outputs=generate();scope=json.loads((ROOT/'docs/qa/2026-10-26/w133/scope.json').read_bytes());assert set(outputs)<=set(scope['owned_paths'])
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
