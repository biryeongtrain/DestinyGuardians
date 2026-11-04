#!/usr/bin/env python3
"""W138 Bug-Out Bag: deterministic semantic solid-cuboid art; full export only.
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
ART = 'art/weapons/w123/bug_out_bag/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/submachine_gun/bug_out_bag.json'
MODEL = ASSET + 'models/weapon_surface_w123/bug_out_bag.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/bug_out_bag.png'
REPORT = 'docs/qa/2026-10-26/w138/bug_out_bag-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/bug_out_bag/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/bug_out_bag.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
EDGE = 1024
PALETTE = dict(steel=[115,119,116], edge=[155,156,144], bronze=[124,108,83],
    graphite=[46,48,46], recess=[20,23,22], rubber=[37,39,38], cloth=[177,176,166],
    stitch=[206,205,193], lens=[42,46,44])
H = runpy.run_path(str(ROOT / HELPER))
FACES = H['FACES']


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG'); return stream.getvalue()


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w138:bug_out_bag:'+name))


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
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/bug_out_bag.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Bug-Out Bag.fbx').read_bytes())==meta['source_files']['Bug-Out Bag.fbx']
    roots=H['parse_fbx'](RAW/'Bug-Out Bag.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for root in roots if root[0]=='Connections' for n in root[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]; basis=[]; sources=[]
    for node in objects:
        if node[0]!='Geometry': continue
        mid=next(p for c,p in links if c==node[1][0]); model=models[mid]
        name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']: continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        cs={c[0]:c for c in node[2]}
        local=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        # FBX centimeters -> source Blender Z-up meters, including THIS asset's
        # actual local rotation, scale and translation. No universal axis guess.
        rot=H['rotation'](dict(zip('xyz',props['Lcl Rotation'])))
        world=(local*np.array(props['Lcl Scaling']))@rot.T+props['Lcl Translation']
        source=world[:,[0,2,1]]/100; source[:,1]*=-1
        v=source[:,[1,2,0]]*[-1,1,-1]*meta['scale']+meta['anchor']
        sources.append(source)
        basis.append(dict(object=name,translation=props['Lcl Translation'],rotation=props['Lcl Rotation'],scaling=props['Lcl Scaling']))
        faces=[]; face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3; faces.append(face); face=[]
        layer=next((c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0),None)
        if layer:
            vals={c[0]:c[1][0] for c in layer[2]}
            assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
            uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        else: uv=np.zeros((len(faces),3,2))
        material=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=material))
    points=np.concatenate([m['vertices'] for m in meshes]);src=np.concatenate(sources)
    assert np.allclose([src.min(0),src.max(0)],meta['source_bounds'],atol=2e-6)
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=4e-5)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    meta=copy.deepcopy(meta);meta['fbx_basis_evidence']=basis
    return meshes,meta


def make_design(meta):
    """Authored by structural role; no source-component or voxel conversion."""
    parts=[]
    def box(name,lo,hi,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:
            axis,angle=turn
            e['rotation']=dict(origin=[round((a+b)/2,6) for a,b in zip(lo,hi)],axis=axis,angle=angle)
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def center(name,c,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,6) for a,b in zip(c,size)],
            [round(a+b/2,6) for a,b in zip(c,size)],mat,group,motif,turn)
    def tube(name,x,y,z0,z1,r,t,mat,group):
        # Hollow bore/rim: eight actual tangent walls around a real void.
        w=2*r*math.tan(math.pi/8)+.012
        for i in range(8):
            a=i*45;q=math.radians(a);cr=r-t/2
            size=[w,t,z1-z0];turn=None
            if a%90==0:
                if a%180:size=[t,w,z1-z0]
            else:turn=('z',45 if i%4==1 else -45)
            center(f'{name}_{i}',[x-cr*math.sin(q),y+cr*math.cos(q),(z0+z1)/2],size,mat,group,'ring',turn)
    def beam(name,a,b,width,depth,mat,group,motif='plain'):
        # Continuous bar between two YZ endpoints, rotated about native X.
        cy=(a[0]+b[0])/2;cz=(a[1]+b[1])/2;dy=b[0]-a[0];dz=b[1]-a[1]
        angle=(-math.degrees(math.atan2(dy,dz))+90)%180-90
        if abs(angle)>45:
            angle=(angle+180)%180-90;size=[width,math.hypot(dy,dz),depth]
        else:size=[width,depth,math.hypot(dy,dz)]
        center(name,[8,cy,cz],size,mat,group,motif,('x',angle))
    # Central load-bearing barrel is filled behind the short open muzzle.
    center('barrel_core',[8,12.03,1.4],[.70,.70,6.9],'graphite','barrel','barrel')
    tube('muzzle',8,12.03,-4.040927464158996,-2.15,.43,.115,'bronze','muzzle')
    box('bore_stop',[7.72,11.75,-2.14],[8.28,12.31,-2.06],'recess','muzzle','bore')
    # Front steel yoke has a central passage, chamfer shoulders and low chin.
    box('front_yoke_top',[7.33,12.54,-2.05],[8.67,13.22,-.72],'steel','front_yoke','yoke')
    box('front_yoke_lower',[7.37,10.87,-2.05],[8.63,11.53,-.72],'graphite','front_yoke','yoke')
    for side in (-1,1):
        center(f'front_yoke_side_{side}',[8+side*.62,12.01,-1.38],[.25,1.50,1.35],'steel','front_yoke','yoke')
        center(f'front_yoke_shoulder_{side}',[8+side*.56,13.16,-1.38],[.30,.30,1.35],'steel','front_yoke','plain',('z',45*side))
    center('front_yoke_chin',[8,10.82,-.88],[1.10,.50,.77],'graphite','front_yoke','yoke',('x',-22.5))
    box('front_sight_base',[7.61,12.44,-3.30],[8.39,12.73,-2.08],'graphite','sights','rail')
    center('front_sight_ramp',[8,12.80,-2.52],[.32,.29,.53],'steel','sights','plain',('x',-22.5))
    # Two bronze floral heat-shield faces have real depth around the inner core.
    # Their shallow decorative apertures are opaque authored relief in UV.
    for side in (-1,1):
        center(f'heat_shield_{side}',[8+side*.46,12.05,2.11],[.29,1.12,5.64],'bronze','heat_shield','floral')
        for y,tag in ((11.48,'lower'),(12.05,'center'),(12.62,'upper')):
            center(f'heat_fold_{tag}_{side}',[8+side*.38,y,2.11],[.30,.16,5.64],'edge','heat_shield','bead')
    # Open forearm chassis: long rails and collars, no opaque side sheets.
    box('forearm_roof',[7.65,12.94,-.80],[8.35,13.14,5.29],'graphite','forearm','rail')
    box('forearm_keel',[7.57,10.84,-.53],[8.43,11.10,5.28],'steel','forearm','rail')
    box('forearm_rear_collar',[7.35,11.02,4.82],[8.65,13.20,5.40],'graphite','forearm','collar')
    for side in (-1,1):
        x=8+side*.88
        center(f'protective_rail_upper_{side}',[x,13.09,3.02],[.23,.24,5.08],'steel','protective_rails','tube')
        center(f'protective_rail_lower_{side}',[x,11.00,3.02],[.23,.24,5.08],'steel','protective_rails','tube')
        center(f'protective_rail_front_{side}',[x,11.89,.33],[.23,1.18,.24],'steel','protective_rails','tube')
        center(f'protective_rail_front_slope_{side}',[x,12.66,.56],[.23,.27,1.02],'steel','protective_rails','tube',('x',-45))
        center(f'protective_rail_rear_{side}',[x,12.01,5.55],[.23,2.18,.24],'graphite','protective_rails','tube')
    # The exposed right/native -X ejection control is true protruding hardware.
    box('receiver_core',[7.43,10.84,5.25],[8.57,13.15,9.75],'graphite','receiver','receiver')
    for side in (-1,1):
        center(f'receiver_shoulder_{side}',[8+side*.51,13.13,7.57],[.27,.27,4.25],'graphite','receiver','receiver',('z',45*side))
    box('receiver_roof',[7.55,13.15,5.39],[8.45,13.37,9.72],'steel','receiver','rail')
    box('receiver_grip_socket',[7.39,10.38,6.40],[8.61,11.22,8.92],'graphite','receiver','socket')
    box('receiver_rear_spine',[7.60,11.43,9.52],[8.40,13.22,12.40],'graphite','receiver','receiver')
    box('ejection_port',[6.94,11.90,8.08],[7.44,12.47,8.93],'recess','controls','port')
    box('ejection_lip',[6.891017553270383,12.40,8.07],[7.45,12.59,8.95],'bronze','controls','port')
    box('charging_rod',[7.21,11.47,6.16],[7.48,11.69,8.69],'steel','controls','tube')
    center('charging_paddle',[7.11,11.38,6.45],[.35,.42,.51],'graphite','controls','knurl')
    # Skeleton forward grip uses full-width diagonal beams and actual open air.
    beam('foregrip_diagonal',(8.68,3.84),(10.85,.72),.84,.53,'graphite','foregrip','foregrip')
    beam('foregrip_rear_join',(8.68,3.84),(10.50,5.54),.87,.48,'graphite','foregrip','foregrip')
    center('foregrip_heel',[8,8.68,3.84],[.94,.42,.82],'rubber','foregrip','grip',('x',-42))
    box('foregrip_guard_bridge',[7.58,10.03,4.86],[8.42,10.32,6.56],'steel','trigger','guard')
    beam('guard_front',(10.26,5.13),(10.88,5.13),.70,.22,'steel','trigger','guard')
    beam('guard_rear',(10.22,6.53),(10.87,6.67),.70,.23,'graphite','trigger','guard')
    beam('trigger',(10.29,6.24),(10.86,6.05),.23,.20,'bronze','trigger','trigger')
    # Fixed original native grip frame. Feed and mag remain inside this grip.
    center('grip_core',[8,9.12,7.42],[1.04,3.49,1.73],'rubber','grip','grip',('x',-6))
    center('grip_front_bevel',[8,9.14,6.60],[.94,3.36,.29],'rubber','grip','grip',('x',-6))
    center('grip_backstrap',[8,9.14,8.27],[1.05,3.38,.25],'graphite','grip','grip',('x',-6))
    box('grip_upper_band',[7.43,10.35,6.46],[8.57,10.62,8.37],'graphite','grip','band')
    box('grip_heel_band',[7.41,7.24,6.35],[8.59,7.79,8.46],'graphite','grip','band')
    box('grip_heel_lip',[7.43,7.11,6.34],[8.57,7.30,8.49],'steel','grip','heel')
    # Magazine is part of full output only. No reload pivots/assets are changed.
    box('magazine_core',[7.66,5.12,6.99],[8.34,7.26,8.13],'bronze','magazine','magazine')
    box('magazine_front_spine',[7.65,5.13,6.88],[8.35,7.25,7.09],'steel','magazine','magazine')
    box('magazine_rear_spine',[7.66,5.13,8.04],[8.34,7.25,8.25],'graphite','magazine','magazine')
    box('magazine_base',[7.48,4.821366217113052,6.84],[8.52,5.17,8.50],'steel','magazine','heel')
    # Fabric saddle is a filled, tapered cheek volume, not two cloth side cards.
    box('cloth_upper_core',[7.27,12.50,9.05],[8.83,13.38,12.62],'cloth','cloth','cloth')
    box('cloth_lower_core',[7.38,11.80,9.48],[8.73,12.52,12.34],'cloth','cloth','cloth')
    box('cloth_bottom_core',[7.52,11.23,10.00],[8.60,11.82,11.91],'cloth','cloth','cloth')
    beam('cloth_front_taper',(12.60,9.17),(11.50,9.91),1.40,.49,'cloth','cloth','cloth')
    beam('cloth_rear_taper',(11.50,11.89),(12.60,12.55),1.40,.49,'cloth','cloth','cloth')
    for side in (-1,1):
        center(f'cloth_upper_shoulder_{side}',[8.05+side*.73,13.23,10.83],[.30,.30,3.50],'cloth','cloth','cloth',('z',45*side))
    for tag,z,y,length,angle in (('front',9.22,12.06,2.42,-19),('rear',12.42,12.18,2.31,16)):
        center(f'cloth_binding_{tag}',[8.05,y,z],[1.64,length,.23],'graphite','cloth','stitch',('x',angle))
    center('cloth_bottom_binding',[8.05,11.28,10.99],[1.13,.21,1.86],'graphite','cloth','stitch')
    # Single diagonal leather securing strap, not random fabric/screw geometry.
    for side in (-1,1):
        center(f'cloth_strap_{side}',[8.05+side*.82,12.35,11.02],[.10,2.02,.22],'graphite','cloth','strap',('x',-26))
    # Wire butt frame with true triangular air and a narrow terminal pad.
    beam('stock_upper_rod',(12.18,12.38),(12.18,15.53),.37,.32,'steel','stock','tube')
    beam('stock_front_drop',(11.03,11.96),(10.83,12.71),.40,.31,'steel','stock','tube')
    beam('stock_diagonal_front',(10.83,12.71),(12.16,13.99),.39,.34,'steel','stock','tube')
    beam('stock_diagonal_rear',(10.01,15.48),(12.16,13.99),.39,.34,'steel','stock','tube')
    box('stock_butt_pad',[7.66,9.42,15.43],[8.34,12.58,15.959072535841006],'graphite','stock','butt')
    box('stock_butt_insert',[7.76,9.69,15.33],[8.24,12.32,15.51],'steel','stock','butt')
    # High open ring with a recessed opaque optic; lens is not a body shell.
    box('optic_base',[7.57,13.15,2.62],[8.43,13.36,4.62],'graphite','sights','rail')
    center('optic_rear_ramp',[8,13.55,4.08],[.70,.47,.80],'graphite','sights','plain',('x',-22.5))
    tube('optic_rim',8,13.85,2.84,3.38,.4331595,.105,'graphite','sights')
    box('optic_lens',[7.75,13.58,3.32],[8.25,14.12,3.35],'lens','sights','lens')
    center('optic_adjuster',[8.45,13.54,3.83],[.20,.27,.31],'bronze','sights','dial')
    # Three visible black lower clamp bands are actual transverse wraps.
    for i,z in enumerate((1.72,2.12,2.52)):
        center(f'lower_clamp_{i}',[8,11.03,z],[1.00,.79,.19],'rubber','forearm','band')
    inputs=[BASE,'art/blockbench/weapons/w30/bug_out_bag.bbmodel',HELPER,
            ASSET+'textures/item/weapon/w30/bug_out_bag.png']
    raw_inputs=[RAW/'Bug-Out Bag.fbx',RAW/'BugOutBagBarrel_Diffuse.dds',RAW/'BugOutBagSight_Diffuse.dds',PHOTO]
    return dict(id='bug_out_bag',revision='W138',method='authored semantic opaque filled cuboids / authored per-face UV',
        source=meta,palette=PALETTE,parts=parts,
        identity=['bronze floral shield in steel protective cage','black open triangular foregrip and grip-fed magazine',
                  'patterned cloth cheek saddle / wire skeleton butt','short open muzzle / high compact optic'],
        coordinate_policy=dict(basis='FBX actual model SRT -> Blender meters [world X,-world Z,world Y]/100 -> native [-source Y,source Z,-source X]; muzzle -Z',
            scale=meta['scale'],anchor=meta['anchor'],grip='native grip frame at [8,9.12,7.42], no global recenter or scale',
            display='exact canonical dictionary',export='full only; existing generic reload / gameplay / audio untouched'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Offline CPU inspection only; native parser / pack / gameplay / performance pending master.',
          'Shallow floral apertures are opaque UV relief, not pierced source mesh holes; static paint is not PBR.',
          'Cloth folds and sculpted curves simplified into broad filled volumes; bounded source textile crop retained.',
          'Reverse-side photo unavailable; consistent materials without invented reverse lettering.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q


_CLOTH=None

def tile(spec,face,w,h):
    global _CLOTH
    role=spec['material'];motif=spec['motif'];e=spec['geometry'];u,v,q=world_points(e,face,w,h)
    rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
    rgb*=(.97+.055*np.exp(-((v-.28)/.33)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    rgb[edge<.7]*=.74;rgb[(edge>=.7)&(edge<1.6)]*=1.07
    side=face in ('east','west');z=q[:,:,2];y=q[:,:,1]
    if motif=='cloth':
        if _CLOTH is None:
            # Safe interior of the actual woven source panel: no trim, holes,
            # or atlas background is transplanted onto the new solid saddle.
            _CLOTH=np.asarray(Image.open(RAW/'BugOutBagBarrel_Diffuse.dds').convert('RGB').crop((95,565,590,775)))
        if side:
            uu=np.clip((z-9.0)/3.7,0,.99999);vv=np.clip((13.40-y)/2.3,0,.99999)
        elif face in ('up','down'):
            uu=np.clip((z-9.0)/3.7,0,.99999);vv=np.clip((q[:,:,0]-7.2)/1.7,0,.99999)
        else:uu=u*.99999;vv=v*.99999
        sample=_CLOTH[(vv*_CLOTH.shape[0]).astype(int),(uu*_CLOTH.shape[1]).astype(int)].astype(float)
        luma=sample@[.2126,.7152,.0722];luma=np.clip((luma-30)*.91+28,24,207)
        rgb=luma[:,:,None]*np.array([1.0,.997,.94])
        # Very restrained weave; source pattern remains the dominant marking.
        rgb*=(.98+.02*np.cos(q[:,:,2]*132)*np.cos(q[:,:,1]*132))[:,:,None]
    if motif=='floral' and side:
        # Authored four-teardrop flower repeats in native coordinates, no alpha.
        # Both sides have their own UV islands; world placement avoids mirroring.
        dz=np.mod(z+.39,.68)-.34;dy=np.mod(y-11.48,.57)-.285
        petals=np.zeros((h,w),bool);rims=np.zeros((h,w),bool)
        for a,b in ((.105,0),(-.105,0),(0,.155),(0,-.155)):
            rr=((dz-a)/(.064 if a else .045))**2+((dy-b)/(.098 if a else .106))**2
            petals|=rr<.72;rims|=(rr>=.72)&(rr<1.28)
        rgb[petals]=PALETTE['recess'];rgb[rims]=[186,175,150]
        seam=(abs(y-11.60)<.024)|(abs(y-12.50)<.024);rgb[seam]*=.53
        rgb[(abs(y-11.64)<.015)|(abs(y-12.54)<.015)]*=1.18
    if side and motif in ('receiver','yoke','socket','guard'):
        # Photo-backed long panel breaks and inset hardware on broad face UV.
        line=((abs(y-12.79)<.025)|(abs(y-11.24)<.022))&(z>5.65)&(z<9.55)
        rgb[line]*=.56
        if motif=='receiver':
            port=(z>8.1)&(z<8.9)&(y>12)&(y<12.55);rgb[port]*=.56
            rgb[(abs(y-12.57)<.025)&(z>8.05)&(z<8.95)]*=1.5
        for zc,yc in ((-1.35,12.06),(5.52,11.15),(5.76,10.44),(7.01,12.72)):
            rr=np.hypot(z-zc,y-yc)
            rgb[(rr>.075)&(rr<.115)]=PALETTE['bronze'];rgb[rr<.070]=PALETTE['recess']
            rgb[(abs(y-yc)<.014)&(rr<.055)]=PALETTE['edge']
    if motif in ('grip','foregrip'):
        # Continuous material pattern across the solid grip faces.
        weave=(np.cos((z+y)*70)*np.cos((z-y)*70))
        rgb*=(.94+.075*weave)[:,:,None]
        if motif=='foregrip' and side:
            rgb[(np.mod((z+y)*4,1)<.22)]*=.65
    if motif=='band':
        rgb[np.mod(y*10,1)<.18]*=.62
        rgb[np.mod(y*10,1)>.86]*=1.18
    if motif=='stitch':
        seam=np.mod((y+z)*9,1)<.27
        rgb[seam]=np.array(PALETTE['stitch'])*.68
    if motif=='magazine' and side:
        for zc in (7.12,7.94):rgb[(abs(z-zc)<.035)&(y<7.04)&(y>5.28)]*=.54
        # Two observed witness holes, intentionally opaque recessed paint.
        for yc in (5.92,6.72):
            r=np.hypot((z-7.51),y-yc)
            rgb[r<.105]=PALETTE['recess'];rgb[(r>.085)&(r<.12)]=PALETTE['edge']
    if motif=='heel' and face in ('east','west','south'):
        rgb[np.mod(u*32,1)<.15]*=.70
    if motif=='butt' and face=='south':rgb[np.mod(v*17,1)<.22]*=.58
    if motif=='knurl':rgb*=(.85+.15*np.cos(u*48)*np.cos(v*48))[:,:,None]
    if motif=='lens' and face in ('north','south'):
        rr=np.hypot((q[:,:,0]-8)/.34,(y-13.85)/.34)
        rgb[:]=[20,28,26];rgb+=np.maximum(0,1-rr)[:,:,None]*[14,21,17]
        rgb+=np.exp(-(((q[:,:,0]-7.88)/.065)**2+((y-14)/.045)**2))[:,:,None]*[45,54,46]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=38 if spec['motif']=='cloth' else 29 if spec['motif']=='floral' else 23
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
    model=dict(credit='Bug-Out Bag W138 authored solid semantic volumes / face UV / full only',
        textures={'0':'destiny:item/weapon/w123/bug_out_bag','particle':'destiny:item/weapon/w123/bug_out_bag'},
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
        name='Bug-Out Bag W138 / offline inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='bug_out_bag.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w138=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],fullOnly=True))


def source_triangles(meshes):
    result=[];textures={}
    for m in meshes:
        mat=m['material'].split('.')[0]
        if mat not in textures:
            path=RAW/(mat+'_Diffuse.dds')
            textures[mat]=np.asarray(Image.open(path).convert('RGBA')) if path.exists() else np.array([[[50,54,50,255]]],np.uint8)
        for t,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((t,uv,textures[mat],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=900,380;sheet=Image.new('RGB',(2700,2070),'#151d27');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'BUG-OUT BAG / W138 / SEMANTIC SOLIDS + AUTHORED FACE UV / OFFLINE INSPECTION',28)
    photo=Image.open(PHOTO).convert('RGB').crop((590,175,1790,925));photo.thumbnail((750,370));sheet.paste(photo,(20,55))
    for i,n in enumerate(('Barrel','Sight')):
        im=Image.open(RAW/('BugOutBag'+n+'_Diffuse.dds')).convert('RGB');im.thumbnail((330,330));sheet.paste(im,(800+i*360,64));label(800+i*360,400,'RAW '+n.upper()+' / UNDYED',17)
    for i,line in enumerate([f'{len(model["elements"])} opaque filled cuboids / full only',
          'Bronze floral shield / black grip / woven cheek',
          'True bore / cage / trigger / stock air',
          'Canonical display + original native frame',
          'CPU render only; live QA pending master']):label(1560,85+i*52,line,23)
    label(20,450,'RAW FBX / 27,895 triangles / UNDYED')
    label(w+20,450,'CANONICAL / 209 cuboids / READ ONLY')
    label(2*w+20,450,f'W138 / {len(model["elements"])} opaque semantic solids')
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/bug_out_bag.png'))
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT THREE-QUARTER',[1,.42,-.65]),('REAR / OPPOSITE THREE-QUARTER',[-1,.36,.65])]):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,490+row*h));label(col*w+15,498+row*h,name,17)
    for col,(groups,cam) in enumerate([(('muzzle','front_yoke'),[.09,.05,-1]),(('cloth','stock'),[-1,.25,.45]),(('foregrip','trigger'),[1,.1,-.1]),(('heat_shield','protective_rails'),[1,.4,-.3])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups}
        sub=dict(elements=[e for e in model['elements'] if e['name'] in names])
        points=np.concatenate([vertices(e) for e in sub['elements']]);im,_=H['render'](model_triangles(sub,atlas),cam,H['frame'](points,cam,675,335),(675,335))
        sheet.paste(im,(col*675,1660));label(col*675+14,1668,' / '.join(groups).upper(),17)
    label(20,2025,'Matched full-model cameras/scale. Native parsing, held/ADS/reload, audio and 10-20 display checks: pending master.',21)
    return png(sheet)


def review_text(d,counts):
    return f"""# Bug-Out Bag W138 offline art review

