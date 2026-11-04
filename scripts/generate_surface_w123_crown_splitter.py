#!/usr/bin/env python3
"""W136 Crown-Splitter: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/crown_splitter/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/sword/crown_splitter.json'
MODEL = ASSET + 'models/weapon_surface_w123/crown_splitter.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/crown_splitter.png'
REPORT = 'docs/qa/2026-10-26/w136/crown_splitter-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/crown_splitter/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/crown_splitter.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(steel=[150,159,164], edge=[210,216,213], bevel=[178,186,188],
               dark=[39,47,53], recess=[30,39,45], navy=[17,25,39], wrap=[198,204,199])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w136:crown_splitter:'+name))


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
    """Inert evidence only: FBX local translation 10cm must precede W30 basis.
    Blender W30 bounds include this translation. Never execute the blend file.
    """
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/crown_splitter.bbmodel').read_bytes())['destiny_w30']
    for name,digest in meta['source_files'].items():
        assert sha((RAW/name).read_bytes())==digest, name
    roots=H['parse_fbx'](RAW/'Crown-Splitter.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(p for c,p in links if c==node[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=2e-5,rtol=0)
        assert props['Lcl Scaling']==[100,100,100] and props['Lcl Translation']==[0,10,0]
        cs={c[0]:c for c in node[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        # FBX centimeters: Y translation10/scale100 becomes +.1 in blade Y.
        native=raw[:,[0,2,1]].copy();native[:,1]+=.1
        v=native*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]);assert np.all((ix<0).reshape(-1,3)==[False,False,True])
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0);vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        mat=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=faces,uv=uv,material=mat))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==4240
    catalogue=json.loads((ROOT/'src/main/resources/destiny/weapons/w30.json').read_bytes())
    assert next(w for w in catalogue if w['id']=='crown_splitter')['family']=='sword'
    return meshes,meta


def make_design(meta):
    parts=[]
    def box(name,lo,hi,mat,group,motif='metal',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='metal',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(pos,size)],[round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name,y0,z0,y1,z1,thickness,width,mat,group,motif='metal'):
        angle=math.degrees(math.atan2(z1-z0,y1-y0))
        c(name,[8,(y0+y1)/2,(z0+z1)/2],[thickness,math.hypot(y1-y0,z1-z0),width],mat,group,motif,('x',angle))
    def collar(name,y,length,r,mat,group):
        # Filled octagonal section: center + four solid bevels. No hollow tube.
        c(name+'_core',[8,y,8],[r*1.54,length,r*1.54],mat,group)
        for i,(sx,sz) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
            c(name+'_facet_'+str(i),[8+sx*r*.59,y,8+sz*r*.59],[r*.64,length,r*.64],mat,group,turn=('y',45))
    # Long solid shoulders are split by a true shallow fuller, never an alpha slit.
    # Central web is fully opaque through the blade's thickness.
    box('fuller_web',[7.934,11.32,7.78],[8.066,29.00,8.22],'recess','blade','fuller')
    for sign in (-1,1):
        c('blade_shoulder_'+str(sign),[8,20.03,8+sign*.30],[.43,17.96,.43],'steel','blade','blade')
        beam('blade_outer_mass_'+str(sign),11.97,8+sign*.70,28.90,8+sign*.39,.34,.50,'steel','blade','blade')
        beam('cutting_edge_'+str(sign),11.96,8+sign*.945,28.90,8+sign*.628,.11,.145,'edge','edge','edge')
        # Actual narrow cross-section facets down to the bright cutting edge.
        beam(f'blade_bevel_{sign}',11.97,8+sign*.865,28.90,8+sign*.548,.22,.18,'bevel','edge','edge')
        beam(f'blade_fine_bevel_{sign}',11.97,8+sign*.920,28.90,8+sign*.603,.16,.10,'bevel','edge','edge')
    for sign in (-1,1):
        beam('fuller_start_'+str(sign),11.48,8,12.50,8+sign*.12,.43,.12,'steel','blade','blade')
        beam('fuller_end_'+str(sign),28.55,8+sign*.12,29.13,8,.30,.10,'steel','tip','blade')
    # Broad flared ricasso/heel, distinct from the blade taper.
    box('ricasso',[7.595,9.38,7.56],[8.405,11.34,8.44],'dark','heel','heel')
    box('heel_shoulder',[7.70,11.18,7.28],[8.30,12.06,8.72],'steel','heel','blade')
    for sign in (-1,1):
        beam('heel_flare_'+str(sign),10.52,8+sign*.47,12.01,8+sign*.88,.50,.22,'steel','heel')
        beam('heel_edge_'+str(sign),10.59,8+sign*.51,12.02,8+sign*.982,.12,.105,'edge','heel','edge')
        c('guard_root_strut_'+str(sign),[8,9.73,8+sign*.59],[.76,.94,.12],'bevel','heel','edge',('x',sign*-22))
    # Point: three filled successively narrower masses with two converging edges.
    box('tip_base',[7.85,28.72,7.55],[8.15,29.48,8.45],'steel','tip','blade')
    box('tip_mid',[7.89,29.46,7.71],[8.11,30.38,8.29],'steel','tip','blade')
    box('tip_core',[7.947,30.34,7.90],[8.053,31.26,8.10],'steel','tip','blade')
    for sign in (-1,1):
        beam('point_shoulder_'+str(sign),28.95,8+sign*.44,31.33,8+sign*.035,.20,.25,'steel','tip','blade')
        beam('point_edge_'+str(sign),28.91,8+sign*.606,31.46,8+sign*.018,.078,.08,'edge','tip','edge')
    # Palm guard: thick load bearing central block, tapering feather fingers.
    box('guard_root',[7.528,9.24,7.41],[8.472,9.74,8.59],'dark','guard','heel')
    for sign in (-1,1):
        beam('wing_root_'+str(sign),9.55,8+sign*.48,9.95,8+sign*2.38,.46,.25,'steel','guard')
        for i in range(6):
            z=8+sign*(.72+i*.32);bottom=9.43+i*.07;top=10.00+i*.105
            c(f'feather_{sign}_{i}',[8,(bottom+top)/2,z],[.48-i*.047,top-bottom,.295],'bevel','guard','feather')
            # Terminal bevels shape the stepped silhouette, not tiny rivet cubes.
            c(f'feather_crown_{sign}_{i}',[8,top-.017,z],[.40-i*.042,.085,.27],'edge','guard','edge',('x',sign*-15))
    # Source hand frame centered [8,4.9901939311,8]. Solid blue leather grip.
    box('grip_core',[7.737,3.31,7.704],[8.263,9.26,8.296],'navy','grip','leather')
    for sign in (-1,1):
        c('grip_spine_'+str(sign),[8+sign*.26,6.28,8],[.11,5.93,.55],'navy','grip','wrap',('y',sign*28))
        c('grip_side_'+str(sign),[8,6.28,8+sign*.29],[.51,5.93,.11],'navy','grip','wrap',('y',sign*28))
    collar('grip_ferrule',9.15,.28,.39,'bevel','ferrule')
    collar('pommel_band',3.24,.28,.34,'edge','pommel')
    collar('pommel',2.98,.32,.30,'dark','pommel')
    # Dark tapered terminal rather than invented ammunition/moving assemblies.
    c('pommel_tip',[8,2.67,8],[.24,.34,.24],'bevel','pommel',turn=('y',45))
    files=[BASE,'art/blockbench/weapons/w30/crown_splitter.bbmodel','art/weapons/w31/references.json',
           'src/main/resources/destiny/weapons/w30.json',HELPER]
    rawfiles=[PHOTO,RAW/'Crown-Splitter.fbx',RAW/'Crown-Splitter.blend',RAW/'Textures/Crown-Splitter_Diffuse.dds']
    return dict(id='crown_splitter',stage='W136',family='sword',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='anchor + scale * [raw.X, raw.Z + 0.1, raw.Y]',
            fbx_translation_cm=[0,10,0],fbx_rotation_deg=[-90,0,0],fbx_scale=[100,100,100],length='+Y',display='canonical exact',
            validation='both source names,4240 triangles and all W30 bounds match within 2e-6; without translation bounds miss by1.8285109194'),
        construction='authored semantic filled cuboids; no source island/voxel conversion; no alpha silhouettes',
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['cuboid point and bevels approximate original smooth taper; small edge nicks and leather cross wraps are face paint',
            'static opaque colors approximate photographed steel/leather; no original PBR or dynamic reflection recovery',
            'offline CPU views are not native acceptance; held/thirdperson/swing/guard/10-20display QA pending master'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    e=spec['geometry'];u,v,q=world_points(e,face,w,h);role=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    # Quiet broad material with limited directional polish; no noisy rip projection.
    rgb*=(.985+.018*np.sin(q[:,:,1]*.7+q[:,:,2]*2.0))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    if spec['group'] not in ('blade','edge','tip'):rgb[edge<.6]*=.94
    y=q[:,:,1];z=q[:,:,2];side=face in ('east','west')
    if motif=='blade' and side:
        # Long fine steel scoring stays continuous in model coordinates.
        rgb[np.mod(z*40+y*.035,1)<.045]*=.92
        for yy,zz in ((13.1,7.18),(17.2,8.79),(22.0,7.25),(26.7,8.65)):
            mark=(abs(y-yy)<.20)&(abs(z-zz-(y-yy)*.20)<.018);rgb[mark]*=.64
    if motif=='fuller':
        rgb*=.82;rgb[np.minimum(abs(z-7.92),abs(z-8.08))<.022]=PALETTE['bevel']
    if motif=='edge':
        # Sparse small edge bites from the photograph, no geometric saw teeth.
        for yy in (14.2,18.8,23.8,28.2):
            rgb[(abs(y-yy)<.055)&(v>.6)]*=.70
    if motif in ('leather','wrap'):
        rgb*=(.98+.016*np.sin(y*35+z*7))[:,:,None]
        # White cross bindings at both grip ends, mapped around actual grip.
        band=((y>3.57)&(y<4.23))|((y>8.26)&(y<9.02))
        period=np.mod((y-3.55)*1.4,1);across=np.clip((z-7.60)/.8,0,1)
        cross=(abs(period-across)<.17)|(abs(period-(1-across))<.17)
        if side:rgb[band&cross]=PALETTE['wrap']
        else:rgb[band&(np.mod(y*2.8+q[:,:,0]*.7,1)<.36)]=PALETTE['wrap']
    if motif=='feather' and side:
        # Each guard finger has its own broad island and recessed lower flute.
        rgb[(u>.30)&(u<.39)&(v>.20)&(v<.87)]*=.65
        rgb[(u>.40)&(u<.46)&(v>.22)&(v<.85)]*=1.12
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(28,36,44,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=21
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
    model=dict(credit='Crown-Splitter W136 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/crown_splitter','particle':'destiny:item/weapon/w123/crown_splitter'},
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
        name='Crown-Splitter W136 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='crown_splitter.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w136=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    tex=np.asarray(Image.open(RAW/'Textures/Crown-Splitter_Diffuse.dds').convert('RGBA'));result=[]
    for m in meshes:
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
            if length>1e-10:result.append((t,uv,tex,n/length))
    return result


def comparison(d,meshes,atlas,model):
    w,h=600,710;sheet=Image.new('RGB',(1800,2100),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'CROWN-SPLITTER / W136 / SOLID STEEL BLADE + DEFAULT BLUE LEATHER',25)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((940,460));sheet.paste(photo,(0,49))
    for i,line in enumerate([f'{len(model["elements"])} filled opaque cuboids / 1024 face atlas',
        'Steel shoulders + inset fuller with solid central web',
        'Stepped wing guard / blue grip / pale cross bindings',
        'FBX local +10cm translation INCLUDED before W30 scale',
        'Canonical +Y sword / exact hand and display frame',
        'CPU study only: native held / swing / guard pending']):label(920,94+i*54,line,20)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/crown_splitter.png'))
    triangles=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    labels=['RAW FBX / UNDYED ALBEDO','CANONICAL /148 CUBOIDS / READ ONLY',f'NEW /{len(model["elements"])} FILLED CUBOIDS']
    for row,cam in enumerate(([1,0,0],[.73,.10,.68])):
        yy=540+row*750
        for col,ts in enumerate(triangles):
            label(col*w+10,yy-26,labels[col],17)
            im,_=H['render'](ts,cam,H['frame'](points,cam,w,h),(w,h),raw=col==0);sheet.paste(im,(col*w,yy))
    label(20,2010,'Same camera / scale per row. Side + oblique show actual fuller depth and guard section.',20)
    label(20,2052,'No combat, audio, stance or timing edits. Native pack / first-third person / swing / guard /10-20 display: PENDING.',18)
    return png(sheet)


def review_text(d,counts):
    return f"""# Crown-Splitter W136

