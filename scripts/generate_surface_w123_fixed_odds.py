#!/usr/bin/env python3
"""W132 Fixed Odds: full-only authored opaque solids, offline art candidate.
W154 feed correction is applied before UV compilation.
Run using bundled numpy/Pillow Python with -B. No DCC/game/native claims.
"""
import argparse
import base64
import copy
import io
import json
import math
from pathlib import Path
import uuid
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw
import generate_surface_w123_beloved as helper

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/fixed_odds/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/machine_gun/fixed_odds.json'
MODEL = ASSET+'models/weapon_surface_w123/fixed_odds.json'
TEXTURE = ASSET+'textures/item/weapon/w123/fixed_odds.png'
RAW = Path('/tmp/destiny-weapons-w30/raw/fixed_odds/extracted/Fixed Odds')
PHOTO = Path('/tmp/destiny-weapons-w31/references/fixed_odds.jpg')
REFS = Path('/tmp/destiny-weapons-w31/references.json')
SOURCE = 'art/blockbench/weapons/w30/fixed_odds.bbmodel'
EDGE = 1024
FACES, NORMALS = helper.FACES, helper.NORMALS
vertices, rotation, sha, encode, png = helper.vertices, helper.rotation, helper.sha, helper.encode, helper.png
PALETTE = dict(gold=[191,158,78], edge=[218,189,112], black=[35,37,39],
               rubber=[26,28,31], steel=[83,87,92], recess=[17,19,23],
               purple=[158,110,203], copper=[205,133,98], brass=[173,130,72])


def source_meshes():
    meta = json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    fbx = RAW/'Fixed Odds.fbx'
    assert sha(fbx.read_bytes()) == meta['source_files']['Fixed Odds/Fixed Odds.fbx']
    roots = helper.parse_fbx(fbx)
    objects = next(n[2] for n in roots if n[0]=='Objects')
    meshes=[]
    # This FBX coalesces the metadata's .00.000/.00.002 into .00.001.
    # Their union plus .01 and .02 gives the exact W30 bounds and 30,249 faces.
    for n in objects:
        if n[0]!='Geometry' or '.03.' in n[1][1]:
            continue
        name=n[1][1].split('\x00')[0]; cs={c[0]:c for c in n[2]}
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]); ends=ix<0
        assert np.all(ends.reshape(-1,3)==[False,False,True])
        ix=np.where(ends,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        tex='171962448_mg01_caluseum_frame_main_var_a_gbit_1024_1024_0.jpg'
        if '.01.' in name: tex='5919876_mg01_caluseum_mods_main_a_gbit_512_256_0.jpg'
        if '.02.' in name: tex='2446285757_mg01_caluseum_scope_a_gbit_512_256_0.jpg'
        meshes.append(dict(name=name,vertices=v,faces=ix,uv=uv,texture=RAW/'Textures/Fixed-Odds'/tex))
    pts=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-5)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    return meshes,meta


