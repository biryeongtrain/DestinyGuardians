#!/usr/bin/env python3
"""W135 Falling Guillotine: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/falling_guillotine/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sword/falling_guillotine.json'
MODEL = ASSET + 'models/weapon_surface_w123/falling_guillotine.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/falling_guillotine.png'
REPORT = 'docs/qa/2026-10-26/w135/falling_guillotine-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/falling_guillotine/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/falling_guillotine.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(silver=[160,170,169],edge=[196,203,199],steel=[93,105,105],black=[30,38,39],rubber=[25,32,32],bronze=[104,85,53],teal=[42,95,94],recess=[11,20,23],energy=[234,214,157],orb=[204,217,218])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w135:falling_guillotine:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/falling_guillotine.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Falling Guillotine.fbx').read_bytes())==meta['source_files']['Falling Guillotine.fbx']
    roots=H['parse_fbx'](RAW/'Falling Guillotine.fbx');objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'};meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(p for c,p in links if c==node[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001) and props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in node[2]};v=np.array(cs['Vertices'][1][0]).reshape(-1,3)[:,[0,2,1]]*meta['scale']+meta['anchor']
        faces=[];face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:assert len(face)==3;faces.append(face);face=[]
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0);vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        mat=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=mat))
    points=np.concatenate([m['vertices'] for m in meshes]);assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-6)
    assert sum(len(m['faces']) for m in meshes)==12233
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
    # Broad filled blade body and separate shorter lower rail around real slot.
    box('blade_core',[7.59,12.00,7.37],[8.41,30.90,9.96],'teal','blade','contour')
    box('silver_long_edge',[7.66,13.95,9.92],[8.34,30.79,11.20],'silver','edge','metal')
    box('silver_spine',[7.71,13.20,4.61],[8.29,30.44,5.94],'silver','lower_blade','metal')
    box('lower_dark_panel',[7.58,14.13,5.00],[8.42,30.44,6.15],'steel','lower_blade','diagram')
    # Bevel shoulders retain real width through rotated filled beams.
    for sign in (-1,1):
        center(f'edge_bevel_{sign}',[8+sign*.33,22.30,11.18],[.20,16.90,.20],'edge','edge',turn=('y',45*sign))
        center(f'lower_bevel_{sign}',[8+sign*.29,22.02,4.62],[.20,16.82,.20],'edge','lower_blade',turn=('y',45*sign))
    # Flared hooked tip, stepped diagonal heel and discrete source teeth.
    beam('hook_tip',8,30.70,10.55,31.38,11.26,.48,'silver','tip')
    box('tip_upper',[7.62,30.56,9.23],[8.38,31.23,10.67],'silver','tip','metal')
    box('tip_end',[7.62,30.46,4.22],[8.38,31.36,4.66],'steel','tip','metal')
    beam('lower_tip',8,30.17,4.74,31.36,4.30,.36,'silver','tip')
    beam('upper_heel',8,11.45,10.92,14.05,10.53,.64,'silver','heel')
    beam('lower_heel',8,11.37,6.08,14.16,4.89,.72,'silver','heel')
    box('heel_core',[7.54,10.90,6.24],[8.46,14.04,10.52],'teal','heel','contour')
    # Inside energy path steps near heel; long slot remains air above16.3.
    beam('inside_transition',8,14.00,7.22,16.69,6.51,.41,'bronze','inner_path')
    box('inside_rail',[7.57,16.62,6.39],[8.43,30.46,6.69],'black','inner_path','rib')
    box('inner_back',[7.57,16.80,7.30],[8.43,30.52,7.51],'black','inner_path','rib')
    # Pale warm strips are matte texture color, not recovered animated emissive.
    for sign in (-1,1):
        x=8+sign*.43
        center(f'outer_energy_{sign}',[x,22.45,11.10],[.10,16.66,.10],'energy','energy')
        center(f'lower_energy_{sign}',[x,22.27,4.72],[.10,16.29,.11],'energy','energy')
        beam(f'energy_heel_{sign}',x,11.47,6.08,14.13,4.92,.11,'energy','energy')
        beam(f'energy_step_{sign}',x,14.02,7.12,16.71,6.58,.11,'energy','energy')
        center(f'inner_energy_{sign}',[x,23.55,6.61],[.10,13.78,.10],'energy','energy')
    # Continuous tilted lower inset is not a flat body shell; both outer rails filled.
    box('slot_recess',[7.77,17.0,6.80],[8.23,30.10,6.97],'recess','slot')
    # Crossguard/hand frame source anchor at [8,5.825,8], pommel and neck.
    box('guard',[7.40,10.35,5.93],[8.60,11.37,10.72],'black','guard','rib')
    center('guard_sweep',[8,10.58,10.69],[1.14,.60,.66],'steel','guard',turn=('x',-18))
    box('handle_core',[7.67,3.34,7.58],[8.33,10.44,8.42],'black','handle','handle')
    box('handle_neck',[7.56,9.67,7.47],[8.44,10.51,8.53],'steel','handle','bolt')
    box('pommel',[7.50,2.50,7.48],[8.50,3.46,8.54],'steel','handle','metal')
    # Black retaining bars above and below heel, shallow fasteners stay UV.
    for zz in (6.05,10.90):
        center('retainer_'+str(zz),[8,12.19,zz],[1.12,3.11,.26],'black','retainers','fasteners')
    for i in range(5):
        for zz in (4.51,11.34):
            center(f'tip_tooth_{i}_{zz}',[8,28.94+i*.29,zz],[.70,.12,.16],'silver','tip_teeth')
    # Raised slim fins around heel silhouette, rather than every small screw cube.
    for i in range(7):
        for zz in (5.87,11.05):
            center(f'heel_tooth_{i}_{zz}',[8,10.99+i*.44,zz],[1.03,.14,.28],'black','heel_teeth')
    def medallion(name,y,z,r):
        for sign in (-1,1):
            x=8+sign*.50
            # Filled octagonal crystal backed by actual thick central body.
            center(f'{name}_heart_{sign}',[x,y,z],[.15,r*1.42,r*1.42],'orb','insert','orb')
            for i in range(8):
                a=i*45;q=math.radians(a);cr=r*.79
                size=[.16,r*.43,2*r*math.tan(math.pi/8)+.015]
                if a%90==0:
                    if a%180:size=[size[0],size[2],size[1]]
                    turn=None
                else:turn=('x',45 if i%4==1 else -45)
                center(f'{name}_rim_{sign}_{i}',[x,y+cr*math.cos(q),z+cr*math.sin(q)],size,'orb','insert','orb',turn)
    medallion('large_insert',13.14,8.63,1.17)
    medallion('small_insert',14.91,8.22,.55)
    files=[BASE,'art/blockbench/weapons/w30/falling_guillotine.bbmodel','art/weapons/w31/references.json']
    rawfiles=[PHOTO,RAW/'Falling Guillotine.fbx',RAW/'FallingGuillotine_Diffuse.dds',RAW/'EnviousTouch_TiledDiffuse01.dds']
    return dict(id='falling_guillotine',stage='W135',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='[8+raw.X*s,5.825038936061844+raw.Z*s,8+raw.Y*s]',length='+Y',display='canonical exact'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['warm edge strips and pale inserts are static opaque color, not dynamic emission/animated Taken shader','small rivets/diagram/wear are faceUV, not individually modeled','hand/thirdperson/swing/guard/native20displays pending'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    e=spec['geometry'];u,v,q=world_points(e,face,w,h);role=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy();side=face in ('east','west')
    rgb*=(.97+.055*np.exp(-((v-.3)/.4)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.7]*=.75;rgb[(edge>=.7)&(edge<1.4)]*=1.08
    if motif=='contour':
        raw=np.asarray(Image.open(RAW/'EnviousTouch_TiledDiffuse01.dds').convert('RGB'));tx=np.mod((q[:,:,2]-6)*65,256).astype(int);ty=np.mod((q[:,:,1]-10.5)*47,256).astype(int);lum=raw[ty,tx].mean(2)/255
        # Actual source contour tile reinterpreted into default teal/bronze, not undyed gray.
        rgb[:]=[79,69,45];rgb[lum<.19]=[23,37,35];rgb[(lum>=.19)&(lum<.29)]=[40,91,88];rgb[lum>.43]=[114,99,64]
    if motif in ('metal','diagram'):
        rgb*=(.97+.015*np.sin(q[:,:,1]*4+q[:,:,2]*10))[:,:,None]
        if motif=='diagram' and side:
            rgb[(np.mod(q[:,:,1]*.45,1)<.012)&(q[:,:,2]<5.8)]*=1.25
            for yy in np.arange(14.5,29.9,.42):
                for zz in (5.65,5.91):
                    rr=np.hypot(q[:,:,1]-yy,q[:,:,2]-zz);rgb[rr<.055]=PALETTE['recess'];rgb[(rr>=.055)&(rr<.071)]=PALETTE['edge']
    if motif in ('rib','handle'):
        rgb[np.mod(q[:,:,1]*4,1)<.23]*=.59
        if motif=='handle' and side:
            raw=np.asarray(Image.open(RAW/'EnviousTouch_TiledDiffuse01.dds').convert('RGB'));tx=np.mod(q[:,:,2]*95,256).astype(int);ty=np.mod(q[:,:,1]*45,256).astype(int);lum=raw[ty,tx].mean(2)/255;rgb[:]=[52,65,57];rgb[lum<.22]=[25,35,31];rgb[lum>.43]=[99,89,58]
            rgb[(np.mod(q[:,:,1]*3.1,1)<.19)&(abs(q[:,:,2]-8)<.20)]=PALETTE['steel']
    if motif=='fasteners' and side:
        for yy in np.arange(10.9,13.6,.39):
            rr=np.hypot(q[:,:,1]-yy,q[:,:,2]-e['from'][2]-.13);rgb[rr<.09]=PALETTE['steel'];rgb[rr<.035]=PALETTE['black']
    if motif=='orb':
        rgb[:]=np.array(PALETTE['orb'],float);rgb*=(.97+.025*np.sin(q[:,:,1]*4)*np.cos(q[:,:,2]*5))[:,:,None]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=17
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
    model=dict(credit='Falling Guillotine W135 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/falling_guillotine','particle':'destiny:item/weapon/w123/falling_guillotine'},
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
        name='Falling Guillotine W135 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='falling_guillotine.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w135=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    result=[];textures={}
    for m in meshes:
        mat=m['material']
        if mat not in textures:
            textures[mat]=np.asarray(Image.open(RAW/'FallingGuillotine_Diffuse.dds').convert('RGBA')) if mat=='FallingGuillotine' else np.array([[[45,65,61,255]]],np.uint8)
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((t,uv,textures[mat],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=600,1050;sheet=Image.new('RGB',(1800,1750),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,14,'FALLING GUILLOTINE / W135 / FILLED BLADE VOLUMES + AUTHORED FACE UV',26)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1000,540));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / no alpha body shells','Original paired blade / actual inner slot','Source contour tile -> teal / bronze interpretation','Pale warm strips and inserts: static matte, NOT glow','Canonical sword display / hand anchor retained','CPU comparison, NOT native gameplay acceptance']):label(980,110+i*54,line,22)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/falling_guillotine.png'))
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes]);labels=['RAW FBX / UNDYED + ENERGY NEUTRAL','CANONICAL / 194 CUBOIDS / READ ONLY',f'NEW / {len(model["elements"])} SOLID CUBOIDS']
    # Vertical sword gets a portrait frame, not a rifle-height strip that clips tips.
    for col,tris in enumerate(ts):
        im,_=H['render'](tris,[1,0,0],H['frame'](points,[1,0,0],w,h),(w,h),raw=col==0);sheet.paste(im,(col*w,570));label(col*w+10,540,labels[col],17)
    label(20,1645,'Source hand frame [8,5.825,8], raw X/Z/Y mapping; no combat/animation/audio changes.',20)
    label(20,1690,'Editable BB and actual oblique review separate. Held/swing/guard/10-20 scene native checks pending.',20)
    return png(sheet)


def review_text(d,counts):
    return f"""# Falling Guillotine W135 — master art

{len(d['parts'])} opaque meaningful cuboids. Broad filled paired silver blades, physical central inset/slot and stepped heel, hooked tips and selective silhouette teeth; black guard/retainers and source hand anchor. Large and small pale raised circular inserts are filled octagons. Actual EnviousTouch source contour tile is resampled in continuous authored face UV and reinterpreted in photo-based teal/bronze. Small fasteners, shallow dimples and diagrams are UV, not source islands or alpha shells.

Read-only original FBX retained two source objects/12233 triangles in original X/Z/Y frame and anchor[8,5.825038936061844,8]; no assumption of gun -Z length. Raw diffuse is neutral and second energy object has labeled neutral reference, not default-dye recovery. Warm edge strips/pale inserts are static matte RGBA, not dynamically emissive, original PBR or animated Taken effects. Generic sword combat/swing/guard/ammo/audio, canonical display/scale and hand frame unchanged. CPU portrait comparisons/BB are offline evidence only. Native held/thirdperson/swing/guard and10-20display pending.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='falling_guillotine',revision='W135',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
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
    outputs=generate();scope=json.loads((ROOT/'docs/qa/2026-10-26/w135/scope.json').read_bytes());assert set(outputs)<=set(scope['owned_paths'])
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
