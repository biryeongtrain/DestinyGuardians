#!/usr/bin/env python3
"""W132 Code Duello: semantic filled solids, authored default-dye face panels.
Offline only. FBX parser/CPU camera helpers are reused read-only from Beloved.
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

ROOT=Path(__file__).resolve().parents[1]
ART='art/weapons/w123/code_duello/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/rocket_launcher/code_duello.json'
MODEL=ASSET+'models/weapon_surface_w123/code_duello.json'
TEXTURE=ASSET+'textures/item/weapon/w123/code_duello.png'
BB='art/blockbench/weapons/w30/code_duello.bbmodel'
GENERATOR='scripts/generate_surface_w123_code_duello.py'
TEST='scripts/qa/test_surface_w123_code_duello.py'
WORKER='docs/qa/2026-10-26/w132/code_duello-worker.md'
RAW=Path('/tmp/destiny-weapons-w30/raw/code_duello/extracted/Code Duello')
PHOTO=Path('/tmp/destiny-weapons-w31/references/code_duello.jpg')
REFERENCES=Path('/tmp/destiny-weapons-w31/references.json')
EDGE=1024
FACES={'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
PALETTE={'teal':[28,61,69],'silver':[153,174,173],'gold':[177,146,79],
         'gold_edge':[211,184,114],'copper':[166,86,48],'black':[26,29,28],
         'rubber':[24,27,26],'steel':[68,85,85],'bore':[36,20,14],'lens':[105,48,22]}
_HELPER=None

def helper():
    global _HELPER
    if _HELPER is None:_HELPER=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
    return _HELPER

def sha(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w132:code_duello:'+s))
def vertices(e):return helper()['vertices'](e)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Code Duello.fbx').read_bytes())==meta['source_files']['Code Duello/Code Duello.fbx']
    roots=helper()['parse_fbx'](RAW/'Code Duello.fbx')
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
        uv[:,:,1]=1-uv[:,:,1]
        material=next(mats[c] for c,p in links if p==model[1][0] and c in mats)
        meshes.append(dict(name=name,vertices=points,faces=np.array(fs),uv=uv,material=material))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==33820
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def make_design(meta):
    solids=[]
    def box(group,name,c,size,mat,angles=(0,0,0),motif='panel'):
        c=np.array(c,float);s=np.array(size,float)
        solids.append(dict(group=group,material=mat,motif=motif,kind='filled_cuboid',geometry={
            'name':name,'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist(),
            'rotation':dict(origin=c.tolist(),**dict(zip('xyz',angles)))}))
    def ring(group,name,x,y,z0,z1,r,t,mat,motif='rim'):
        # Tangent opaque solids; only explicit functional bores stay open.
        for i in range(8):
            a=i*45;q=math.radians(a)
            box(group,f'{name}_{i}',[x-r*math.sin(q),y+r*math.cos(q),(z0+z1)/2],
                [2*r*math.tan(math.pi/8)+.014,t,z1-z0],mat,(0,0,a),motif)
    # Broad continuous tube panels + large central mass, never an empty skin body.
    # Front 3.2 units of the tube are intentionally open with a copper liner.
    ring('main_tube','Tube',8,12,-5.35,10.95,.80,.30,'teal','helix')
    box('main_tube','Tube_solid_heart',[8,12,4.45],[1.32,1.32,13.0],'teal',motif='helix')
    ring('bore','Copper_throat',8,12,-5.38,-2.06,.61,.11,'copper','bore_flutes')
    ring('bore','Copper_muzzle_lip',8,12,-5.43,-5.16,.75,.19,'copper','rim')
    box('bore','Bore_backstop',[8,12,-1.94],[1.20,1.20,.23],'bore')
    ring('rear_tube','Rear_tube',8,12,11.0,20.34,.59,.26,'teal','helix')
    box('rear_tube','Rear_solid_heart',[8,12,15.65],[.94,.94,9.40],'teal',motif='helix')
    # Selected raised diagonal ribs introduce real parallax and silhouette rhythm.
    # Remaining continuous spiral detail is face paint across the long panels.
    for side in (-1,1):
        for i,z in enumerate(np.arange(-4.52,10.0,1.42)):
            box('raised_ribs',f'Main_ridge_{side}_{i}',[8+side*.93,12,float(z)],[.15,1.27,.16],
                'silver',(side*-24,0,0),'helix')
        for i,z in enumerate(np.arange(12.0,20.0,1.18)):
            box('raised_ribs',f'Rear_ridge_{side}_{i}',[8+side*.705,12,float(z)],[.105,.91,.13],
                'silver',(side*-24,0,0),'helix')
    ring('transition','Breech_gold_band',8,12,10.52,11.15,.82,.20,'gold','band')
    ring('transition','Breech_teal_collar',8,12,11.13,11.63,.76,.28,'teal','band')
    ring('transition','Rear_heel_band',8,12,20.20,20.48,.66,.16,'gold','band')
    # Gold cage is separated from the tube; broad rails take the ornament in UV.
    # Fin cutouts are constructed from a floor, sloping cheeks and shared crowns.
    for side in (-1,1):
        x=8+side*.85
        box('gold_rails',f'Upper_rail_{side}',[x,13.19,1.40],[.24,.28,15.60],'gold',motif='gold_rail')
        box('gold_rails',f'Lower_rail_{side}',[x,10.79,2.95],[.24,.25,18.68],'gold',motif='gold_rail')
        box('gold_rails',f'Rear_lower_rail_{side}',[8+side*.66,11.10,16.0],[.20,.18,8.70],'gold',motif='gold_rail')
        # Continuous spine under each sequence; gold fin plates have true U air.
        for station,z0,count in [('front',.25,4),('rear',5.65,4)]:
            box('scalloped_fins',f'{station}_fin_floor_{side}',[x,13.43,z0+(count-1)*.67/2],[.20,.36,count*.67+.30],'gold',motif='filigree')
            for i in range(count):
                z=z0+i*.67
                for end in (-1,1):
                    box('scalloped_fins',f'{station}_notch_cheek_{side}_{i}_{end}',[x,13.66,z+end*.215],
                        [.20,.20,.14],'gold',(-end*30,0,0),'filigree')
            for i in range(count+1):
                box('scalloped_fins',f'{station}_crown_{side}_{i}',[x,13.64,z0-.335+i*.67],
                    [.20,.32,.19],'gold',motif='filigree')
        # Bottom reverse scallops are small but volumetric, not painted black dots.
        box('gold_rails',f'Lower_front_panel_{side}',[x,10.52,-1.9],[.22,.32,7.6],'gold',motif='filigree')
        for i in range(4):
            box('scalloped_fins',f'Bottom_scallop_lobe_{side}_{i}',[x,10.37,-1.77+i*.86],
                [.20,.26,.33],'gold',(18,0,0),'filigree')
        box('gold_rails',f'Breech_rail_slope_{side}',[x,11.04,11.0],[.20,.23,1.83],'gold',(-24,0,0),'gold_rail')
    # Full-width structural saddles connect the floating rails at actual mount sites.
    for i,z in enumerate((-3.8,4.2,9.6)):
        box('gold_rails',f'Top_saddle_{i}',[8,13.05,z],[1.85,.20,.42],'teal')
        box('gold_rails',f'Bottom_saddle_{i}',[8,10.98,z],[1.85,.22,.42],'teal')
    box('gold_rails','Top_recess_copper_inlay',[8,13.04,3.85],[.42,.13,2.5],'copper',motif='inlay')
    # Black action has broad filled faces with authored grooves and fastener seats.
    box('action','Action_mass',[8,10.31,5.20],[1.18,.89,5.40],'black',motif='action')
    box('action','Action_forward_seat',[8,10.36,2.00],[1.20,.75,1.20],'black',motif='action')
    box('grips','Foregrip',[8,9.19,2.0],[1.06,2.85,.67],'rubber',motif='foregrip')
    box('grips','Foregrip_copper_heel',[8,7.70,2.0],[.99,.22,.65],'copper',motif='rim')
    box('grips','Foregrip_base',[8,7.50,2.0],[1.00,.27,.70],'rubber')
    box('grips','Pistol_grip',[8,8.45,8.15],[1.06,3.13,1.00],'rubber',(-17,0,0),'grip')
    box('grips','Pistol_heel',[8,6.99,8.65],[1.10,.38,1.04],'black',(-17,0,0),'grip')
    # Guard is a real three-sided structural loop; copper trigger hangs in its air.
    box('guard','Guard_front',[8,9.12,5.48],[.70,1.25,.24],'black')
    box('guard','Guard_floor',[8,8.57,6.44],[.70,.23,2.15],'black')
    box('guard','Guard_rear',[8,9.14,7.42],[.70,1.25,.24],'black',(-10,0,0))
    box('guard','Copper_trigger',[8,9.32,6.63],[.19,.63,.14],'copper',(-24,0,0))
    # Original right-mounted optic: real aperture and a lens recessed behind rim.
    box('optic','Optic_mount',[8.88,11.66,5.53],[.59,.39,2.0],'black',motif='action')
    ring('optic','Optic_body',9.55,12.0,3.76,6.87,.43,.18,'teal','optic')
    ring('optic','Optic_copper_front',9.55,12.0,3.68,4.04,.43,.14,'copper','rim')
    ring('optic','Optic_gold_band',9.55,12.0,4.20,4.49,.45,.10,'gold','band')
    box('optic','Optic_recessed_lens',[9.55,12,4.67],[.66,.66,.10],'lens',motif='lens')
    box('optic','Optic_rear_termination',[9.55,12,6.74],[.74,.74,.22],'black',motif='optic')
    # Short rear iron sight has a deep open U, separate from the side telescope.
    box('sight','Rear_sight_seat',[8,12.82,19.75],[.72,.16,.54],'gold')
    for side in (-1,1):box('sight',f'Rear_sight_ear_{side}',[8+side*.28,13.03,19.75],[.16,.40,.40],'copper')
    groups=dict(collections.Counter(s['group'] for s in solids))
    readonly=[BB,BASE,'scripts/generate_surface_w123_beloved.py',
        ASSET+'items/weapon/code_duello.json',ASSET+'items/weapon_aim_w70/code_duello.json']
    readonly += [str(p.relative_to(ROOT)) for p in sorted((ROOT/(ASSET+'models/weapon_aim_w70')).glob('code_duello*.json'))]
    readonly += [str(p.relative_to(ROOT)) for p in sorted((ROOT/(ASSET+'models/weapon/rocket_launcher')).glob('code_duello_*.json'))]
    rawpaths=[RAW/'Code Duello.fbx',RAW/'084ceb80_Diffuse.png',RAW/'5a5aeb80_Diffuse.png',RAW/'e8baeb80_Diffuse.png',PHOTO,REFERENCES]
    return dict(stage='W132',id='code_duello',family='rocket_launcher',revision='authored-solid-gold-cage-v1',
        source=meta,anchor=meta['anchor'],scale=meta['scale'],coordinate_mapping='[8+X*s,8+Z*s,8+Y*s]; muzzle -Z; unchanged source hand frame',
        full_only=True,palette=PALETTE,solids=solids,groups=groups,
        paint_evidence={'photo':str(PHOTO),'raw_diffuse':'Neutral undyed structure only; not the finished default shader.',
            'observations':['Long silver/teal spiral-rib tube, narrower ribbed rear extension.',
                'Aged gold top/bottom rails, U scallops, teal borders and sparse rubbed edges.',
                'Copper inner muzzle, right-side optic lip and trigger; black separated grips.'],
            'method':'Authored continuous world-coordinate helix on broad per-face islands; restrained deterministic gold engraving/wear.'},
        air_probes={'bore_front':[8,12,-5.40],'bore_deep':[8,12,-2.20],
            'top_rail_gap':[7.15,13.025,0],'bottom_rail_gap':[7.15,10.96,0],
            'front_U_scallop':[7.15,13.73,.25],'rear_U_scallop':[8.85,13.73,5.65],
            'trigger_guard':[8,9.13,5.95],'grip_separation':[8,8.1,4.1],
            'optic_front':[9.55,12,3.73],'optic_deep':[9.55,12,4.54],
            'rear_sight':[8,13.10,19.75]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in readonly},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in rawpaths},
        limitations=['Faceted octagonal contours; selected raised ribs, remaining helix and fine engraving use UV.',
            'Gold wear is authored evidence-led paint, not recovered PBR or exact dye/shader reconstruction.',
            'Native parser/pack, held/ADS/generic reload, audio and 10-20 displays pending master.'])

def tile(spec,face,w,h):
    e=spec['geometry'];p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    pos=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0])
    x,y,z=[pos[:,:,i] for i in range(3)]
    mat=spec['material'];motif=spec['motif'];c=np.array(PALETTE[mat],float)
    arr=np.broadcast_to(c,(h,w,3)).copy()
    edge=np.minimum.reduce([u,1-u,v,1-v])
    # Clean material planes first; restrained roughness, no stochastic dirt spray.
    wave=np.sin(x*19+z*7)*np.sin(y*23-z*3)
    arr+=wave[:,:,None]*1.5
    if motif=='helix':
        theta=np.arctan2(y-12,x-8)
        phase=z/(.71 if spec['group']!='rear_tube' and not e['name'].startswith('Rear_') else .59)+theta/(2*math.pi)*2.1
        q=(np.cos(phase*2*math.pi)+1)/2
        a=np.clip((q-.17)/.80,0,1)**1.4
        teal=np.array(PALETTE['teal']);silver=np.array(PALETTE['silver'])
        arr=teal+(silver-teal)*a[:,:,None]
        arr-=((q<.15)*12)[:,:,None]
        arr+=wave[:,:,None]*2
    elif mat in ('gold','gold_edge'):
        # Teal border, a continuous bright rub, and small aged recessed patches.
        arr[edge<.075]=PALETTE['teal']
        arr[(edge>=.075)&(edge<.105)]=PALETTE['gold_edge']
        pat=np.sin(z*13+y*17+x*11)*np.cos(z*23-y*11)
        wear=(pat>.82)&(edge>.11)
        arr[wear]=np.array([114,101,61])
        if motif=='filigree':
            # Repeated shallow arcs, kept in UV instead of source mesh fragments.
            line=np.abs(np.sin(z*9.3+.75*np.sin(y*18)))<.055
            arr[line&(edge>.16)]=[116,100,55]
    elif mat=='copper':
        arr+=(np.cos(u*math.pi*2)*13)[:,:,None]
        arr[edge<.055]=[217,142,91]
        if motif=='bore_flutes':
            arr*= (.68+.32*(np.sin(u*8*math.pi)>.15))[:,:,None]
    elif motif in ('grip','foregrip'):
        arr+=((np.sin(y*29)>0)*5)[:,:,None]
        if motif=='grip':
            diamond=(np.sin(y*47+z*38)*np.sin(y*47-z*38)>.25)
            arr[diamond]=[45,48,45]
        else:
            grooves=np.abs(np.sin(y*6.4))<.16
            arr[grooves]=[10,13,12]
    elif motif=='action':
        arr[edge<.045]=[57,64,61]
        grooves=(y>10.1)&(np.abs(np.sin(y*25))<.22)
        arr[grooves]=[12,17,16]
        # Photo-supported small copper fastener seats, only side faces.
        if face in ('east','west'):
            for zz in (3.0,4.7,6.2,7.3):
                r=(z-zz)**2+(y-10.15)**2
                arr[(r<.004)&(r>.0013)]=PALETTE['copper']
    elif motif=='optic':
        arr[(z>5.25)&(z<6.64)]=[31,35,32]
        for zz in (4.93,6.48):
            arr[np.abs(z-zz)<.065]=PALETTE['gold']
        seat=(z-5.83)**2+(y-11.84)**2
        if face in ('east','west'):
            arr[(seat<.025)&(seat>.012)]=PALETTE['copper']
    elif motif=='lens':
        rr=((x-9.55)/.34)**2+((y-12)/.34)**2
        arr[:]=[47,23,13];arr[rr<.7]=[119,59,25];arr[rr<.24]=[167,94,40]
        arr[(rr>.53)&(rr<.59)]=[208,127,60]
    else:
        arr[edge<.035]=c*.75
    return Image.fromarray(np.dstack((np.clip(arr,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))

def compile_model(d):
    requests=[]
    for s in d['solids']:
        e=s['geometry'];e['faces']={}
        for f in FACES:
            p=vertices(e)[list(FACES[f])];a=np.linalg.norm(p[1]-p[0]);b=np.linalg.norm(p[3]-p[0])
            density=24 if s['motif']=='helix' else 18
            requests.append((max(4,math.ceil(b*density)),max(4,math.ceil(a*density)),e['name'],f,s))
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
    model=dict(credit='W132 Code Duello: authored solid gold cage / continuous ribbed teal tube / default-photo paint',
        textures={'0':'destiny:item/weapon/w123/code_duello','particle':'destiny:item/weapon/w123/code_duello'},
        elements=[copy.deepcopy(s['geometry']) for s in d['solids']],display=json.loads((ROOT/BASE).read_bytes())['display'])
    return atlas,model

def inspection(d,atlas,model):
    cubes=[];groups=collections.defaultdict(list)
    for s,e in zip(d['solids'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation');b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f.update(texture=0,uv=[q*EDGE/16 for q in f['uv']])
        cubes.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W132 Code Duello editable solid inspection',
        resolution={'width':EDGE,'height':EDGE},elements=cubes,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],children=c,export=True) for g,c in groups.items()],
        textures=[dict(name='code_duello.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=model['display'],destiny_w132={'anchor':[8,8,8],'scale':d['scale'],'native_accepted':False,'rotation_order':'RzRyRx','full_only':True})

def raw_triangles(meshes):
    images={m:np.array(Image.open(RAW/file).convert('RGBA')) for m,file in
            [('Main','084ceb80_Diffuse.png'),('Scope','5a5aeb80_Diffuse.png'),('Scope Glass','e8baeb80_Diffuse.png')]}
    out=[]
    for m in meshes:
        for tri,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=max(np.linalg.norm(n),1e-20)
            out.append((tri,uv,images[m['material']],n))
    return out

def comparison(d,meshes,atlas,model):
    raster=helper();tris=[raw_triangles(meshes),raster['model_triangles']({'full':model},atlas)]
    points=np.concatenate([m['vertices'] for m in meshes]+[vertices(e) for e in model['elements']])
    w,h=1050,345;sheet=Image.new('RGB',(2100,1970),'#161e27');draw=ImageDraw.Draw(sheet)
    draw.text((22,14),'CODE DUELLO | W132 | AUTHORED SOLID REMODEL | OFFLINE COMPARISON',fill='#eef1ed',font_size=26)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1000,465));sheet.paste(photo,(12,55))
    for i,line in enumerate([f'{len(model["elements"])} opaque solid cuboids / {len(model["elements"])*6} face UVs',
        'Actual default photo: Bungie 2496242052',
        'Teal / silver spiral tube, aged GOLD open cage',
        'COPPER deep bore / right optic / trigger; black grips',
        'Real rail gaps, U notches, guard and sight recess',
        'Original anchor, scale, muzzle -Z and full display',
        'Native / held / ADS / generic reload: pending master']):
        draw.text((1040,95+i*56),line,fill='#dbe4e7',font_size=22)
    draw.text((20,540),'ORIGINAL FBX + RAW NEUTRAL DIFFUSE (NOT DEFAULT DYE)',fill='#e4e9ee',font_size=21)
    draw.text((w+20,540),'NEW FILLED SOLIDS + PHOTO-BASED DEFAULT MATERIAL PAINT',fill='#e4e9ee',font_size=21)
    views=[('RIGHT SIDE / OPTIC',[1,0,0]),('FRONT OBLIQUE / GOLD CAGE',[1,.42,-.57]),
        ('REVERSE OBLIQUE / GRIPS',[-1,.30,.52]),('MUZZLE / OPTIC / REAL DEPTH',[.26,.17,-1])]
    for row,(label,cam) in enumerate(views):
        extent=raster['frame'](points,cam,w,h)
        for col,t in enumerate(tris):
            im,_=raster['render'](t,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,575+row*h))
            draw.text((col*w+18,580+row*h),label,fill='#e1ebed',font_size=19)
    draw.text((22,1943),'Matched camera/frame in each row. CPU diagnostic raster only. Native/gameplay/performance acceptance remains with master.',fill='#c5d0d9',font_size=19)
    return png(sheet)

def review_text(d,model):
    n=len(model['elements'])
    return f'''# Code Duello W132 art review

Reference: actual default photo `{PHOTO}`, Bungie item 2496242052, hash
`01bb55eb7026cb4ab762df9b406628e0a89307ef8a189ec0dabe57be9c3b6366`.
The reference photo and neutral 084ceb80 diffuse were actually opened with view_image.
Photo identity: long dark teal/silver spiral ribs; separate aged GOLD top/bottom
rails with U scallops; COPPER bore, right side optic and trigger; black grips.
Raw diffuse is neutral undyed material structure, not the completed default dye.

{n} emitted opaque solid cuboids / {n*6} explicit authored UV faces / 0 triangle
adapters, alpha-contour parts, source islands or voxel transplants. Full only.
The draft starts from long tube panels with a filled central heart, structural
rails and two substantial grips; additional output constructs octagonal bore and
optic walls, selected raised spiral ridges, actual scallop cheeks and collars.
These parts add silhouette, cross section, parallax or functional openings.
Broad tube panels have continuous world-coordinate helical UV paint; shallow
filigree, fine ribs, small fastener seats and grip tread live in per-face paint.
Gold uses coherent teal-edged panels with restrained aged patches and rubs.

Muzzle: 3.3-unit open copper-lined throat with a recessed dark backstop. Right
optic: visible copper rim and open recess ending in a painted opaque lens.
The gold cage has separate upper/lower rails and an air gap to the tube between
mount saddles. The upper fin U scallops, trigger loop, space between grips and
rear iron sight are real geometry air, not alpha or black silhouette paint.

Frame: {d['coordinate_mapping']}. Anchor {d['anchor']}, original scale {d['scale']}.
Existing full native display is copied exactly; no recenter, invented resource
split, custom graph, registration, Java, ADS, generic reload, timing or audio edits.
Candidate resource: `destiny:weapon_surface_w123/code_duello`.
1024 atlas, independent aspect-proportional face islands with opaque 2px gutters.
Editable inspection embeds exact solid transforms, UVs, texture and full display.
Comparison includes actual default photo, textured original FBX with neutral
albedo explicitly labeled, new side, both obliques and muzzle/depth views.
CPU renders are diagnostic and do not establish native acceptance.

Limitations: faceted octagonal tube/collars; selected ribs have volume while finer
spiral rhythm is UV. Gold engraving and wear are simplified and authored, not
recovered PBR/default shader equivalence. Master still owns pack/native parser
and rotation acceptance, first/third person and hand fit, ADS/optic obstruction,
existing generic reload/muzzle placement/timing/audio, and 10-20 displays.
'''

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    ref=next(r for r in json.loads(REFERENCES.read_bytes()) if r['id']=='code_duello')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,model)),ART+'review.md':review_text(d,model).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);n=len(model['elements'])
    manifest=dict(stage='W132',id='code_duello',assembled_elements=n,counts={'full':n},opaque_cuboids=n,emitted_faces=n*6,
        alpha_contour_elements=0,triangle_adapter_elements=0,max_assembled_elements=1000,source_triangles=meta['source_triangles'],
        semantic_groups=d['groups'],actual_bounds=[p.min(0).round(6).tolist(),p.max(0).round(6).tolist()],
        anchor=meta['anchor'],scale=meta['scale'],canonical_display_exact=True,full_only=True,native_accepted=False,
        texture_size=[EDGE,EDGE],face_islands=d['atlas']['face_islands'],generator_sha256=sha(Path(__file__).read_bytes()),
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={k:sha(v) for k,v in sorted(outputs.items())},
        validation={'targeted_test':TEST,'determinism':'generator --verify','native':'pending master','performance':'not measured'},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w132/batch.json').read_bytes())
    scope=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w132-code_duello'))
    assert len(scope)==10 and set(outputs)<=scope
    for path,data in outputs.items():
        dest=ROOT/path
        if args.verify:assert dest.read_bytes()==data,'Regeneration differs: '+path
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} assets; {m["assembled_elements"]} solids / {m["emitted_faces"]} faces; full only')

if __name__=='__main__':main()