def make_design(meta):
    specs=[]
    def box(name,lo,hi,mat,group,motif='panel',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:
            e['rotation']=dict(origin=[round((a+b)/2,6) for a,b in zip(lo,hi)],x=0,y=0,z=0)
            e['rotation'][turn[0]]=turn[1]
        specs.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='panel',turn=None):
        box(name,[round(a-b/2,6) for a,b in zip(pos,size)],
            [round(a+b/2,6) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name,a,b,width,depth,mat,group,motif='panel'):
        # Beam lies in YZ; rotation keeps stock/guard voids genuinely empty.
        mid=[(p+q)/2 for p,q in zip(a,b)]; dy=b[1]-a[1]; dz=b[2]-a[2]
        c(name,mid,[width,depth,math.hypot(dy,dz)],mat,group,motif,('x',-math.degrees(math.atan2(dy,dz))))
    def tube(name,x,y,z0,z1,r,t,mat,group,motif='rim'):
        for i in range(8):
            a=math.radians(i*45); rr=r-t/2
            c(f'{name}_{i}',[x-rr*math.sin(a),y+rr*math.cos(a),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.006,t,z1-z0],mat,group,motif,('z',i*45))
    # Muzzle completion follows the raw FBX (cropped in the default photo).
    tube('muzzle_bore_wall',8,11.41,-13.50,-10.05,.58,.135,'black','muzzle','barrel_flute')
    c('muzzle_deep_throat',[8,11.41,-10.03],[.88,.88,.12],'recess','muzzle','plain')
    # The housing is a filled receiver, with long shoulders and UV panel relief.
    box('gold_receiver',[7.47,10.64,-9.95],[8.53,12.12,2.85],'gold','receiver','gold_receiver')
    box('receiver_crown',[7.64,12.12,-9.80],[8.36,12.35,3.06],'edge','receiver','crown')
    box('receiver_keel',[7.52,10.40,-9.85],[8.48,10.70,2.91],'gold','receiver','rail')
    for side in (-1,1):
        c(f'receiver_shoulder_{side}',[8+side*.48,12.10,-3.53],[.26,.26,12.70],'gold','receiver','crown',('z',side*45))
    # The distinct black separator bands taper into the continuous gold shell.
    for i,z in enumerate([-4.44,1.02]):
        for side in (-1,1):
            c(f'black_band_{i}_{side}',[8+side*.548,11.25,z],[.105,.70,.38],'black','receiver','band')
            c(f'gold_band_crest_{i}_{side}',[8+side*.55,11.91,z],[.12,.56,1.35],'gold','receiver','crest')
    for z,tag in [(-9.94,'front'),(2.98,'rear')]:
        box(tag+'_gold_collar',[7.37,10.55,z-.14],[8.63,12.36,z+.14],'gold','receiver','collar')
    # Recessed purple rectangles, bordered in their own per-face UV patches.
    for i,(z,length) in enumerate([(-6.35,1.88),(-2.14,3.02),(1.94,1.42)]):
        for side in (-1,1):
            c(f'purple_inset_{i}_{side}',[8+side*.551,11.30,z],[.065,.53,length],'purple','ornament','inset')
    # Octagonal raised orb bezels surround filled faceted cabochons. Their
    # thick tangent walls and central plugs are opaque solids, not alpha discs.
    for side in (-1,1):
        for i in range(8):
            a=math.radians(i*45)
            for tag,r,t,depth,xoff,mat in [('bezel',.49,.10,.14,.61,'gold'),('gem',.385,.23,.09,.72,'purple')]:
                rr=r-t/2
                c(f'orb_{tag}_{side}_{i}',[8+side*xoff,11.37+rr*math.cos(a),-2.14+rr*math.sin(a)],
                  [depth,t,2*r*math.tan(math.pi/8)+.004],mat,'ornament','orb' if tag=='gem' else 'bezel',('x',i*45))
        c(f'orb_gem_core_{side}',[8+side*.72,11.37,-2.14],[.09,.36,.36],'purple','ornament','orb')
    # Forearm: continuous black rails and discrete bridges create real slots.
    box('forearm_top_rail',[7.43,10.13,-8.62],[8.57,10.44,2.63],'black','forearm','rail')
    box('forearm_bottom_rail',[7.45,9.36,-8.60],[8.55,9.60,2.62],'black','forearm','rail')
    for i,z in enumerate([-8.48,-5.43,-2.55,.13,2.49]):
        box(f'forearm_bridge_{i}',[7.46,9.53,z-.16],[8.54,10.20,z+.16],'black','forearm','bridge')
    c('forward_hand_stop',[8,9.16,-7.31],[1.03,.69,.69],'black','forearm','grip',('x',-18))
    c('rear_forearm_swell',[8,9.59,-1.91],[1.19,.80,1.67],'black','forearm','grip')
    c('gas_tube',[8,9.94,-9.45],[.57,.54,1.68],'steel','gas','flute')
    tube('gas_socket',8,9.94,-10.34,-10.03,.32,.09,'black','gas')
    # Rear feed housing: solid roof/floor, genuinely open belt port on +X.
    box('feed_roof',[7.40,11.91,3.17],[8.60,12.27,6.74],'gold','feed','feed')
    box('feed_floor',[7.40,10.34,3.17],[8.60,10.77,6.81],'gold','feed','feed')
    box('feed_far_wall',[7.36,10.66,3.17],[7.64,12.00,6.81],'black','feed','feed')
    for z,tag in [(3.28,'front'),(6.66,'back')]:
        c('feed_'+tag+'_post',[8,11.36,z],[1.20,1.37,.30],'gold','feed','collar')
    c('rear_action',[8,11.29,7.28],[1.12,1.10,1.10],'gold','feed','rear_action',('x',12))
    for side in (-1,1):
        c(f'rear_cheek_inlay_{side}',[8+side*.59,11.63,6.08],[.10,.47,1.02],'black','feed','inset')
        c(f'rear_purple_pin_{side}',[8+side*.66,11.29,7.18],[.10,.34,.34],'purple','ornament','orb',('x',45))
    c('charging_shaft',[7.02,10.51,6.58],[1.29,.20,.25],'steel','feed','plain',('y',-14))
    c('charging_knob',[6.55,10.45,6.71],[.29,.44,.46],'black','feed','grip')
    # Original contact frame: grip near Z8, Y7.2..10.0, no transform offset.
    beam('pistol_grip',[8,7.64,8.92],[8,9.98,7.60],1.04,.94,'black','grip','grip')
    c('grip_heel',[8,7.41,8.92],[1.18,.34,1.03],'rubber','grip','grip')
    # Guard wraps around an empty trigger aperture, separate curved trigger.
    beam('guard_front',[8,8.79,6.58],[8,10.22,6.26],.27,.22,'black','guard')
    beam('guard_lower',[8,8.76,6.55],[8,8.76,7.88],.27,.22,'black','guard')
    beam('trigger',[8,9.44,7.16],[8,10.03,7.36],.21,.17,'steel','guard','plain')
    # Skeleton stock: open triangle bordered by comb, butt, and lower brace.
    c('stock_wrist',[8,10.95,8.50],[.84,.95,1.19],'black','stock','stock',('x',18))
    beam('stock_comb',[8,11.04,8.86],[8,10.96,12.94],.78,.52,'black','stock','stock')
    beam('stock_lower_brace',[8,7.84,9.02],[8,8.65,12.92],.77,.46,'black','stock','stock')
    beam('stock_butt_spine',[8,8.57,12.84],[8,11.05,12.84],.78,.67,'black','stock','stock')
    c('stock_butt_pad',[8,9.85,13.24],[.88,2.91,.44],'rubber','stock','butt')
    beam('stock_diagonal_web',[8,8.55,11.14],[8,10.75,12.53],.48,.36,'black','stock','stock')
    # Visible sling loop above the comb has a clear physical opening.
    for z in (9.47,11.57):
        c(f'sling_foot_{z}',[8,11.28,z],[.36,.47,.22],'black','stock','plain')
    c('sling_top',[8,11.52,10.52],[.36,.19,2.24],'steel','stock','plain')
    # +X ammunition box has real top recess, four walls and a solid bottom.
    box('ammo_box_bottom',[8.52,7.98,3.18],[12.44,8.25,6.03],'black','ammo_box','box')
    box('ammo_box_outside',[12.10,8.23,3.18],[12.44,9.79,6.03],'black','ammo_box','box')
    box('ammo_box_inside',[8.52,8.23,3.18],[8.82,9.79,6.03],'black','ammo_box','box')
    for z,tag in [(3.18,'front'),(5.72,'rear')]:
        box('ammo_box_'+tag,[8.79,8.23,z],[12.11,9.79,z+.31],'black','ammo_box','box')
    # W154: linked muzzleward rounds are authored by correct_parts below.
    # Rear triangular sight hood, actual clear aperture viewed down -Z.
    c('rear_sight_pedestal',[8,12.39,4.39],[.85,.25,.96],'gold','sight','sight')
    c('rear_sight_base',[8,12.55,4.42],[1.02,.14,.26],'gold','sight','rim')
    for side in (-1,1):
        c(f'rear_sight_arch_{side}',[8+side*.26,12.84,4.42],[.16,.79,.26],'gold','sight','rim',('z',side*31))
    for side in (-1,1):
        c(f'front_sight_ear_{side}',[8+side*.43,12.50,-9.85],[.20,.47,.35],'gold','sight','sight')
    from fix_belt_feed_w154 import correct_parts
    feed_w154=correct_parts('fixed_odds',{'full':specs})
    inputs=[SOURCE,BASE,'scripts/generate_surface_w123_beloved.py',
            ASSET+'items/weapon/fixed_odds.json',ASSET+'models/weapon/machine_gun/fixed_odds_ads.json',
            'src/main/resources/destiny/weapons/w46-timing.json','src/main/resources/destiny/sounds/w63-reload.json']
    ref=next(r for r in json.loads(REFS.read_bytes()) if r['id']=='fixed_odds')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    rawfiles=[RAW/'Fixed Odds.fbx',PHOTO,REFS]+[m for m in (RAW/'Textures/Fixed-Odds').glob('*_0.jpg')]
    return dict(id='fixed_odds',belt_feed_w154=feed_w154,family='machine_gun',revision='W154',method='authored semantic filled cuboids, full only',
                source=meta,reference=ref,palette=PALETTE,parts={'full':specs},
                atlas=dict(size=EDGE,gutter=2,texels_per_unit=24),
                frame=dict(anchor=meta['anchor'],scale=meta['scale'],muzzle_axis=[0,0,-1],display_policy='exact existing native full display',
                           hand_contact=[8,8.7,8.3],reload_policy='existing generic full-only; no split or animation graph'),
                openings=dict(stock=[8,9.75,10.20],trigger_guard=[8,9.45,6.80],sight=[8,12.80,4.42],muzzle=[8,11.41,-13.2],
                              forearm=[8,9.85,-6.80],ammo_box=[10.6,9.3,5.4],feed_port=[8.25,11.45,5.8]),
                input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
                raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawfiles},
                identity=['long gold receiver and dark longitudinal lower frame','purple rectangular insets and raised faceted medallions',
                          'open black stock, trigger guard and triangular rear sight','black open ammunition box and separate copper belt rounds'],
                limitations=['Offline CPU inspection only; native registration/parser/holding/ADS/reload pending master.',
                             'Clean default-dye reinterpretation with simplified sculpting; not an exact rip or PBR restoration.',
                             'FBX skin/rest belt is shown as raw reference; authored belt follows the assembled photo.'])


