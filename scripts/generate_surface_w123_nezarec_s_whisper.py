#!/usr/bin/env python3
"""W143 Nezarecs Whisper: semantic solids, open muzzle/guard, clean default-dye face UV.

Inert FBX is used as reference only, never exported geometry. Full model only;
canonical item/ADS/generic reload/display and all gameplay remain unchanged.
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
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/nezarec_s_whisper/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/glaive/nezarec_s_whisper.json'
MODEL = ASSET+'models/weapon_surface_w123/nezarec_s_whisper.json'
TEXTURE = ASSET+'textures/item/weapon/w123/nezarec_s_whisper.png'
RAW = Path('/tmp/destiny-weapons-w30/raw/nezarec_s_whisper/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/nezarec_s_whisper.jpg')
BB = 'art/blockbench/weapons/w30/nezarec_s_whisper.bbmodel'
EDGE = 1024
H = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
FACES = H['FACES']
PALETTE = dict(gold=[176,148,73],gold_edge=[213,187,112],black=[32,33,34],forged=[64,63,61],blade=[38,39,40],steel=[87,91,92],ivory=[210,199,155],magenta=[190,30,102],red=[204,25,56],recess=[11,13,14])

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()
def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(v): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w142:nezarec_s_whisper:'+v))
def vertices(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['vertices'](e)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    for name,expected in meta['source_files'].items():assert sha((RAW/name).read_bytes())==expected
    roots=H['parse_fbx'](RAW/"Nezarec's Whisper.fbx")
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    meshes=[]
    for n in objects:
        if n[0]!='Geometry':continue
        model=models[next(parent for child,parent in links if child==n[1][0])]
        name=model[1][1].split('\x00')[0]
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in n[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        # Original baked FBX coordinates; native shaft is +Y, not gun -Z.
        v=raw*np.array([1,-1,1])*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]);faces=np.where(ix>=0,ix,-ix-1).reshape(-1,3)
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        meshes.append(dict(name=name,vertices=v,faces=faces,uv=uv,
            texture='NezarecsWhisperDetail_Diffuse.png' if '.01.' in name else 'NezarecsWhisperBody_Diffuse.png',
            textured='.02.' not in name))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert len(meshes)==5 and sum(len(m['faces']) for m in meshes)==34330
    assert sum(len(m['faces']) for m in meshes if m['textured'])==34246
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def make_design(meta):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);sz=np.array(size,float)
        e=dict(name=name,**{'from':(c-sz/2).round(6).tolist(),'to':(c+sz/2).round(6).tolist()})
        if turn:e['rotation']=dict(origin=c.tolist(),axis=turn[0],angle=turn[1])
        parts.append(dict(group=group,material=mat,motif=motif,kind='opaque_solid_cuboid',geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='plain'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,('x',math.degrees(math.atan2(v[2],v[1]))))
    def shaft(group,name,y0,y1,r,mat,motif='plain',z=8):
        # Filled octagon: square core plus four broad flat sides, not a hollow shell.
        box(group,name+'_core',[8,(y0+y1)/2,z],[r*1.4142,y1-y0,r*1.4142],mat,motif)
        for axis in (0,2):
            for side in (-1,1):
                c=[8,(y0+y1)/2,z];c[axis]+=side*r*.85355
                sz=[r*1.4142,y1-y0,r*1.4142];sz[axis]=r*.2929
                box(group,name+f'_facet_{axis}_{side}',c,sz,mat,motif)
    # Gold lower stock; compact 3D butt and red-magenta cells, not a flat strip.
    box('stock','gold_stock',[8,4.64,8],[.52,5.40,.48],'gold','stock')
    for side in (-1,1):
        box('stock',f'stock_shoulder_{side}',[8+side*.22,4.65,8.20],[.15,5.34,.16],'gold_edge','edge',('y',side*35))
        box('stock',f'magenta_rear_cell_{side}',[8+side*.29,4.95,8.0],[.055,1.04,.36],'magenta','cell')
        box('stock',f'magenta_front_cell_{side}',[8+side*.29,6.37,8.0],[.055,.90,.36],'magenta','cell')
    shaft('butt','butt_neck',1.83,2.36,.29,'gold')
    box('butt','butt_plate',[8,1.37,8],[.90,1.12,1.63],'gold','butt')
    beam('butt','butt_back',[8,.67,7.95],[8,1.12,7.26],.98,.24,'gold','butt')
    beam('butt','butt_front',[8,.67,7.95],[8,1.12,8.76],.98,.24,'gold','butt')
    beam('butt','butt_leftflare',[8,1.07,7.24],[8,1.88,6.97],.94,.24,'gold','butt')
    beam('butt','butt_rightflare',[8,1.07,8.76],[8,1.88,9.02],.94,.24,'gold','butt')
    # Stock underguard has real air; two slender curved runs rather than a black decal.
    beam('underguard','rear_guard_toe',[8,3.96,6.85],[8,4.34,7.23],.13,.13,'black')
    beam('underguard','guard_span',[8,4.34,7.23],[8,6.12,7.23],.13,.11,'black')
    beam('underguard','guard_front',[8,6.12,7.23],[8,6.52,7.52],.13,.13,'gold')
    beam('underguard','guard_root',[8,4.34,7.23],[8,4.40,7.78],.15,.10,'black')
    for i in range(6):
        a=math.radians(i*45-35)
        box('trigger',f'trigger_arc_{i}',[8,6.27+.25*math.cos(a),7.58+.25*math.sin(a)],[.15,.24,.09],'gold','edge',('x',i*45-35))
    shaft('collars','stock_collar',7.30,7.77,.43,'gold_edge','collar')
    shaft('shaft','bare_fluted_shaft',7.76,9.63,.20,'gold','flute')
    shaft('collars','lower_grip_collar',9.57,9.80,.30,'black','collar')
    shaft('grip','ivory_bound_grip',9.78,14.10,.255,'ivory','wrap')
    shaft('collars','upper_grip_collar',14.04,14.28,.34,'black','collar')
    # Receiver/tang is a substantial 3D octagonal body with quiet forged texture.
    shaft('receiver','forged_core',14.22,18.63,.39,'forged','forged',z=7.91)
    for side in (-1,1):
        box('receiver',f'gold_top_rail_{side}',[8+side*.31,15.29,8.30],[.12,1.88,.10],'gold','edge')
        box('receiver',f'forged_cheek_{side}',[8+side*.36,16.68,7.84],[.12,1.82,.83],'forged','forged')
    box('receiver','forged_belly',[8,16.47,7.30],[.82,2.54,.45],'forged','forged')
    beam('receiver','belly_taper',[8,17.48,7.34],[8,18.65,7.53],.72,.36,'forged','forged')
    # Photo-supported pierced/ivory cheek rings are shallow UV; crown spikes are real.
    for i in range(5):
        y=16.10+i*.30;z=8.56+.18*math.sin(i*math.pi/4)
        beam('crown',f'crown_spike_base_{i}',[8,y,z-.16],[8,y+.12,z+.23],.30,.25,'forged','forged')
        beam('crown',f'crown_spike_tip_{i}',[8,y+.12,z+.21],[8,y+.19,z+.61],.13,.11,'forged','edge')
    # Gold/red crescent below the receiver. Open inner crescent, no alpha cutout.
    for i in range(7):
        a=math.radians(90-i*20);b=math.radians(90-(i+1)*20)
        outer1=[8,15.50+1.75*math.cos(a),6.70+.95*math.sin(a)]
        outer2=[8,15.50+1.75*math.cos(b),6.70+.95*math.sin(b)]
        beam('crescent',f'gold_crescent_{i}',outer1,outer2,.36,.18,'gold_edge','edge')
        inner1=[8,15.50+1.58*math.cos(a),6.70+.79*math.sin(a)]
        inner2=[8,15.50+1.58*math.cos(b),6.70+.79*math.sin(b)]
        beam('crescent',f'red_crescent_{i}',inner1,inner2,.33,.16,'red','glow')
        fill1=[8,15.50+1.42*math.cos(a),6.70+.67*math.sin(a)]
        fill2=[8,15.50+1.42*math.cos(b),6.70+.67*math.sin(b)]
        beam('crescent',f'filled_crescent_{i}',fill1,fill2,.51,.30,'forged','forged')
    beam('crescent','crescent_root',[8,15.35,7.55],[8,15.50,7.65],.46,.23,'black','forged')
    box('crescent','red_pivot_face',[8,15.09,7.24],[.70,.48,.48],'red','glow')
    box('crescent','red_pivot_bevel',[8,15.09,7.24],[.70,.42,.42],'red','glow',('x',45))
    for i in range(8):
        a=math.radians(i*45);b=math.radians((i+1)*45)
        beam('crescent',f'gold_pivot_rim_{i}',[8,15.09+.37*math.cos(a),7.24+.37*math.sin(a)],[8,15.09+.37*math.cos(b),7.24+.37*math.sin(b)],.67,.085,'gold_edge','edge')
    # Large blade root, rising quillon and forward collar.
    shaft('blade_root','blade_socket',18.59,19.61,.44,'black','binding',z=7.89)
    beam('blade_root','quillon',[8,19.03,8.25],[8,19.28,8.95],.26,.19,'black','forged')
    beam('blade_root','quillon_tip',[8,19.28,8.95],[8,19.32,9.11],.11,.09,'black','edge')
    # Broad filled blade, few clean long volumes; shallow white channels stay UV.
    box('blade','blade_core',[8,23.80,7.76],[.24,8.48,.97],'blade','ivory_channels')
    box('blade','blade_spine',[8,23.74,8.28],[.24,8.40,.13],'black','spine')
    box('blade','edge_strip',[8,23.65,7.14],[.10,8.23,.16],'steel','edge')
    for side in (-1,1):
        box('blade',f'blade_side_bevel_{side}',[8+side*.105,23.80,7.25],[.11,8.46,.19],'blade','ivory_channels',('y',side*28))
    beam('blade','point_upper',[8,27.88,8.11],[8,29.55,8.31],.19,.12,'blade','ivory_channels')
    beam('blade','point_lower',[8,27.83,7.19],[8,29.56,8.31],.11,.14,'blade','ivory_channels')
    # Tapered filled point between two sloping boundaries, not alpha or a uniform plate.
    for j,(y,depth,z) in enumerate([(28.18,.92,7.79),(28.57,.66,7.96),(28.90,.42,8.10),(29.17,.23,8.22),(29.44,.10,8.30)]):
        box('blade',f'point_fill_{j}',[8,y,z],[.18,.44,depth],'blade','ivory_channels')
    # Low relief blade ribs influence silhouette/oblique depth; fine repeated scoring is paint.
    for i in range(12):
        y=20.02+i*.57
        for side in (-1,1):
            beam('blade_ribs',f'raised_rib_{i}_{side}',[8+side*.15,y,7.13],[8+side*.15,y+.20,8.28],.035,.065,'black','edge')
    inputs=[BASE,BB,'art/weapons/w31/references.json','src/main/resources/destiny/weapons/w30.json',
            'src/main/resources/assets/destiny/items/weapon/nezarec_s_whisper.json']
    raw=[RAW/"Nezarec's Whisper.fbx",RAW/"Nezarec's Whisper.blend",RAW/'textures/NezarecsWhisperBody_Diffuse.png',RAW/'textures/NezarecsWhisperDetail_Diffuse.png',PHOTO]
    return dict(id='nezarec_s_whisper',stage='W143',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='bakedFBX[X,-Y,Z]*scale+anchor',blade_axis='+Y',display='canonical exact'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        identity=['gold stock and pink cells','ivory wrapped grip','forged black spiked receiver','gold/red open crescent','long black ribbed blade with ivory channels'],
        limitations=['Static authored default dye approximates forged black, gold, ivory and red; not dynamic PBR or recovered emissive shader',
                    'Small blade markings and cheek holes use UV; crescent and stock underguard are physically open',
                    'Full-only generic reload; 84 untextured source auxiliary triangles accounted separately, not reproduced as literal wide plates'])

def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q

def tile(spec,face,w,h):
    u,v,q=world_points(spec['geometry'],face,w,h);mat=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.6]*=.67;rgb[(edge>.6)&(edge<1.3)]*=1.08
    y=q[:,:,1];z=q[:,:,2];side=face in ('east','west')
    if motif=='wrap':
        t=np.mod(y*2.2+(q[:,:,0]-8)*.85+(z-8)*.6,1)
        rgb[t<.09]=PALETTE['gold'];rgb[(t>=.09)&(t<.15)]*=.56
        rivet=(abs(np.mod(y*2.2,1)-.46)<.055)&(abs(z-8)<.055);rgb[rivet]=PALETTE['black']
    if motif=='cell':
        rgb[(u>.14)&(u<.86)&(v>.14)&(v<.86)]=[226,49,128]
        line=(abs(np.mod(u*5+v*2,1)-.5)<.055)&(u>.18)&(u<.82)&(v>.18)&(v<.82)
        rgb[line]=[232,133,170]
    if motif=='stock' and side:
        rgb[(abs(z-8.14)<.025)]=PALETTE['gold_edge']
        if np.any(y<3.7):
            r=np.hypot((np.mod(y*2,1)-.5)*1.2,(z-8)*3);rgb[(r>.22)&(r<.33)]=PALETTE['black']
    if motif=='butt':
        rgb*=(.9+.09*np.sin(y*8))[:,:,None]
        rgb[(u<.07)|(u>.93)]=PALETTE['black']
    if motif=='flute':
        t=np.mod((q[:,:,0]+q[:,:,2])*13,1);rgb[t<.17]*=.61
    if motif=='collar':
        rgb[(v>.42)&(v<.48)]*=.5
    if motif=='forged':
        tone=.94+.035*np.sin(y*13+z*21)*np.sin(z*19-y*7)
        rgb*=tone[:,:,None]
        if side:
            for yy,zz in [(15.55,7.81),(15.85,7.80),(16.20,7.86),(16.48,7.96),(16.80,7.91)]:
                rr=np.hypot((y-yy)/.11,(z-zz)/.11)
                rgb[(rr>.66)&(rr<1.02)]=PALETTE['ivory'];rgb[rr<.60]=PALETTE['recess']
    if motif in ('ivory_channels','spine') and side:
        # Source-supported alternating ribs/channels, stable across adjacent bevels.
        yy=y+.18*(z-7.1);t=np.mod((yy-19.66)/.57,1)
        white=(t>.12)&(t<.40)&(y<28.2)&(z>7.15)&(z<8.12)
        rgb[white]=PALETTE['ivory'];rgb[(t>.40)&(t<.45)]*=.48
        red=(t>.71)&(t<.77)&(y<23.3)&(z>7.55)&(z<8.06)
        rgb[red]=PALETTE['red']
    if motif=='binding':
        rgb[np.mod(y*3.6+z*.38,1)<.15]*=.49
    if motif=='glow':
        rgb[(v>.18)&(v<.30)]=[231,56,82]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=28
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[];uvs={}
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
        im=tile(spec,face,w,h);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvs[(name,face)]=[v*16/EDGE for v in [x,y,x+w,y+h]];ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,dict(credit='W143 Nezarecs Whisper / authored solids / opaque default dye face atlas',
        textures={'0':'destiny:item/weapon/w123/nezarec_s_whisper','particle':'destiny:item/weapon/w123/nezarec_s_whisper'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])

def model_triangles(model,atlas):
    m=copy.deepcopy(model)
    for e in m['elements']:
        if 'rotation' in e:
            r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['model_triangles']({'full':m},atlas)

def inspection(d,model,atlas):
    es=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        children=[];names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Nezarecs Whisper W143 owned inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='nezarec_s_whisper.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']))

def for_preview(tris):
    # Presentation-only axis rotation; native JSON remains the original tall frame.
    out=[]
    for ps,uv,tex,n in tris:
        pp=np.c_[ps[:,0],ps[:,2],-ps[:,1]]
        out.append((pp,uv,tex,np.array([n[0],n[2],-n[1]])))
    return out

def comparison(d,meshes,atlas,model):
    w,h=820,300;sheet=Image.new('RGB',(2460,1510),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'NEZARECS WHISPER W143 / SEMANTIC SOLIDS + CLEAN DEFAULT DYE UV',28)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((940,510));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / full only / no alpha body shells','Gold stock / pink cells / ivory wrap / black spiked receiver','Open gold-red crescent / broad ribbed blade with ivory channels','Actual canonical +Y blade axis and accepted display preserved','Small cheek rings and blade scoring use UV, not noisy fragments','Raw source names differ from W30 import labels; all 34330 accounted','Offline comparison, not native or dynamic PBR certification']):label(1000,85+i*48,line,22)
    raw=[]
    for m in meshes:
        if not m['textured']:continue
        tex=np.array(Image.open(RAW/'textures'/m['texture']).convert('RGBA'))
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);n/=max(np.linalg.norm(n),1e-20);raw.append((ps,uv,tex,n))
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/nezarec_s_whisper.png'))
    ts=[for_preview(raw),for_preview(model_triangles(old,oldtex)),for_preview(model_triangles(model,atlas))]
    points=np.concatenate([m['vertices'] for m in meshes]);points=np.c_[points[:,0],points[:,2],-points[:,1]]
    for col,s in enumerate(['RIP / UNDYED DIFFUSE /34246 TEXTURED TRI','OLD CANONICAL / READ ONLY',f'NEW / {len(model["elements"])} SEMANTIC CUBOIDS']):label(col*w+15,560,s,19)
    for row,(s,cam) in enumerate([('SIDE',[1,0,0]),('BLADE OBLIQUE',[1,.4,-.50]),('BUTT OBLIQUE',[-1,.3,.5])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,600+row*h));label(col*w+15,608+row*h,s,17)
    return png(sheet)

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    review=f'''# Nezarecs Whisper W143\n\n{len(model['elements'])} authored opaque semantic cuboids, filled gold stock/shaft/grip/receiver and broad thin blade. Open crescent and stock underguard; gold and pink cells, ivory bound grip, black spiked receiver and black/ivory ribbed blade preserve exact default-photo identity. Small forged cheek rings and blade scoring are UV; no alpha silhouette shell, rip-island transfer or literal auxiliary plates.\n\nActual W31 Bungie/light.gg default photo and FBX7400/BLEND/hash-pinned source: five source records34330triangles,34246textured plus84 untextured auxiliary. W30 import labels differ from original file labels. Exact coordinate mapping bakedFBX[X,-Y,Z]*scale+anchor validated against all W30 bounds. No scripts/shaders executed. Background Blender probe did not match renamed W30 labels and failed before output; inert FBX now provides the verified original frame.\n\nCanonical +Y shaft/head axis, source scale10.957073806928383,anchor8cubed and all display transforms retained, including accepted firstperson and blade-forward thirdperson two-hand parents. Full-only generic reload/gameplay/audio remain unchanged. Static authored matte paint approximates gold/ivory/black/red and blade marks; not recovered PBR/emissive animation.\n\ncomparison.png includes actual default photo, raw undyed reference34246texturedtriangles, old canonical and new solids at matched cameras (presentation-only rotation for long horizontal comparison; native model remains tall). Native parser/pack/actual hip and ordinarythirdfront/glaiveuse/attack/guard input and20display smoke remain master-owned, not proven by offline art.\n'''
    out={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review.encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);assert 0<len(model['elements'])<=1000
    manifest=dict(id='nezarec_s_whisper',revision='W143',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=6*len(model['elements']),max_assembled_elements=1000,texture_size=[EDGE,EDGE],actual_bounds=[p.min(0).tolist(),p.max(0).tolist()],source_bounds=meta['model_bounds'],source_triangles=34330,textured_triangles=34246,untextured_auxiliary_triangles=84,source_scale=meta['scale'],source_anchor=meta['anchor'],canonical_display_exact=True,full_only=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(data) for p,data in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest);return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if args.verify:assert target.is_file() and target.read_bytes()==data,path
        else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    print('Nezarecs Whisper W143', 'verified' if args.verify else 'generated')
if __name__=='__main__':main()
