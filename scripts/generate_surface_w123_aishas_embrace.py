#!/usr/bin/env python3
"""Aisha's Embrace W142: authored filled solids and coherent opaque face UV.

Only inert FBX arrays and images are read from the rip; no rip code is executed.
The existing reviewed Beloved parser/CPU raster helper is reused read-only.
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
ART = 'art/weapons/w123/aishas_embrace/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/scout_rifle/aishas_embrace.json'
MODEL = ASSET+'models/weapon_surface_w123/aishas_embrace.json'
TEXTURE = ASSET+'textures/item/weapon/w123/aishas_embrace.png'
BB = 'art/blockbench/weapons/w30/aishas_embrace.bbmodel'
RAW = Path('/tmp/destiny-weapons-w30/raw/aishas_embrace/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/aishas_embrace.jpg')
EDGE = 1024
H = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
FACES = H['FACES']
PALETTE = dict(black=[48,49,46], dark=[21,24,24], steel=[92,94,87],
               gold=[194,161,82], bright=[222,197,123], rubber=[30,33,31], lens=[22,27,31])

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()
def png(im):
    b=io.BytesIO(); im.save(b,format='PNG'); return b.getvalue()
def uid(v): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w142:aishas_embrace:'+v))
def vertices(e): return H['vertices'](e)

def source_meshes():
    """Read accepted W30 objects, verify the actual source frame and provenance."""
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Aishas Embrace.fbx').read_bytes())==meta['source_files']['Aishas Embrace.fbx']
    roots=H['parse_fbx'](RAW/'Aishas Embrace.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for n in objects:
        if n[0]!='Geometry':continue
        mid=next(parent for child,parent in links if child==n[1][0])
        model=models[mid]; name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        cs={c[0]:c for c in n[2]}
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        # FBX local basis already carries the 90-degree length-axis turn.
        v=np.c_[-raw[:,0],raw[:,2],raw[:,1]]*meta['scale']+meta['anchor']
        faces=[]; face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                faces.append(face);face=[]
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        mat=next((materials[child] for child,parent in links if parent==mid and child in materials),'AishasEmbraceReticle')
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,material=mat))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert {m['name'] for m in meshes}==set(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def source_triangles(meshes):
    textures={}
    for m in meshes:
        name=m['material'];path=RAW/(name+'_Diffuse.png')
        if not path.exists():path=RAW/(name+'.png')
        textures[name]=np.array(Image.open(path).convert('RGBA'))
    out=[]
    for m in meshes:
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:out.append((ps,uv,textures[m['material']],n/length))
    return out

def model_triangles(model,atlas):return H['model_triangles']({'full':model},atlas)

def reference_preview():
    meshes,meta=source_meshes();old=json.loads((ROOT/BASE).read_bytes())
    tex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/aishas_embrace.png'))
    ts=[source_triangles(meshes),model_triangles(old,tex)]
    points=np.concatenate([m['vertices'] for m in meshes]); w,h=1200,450
    sheet=Image.new('RGB',(2400,900),'#202730')
    draw=ImageDraw.Draw(sheet)
    for row,cam in enumerate(([1,0,0],[1,.4,-.65])):
        for col,t in enumerate(ts):
            im,_=H['render'](t,cam,H['frame'](points,cam,w,h),(w,h),raw=col==0)
            sheet.paste(im,(col*w,row*h))
            draw.text((col*w+20,row*h+20),'RAW NEUTRAL' if col==0 else 'OLD W30',fill='white',font_size=25)
    target=ROOT/(ART+'comparison.png');target.parent.mkdir(parents=True,exist_ok=True);sheet.save(target)

def make_design(meta):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);s=np.array(size,float)
        e=dict(name=name,**{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()})
        if turn:e['rotation']=dict(origin=c.tolist(),x=0,y=0,z=0);e['rotation'][turn[0]]=turn[1]
        parts.append(dict(group=group,material=mat,motif=motif,kind='filled_semantic_cuboid',geometry=e))
    def beam(group,name,a,b,width,thick,mat,motif='plain'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),thick],mat,motif,('x',round(math.degrees(math.atan2(v[2],v[1])),6)))
    def tube(group,name,z0,z1,y,r,t,mat,motif='plain'):
        for i in range(8):
            a=i*45;rc=r-t/2
            box(group,f'{name}_{i}',[8-rc*math.sin(math.radians(a)),y+rc*math.cos(math.radians(a)),(z0+z1)/2],
                [2*r*math.tan(math.pi/8)+.008,t,z1-z0],mat,motif,('z',a))
    # Continuous hollow barrel; gold nose and dark rear are paint on the same walls.
    tube('muzzle','barrel_wall',-9.224819,-5.35,10.12,.275,.105,'black','barrel')
    box('muzzle','bore_backstop',[8,10.12,-7.77],[.31,.31,.08],'dark')
    # The upper barrel rib has a real longitudinal slot, with supporting end bridges.
    for side in (-1,1):box('muzzle',f'slotted_rib_side_{side}',[8+side*.24,10.98,-7.46],[.16,.20,3.10],'black','rail')
    for z in (-8.98,-5.94):box('muzzle',f'rib_bridge_{z}',[8,10.98,z],[.62,.20,.16],'steel')
    # Broad load-bearing forebody, a solid tapered nose, and a long gold dorsal rail.
    box('forebody','forebody_core',[8,10.25,.28],[1.46,1.04,9.16],'black','body')
    box('forebody','forebody_upper',[8,10.94,.78],[1.35,.46,8.94],'black','wing')
    box('forebody','front_shroud',[8,10.37,-4.35],[1.52,1.25,2.35],'gold','nose')
    beam('forebody','swept_nose',[8,10.08,-5.75],[8,10.59,-4.80],1.32,.80,'gold','nose')
    box('forebody','dorsal_gold_rail',[8,11.30,.76],[.75,.18,7.75],'gold','rail')
    for side in (-1,1):
        box('forebody',f'upper_shoulder_{side}',[8+side*.62,11.08,.73],[.26,.26,8.90],'black','wing',('z',45*side))
        box('forebody',f'lower_chamfer_{side}',[8+side*.65,9.78,.26],[.24,.24,9.06],'black','body',('z',45*side))
    box('forebody','lower_access_panel',[8,9.66,1.50],[1.27,.28,4.93],'black','lower')
    box('forebody','underside_picatinny',[8,9.47,1.95],[1.13,.19,3.35],'steel','teeth')
    for z in (-1.94,-.98):
        for side in (-1,1):box('rail_clamps',f'rail_clamp_{z}_{side}',[8+side*.48,11.21,z],[.16,.81,.17],'gold','plain')
        box('rail_clamps',f'rail_clamp_bridge_{z}',[8,11.62,z],[1.10,.15,.17],'bright')
    # Deep receiver carries the Trials medallion; its long side is a coherent UV field.
    box('receiver','receiver_core',[8,10.94,7.52],[1.43,1.17,5.68],'black','receiver')
    box('receiver','receiver_comb',[8,11.60,7.70],[1.16,.19,5.43],'gold','comb')
    for side in (-1,1):box('receiver',f'receiver_shoulder_{side}',[8+side*.64,11.44,7.48],[.25,.25,5.13],'steel','receiver',('z',45*side))
    beam('receiver','forebody_receiver_slope',[8,10.05,3.78],[8,10.70,5.83],1.27,.46,'black','lower')
    box('receiver','guard_top_bridge',[8,10.20,8.02],[1.22,.32,4.10],'black','guard_top')
    # Upper stock arc and independent butt frame surround physical transverse air.
    arc=[(10.12,11.46),(11.60,11.13),(12.77,10.49),(13.70,9.44),(14.35,8.32)]
    for i,((z0,y0),(z1,y1)) in enumerate(zip(arc,arc[1:])):
        beam('stock',f'curved_stock_segment_{i}',[8,y0,z0],[8,y1,z1],1.15,.48,'black','stock')
    beam('stock','butt_upper_web',[8,10.73,14.19],[8,10.85,15.47],1.19,.37,'black','butt')
    box('stock','butt_plate',[8,9.42,15.54],[1.28,2.89,.29],'steel','butt')
    box('stock','butt_rubber',[8,9.42,15.73],[1.22,2.83,.09],'rubber','grip')
    box('stock','stock_heel',[8,7.94,14.80],[1.30,.27,1.50],'black','gold_edge')
    box('stock','heel_gold_cap',[8,7.78,14.96],[.54,.18,.37],'gold')
    # Filled hand-contact volume, sloping frontstrap and broad rear palm block.
    beam('grip','grip_frontstrap',[8,7.99,9.85],[8,9.71,10.68],1.10,.57,'black','grip')
    box('grip','palm_block',[8,9.02,11.76],[1.24,1.18,2.35],'black','palm')
    beam('grip','grip_heel',[8,7.82,10.05],[8,8.55,12.48],1.15,.58,'black','palm')
    box('grip','gold_upper_palm_insert',[8,9.74,11.42],[1.26,.19,1.47],'gold','insert')
    # Large loop guard: six substantial bars, finger space stays empty through X.
    guard=[(7.03,10.04),(7.13,9.25),(7.78,8.05),(8.52,7.25),(9.20,7.38),(9.91,8.03)]
    for i,((z0,y0),(z1,y1)) in enumerate(zip(guard,guard[1:])):
        beam('guard',f'guard_segment_{i}',[8,y0,z0],[8,y1,z1],.67,.37,'black','guard')
    beam('guard','guard_front_gold_spine',[8,9.56,7.08],[8,8.13,7.73],.71,.15,'gold','guard')
    beam('trigger','trigger',[8,10.02,8.05],[8,9.53,8.32],.22,.16,'gold','teeth')
    # Three filled continuous magazine lengths describe the source's curved sweep.
    beam('magazine','magazine_feed',[8,7.18,11.05],[8,8.27,11.72],1.17,1.95,'black','magazine')
    beam('magazine','magazine_curve',[8,6.15,10.53],[8,7.20,11.07],1.13,1.94,'black','magazine')
    beam('magazine','magazine_lower',[8,5.69,10.27],[8,6.25,10.58],1.10,1.94,'black','magazine')
    box('magazine','magazine_floor',[8,5.62,10.25],[1.24,.20,2.15],'gold','floor',('x',30))
    # Underslung rangefinder: solid enclosure, recessed front face, hanging blade.
    box('module','underbarrel_module',[8,9.16,-2.52],[1.57,.90,2.77],'black','module')
    for z in (-3.95,-1.06):box('module',f'module_gold_cap_{z}',[8,9.16,z],[1.65,.96,.16],'gold','module_cap')
    box('module','recessed_front_glass',[8,9.16,-4.055],[1.26,.61,.06],'dark','lens')
    for z in (-3.53,-1.54):box('module',f'module_saddle_{z}',[8,9.77,z],[1.06,.34,.27],'gold')
    beam('module','hanging_blade',[8,8.73,-4.02],[8,6.94,-3.36],.10,.14,'black','blade')
    # Raised optic, with an open front/rear recess and separate, inset opaque glass.
    box('optic','optic_rail',[8,11.74,6.03],[1.10,.14,3.00],'dark','teeth')
    for z in (5.18,6.99):box('optic',f'optic_foot_{z}',[8,11.87,z],[.75,.21,.40],'steel','mount')
    box('optic','optic_roof',[8,12.60,6.08],[.78,.23,2.77],'black','optic')
    box('optic','optic_floor',[8,12.01,6.08],[.83,.20,2.77],'black','optic')
    for side in (-1,1):
        box('optic',f'optic_sidewall_{side}',[8+side*.42,12.31,6.08],[.18,.64,2.77],'black','optic')
        box('optic',f'optic_roof_bevel_{side}',[8+side*.36,12.58,6.08],[.20,.20,2.77],'steel','optic',('z',side*45))
    for end,z in (('front',4.67),('rear',7.50)):
        for side in (-1,1):box('optic',f'{end}_hood_side_{side}',[8+side*.44,12.29,z],[.16,.89,.17],'steel','hood')
        for y in (11.90,12.69):box('optic',f'{end}_hood_cross_{y}',[8,y,z],[1.02,.14,.17],'black','hood')
        box('optic',f'{end}_recessed_lens',[8,12.29,z+(.33 if end=='front' else -.33)],[.65,.62,.045],'lens','lens')
    for z in (5.65,6.85):box('optic',f'optic_dial_{z}',[8.57,12.28,z],[.18,.40,.40],'black','dial',('x',45))
    # Source-supported side handle and the forward and rear small sight blades.
    box('controls','charging_handle',[7.18,11.21,5.44],[.35,.30,.66],'gold','handle')
    box('controls','handle_stem',[7.39,11.15,5.47],[.36,.16,.20],'black')
    box('sights','front_blade',[8,11.55,3.94],[.13,.56,.13],'gold','plain',('x',-15))
    box('sights','rear_blade',[8,11.78,11.00],[.13,.18,.24],'black')
    immutable=[BASE,BB,ASSET+'textures/item/weapon/w30/aishas_embrace.png','scripts/generate_surface_w123_beloved.py']
    raw=[PHOTO,RAW/'Aishas Embrace.fbx',RAW/'AishasEmbraceBody_Diffuse.png',RAW/'AishasEmbraceSight_Diffuse.png']
    return dict(id='aishas_embrace',revision='W142',method='authored filled semantic solids; selected source artwork on clean face UV',
        parts=parts,palette=PALETTE,source_metadata=meta,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='FBX local [-X,Z,Y] * source scale + source anchor',muzzle='-Z',display='canonical exact'),
        identity=['long black/gold forebody and paired gold dorsal clamps','original Trials suns and wing bands','raised black optic with deep end recesses','curving open stock / large loop guard','curved black/gold magazine and underslung module with hanging blade'],
        openings=dict(muzzle=dict(probe=[8,10.12,-9.1],axis='Z',backstop=-7.81),
                      optic_front=dict(probe=[8,12.29,4.70],axis='Z',lens=5.0),
                      optic_rear=dict(probe=[8,12.29,7.45],axis='Z',lens=7.17),
                      trigger_space=dict(probe=[8,8.9,8.65],axis='X'),
                      stock_air=dict(probe=[8,9.65,14.55],axis='X'),
                      optic_saddle=dict(probe=[8,11.87,6.0],axis='X')),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in immutable},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        selected_source_art=dict(receiver_medallion=dict(image='AishasEmbraceBody_Diffuse.png',pixels=[204,1170,382,1307]),
                                 wing_module_magazine='source-world side projection; intentional dark artwork only'),
        limitations=['Faceted circular barrel and segmented stock/magazine curves; local fillets simplified.',
            'Shallow vents, grip stipple, panel seams and Trials artwork are opaque face paint.',
            'Selected neutral-source artwork masks recolored to the actual default photo; static satin albedo, no dynamic PBR or optical refraction.',
            'Full-only output; native parser/pack/held/ADS/reload/audio/20-display checks remain with master.'])

class Paint:
    def __init__(self,meshes):
        # Project original artwork once, then keep only intentional dark motif shapes.
        # This never creates geometry from the source mesh or transplants UV fragments.
        points=np.concatenate([m['vertices'] for m in meshes]);self.fields={}
        self.medallion=np.array(Image.open(RAW/'AishasEmbraceBody_Diffuse.png').convert('RGB').crop((204,1170,382,1307)))
        tris=source_triangles(meshes)
        unlit=[(p,uv,t,np.zeros(3)) for p,uv,t,n in tris]
        for side in (-1,1):
            cam=[side,0,0];ext=H['frame'](points,cam,2048,720)
            im,mask=H['render'](unlit,cam,ext,(2048,720),raw=True)
            self.fields[side]=(np.array(im),mask,ext)

    def source_ink(self,q,side):
        im,mask,(c,s)=self.fields[side]
        # camera +X has right=-Z, camera -X has right=+Z.
        x=np.clip(np.rint((-side*q[:,:,2]-c[0])*s+1024-.5).astype(int),0,2047)
        y=np.clip(np.rint(360-(q[:,:,1]-c[1])*s-.5).astype(int),0,719)
        return (im[y,x,:3].mean(2)<18)&mask[y,x]

    def tile(self,spec,face,w,h):
        u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
        p=vertices(spec['geometry'])[list(FACES[face])]
        q=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0]);x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
        role=spec['material'];motif=spec['motif'];base=np.array(PALETTE[role],float)
        arr=np.broadcast_to(base,(h,w,3)).copy()*(.98+.035*np.cos(y*2.1))[:,:,None]
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        arr[edge<.7]*=.77;arr[(edge>=.7)&(edge<1.4)]*=1.12
        side=face in ('east','west');ink=self.source_ink(q,1 if face=='east' else -1) if side else np.zeros((h,w),bool)
        def paint(mask,color):arr[mask]=color
        if motif=='barrel':
            paint(z<-7.85,PALETTE['gold']);paint(abs(z+8.35)<.025,PALETTE['bright'])
            paint((abs(z+8.40)<.018)|(abs(z+7.88)<.02),[105,83,38])
        if motif in ('wing','body'):
            paint((y>10.52)&(z>-2.20)&(z<4.07)&ink,PALETTE['gold'])
            if side:
                paint((abs(y-10.13)<.022)&(z>-1.45)&(z<3.50),[14,18,19])
                paint((abs(z+3.86)<.025)|(abs(z-4.52)<.025),[74,75,66])
                paint((z+3.46)**2+(y-10.61)**2<.10**2,PALETTE['gold'])
        if motif=='nose':
            paint((z>-4.6)&(y<10.27+.36*(z+4.6)),PALETTE['black'])
            if side:paint(abs(z+5.05)<.018,[134,111,58])
        if motif=='receiver' and side:
            # Original eye/sun crop with its complete aspect; separate side islands.
            a=np.clip((z-9.00)/1.30,0,1);b=np.clip((11.57-y)/1.00,0,1)
            art=self.medallion[np.minimum((b*137).astype(int),136),np.minimum((a*178).astype(int),177)]
            paint((z>9.00)&(z<10.30)&(y>10.57)&(y<11.57)&(art.mean(2)<65),PALETTE['bright'])
            port=((z-5.55)/.54)**2+((y-11.18)/.19)**2
            paint(port<1,[18,22,22]);paint((port>.88)&(port<1.10),[102,101,85])
            paint((abs(y-10.66)<.018)&(z>5.7)&(z<9.6),[67,69,64])
            paint((z>7.15)&(z<7.52)&(y>11.03)&(y<11.17),[12,16,17])
            for zz in (6.00,8.45,10.12):
                r=(z-zz)**2+(y-10.79)**2
                paint(r<.050**2,[15,19,20]);paint((r>.05**2)&(r<.070**2),[108,107,89])
        if motif=='comb':paint((z>8.45)&(np.mod(z*.98,.5)<.11),PALETTE['black'])
        if motif=='lower' and side:
            paint((y<9.9)&(z>-.1)&(z<4.4)&(y>9.58+.12*(z-.5)),PALETTE['gold'])
            paint((abs(y-9.77)<.025)&(z>1.2)&(z<3.8),[12,16,18])
        if motif=='stock':
            e=spec['geometry'];r=e['rotation'];local=(q-np.array(r['origin']))@H['rotation'](r)
            paint((local[:,:,2]<-.16)&side,PALETTE['gold'])
            if side:paint((local[:,:,2]>.12)&(local[:,:,2]<.145),[88,88,77])
        if motif=='butt' and side:
            paint((z>14.90)&(y>10.0)&(np.mod(y*9,.5)<.20)&(np.mod(z*9,.5)<.20),[14,18,19])
            paint((z>15.54)&(abs(y-8.2)<.07),PALETTE['gold'])
        if motif=='gold_edge':paint((v<.22)|((u>.81)&side),PALETTE['gold'])
        if motif=='palm' and side:
            for zz,yy,r in ((11.08,9.27,.12),(12.07,8.88,.105),(12.37,8.90,.105)):
                rr=(z-zz)**2+(y-yy)**2;paint(rr<r*r,PALETTE['gold']);paint(rr<(r*.67)**2,[29,33,32])
            paint((abs(y-8.36)<.021)&(z>11.1),[102,104,91])
        if motif in ('grip','guard') and side:
            paint((np.mod(y*9+z*2,1)<.23),np.array(PALETTE[role])*.67)
            if motif=='guard':paint(ink&(z<8.8),PALETTE['gold'])
        if motif=='magazine' and side:
            paint(ink,PALETTE['gold'])
            # Keep source band geometry, restrained edge-rib relief.
            paint((u<.07)|(u>.93),[139,119,68])
        if motif=='module' and side:
            paint(ink,PALETTE['gold'])
            paint((v<.06)|(v>.94),PALETTE['gold'])
        if motif=='module_cap':
            rr=(u-.5)**2+(v-.5)**2
            if side:paint((rr>.07)&(rr<.13),PALETTE['bright']);paint(rr<.045,[101,84,44])
        if motif in ('teeth','floor'):
            paint(np.mod(z*9,1)<.22,base*.51)
        if motif in ('optic','hood'):
            if side:
                paint((abs(z-5.11)<.025)|(abs(z-6.70)<.026),[110,112,105])
                paint((y<12.15)&(z>5.42)&(z<6.7),[16,20,22])
                paint((abs(y-12.40)<.02)&(z>5.25)&(z<5.73),[87,92,89])
        if motif=='lens':
            rr=(u-.5)**2+(v-.5)**2
            paint(rr<.19,[18,29,34]);paint((rr>.18)&(rr<.24),[50,65,69])
            paint((u<.27)&(v<.25),[76,91,93])
        if motif=='dial':
            rr=(u-.5)**2+(v-.5)**2;paint(rr<.12,PALETTE['steel']);paint(rr<.065,PALETTE['black'])
        return Image.fromarray(np.dstack([np.clip(arr,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d,meshes):
    painter=Paint(meshes);atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry'];e['faces']={}
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=23 if face in ('east','west') else 16
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[]
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,('atlas overflow',name,y+h)
        im=painter.tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        spec['geometry']['faces'][face]=dict(uv=[v*16/EDGE for v in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,dict(credit='W142 Aishas Embrace / semantic filled solids / source Trials art / clean default-dye face UV',
        textures={'0':'destiny:item/weapon/w123/aishas_embrace','particle':'destiny:item/weapon/w123/aishas_embrace'},
        elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])

def inspection(d,model,atlas):
    es=[];groups=collections.defaultdict(list)
    for spec,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation',None)
        b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],rotation=[r.get(a,0) if r else 0 for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);groups[spec['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name="Aisha's Embrace W142 editable inspection",
        resolution={'width':EDGE,'height':EDGE},elements=es,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=c,export=True) for g,c in groups.items()],
        textures=[dict(name='aishas_embrace.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=copy.deepcopy(model['display']),destiny_w142=dict(full_only=True,anchor=d['coordinate_policy']['anchor'],native_accepted=False))

def comparison(d,meshes,atlas,model):
    w,h=1000,365;sheet=Image.new('RGB',(3000,1940),'#171f29');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=22):draw.text((x,y),s,fill='#e3e9e9',font_size=size)
    label(22,14,"AISHA'S EMBRACE / W142 / FILLED SEMANTIC SOLIDS + COHERENT FACE UV / OFFLINE",30)
    photo=Image.open(PHOTO).convert('RGB').crop((300,260,1900,900));photo.thumbnail((1230,440));sheet.paste(photo,(20,60))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / {6*len(model["elements"])} face UVs / full only',
        'Actual default photo: black satin, warm gold, original Trials sun/wing art',
        'Physical muzzle bore, sight recesses, loop guard, curved stock air and width',
        'Existing scale / anchor / axes / canonical display retained',
        'No gameplay / ADS / twohand / audio / reload edits; no split reload added',
        'Raw = inert FBX + neutral diffuse; old = unchanged canonical W30 + texture',
        'All model panels are matched-camera CPU renders, not native screenshots']):label(1300,77+i*49,line,23)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/aishas_embrace.png'))
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes]+[vertices(e) for e in model['elements']])
    for col,s in enumerate(['ACTUAL RAW / 26,485 TRIANGLES / NEUTRAL','OLD W30 / 217 CUBOIDS / EXISTING PAINT',f'NEW W142 / {len(model["elements"])} FILLED CUBOIDS']):label(col*w+15,503,s,22)
    for row,(name,cam) in enumerate([('SIDE / MUZZLE LEFT',[-1,0,0]),('MUZZLE OBLIQUE / TRANSVERSE DEPTH',[-1,.45,-.65]),('REAR OBLIQUE / STOCK AND GUARD',[1,.35,.60])]):
        ext=H['frame'](points,cam,w,h)
        for col,t in enumerate(ts):
            im,_=H['render'](t,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,540+row*h));label(col*w+15,548+row*h,name,19)
    for i,group in enumerate(('muzzle','optic','guard','stock')):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        sub=[e for e in model['elements'] if e['name'] in names];pts=np.concatenate([vertices(e) for e in sub])
        cam=[-.28,.18,-1] if group in ('muzzle','optic') else [-1,.3,-.45]
        im,_=H['render'](model_triangles(dict(elements=sub),atlas),cam,H['frame'](pts,cam,750,255),(750,255))
        sheet.paste(im,(i*750,1650));label(i*750+15,1657,group.upper()+' / PHYSICAL GEOMETRY',19)
    label(20,1913,'Offline evidence only. Master owns native pack/parser, held views, ADS, generic reload/audio and 10-20-display smoke. No DCC or game launched.',19)
    return png(sheet)

def review_text(d,n):
    return f'''# Aisha's Embrace W142 review

{n} emitted filled cuboids, {n*6} face UV islands, zero triangle adapters and zero alpha silhouette elements. Full only, beneath the assembled 1,000-element hard cap. The first blockout uses about 100 semantic pieces; geometry is justified by shape/depth, not by a count target.

Actual default Bungie/light.gg photo: `{PHOTO}`. Actual local W30 FBX was parsed as inert arrays: exactly eight accepted objects, 26,485 source triangles, verified W30 bounds and immutable FBX hash. Original raw body diffuse and its Trials sun/wing artwork are structural/art inputs, not finished default dye. The clean black/warm-gold palette follows the actual photo. Selected original dark motif masks are world-projected into independent UV faces; panel fields are repainted, rather than copying rip fragments or noisy albedo indiscriminately. No source script, shader, blend executable content, DCC app or game was run. Read-only Beloved FBX parser, vertex math and CPU raster helper are reused.

Identity: long black/gold shroud and upper gold rail/clamps, original Trials wing bands and sun medallions, raised black optic, curving stock, large loop guard, curved magazine and underslung module/hanging blade. Main housing, receiver, palm grip and magazine are filled transverse solids. Eight thick barrel walls surround a real bore with a backstop 1.41 units behind the tip. Optic hood walls and glass have physical end recesses; guard, stock and optic saddle have actual through-X air. Stock and magazine curvature use a few rotated substantial volumes. Shallow screw heads, seams, vents, rail teeth and grip ribs remain UV details. No invented text or imported foreign emblem.

Frame: `{d['coordinate_policy']['mapping']}`, source scale {d['coordinate_policy']['scale']}, anchor {d['coordinate_policy']['anchor']}, muzzle -Z. No recenter/rescale. Canonical display dictionaries copied exactly. Existing ADS/twohand parents, generic reload, timings, audio, gameplay, HUD and registries are untouched. No new split reload requirement.

1024 RGBA atlas: aspect-proportional face islands, 2px extruded gutters, opaque pixels on all faces. Selected source motifs are continuous in world Y/Z across the forebody and its bevels; side fields have independent allocations. Editable inspection.bbmodel embeds the exact solids, all rotations, semantic groups, face UVs, atlas and canonical display. It was prepared on disk without touching live Blockbench/Blender.

comparison.png contains the actual default photo plus actual raw FBX/neutral diffuse, unchanged old W30 JSON/texture, and the new full model at matched side, muzzle-oblique and rear-oblique cameras. Four extra geometry views inspect muzzle, optic recesses, guard and curved stock. These are offline CPU evidence. Native parser/resource-pack loading, first/third-person and ADS contact/visibility, generic reload/audio continuity and a short 10-20-display observation remain with master. Native acceptance and performance are not claimed.

Limits: faceted tube cross section; simplified stock/palm/magazine fillets and local controls; a static matte/satin interpretation of gold and glass, not PBR, reflection or refraction recovery. Small vents/teeth are painted. Test results and exact scope/export evidence are in the worker report.
'''

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d,meshes);n=len(model['elements'])
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='aishas_embrace')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    out={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,n).encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);assert 0<n<=1000
    m=dict(id=d['id'],revision='W142',assembled_elements=n,counts={'full':n},opaque_cuboids=n,emitted_faces=n*6,
        alpha_body_elements=0,triangle_adapter_elements=0,max_assembled_elements=1000,
        groups=dict(collections.Counter(s['group'] for s in d['parts'])),actual_bounds=[p.min(0).round(6).tolist(),p.max(0).round(6).tolist()],
        source_bounds=meta['model_bounds'],source_triangles=meta['source_triangles'],canonical_elements=217,
        source_scale=meta['scale'],source_anchor=meta['anchor'],canonical_display_exact=True,full_only=True,native_accepted=False,
        texture_size=[EDGE,EDGE],face_islands=d['atlas']['face_islands'],generator_sha256=sha(Path(__file__).read_bytes()),
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(b) for p,b in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(m);return out

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    out=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w142/batch.json').read_bytes())
    scope=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w142-aishas_embrace'))
    assert len(scope)==10 and set(out)<=scope
    for path,data in out.items():
        target=ROOT/path
        if args.verify:assert target.read_bytes()==data,'Regeneration differs: '+path
        else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    m=json.loads(out[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(out)} artifacts / {m["assembled_elements"]} solids / {m["emitted_faces"]} faces / full only')

if __name__=='__main__':main()
