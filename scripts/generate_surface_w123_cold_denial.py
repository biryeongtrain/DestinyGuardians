#!/usr/bin/env python3
"""W138 Cold Denial: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/cold_denial/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/pulse_rifle/cold_denial.json'
MODEL = ASSET + 'models/weapon_surface_w123/cold_denial.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/cold_denial.png'
REPORT = 'docs/qa/2026-10-26/w138/cold_denial-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/cold_denial/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/cold_denial.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(teal=[30,80,84], bronze=[154,113,70], steel=[153,161,164],
    dark=[34,39,42], rubber=[26,29,31], recess=[15,22,25], light=[236,225,201])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w138:cold_denial:'+name))


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
    """Cold Denial FBX basis checked independently against all W30 bounds.

    Geometry objects are root children, not armature children; bone transforms
    must not be applied to already-resting mesh arrays. Read data, never shaders.
    """
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/cold_denial.bbmodel').read_bytes())['destiny_w30']
    for name,digest in meta['source_files'].items():
        assert sha((RAW/name).read_bytes())==digest,name
    roots=H['parse_fbx'](RAW/'Cold Denial/Cold Denial.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(parent for child,parent in links if child==node[1][0] and parent in models)
        model=models[mid];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        assert [p for c,p in links if c==mid]==[0], 'Unexpected parent basis'
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=2e-5,rtol=0)
        assert np.allclose(props['Lcl Scaling'],[100]*3,atol=2e-5,rtol=0)
        assert np.allclose(props['Lcl Translation'],[0]*3,atol=2e-7,rtol=0)
        cs={c[0]:c for c in node[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0])
        assert np.all((ix<0).reshape(-1,3)==[False,False,True])
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        material=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=faces,uv=uv,material=material,fbx_properties=props))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==24191
    return meshes,meta


def make_design(meta):
    """Hand-authored load-bearing parts; source arrays are evidence only."""
    parts=[]
    def c(name,pos,size,mat,group,motif='panel',turn=None):
        e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],
                            'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
        if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def beam(name,x,y0,z0,y1,z1,width,depth,mat,group,motif='panel'):
        c(name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(y1-y0,z1-z0)],mat,group,motif,
          ('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
    def bore(name,y,z0,z1,r,thick,mat):
        # Real bore through 8 solid tangent walls, backed by a solid throat.
        for i in range(8):
            a=math.radians(i*45);rr=r-thick/2
            c(f'{name}_wall_{i}',[8-rr*math.sin(a),y+rr*math.cos(a),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.035,thick,z1-z0],mat,'muzzle','muzzle',('z',i*45))
        c(name+'_throat',[8,y,z1+.10],[r*1.48,r*1.48,.24],'recess','muzzle','bore')
    # Filled front upper body, with physically stepped shoulders and rail.
    c('upper_receiver_core',[8,13.10,.42],[1.32,1.86,12.72],'teal','receiver','damascus')
    c('upper_receiver_roof',[8,13.62,.42],[1.64,.82,12.72],'teal','receiver','damascus')
    c('upper_receiver_lower_lip',[8,12.375,.42],[1.64,.41,12.72],'teal','receiver','damascus')
    for side in (-1,1):
        c('upper_inset_channel_'+str(side),[8+side*.675,12.865,.40],[.12,.49,8.3],'recess','receiver','panel')
    c('upper_receiver_crown',[8,14.075,.45],[1.38,.25,12.72],'teal','receiver','eyes')
    c('top_rail',[8,14.285,.28],[1.02,.17,13.22],'dark','rail','rail')
    for side in (-1,1):
        c('upper_shoulder_'+str(side),[8+side*.74,13.98,.45],[.28,.32,12.65],'teal','receiver','eyes',('z',side*40))
        # A thick relief strip, whose coins/recesses are face paint.
        c('forward_medallion_rail_'+str(side),[8+side*.84,13.25,1.68],[.18,.47,6.65],'dark','receiver','coins')
    c('receiver_mid_bridge',[8,12.18,7.85],[1.72,2.78,4.52],'teal','receiver','damascus')
    c('stock_upper_core',[8,12.60,13.80],[1.64,2.02,8.72],'teal','stock','damascus')
    c('rear_lower_rail',[8,11.35,12.8],[1.64,.60,10.40],'dark','stock','grain')
    c('stock_comb',[8,13.67,13.84],[1.60,.34,8.55],'dark','stock','grain')
    c('stock_heel',[8,10.63,17.72],[1.59,5.10,.79],'teal','stock','damascus')
    c('stock_butt_pad',[8,10.72,18.115],[1.64,5.08,.30],'rubber','stock','rubber')
    for side in (-1,1):
        c('stock_coin_rail_'+str(side),[8+side*.86,12.64,13.50],[.18,.49,4.64],'dark','stock','coins')
        c('stock_silver_vent_'+str(side),[8+side*.88,11.76,14.25],[.20,.80,2.05],'steel','stock','vent')
        c('rear_latch_'+str(side),[8+side*.87,12.03,16.48],[.24,.70,1.54],'dark','stock','latch')
    # Lower housing is a solid hand-filling mass; no hollow side envelopes.
    c('lower_receiver_core',[8,10.88,1.0],[1.76,1.64,12.6],'dark','handguard','perforations')
    c('lower_handguard',[8,10.12,.30],[1.76,.89,9.05],'dark','handguard','perforations')
    for side in (-1,1):
        beam('handguard_bevel_'+str(side),8+side*.78,9.76,-3.55,9.93,4.58,.28,.36,'dark','handguard','perforations')
        c('muzzle_side_vent_'+str(side),[8+side*.82,10.94,-5.37],[.22,.40,2.1],'steel','muzzle','vent')
    # Two vertically stacked real muzzle apertures preserve the unusual front.
    bore('upper_muzzle',13.35,-6.7350967,-5.83,.88,.25,'teal')
    bore('lower_muzzle',10.36,-6.7350967,-5.50,.90,.27,'dark')
    c('muzzle_web',[8,11.94,-6.12],[1.51,1.13,.95],'dark','muzzle','grain')
    # Bronze bundles are actual proud bends. Five parallel grooves are UV,
    # rather than 5*each segment thin rods and decorative screw geometry.
    for side in (-1,1):
        x=8+side*.94
        beam('conduit_low_'+str(side),x,11.81,-2.03,11.81,3.42,.22,.66,'bronze','conduits','bundle')
        beam('conduit_rise_'+str(side),x,11.81,3.35,13.46,6.85,.22,.66,'bronze','conduits','bundle')
        beam('conduit_top_'+str(side),x,13.46,6.79,13.91,7.90,.22,.66,'bronze','conduits','bundle')
        c('front_conduit_cap_'+str(side),[x,13.05,-5.10],[.22,.68,2.23],'bronze','conduits','bundle')
        beam('front_conduit_elbow_'+str(side),x,13.05,-4.05,12.09,-3.55,.22,.60,'bronze','conduits','bundle')
        beam('front_conduit_return_'+str(side),x,12.09,-3.55,11.81,-2.03,.22,.60,'bronze','conduits','bundle')
        c('stock_conduit_'+str(side),[x,13.07,15.25],[.20,.60,3.14],'bronze','conduits','bundle')
    # Raised silver capsule around the dark receiver insert; the underlying
    # receiver remains filled. This is trim, not a fabricated through-window.
    for side in (-1,1):
        x=8+side*.91
        c('action_insert_'+str(side),[x,12.57,7.78],[.22,1.32,2.55],'dark','action','eyes')
        c('action_top_trim_'+str(side),[x,13.40,7.50],[.26,.17,2.61],'steel','action','grain')
        c('action_bottom_trim_'+str(side),[x,11.72,7.50],[.26,.17,2.61],'steel','action','grain')
        for end in (-1,1):
            # Two angled corner blocks and an end wall form each rounded end.
            zz=7.50+end*1.42
            c(f'action_end_{side}_{end}',[x,12.56,zz],[.26,.78,.19],'steel','action','grain')
            for top in (-1,1):
                beam(f'action_corner_{side}_{end}_{top}',x,12.56+top*.39,zz,
                     12.56+top*.81,zz-end*.27,.26,.18,'steel','action','grain')
        c('action_selector_'+str(side),[8+side*1.00,12.58,8.36],[.17,1.46,.98],'dark','action','three_eyes')
    # Exact hand-frame point lies inside this raked, fully filled pistol grip.
    beam('grip_core',8,10.70,7.38,6.81,9.19,1.08,1.19,'rubber','grip','grip')
    beam('grip_backstrap',8,10.52,8.01,6.77,9.82,1.18,.26,'dark','grip','grain')
    c('grip_heel',[8,6.80,9.54],[1.18,.37,1.41],'dark','grip','grip')
    # Open trigger guard: one front post, a bottom rail and a sloping corner.
    c('trigger_front',[8,10.10,5.26],[.58,1.45,.23],'dark','trigger')
    c('trigger_bow_bottom',[8,9.34,6.08],[.58,.23,1.64],'dark','trigger')
    beam('trigger_bow_corner',8,9.35,6.83,9.78,7.20,.58,.23,'dark','trigger')
    beam('trigger',8,10.79,6.46,9.88,6.23,.19,.17,'steel','trigger')
    # Rear magazine remains part of full model, no new reload split/pivot.
    c('magazine_socket',[8,10.91,12.16],[1.57,.56,2.36],'dark','magazine','panel')
    c('magazine_core',[8,8.45,12.14],[1.18,4.97,1.96],'light','magazine','luminous')
    for zz in (11.08,13.16):
        c('magazine_edge_'+str(zz),[8,8.45,zz],[1.36,4.95,.20],'dark','magazine','grain')
    c('magazine_floor',[8,6.14,12.14],[1.40,.36,2.40],'dark','magazine','grain')
    c('magazine_feed_band',[8,10.60,12.14],[1.38,.43,2.38],'dark','magazine','grain')
    # Actual open-top reflex sight, with sloping wings and narrow feet.
    c('sight_foot',[8,14.39,5.48],[1.48,.23,1.75],'dark','sight','grain')
    for side in (-1,1):
        c('sight_wing_'+str(side),[8+side*.57,14.92,5.53],[.19,1.08,.65],'steel','sight','grain')
        beam('sight_ramp_'+str(side),8+side*.57,14.39,4.75,15.18,5.42,.19,.22,'steel','sight','grain')
    # Files are hashed read-only; no runtime registry or shared HUD changes.
    files=[BASE,'art/blockbench/weapons/w30/cold_denial.bbmodel',HELPER,
           ASSET+'textures/item/weapon/w30/cold_denial.png']
    rawfiles=[PHOTO,RAW/'Cold Denial/Cold Denial.fbx',RAW/'Cold Denial/Cold Denial.blend']
    rawfiles += [RAW/('Cold Denial/'+name) for name in ('CDFrame_Diffuse.png','CDMag_Diffuse.png','CDSight_Diffuse.png')]
    return dict(id='cold_denial',stage='W138',family='pulse_rifle',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='anchor + scale * [raw.X, raw.Z, raw.Y]',
            fbx_rotation_deg=[-90,0,0],fbx_scale=[100]*3,fbx_translation_approx=[0]*3,muzzle='-Z',
            grip=[8,8,8],display='canonical exact',validation='five root meshes / 24191 triangles / all six bounds within 2e-6'),
        construction='hand-authored filled semantic cuboids; full only; no alpha side shells, mesh islands or voxel conversion',
        references=['Ace of Spades 87 cubes and Izanagi 79 cubes: long masses, rotated silhouette parts and authored face UV; not fixed caps',str(PHOTO)],
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in files},raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
        limitations=['Cuboid muzzle facets, conduit elbows and capsule trim approximate smooth source curvature.',
            'Teal marbling, eye emblems, circular recesses and grip texture are authored face paint, not original PBR reconstruction.',
            'Bright magazine is fully opaque; no source transparency, runtime emission or glass refraction is claimed.',
            'Full-only art candidate: existing reload/gameplay/audio unchanged; native first/third person, ADS, reload and 10-20 display QA pending master.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


def tile(spec,face,w,h):
    u,v,q=world_points(spec['geometry'],face,w,h)
    mat=spec['material'];motif=spec['motif'];side=face in ('east','west')
    y=q[:,:,1];z=q[:,:,2];rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb*=(.985+.018*np.sin(y*.8+z*.3))[:,:,None]
    border=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[border<.75]*=.80
    if motif in ('damascus','eyes') and mat=='teal':
        # Large flowing strata follow longitudinal panel coordinates, not noise.
        phase=y*29+4*np.sin(z*.85)+2*np.sin(z*1.6+y*2.8)
        rgb[np.sin(phase)>.79]*=1.17;rgb[np.sin(phase)<-.85]*=.80
        rgb[(np.sin(phase*1.06)>.98)]=[62,92,72]
    if motif in ('eyes','three_eyes','grip') and side:
        # Paired arcs + pupil reproduce the source's repeated eye vocabulary.
        zz=np.mod(z+.14,.64)-.32;yy=y-13.96
        if motif=='three_eyes':zz=np.mod(z-.04,.30)-.15;yy=y-12.60
        if motif=='grip':zz=np.mod(z,.39)-.195;yy=np.mod(y,.43)-.215
        width=.20 if motif!='three_eyes' else .105
        eye=(abs(yy)<.15)&(abs(zz)<width)&(abs(abs(yy)-(.13*(1-(zz/width)**2)))<.022)
        pupil=(zz**2+(yy*.7)**2)<.035**2
        rgb[eye|pupil]=[17,30,32] if mat=='teal' else [112,120,118]
    if motif in ('coins','perforations','vent') and side:
        spacing=.56 if motif=='coins' else .61
        zz=np.mod(z+.13,spacing)-spacing/2
        yy=(y-13.25) if spec['group']=='receiver' else (y-12.64)
        if motif=='perforations':yy=np.mod(y-10.02,.58)-.29
        if motif=='vent':yy=np.mod(y,.30)-.15;zz=np.mod(z,.36)-.18
        r=np.hypot(zz,yy);radius=.19 if motif=='coins' else (.145 if motif=='perforations' else .10)
        rgb[r<radius]=[15,22,25];rgb[(r>radius*.79)&(r<radius)]=[89,96,97]
        if motif=='coins':
            rgb[(r<radius*.72)&(r>radius*.45)]=[116,124,122]
            rgb[(abs(zz)<.023)&(abs(yy)<radius*.68)]=[126,130,126]
    if motif=='bundle':
        # Continuous five bronze strands aligned to each authored beam.
        grooves=np.mod(v*5,1);rgb[grooves<.19]*=.28;rgb[(grooves>.2)&(grooves<.32)]*=1.20
    if motif=='luminous':
        warm=np.clip((z-11.4)/1.5,0,1);rgb[:,:,0]=236;rgb[:,:,1]=235-warm*39;rgb[:,:,2]=219-warm*69
        rgb*=(.98+.018*np.sin(y*8))[:,:,None]
    if motif=='rail':
        teeth=np.mod(z/.41,1)<.48;rgb[teeth]*=1.9
    if motif in ('grain','rubber','grip'):
        rgb[np.mod(y*14+z*1.5,1)<.10]*=.82
    if motif=='bore':rgb*=.45
    if motif=='panel' and side:
        rgb[(u>.07)&(u<.93)&(abs(v-.86)<.018)]*=.6
    if motif=='latch' and side:
        rgb[(u>.22)&(u<.76)&(v>.4)&(v<.6)]=[153,158,154]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(28,36,44,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=23
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
    model=dict(credit='Cold Denial W138 semantic solid volumes / photo default paint / full only',
        textures={'0':'destiny:item/weapon/w123/cold_denial','particle':'destiny:item/weapon/w123/cold_denial'},
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
        name='Cold Denial W138 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='cold_denial.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w138=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    textures={name:np.asarray(Image.open(RAW/('Cold Denial/'+name+'_Diffuse.png')).convert('RGBA'))
              for name in ('CDFrame','CDMag','CDSight')}
    neutral=np.full((2,2,4),[126,130,131,255],dtype=np.uint8)
    texmap=dict(Frame='CDFrame',Mag='CDMag',Sight='CDSight');result=[]
    for m in meshes:
        tex=textures[texmap[m['material']]] if m['material'] in texmap else neutral
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:result.append((ps,uv,tex,n/length))
    return result


def comparison(d,meshes,atlas,model):
    w,h=1000,350;sheet=Image.new('RGB',(3000,1950),'#151c25');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e3e7ed',font_size=size)
    label(24,14,'COLD DENIAL / W138 / FILLED SEMANTIC VOLUMES + AUTHORED OPAQUE FACE UV',30)
    photo=Image.open(PHOTO).convert('RGB').crop((950,225,1885,735));photo.thumbnail((990,370));sheet.paste(photo,(8,60))
    lines=[f'{len(model["elements"])} solid cuboids / {len(model["elements"])*6} faces / FULL ONLY',
           'Teal flowing pattern / bronze stepped bundles / silver capsule',
           'Real twin bores + open reflex sight and trigger guard',
           'Filled stock, receiver, grip and bright opaque magazine',
           'FBX basis [X,Z,Y] / -Z muzzle / scale and grip frame retained',
           'Native pack, held, ADS, reload and 10-20 displays: PENDING MASTER']
    for i,line in enumerate(lines):label(1060,82+i*53,line,25)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/cold_denial.png'))
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    labels=['RAW FBX / 24,191 tris / UNDYED + NEUTRAL GLASS','CANONICAL / 241 cubes / READ ONLY',f'W138 / {len(model["elements"])} FILLED CUBOIDS']
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT OBLIQUE',[1,.35,-.70]),('REAR OBLIQUE',[-1,.30,.65])]):
        yy=480+row*375;extent=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            label(col*w+14,yy-28,labels[col],18)
            im,_=H['render'](ts,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,yy))
            label(col*w+14,yy+10,name,18)
    for i,group in enumerate(('muzzle','sight','trigger','magazine')):
        names={p['geometry']['name'] for p in d['parts'] if p['group']==group}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names]);ps=np.concatenate([vertices(e) for e in sub['elements']])
        cam=[.25,.10,-1] if group in ('muzzle','sight') else [1,.1,-.22]
        im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](ps,cam,750,270),(750,270));sheet.paste(im,(i*750,1620))
        label(i*750+20,1628,group.upper()+' / actual solid geometry',18)
    label(24,1910,'Same camera/scale per full-model row. Raw albedo is undyed; Tube/MagGlass shown neutral. CPU comparison is not native acceptance.',20)
    return png(sheet)


def review_text(d):
    return f'''# Cold Denial W138 offline review

Actual reference: `{PHOTO}` plus inert Cold Denial FBX and CDFrame/CDMag/CDSight diffuse PNGs. The reference was opened using local view_image. The undyed raw source has 24,191 triangles across five included meshes; 1,992 Tube/MagGlass triangles have no separate diffuse map and are shown neutral in the comparison. The excluded reticle card is not reconstructed as an alpha plane.

The final full-only candidate has {len(d['parts'])} authored opaque cuboids and {len(d['parts'])*6} explicit faces. Long upper/lower receiver and stock cores, raked pistol grip and opaque bright magazine are filled volumes. Two eight-wall muzzles have real recessed throats; the reflex sight and trigger guard have actual openings. Bronze conduit bundles stand proud and change direction in three structural segments, with five strands painted in each face UV. Silver action-capsule trim has real depth around a filled receiver. No mesh island, polygon, voxel conversion or alpha side shells are used.

Identity: long squared bullpup silhouette, teal flowing surface pattern, repeated eye emblems, bronze stepped conduits, dark medallion/perforation strips, open reflex sight, silver action surround and pale rear magazine. Reference-guided decorative circles are shallow UV recesses, not through-holes. All six faces of every cube have independent proportional atlas rectangles and two-pixel extruded gutters in an opaque 1024 atlas. Teal marbling, eye motifs, small rail teeth, recess rings and material scoring are authored paint without stochastic noise. Ace87/Izanagi79 informed continuous volumes and face detail; cube count was not a substitute for silhouette quality.

Verified source mapping: `anchor + scale * [raw.X, raw.Z, raw.Y]`, all six W30 bounds within 2e-6. Each of five mesh models is a root object; local rotation approximately [-90,0,0], scale100 and negligible translation were inspected. Armature transforms are not applied to the resting mesh. Native -Z muzzle, scale {d['source']['scale']}, anchor/grip [8,8,8] and every canonical display transform are retained. Canonical and gameplay/reload/audio sources are read-only. Full-only art does not introduce a magazine split or replacement pivot.

Comparison: actual appearance photograph, then matched-camera side/front/rear oblique rows for raw source, canonical 241-cube model and candidate; detail views show bore depth, sight, trigger and magazine. inspection.bbmodel embeds the exact atlas and semantic groups, for later user/master opening only.

Limitations: faceted curves and simplified small bevels; authored paint approximates source material patterns rather than recovering PBR; magazine is opaque static color rather than emission/refraction. Offline CPU renders do not establish native pack loading, 26.3 rotation support, first/third-person holding, ADS clearance, reload trajectory or 10-20 display behavior. Those checks remain pending master. No Gradle, game, GUI, Blender, Blockbench or other workers were used.
'''


def worker_text(d):
    return f'''# W138 Cold Denial worker

Worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w138-cold_denial`.
Scope: exactly the ten paths in `docs/qa/2026-10-26/w138/batch.json`; main is not edited.

Implemented {len(d['parts'])} filled opaque cuboids, {len(d['parts'])*6} explicit authored UV faces, one 1024 RGBA atlas (alpha255). Full-only assembled count is {len(d['parts'])}, below the 1,000 emitted-element ceiling. No adapter triangles or secondary simultaneous models. Each semantic volume is authored; no rip island/voxel generation. Exact original source scale/anchor/axis and canonical display are preserved. Shared registry/HUD, reload, gameplay and audio remain master's scope.

Read worktree AGENTS, RTK, minecraft-weapon-art-design and linked Ace87/Izanagi79 study. Inspected actual appearance locally, raw diffuse and source-basis evidence. Deterministic comparison provides raw/canonical/candidate side and both obliques plus structural detail views. CPU-only, bundled Python -B, numpy/Pillow, no runtime/dependency/raw copies.

Sequential validation command order:
1. `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/generate_surface_w123_cold_denial.py`
2. `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/qa/test_surface_w123_cold_denial.py`
3. `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/generate_surface_w123_cold_denial.py --verify`

Observed validation: generation completed with {len(d['parts'])} cubes / {len(d['parts'])*6} faces and eight generated artifacts; all 12 targeted tests passed (6.007s), followed sequentially by successful byte-exact --verify. The first targeted attempt exposed a detached magazine socket; the solid rear lower rail was added and all 12 checks then passed. The final comparison was opened locally using view_image. Final delivery reruns generation, targeted tests and --verify after recording this evidence; final timing/export byte counts are in the return message.

Targeted tests are root-relative and check exact ownership, input/output hashes, opaque filled mass, apertures, connected assembly, atlas packing/gutters, BB parity and deterministic regeneration. They support the worktree and main after hash-checked integration; main checks the adjacent export's exact ten paths and after hashes instead of requiring the worker cwd. The main test branch has not been executed here because this worker does not integrate into main.

Baseline SHA256: `61d9f956c2c0b096efad4a646a84d6f7b308429d08ab2245e1e621419bc89f2f`; HEAD `bfd4b4573fd8651bf1ea850bf829622ccce5c3c2`. The private worktree-batch baseline is read-only. Export dry run checks exact scope and main/source baseline consistency before the actual bundle is written.

Export: `scripts/qa/worktree_batch.py export --worktree /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w138-cold_denial --output /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w138-cold_denial-export`. The exporter preserves private baseline provenance, rejects scope drift and source conflicts, and records before/after hashes.

Native acceptance PENDING MASTER: shared registration/texture pack load, held first/third person, ADS, generic reload, gameplay/audio listening and 10-20 simultaneous displays. Faceted curves, static opaque magazine and approximate authored surface motifs remain visual limitations; no performance/native success is claimed.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    assert 80<=len(model['elements'])<=1000
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d).encode(),
             REPORT:worker_text(d).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='cold_denial',revision='W138',family='pulse_rifle',assembled_elements=len(model['elements']),
        opaque_cuboids=len(model['elements']),groups=counts,alpha_elements=0,triangle_adapter_elements=0,
        emitted_faces=len(model['elements'])*6,max_assembled_elements=1000,texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],coordinate_policy=d['coordinate_policy'],
        canonical_display_exact=True,full_only=True,existing_generic_handling_unchanged=True,combat_audio_timing_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w138/batch.json').read_bytes())
    scope=next(f['owned_paths'] for f in batch['features'] if f['name']=='w138-cold_denial')
    assert len(scope)==10 and set(outputs)|{'scripts/generate_surface_w123_cold_denial.py','scripts/qa/test_surface_w123_cold_denial.py'}==set(scope)
    assert sum(len(b) for b in outputs.values())<25*1024*1024
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')


if __name__=='__main__':main()