class Paint:
    def tile(self,spec,face,width,height):
        role=spec['material']; motif=spec['motif']
        u,v=np.meshgrid((np.arange(width)+.5)/width,(np.arange(height)+.5)/height)
        rgb=np.broadcast_to(np.array(PALETTE[role],float),(height,width,3)).copy()
        rgb*= (.91+.14*np.exp(-((v-.30)/.34)**2))[:,:,None]
        edge=np.minimum.reduce([u*width,(1-u)*width,v*height,(1-v)*height])
        rgb[edge<1]*=.63; rgb[(edge>=1)&(edge<2)]*=1.14
        side=face in ('east','west')
        if role in ('gold','edge'):
            rgb+=(2*np.cos(u*math.pi*2))[:,:,None]
        if side and motif=='gold_receiver':
            # Location-aware authored panels map consistently onto both sides.
            pts=vertices(spec['geometry'])[list(FACES[face])]
            pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
            zz,yy=pos[:,:,2],pos[:,:,1]
            rgb[abs(yy-11.12)<.020]*=.49
            # Front tapered black flute and lower engraved counterpart.
            taper=np.clip((-zz-6.8)/2.5,0,1)
            flute=(zz<-6.8)&(yy>11.50)&(yy<11.50+.23*taper)
            rgb[flute]=[29,31,32]
            rgb[(zz<-6.8)&(abs(yy-(10.79+.18*taper))<.025)]*=.52
            # Two sweeping saddle boundaries frame the black separator bands.
            for seam in (-4.44,1.02):
                dz=np.abs(zz-seam)
                curve=11.69+.50*np.clip(dz/1.05,0,1)**1.6
                rgb[(dz<1.05)&(np.abs(yy-curve)<.024)]*=.34
                rr=((zz-seam)/.085)**2+((yy-11.91)/.085)**2
                rgb[rr<1]*=.20
                rgb[(rr>1)&(rr<1.8)]*=1.15
        if side and motif=='crest':
            # Tapered saddle engraving and a real source-observed fastener mark.
            line=abs(v-(.18+.38*np.abs(u-.5)*2))<.026
            rgb[line]*=.40
            rr=((u-.50)/.065)**2+((v-.48)/.14)**2
            rgb[rr<1]*=.24; rgb[(rr>1)&(rr<1.7)]*=1.18
        if side and motif in ('feed','rear_action','stock','box'):
            line=(u>.10)&(u<.90)&((abs(v-.19)<.022)|(abs(v-.81)<.022))
            rgb[line]*=.50
            if motif=='box':
                for q in (.19,.50,.81):
                    rr=((u-q)/.025)**2+((v-.78)/.05)**2
                    rgb[rr<1]*=.5; rgb[(rr>1)&(rr<1.7)]*=1.45
        if role=='purple':
            # Broad lavender inset with dark frame, concentric cabochon relief.
            rgb[:]=np.array(PALETTE['purple'])*(.82+.24*np.exp(-((v-.3)/.34)**2))[:,:,None]
            if motif=='inset' and side:
                rgb[edge<2]=[46,36,48]; rgb[(edge>=2)&(edge<3)]*=1.26
            if motif=='orb' and side:
                pts=vertices(spec['geometry'])[list(FACES[face])]
                pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
                r=np.sqrt(((pos[:,:,1]-11.37)/.385)**2+((pos[:,:,2]+2.14)/.385)**2) if spec['geometry']['name'].startswith('orb_') else np.sqrt(((u-.5)*2)**2+((v-.5)*2)**2)
                rgb[(r>.69)&(r<.82)]*=.62
                rgb[(r>.57)&(r<.65)]*=1.20
                rgb+=np.exp(-(((u-.34)/.16)**2+((v-.28)/.16)**2))[:,:,None]*[24,20,25]
        if motif in ('butt','grip','barrel_flute','flute'):
            stripe=(np.mod(u*(18 if motif=='barrel_flute' else 9),1)<.13)&(v>.10)&(v<.90)
            rgb[stripe]*=.59
        if motif=='case':
            rgb*= (.83+.20*np.sin(u*math.pi))[:,:,None]
            rgb[(v>.82)&(v<.90)]*=.60
        if motif=='copper':
            rgb*= (.81+.27*np.sin(u*math.pi))[:,:,None]
        if motif=='link':
            rgb[(u>.30)&(u<.70)&(v>.27)&(v<.70)]*=.46
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((height,width),255,dtype='uint8')]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0)); tiles=[]; paint=Paint()
    for s in d['parts']['full']:
        vs=vertices(s['geometry'])
        for f,ix in FACES.items():
            p=vs[list(ix)]; w=np.linalg.norm(p[1]-p[0]); h=np.linalg.norm(p[3]-p[0])
            tw,th=max(6,min(320,math.ceil(w*24))),max(6,min(160,math.ceil(h*24)))
            tiles.append((s,f,tw,th))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2; row=0; uv={}; islands=[]
    for s,f,w,h in tiles:
        if x+w+2>EDGE: x=2; y+=row+4; row=0
        assert y+h+2<=EDGE,'1024 atlas overflow'
        tile=paint.tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        name=s['geometry']['name']; uv[name,f]=[q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=name,face=f,rect=[x,y,x+w,y+h]))
        x+=w+4; row=max(row,h)
    es=[]
    for s in d['parts']['full']:
        e=copy.deepcopy(s['geometry']); e['faces']={f:dict(uv=uv[e['name'],f],texture='#0') for f in FACES}; es.append(e)
    m=dict(credit='W132 Fixed Odds | authored filled semantic solids, full-only offline candidate',
           textures={'0':'destiny:item/weapon/w123/fixed_odds','particle':'destiny:item/weapon/w123/fixed_odds'},
           elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    d['atlas'].update(islands=islands,used_height=y+row+2)
    return atlas,m


def inspection(d,m,atlas):
    uid=lambda n:str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w132:fixed_odds:'+n))
    es=[]; groups={}
    for s,e in zip(d['parts']['full'],m['elements']):
        b=copy.deepcopy(e); r=b.pop('rotation',{})
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
                 origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values(): f.update(texture=0,uv=[q*EDGE/16 for q in f['uv']])
        es.append(b); groups.setdefault(s['group'],[]).append(b['uuid'])
    return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Fixed Odds W132 / editable full solids',
                resolution=dict(width=EDGE,height=EDGE),elements=es,
                outliner=[dict(name=k,uuid=uid(k),origin=[8,8,8],rotation=[0,0,0],children=v,export=True) for k,v in groups.items()],
                textures=[dict(name='fixed_odds.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                               source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
                display=m['display'],destiny_w132=dict(nativeAccepted=False,frame=d['frame'],representation='full only; groups are editing semantics'))


def source_triangles(meshes):
    result=[]
    for m in meshes:
        tex=np.array(Image.open(m['texture']).convert('RGBA'))
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]); length=np.linalg.norm(n)
            if length>1e-10: result.append((ps,uv,tex,n/length))
    return result