{len(d['parts'])} authored solid cuboids, {len(d['parts'])*6} opaque faces; no triangle adapter. Broad continuous steel shoulders, solid central web under a physically recessed fuller, bright cutting edges, flared heel and converging point. Stepped feather guards have real depth and gaps between terminal fingers; navy leather grip has pale crossing bindings at both ends. Shallow flutes, restrained steel scoring and small edge bites are per-face UV. No source island/voxel construction or alpha silhouette skins. The 1024 atlas assigns every face a continuous rectangle with two-pixel extruded gutters.

The actual default-paint photograph is `/tmp/destiny-weapons-w31/references/crown_splitter.jpg`. Raw albedo is explicitly labeled undyed in comparison.png. Photo informs steel/bevel value contrast, dark blue leather and pale grip wraps. This is a cuboid interpretation: point/bevel curvature and fine surface wear are simplified; opaque static materials do not reproduce PBR reflections.

Read-only W30 metadata and inert FBX evidence: both objects, 4240 source triangles; FBX rotation [-90,0,0], scale100, translation[0,10,0] centimeters. Verified mapping `anchor + scale * [raw.X, raw.Z + 0.1, raw.Y]` matches all six W30 bounds within2e-6. Copying the untranslated mapping from another sword would shift this weapon by1.8285109194 units. W30 scale18.28510919435076 and hand anchor[8,4.9901939311001655,8] retained; blade points +Y. Catalogue confirms sword / aggressive frame. Canonical display is byte-equivalent as JSON data. Full-only candidate, existing generic handling; no new moving parts or combat/audio/timing edits.

Comparison contains the actual default photo plus same-camera side and oblique views of raw FBX, canonical148 and final model. Offline CPU/BB inspection is evidence for geometry and paint only. Native pack loading, held first/third person, swing, guard and10-20 displays remain pending master. User unsaved DCC work was untouched.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    assert len(model['elements'])<=1000
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='crown_splitter',revision='W136',family='sword',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
        groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,
        max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],coordinate_policy=d['coordinate_policy'],
        canonical_display_exact=True,full_only=True,existing_generic_handling_unchanged=True,combat_audio_timing_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w136/batch.json').read_bytes())
    scope=next(f['owned_paths'] for f in batch['features'] if f['name']=='w136-crown_splitter')
    assert len(scope)==10 and set(outputs)<=set(scope)
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