Default appearance `/tmp/destiny-weapons-w31/references/bug_out_bag.jpg`, raw FBX/DDS and canonical W30 were inspected using local view_image. The actual supplied appearance has bronze floral heat shielding, steel protective rails, charcoal receiver/grips, black-and-ivory woven cheek saddle, wire butt frame, high compact sight and grip-fed magazine. The raw metal albedos are largely undyed; their gray does not define default paint.

{sum(counts.values())} emitted opaque filled cuboids; {sum(counts.values())*6} explicit face UVs. Groups: {json.dumps(counts,sort_keys=True)}. Full only, no split exports. Every element is an authored structural volume: solid receiver, inner barrel, folded bronze shield, open protection rails, two diagonal foregrip beams, guard, grip, magazine, filled three-level fabric saddle, wire butt and hollow muzzle. The 80-120 draft range guided the design; the 1,000 ceiling is not a target. No source mesh islands, voxel conversion, alpha side-shells, triangle adapters or invented mesh JSON are used.

1024² atlas has {d['atlas']['face_islands']} independent face islands, proportional density and 2px opaque extruded gutters. A bounded interior crop of the actual source cloth (Barrel DDS pixels 95,565 to 590,775) retains its textile identity with continuous placement across the broad saddle faces. Original source UV islands are not transplanted. Bronze four-petal repeats, receiver seams, observed witness holes, grip weave, bindings and butt ribs use authored face paint. Floral apertures are intentionally shallow opaque UV relief; they do not claim the original perforated topology. Static shading does not reproduce PBR. There is no invented text or random noise.