def comparison(d,meshes,atlas,m):
    w,h=1000,325; sheet=Image.new('RGB',(3000,1900),'#151c25'); draw=ImageDraw.Draw(sheet)
    def label(x,y,t,size=22): draw.text((x,y),t,fill='#e4e8ee',font_size=size)
    label(24,16,'FIXED ODDS / W132 / FULL-ONLY SOLID REMODEL / OFFLINE CPU INSPECTION',30)
    photo=Image.open(PHOTO).convert('RGB').crop((0,200,1850,880)); photo.thumbnail((1720,460)); sheet.paste(photo,(20,65))
    label(1770,90,'ACTUAL DEFAULT PHOTO',26)
    label(1770,140,'Gold + black / purple insets and orbs',24)
    label(1770,180,'Copper belt / open black stock and box',24)
    label(1770,230,'Photo muzzle is cropped: raw FBX supplies completion',21)
    label(1770,280,'Raw diffuse below is neutral, NOT the finished dye',21)
    label(1770,330,'Belt raw skin/rest pose differs from assembled photo',21)
    label(1770,380,'Native acceptance: PENDING MASTER',23)
    label(24,510,'RAW TEXTURED FBX / 30,249 triangles / neutral')
    label(w+24,510,'LOCAL W30 CANONICAL / 221 cuboids')
    label(2*w+24,510,f'NEW W132 / {len(m["elements"])} filled cuboids')
    old=json.loads((ROOT/BASE).read_bytes()); oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/fixed_odds.png'))
    ts=[source_triangles(meshes),helper.model_triangles({'old':old},oldtex),helper.model_triangles({'full':m},atlas)]
    pts=np.concatenate([v['vertices'] for v in meshes]+[vertices(e) for e in m['elements']])
    for row,(name,cam) in enumerate([('SIDE / BELT SIDE',[1,0,0]),('FRONT OBLIQUE / DEPTH',[1,.65,-.72]),('REAR / OPPOSITE SIDE',[-1,.45,.65])]):
        extent=helper.frame(pts,cam,w,h)
        for col,tr in enumerate(ts):
            im,_=helper.render(tr,cam,extent,(w,h),raw=col==0); sheet.paste(im,(col*w,550+row*h)); label(col*w+18,558+row*h,name,18)
    for i,(group,cam) in enumerate([('belt',[1,.6,-.8]),('stock',[1,.2,.2]),('muzzle',[.3,.2,-1]),('sight',[.1,.07,-1])]):
        names={s['geometry']['name'] for s in d['parts']['full'] if s['group']==group}
        es=[e for e in m['elements'] if e['name'] in names]; pts=np.concatenate([vertices(e) for e in es])
        im,_=helper.render(helper.model_triangles({'detail':dict(elements=es)},atlas),cam,helper.frame(pts,cam,750,320),(750,320))
        sheet.paste(im,(i*750,1540)); label(i*750+18,1548,group.upper()+' / actual solids',20)
    label(24,1873,'Shared camera + scale per full-model row. GUI, pack, first/third person, ADS, generic reload, audio, 10-20 displays: pending master.',18)
    return png(sheet)


