#!/usr/bin/env python3
"""W128 Dust Rock Blues: hand-authored solids, opaque face atlas, full model only.

Run with the bundled numpy/Pillow Python. Helpers are loaded read-only; no DCC,
network, subprocess, shared manifest mutation, or source-mesh conversion.
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
ID = 'dust_rock_blues'
ART = f'art/weapons/w123/{ID}/'
ASSET = 'src/main/resources/assets/destiny/'
MODEL = ASSET + f'models/weapon_surface_w123/{ID}.json'
TEXTURE = ASSET + f'textures/item/weapon/w123/{ID}.png'
BASE = ASSET + f'models/weapon/shotgun/{ID}.json'
BB = f'art/blockbench/weapons/w30/{ID}.bbmodel'
GENERATOR = f'scripts/generate_surface_w123_{ID}.py'
RAW = Path('/tmp/destiny-weapons-w30/raw/dust_rock_blues/extracted/Dust Rock Blues')
FBX = RAW / 'Dust Rock Blues.fbx'
PHOTO = Path('/tmp/destiny-weapons-w31/references/dust_rock_blues.jpg')
EDGE = 1024
HELPER = runpy.run_path(str(ROOT/'scripts/generate_surface_w115_hammerhead.py'))
FACES = HELPER['FACES']
PALETTE = {'red':[169,60,57], 'red_edge':[181,69,63], 'ivory':[204,199,176],
           'steel':[157,162,158], 'darksteel':[69,73,68], 'rubber':[29,31,29],
           'bore':[16,20,22], 'lamp':[215,234,255]}

def sha(data): return hashlib.sha256(data).hexdigest()
def encode(data): return (json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(name): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w128:dust_rock_blues:'+name))

def source_meshes():
    """Apply the FBX carrier translation before the unchanged W30 axis mapping."""
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha(FBX.read_bytes())==meta['source_files']['Dust Rock Blues/Dust Rock Blues.fbx']
    parser=runpy.run_path(str(ROOT/'scripts/generate_reload_models_w100.py'))['parse_fbx']
    roots=parser(FBX);objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'};meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        model=models[next(p for c,p in links if c==node[1][0])]
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        assert np.allclose(props['Lcl Translation'],[0,-2.997842311859131,-11.230729103088379])
        c={n[0]:n for n in node[2]};v=np.array(c['Vertices'][1][0]).reshape(-1,3)
        # FBX centimetre Y-up translation expressed in original Blender Z-up metres.
        t=props['Lcl Translation'];v+=np.array([t[0],-t[2],t[1]])/100
        v=8+v[:,[0,2,1]]*meta['scale'];faces=[];poly=[]
        for i in c['PolygonVertexIndex'][1][0]:
            poly.append(i if i>=0 else -i-1)
            if i<0:
                faces.extend((poly[0],poly[j],poly[j+1]) for j in range(1,len(poly)-1));poly=[]
        assert not poly
        meshes.append(dict(name=node[1][1].split('\0')[0],vertices=v,faces=np.array(faces)))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=.00001)
    assert sum(len(m['faces']) for m in meshes)==19031
    return meshes,meta

def geometry():
    specs=[]
    def box(group,name,c,size,mat,motif='',angles=(0,0,0)):
        c=np.array(c,float);s=np.array(size,float)
        specs.append(dict(group=group,material=mat,motif=motif,kind='solid_cuboid',geometry={
            'name':name,'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist(),
            'rotation':dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles)))}))
    def beam(group,name,a,b,width,depth,mat,motif=''):
        a=np.array(a,float);b=np.array(b,float);v=b-a;assert abs(v[0])<1e-8
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0))
    def ring(group,name,z,y,r,wall,depth,mat):
        for i in range(8):
            a=i*45;t=math.radians(a)
            box(group,f'{name}_{i}',[8+r*math.cos(t),y+r*math.sin(t),z],
                [2*r*math.tan(math.pi/8)+.012,wall,depth],mat,'collar',(0,0,a-90))

    # A long, deep octagonal shroud: one broad core, two crown shoulders and
    # bevels. The nose/crown/tail are separated only for silhouette transitions.
    box('shroud','Long_red_shroud',[8,10.91,2.27],[1.72,1.29,13.40],'red','shroud')
    box('shroud','Raised_crown',[8,11.89,1.0],[1.24,.42,8.9],'red','crown')
    beam('shroud','Crown_front_slope',[8,11.57,-4.25],[8,12.00,-3.05],1.24,.29,'red')
    beam('shroud','Crown_rear_slope',[8,12.00,5.35],[8,11.50,7.55],1.24,.29,'red')
    for side in (-1,1):
        box('shroud',f'Crown_shoulder_{side}',[8+side*.62,11.72,1.0],[.52,.52,8.90],
            'red_edge','shroud',(0,0,side*38))
        box('shroud',f'Lower_shroud_bevel_{side}',[8+side*.68,10.30,2.27],[.37,.35,13.4],
            'red','stripe',(0,0,-side*36))
    box('shroud','Breech_red_tail',[8,10.87,10.02],[1.66,1.17,2.26],'red','breech')
    box('shroud','Breech_top',[8,11.47,9.93],[1.26,.24,2.42],'red','crown')
    box('shroud','Nose_drop',[8,9.81,-3.55],[1.63,.93,1.63],'red','nose')
    beam('shroud','Nose_lower_slope',[8,9.44,-3.05],[8,9.97,-1.60],1.54,.29,'red')
    box('receiver','Loading_housing',[8,9.67,6.99],[1.42,.73,4.72],'red','loading')
    box('receiver','Loading_floor',[8,9.27,7.10],[1.16,.18,4.60],'darksteel','floor')
    box('receiver','Breech_lock',[8,10.02,10.06],[1.53,.61,1.95],'red','breech')
    # Exposed rear barrel ribs are painted on a broad full-section inset, not
    # converted into dozens of stacked strips or source components.
    box('receiver','Exposed_barrel_sleeve',[8,11.02,8.55],[1.78,.90,1.75],'darksteel','sleeve')
    box('receiver','Underbarrel_rail',[8,9.73,1.00],[1.06,.37,7.54],'darksteel','rail')
    for side in (-1,1):
        box('receiver',f'Bright_slide_rail_{side}',[8+side*.61,9.61,2.58],[.17,.24,7.20],'steel','rail')

    # Solid ivory stock, with the original shallow drop, raised heel, and low
    # pistol-grip hand contact. No alpha profile and no invented stock window.
    box('stock','Ivory_stock',[8,10.20,14.15],[1.38,1.80,5.76],'ivory','stock')
    beam('stock','Stock_sloping_comb',[8,11.25,11.22],[8,10.70,15.48],1.24,.37,'ivory','comb')
    box('stock','Stock_wrist',[8,10.11,11.15],[1.30,1.69,1.48],'ivory','wrist')
    beam('stock','Stock_lower_drop',[8,9.44,15.55],[8,8.99,17.65],1.21,.31,'ivory')
    beam('stock','Heel_riser',[8,10.81,16.54],[8,11.70,18.14],1.23,.45,'ivory','comb')
    box('stock','Butt_attachment',[8,10.37,17.95],[1.32,2.69,.87],'ivory','stock')
    box('stock','Heel_solid_web',[8,10.25,17.15],[1.30,1.50,1.60],'ivory')
    beam('grip','Ivory_grip',[8,9.24,10.62],[8,6.43,12.30],1.23,1.25,'ivory','grip')
    beam('grip','Grip_backstrap',[8,9.05,11.10],[8,6.40,12.77],1.10,.29,'ivory','grip')
    beam('grip','Grip_black_insert',[8,8.55,10.79],[8,6.28,12.10],1.25,.37,'rubber','grip_ribs')
    box('grip','Grip_rounded_heel',[8,5.92,12.55],[1.23,.78,1.23],'ivory','grip')
    beam('grip','Grip_rear_flare',[8,6.12,12.90],[8,7.03,13.35],1.16,.57,'ivory','grip')
    beam('grip','Ivory_diagonal_latch',[7.24,9.16,10.43],[7.24,10.30,12.32],.20,.57,'ivory','latch')
    # Original trigger is exposed. Preserve surrounding air, do not invent a
    # closed guard loop or a magazine reload partition.
    beam('trigger','Trigger_blade',[8,9.33,9.41],[8,8.63,9.58],.25,.24,'darksteel')
    beam('trigger','Trigger_hook',[8,8.63,9.58],[8,8.55,9.24],.25,.22,'darksteel')

    # Thick butt pad, three segments justified by heel/waist/toe silhouette.
    box('butt','Red_butt_main',[8,10.25,18.59],[1.59,2.92,.74],'red','butt')
    beam('butt','Red_butt_heel',[8,11.53,18.10],[8,11.95,18.46],1.48,.62,'red','butt')
    beam('butt','Red_butt_toe',[8,8.45,17.53],[8,8.72,18.57],1.54,.59,'red','butt')
    box('butt','Butt_dark_contact',[8,10.19,19.05],[1.44,2.73,.25],'rubber','pad')
    beam('butt','Butt_waist_inset',[7.16,10.20,17.94],[7.16,9.63,18.24],.13,.40,'rubber','pad')

    # The six physical silver wrap ribs dominate the side and underside. Three
    # solid bars per rib create real black inter-rib channels and open corners.
    box('foreend','Foreend_black_core',[8,9.12,.74],[1.37,.69,4.62],'rubber','pump')
    for i,z in enumerate(np.linspace(-1.18,2.81,6)):
        for side in (-1,1):
            box('foreend',f'Pump_rib_{i}_side_{side}',[8+side*.81,9.13,z],[.27,1.01,.32],
                'steel','pump_rib',(0,0,side*8))
        box('foreend',f'Pump_rib_{i}_bottom',[8,8.69,z],[1.57,.26,.32],'steel','pump_rib')
    box('foreend','Pump_front_stop',[8,9.17,-1.73],[1.66,.73,.32],'darksteel','pump')
    box('foreend','Pump_rear_stop',[8,9.16,3.38],[1.65,.74,.36],'darksteel','pump')

    # Real muzzle entry, continuous ring walls and a recessed blind bore.
    ring('muzzle','Muzzle_collar',-4.96,10.96,.57,.20,.62,'darksteel')
    ring('muzzle','Muzzle_lip',-5.48,10.96,.47,.14,.22,'steel')
    ring('muzzle','Bore_wall',-4.98,10.96,.385,.12,.91,'bore')
    box('muzzle','Bore_backstop',[8,10.96,-4.48],[.67,.67,.10],'bore')
    # Lamp below barrel: geometric surround and inset lens. Lens is static UV.
    box('lamp','Lamp_housing',[8,9.72,-4.77],[1.10,.91,.77],'steel','lamp_housing')
    for side in (-1,1):
        box('lamp',f'Lamp_bezel_side_{side}',[8+side*.31,9.72,-5.22],[.13,.75,.24],'darksteel')
        box('lamp',f'Lamp_bezel_cross_{side}',[8,9.72+side*.31,-5.22],[.51,.13,.24],'darksteel')
    box('lamp','Lamp_lens',[8,9.72,-5.30],[.47,.47,.06],'lamp','lens')
    # Twin open rear iron ears, no opaque optic block in the aiming aperture.
    box('sights','Rear_sight_base',[8,11.66,10.12],[.93,.25,.87],'darksteel','rail')
    for side in (-1,1):
        box('sights',f'Rear_sight_ear_{side}',[8+side*.33,12.10,10.17],[.15,.73,.21],'steel')
    box('sights','Rear_notch_sill',[8,11.92,10.17],[.64,.19,.21],'darksteel')
    box('sights','Front_sight_base',[8,11.66,-4.16],[.66,.16,.65],'darksteel')
    box('sights','Front_sight_blade',[8,11.86,-4.17],[.15,.30,.36],'steel')
    return specs

def tile(spec,face,w,h):
    mat=spec['material'];base=np.array(PALETTE[mat],float);yy,xx=np.mgrid[:h,:w]
    u=(xx+.5)/w;v=(yy+.5)/h
    col=np.broadcast_to(base,(h,w,3)).copy()*(.97+.045*np.sin(v*math.pi))[:,:,None]
    rim=(xx==0)|(yy==0)|(xx==w-1)|(yy==h-1)
    if mat not in ('rubber','bore','lamp'):col[rim]=np.minimum(255,base+12)
    im=Image.fromarray(np.dstack([col.clip(0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))
    pts=HELPER['vertices'](spec['geometry'])[list(FACES[face])]
    world=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0]);wy=world[:,:,1];wz=world[:,:,2]
    motif=spec['motif'];side=face in ('east','west');dr=ImageDraw.Draw(im)
    def paint(mask,color):
        nonlocal im,dr
        a=np.array(im);a[mask,:3]=color;im=Image.fromarray(a);dr=ImageDraw.Draw(im)
    def line(points,color,width=1):dr.line([(int(x*w),int(y*h)) for x,y in points],fill=color,width=width)
    if side and motif in ('shroud','stock','wrist','loading','breech','butt','grip'):
        line([(.04,.15),(.25,.15),(.28,.25),(.70,.25),(.78,.10),(.95,.10),(.95,.87),(.65,.87)],
             '#6e3330' if mat=='red' else '#77756a')
        for fx,fy in ((.09,.73),(.88,.21)):
            cx=int(fx*w);cy=int(fy*h);r=max(1,round(min(w,h)*.045))
            dr.ellipse([cx-r,cy-r,cx+r,cy+r],fill='#3e423c',outline='#9b9b8b')
    if mat=='red' and side:
        # Restrained edge chips at the lower seam rather than noisy full diffuse.
        wear=(wy<10.56)&(np.sin(wz*17.1)+np.cos(wy*21+wz*5)>1.64)
        paint(wear,[65,60,55])
    if motif in ('stripe','sleeve','pump','grip_ribs','pad','collar'):
        if motif=='sleeve':paint((np.mod(wz,.15)<.045),[145,64,57])
        elif motif in ('grip_ribs','pad'):paint(np.mod(wy+wz*.14,.095)<.025,[74,75,65])
        elif motif=='stripe':paint(np.mod(wy,.105)<.045,[58,42,36])
        elif motif=='pump':paint(np.mod(wz,.22)<.040,[65,69,61])
        elif motif=='collar' and face not in ('north','south'):paint(np.mod(wz,.12)<.027,[106,109,96])
    if motif=='pump_rib':
        line([(.16,.12),(.16,.86),(.83,.86)],'#e0e0d0')
        line([(.34,.20),(.34,.74)],'#595e57',max(1,w//12))
    if motif in ('stock','wrist','grip') and side:
        grid=(wz>13.15)&(wz<14.30)&(wy>9.86)&(wy<10.56)
        grid|=(wz>11.25)&(wz<12.05)&(wy>7.53)&(wy<8.20)
        paint(grid&(np.mod(wz,.13)<.055)&(np.mod(wy,.12)<.055),[42,45,39])
        if motif=='stock':
            # Actual small technical label from DRBDecals, below the stock grid.
            source=np.array(Image.open(RAW/'DRBDecals.png').convert('RGB').crop((97,175,331,232)))
            uu=(wz-13.22)/.91;vv=(10.00-wy)/.23
            inside=(uu>=0)&(uu<1)&(vv>=0)&(vv<1)
            sx=np.clip((uu*source.shape[1]).astype(int),0,source.shape[1]-1)
            sy=np.clip((vv*source.shape[0]).astype(int),0,source.shape[0]-1)
            mask=inside&(source[sy,sx].mean(2)<70);paint(mask,[37,42,38])
            paint(inside&~mask,[194,189,167])
    if motif=='loading' and side:
        # The circular maker seal is source art, not a fabricated glyph.
        source=np.array(Image.open(RAW/'DRBDecals.png').convert('RGB').crop((3,726,145,854)))
        uu=(wz-6.75)/.43;vv=(9.88-wy)/.43
        inside=(uu>=0)&(uu<1)&(vv>=0)&(vv<1)
        sx=np.clip((uu*source.shape[1]).astype(int),0,source.shape[1]-1)
        sy=np.clip((vv*source.shape[0]).astype(int),0,source.shape[0]-1)
        paint(inside&(source[sy,sx].mean(2)<65),[39,34,28])
    if motif=='shroud' and side:
        # Photo's 90 and triple white wedge insignia, manually placed in world
        # coordinates so each side reads correctly rather than mirroring text.
        for k in range(3):
            z=-2.68+k*.20
            paint((wz>z)&(wz<z+.13)&(wy>10.61)&(wy<10.96-.9*(wz-z)),[234,225,196])
        # Seven-segment numerals 9 and 0 using the source decal's block idiom.
        for number,z in ((9,-3.45),(0,-3.12)):
            seg={0:'abcedf',9:'abcdfg'}[number]
            zz=wz-z;yy=wy-10.59
            masks={'a':(abs(yy-.31)<.025)&(zz>.02)&(zz<.18),
                   'g':(abs(yy-.16)<.025)&(zz>.02)&(zz<.18),
                   'd':(abs(yy)<.025)&(zz>.02)&(zz<.18),
                   'b':(abs(zz-.18)<.025)&(yy>.16)&(yy<.31),
                   'c':(abs(zz-.18)<.025)&(yy>0)&(yy<.16),
                   'e':(abs(zz-.02)<.025)&(yy>0)&(yy<.16),
                   'f':(abs(zz-.02)<.025)&(yy>.16)&(yy<.31)}
            for s in seg:paint(masks[s],[36,32,26])
    if motif=='lens':
        q=(u-.5)**2+(v-.5)**2;paint(q<.22,[199,221,247]);paint(q<.13,[238,244,255])
    if motif=='rail' and face=='up':paint(np.mod(wz,.22)<.06,[39,43,39])
    return im

def compile_model(specs):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[];ledger=[]
    for s in specs:
        e=s['geometry'];e['faces']={}
        for f in FACES:
            pts=HELPER['vertices'](e)[list(FACES[f])]
            w=max(5,math.ceil(np.linalg.norm(pts[1]-pts[0])*19))
            h=max(5,math.ceil(np.linalg.norm(pts[3]-pts[0])*19))
            requests.append((h,w,e['name'],f,s))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0
    for h,w,name,f,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,('atlas overflow',name,y+h)
        im=tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][f]=dict(uv=[v*16/EDGE for v in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    model=dict(credit='W128 Dust Rock Blues authored solids / face UV',
               textures={'0':'destiny:item/weapon/w123/dust_rock_blues','particle':'destiny:item/weapon/w123/dust_rock_blues'},
               elements=[copy.deepcopy(s['geometry']) for s in specs],display=json.loads((ROOT/BASE).read_bytes())['display'])
    assert len(specs)<=1000
    return model,atlas,ledger

def inspection(specs,model,atlas):
    elements=[];groups=[]
    for group in dict.fromkeys(s['group'] for s in specs):
        children=[]
        for s in specs:
            if s['group']!=group:continue
            e=copy.deepcopy(s['geometry']);r=e.pop('rotation')
            e.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
            for f in e['faces'].values():f['uv']=[v*EDGE/16 for v in f['uv']];f['texture']=0
            elements.append(e);children.append(e['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='W128 Dust Rock Blues full inspection',
                resolution=dict(width=EDGE,height=EDGE),elements=elements,outliner=groups,display=model['display'],
                textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                               source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
                destiny_w128=dict(anchor=[8,8,8],rotationOrder='RzRyRx',partition='full only',nativeAccepted=False))

def source_triangles(meshes):
    out=[]
    for m in meshes:
        for t in m['vertices'][m['faces']]:
            x,y,z=t.mean(0);mat='red'
            if z>11.15:mat='ivory'
            if y<9.2 and z>9.8:mat='ivory'
            if y<8.4 and z<12.0 and z>10:mat='rubber'
            if z>17.55:mat='red'
            if y<9.8 and -2<z<3.7:mat='steel'
            if z<-4.65:mat='darksteel' if y>10.2 else 'steel'
            if z<-5.15 and y<10.1:mat='lamp'
            if y>11.7 and z>9:mat='darksteel'
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            out.append((t,np.zeros((3,2)),np.array([[PALETTE[mat]+[255]]],np.uint8),n))
    return out

def comparison(meshes,model,atlas):
    w,h=950,310;sheet=Image.new('RGB',(w*2,1555),'#151d27');dr=ImageDraw.Draw(sheet)
    dr.text((20,12),'DUST ROCK BLUES | W128 AUTHORed SOLIDS + FACE UV | OFFLINE'.upper(),fill='#edf0f4',font_size=24)
    ref=Image.open(PHOTO).convert('RGB').crop((835,235,1870,650));ref.thumbnail((820,300));sheet.paste(ref,(15,55))
    for i,txt in enumerate([f'{len(model["elements"])} opaque cuboids / full only',
                            'Default red + ivory / silver fore-end / black inserts',
                            'Left: original 19,031-triangle FBX, schematic recolor',
                            'Right: semantic solids with authored 1024 face atlas',
                            'Exact carrier + display; bore / sight / trigger air',
                            'No moving split; generic graphs inherit full',
                            'Native / held / ADS / reload / 10-20 pending master']):
        dr.text((870,65+i*37),txt,fill='#d9e3ec',font_size=18)
    arrays=[source_triangles(meshes),HELPER['model_triangles']({'full':model},atlas,{})]
    points=np.concatenate([m['vertices'] for m in meshes]);views=[('SIDE',[-1,0,0]),('FRONT OBLIQUE',[-1,.45,-.60]),('REAR OBLIQUE',[1,.35,.60]),('BORE / LAMP / SECTION',[.25,.12,-1])]
    for row,(label,cam) in enumerate(views):
        cam=np.array(cam,float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
        q=np.c_[points@right,points@up];lo,hi=q.min(0),q.max(0);extent=((lo+hi)/2,min((w-70)/(hi[0]-lo[0]),(h-50)/(hi[1]-lo[1])))
        for col,tris in enumerate(arrays):
            im,_=HELPER['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,310+row*h))
            dr.text((col*w+15,318+row*h),label+(' / RAW FBX' if col==0 else ' / NEW'),fill='#e3ecf4',font_size=17)
    return png(sheet)

def generate():
    meshes,meta=source_meshes();specs=geometry();model,atlas,ledger=compile_model(specs)
    groups=dict(collections.Counter(s['group'] for s in specs));n=len(specs)
    historical=[BASE,BB,'art/weapons/w31/references.json','art/weapons/w31/palette-overrides.json',
                'scripts/generate_surface_w115_hammerhead.py','scripts/generate_reload_models_w100.py',
                ASSET+'textures/item/weapon/w30/dust_rock_blues.png']
    raw=[FBX,RAW/'DRBFrame_Diffuse.png',RAW/'DRBDecals.png',PHOTO]
    design=dict(stage='W128',id=ID,revision='semantic-r1',method='Authored semantic cuboids; no source-island tessellation or alpha contour',
                parts={'full':specs},groups=groups,palette=PALETTE,source=meta,
                frame=dict(mapping='[8+X*scale,8+Z*scale,8+Y*scale] after FBX carrier translation',
                           fbx_translation_cm=[0,-2.997842311859131,-11.230729103088379],scale=meta['scale'],anchor=meta['anchor'],
                           held_axis='X thin; Y up; muzzle -Z',grip_axis_endpoints=[[8,9.24,10.62],[8,6.43,12.30]]),
                partition='full only; no moving reload split exists; generic graph/ADS inherits full',
                required_air_probes={'bore_entry':[8,10.96,-5.5],'bore_depth':[8,10.96,-4.65],
                                     'rear_sight_notch':[8,12.20,10.17],'trigger_clearance':[8,8.86,9.93],
                                     'pump_side_channel':[7.17,9.05,-.78]},
                uv=dict(size=EDGE,gutter=2,face_islands=len(ledger),islands=ledger,policy='Unique aspect-proportional face islands; opaque used texels; no diffuse reprojection'),
                input_sha256={p:sha((ROOT/p).read_bytes()) for p in historical},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
                limitations=['Faceted shroud/stock curves; small screws and panel relief use UV.',
                             'Supplied-side paint/photo governs palette; reverse details are inferred.',
                             'Raw FBX comparison has schematic regional paint, not reconstructed PBR.',
                             'Static lamp texture; no emitted light, PBR or dynamic reflections.',
                             'Offline inspection only; native and 10-20 display QA pending master.'])
    review=f'''# Dust Rock Blues W128

{n} actual emitted solid cuboids, {n*6} explicit face UVs, 0 triangle adapters,
0 alpha silhouette elements. Functional groups: {json.dumps(groups)}.
One full model only. No body/magazine files, animation graph, Java, sound or
timing edits. Existing generic graph/ADS inheritance remains master-owned.

Photo: https://www.bungie.net/common/destiny2_content/screenshots/636912560.jpg
The actual local W31 photo, raw undyed DRBFrame_Diffuse, DRBDecals and binary FBX
were inspected. W31 records default dyes 449377312/313/314, no palette override.
The red long shroud, ivory stock/grip, red butt, silver six-rib fore-end and dark
inserts follow that photo. Diffuse alone is not the finished paint.

Broad deep volumes replace the 235-element W30 voxel model. Shroud crown,
lower nose drop, ivory comb/heel and swept grip define silhouette. Six metal
wrap ribs have physical depth and channels. Muzzle lip + bore walls enclose a
real opening to a recessed backstop; twin sight ears leave an open notch.
The source has an exposed trigger: no guard or stock window was invented.
Panel lines, restricted edge chips, 90/triple wedges, stock perforation grids,
rubber ribs and sleeve grooves are authored into continuous face islands.
1024 RGBA atlas, {len(ledger)} unique face rectangles, 2-pixel edge dilation.

Exact W30 carrier [8,8,8], scale {meta['scale']}, -Z muzzle and canonical display
are retained. FBX translation was applied before axis conversion and source
bounds match W30 within 1e-5. Grip is authored in the original contact region;
no recenter, axis swap, or display adjustment was applied to fit the new art.
Inspection bbmodel embeds the atlas and full-model semantic groups with neutral
group transforms. Source meshes remain read-only comparison references.

comparison.png includes the actual reference photo and four matched-camera
source/new pairs: side, front oblique, rear oblique, and bore depth. Source FBX
triangles are unchanged; source colors are clearly schematic, not shader proof.

Limits: compound curves are faceted; some small relief is UV; reverse markings
are inferred from the source; no PBR/dynamic lamp. Native parser/resource pack,
held first/third-person, ADS/inspect, generic reload, and 10-20 simultaneous
displays remain pending master. Offline render is not native acceptance.
'''
    outputs={ART+'design.json':encode(design),MODEL:encode(model),TEXTURE:png(atlas),
             ART+'inspection.bbmodel':encode(inspection(specs,model,atlas)),ART+'comparison.png':comparison(meshes,model,atlas),ART+'review.md':review.encode()}
    points=np.concatenate([HELPER['vertices'](e) for e in model['elements']])
    manifest=dict(stage='W128',id=ID,counts={'full':n},assembled_elements=n,max_assembled_elements=1000,
                  opaque_cuboids=n,triangle_adapter_elements=0,alpha_contour_elements=0,emitted_faces=n*6,
                  semantic_groups=groups,source_triangles=19031,canonical_elements=235,texture_size=[EDGE,EDGE],
                  atlas_face_islands=len(ledger),actual_bounds=[points.min(0).round(7).tolist(),points.max(0).round(7).tolist()],
                  full_only=True,canonical_display_exact=True,anchor=meta['anchor'],scale=meta['scale'],native_accepted=False,
                  generator_sha256=sha((ROOT/GENERATOR).read_bytes()),input_sha256=design['input_sha256'],raw_input_sha256=design['raw_input_sha256'],
                  output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=design['limitations'],
                  validation={'targeted_python':'scripts/qa/test_surface_w123_dust_rock_blues.py','native':'pending master','performance':'not measured'})
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w128/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w128-dust_rock_blues'))
    assert len(owned)==10 and set(outputs)<=owned
    for rel,data in outputs.items():
        path=ROOT/rel
        if args.verify:assert path.read_bytes()==data,'Regeneration differs: '+rel
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} files; {json.loads(outputs[ART+"manifest.json"])["counts"]}; full only')

if __name__=='__main__':main()
