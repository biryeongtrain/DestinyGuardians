#!/usr/bin/env python3
"""W129 Halfdan-D: hand-authored solid volumes and opaque per-face paint.
Read-only reference parsing/raster helpers; writes only this worker's batch files.
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
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
ART='art/weapons/w123/halfdan_d/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/auto_rifle/halfdan_d.json'
MODEL=ASSET+'models/weapon_surface_w123/halfdan_d.json'
TEXTURE=ASSET+'textures/item/weapon/w123/halfdan_d.png'
BB='art/blockbench/weapons/w30/halfdan_d.bbmodel'
RAW=Path('/tmp/destiny-weapons-w30/raw/halfdan_d/extracted/Halfdan-D')
PHOTO=Path('/tmp/destiny-weapons-w31/references/halfdan_d.jpg')
REPORT='docs/qa/2026-10-26/w129/halfdan_d-worker.md'
EDGE=1024
FACES={'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
PALETTE={'ivory':[205,207,191],'edge':[228,229,215],'steel':[166,174,174],
         'brown':[69,36,24],'rubber':[32,33,29],'black':[24,28,27],
         'orange':[202,100,65],'olive':[73,84,61],'mag':[180,185,178]}
_HELPER=None

def helper():
    global _HELPER
    if _HELPER is None:_HELPER=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
    return _HELPER

def sha(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w129:halfdan_d:'+s))
def vertices(e):return helper()['vertices'](e)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Halfdan-D.fbx').read_bytes())==meta['source_files']['Halfdan-D/Halfdan-D.fbx']
    roots=helper()['parse_fbx'](RAW/'Halfdan-D.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    mats={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for n in objects:
        if n[0]!='Geometry':continue
        model=models[next(p for c,p in links if c==n[1][0])];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=1e-4)
        assert np.allclose(props['Lcl Translation'],[0,0,0],atol=1e-6)
        assert props['Lcl Scaling']==[100,100,100]
        ch={c[0]:c for c in n[2]};raw=np.array(ch['Vertices'][1][0]).reshape(-1,3)
        points=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        fs=[];face=[]
        for i in ch['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                fs.append(face);face=[]
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        uvdata={c[0]:c[1][0] for c in layer[2]}
        assert uvdata['MappingInformationType']=='ByPolygonVertex'
        uv=np.array(uvdata['UV']).reshape(-1,2)[np.array(uvdata['UVIndex'])].reshape(-1,3,2)
        material=next(mats[c] for c,p in links if p==model[1][0] and c in mats)
        meshes.append(dict(name=name,vertices=points,faces=np.array(fs),uv=uv,material=material))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==11642
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def make_design(meta):
    specs=[]
    def box(group,name,c,size,material,angles=(0,0,0),motif=''):
        c=np.array(c,float);s=np.array(size,float)
        specs.append(dict(group=group,material=material,motif=motif,kind='opaque_solid_cuboid',geometry={
            'name':name,'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist(),
            'rotation':dict(origin=c.tolist(),**dict(zip('xyz',angles)))}))
    def beam(group,name,a,b,width,depth,material,motif=''):
        a=np.array(a,float);b=np.array(b,float);v=b-a;assert v[0]==0
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],material,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0),motif)
    def ring(group,name,z,y,r,t,depth,material):
        for i in range(8):
            a=i*45;q=math.radians(a)
            box(group,f'{name}_{i}',[8+r*math.cos(q),y+r*math.sin(q),z],
                [2*r*math.tan(math.pi/8)+.012,t,depth],material,(0,0,a-90))
    # Major solids reflect Halfdan's long shroud and short rearward receiver.
    box('receiver','Receiver_upper',[8,12.05,5.90],[1.62,1.24,6.32],'ivory',motif='receiver')
    box('receiver','Receiver_top',[8,12.76,5.90],[1.38,.19,6.32],'edge',motif='top')
    for side in (-1,1):
        box('receiver',f'Receiver_shoulder_{side}',[8+side*.73,12.62,5.90],[.24,.26,6.32],'ivory',(0,0,side*35))
    box('receiver','Lower_housing',[8,10.83,4.65],[1.38,1.19,4.7],'brown',motif='lower')
    box('receiver','Lower_rear',[8,11.08,8.10],[1.30,.86,2.22],'brown',motif='lower')
    box('receiver','Well_front',[8,10.30,1.60],[1.50,.88,.50],'brown')
    box('receiver','Well_rear',[8,10.33,4.85],[1.46,.81,.35],'brown')
    box('receiver','Well_lower_bridge',[8,9.96,3.23],[1.43,.29,3.35],'brown',motif='well')
    box('receiver','Well_strap',[7.23,10.48,4.65],[.20,1.96,.46],'ivory',motif='strap')
    box('receiver','Charging_handle',[8.99,11.15,6.25],[.58,.28,.55],'black')
    # Fore-end is a broad, filled volume; diagonal vent recesses are painted.
    box('foreend','Handguard_upper',[8,11.96,-1.15],[1.92,1.18,7.76],'ivory',motif='upper_vents')
    box('foreend','Handguard_lower',[8,10.39,-1.15],[1.87,.85,7.76],'ivory',motif='lower_vents')
    box('foreend','Handguard_spine',[8,11.20,-1.15],[1.48,.92,7.76],'black')
    box('foreend','Shroud_roof',[8,12.63,-1.15],[1.64,.18,7.76],'edge',motif='top')
    box('foreend','Shroud_floor',[8,9.91,-1.15],[1.76,.14,7.76],'steel')
    for side in (-1,1):
        box('foreend',f'Side_rail_spine_{side}',[8+side*.98,11.02,-1.15],[.18,.30,7.70],'steel',motif='side_rail')
        box('foreend',f'Handguard_top_edge_{side}',[8+side*.86,12.48,-1.15],[.26,.28,7.76],'ivory',(0,0,side*34))
    # Actual rail teeth interrupt the top silhouette; side rail teeth remain UV.
    box('rail','Top_rail_base',[8,12.86,1.07],[.71,.18,12.0],'steel',motif='rail')
    for i in range(22):
        box('rail',f'Top_rail_tooth_{i:02}',[8,13.015,-4.68+i*.53],[.86,.17,.30],'steel')
    # Upper gas plug and lower barrel are offset vertically as in the raw asset.
    ring('front','Gas_front_ring',-5.18,11.95,.49,.22,.36,'steel')
    box('front','Gas_plug',[8,11.95,-5.51],[.58,.59,.38],'olive',motif='gas')
    box('front','Gas_center',[8,11.95,-5.74],[.19,.21,.15],'black')
    box('front','Front_bulkhead',[8,10.98,-4.94],[1.72,1.97,.30],'steel',motif='bulkhead')
    box('barrel','Barrel_shaft',[8,10.66,-6.48],[.72,.72,2.84],'steel',motif='barrel')
    ring('barrel','Barrel_collar',-6.06,10.66,.43,.16,.24,'steel')
    # Continuous octagonal bore liner and front rim, deep backstop, no alpha hole.
    ring('muzzle','Brake_body',-8.54,10.66,.43,.20,1.66,'steel')
    ring('muzzle','Muzzle_lip',-9.31,10.66,.45,.20,.24,'steel')
    ring('muzzle','Bore_liner',-8.72,10.66,.29,.10,1.05,'black')
    box('muzzle','Bore_backstop',[8,10.66,-8.12],[.50,.50,.12],'black')
    # Stock: solid upper comb, actual long opening over lower bar, sloped butt pad.
    box('stock','Buffer_socket',[8,11.88,9.41],[1.53,1.52,.57],'steel',motif='socket')
    box('stock','Buffer_tube',[8,11.92,10.06],[.86,.85,1.06],'black')
    box('stock','Stock_cheek',[8,12.03,12.78],[1.65,1.40,4.57],'ivory',motif='stock')
    box('stock','Stock_comb',[8,12.79,12.78],[1.43,.16,4.57],'edge')
    for side in (-1,1):
        box('stock',f'Stock_shoulder_{side}',[8+side*.72,12.59,12.78],[.24,.35,4.57],'ivory',(0,0,side*32))
    box('stock','Stock_window_lower',[8,10.76,12.71],[1.32,.29,4.33],'ivory',motif='stock_lower')
    box('stock','Stock_window_front',[8,11.12,10.60],[1.26,.63,.23],'steel')
    beam('stock','Stock_butt',[8,12.48,15.19],[8,8.67,15.19],1.24,.50,'rubber','butt')
    beam('stock','Stock_lower_brace',[8,10.69,14.00],[8,8.67,15.18],.70,.37,'ivory','stock_lower')
    # Halfdan pistol grip and its enclosed-but-empty trigger guard.
    box('grip','Grip_root',[8,10.10,8.12],[1.10,.88,1.17],'brown')
    beam('grip','Pistol_grip',[8,9.98,8.14],[8,6.97,9.01],1.03,1.27,'brown','grip')
    beam('grip','Grip_backstrap',[8,9.94,8.80],[8,6.88,9.60],.99,.20,'black','grip')
    beam('grip','Grip_heel',[8,6.67,8.43],[8,6.88,9.56],1.07,.33,'brown')
    beam('guard','Guard_front',[8,10.34,5.12],[8,9.12,5.28],.65,.22,'brown')
    beam('guard','Guard_floor',[8,9.12,5.28],[8,9.12,7.62],.65,.22,'brown')
    beam('guard','Guard_rear',[8,9.12,7.62],[8,10.13,8.04],.65,.22,'brown')
    beam('guard','Trigger',[8,10.51,6.78],[8,9.68,6.58],.21,.19,'steel')
    # Magazine is integrated in full; existing generic reload graph is untouched.
    box('magazine','Magazine_neck',[8,9.89,3.05],[.90,.74,2.74],'mag',motif='magazine')
    box('magazine','Magazine_body',[8,7.91,3.10],[.90,3.43,2.77],'mag',(-3,0,0),'magazine')
    box('magazine','Magazine_floor',[8,5.92,3.17],[.93,.61,2.91],'brown',motif='mag_floor')
    box('magazine','Magazine_heel',[8,5.62,3.17],[.96,.15,2.98],'black')
    # Original compact rear open iron sight, no invented magnifying optic.
    box('sight','Sight_base',[8,13.03,7.59],[.88,.27,.94],'steel',motif='sight')
    for side in (-1,1):
        box('sight',f'Sight_ear_{side}',[8+side*.35,13.61,7.57],[.19,.76,.40],'ivory',(0,0,-side*12),'sight')
    box('sight','Sight_sill',[8,13.30,7.57],[.65,.16,.39],'steel')
    inputs=[BASE,BB,'art/weapons/w31/references.json','art/weapons/w31/palette-overrides.json',
            'scripts/generate_surface_w123_beloved.py']
    return dict(stage='W129',id='halfdan_d',revision='semantic-r1',source=meta,
        coordinate_mapping='[8+raw.X*scale,8+raw.Z*scale,8+raw.Y*scale]; -Z muzzle, X width, Y up',
        anchor=meta['anchor'],scale=meta['scale'],display_policy='Canonical display copied exactly; no translation/recenter, full only.',
        method='Hand-authored broad opaque functional cuboids; no source-island mapping or alpha body shells; real bore/stock/guard/sight air.',
        palette=PALETTE,paint_evidence='Supplied default photo: ivory/silver upper, orange HAKKE stripe, brown lower/grip, white worn steel magazine. Neutral raw diffuse is not default dye.',
        starting_draft='Started near 100 functional solids; expanded for rail silhouette and octagonal deep muzzle, no element-count target.',
        max_assembled_elements=1000,groups=dict(collections.Counter(s['group'] for s in specs)),solids=specs,
        required_air_probes={'guard':[8,9.65,5.90],'sight':[8,13.65,7.57],
            'stock_window':[8,11.10,12.90],'bore_entry':[8,10.66,-9.35],'bore_depth':[8,10.66,-8.55]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in [RAW/'Halfdan-D.fbx',PHOTO,*sorted(RAW.glob('*_Diffuse.png'))]},
        limitations=['Broad solid reinterpretation; small vent recesses and muzzle side ports represented in UV, not through-cut.',
            'Single photo proves supplied-side default paint; reverse asymmetry simplified without invented text.',
            'Opaque static paint, no recovered PBR shader; native parser, held/ADS/reload and 10-20 displays pending master.'])

def tile(spec,face,w,h):
    role=spec['material'];base=np.array(PALETTE[role],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    arr=np.broadcast_to(base,(h,w,3)).copy()*(.97+.04*(1-v))[:,:,None]
    if role not in ('black','rubber','brown'):
        arr[(xx==0)|(yy==0)|(xx==w-1)|(yy==h-1)]=np.minimum(base+10,255)
    pts=vertices(spec['geometry'])[list(FACES[face])]
    world=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0])
    wy,wz=world[:,:,1],world[:,:,2];side=face in ('west','east');motif=spec['motif']
    def paint(mask,c):arr[mask]=c
    # Discrete, clean source-supported recesses; no noisy all-over bake.
    if side and motif in ('upper_vents','lower_vents'):
        start=-4.40;pitch=.79
        for i in range(9):
            z=start+i*pitch
            yc=11.96 if motif=='upper_vents' else 10.39
            diag=wz-z-(wy-yc)*(.52 if motif=='upper_vents' else -.56)
            mask=(abs(diag)<.102)&(abs(wy-yc)<(.38 if motif=='upper_vents' else .28))
            paint(mask,[72,78,73]);paint(mask&(diag>.065),[153,160,149])
        paint((abs(wy-(12.43 if motif=='upper_vents' else 10.01))<.022),[153,160,149])
    if motif=='receiver' and side:
        stripe=(wy>12.05+(wz-3.67)*.052)&(wy<12.56)&(wz>3.67)&(wz<8.82)
        paint(stripe,PALETTE['orange'])
        paint((abs(wy-11.58)<.018)&(wz>3.15)&(wz<8.78),[144,149,134])
        for z in (7.65,7.82,7.99,8.16):paint((abs(wz-z)<.025)&(wy>11.91)&(wy<12.17),[110,119,106])
    if motif in ('lower','well') and side:
        paint((abs(wy-10.42)<.025)&(wz>2.8)&(wz<8.6),[92,56,38])
        for z,y in ((5.72,10.96),(7.3,10.82),(8.45,11.1)):
            r=(wz-z)**2+(wy-y)**2
            paint(r<.075**2,[16,22,19]);paint((r<.075**2)&(r>.054**2),[101,93,69])
    if motif=='grip' and side:
        region=(wy<9.33)&(wy>7.1)
        paint(region&((np.mod(wz+wy*.55,.16)<.022)|(np.mod(wz-wy*.55,.16)<.022)),[89,51,32])
    if motif=='side_rail' and side:
        paint(np.mod(wz+4.8,.63)<.27,[80,87,84])
        paint(abs(wy-11.02)<.04,[37,42,40])
    if motif=='magazine' and side:
        for z in (2.05,2.70,3.39,4.09):
            mask=abs(wz-z)<.105
            paint(mask,[44,49,46]);paint((wz-z>.075)&(wz-z<.11),[221,222,209])
        # Broad, restrained chipped edges derived from the photo's vertical wear.
        wear=(np.sin(wy*13+wz*29)+np.sin(wy*29-wz*7)>1.4)&(np.mod(wz-.1,.67)<.14)
        paint(wear,[112,122,117])
    if motif=='barrel':paint(np.mod(wz,.32)<.075,[71,81,80])
    if spec['group']=='muzzle' and role=='steel' and face in ('west','east','up','down'):
        ports=(wz<-8.18)&(wz>-9.04)&(np.mod(wz+9.04,.43)<.22)
        paint(ports,[35,42,40])
    if motif=='stock_lower' and side:
        paint((abs(wy-10.74)<.025)&(wz>11),[132,140,129])
    if motif=='butt':paint(np.mod(wy,.16)<.045,[53,56,48])
    im=Image.fromarray(np.dstack((np.clip(arr,0,255).astype('uint8'),np.full((h,w),255,'uint8'))))
    # Supplied photo's wordmark only on its evidenced side; independent UV, no mirror.
    if motif=='receiver' and face=='west':
        dr=ImageDraw.Draw(im);font=ImageFont.load_default(size=max(6,round(h*.21)))
        # west U increases toward stock. Marking starts just behind fore-end.
        x=int(w*(3.88-2.74)/6.32);y=int(h*(12.67-12.44)/1.24)
        dr.text((x,y),'HÄKKE',font=font,fill=(236,229,205,255),stroke_width=0)
    if motif=='receiver' and side:
        # Red-orange selector loop visible below the rear stripe in default photo.
        dr=ImageDraw.Draw(im)
        def screen(z,y):
            z0,z1=pts[0,2],pts[1,2]
            return (round((z-z0)/(z1-z0)*w),round((pts[0,1]-y)/1.24*h))
        loop=[(7.28,11.83),(7.56,11.86),(7.70,11.59),(7.38,11.54),(7.28,11.83)]
        dr.line([screen(z,y) for z,y in loop],fill=(153,63,39,255),width=max(2,round(h*.055)),joint='curve')
    return im

def compile_model(d):
    requests=[]
    for s in d['solids']:
        e=s['geometry'];e['faces']={}
        for f in FACES:
            p=vertices(e)[list(FACES[f])];a=np.linalg.norm(p[1]-p[0]);b=np.linalg.norm(p[3]-p[0])
            density=26 if s['motif'] in ('receiver','upper_vents','lower_vents','magazine') else 17
            requests.append((max(5,math.ceil(b*density)),max(5,math.ceil(a*density)),e['name'],f,s))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0))
    x=y=2;row=0;ledger=[]
    for h,w,name,f,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,('atlas overflow',name,y+h)
        patch=tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(patch),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][f]=dict(uv=[q*16/EDGE for q in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    d['atlas']={'size':EDGE,'gutter':2,'face_islands':len(ledger),'islands':ledger}
    model=dict(credit='W129 Halfdan-D: authored semantic solid cuboids / default-photo paint',
        textures={'0':'destiny:item/weapon/w123/halfdan_d','particle':'destiny:item/weapon/w123/halfdan_d'},
        elements=[copy.deepcopy(s['geometry']) for s in d['solids']],display=json.loads((ROOT/BASE).read_bytes())['display'])
    return atlas,model

def inspection(d,atlas,model):
    cubes=[];groups=collections.defaultdict(list)
    for s,e in zip(d['solids'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation');b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f.update(texture=0,uv=[q*EDGE/16 for q in f['uv']])
        cubes.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W129 Halfdan-D solid inspection',
        resolution={'width':EDGE,'height':EDGE},elements=cubes,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],children=c,export=True) for g,c in groups.items()],
        textures=[dict(name='halfdan_d.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=model['display'],destiny_w129={'anchor':[8,8,8],'scale':d['scale'],'native_accepted':False,'rotation_order':'RzRyRx'})

def raw_triangles(meshes):
    images={m:np.array(Image.open(RAW/('HD'+m+'_Diffuse.png')).convert('RGBA')) for m in ('Barrel','Grip','Mag','Sight','Stock')}
    out=[]
    for m in meshes:
        img=images.get(m['material'],np.array([[[185,185,178,255]]],dtype='uint8'))
        for tri,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=max(np.linalg.norm(n),1e-20)
            uv=uv.copy();uv[:,1]=1-uv[:,1]
            out.append((tri,uv,img,n))
    return out

def comparison(d,meshes,atlas,model):
    raster=helper()
    tris=[raw_triangles(meshes),raster['model_triangles']({'full':model},atlas)]
    points=np.concatenate([m['vertices'] for m in meshes]+[vertices(e) for e in model['elements']])
    w,h=1050,365;sheet=Image.new('RGB',(2*w,1980),'#161e27');draw=ImageDraw.Draw(sheet)
    draw.text((22,14),'HALFDAN-D | W129 | AUTHORED SOLIDS + DEFAULT PHOTO PAINT | OFFLINE',fill='#eef1ed',font_size=26)
    photo=Image.open(PHOTO).convert('RGB').crop((710,290,1840,900));photo.thumbnail((800,375));sheet.paste(photo,(12,55))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / {len(model["elements"])*6} authored face UVs',
        'Ivory + silver / orange HAKKE / brown grip + lower',
        'Actual bore depth / open iron sight / guard / stock slot',
        'Raw LEFT = undyed diffuse; photo establishes final dye',
        'Full only / original frame + exact canonical display',
        'Native / first-third person / ADS / reload: pending master']):
        draw.text((830,72+i*48),line,fill='#dbe4e7',font_size=22)
    draw.text((20,430),'ORIGINAL RAW FBX + NEUTRAL DIFFUSE (NOT DEFAULT DYE)',fill='#e4e9ee',font_size=21)
    draw.text((w+20,430),'NEW SOLID VOLUMES + AUTHORED DEFAULT-PAINT FACE ATLAS',fill='#e4e9ee',font_size=21)
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.45,-.55]),('REAR THREE-QUARTER',[1,.35,.60]),('BORE / SIGHT / DEPTH',[-.28,.14,-1])]
    for row,(label,cam) in enumerate(views):
        c=np.array(cam,float);c/=np.linalg.norm(c);right=np.cross([0,1,0],c);right/=np.linalg.norm(right);up=np.cross(c,right)
        p=np.c_[points@right,points@up];lo,hi=p.min(0),p.max(0);extent=((lo+hi)/2,min((w-80)/(hi[0]-lo[0]),(h-58)/(hi[1]-lo[1])))
        for col,t in enumerate(tris):
            im,_=raster['render'](t,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,470+row*h))
            draw.text((col*w+18,478+row*h),label,fill='#e1ebed',font_size=19)
    draw.text((22,1946),'Matched axes/scale/framing. CPU diagnostic raster only. Native/gameplay/performance acceptance remains with master.',fill='#c5d0d9',font_size=20)
    return png(sheet)

def review_text(d,model):
    n=len(model['elements'])
    return f'''# Halfdan-D W129 art review

Supplied default photo: `{PHOTO}` (Bungie item 3778520450; W31 reference hash verified).
Actually inspected reference photo and HDBarrel/HDGrip/HDStock neutral diffuse via view_image.
Photo establishes ivory alloy/silver shroud and stock, orange HAKKE receiver stripe,
brown lower frame/grip and silver worn channel magazine. Raw diffuse is undyed;
it provides panel/vent/grip structure, never a finished-dye claim. W31 has no
Halfdan-specific palette override. No alternate shader or other weapon identity used.

{n} actual emitted solid cuboids, {n*6} explicit authored face UV rectangles;
0 triangle adapters, 0 alpha-contour/body-shell elements, 1 full model, no split files.
The first functional draft expanded for silhouette rail teeth and octagonal muzzle.
Long filled shroud and receiver volumes carry continuous clean UV, rather than
transplanting FBX islands. Magazine and sloped grip are thick complete solids.
Smaller recesses, ports, source-supported fasteners and magazine channels are UV.
Barrel bore has an open central tube and backstop 1.25 units behind the front;
trigger guard, stock slot and rear iron-sight aperture contain real air.
There is no invented scope, transparent lens, arbitrary triangle schema or alpha shell.

Coordinate mapping: {d['coordinate_mapping']}. Scale {d['scale']}, anchor [8,8,8].
Canonical display is copied verbatim, original grip frame preserved without recentering.
Only full art asset is output; existing generic reload/ADS, canonical/W30/W31,
registries, Java, timing and sounds remain read-only. Native parsing/substitution,
held views, ADS, reload seat and 10-20 display observations remain pending master.

1024 RGBA atlas, independent aspect-proportional face islands and 2-pixel dilation;
every exported face samples fully opaque texels. Wordmark is authored only on the
photo-evidenced side, avoiding mirrored reverse text. No source PBR or reflections
are claimed. `inspection.bbmodel` embeds texture, face UV, exact cube transforms,
semantic groups with [8,8,8] group origin, and canonical display.
`comparison.png` uses the actual default photo and unchanged original FBX topology
with neutral diffuse alongside the new geometry at matched side, front/rear quarter
and bore cameras. The diagnostic CPU raster is not a native screenshot.

Limits: faceted contours; vents and muzzle side ports are painted recesses, not
through-cuts; simplified local wear, rear-side decal layout and small compound curves.
Native quality, live reload fit and multi-display performance have not been tested.
'''

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='halfdan_d')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,model)),ART+'review.md':review_text(d,model).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);n=len(model['elements'])
    manifest=dict(stage='W129',id='halfdan_d',assembled_elements=n,counts={'full':n,'body_in_full':n-d['groups']['magazine'],'magazine_in_full':d['groups']['magazine']},
        opaque_cuboids=n,emitted_faces=n*6,alpha_contour_elements=0,triangle_adapter_elements=0,
        max_assembled_elements=1000,source_triangles=meta['source_triangles'],canonical_elements=238,semantic_groups=d['groups'],
        actual_bounds=[p.min(0).round(6).tolist(),p.max(0).round(6).tolist()],anchor=meta['anchor'],scale=meta['scale'],
        canonical_display_exact=True,full_only=True,native_accepted=False,texture_size=[EDGE,EDGE],face_islands=d['atlas']['face_islands'],
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={k:sha(v) for k,v in sorted(outputs.items())},
        validation={'targeted_test':'scripts/qa/test_surface_w123_halfdan_d.py','determinism':'generator --verify',
            'native':'pending master','gameplay':'pending master','performance':'not measured'},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w129/batch.json').read_bytes())
    scope=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w129-halfdan_d'))
    assert len(scope)==10 and set(outputs)<=scope
    for path,data in outputs.items():
        dest=ROOT/path
        if args.verify:assert dest.read_bytes()==data,'Regeneration differs: '+path
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} assets; {m["assembled_elements"]} solids / {m["emitted_faces"]} faces; full only')

if __name__=='__main__':main()