def review_text(count,groups):
    return f"""# Fixed Odds W132 — offline art review

Actual default photo: `{PHOTO}`, Bungie screenshot 2194955522. Opened with view_image before authoring. Gold broad receiver, black lower frame/open stock/ammunition box, purple inset rectangles and medallions, exposed copper rounds. The muzzle is partly outside that photo; the complete raw FBX supplies its length and bore. The source neutral gray diffuse was opened too and is not treated as a finished default dye.

**{count} opaque, filled cuboids; 0 triangle-adapter outputs; full assembled count {count}/1000.** Semantic counts: {dict(groups)}. Started around a 100-element structural plan; the separate seven cartridges/links and real bored muzzle, vent rail, sight and box openings account for the additional meaningful solids. No source connected-island conversion, voxel transplant, alpha side shells or split resources. Broad receiver planes remain continuous; colored insets, tapered black flutes, fastener/crease relief, medallion rings and grip grooves use authored face UV. 1024 atlas, independent islands per face, two-pixel extruded gutters, fully opaque mapped faces. These are clean painted surfaces rather than raw grayscale reprojection or runtime metallic/PBR reflections.

The full-only candidate is `destiny:weapon_surface_w123/fixed_odds`. The production registry and wrappers are untouched. `inspection.bbmodel` embeds final editable cubes, face UVs and PNG; semantic editor groups are not reload splits. Existing full display is copied exactly. Coordinates retain W30 anchor {meta_placeholder()} and scale 18.72942333399612, negative-Z muzzle and original pistol-grip area. Existing ADS wrappers, generic full-only reload, timing and audio remain read-only inputs. No custom animation graph or animated belt was invented.

Comparison includes actual photo, original textured 30,249-triangle FBX (neutral diffuse and skin/rest belt explicitly labeled), the local 221-cube canonical and the new solid design, shared frame per row, side and both oblique views plus belt/stock/muzzle/sight close-ups. The FBX's .00.001 coalesces W30 metadata .00.000/.00.002; exact 30,249 triangles and W30 union bounds verify selection, with .03 reticle excluded.

Tests cover deterministic generation, real emitted schema/count, finite positive cube dimensions, valid face UV/opaque gutters, reference hashes, existing full display/anchor/scale/grip frame, embedded inspection parity, connected belt and clear stock/guard/forearm/feed/box/sight/muzzle points. These are practical offline regression checks, not an art score or a native acceptance claim. Sculpted curves, perfectly conical bullet tips and metallic reflections are simplified.

Master pending: register candidate in the existing full path; target 26.3 parser/rotation and pack/texture load; first/third-person hand contact and muzzle axis; ADS transition/sight; generic full-only reload with ammunition box and belt staying assembled, timing and audio; representative fire/muzzle alignment; short 10–20 display check. No Gradle, server, CU/Vision, Blockbench/Blender app or leases used.
"""