Raw FBX objects have actual SRT rotation [-90,+90,0] approximately, scale 135.4697876%, translation [4.7623463,4.5683441,0] centimeters. Each model transform is applied before converting world centimeters to source Z-up meters [X,-Z,Y]/100, then native [-source Y,source Z,-source X]. Source and native bounds are asserted against W30 within 0.00004 units. Muzzle is -Z, scale {d['source']['scale']}, anchor {d['source']['anchor']}. There is no global scale/recenter, display compensation or gameplay grip transform edit. The grip and feed remain at their original native positions. The display dictionary is copied exactly from canonical. Canonical JSON, metadata, reload, registry, HUD, gameplay and audio files are read-only.

comparison.png shows the supplied appearance, raw diffuse evidence, and matched-camera side/front/rear views of unchanged source, canonical and W138. Detail panels show bore, cloth/stock, guard/foregrip and shield/cage depth. inspection.bbmodel embeds the exact atlas with semantic groups and matching geometry. Broad filled cloth volumes approximate the original rounded hanging fold; metallic reflections and fine sculpted transitions remain simplified. Reverse-side photograph unavailable; consistent material placement is used without invented lettering.

Offline targeted regression covers exact ten-path ownership and portable main/worktree execution, solid volume/schema budget, full UV opacity/gutters/non-overlap, frame and display/source provenance, real bore and structural voids, inspection parity, hashes and deterministic regeneration. Master owns native 26.3 parsing/resource registration, first/third-person, ADS, generic reload and audio listening, and 10-20 simultaneously displayed weapons. These are pending; no GUI/game/Gradle/server or native performance acceptance is claimed.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='bug_out_bag',revision='W138',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
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
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w138/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w138-bug_out_bag'))
    assert len(owned)==10 and set(outputs)<=owned
    for path,data in outputs.items():
        p=ROOT/path
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+path
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts / {m["assembled_elements"]} solid cuboids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