def meta_placeholder(): return '[8, 8, 8]'


def generate(include_comparison=True):
    meshes,meta=source_meshes(); d=make_design(meta); atlas,m=compile_model(d)
    count=len(m['elements']); assert count<=1000
    groups=Counter(s['group'] for s in d['parts']['full'])
    pts=np.concatenate([vertices(e) for e in m['elements']])
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(m),
             ART+'inspection.bbmodel':encode(inspection(d,m,atlas)),ART+'review.md':review_text(count,groups).encode()}
    manifest=dict(id='fixed_odds',family='machine_gun',revision='W132',representation='full',counts={'full':count},
                  assembled_elements=count,opaque_cuboids=count,triangle_adapter_elements=0,alpha_elements=0,emitted_faces=count*6,
                  semantic_counts=dict(groups),max_assembled_elements=1000,texture_size=[EDGE,EDGE],
                  actual_bounds=[pts.min(0).round(7).tolist(),pts.max(0).round(7).tolist()],source_bounds=meta['model_bounds'],
                  source_anchor=meta['anchor'],source_scale=meta['scale'],source_triangles=meta['source_triangles'],
                  canonical_display_exact=True,native_accepted=False,full_only=True,frame=d['frame'],
                  input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha(Path(__file__).read_bytes()),
                  output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    from fix_belt_feed_w154 import finish_outputs
    return finish_outputs('fixed_odds',outputs,include_comparison)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--verify',action='store_true'); args=p.parse_args()
    outputs=generate(); batch=json.loads((ROOT/'docs/qa/2026-10-26/w132/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w132-fixed_odds'))
    assert set(outputs)<=owned
    for rel,data in outputs.items():
        path=ROOT/rel
        if args.verify: assert path.is_file() and path.read_bytes()==data,'Regeneration differs: '+rel
        else: path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; full={m["assembled_elements"]}; faces={m["emitted_faces"]}')


if __name__=='__main__': main()
